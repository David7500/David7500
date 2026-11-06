"""Varna napoved v senci (6. 11. 2026, docs/presoja/vlaki-prenova/modeli.md).

`stats.predict` poleg `predicted_delay_s` vrne `varna_delay_s`, `ocena.snapshot`
jo zapiše v `napoved.varna_s`, `ocena.report` jo izpiše ob naši oceni. Prikaz
je ne bere.

    ./venv/bin/python -m pytest tests/test_varna.py -q
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

import pytest

from kajros import backtest, db, ocena, stats


def _pred(dni: int) -> str:
    return (date.today() - timedelta(days=dni)).isoformat()


def _ob(ura_s: int) -> datetime:
    return datetime(2026, 8, 31, tzinfo=ocena.TZ) + timedelta(seconds=ura_s)


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "Ajdovščina", 45.9, 13.9), ("Z", "Zidani Most", 46.1, 15.0),
                   ("C", "Celje", 46.2, 15.3)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', '2026-08-31')")
    # A 08:00 -> Z 09:00/09:05 (rezerva 180 s) -> C 10:00
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t1','r1','IC 1','A - C','S1')")
    c.executemany(
        "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('t1',?,?,?,?)",
        [(1, "A", None, 28800), (2, "Z", 32400, 32700), (3, "C", 36000, None)])
    db.fill_trip_window(c)
    # Zgodovina: na Zidanem Mostu vedno +10 min, v Celju različno.
    for dni, d_c in enumerate([300, 360, 420, 480, 540, 600], start=1):
        for seq, d in ((2, 600), (3, d_c)):
            c.execute("INSERT OR IGNORE INTO run(trip_id,service_date,stop_seq,delay_arr,"
                      "delay_dep,feed_ts) VALUES('t1',?,?,?,?,4102444800)",
                      (_pred(dni), seq, d, d))
    c.commit()
    return c


def _celje(napoved):
    return next(x for x in napoved if x["name"] == "Celje")


def test_varna_ni_nad_natancno_na_istem_stanju(conn):
    """Isti razred, isti dnevi: kvantil 0,25 ostanka ≤ mediana. Ostanki so
    -300, -240, -180, -120, -60, 0 (mediana -150, kvantil -225)."""
    c = _celje(stats.predict(conn, "IC 1", 2, 600))
    assert c["predicted_delay_s"] == 450 and c["varna_delay_s"] == 375
    assert c["varna_delay_s"] <= c["predicted_delay_s"]


def test_varna_ne_vzame_prevoznika(conn):
    """Prevoznik objavi +30 min: `predicted_delay_s` gre navzgor, varna ne."""
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", ("2026-08-30",))
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('t1','2026-08-31',2,600,600,4102444800)")
    conn.execute("INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
                 "VALUES('t1','2026-08-31',3,1800,1800,4102444800)")
    conn.commit()
    c = _celje(stats.predict(conn, "IC 1", 2, 600, service_date="2026-08-31",
                                  exclude_date="2026-08-31"))
    assert c["predicted_delay_s"] == 1800 and c["varna_delay_s"] == 375


def test_varna_izpusti_prikazani_dan(conn):
    brez = _celje(stats.predict(conn, "IC 1", 2, 600))["varna_delay_s"]
    # dan z najnižjim ostankom (Celje 300) izpuščen -> kvantil se premakne navzgor
    iz = _celje(stats.predict(conn, "IC 1", 2, 600, exclude_date=_pred(1)))["varna_delay_s"]
    assert iz > brez


def test_varna_za_avtobus_je_none(conn):
    conn.execute("UPDATE trip SET network = 'avtobus'")
    conn.commit()
    assert all(x["varna_delay_s"] is None for x in stats.predict(conn, "IC 1", 2, 600))


def test_varna_brez_zgodovine_je_rezerva(conn):
    conn.execute("DELETE FROM run")
    conn.commit()
    c = _celje(stats.predict(conn, "IC 1", 2, 600))
    assert c["varna_delay_s"] == c["predicted_delay_s"] == 600


def test_backtest_in_predict_imata_isti_ostanek(conn):
    """Backtestov `varna_q 0,25` in `predict` kličeta isto funkcijo: iz istih
    ostankov dasta isto številko."""
    ost = [-300, -240, -180, -120, -60, 0]
    t = {"train_no": "IC 1", "i": 2, "j": 3, "d_i": 600, "d_j": 0, "slack": 180,
         "day": "x", "network": "zeleznica"}
    odlocitev = backtest._varna_q(0.25)
    assert odlocitev(t, 600, 600, ost, ost) == 600 + stats.varni_ostanek(
        ost, ost, 600, "zeleznica") == 375
    assert _celje(stats.predict(conn, "IC 1", 2, 600))["varna_delay_s"] == 375


def test_snapshot_zapise_varno(conn):
    ocena.init(conn)
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                 " feed_ts) VALUES('t1','2026-08-31',2,600,600,4102444800)")
    ocena.snapshot(conn, _ob(34500))
    v = conn.execute("SELECT * FROM napoved").fetchone()
    assert v["stop_seq"] == 3 and v["from_seq"] == 2
    assert v["varna_s"] == 375 and v["ours_s"] == 450


def test_snapshot_pred_odhodom_ima_varno_enako_vozni_red(conn):
    ocena.init(conn)
    ocena.snapshot(conn, _ob(34500))
    v = conn.execute("SELECT * FROM napoved").fetchone()
    assert v["from_seq"] is None and v["varna_s"] == 0


def _vstavi(conn, tid, varna, ours, actual, from_seq=2):
    conn.execute(
        "INSERT INTO napoved(trip_id, service_date, stop_seq, network, made_ts, horizon_s,"
        " current_s, from_seq, ours_s, ours_own_s, carry_s, actual_s, varna_s)"
        " VALUES(?, ?, 3, 'zeleznica', 0, 1500, ?, ?, ?, ?, 600, ?, ?)",
        (tid, _pred(1), None if from_seq is None else 600, from_seq, ours, ours, actual, varna))


def test_report_izpise_varno_in_ne_steje_null(conn):
    ocena.init(conn)
    _vstavi(conn, "a", 400, 450, 400)
    _vstavi(conn, "b", None, 450, 400)          # stara vrstica, pred stolpcem
    _vstavi(conn, "c", 0, 0, 100, from_seq=None)
    conn.commit()
    r = ocena.report(conn, days=30)
    assert r["skupaj"]["nasa"]["n"] == 2 and r["skupaj"]["varna"]["n"] == 1
    assert r["skupaj"]["parno"]["varna"]["n"] == 0        # prevoznika ni
    assert r["po_omrezju"]["zeleznica"]["varna"]["mae_min"] == 0
    assert r["pred_odhodom"]["zeleznica"]["varna"]["n"] == 1


def test_cli_izpise_vrstico_varna(conn, capsys, monkeypatch):
    from kajros import cli
    ocena.init(conn)
    _vstavi(conn, "a", 400, 450, 400)
    conn.commit()
    monkeypatch.setattr(cli.db, "connect", lambda *a, **k: conn)
    cli.cmd_ocena(type("A", (), {"tick": False, "days": 30, "network": None})())
    assert "varna (senca)" in capsys.readouterr().out


def test_migracija_stare_sheme_doda_stolpec():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    stara = "\n".join(v for v in ocena.SHEMA.split("\n") if "varna_s" not in v)
    c.executescript(stara)
    assert "varna_s" not in {r[1] for r in c.execute("PRAGMA table_info(napoved)")}
    c.execute("INSERT INTO napoved(trip_id, service_date, stop_seq, network, made_ts, horizon_s)"
              " VALUES('t','d',1,'zeleznica',0,0)")
    ocena.init(c)
    assert "varna_s" in {r[1] for r in c.execute("PRAGMA table_info(napoved)")}
    assert c.execute("SELECT varna_s FROM napoved").fetchone()[0] is None
    ocena.init(c)                                            # drugič ne pade
