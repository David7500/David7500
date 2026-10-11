"""Lege avtobusov IJPP naravnost z NAP (SIRI-VM), mimo derp.si.

Zakaj: lege IJPP, ki jih beremo z derp.si, so prav ta vir, le pretvorjen
(`derp-si/ijpp-rt`, `ijppService.js`: SIRI z NAP na 5 s v GTFS-RT). 8. 10.
2026 je strežnik RT derp.si od 16:00 zavračal povezave in zemljevid je ostal
brez medkrajevnih avtobusov, čeprav so vozila lego pošiljala naprej. NAP je
izvirnik: naprava na vozilu -> Realis -> NAP.

Dostop: račun na nap.si in odobritev vsebine „SIRI dinamični podatki - API“
(zaprošeno 8. 10. 2026). Prijava je v `${KAJROS_DATA_DIR}/.nap-prijava` kot
`e-naslov:geslo` (postavi jo `deploy/nap.sh`) ali v `KAJROS_NAP_PRIJAVA`.
API sprejme avtentikacijo basic (`b2b.siri.api.sl.pdf`), zato brez žetonov.

Id vožnje: `VehicleJourneyRef` je NeTEx id
`SI:SI0:ServiceJourney:<GUID>:IJPP`, zadnji štirje bajti GUID-a so `trip_id`
v GTFS IJPP -- isto pretvorbo dela `derp-si/ijpp-rt` (`realisToIjpp`).

Kam gre:

* `vehicle_now` za vsa pripeta vozila; zmaga novejša lega (`zapisi`).
* zamuda iz lege (`iz_lege.opazuj`) za vozila, ki jih derp.si ta hip nima
  (`collector.lege_derp`), kadar feed zamud vožnje ne nosi -- ob izpadu
  derp.si torej za vse.
* kadar imata vozilo oba, se primerjata (`primerjaj`): ista vožnja, odmik
  lege ob istem času, kateri je svežejši. Vse v `meta.nap` za `/admin`.

NAP nima mestnega LPP in ne primestnih vozil LPP (`LJLPP…`), ki jih derp.si
v isti feed doda iz LPP-jevega vira: 9. 10. 2026 55 od ~80 vozil „samo
derp“. Vlakov nima (`VehicleMode` 705-krat `bus`).
"""
from __future__ import annotations

import json
import sqlite3
import statistics
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Callable

import requests

from . import collector, config, db, geo, iz_lege, stats, viri

TZ = collector.TZ

#: Zahtevek za lege vseh vozil (dokumentacija NAP, „Pridobivanje lokacij vseh
#: vozil“). Brez filtra: ene linije potnik ne izbere vnaprej.
_ZAHTEVEK = """<?xml version="1.0" encoding="utf-8"?>
<ServiceRequest xmlns="http://www.siri.org.uk/siri">
  <RequestTimestamp>{cas}</RequestTimestamp>
  <VehicleMonitoringRequest>
    <RequestTimestamp>{cas}</RequestTimestamp>
  </VehicleMonitoringRequest>
</ServiceRequest>"""

#: `derp-si/ijpp-rt` popravlja `RecordedAtTime`, ki je natanko uro v
#: prihodnosti (±3 min) -- naprava očitno pošlje lokalni čas z napačnim
#: zamikom. Popravek prevzamemo; koliko jih je, šteje `popravljenih`.
URA_NAPREJ_S, URA_TOLERANCA_S = 3600, 180
#: Lega, ki je po popravku še v prihodnosti, je napačna.
NAJVEC_NAPREJ_S = 30
#: derp.si izpusti vožnje, ki se začnejo čez več kot 30 min (vozilo čaka na
#: izhodišču prejšnjo vožnjo). Ista meja, da je primerjava primerljiva.
PREZGODAJ_S = 1800
#: Lege derp.si so „zdaj“, dokler jih je zajem potrdil v tem času. Bere jih
#: na 10 s; minuta je šest zgrešenih branj.
DERP_SVEZE_S = 60
#: 401/403 = dostop (še) ni odobren. Ne trkaj na 10 s, ko se ne more nič
#: spremeniti brez človeka.
NI_DOSTOPA_CAKAJ_S = 600
TIMEOUT_S = (10, 20)


class NiDostopa(RuntimeError):
    """NAP je prijavo zavrnil: napačno geslo ali vsebina ni odobrena."""

    def __init__(self, http: int):
        super().__init__(f"NAP zavrnil prijavo (HTTP {http})")
        self.http = http


def prijava() -> tuple[str, str] | None:
    """(uporabnik, geslo) ali None. Bere se ob vsakem obhodu, da prijava, ki
    jo skrbnik postavi pozneje, velja brez ponovnega zagona."""
    vrstica = config.okolje("NAP_PRIJAVA", "") or ""
    if not vrstica:
        try:
            vrstica = (config.DATA_DIR / ".nap-prijava").read_text(encoding="utf-8")
        except OSError:
            return None
    # Uporabnik je e-naslov, dvopičja nima; geslo ga sme imeti.
    uporabnik, _, geslo = vrstica.strip().partition(":")
    return (uporabnik, geslo) if uporabnik and geslo else None


def ijpp_id(ref: str | None) -> str | None:
    """`SI:SI0:ServiceJourney:00000000-1177-0008-0000-000000049908:IJPP` ->
    `301320` (zadnji štirje bajti GUID-a)."""
    deli = (ref or "").split(":")
    if len(deli) != 5:
        return None
    guid = deli[3].replace("-", "")
    if len(guid) != 32:
        return None
    try:
        return str(int(guid[-8:], 16))
    except ValueError:
        return None


def _lokalno(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _otrok(el, *pot: str):
    """Otrok po lokalnem imenu: imenski prostor SIRI je pri NAP en, a ga ne
    vežemo -- `derp-si/ijpp-rt` ga prav tako odreže."""
    for ime in pot:
        if el is None:
            return None
        el = next((o for o in el if _lokalno(o.tag) == ime), None)
    return el


def _besedilo(el, *pot: str) -> str | None:
    o = _otrok(el, *pot)
    return o.text.strip() if o is not None and o.text else None


def _cas(s: str | None) -> float | None:
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()


def razberi(vsebina: bytes, zdaj: float) -> tuple[list[dict], dict]:
    """Odgovor SIRI -> [vozilo], števci.

    Vozilo: `vozilo`, `ijpp` (trip_id po pretvorbi), `ts`, `lat`, `lon`,
    `smer`, `nacin`. Brez lege ali s časom zunaj meja se izpusti in šteje.
    """
    koren = ET.fromstring(vsebina)
    dostava = next((e for e in koren.iter() if _lokalno(e.tag) == "ServiceDelivery"), koren)
    odgovor = _cas(_besedilo(dostava, "ResponseTimestamp")) or zdaj
    st = {"vozil": 0, "popravljenih": 0, "starih": 0, "naprej": 0, "brez_lege": 0,
          "brez_id": 0}
    out = []
    for va in koren.iter():
        if _lokalno(va.tag) != "VehicleActivity":
            continue
        st["vozil"] += 1
        mvj = _otrok(va, "MonitoredVehicleJourney")
        vozilo = _besedilo(mvj, "VehicleRef")
        ts = _cas(_besedilo(va, "RecordedAtTime"))
        try:
            lat = float(_besedilo(mvj, "VehicleLocation", "Latitude") or "")
            lon = float(_besedilo(mvj, "VehicleLocation", "Longitude") or "")
        except ValueError:
            lat = lon = None
        if lat is None or ts is None or not vozilo:
            st["brez_lege"] += 1
            continue
        if abs(ts - odgovor - URA_NAPREJ_S) <= URA_TOLERANCA_S:
            ts -= URA_NAPREJ_S
            st["popravljenih"] += 1
        if ts - odgovor > NAJVEC_NAPREJ_S:
            st["naprej"] += 1
            continue
        if odgovor - ts > collector.POSITION_FRESH_S:
            st["starih"] += 1
            continue
        ijpp = ijpp_id(_besedilo(mvj, "VehicleJourneyRef"))
        if ijpp is None:
            st["brez_id"] += 1
            continue
        try:
            smer = float(_besedilo(mvj, "Bearing") or "")
        except ValueError:
            smer = None
        out.append({"vozilo": vozilo, "ijpp": ijpp, "ts": int(ts), "lat": lat,
                    "lon": lon, "smer": smer, "nacin": _besedilo(mvj, "VehicleMode")})
    return out, st


def _nacin(conn: sqlite3.Connection) -> dict[str, str]:
    """trip_id -> `mode` (bus/rail). Vlake NAP morda nosi; ali jih, in pod
    katerim id-jem, se bo videlo -- do takrat jih le štejemo."""
    def build():
        return {r[0]: r[1] for r in conn.execute("SELECT trip_id, mode FROM trip")}
    return collector._cached(conn, "nap_nacin", None, build)


def pripni(conn: sqlite3.Connection, vozila: list[dict],
           zdaj: float) -> tuple[list[dict], dict]:
    """Vozilo -> naša vožnja in obratovalni dan. Isti prevod starega id-ja
    kot pri derp.si (`zamenjava`), isti izbor dneva kot pri vlakih SŽ, ki
    `start_date` tudi nimajo (`collector.resolve_service_date`)."""
    okna = collector._rail_trip_windows(conn)
    zdaj_dt = datetime.fromtimestamp(zdaj, TZ)
    dnevi = collector._service_dates(conn, zdaj_dt)
    zamenjave = collector._zamenjave(conn)
    nacin = _nacin(conn)
    agencije = collector._agencije(conn)
    st = {"pripetih": 0, "brez_voznje": 0, "brez_dneva": 0, "prezgodaj": 0, "vlakov": 0}
    out = []
    for v in vozila:
        tid = v["ijpp"]
        if tid not in okna and tid in zamenjave:
            tid = zamenjave[tid][0]
        if tid not in okna:
            st["brez_voznje"] += 1
            continue
        dan = collector.resolve_service_date(tid, okna[tid], dnevi.get(tid), zdaj_dt)
        if dan is None:
            st["brez_dneva"] += 1
            continue
        if stats.polnoc(dan) + okna[tid][0] - zdaj > PREZGODAJ_S:
            st["prezgodaj"] += 1
            continue
        if nacin.get(tid) != "bus":
            st["vlakov"] += 1
            continue
        st["pripetih"] += 1
        out.append({**v, "trip_id": tid, "dan": dan, "agency": agencije.get(tid)})
    return out, st


def primerjaj(vozila: list[dict], derp: dict | None) -> dict:
    """NAP proti derp.si po vozilu. derp.si bere isti vir, torej morata
    vožnja in lega ob istem času soupasti; razlika je napaka pretvorbe na
    eni strani. `prednost_s` = za koliko je NAP-ova lega novejša."""
    if derp is None:
        return {"derp": False}
    skupni = [(v, derp[v["vozilo"]]) for v in vozila if v["vozilo"] in derp]
    odmiki = [geo.haversine(v["lat"], v["lon"], d[2], d[3])
              for v, d in skupni if v["ts"] == d[1]]
    prednost = [v["ts"] - d[1] for v, d in skupni]
    nap = {v["vozilo"] for v in vozila}
    return {
        "derp": True, "skupnih": len(skupni),
        "ista_voznja": sum(v["ijpp"] == d[0] for v, d in skupni),
        "isti_cas": len(odmiki),
        "odmik_m": round(statistics.median(odmiki), 1) if odmiki else None,
        "odmik_max_m": round(max(odmiki), 1) if odmiki else None,
        "prednost_s": statistics.median(prednost) if prednost else None,
        "samo_nap": len(nap - derp.keys()), "samo_derp": len(derp.keys() - nap),
    }


def zapisi(conn: sqlite3.Connection, pripeta: list[dict], derp: dict | None,
           zdaj: float) -> dict:
    """Lega v `vehicle_now` za vsa vozila, zamuda iz lege samo za tista, ki
    jih derp.si nima.

    Lega: NAP je izvirnik in je novejši (9. 10. 2026 mediana 7-20 s na ~640
    skupnih vozilih, ista vožnja 99,8 %, odmik ob istem času 0,1 m), zato
    zmaga po `seen_ts`; derp-ova starejša lega istega vozila je ne povozi.
    Zamuda iz lege: za vozilo, ki ga derp.si nosi, jo računa njegov zajem
    (`iz_lege.iz_feeda`) -- isto sled bi sicer vodili dve niti.
    """
    zapisanih = prehodov = 0
    for v in pripeta:
        conn.execute(
            "INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, bearing,"
            "                        vehicle_id) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id) DO UPDATE SET "
            "  service_date=excluded.service_date, seen_ts=excluded.seen_ts,"
            "  lat=excluded.lat, lon=excluded.lon, bearing=excluded.bearing,"
            "  speed_ms=NULL, stop_seq=NULL, status=NULL,"
            "  vehicle_id=excluded.vehicle_id "
            "WHERE excluded.seen_ts > vehicle_now.seen_ts",
            (v["trip_id"], v["dan"], v["ts"], v["lat"], v["lon"], v["smer"], v["vozilo"]))
        zapisanih += 1
        if (derp is not None and v["vozilo"] in derp
                and not iz_lege.nap_vodi(v.get("agency"), zdaj)):
            continue
        if config.ZAMUDA_IZ_LEGE and iz_lege.brez_feeda(v["trip_id"], zdaj):
            prehodov += iz_lege.opazuj(conn, v["trip_id"], v["dan"], v["ts"],
                                       v["lat"], v["lon"])
    # Kot `collector.ingest_positions`: ob izpadu derp.si briše le ta nit.
    conn.execute("DELETE FROM vehicle_now WHERE seen_ts < ?", (int(zdaj) - 3600,))
    return {"zapisanih": zapisanih, "prehodov": prehodov}


def korak(conn: sqlite3.Connection, vsebina: bytes, zdaj: float) -> dict:
    """En odgovor NAP: razberi, primerjaj, pripni, zapiši, povzemi v `meta`."""
    vozila, st = razberi(vsebina, zdaj)
    iz_lege.nap_prebran(zdaj)
    derp = collector.lege_derp(zdaj, DERP_SVEZE_S)
    st.update(primerjaj(vozila, derp))
    pripeta, s = pripni(conn, vozila, zdaj)
    st.update(s)
    st.update(zapisi(conn, pripeta, derp, zdaj))
    st.update(ts=int(zdaj), bajtov=len(vsebina))
    db.set_meta(conn, "nap", json.dumps(st, sort_keys=True))
    # Ključ predpomnilnika `/api/vehicles`: brez tega ob izpadu derp.si
    # zemljevid NAP-ovih leg ne bi videl nikoli.
    db.set_meta(conn, "positions_fetched", str(int(zdaj)))
    iz_lege.pospravi(zdaj, conn)
    conn.commit()
    return st


def beri(seja: requests.Session, prijava_: tuple[str, str]) -> bytes:
    cas = datetime.now(TZ).isoformat()
    with viri.branje("nap") as b:
        r = seja.post(config.NAP_URL, data=_ZAHTEVEK.format(cas=cas).encode(),
                      headers={"Content-Type": "application/xml"},
                      auth=prijava_, timeout=TIMEOUT_S)
        b.http = r.status_code
        if r.status_code in (401, 403):
            raise NiDostopa(r.status_code)
        r.raise_for_status()
        b.bajtov = len(r.content)
    return r.content


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: tuj strežnik ne sme zamikati zajema derp.si."""
    conn = db.connect()
    seja = requests.Session()
    seja.headers["User-Agent"] = config.USER_AGENT
    napak, brez_prijave = 0, False
    try:
        while not stop.is_set():
            zacetek = time.time()
            p = prijava()
            if p is None:
                if not brez_prijave:
                    log("NAP: prijave ni (deploy/nap.sh), lege samo z derp.si")
                    viri.caka("nap", "prijave ni: na strežniku `deploy/nap.sh`")
                brez_prijave = True
                stop.wait(60)
                continue
            if brez_prijave:
                viri.caka("nap", None)
            brez_prijave = False
            cakaj = config.NAP_SECONDS
            try:
                korak(conn, beri(seja, p), time.time())
                if napak:
                    log(f"NAP spet odgovarja (po {napak} napakah)")
                napak = 0
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"NAP: {exc}")
                http = getattr(exc, "http", None)
                if http:
                    cakaj = NI_DOSTOPA_CAKAJ_S
                try:
                    s = json.loads(db.get_meta(conn, "nap") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(time.time()), http=http)
                    db.set_meta(conn, "nap", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            stop.wait(max(1.0, cakaj - (time.time() - zacetek)))
    finally:
        conn.close()
