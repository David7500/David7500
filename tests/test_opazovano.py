"""Opazovano (`opazovano.py`): kje vozila ne ustavijo, ena koda za vse prevoznike.

    ./venv/bin/python -m pytest tests/test_opazovano.py -q
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta

import pytest

from kajros import db, opazovano, stats, straza

ZACETEK = date(2026, 10, 1)
#: Postanek brez prehoda je `seq` 3, postajališče P2.
LAT, LON = 46.0, 14.02
#: Vozilo tako daleč od P2 (stopinje širine): 1,1 km in 150 m.
DALEC = 0.01
BLIZU = 0.00135


def _dan(i: int) -> str:
    return (ZACETEK + timedelta(days=i)).isoformat()


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    for i, lon in enumerate((14.0, 14.01, 14.02, 14.03)):
        c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  (f"P{i}", f"Postaja {i}", 46.0, lon))
    # Prvi dan v `lega` je obrezan in se preskoči.
    c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon) VALUES(?, 'x', 1, 46, 14)",
              ((ZACETEK - timedelta(days=1)).isoformat(),))
    return c


def _vozni(c, trip_id, agency="A", linija="L1", smer="Tja"):
    c.execute("INSERT OR IGNORE INTO trip(trip_id, route_id, train_no, headsign, service_id, mode, "
              "network, agency, first_seq, last_seq) "
              "VALUES(?, 'r', ?, ?, 'S', 'bus', 'avtobus', ?, 1, 4)",
              (trip_id, linija, smer, agency))
    for seq in range(1, 5):
        c.execute("INSERT OR IGNORE INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                  "VALUES(?,?,?,0,0)", (trip_id, seq, f"P{seq - 1}"))


def _voznja(c, dan, ura, trip_id=None, odmik=DALEC, prehod=False, korak_s=20, **kw):
    """Obkrožena vožnja: prehoda na `seq` 2 in 4, sled vmes na `odmik` od P2.
    Ena vožnja na dan, kot v voznem redu: `gps_prehod` ima ključ po vožnji in dnevu."""
    trip_id = trip_id or f"T{ura}"
    _vozni(c, trip_id, **kw)
    t0 = stats.polnoc(dan) + int(ura * 3600)
    for seq, ts in ((2, t0), (4, t0 + 200)) + (((3, t0 + 100),) if prehod else ()):
        c.execute("INSERT OR REPLACE INTO gps_prehod(service_date, trip_id, stop_seq, zamuda_s, "
                  "prehod_ts, je_cilj, dopolnjen, zapisano_ts) VALUES(?,?,?,0,?,0,0,?)",
                  (dan, trip_id, seq, ts, ts))
    for ts in range(t0, t0 + 201, korak_s):
        c.execute("INSERT OR REPLACE INTO lega(service_date, trip_id, ts, lat, lon) VALUES(?,?,?,?,?)",
                  (dan, trip_id, ts, LAT + odmik, LON))


def _dokazi(c, dni=(0, 1), na_dan=5, trip_id="T", **kw):
    for d in dni:
        for i in range(na_dan):
            _voznja(c, _dan(d), 7 + i, trip_id=f"{trip_id}{i}", **kw)


def _racunaj(c, do_dne: int):
    return opazovano.dopolni(c, ZACETEK + timedelta(days=do_dne + 1))


def _vrstice(c):
    return [dict(zip(opazovano._POLJA, r)) for r in c.execute(
        f"SELECT {', '.join(opazovano._POLJA)} FROM opazovano ORDER BY prvi_ts")]


def test_odpre_deset_dokazov_cez_24_ur(conn):
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["stanje"] == "ne_ustavi" and v["dokazov"] == 10
    assert (v["prevoznik"], v["linija"], v["smer"], v["stop_id"]) == ("A", "L1", "Tja", "P2")
    assert v["odprto_ts"] == v["zadnji_ts"]
    assert 1090 < v["dmin_m"] < 1130


def test_devet_dokazov_ne_odpre(conn):
    _dokazi(conn)
    conn.execute("DELETE FROM gps_prehod WHERE service_date = ? AND prehod_ts = "
                 "(SELECT MAX(prehod_ts) FROM gps_prehod WHERE service_date = ?)",
                 (_dan(1), _dan(1)))
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["stanje"] == "niz" and v["dokazov"] == 9


def test_deset_dokazov_v_enem_dnevu_ne_odpre(conn):
    """Enodnevna zapora (G3 Meljska) po zasnovi ne odpre: trditev je „zadnje dni“."""
    _dokazi(conn, dni=(0,), na_dan=12)    # 7:00 do 18:00
    _racunaj(conn, 0)
    v, = _vrstice(conn)
    assert v["stanje"] == "niz" and v["dokazov"] == 12


def test_zapre_prvi_prehod_in_vrstica_ostane(conn):
    _dokazi(conn)
    _voznja(conn, _dan(2), 7)
    _voznja(conn, _dan(2), 8, prehod=True)
    _voznja(conn, _dan(2), 9, prehod=True)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "zaprto" and v["vzrok"] == "prehod"
    assert v["zaprto_ts"] == stats.polnoc(_dan(2)) + 8 * 3600 + 100


def test_zapre_dokaz_pod_pragom(conn):
    _dokazi(conn)
    _voznja(conn, _dan(2), 8, odmik=BLIZU)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "zaprto" and v["vzrok"] == "blizu"


def test_niz_brez_odprtja_po_prehodu_izgine(conn):
    _dokazi(conn, dni=(0,), na_dan=3)
    _voznja(conn, _dan(1), 8, prehod=True)
    _racunaj(conn, 1)
    assert _vrstice(conn) == []


def test_prehod_po_dokazih_istega_dne_pretrga_tudi_brez_branja_sledi(conn):
    """Dokazi pred zadnjim prehodom dneva se ne berejo: isti rezultat kot po vrsti."""
    _voznja(conn, _dan(0), 7)
    _voznja(conn, _dan(0), 8, prehod=True)
    _voznja(conn, _dan(0), 9)
    _racunaj(conn, 0)
    v, = _vrstice(conn)
    assert v["stanje"] == "niz" and v["dokazov"] == 1


def test_pozabi_sedem_dni_po_zadnjem_dokazu(conn):
    _dokazi(conn)
    _voznja(conn, _dan(9), 8, trip_id="druga", linija="L2")
    _racunaj(conn, 9)
    vrstice = {v["linija"]: v for v in _vrstice(conn)}
    assert vrstice["L1"]["stanje"] == "zaprto" and vrstice["L1"]["vzrok"] == "zastarelo"
    assert vrstice["L1"]["zaprto_ts"] == vrstice["L1"]["zadnji_ts"] + opazovano.POZABI_S
    assert vrstice["L2"]["stanje"] == "niz"


def test_luknja_v_sledi_ni_dokaz_in_ne_pretrga(conn):
    _dokazi(conn)
    _voznja(conn, _dan(2), 7, korak_s=60)      # vrzel nad 40 s ob najbližji točki
    _voznja(conn, _dan(2), 8, korak_s=130)     # luknja
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "ne_ustavi" and v["dokazov"] == 10


def test_kljuc_je_linija_in_smer_ne_voznja(conn):
    """Nova `trip_id` po uvozu nadaljuje niz; prehod druge vožnje iste linije ga
    zapre; druga linija in druga smer sta svoj ključ."""
    _dokazi(conn, dni=(0,), trip_id="stara")
    _dokazi(conn, dni=(1,), trip_id="nova")
    _voznja(conn, _dan(1), 9, trip_id="druga_linija", linija="L2")
    _voznja(conn, _dan(1), 9, trip_id="druga_smer", smer="Nazaj")
    _racunaj(conn, 1)
    vrstice = {(v["linija"], v["smer"]): v for v in _vrstice(conn)}
    assert vrstice[("L1", "Tja")]["stanje"] == "ne_ustavi"
    assert vrstice[("L2", "Tja")]["dokazov"] == 1
    assert vrstice[("L1", "Nazaj")]["dokazov"] == 1


def test_isto_za_vse_prevoznike(conn):
    for agency in ("marprom", "1119"):
        _dokazi(conn, trip_id=f"t{agency}", agency=agency)
    _racunaj(conn, 1)
    assert sorted((v["prevoznik"], v["stanje"]) for v in _vrstice(conn)) == [
        ("1119", "ne_ustavi"), ("marprom", "ne_ustavi")]


def test_nagrobnik_brez_sched_odpade(conn):
    _dokazi(conn, dni=(0,))
    conn.execute("DELETE FROM sched")
    _racunaj(conn, 0)
    assert _vrstice(conn) == []
    assert conn.execute("SELECT brez_sched FROM opazovano_dan").fetchone()[0] == 5


def test_dan_se_obdela_enkrat(conn):
    _dokazi(conn)
    assert _racunaj(conn, 1) == [_dan(0), _dan(1)]
    pred = _vrstice(conn)
    assert _racunaj(conn, 1) == []
    brez_casa = lambda vrstice: [{**v, "preverjeno_ts": None} for v in vrstice]
    assert brez_casa(_vrstice(conn)) == brez_casa(pred)
    assert _vrstice(conn)[0]["dokazov"] == 10


def test_nadaljuje_cez_noci_kot_v_enem_kosu(conn):
    """Stanje po noči mora biti isto kot po vseh dneh hkrati."""
    _dokazi(conn, dni=(0, 1, 2))
    _racunaj(conn, 0)
    _racunaj(conn, 1)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["dokazov"] == 15 and v["stanje"] == "ne_ustavi"
    assert len(json.loads(v["tocke"])) == 15


def test_tock_ne_raste_cez_mejo(conn):
    _dokazi(conn, dni=tuple(range(7)), na_dan=6)
    _racunaj(conn, 6)
    v, = _vrstice(conn)
    assert v["dokazov"] == 42 and len(json.loads(v["tocke"])) == opazovano.TOCK


# ---------------------------------------------------------------- neodvisen dokaz

@pytest.fixture()
def osm(monkeypatch):
    def nastavi(*vrstice):
        mreza: dict = {}
        for la, lo, ime in vrstice:
            mreza.setdefault((int(la * 1000), int(lo * 1000)), []).append((la, lo, ime))
        monkeypatch.setattr(opazovano, "_osm", lambda: mreza)
    nastavi()
    return nastavi


def test_brez_potrditve_je_neznan(conn, osm):
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert (v["oznaka"], v["osm_ime"], v["osm_blizu"], v["osm_ob_poti"]) == ("neznan", 0, 0, 0)
    assert v["druge_obkrozenih"] == 0 and not opazovano.dovolj_za_prikaz(v)


def test_osm_isto_ime_potrdi(conn, osm):
    osm((LAT, LON, "POSTAJA 2"))
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["oznaka"] == "pravi" and v["osm_ime"] == 1 and opazovano.dovolj_za_prikaz(v)


def test_osm_brez_imena_ni_oznaka_je_pa_dovolj(conn, osm):
    """Ormož bolnica: OSM ima neimenovano postajališče na koordinati."""
    osm((LAT, LON, ""))
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["oznaka"] == "neznan" and v["osm_blizu"] == 1
    assert opazovano.dovolj_za_prikaz(v)


def test_istoimensko_ob_poti_je_napacen(conn, osm):
    """Vozilo ustavi pri istem imenu drugje, koordinata je najbrž zgrešena."""
    osm((LAT + DALEC, LON, "Postaja 2"))
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["oznaka"] == "napacen" and v["osm_ob_poti"] == 1
    assert not opazovano.dovolj_za_prikaz(v)


def test_oboje_je_dvoumen(conn, osm):
    osm((LAT, LON, "Postaja 2"), (LAT + DALEC, LON, "Postaja 2"))
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["oznaka"] == "dvoumen" and not opazovano.dovolj_za_prikaz(v)


def test_druge_linije_potrdijo_koordinato(conn, osm):
    """Vsaj 10 obkroženih in 20 % prehodov pri drugih ključih na istem `stop_id`."""
    _dokazi(conn)
    for i in range(10):
        _voznja(conn, _dan(1), 10 + i / 2, trip_id=f"d{i}", linija="L2", prehod=i < 2)
    _racunaj(conn, 1)
    v = {x["linija"]: x for x in _vrstice(conn)}["L1"]
    assert (v["druge_obkrozenih"], v["druge_prehodov"]) == (10, 2)
    assert v["oznaka"] == "pravi"


def test_premalo_drugih_ne_potrdi(conn, osm):
    _dokazi(conn)
    for i in range(10):
        _voznja(conn, _dan(1), 10 + i / 2, trip_id=f"d{i}", linija="L2", prehod=i < 1)
    _racunaj(conn, 1)
    v = {x["linija"]: x for x in _vrstice(conn)}["L1"]
    assert v["oznaka"] == "neznan"


def test_brez_posnetka_osm_ostane_neznano(conn, monkeypatch):
    monkeypatch.setattr(opazovano, "_osm", lambda: None)
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["osm_ime"] is None and v["osm_blizu"] is None and v["oznaka"] == "neznan"


def test_posnetek_osm_je_v_repozitoriju():
    opazovano._osm.cache_clear()
    assert sum(len(x) for x in opazovano._osm().values()) > 5000


# ---------------------------------------------------------------- izpis, senca, straža

def test_senca_na_bazi_samo_za_branje(tmp_path):
    pot = tmp_path / "b.sqlite"
    c = db.connect(pot)
    db.init(c)
    for i, lon in enumerate((14.0, 14.01, 14.02, 14.03)):
        c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  (f"P{i}", f"Postaja {i}", 46.0, lon))
    c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon) VALUES(?, 'x', 1, 46, 14)",
              ((ZACETEK - timedelta(days=1)).isoformat(),))
    _dokazi(c)
    c.commit()
    c.close()
    ro = sqlite3.connect(f"file:{pot}?mode=ro", uri=True)
    opazovano.senca(ro)
    assert opazovano.dopolni(ro, ZACETEK + timedelta(days=2)) == [_dan(0), _dan(1)]
    assert "L1" in opazovano.izpis(ro)
    ro.close()
    c = db.connect(pot)
    assert c.execute("SELECT COUNT(*) FROM opazovano").fetchone()[0] == 0


def test_izpis_pove_po_prevozniku(conn, osm):
    osm((LAT, LON, "Postaja 2"))
    _dokazi(conn, trip_id="ta", agency="marprom", linija="G2")
    _racunaj(conn, 1)
    izpis = opazovano.izpis(conn)
    assert "marprom" in izpis and "Postaja 2" in izpis and "pravi" in izpis


def test_straza_steje_odprte_nove_zaprte(conn, osm):
    _dokazi(conn)
    _dokazi(conn, trip_id="T9", linija="L9")
    _voznja(conn, _dan(2), 8, prehod=True, trip_id="T9", linija="L9")
    _racunaj(conn, 2)
    assert straza.merila_dneva(conn, _dan(0))["A"]["opazovano"] is None
    assert straza.merila_dneva(conn, _dan(1))["A"]["opazovano"] == {
        "odprtih": 2, "novih": 2, "zaprtih": 0}
    assert straza.merila_dneva(conn, _dan(2))["A"]["opazovano"] == {
        "odprtih": 1, "novih": 0, "zaprtih": 1}
    izpis = straza.izpis(_dan(2), straza.merila_dneva(conn, _dan(2)))
    assert "1/0/1" in izpis


def test_straza_pred_prvim_racunom_ne_ve(conn):
    _voznja(conn, _dan(0), 8)
    assert straza.merila_dneva(conn, _dan(0))["A"]["opazovano"] is None
    assert "–" in straza.izpis(_dan(0), straza.merila_dneva(conn, _dan(0)))
