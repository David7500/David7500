"""Testi poizvedb nad shemo, na majhni bazi v pomnilniku.

Zakaj sintetična baza in ne `data/sz.sqlite`: pravila, ki jih tu preverjamo,
so robna. V pravih podatkih se pojavijo redko in nepredvidljivo, tako da bi
test enkrat lovil, drugič ne. Tu je vsak primer postavljen namenoma.

    ./venv/bin/python -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from sztrack import db, journey, stats


def _pred(dni: int) -> str:
    """Datum pred toliko dnevi. Trdi datumi bi test cez tri mesece podrli:
    `typical_at_stops` gleda samo zadnjih 90 dni."""
    return (date.today() - timedelta(days=dni)).isoformat()


# ---------------------------------------------------------------- pripravljena baza

def _sched(conn, trip_id, stops):
    """stops: [(stop_seq, stop_id, arr_s, dep_s)]"""
    conn.executemany(
        "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
        [(trip_id, *row) for row in stops],
    )


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

    c.commit()
    return c


# ---------------------------------------------------------------- iskanje postaj

def test_iskanje_prezre_sumnike(conn):
    assert [s["name"] for s in journey.search_stations(conn, "ajdovscina")] == ["Ajdovščina"]
    assert [s["name"] for s in journey.search_stations(conn, "divaca")] == ["Divača"]


def test_iskanje_ujame_sredino_besede(conn):
    assert [s["name"] for s in journey.search_stations(conn, "jezero")] == ["Bled Jezero"]


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
