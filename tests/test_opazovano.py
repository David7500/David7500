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


@pytest.fixture(autouse=True)
def brez_osrm(monkeypatch):
    monkeypatch.setattr(opazovano.pripni, "_dosegljiv", lambda naslov: False)


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


def _vozni(c, trip_id, agency="A", linija="L1", smer="Tja", start_s=0, postankov=4):
    c.execute("INSERT OR IGNORE INTO trip(trip_id, route_id, train_no, headsign, service_id, mode, "
              "network, agency, first_seq, last_seq, start_s) "
              "VALUES(?, 'r', ?, ?, 'S', 'bus', 'avtobus', ?, 1, 4, ?)",
              (trip_id, linija, smer, agency, start_s))
    for seq in range(1, postankov + 1):
        c.execute("INSERT OR IGNORE INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                  "VALUES(?,?,?,0,0)", (trip_id, seq, f"P{seq - 1}"))


def _voznja(c, dan, ura, trip_id=None, odmik=DALEC, prehod=False, korak_s=20, **kw):
    """Obkrožena vožnja: prehoda na `seq` 2 in 4, sled vmes na `odmik` od P2.
    Ena vožnja na dan, kot v voznem redu: `gps_prehod` ima ključ po vožnji in dnevu."""
    trip_id = trip_id or f"T{ura}"
    _vozni(c, trip_id, start_s=int(ura * 3600), **kw)
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


def _izidi(c, linija="L1", smer="Tja"):
    return [tuple(r) for r in c.execute(
        "SELECT start_s, mimo FROM opazovano_izid WHERE linija = ? AND smer = ? ORDER BY ts",
        (linija, smer))]


def test_odpre_deset_dokazov_cez_24_ur(conn):
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["stanje"] == "ne_ustavi" and v["dokazov"] == 10 and v["voznje"] is None
    assert (v["prevoznik"], v["linija"], v["smer"], v["stop_id"]) == ("A", "L1", "Tja", "P2")
    assert v["odprto_ts"] == v["zadnji_ts"]
    assert 1090 < v["dmin_m"] < 1130


def test_devet_dokazov_ne_odpre(conn):
    _dokazi(conn)
    conn.execute("DELETE FROM gps_prehod WHERE service_date = ? AND prehod_ts = "
                 "(SELECT MAX(prehod_ts) FROM gps_prehod WHERE service_date = ?)",
                 (_dan(1), _dan(1)))
    _racunaj(conn, 1)
    assert _vrstice(conn) == [] and len(_izidi(conn)) == 9


def test_deset_dokazov_v_enem_dnevu_ne_odpre(conn):
    """Enodnevna zapora (G3 Meljska) po zasnovi ne odpre: trditev je „zadnje dni“."""
    _dokazi(conn, dni=(0,), na_dan=12)    # 7:00 do 18:00
    _racunaj(conn, 0)
    assert _vrstice(conn) == [] and len(_izidi(conn)) == 12


def test_prehod_po_zapori_omili_in_ne_zapre(conn):
    """En prehod ne pove, ali postajališče spet deluje: N6217 ima enega na 29 voženj."""
    _dokazi(conn)
    _voznja(conn, _dan(2), 7)
    _voznja(conn, _dan(2), 8, prehod=True)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "redko" and v["dokazov"] == 11 and v["prislo"] == 1


def test_postajalisce_spet_deluje_zapre_in_vrstica_ostane(conn):
    _dokazi(conn)
    for i in range(5):
        _voznja(conn, _dan(2), 7 + i, prehod=True)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "zaprto" and v["vzrok"] == "prehod"
    assert v["zaprto_ts"] == stats.polnoc(_dan(2)) + 11 * 3600 + 100


def test_blizu_steje_kot_prislo(conn):
    _dokazi(conn)
    _voznja(conn, _dan(2), 8, odmik=BLIZU)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "redko" and v["prislo"] == 1


def test_vozilo_z_manj_kot_pol_postankov_ne_dokaze(conn):
    """N6217 Idrija: 36 % postankov. Morda ni ta vožnja; o postanku ne pove nič."""
    _dokazi(conn, postankov=5)
    _racunaj(conn, 1)
    assert _vrstice(conn) == [] and _izidi(conn) == []


def test_prehodi_samo_za_kljuce_z_dokazom(conn):
    _voznja(conn, _dan(0), 8, prehod=True)
    _racunaj(conn, 0)
    assert _izidi(conn) == []
    _voznja(conn, _dan(1), 8)
    _voznja(conn, _dan(2), 8, prehod=True)
    _racunaj(conn, 2)
    assert _izidi(conn) == [(8 * 3600, 1), (8 * 3600, 0)]


def test_spodrsljaj_dobro_prevozenega_se_ne_bere(conn):
    for i in range(opazovano.SPODRSLJAJ):
        _voznja(conn, _dan(0), 7 + i / 10, prehod=True)
    _voznja(conn, _dan(0), 20)
    _racunaj(conn, 0)
    assert _izidi(conn) == []
    assert conn.execute("SELECT sledi FROM opazovano_dan").fetchone()[0] == 0


def test_pozabi_sedem_dni_po_zadnjem_dokazu(conn):
    _dokazi(conn)
    _voznja(conn, _dan(9), 8, trip_id="druga", linija="L2")
    _racunaj(conn, 9)
    v, = _vrstice(conn)
    assert v["linija"] == "L1" and v["stanje"] == "zaprto" and v["vzrok"] == "zastarelo"
    assert v["zaprto_ts"] == v["zadnji_ts"] + opazovano.POZABI_S


def test_izidi_starejsi_od_okna_izginejo(conn):
    _dokazi(conn, dni=(0,))
    _voznja(conn, _dan(opazovano.OKNO_DNI), 8, trip_id="druga", linija="L2")
    _racunaj(conn, opazovano.OKNO_DNI)
    assert _izidi(conn) == []


def test_luknja_v_sledi_ni_dokaz_in_ne_pretrga(conn):
    _dokazi(conn)
    _voznja(conn, _dan(2), 7, korak_s=60)      # vrzel nad 40 s ob najbližji točki
    _voznja(conn, _dan(2), 8, korak_s=130)     # luknja
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "ne_ustavi" and v["dokazov"] == 10


def test_kljuc_je_linija_in_smer_ne_voznja(conn):
    """Nova `trip_id` po uvozu nadaljuje; druga linija in druga smer sta svoj ključ."""
    _dokazi(conn, dni=(0,), trip_id="stara")
    _dokazi(conn, dni=(1,), trip_id="nova")
    _voznja(conn, _dan(1), 9, trip_id="druga_linija", linija="L2")
    _voznja(conn, _dan(1), 9, trip_id="druga_smer", smer="Nazaj")
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert (v["linija"], v["smer"], v["stanje"]) == ("L1", "Tja", "ne_ustavi")
    assert _izidi(conn, "L2") == [(9 * 3600, 1)] and _izidi(conn, "L1", "Nazaj") == [(9 * 3600, 1)]


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


# ---------------------------------------------------------------- presoja

def _i(*izidi, korak=3 * 3600):
    """Izidi po treh urah: (start, mimo)."""
    return [(i * korak, s, m) for i, (s, m) in enumerate(izidi)]


ZDAJ = 40 * 3 * 3600


def test_presodi_samo_dokazi():
    assert opazovano.presodi(_i(*[(i, 1) for i in range(10)]), ZDAJ) == ("ne_ustavi", None)


def test_presodi_premalo_ali_prekratko():
    assert opazovano.presodi(_i(*[(i, 1) for i in range(9)]), ZDAJ) is None
    assert opazovano.presodi(_i(*[(i, 1) for i in range(10)], korak=600), ZDAJ) is None


def test_presodi_zacetek_zapore():
    """Prej je delovalo: po nizu dokazov je zapora, starih prihodov ne vlečemo s sabo."""
    prej = [(s, 0) for s in range(5)] * 3
    assert opazovano.presodi(_i(*prej, *[(s, 1) for s in range(5)] * 2), ZDAJ) == ("ne_ustavi", None)


def test_presodi_stalna_izjema():
    """A6227 Naklo: prva zjutraj pride, 11 drugih nikoli, ista trasa."""
    dan = [(0, 0)] + [(s, 1) for s in range(1, 6)]
    r = opazovano.presodi(_i(*dan * 4), ZDAJ)
    assert r == ("ne_ustavi", [1, 2, 3, 4, 5])


def test_presodi_tu_in_tam():
    """N6217 Podroteja: redki prehodi na različnih vožnjah, nič stalnega."""
    izidi = [(s, 1) for s in range(6)] * 4
    izidi[7] = (1, 0)
    izidi[20] = (2, 0)
    assert opazovano.presodi(_i(*izidi), ZDAJ) == ("redko", None)


def test_presodi_tu_in_tam_ob_stalni_izjemi():
    """Vožnja, ki stalno pride, ni med tistimi, ki redko."""
    dan = [(0, 0), (1, 1), (2, 1), (3, 1)]
    izidi = dan * 4
    izidi[5] = (1, 0)
    assert opazovano.presodi(_i(*izidi), ZDAJ) == ("redko", [1, 2, 3])


def test_presodi_konec_zapore():
    dokazi = [(s, 1) for s in range(5)] * 3
    assert opazovano.presodi(_i(*dokazi, (0, 0)), ZDAJ)[0] == "redko"
    assert opazovano.presodi(_i(*dokazi, *[(s, 0) for s in range(5)]), ZDAJ) is None


def test_presodi_predolgo_nic():
    izidi = _i(*[(i, 1) for i in range(10)])
    assert opazovano.presodi(izidi, izidi[-1][0] + opazovano.POZABI_S) is not None
    assert opazovano.presodi(izidi, izidi[-1][0] + opazovano.POZABI_S + 1) is None


def test_stalna_izjema_v_tabeli(conn, osm):
    """Vožnja ob 7 pride vsak dan, ob 8–12 nikoli."""
    osm((LAT, LON, "Postaja 2"))
    for d in (0, 1, 2):
        _voznja(conn, _dan(d), 7, prehod=True)
        for i in range(1, 6):
            _voznja(conn, _dan(d), 7 + i)
    _racunaj(conn, 2)
    v, = _vrstice(conn)
    assert v["stanje"] == "ne_ustavi" and json.loads(v["voznje"]) == [h * 3600 for h in range(8, 13)]
    pari = opazovano.za_prikaz(conn, stats.polnoc(_dan(3)))
    assert ("T7", "P2") not in pari and pari[("T8", "P2")]["vrsta"] == "ne_ustavi"


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


def test_osm_z_drugim_imenom_ni_dovolj(conn, osm):
    """„Krško Š“ na OSM „Krško - Resa“: koordinata je morda zgrešena."""
    osm((LAT, LON, "Druga postaja"))
    _dokazi(conn)
    _racunaj(conn, 1)
    v, = _vrstice(conn)
    assert v["oznaka"] == "neznan" and v["osm_blizu"] == 0 and not opazovano.dovolj_za_prikaz(v)


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
    for i in range(5):
        _voznja(conn, _dan(2), 7 + i, prehod=True, trip_id=f"T9{i}", linija="L9")
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


# ---------------------------------------------------------------- prikaz

#: Noč po dveh dnevih dokazov (`_dokazi`).
TAKOJ = stats.polnoc(_dan(2))


@pytest.fixture()
def z_oznako(conn, osm):
    osm((LAT, LON, "Postaja 2"))
    _dokazi(conn)
    _racunaj(conn, 1)
    return conn


def test_za_prikaz_vse_voznje_kljuca(z_oznako):
    pari = opazovano.za_prikaz(z_oznako, TAKOJ)
    assert set(pari) == {(f"T{i}", "P2") for i in range(5)}
    o = pari[("T0", "P2")]
    assert o["vrsta"] == "ne_ustavi" and o["dokazov"] == 10 and o["seq"] == 3
    assert opazovano.ne_ustavi(z_oznako, TAKOJ) == set(pari)


def test_za_prikaz_nova_voznja_po_uvozu_podeduje(z_oznako):
    _vozni(z_oznako, "nova", start_s=99)
    assert ("nova", "P2") in opazovano.za_prikaz(z_oznako, TAKOJ)


def test_za_prikaz_samo_z_neodvisnim_dokazom(conn, osm):
    _dokazi(conn)
    _racunaj(conn, 1)
    assert opazovano.za_prikaz(conn, TAKOJ) == {}


def test_za_prikaz_stikalo(z_oznako, monkeypatch):
    monkeypatch.setattr(opazovano.config, "OPAZOVANO_PRIKAZ", False)
    assert opazovano.za_prikaz(z_oznako, TAKOJ) == {}


def test_danasnji_prehod_takoj_omili(z_oznako):
    """Zapora se konča zjutraj: tabla ne trdi do naslednje noči, da ne ustavi."""
    dan = _dan(2)
    zdaj = stats.polnoc(dan) + 9 * 3600
    assert opazovano.ne_ustavi(z_oznako, zdaj)
    z_oznako.execute("INSERT INTO gps_prehod(service_date, trip_id, stop_seq, zamuda_s, prehod_ts, "
                     "je_cilj, dopolnjen, zapisano_ts) VALUES(?, 'T1', 3, 0, ?, 0, 0, ?)",
                     (dan, zdaj, zdaj))
    pari = opazovano.za_prikaz(z_oznako, zdaj)
    assert opazovano.ne_ustavi(z_oznako, zdaj) == set()
    assert {o["vrsta"] for o in pari.values()} == {"redko"} and len(pari) == 5
    assert all(o["pot"] is None for o in pari.values())


def test_ko_nocni_racun_stoji_trditve_odpadejo(z_oznako):
    assert opazovano.za_prikaz(z_oznako, TAKOJ)
    assert opazovano.za_prikaz(z_oznako, TAKOJ + opazovano.POZABI_S + 86400) == {}


def _ob_pravem_casu(monkeypatch):
    """Tabla in zveze računajo z uro stene, dokazi v pripravi pa so iz oktobra."""
    monkeypatch.setattr(opazovano, "POZABI_S", 10 ** 10)


def test_tabla_oznaci_vrstico(z_oznako, monkeypatch):
    _ob_pravem_casu(monkeypatch)
    from datetime import datetime
    from kajros import api
    vrstice = [{"trip_id": "T1", "stop_id": "P2", "train_no": "L1", "agency": "A"},
               {"trip_id": "T1", "stop_id": "P1", "train_no": "L1", "agency": "A"}]
    assert api._oznaci_obvoze(z_oznako, vrstice, datetime.now(), zasloni=False) == 1
    assert vrstice[0]["ne_ustavi"] is True and vrstice[0]["opazovano"] == "ne_ustavi"
    assert "ne_ustavi" not in vrstice[1] and "opazovano" not in vrstice[1]


def test_redko_na_tabli_ostane_odhod(conn, osm, monkeypatch):
    _ob_pravem_casu(monkeypatch)
    from datetime import datetime
    from kajros import api
    osm((LAT, LON, "Postaja 2"))
    _dokazi(conn)
    _voznja(conn, _dan(2), 8, prehod=True)
    _racunaj(conn, 2)
    vrstice = [{"trip_id": "T1", "stop_id": "P2", "train_no": "L1", "agency": "A"}]
    assert api._oznaci_obvoze(conn, vrstice, datetime.now(), zasloni=False) == 0
    assert vrstice[0]["opazovano"] == "redko" and "ne_ustavi" not in vrstice[0]


def _zveza(trip_id="T1", od=1, do=3):
    return {"trip_id": trip_id, "from_seq": od, "to_seq": do}


def test_zveza_na_izhodiscu_in_cilju(z_oznako, monkeypatch):
    """P2 je `seq` 3: vstop ali izstop tam ne gre, vožnja mimo pa."""
    _ob_pravem_casu(monkeypatch)
    from kajros import alerts
    rows = [_zveza(od=3, do=4), _zveza(od=1, do=3), _zveza(od=1, do=2)]
    alerts.oznaci_zveze(z_oznako, rows, TAKOJ)
    assert [r.get("ne_ustavi") for r in rows] == ["od", "do", None]
    assert [r.get("opazovano") for r in rows] == ["ne_ustavi", "ne_ustavi", None]


def test_zveza_redko_ostane_zveza(conn, osm, monkeypatch):
    _ob_pravem_casu(monkeypatch)
    from kajros import alerts
    osm((LAT, LON, "Postaja 2"))
    _dokazi(conn)
    _voznja(conn, _dan(2), 8, prehod=True)
    _racunaj(conn, 2)
    rows = [_zveza(od=1, do=3)]
    alerts.oznaci_zveze(conn, rows, TAKOJ)
    assert "ne_ustavi" not in rows[0] and rows[0]["opazovano"] == "redko"
    assert rows[0]["opazovano_kje"] == "do"


def test_zveza_drug_dan_samo_beseda(z_oznako, monkeypatch):
    """Za jutri ne vemo; da zadnje dni ni ustavljal, pa drži."""
    _ob_pravem_casu(monkeypatch)
    from kajros import alerts
    rows = [_zveza(od=1, do=3)]
    alerts.oznaci_zveze(z_oznako, rows, TAKOJ, drug_dan=True)
    assert "ne_ustavi" not in rows[0] and rows[0]["opazovano"] == "ne_ustavi"


def test_prestop_ne_gre_cez_postanek_brez_ustavljanja(z_oznako, monkeypatch):
    _ob_pravem_casu(monkeypatch)
    from kajros import alerts
    noga = lambda t, a, b: {"trip_id": t, "from": a, "to": b}
    dober = {"legs": [noga("T1", "Postaja 0", "Postaja 1"), noga("X", "Postaja 1", "Postaja 3")]}
    na_p2 = {"legs": [noga("T1", "Postaja 0", "Postaja 2"), noga("X", "Postaja 2", "Postaja 3")]}
    druga = {"legs": [noga("X", "Postaja 0", "Postaja 2"), noga("Y", "Postaja 2", "Postaja 3")]}
    assert alerts.brez_zaprtih_prestopov(z_oznako, [dober, na_p2, druga], TAKOJ) == [dober, druga]


def test_pot_ne_vstopi_kjer_zadnje_dni_ni_ustavljal(z_oznako, monkeypatch):
    _ob_pravem_casu(monkeypatch)
    from kajros import alerts, pot
    assert pot.obvozi_po_postaji(alerts.ne_ustavi_vsi(z_oznako, TAKOJ))["P2"] == {f"T{i}" for i in range(5)}


def test_trasa_vozila_gre_po_poti(z_oznako, monkeypatch):
    """/api/trip/{id}/shape: pot vozil namesto objavljene, objavljena posebej."""
    _ob_pravem_casu(monkeypatch)
    from kajros import api
    kos = [[46.0, 14.0], [46.0, 14.01], [46.0, 14.02], [46.0, 14.03]]
    z_oznako.execute("INSERT INTO shape(shape_id, points) VALUES('S1', ?)", (json.dumps([kos]),))
    z_oznako.execute("UPDATE trip SET shape_id = 'S1' WHERE trip_id = 'T1'")
    z_oznako.execute("UPDATE opazovano SET pot = ?", (json.dumps([[46.0005, 14.011], [46.0005, 14.029]]),))
    z_oznako.commit()
    monkeypatch.setattr(api, "_conn", lambda: _Kontekst(z_oznako))
    d = api.api_shape("T1")
    assert [46.0, 14.02] not in d["points"][0] and [46.0005, 14.011] in d["points"][0]
    assert [46.0, 14.02] in d["po_voznem_redu"][0]


class _Kontekst:
    def __init__(self, c):
        self.c = c

    def __enter__(self):
        return self.c

    def __exit__(self, *a):
        return False


def test_pot_vozil_v_vrstici(z_oznako):
    v, = _vrstice(z_oznako)
    pot = json.loads(v["pot"])
    assert len(pot) >= 2 and all(abs(la - (LAT + DALEC)) < 1e-6 for la, _ in pot)


def test_sled_kraka_tja_in_nazaj(conn):
    """Prehoda ob isti uri, tudi obrnjena: vozilo na križišču velja za oba postanka."""
    t0 = stats.polnoc(_dan(0)) + 8 * 3600
    for i, ts in enumerate(range(t0 - 40, t0 + 41, 20)):
        conn.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon) VALUES(?, 'K', ?, 46, ?)",
                     (_dan(0), ts, 14 + i / 1000))
    assert len(opazovano._sled(conn, _dan(0), "K", t0, t0 - 1)) == 3
    assert len(opazovano._sled(conn, _dan(0), "K", t0 - 40, t0 + 40)) == 5


def test_trasa_obvoz_zamenja_odsek():
    """Pot vozil namesto objavljenega odseka, objavljeni posebej."""
    kos = [[46.0, 14.0 + i / 100] for i in range(6)]
    pot = [[46.0, 14.012], [46.01, 14.02], [46.01, 14.03], [46.0, 14.038]]
    kosi, objavljeni = opazovano.trasa_po_obvozih([kos], [(pot, 46.0, 14.025)])
    assert kosi == [[kos[0], kos[1], *pot, kos[4], kos[5]]]
    assert objavljeni == [[[46.0, 14.012], kos[2], kos[3], [46.0, 14.038]]]


def test_trasa_krak_tja_in_nazaj():
    """Oba konca poti sta na istem mestu trase: odsek loči skriti postanek."""
    kos = [[46.0, 14.0], [46.0, 14.01], [46.01, 14.01], [46.0, 14.01], [46.0, 14.02]]
    pot = [[46.0, 14.0098], [46.0, 14.0102]]
    kosi, objavljeni = opazovano.trasa_po_obvozih([kos], [(pot, 46.01, 14.01)])
    assert [46.01, 14.01] not in kosi[0] and pot[0] in kosi[0]
    assert [46.01, 14.01] in objavljeni[0]


def test_trasa_pot_stran_od_trase_ostane_zunaj():
    kos = [[46.0, 14.0 + i / 100] for i in range(6)]
    pot = [[46.1, 14.01], [46.1, 14.03]]
    assert opazovano.trasa_po_obvozih([kos], [(pot, 46.0, 14.025)]) == ([kos], [])


def test_stara_senca_se_ob_zagonu_izracuna_znova(tmp_path):
    pot = tmp_path / "b.sqlite"
    c = sqlite3.connect(pot)
    c.execute("CREATE TABLE opazovano (prevoznik TEXT, stanje TEXT)")
    c.execute("CREATE TABLE opazovano_dan (dan TEXT PRIMARY KEY)")
    c.execute("INSERT INTO opazovano_dan VALUES ('2026-10-29')")
    c.commit()
    c.close()
    c = db.connect(pot)
    db.init(c)
    assert "prislo" in {r[1] for r in c.execute("PRAGMA table_info(opazovano)")}
    assert c.execute("SELECT COUNT(*) FROM opazovano_dan").fetchone()[0] == 0
