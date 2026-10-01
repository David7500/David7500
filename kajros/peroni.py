"""Tir vlaka na postaji, s table SŽ.

GTFS perona nima (ne IJPP ne NeTEx), feed v živo tudi ne. Ima ga tabla
prihodov in odhodov na potniski.sz.si, ki je za Cloudflarovim izzivom; beremo
jo prek `api.modra.ninja` (glej `docs/MERITVE.md`, 25. 9. 2026). Vir je
tretja oseba brez lastnika, zato je tir **dodatek**: kadar ga ni ali je star,
ga prikaz izpusti, nikoli ne ugiba.

Izmerjeno na 20 postajah: 14 jih ima tir pri vseh vlakih, 6 (Jesenice, Novo
mesto, Kranj, Dobova, Trbovlje, Škofja Loka) pri nobenem. Ena tabla je
13-17 s, s premorom ~20 s na postajo, zato vir bere ena sama nit, postajo za
postajo -- in to ne zmore vseh postaj vsakih nekaj minut. Velike se berejo
pogosto, majhne redko (`_RAZMIK_SQL`). Tabla kaže le vlake, ki še pridejo,
zato je treba brati čez ves dan -- in tir se čez dan spreminja: v Ljubljani
je bil pri 8 od 121 vlakov drugačen od „običajnega“, ki ga kaže brezavta.si.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

import requests

from . import config, db

TZ = ZoneInfo(config.TIMEZONE)

# Kako pogosto preberemo postajo, ki tir ima: najprometnejše (Ljubljana,
# Maribor, Celje) vsakih `OBHOD_S`, ostale redkeje v razmerju s prometom, a
# vsaj vsakih `NAJDLJE_S`. Ena nit zmore ~180 tabel na uro; vseh 266 postaj
# na deset minut bi jih zahtevalo 1 600.
OBHOD_S = config.PERONI_SECONDS
PROMET_POLN = 150            # postankov v voznem redu; toliko in več = `OBHOD_S`
NAJDLJE_S = 2 * 3600
# Postaja brez tira na tabli: vsak dan znova, ker se to lahko spremeni.
BREZ_TIRA_S = 24 * 3600
# Prazna tabla (noč, postaja brez prometa) ne pove, ali tir ima.
PRAZNA_S = 3600
# Premor med dvema branjema, da zadetki v predpomnilniku (70 ms) ne postanejo
# naval zahtev na vir, ki nam ni dolžan ničesar.
PREMOR_S = 2
# Po napaki postaja počaka, da ena pokvarjena ne zasede niti.
PO_NAPAKI_S = 300

# Razmik med branji postaje s tirom. En izraz za oboje: kdaj je postaja na
# vrsti in kdaj je njen tir prestar, da bi ga pokazali.
_RAZMIK_SQL = ("MIN(:najdlje, :obhod * MAX(1.0, :poln * 1.0 / MAX({t}promet, 1)))")
_PARAMETRI = {"najdlje": NAJDLJE_S, "obhod": OBHOD_S, "poln": PROMET_POLN}


def stevilka(train_no: str) -> str:
    """'LPV 2010' -> '2010'. Tabla SŽ nosi samo številko."""
    return train_no.split()[-1].lstrip("0") if train_no else ""


def _kljuc_imena(ime: str) -> str:
    # SŽ piše "Lavrica", IJPP "Lavrica(Železniški)". Vseh 266 naših postaj
    # se tako ujame z imenom pri SŽ (izmerjeno 25. 9. 2026).
    return ime.replace("(Železniški)", "").strip().casefold()


def razberi(tabla: dict) -> tuple[dict[str, str], int]:
    """Tabla SŽ -> ({številka vlaka: tir}, število vlakov na tabli).

    Odhod ima prednost pred prihodom, a prazen tir ne prekrije polnega.
    Nadomestni avtobus ("Bus") tira nima in ni vlak.
    """
    tiri: dict[str, str] = {}
    vlaki = set()
    for e in (tabla.get("departures") or []) + (tabla.get("arrivals") or []):
        st = (e.get("Št. vlaka") or "").strip()
        if not st or st.casefold() == "bus":
            continue
        st = st.lstrip("0")
        vlaki.add(st)
        tir = (e.get("Tir") or "").strip()
        if tir and st not in tiri:
            tiri[st] = tir
    return tiri, len(vlaki)


def _get(pot: str):
    r = requests.get(f"{config.PERONI_URL}{pot}",
                     headers={"User-Agent": config.USER_AGENT}, timeout=90)
    r.raise_for_status()
    return r.json()


def osvezi_postaje(conn: sqlite3.Connection) -> int:
    """Seznam postaj SŽ, preslikan na naša imena. Vrne število znanih.

    Postaja, ki je pri nas ni (tuja, zaprta), se ne bere -- vlaka z njo tako
    ne bi mogli pokazati nikjer.
    """
    # Promet določi vrstni red prvega branja: Ljubljana mora imeti tir v
    # minuti po zagonu, ne čez uro, ko pride na vrsto po abecedi.
    nase = {_kljuc_imena(r[0]): (r[0], r[1]) for r in conn.execute(
        "SELECT st.name, COUNT(*) FROM station st JOIN sched s USING(stop_id) "
        "JOIN trip t USING(trip_id) WHERE t.network = 'zeleznica' AND t.mode != 'bus' "
        "GROUP BY st.name")}
    vrstice = []
    for p in _get("/postaje_oprema"):
        ime = nase.get(_kljuc_imena(p.get("naziv") or ""))
        if ime and p.get("st"):
            vrstice.append((str(p["st"]), *ime))
    with conn:
        conn.executemany(
            "INSERT INTO peron_postaja(st, postaja, promet) VALUES(?, ?, ?) "
            "ON CONFLICT(st) DO UPDATE SET postaja = excluded.postaja, "
            "promet = excluded.promet", vrstice)
    return len(vrstice)


def na_vrsti(conn: sqlite3.Connection, zdaj: float,
             odlozene: Iterable[str] = ()) -> sqlite3.Row | None:
    """Postaja, ki je najdlje čakala in je že na vrsti; sicer None.

    Neznana postaja je na vrsti „zdaj“, ne „od nekdaj“: prvo branje vseh 266
    traja uro in pol, in z rokom 0 je Ljubljana ves ta čas čakala -- po
    prvem branju je bila 21 min brez novega, torej brez tira na zaslonu.
    """
    odlozene = list(odlozene)
    return conn.execute(
        "SELECT st, postaja FROM ("
        "  SELECT st, postaja, promet, preverjeno + CASE"
        "    WHEN preverjeno = 0 THEN :zdaj"
        "    WHEN vlakov = 0 THEN :prazna"
        f"    WHEN ima_tir = 1 THEN {_RAZMIK_SQL.format(t='')}"
        "    ELSE :brez END AS rok"
        "  FROM peron_postaja"
        f"  WHERE st NOT IN ({','.join(':o%d' % i for i in range(len(odlozene)))}))"
        " WHERE rok <= :zdaj ORDER BY rok, promet DESC LIMIT 1",
        {**_PARAMETRI, "prazna": PRAZNA_S, "brez": BREZ_TIRA_S, "zdaj": int(zdaj),
         **{f"o{i}": st for i, st in enumerate(odlozene)}}).fetchone()


def zapisi(conn: sqlite3.Connection, st: str, postaja: str, datum: str,
           tabla: dict, zdaj: float) -> int:
    """Tabla ene postaje v bazo. Vrne število vlakov s tirom."""
    tiri, vlakov = razberi(tabla)
    ts = int(zdaj)
    with conn:
        # `prvi` se ob posodobitvi ne spremeni: razlika do `tir` je sprememba
        # perona čez dan, in prav ta je potniku najbolj koristna.
        conn.executemany(
            "INSERT INTO peron(datum, vlak, postaja, tir, prvi, videno) "
            "VALUES(?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(datum, vlak, postaja) DO UPDATE SET "
            "  tir = excluded.tir, videno = excluded.videno",
            [(datum, v, postaja, t, t, ts) for v, t in tiri.items()])
        # Prazna tabla ne pove, ali postaja tir ima -- znanje ostane.
        conn.execute(
            "UPDATE peron_postaja SET preverjeno = ?, vlakov = ?, "
            "ima_tir = CASE WHEN ? > 0 THEN 1 WHEN ? > 0 THEN 0 ELSE ima_tir END "
            "WHERE st = ?", (ts, vlakov, len(tiri), vlakov, st))
    return len(tiri)


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Ena nit, ena postaja naenkrat, dokler `stop` ni postavljen."""
    conn = db.connect()
    napak = 0
    seznam_do = 0.0
    # Po napaki postaja počaka v pomnilniku, ne v bazi: `preverjeno` pomeni
    # „tabla je bila prebrana“, in prikaz po njem sodi, ali je tir še velja.
    odlozene: dict[str, float] = {}
    try:
        while not stop.is_set():
            zdaj = time.time()
            if zdaj >= seznam_do:
                try:
                    n = osvezi_postaje(conn)
                    seznam_do = zdaj + 24 * 3600
                    log(f"peroni: {n} postaj SŽ; tabla velikih vsakih {OBHOD_S // 60} min,"
                        f" majhnih najdlje {NAJDLJE_S // 3600} h")
                except Exception as exc:    # noqa: BLE001 -- vir ni naš
                    conn.rollback()            # glej `zamude_sz.teci()`
                    log(f"peroni: seznama postaj ni bilo mogoče dobiti: {exc}")
                    seznam_do = zdaj + 600
            odlozene = {st: do for st, do in odlozene.items() if do > zdaj}
            p = na_vrsti(conn, zdaj, odlozene)
            if p is None:
                stop.wait(60)
                continue
            try:
                datum = datetime.now(TZ).date().isoformat()
                zapisi(conn, p["st"], p["postaja"], datum,
                       _get(f"/postaje/{p['st']}/prihodi_raw?datum={datum}"), zdaj)
                if napak:
                    log(f"peroni: vir spet odgovarja (po {napak} napakah)")
                napak = 0
            except Exception as exc:        # noqa: BLE001
                conn.rollback()            # glej `zamude_sz.teci()`
                odlozene[p["st"]] = zdaj + PO_NAPAKI_S
                napak += 1
                if napak == 1:
                    log(f"peroni: {p['postaja']} ni uspelo: {exc}")
                stop.wait(30)
            stop.wait(PREMOR_S)
    finally:
        conn.close()


def tiri(conn: sqlite3.Connection, zahteve: Iterable[tuple[str, str, str]],
         zdaj: float | None = None) -> dict[tuple[str, str, str], tuple[str, str]]:
    """{(datum, vlak, postaja): (tir, prvi)} za veljavne tire.

    Veljaven je tir, ki ga je potrdilo ZADNJE branje postaje (vlak, ki je
    odpeljal, s table izgine), to branje pa ni zamujeno za več kot dva
    razmika -- sicer je vir obstal in bolje je ne povedati nič.
    """
    zahteve = set(zahteve)
    if not zahteve:
        return {}
    datumi = sorted({z[0] for z in zahteve})
    postaje = sorted({z[2] for z in zahteve})
    zdaj = int(zdaj if zdaj is not None else time.time())
    vrstice = conn.execute(
        "SELECT p.datum, p.vlak, p.postaja, p.tir, p.prvi FROM peron p "
        "JOIN peron_postaja pp ON pp.postaja = p.postaja "
        f"WHERE p.datum IN ({','.join(':d%d' % i for i in range(len(datumi)))}) "
        f"AND p.postaja IN ({','.join(':p%d' % i for i in range(len(postaje)))}) "
        "AND p.videno >= pp.preverjeno "
        f"AND pp.preverjeno + 2 * {_RAZMIK_SQL.format(t='pp.')} >= :zdaj",
        {**_PARAMETRI, "zdaj": zdaj,
         **{f"d{i}": d for i, d in enumerate(datumi)},
         **{f"p{i}": p for i, p in enumerate(postaje)}})
    return {(r[0], r[1], r[2]): (r[3], r[4]) for r in vrstice
            if (r[0], r[1], r[2]) in zahteve}


def dopolni(conn: sqlite3.Connection, vrstice: list[dict],
            kako: Callable[[dict], tuple[str, str, str | None] | None],
            kljuc: str = "tir", zdaj: float | None = None) -> None:
    """Vrsticam pripiše `kljuc` (tir) in `<kljuc>_prej` (kadar se je spremenil).

    `kako(vrstica)` vrne (številka vlaka, ime postaje, ura v ISO) ali None.
    Datum je koledarski dan ure, ne prometni dan: vlak ob 00:30 je na tabli
    SŽ naslednjega dne.
    """
    kje = {}
    for v in vrstice:
        k = kako(v)
        if k and k[0] and k[2]:
            kje[id(v)] = (k[2][:10], stevilka(k[0]), k[1])
    najdeno = tiri(conn, kje.values(), zdaj)
    for v in vrstice:
        t = najdeno.get(kje.get(id(v)))
        if t:
            v[kljuc] = t[0]
            if t[1] != t[0]:
                v[f"{kljuc}_prej"] = t[1]
