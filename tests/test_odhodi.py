"""Odhodna tabla prek API (`/api/departures`): kar rabi widget na telefonu.

Widget shrani prvih 30 vrstic in jih vprasa vsakih 15 minut prek mobilnega
omrezja. Mestno postajalisce ima v treh urah tudi 150 odhodov, zato `limit`.
"""
from __future__ import annotations

import pytest

from kajros import api, db


@pytest.fixture()
def conn(monkeypatch):
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)", [
        ("A", "Postaja", 46.05, 14.50), ("B", "Konec", 46.06, 14.51)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', '2026-09-22')")
    for i in range(5):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                  "                 mode, agency, network) "
                  "VALUES(?, 'r', ?, 'Konec', 'S1', 'rail', '1', 'zeleznica')",
                  (f"t{i}", f"LP {2400 + i}"))
        c.executemany(
            "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
            [(f"t{i}", 1, "A", 30000 + i * 600, 30000 + i * 600),
             (f"t{i}", 2, "B", 30600 + i * 600, 30600 + i * 600)])
    db.fill_trip_window(c)
    c.commit()
    monkeypatch.setattr(api, "_conn", lambda: c)
    return c


def _tabla(**kw):
    return api.api_departures(station="Postaja", date="2026-09-22", from_time="08:00",
                              window=240, kind="odhodi", network="zeleznica", smer=None,
                              **kw)


def test_brez_omejitve_cela_tabla(conn):
    assert len(_tabla(limit=None)["board"]) == 5


def test_omejitev_vzame_prve_po_uri(conn):
    vrstice = _tabla(limit=2)["board"]
    assert [r["train_no"] for r in vrstice] == ["LP 2400", "LP 2401"]
