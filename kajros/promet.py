"""Promet na cestah z NAP: koliko traja vožnja z avtom, minuto za minuto.

Zakaj: vprašanje „kdaj je vlak hitrejši od avta“ (slo-tech, 14. 10. 2026)
rabi čas vožnje z avtom ob konici, ne dolžine, deljene s hitrostjo. NAP ga ima
(FCD NCUP, potovalni časi DARS), a samo trenutno stanje -- zgodovine ni
nikjer, zato jo posnamemo sami. Vsebini sta odobreni 9. 10. 2026 do 9. 10.
2029, prijava je ista kot za lege (`nap.prijava`).

Dva vira, ena nit, vsako minuto:

* **FCD stanje** (`b2b.fcd.datexii33.status`): čas vožnje odseka ceste.
  Odgovor nosi samo odseke, ki so ta hip počasnejši od proste vožnje
  (14. 10. 2026: vseh 11 201 vsaj za 20 %), zato odsotnost pomeni „prosto“,
  ne „ni podatka“. Kdaj podatek sploh je bil, pove `obhod`: vrzel med dvema
  obhodoma je neznano, ne prosto. Metapodatki pravijo „avtoceste“, v
  odgovoru je tudi 617 odsekov znotraj ljubljanske obvoznice.
* **Potovalni časi AC** (`b2b.traveltimes.promet.datexii33`): deset
  avtocestnih relacij DARS (LJ - MB, LJ - KP …) z že sešteto vožnjo.

FCD se piše kot `obs`: samo ob spremembi za vsaj `PRAG_DS` od zadnje
ZAPISANE vrednosti, `NULL` ko odsek izgine (spet prosto). Izmerjeno na šestih
zaporednih odgovorih: ~700 sprememb, ~600 novih in ~600 izginulih odsekov na
minuto, ~40-60 MB na dan. Zato svoja baza (`config.PROMET_DB`), ne glavna: ta
se vleče z maline in varnostno kopira, prikaz pa tega ne rabi.

Geometrije odsekov (`b2b.fcd.datexii33.locations`, 107 MB gzip, 3 GB XML,
osveži se letno) nit ne bere; rabi jo šele preslikava odseka na pot.
"""
from __future__ import annotations

import gzip
import io
import json
import sqlite3
import threading
import time
import xml.etree.ElementTree as ET
from typing import Callable

import requests

from . import config, db, nap, viri

#: Pod pol sekunde je šum: mediana odseka je 8,1 s (p90 18,2 s). Na šestih
#: odgovorih 14. 10. 2026 prag 0,1 s 1 100 sprememb na minuto, 0,5 s 700.
PRAG_DS = 5
TIMEOUT_S = (10, 60)

SHEMA = """
CREATE TABLE IF NOT EXISTS obhod(
    ts INTEGER PRIMARY KEY,         -- čas objave FCD
    odsekov INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS fcd(
    odsek INTEGER NOT NULL,         -- id iz FCD lokacij
    ts INTEGER NOT NULL,
    cas_ds INTEGER,                 -- desetinke sekunde; NULL = spet prosto
    PRIMARY KEY (odsek, ts)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS fcd_zdaj(   -- zadnja zapisana vrednost, za prag
    odsek INTEGER PRIMARY KEY,
    cas_ds INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS fcd_odsek(
    odsek INTEGER PRIMARY KEY,
    prosto_ds INTEGER,              -- čas brez prometa, kot ga da FCD
    prvic INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ac(
    relacija TEXT NOT NULL,
    ts INTEGER NOT NULL,            -- čas objave DARS
    cas_s INTEGER NOT NULL,
    prosto_s INTEGER,
    PRIMARY KEY (relacija, ts)
) WITHOUT ROWID;
"""


def povezi(path=None) -> sqlite3.Connection:
    conn = db.connect(path or config.PROMET_DB)
    conn.executescript(SHEMA)
    return conn


def _lok(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def razberi_fcd(vsebina: bytes) -> tuple[int | None, dict[int, tuple[int, int | None]]]:
    """Odgovor FCD -> (čas objave, {odsek: (čas, čas brez prometa)}) v
    desetinkah sekunde. NAP ga pošlje kot datoteko gzip (12 MB razpakiran),
    zato po kosih: celo drevo bi bilo za ~11 000 odsekov po nepotrebnem."""
    if vsebina[:2] == b"\x1f\x8b":
        vsebina = gzip.decompress(vsebina)
    objava = None
    odseki: dict[int, tuple[int, int | None]] = {}
    odsek = cas = prosto = polje = None
    for dogodek, el in ET.iterparse(io.BytesIO(vsebina), events=("start", "end")):
        ime = _lok(el.tag)
        if dogodek == "start":
            if ime == "physicalQuantity":
                odsek = cas = prosto = None
            elif ime in ("travelTime", "freeFlowTravelTime"):
                polje = ime
            continue
        if ime == "duration" and polje:
            try:
                ds = round(float(el.text) * 10)
            except (TypeError, ValueError):
                ds = None
            if polje == "travelTime":
                cas = ds
            else:
                prosto = ds
        elif ime in ("travelTime", "freeFlowTravelTime"):
            polje = None
        elif ime == "predefinedLocationReference":
            try:
                odsek = int(el.get("id"))
            except (TypeError, ValueError):
                odsek = None
        elif ime == "publicationTime" and objava is None:
            t = nap._cas((el.text or "").strip())
            objava = int(t) if t else None
        elif ime == "physicalQuantity":
            if odsek is not None and cas is not None:
                odseki[odsek] = (cas, prosto)
            el.clear()
    return objava, odseki


def zapisi_fcd(conn: sqlite3.Connection, ts: int, odseki: dict) -> dict:
    """En odgovor FCD v dnevnik. Isti čas objave dvakrat = nespremenjeno."""
    if conn.execute("SELECT 1 FROM obhod WHERE ts = ?", (ts,)).fetchone():
        return {"nespremenjeno": True}
    prej = {r[0]: r[1] for r in conn.execute("SELECT odsek, cas_ds FROM fcd_zdaj")}
    vrstice = [(o, ts, c) for o, (c, _) in odseki.items()
               if o not in prej or abs(c - prej[o]) >= PRAG_DS]
    prosti = [(o, ts, None) for o in prej.keys() - odseki.keys()]
    conn.executemany("INSERT OR IGNORE INTO fcd VALUES(?,?,?)", vrstice + prosti)
    # Prag se meri od zadnje ZAPISANE vrednosti, ne prebrane (kot `obs`):
    # počasno lezenje se tako sešteje in ne izgine.
    conn.executemany("INSERT INTO fcd_zdaj VALUES(?,?) ON CONFLICT(odsek) DO UPDATE "
                     "SET cas_ds = excluded.cas_ds", [(o, c) for o, _, c in vrstice])
    conn.executemany("DELETE FROM fcd_zdaj WHERE odsek = ?", [(o,) for o, _, _ in prosti])
    conn.executemany(
        "INSERT INTO fcd_odsek VALUES(?,?,?) ON CONFLICT(odsek) DO UPDATE "
        "SET prosto_ds = excluded.prosto_ds "
        "WHERE excluded.prosto_ds IS NOT NULL AND prosto_ds IS NOT excluded.prosto_ds",
        [(o, p, ts) for o, (_, p) in odseki.items()])
    conn.execute("INSERT INTO obhod VALUES(?,?)", (ts, len(odseki)))
    return {"odsekov": len(odseki), "novih": sum(o not in prej for o, _, _ in vrstice),
            "zapisanih": len(vrstice) + len(prosti), "prostih": len(prosti)}


def razberi_ac(vsebina: bytes) -> tuple[int | None, list[tuple[str, int, int | None]]]:
    """Odgovor potovalnih časov AC -> (čas objave, [(relacija, čas, čas brez
    prometa)]) v sekundah. Vsota je v `basicData` relacije; njenih ~500
    delov poti tu ne rabimo."""
    if vsebina[:2] == b"\x1f\x8b":
        vsebina = gzip.decompress(vsebina)
    koren = ET.fromstring(vsebina)

    def otrok(el, ime):
        return next((o for o in el if _lok(o.tag) == ime), None)

    def trajanje(bd, ime):
        el = otrok(bd, ime)
        el = otrok(el, "duration") if el is not None else None
        try:
            return round(float(el.text))
        except (AttributeError, TypeError, ValueError):
            return None

    objava = otrok(koren, "publicationTime")
    t = nap._cas((objava.text or "").strip()) if objava is not None else None
    out = []
    for pq in koren:
        if _lok(pq.tag) != "physicalQuantity":
            continue
        ime = next((v.text.strip() for v in pq.iter()
                    if _lok(v.tag) == "value" and v.text and v.text.strip()), None)
        bd = otrok(pq, "basicData")
        cas = trajanje(bd, "travelTime") if bd is not None else None
        if ime and cas is not None:
            out.append((ime, cas, trajanje(bd, "freeFlowTravelTime")))
    return (int(t) if t else None), out


def zapisi_ac(conn: sqlite3.Connection, ts: int, relacije: list) -> int:
    """Nove vrstice; ista objava se ne zapiše dvakrat."""
    pred = conn.total_changes
    conn.executemany("INSERT OR IGNORE INTO ac VALUES(?,?,?,?)",
                     [(ime, ts, cas, prosto) for ime, cas, prosto in relacije])
    return conn.total_changes - pred


def _get(seja: requests.Session, b, url: str, prijava: tuple[str, str]) -> bytes:
    r = seja.get(url, auth=prijava, timeout=TIMEOUT_S)
    b.http = r.status_code
    if r.status_code in (401, 403):
        raise nap.NiDostopa(r.status_code)
    r.raise_for_status()
    b.bajtov = len(r.content)
    return r.content


def _povzetek(glavna: sqlite3.Connection, kljuc: str, st: dict) -> None:
    """Stanje v `meta` glavne baze: `/admin` in `viri.zapisano` gledata tja."""
    try:
        db.set_meta(glavna, kljuc, json.dumps(st, sort_keys=True))
        glavna.commit()
    except sqlite3.Error:
        glavna.rollback()


def korak_fcd(conn, glavna, seja, prijava) -> dict:
    with viri.branje("promet_fcd") as b:
        vsebina = _get(seja, b, config.PROMET_FCD_URL, prijava)
    zacetek = time.monotonic()
    objava, odseki = razberi_fcd(vsebina)
    if objava is None:
        raise ValueError("FCD brez časa objave")
    st = zapisi_fcd(conn, objava, odseki)
    conn.commit()
    if not st.get("nespremenjeno"):
        _povzetek(glavna, "promet_fcd", {**st, "ts": objava, "bajtov": len(vsebina),
                                         "ms": round((time.monotonic() - zacetek) * 1000)})
    return st


def korak_ac(conn, glavna, seja, prijava) -> int:
    with viri.branje("promet_ac") as b:
        vsebina = _get(seja, b, config.PROMET_AC_URL, prijava)
    objava, relacije = razberi_ac(vsebina)
    if objava is None:
        raise ValueError("potovalni časi AC brez časa objave")
    novih = zapisi_ac(conn, objava, relacije)
    conn.commit()
    if novih:
        _povzetek(glavna, "promet_ac", {"ts": objava, "relacij": len(relacije)})
    return novih


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: 12 MB XML na minuto ne sme zamikati zajema zamud."""
    conn = povezi()
    glavna = db.connect()
    seja = requests.Session()
    seja.headers["User-Agent"] = config.USER_AGENT
    napak = {"promet_fcd": 0, "promet_ac": 0}
    try:
        while not stop.is_set():
            zacetek = time.time()
            prijava = nap.prijava()
            if prijava is None:
                for k in napak:
                    viri.caka(k, "prijave ni: na strežniku `deploy/nap.sh`")
                stop.wait(300)
                continue
            cakaj = config.PROMET_SECONDS
            for kljuc, korak in (("promet_fcd", korak_fcd), ("promet_ac", korak_ac)):
                viri.caka(kljuc, None)
                try:
                    korak(conn, glavna, seja, prijava)
                    if napak[kljuc]:
                        log(f"{kljuc} spet odgovarja (po {napak[kljuc]} napakah)")
                    napak[kljuc] = 0
                except Exception as exc:    # noqa: BLE001 -- vir ni naš
                    conn.rollback()         # glej `zamude_sz.teci()`
                    napak[kljuc] += 1
                    if napak[kljuc] == 1:
                        log(f"{kljuc}: {exc}")
                    if getattr(exc, "http", None):
                        cakaj = nap.NI_DOSTOPA_CAKAJ_S
            stop.wait(max(1.0, cakaj - (time.time() - zacetek)))
    finally:
        conn.close()
        glavna.close()
