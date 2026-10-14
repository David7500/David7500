"""Prehod postanka iz GPS brez trase (`prehod.py`).

Postanki so 0,01° (~773 m) narazen ob vzporedniku 46°, vozni red na 100 s,
vozilo vozi 0,002° (~155 m) na 20 s, torej ravno po voznem redu, le z
zamudo. Lega točno na postanku pomeni najbližjo točko; odhod je ~6 s za njo
(50 m pri 7,7 m/s).

    ./venv/bin/python -m pytest tests/test_prehod.py -q
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from kajros import config, db, iz_lege, prehod, stats

DAN = date.today().isoformat()
POLNOC = stats.polnoc(DAN)


@pytest.fixture(autouse=True)
def _cist_spomin():
    prehod._sledi.clear()
    prehod._vodje.clear()
    yield
    prehod._sledi.clear()
    prehod._vodje.clear()


def _sled(postanki):
    return prehod.Sled("n", DAN, [(i + 1, lat, lon, cas) for i, (lat, lon, cas) in enumerate(postanki)])


def _ravna(n=4):
    return _sled([(46.0, 14.0 + 0.01 * i, 36000 + 100 * i) for i in range(n)])


def _vozi(sled, tocke):
    """[(t_s, lat, lon)] -> {stop_seq: (zamuda, je_cilj, dopolnjen)}"""
    out = {}
    for t, lat, lon in tocke:
        for seq, zamuda, je_cilj, dopolnjen, _ in prehod.dodaj(sled, t, lat, lon):
            assert seq not in out, "postanek dvakrat"
            out[seq] = (zamuda, je_cilj, dopolnjen)
    return out


def _vzhod(od_t, od_lon, do_lon, lat=46.0):
    """Vožnja proti vzhodu po 0,002° na 20 s."""
    k = round((do_lon - od_lon) / 0.002)
    return [(od_t + 20 * i, lat, od_lon + 0.002 * i) for i in range(k + 1)]


def test_vozi_mimo_postankov_odhod_in_prihod_na_cilj():
    s = _ravna()
    # 60 s zamude, na cilju (D) stoji tri minute.
    pot = _vzhod(36060, 14.0, 14.03) + [(36360 + 20 * i, 46.0, 14.03) for i in range(1, 10)]
    out = _vozi(s, pot)
    assert 1 not in out, "izhodišča ne merimo"
    assert 60 <= out[2][0] <= 70 and 60 <= out[3][0] <= 70, "odhod malo za najbližjo točko"
    assert out[4][1], "cilj je prihod"
    assert 50 <= out[4][0] <= 60, "prihod malo pred najbližjo točko"


def test_cilj_se_zakljuci_ko_vozilo_utihne():
    s = _ravna()
    out = _vozi(s, _vzhod(36060, 14.0, 14.03))
    assert 4 not in out, "vozilo je še v krogu"
    assert prehod.tiho(s, POLNOC + 36360 + 60) == []
    ((seq, zamuda, je_cilj, _, _),) = prehod.tiho(s, POLNOC + 36360 + prehod.CILJ_S)
    assert (seq, je_cilj) == (4, True) and 50 <= zamuda <= 60


def test_izlet_tja_in_nazaj_ne_preskoci_postankov():
    """B in B2 sta isto postajališče v obe smeri, vmes C na koncu kraka. Ob
    prvem obisku B se konča tudi obisk B2 -- brez potrditve bi bil C
    preskočen, B2 pa izmerjen 200 s prezgodaj."""
    s = _sled([(46.0, 14.00, 36000), (46.0, 14.01, 36100), (46.0, 14.02, 36200),
               (46.0, 14.01, 36300), (46.01, 14.01, 36450)])
    pot = (_vzhod(36000, 14.0, 14.02)
           + [(36200 + 20 * i, 46.0, 14.02 - 0.002 * i) for i in range(1, 6)]
           + [(36300 + 20 * i, 46.0 + 0.0014 * i, 14.01) for i in range(1, 9)])
    out = _vozi(s, pot)
    assert sorted(out) == [2, 3, 4, 5]
    assert all(0 <= out[q][0] <= 15 for q in (2, 3, 4)), out


def test_prvi_obisk_pocaka_na_potrditev():
    """Vozilo pelje na izhodišče mimo B 17 min pred voznim redom, nato vozi
    s 5 min zamude. Prej je obveljal prvi obisk B, vsi naslednji pa so padli
    na skoku zamude (13. 10. 2026: 18 min prej, nato do +22 min)."""
    s = _ravna(5)
    na_izhodisce = [(35000 + 20 * i, 46.0, 14.016 - 0.002 * i) for i in range(9)]
    caka = [(35160 + 20 * i, 46.0, 14.0) for i in range(1, 58)]
    out = _vozi(s, na_izhodisce + caka + _vzhod(36300, 14.0, 14.04))
    assert sorted(out) == [2, 3, 4]
    assert all(300 <= out[q][0] <= 310 for q in (2, 3, 4)), out


def test_prvi_obisk_pred_dolgim_odsekom_velja_po_casu():
    """Izola -> Koper -> 80 km do Ljubljane: Koper je prej čakal do Ljubljane,
    potnik pa 70 min ni videl zamude. Zdaj velja 15 min po odhodu."""
    s = _sled([(46.0, 14.0, 36000), (46.0, 14.01, 36100), (46.0, 15.0, 39600)])
    pot = _vzhod(36060, 14.0, 14.12)                   # B s +60 s, nato 18 min proti C
    odhod_b = 36060 + 20 * 5 + 6
    pred = _vozi(s, [p for p in pot if p[0] < odhod_b + prehod.POTRDI_PRVI_S])
    assert pred == {}
    po = _vozi(s, [p for p in pot if p[0] >= odhod_b + prehod.POTRDI_PRVI_S])
    assert list(po) == [2] and 60 <= po[2][0] <= 70, po


def test_prezgodnji_prvi_obisk_ne_velja_po_casu():
    """Vozilo na poti na izhodišče pelje mimo B 15 min pred voznim redom in
    nato dolgo stoji drugje: to ni obisk."""
    s = _sled([(46.0, 14.0, 36000), (46.0, 14.01, 36100), (46.0, 15.0, 39600)])
    mimo = [(35200 + 20 * i, 46.0, 14.016 - 0.002 * i) for i in range(6)]
    stoji = [(35300 + 20 * i, 46.0, 14.005) for i in range(1, 80)]
    assert _vozi(s, mimo + stoji) == {}


def test_skok_zamude_potrdi_naslednji_postanek():
    """Okvara med B in C: 25 min stoji. C pade na skoku, a ga D potrdi."""
    s = _ravna(6)
    pot = (_vzhod(36000, 14.0, 14.014)
           + [(36140 + 20 * i, 46.0, 14.014) for i in range(1, 76)]
           + _vzhod(37640, 14.014, 14.05)[1:])
    out = _vozi(s, pot)
    assert sorted(out) == [2, 3, 4, 5]
    assert 0 <= out[2][0] <= 10
    assert all(1500 <= out[q][0] <= 1510 for q in (3, 4, 5)), out


def test_molk_za_postankom_ga_zakljuci_molk_na_njem_ne():
    """Vozilo obmolkne 70 m za D (NAP ga prestavi na naslednjo vožnjo): D
    velja. Ko obmolkne, ko na D stoji, odhod ni znan."""
    za = _vzhod(36000, 14.0, 14.03) + [(36309, 46.0, 14.0309)]
    s = _ravna(5)
    out = _vozi(s, za)
    assert 4 not in out
    ((seq, zamuda, _, _, _),) = prehod.tiho(s, POLNOC + 36309 + prehod.CILJ_S)
    assert seq == 4 and 0 <= zamuda <= 10
    s = _ravna(5)
    _vozi(s, _vzhod(36000, 14.0, 14.03) + [(36320, 46.0, 14.03)])
    assert prehod.tiho(s, POLNOC + 36320 + prehod.CILJ_S) == []


def test_obvoz_mimo_postanka():
    """Vozilo B obide 300 m severno: B ostane brez meritve, C počaka na
    potrditev z D in velja."""
    s = _ravna(5)
    pot = (_vzhod(36000, 14.0, 14.006)
           + [(36060 + 20 * i, 46.0027, 14.006 + 0.002 * i) for i in range(1, 4)]
           + _vzhod(36140, 14.014, 14.04))
    out = _vozi(s, pot)
    assert 2 not in out
    assert out[3][0] == pytest.approx(5, abs=10) and 4 in out


def test_skok_gps_se_zavrze():
    s, s2 = _ravna(), _ravna()
    pot = _vzhod(36000, 14.0, 14.03)
    z_napako = pot[:7] + [(pot[6][0] + 10, 46.05, 14.012)] + pot[7:]
    assert _vozi(s, z_napako) == _vozi(s2, pot)


def test_predolg_razmik_ni_obisk():
    s = _ravna()
    pot = [p for p in _vzhod(36000, 14.0, 14.04) if not 36060 < p[0] < 36200]
    out = _vozi(s, pot)
    assert 2 not in out and 3 in out


def test_krozna_voznja_ob_odhodu_ni_na_cilju():
    """Cilj je na izhodišču: vozilo, ki tam čaka na odhod, cilja ne obišče."""
    s = _sled([(46.0, 14.00, 36000), (46.0, 14.01, 36100), (46.0, 14.00, 36300)])
    cakanje = [(35900 + 20 * i, 46.0, 14.0) for i in range(5)]
    out = _vozi(s, cakanje + _vzhod(36000, 14.0, 14.012))
    assert 3 not in out


# ------------------------------------------------------------ v strežniku

def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46.0,?)",
                  [(k, k, 14.0 + 0.01 * i) for i, k in enumerate("ABCD")])
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id,"
              " mode, agency, network) VALUES('n', 'r', 'N1', 'D', 'S', NULL, 'bus', '1119', 'avtobus')")
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('n',?,?,?,?)",
                  [(1, "A", None, 36000), (2, "B", 36100, 36100),
                   (3, "C", 36200, 36200), (4, "D", 36300, None)])
    db.fill_trip_window(c)
    c.commit()
    return c


def test_sled_se_po_zagonu_obnovi_iz_tabele_lega():
    c = _baza()
    pot = _vzhod(36060, 14.0, 14.03)
    novi = []
    for i, (t, lat, lon) in enumerate(pot):
        if i == 5:              # vozilo je na B; proces se znova zažene
            prehod._sledi.clear()
        novi += prehod.lega(c, "n", DAN, int(POLNOC + t), lat, lon)
    assert [p[0] for p in novi] == [2, 3]
    assert c.execute("SELECT COUNT(*) FROM lega").fetchone()[0] == len(pot)


def test_dve_vozili_na_isti_vozji_vsako_svoja_sled():
    """NAP pod isto vožnjo javlja dve vozili: eno stoji 5 km stran, drugo
    vozi. Ena sled je sledila prvemu in lege drugega zavrgla kot skoke GPS
    (14. 10. 2026 Nomago Ljubno -> Celje brez vsake zamude)."""
    c = _baza()
    stoji = [(36050 + 20 * i, 46.05, 14.015) for i in range(16)]
    vozi = _vzhod(36060, 14.0, 14.03)
    novi = []
    for t, lat, lon, v in sorted([(*p, "stoji") for p in stoji] + [(*p, "vozi") for p in vozi]):
        novi += prehod.lega(c, "n", DAN, int(POLNOC + t), lat, lon, v)
    assert [p[0] for p in novi] == [2, 3]
    assert all(60 <= p[1] <= 70 for p in novi), novi
    assert prehod.vodja("n", DAN)[0] == "vozi"
    assert {r[0] for r in c.execute("SELECT vozilo FROM lega")} == {"stoji", "vozi"}


def test_vozjo_prevzame_vozilo_z_vec_prehodi():
    """Prvo vozilo prevozi B in C, nato zavije drugam; pravo vozi vso pot s
    5 min zamude. Ko ima več prehodov, veljajo njegovi in povozijo prve."""
    c = _baza()
    napacno = _vzhod(36000, 14.0, 14.022) + [(36220 + 20 * i, 46.0 + 0.002 * i, 14.022)
                                             for i in range(1, 10)]
    prav = _vzhod(36300, 14.0, 14.03) + [(36600 + 20 * i, 46.0, 14.03) for i in range(1, 9)]
    zapisano = {}
    for t, lat, lon in napacno:
        for p in prehod.lega(c, "n", DAN, int(POLNOC + t), lat, lon, "napacno"):
            zapisano[p[0]] = p[1]
    assert sorted(zapisano) == [2, 3] and all(abs(z) < 30 for z in zapisano.values())
    for t, lat, lon in prav:
        for p in prehod.lega(c, "n", DAN, int(POLNOC + t), lat, lon, "prav"):
            zapisano[p[0]] = p[1]
    assert sorted(zapisano) == [2, 3, 4]
    assert all(290 <= z <= 320 for z in zapisano.values()), zapisano
    assert prehod.vodja("n", DAN)[0] == "prav"


def test_senca_pise_gps_prehod_ne_run(monkeypatch):
    monkeypatch.setattr(config, "PREHOD_GPS", "senca")
    c = _baza()
    for t, lat, lon in _vzhod(36060, 14.0, 14.03):
        iz_lege.opazuj(c, "n", DAN, int(POLNOC + t), lat, lon)
    assert [r[0] for r in c.execute("SELECT stop_seq FROM gps_prehod ORDER BY stop_seq")] == [2, 3]
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0, "vožnja brez trase"


def test_vodi_pise_run(monkeypatch):
    monkeypatch.setattr(config, "PREHOD_GPS", "vodi")
    c = _baza()
    pot = _vzhod(36060, 14.0, 14.03)
    for t, lat, lon in pot:
        iz_lege.opazuj(c, "n", DAN, int(POLNOC + t), lat, lon)
    iz_lege.pospravi(POLNOC + pot[-1][0] + prehod.CILJ_S, c)
    run = {r[0]: r[1:] for r in c.execute("SELECT stop_seq, delay_arr, delay_dep, feed_ts FROM run")}
    assert sorted(run) == [2, 3, 4]
    assert run[2][0] is None and 60 <= run[2][1] <= 70
    assert run[4][1] is None and 50 <= run[4][0] <= 60, "cilj je prihod"
    assert all(stats.potrjen_prehod(r[2], POLNOC + 36000 + 100 * (q - 1) + r[1 if q < 4 else 0])
               for q, r in run.items()), "čas lege je po prehodu"


def test_stare_lege_se_pobrisejo():
    c = _baza()
    staro = (date.today() - timedelta(days=prehod.HRANI_DNI + 1)).isoformat()
    c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon) VALUES(?, 'n', 1, 46.0, 14.0)", (staro,))
    c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon) VALUES(?, 'n', 2, 46.0, 14.0)", (DAN,))
    prehod._brisi_po = 0
    prehod.pospravi(c)
    assert [r[0] for r in c.execute("SELECT service_date FROM lega")] == [DAN]


def test_primerjava_s_sedanjim_nacinom():
    """Sedanji način izmeri B, novi B in C; cilj samo novi."""
    c = _baza()
    for t, lat, lon in _vzhod(36060, 14.0, 14.03):
        prehod.zapisi(c, "n", DAN, prehod.lega(c, "n", DAN, int(POLNOC + t), lat, lon), int(POLNOC + t))
    prehod.zapisi(c, "n", DAN, prehod.tiho(prehod._sledi[("n", DAN, None)], POLNOC + 37000), int(POLNOC + 36360))
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('n', ?, 2, NULL, 60, 0)", (DAN,))
    p = prehod.primerjava(c, DAN, DAN)
    assert (p["vozenj"], p["vmesnih"], p["star"], p["nov"], p["samo_nov"]) == (1, 2, 1, 2, 1)
    assert p["razlika"]["n"] == 1 and p["razlika"]["mediana"] <= 10
    assert (p["cilj"]["star"], p["cilj"]["nov"]) == (0, 1)
