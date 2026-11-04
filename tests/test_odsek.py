"""Zamuda na dolgem odseku iz lege: profil, razdalja, senca v `ocena`.

    ./venv/bin/python -m pytest tests/test_odsek.py -q
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from kajros import db, deljenje, ocena, odsek, stats

DAN = "2026-11-03"
POLNOC = stats.polnoc(DAN)
TRIP = "v1"
# A -- B 40 min po voznem redu, ~21 km, nato C 10 min.
A, B, C = (46.00, 14.50), (46.19, 14.50), (46.23, 14.50)
T_A, T_B, T_C = 36000, 38400, 39000


def _baza(agency="1123"):
    c = db.connect(":memory:")
    db.init(c)
    ocena.init(c)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode, agency,"
              " network, shape_id) VALUES(?, 'R', 'A1', 'C', 'S', 'bus', ?, 'avtobus', 'sh')",
              (TRIP, agency))
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "Alfa", *A), ("B", "Beta", *B), ("C", "Cena", *C)])
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [(TRIP, 1, "A", T_A, T_A), (TRIP, 2, "B", T_B, T_B), (TRIP, 3, "C", T_C, T_C)])
    tocke = [[A[0] + (C[0] - A[0]) * i / 230, A[1]] for i in range(231)]
    c.execute("INSERT INTO shape(shape_id, points) VALUES('sh', ?)", (json.dumps([tocke]),))
    c.commit()
    db.fill_trip_window(c)
    deljenje._predpomnilnik.clear()
    deljenje._vzorci.clear()
    return c


@pytest.fixture(autouse=True)
def _cisto():
    odsek._profil, odsek._profil_znacka = {}, None
    yield
    deljenje._predpomnilnik.clear()


def _voznja(c, dan, odhod_ts, trajanje_s):
    """Prehoda A in B ter lege vmes, vsakih 30 s, enakomerno."""
    prihod = odhod_ts + trajanje_s
    polnoc = stats.polnoc(dan)
    c.executemany("INSERT INTO gps_prehod(service_date, trip_id, stop_seq, zamuda_s, prehod_ts,"
                  " je_cilj, dopolnjen, zapisano_ts) VALUES(?,?,?,?,?,0,0,?)",
                  [(dan, TRIP, 1, odhod_ts - polnoc - T_A, odhod_ts, odhod_ts),
                   (dan, TRIP, 2, prihod - polnoc - T_B, prihod, prihod)])
    for ts in range(odhod_ts + 30, prihod, 30):
        d = (ts - odhod_ts) / trajanje_s
        c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon, vozilo) VALUES(?,?,?,?,?,'x')",
                  (dan, TRIP, ts, A[0] + (B[0] - A[0]) * d, A[1]))


def _dnevi(n=3):
    return [(datetime.fromisoformat(DAN) - timedelta(days=i)).date().isoformat() for i in range(1, n + 1)]


def _profil_iz(c, n=3, trajanje_s=1800):
    for d in _dnevi(n):
        _voznja(c, d, stats.polnoc(d) + T_A, trajanje_s)
    c.commit()
    return odsek.dopolni(c, datetime(2026, 11, 3, 3, 30, tzinfo=stats.TZ))


def _lega(c, delez, ts):
    c.execute("INSERT OR REPLACE INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon) "
              "VALUES(?,?,?,?,?)", (TRIP, DAN, ts, A[0] + (B[0] - A[0]) * delez, A[1]))


def test_profil_pove_prihod_preden_vozilo_pride():
    """Vozni red 40 min, vozilo običajno 30: na polovici je do B še ~15 min,
    čeprav vozni red in prenos pravita drugače."""
    c = _baza()
    assert odsek.dopolni(c, datetime(2026, 11, 3, 3, 30, tzinfo=stats.TZ)) == []
    dnevi = _profil_iz(c)
    assert dnevi == sorted(_dnevi())[-len(dnevi):] and len(dnevi) == 3
    assert c.execute("SELECT COUNT(DISTINCT dan) FROM odsek_profil").fetchone()[0] == 3
    # Odpelje 5 min pozno, po 15 min vožnje je na polovici: pride 35 min po voznorednem
    # odhodu, 5 min pred voznim redom B, čeprav prenos pravi +5.
    ts = POLNOC + T_A + 300 + 900
    _lega(c, 0.5, ts)
    o = odsek.ocena(c, TRIP, DAN, 1, ts)
    assert o["vir"] == "profil" and o["seq"] == 2
    assert abs(o["zamuda_s"] - (-300)) <= 90     # koš je 5 % odseka


def test_brez_treh_dni_velja_razdalja_sele_od_tretjine():
    """Razdalja sredi mesta laže (`RAZDALJA_OD`), zato pred tem nič."""
    c = _baza()
    _profil_iz(c, n=2)
    ts = POLNOC + T_A + 600
    _lega(c, 0.1, ts)
    assert odsek.ocena(c, TRIP, DAN, 1, ts) is None
    _lega(c, 0.5, ts)
    o = odsek.ocena(c, TRIP, DAN, 1, ts)
    assert o["vir"] == "razdalja"
    assert abs(o["zamuda_s"] - (600 - 1200)) < 60     # 10 min vožnje za 20 min voznega reda


def test_ocene_ni_kjer_ne_velja():
    c = _baza()
    _profil_iz(c)
    ts = POLNOC + T_A + 900
    assert odsek.ocena(c, TRIP, DAN, 1, ts) is None, "brez lege"
    _lega(c, 0.5, ts - 400)
    assert odsek.ocena(c, TRIP, DAN, 1, ts) is None, "stara lega"
    _lega(c, 0.5, ts)
    assert odsek.ocena(c, TRIP, DAN, 2, ts) is None, "kratek odsek"
    assert odsek.ocena(c, TRIP, DAN, 3, ts) is None, "konec vožnje"
    c.execute("UPDATE vehicle_now SET lat = 46.0, lon = 14.7")
    assert odsek.ocena(c, TRIP, DAN, 1, ts) is None, "lega ni na trasi"


def test_mestni_prevoznik_nima_ocene():
    """Samo prevozniki, ki jih meri prehod iz lege (`config.NAP_PREVOZNIKI`)."""
    c = _baza(agency="lpp")
    ts = POLNOC + T_A + 900
    _lega(c, 0.5, ts)
    assert odsek.ocena(c, TRIP, DAN, 1, ts) is None


def test_dan_se_racuna_enkrat_in_star_profil_izgine():
    c = _baza()
    _profil_iz(c)
    assert odsek.dopolni(c, datetime(2026, 11, 3, 4, 0, tzinfo=stats.TZ)) == []
    c.execute("INSERT INTO odsek_profil VALUES('x', 'y', 1, 0, '2026-09-01', 60, 1)")
    c.commit()
    odsek.dopolni(c, datetime(2026, 11, 4, 3, 30, tzinfo=stats.TZ))
    assert c.execute("SELECT COUNT(*) FROM odsek_profil WHERE od_ime = 'x'").fetchone()[0] == 0


def test_senca_zapise_oceno_iz_lege_ob_prikazu(monkeypatch):
    """Parna primerjava: lega v isti vrstici kot prikaz in prenos. Izhodišče je
    naslednji postanek, postanek za njim gre skozi `predict`."""
    c = _baza()
    _profil_iz(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S', ?)", (DAN,))
    ts = POLNOC + T_A + 1560        # 26 min po odhodu, B po voznem redu čez 14 min
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES(?,?,1,300,300,?)", (TRIP, DAN, POLNOC + T_A + 300))
    _lega(c, 0.8, ts)
    c.commit()
    monkeypatch.setattr(ocena, "_v_vzorcu", lambda *a: True)
    monkeypatch.setattr(stats, "predict", lambda *a, **k: [
        {"stop_seq": 2, "predicted_delay_s": 300, "own_delay_s": 300, "n_samples": 5},
        {"stop_seq": 3, "predicted_delay_s": 400, "own_delay_s": 400, "n_samples": 5}]
        if a[2] == 1 else [{"stop_seq": 3, "predicted_delay_s": -200, "own_delay_s": -200, "n_samples": 5}])
    ocena.snapshot(c, datetime.fromtimestamp(ts, ocena.TZ))
    r = c.execute("SELECT * FROM napoved WHERE stop_seq = 2").fetchone()
    assert r["carry_s"] == 300 and r["ours_s"] == 300
    assert r["lega_vir"] == "profil" and r["ours_lega_s"] == r["lega_s"] < 0

    # Resnica in poročilo: iste vrstice, po viru.
    c.execute("UPDATE napoved SET actual_s = -300, service_date = date('now')")
    izid = ocena.report(c)
    x = izid["iz_lege"]["profil"]
    assert x["iz_lege"]["n"] == x["prenos"]["n"] == 1
    assert x["iz_lege"]["mae_min"] < x["prenos"]["mae_min"]
    assert izid["iz_lege"]["razdalja"]["iz_lege"]["n"] == 0
