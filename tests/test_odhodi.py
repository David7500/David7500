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


# ---------- relacija (`/api/connections`): widget s ciljem ----------

def _zveze(**kw):
    return api.api_connections(from_="Postaja", to="Konec", date="2026-09-22",
                               with_transfers=False, network="zeleznica", **kw)


def test_zveze_brez_od_ves_dan(conn):
    assert len(_zveze(od=None, limit=None)["connections"]) == 5


def test_zveze_od_ure_in_omejene(conn):
    # Odhodi so ob 8:20, 8:30, 8:40, 8:50 in 9:00 (30000 s + 600 s na vožnjo).
    z = _zveze(od="08:35", limit=2)["connections"]
    assert [r["train_no"] for r in z] == ["LP 2402", "LP 2403"]


def test_zveze_od_obdrzi_zamujeni_vlak(conn, monkeypatch):
    """Rez gre po pričakovanem odhodu: LP 2401 (8:30) z zamudo 10 min ob
    8:35 še ni odpeljal. Po voznem redu bi šel ven -- in widget bi kazal
    naslednjega, medtem ko zamujeni še stoji na peronu."""
    from kajros import stats
    prava = stats.connections

    def z_zamudo(*a, **kw):
        vrstice = prava(*a, **kw)
        for r in vrstice:
            if r["train_no"] == "LP 2401":
                r["delay_s"] = 600
        return vrstice

    monkeypatch.setattr(stats, "connections", z_zamudo)
    z = _zveze(od="08:35", limit=2)["connections"]
    assert [r["train_no"] for r in z] == ["LP 2401", "LP 2402"]


def test_od_na_dan_premika_ure():
    """25. 10. 2026 vozni red do treh šteje od 01:00 poletnega časa
    (`stats.polnoc`): ura stene 01:30 je `dep_s` 1800, ne 5400."""
    from kajros import stats
    assert api._ura_ts("2026-10-25", "01:30", "od") - stats.polnoc("2026-10-25") == 1800
    assert api._ura_ts("2026-09-22", "08:35", "od") - stats.polnoc("2026-09-22") == 30900


def test_napacna_ura_je_napaka(conn):
    with pytest.raises(api.HTTPException):
        _zveze(od="25:99", limit=None)
