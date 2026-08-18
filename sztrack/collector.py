"""Zajem zamud iz GTFS-RT.

Feed nosi samo `delay` (brez absolutnega časa) in je drseče okno -- v enem klicu
dobiš le postanke okoli trenutnega položaja vlaka. Celotno vožnjo zato sestavimo
iz zaporednih pollov; zato pišemo ob vsaki spremembi in vzdržujemo tabelo `run`
z zadnjim znanim stanjem.
"""
from __future__ import annotations

import sqlite3
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from google.transit import gtfs_realtime_pb2

from . import config, db

TZ = ZoneInfo(config.TIMEZONE)


def fetch(url: str, conn: sqlite3.Connection, etag_key: str):
    """Pogojni GET. Vrne None, kadar se feed ni spremenil."""
    headers = {"User-Agent": config.USER_AGENT}
    etag = db.get_meta(conn, etag_key)
    if etag:
        headers["If-None-Match"] = etag
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 304:
        return None
    resp.raise_for_status()
    if resp.headers.get("ETag"):
        db.set_meta(conn, etag_key, resp.headers["ETag"])
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def _rail_trip_windows(conn: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    """trip_id -> (prvi odhod, zadnji prihod) v sekundah od polnoči."""
    rows = conn.execute(
        "SELECT trip_id, MIN(COALESCE(dep_s, arr_s)) AS a, MAX(COALESCE(arr_s, dep_s)) AS b "
        "FROM sched GROUP BY trip_id"
    )
    return {r["trip_id"]: (r["a"], r["b"]) for r in rows}


def _service_dates(conn: sqlite3.Connection) -> dict[str, set[str]]:
    rows = conn.execute(
        "SELECT t.trip_id, sd.date FROM trip t JOIN service_day sd USING (service_id)"
    )
    out: dict[str, set[str]] = {}
    for r in rows:
        out.setdefault(r["trip_id"], set()).add(r["date"])
    return out


def resolve_service_date(trip_id, window, valid_dates, now: datetime) -> str | None:
    """Ugotovi, kateremu obratovalnemu dnevu pripada ta vožnja.

    SŽ zapisi nimajo `start_date`, vožnje pa gredo lahko čez polnoč, zato datum
    izberemo tako, da se voznoredno okno vožnje ujema s trenutnim časom.
    """
    if not window or not valid_dates:
        return None
    start_s, end_s = window
    best, best_gap = None, None
    for offset in (-1, 0, 1):
        d = (now.date() + timedelta(days=offset)).isoformat()
        if d not in valid_dates:
            continue
        midnight = datetime.combine(date.fromisoformat(d), datetime.min.time(), tzinfo=TZ)
        start = midnight + timedelta(seconds=start_s)
        end = midnight + timedelta(seconds=end_s)
        if not (start - timedelta(minutes=45) <= now <= end + timedelta(hours=3)):
            continue
        gap = 0 if start <= now <= end else min(abs((now - start).total_seconds()),
                                                abs((now - end).total_seconds()))
        if best_gap is None or gap < best_gap:
            best, best_gap = d, gap
    return best


def ingest(conn: sqlite3.Connection, feed) -> dict:
    """Zapiše spremembe zamud. Vrne števce za log."""
    now = datetime.now(TZ)
    windows = _rail_trip_windows(conn)
    valid = _service_dates(conn)
    feed_ts = feed.header.timestamp or int(time.time())
    observed_at = int(time.time())

    changed = 0
    trips_seen = 0
    skipped = 0

    for entity in feed.entity:
        tu = entity.trip_update
        trip_id = tu.trip.trip_id
        if trip_id not in windows:      # ni železnica -- avtobuse ignoriramo
            continue
        trips_seen += 1

        service_date = tu.trip.start_date or None
        if service_date and len(service_date) == 8:
            service_date = f"{service_date[:4]}-{service_date[4:6]}-{service_date[6:]}"
        else:
            service_date = resolve_service_date(trip_id, windows.get(trip_id), valid.get(trip_id), now)
        if not service_date:
            skipped += 1
            continue

        ts = tu.timestamp or feed_ts
        for stu in tu.stop_time_update:
            arr = stu.arrival.delay if stu.HasField("arrival") else None
            dep = stu.departure.delay if stu.HasField("departure") else None
            seq = stu.stop_sequence

            prev = conn.execute(
                "SELECT delay_arr, delay_dep FROM run "
                "WHERE trip_id=? AND service_date=? AND stop_seq=?",
                (trip_id, service_date, seq),
            ).fetchone()
            if prev and prev["delay_arr"] == arr and prev["delay_dep"] == dep:
                continue    # nespremenjeno -- ne pisi

            conn.execute(
                "INSERT OR IGNORE INTO obs"
                "(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts,observed_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (trip_id, service_date, seq, arr, dep, ts, observed_at),
            )
            conn.execute(
                "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                "VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET "
                "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, "
                "feed_ts=excluded.feed_ts WHERE excluded.feed_ts >= run.feed_ts",
                (trip_id, service_date, seq, arr, dep, ts),
            )
            changed += 1

    conn.commit()
    return {"trips": trips_seen, "changed": changed, "skipped": skipped, "feed_ts": feed_ts}


def poll_once(conn: sqlite3.Connection) -> dict:
    feed = fetch(config.TRIP_UPDATES_URL, conn, "rt_etag")
    if feed is None:
        return {"trips": 0, "changed": 0, "skipped": 0, "unchanged": True}
    return ingest(conn, feed)


def run_forever(conn: sqlite3.Connection, interval: int | None = None) -> None:
    interval = interval or config.POLL_SECONDS
    while True:
        started = time.monotonic()
        try:
            info = poll_once(conn)
            stamp = datetime.now(TZ).strftime("%H:%M:%S")
            if not info.get("unchanged"):
                print(f"{stamp}  vlakov={info['trips']:3d}  sprememb={info['changed']:3d}"
                      f"  brez datuma={info['skipped']}", flush=True)
        except Exception as exc:               # feed občasno resetira povezavo
            print(f"{datetime.now(TZ):%H:%M:%S}  napaka: {exc}", flush=True)
        time.sleep(max(1.0, interval - (time.monotonic() - started)))
