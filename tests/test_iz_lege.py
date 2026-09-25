"""Zamuda iz lege vozila za vožnje, ki jih feed zamud ne nosi.

Proga je ravna črta vzhodno od (46, 14): postajališča A, B, C, D so 0,01°
(~773 m) narazen, vozni red na pet minut. Vozilo, ki je ob 10:12:00 malo pred
C in ob 10:12:20 malo za njim, je C prevozilo ob 10:12:10 -- torej +130 s.

    ./venv/bin/python -m pytest tests/test_iz_lege.py -q
"""
from __future__ import annotations

import json
import time
from datetime import date, datetime

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import db, deljenje, iz_lege

DAN = date.today().isoformat()
POLNOC = datetime.fromisoformat(DAN).replace(tzinfo=iz_lege.TZ).timestamp()
LON = {"A": 14.00, "B": 14.01, "C": 14.02, "D": 14.03}


@pytest.fixture(autouse=True)
def _cist_spomin():
    for s in (iz_lege._v_feedu, iz_lege._sled, deljenje._predpomnilnik, deljenje._trase):
        s.clear()
    iz_lege._prvic = None
    yield
    for s in (iz_lege._v_feedu, iz_lege._sled, deljenje._predpomnilnik, deljenje._trase):
        s.clear()
    iz_lege._prvic = None


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46.0,?)",
                  [(k, k, v) for k, v in LON.items()])
    tocke = [[46.0, 14.0 + i * 0.001] for i in range(31)]
    c.execute("INSERT INTO shape(shape_id, points) VALUES('sh', ?)", (json.dumps([tocke]),))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id,"
              " mode, agency, network) VALUES('n', 'r', 'N1', 'D', 'S', 'sh', 'bus', '1119', 'avtobus')")
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('n',?,?,?,?)",
                  [(1, "A", None, 36000), (2, "B", 36300, 36300),
                   (3, "C", 36600, 36600), (4, "D", 36900, None)])
    db.fill_trip_window(c)
    c.commit()
    return c


def _ts(ura_s):
    return int(POLNOC + ura_s)


def _run(c):
    return [tuple(r) for r in c.execute(
        "SELECT stop_seq, delay_arr, delay_dep FROM run ORDER BY stop_seq")]


def test_prehod_postanka_da_zamudo():
    c = _baza()
    assert iz_lege.opazuj(c, "n", DAN, _ts(36720), 46.0, 14.019) == 0
    assert iz_lege.opazuj(c, "n", DAN, _ts(36740), 46.0, 14.021) == 1
    assert _run(c) == [(3, None, 130)]
    # Prehod je potrjen: vrednost nosi čas lege PO prehodu.
    assert c.execute("SELECT feed_ts FROM run").fetchone()[0] == _ts(36740)


def test_koncna_postaja_je_prihod():
    """Za D je vozni red samo prihod (36 900); lega za koncem trase je na njem."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(37000), 46.0, 14.029)
    iz_lege.opazuj(c, "n", DAN, _ts(37020), 46.0, 14.0305)
    assert _run(c) == [(4, 120, None)]


def test_izhodisca_ne_merimo():
    """Pred odhodom vozilo kroži po postajališču; prehod izhodišča laže."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(35400), 46.0, 13.9995)
    iz_lege.opazuj(c, "n", DAN, _ts(35420), 46.0, 14.0005)
    assert _run(c) == []


def test_skok_lege_ni_prehod():
    """Dva kilometra v 20 s je napačna projekcija, ne vožnja."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36400), 46.0, 14.001)
    iz_lege.opazuj(c, "n", DAN, _ts(36420), 46.0, 14.027)
    assert _run(c) == []


def test_predolg_razmik_ni_prehod():
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36500), 46.0, 14.019)
    iz_lege.opazuj(c, "n", DAN, _ts(36500 + iz_lege.NAJVEC_RAZMIK_S + 1), 46.0, 14.021)
    assert _run(c) == []


def test_tresenje_ob_postajaliscu_da_en_prehod():
    c = _baza()
    for ura, lon in ((36720, 14.019), (36740, 14.021), (36760, 14.0195), (36780, 14.0212)):
        iz_lege.opazuj(c, "n", DAN, _ts(ura), 46.0, lon)
    assert _run(c) == [(3, None, 130)]


def test_lega_dalec_od_trase_se_ne_steje():
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36720), 46.0, 14.019)
    iz_lege.opazuj(c, "n", DAN, _ts(36740), 46.01, 14.021)      # 1,1 km severno
    assert _run(c) == []


def _lege(*tocke):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    for i, (ura, lon) in enumerate(tocke):
        e = f.entity.add()
        e.id = str(i)
        e.vehicle.trip.trip_id = "n"
        e.vehicle.trip.start_date = DAN.replace("-", "")
        e.vehicle.timestamp = _ts(ura)
        e.vehicle.position.latitude, e.vehicle.position.longitude = 46.0, lon
    return f


def test_iz_feeda_samo_za_vozje_ki_jih_feed_zamud_ne_nosi():
    c = _baza()
    iz_lege.zabelezi_feed(["n"], time.time() - 120)             # feed jo nosi
    iz_lege.iz_feeda(c, _lege((36720, 14.019)))
    iz_lege.iz_feeda(c, _lege((36740, 14.021)))
    assert _run(c) == []

    iz_lege._v_feedu.clear()                                     # feed jo izpušča
    iz_lege.iz_feeda(c, _lege((36720, 14.019)))
    assert iz_lege.iz_feeda(c, _lege((36740, 14.021))) == 1
    assert _run(c) == [(3, None, 130)]


def test_pred_prvim_branjem_feeda_nic():
    """Po zagonu še ne vemo, katere vožnje feed nosi -- ne ugibamo."""
    c = _baza()
    iz_lege.iz_feeda(c, _lege((36720, 14.019)))
    iz_lege.iz_feeda(c, _lege((36740, 14.021)))
    assert _run(c) == []
