"""Testi iskanja od vrat do vrat.

Hoja je tu **izračunana iz zračne razdalje**, ne iz usmerjevalnika: preverjamo
iskanje, ne OSRM. Vrednosti so zato predvidljive in test ne rabi vsebnika.
"""
from __future__ import annotations

import pytest

from kajros import db, geo, hoja, pot

D = "2026-09-08"

# Izhodišče in cilj sta 11 km narazen, torej hoje vso pot ni.
OD = (46.000, 14.500)
DO = (46.100, 14.500)


@pytest.fixture(autouse=True)
def hoja_po_zraku(monkeypatch):
    """Hoja = zračna razdalja pri 5 km/h, brez faktorja in brez omrežja."""
    def matrika(lat, lon, cilji, smer="od"):
        return ([round(geo.haversine(lat, lon, a, b) / hoja.HITROST_MS)
                 for a, b in cilji], hoja.OSRM)
    monkeypatch.setattr(hoja, "matrika", matrika)
    monkeypatch.setattr(pot.hoja, "matrika", matrika)
    hoja._PES_CACHE.clear()
    pot._VOZJE_CACHE.clear()
    pot._IMENA_CACHE.clear()
    yield
    hoja._PES_CACHE.clear()


def _postaja(c, stop_id, ime, lat, lon):
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
              (stop_id, ime, lat, lon))


def _voznja(c, trip_id, ime, postanki, omrezje="avtobus"):
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, "
              "mode, network) VALUES(?,?,?,?, 'S1', 'bus', ?)",
              (trip_id, "r" + trip_id, ime, "kam", omrezje))
    for seq, stop_id, t in postanki:
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                  "VALUES(?,?,?,?,?)", (trip_id, seq, stop_id, t, t))


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (D,))
    #   BLIZU   111 m od izhodišča  -> 1,3 min hoje
    #   DALEC   1,1 km od izhodišča -> 13 min hoje
    #   CILJ    111 m od cilja      -> 1,3 min hoje
    #   ROB     1,1 km od cilja     -> 13 min hoje
    _postaja(c, "BLIZU", "Blizu", 46.001, 14.500)
    _postaja(c, "DALEC", "Daleč", 46.010, 14.500)
    _postaja(c, "ROB", "Rob", 46.090, 14.500)
    _postaja(c, "CILJ", "Cilj", 46.099, 14.500)
    c.commit()
    return c


def test_hoja_do_postaje_lahko_zamudi_odhod(conn):
    """Odhod čez pet minut s postajališča, ki je trinajst minut hoje daleč,
    ni povezava — in to je edina razlika med to stranjo in odhodno tablo."""
    _voznja(conn, "t1", "prezgodaj", [(1, "DALEC", 8 * 3600 + 300),
                                      (2, "CILJ", 8 * 3600 + 900)])
    _voznja(conn, "t2", "ujameš", [(1, "DALEC", 8 * 3600 + 1200),
                                   (2, "CILJ", 8 * 3600 + 1800)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    voznje = [n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja"]
    assert [v["train_no"] for v in voznje] == ["ujameš"]


def test_zmaga_najmanjsa_vsota_prihoda_in_hoje(conn):
    """Cilj ni postaja, ampak točka.

    Ena vožnja pripelje prej, a se ustavi trinajst minut hoje od cilja; druga
    pripelje pozneje in ustavi pred vrati. Zmagati mora druga.
    """
    # Odhodi so po 8:10, ker je do postajališča 80 s hoje -- avtobus ob 8:00
    # potnik ne ujame in test bi meril nekaj drugega, kot piše.
    _voznja(conn, "t1", "prej_dalec", [(1, "BLIZU", 8 * 3600 + 600),
                                       (2, "ROB", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "pozneje_blizu", [(1, "BLIZU", 8 * 3600 + 660),
                                          (2, "CILJ", 8 * 3600 + 1500)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    voznje = [n for n in prvi["noge"] if n["vrsta"] == "voznja"]
    assert [v["train_no"] for v in voznje] == ["pozneje_blizu"]


def test_pes_prestop_med_postajaliscema(conn):
    """"Izstopi tu, prehodi 200 m, vkrcaj se tam" — brez tega je pot brez izida."""
    _voznja(conn, "t1", "prva", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "ROB", 8 * 3600 + 1200)])
    _voznja(conn, "t2", "druga", [(1, "CILJ", 8 * 3600 + 1800),
                                  (2, "ROB", 8 * 3600 + 2400)])
    conn.commit()
    # Brez peš poti se z ROB na CILJ ne pride: vožnja t2 pelje v napačno smer.
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    assert [n["do"] for n in prvi["noge"] if n["vrsta"] == "voznja"] == ["Rob"]

    conn.execute("INSERT INTO pespot(a_stop, b_stop, sekunde) VALUES('ROB','CILJ',120)")
    conn.commit()
    hoja._PES_CACHE.clear()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    prvi = r["predlogi"][0]
    # Peš prestop in hoja do vrat sta zaporedni hoji in se zlijeta v eno.
    zadnja = prvi["noge"][-1]
    assert zadnja["vrsta"] == "hoja" and zadnja["od"] == "Rob"
    assert zadnja["sekunde"] == 120 + round(
        geo.haversine(46.099, 14.500, *DO) / hoja.HITROST_MS)


def test_max_nog_omeji_stevilo_vozenj(conn):
    """Krogi morajo res omejevati noge.

    Z eno samo tabelo najboljših prihodov jih niso: ko poznejši krog izboljša
    postajališče, se prepiše tudi njegov starš in veriga nazaj preskoči kroge.
    Na pravih podatkih je iskanje pri meji dveh nog vračalo pot s štirimi.
    """
    _voznja(conn, "t1", "a", [(1, "BLIZU", 8 * 3600 + 600),
                              (2, "DALEC", 8 * 3600 + 900)])
    _voznja(conn, "t2", "b", [(1, "DALEC", 8 * 3600 + 1500),
                              (2, "ROB", 8 * 3600 + 1800)])
    _voznja(conn, "t3", "c", [(1, "ROB", 8 * 3600 + 2400),
                              (2, "CILJ", 8 * 3600 + 2700)])
    conn.commit()
    izh, _ = pot.blizu(conn, OD[0], OD[1], {"BLIZU", "DALEC", "ROB", "CILJ"})
    cil, _ = pot.blizu(conn, DO[0], DO[1], {"BLIZU", "DALEC", "ROB", "CILJ"}, smer="do")
    for meja in (1, 2, 3):
        n = pot._isci_dan(conn, izh, cil, D, 8 * 3600, meja)
        if n is None:
            continue
        voznje = [x for x in n["noge"] if x[0] is not None]
        assert len(voznje) <= meja, f"{meja} nog, dobil {len(voznje)} voženj"


def test_hoja_vso_pot_je_predlog(conn):
    """Peš je včasih hitreje in stran tega ne sme zamolčati."""
    _voznja(conn, "t1", "pocasna", [(1, "BLIZU", 10 * 3600),
                                    (2, "CILJ", 11 * 3600)])
    conn.commit()
    blizu_cilj = (46.003, 14.500)      # ~330 m: štiri minute hoje
    r = pot.isci(conn, OD, blizu_cilj, D, 8 * 3600)
    prvi = r["predlogi"][0]
    assert [n["vrsta"] for n in prvi["noge"]] == ["hoja"]
    assert prvi["trajanje_s"] < 10 * 60


def test_brez_postajalisc_v_dosegu_ni_izmisljenega_odgovora(conn):
    """Postajališče, ki ta dan nič ne streže, ne sme priti v matriko hoje."""
    izh, _ = pot.blizu(conn, OD[0], OD[1], set())
    assert izh == {}
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    assert r["predlogi"] == []


def test_nicelna_hoja_ni_noga(conn):
    """Postajališče pred vrati ne sme roditi noge „peš 0 min"."""
    _postaja(conn, "PRAG", "Prag", OD[0], OD[1])
    _voznja(conn, "t1", "a", [(1, "PRAG", 8 * 3600), (2, "CILJ", 8 * 3600 + 600)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    noge = r["predlogi"][0]["noge"]
    assert noge[0]["vrsta"] == "voznja"
    assert all(n["sekunde"] >= 60 for n in noge if n["vrsta"] == "hoja")


def test_ista_zamuda_kot_iskalnik_zvez(conn, monkeypatch):
    """Ista vožnja, isti postanek, dve strani — ena številka.

    Pravilo, katera zamuda velja in od kod je, je `stats.zamuda_na_postanku()`.
    Dokler je bilo napisano dvakrat, se je razlika pokazala na zaslonu: RG 318
    je v iskalniku pisal +11, v oknu iste vožnje pa +24.
    """
    from kajros import stats

    _voznja(conn, "t1", "LP 1", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "CILJ", 8 * 3600 + 1200)], omrezje="zeleznica")
    # Vozilo je videno pred potnikovo postajo: zamuda na njegovem postanku je
    # torej OCENA, ne meritev -- in prav tam sta se poti razšli.
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, "
                 "delay_arr, feed_ts) VALUES('t1', ?, 1, 240, 240, ?)",
                 (D, 4102444800))
    conn.commit()

    zveze = stats.connections(conn, "Blizu", "Cilj", D, now_s=8 * 3600 + 700)
    assert zveze, "iskalnik zvez mora najti to vožnjo"
    r = pot.isci(conn, OD, DO, D, 8 * 3600, now_s=8 * 3600 + 700)
    noga = next(n for n in r["predlogi"][0]["noge"] if n["vrsta"] == "voznja")
    assert noga["zamuda"]["s"] == zveze[0]["zamuda"]["s"]
    assert noga["zamuda"]["vrsta"] == zveze[0]["zamuda"]["vrsta"]


def test_prestop_uposteva_zamudo_obeh_vozenj(conn, monkeypatch):
    """Preostanek prestopa je načrtovani čas plus zamuda drugega minus prvega.

    Če zamuja tudi vozilo, na katero prestopaš, zveza morda vseeno drži — in
    to je natanko primer, ki potnika najbolj zanima.
    """
    _voznja(conn, "t1", "prva", [(1, "BLIZU", 8 * 3600 + 600),
                                 (2, "DALEC", 8 * 3600 + 900)])
    _voznja(conn, "t2", "druga", [(1, "DALEC", 8 * 3600 + 1500),
                                  (2, "CILJ", 8 * 3600 + 1800)])
    conn.commit()
    r = pot.isci(conn, OD, DO, D, 8 * 3600)
    p = r["predlogi"][0]
    assert len(p["prestopi"]) == 1
    t = p["prestopi"][0]
    assert t["kje"] == "Daleč"
    assert t["nacrtovano_s"] == 600, "1500 - 900, brez hoje vmes"
    assert t["ostane_s"] is None, "brez meritev ni ocene, in tega ne izmišljamo"
