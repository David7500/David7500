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


# ------------------------------------------------------------- konca trase

# Postaja je ~460 m vzhodno od začetka trase, kot Ljubljana AP 4. 10. 2026.
POSTAJA = [46.05, 14.506]


def test_trasa_brez_postanka_na_zacetku_se_podaljsa_po_cesti():
    """Trasa se začne na stari legi postaje in pelje stran od nove: do nove
    jo podaljša pot po cesti, ne ravna črta."""
    trasa = [[[46.05, 14.500], [46.05, 14.499], [46.05, 14.490]]]
    cesta = [POSTAJA, [46.049, 14.503], [46.05, 14.500]]
    klici = []
    out = pripni.do_postaj(trasa, POSTAJA, [46.05, 14.490],
                           lambda a, b: klici.append((a, b)) or cesta)
    assert klici == [(POSTAJA, [46.05, 14.500])]
    assert out[0][0] == POSTAJA and out[0][:3] == cesta
    assert out[0][-1] == [46.05, 14.490]


def test_trasa_ki_gre_mimo_postanka_se_tam_odreze():
    """Trasa se začne v garaži in pelje mimo prvega postanka: odreže se pri
    njem, pot po cesti ni potrebna."""
    trasa = [[[46.05, 14.500], [46.05, 14.510], [46.05, 14.520]]]
    out = pripni.do_postaj(trasa, [46.0501, 14.506], [46.05, 14.520],
                           lambda a, b: (_ for _ in ()).throw(AssertionError("brez poti")))
    assert out[0][0] == [46.05, 14.506]
    assert out[0][-1] == [46.05, 14.520]


def test_krozna_linija_se_ne_odreze_na_poti_nazaj():
    """Krožna linija gre mimo začetnega postanka tudi na koncu. Začetek se
    sme odrezati samo v prvi polovici, sicer bi ostal le zadnji kos."""
    tja = [[46.05, 14.500 + i * 0.002] for i in range(6)]            # 14.500 -> 14.510
    nazaj = [[46.0508, 14.510 - i * 0.002] for i in range(6)]        # 90 m severneje
    postanek = [46.0508, 14.5061]
    cesta = [postanek, [46.0502, 14.503], [46.05, 14.500]]
    out = pripni.do_postaj([tja + nazaj], postanek, None, lambda a, b: cesta)
    assert out[0][:3] == cesta, "podaljšana, ne odrezana na poti nazaj"


def test_bliznji_konci_ostanejo():
    trasa = [[A, B, C]]
    assert not pripni.potrebuje_konca(trasa, A, C)
    assert pripni.do_postaj(trasa, A, C, lambda a, b: None) == trasa


def test_predalec_ni_preselitev_ampak_napaka():
    trasa = [[A, B, C]]
    assert not pripni.potrebuje_konca(trasa, [46.10, 14.5], None)        # 5,5 km


def test_pripni_doda_pot_do_postaje(monkeypatch):
    c = _baza()
    c.execute("UPDATE trip SET first_seq = 1, last_seq = 2")
    c.execute("UPDATE station SET lon = 14.508 WHERE stop_id = 'P1'")    # ~620 m od A
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('T1', 1, 'P1', 0, 0)")
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('T1', 2, 'P2', 60, 60)")
    _osrm(monkeypatch, [])
    poti = []
    monkeypatch.setattr(pripni, "po_cesti",
                        lambda naslov, p: poti.append(p) or [p[0], [46.051, 14.504], p[1]])
    pripni.pripni(c, log=lambda *_: None)
    assert poti and poti[0][0] == [46.05, 14.508]
    osm = json.loads(c.execute("SELECT osm FROM shape").fetchone()[0])
    assert osm[0][0] == [46.05, 14.508]

    # Drugič iz predpomnilnika: ključ nosi postanka, pot se ne išče znova.
    c.execute("UPDATE shape SET osm = NULL")
    poti.clear()
    pripni.pripni(c, log=lambda *_: None)
    assert poti == []


def test_voznja_brez_trase_dobi_pot_skozi_postajalisca(monkeypatch):
    """LPP za devet linij trase nima; dobijo pot po cesti, enkrat na zaporedje
    postajališč, in drugič iz predpomnilnika."""
    c = _baza()
    c.execute("UPDATE trip SET shape_id = NULL")
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
              "VALUES('T2', 'R', '25', 'X', 'bus', 'lpp', 'avtobus')")
    for t in ("T1", "T2"):
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?, 1, 'P1', 0, 0)", (t,))
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?, 2, 'P2', 60, 60)", (t,))
    _osrm(monkeypatch, [])
    cesta = [[46.05, 14.5], [46.0502, 14.501], [46.05, 14.502]]
    poti = []
    monkeypatch.setattr(pripni, "po_cesti", lambda naslov, p: poti.append(p) or cesta)
    izid = pripni.pripni(c, log=lambda *_: None)
    assert izid["iz_postajalisc"] == 1 and len(poti) == 1, "dve vožnji, eno zaporedje"
    oblike = {r[0] for r in c.execute("SELECT shape_id FROM trip")}
    assert len(oblike) == 1 and next(iter(oblike)).startswith(pripni.IZ_POSTAJALISC)
    assert json.loads(c.execute("SELECT osm FROM shape WHERE shape_id = ?",
                                (next(iter(oblike)),)).fetchone()[0]) == [cesta]

    # Uvoz trase pobriše; drugič pride iz predpomnilnika.
    c.execute("DELETE FROM shape WHERE shape_id LIKE 'postajalisca:%'")
    c.execute("UPDATE trip SET shape_id = NULL")
    poti.clear()
    pripni.pripni(c, log=lambda *_: None)
    assert poti == [] and c.execute("SELECT COUNT(*) FROM trip WHERE shape_id IS NULL").fetchone()[0] == 0


# ------------------------------------------------------------- postajališča

def test_ob_trasi_smer_in_stran():
    """Trasa proti vzhodu; postajališče 5 m južno je desno od smeri vožnje."""
    crta = [[46.05, 14.500], [46.05, 14.502]]
    d, j, smer, desno = pripni._ob_trasi(crta, 46.05 - 5 / 110574, 14.501, 0)
    assert abs(d - 5) < 0.1 and j == 0
    assert abs(smer - 90) < 0.5
    assert abs(desno - 5) < 0.1
    _, _, _, levo = pripni._ob_trasi(crta, 46.05 + 5 / 110574, 14.501, 0)
    assert abs(levo + 5) < 0.1


def test_postajalisca_smer_prevozniki_postaja():
    c = _baza()
    c.execute("UPDATE trip SET first_seq = 1, last_seq = 2")
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('AP', 'Kraj AP', 46.05, 14.501)")
    c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES('D', 'Daleč', 46.06, 14.501)")
    for seq, sid in ((1, "P1"), (2, "AP"), (3, "D"), (4, "P2")):
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('T1', ?, ?, 0, 0)",
                  (seq, sid))
    c.execute("UPDATE trip SET last_seq = 4")
    assert pripni.postajalisca(c) == 4
    p = {r["stop_id"]: dict(r) for r in c.execute("SELECT * FROM postajalisce")}
    assert abs(p["P1"]["smer"] - 90) < 1 and p["P1"]["prevozniki"] == "1118"   # mestni LPP = 1118
    assert p["AP"]["postaja"] == 1, "ime z AP je avtobusna postaja"
    assert p["D"]["smer"] is None, "1,1 km od trase ni ob cesti"
    assert p["P1"]["postaja"] == 0


def test_postaje_avtobus_nosijo_smer(monkeypatch):
    c = _baza()
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('T1', 1, 'P1', 0, 0)")
    c.execute("INSERT INTO postajalisce(stop_id, smer, desno, prevozniki, postaja) "
              "VALUES('P1', 90, 4.2, '1118', 0)")
    v = stats.stations(c, "avtobus")
    assert v == [{"stop_id": "P1", "name": "Prva", "lat": 46.05, "lon": 14.5, "smer": 90.0,
                  "desno": 4.2, "prevozniki": "1118", "postaja": 0}]
