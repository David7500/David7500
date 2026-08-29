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


def _edge_builder(stops):
    """Zbira dolžine in geometrijo odsekov, shape po shape.

    Shapes.txt je zvezno grupiran po shape_id, zato ga beremo pretočno in
    obdržimo v pomnilniku vedno le eno progo -- celotna datoteka je 135 MB in
    je naenkrat ne moremo naložiti na majhnem strežniku.
    """
    lengths: dict[tuple[str, str], list[float]] = defaultdict(list)
    geoms: dict[tuple[str, str], list] = {}

    def feed(points, stop_sequences):
        """points: polilinija ene proge; stop_sequences: postanki vlakov po njej."""
        if len(points) < 2:
            return
        cums = geo.cumulative(points)
        cache: dict[str, tuple[float, float]] = {}
        for stop_seq in stop_sequences:
            projected = []
            for _, stop_id in stop_seq:
                if stop_id not in cache:
                    st = stops[stop_id]
                    cache[stop_id] = geo.project(points, cums, st["lat"], st["lon"])
                along, off = cache[stop_id]
                projected.append((stop_id, along, off))

            for (a, along_a, off_a), (b, along_b, off_b) in zip(projected, projected[1:]):
                dist = abs(along_b - along_a)
                if max(off_a, off_b) > config.MAX_STATION_OFFSET_M or dist < 50:
                    continue
                key = (a, b) if a < b else (b, a)
                lengths[key].append(dist)
                line = geo.slice_between(points, cums, along_a, along_b)
                if len(line) >= 2 and len(line) > len(geoms.get(key, ())):
                    geoms[key] = line

    def finish():
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
            simple = geo.simplify(line, 1e-4)
            elementary = True
            for lat, lon in simple[1:-1]:
                if any(
                    st["stop_id"] not in key
                    and geo.haversine(lat, lon, st["lat"], st["lon"]) < 300
                    for st in nearby(lat, lon)
                ):
                    elementary = False
                    break
            coords = [[round(lon, 6), round(lat, 6)] for lat, lon in simple]
            out.append((
                key[0], key[1], round(statistics.median(lens) / 1000, 3),
                int(elementary), len(lens),
                json.dumps({"type": "LineString", "coordinates": coords}),
            ))
        return out

    return feed, finish


def import_static(conn: sqlite3.Connection, zip_path: Path) -> dict:
    """Uvozi železniški del GTFS zipa (in nadomestne prevoze SŽ).

    Statične tabele se v celoti zamenjajo -- zajem (`obs`, `run`) ostane.
    """
    with zipfile.ZipFile(zip_path) as zf:
        wanted_types = {config.RAIL_ROUTE_TYPE}
        if config.INCLUDE_REPLACEMENT_BUS:
            wanted_types.add(config.BUS_ROUTE_TYPE)
        extra = set(config.EXTRA_AGENCIES)

        def _wanted(r) -> bool:
            if r["agency_id"] == config.RAIL_AGENCY_ID:
                return r["route_type"] in wanted_types
            return r["agency_id"] in extra

        routes = {r["route_id"]: r for r in _rows(zf, "routes.txt") if _wanted(r)}
        trips = {t["trip_id"]: t for t in _rows(zf, "trips.txt") if t["route_id"] in routes}
        # Nadomestni prevozi vozijo po cesti. Njihova geometrija ne sme v
        # `edge`: mreza prog bi dobila odseke, ki niso proge, in dolzine, ki
        # niso zelezniske. Za vozni red in iskanje povezav pa so enakovredni.
        rail_trips = {
            tid for tid, t in trips.items()
            if routes[t["route_id"]]["route_type"] == config.RAIL_ROUTE_TYPE
        }

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

        used_stops = {sid for v in seq_by_trip.values() for _, sid in v}
        stops = {
            s["stop_id"]: {
                "stop_id": s["stop_id"], "name": s["stop_name"],
                "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"]),
            }
            for s in _rows(zf, "stops.txt")
            if s["stop_id"] in used_stops
        }

        by_shape: dict[str, list] = defaultdict(list)
        for trip_id, t in trips.items():
            if t["shape_id"] and trip_id in rail_trips:
                by_shape[t["shape_id"]].append(seq_by_trip[trip_id])

        # Elementarnost odseka se presoja po tem, ali na njem lezi kaksna druga
        # postaja. Avtobusna postajalisca sem ne sodijo -- ce bi, bi odsek
        # Divaca - Koper nehal biti elementaren zaradi Rodika ob cesti.
        rail_stop_ids = {sid for tid in rail_trips for _, sid in seq_by_trip.get(tid, ())}
        feed, finish = _edge_builder({k: v for k, v in stops.items() if k in rail_stop_ids})
        current, points = None, []
        for p in _rows(zf, "shapes.txt"):
            shape_id = p["shape_id"]
            if shape_id != current:
                if current in by_shape:
                    feed([pt for _, pt in sorted(points)], by_shape[current])
                current, points = shape_id, []
            if shape_id in by_shape:
                points.append((int(p["shape_pt_sequence"]),
                               (float(p["shape_pt_lat"]), float(p["shape_pt_lon"]))))
        if current in by_shape:
            feed([pt for _, pt in sorted(points)], by_shape[current])
        edges = finish()

        days = _service_days(zf, {t["service_id"] for t in trips.values()})

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
            "INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id,color,"
            "                 mode,agency,network,block_id) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            [
                (tid, t["route_id"], routes[t["route_id"]]["route_short_name"],
                 t.get("trip_headsign"), t["service_id"], routes[t["route_id"]].get("route_color"),
                 "vlak" if tid in rail_trips else "bus",
                 routes[t["route_id"]].get("agency_id"),
                 # Nadomestni prevoz SZ je avtobus, a pripada zeleznici: na
                 # tisti relaciji zamenjuje vlak. LPP in ostali imajo svojo stran.
                 "zeleznica" if routes[t["route_id"]]["agency_id"] == config.RAIL_AGENCY_ID
                 else "avtobus",
                 # Prazen niz je v GTFS "nimam podatka" -- shranimo NULL, da
                 # se poizvedbe ne lovijo na razliko med '' in NULL.
                 t.get("block_id") or None)
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
        # Voznoredni okvir voznje se da izracunati sele, ko je `sched` poln.
        db.fill_trip_window(conn)
        db.set_meta(conn, "gtfs_imported_at", datetime.now().isoformat(timespec="seconds"))

    return {
        "stations": len(stops), "edges": len(edges),
        "trips": len(trips), "trips_rail": len(rail_trips),
        "trips_bus": len(trips) - len(rail_trips),
        "stop_times": len(sched_rows), "service_days": sum(len(d) for d in days.values()),
        "trips_blocked": sum(1 for t in trips.values() if t.get("block_id")),
    }
