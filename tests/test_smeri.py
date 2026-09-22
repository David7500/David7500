"""Strani ceste na avtobusnem postajaliscu (`journey.smeri_postaje`).

Mestno postajalisce ima svoj `stop_id` za vsako stran ceste in vsak vir
svojega, aplikacija pa gradi po imenu -- zato je tabla kazala obe strani
skupaj. Tu so primeri, ki jih pravilo mora locevati: dve strani iste ceste,
isti rob iz dveh virov, postajalisce, kjer se voznje samo koncajo, in kraj
z istim imenom drugje po drzavi.
"""
from __future__ import annotations

import pytest

from kajros import db, journey


def _voznja(c, trip_id, stops, dep_s=30000):
    """stops: zaporedje `stop_id`; vsak postanek minuto za prejsnjim."""
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
              "                 mode, agency, network) "
              "VALUES(?, 'r', '6', 'A - B', 'S1', 'bus', 'lpp', 'avtobus')", (trip_id,))
    c.executemany(
        "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
        [(trip_id, i + 1, sid, dep_s + i * 60, dep_s + i * 60) for i, sid in enumerate(stops)])


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)", [
        # dve strani iste ceste, 15 m narazen: ena pelje proti vzhodu, druga
        # proti zahodu
        ("H1", "Hajdrihova", 46.04570, 14.49050),
        ("H2", "Hajdrihova", 46.04583, 14.49045),
        # isti rob kot H1, a iz drugega vira in z drugim imenom naslednje
        ("H3", "Hajdrihova", 46.04575, 14.49060),
        # tu se voznje samo koncajo
        ("H4", "Hajdrihova", 46.04585, 14.49040),
        # kraj z istim imenom drugje
        ("H5", "Hajdrihova", 45.50000, 15.00000),
        ("T", "Tobačna", 46.04570, 14.49500),
        ("T2", "Ljubljana Tobačna", 46.04575, 14.49510),
        ("V", "Vič Glince", 46.04583, 14.48500),
        ("X", "Drugje", 45.50000, 15.01000),
        # zanka: obe smeri imata isto naslednjo postajo
        ("Z1", "Zanka", 46.10000, 14.50000),
        ("Z2", "Zanka", 46.10000, 14.50030),
        ("O1", "Obračališče", 46.10100, 14.50000),
        ("O2", "Obračališče", 46.09900, 14.50030),
    ])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', '2026-09-22')")
    for i in range(3):
        _voznja(c, f"vzhod{i}", ["H1", "T"], 30000 + i * 600)
    _voznja(c, "vzhod-ijpp", ["H3", "T2"], 30300)
    for i in range(2):
        _voznja(c, f"zahod{i}", ["H2", "V"], 30100 + i * 600)
    _voznja(c, "konec", ["V", "H4"], 30200)
    _voznja(c, "drugje", ["H5", "X"], 30400)
    _voznja(c, "zanka1", ["Z1", "O1"], 30000)
    _voznja(c, "zanka2", ["Z2", "O2"], 30000)
    db.fill_trip_window(c)
    c.commit()
    return c


def _po_kljucu(smeri):
    return {d["kljuc"]: d for d in smeri}


def test_strani_ceste_sta_dve_smeri(conn):
    smeri = _po_kljucu(journey.smeri_postaje(conn, "Hajdrihova"))
    assert smeri["H1"]["naslednje"] == ["Tobačna"]
    assert smeri["H2"]["naslednje"] == ["Vič Glince"]


def test_isti_rob_iz_dveh_virov_je_ena_smer(conn):
    """IJPP in LPP imata za isto stran svoje postajalisce in svoje ime
    naslednjega. Oznaka je z najprometnejsega -- sicer bi pisalo
    "Tobačna, Ljubljana Tobačna"."""
    h1 = _po_kljucu(journey.smeri_postaje(conn, "Hajdrihova"))["H1"]
    assert sorted(h1["stop_ids"]) == ["H1", "H3"]
    assert h1["odhodov"] == 4
    assert h1["naslednje"] == ["Tobačna"]


def test_koncno_postajalisce_gre_k_najblizji_smeri(conn):
    h2 = _po_kljucu(journey.smeri_postaje(conn, "Hajdrihova"))["H2"]
    assert sorted(h2["stop_ids"]) == ["H2", "H4"]


def test_isto_ime_drugje_je_svoja_smer(conn):
    smeri = journey.smeri_postaje(conn, "Hajdrihova")
    assert len(smeri) == 3
    assert _po_kljucu(smeri)["H5"]["naslednje"] == ["Drugje"]


def test_smeri_so_po_prometu(conn):
    assert [d["kljuc"] for d in journey.smeri_postaje(conn, "Hajdrihova")] == ["H1", "H2", "H5"]


def test_ista_naslednja_postaja_je_ena_izbira(conn):
    """Obe smeri pri zanki peljeta na isto postajo; dva enaka gumba bi bila
    uganka, ne izbira."""
    smeri = journey.smeri_postaje(conn, "Zanka")
    assert len(smeri) == 1
    assert sorted(smeri[0]["stop_ids"]) == ["Z1", "Z2"]


def test_kljuc_je_katerikoli_stop_id_smeri(conn):
    """Shranjen kljuc (widget) ne sme izgubiti smeri, ce ob uvozu prevlada
    drugo postajalisce iste strani."""
    smeri = journey.smeri_postaje(conn, "Hajdrihova")
    assert journey.smer_za(smeri, "H3")["kljuc"] == "H1"
    assert journey.smer_za(smeri, "neznan") is None
    assert journey.smer_za(smeri, None) is None


def test_tabla_s_smerjo_kaze_samo_to_stran(conn):
    vse = journey.board(conn, "Hajdrihova", "2026-09-22", 0, 1440, network="avtobus")
    assert {r["trip_id"] for r in vse} >= {"vzhod0", "zahod0"}
    h1 = journey.smer_za(journey.smeri_postaje(conn, "Hajdrihova"), "H1")
    ena = journey.board(conn, "Hajdrihova", "2026-09-22", 0, 1440, network="avtobus",
                        stop_ids=set(h1["stop_ids"]))
    assert {r["trip_id"] for r in ena} == {"vzhod0", "vzhod1", "vzhod2", "vzhod-ijpp"}
    assert {r["stop_id"] for r in ena} == {"H1", "H3"}
