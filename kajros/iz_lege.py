"""Zamuda iz lege vozila -- za vožnje, ki jih feed zamud ne nosi.

Zakaj: od 21. 9. 2026 IJPP `trip_updates` nima nobene vožnje z veljavnostjo
od 21. 9. (Nomago ~430 na dan, Arriva 51), `vehicle_positions` pa ista vozila
da. Tabla je pri njih pisala „brez podatka“, četudi je bil avtobus na
zemljevidu. Števec `collector.lega_brez_zamude` to pokaže; ta modul zapolni.

Kako: vsaka lega se projicira na traso vožnje (`deljenje.Voznja`). Kadar dve
zaporedni legi, največ `NAJVEC_RAZMIK_S` narazen, oklepata postanek, je čas
prehoda linearno vmes, zamuda pa ta čas minus vozni red. Zapiše se v `run` in
`obs` kot vrednost iz feeda, z `feed_ts` = časom lege PO prehodu -- torej je
prehod potrjen (`stats.potrjen_prehod`) in vse, kar bere `run`, dela naprej
brez sprememb.

Izmerjeno 25. 9. 2026 s to kodo na vožnjah, ki imajo oboje (lege 11:40-12:04,
1 551 prehodov; Arriva, Nomago, LPP primestni, AP Murska Sobota): razlika
proti feedu mediana -4 s, absolutna mediana 5 s, p90 54 s, 92 % v 60 s in
96 % v 120 s. Brez okna voznega reda za prvo lego in brez meje hitrosti je bil
p90 759 s: krožna linija se je projicirala na napačen krak, lega pa je med
dvema točkama skočila čez osem postajališč. Cena: 0,13 ms na lego (mediana).

Izhodišča ne merimo: vozilo pred odhodom kroži po postajališču in „prehod“
izhodišča je bil v meritvi 10 min prezgodaj.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# `collector` uvozi ta modul, zato ga tu beremo šele ob klicu.
from . import collector, config, deljenje

TZ = ZoneInfo(config.TIMEZONE)

#: Dve legi dlje narazen ne povesta, kdaj je vozilo prevozilo postanek vmes.
NAJVEC_RAZMIK_S = 60
#: Hitreje vzdolž trase avtobus ne vozi; tak skok je napačna projekcija.
NAJVEC_HITROST_MS = 30
#: Lega dlje od trase ni na tej vožnji (ali pa je GPS slab).
ODMIK_MAX_M = 150
#: Kje na trasi sme biti prva lega: od toliko zamude ...
OKNO_ZAMUDA_S = 3600
#: ... do toliko prehitevanja. Brez okna se krožna linija ujame na napačen krak.
OKNO_PREHITEVA_S = 1200
#: Kako dolgo po zadnji omembi v feedu zamud vožnja še velja za pokrito.
FEED_POZABI_S = 300
#: Sled vožnje, o kateri toliko časa ni bilo lege, se pozabi.
SLED_POZABI_S = 3600

_zaklep = threading.Lock()
#: trip_id -> kdaj ga je feed zamud nazadnje omenil (time.time()).
_v_feedu: dict[str, float] = {}
#: Kdaj je feed zamud prvič prebran. Pred tem ne vemo, katere vožnje nosi.
_prvic: float | None = None
#: (trip_id, dan) -> (t_s, along, zadnji zapisani stop_seq, kdaj osveženo)
_sled: dict[tuple[str, str], tuple[float, float, int, float]] = {}


def zabelezi_feed(trip_ids, zdaj: float | None = None) -> None:
    """Vožnje, ki jih je feed zamud pravkar nosil. Kliče `collector.ingest`."""
    global _prvic
    zdaj = time.time() if zdaj is None else zdaj
    with _zaklep:
        if _prvic is None:
            _prvic = zdaj
        for t in trip_ids:
            _v_feedu[t] = zdaj


def brez_feeda(trip_id: str, zdaj: float | None = None) -> bool:
    """Ali feed zamud to vožnjo res izpušča -- in ne le še ni bil prebran.

    Po zagonu počakamo, da sta prebrana oba vira (IJPP in LPP, oba na 30 s):
    sicer bi prve lege vožnje, ki jo feed nosi, šle v `run` kot iz lege.
    """
    zdaj = time.time() if zdaj is None else zdaj
    with _zaklep:
        if _prvic is None or zdaj - _prvic < 2 * config.POLL_SECONDS:
            return False
        return zdaj - _v_feedu.get(trip_id, 0.0) > FEED_POZABI_S


def _cas(p: dict) -> float:
    return p["dep_s"] if p["dep_s"] is not None else p["arr_s"]


def _okno(v: deljenje.Voznja, t_s: float) -> tuple[float, float]:
    """Del trase, kjer je vozilo ob `t_s` lahko, po voznem redu."""
    ps = v.postanki
    lo = [p["along"] for p in ps if _cas(p) <= t_s - OKNO_ZAMUDA_S]
    hi = [p["along"] for p in ps if _cas(p) >= t_s + OKNO_PREHITEVA_S]
    return (lo[-1] if lo else -1.0), (hi[0] if hi else float("inf"))


def prehodi(v: deljenje.Voznja, prej: tuple[float, float] | None,
            t_s: float, along: float, zapisan_seq: int) -> list[tuple[dict, float]]:
    """Postanki, ki jih je vozilo prevozilo med `prej` in to lego, s časom prehoda.

    `zapisan_seq` je zadnji že zapisani postanek: tresenje lege naprej in nazaj
    ob postajališču ne sme dati dveh prehodov istega postanka.
    """
    if prej is None:
        return []
    t0, a0 = prej
    if not (0 < t_s - t0 <= NAJVEC_RAZMIK_S) or along <= a0:
        return []
    if (along - a0) / (t_s - t0) > NAJVEC_HITROST_MS:
        return []
    out = []
    for i, p in enumerate(v.postanki):
        if i == 0 or p["stop_seq"] <= zapisan_seq:
            continue
        if a0 < p["along"] <= along:
            out.append((p, t0 + (p["along"] - a0) / (along - a0) * (t_s - t0)))
    return out


def opazuj(conn: sqlite3.Connection, trip_id: str, dan: str, ts: int,
           lat: float, lon: float) -> int:
    """Ena lega vožnje brez zamud. Vrne število zapisanih prehodov."""
    v = deljenje.voznja(conn, trip_id)
    if v is None:
        return 0
    polnoc = datetime.fromisoformat(dan).replace(tzinfo=TZ).timestamp()
    t_s = ts - polnoc
    kljuc = (trip_id, dan)
    sled = _sled.get(kljuc)
    if sled is None:
        od, do = _okno(v, t_s)
    else:
        od, do = sled[1] - deljenje.NAZAJ_MAX_M, float("inf")
    along, odmik = v.trasa.projiciraj(lat, lon, od_m=od, do_m=do)
    if odmik > ODMIK_MAX_M:
        return 0
    zapisan = sled[2] if sled else 0
    pari = prehodi(v, (sled[0], sled[1]) if sled else None, t_s, along, zapisan)
    zadnji = len(v.postanki) - 1
    for p, t_prehod in pari:
        zamuda = round(t_prehod - _cas(p))
        je_konec = p is v.postanki[zadnji]
        _zapisi(conn, trip_id, dan, p["stop_seq"],
                zamuda if je_konec else None, None if je_konec else zamuda, ts)
        zapisan = p["stop_seq"]
    # Lega nazaj po trasi (tresenje) ne premakne sledi nazaj.
    if sled is None or along >= sled[1]:
        _sled[kljuc] = (t_s, along, zapisan, time.time())
    else:
        _sled[kljuc] = (sled[0], sled[1], zapisan, time.time())
    return len(pari)


def _zapisi(conn: sqlite3.Connection, trip_id: str, dan: str, seq: int,
            arr: int | None, dep: int | None, ts: int) -> None:
    """Isto kot zapis iz feeda v `collector.ingest`, brez varoval za feedove
    napake (ničla, odpoklic prehoda) -- prehod iz lege je opažen, ne sporočen."""
    last = conn.execute(
        "SELECT delay_arr, delay_dep FROM obs WHERE trip_id=? AND service_date=? "
        "AND stop_seq=? ORDER BY feed_ts DESC LIMIT 1", (trip_id, dan, seq)).fetchone()
    if collector.worth_logging(last, arr, dep):
        conn.execute(
            "INSERT OR IGNORE INTO obs"
            "(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts,observed_at) "
            "VALUES(?,?,?,?,?,?,?)", (trip_id, dan, seq, arr, dep, ts, int(time.time())))
    conn.execute(
        "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
        "VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET "
        "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, "
        "feed_ts=excluded.feed_ts WHERE excluded.feed_ts >= run.feed_ts",
        (trip_id, dan, seq, arr, dep, ts))


def iz_feeda(conn: sqlite3.Connection, feed) -> int:
    """Vse lege iz `vehicle_positions` za vožnje, ki jih feed zamud ne nosi.

    Vrne število zapisanih prehodov.
    """
    okna = collector._rail_trip_windows(conn)
    zamenjave = collector._zamenjave(conn)
    n = 0
    for e in feed.entity:
        v = e.vehicle
        tid = v.trip.trip_id
        if tid not in okna and tid in zamenjave:
            tid = zamenjave[tid][0]
        dan = v.trip.start_date
        if (tid not in okna or len(dan) != 8 or not v.timestamp
                or not v.HasField("position") or not brez_feeda(tid)):
            continue
        n += opazuj(conn, tid, f"{dan[:4]}-{dan[4:6]}-{dan[6:]}", v.timestamp,
                    v.position.latitude, v.position.longitude)
    conn.commit()
    pospravi()
    return n


def pospravi(zdaj: float | None = None) -> None:
    """Pozabi sledi voženj brez lege in vožnje, ki jih feed ne nosi več."""
    zdaj = time.time() if zdaj is None else zdaj
    for k in [k for k, s in _sled.items() if zdaj - s[3] > SLED_POZABI_S]:
        del _sled[k]
    with _zaklep:
        for t in [t for t, kdaj in _v_feedu.items() if zdaj - kdaj > SLED_POZABI_S]:
            del _v_feedu[t]
