"""Linije LPP, ki vozijo mimo voznega reda.

2. 10. 2026 (kolesarsko prvenstvo, zaprta Slovenska) je LPP vožnje linije 1
izdal na novo, pod id-ji, ki jih objavljeni vozni red nima: 38 od 44 v feedu.
Zajem jih je zavrgel, tabla je kazala vozni red „brez podatka“, z zemljevida
pa je izginilo 15 od 16 vozil linije.

    ./venv/bin/python -m pytest tests/test_brez_voznje.py -q
"""
from __future__ import annotations

import json
from datetime import datetime

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import collector, db, iz_lege, lpp, stats

DAN = "2026-10-02"
ZDAJ = datetime(2026, 10, 2, 15, 0, tzinfo=stats.TZ)
# Trojni id LPP: prometni dan | vožnja | vzorec proge.
ZNANA = "D|znana|VZOREC1"


@pytest.fixture(autouse=True)
def _cist_spomin():
    iz_lege._v_feedu.clear()
    iz_lege._sled.clear()
    iz_lege._prvic = None
    lpp._prihodi.clear()
    yield
    iz_lege._v_feedu.clear()
    iz_lege._sled.clear()
    iz_lege._prvic = None
    lpp._prihodi.clear()


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
              " agency, network) VALUES(?, 'R1', '1', 'STANEŽIČE P+R - DOLGI MOST P+R',"
              " 'D', 'bus', 'lpp', 'avtobus')", (ZNANA,))
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  [(ZNANA, 1, "A", None, 54000), (ZNANA, 2, "B", 55000, None)])
    db.fill_trip_window(c)
    return c


def _feed(*voznje, vozilo_na=None):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    f.header.timestamp = int(ZDAJ.timestamp())
    for i, tid in enumerate(voznje):
        e = f.entity.add(id=f"t{i}")
        e.trip_update.trip.trip_id = tid
        e.trip_update.trip.route_id = "R1"
        e.trip_update.trip.start_date = DAN.replace("-", "")
    if vozilo_na:
        e = f.entity.add(id="v")
        e.vehicle.trip.trip_id = vozilo_na
        e.vehicle.vehicle.id = "bus-7"
        e.vehicle.timestamp = int(ZDAJ.timestamp())
        e.vehicle.position.latitude = 46.06
        e.vehicle.position.longitude = 14.50
    return f


def test_zajem_steje_neznane_po_liniji_in_vozila_ohrani():
    c = _baza()
    neznane = ["D|nova1|VZOREC1", "D|nova2|VZOREC1", "D|nova3|VZOREC1"]
    feed = _feed(ZNANA, *neznane, vozilo_na=neznane[0])
    izid = collector.ingest(c, feed, vir="lpp")
    assert izid["neznanih"] == 3
    vozila: list[dict] = []
    collector.ingest_positions(c, feed, vozila)
    collector._zapisi_brez_voznje(c, izid.pop("proge"), vozila)

    linije = json.loads(db.get_meta(c, "lpp_linije_brez_voznje"))["linije"]
    assert linije == {"1": [3, 4]}
    # Vozilo dobi linijo in smer iz vzorca proge, v `vehicle_now` pa ne gre.
    v = json.loads(db.get_meta(c, "lpp_vozila_brez_voznje"))["vozila"]
    assert [(x["train_no"], x["headsign"], x["vehicle_id"]) for x in v] == [
        ("1", "STANEŽIČE P+R - DOLGI MOST P+R", "bus-7")]
    assert c.execute("SELECT COUNT(*) FROM vehicle_now").fetchone()[0] == 0


def test_ijpp_ne_steje_po_progah():
    """Števec po linijah je samo za LPP; IJPP ga ne rabi in ne nosi."""
    c = _baza()
    assert collector.ingest(c, _feed(ZNANA, "D|nova|VZOREC1"))["proge"] == {}


def test_prag_linije():
    # 2. 10. 2026 ob 15h: linija 1 38 od 44, 27 4 od 21, 11 3 od 26.
    assert lpp.je_brez_voznje(38, 44)
    assert not lpp.je_brez_voznje(4, 21)
    assert not lpp.je_brez_voznje(3, 26)
    assert not lpp.je_brez_voznje(2, 2)       # ena ali dve tuji vožnji nista zapora


def test_star_zapis_zajema_ne_velja():
    c = _baza()
    db.set_meta(c, "lpp_linije_brez_voznje", json.dumps(
        {"ts": ZDAJ.timestamp() - 60, "linije": {"1": [38, 44], "27": [4, 21]}}))
    assert lpp.linije_brez_voznje(c, ZDAJ.timestamp()) == {"1"}
    assert lpp.linije_brez_voznje(c, ZDAJ.timestamp() + lpp.BREZ_VOZNJE_SVEZE_S) == set()


def _prihod(eta, linija="1", tip=0, cilj="DOLGI MOST P+R", depot=0):
    return {"route_name": linija, "eta_min": eta, "type": tip, "depot": depot,
            "trip_name": f"STANEŽIČE P+R - {cilj}", "vehicle_id": "x",
            "stations": {"departure": "STANEŽIČE P+R", "arrival": cilj}}


def test_vrstice_prihodov():
    prihodi = [_prihod(5), _prihod(31, tip=1), _prihod(3, linija="3"),
               _prihod(8, depot=1), _prihod(12, cilj="Tivoli")]
    v = lpp.vrstice_prihodov(prihodi, "S1", {"1"}, ZDAJ.timestamp(), DAN, True, "Tivoli")
    # Linija 3 ni zamenjana, vožnja v garažo ni za potnika, na končni se ne odpelje.
    assert [(r["train_no"], r["t_s"], r["lpp_vrsta"]) for r in v] == [
        ("1", 15 * 3600 + 300, "napoved"), ("1", 15 * 3600 + 1860, "po načrtu")]
    assert v[0]["sched"] == v[0]["expected"] == "2026-10-02T15:05:00+02:00"
    assert "trip_id" not in v[0]
    assert v[0]["towards"] == "DOLGI MOST P+R"


def _vrstica(t_s, linija="1", agency="lpp"):
    return {"trip_id": f"{linija}@{t_s}", "train_no": linija, "agency": agency,
            "stop_id": "S1", "service_date": DAN, "t_s": t_s}


def _tabla(c, monkeypatch, prihodi):
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('S1', 'Tivoli', 46.0604, 14.4972)")
    db.set_meta(c, "lpp_linije_brez_voznje", json.dumps(
        {"ts": ZDAJ.timestamp(), "linije": {"1": [38, 44]}}))
    monkeypatch.setattr(lpp, "_postaje_lpp", lambda: [
        {"ref_id": "801011", "latitude": 46.0604, "longitude": 14.4972},
        {"ref_id": "801012", "latitude": 46.0602, "longitude": 14.4977}])     # 45 m stran
    monkeypatch.setattr(lpp, "_prihodi_postaje", lambda koda: prihodi.get(koda))
    rows = [_vrstica(15 * 3600 - 300), _vrstica(15 * 3600 + 600),
            _vrstica(15 * 3600 + 5400), _vrstica(15 * 3600 + 600, linija="3")]
    return lpp.na_tablo(c, rows, ZDAJ, True, "Tivoli")


def test_tabla_zamenja_vozni_red_do_obzorja_lpp(monkeypatch):
    c = _baza()
    rows, mimo = _tabla(c, monkeypatch, {"801011": [_prihod(4), _prihod(33)],
                                         "801012": [_prihod(1, cilj="STANEŽIČE P+R")]})
    assert mimo == ["1"]
    ostale = sorted((r["train_no"], r["t_s"], "trip_id" in r) for r in rows)
    # Vozni red linije 1 ostane le za zadnjim LPP-jevim prihodom (15:33), linija 3
    # ostane cela, s postajališča na drugi strani ceste (801012) ni ničesar.
    assert ostale == [("1", 15 * 3600 + 240, False), ("1", 15 * 3600 + 1980, False),
                      ("1", 15 * 3600 + 5400, True), ("3", 15 * 3600 + 600, True)]


def test_ob_izpadu_vira_ostane_vozni_red(monkeypatch):
    c = _baza()
    rows, mimo = _tabla(c, monkeypatch, {})
    assert mimo == []
    assert len(rows) == 4 and all("trip_id" in r for r in rows)
