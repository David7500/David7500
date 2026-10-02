"""Pripenjanje tras na OSM: lepljenje odgovora OSRM, predpomnilnik, rezerva.

    ./venv/bin/python -m pytest tests/test_pripni.py -q
"""
from __future__ import annotations

import json

from kajros import config, db, pripni, stats

# Ravna cesta proti vzhodu v Ljubljani; 0,001° dolžine je tu ~77 m.
A, B, C = [46.05, 14.500], [46.05, 14.501], [46.05, 14.502]


def _odgovor(odseki, matching=0):
    """Odgovor `/match` z enim matchingom: `odseki` so seznami (lat, lon)."""
    coords, annot = [], []
    for k, o in enumerate(odseki):
        tocke = o if k == 0 else o[1:]
        coords += [[lon, lat] for lat, lon in tocke]
        annot.append({"annotation": {"distance": [1.0] * (len(o) - 1)}})
    sledi = [{"matchings_index": matching, "waypoint_index": i, "location": None}
             for i in range(len(odseki) + 1)]
    return {"code": "Ok", "tracepoints": sledi,
            "matchings": [{"geometry": {"coordinates": coords}, "legs": annot}]}


def test_polyline_kot_v_googlovem_primeru():
    assert pripni.polyline([(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]) \
        == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"


def test_dlje_od():
    crta = [A, C]
    assert not pripni.dlje_od([[46.05005, 14.501]], crta, 10)     # 5,6 m
    assert pripni.dlje_od([[46.0502, 14.501]], crta, 10)          # 22 m


def test_zlepi_vzame_pripeto_kjer_se_ujema():
    # Pripeta cesta 3 m severno od surove: to je pripenjanje, ne obvoz.
    s = 46.05003
    odg = _odgovor([[[s, 14.500], [s, 14.5005], [s, 14.501]],
                    [[s, 14.501], [s, 14.502]]])
    tocke, delez = pripni.zlepi([A, B, C], odg, 35)
    assert all(abs(p[0] - s) < 1e-9 for p in tocke)
    assert delez > 0.99
    # Robna točka med odsekoma ni podvojena.
    assert len(tocke) == 4


def test_zlepi_zavrne_obvoz_samo_v_tistem_odseku():
    s = 46.05003
    obvoz = [[s, 14.501], [46.0515, 14.501], [46.0515, 14.502], [s, 14.502]]  # 160 m stran
    odg = _odgovor([[[s, 14.500], [s, 14.501]], obvoz])
    tocke, delez = pripni.zlepi([A, B, C], odg, 35)
    assert [46.0515, 14.501] not in tocke
    assert tocke[-1] == C                      # drugi odsek je ostal surov
    assert 0.4 < delez < 0.6


def test_zlepi_brez_odgovora_vrne_surovo():
    assert pripni.zlepi([A, B, C], None, 35) == ([A, B, C], 0.0)


def test_zlepi_nepripete_tocke_ostanejo_surove():
    s = 46.05003
    odg = _odgovor([[[s, 14.500], [s, 14.501]]])
    odg["tracepoints"].append(None)            # tretja točka ni pripeta
    tocke, _ = pripni.zlepi([A, B, C], odg, 35)
    assert tocke[-1] == C


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO shape(shape_id, points) VALUES('S1', ?)", (json.dumps([[A, B, C]]),))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network, shape_id) "
              "VALUES('T1', 'R', '25', 'X', 'bus', 'lpp', 'avtobus', 'S1')")
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('P1', 'Prva', 46.05, 14.5)")
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('P2', 'Druga', 46.05, 14.502)")
    c.execute("INSERT INTO edge(from_id, to_id, km, elementary, trips, geojson) "
              "VALUES('P1', 'P2', 0.15, 1, 3, ?)",
              (json.dumps({"type": "LineString", "coordinates": [[14.5, 46.05], [14.502, 46.05]]}),))
    c.commit()
    return c


def _osrm(monkeypatch, klici):
    s = 46.05003

    def zahtevaj(naslov, tocke, polmer):
        klici.append(naslov)
        n = len(tocke)
        return _odgovor([[[s, tocke[i][1]], [s, tocke[i + 1][1]]] for i in range(n - 1)])
    monkeypatch.setattr(pripni, "_zahtevaj", zahtevaj)
    monkeypatch.setattr(pripni, "_dosegljiv", lambda naslov: True)


def test_pripni_zapise_in_drugic_bere_predpomnilnik(monkeypatch):
    c = _baza()
    klici = []
    _osrm(monkeypatch, klici)
    izid = pripni.pripni(c, log=lambda *_: None)
    assert izid["trase"] == 1 and izid["odseki"] == 1 and izid["novih"] == 2
    osm = json.loads(c.execute("SELECT osm FROM shape").fetchone()[0])
    assert abs(osm[0][0][0] - 46.05003) < 1e-9
    assert klici == [config.OSRM_AVTOBUS_URL, config.OSRM_TIR_URL]

    # Uvoz `shape` zamenja: ista vsebina, nova vrstica -- OSRM ni vprašan.
    c.execute("UPDATE shape SET osm = NULL")
    c.execute("UPDATE edge SET osm = NULL")
    klici.clear()
    izid = pripni.pripni(c, log=lambda *_: None)
    assert klici == [] and izid["trase"] == 1 and izid["novih"] == 0

    # Mreža prog nosi pripeto geometrijo.
    mreza = stats.network_geojson(c)
    assert abs(mreza["features"][0]["geometry"]["coordinates"][0][1] - 46.05003) < 1e-9


def test_nova_razlicica_pripne_znova(monkeypatch):
    c = _baza()
    _osrm(monkeypatch, [])
    pripni.pripni(c, log=lambda *_: None)
    monkeypatch.setattr(pripni, "RAZLICICA", pripni.RAZLICICA + 1)
    izid = pripni.pripni(c, log=lambda *_: None)
    assert izid["novih"] == 2


def test_brez_osrm_ne_naredi_nicesar(monkeypatch):
    c = _baza()
    monkeypatch.setattr(pripni, "_dosegljiv", lambda naslov: False)
    izid = pripni.pripni(c, log=lambda *_: None)
    assert izid["trase"] == 0
    assert c.execute("SELECT osm FROM shape").fetchone()[0] is None


def test_nadomestni_po_tirih_dobi_pot_po_cesti(monkeypatch):
    c = _baza()
    c.execute("UPDATE trip SET agency = ?, network = 'zeleznica'", (config.RAIL_AGENCY_ID,))
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('T1', 1, 'P1', 0, 0)")
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('T1', 2, 'P2', 60, 60)")
    monkeypatch.setattr(pripni, "_dosegljiv", lambda naslov: True)
    monkeypatch.setattr(pripni, "_zahtevaj", lambda *a: None)       # na ceste se ne pripne
    cesta = [[46.051, 14.5], [46.051, 14.502]]
    postaje = []
    monkeypatch.setattr(pripni, "po_cesti", lambda naslov, p: postaje.append(p) or cesta)
    pripni.pripni(c, log=lambda *_: None)
    assert postaje == [[[46.05, 14.5], [46.05, 14.502]]]
    assert json.loads(c.execute("SELECT osm FROM shape").fetchone()[0]) == [cesta]


def test_na_cesto_desni_pas_in_smer():
    from kajros.deljenje import Trasa
    t = Trasa([[(46.05, 14.500), (46.05, 14.510)]])        # proti vzhodu
    lega = pripni.na_cesto(t, 46.05005, 14.505, 85)        # 5,6 m severno
    assert lega is not None
    lat, lon, smer = lega
    assert abs(smer - 90) < 1
    # Desno od smeri proti vzhodu je jug: 1,9 m pod osjo.
    assert abs((46.05 - lat) * 111195 - pripni.DESNO_M) < 0.05
    assert abs(lon - 14.505) < 1e-6


def test_na_cesto_ne_pripne_dalec_ali_v_nasprotni_smeri():
    from kajros.deljenje import Trasa
    t = Trasa([[(46.05, 14.500), (46.05, 14.510)]])
    assert pripni.na_cesto(t, 46.0503, 14.505, 90) is None    # 33 m stran
    assert pripni.na_cesto(t, 46.05005, 14.505, 270) is None  # nasprotna smer
    assert pripni.na_cesto(t, 46.05005, 14.505, None) is not None
