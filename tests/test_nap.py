"""Lege IJPP z NAP: razbor SIRI, id vožnje, pripenjanje, primerjava z derp.si
in kdaj NAP piše.

    ./venv/bin/python -m pytest tests/test_nap.py -q
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import datetime

import pytest

from google.transit import gtfs_realtime_pb2

from kajros import collector, db, iz_lege, nap, prehod, stats, zdravje

DAN = "2026-10-08"
POLNOC = stats.polnoc(DAN)
ZDAJ = POLNOC + 16 * 3600 + 30 * 60          # 16:30
GUID = "00000000-1177-0008-0000-{:012x}"


def _ref(trip: int) -> str:
    return f"SI:SI0:ServiceJourney:{GUID.format(trip)}:IJPP"


def _iso(ts: float, zamik: str = "+02:00") -> str:
    return datetime.fromtimestamp(ts, collector.TZ).strftime("%Y-%m-%dT%H:%M:%S.0000000") + zamik


def _va(vozilo, trip, ts, lat=46.05, lon=14.50, cas=None):
    cas = cas or _iso(ts)
    return f"""<VehicleActivity><RecordedAtTime>{cas}</RecordedAtTime>
      <MonitoredVehicleJourney><LineRef>SI:SI0:Line:x:IJPP</LineRef>
        <VehicleMode>bus</VehicleMode>
        <VehicleLocation><Longitude>{lon}</Longitude><Latitude>{lat}</Latitude></VehicleLocation>
        <Bearing>154</Bearing><VehicleJourneyRef>{_ref(trip) if trip else ''}</VehicleJourneyRef>
        <VehicleRef>{vozilo}</VehicleRef></MonitoredVehicleJourney></VehicleActivity>"""


def _odgovor(*aktivnosti, odgovor=ZDAJ) -> bytes:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ServiceDelivery xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.siri.org.uk/siri">
  <ResponseTimestamp>{_iso(odgovor)}</ResponseTimestamp>
  <VehicleMonitoringDelivery><ResponseTimestamp>{_iso(odgovor)}</ResponseTimestamp>
  {''.join(aktivnosti)}</VehicleMonitoringDelivery></ServiceDelivery>""".encode()


@pytest.fixture(autouse=True)
def _cist_spomin():
    iz_lege._v_feedu.clear()
    iz_lege._sled.clear()
    iz_lege._zadnja.clear()
    iz_lege._odklon.clear()
    prehod._sledi.clear()
    iz_lege._prvic = None
    iz_lege._nap_ts = 0.0
    collector._LEGE_DERP = (0.0, {})
    nap.senca = nap.Senca()
    yield
    iz_lege._nap_ts = 0.0
    iz_lege._v_feedu.clear()
    iz_lege._sled.clear()
    iz_lege._zadnja.clear()
    iz_lege._odklon.clear()
    prehod._sledi.clear()
    iz_lege._prvic = None
    collector._LEGE_DERP = (0.0, {})


def _baza():
    """Avtobusni vožnji 1001 (16:00) in 1002 (17:10), vlak 2001 (16:10)."""
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "Kranj", 46.24, 14.36), ("B", "Ljubljana", 46.05, 14.50)])
    for tid, zacetek, mode, net in (("1001", 16 * 3600, "bus", "avtobus"),
                                    ("1002", 17 * 3600 + 600, "bus", "avtobus"),
                                    ("2001", 16 * 3600 + 600, "rail", "zeleznica")):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network) VALUES(?, 'r', ?, 's', ?, '1123', ?)", (tid, tid, mode, net))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)",
                      [(tid, 1, "A", None, zacetek), (tid, 2, "B", zacetek + 3600, None)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s', ?)", (DAN,))
    db.fill_trip_window(c)
    c.commit()
    return c


def test_id_vožnje_je_zadnji_štirje_bajti_guida():
    """Primer iz dokumentacije NAP; isto računa `derp-si/ijpp-rt`."""
    ref = "SI:SI0:ServiceJourney:00000000-1177-0008-0000-000000049908:IJPP"
    assert nap.ijpp_id(ref) == str(0x49908) == "301320"
    for slab in (None, "", "SI:SI0:ServiceJourney:IJPP", "a:b:c:nihex-ni-guid:IJPP",
                 "SI:SI0:ServiceJourney:00000000-1177-0008-0000-00000004990:IJPP"):
        assert nap.ijpp_id(slab) is None


def test_razbor_popravi_uro_naprej_in_izpusti_staro():
    """Ura naprej (napačen zamik naprave) se popravi, kot pri derp.si; stara
    lega in lega brez id-ja vožnje gresta ven in se štejeta."""
    vsebina = _odgovor(
        _va("950133", 1001, ZDAJ - 20),
        _va("950134", 1001, ZDAJ + 3600 - 10),               # ura naprej
        _va("950135", 1001, ZDAJ - 600),                     # stara
        _va("950136", 1001, ZDAJ + 300),                     # v prihodnosti
        _va("950137", None, ZDAJ - 5),                       # brez vožnje
        _va("950138", 1001, ZDAJ - 5, cas=_iso(ZDAJ - 5)[:19]),   # brez zamika
    )
    vozila, st = nap.razberi(vsebina, ZDAJ + 99)
    assert st == {"vozil": 6, "popravljenih": 1, "starih": 1, "naprej": 1,
                  "brez_lege": 0, "brez_id": 1}
    po = {v["vozilo"]: v for v in vozila}
    assert set(po) == {"950133", "950134", "950138"}
    assert po["950133"] == {"vozilo": "950133", "ijpp": "1001", "ts": ZDAJ - 20,
                            "lat": 46.05, "lon": 14.5, "smer": 154.0, "nacin": "bus"}
    assert po["950134"]["ts"] == ZDAJ - 10
    # Čas brez zamika je lokalni čas (kot `derp-si/ijpp-rt`).
    assert po["950138"]["ts"] == ZDAJ - 5


def test_pripni_najde_vožnjo_in_dan_vlaka_in_prezgodnje_ne():
    c = _baza()
    vozila = [{"vozilo": "a", "ijpp": "1001", "ts": ZDAJ}, {"vozilo": "b", "ijpp": "1002", "ts": ZDAJ},
              {"vozilo": "c", "ijpp": "2001", "ts": ZDAJ}, {"vozilo": "d", "ijpp": "9999", "ts": ZDAJ}]
    pripeta, st = nap.pripni(c, vozila, ZDAJ)
    assert [(v["vozilo"], v["trip_id"], v["dan"]) for v in pripeta] == [("a", "1001", DAN)]
    nepripeti = st.pop("nepripeti")
    assert st == {"pripetih": 1, "brez_voznje": 1, "brez_dneva": 0, "prezgodaj": 1, "vlakov": 1}
    # Vzrok po vozilu, za /preveri-vire (praznik 31. 10. 2026: brez_dneva 13).
    assert sorted(n["razlog"] for n in nepripeti) == ["brez_voznje", "prezgodaj"]


def test_pripni_prevede_star_id_na_naslednico():
    c = _baza()
    c.execute("INSERT INTO zamenjava(stari_trip, stari_seq, novi_trip, novi_seq) "
              "VALUES('888', 1, '1001', 1)")
    pripeta, _ = nap.pripni(c, [{"vozilo": "a", "ijpp": "888", "ts": ZDAJ}], ZDAJ)
    assert [v["trip_id"] for v in pripeta] == ["1001"]


def test_primerjava_z_derp():
    """derp.si bere isti vir: ob istem času mora biti lega ista, vožnja ista."""
    v = [{"vozilo": "a", "ijpp": "1001", "ts": ZDAJ, "lat": 46.1, "lon": 14.4, "smer": None},
         {"vozilo": "b", "ijpp": "1001", "ts": ZDAJ, "lat": 46.1, "lon": 14.4, "smer": None}]
    derp = {"a": ("1001", ZDAJ, 46.1, 14.4), "z": ("1002", ZDAJ - 30, 46.0, 14.0)}
    p = nap.primerjaj(v, derp)
    assert p == {"derp": True, "skupnih": 1, "ista_voznja": 1, "isti_cas": 1, "odmik_m": 0.0,
                 "odmik_max_m": 0.0, "prednost_s": 0, "samo_nap": 1, "samo_derp": 1}
    assert nap.primerjaj(v, None) == {"derp": False}


def test_lega_za_vsa_vozila_zamuda_iz_lege_le_brez_derp(monkeypatch):
    """Lega z NAP gre v `vehicle_now` za vsa vozila (novejša je); zamudo iz
    lege za vozilo, ki ga derp.si nosi, računa zajem derp.si -- sicer bi isto
    sled vodili dve niti."""
    c = _baza()
    klici = []
    monkeypatch.setattr(iz_lege, "brez_feeda", lambda t, z=None: True)
    monkeypatch.setattr(iz_lege, "opazuj", lambda conn, t, d, ts, lat, lon, vozilo=None: klici.append(ts) or 0)
    v = [{"vozilo": "a", "ijpp": "1001", "ts": ZDAJ, "lat": 46.1, "lon": 14.4, "smer": None}]
    izid = nap.zapisi(c, nap.pripni(c, v, ZDAJ)[0], {"a": ("1001", ZDAJ - 20, 46.1, 14.4)}, ZDAJ)
    assert izid["zapisanih"] == 1 and klici == []
    assert tuple(c.execute("SELECT vehicle_id, seen_ts FROM vehicle_now").fetchone()) == ("a", ZDAJ)
    v[0]["ts"] = ZDAJ + 10
    nap.zapisi(c, nap.pripni(c, v, ZDAJ)[0], None, ZDAJ)
    assert klici == [ZDAJ + 10]


def test_zemljevid_kaze_vozilo_ki_vozjo_vodi(monkeypatch):
    """Dve vozili na isti vožnji: ikona ne skače k vozilu, ki je ne vodi."""
    c = _baza()
    monkeypatch.setattr(prehod, "vodja", lambda t, d: ("a", ZDAJ - 30))
    v = [{"vozilo": "b", "ijpp": "1001", "ts": ZDAJ, "lat": 46.2, "lon": 14.4, "smer": None},
         {"vozilo": "a", "ijpp": "1001", "ts": ZDAJ - 10, "lat": 46.1, "lon": 14.4, "smer": None}]
    nap.zapisi(c, nap.pripni(c, v, ZDAJ)[0], None, ZDAJ)
    assert tuple(c.execute("SELECT vehicle_id, seen_ts FROM vehicle_now").fetchone()) == ("a", ZDAJ - 10)
    # Vodilno vozilo je utihnilo: drugo se pokaže.
    monkeypatch.setattr(prehod, "vodja", lambda t, d: ("a", ZDAJ - 10 - prehod.RAZMIK_S - 60))
    nap.zapisi(c, nap.pripni(c, v[:1], ZDAJ)[0], None, ZDAJ)
    assert c.execute("SELECT vehicle_id FROM vehicle_now").fetchone()[0] == "b"


def test_derp_molči_nap_piše_vse_in_ne_povozi_novejšega():
    c = _baza()
    c.execute("INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, vehicle_id) "
              "VALUES('1001', ?, ?, 46.0, 14.0, 'a')", (DAN, ZDAJ + 5))
    v = [{"vozilo": "a", "ijpp": "1001", "ts": ZDAJ, "lat": 46.1, "lon": 14.4, "smer": 10.0}]
    nap.zapisi(c, nap.pripni(c, v, ZDAJ)[0], None, ZDAJ)
    assert c.execute("SELECT seen_ts FROM vehicle_now").fetchone()[0] == ZDAJ + 5
    v[0]["ts"] = ZDAJ + 10
    nap.zapisi(c, nap.pripni(c, v, ZDAJ)[0], None, ZDAJ)
    r = c.execute("SELECT seen_ts, lat, bearing, service_date FROM vehicle_now").fetchone()
    assert tuple(r) == (ZDAJ + 10, 46.1, 10.0, DAN)


def test_lege_derp_zastarijo():
    collector._LEGE_DERP = (ZDAJ, {"a": ("1001", ZDAJ, 46.0, 14.0)})
    assert collector.lege_derp(ZDAJ + 60) == {"a": ("1001", ZDAJ, 46.0, 14.0)}
    assert collector.lege_derp(ZDAJ + 61) is None


def test_korak_zapiše_meta_in_premakne_ključ_predpomnilnika():
    c = _baza()
    st = nap.korak(c, _odgovor(_va("950133", 1001, ZDAJ - 20)), ZDAJ)
    assert st["pripetih"] == 1 and st["zapisanih"] == 1 and st["derp"] is False
    assert json.loads(db.get_meta(c, "nap"))["vozil"] == 1
    assert db.get_meta(c, "positions_fetched") == str(ZDAJ)


def test_prijava_iz_okolja_in_datoteke(tmp_path, monkeypatch):
    monkeypatch.setattr(nap.config, "DATA_DIR", tmp_path)
    monkeypatch.delenv("KAJROS_NAP_PRIJAVA", raising=False)
    assert nap.prijava() is None
    (tmp_path / ".nap-prijava").write_text("kdo@primer.si:ge:slo\n")
    assert nap.prijava() == ("kdo@primer.si", "ge:slo")
    monkeypatch.setenv("KAJROS_NAP_PRIJAVA", "drug@primer.si:x")
    assert nap.prijava() == ("drug@primer.si", "x")
    monkeypatch.setenv("KAJROS_NAP_PRIJAVA", "brez-gesla")
    assert nap.prijava() is None


def test_zdravje_zavrnjena_prijava_je_rumena_stoječa_nit_rdeča():
    """Zavrnjena prijava: rumeno, po uri oranžno (novo geslo ali odobritev se
    ne zgodi samo). Vir brez odgovora rumeno, po dveh urah oranžno."""
    vozi = {"zeleznica": 5, "avtobus": 50}
    ocena = lambda nm: zdravje.ocena({"vozi_zdaj": vozi, "nap": nm}, {}, ZDAJ).get("nap")
    assert ocena(None) is None
    assert ocena({"ts": ZDAJ - 600, "http": 401, "napaka_ts": ZDAJ - 30})[0] == zdravje.MLACNA
    assert ocena({"ts": ZDAJ - 2 * 3600, "http": 401, "napaka_ts": ZDAJ - 30})[0] == zdravje.ORANZNA
    assert ocena({"ts": ZDAJ - 15})[0] == zdravje.DOBRA
    assert ocena({"ts": ZDAJ - 1000, "napaka_ts": ZDAJ - 20})[0] == zdravje.MLACNA
    assert ocena({"ts": ZDAJ - 3 * 3600, "napaka_ts": ZDAJ - 20})[0] == zdravje.ORANZNA
    assert ocena({"ts": ZDAJ - 1000, "napaka_ts": ZDAJ - 1000})[0] == zdravje.SLABA


def _feed_zamud(trip_id, zamuda):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    e = f.entity.add()
    e.id = "1"
    e.trip_update.trip.trip_id = trip_id
    e.trip_update.trip.start_date = DAN.replace("-", "")
    stu = e.trip_update.stop_time_update.add()
    stu.stop_sequence = 2
    stu.departure.delay = zamuda
    return f


def test_nap_vodi_le_svoje_prevoznike_in_le_dokler_odgovarja():
    assert not iz_lege.nap_vodi("1123", ZDAJ)            # NAP še ni prebran
    iz_lege.nap_prebran(ZDAJ)
    assert iz_lege.nap_vodi("1123", ZDAJ + 60)
    assert not iz_lege.nap_vodi("1118", ZDAJ)            # primestni LPP ostane derp.si
    assert not iz_lege.nap_vodi(None, ZDAJ)
    assert not iz_lege.nap_vodi("1123", ZDAJ + 61)       # NAP obmolknil: spet derp.si


def test_zajem_derp_izpusti_vožnje_ki_jih_vodi_nap():
    """Ko NAP odgovarja, feed derp.si za Arrivo ne piše v `run`, vožnja pa ni
    „v feedu“, da jo zamuda iz lege vzame takoj. Ko NAP obmolkne, piše."""
    c = _baza()
    iz_lege.zabelezi_feed(["1001"], ZDAJ - 30)
    iz_lege.nap_prebran()
    izid = collector.ingest(c, _feed_zamud("1001", 240))
    assert izid["nap_prevzel"] == 1 and izid["trips"] == 1
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
    assert "1001" not in iz_lege._v_feedu
    iz_lege._nap_ts = 0.0
    assert collector.ingest(c, _feed_zamud("1001", 240))["nap_prevzel"] == 0
    assert c.execute("SELECT delay_dep FROM run").fetchone()[0] == 240


def test_nap_meri_zamudo_tudi_za_vozilo_ki_ga_ima_derp(monkeypatch):
    c = _baza()
    klici = []
    monkeypatch.setattr(iz_lege, "brez_feeda", lambda t, z=None: True)
    monkeypatch.setattr(iz_lege, "opazuj", lambda conn, t, d, ts, lat, lon, vozilo=None: klici.append(t) or 0)
    iz_lege.nap_prebran(ZDAJ)
    v = [{"vozilo": "a", "ijpp": "1001", "ts": ZDAJ, "lat": 46.1, "lon": 14.4, "smer": None}]
    nap.zapisi(c, nap.pripni(c, v, ZDAJ)[0], {"a": ("1001", ZDAJ - 20, 46.1, 14.4)}, ZDAJ)
    assert klici == ["1001"]



def test_prehodna_zavrnitev_prijave_ne_cakaj_deset_minut():
    """17. 10. 2026 6:35 in 7:36: NAP pod obremenitvijo vrne 401 z isto
    prijavo, ki je minuto prej delala, in se čez minuto vrne sam."""
    from kajros import nap
    assert nap.cakaj_po_zavrnitvi(1, 30) == nap.ZAVRNJENA_CAKAJ_S
    assert nap.cakaj_po_zavrnitvi(2, 120) == nap.ZAVRNJENA_CAKAJ_S
    assert nap.cakaj_po_zavrnitvi(3, 180) == nap.NI_DOSTOPA_CAKAJ_S
    # Brez uspeha v zadnji uri (ali od zagona) je zavrnitev prava.
    assert nap.cakaj_po_zavrnitvi(1, 1e9) == nap.NI_DOSTOPA_CAKAJ_S


def test_zaklenjena_baza_ni_molk_nap():
    """3. 11. 2026: uvoz je bazo držal ~80 s, NAP je molčal > `NAP_VODI_S` in
    derp.si je ob koncu zaklepa prepisal 98 meritev NAP."""
    iz_lege.nap_prebran(ZDAJ)
    iz_lege.nap_zaklenjen(ZDAJ + 40)                     # zapis čakal 30 s, padel
    assert iz_lege.nap_vodi("1123", ZDAJ + 90)            # konec zaklepa: še NAP
    assert not iz_lege.nap_vodi("1123", ZDAJ + 101)
    iz_lege.nap_zaklenjen(ZDAJ + 200)                    # NAP, ki ne vodi, ne obudi
    assert not iz_lege.nap_vodi("1123", ZDAJ + 201)


def test_nit_nap_po_zaklenjeni_bazi_vodi_naprej(monkeypatch, tmp_path):
    stop = threading.Event()
    pot, poveži = tmp_path / "kajros.sqlite", db.connect
    db.init(poveži(pot))

    def korak(conn, vsebina, zdaj):
        stop.set()
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(db, "connect", lambda: poveži(pot))
    monkeypatch.setattr(nap, "prijava", lambda: ("a", "b"))
    monkeypatch.setattr(nap, "beri", lambda seja, p: b"")
    monkeypatch.setattr(nap, "korak", korak)
    iz_lege.nap_prebran(time.time() - 50)
    nap.teci(stop, lambda s: None)
    assert iz_lege.nap_vodi("1123", time.time() + 30)
    assert "napaka" not in json.loads(db.get_meta(poveži(pot), "nap") or "{}")


def test_nap_vodi_le_ko_kaj_pripne(monkeypatch):
    """Presoja 31. 10. 2026: prazen ali nepripet odgovor 200 je prej vodil in
    derp.si se za medkrajevne ni vklopil -- vozila brez zamud."""
    monkeypatch.setattr(iz_lege, "_nap_ts", 0.0)
    c = _baza()
    nap.korak(c, _odgovor(), ZDAJ)                                # prazen
    assert not iz_lege.nap_vodi("1123", ZDAJ)
    nap.korak(c, _odgovor(_va("950133", 9999, ZDAJ - 20)), ZDAJ)  # vožnje ne poznamo
    assert not iz_lege.nap_vodi("1123", ZDAJ)
    nap.korak(c, _odgovor(_va("950133", 1001, ZDAJ - 20)), ZDAJ)
    assert iz_lege.nap_vodi("1123", ZDAJ)


# ------------------------------------------------------------- senca pripisa

def _baza_senca(dan_t1: str = DAN):
    """A (14,00) -> B (14,10) -> C (14,20) na isti vzporednici, 10 min na
    odsek. 3001 ob 16:00 A->C, v verigi z 3002 ob 16:50 C->A; 3001 vozi na
    `dan_t1`, 3002 na DAN."""
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "A", 46.0, 14.0), ("B", "B", 46.0, 14.1), ("C", "C", 46.0, 14.2)])
    for tid, sid, zacetek, postaje in (("3001", "s1", 16 * 3600, "ABC"),
                                       ("3002", "s2", 16 * 3600 + 3000, "CBA")):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network, block_id) VALUES(?, 'r', ?, ?, 'bus', '1123', 'avtobus', 'b')",
                  (tid, tid, sid))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                      [(tid, i + 1, p, zacetek + 600 * i, zacetek + 600 * i)
                       for i, p in enumerate(postaje)])
    c.executemany("INSERT INTO service_day(service_id, date) VALUES(?, ?)",
                  [("s1", dan_t1), ("s2", DAN)])
    db.fill_trip_window(c)
    c.commit()
    return c


def _senca(c):
    return [tuple(r) for r in c.execute(
        "SELECT ts, vozilo, vzrok, nap_voznja, nasa_voznja, nas_dan, razlog, zamuda_s "
        "FROM pripis_senca ORDER BY ts")]


def test_senca_pripne_vožnjo_ki_je_naš_koledar_na_praznik_nima():
    """NAP javi 3001, ki po našem uvozu ta dan ne vozi (`brez_dneva`); vozilo
    vozi po njeni trasi ob njeni uri -> senca jo pripne na današnji dan. V
    `vehicle_now`, `run`, `obs` nič."""
    c = _baza_senca(dan_t1="2026-10-09")
    t1, t2 = POLNOC + 16 * 3600 + 480, POLNOC + 16 * 3600 + 720
    nap.korak(c, _odgovor(_va("v1", 3001, t1, lat=46.0, lon=14.08), odgovor=t1), t1)
    st = nap.korak(c, _odgovor(_va("v1", 3001, t2, lat=46.0, lon=14.12), odgovor=t2), t2)
    vrste = _senca(c)
    # Napredek rabi dve opazovanji, vrata smeri premik naprej od 2-5 min nazaj.
    assert [r[6] for r in vrste] == ["miruje", ""]
    assert vrste[1][2:6] == ("brez_dneva", "3001", "3001", DAN)
    assert abs(vrste[1][7]) < 30
    assert st["senca"]["par"] == 1 and st["senca"]["racunov"] == 2
    for tabela in ("vehicle_now", "run", "obs"):
        assert c.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] == 0


def test_senca_vozilo_ki_se_obrne_vrata_smeri_izpustijo():
    """Vozilo pripelje čez B in se počasi vrača proti A: kraj na 3001 pada
    11 s na minuto, pod `NAZAJ_S`, napredek pa ostane (naslednji postanek se
    je na varianti že spremenil). Brez vrat smeri bi ostalo na 3001."""
    c = _baza_senca(dan_t1="2026-10-09")
    t0 = POLNOC + 16 * 3600 + 480
    lege = [(t0, 14.08), (t0 + 180, 14.11)] + [(t0 + 180 + 60 * k, 14.11 - 0.003 * k)
                                               for k in range(1, 5)]
    for ts, lon in lege:
        nap.korak(c, _odgovor(_va("v1", 3001, ts, lat=46.0, lon=lon), odgovor=ts), ts)
    assert [r[6] for r in _senca(c)] == ["miruje", "", "", "", "smer", "smer"]
    assert nap.senca.stevci["smer"] == 2


def test_senca_vozilo_ki_nap_javi_naslednjo_drži_na_prejšnji_v_verigi():
    """NAP ob 16:08 javi 3002 (16:50, `prezgodaj`), vozilo pa vozi 3001."""
    c = _baza_senca()
    t1, t2 = POLNOC + 16 * 3600 + 480, POLNOC + 16 * 3600 + 720
    nap.korak(c, _odgovor(_va("v1", 3002, t1, lat=46.0, lon=14.08), odgovor=t1), t1)
    nap.korak(c, _odgovor(_va("v1", 3002, t2, lat=46.0, lon=14.12), odgovor=t2), t2)
    assert _senca(c)[-1][2:7] == ("prezgodaj", "3002", "3001", DAN, "")


def test_senca_računa_vozilo_enkrat_na_minuto_in_vožnje_drugega_ne_da():
    c = _baza_senca()
    t1 = POLNOC + 16 * 3600 + 480
    for dt in (0, 30):
        nap.korak(c, _odgovor(_va("v1", 3002, t1 + dt, lat=46.0, lon=14.08), odgovor=t1 + dt), t1 + dt)
    assert len(_senca(c)) == 1
    # 3001 ima drugo vozilo (NAP ga je pripel): vozilu v1 ni prosta.
    t2 = POLNOC + 16 * 3600 + 720
    nap.korak(c, _odgovor(_va("v1", 3002, t2, lat=46.0, lon=14.12),
                          _va("v2", 3001, t2, lat=46.0, lon=14.121), odgovor=t2), t2)
    assert _senca(c)[-1][4:7] == (None, None, "ni_prosta")


def test_napaka_sence_ne_ustavi_leg(monkeypatch):
    c = _baza()
    def pade(*a, **k):
        raise RuntimeError("senca")
    monkeypatch.setattr(nap.senca, "opazuj", pade)
    st = nap.korak(c, _odgovor(_va("a", 1001, ZDAJ - 5)), ZDAJ)
    assert st["senca"] == {"napaka": "RuntimeError: senca"}
    assert [tuple(r) for r in c.execute("SELECT vehicle_id FROM vehicle_now")] == [("a",)]


def test_senca_obreže_starejše_od_14_dni():
    c = _baza_senca()
    c.execute("INSERT INTO pripis_senca(ts, vozilo, dan, vzrok, nap_voznja, razlog, kandidatov, "
              "lat, lon) VALUES(?, 'x', '2026-09-20', 'prezgodaj', '1', 'vec', 2, 46, 14)",
              (int(ZDAJ) - 15 * 86400,))
    nap.senca.opazuj(c, [], [], None, ZDAJ)
    assert _senca(c) == []
