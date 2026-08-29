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

-- `mode`: 'vlak' ali 'bus'. Nadomestni prevozi SZ so v istem feedu pod
-- route_type = 3 in sodijo v isti iskalnik -- potnik na relaciji Ljubljana -
-- Logatec do 12. decembra ne bo sel na vlak, ker ta ne vozi. Locimo ju
-- s stolpcem, ne z locenimi tabelami: GTFS ju modelira enako.
CREATE TABLE IF NOT EXISTS trip (
    trip_id    TEXT PRIMARY KEY,
    route_id   TEXT NOT NULL,
    train_no   TEXT NOT NULL,   -- npr. "LPV 2206" ali "BUS 44201"
    headsign   TEXT,
    service_id TEXT NOT NULL,
    color      TEXT,
    mode       TEXT NOT NULL DEFAULT 'vlak',
    agency     TEXT
);
CREATE INDEX IF NOT EXISTS trip_train_no ON trip(train_no);
CREATE INDEX IF NOT EXISTS trip_mode ON trip(mode);

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

-- ---------- obvestila (iz GTFS-RT service_alerts) ----------

-- Dvoje v enem viru: `ovira` so dela in nadomestni prevozi (edini vir odgovora
-- ZAKAJ vlak zamuja), `delay` pa ziva zamuda z imenom prometnega mesta.
-- Isto obvestilo pride v paru sl + en pod razlicnima id-jema; `lang` ju loci.
-- ---------- lega vozil (iz GTFS-RT vehicle_positions) ----------

-- Samo TRENUTNA lega, ena vrstica na vožnjo, brez zgodovine. Sled bi pri 130
-- vozilih na 30 s pomenila ~300 000 točk na dan; za prikaz "kje je zdaj" pa
-- zadošča zadnja. Zgodovino zamud imamo v `obs`, ta tabela je drugo vprašanje.
--
-- Vlakov tu ni: feed nosi samo avtobuse. Zato je to edini vir prave lege v
-- projektu -- vse drugo je zadnja postaja z meritvijo.
CREATE TABLE IF NOT EXISTS vehicle_now (
    trip_id      TEXT PRIMARY KEY,
    service_date TEXT,
    seen_ts      INTEGER NOT NULL,
    lat          REAL NOT NULL,
    lon          REAL NOT NULL,
    bearing      REAL,
    speed_ms     REAL,
    stop_seq     INTEGER,
    status       INTEGER,     -- GTFS-RT VehicleStopStatus
    vehicle_id   TEXT,
    plate        TEXT
);
CREATE INDEX IF NOT EXISTS vehicle_now_seen ON vehicle_now(seen_ts);

CREATE TABLE IF NOT EXISTS alert (
    alert_id     TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,      -- ovira | delay | drugo
    cause        INTEGER,
    effect       INTEGER,
    start_ts     INTEGER,
    end_ts       INTEGER,
    header       TEXT,
    description  TEXT,
    url          TEXT,
    lang         TEXT,
    first_seen   INTEGER NOT NULL,
    last_seen    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS alert_kind ON alert(kind, lang);

CREATE TABLE IF NOT EXISTS alert_entity (
    alert_id TEXT NOT NULL,
    route_id TEXT NOT NULL DEFAULT '',
    trip_id  TEXT NOT NULL DEFAULT '',
    stop_id  TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (alert_id, route_id, trip_id, stop_id)
);
CREATE INDEX IF NOT EXISTS alert_entity_route ON alert_entity(route_id);

-- Zaporedje porocil o eni voznji: kje je bil vlak in koliko je zamujal.
-- Prometno mesto pogosto ni voznoredni postanek, zato ga `run` ne pozna.
-- Pisemo samo ob spremembi (zamuda ali mesto), sicer bi bilo to vsakih 30 s.
CREATE TABLE IF NOT EXISTS delay_report (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    seen_ts      INTEGER NOT NULL,
    train_no     TEXT NOT NULL,
    delay_min    INTEGER NOT NULL,
    station      TEXT NOT NULL,
    event        TEXT,               -- prihod | odhod
    severe       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (trip_id, service_date, seen_ts)
);
CREATE INDEX IF NOT EXISTS delay_report_train ON delay_report(train_no, service_date);
CREATE INDEX IF NOT EXISTS delay_report_date ON delay_report(service_date);
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


def _migrate(conn: sqlite3.Connection) -> None:
    """Popravi sheme, ki so nastale pred to razlicico.

    Tabela `alert` je prvotno hranila samo besedilo brez vzroka, ucinka in
    prizadetih poti. Nikoli ni bila napolnjena -- zajema obvestil takrat ni
    bilo -- zato je vrzenje stran varno in cenejse od dodajanja stolpcev.
    """
    # `trip` je dobil `mode` in `agency`, ko so se pridruzili nadomestni
    # prevozi. Stolpca dodamo -- vsebina tabele je izpeljana iz GTFS zipa in
    # se ob naslednjem uvozu tako ali tako zamenja, dotlej pa je vse `vlak`.
    have = {r[1] for r in conn.execute("PRAGMA table_info(trip)")}
    if have and "mode" not in have:
        conn.execute("ALTER TABLE trip ADD COLUMN mode TEXT NOT NULL DEFAULT 'vlak'")
        conn.execute("ALTER TABLE trip ADD COLUMN agency TEXT")
        conn.commit()

    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='alert'"
    ).fetchone()
    if row and "kind" not in (row[0] or ""):
        n = conn.execute("SELECT COUNT(*) FROM alert").fetchone()[0]
        if n:                       # ce bi kdaj vendarle kaj bilo, ne brisi tiho
            conn.execute("ALTER TABLE alert RENAME TO alert_stara")
        else:
            conn.execute("DROP TABLE alert")
        conn.commit()


def init(conn: sqlite3.Connection) -> None:
    _migrate(conn)
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


def _has(conn: sqlite3.Connection, table: str, *columns: str) -> bool:
    """Ali priklopljena baza (`src`) pozna to tabelo -- in te stolpce?

    Stolpci niso pretiravanje: baza na malini je imela tabelo `alert` po stari
    shemi, brez `kind` in `cause`. Preverjanje samo imena bi prilivanje pognalo
    v `no such column` sredi transakcije, torej ob najslabšem trenutku --
    med selitvijo zajema, ki ga ne smemo izgubiti.
    """
    if conn.execute(
        "SELECT 1 FROM src.sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is None:
        return False
    if not columns:
        return True
    have = {r[1] for r in conn.execute(f"PRAGMA src.table_info({table})")}
    return set(columns) <= have


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
            if _has(conn, "weather", "source"):
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
            # Obvestila in porocila o zamudi: starejsa baza teh tabel nima.
            if _has(conn, "alert", "kind", "cause", "effect", "lang"):
                conn.execute(
                    "INSERT INTO alert(alert_id, kind, cause, effect, start_ts, end_ts,"
                    "                  header, description, url, lang, first_seen, last_seen) "
                    "SELECT alert_id, kind, cause, effect, start_ts, end_ts,"
                    "       header, description, url, lang, first_seen, last_seen "
                    "FROM src.alert WHERE true "
                    "ON CONFLICT(alert_id) DO UPDATE SET "
                    "  first_seen = MIN(alert.first_seen, excluded.first_seen), "
                    "  last_seen  = MAX(alert.last_seen,  excluded.last_seen)"
                )
            if _has(conn, "alert_entity", "route_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO alert_entity(alert_id, route_id, trip_id, stop_id) "
                    "SELECT alert_id, route_id, trip_id, stop_id FROM src.alert_entity"
                )
            if _has(conn, "delay_report", "train_no", "station"):
                conn.execute(
                    "INSERT OR IGNORE INTO delay_report"
                    "(trip_id, service_date, seen_ts, train_no, delay_min, station, event, severe) "
                    "SELECT trip_id, service_date, seen_ts, train_no, delay_min, station,"
                    "       event, severe FROM src.delay_report"
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


# Tabele, ki jih prinese GTFS zip. Vse ostalo je zajem in v priloženo bazo
# ne sodi -- namestitev dobi vozni red, zgodovino pa si posname sama.
STATIC_TABLES = ("station", "edge", "trip", "sched", "service_day")


def build_seed(conn: sqlite3.Connection, target: Path) -> dict:
    """Zgradi priloženo bazo za namestitev: samo vozni red, brez zajema.

    Zakaj sploh obstaja: uvoz iz GTFS zipa pomeni 43 MB prenosa in nekaj minut
    na počasnem jedru, česar nova namestitev ne bi smela čakati. Doslej je bila
    ta datoteka narejena ročno in je zaostala -- imela je staro shemo, star
    vozni red in nič nadomestnih prevozov.

    Kopira se s `.backup` in nato izprazni zajem, ne obratno: tako je rezultat
    zagotovo iste sheme kot delujoča baza.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)

    dst = sqlite3.connect(tmp)
    conn.backup(dst)
    dst.row_factory = sqlite3.Row
    with dst:
        for table in ("obs", "run", "weather", "alert", "alert_entity", "delay_report"):
            try:
                dst.execute(f"DELETE FROM {table}")
            except sqlite3.OperationalError:
                pass        # starejsa baza te tabele nima
        # ETagi so vezani na vsebino, ki je ne prilagamo -- ce ostanejo, prva
        # osvezitev dobi 304 in namestitev obtici na tem voznem redu.
        dst.execute("DELETE FROM meta WHERE key LIKE '%etag%' OR key LIKE '%last_modified%'")
    counts = {t: dst.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in STATIC_TABLES}
    dst.execute("VACUUM")
    dst.close()

    tmp.replace(target)
    counts["bytes"] = target.stat().st_size
    return counts
