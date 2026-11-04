"""Vozilo po končni: feed mestnega LPP ga drži na stari vožnji.

LPP 9 proti Barju, 30. 10. 2026: prihoda na končno feed ne zazna, zamuda raste
z uro, vozilo pa že pelje nazaj (`docs/MERITVE.md`).
"""
from __future__ import annotations

from datetime import datetime

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import api, collector, db, stats
from kajros.deljenje import Trasa

DAN = "2026-10-30"
TRIP = "D|voznja|VZOREC"
RED_S = 38940                       # prihod na končno ob 10.49
KONCNA = (46.0270, 14.5000)
# Vozilo proti jugu do končne, nato nazaj: razdalja do končne okoli 1 km, 220 m, 110 m.
SEVER = (46.0360, 14.5000)
BLIZU = (46.0290, 14.5000)
TIK = (46.0280, 14.5000)


def _ob(h, m):
    return int(datetime(2026, 10, 30, h, m, tzinfo=stats.TZ).timestamp())


@pytest.fixture(autouse=True)
def _cisto():
    collector._najblizje_koncni.clear()


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
              " agency, network) VALUES(?, 'R9', '9', 'ŠTEPANJSKO - BARJE P+R', 'D', 'bus',"
              " 'lpp', 'avtobus')", (TRIP,))
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "Predzadnja", 46.0330, 14.5000), ("B", "BARJE P+R", *KONCNA)])
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [(TRIP, 1, "A", 38700, 38700), (TRIP, 2, "B", RED_S, None)])
    db.fill_trip_window(c)
    return c


def _branje(c, kje, ts, zamuda):
    """Eno branje LPP: lega vozila in napoved prihoda na končno."""
    c.execute("INSERT INTO vehicle_now(trip_id, seen_ts, lat, lon) VALUES(?,?,?,?) "
              "ON CONFLICT(trip_id) DO UPDATE SET seen_ts=excluded.seen_ts, "
              "lat=excluded.lat, lon=excluded.lon", (TRIP, ts, *kje))
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    f.header.timestamp = ts
    e = f.entity.add(id="t")
    e.trip_update.trip.trip_id = TRIP
    e.trip_update.trip.route_id = "R9"
    e.trip_update.trip.start_date = DAN.replace("-", "")
    e.trip_update.timestamp = ts
    u = e.trip_update.stop_time_update.add(stop_sequence=2, stop_id="B")
    u.arrival.time = stats.polnoc(DAN) + RED_S + zamuda
    return collector.ingest(c, f, vir="lpp")


def _zapisano(c):
    return c.execute("SELECT delay_arr FROM run WHERE trip_id=? AND stop_seq=2",
                     (TRIP,)).fetchone()["delay_arr"]


def test_ura_se_ustavi_ko_vozilo_stoji_na_koncni():
    c = _baza()
    _branje(c, TIK, _ob(10, 55), 360)                     # napoved, še ni ura
    _branje(c, TIK, _ob(10, 59), 600)                     # prvič "zdaj"
    izid = _branje(c, TIK, _ob(11, 3), 840)               # stoji, ura teče
    assert izid["ure_na_koncni"] == 1
    assert _zapisano(c) == 600


def test_ura_se_ne_zapise_ko_vozilo_pelje_nazaj():
    c = _baza()
    _branje(c, TIK, _ob(10, 55), 360)
    _branje(c, TIK, _ob(10, 59), 600)
    _branje(c, TIK, _ob(11, 0), 660)
    _branje(c, BLIZU, _ob(11, 3), 840)
    _branje(c, SEVER, _ob(11, 6), 1020)
    assert _zapisano(c) == 600
    # Dnevnik obdrži, kar je feed rekel.
    assert c.execute("SELECT MAX(delay_arr) m FROM obs WHERE trip_id=?",
                     (TRIP,)).fetchone()["m"] == 1020


def test_vozilo_v_koloni_zamudo_res_nabira():
    c = _baza()
    _branje(c, SEVER, _ob(10, 59), 600)
    _branje(c, BLIZU, _ob(11, 3), 840)
    assert _zapisano(c) == 840
    _branje(c, BLIZU, _ob(11, 5), 960)                    # stoji v koloni
    assert _zapisano(c) == 840
    _branje(c, TIK, _ob(11, 7), 1080)                     # spet se bliža
    assert _zapisano(c) == 1080


def test_brez_sveze_lege_ostane_feed():
    c = _baza()
    _branje(c, TIK, _ob(10, 59), 600)
    _branje(c, TIK, _ob(11, 0), 660)
    c.execute("UPDATE vehicle_now SET seen_ts = ?", (_ob(10, 50),))
    # Branje mimo `_branje`, ki bi lego osvežilo.
    prev = {"delay_arr": 600}
    assert not collector.ura_na_koncni(c, TRIP, DAN, 2, prev, (RED_S, None), 660, _ob(11, 0))


def test_predzadnji_postanek_ni_koncna():
    c = _baza()
    c.execute("INSERT INTO vehicle_now(trip_id, seen_ts, lat, lon) VALUES(?,?,?,?)",
              (TRIP, _ob(10, 59), *TIK))
    prev = {"delay_arr": 300}
    for _ in range(2):
        assert not collector.ura_na_koncni(c, TRIP, DAN, 1, prev, (38700, 38700), 840, _ob(10, 59))


JUG = Trasa([[(46.0360, 14.5000), (46.0270, 14.5000)]])      # proti jugu, končna spodaj


def _vozilo(**k):
    return {"measured_seq": 2, "last_seq": 2, "lat": 46.0290, "lon": 14.5000, "bearing": 15.0, **k}


def test_koncana_ko_vozilo_pelje_proti_trasi():
    assert api._voznja_koncana(_vozilo(), JUG)


def test_koncana_ko_je_vozilo_dalec_od_trase():
    assert api._voznja_koncana(_vozilo(lon=14.5100, bearing=None), JUG)


def test_ni_koncana_ko_vozilo_pelje_po_trasi():
    assert not api._voznja_koncana(_vozilo(bearing=185.0), JUG)


def test_ni_koncana_pred_koncno_ali_brez_podatka():
    assert not api._voznja_koncana(_vozilo(measured_seq=1), JUG)
    assert not api._voznja_koncana(_vozilo(measured_seq=None), JUG)
    assert not api._voznja_koncana(_vozilo(bearing=None), JUG)
    assert not api._voznja_koncana(_vozilo(), None)


def test_vozilo_na_dveh_voznjah_velja_novejsa_lega():
    """Ob menjavi ostane vrstica končane vožnje sveža še do `POSITION_FRESH_S`:
    isti avtobus bi bil narisan dvakrat. Enaka ura ni menjava."""
    vrstice = [{"trip_id": "stara", "vehicle_id": "V", "seen_ts": 100},
               {"trip_id": "nova", "vehicle_id": "V", "seen_ts": 150},
               {"trip_id": "brez", "vehicle_id": None, "seen_ts": 90},
               {"trip_id": "a", "vehicle_id": "W", "seen_ts": 90},
               {"trip_id": "b", "vehicle_id": "W", "seen_ts": 90}]
    assert [d["trip_id"] for d in api._novejsa_lega(vrstice)] == ["nova", "brez", "a", "b"]


def test_koncana_voznja_ne_dobi_ur_naslednje(monkeypatch):
    """Eta LPP gre po vozilu: vozilo, ki že vozi naslednjo vožnjo, končani
    prinese njene ure."""
    c = _baza()
    zdaj = datetime(2026, 10, 30, 10, 45, tzinfo=stats.TZ)
    ts = int(zdaj.timestamp())
    c.execute("INSERT INTO vehicle_now(trip_id, seen_ts, lat, lon, vehicle_id) "
              "VALUES(?,?,0,0,'V')", (TRIP, ts - 90))
    c.execute("INSERT INTO vehicle_now(trip_id, seen_ts, lat, lon, vehicle_id) "
              "VALUES('naslednja',?,0,0,'V')", (ts - 5,))
    monkeypatch.setattr(api.lpp, "eta_po_postankih", lambda *a: {2: 4})
    vrstice = [{"stop_seq": 2, "sched_arr": zdaj.isoformat(), "sched_dep": None}]
    assert api._lpp_zivo(c, TRIP, vrstice, DAN, 1, zdaj) is None
    assert "zamuda" not in vrstice[0]
    c.execute("DELETE FROM vehicle_now WHERE trip_id = 'naslednja'")
    assert api._lpp_zivo(c, TRIP, vrstice, DAN, 1, zdaj) == "LPP"
    assert vrstice[0]["eta_min"] == 4
