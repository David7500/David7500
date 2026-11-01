"""Mestni Kranj (MOK) v živo: lege Ridanga prek derp.si, zamuda iz leg.

Vozni red je uradni (Mestna občina Kranj prek Ridanga, `gtfs.mestni_viri`).
Lege objavlja Ridangov GTFS-RT, ki ga javno posreduje le derp.si
(`sources/kranj`). Id-ji voženj v njem so Ridangovi (`0D3o9RWfWG_154963`)
in jih ima samo uradni zip -- isti sistem, ne sklepanje: 27. 10. 2026 v dveh
branjih 3 od 3 vozil na vožnjah uradnega zipa, po voznem redu sta tedaj
vozili še vožnji Kranvaja, ki lege nima.

Zamude ne vzamemo iz feeda, izmerimo jo iz leg (`iz_lege.opazuj`, prehod
brez trase) -- kot pri Marpromu in NAP, da je ista za vsa mesta.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Callable

import requests
from google.transit import gtfs_realtime_pb2

from . import collector, config, db, dosje, gtfs, iz_lege, stats, straza, viri

TZ = collector.TZ
KR = gtfs.KR
TIMEOUT_S = (5, 15)


def razberi(vsebina: bytes) -> tuple[list[dict], int]:
    """GTFS-RT `vehicle_positions` -> vozila, čas glave."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(vsebina)
    glava = feed.header.timestamp or 0
    out = []
    for e in feed.entity:
        if not e.HasField("vehicle") or not e.vehicle.HasField("position"):
            continue
        v = e.vehicle
        out.append({
            "vozilo": v.vehicle.id or e.id, "trip": v.trip.trip_id or None,
            "dan": v.trip.start_date or None, "ts": v.timestamp or glava,
            "lat": v.position.latitude, "lon": v.position.longitude,
            "smer": v.position.bearing if v.position.HasField("bearing") else None,
            "hitrost": v.position.speed if v.position.HasField("speed") else None,
            "vp": v,
        })
    return out, glava


def _dan(trip_id: str, start_date: str | None, okno, dnevi, zdaj: float) -> str | None:
    if start_date and len(start_date) == 8:
        return f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    return collector.resolve_service_date(trip_id, okno, dnevi.get(trip_id),
                                          datetime.fromtimestamp(zdaj, TZ))


def korak(conn: sqlite3.Connection, vozila: list[dict], zdaj: float) -> dict:
    """Pripni vozila na vožnje uradnega zipa, lega v `vehicle_now`, zamuda iz leg."""
    okna = collector._rail_trip_windows(conn)
    dnevi = collector._service_dates(conn, datetime.fromtimestamp(zdaj, TZ))
    st = {"vozil": len(vozila), "pripetih": 0, "brez_voznje": 0, "starih": 0, "prehodov": 0}
    for v in vozila:
        vozilo_id = f"kranj-{v['vozilo']}"
        if zdaj - v["ts"] > collector.POSITION_FRESH_S:
            st["starih"] += 1
            dosje.opazi_gtfs("kranj", v["vp"], None, None, (), vozilo_id, zdaj)
            continue
        tid = KR + v["trip"] if v["trip"] else None
        if tid not in okna:
            st["brez_voznje"] += 1
            straza.vzorec("kranj", vozilo_id, None, zdaj)
            dosje.opazi_gtfs("kranj", v["vp"], None, None, ("brez_voznje",), vozilo_id, zdaj)
            continue
        dan = _dan(tid, v["dan"], okna[tid], dnevi, zdaj)
        if dan is None:
            st["brez_voznje"] += 1
            straza.vzorec("kranj", vozilo_id, None, zdaj)
            dosje.opazi_gtfs("kranj", v["vp"], None, None, ("brez_dneva",), vozilo_id, zdaj)
            continue
        st["pripetih"] += 1
        straza.vzorec("kranj", vozilo_id, tid, zdaj)
        dosje.opazi_gtfs("kranj", v["vp"], tid, dan, (), vozilo_id, zdaj)
        conn.execute(
            "INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, bearing,"
            "                        speed_ms, vehicle_id) VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id) DO UPDATE SET "
            "  service_date=excluded.service_date, seen_ts=excluded.seen_ts,"
            "  lat=excluded.lat, lon=excluded.lon, bearing=excluded.bearing,"
            "  speed_ms=excluded.speed_ms, stop_seq=NULL, status=NULL,"
            "  vehicle_id=excluded.vehicle_id "
            "WHERE excluded.seen_ts >= vehicle_now.seen_ts",
            (tid, dan, int(v["ts"]), v["lat"], v["lon"], v["smer"], v["hitrost"], vozilo_id))
        if config.ZAMUDA_IZ_LEGE and iz_lege.brez_feeda(tid, zdaj):
            st["prehodov"] += iz_lege.opazuj(conn, tid, dan, int(v["ts"]), v["lat"],
                                             v["lon"], vozilo_id)
    return st


_po_voznem_redu: list = [0.0, 0]


def po_voznem_redu(conn: sqlite3.Connection, zdaj: float) -> int:
    """Koliko voženj Kranja bi po voznem redu ta hip vozilo (na minuto)."""
    if zdaj - _po_voznem_redu[0] < 60:
        return _po_voznem_redu[1]
    n = 0
    danes = datetime.fromtimestamp(zdaj, TZ).date()
    for o in (-1, 0):
        dan = (danes + timedelta(days=o)).isoformat()
        t = zdaj - stats.polnoc(dan)
        n += conn.execute(
            "SELECT COUNT(*) FROM trip t JOIN service_day sd "
            "ON sd.service_id = t.service_id AND sd.date = ? "
            "WHERE t.agency = ? AND t.start_s <= ? AND t.end_s >= ?",
            (dan, gtfs.KRANJ_AGENCIJA, t, t)).fetchone()[0]
    _po_voznem_redu[:] = [zdaj, n]
    return n


def beri(seja: requests.Session) -> bytes:
    with viri.branje("kranj") as b:
        r = seja.get(config.KRANJ_RT_URL, timeout=TIMEOUT_S)
        b.http = r.status_code
        r.raise_for_status()
        b.bajtov = len(r.content)
    return r.content


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: tuj strežnik ne sme zamikati zajema."""
    conn = db.connect()
    seja = requests.Session()
    seja.headers["User-Agent"] = config.USER_AGENT
    napak = 0
    try:
        while not stop.is_set():
            zacetek = time.time()
            try:
                vozila, _ = razberi(beri(seja))
                zdaj = time.time()
                st = korak(conn, vozila, zdaj)
                st.update(ts=int(zdaj), po_voznem_redu=po_voznem_redu(conn, zdaj))
                db.set_meta(conn, "kranj", json.dumps(st, sort_keys=True))
                # Ključ predpomnilnika `/api/vehicles` (glej `nap.korak`).
                db.set_meta(conn, "positions_fetched", str(int(zdaj)))
                conn.commit()
                if napak:
                    log(f"Kranj spet odgovarja (po {napak} napakah)")
                napak = 0
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"Kranj: {exc}")
                try:
                    s = json.loads(db.get_meta(conn, "kranj") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(time.time()))
                    db.set_meta(conn, "kranj", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            stop.wait(max(1.0, config.KRANJ_SECONDS - (time.time() - zacetek)))
    finally:
        conn.close()
