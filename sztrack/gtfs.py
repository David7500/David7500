"""Prenos in uvoz statičnega GTFS voznega reda (samo železnica)."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
import statistics
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

from . import config, db, geo


def _rows(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as fh:
        yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))


def download(conn: sqlite3.Connection, force: bool = False) -> Path | None:
    """Prenese zip samo, če se je spremenil. Vrne pot ali None (ni sprememb).

    Zip je ~41 MB in se regenerira približno enkrat dnevno -- pogojni GET s
    shranjenim ETagom pomeni, da običajno prenesemo nič.
    """
    target = config.DATA_DIR / "ijpp_gtfs.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": config.USER_AGENT}
    if not force and target.exists():
        etag = db.get_meta(conn, "gtfs_etag")
        modified = db.get_meta(conn, "gtfs_last_modified")
        if etag:
            headers["If-None-Match"] = etag
        if modified:
            headers["If-Modified-Since"] = modified

    resp = requests.get(config.GTFS_URL, headers=headers, timeout=300, stream=True)
    if resp.status_code == 304:
        return None
    resp.raise_for_status()

    tmp = target.with_suffix(".tmp")
    with open(tmp, "wb") as fh:
        for chunk in resp.iter_content(1 << 20):
            fh.write(chunk)
    tmp.replace(target)

    if resp.headers.get("ETag"):
        db.set_meta(conn, "gtfs_etag", resp.headers["ETag"])
    if resp.headers.get("Last-Modified"):
        db.set_meta(conn, "gtfs_last_modified", resp.headers["Last-Modified"])
    conn.commit()
    return target


def _service_days(zf: zipfile.ZipFile, service_ids: set[str]):
    """Razširi calendar.txt + calendar_dates.txt v konkretne datume."""
    days: dict[str, set[str]] = defaultdict(set)
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    names = set(zf.namelist())

    if "calendar.txt" in names:
        for r in _rows(zf, "calendar.txt"):
            sid = r["service_id"]
            if sid not in service_ids:
                continue
            start = datetime.strptime(r["start_date"], "%Y%m%d").date()
            end = datetime.strptime(r["end_date"], "%Y%m%d").date()
            active = {i for i, w in enumerate(weekdays) if r.get(w) == "1"}
            if not active:
                continue
            d = start
            while d <= end:
                if d.weekday() in active:
                    days[sid].add(d.isoformat())
                d += timedelta(days=1)

    if "calendar_dates.txt" in names:
        for r in _rows(zf, "calendar_dates.txt"):
            sid = r["service_id"]
            if sid not in service_ids:
                continue
            d = datetime.strptime(r["date"], "%Y%m%d").date().isoformat()
            if r["exception_type"] == "1":
                days[sid].add(d)
            else:
                days[sid].discard(d)
    return days


def _to_seconds(hhmmss: str) -> int | None:
    """GTFS dopušča ure >= 24 za vožnje čez polnoč."""
    if not hhmmss:
        return None
    h, m, s = (int(x) for x in hhmmss.split(":"))
    return h * 3600 + m * 60 + s


def _build_edges(stops, seq_by_trip, trips, shapes):
    """Razdalje in geometrija med zaporednimi postanki.

    Postaje projiciramo na polilinijo proge; razlika kumulativnih razdalj je
    dolžina odseka. Čez vse vlake, ki vozijo isti odsek, vzamemo mediano.
    """
    lengths: dict[tuple[str, str], list[float]] = defaultdict(list)
    geoms: dict[tuple[str, str], list] = {}
    cache: dict[str, tuple[list, list]] = {}

    for trip_id, stop_seq in seq_by_trip.items():
        shape_id = trips[trip_id]["shape_id"]
        pts = shapes.get(shape_id)
        if not pts:
            continue
        if shape_id not in cache:
            cache[shape_id] = (pts, geo.cumulative(pts))
        pts, cums = cache[shape_id]

        projected = []
        for _, stop_id in stop_seq:
            st = stops[stop_id]
            along, off = geo.project(pts, cums, st["lat"], st["lon"])
            projected.append((stop_id, along, off))

        for (a, along_a, off_a), (b, along_b, off_b) in zip(projected, projected[1:]):
            dist = abs(along_b - along_a)
            if max(off_a, off_b) > config.MAX_STATION_OFFSET_M or dist < 50:
                continue
            key = (a, b) if a < b else (b, a)
            lengths[key].append(dist)
            line = geo.slice_between(pts, cums, along_a, along_b)
            if len(line) >= 2 and len(line) > len(geoms.get(key, ())):
                geoms[key] = line

    # Odsek je "elementaren", če na njem ne leži nobena druga postaja.
    grid: dict[tuple[float, float], list] = defaultdict(list)
    for st in stops.values():
        grid[(round(st["lat"], 1), round(st["lon"], 1))].append(st)

    def nearby(lat, lon):
        for dla in (-0.1, 0.0, 0.1):
            for dlo in (-0.1, 0.0, 0.1):
                yield from grid.get((round(lat + dla, 1), round(lon + dlo, 1)), ())

    out = []
    for key, lens in lengths.items():
        line = geoms.get(key)
        if not line:
            continue
        a, b = key
        elementary = True
        for lat, lon in geo.simplify(line, 1e-4)[1:-1]:
            if any(
                st["stop_id"] not in key and geo.haversine(lat, lon, st["lat"], st["lon"]) < 300
                for st in nearby(lat, lon)
            ):
                elementary = False
                break
        coords = [[round(lon, 6), round(lat, 6)] for lat, lon in geo.simplify(line, 1e-4)]
        out.append(
            (a, b, round(statistics.median(lens) / 1000, 3), int(elementary), len(lens),
             json.dumps({"type": "LineString", "coordinates": coords}))
        )
    return out


def import_static(conn: sqlite3.Connection, zip_path: Path) -> dict:
    """Uvozi železniški del GTFS zipa. Statične tabele se v celoti zamenjajo."""
    with zipfile.ZipFile(zip_path) as zf:
        routes = {
            r["route_id"]: r
            for r in _rows(zf, "routes.txt")
            if r["agency_id"] == config.RAIL_AGENCY_ID
            and r["route_type"] == config.RAIL_ROUTE_TYPE
        }
        trips = {t["trip_id"]: t for t in _rows(zf, "trips.txt") if t["route_id"] in routes}

        seq_by_trip: dict[str, list[tuple[int, str]]] = defaultdict(list)
        sched_rows = []
        for st in _rows(zf, "stop_times.txt"):
            if st["trip_id"] not in trips:
                continue
            n = int(st["stop_sequence"])
            seq_by_trip[st["trip_id"]].append((n, st["stop_id"]))
            sched_rows.append(
                (st["trip_id"], n, st["stop_id"],
                 _to_seconds(st["arrival_time"]), _to_seconds(st["departure_time"]))
            )
        for v in seq_by_trip.values():
            v.sort()

        rail_stops = {sid for v in seq_by_trip.values() for _, sid in v}
        stops = {
            s["stop_id"]: {
                "stop_id": s["stop_id"], "name": s["stop_name"],
                "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"]),
            }
            for s in _rows(zf, "stops.txt")
            if s["stop_id"] in rail_stops
        }

        wanted_shapes = {t["shape_id"] for t in trips.values() if t["shape_id"]}
        raw: dict[str, list] = defaultdict(list)
        for p in _rows(zf, "shapes.txt"):
            if p["shape_id"] in wanted_shapes:
                raw[p["shape_id"]].append(
                    (int(p["shape_pt_sequence"]), float(p["shape_pt_lat"]), float(p["shape_pt_lon"]))
                )
        shapes = {k: [(lat, lon) for _, lat, lon in sorted(v)] for k, v in raw.items()}

        days = _service_days(zf, {t["service_id"] for t in trips.values()})

    edges = _build_edges(stops, seq_by_trip, trips, shapes)

    with conn:
        for table in ("station", "edge", "trip", "sched", "service_day"):
            conn.execute(f"DELETE FROM {table}")
        conn.executemany(
            "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
            [(s["stop_id"], s["name"], s["lat"], s["lon"]) for s in stops.values()],
        )
        conn.executemany(
            "INSERT INTO edge(from_id,to_id,km,elementary,trips,geojson) VALUES(?,?,?,?,?,?)", edges
        )
        conn.executemany(
            "INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id,color) "
            "VALUES(?,?,?,?,?,?)",
            [
                (tid, t["route_id"], routes[t["route_id"]]["route_short_name"],
                 t.get("trip_headsign"), t["service_id"], routes[t["route_id"]].get("route_color"))
                for tid, t in trips.items()
            ],
        )
        conn.executemany(
            "INSERT INTO sched(trip_id,stop_seq,stop_id,arr_s,dep_s) VALUES(?,?,?,?,?)", sched_rows
        )
        conn.executemany(
            "INSERT INTO service_day(service_id,date) VALUES(?,?)",
            [(sid, d) for sid, ds in days.items() for d in ds],
        )
        db.set_meta(conn, "gtfs_imported_at", datetime.now().isoformat(timespec="seconds"))

    return {
        "stations": len(stops), "edges": len(edges), "trips": len(trips),
        "stop_times": len(sched_rows), "service_days": sum(len(d) for d in days.values()),
    }
