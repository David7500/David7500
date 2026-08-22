"""SQLite shema in dostop.

SQLite je izbran zato, ker je ena datoteka brez postavljanja strežnika, obenem pa
so vse poizvedbe navaden SQL -- selitev na Postgres je kasneje mehanska.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- ---------- statika (iz GTFS zipa) ----------

CREATE TABLE IF NOT EXISTS station (
    stop_id TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    lat     REAL NOT NULL,
    lon     REAL NOT NULL
);

-- Odsek med dvema postajama. Shranjen neusmerjeno (from_id < to_id).
-- elementary = 0 pomeni "preskok" hitrega vlaka cez vmesne postaje.
CREATE TABLE IF NOT EXISTS edge (
    from_id    TEXT NOT NULL,
    to_id      TEXT NOT NULL,
    km         REAL NOT NULL,
    elementary INTEGER NOT NULL,
    trips      INTEGER NOT NULL,
    geojson    TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id)
);

CREATE TABLE IF NOT EXISTS trip (
    trip_id    TEXT PRIMARY KEY,
    route_id   TEXT NOT NULL,
    train_no   TEXT NOT NULL,   -- npr. "LPV 2206"
    headsign   TEXT,
    service_id TEXT NOT NULL,
    color      TEXT
);
CREATE INDEX IF NOT EXISTS trip_train_no ON trip(train_no);

-- Vozni red. arr_s/dep_s sta sekundi od polnoci in lahko presezeta 86400.
CREATE TABLE IF NOT EXISTS sched (
    trip_id  TEXT NOT NULL,
    stop_seq INTEGER NOT NULL,
    stop_id  TEXT NOT NULL,
    arr_s    INTEGER,
    dep_s    INTEGER,
    PRIMARY KEY (trip_id, stop_seq)
);

CREATE TABLE IF NOT EXISTS service_day (
    service_id TEXT NOT NULL,
    date       TEXT NOT NULL,  -- YYYY-MM-DD
    PRIMARY KEY (service_id, date)
);
CREATE INDEX IF NOT EXISTS service_day_date ON service_day(date);

-- ---------- zajem (iz GTFS-RT) ----------

-- Dnevnik sprememb. Nova vrstica samo, kadar se zamuda dejansko spremeni.
CREATE TABLE IF NOT EXISTS obs (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    delay_arr    INTEGER,
    delay_dep    INTEGER,
    feed_ts      INTEGER NOT NULL,  -- timestamp iz feeda
    observed_at  INTEGER NOT NULL,  -- kdaj smo ga mi videli
    PRIMARY KEY (trip_id, service_date, stop_seq, feed_ts)
);

-- Zadnje znano stanje na postanek; to je tisto, kar steje kot "dejansko".
CREATE TABLE IF NOT EXISTS run (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    delay_arr    INTEGER,
    delay_dep    INTEGER,
    feed_ts      INTEGER NOT NULL,
    PRIMARY KEY (trip_id, service_date, stop_seq)
);
CREATE INDEX IF NOT EXISTS run_date ON run(service_date);

-- ---------- vreme (iz Open-Meteo, dopolnjeno za nazaj) ----------

-- Mreza 0,1 stopinje (~8 km) x ena ura. `cell` je sredisce celice ("46.1,14.5").
-- `source`: 'archive' je reanaliza za nazaj, 'forecast' napoved za danes --
-- naslednji dan jo dnevno opravilo zamenja z arhivsko vrednostjo.
CREATE TABLE IF NOT EXISTS weather (
    cell          TEXT NOT NULL,
    hour_ts       INTEGER NOT NULL,   -- zacetek ure, unix UTC
    temp_c        REAL,
    precip_mm     REAL,
    snowfall_cm   REAL,
    wind_gust_kmh REAL,
    code          INTEGER,            -- WMO sifra vremena
    source        TEXT NOT NULL,
    fetched_at    INTEGER NOT NULL,
    PRIMARY KEY (cell, hour_ts)
);
CREATE INDEX IF NOT EXISTS weather_hour ON weather(hour_ts);

CREATE TABLE IF NOT EXISTS alert (
    alert_id     TEXT NOT NULL,
    first_seen   INTEGER NOT NULL,
    last_seen    INTEGER NOT NULL,
    header       TEXT,
    description  TEXT,
    PRIMARY KEY (alert_id)
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def merge_from(conn: sqlite3.Connection, other: Path) -> dict:
    """Prilije zajem iz druge baze v to.

    Uporabno ob selitvi: zajeto drugje se ne sme izgubiti. Vrstice v `obs` so
    ključene po (trip_id, service_date, stop_seq, feed_ts), zato je združevanje
    varno tudi, če sta bazi nekaj časa tekli vzporedno -- podvojene meritve se
    tiho zavržejo. V `run` obdržimo novejši zapis, torej tistega z višjim
    `feed_ts`.
    """
    other = Path(other)
    if not other.exists():
        raise FileNotFoundError(other)

    before = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("obs", "run")
    }
    conn.execute("ATTACH DATABASE ? AS src", (str(other),))
    try:
        src_obs = conn.execute("SELECT COUNT(*) FROM src.obs").fetchone()[0]
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO obs"
                "(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts, observed_at) "
                "SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts, observed_at "
                "FROM src.obs"
            )
            conn.execute(
                "INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                "SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts FROM src.run "
                "WHERE true "
                "ON CONFLICT(trip_id, service_date, stop_seq) DO UPDATE SET "
                "  delay_arr = excluded.delay_arr, delay_dep = excluded.delay_dep, "
                "  feed_ts   = excluded.feed_ts "
                "WHERE excluded.feed_ts > run.feed_ts"
            )
            # Vreme je izpeljano in bi se dalo znova pobrati, a prilivanje je
            # zastonj. Starejsa baza te tabele nima -- takrat korak preskocimo.
            has_weather = conn.execute(
                "SELECT 1 FROM src.sqlite_master WHERE type='table' AND name='weather'"
            ).fetchone()
            if has_weather:
                conn.execute(
                    "INSERT INTO weather(cell, hour_ts, temp_c, precip_mm, snowfall_cm,"
                    "                    wind_gust_kmh, code, source, fetched_at) "
                    "SELECT cell, hour_ts, temp_c, precip_mm, snowfall_cm,"
                    "       wind_gust_kmh, code, source, fetched_at FROM src.weather "
                    "WHERE true "
                    "ON CONFLICT(cell, hour_ts) DO UPDATE SET "
                    "  temp_c = excluded.temp_c, precip_mm = excluded.precip_mm, "
                    "  snowfall_cm = excluded.snowfall_cm, wind_gust_kmh = excluded.wind_gust_kmh, "
                    "  code = excluded.code, source = excluded.source, "
                    "  fetched_at = excluded.fetched_at "
                    "WHERE excluded.source = 'archive' OR weather.source = excluded.source"
                )
    finally:
        conn.execute("DETACH DATABASE src")

    after = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("obs", "run")
    }
    return {
        "source_observations": src_obs,
        "observations_added": after["obs"] - before["obs"],
        "runs_touched": after["run"] - before["run"],
        "observations_total": after["obs"],
        "days_covered": conn.execute(
            "SELECT COUNT(DISTINCT service_date) FROM run"
        ).fetchone()[0],
    }
