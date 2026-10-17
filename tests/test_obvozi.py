"""Obvoz LPP: vožnja tu ne ustavi -- tabla, zveze, pristajalna stran, pot.

17. 10. 2026 (maraton, zaprta Slovenska) je kajros na Konzorciju, Pošti in
Ajdovščini kazal redne odhode linij 1, 2, 3, 6, 9, 27, avtobusi pa tam niso
ustavljali. Vzrok: LPP isti naslov obvestila rabi za nov dogodek, zapis pa je
obdržal veljavnost prvega; in obvoz je bil na postajališče, ne na vožnjo.

    ./venv/bin/python -m pytest tests/test_obvozi.py -q
"""
from __future__ import annotations

import time
from datetime import datetime

import pytest
from google.transit import gtfs_realtime_pb2 as rt

from kajros import alerts, api, db, geo, hoja, lpp, pot

D = "2026-10-17"


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (D,))
    for sid, ime, lat in (("KON", "Konzorcij", 46.0514), ("BAV", "Bavarski dvor", 46.0562),
                          ("TIV", "Tivoli", 46.0590)):
        c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,14.503)",
                  (sid, ime, lat))
    for tid, linija, agencija in (("t1", "1", "lpp"), ("t7", "7", "lpp"), ("g3", "3G", "1118")):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, "
                  "mode, network, agency) VALUES(?, ?, ?, 'kam', 'S1', 'bus', 'avtobus', ?)",
                  (tid, "r" + tid, linija, agencija))
    c.commit()
    return c


def _feed(header, pari, zacetek, konec):
    feed = rt.FeedMessage()
    for i, (trip_id, stop_id) in enumerate(pari):
        e = feed.entity.add()
        e.id = f"x{i}"
        a = e.alert
        t = a.header_text.translation.add(); t.language = "sl"; t.text = header
        d = a.description_text.translation.add(); d.language = "sl"
        d.text = "Vozilo se ne bo ustavilo na postaji"
        p = a.active_period.add(); p.start = zacetek; p.end = konec
        ie = a.informed_entity.add()
        ie.stop_id = stop_id
        if trip_id:
            ie.trip.trip_id = trip_id
    return feed


def test_isti_naslov_nov_dogodek_prepise_veljavnost(conn):
    zdaj = int(time.time())
    # Dopoldne obvoz, ki se konča ob 15h ...
    alerts.ingest_lpp(conn, _feed("Postaja Konzorcij na obvozu", [("t1", "KON")],
                                  zdaj - 7200, zdaj - 3600))
    assert alerts.for_stops(conn, ["KON"]) == []
    # ... popoldne isti naslov za maraton, do nedelje.
    alerts.ingest_lpp(conn, _feed("Postaja Konzorcij na obvozu", [("t1", "KON")],
                                  zdaj - 600, zdaj + 86400))
    obv = alerts.for_stops(conn, ["KON"])
    assert [a["header"] for a in obv] == ["Postaja Konzorcij na obvozu"]
    assert obv[0]["linije"] == ["1"]
    assert alerts.ne_ustavi(conn, ["KON"]) == {("t1", "KON")}


def test_na_bavarskem_dvoru_ustavijo_nekatere_linije(conn):
    """Obvestilo je na postajališče, vožnje pa so naštete: linija 7 ustavi."""
    zdaj = int(time.time())
    alerts.ingest_lpp(conn, _feed("Postaja Bavarski dvor na obvozu", [("t1", "BAV")],
                                  zdaj - 600, zdaj + 3600))
    vrstice = [{"trip_id": "t1", "stop_id": "BAV", "train_no": "1", "agency": "lpp"},
               {"trip_id": "t7", "stop_id": "BAV", "train_no": "7", "agency": "lpp"}]
    n = api._oznaci_obvoze(conn, vrstice, datetime.now(), zasloni=False)
    assert n == 1 and [bool(r.get("ne_ustavi")) for r in vrstice] == [True, False]


def test_obvestilo_brez_voznje_velja_za_vse(conn):
    zdaj = int(time.time())
    alerts.ingest_lpp(conn, _feed("Postaja Tivoli na obvozu", [("", "TIV")],
                                  zdaj - 600, zdaj + 3600))
    vrstice = [{"trip_id": "t7", "stop_id": "TIV", "train_no": "7", "agency": "lpp"}]
    api._oznaci_obvoze(conn, vrstice, datetime.now(), zasloni=False)
    assert vrstice[0]["ne_ustavi"] is True


def test_primestne_linije_po_lpp_jevem_zaslonu(conn, monkeypatch):
    """3G v RT LPP ni; LPP-jev zaslon jo kaže kot obvoz (`type` 3) -- dve vozili,
    torej dva naslednja odhoda, tretji ostane, ker zanj ne vemo."""
    monkeypatch.setattr(lpp.config, "LPP_ZIVO", True)
    monkeypatch.setattr(lpp, "_postaje_lpp", lambda: [
        {"ref_id": "601012", "latitude": 46.0514, "longitude": 14.503}])
    monkeypatch.setattr(lpp, "_prihodi_postaje", lambda koda: [
        {"route_name": "3G", "type": 3, "eta_min": 1},
        {"route_name": "3G", "type": 3, "eta_min": 1},
        {"route_name": "1", "type": 0, "eta_min": 4}])
    assert lpp.obvozi_zaslonov(conn, ["KON"]) == {("3G", "KON"): 2}
    # Postajališče IJPP z istim imenom 36 m stran (Konzorcij 1167156): ista koda.
    conn.execute("INSERT INTO station(stop_id, name, lat, lon) "
                 "VALUES('1167156', 'Konzorcij', 46.051095, 14.502932)")
    monkeypatch.setattr(lpp, "_postaje_lpp", lambda: [
        {"ref_id": "601012", "name": "Konzorcij", "latitude": 46.05141, "longitude": 14.50305}])
    assert lpp.obvozi_zaslonov(conn, ["1167156"]) == {("3G", "1167156"): 2}
    zdaj = datetime.now().astimezone()
    vrstice = [{"trip_id": f"g{i}", "stop_id": "KON", "train_no": "3G", "agency": "1118",
                "sched": datetime.fromtimestamp(zdaj.timestamp() + 600 * i).astimezone().isoformat()}
               for i in range(3)]
    api._oznaci_obvoze(conn, vrstice, zdaj)
    assert [bool(r.get("ne_ustavi")) for r in vrstice] == [True, True, False]


def test_pot_ne_vstopi_tam_kjer_voznja_ne_ustavi(conn, monkeypatch):
    def matrika(lat, lon, cilji, smer="od"):
        return ([round(geo.haversine(lat, lon, a, b) / hoja.HITROST_MS)
                 for a, b in cilji], hoja.OSRM)
    monkeypatch.setattr(pot.hoja, "matrika", matrika)
    hoja._PES_CACHE.clear()
    pot._VOZJE_CACHE.clear()
    for tid, odhod in (("t1", 8 * 3600 + 300), ("t7", 8 * 3600 + 1200)):
        conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                         "VALUES(?,?,?,?,?)",
                         [(tid, 1, "KON", odhod, odhod), (tid, 2, "TIV", odhod + 600, odhod + 600)])
    conn.commit()
    izh, cil = {"KON": 60}, {"TIV": 60}
    n = pot._isci_dan(conn, izh, cil, D, 8 * 3600, 2)
    assert n["noge"][0][0] == "t1"
    obvozi = pot.obvozi_po_postaji({("t1", "KON")})
    n = pot._isci_dan(conn, izh, cil, D, 8 * 3600, 2, ne_ustavi=obvozi)
    assert n["noge"][0][0] == "t7"
    # Tudi izstopa ni: cilj, kjer vožnja ne ustavi, ni dosežen z njo.
    n = pot._isci_dan(conn, izh, cil, D, 8 * 3600, 2,
                      ne_ustavi=pot.obvozi_po_postaji({("t1", "TIV"), ("t7", "TIV")}))
    assert n is None
    n = pot._isci_nazaj(conn, izh, cil, D, 9 * 3600, 2,
                        ne_ustavi=pot.obvozi_po_postaji({("t7", "KON")}))
    assert n["noge"][0][0] == "t1"



def test_odpovedana_voznja(conn, monkeypatch):
    """RT LPP 17. 10. 2026: 20Z ob 17:45 `CANCELED`; tabla jo je kazala kot
    redni odhod. Odpoved velja, dokler jo feed nosi."""
    from kajros import collector
    monkeypatch.setattr(collector, "_ODPOVEDANE", {})
    conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                     "VALUES('t7', ?, ?, ?, ?)", [(1, "BAV", 63900, 63900), (2, "TIV", 64500, 64500)])
    db.fill_trip_window(conn)
    feed = rt.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    e = feed.entity.add()
    e.id = "1"
    e.trip_update.trip.trip_id = "t7"
    e.trip_update.trip.start_date = D.replace("-", "")
    e.trip_update.trip.schedule_relationship = collector.ODPOVEDANA
    collector.ingest(conn, feed, vir="lpp")
    assert collector.odpovedane() == {("t7", D)}
    vrstice = [{"trip_id": "t7", "service_date": D, "stop_id": "BAV", "train_no": "7"},
               {"trip_id": "t1", "service_date": D, "stop_id": "BAV", "train_no": "1"}]
    api._oznaci_obvoze(conn, vrstice, datetime.now(), zasloni=False)
    assert [r.get("odpovedano", False) for r in vrstice] == [True, False]
    # Feed, ki pet minut ni odgovoril, ne šteje več.
    assert collector.odpovedane(time.time() + collector.ODPOVEDANE_SVEZE_S + 1) == frozenset()
