"""Testi poizvedb nad shemo, na majhni bazi v pomnilniku.

Zakaj sintetična baza in ne `data/sz.sqlite`: pravila, ki jih tu preverjamo,
so robna. V pravih podatkih se pojavijo redko in nepredvidljivo, tako da bi
test enkrat lovil, drugič ne. Tu je vsak primer postavljen namenoma.

    ./venv/bin/python -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from sztrack import db, journey, ocena, stats


def _pred(dni: int) -> str:
    """Datum pred toliko dnevi. Trdi datumi bi test cez tri mesece podrli:
    `typical_at_stops` gleda samo zadnjih 90 dni."""
    return (date.today() - timedelta(days=dni)).isoformat()


# ---------------------------------------------------------------- pripravljena baza

def _sched(conn, trip_id, stops):
    """stops: [(stop_seq, stop_id, arr_s, dep_s)]

    Za voznim redom takoj tudi voznoredni okvir vozjne (`trip.start_s/end_s`),
    kot to dela uvoz GTFS. Brez njega poizvedba "kaj se zdaj vozi" vozjne ne
    vidi -- in test, ki bi to spregledal, bi bil test na drugacni bazi, kot
    jo ima aplikacija.
    """
    conn.executemany(
        "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
        [(trip_id, *row) for row in stops],
    )
    db.fill_trip_window(conn)


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)

    stations = [
        ("A", "Ajdovščina", 45.9, 13.9),
        ("B", "Bled Jezero", 46.4, 14.1),
        ("C", "Celje", 46.2, 15.3),
        ("D", "Divača", 45.7, 14.0),
        ("Z", "Zidani Most", 46.1, 15.0),
    ]
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)", stations)
    # Trd datum: nanj se sklicuje 55 preizkusov. Testi, ki dan racunajo
    # (`_pred`), morajo zato vstavljati z `INSERT OR IGNORE` -- sicer padejo
    # natanko na tisti koledarski dan, ko se datuma ujameta. To se je zgodilo
    # 31. 8. 2026 in podrlo pet preizkusov, ki so bili prejsnji dan zeleni.
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', '2026-08-31')")

    # vlak 1: A -> Z -> C  (neposredno do C)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t1','r1','IC 1','A - C','S1')")
    _sched(c, "t1", [(1, "A", None, 28800), (2, "Z", 32400, 32700), (3, "C", 36000, None)])

    # vlak 2: A -> Z  (samo do prestopne postaje)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t2','r2','LP 2','A - Z','S1')")
    _sched(c, "t2", [(1, "A", None, 25200), (2, "Z", 28800, None)])

    # vlak 3: Z -> C  (nadaljevanje; NE ustavlja v A)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t3','r3','LP 3','Z - C','S1')")
    _sched(c, "t3", [(1, "Z", None, 30600), (2, "C", 34200, None)])

    # vlak 4: B -> D. Brez njega bi bili Bled Jezero in Divača postaji, ki ju
    # ne streže nič -- takih v pravih podatkih ni (postaje nastanejo iz
    # `stop_times`) in iskanje jih namenoma ne vraca.
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t4','r4','LP 4','B - D','S1')")
    _sched(c, "t4", [(1, "B", None, 40000), (2, "D", 44000, None)])

    c.commit()
    return c


def test_postaja_brez_voznje_ni_v_iskanju(conn):
    """Postaja, ki je ne streže nič, ni koristen zadetek.

    V pravih podatkih takih ni -- `station` nastane iz `stop_times` -- a
    poizvedba to zdaj tudi izraža, namesto da bi se zanašala na uvoz.
    """
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) "
                 "VALUES('X','Nikogaršnja',46.0,14.0)")
    conn.commit()
    assert journey.search_stations(conn, "nikogar") == []


# ---------------------------------------------------------------- iskanje postaj

def test_iskanje_prezre_sumnike(conn):
    assert [s["name"] for s in journey.search_stations(conn, "ajdovscina")] == ["Ajdovščina"]
    assert [s["name"] for s in journey.search_stations(conn, "divaca")] == ["Divača"]


def test_iskanje_ujame_sredino_besede(conn):
    assert [s["name"] for s in journey.search_stations(conn, "jezero")] == ["Bled Jezero"]


def test_beseda_sredi_imena_ne_pade_za_neprometno_postajo(conn):
    """Zacetek imena in zacetek besede sta za potnika enako dober zadetek.

    Prava napaka, prijavljena 2. 9. 2026: na avtobusni strani je "polje"
    vrnilo samo postaje, ki se tako ZACNEJO. "Polje (Tolmin)" z dvema
    voznjama je bilo pred "Kranj Zlato Polje P+R" s 586, "Novo Polje" s 199
    pa je padlo na deveto mesto -- stran zahteva osem in ga ni bilo videti.
    """
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) "
                 "VALUES('P1','Polje (Tolmin)',46.2,13.7)")
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) "
                 "VALUES('P2','Novo Polje',46.0,14.6)")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('tp','rp','LP 9','P1 - P2','S1')")
    _sched(conn, "tp", [(1, "P1", None, 30000), (2, "P2", 31000, None)])
    for i, tid in enumerate(("tq1", "tq2", "tq3")):
        conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                     f"VALUES('{tid}','r{tid}','LP {10 + i}','P2 - C','S1')")
        _sched(conn, tid, [(1, "P2", None, 30000 + i), (2, "C", 34000, None)])
    conn.commit()
    names = [s["name"] for s in journey.search_stations(conn, "polje")]
    assert names[:2] == ["Novo Polje", "Polje (Tolmin)"]


def test_isto_ime_se_sesteje_pred_razvrscanjem(conn):
    """Mestno postajalisce ima svoj `stop_id` za vsako smer.

    Prej se je razvrscalo po postankih ENEGA `stop_id`, izpisala pa se je
    vsota vseh -- seznam je bil torej urejen po drugi stevilki, kot jo je
    kazal. Tu ima "Beli dvor" dve smeri po dve voznji (skupaj stiri),
    "Dvorec" pa eno smer s tremi: po vsoti mora biti prvi Beli dvor.
    """
    for sid, ime in (("B1", "Beli dvor"), ("B2", "Beli dvor"), ("B3", "Dvorec")):
        conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46.1,14.5)",
                     (sid, ime))
    for i, (tid, sid) in enumerate((("td1", "B1"), ("td2", "B1"),
                                    ("td3", "B2"), ("td4", "B2"),
                                    ("td5", "B3"), ("td6", "B3"), ("td7", "B3"))):
        conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                     f"VALUES('{tid}','r{tid}','LP {20 + i}','x','S1')")
        _sched(conn, tid, [(1, sid, None, 30000 + i), (2, "C", 34000, None)])
    conn.commit()
    hits = journey.search_stations(conn, "dvor")
    assert [h["name"] for h in hits] == ["Beli dvor", "Dvorec"]
    assert hits[0]["trips"] == 4        # obe smeri skupaj, ne le najmocnejsa


def test_tocno_ime_je_pred_delnim(conn):
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('C2','Celje Center',46.2,15.3)")
    names = [s["name"] for s in journey.search_stations(conn, "celje")]
    assert names[0] == "Celje"


def test_resolve_sprejme_delno_ime(conn):
    assert journey.resolve_station(conn, "zidani") == "Zidani Most"
    assert journey.resolve_station(conn, "cisto neznano") is None


# ---------------------------------------------------------------- odhodna tabla

def test_tabla_izpusti_koncno_postajo(conn):
    # V C se nic ne odpelje -- vsi trije vlaki tam koncajo ali sploh ne vozijo.
    board = journey.board(conn, "Celje", "2026-08-31", 0, 1440, kind="odhodi")
    assert board == []


def test_tabla_izpusti_izhodisce_pri_prihodih(conn):
    board = journey.board(conn, "Ajdovščina", "2026-08-31", 0, 1440, kind="prihodi")
    assert board == []


def test_tabla_kaze_cilj_voznje(conn):
    board = journey.board(conn, "Ajdovščina", "2026-08-31", 0, 1440, kind="odhodi")
    assert {(r["train_no"], r["towards"]) for r in board} == {("IC 1", "Celje"), ("LP 2", "Zidani Most")}


def test_tabla_vzame_zamudo_z_naslednje_postaje(conn):
    # Feed ne porocá stop_seq = 1; meritev na drugi postaji je edini priblizek
    # odhodne zamude z izhodisca in prikaz mora povedati, od kod je.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                 "VALUES('t1','2026-08-31',2,600,600,1)")
    conn.commit()
    row = next(r for r in journey.board(conn, "Ajdovščina", "2026-08-31", 0, 1440) if r["train_no"] == "IC 1")
    assert row["delay_s"] == 600
    assert row["delay_from"] == "Zidani Most"


# ---------------------------------------------------------------- prestopi

def test_prestop_najden_ko_ni_neposredne(conn):
    legs = journey.transfers(conn, "Ajdovščina", "Celje", "2026-08-31", direct=[])
    vias = {t["via"] for t in legs}
    assert "Zidani Most" in vias


def test_prestop_ne_ponudi_ce_drugi_vlak_pelje_z_izhodisca(conn):
    # LP 2 ob 07:00 do Zidanega Mosta, tam prestop na IC 1 -- a IC 1 odpelje
    # z Ajdovscine ob 08:00, torej po nasem odhodu. Potnik bi ga pocakal.
    legs = journey.transfers(conn, "Ajdovščina", "Celje", "2026-08-31", direct=[])
    assert all(t["train2"] != "IC 1" for t in legs)


def test_neposredna_voznja_prekasa_prestop(conn):
    # Neposredna odpelje kasneje in pripelje prej ali hkrati -> prestop odpade.
    direct = [{"dep_s": 25200, "arr_s": 34200}]
    legs = journey.transfers(conn, "Ajdovščina", "Celje", "2026-08-31", direct=direct)
    assert legs == []


def test_prekratek_prestop_se_ne_ponudi(conn):
    # LP 2 pride v Zidani Most ob 08:00, LP 3 odpelje ob 08:30 -- to gre.
    # Ce prihod premaknemo na 08:28, ostaneta dve minuti in povezava odpade.
    conn.execute("UPDATE sched SET arr_s = 30480 WHERE trip_id='t2' AND stop_seq=2")
    conn.commit()
    legs = journey.transfers(conn, "Ajdovščina", "Celje", "2026-08-31", direct=[])
    assert all(t["train1"] != "LP 2" for t in legs)


# ---------------------------------------------------------------- običajna zamuda

def test_obicajna_zamuda_rabi_dovolj_voznj(conn):
    # Dve vozjni sta premalo: "mediana" dveh stevilk bralcu obljublja vec,
    # kot zasluzi.
    for i, day in enumerate((_pred(9), _pred(8))):
        conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                     "VALUES('t1',?,3,?,?,?)", (day, 300 + i, 300 + i, i))
    conn.commit()
    assert stats.typical_at_stops(conn, [("t1", 3)]) == {}

    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                 "VALUES('t1',?,3,600,600,9)", (_pred(7),))
    conn.commit()
    got = stats.typical_at_stops(conn, [("t1", 3)])
    assert got[("t1", 3)]["n"] == 3
    assert got[("t1", 3)]["median_s"] == 301


def test_obicajna_zamuda_v_enem_svezni_za_vec_tripov(conn):
    for trip in ("t1", "t2"):
        for i, day in enumerate((_pred(9), _pred(8), _pred(7))):
            conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                         "VALUES(?,?,2,?,?,?)", (trip, day, 60 * (i + 1), 60 * (i + 1), i))
    conn.commit()
    got = stats.typical_at_stops(conn, [("t1", 2), ("t2", 2)])
    assert set(got) == {("t1", 2), ("t2", 2)}
    assert got[("t1", 2)]["median_s"] == 120


def test_naslednja_postaja_tudi_pri_vrzeli_v_zaporedju(conn):
    """GTFS ne zahteva strnjenega `stop_sequence`.

    V tem feedu so zaporedja sicer strnjena od 1, a če bi se to kdaj
    spremenilo, bi se odhodna tabla tiho sklicevala na napačno postajo --
    "izmerjeno v Divači" ob meritvi, ki je iz Celja. Zato preverimo z vrzeljo.
    """
    c = conn
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t9','r9','LP 9','A - C','S1')")
    _sched(c, "t9", [(1, "A", None, 20000), (5, "Z", 22000, 22100), (9, "C", 24000, None)])
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('t9','2026-08-31',5,420,420,1)")
    c.commit()

    row = next(r for r in journey.board(c, "Ajdovščina", "2026-08-31", 0, 1440)
               if r["train_no"] == "LP 9")
    assert row["delay_s"] == 420
    assert row["delay_from"] == "Zidani Most"


def test_stevilka_vlaka_z_vec_tripi_ne_podvoji_voznega_reda(conn):
    """Številka vlaka ni ključ.

    Devet vlakov v voznem redu ima dva ali tri tripe -- sezonske različice
    iste poti. Brez izbora je vozni red vlaka 4292 vračal 38 postankov
    namesto 19, vsako postajo dvakrat. Pri avtobusih je isto pravilo nujno:
    LPP linija 3G ima 388 voženj.
    """
    c = conn
    # Ista stevilka, dve razlicici: glavna vozi vsak dan, sezonska en dan.
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S2','2026-08-31')")
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S2','2026-09-01')")
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S3','2026-08-31')")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('tA','rA','LP 7','A - Z','S2')")
    _sched(c, "tA", [(1, "A", None, 30000), (2, "Z", 33000, None)])
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('tB','rB','LP 7','A - Z','S3')")
    _sched(c, "tB", [(1, "A", None, 31000), (2, "Z", 34000, None)])
    c.commit()

    tt = stats.timetable(c, "LP 7", "2026-08-31")
    assert len(tt) == 2, "vozni red ene vožnje, ne obeh različic"
    assert [r["stop_seq"] for r in tt] == [1, 2]

    # Na dan, ko vozi samo glavna, mora izbrati njo.
    assert stats.resolve_trip(c, "LP 7", "2026-09-01") == "tA"
    # Ko vozita obe, zmaga tista z več obratovalnimi dnevi.
    assert stats.resolve_trip(c, "LP 7", "2026-08-31") == "tA"


def test_run_detail_ne_podvoji_postankov(conn):
    c = conn
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S2','2026-08-31')")
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S3','2026-08-31')")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('tA','rA','LP 8','A - Z','S2')")
    _sched(c, "tA", [(1, "A", None, 30000), (2, "Z", 33000, None)])
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('tB','rB','LP 8','A - Z','S3')")
    _sched(c, "tB", [(1, "A", None, 31000), (2, "Z", 34000, None)])
    c.commit()
    assert len(stats.run_detail(c, "LP 8", "2026-08-31")) == 2


# ---------------------------------------------------------------- ločeni omrežji

def _add_bus(conn):
    """LPP linija in njeni postajališči. Ločeno omrežje, ne ločena tabela.

    Postajališči sta svoji -- avtobus, ki bi ustavljal tudi na železniški
    postaji, bi se v obeh iskanjih pojavil upravičeno in test ne bi meril
    ločitve omrežij, ampak nekaj drugega.
    """
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) "
                 "VALUES('P','Ajdovščina/Lj.',46.05,14.51)")
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) "
                 "VALUES('Q','Bavarski dvor',46.06,14.51)")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                 "                 mode, agency, network) "
                 "VALUES('b1','rb','6B','Center - Črnuče','S1','bus','1118','avtobus')")
    _sched(conn, "b1", [(1, "Q", None, 30000), (2, "P", 31000, None)])
    conn.commit()


def test_omrezji_se_ne_mesata_v_iskanju(conn):
    """Iskalnik vlakov ne sme ponujati mestnih postajališč in obratno.

    Ni le vprašanje preglednosti: pri pravih podatkih ima LPP na "Ljubljana..."
    veliko več postankov kot železnica, zato je mešano iskanje "ljublj"
    vračalo postajališča in postajo Ljubljana potisnilo iz prvih petih.
    """
    _add_bus(conn)
    rail = [s["name"] for s in journey.search_stations(conn, "ajdov", network="zeleznica")]
    bus = [s["name"] for s in journey.search_stations(conn, "ajdov", network="avtobus")]
    assert rail == ["Ajdovščina"]
    assert bus == ["Ajdovščina/Lj."]


def test_omrezji_se_ne_mesata_na_tabli(conn):
    _add_bus(conn)
    rail = journey.board(conn, "Ajdovščina", "2026-08-31", 0, 1440, network="zeleznica")
    assert {r["train_no"] for r in rail} == {"IC 1", "LP 2"}
    # Ista postaja na avtobusnem omrežju ne obstaja -- tam nič ne ustavlja.
    assert journey.board(conn, "Ajdovščina", "2026-08-31", 0, 1440, network="avtobus") == []
    bus = journey.board(conn, "Bavarski dvor", "2026-08-31", 0, 1440, network="avtobus")
    assert {r["train_no"] for r in bus} == {"6B"}
    assert journey.board(conn, "Bavarski dvor", "2026-08-31", 0, 1440, network="zeleznica") == []


def test_nadomestni_prevoz_ostane_pri_vlakih(conn):
    """Avtobus SŽ na relaciji, kjer vlak ne vozi, sodi med vlake.

    To je edini avtobus, ki pripada železnici: na tisti relaciji ZAMENJUJE
    vlak in bi bil na avtobusni strani neuporaben -- tam ga nihče ne išče.
    """
    c = conn
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              "                 mode, agency, network) "
              "VALUES('n1','rn','BUS 111','Ajdovščina - Celje','S1','bus','1161','zeleznica')")
    _sched(c, "n1", [(1, "A", None, 35000), (2, "C", 39000, None)])
    c.commit()

    rail = stats.connections(c, "Ajdovščina", "Celje", "2026-08-31", network="zeleznica")
    bus = stats.connections(c, "Ajdovščina", "Celje", "2026-08-31", network="avtobus")
    assert "BUS 111" in {r["train_no"] for r in rail}
    assert bus == []


def test_statistika_ne_steje_mestnih_avtobusov(conn):
    """Avtobus ne sme šteti med vlake v nobeni številki.

    Iskalnik je bil le prvo mesto, kjer je mešanje bolelo. `day_summary`,
    `network_stats` in `breakdowns` berejo `run` in bi brez filtra LPP
    prištele k železnici -- pri 3060 LPP vožnjah proti 733 vlakom bi to
    "delež točnih vlakov" spremenilo v delež točnih avtobusov.
    """
    _add_bus(conn)
    for trip, day, d in (("t1", "2026-08-31", 600), ("b1", "2026-08-31", 60)):
        conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
                     "VALUES(?,?,2,?,?,1)", (trip, day, d, d))
    conn.commit()

    rail = stats.day_summary(conn, "2026-08-31", network="zeleznica")
    bus = stats.day_summary(conn, "2026-08-31", network="avtobus")
    assert rail["runs"] == 1 and rail["median_s"] == 600
    assert bus["runs"] == 1 and bus["median_s"] == 60

    assert {r["train_no"] for r in stats.network_stats(conn, network="zeleznica")} == {"IC 1"}
    assert {r["train_no"] for r in stats.network_stats(conn, network="avtobus")} == {"6B"}


def test_breakdowns_loci_vrsto_vlaka_od_prevoznika(conn):
    """Pri vlaku je predpona številke vrsta, pri avtobusu je ni.

    "3G" ni vrsta avtobusa, ampak linija; skupina po njej bi dala 134 skupin
    po eno vožnjo. Zato avtobusi po prevozniku, nadomestni prevoz pa svoja
    skupina -- ta ni linija in ni vrsta vlaka.
    """
    _add_bus(conn)
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                 "                 mode, agency, network) "
                 "VALUES('n1','rn','BUS 111','A - C','S1','bus','1161','zeleznica')")
    _sched(conn, "n1", [(1, "A", None, 35000), (2, "C", 39000, None)])
    # Skupina pod desetimi vožnjami se namenoma ne pokaže (MIN_RUNS_FOR_GROUP),
    # zato jih je tu deset na vožnjo -- sicer bi test meril prag, ne razvrstitve.
    for trip in ("t1", "b1", "n1"):
        for i in range(10):
            conn.execute("INSERT INTO run(trip_id, service_date, stop_seq,"
                         "                delay_arr, delay_dep, feed_ts) "
                         "VALUES(?,?,2,120,120,1)", (trip, _pred(i + 1)))
    conn.commit()

    rail = {r["key"] for r in stats.breakdowns(conn, network="zeleznica")["by_kind"]}
    bus = {r["key"] for r in stats.breakdowns(conn, network="avtobus")["by_kind"]}
    assert rail == {"IC", "nadomestni prevoz"}
    assert bus == {"LPP"}


def test_prag_za_prestop_je_odvisen_od_omrezja(conn):
    """Tri minute so pri mestnem avtobusu prestop, pri vlaku lovljenje.

    Postajališči sta blizu in linija vozi pogosto; enoten železniški prag
    šestih minut bi veljavne zveze skril. V drugo smer velja isto: čakanje
    pol ure na liniji, ki vozi vsakih deset minut, ni prestop, ampak znak,
    da smo zamudili tri boljše -- zato je zgornja meja pri avtobusu 30 minut
    in ne dve uri.
    """
    c = conn
    _add_bus(c)     # ustvari postajališče Q = "Bavarski dvor"
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('M','Vmesna',46.0,14.5)")
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('K','Konec',46.0,14.6)")
    for tid, no, stops in (
        ("x1", "11", [(1, "Q", None, 30000), (2, "M", 30300, None)]),
        ("x2", "22", [(1, "M", None, 30480), (2, "K", 31000, None)]),   # 3 min pozneje
    ):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                  "                 mode, agency, network) "
                  "VALUES(?,?,?,'x','S1','bus','1118','avtobus')", (tid, "r" + tid, no))
        _sched(c, tid, stops)
    c.commit()

    bus = journey.transfers(c, "Bavarski dvor", "Konec", "2026-08-31",
                            direct=[], network="avtobus")
    assert [t["train2"] for t in bus] == ["22"], "tri minute morajo zadoščati"

    # Isti vozni red na železniškem omrežju: pod šestimi minutami ne ponudimo.
    c.execute("UPDATE trip SET network='zeleznica' WHERE trip_id IN ('x1','x2')")
    c.commit()
    assert journey.transfers(c, "Bavarski dvor", "Konec", "2026-08-31",
                             direct=[], network="zeleznica") == []


def test_najblizja_postajalisca_po_omrezju(conn):
    """Bližina je za mestni avtobus glavni način iskanja postaje.

    Preveri tudi, da razdalja ureja rezultat in da se omrežji ne mešata:
    železniška postaja se ne sme pojaviti med avtobusnimi postajališči,
    čeprav je morda bližja.
    """
    _add_bus(conn)     # Q = Bavarski dvor (46.06, 14.51), P = Ajdovščina/Lj. (46.05, 14.51)
    here = (46.06, 14.51)

    bus = journey.nearby_stations(conn, *here, network="avtobus")
    assert [x["name"] for x in bus] == ["Bavarski dvor", "Ajdovščina/Lj."]
    assert bus[0]["meters"] < bus[1]["meters"]

    # Ajdovščina (železniška, 45.9/13.9) je predaleč; v treh kilometrih je nič.
    assert journey.nearby_stations(conn, *here, network="zeleznica") == []


def test_najblizja_upostevajo_polmer(conn):
    _add_bus(conn)
    assert journey.nearby_stations(conn, 45.5, 14.0, network="avtobus") == []


# ---------------------------------------------------------------- nočne vožnje

def test_nocna_voznja_ostane_na_seznamu_tudi_ob_veliki_zamudi(conn):
    """Vožnja z voznorednim koncem pred polnočjo in veliko zamudo je po
    polnoči še vedno na progi.

    Optimizacija, ki vključi le vožnje z `arr_s > 86400`, jo izpusti — prav
    to je primer, ki potnika najbolj zanima (EC 79 je imel 161 minut zamude
    in je pripeljal ob 00:29). Zato pogoj računa z dopustno zamudo.
    """
    from sztrack import api

    c = conn
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('nz','rz','EC 9','A - C','S1')")
    # Voznoredni prihod na cilj ob 21:48; nič ne kaže na vožnjo čez polnoč.
    _sched(c, "nz", [(1, "A", None, 70000), (2, "Z", 74000, 74100), (3, "C", 78480, None)])
    # ...a zamuja 161 minut. Vmesno postajo je s to zamudo že prevozil
    # (74100 + 9660 = 83760, torej ob 23:16), cilj pa doseže ob 00:29.
    for seq in (2, 3):
        c.execute("INSERT INTO run(trip_id, service_date, stop_seq,"
                  "                delay_arr, delay_dep, feed_ts) "
                  "VALUES('nz','2026-08-31',?,9660,9660,1)", (seq,))
    c.commit()

    now_s = 20 * 60 + 86400          # 00:20 naslednjega dne
    strict = api._live_rows(c, "2026-08-31", now_s, overnight_only=True)
    full = api._live_rows(c, "2026-08-31", now_s, overnight_only=False)
    assert "EC 9" in {r["train_no"] for r in strict}
    assert {r["train_no"] for r in strict} == {r["train_no"] for r in full}


# ---------------------------------------------------------------- več prestopov

def test_pot_s_tremi_nogami_se_najde(conn):
    """En prestop ni dovolj za slovensko mrežo.

    Vzorec 80 parov železniških postaj: 15 neposredno, 36 z enim prestopom,
    **29 brez odgovora**, čeprav pot obstaja. Z iskanjem do treh prestopov
    jih brez odgovora ostane 3.
    """
    c = conn
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('K','Konec',46.5,15.9)")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t5','r5','LP 5','C - K','S1')")
    # Odpelje iz C ob 36300. IC 1 (neposredno A -> C) pripelje ob 36000, torej
    # pet minut prej -- premalo za prestop. Počasna pot prek Z pripelje ob
    # 34200 in zvezo ujame. Tako je edini odgovor tri noge, ne ena in ne dve.
    _sched(c, "t5", [(1, "C", None, 36300), (2, "K", 40000, None)])
    c.commit()

    assert stats.connections(c, "Ajdovščina", "Konec", "2026-08-31") == []
    assert journey.transfers(c, "Ajdovščina", "Konec", "2026-08-31", direct=[]) == []

    found = journey.plan(c, "Ajdovščina", "Konec", "2026-08-31")
    assert len(found) == 1
    p = found[0]
    assert p["transfers"] == 2
    assert [l["train_no"] for l in p["legs"]] == ["LP 2", "LP 3", "LP 5"]
    assert p["legs"][-1]["to"] == "Konec"


def test_iskanje_z_vec_prestopi_spostuje_cas_za_prestop(conn):
    """Prestop, ki je prekratek, ni pot.

    Če drugi vlak odpelje minuto po prihodu prvega, ga ne ponudimo — enako
    kot pri enem prestopu, le da tu prag velja med vsakima nogama.
    """
    c = conn
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('K','Konec',46.5,15.9)")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t5','r5','LP 5','C - K','S1')")
    # LP 3 pride v C ob 34200; ta odpelje ze ob 34260, torej cez eno minuto.
    _sched(c, "t5", [(1, "C", None, 34260), (2, "K", 40000, None)])
    c.commit()
    assert journey.plan(c, "Ajdovščina", "Konec", "2026-08-31") == []


def test_iskanje_ne_zaide_med_omrezji(conn):
    """Pot čez tri noge ne sme skočiti z vlaka na mestni avtobus in nazaj."""
    _add_bus(conn)
    c = conn
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('K','Konec',46.5,15.9)")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              "                 mode, agency, network) "
              "VALUES('b9','rb9','9X','P - K','S1','bus','1118','avtobus')")
    _sched(c, "b9", [(1, "P", None, 34000), (2, "K", 36000, None)])
    c.commit()
    # Na zelezniskem omrezju avtobusne noge ni, zato do 'Konec' ni poti.
    assert journey.plan(c, "Ajdovščina", "Konec", "2026-08-31", network="zeleznica") == []


# ---------------------------------------------------------------- dnevni povzetek

def _vozba(conn, trip, day, stops):
    """stops: [(stop_seq, delay_s)] -- zadnji je koncna zamuda vozjne."""
    for seq, d in stops:
        conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr,"
                     " delay_dep, feed_ts) VALUES(?,?,?,?,?,1)", (trip, day, seq, d, d))


def test_povzetek_vzame_zadnji_postanek(conn):
    """Konca zamuda je zamuda na zadnjem zajetem postanku, ne najvecja."""
    _vozba(conn, "t1", _pred(2), [(2, 600), (3, 120)])
    conn.commit()
    got = stats.summary_build(conn, "network_stats", "zeleznica", 90)
    row = next(r for r in got["rows"] if r["train_no"] == "IC 1")
    assert row["median_s"] == 120


def test_povzetek_ne_mesa_omrezij(conn):
    """Statistika vlakov ne sme vsebovati avtobusov in obratno.

    Filter mora biti **znotraj** poizvedbe, ne za njo: sicer jo pri milijonih
    vrstic zeleznisko vprasanje placa z avtobusnimi vrsticami.
    """
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                 " mode, agency, network) VALUES('b1','rb','LPP 6','B','S1',"
                 "'bus','1118','avtobus')")
    _sched(conn, "b1", [(1, "A", None, 30000), (2, "C", 33000, None)])
    _vozba(conn, "t1", _pred(2), [(3, 120)])
    _vozba(conn, "b1", _pred(2), [(2, 900)])
    conn.commit()

    rail = stats.summary_build(conn, "network_stats", "zeleznica", 90)["rows"]
    bus = stats.summary_build(conn, "network_stats", "avtobus", 90)["rows"]
    assert [r["train_no"] for r in rail] == ["IC 1"]
    assert [r["train_no"] for r in bus] == ["LPP 6"]


def test_povzetek_se_postreze_iz_predpomnilnika(conn):
    """Drugi klic ne sme znova racunati -- in mora povedati, iz kdaj je."""
    _vozba(conn, "t1", _pred(2), [(3, 120)])
    conn.commit()
    prvi = stats.summary_get(conn, "breakdowns", "zeleznica", 90)
    assert prvi["cached"] is False and prvi["computed_at"]

    # Nova meritev, ki je predpomnilnik se ne pozna: odgovor ostane stari.
    _vozba(conn, "t2", _pred(1), [(2, 3000)])
    conn.commit()
    drugi = stats.summary_get(conn, "breakdowns", "zeleznica", 90)
    assert drugi["cached"] is True
    assert drugi["runs"] == prvi["runs"] == 1
    assert drugi["computed_at"] == prvi["computed_at"]

    # Sele osvezitev jo vkljuci.
    stats.refresh_summaries(conn, windows=(90,), networks=("zeleznica",))
    assert stats.summary_get(conn, "breakdowns", "zeleznica", 90)["runs"] == 2


def test_prestar_povzetek_se_izracuna_znova(conn):
    """Ce nocno opravilo ni teklo, sme zahteva placati racun sama."""
    _vozba(conn, "t1", _pred(2), [(3, 120)])
    conn.commit()
    stats.summary_build(conn, "breakdowns", "zeleznica", 90)
    conn.execute("UPDATE povzetek SET computed_at = ?", (_pred(3) + "T03:30:00+02:00",))
    conn.commit()
    assert stats.summary_get(conn, "breakdowns", "zeleznica", 90)["cached"] is False


def test_voznja_z_nemogoco_zamudo_ni_ziva(conn):
    """Vožnja, ki po feedu zamuja več kot `MAX_LIVE_DELAY_S`, ni na seznamu živih.

    To je pravilo prikaza, ne pospešek. Nomagov N6571 je imel 27 060 s
    (7 h 31 min) enako na vseh 44 postankih vožnje, ki je vozila ob 04:15 —
    to je feedova zamenjava prometnega dne, ne avtobus, ki bi se opoldne še
    vozil. Prej je tak zapis pristal na zemljevidu kot vozilo na progi.
    """
    from sztrack import api

    c = conn
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              " mode, agency, network) VALUES('nz2','rz2','N 6571','A - C','S1',"
              "'bus','1119','avtobus')")
    _sched(c, "nz2", [(1, "A", None, 15300), (2, "Z", 18000, 18000), (3, "C", 20640, None)])
    for seq in (2, 3):
        c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr,"
                  " delay_dep, feed_ts) VALUES('nz2','2026-08-31',?,27060,27060,1)", (seq,))
    c.commit()

    opoldne = 12 * 3600 + 1800
    assert "N 6571" not in {r["train_no"]
                            for r in api._live_rows(c, "2026-08-31", opoldne, "avtobus")}

    # Ista vožnja z dvourno zamudo pa je živa -- meja ni "vsaka velika zamuda".
    c.execute("UPDATE run SET delay_arr = 7200, delay_dep = 7200 WHERE trip_id = 'nz2'")
    c.commit()
    zdaj = 20640 + 7200 - 60         # tik pred voznorednim koncem z zamudo
    assert "N 6571" in {r["train_no"]
                        for r in api._live_rows(c, "2026-08-31", zdaj, "avtobus")}


# ---------------------------------------------------------------- tabla: meritev proti oceni

def test_tabla_ne_kaze_feedove_napovedi_kot_meritve(conn):
    """Feedova vrednost za še nedosežen postanek ni zamuda na tej postaji.

    Živ primer, ki je to odkril: IC 502 je bil v Borovnici +17 min, feed je
    za Litijo dve postaji naprej objavil 0, tabla pa je to pokazala kot
    zamudo. Potnik bi bral, da je vlak točen.

    Merjeno (`sztrack backtest --operator`): prevoznikova napoved naprej ima
    MAE 7,9 min, prenos trenutne zamude 1,3 min. Zato prenos in oznaka
    „ocena", feedova številka pa samo v naprednem pogledu.
    """
    # IC 1: A(1) -> Z(2) -> C(3). Vlak je pri Z, feed za C pravi 0.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr,"
                 " delay_dep, feed_ts) VALUES('t1','2026-08-31',2,1020,1020,1)")
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr,"
                 " delay_dep, feed_ts) VALUES('t1','2026-08-31',3,0,0,1)")
    conn.commit()

    # Ob 09:30 je vlak Z že prevozil (32700 + 1020 = 09:22), C (10:00) pa je
    # še pred njim -- torej je feedova ničla za C napoved, ne meritev.
    ob = 9 * 3600 + 30 * 60
    vrstice = journey.board(conn, "Celje", "2026-08-31", 0, 1440,
                            kind="prihodi", now_s=ob)
    r = next(x for x in vrstice if x["train_no"] == "IC 1")
    assert r["delay_kind"] == "ocena"
    assert r["delay_s"] == 1020          # prenos, ne feedova nicla
    assert r["feed_delay_s"] == 0        # ostane vidna v naprednem pogledu


def test_tabla_prevozeni_postanek_je_meritev(conn):
    """Kar je vozilo že prevozilo, je meritev in se tako tudi imenuje."""
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr,"
                 " delay_dep, feed_ts) VALUES('t1','2026-08-31',2,600,600,1)")
    conn.commit()
    ob = 10 * 3600                        # Z je ob 09:05 + 10 min = mimo
    r = next(x for x in journey.board(conn, "Zidani Most", "2026-08-31", 0, 1440,
                                      now_s=ob) if x["train_no"] == "IC 1")
    assert r["delay_kind"] == "izmerjeno"
    assert r["delay_s"] == 600
    assert r["delay_from"] is None        # meritev je s te postaje


def test_obe_poti_do_prestopa_vrneta_enake_kljuce(conn):
    """`transfers()` in `plan()` odgovarjata na isto vprašanje — enaka oblika.

    Noga iz `transfers()` je imela samo `dep`/`arr`, noga iz `plan()` pa še
    `dep_s`/`arr_s`. Prikaz je čakanje računal iz sekund, zato je pri enem
    prestopu pisalo „prestop na postaji Zidani Most · NaN min", pri treh pa
    pravilno. Dve poti, ki vračata isto stvar, morata vračati enake ključe.
    """
    # `plan()` se oglasi šele, ko en prestop ne da ničesar -- zato postaja,
    # do katere je treba dvakrat prestopiti (ista postavitev kot pri testu
    # treh nog).
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('K','Konec',46.5,15.9)")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('t5','r5','LP 5','C - K','S1')")
    _sched(conn, "t5", [(1, "C", None, 36300), (2, "K", 40000, None)])
    conn.commit()

    ena = journey.transfers(conn, "Ajdovščina", "Celje", "2026-08-31", direct=[])
    vec = journey.plan(conn, "Ajdovščina", "Konec", "2026-08-31")
    assert ena and vec, "obe poti morata kaj najti, sicer test ne preveri ničesar"
    nujni = {"train_no", "trip_id", "from", "to", "dep", "arr", "dep_s", "arr_s"}
    assert nujni <= set(ena[0]["legs"][0])
    assert nujni <= set(vec[0]["legs"][0])

    # In sekunde se morajo ujemati s časi, sicer je "NaN min" le drugače napisan.
    for pot in (ena[0], vec[0]):
        for a, b in zip(pot["legs"], pot["legs"][1:]):
            assert b["dep_s"] - a["arr_s"] >= 0


# ---------------------------------------------------------------- veriga vozila

def _blok(conn):
    """Dve avtobusni voznji istega vozila in ena tuja z istim casom.

    Tuja je nujna: brez nje bi test prestal tudi koda, ki `block_id` ignorira
    in vzame prvo voznjo, ki se konca pravocasno.
    """
    # S2 vozi DRUG dan: `b4` je v istem bloku in bi bil casovno pravi
    # predhodnik, a tega dne ne vozi.
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S2','2026-09-01')")
    for tid, no, blok, sid in (("b1", "LPP 3", "BL1", "S1"),
                               ("b2", "LPP 6", "BL1", "S1"),
                               ("b3", "LPP 9", "BL2", "S1"),
                               ("b4", "LPP 11", "BL1", "S2")):
        conn.execute(
            "INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id,"
            "                 mode,agency,network,block_id) "
            "VALUES(?,?,?,'x',?, 'bus','1118','avtobus',?)",
            (tid, "r" + tid, no, sid, blok))
    _sched(conn, "b1", [(1, "A", None, 28800), (2, "Z", 30600, None)])   # 08:00-08:30
    _sched(conn, "b2", [(1, "Z", None, 32400), (2, "C", 34200, None)])   # 09:00-09:30
    _sched(conn, "b3", [(1, "A", None, 28800), (2, "Z", 30600, None)])   # ista ura, drug blok
    _sched(conn, "b4", [(1, "A", None, 25200), (2, "Z", 27000, None)])   # isti blok, drug dan
    conn.commit()


def test_veriga_najde_prejsnjo_in_naslednjo_voznjo(conn):
    _blok(conn)
    c = stats.vehicle_chain(conn, "LPP 6", "2026-08-31", "b2")
    assert c["prev"]["trip_id"] == "b1"
    assert c["prev"]["layover_s"] == 1800          # 08:30 -> 09:00
    assert c["next"] is None

    c = stats.vehicle_chain(conn, "LPP 3", "2026-08-31", "b1")
    assert c["prev"] is None
    assert c["next"]["trip_id"] == "b2"


def test_veriga_ne_prestopi_v_drug_blok(conn):
    """`b3` se konca ob isti uri kot `b1`, a je drugo vozilo."""
    _blok(conn)
    c = stats.vehicle_chain(conn, "LPP 6", "2026-08-31", "b2")
    assert c["prev"]["trip_id"] != "b3"


def test_veriga_upostevaj_obratovalni_dan(conn):
    """Isti `block_id` nastopa pri vec `service_id` -- v GTFS pri 788 od 1385.

    Brez preverjanja dneva bi vozilo "prislo" z voznje, ki danes ne vozi.
    """
    _blok(conn)
    assert stats.vehicle_chain(conn, "LPP 3", "2026-08-31", "b1")["prev"] is None
    # Isti blok, ista ura -- razlika je samo v tem, ali ta dan vozi.
    conn.execute("INSERT INTO service_day(service_id,date) VALUES('S2','2026-08-31')")
    conn.commit()
    assert stats.vehicle_chain(conn, "LPP 3", "2026-08-31", "b1")["prev"]["trip_id"] == "b4"


def test_vlak_nima_verige(conn):
    """`block_id` je v GTFS samo pri avtobusih -- vseh 789 voznj SZ je brez."""
    assert stats.vehicle_chain(conn, "IC 1", "2026-08-31", "t1") == {}


def test_najblizja_postaja_ima_mejo(conn):
    assert stats.nearest_station(conn, 45.9, 13.9) == ("Ajdovščina", 0)
    # Sredi Madzarske ni slovenskega postajalisca in izmisliti si ga ne smemo.
    assert stats.nearest_station(conn, 47.5, 19.0) is None


# ---------------------------------------------------------------- rezerva voznega reda

def test_rezerva_se_porabi_le_do_visine_zamude():
    """Vlak lahko nadoknadi najvec toliko, kolikor zamuja -- ne prihiti."""
    assert stats._after_slack(600, 180) == 420      # 10 min zamude, 3 min rezerve
    assert stats._after_slack(120, 600) == 0        # rezerve je vec kot zamude
    assert stats._after_slack(0, 600) == 0
    # Prehiter avtobus ostane prehiter; rezerve nima cesa porabiti.
    assert stats._after_slack(-120, 600) == -120


def test_napoved_porabi_rezervo_tudi_brez_zgodovine(conn):
    """Rezerva je vozni red, ne statistika -- zna jo prvi dan zajema.

    Prav to je locilo staro napoved od nove: LP 4219 ima na Mostu na Soci
    devet minut postanka in je iz +11 pripeljal +3, model s konstantno
    mediano spremembe pa je napovedal +9.
    """
    # t1 stoji v Zidanem Mostu pet minut (32400 -> 32700).
    f = {p["name"]: p for p in stats.predict(conn, "IC 1", 1, 600)}
    rezerva = 300 - stats.MIN_DWELL_S
    assert f["Zidani Most"]["slack_s"] == rezerva
    assert f["Zidani Most"]["predicted_delay_s"] == 600 - rezerva
    assert f["Zidani Most"]["basis"] == "rezerva voznega reda"


def test_brez_postanka_ni_rezerve_in_zamuda_se_prenese(conn):
    """`t3` nikjer ne stoji, zato se zamuda prenese nespremenjena."""
    f = {p["name"]: p for p in stats.predict(conn, "LP 3", 1, 600)}
    assert f["Celje"]["slack_s"] == 0
    assert f["Celje"]["predicted_delay_s"] == 600


def test_rezerva_se_sesteva_po_postajah(conn):
    """Dve postaji s postankom dasta vec rezerve kot ena."""
    conn.execute("INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id) "
                 "VALUES('t9','r9','LP 9','A - C','S1')")
    _sched(conn, "t9", [(1, "A", None, 28800), (2, "Z", 32400, 33000),
                        (3, "D", 34200, 34800), (4, "C", 36000, None)])
    conn.commit()
    f = {p["name"]: p for p in stats.predict(conn, "LP 9", 1, 3000)}
    ena = 600 - stats.MIN_DWELL_S
    assert f["Zidani Most"]["slack_s"] == ena
    assert f["Divača"]["slack_s"] == 2 * ena
    assert f["Celje"]["slack_s"] == 2 * ena          # zadnja postaja nima odhoda
    assert f["Divača"]["predicted_delay_s"] == 3000 - 2 * ena


def test_tabla_upostevaj_rezervo_dolgega_postanka(conn):
    """Vlak, ki na vmesni postaji stoji dolgo, zamude naprej ne prinese.

    RG 1604 stoji v Ljubljani 21 minut: pride +15 in odpelje ob 23:05 po
    voznem redu. Tabla je pisala 23:20 -- potnik bi prisel na prazen peron.
    Napaka v najslabso smer, zato ima test svoje mesto.
    """
    dan = _pred(0)
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) "
                 "VALUES('S1', ?)", (dan,))
    # A (08:00) -> Z: stoji 20 min (09:00 - 09:20) -> C (10:00)
    conn.execute("INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id) "
                 "VALUES('tr','rr','LP 7','A - C','S1')")
    _sched(conn, "tr", [(1, "A", None, 28800), (2, "Z", 32400, 33600), (3, "C", 36000, None)])
    # Izmerjeno na izhodiscu: +15 min.
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('tr',?,1,900,900,0)", (dan,))
    conn.commit()

    # Ob 08:30 je vlak med A in Z; tabla v Zidanem Mostu velja za odhod 09:20.
    b = journey.board(conn, "Zidani Most", dan, 30000, 240, now_s=30600)
    vrstica = next(r for r in b if r["train_no"] == "LP 7")
    assert vrstica["delay_kind"] == "ocena"
    # 20 min postanka - 2 min najkrajsega = 18 min rezerve, zamuda 15 -> 0.
    assert vrstica["delay_s"] == 0


def test_prihodna_tabla_ne_steje_lastnega_postanka(conn):
    """Pri prihodu vozilo se pride -- postanek je sele za tem."""
    dan = _pred(0)
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) "
                 "VALUES('S1', ?)", (dan,))
    conn.execute("INSERT INTO trip(trip_id,route_id,train_no,headsign,service_id) "
                 "VALUES('tr','rr','LP 7','A - C','S1')")
    _sched(conn, "tr", [(1, "A", None, 28800), (2, "Z", 32400, 33600), (3, "C", 36000, None)])
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('tr',?,1,900,900,0)", (dan,))
    conn.commit()

    b = journey.board(conn, "Zidani Most", dan, 30000, 240, kind="prihodi", now_s=30600)
    vrstica = next(r for r in b if r["train_no"] == "LP 7")
    assert vrstica["delay_s"] == 900        # rezerve pred prihodom ni


# ---------------------------------------------------------------- prevoznikova napoved

def test_prevoznikova_napoved_steje_samo_navzgor():
    """Nizka je nerazrešena ničla, visoka pomeni, da prevoznik ve za oviro.

    Izmerjeno na 12 026 primerih: kadar napove več od nas, ima MAE 0,21 min
    (mi 2,66); kadar napove manj ali enako, 9,17 min (mi 1,22).
    """
    assert stats._with_operator(300, 900) == 900     # ve za oviro -- verjamemo
    assert stats._with_operator(900, 0) == 900       # nerazresena nicla -- ne
    assert stats._with_operator(900, None) == 900    # o tem postanku ne pravi nic


def test_napoved_dvigne_kadar_prevoznik_ve_vec(conn):
    dan = _pred(0)
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) "
                 "VALUES('S1', ?)", (dan,))
    conn.commit()
    # Feed za Zidani Most (stop_seq 2) trdi +30 min, nasa ocena bi bila +10.
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('t1',?,2,1800,1800,0)", (dan,))
    conn.commit()
    f = {p["name"]: p for p in stats.predict(conn, "IC 1", 1, 600, service_date=dan)}
    z = f["Zidani Most"]
    assert z["operator_delay_s"] == 1800
    assert z["from_operator"] is True
    assert z["predicted_delay_s"] == 1800
    assert z["own_delay_s"] < 1800          # nasa ocena je bila nizja


def test_napoved_ne_pade_na_prevoznikovo_niclo(conn):
    dan = _pred(0)
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) "
                 "VALUES('S1', ?)", (dan,))
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('t1',?,3,0,0,0)", (dan,))
    conn.commit()
    f = {p["name"]: p for p in stats.predict(conn, "IC 1", 1, 600, service_date=dan)}
    assert f["Celje"]["from_operator"] is False
    assert f["Celje"]["predicted_delay_s"] == f["Celje"]["own_delay_s"]


def test_prevoznikove_vrednosti_ne_vzamemo_dokler_vlak_stoji():
    """Dokler vlak stoji na dolgem postanku, njegova vrednost za naprej ni
    napoved, ampak prenos zamude, s katero je prišel.

    Ujeto v živo 29. 8.: RG 1604 je stal v Ljubljani (21 min postanka, prišel
    +19); prevoznik je za naslednjo postajo objavil +19 in to čez osem minut
    popravil na +5. Vlak je prišel +5.
    """
    # prišel +19 (1140), odpelje po voznem redu (0), postanek 21 min
    assert stats._operator_is_stale(1140, 1140, 0, 1260) is True
    # ista številka, a postanek je kratek -- vlak ne stoji, vrednost je napoved
    assert stats._operator_is_stale(1140, 1140, 0, 60) is False
    # prevoznik pove NEKAJ DRUGEGA kot zamudo ob prihodu -- to je znanje
    assert stats._operator_is_stale(1800, 1140, 0, 1260) is False
    # ni vecja od tega, kar ze vemo -- pravilo tako ali tako ne bi ugriznilo
    assert stats._operator_is_stale(1140, 1140, 1140, 1260) is False


def test_napoved_ne_prevzame_prenesene_zamude(conn):
    """Isto, na celotni poti: model ne sme prevzeti prevoznikovega prenosa."""
    dan = _pred(0)
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) "
                 "VALUES('S1', ?)", (dan,))
    # t1 dobi v Zidanem Mostu dolg postanek: 09:00 -> 09:25
    conn.execute("UPDATE sched SET dep_s = 34200 WHERE trip_id='t1' AND stop_seq=2")
    db.fill_trip_window(conn)
    # vlak stoji v Zidanem Mostu: prišel +20, odhod po voznem redu
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('t1',?,2,1200,0,0)", (dan,))
    # prevoznik za Celje objavi natanko zamudo ob prihodu -- prenos, ne napoved
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('t1',?,3,1200,1200,0)", (dan,))
    conn.commit()
    f = {p["name"]: p for p in stats.predict(conn, "IC 1", 2, 0, service_date=dan)}
    assert f["Celje"]["from_operator"] is False
    assert f["Celje"]["predicted_delay_s"] == f["Celje"]["own_delay_s"]


# --------------------------------------------------------------- senca napovedi
#
# `ocena.py` meri, kar je potnik RES videl: kaj je prikaz trdil 25 minut pred
# vlakom in kaj se je potem zgodilo. Preizkus pelje cel krog -- posnetek,
# vozilo prevozi postanek, resnica se dopise -- ker je prav ta krog tisto, kar
# se lahko tiho pokvari: posnetek brez resevanja je tabela, ki samo raste.

def _ob(ura_s):
    """Datum priprave (`2026-08-31`) ob dani sekundi dneva."""
    from datetime import datetime
    return datetime(2026, 8, 31, tzinfo=ocena.TZ) + timedelta(seconds=ura_s)


def test_senca_posname_napoved_in_dopise_resnico(conn):
    ocena.init(conn)
    # Vlak t1: A 08:00 -> Z 09:00/09:05 -> C 10:00. Izmerjen je na Z (+10 min),
    # torej je bil tam ob 09:15 -- ob 09:35 je C se 25 minut proc.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                 " feed_ts) VALUES('t1','2026-08-31',2,600,600,0)")

    izid = ocena.snapshot(conn, _ob(34500))
    assert izid["zapisanih"] == 1

    vrstica = conn.execute("SELECT * FROM napoved").fetchone()
    assert (vrstica["stop_seq"], vrstica["from_seq"]) == (3, 2)
    assert vrstica["current_s"] == 600
    assert vrstica["carry_s"] == 600          # referenca je prenos zamude
    assert vrstica["horizon_s"] == 1500       # natanko potnikovo okno
    assert vrstica["actual_s"] is None

    # Dokler vlak ni tam, resnice ni -- to je bistvo meje `last_measured`.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                 " feed_ts) VALUES('t1','2026-08-31',3,300,300,0)")
    assert ocena.resolve(conn, _ob(34500))["resenih"] == 0
    assert conn.execute("SELECT actual_s FROM napoved").fetchone()["actual_s"] is None

    # Ob 10:10 je vlak (vozni red 10:00 + 5 min) mimo: resnica je +5 min.
    assert ocena.resolve(conn, _ob(36600))["resenih"] == 1
    assert conn.execute("SELECT actual_s FROM napoved").fetchone()["actual_s"] == 300


def test_senca_ne_meri_voznje_brez_meritve(conn):
    """Brez izmerjenega postanka nase ocene ni -- in izmisljena ocena je
    slabsa od priznanja, da je ne poznamo. Tak primer se sam presteje."""
    ocena.init(conn)
    izid = ocena.snapshot(conn, _ob(34500))
    assert izid["zapisanih"] == 0
    assert izid["brez_meritve"] >= 1


def test_senca_posname_postanek_samo_enkrat(conn):
    """Potnik pogleda enkrat. Drugi obhod cez minuto ne sme prepisati prvega,
    sicer bi merili napoved z vedno krajsim horizontom."""
    ocena.init(conn)
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                 " feed_ts) VALUES('t1','2026-08-31',2,600,600,0)")
    ocena.snapshot(conn, _ob(34500))
    prvi = conn.execute("SELECT made_ts, horizon_s FROM napoved").fetchone()
    assert ocena.snapshot(conn, _ob(34560))["zapisanih"] == 0
    drugi = conn.execute("SELECT made_ts, horizon_s FROM napoved").fetchone()
    assert (drugi["made_ts"], drugi["horizon_s"]) == (prvi["made_ts"], prvi["horizon_s"])
