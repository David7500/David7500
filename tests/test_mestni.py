"""Mestna prevoza Kranj in Murska Sobota: oznake prog, uvoz z id-ji IJPP,
lege Kranja.

    ./venv/bin/python -m pytest tests/test_mestni.py -q
"""
from __future__ import annotations

import zipfile

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import collector, config, db, gtfs, iz_lege, kranj, prehod, stats

DAN = "2026-10-27"                                   # torek
ZDAJ = stats.polnoc(DAN) + 11 * 3600 + 15 * 60       # 11:15


@pytest.fixture(autouse=True)
def _cist_spomin(monkeypatch):
    iz_lege._v_feedu.clear()
    iz_lege._prvic = None
    prehod._sledi.clear()
    kranj._po_voznem_redu[:] = [0.0, 0]
    # Predpomnilnik voznega reda je po znački uvoza: drug test z isto sekundo
    # uvoza bi dal svoja okna voženj.
    collector._STATIC_CACHE.clear()
    monkeypatch.setattr(config, "MARPROM", False)
    monkeypatch.setattr(config, "KRANJ", True)
    monkeypatch.setattr(config, "MS", True)
    monkeypatch.setattr(config, "EXTRA_AGENCIES", ("1121",))


def test_kranj_oznaka_iz_proge():
    """V zipu so šifre (4012); potnik pozna „PROGO 1“. Proge brez številke v
    imenu so po id-ju iste družine (401x = 1)."""
    o = gtfs._kranj_oznaka
    assert o({"route_id": "4012", "route_long_name": "PROGA 1: Kranj kolodvor-Qlandia"}) == "1"
    assert o({"route_id": "4153", "route_long_name": "PROGA 15: Kolodvor-Planina"}) == "15"
    assert o({"route_id": "4010", "route_long_name": "Kranj kolodvor - Plinarna"}) == "1"
    assert o({"route_id": "4077", "route_long_name": "Planika-Globus-Mlaka-Predoslje"}) == "7"
    assert o({"route_id": "4000", "route_long_name": "KRANVAJ"}) == "Kranvaj"


def test_kranj_smer_s_ciljem_na_koncu():
    """V `trip_headsign` je ime proge; prikaz cilj bere za zadnjim „ - “."""
    s = gtfs._kranj_smer
    assert s("PROGA 1: Kranj kolodvor-Qlandia-Prebačevo") == "Kranj kolodvor - Qlandia - Prebačevo"
    assert s("Kranj kolodvor - Plinarna - Planina -  Hrastje - Prebačevo") == \
        "Kranj kolodvor - Plinarna - Planina - Hrastje - Prebačevo"
    assert s("PROGA 1") == "PROGA 1"
    assert s("") == ""


def _zip(pot, datoteke: dict[str, str]):
    with zipfile.ZipFile(pot, "w") as zf:
        for ime, vsebina in datoteke.items():
            zf.writestr(ime, vsebina)
    return pot


def _ijpp(pot):
    """IJPP: vožnja AP MS 406150 (že v IJPP) in postajališče 1122459."""
    return _zip(pot, {
        "routes.txt": "route_id,agency_id,route_short_name,route_type\nr1,1121,M2105,3\n",
        "trips.txt": "trip_id,route_id,service_id,shape_id,trip_headsign\n"
                     "406150,r1,s1,,Rakičan\n",
        "stop_times.txt": "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
                          "406150,1,1122459,08:00:00,08:00:00\n406150,2,9,08:20:00,08:20:00\n",
        "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\n"
                     "1122459,Murska Sobota Ul.Mikloša Kuzmiča,46.657059,16.153906\n"
                     "9,Rakičan,46.64,16.19\n",
        "shapes.txt": "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n",
        "calendar_dates.txt": "service_id,date,exception_type\ns1,20261027,1\n"})


def _ms(pot):
    """Mestni MS kot iz NeTEx: id-ji vožnje in postajališč so IJPP-jevi."""
    return _zip(pot, {
        "routes.txt": "route_id,agency_id,route_short_name,route_type\n59507,1121,1,3\n",
        "trips.txt": "route_id,service_id,trip_id,trip_headsign,shape_id\n"
                     "59507,e713f6,406149,BTC trgovina — Ulica Štefana Kuzmiča,\n"
                     "59507,e713f6,406150,BTC trgovina — Ulica Štefana Kuzmiča,\n",
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                          "406149,10:00:00,10:00:00,1122459,1\n406149,10:05:00,10:05:00,1122470,2\n"
                          "406150,11:00:00,11:00:00,1122459,1\n406150,11:05:00,11:05:00,1122470,2\n",
        "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\n"
                     "1122459,Ul.Mikloša Kuzmiča II,46.657059,16.153906\n"
                     "1122470,BTC trgovina,46.664,16.170\n",
        "calendar_dates.txt": "service_id,date,exception_type\ne713f6,20261027,1\n"})


def test_ms_z_idji_ijpp_ostali_s_predpono(tmp_path):
    """NAP lege mestnih linij MS javi z id-ji NeTEx: vožnja brez predpone, da
    jo `nap.pripni` najde. Postajališče, ki ga IJPP že ima, ostane njegovo;
    vožnja, ki jo IJPP že ima, se ne podvoji."""
    c = db.connect(":memory:")
    db.init(c)
    izid = gtfs.import_static(c, _ijpp(tmp_path / "ijpp.zip"),
                              mestni={"ms": _ms(tmp_path / "ms.zip")})
    assert izid["trips_mestni"] == {"ms": 1}
    t = dict(c.execute("SELECT trip_id, route_id, service_id, agency, network, train_no "
                       "FROM trip WHERE trip_id = '406149'").fetchone())
    assert t == {"trip_id": "406149", "route_id": "ms-59507", "service_id": "ms-e713f6",
                 "agency": "1121", "network": "avtobus", "train_no": "1"}
    assert c.execute("SELECT route_id FROM trip WHERE trip_id = '406150'").fetchone()[0] == "r1"
    imena = dict(c.execute("SELECT stop_id, name FROM station").fetchall())
    assert imena["1122459"] == "Murska Sobota Ul.Mikloša Kuzmiča"
    assert imena["1122470"] == "BTC trgovina"
    assert c.execute("SELECT stop_id FROM sched WHERE trip_id = '406149' ORDER BY stop_seq"
                     ).fetchall()[0][0] == "1122459"


def _kranj_zip(pot):
    return _zip(pot, {
        "routes.txt": "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                      "4012,MP_Kranj,4012,PROGA 1: Kranj kolodvor-Qlandia-Prebačevo,3\n",
        "trips.txt": "route_id,service_id,trip_id,trip_headsign,block_id,shape_id\n"
                     "4012,1,0D3o9RWfWG_154963,PROGA 1,4504,\n",
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                          "0D3o9RWfWG_154963,11:10:00,11:10:00,88,1\n"
                          "0D3o9RWfWG_154963,11:20:00,11:20:00,89,2\n"
                          "0D3o9RWfWG_154963,11:30:00,11:30:00,90,3\n",
        "stops.txt": "stop_id,stop_code,stop_name,stop_lat,stop_lon\n"
                     "88,10053,Rupa,46.25669,14.36488\n89,10052,Rožna ulica,46.23317,14.33809\n"
                     "90,10051,Kolodvor,46.2377,14.3497\n",
        "calendar.txt": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
                        "start_date,end_date\n1,1,1,1,1,1,0,0,20261026,20261030\n"})


def _vp(trip_id, ts, start_date="20261027"):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    f.header.timestamp = int(ts)
    e = f.entity.add()
    e.id = "1"
    e.vehicle.trip.trip_id = trip_id
    e.vehicle.trip.start_date = start_date
    e.vehicle.vehicle.id = "KRJN601"
    e.vehicle.position.latitude = 46.2469
    e.vehicle.position.longitude = 14.3628
    e.vehicle.position.bearing = 127.6
    e.vehicle.position.speed = 9.8
    e.vehicle.timestamp = int(ts)
    return f.SerializeToString()


def test_kranj_lega_na_voznjo_uradnega_zipa(tmp_path):
    c = db.connect(":memory:")
    db.init(c)
    izid = gtfs.import_static(c, _ijpp(tmp_path / "ijpp.zip"),
                              mestni={"kranj": _kranj_zip(tmp_path / "kranj.zip")})
    assert izid["trips_mestni"] == {"kranj": 1}
    assert c.execute("SELECT train_no, agency, block_id FROM trip WHERE trip_id = "
                     "'kr-0D3o9RWfWG_154963'").fetchone()[:] == ("1", "kranj", "kr-4504")
    vozila, glava = kranj.razberi(_vp("0D3o9RWfWG_154963", ZDAJ - 5))
    assert glava == int(ZDAJ - 5) and vozila[0]["hitrost"] == pytest.approx(9.8, abs=0.01)
    vozila += kranj.razberi(_vp("neznana", ZDAJ - 5))[0]
    vozila += kranj.razberi(_vp("0D3o9RWfWG_154963", ZDAJ - 3600))[0]
    st = kranj.korak(c, vozila, ZDAJ)
    assert (st["pripetih"], st["brez_voznje"], st["starih"]) == (1, 1, 1)
    v = dict(c.execute("SELECT trip_id, service_date, vehicle_id, speed_ms FROM vehicle_now"
                       ).fetchone())
    assert v["trip_id"] == "kr-0D3o9RWfWG_154963" and v["service_date"] == DAN
    assert v["vehicle_id"] == "kranj-KRJN601" and v["speed_ms"] == pytest.approx(9.8, abs=0.01)
    assert kranj.po_voznem_redu(c, ZDAJ) == 1
