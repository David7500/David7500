"""Vozilo ima lego, feed zamud pa za njegovo vožnjo nima ničesar.

Od 21. 9. 2026 IJPP `trip_updates` ni nosil nobene vožnje z veljavnostjo od
21. 9. (Nomago ~430 na dan), `vehicle_positions` pa ista vozila da. Števec
`rt_neznanih` je bil zelen, ker šteje obratno.

    ./venv/bin/python -m pytest tests/test_lega_brez_zamude.py -q
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from kajros import collector, db

DANES = date.today()
ZDAJ = datetime(DANES.year, DANES.month, DANES.day, 12, 0, tzinfo=collector.TZ)


def _vozja(c, trip_id, agency, zacetek_s, konec_s):
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network)"
              " VALUES(?, 'r', 'N1', 'S', 'bus', ?, 'avtobus')", (trip_id, agency))
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [(trip_id, 1, "A", None, zacetek_s), (trip_id, 2, "B", konec_s, None)])


def _lega(c, trip_id, dan=DANES.isoformat(), pred_s=20):
    c.execute("INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon)"
              " VALUES(?, ?, ?, 46, 14)", (trip_id, dan, int(ZDAJ.timestamp()) - pred_s))


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    return c


def test_steje_vozilo_na_poti_brez_zamude():
    c = _baza()
    _vozja(c, "nov", "1119", 11 * 3600 + 30 * 60, 13 * 3600)     # na poti 30 min
    _vozja(c, "star", "1119", 11 * 3600 + 30 * 60, 13 * 3600)
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts)"
              " VALUES('star', ?, 1, 60, 0)", (DANES.isoformat(),))
    db.fill_trip_window(c)
    _lega(c, "nov")
    _lega(c, "star")
    assert collector.lega_brez_zamude(c, ZDAJ) == {"1119": [1, 2]}


def test_ne_steje_vozila_ki_je_komaj_odpeljalo_ali_je_ze_na_koncu():
    """Prvo sporočilo feeda lahko pride z zamudo; po koncu vožnje zamude ni več."""
    c = _baza()
    _vozja(c, "komaj", "1123", 12 * 3600 - 5 * 60, 13 * 3600)
    _vozja(c, "konec", "1123", 10 * 3600, 11 * 3600 + 50 * 60)
    db.fill_trip_window(c)
    _lega(c, "komaj")
    _lega(c, "konec")
    assert collector.lega_brez_zamude(c, ZDAJ) == {}


def test_ne_steje_stare_lege():
    c = _baza()
    _vozja(c, "t", "1119", 11 * 3600, 13 * 3600)
    db.fill_trip_window(c)
    _lega(c, "t", pred_s=collector.POSITION_FRESH_S + 60)
    assert collector.lega_brez_zamude(c, ZDAJ) == {}


def test_nocna_vozja_s_vcerajsnjim_dnem():
    """Vožnja z včerajšnjim prometnim dnem ima ure čez 24:00."""
    c = _baza()
    _vozja(c, "noc", "1119", 35 * 3600, 37 * 3600)                # 11:00-13:00 naslednji dan
    db.fill_trip_window(c)
    _lega(c, "noc", dan=(DANES - timedelta(days=1)).isoformat())
    assert collector.lega_brez_zamude(c, ZDAJ) == {"1119": [1, 1]}


def test_lpp_brez_dneva_v_legi_velja_danes():
    """Mestni LPP v legi ne pošlje prometnega dne."""
    c = _baza()
    _vozja(c, "d|v|p", "lpp", 11 * 3600, 13 * 3600)
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts)"
              " VALUES('d|v|p', ?, 1, 60, 0)", (DANES.isoformat(),))
    db.fill_trip_window(c)
    _lega(c, "d|v|p", dan=None)
    assert collector.lega_brez_zamude(c, ZDAJ) == {"lpp": [0, 1]}
