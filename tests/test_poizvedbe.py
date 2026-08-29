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
    assert bus == {"avtobus 1118"}


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
