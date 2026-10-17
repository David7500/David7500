"""Meja meritve (`stats.last_measured`, `api._LIVE_SQL`): ničla po zamudi.

Ničla (pri vlaku do 2 min) po zamudi vsaj 5 min velja, kadar jo pojasni
rezerva voznega reda (dolg postanek), sicer ne -- SŽ obtičali vlak riše po
voznem redu. Do 17. 10. 2026 ni veljala nikoli in prikaz je vlaku, ki je na
dolgem postanku res nadoknadil, ostal na stari zamudi (nevarna smer).

    ./venv/bin/python -m pytest tests/test_meja_meritve.py -q
"""
from __future__ import annotations

import pytest

from kajros import db

D = "2026-10-17"


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (D,))
    return c


def _vlak(c, trip_id, postanki, network="zeleznica", feed_ts=4102444800):
    """postanki = [(seq, prihod_s, odhod_s, zamuda_s)]."""
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network) "
              "VALUES(?, 'r', ?, 'S1', 'rail', ?)", (trip_id, trip_id, network))
    for seq, arr, dep, zamuda in postanki:
        c.execute("INSERT OR IGNORE INTO station(stop_id, name, lat, lon) VALUES(?, ?, 46, 14)",
                  (f"P{seq}", f"Postaja {seq}"))
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  (trip_id, seq, f"P{seq}", arr, dep))
        if zamuda is not None:
            c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts) "
                      "VALUES(?, ?, ?, ?, ?)", (trip_id, D, seq, zamuda, feed_ts))


def test_nicla_na_dolgem_postanku_velja(conn):
    """LPV 2419 16. 10. 2026: Otoče +10, Podnart (postanek 16 min) odpeljal
    točen, do cilja 0. Prikaz je 45 min trdil +10 -- potnik bi vlak zamudil."""
    from kajros import stats
    h = 3600
    _vlak(conn, "lpv", [(1, None, 8 * h, 600), (2, 8 * h + 600, 8 * h + 1560, 0),
                        (3, 8 * h + 1900, 8 * h + 1900, 0), (4, 9 * h, None, None)])
    m = stats.last_measured(conn, D, ["lpv"], 8 * h + 2000)["lpv"]
    assert (m["stop_seq"], m["delay_s"]) == (3, 0)


def test_nicla_brez_rezerve_ne_velja(conn):
    """RG 210 17. 10. 2026: Brezovica +16, nato SŽ uro riše po voznem redu z 0
    (vlak je stal); rezerve med postajama ni, zato ničla ni meritev."""
    from kajros import stats
    h = 3600
    _vlak(conn, "rg", [(1, None, 8 * h, 960), (2, 8 * h + 300, 8 * h + 330, 0),
                       (3, 8 * h + 600, 8 * h + 630, 0), (4, 9 * h, None, None)])
    m = stats.last_measured(conn, D, ["rg"], 8 * h + 2000)["rg"]
    assert (m["stop_seq"], m["delay_s"]) == (1, 960)
    # Vlak tudi s +1 (LP 3217 16. 10.: SŽ +1 po voznem redu, vlak +16).
    _vlak(conn, "lp", [(1, None, 8 * h, 960), (2, 8 * h + 300, 8 * h + 330, 60),
                       (3, 9 * h, None, None)])
    m = stats.last_measured(conn, D, ["lp"], 8 * h + 2000)["lp"]
    assert (m["stop_seq"], m["delay_s"]) == (1, 960)
    # Avtobus s +1 pa velja: avtobus nadoknadi brez postanka (prej in zdaj).
    _vlak(conn, "bus", [(1, None, 8 * h, 960), (2, 8 * h + 300, 8 * h + 330, 60),
                        (3, 9 * h, None, None)], network="avtobus")
    m = stats.last_measured(conn, D, ["bus"], 8 * h + 2000)["bus"]
    assert (m["stop_seq"], m["delay_s"]) == (2, 60)


def test_zemljevid_isto_pravilo(conn):
    """`/api/live` (zemljevid) ima pravilo v svoji poizvedbi -- isti izid."""
    from kajros import api
    h = 3600
    _vlak(conn, "lpv", [(1, None, 8 * h, 600), (2, 8 * h + 600, 8 * h + 1560, 0),
                        (3, 8 * h + 1900, 8 * h + 1900, 0), (4, 9 * h, None, None)])
    _vlak(conn, "rg", [(1, None, 8 * h, 960), (2, 8 * h + 300, 8 * h + 330, 0),
                       (3, 8 * h + 600, 8 * h + 630, 0), (4, 9 * h, None, None)])
    db.fill_trip_window(conn)
    vrstice = {r["trip_id"]: (r["stop_seq"], r["delay_s"])
               for r in api._live_rows(conn, D, 8 * h + 2000, network="zeleznica")}
    assert vrstice == {"lpv": (3, 0), "rg": (1, 960)}
