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
    lon     REAL NOT NULL,
    -- LPP-jeva koda postajališča (`stop_code`, 600011): zadnja števka liha =
    -- proti centru, soda = iz centra (`journey.smeri_postaje`). Samo mestni LPP.
    koda    TEXT
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
    osm        TEXT,              -- ista geometrija, pripeta na tir OSM (`pripni.py`)
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
    points   TEXT NOT NULL,     -- JSON [[lat,lon], ...], 5 decimalk (~1 m)
    -- Ista trasa, pripeta na ceste oz. tire OSM (`pripni.py`), za prikaz.
    -- NULL, dokler ni pripeta; prikaz takrat riše `points`.
    osm      TEXT
);

-- Pripete trase po VSEBINI surove (ključ = točke + profil + različica
-- postopka). Uvoz `shape` vsak dan zamenja, id-ji se ponovno uporabijo,
-- točke pa ostanejo -- zato ključ ni `shape_id`. `delez` = del dolžine,
-- ki je res na OSM (ostalo je ostalo surovo).
CREATE TABLE IF NOT EXISTS pripeto (
    kljuc TEXT PRIMARY KEY,
    tocke TEXT NOT NULL,
    delez REAL NOT NULL,
    ts    INTEGER NOT NULL
);

-- Avtobusno postajališče na zemljevidu (`pripni.postajalisca`): smer ceste
-- ob njem in kdo tam ustavlja. Izračunljivo iz pripetih tras in voznega reda,
-- shranjeno, ker je prehod čez vse trase predrag za zahtevo.
CREATE TABLE IF NOT EXISTS postajalisce (
    stop_id    TEXT PRIMARY KEY,
    smer       REAL,              -- smer vožnje ob njem, ° od severa; NULL = ni ob cesti
    desno      REAL,              -- m desno od osi pripete trase (levo negativno)
    prevozniki TEXT NOT NULL,     -- '1118,1123'; mestni LPP je 1118
    postaja    INTEGER NOT NULL DEFAULT 0   -- avtobusna postaja, ne postajališče ob cesti
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

-- Voznja, ki jo je nov vozni red zamenjal z drugim id-jem, feed v zivo pa jo
-- se nosi pod starim. 22. 9. 2026 so linije LPP 25, 12D in 15 v IJPP dobile
-- nove id-je, feed pa je vozila se naprej javljal pod starimi -- zajem jih je
-- zavrgel in iskalnik je avtobus, ki je zamujal okoli 20 minut, ponudil po
-- voznem redu.
--
-- Vrstica na postanek, ker se zaporedje postankov lahko spremeni, in s
-- STARIM voznim redom, ker se feedova zamuda nanasa nanj. Nastane ob uvozu,
-- dokler je stari vozni red se v bazi -- pozneje ga ni vec od kod vzeti.
CREATE TABLE IF NOT EXISTS zamenjava (
    stari_trip  TEXT NOT NULL,
    stari_seq   INTEGER NOT NULL,
    novi_trip   TEXT NOT NULL,
    novi_seq    INTEGER NOT NULL,
    stari_arr_s INTEGER,
    stari_dep_s INTEGER,
    PRIMARY KEY (stari_trip, stari_seq)
);

-- Ista vožnja pod starim id-jem, za zgodovino: običajna zamuda, okno vožnje in
-- model štejejo tudi meritve stare (`PREDNIKI_SQL`). Obe strani sta vožnji čez
-- dneve (`voznja_sql`), ne `trip_id`, in vrstica ostane: `zamenjava` je za
-- zajem in izgine z voznim redom nove vožnje. Mestni LPP ima za vsak dan svoj
-- id; 13.–20. 10. 2026 je 228 voženj na 11 linijah dobilo nov srednji del,
-- `zamenjava` pa je vsako povezala s staro vožnjo ISTEGA dne -- ta ni nikoli
-- vozila (0 od 824), zgodovine ni bilo od nikoder. Polni `zapisi_prednike`.
CREATE TABLE IF NOT EXISTS prednik (
    nova        TEXT NOT NULL,
    stara       TEXT NOT NULL,
    stari_seq   INTEGER NOT NULL,
    novi_seq    INTEGER NOT NULL,
    stari_arr_s INTEGER,
    stari_dep_s INTEGER,
    PRIMARY KEY (nova, stara, stari_seq)
);
CREATE INDEX IF NOT EXISTS prednik_postanek ON prednik(nova, novi_seq);

-- Vožnja mestnega LPP, ki jo feed v živo nosi pod id-jem, ki ga objavljeni
-- vozni red nima, pripeta na objavljeno vožnjo z istim načrtom (`zive.py`).
-- 26. 10. 2026 je feed nosil 14 od 15 voženj linije 27 pod id-ji, ki jih ni
-- bilo nikjer; ure so bile ure objavljenih voženj do minute (13 od 13 načrtov
-- z LPP-jevih zaslonov). Zamuda gre pod objavljeno vožnjo, kot da bi feed
-- nosil njen id. Ena naša vožnja ima največ eno živo -- sicer bi dve vozili
-- pisali v isto.
CREATE TABLE IF NOT EXISTS ziva_voznja (
    ziva         TEXT PRIMARY KEY,   -- trip_id iz feeda
    nasa         TEXT NOT NULL,      -- naša vožnja
    service_date TEXT NOT NULL,
    nacin        TEXT NOT NULL,      -- 'nacrt' (LPP-jev zaslon) ali 'ura' (napoved)
    zamik_s      INTEGER,            -- napoved minus naš vozni red ob paru
    ts           INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ziva_voznja_nasa ON ziva_voznja(nasa);

-- Objavljena vožnja, ki jo je zajem prestavil na vzorec, ki ga LPP res vozi
-- (`zive.popravi`). 26. 10. 2026 je objava linijo 27 peljala mimo kolodvora
-- (Kolodvor, Friškovec), avtobusi in LPP-jevi zasloni pa po Vilharjevi
-- (Navje). Hrani objavljene postanke, traso in smer -- za razveljavitev --,
-- prestavljene -- uvoz objavljeni vozni red spet zapiše po svoje in popravek
-- za dneve v oknu naredi znova, tudi kadar vzorca ni nikjer drugje -- in
-- koliko sparjenih voženj je to pokazalo.
CREATE TABLE IF NOT EXISTS popravek_vzorca (
    trip_id      TEXT PRIMARY KEY,
    service_date TEXT NOT NULL,
    route_id     TEXT NOT NULL,
    objavljen    TEXT NOT NULL,     -- vzorec v objavljenem voznem redu
    ziv          TEXT NOT NULL,     -- vzorec, ki ga LPP vozi
    dokazov      INTEGER NOT NULL,
    ts           INTEGER NOT NULL,
    shape_id     TEXT,
    headsign     TEXT,
    postanki     TEXT NOT NULL,     -- JSON [[stop_seq, stop_id, arr_s, dep_s], ...]
    prestavljen  TEXT NOT NULL      -- JSON {"postanki": [...], "shape_id", "headsign"}
);
CREATE INDEX IF NOT EXISTS popravek_vzorca_dan
    ON popravek_vzorca(service_date, route_id, objavljen);

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
-- `MAX(feed_ts)` je vprasanje "ali zajem se dela" in ga `/api/health` postavi
-- ob vsakem klicu -- torej vsakih 30 s na vsak odprt zavihek. Brez indeksa je
-- to pregled cele tabele: izmerjeno 7. 9. 2026 na arwenu **938 ms** pri
-- 1,25 mio vrstic, po prilitju maline. Z indeksom je to en poskok po drevesu.
-- Pisanja to skoraj ne stane: zajem doda ~300 vrstic na 30 s.
CREATE INDEX IF NOT EXISTS run_feed_ts ON run(feed_ts);

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

-- Zamude vlakov z zemljevida SZ (`zamude_sz.py`), drugi vir poleg derp.si.
-- Zadnje stanje na postanek kot `run`. `v_run = 1`: derp.si vlaka ni imel
-- in vrednost je sla tudi v `run`; take vrstice ne stejejo v primerjavo virov.
CREATE TABLE IF NOT EXISTS sz_zamuda (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    delay_s      INTEGER NOT NULL,
    prvic_ts     INTEGER NOT NULL,
    zadnjic_ts   INTEGER NOT NULL,
    v_run        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (trip_id, service_date, stop_seq)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS sz_zamuda_ts ON sz_zamuda(zadnjic_ts);

-- Zamude mestnega LPP z LPP-jevih zaslonov (`zamude_lpp.py`), drugi vir
-- poleg derp.si. Isto kot `sz_zamuda`: zadnje stanje na postanek, `v_run = 1`
-- = derp.si voznje ni nosil in vrednost je sla tudi v `run`.
CREATE TABLE IF NOT EXISTS lpp_zamuda (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    delay_s      INTEGER NOT NULL,
    prvic_ts     INTEGER NOT NULL,
    zadnjic_ts   INTEGER NOT NULL,
    v_run        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (trip_id, service_date, stop_seq)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS lpp_zamuda_ts ON lpp_zamuda(zadnjic_ts);

-- Odkloni od trase (`iz_lege`), kjer vozila trase ne vozijo (`kajros
-- odkloni`). `vrsta` 'izven' = lege vec kot 150 m od trase med voznjo, z
-- zadnjo lego na trasi pred njimi in prvo za njimi (sidri); 'preskok' = dve
-- zaporedni legi ob trasi, a vmes po trasi hitreje od 30 m/s: vozilo je
-- preskocilo zanko ali krak, ki ga ima trasa. `along_*` = metri po trasi
-- `shape_id`; `along_za` NULL = vozilo se na traso ni vrnilo. `tocke` = JSON
-- [[ts, lat, lon], ...] s sidroma.
CREATE TABLE IF NOT EXISTS odklon (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    shape_id     TEXT,
    od_ts        INTEGER NOT NULL,
    do_ts        INTEGER NOT NULL,
    along_pred   INTEGER NOT NULL,
    along_za     INTEGER,
    leg          INTEGER NOT NULL,
    odmik_max    INTEGER NOT NULL,
    tocke        TEXT NOT NULL,
    vrsta        TEXT NOT NULL DEFAULT 'izven',
    PRIMARY KEY (trip_id, service_date, od_ts)
);
CREATE INDEX IF NOT EXISTS odklon_ts ON odklon(od_ts);

-- Lege voženj, iz katerih se meri prehod brez trase (`prehod.py`), zadnjih
-- 14 dni: obnova sledi po zagonu in ponovitev meritve na pravih podatkih.
-- `vozilo` od 14. 10. 2026 (prej NULL): NAP zna pod isto vožnjo javljati dve.
CREATE TABLE IF NOT EXISTS lega (
    service_date TEXT NOT NULL,
    trip_id      TEXT NOT NULL,
    ts           INTEGER NOT NULL,
    lat          REAL NOT NULL,
    lon          REAL NOT NULL,
    vozilo       TEXT,
    PRIMARY KEY (service_date, trip_id, ts)
) WITHOUT ROWID;

-- Prehodi postankov iz GPS brez trase (`prehod.py`). `prehod_ts` = odhod,
-- na cilju (`je_cilj`) prihod; `dopolnjen` = najden naknadno med sosedoma.
CREATE TABLE IF NOT EXISTS gps_prehod (
    service_date TEXT NOT NULL,
    trip_id      TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    zamuda_s     INTEGER NOT NULL,
    prehod_ts    INTEGER NOT NULL,
    je_cilj      INTEGER NOT NULL,
    dopolnjen    INTEGER NOT NULL,
    zapisano_ts  INTEGER NOT NULL,
    PRIMARY KEY (service_date, trip_id, stop_seq)
) WITHOUT ROWID;

-- Obvestila skrbnika potnikom (`obvestila.py`). Vsako ima rok; umaknjeno
-- dobi rok v preteklosti in ostane, da se ve, kaj je bilo recenega.
-- `omrezje` NULL = obe omrezji.
CREATE TABLE IF NOT EXISTS obvestilo (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    besedilo TEXT    NOT NULL,
    omrezje  TEXT,
    od_ts    INTEGER NOT NULL,
    do_ts    INTEGER NOT NULL
);

-- Tir vlaka na postaji s table SŽ (`peroni.py`). Kljuc je koledarski dan
-- table in stevilka vlaka brez vrste, ker tabla SZ drugega ne pozna; postaja
-- je nase ime. `prvi` je tir ob prvem branju -- razlika do `tir` je
-- sprememba perona cez dan. Hrani se vse: kateri vlak obicajno stoji kje,
-- ne ve nihce drug.
CREATE TABLE IF NOT EXISTS peron (
    datum   TEXT NOT NULL,
    vlak    TEXT NOT NULL,
    postaja TEXT NOT NULL,
    tir     TEXT NOT NULL,
    prvi    TEXT NOT NULL,
    videno  INTEGER NOT NULL,   -- zadnje branje, unix cas
    PRIMARY KEY (datum, vlak, postaja)
) WITHOUT ROWID;

-- Katere postaje SZ beremo in kdaj. `ima_tir` NULL = se ne vemo.
CREATE TABLE IF NOT EXISTS peron_postaja (
    st         TEXT PRIMARY KEY,   -- id postaje pri SZ
    postaja    TEXT NOT NULL,      -- nase ime
    ima_tir    INTEGER,
    vlakov     INTEGER,            -- vlakov na zadnji tabli
    promet     INTEGER NOT NULL DEFAULT 0,  -- postankov v voznem redu
    preverjeno INTEGER NOT NULL DEFAULT 0
);

-- Statistika cez vso zgodovino, izracunana enkrat na dan.
--
-- Razrez 90 dni je agregat cez milijone vrstic `run` in ga ni smiselno racunati
-- ob vsakem obisku strani: en nov dan premakne mediano 90-dnevnega okna za
-- odstotek. Zato se rezultat shrani cel (JSON) skupaj s casom izracuna, ki ga
-- stran pokaze -- predpomnjena stevilka brez datuma je laz, ki caka na priloznost.
-- Peš povezave med bližnjimi postajališči: "izstopi tu, prehodi 200 m, vkrcaj
-- se tam".
--
-- Brez njih se prestopa **samo na istem `stop_id`**, torej "Bavarski dvor" v
-- eno smer in "Bavarski dvor" v drugo za iskalnik nista isti kraj. Takih imen
-- je 4 507 od 5 500.
--
-- Vrstice so usmerjene (A->B in B->A sta dve), ker `oneway:foot` obstaja in
-- simetrije ni treba privzeti. V tabeli so **samo izmerjene** poti iz peš
-- usmerjevalnika; ocene po zraku se ne shranjujejo, sicer bi se en izpad
-- usmerjevalnika za vedno zapekel v podatke.
CREATE TABLE IF NOT EXISTS pespot (
    a_stop  TEXT NOT NULL,
    b_stop  TEXT NOT NULL,
    sekunde INTEGER NOT NULL,
    PRIMARY KEY (a_stop, b_stop)
);

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

-- Dnevni agregati za strani statistike (`statistika.py`). NE obrezuje se:
-- viri se (`napoved` 30 dni, `lega` 14), in brez tega trenda čez mesec ni.
CREATE TABLE IF NOT EXISTS stat_dan (
    dan         TEXT NOT NULL,      -- prometni dan
    vrsta       TEXT NOT NULL,      -- napoved | prevoznik | prazno
    kljuc       TEXT NOT NULL,      -- omrežje|prevoznik|skupina
    podatki     TEXT NOT NULL,      -- JSON seštevljivih vsot
    izracunano  INTEGER NOT NULL,   -- epoha izračuna
    PRIMARY KEY (dan, vrsta, kljuc)
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    # WAL se po prepisu v bazo sicer nikoli ne skrči: 1. 10. 2026 ga je
    # obstala transakcija napihnila na 5,4 GB in toliko je ostal tudi po
    # popravku -- na disku z 8 % prostora. Meja velja ob vsakem ponastavljenem
    # WAL-u, ne zmanjša pa rednega dela.
    conn.execute("PRAGMA journal_size_limit=67108864")
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
        conn.commit()
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
        conn.commit()

    # Pripeta trasa za prikaz. Izračunljiva (`pripni.pripni()`), a šele z
    # dosegljivim OSRM -- do takrat prikaz riše surovo, kot doslej.
    for tabela in ("shape", "edge"):
        stolpci = {r[1] for r in conn.execute(f"PRAGMA table_info({tabela})")}
        if stolpci and "osm" not in stolpci:
            conn.execute(f"ALTER TABLE {tabela} ADD COLUMN osm TEXT")
            conn.commit()
    # `odklon` je 12. 10. 2026 dobil preskoke (vozilo ostane ob trasi, a
    # preskoči zanko ali krak); do tedaj so bili vsi lege izven trase.
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(odklon)")}
    if stolpci and "vrsta" not in stolpci:
        conn.execute("ALTER TABLE odklon ADD COLUMN vrsta TEXT NOT NULL DEFAULT 'izven'")
        conn.commit()
    # `lega` je 14. 10. 2026 dobila vozilo: dve vozili na isti vožnji imata
    # vsako svojo sled (`prehod._sledi`). Starejše lege ostanejo brez.
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(lega)")}
    if stolpci and "vozilo" not in stolpci:
        conn.execute("ALTER TABLE lega ADD COLUMN vozilo TEXT")
        conn.commit()
    # `station.koda` od 22. 10. 2026. Napolni jo uvoz LPP-jevega zipa; da ne
    # čaka, da LPP objavi nov vozni red, pozabimo njegov ETag -- naslednja
    # osvežitev ga prenese in uvozi znova.
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(station)")}
    if stolpci and "koda" not in stolpci:
        conn.execute("ALTER TABLE station ADD COLUMN koda TEXT")
        conn.execute("DELETE FROM meta WHERE key IN ('lpp_etag', 'lpp_last_modified')")
        conn.commit()
    # Rabil ga je `PREDNIKI_SQL`, ki od 21. 10. 2026 bere `prednik`.
    conn.execute("DROP INDEX IF EXISTS zamenjava_novi")

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
    znacka = znacka_reda(conn)
    if znacka is None:
        return None
    where = conn.execute("PRAGMA database_list").fetchone()[2]
    return (where, znacka)


#: Ključi `meta`, od katerih je odvisno vse, kar se izračuna iz voznega reda:
#: uvoz in popravki vzorcev med uvozoma (`zive.popravi`). Predpomnilnik na
#: samem uvozu bi po popravku do naslednjega jutra kazal linijo 27 mimo
#: kolodvora.
KLJUCI_REDA = ("gtfs_imported_at", "vozni_red_popravljen")


def znacka_reda(conn: sqlite3.Connection) -> str | None:
    """Značka voznega reda za predpomnilnike, ali None brez uvoza (sveža ali
    testna baza, ki se lahko spremeni pod nami)."""
    vr = dict(conn.execute(
        f"SELECT key, value FROM meta WHERE key IN ({','.join('?' * len(KLJUCI_REDA))})",
        KLJUCI_REDA).fetchall())
    if not vr.get("gtfs_imported_at"):
        return None
    return "|".join(vr.get(k) or "" for k in KLJUCI_REDA)


def fill_trip_window(conn: sqlite3.Connection, trip_ids: list[str] | None = None) -> int:
    """Zapolni `trip.start_s` / `end_s` / `first_seq` / `last_seq` iz `sched`.

    Klicano ob uvozu GTFS in ob migraciji obstojece baze. Idempotentno.
    `trip_ids` zameji na te vožnje (popravek vzorca, `zive.popravi`): vseh
    60 000 voženj za eno linijo bi bilo zaman.

    `first_seq` in `last_seq` sta tu iz istega razloga kot okvir: odhodna
    tabla ju je racunala kot `MIN/MAX(stop_seq) GROUP BY trip_id` cez vseh
    403 208 vrstic `sched` ob vsaki zahtevi -- 117 ms od 120.

    **Ne potrdi sama; to naredi klicatelj.** Uvoz (`gtfs.import_static`) jo
    klice sredi svoje transakcije, in `commit()` tu je nov vozni red zapisal
    PRED zamenjavami in znacko `gtfs_imported_at`. Ce bi preostanek uvoza
    padel, bi ostal nov vozni red s staro znacko -- in vsi predpomnilniki na
    znacki (tudi okna voznj v zajemu) bi do restarta drzali staro sliko, zajem
    pa bi nove id-je zavrgel.
    """
    sql = """
        UPDATE trip SET
            start_s = (SELECT MIN(COALESCE(s.dep_s, s.arr_s)) FROM sched s
                       WHERE s.trip_id = trip.trip_id),
            end_s   = (SELECT MAX(COALESCE(s.arr_s, s.dep_s)) FROM sched s
                       WHERE s.trip_id = trip.trip_id),
            first_seq = (SELECT MIN(s.stop_seq) FROM sched s
                         WHERE s.trip_id = trip.trip_id),
            last_seq  = (SELECT MAX(s.stop_seq) FROM sched s
                         WHERE s.trip_id = trip.trip_id)
    """
    if trip_ids is None:
        conn.execute(sql)
    else:
        for i in range(0, len(trip_ids), 500):
            kos = trip_ids[i:i + 500]
            conn.execute(sql + f" WHERE trip_id IN ({','.join('?' * len(kos))})", kos)
    return conn.execute("SELECT COUNT(*) FROM trip WHERE start_s IS NOT NULL").fetchone()[0]


def voznja_sql(alias: str = "") -> str:
    """Ista vožnja čez dneve, kot SQL izraz nad `trip`.

    Pri IJPP je to `trip_id`: ena vožnja iz voznega reda vozi vse dni svojega
    `service_id`. Mestni LPP pa ima svojo vožnjo za VSAK datum in prva
    komponenta trojnega id-ja (`dan|vožnja|vzorec`) je dan -- ključ je torej
    ostanek za prvo navpičnico. Brez tega model pri LPP nikoli ni imel
    zgodovine: senca je 3.–18. 9. 2026 pri 62 498 napovedih za LPP pokazala 0 %
    z vsaj tremi dnevi, pri IJPP 77–89 %.

    Srednja komponenta je med regeneracijami GTFS stabilna (ista vožnja je
    22-krat v 31 dneh, na novem zipu z istim srednjim delom), in na dan je
    ključ enoličen (0 podvojitev med 39 907 LPP vožnjami, 18. 9. 2026).

    Izraz je v indeksu `trip_voznja` **dobesedno** -- poizvedba ga mora
    ponoviti, sicer indeks ne prime. Zato vedno skozi to funkcijo.
    """
    p = f"{alias}." if alias else ""
    return (f"CASE WHEN {p}agency = 'lpp' "
            f"THEN substr({p}trip_id, instr({p}trip_id, '|') + 1) ELSE {p}trip_id END")


def voznja(trip_id: str, agency: str | None) -> str:
    """Isto kot `voznja_sql`, v Pythonu."""
    if agency == "lpp" and "|" in trip_id:
        return trip_id.split("|", 1)[1]
    return trip_id


#: Pretekle meritve vožnje, ki jo je nov vozni red zamenjal (`prednik`),
#: prevedene na postanke in vozni red NOVE. Stolpci: `trip_id` (nova vožnja),
#: `stop_seq` (njen postanek), `service_date`, `delay_arr`, `delay_dep`.
#:
#: `voznja_sql` ista vožnja čez dneve ne ujame, kadar ji je uvoz dal nov id.
#: 22. 9. 2026 se je to zgodilo 247 vožnjam (192 LPP v IJPP, 52 Nomago,
#: 3 Arriva) in vse so ostale brez zgodovine: LPP 25 z Novega Polja je imel
#: pod starim id-jem 15 dni meritev, pod novim dva, zato je tabla pisala
#: „brez podatka“ namesto običajne zamude, model pa se je učil iz dveh dni.
#:
#: Zamuda se preračuna na nov vozni red kot v zajemu
#: (`collector.zamuda_po_zamenjavi`): absolutni čas ostane, premakne se
#: vozni red. Stari 15:29 +2 min je pri novem 15:28 +3 min. Izmerjeno
#: 21. 10. 2026, mediana stare vožnje proti vsakemu dnevu nove od 14. 10.:
#: IJPP s spremenjenim voznim redom (95 parov) MAE 3,12 min, brez prevoda
#: 6,32; z istim (112) 2,22 min, brez zgodovine (ničla) 4,84.
#:
#: Ta oblika je za posamezne postanke (`WHERE p.trip_id = ? AND p.stop_seq = ?`).
#: Za celo vožnjo je `PREDNIKI_VOZNJE_SQL`.
#:
#: Plus pred `stara` ni tipkarska napaka: stolpec je TEXT, izraz `voznja_sql`
#: brez afinitete, in primerjava z afiniteto TEXT indeksa `trip_voznja` ne sme
#: uporabiti -- vsaka vožnja s predhodnico bi prebrala vso tabelo `trip`.
_PREDNIKI_ZAMUDE = (
    "r.service_date, "
    "r.delay_arr + COALESCE(p.stari_arr_s, p.stari_dep_s) "
    "            - COALESCE(s.arr_s, s.dep_s) AS delay_arr, "
    "r.delay_dep + COALESCE(p.stari_dep_s, p.stari_arr_s) "
    "            - COALESCE(s.dep_s, s.arr_s) AS delay_dep "
)
PREDNIKI_SQL = (
    f"SELECT a.trip_id AS trip_id, p.novi_seq AS stop_seq, {_PREDNIKI_ZAMUDE}"
    "FROM trip a "
    f"CROSS JOIN prednik p ON p.nova = {voznja_sql('a')} "
    f"CROSS JOIN trip t ON {voznja_sql('t')} = +p.stara "
    "CROSS JOIN run r ON r.trip_id = t.trip_id AND r.stop_seq = p.stari_seq "
    "CROSS JOIN sched s ON s.trip_id = a.trip_id AND s.stop_seq = p.novi_seq"
)
#: Isto za vse postanke ene vožnje; edini parameter (`?`) je nova vožnja.
#:
#: Drugačen vrstni red zato, ker ključ `run` je (vožnja, dan, postanek):
#: pot od postanka nove vožnje k `run` prebere vse dni stare vožnje ZA VSAK
#: postanek posebej. Izmerjeno na LPP 25 (36 postankov, 17 dni): 9,8 ms na
#: klic in `predict` 1,3 -> 11,5 ms. Tu se `run` prebere enkrat.
PREDNIKI_VOZNJE_SQL = (
    f"SELECT k.novi AS trip_id, p.novi_seq AS stop_seq, {_PREDNIKI_ZAMUDE}"
    "FROM (SELECT DISTINCT a.trip_id AS novi, q.nova, q.stara FROM trip a "
    f"      CROSS JOIN prednik q ON q.nova = {voznja_sql('a')} WHERE a.trip_id = ?) k "
    f"CROSS JOIN trip t ON {voznja_sql('t')} = +k.stara "
    "CROSS JOIN run r ON r.trip_id = t.trip_id "
    "CROSS JOIN prednik p ON p.nova = k.nova AND p.stara = k.stara "
    "                    AND p.stari_seq = r.stop_seq "
    "CROSS JOIN sched s ON s.trip_id = k.novi AND s.stop_seq = p.novi_seq"
)

#: Mestni LPP: zgodovina gre na novo vožnjo samo, če se vozni red na nobenem
#: skupnem postanku ne razlikuje za več kot toliko. Pri IJPP prevod po uri
#: drži (zgoraj) -- nova vožnja vozi ob urah stare --, pri mestnem LPP je nova
#: ura prava: LPP 16 iz Črnega Loga od 16. 10. 2026 ob 07:35 namesto 07:45,
#: prevod bi mu pripisal +10 min (46 primerjav: MAE 12,2 min, vse precenjene),
#: brez zgodovine 1,6 min. Do 3 min razlike (4 vožnje, 108 primerjav) MAE
#: 5,0 min, precenjenih 0,9 %.
PREDNIK_LPP_RAZLIKA_S = 180


def zapisi_prednike(conn: sqlite3.Connection) -> None:
    """Pare iz `zamenjava` zapiše v `prednik`: vožnjo čez dneve k vožnji.

    Zapisano ostane, tudi ko par v `zamenjava` izgine z voznim redom nove
    vožnje. Kliče jo vsak uvoz (`gtfs._zapisi_zamenjave`).
    """
    pari: dict[tuple, list[tuple]] = {}
    for r in conn.execute(
            "SELECT z.stari_trip, z.novi_trip, n.agency, z.stari_seq, z.novi_seq, "
            "       z.stari_arr_s, z.stari_dep_s, "
            "       COALESCE(z.stari_dep_s, z.stari_arr_s), COALESCE(s.dep_s, s.arr_s) "
            "FROM zamenjava z JOIN trip n ON n.trip_id = z.novi_trip "
            "JOIN sched s ON s.trip_id = z.novi_trip AND s.stop_seq = z.novi_seq"):
        r = tuple(r)
        pari.setdefault(r[:3], []).append(r[3:])
    vrstice = []
    for (stari, novi, agency), postanki in pari.items():
        if agency == "lpp" and any(
                staro is None or novo is None or abs(novo - staro) > PREDNIK_LPP_RAZLIKA_S
                for *_, staro, novo in postanki):
            continue
        vrstice += [(voznja(novi, agency), voznja(stari, agency), *p[:4]) for p in postanki]
    conn.executemany(
        "INSERT OR IGNORE INTO prednik(nova, stara, stari_seq, novi_seq,"
        "                              stari_arr_s, stari_dep_s) VALUES(?,?,?,?,?,?)",
        vrstice)
    # Stara vožnja je lahko že sama naslednica: nova dobi tudi zgodovino njene
    # predhodnice. Vsak klic sestavi en člen verige več.
    conn.execute(
        "INSERT OR IGNORE INTO prednik(nova, stara, stari_seq, novi_seq,"
        "                              stari_arr_s, stari_dep_s) "
        "SELECT q.nova, p.stara, p.stari_seq, q.novi_seq, p.stari_arr_s, p.stari_dep_s "
        "FROM prednik q CROSS JOIN prednik p ON p.nova = q.stara AND p.novi_seq = q.stari_seq "
        "WHERE p.stara <> q.nova")


def init(conn: sqlite3.Connection) -> None:
    _migrate(conn)
    brez_prednikov = not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'prednik'").fetchone()
    conn.executescript(SCHEMA)
    # Izrazni indeks, ne stolpec: vrednost je izpeljana iz `trip_id` in
    # `agency`, zato je ni treba polniti ne ob uvozu ne ob prilivanju, in
    # nagrobniki (vožnje brez voznega reda, ki jih uvoz obdrži) jo imajo sami
    # od sebe. Izmerjeno: 30 ms za 60 951 voženj.
    conn.execute(f"CREATE INDEX IF NOT EXISTS trip_voznja ON trip({voznja_sql()})")
    # Pari izpred tabele `prednik` gredo vanjo takoj: naslednji uvoz bi jih
    # pobral šele, ko bi bil del že izginil z voznim redom nove vožnje.
    if brez_prednikov:
        zapisi_prednike(conn)
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
            if _has(conn, "peron", "prvi"):
                conn.execute(
                    "INSERT INTO peron(datum, vlak, postaja, tir, prvi, videno) "
                    "SELECT datum, vlak, postaja, tir, prvi, videno FROM src.peron WHERE true "
                    "ON CONFLICT(datum, vlak, postaja) DO UPDATE SET "
                    "  tir = CASE WHEN excluded.videno > peron.videno"
                    "             THEN excluded.tir ELSE peron.tir END, "
                    "  videno = MAX(peron.videno, excluded.videno)"
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
