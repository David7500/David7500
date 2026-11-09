"""Model »podobni dnevi + veriga« v senci (9. 11. 2026,
docs/presoja/2026-11-09-napoved/zapis.md).

`stats.predict(podobni_do=...)` vrne `podobni_delay_s` in `podobni_varna_s`,
`ocena.snapshot` ju zapiše v `napoved`, `ocena.report` izpiše. Prikaz ju ne bere.

    ./venv/bin/python -m pytest tests/test_podobni.py -q
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from kajros import backtest, db, ocena, stats


def _pred(dni: int) -> str:
    return (date.today() - timedelta(days=dni)).isoformat()


@pytest.fixture()
def conn():
    """RG 318: vlak običajno zamuja 18–19 min in zamude po progi ne spremeni.
    Trije nedavni dnevi imajo pri Lazah osamelec »V« (240–360 s med 1200 in
    1500+): edini dnevi v razredu 2–10 min."""
    c = db.connect(":memory:")
    db.init(c)
    imena = ["Litija", "Kresnice", "Jevnica", "Laze", "Ljubljana Zalog", "Ljubljana Polje"]
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46.0,14.8)",
                  [(str(k), ime) for k, ime in enumerate(imena, 1)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', '2026-08-31')")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id) "
              "VALUES('t1','r1','RG 318','Dobova - Jesenice','S1')")
    # Postanki po minuto (brez rezerve), 10 min narazen: Kresnice 07:20/07:21,
    # Polje 08:00.
    c.executemany(
        "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('t1',?,?,?,?)",
        [(k, str(k), None if k == 1 else 25200 + k * 600, 25260 + k * 600)
         for k in range(1, 7)])
    db.fill_trip_window(c)
    for dni in range(1, 41):
        if dni in (2, 4, 6):
            dan = {2: 1200, 3: 1200, 4: 240 + 60 * (dni // 3), 5: 1500, 6: 1500}
        else:
            d = 1080 + 60 * (dni % 3)
            dan = {k: d for k in range(2, 7)}
        for seq, d in dan.items():
            # Računan datum: OR IGNORE (CLAUDE.md, »trd datum + računan datum«).
            c.execute("INSERT OR IGNORE INTO run(trip_id,service_date,stop_seq,delay_arr,"
                      "delay_dep,feed_ts) VALUES('t1',?,?,?,?,4102444800)",
                      (_pred(dni), seq, d, d))
    c.commit()
    return c


def _na(napoved, ime):
    return next(x for x in napoved if x["name"] == ime)


def test_utezen_kvantil():
    assert stats.utezen_kvantil([(10, 1), (20, 1), (30, 1)], 0.5) == 20
    assert stats.utezen_kvantil([(0, 1), (100, 1)], 0.5) == 50
    assert stats.utezen_kvantil([], 0.5) is None
    # Zvezen v uteži: dan s skoraj nič teže ne premakne mediane.
    brez = stats.utezen_kvantil([(0, 1), (10, 1), (20, 1)], 0.5)
    z = stats.utezen_kvantil([(0, 1), (10, 1), (20, 1), (5000, 0.001)], 0.5)
    assert abs(z - brez) < 0.1


def test_rg318_trije_slabi_dnevi_ne_premaknejo_napovedi(conn):
    """Razred skoči na +17 min, podobni ostanejo pri izmerjeni zamudi."""
    n = stats.predict(conn, "RG 318", 4, 420, podobni_do=6)
    zalog = _na(n, "Ljubljana Zalog")
    assert zalog["predicted_delay_s"] == 1020           # 420 + odrezan ostanek 600
    assert abs(zalog["podobni_delay_s"] - 420) <= 60
    assert zalog["podobni_varna_s"] <= zalog["podobni_delay_s"]


def test_sosednji_izhodisci_dasta_isto(conn):
    """Zveznost: Laze +7 in nato Zalog +7 morata za Polje napovedati isto."""
    iz_laz = _na(stats.predict(conn, "RG 318", 4, 420, podobni_do=6), "Ljubljana Polje")
    iz_zaloga = _na(stats.predict(conn, "RG 318", 5, 420, podobni_do=6), "Ljubljana Polje")
    assert abs(iz_laz["predicted_delay_s"] - iz_zaloga["predicted_delay_s"]) >= 300
    assert abs(iz_laz["podobni_delay_s"] - iz_zaloga["podobni_delay_s"]) <= 60


def test_obicajen_dan_ostane_pri_obicajnem(conn):
    polje = _na(stats.predict(conn, "RG 318", 3, 1140, podobni_do=6), "Ljubljana Polje")
    assert polje["podobni_delay_s"] == 1140 and polje["podobni_varna_s"] == 1140


def test_brez_zahteve_in_za_avtobus_none(conn):
    assert all(x["podobni_delay_s"] is None for x in stats.predict(conn, "RG 318", 3, 600))
    n = stats.predict(conn, "RG 318", 3, 600, podobni_do=5)
    assert [x["podobni_delay_s"] is not None for x in n] == [True, True, False]
    conn.execute("UPDATE trip SET network = 'avtobus'")
    conn.commit()
    assert all(x["podobni_delay_s"] is None
               for x in stats.predict(conn, "RG 318", 3, 600, podobni_do=6))


def test_brez_zgodovine_je_rezerva(conn):
    conn.execute("DELETE FROM run")
    conn.commit()
    polje = _na(stats.predict(conn, "RG 318", 3, 600, podobni_do=6), "Ljubljana Polje")
    assert polje["podobni_delay_s"] == polje["podobni_varna_s"] == 600


def test_backtest_klice_isto_funkcijo(conn):
    """`backtest` model `podobni` in `predict` dasta iz iste zgodovine isto."""
    vsi = backtest.build_tasks(conn, "zeleznica", "", oznaci=True)
    cisti = [t for t in vsi if t["ok"]]
    dan = _pred(1)
    t = next(x for x in cisti if x["day"] == dan and x["i"] == 3 and x["j"] == 6)
    for ime, kljuc in (("podobni", "podobni_delay_s"), ("podobni varna", "podobni_varna_s")):
        iz_backtesta = backtest.MODELI_VARNI[ime][0](cisti)(t)
        iz_predict = _na(stats.predict(conn, "RG 318", 3, t["d_i"], exclude_date=dan,
                                       service_date=dan, podobni_do=6),
                         "Ljubljana Polje")[kljuc]
        assert iz_backtesta == iz_predict


def test_snapshot_zapise_podobne(conn):
    ocena.init(conn)
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                 " feed_ts) VALUES('t1','2026-08-31',2,420,420,4102444800)")
    # 07:36: vlak je odpeljal s Kresnic (07:21 + 7 min), Polje (08:01) je čez 25 min.
    ocena.snapshot(conn, datetime(2026, 8, 31, tzinfo=ocena.TZ) + timedelta(seconds=27360))
    v = conn.execute("SELECT * FROM napoved WHERE from_seq IS NOT NULL").fetchall()
    assert v and all(r["podobni_s"] is not None and r["podobni_varna_s"] <= r["podobni_s"]
                     for r in v)


def test_report_ima_vrstici_podobnih(conn):
    ocena.init(conn)
    conn.execute(
        "INSERT INTO napoved(trip_id, service_date, stop_seq, network, made_ts, horizon_s,"
        " current_s, from_seq, ours_s, ours_own_s, carry_s, actual_s, podobni_s,"
        " podobni_varna_s) VALUES('a', ?, 3, 'zeleznica', 0, 1500, 600, 2, 450, 450, 600,"
        " 400, 400, 340)", (_pred(1),))
    conn.commit()
    r = ocena.report(conn, days=30)["po_omrezju"]["zeleznica"]
    assert r["podobni"]["n"] == 1 and r["podobni"]["mae_min"] == 0
    assert r["podobni_varna"]["mae_min"] == 1
