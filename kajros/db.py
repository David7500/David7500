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
-- Vse potniske poizvedbe se zacnejo pri IMENU postaje, ne pri stop_id.
CREATE INDEX IF NOT EXISTS station_name ON station(name);

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
-- Trasa vožnje po cesti oz. progi (GTFS `shapes.txt`), poenostavljena z
-- Douglas-Peuckerjem na ~10 m. Statična tabela: ob uvozu se zamenja in ne
-- raste. Izmerjeno na celotnem slovenskem GTFS: 2 897 oblik in 519 490 točk
-- po poenostavitvi (iz 4,85 milijona), kar je 11,4 MB -- proti bazi, ki iz
-- `run` zraste za 0,2--3,4 GB na leto, je to nič.
--
-- Zakaj sploh: `edge` ima železniško mrežo, sestavljeno iz odsekov med
-- postajami, avtobusi pa vanjo namenoma ne gredo (vozijo po cesti in bi mreži
-- prog dodali odseke, ki niso proge). Za vprašanje "kod pelje MOJ avtobus" je
-- torej to edini vir.
CREATE TABLE IF NOT EXISTS shape (
    shape_id TEXT PRIMARY KEY,
    points   TEXT NOT NULL      -- JSON [[lat,lon], ...], 5 decimalk (~1 m)
);

CREATE TABLE IF NOT EXISTS trip (
    trip_id    TEXT PRIMARY KEY,
    route_id   TEXT NOT NULL,
    train_no   TEXT NOT NULL,   -- npr. "LPV 2206" ali "BUS 44201"
    headsign   TEXT,
    service_id TEXT NOT NULL,
    color      TEXT,
    mode       TEXT NOT NULL DEFAULT 'vlak',
    agency     TEXT,
    -- Kateri strani aplikacije voznja pripada. NI isto kot `mode`:
    -- nadomestni prevoz SZ je `mode = 'bus'`, a `network = 'zeleznica'`,
    -- ker na tisti relaciji ZAMENJUJE vlak in sodi v isti odgovor kot vlaki.
    -- LPP in medkrajevni prevozniki so `avtobus` in imajo svojo stran:
    -- potnik ve, ali gre z vlakom ali z busom, in ju ne isce skupaj.
    network    TEXT NOT NULL DEFAULT 'zeleznica',
    -- Prvi in zadnji postanek voznje. Izpeljano iz `sched`, a shranjeno:
    -- odhodna tabla je to prej racunala kot `MIN/MAX(stop_seq) GROUP BY
    -- trip_id` cez vseh 403 208 vrstic `sched` ob VSAKI zahtevi -- 117 ms od
    -- 120. Vozni red se med uvozi ne spreminja, zato je to statika.
    first_seq  INTEGER,
    last_seq   INTEGER,
    -- Voznoredni okvir voznje: prvi odhod in zadnji prihod, sekundi od
    -- polnoci prometnega dne (zna cez 86400). Izpeljano iz `sched`, a
    -- shranjeno tu, ker ga potrebuje najbolj vroca poizvedba -- "kaj se
    -- zdaj vozi" -- in grupiranje 403 000 vrstic `sched` ob vsakem klicu
    -- je bilo pri vseh prevoznikih sekunda. Polni se ob uvozu GTFS.
    start_s    INTEGER,
    end_s      INTEGER,
    -- Katera trasa pripada tej vožnji (`shape.shape_id`). Vsaka vožnja v
    -- zajetem GTFS jo ima -- 0 od 20 736 je brez.
    shape_id   TEXT,
    -- Veriga voznj istega fizicnega vozila (GTFS `trips.block_id`). Imajo ga
    -- SAMO avtobusi -- vseh 789 voznj SZ je brez njega -- in tudi tam le
    -- 7 547 od 20 736 (36 %). Zato je stolpec pogosto NULL in indeks delen.
    --
    -- Sluzi za vprasanje "kje je zdaj moj avtobus, ki se se ni zacel":
    -- vozilo je na prejsnji voznji v bloku in tam ima GPS lego. NE sluzi za
    -- napoved zamude -- to je izmerjeno in ne drzi (glej `vehicle_chain`).
    block_id   TEXT
);
CREATE INDEX IF NOT EXISTS trip_train_no ON trip(train_no);
-- Za "kaj se zdaj vozi": omrezje in casovno okno v enem branju indeksa.
CREATE INDEX IF NOT EXISTS trip_running ON trip(network, start_s, end_s);
CREATE INDEX IF NOT EXISTS trip_mode ON trip(mode);
CREATE INDEX IF NOT EXISTS trip_network ON trip(network);
-- Obvestila o ovirah so vezana na `route_id` in edini most do stevilke vlaka
-- je ta stolpec. Brez indeksa je vsako obvestilo poln pregled 20 736 voznj:
-- pri 21 hkrati veljavnih obvestilih 435 000 vrstic za en klic /api/overview.
CREATE INDEX IF NOT EXISTS trip_route ON trip(route_id);
-- Delen: block_id ima le tretjina avtobusnih voznj in noben vlak. Poln indeks
-- bi hranil 13 000 NULL vrstic, ki jih nobena poizvedba ne isce.
CREATE INDEX IF NOT EXISTS trip_block ON trip(block_id, start_s)
    WHERE block_id IS NOT NULL;

-- Vozni red. arr_s/dep_s sta sekundi od polnoci in lahko presezeta 86400.
CREATE TABLE IF NOT EXISTS sched (
    trip_id  TEXT NOT NULL,
    stop_seq INTEGER NOT NULL,
    stop_id  TEXT NOT NULL,
    arr_s    INTEGER,
    dep_s    INTEGER,
    PRIMARY KEY (trip_id, stop_seq)
);
-- Kljuc je (trip_id, stop_seq), iskanje pa gre v drugo smer: "kaj ustavlja
-- na tej postaji". Brez tega indeksa je vsaka poizvedba po postaji poln
-- pregled 403 000 vrstic -- pri sami zeleznici neopazno, pri vseh
-- prevoznikih pol sekunde.
CREATE INDEX IF NOT EXISTS sched_stop ON sched(stop_id);

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

-- Statistika cez vso zgodovino, izracunana enkrat na dan.
--
-- Razrez 90 dni je agregat cez milijone vrstic `run` in ga ni smiselno racunati
-- ob vsakem obisku strani: en nov dan premakne mediano 90-dnevnega okna za
-- odstotek. Zato se rezultat shrani cel (JSON) skupaj s casom izracuna, ki ga
-- stran pokaze -- predpomnjena stevilka brez datuma je laz, ki caka na priloznost.
CREATE TABLE IF NOT EXISTS povzetek (
    kind        TEXT NOT NULL,      -- network_stats | breakdowns
    network     TEXT NOT NULL,      -- zeleznica | avtobus
    days        INTEGER NOT NULL,   -- sirina okna
    computed_at TEXT NOT NULL,      -- ISO 8601 z obmocjem
    through     TEXT,               -- zadnji obratovalni dan v izracunu
    took_ms     INTEGER,            -- koliko je racun trajal
    runs        INTEGER,            -- koliko vozenj je zajel
    payload     TEXT NOT NULL,      -- JSON odgovora
    PRIMARY KEY (kind, network, days)
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
        have.add("mode")
    if have and "network" not in have:
        conn.execute("ALTER TABLE trip ADD COLUMN network TEXT NOT NULL DEFAULT 'zeleznica'")
        conn.commit()
        have.add("network")
    # Voznoredni okvir voznje. Za razliko od `mode` in `network` ga ne moremo
    # pustiti praznega do naslednjega uvoza -- poizvedba "kaj se zdaj vozi"
    # bi brez njega vrnila nic -- zato ga tu tudi izracunamo.
    if have and "start_s" not in have:
        conn.execute("ALTER TABLE trip ADD COLUMN start_s INTEGER")
        conn.execute("ALTER TABLE trip ADD COLUMN end_s INTEGER")
        conn.commit()
        fill_trip_window(conn)
        have.add("start_s")
    # Veriga vozila. Tega izracunati ne moremo -- je v GTFS zipu -- zato ostane
    # prazen do naslednjega `kajros update`, prikaz pa ga zna pogresati.
    if have and "block_id" not in have:
        conn.execute("ALTER TABLE trip ADD COLUMN block_id TEXT")
        conn.commit()
    # Trasa voznje. Kot `block_id`: v GTFS zipu je, izracunati je ni mogoce,
    # zato ostane prazna do naslednjega `kajros update`. Prikaz jo zna
    # pogresati -- brez trase se zemljevid ne pokvari, samo manj pove.
    if have and "shape_id" not in have:
        conn.execute("ALTER TABLE trip ADD COLUMN shape_id TEXT")
        conn.commit()
    # Prvi in zadnji postanek. Kot okvir: izracunljivo iz `sched`, zato ga tu
    # tudi izracunamo -- odhodna tabla bi brez njega vrnila prazno.
    if have and "first_seq" not in have:
        conn.execute("ALTER TABLE trip ADD COLUMN first_seq INTEGER")
        conn.execute("ALTER TABLE trip ADD COLUMN last_seq INTEGER")
        conn.commit()
        fill_trip_window(conn)

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


def cache_key(conn: sqlite3.Connection) -> tuple | None:
    """Kljuc za predpomnjenje staticnih podatkov, ali None, ce ne gre.

    Vsebuje **tudi pot do baze**: sicer si dve bazi z istim zigom delita
    predpomnilnik, kar se v testih pokaze takoj -- vsak test dobi svojo bazo
    v pomnilniku in vse imajo zig prazen. Brez ziga vrne None: to je sveza
    ali testna baza, ki se lahko spremeni pod nami, ne da bi nam kdo povedal.
    """
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'gtfs_imported_at'").fetchone()
    if not row or not row[0]:
        return None
    where = conn.execute("PRAGMA database_list").fetchone()[2]
    return (where, row[0])


def fill_trip_window(conn: sqlite3.Connection) -> int:
    """Zapolni `trip.start_s` / `end_s` / `first_seq` / `last_seq` iz `sched`.

    Klicano ob uvozu GTFS in ob migraciji obstojece baze. Idempotentno.

    `first_seq` in `last_seq` sta tu iz istega razloga kot okvir: odhodna
    tabla ju je racunala kot `MIN/MAX(stop_seq) GROUP BY trip_id` cez vseh
    403 208 vrstic `sched` ob vsaki zahtevi -- 117 ms od 120.
    """
    conn.execute("""
        UPDATE trip SET
            start_s = (SELECT MIN(COALESCE(s.dep_s, s.arr_s)) FROM sched s
                       WHERE s.trip_id = trip.trip_id),
            end_s   = (SELECT MAX(COALESCE(s.arr_s, s.dep_s)) FROM sched s
                       WHERE s.trip_id = trip.trip_id),
            first_seq = (SELECT MIN(s.stop_seq) FROM sched s
                         WHERE s.trip_id = trip.trip_id),
            last_seq  = (SELECT MAX(s.stop_seq) FROM sched s
                         WHERE s.trip_id = trip.trip_id)
    """)
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM trip WHERE start_s IS NOT NULL").fetchone()[0]


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
            # VOZNJE, ki jih tu ni, a imajo v viru meritve.
            #
            # Brez tega prilitje pripelje meritve, njihove identitete pa ne:
            # `run` dobi vrstice za `trip_id`, ki ga v `trip` ni, in ker gre
            # vsaka poizvedba skozi `JOIN trip` (omrezje je tam), teh meritev
            # od tedaj ne vidi nihce. Tiho, brez napake.
            #
            # Tako je nastalo 114 osirotelih voznj s 3 043 meritvami: uvoz
            # novega voznega reda jih je izbrisal iz `trip`, prilitje z maline
            # pa je vrnilo samo meritve. Izmerjeno 4. 9. 2026.
            #
            # `INSERT OR IGNORE`: kar ze imamo, je iz novejsega voznega reda in
            # ostane. Pogoj EXISTS pa poskrbi, da ne vlecemo celega starega
            # voznega reda -- samo tisto, kar nosi meritve.
            if _has(conn, "trip", "train_no", "network", "mode"):
                conn.execute(
                    "INSERT OR IGNORE INTO trip"
                    "(trip_id, route_id, train_no, headsign, service_id, color,"
                    " mode, agency, network, start_s, end_s, block_id, shape_id) "
                    "SELECT t.trip_id, t.route_id, t.train_no, t.headsign, t.service_id,"
                    "       t.color, t.mode, t.agency, t.network, t.start_s, t.end_s,"
                    "       t.block_id, t.shape_id "
                    "FROM src.trip t "
                    "WHERE EXISTS (SELECT 1 FROM src.run r WHERE r.trip_id = t.trip_id)"
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
# Kar sodi v seme: vozni red in mreza. `shape` je zraven, ker je trasa del
# staticne slike -- a se v semenu obreze na izbrano omrezje (12,3 MB tras je
# vecinoma avtobusnih).
STATIC_TABLES = ("station", "edge", "trip", "sched", "service_day", "shape")


def build_seed(conn: sqlite3.Connection, target: Path,
               network: str | None = "zeleznica") -> dict:
    """Zgradi priloženo bazo za namestitev: samo vozni red, brez zajema.

    Zakaj sploh obstaja: uvoz iz GTFS zipa pomeni 43 MB prenosa in nekaj minut
    na počasnem jedru, česar nova namestitev ne bi smela čakati. Doslej je bila
    ta datoteka narejena ročno in je zaostala -- imela je staro shemo, star
    vozni red in nič nadomestnih prevozov.

    Kopira se s `.backup` in nato izprazni zajem, ne obratno: tako je rezultat
    zagotovo iste sheme kot delujoča baza.

    **Privzeto samo železnica, in to je izmerjeno.** Z avtobusi vred je seme
    53 MB -- torej vec od samega GTFS zipa (41 MB), ki bi ga namestitev sicer
    prenesla. Seme, ki je drazje od tega, cemur se izogiba, nima smisla.
    Zeleznisko je 1,9 MB. Avtobusi so izbirni (`KAJROS_AGENCIES`) in tako ali
    tako sprozijo ponovni uvoz voznega reda, ker jih v semenu ni.
    `network=None` zgradi vse -- za stroj, ki seme dobi drugace kot po zipu.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)

    dst = sqlite3.connect(tmp)
    conn.backup(dst)
    dst.row_factory = sqlite3.Row
    with dst:
        # Izprazni VSE, kar ni statika -- ne le nasteto. Prejsnji seznam je bil
        # rocen in je zaostal: seme je prilagalo `napoved` (5,4 MB sence
        # meritev) in `povzetek`, ker sta tabeli nastali kasneje. Kar se doda
        # jutri, bo tu pravilno obravnavano brez popravka.
        vse = [r[0] for r in dst.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'")]
        for table in vse:
            if table in STATIC_TABLES or table == "meta":
                continue
            dst.execute(f"DELETE FROM {table}")
        # ETagi so vezani na vsebino, ki je ne prilagamo -- ce ostanejo, prva
        # osvezitev dobi 304 in namestitev obtici na tem voznem redu.
        # ETagi in casi zadnjega zajema: oboje je stanje TEGA stroja, ne vozni
        # red. `gtfs_imported_at` ostane -- pove, iz kdaj je prilozeni red.
        dst.execute("DELETE FROM meta WHERE key LIKE '%etag%' "
                    "OR key LIKE '%last_modified%' OR key LIKE '%_fetched'")

        if network:
            # Vrstni red je pomemben: najprej odvisne tabele, sele nato `trip`.
            # `station` pustimo pri miru -- postajalisce brez voznje ne skodi
            # in brisanje bi zahtevalo se `edge` in `shape`.
            dst.execute("DELETE FROM sched WHERE trip_id IN "
                        "(SELECT trip_id FROM trip WHERE network != ?)", (network,))
            dst.execute("DELETE FROM service_day WHERE service_id NOT IN "
                        "(SELECT service_id FROM trip WHERE network = ?)", (network,))
            dst.execute("DELETE FROM trip WHERE network != ?", (network,))
            # Trase in postaje, ki jih po tem ne rabi nihce. Brez tega je seme
            # 21 MB namesto 2 -- vecina tras je avtobusnih.
            dst.execute("DELETE FROM shape WHERE shape_id NOT IN "
                        "(SELECT shape_id FROM trip WHERE shape_id IS NOT NULL)")
            dst.execute("DELETE FROM station WHERE stop_id NOT IN "
                        "(SELECT stop_id FROM sched)")
    counts = {t: dst.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in STATIC_TABLES}
    dst.execute("VACUUM")
    dst.close()

    tmp.replace(target)
    counts["bytes"] = target.stat().st_size
    return counts
