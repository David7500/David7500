"""Testi poizvedb nad shemo, na majhni bazi v pomnilniku.

Zakaj sintetična baza in ne `data/kajros.sqlite`: pravila, ki jih tu preverjamo,
so robna. V pravih podatkih se pojavijo redko in nepredvidljivo, tako da bi
test enkrat lovil, drugič ne. Tu je vsak primer postavljen namenoma.

    ./venv/bin/python -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import date, timedelta

import json
import pytest

from kajros import db, journey, ocena, stats


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
    # Dnevni povzetek preverjamo na 31. 8. (natanko ena vozjna na omrezje),
    # lestvica pa ima prag `MIN_RUNS_FOR_RANK`, zato so ostali dnevi zraven.
    # Datumi so trdi, ker jih testira tudi `day_summary`; v `service_day` se ne
    # vstavlja nic, zato trka z vrstico iz priprave ni.
    for trip, day, d in (("t1", "2026-08-31", 600), ("b1", "2026-08-31", 60),
                         ("t1", "2026-08-30", 600), ("b1", "2026-08-30", 60),
                         ("t1", "2026-08-29", 600), ("b1", "2026-08-29", 60),
                         ("t1", "2026-08-28", 600), ("b1", "2026-08-28", 60),
                         ("t1", "2026-08-27", 600), ("b1", "2026-08-27", 60)):
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
    # Agencija 1118 je LPP-jev PRIMESTNI promet iz IJPP. Mestni je drug vir
    # (`agency = 'lpp'`) in mora biti svoja skupina: izmerjeno na istem dnevu
    # ima mestni mediano zamude 0 min in 91 % v petih minutah, primestni pa
    # 2,6 min in 66 %. Skupna vrstica ni opisovala nobenega od njiju.
    assert bus == {"LPP primestni"}


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
    from kajros import api

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
    """Konca zamuda je zamuda na zadnjem zajetem postanku, ne najvecja.

    Pet dni, ker ima lestvica prag `MIN_RUNS_FOR_RANK`: vozjna z enim samim
    zajemom na vrhu ni najslabsi vlak, ampak najmanjsi vzorec.
    """
    for dan in range(2, 7):
        _vozba(conn, "t1", _pred(dan), [(2, 600), (3, 120)])
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
    for dan in range(2, 7):            # prag MIN_RUNS_FOR_RANK
        _vozba(conn, "t1", _pred(dan), [(3, 120)])
        _vozba(conn, "b1", _pred(dan), [(2, 900)])
    conn.commit()

    rail = stats.summary_build(conn, "network_stats", "zeleznica", 90)["rows"]
    bus = stats.summary_build(conn, "network_stats", "avtobus", 90)["rows"]
    assert [r["train_no"] for r in rail] == ["IC 1"]
    assert [r["train_no"] for r in bus] == ["LPP 6"]


def test_tabla_zdruzi_sezonske_razlicice(conn):
    """Ista voznja z dvema tripoma ne sme biti na tabli dvakrat.

    Devet vlakov v zajetem voznem redu ima dva ali tri tripe -- sezonske
    razlicice iste poti. Kadar oba veljata isti dan, je bila 3. 9. 2026 na
    Bled Jezeru LP 4208 ob 09:13 v DVEH vrsticah, ena brez meritve in ena
    s +6 min. Obdrzi se tista, ki ima kaj povedati.
    """
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S2','2026-08-31')")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('t1b','r1','IC 1','A - C','S2')")
    _sched(conn, "t1b", [(1, "A", None, 28800), (2, "Z", 32400, 32700), (3, "C", 36000, None)])
    # Meritev ima samo sezonska razlicica.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                 " feed_ts) VALUES('t1b','2026-08-31',1,300,300,1)")
    conn.commit()

    # Tabla isce po IMENU postaje, ne po `stop_id`.
    vrstice = journey.board(conn, "Ajdovščina", "2026-08-31", 0, window_min=24 * 60)
    ic = [r for r in vrstice if r["train_no"] == "IC 1"]
    assert len(ic) == 1, [(r["trip_id"], r["t_s"]) for r in ic]
    assert ic[0]["trip_id"] == "t1b"        # obdrzana je tista z meritvijo


def test_izbere_voznjo_z_meritvami(conn):
    """Katera voznja danes res pelje, pove MERITEV, ne vozni red.

    LP 4208 ima tri tripe. Danes je peljal tisti s 30 meritvami, izbira po
    dnevih veljavnosti pa je vzela tistega z 232 dnevi in NIC meritvami --
    kdor je vlak kliknil na zivem seznamu, je pristal na strani, ki o njem ne
    ve nicesar, ceprav je vlak vozil 8 minut pozno.
    """
    dan = _pred(1)
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S1',?)", (dan,))
    # Druga voznja iste stevilke: vec dni veljavnosti, a brez meritev.
    conn.execute("INSERT INTO service_day(service_id, date) "
                 "SELECT 'S9', date FROM service_day WHERE service_id='S1'")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('t1x','r1','IC 1','A - C','S9')")
    _sched(conn, "t1x", [(1, "A", None, 28800), (2, "Z", 32400, 32700), (3, "C", 36000, None)])
    # Meritev ima SAMO t1.
    _vozba(conn, "t1", dan, [(2, 480)])
    conn.commit()
    assert stats.resolve_trip(conn, "IC 1", dan) == "t1"


def test_neobstojec_trip_ne_vrne_druge_voznje(conn):
    """Zastarel `?trip=` mora dati napako, ne tujega voznega reda.

    Prej je preverjanje bilo, a je ob neujemanju tiho padlo na izbiro po
    dnevih: `/api/train/3G?trip=999999999` je vrnil 200 in vozni red povsem
    druge voznje, neobstojeci id pa odzvanjal nazaj.
    """
    assert stats.resolve_trip(conn, "IC 1") == "t1"          # brez id-ja izbere sam
    assert stats.resolve_trip(conn, "IC 1", trip_id="t1") == "t1"
    assert stats.resolve_trip(conn, "IC 1", trip_id="ne-obstaja") is None
    assert stats.resolve_trip(conn, "IC 1", trip_id="t2") is None   # tuja voznja


def test_lestvica_neverjetne_zamude_ne_steje(conn):
    """Zamuda nad `MAX_REALNA_ZAMUDA_S` ni zamuda, ampak zamenjan prometni dan.

    Izmerjeno 3. 9. 2026: zeleznica nima nobene vrstice nad 3 h v 69 803
    meritvah, pri avtobusih pa jih je 2 614 (0,49 %) in povprecje zaradi njih
    zraste s 4,86 na 7,25 min. Lestvica je bila prej polna voznj z mediano
    cez deset ur.
    """
    for dan in range(2, 7):
        _vozba(conn, "t1", _pred(dan), [(3, 10 * 3600)])     # 10 ur
    conn.commit()
    imena = {r["train_no"] for r in stats.network_stats(conn, network="zeleznica")}
    assert "IC 1" not in imena


def test_lestvica_potrebuje_dovolj_voznj(conn):
    """Vozjna z dvema zajemoma ni najslabsi vlak, ampak najmanjsi vzorec."""
    for dan in (2, 3):
        _vozba(conn, "t1", _pred(dan), [(3, 3000)])
    conn.commit()
    assert stats.network_stats(conn, network="zeleznica") == []


def test_ure_so_po_postanku_ne_po_odhodu(conn):
    """`by_stop_hour` steje zamudo pri URI POSTANKA, ne uri odhoda vozjne.

    Vlak t1 odpelje ob 08:00 (28 800 s) in ima drugi postanek ob 09:00
    (32 400) ter tretjega ob 10:00 (36 000). Zamuda na zadnjem mora pasti v
    deseto uro, ne v osmo -- sicer bi jo stran pripisala uri, ko na omrezju
    se ni bilo nic narobe.
    """
    # Dvanajst dni, ker ima razrez prag `MIN_RUNS_FOR_GROUP` (10 postankov).
    for dan in range(2, 14):
        _vozba(conn, "t1", _pred(dan), [(2, 60), (3, 1800)])
    conn.commit()
    razrez = stats.breakdowns(conn, 90, "zeleznica")["by_stop_hour"]
    po_urah = {v["key"]: v["median_s"] for v in razrez}
    assert po_urah.get("10") == 1800, po_urah
    assert po_urah.get("09") == 60, po_urah
    assert "08" not in po_urah      # prvi postanek ni bil zajet


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
    from kajros import api

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

    Merjeno (`kajros backtest --operator`): prevoznikova napoved naprej ima
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


def test_povzetek_stare_oblike_se_ne_postreze(conn):
    """Stara OBLIKA je enako neuporabna kot star podatek, le tišja.

    Ko `breakdowns()` dobi novo polje, ga zapis v `povzetek` še nima. Brez te
    varovalke bi ga predpomnilnik do 36 ur stregel naprej, stran bi polje
    izpustila in videti bi bilo, kot da sprememba ne dela. Točno to se je
    zgodilo pri `median_s` (4. 9. 2026).
    """
    _vozba(conn, "t1", _pred(2), [(3, 120)])
    conn.commit()
    prvi = stats.summary_get(conn, "breakdowns", "zeleznica", 90)
    assert prvi["cached"] is False

    # Isti zapis, samo s starejšo oznako oblike -- čas ostane svež.
    star = json.loads(conn.execute(
        "SELECT payload FROM povzetek WHERE kind='breakdowns'").fetchone()[0])
    star["v"] = stats.SUMMARY_VERSION - 1
    star.pop("median_s", None)
    conn.execute("UPDATE povzetek SET payload = ? WHERE kind='breakdowns'",
                 (json.dumps(star),))
    conn.commit()

    znova = stats.summary_get(conn, "breakdowns", "zeleznica", 90)
    assert znova["cached"] is False, "stara oblika se ne sme postreči"
    assert znova["v"] == stats.SUMMARY_VERSION
    assert znova["median_s"] is not None


def test_razrezi_nosijo_sidro_cez_vse_voznje(conn):
    """Lestvica je urejena padajoče, zato njena prva vrstica ni tipična.

    Brez mediane čez vse vožnje se `EC 211 · 46 min` bere kot opis omrežja,
    čeprav je mediana vseh železniških voženj 3 min.
    """
    # Vozjne v testni bazi so t1..t4; `t0` ne obstaja in bi ga JOIN vrgel ven.
    for trip, dan, zamuda in [("t1", 3, 60), ("t2", 2, 120), ("t3", 1, 3000)]:
        _vozba(conn, trip, _pred(dan), [(2, zamuda)])
    conn.commit()
    d = stats.breakdowns(conn, 90, "zeleznica")
    assert d["runs"] == 3
    assert d["median_s"] == 120           # ne 3000 in ne 60
    assert d["on_time_share"] == round(2 / 3, 3)


def test_razred_zamude_gre_po_zaokrozeni_minuti(conn):
    """Razred mora slediti izpisani minuti, ne sekundam.

    `common.delayLabel()` izpiše `Math.round(s/60)`, zato mora razred pri
    30 s že biti „1–5 min“ — sicer je vrstica siva in piše „+1“. Meja je bila
    sekundna (`v <= 60`) in v režo 30–60 s pade 3 280 od 45 015 voženj
    (7,29 %). `floor(x+0.5)` in ne `round()`: Pythonov `round(0.5)` je 0,
    JS `Math.round(0.5)` pa 1.
    """
    assert stats._razred_zamude(29) == "točno"
    assert stats._razred_zamude(30) == "1–5 min"      # prej "točno"
    assert stats._razred_zamude(60) == "1–5 min"      # prej "točno"
    assert stats._razred_zamude(300) == "1–5 min"     # 5 min je še "1–5"
    assert stats._razred_zamude(330) == "5–15 min"    # 6 min
    assert stats._razred_zamude(900) == "5–15 min"    # 15 min je še "5–15"
    assert stats._razred_zamude(930) == "nad 15 min"  # 16 min


def test_delez_tocnih_se_ujame_z_vsoto_razredov(conn):
    """Kar stoji v istem okvirju, mora dati isto vsoto.

    `on_time_share` je meril `<= 300 s`, razred „1–5 min“ pa sega do
    zaokroženih pet minut (330 s). V to režo je padlo 553 od 45 043 voženj
    (1,23 %): bile so v razredu, a ne med točnimi, in bralec, ki sešteje
    „točno“ in „1–5 min“, ni dobil izpisanega odstotka.
    """
    assert stats.ON_TIME_MIN == 5
    # 310 s je zaokrozeno 5 min -> v razredu "1-5 min" IN med tocnimi.
    for trip, zamuda in (("t1", 290), ("t2", 310), ("t3", 400)):
        _vozba(conn, trip, _pred(2), [(2, zamuda)])
    conn.commit()
    d = stats.breakdowns(conn, 90, "zeleznica")
    razredi = stats._bucket_counts([290, 310, 400])
    v_pragu = razredi["točno"] + razredi["1–5 min"]
    assert v_pragu == 2
    assert d["on_time_share"] == round(v_pragu / 3, 3)


# ------------------------------------------------------- prilivanje iz druge baze

def test_merge_prinese_tudi_voznje_z_meritvami(tmp_path, conn):
    """Meritev brez svoje vožnje je nevidna, ne izgubljena — a to je isto.

    Vsaka poizvedba gre skozi `JOIN trip`, ker je omrežje tam. Če prilitje
    prinese `run`, njegove vožnje pa ne, teh meritev od tedaj ne vidi nihče
    in nihče tega ne opazi. Tako je nastalo 114 osirotelih voženj s 3 043
    meritvami (4. 9. 2026): uvoz novega voznega reda jih je izbrisal iz
    `trip`, prilitje z maline pa je vrnilo samo meritve.
    """
    vir = tmp_path / "vir.sqlite"
    v = db.connect(vir)
    db.init(v)
    v.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              " mode, network) VALUES('tX','rX','LP 9','A - B','S1','vlak','zeleznica')")
    v.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
              " feed_ts) VALUES('tX', ?, 2, 120, 120, 999)", (_pred(1),))
    # Vožnja BREZ meritev se ne sme priliti -- sicer bi vlekli cel star vozni red.
    v.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              " mode, network) VALUES('tPrazna','rX','LP 8','A - B','S1','vlak','zeleznica')")
    v.commit()
    v.close()

    db.merge_from(conn, vir)

    assert conn.execute("SELECT COUNT(*) FROM trip WHERE trip_id='tX'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM trip WHERE trip_id='tPrazna'").fetchone()[0] == 0
    sirote = conn.execute("SELECT COUNT(*) FROM run r LEFT JOIN trip t USING(trip_id)"
                          " WHERE t.trip_id IS NULL").fetchone()[0]
    assert sirote == 0


def test_merge_ne_povozi_novejsega_voznega_reda(tmp_path, conn):
    """Kar že imamo, je iz novejšega voznega reda in ostane.

    `INSERT OR IGNORE`, ne `REPLACE`: sicer bi prilitje s stroja s starejšim
    voznim redom vrnilo stara imena in omrežja.
    """
    vir = tmp_path / "vir.sqlite"
    v = db.connect(vir)
    db.init(v)
    v.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              " mode, network) VALUES('t1','staro','STARO IME','X','S1','vlak','avtobus')")
    v.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
              " feed_ts) VALUES('t1', ?, 2, 60, 60, 999)", (_pred(1),))
    v.commit()
    v.close()

    db.merge_from(conn, vir)
    r = conn.execute("SELECT train_no, network FROM trip WHERE trip_id='t1'").fetchone()
    assert r["train_no"] == "IC 1" and r["network"] == "zeleznica"


def test_seme_ne_prilaga_meritev(tmp_path, conn):
    """Seme je vozni red, ne zajem.

    Seznam praznjenih tabel je bil ročen in je zaostal: seme je prilagalo
    `napoved` (5,4 MB sence meritev) in `povzetek`, ker sta tabeli nastali
    kasneje. Zdaj se izprazni vse, kar ni v `STATIC_TABLES`.
    """
    ocena.init(conn)          # `napoved` nastane tu, ne v `db.init()`
    _vozba(conn, "t1", _pred(1), [(2, 120)])
    conn.execute("INSERT INTO napoved(trip_id, service_date, stop_seq, network,"
                 " made_ts, horizon_s, from_seq, ours_s)"
                 " VALUES('t1', ?, 2, 'zeleznica', 1, 1500, 1, 60)", (_pred(1),))
    conn.execute("INSERT INTO meta(key, value) VALUES('rt_fetched','123')")
    conn.execute("INSERT INTO meta(key, value) VALUES('rt_etag','abc')")
    conn.commit()

    cilj = tmp_path / "seme.sqlite"
    db.build_seed(conn, cilj)

    s = db.connect(cilj)
    assert s.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
    assert s.execute("SELECT COUNT(*) FROM napoved").fetchone()[0] == 0
    assert s.execute("SELECT COUNT(*) FROM obs").fetchone()[0] == 0
    # Vozni red mora ostati.
    assert s.execute("SELECT COUNT(*) FROM trip").fetchone()[0] > 0
    # Stanje tega stroja ne sme z njim.
    kljuci = {r[0] for r in s.execute("SELECT key FROM meta")}
    assert "rt_fetched" not in kljuci and "rt_etag" not in kljuci


def test_seme_privzeto_le_zeleznica(tmp_path, conn):
    """Z avtobusi je seme 53 MB — več od GTFS zipa (41 MB), ki bi ga
    namestitev sicer prenesla. Seme, dražje od tega, čemur se izogiba, nima
    smisla."""
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign,"
                 " service_id, mode, network)"
                 " VALUES('bus1','r','3G','A - B','S1','bus','avtobus')")
    conn.commit()
    cilj = tmp_path / "seme.sqlite"
    db.build_seed(conn, cilj)
    s = db.connect(cilj)
    assert s.execute("SELECT COUNT(*) FROM trip WHERE network='avtobus'").fetchone()[0] == 0
    assert s.execute("SELECT COUNT(*) FROM trip WHERE network='zeleznica'").fetchone()[0] > 0


def test_vse_poti_odgovarjajo_na_head():
    """HEAD je prva stvar, ki jo posljejo nadzorniki dosegljivosti.

    FastAPIjev `APIRoute` ob GET ne doda HEAD (Starlettov `Route` ga), zato so
    vse poti vracale 405. Javno je to videti kot "stran ne dela".
    """
    from fastapi.routing import APIRoute
    from kajros.api import app

    brez = [r.path for r in app.routes
            if isinstance(r, APIRoute) and "HEAD" not in r.methods]
    assert brez == [], f"poti brez HEAD: {brez}"


def test_head_ni_v_dokumentaciji():
    """34 vnosov "isto kot GET, brez telesa" je samo dvakrat daljsi seznam."""
    from kajros.api import app

    app.openapi_schema = None
    shema = app.openapi()
    z_head = [p for p, o in shema["paths"].items() if "head" in o]
    assert z_head == [], f"HEAD v shemi: {z_head}"


def test_mestni_in_primestni_lpp_nista_ista_skupina(conn):
    """Dve agenciji, dve skupini — tudi ko na avtobusu piše isto.

    Mestni LPP pride iz drugega vira (`agency = 'lpp'`, glej `config.LPP_*`),
    primestni iz IJPP (`1118`). Dokler sta se preslikala v isto ime, je bila
    v razrezu ena vrstica za dve različni storitvi.
    """
    _add_bus(conn)          # agencija 1118, linija 6B
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                 "                 mode, agency, network) "
                 "VALUES('m1','rm','6','ZALOG - BEŽIGRAD','S1','bus','lpp','avtobus')")
    _sched(conn, "m1", [(1, "A", None, 35000), (2, "C", 39000, None)])
    for trip in ("b1", "m1"):
        for i in range(10):
            conn.execute("INSERT INTO run(trip_id, service_date, stop_seq,"
                         "                delay_arr, delay_dep, feed_ts) "
                         "VALUES(?,?,2,120,120,1)", (trip, _pred(i + 1)))
    conn.commit()

    kljuci = {r["key"] for r in stats.breakdowns(conn, network="avtobus")["by_kind"]}
    assert kljuci == {"LPP primestni", "LPP mestni"}


def test_obvestila_lpp_se_zdruzijo_po_besedilu(conn):
    """Feed pošlje isto obvestilo na vsako vožnjo, ne na dogodek.

    Izmerjeno 7. 9. 2026: 181 obvestil, od tega dve različni — „Postaja
    Čerinova na obvozu" (147 voženj) in „Postaja Tbilisijska" (34). Brez
    združevanja bi stran pokazala isto poved stokrat.
    """
    from google.transit import gtfs_realtime_pb2 as rt
    from kajros import alerts

    feed = rt.FeedMessage()
    for i in range(5):
        e = feed.entity.add()
        e.id = f"nakljucen-uuid-{i}"
        a = e.alert
        t = a.header_text.translation.add(); t.language = "sl"
        t.text = "Postaja Čerinova na obvozu"
        d = a.description_text.translation.add(); d.language = "sl"
        d.text = "Vozilo se ne bo ustavilo na postaji"
        ie = a.informed_entity.add()
        # Dve različni postajališči istega imena (mestno jih ima po eno na smer)
        ie.stop_id = "S1" if i % 2 else "S2"

    izid = alerts.ingest_lpp(conn, feed)
    assert izid["obvestil"] == 1          # pet vrstic, eno obvestilo
    assert izid["iz_vrstic"] == 5

    vrstice = conn.execute("SELECT alert_id, kind FROM alert WHERE kind='obvoz'").fetchall()
    assert len(vrstice) == 1
    aid = vrstice[0]["alert_id"]
    # Obe postajališči morata biti zapisani. `route_id` in `trip_id` sta
    # NOT NULL DEFAULT '' -- z NULL je vstavljanje tiho padlo in obvestilo je
    # ostalo brez postajališč.
    stops = {r["stop_id"] for r in conn.execute(
        "SELECT stop_id FROM alert_entity WHERE alert_id = ?", (aid,))}
    assert stops == {"S1", "S2"}
    assert [a["header"] for a in alerts.for_stops(conn, ["S1"])] == ["Postaja Čerinova na obvozu"]
    assert alerts.for_stops(conn, ["S9"]) == []


def test_izhodisce_dobi_obicajno_zamudo_naslednje_postaje():
    # Feed prvega postanka ne poroca nikoli (0 od 716 voznj), zato bi tam
    # ostal "?" tudi po devetnajstih zajetih vozjnah. Prepis je dovoljen samo
    # z oznako, od kod je -- brez nje bi prikaz trdil meritev, ki je ni bilo.
    rows = [{"stop_seq": 1, "name": "Ljubljana", "typical": None},
            {"stop_seq": 2, "name": "Ljubljana Polje",
             "typical": {"n": 16, "median_s": 60.0}}]
    stats.typical_na_izhodisce(rows)
    assert rows[0]["typical"]["median_s"] == 60.0
    assert rows[0]["typical"]["od_ime"] == "Ljubljana Polje"
    assert "od_seq" not in rows[1]["typical"]


def test_prepis_na_izhodisce_ne_preskoci_sredine():
    # Vrzel sredi proge ni izhodisce: tam meritev MANJKA, kar je drugacna
    # novica od "feed je ne posilja". Prepis sme zapolniti samo zacetek.
    rows = [{"stop_seq": 1, "name": "A", "typical": {"n": 9, "median_s": 0.0}},
            {"stop_seq": 2, "name": "B", "typical": None},
            {"stop_seq": 3, "name": "C", "typical": {"n": 9, "median_s": 120.0}}]
    stats.typical_na_izhodisce(rows)
    assert rows[1]["typical"] is None


def test_neskladna_ura_je_oznacena_ne_meritev():
    # Vozilo ne more priti na postajo, preden je odpeljalo s prejšnje.
    # Tretji postanek trdi 09:50, čeprav sta soseda ob 10:40 in 11:00 -- to
    # je nepotrjena napoved, ki je ostala v `run`, ne meritev. Mora biti pod
    # OBEMA sosedoma, sicer sta verigi enako dolgi in izbira je poljubna.
    rows = [{"dep_s": 36000, "delay_dep": 0},        # 10:00
            {"dep_s": 36600, "delay_dep": 1800},     # 10:40
            {"dep_s": 37200, "delay_dep": -1800},    # 09:50  <- nasprotuje
            {"dep_s": 37800, "delay_dep": 1800},     # 11:00
            {"dep_s": 38400, "delay_dep": 1800}]     # 11:10
    stats.oznaci_neskladne(rows)
    assert [r.get("neskladno") for r in rows] == [None, None, True, None, None]


def test_neskladnost_obdrzi_daljso_verigo_in_ne_prve():
    # Kadar se feed za nazaj popravi, je napačen ZAČETEK, ne konec: pravilo
    # mora obdržati daljše zaporedje, ne prvega. Sicer bi ena smet na drugem
    # postanku pobrisala vso ostalo vožnjo.
    rows = ([{"dep_s": 0, "delay_dep": 7200}, {"dep_s": 60, "delay_dep": 7200}]
            + [{"dep_s": 120 + 60 * i, "delay_dep": 0} for i in range(8)])
    stats.oznaci_neskladne(rows)
    assert [bool(r.get("neskladno")) for r in rows] == [True, True] + [False] * 8


def test_skok_pod_minuto_ni_neskladje():
    # 20 sekund nazaj ni nemogoč vozni red, ampak zaokroževanje: prikaz kaže
    # minute. Brez tega bi pravilo lovilo lastno natančnost -- pri mestnem
    # LPP bi zadelo 38 % voženj namesto 17 %.
    rows = [{"dep_s": 36000, "delay_dep": 40},
            {"dep_s": 36020, "delay_dep": 0}]
    stats.oznaci_neskladne(rows)
    assert all(r.get("neskladno") is None for r in rows)


def test_postanek_brez_meritve_ne_pretrga_verige():
    # Postanek, o katerem feed ni povedal nič, ni neskladen -- in ne sme
    # pretrgati zaporedja okoli sebe.
    rows = [{"dep_s": 36000, "delay_dep": 0},
            {"dep_s": 36600, "delay_dep": None, "delay_arr": None},
            {"dep_s": 37200, "delay_dep": 0}]
    stats.oznaci_neskladne(rows)
    assert all(r.get("neskladno") is None for r in rows)


def test_sumljiv_a_skladen_postanek_se_obdrzi():
    # Postanek, ki ga feed po nekem trenutku ni več osvežil, je sumljiv --
    # ni pa to razlog, da bi vrgli stran vrednost, ki se z ostalimi ujema.
    rows = [{"dep_s": 36000, "delay_dep": 0, "feed_ts": 900},
            {"dep_s": 36600, "delay_dep": 0, "feed_ts": 300},   # star zapis
            {"dep_s": 37200, "delay_dep": 0, "feed_ts": 1200}]
    stats.oznaci_neskladne(rows)
    assert all(r.get("neskladno") is None for r in rows)


def test_sumljiva_luknja_ne_prevlada_ene_prave_vrednosti():
    # RG 310: Litostroj +29 min, nato dve ničli (Stegne, Vižmarje), ki ju
    # feed ni več osvežil, nato spet +22. Štetje samih postankov bi zavrglo
    # Litostroj, ker sta ničli dve -- teža ju razkrije kot ostanek.
    rows = [{"dep_s": 63120, "delay_dep": 1740, "feed_ts": 1000},   # 18:01
            {"dep_s": 63300, "delay_dep": 0, "feed_ts": 100},       # 17:35 ostanek
            {"dep_s": 63480, "delay_dep": 0, "feed_ts": 200},       # 17:38 ostanek
            {"dep_s": 63660, "delay_dep": 1320, "feed_ts": 1100},   # 18:03
            {"dep_s": 63900, "delay_dep": 1320, "feed_ts": 1200}]   # 18:07
    stats.oznaci_neskladne(rows)
    assert [bool(r.get("neskladno")) for r in rows] == [False, True, True, False, False]


def test_tabla_ne_kaze_nemogoce_meritve(conn):
    # IC 1 vozi A (08:00) -> Z (odhod 09:05) -> C (10:00). Za Zidani Most je
    # v `run` ostala nepotrjena +80 min, torej odhod ob 10:25, za Celje pa
    # izmerjenih +5 min, torej prihod ob 10:05. Vozilo bi moralo odpeljati iz
    # Zidanega Mosta, PREDEN je prišlo v Celje -- ena od vrednosti ni meritev.
    #
    # Tabla vidi en sam postanek in celotne verige ne zmore (to dela
    # `stats.oznaci_neskladne()`), zmore pa to primerjavo: raje pove zadnjo
    # znano zamudo in od kod je, kot da bi trdila nemogoče.
    for seq, d in ((2, 4800), (3, 300)):
        conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, "
                     "delay_dep, feed_ts) VALUES('t1','2026-08-31',?,?,?,1)", (seq, d, d))
    conn.commit()
    row = next(r for r in journey.board(conn, "Zidani Most", "2026-08-31", 0, 1440,
                                        now_s=40000) if r["train_no"] == "IC 1")
    assert row["delay_kind"] == "izmerjeno"
    assert row["delay_s"] == 300
    assert row["delay_from"] == "Celje"


def test_nicev_tocni_zadetek_ne_prehiti_prometne_postaje(conn):
    """Šumniki se pri iskanju zlijejo, promet pa ne sme izginiti.

    Prava napaka, izmerjena 7. 9. 2026: „celje" je na avtobusnem omrežju
    vrnilo vas **Čelje** z dvema postankoma v vsem voznem redu pred
    „Celje AP" s 1014 — in `resolve_station()` je iskalniku zvez tiho podtaknil
    kraj 112 km stran. Točno ime ostane vidno, prvo mesto pa dobi promet.
    """
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('CV','Čelje',45.6,14.2)")
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('CA','Celje AP',46.2,15.3)")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('tc','rc','N1','vas','S1')")
    _sched(conn, "tc", [(1, "CV", None, 20000), (2, "A", 21000, None)])
    # Celje AP je stokrat bolj prometno: ena vožnja proti stotim.
    for i in range(100):
        conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                     f"VALUES('ta{i}','ra','N2','mesto','S1')")
        _sched(conn, f"ta{i}", [(1, "CA", None, 20000 + i), (2, "A", 21000 + i, None)])
    conn.commit()
    imena = [s["name"] for s in journey.search_stations(conn, "celje", 8)]
    assert imena[0] == "Celje AP"
    assert "Čelje" in imena, "točnega zadetka ni dovoljeno skriti"
    # Tako, kot človek vtipka -- brez velike začetnice in brez šumnika.
    assert journey.resolve_station(conn, "celje") == "Celje AP"


def test_tocno_ime_s_podobnim_prometom_ostane_prvo(conn):
    # Pravilo velja samo za nicev promet. Postaja, ki je le nekajkrat manj
    # prometna od soseda, mora ostati prva -- sicer bi „Boršt" izgubil proti
    # „Boršt/Krki K", ki je isti kraj.
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('B1','Boršt',45.8,13.9)")
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('B2','Boršt/Krki K',45.8,13.9)")
    for i in range(3):
        conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                     f"VALUES('tb{i}','rb','N3','x','S1')")
        _sched(conn, f"tb{i}", [(1, "B1", None, 20000 + i), (2, "A", 21000 + i, None)])
    for i in range(9):
        conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                     f"VALUES('tk{i}','rk','N4','x','S1')")
        _sched(conn, f"tk{i}", [(1, "B2", None, 22000 + i), (2, "A", 23000 + i, None)])
    conn.commit()
    assert [s["name"] for s in journey.search_stations(conn, "borst", 5)][0] == "Boršt"


def test_tabla_zjutraj_vidi_vceraj_zacet_promet(conn):
    """Vožnja, ki je odpeljala pred polnočjo, pripada VČERAJŠNJEMU dnevu.

    Prava napaka, izmerjena 7. 9. 2026: tabla ob 00:30 je na Laškem kazala
    šele vlak ob 01:58, medtem ko je LPV 2007 pripeljal ob 00:56 — pripadal
    je prometnemu dnevu prej in ga poizvedba ni videla. Čez polnoč sega 10
    železniških in 154 avtobusnih voženj, najdlje do 33:48.
    """
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('tn','rn','EN 99','A - C','S1')")
    # odhod ob 23:40, prihod v Celje ob 00:56 NASLEDNJEGA dne (24:56)
    _sched(conn, "tn", [(1, "A", None, 85200), (2, "C", 89760, None)])
    conn.commit()

    # 1. 9. ob 00:30 -- vlak je še na poti in pride čez 26 minut.
    vrstice = journey.board(conn, "Celje", "2026-09-01", 20 * 60, 180,
                            kind="prihodi", now_s=30 * 60)
    assert any(r["train_no"] == "EN 99" for r in vrstice)
    r = next(r for r in vrstice if r["train_no"] == "EN 99")
    assert r["sched"].startswith("2026-09-01T00:56"), r["sched"]

    # Podnevi te poizvedbe ni: ob 17:00 včerajšnjega dneva ne gledamo.
    dnevna = journey.board(conn, "Celje", "2026-09-01", 17 * 3600, 180,
                           kind="prihodi", now_s=17 * 3600)
    assert all(r["train_no"] != "EN 99" for r in dnevna)


def test_iskalnik_zjutraj_vidi_nocno_zvezo(conn):
    """Nočna vožnja pripada VČERAJŠNJEMU prometnemu dnevu — tudi v iskalniku.

    Ista napaka kot pri tabli: vstopnih postankov med polnočjo in tretjo uro
    je 2 145 (avtobusi) in 41 (vlaki), ponoči pa so pogosto edini.
    """
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
                 "VALUES('tnc','rnc','EN 98','A - C','S1')")
    # Ajdovščina ob 24:34, Celje ob 25:10 -- torej 00:34 in 01:10 naslednjega dne.
    _sched(conn, "tnc", [(1, "A", None, 88440), (2, "C", 90600, None)])
    conn.commit()

    zjutraj = stats.connections(conn, "Ajdovščina", "Celje", "2026-09-01", 30 * 60)
    nocne = [c for c in zjutraj if c["train_no"] == "EN 98"]
    assert nocne, "nočne zveze iskalnik ne sme skriti"
    assert nocne[0]["sched_dep"].startswith("2026-09-01T00:34"), nocne[0]["sched_dep"]

    # Podnevi te poizvedbe ni -- včerajšnji dan takrat ne pripada vprašanju.
    podnevi = stats.connections(conn, "Ajdovščina", "Celje", "2026-09-01", 17 * 3600)
    assert all(c["train_no"] != "EN 98" for c in podnevi)


def test_znano_do_loci_vire(conn):
    """Viri segajo različno daleč in prikaz mora to vedeti.

    Izmerjeno 7. 9. 2026: železnica do 12. 12., IJPP avtobusi do 31. 12. 2027,
    mestni LPP do 15. 9. — ker se uvaža okno osmih dni. Prazen odgovor čez to
    mejo ni „ta dan nič ne vozi", ampak „voznega reda še ni".
    """
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S2','2026-12-24')")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, "
                 "network, agency) VALUES('tz','rz','LP 9','A - C','S2','zeleznica','SZ')")
    _sched(conn, "tz", [(1, "A", None, 30000), (2, "C", 33000, None)])
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S3','2026-09-15')")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, "
                 "network, agency) VALUES('tl','rl','3','A - C','S3','avtobus','lpp')")
    _sched(conn, "tl", [(1, "A", None, 30000), (2, "C", 33000, None)])
    conn.commit()

    assert stats.znano_do(conn, "zeleznica") == "2026-12-24"
    assert stats.znano_do(conn, agency="lpp") == "2026-09-15"
    # Brez omejitve je meja najdaljša od vseh.
    assert stats.znano_do(conn) == "2026-12-24"


# ---------------------------------------------------------------- živi LPP

def _lpp_voznja(conn):
    """Mestna vožnja s štirimi postajami, kot jo pozna naša baza."""
    conn.executemany(
        "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
        [("L1", "Zalog", 46.0628, 14.6033),
         ("L2", "Silos", 46.0640, 14.5900),
         ("L3", "Polje", 46.0650, 14.5800),
         ("L4", "Nove Fužine", 46.0660, 14.5700)])
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, "
                 "                 agency, network, mode) "
                 "VALUES('a|b|c','rl','11','ZALOG - VIŽMARJE','S1','lpp','avtobus','bus')")
    _sched(conn, "a|b|c", [(1, "L1", None, 20000), (2, "L2", 20300, 20300),
                           (3, "L3", 20600, 20600), (4, "L4", 20900, None)])
    conn.commit()


def _odgovor_lpp(vozilo="V1"):
    """Odgovor `arrivals-on-route`, kakršnega vrne data.lpp.si."""
    return [
        {"name": "ZALOG", "latitude": 46.0628, "longitude": 14.6033,
         "arrivals": [{"vehicle_id": vozilo, "eta_min": 1}]},
        {"name": "Silos", "latitude": 46.0640, "longitude": 14.5900,
         "arrivals": [{"vehicle_id": vozilo, "eta_min": 4},
                      {"vehicle_id": "TUJ", "eta_min": 12}]},
        {"name": "Polje", "latitude": 46.0650, "longitude": 14.5800,
         "arrivals": [{"vehicle_id": "TUJ", "eta_min": 15}]},
        {"name": "Nove Fužine", "latitude": 46.0660, "longitude": 14.5700,
         "arrivals": [{"vehicle_id": vozilo, "eta_min": 9}]},
    ]


def test_zivi_lpp_spoji_postanke_po_koordinati(conn, monkeypatch):
    """Postanki se spajajo po legi, ne po vrstnem redu.

    Njihov `trip-id` je **vzorec proge**, ne vožnja (19 163 naših voženj ima
    85 različnih tretjih komponent), zato je lahko daljši od naše vožnje --
    in vrstni red bi takrat vse postanke tiho zamaknil.
    """
    from kajros import lpp
    _lpp_voznja(conn)
    monkeypatch.setattr(lpp, "_prinesi", lambda vzorec: _odgovor_lpp())
    assert lpp.eta_po_postankih(conn, "a|b|c", "V1") == {1: 1, 2: 4, 4: 9}


def test_zivi_lpp_prezre_tuje_vozilo(conn, monkeypatch):
    """Postanek, kjer je napovedan samo TUJ avtobus, ne sme pripasti nam.

    `arrivals-on-route` našteje prihode vseh vozil na vzorcu; brez izbire po
    `vehicle_id` bi na zaslon prišla ura naslednjega avtobusa iste linije.
    """
    from kajros import lpp
    _lpp_voznja(conn)
    monkeypatch.setattr(lpp, "_prinesi", lambda vzorec: _odgovor_lpp())
    izid = lpp.eta_po_postankih(conn, "a|b|c", "V1")
    assert 3 not in izid


def test_zivi_lpp_brez_vozila_molci(conn, monkeypatch):
    """Brez sveže lege ne vemo, katero vozilo je naše -- takrat nič."""
    from kajros import lpp
    _lpp_voznja(conn)
    monkeypatch.setattr(lpp, "_prinesi", lambda vzorec: _odgovor_lpp())
    assert lpp.eta_po_postankih(conn, "a|b|c", None) is None


def test_zivi_lpp_ob_izpadu_vira_molci(conn, monkeypatch):
    """Vir je postranski: ko pade, stran še vedno stoji na derp.si."""
    from kajros import lpp
    _lpp_voznja(conn)
    monkeypatch.setattr(lpp, "_prinesi", lambda vzorec: None)
    assert lpp.eta_po_postankih(conn, "a|b|c", "V1") is None


def test_zivi_lpp_vzorec_je_tretja_komponenta():
    """Njihov `trip-id` je tretji del našega trojnega id-ja; drugod ga ni."""
    from kajros import lpp
    assert lpp._vzorec("a|b|c") == "c"
    assert lpp._vzorec("navaden_id") is None


# ---------------------------------------------------------------- predpomnilnik

def test_predpomnilnik_v_ozadju_postrezi_staro_in_osvezi():
    """Predrag izračun se ne sme zgoditi v zahtevi obiskovalca.

    Izmerjeno 8. 9. 2026: števci `/api/health` so po prilitju stali 932 ms
    (`COUNT(*) obs`) in 1 452 ms (razrez po omrežjih) s toplim predpomnilnikom,
    ob hladnem pa je bil odziv 13 s. Po izteku mora klic vrniti **staro**
    vrednost takoj, novo pa izračunati v niti.
    """
    import time as _t
    from kajros import api

    klici = []

    def izracun():
        klici.append(1)
        return f"vrednost-{len(klici)}"

    kljuc = "test-v-ozadju"
    api._ODGOVORI.pop(kljuc, None)

    # prvi klic nima cesa postreci -- izracuna sinhrono
    assert api._predpomni(kljuc, None, 0.05, izracun, v_ozadju=True) == "vrednost-1"
    _t.sleep(0.1)                                   # predpomnilnik je potekel

    # drugi klic vrne STARO vrednost, novo pa izracuna v ozadju
    assert api._predpomni(kljuc, None, 0.05, izracun, v_ozadju=True) == "vrednost-1"
    for _ in range(50):                             # pocakaj na nit
        if len(klici) > 1:
            break
        _t.sleep(0.02)
    assert len(klici) == 2, "osvežitev v ozadju se ni zgodila"
    assert api._ODGOVORI[kljuc][1] == "vrednost-2"


def test_predpomnilnik_brez_ozadja_ostane_sinhron():
    """Privzeto vedenje se ne sme spremeniti: brez zastavice je izračun v zahtevi."""
    from kajros import api
    klici = []
    kljuc = "test-sinhroni"
    api._ODGOVORI.pop(kljuc, None)

    def izracun():
        klici.append(1)
        return len(klici)

    assert api._predpomni(kljuc, None, 0, izracun) == 1
    assert api._predpomni(kljuc, None, 0, izracun) == 2   # takoj potekel, znova


def test_okno_lpp_vkljuci_vcerajsnji_dan(tmp_path):
    """Nočni avtobus ob 01:00 nosi VČERAJŠNJI prometni dan.

    Pri LPP je dan zapisan v `trip_id` (prva komponenta trojnega id-ja), zato
    vožnja, ki je v bazi ni, tiho odpade — `poll_lpp` vrne `trips: 0` in to je
    videti, kot da ponoči nič ne vozi. Ujeto na malini 8. 9. 2026: uvoz ob
    00:15 je postavil okno od 8. 9., feed ob 01:10 pa je govoril o 7. 9.
    """
    import zipfile
    from kajros import gtfs

    z = tmp_path / "lpp.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("calendar_dates.txt",
                    "service_id,date,exception_type\n"
                    "vceraj,20260907,1\n"
                    "danes,20260908,1\n"
                    "predvceraj,20260906,1\n")
        zf.writestr("routes.txt", "route_id,route_short_name,route_long_name,route_type\n"
                                  "r1,11,ZALOG - VIZMARJE,3\n")
        zf.writestr("trips.txt", "trip_id,route_id,service_id,trip_headsign,direction_id\n"
                                 "a|b|vceraj,r1,vceraj,VIZMARJE,0\n"
                                 "a|b|danes,r1,danes,VIZMARJE,0\n"
                                 "a|b|predvceraj,r1,predvceraj,VIZMARJE,0\n")
        zf.writestr("stop_times.txt",
                    "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
                    "a|b|vceraj,1,S1,23:50:00,23:50:00\n"
                    "a|b|danes,1,S1,08:00:00,08:00:00\n"
                    "a|b|predvceraj,1,S1,08:00:00,08:00:00\n")
        zf.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\n"
                                 "S1,Zalog,46.06,14.60\n")

    izid = gtfs.beri_lpp(z, dni=8, danes="2026-09-08")
    assert "a|b|danes" in izid["trips"], "današnjega dne ni v oknu"
    assert "a|b|vceraj" in izid["trips"], "včerajšnjega dne ni v oknu — nočne vožnje bodo odpadle"
    assert "a|b|predvceraj" not in izid["trips"], "okno sega predaleč nazaj"
