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


# Zamuda, pod katero skok na niclo ni sumljiv. Vlak, ki je bil dve minuti v
# zamudi in je zdaj tocen, je vsakdanji dogodek; vlak, ki je bil dvajset minut
# v zamudi in je cez pol minute tocen, ni.
SUSPECT_DROP_S = 300


def is_zero_blip(prev, last, arr, dep) -> bool:
    """Ali je to prehodna nicla, ki jo feed vrine med dve pravi vrednosti?

    V zajetih podatkih se pri 14 % postankov z vec kot dvema zapisoma pojavi
    vzorec X, 0, X -- ista nenicelna vrednost, med njima ena sama nicla, vse
    v razmiku ene minute. Osemnajst vrstic v `run` je zaradi tega trdilo, da
    je bil vlak tocen, ceprav je zamujal pet minut ali vec.

    Fizikalno je to nemogoce: pri ze prevozenem postanku je zamuda razlika med
    dejanskim in voznorednim casom in se med dvema klicema ne more zmanjsati
    za vec, kot je vmes minilo casa.

    Pravilo je zato ozko: niclo sprejmemo sele, ko jo potrdi drugi zaporedni
    poll. Dnevnik `obs` obdrzi vse, kar je feed rekel -- zavrzemo nicesar,
    samo `run` pocaka en korak.
    """
    if arr not in (0, None) or dep not in (0, None):
        return False
    if arr is None and dep is None:
        return False
    before = None
    if prev is not None:
        before = prev["delay_arr"] if prev["delay_arr"] is not None else prev["delay_dep"]
    if before is None or before < SUSPECT_DROP_S:
        return False
    # Ce je ze prejsnji zapis v dnevniku govoril niclo, je to potrditev in ne blip.
    if last is not None:
        prior = last["delay_arr"] if last["delay_arr"] is not None else last["delay_dep"]
        if prior == 0:
            return False
    return True


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
    blips = 0
    # GTFS-RT zna povedati, da je voznja odpovedana (`schedule_relationship`),
    # a SZ tega polja ne uporablja -- odpovedi sporocajo z besedilom obvestila
    # (`effect = 6`, "vlak vozi samo do ..."). Vseeno stejemo: ce se to kdaj
    # spremeni, hocemo izvedeti takoj in ne cez pol leta.
    non_scheduled = 0

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

        if tu.trip.schedule_relationship != 0:
            non_scheduled += 1

        ts = tu.timestamp or feed_ts
        for stu in tu.stop_time_update:
            if stu.schedule_relationship != 0:
                non_scheduled += 1
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

            # Zadnji zapis v dnevniku rabimo, preden vanj pisemo: na njem
            # sloni preverjanje sumljivega skoka na niclo (glej spodaj).
            last = conn.execute(
                "SELECT delay_arr, delay_dep FROM obs "
                "WHERE trip_id=? AND service_date=? AND stop_seq=? "
                "ORDER BY feed_ts DESC LIMIT 1",
                (trip_id, service_date, seq),
            ).fetchone()

            conn.execute(
                "INSERT OR IGNORE INTO obs"
                "(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts,observed_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (trip_id, service_date, seq, arr, dep, ts, observed_at),
            )
            changed += 1

            if is_zero_blip(prev, last, arr, dep):
                # Dnevnik obdrzi vse, `run` pa ne prevzame vrednosti, dokler je
                # ne potrdi naslednji poll. Zamuda se v pol minute ne more
                # zmanjsati za dvajset minut.
                blips += 1
                continue

            conn.execute(
                "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                "VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET "
                "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, "
                "feed_ts=excluded.feed_ts WHERE excluded.feed_ts >= run.feed_ts",
                (trip_id, service_date, seq, arr, dep, ts),
            )

    conn.commit()
    return {"trips": trips_seen, "changed": changed, "skipped": skipped,
            "blips": blips, "non_scheduled": non_scheduled, "feed_ts": feed_ts}


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


def rebuild_run(conn: sqlite3.Connection) -> dict:
    """Znova zgradi `run` iz dnevnika `obs` po istem pravilu kot zajem.

    Rabi se enkrat, po uvedbi preverjanja prehodnih nicel: vrstice, ki so
    nastale prej, so lahko obtičale na nicli, ki jo je feed vrnil za en klic.
    Idempotentno -- ponovni zagon ne spremeni nič, ker je pravilo isto.

    Dnevnik je merodajen in ostane nedotaknjen; popravlja se samo povzetek.
    """
    rows = conn.execute(
        "SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts "
        "FROM obs ORDER BY trip_id, service_date, stop_seq, feed_ts"
    ).fetchall()

    accepted: dict[tuple, tuple] = {}
    fixed = 0
    key = None
    prev = last = None
    for r in rows:
        k = (r["trip_id"], r["service_date"], r["stop_seq"])
        if k != key:
            key, prev, last = k, None, None
        if not is_zero_blip(prev, last, r["delay_arr"], r["delay_dep"]):
            accepted[k] = (r["delay_arr"], r["delay_dep"], r["feed_ts"])
            prev = {"delay_arr": r["delay_arr"], "delay_dep": r["delay_dep"]}
        else:
            fixed += 1
        last = {"delay_arr": r["delay_arr"], "delay_dep": r["delay_dep"]}

    changed = 0
    with conn:
        for (trip_id, day, seq), (arr, dep, ts) in accepted.items():
            cur = conn.execute(
                "SELECT delay_arr, delay_dep FROM run "
                "WHERE trip_id=? AND service_date=? AND stop_seq=?",
                (trip_id, day, seq),
            ).fetchone()
            if cur and cur["delay_arr"] == arr and cur["delay_dep"] == dep:
                continue
            conn.execute(
                "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                "VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET "
                "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, "
                "feed_ts=excluded.feed_ts",
                (trip_id, day, seq, arr, dep, ts),
            )
            changed += 1
    return {"stops": len(accepted), "blips_skipped": fixed, "run_rows_corrected": changed}


# ---------------------------------------------------------------- lega vozil

# Koliko sekund je lega še "zdaj". Feed osvežuje na ~30 s; nad tem je vozilo
# ali končalo vožnjo ali izgubilo signal in prikaz ga ne sme risati kot živega.
POSITION_FRESH_S = 180


def ingest_positions(conn: sqlite3.Connection, feed) -> dict:
    """Zapiše trenutno lego vozil.

    Feed `vehicle_positions` nosi **samo avtobuse** -- vlakov v njem ni. Za
    avtobus je to torej edina prava lega v celem projektu: vse drugo, kar
    aplikacija riše, je zadnja postaja z meritvijo, ne dejanski položaj.

    Zgodovine ne vodimo. 130 vozil na 30 s je ~300 000 točk na dan, prikaz
    "kje je zdaj" pa rabi eno vrstico na vožnjo -- zato upsert.
    """
    known = {r["trip_id"] for r in conn.execute("SELECT trip_id FROM trip")}
    seen_at = int(time.time())
    written = 0

    for entity in feed.entity:
        v = entity.vehicle
        trip_id = v.trip.trip_id
        if trip_id not in known or not v.HasField("position"):
            continue
        day = v.trip.start_date or ""
        if len(day) == 8:
            day = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        conn.execute(
            "INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, bearing,"
            "                        speed_ms, stop_seq, status, vehicle_id, plate) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id) DO UPDATE SET "
            "  service_date=excluded.service_date, seen_ts=excluded.seen_ts,"
            "  lat=excluded.lat, lon=excluded.lon, bearing=excluded.bearing,"
            "  speed_ms=excluded.speed_ms, stop_seq=excluded.stop_seq,"
            "  status=excluded.status, vehicle_id=excluded.vehicle_id, plate=excluded.plate "
            "WHERE excluded.seen_ts >= vehicle_now.seen_ts",
            (trip_id, day or None, v.timestamp or seen_at,
             v.position.latitude, v.position.longitude,
             v.position.bearing if v.position.HasField("bearing") else None,
             v.position.speed if v.position.HasField("speed") else None,
             v.current_stop_sequence or None, v.current_status,
             v.vehicle.id or None, v.vehicle.license_plate or None),
        )
        written += 1

    # Stare lege pobrisi -- tabela naj ostane "zdaj", ne smetisce.
    conn.execute("DELETE FROM vehicle_now WHERE seen_ts < ?", (seen_at - 3600,))
    conn.commit()
    return {"vehicles": written}


def poll_positions(conn: sqlite3.Connection) -> dict:
    feed = fetch(config.VEHICLE_POSITIONS_URL, conn, "positions_etag")
    if feed is None:
        return {"vehicles": 0, "unchanged": True}
    return ingest_positions(conn, feed)
