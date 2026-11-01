"""Dosje vozila (`dosje.py`): vsak vzorec vsakega vozila, in kaj smo iz njega naredili.

    ./venv/bin/python -m pytest tests/test_dosje.py -q
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from google.transit import gtfs_realtime_pb2 as pb
from starlette.requests import Request

from kajros import api, collector, config, db, dosje, kranj, marprom, nap, zamude_sz, zdravje

TZ = ZoneInfo("Europe/Ljubljana")
ZDAJ = int(datetime(2026, 11, 1, 13, 0, tzinfo=TZ).timestamp())
DAN = "2026-11-01"


@pytest.fixture(autouse=True)
def _prazen():
    """Stanje modula je globalno, kot pri `straza`."""
    dosje.pocisti()
    dosje.vklopi()
    yield
    dosje.pocisti()


@pytest.fixture()
def baza(tmp_path, monkeypatch):
    pot = tmp_path / "dosje.sqlite"
    monkeypatch.setattr(config, "DOSJE_DB", pot)
    conn = dosje.povezi(pot)
    yield conn
    conn.close()


def _opazi(vozilo="1302014", ts=ZDAJ, lat=46.0, lon=14.0, zdaj=ZDAJ, **k):
    k.setdefault("kljuc", ("voznja-a",))
    k.setdefault("telo", {"voznja": "a"})
    dosje.opazi("nap", vozilo, ts, lat, lon, zdaj=zdaj, **k)


def _tocke(conn, vozilo="1302014"):
    out = []
    for r in conn.execute("SELECT vsebina FROM tocke WHERE vozilo = ? ORDER BY od_ts", (vozilo,)):
        out += json.loads(zlib.decompress(r[0]))
    return out


def test_vzorec_brez_vklopa_ne_pusti_nic():
    """Malina in ukazna vrstica nimata niti, ki bi praznila: medpomnilnik bi rasel."""
    dosje.pocisti()
    _opazi()
    dosje.oznaci("1302014", "brez_zamude")
    assert not dosje._vozila and not dosje._stanja and not dosje._oznake


def test_stanje_samo_ob_spremembi_tocke_vsak_vzorec(baza):
    for i in range(4):
        _opazi(ts=ZDAJ + i * 10, lat=46.0 + i / 1000, zdaj=ZDAJ + i * 10, trip_id="T1", dan=DAN)
    _opazi(ts=ZDAJ + 40, zdaj=ZDAJ + 40, trip_id="T2", dan=DAN)
    dosje.izprazni(baza, ZDAJ + 50, vse=True)
    assert [r[0] for r in baza.execute("SELECT trip_id FROM stanje ORDER BY ts")] == ["T1", "T2"]
    assert len(_tocke(baza)) == 5
    assert baza.execute("SELECT vzorcev, prvic, nazadnje FROM vozilo_dan WHERE razlog = ''"
                        ).fetchone()[:] == (5, ZDAJ, ZDAJ + 40)


def test_ponovljen_vzorec_vira_ni_nova_tocka_a_se_steje(baza):
    _opazi()
    _opazi(zdaj=ZDAJ + 10)
    dosje.izprazni(baza, ZDAJ + 20, vse=True)
    assert len(_tocke(baza)) == 1
    assert baza.execute("SELECT vzorcev FROM vozilo_dan WHERE razlog = ''").fetchone()[0] == 2


def test_razlog_gre_v_dnevnik_in_v_stetje_po_dnevu(baza):
    _opazi(razlogi=("brez_dneva",))
    _opazi(ts=ZDAJ + 10, zdaj=ZDAJ + 10, razlogi=("brez_dneva",))
    _opazi(ts=ZDAJ + 20, zdaj=ZDAJ + 20, trip_id="T1", dan=DAN)
    dosje.izprazni(baza, ZDAJ + 30, vse=True)
    assert [r[0] for r in baza.execute("SELECT razlogi FROM stanje ORDER BY ts")] == ["brez_dneva", ""]
    assert dict(baza.execute("SELECT razlog, vzorcev FROM vozilo_dan").fetchall()) == {
        "": 3, "brez_dneva": 2}


def test_telo_je_po_vsebini_in_se_racuna_le_ob_novem_kljucu(baza):
    klici = []

    def telo():
        klici.append(1)
        return {"voznja": "a"}

    _opazi(telo=telo)
    _opazi(ts=ZDAJ + 10, zdaj=ZDAJ + 10, telo=telo, razlogi=("miruje",))    # isti ključ
    _opazi(vozilo="drugo", telo=telo)                                       # ista vsebina
    dosje.izprazni(baza, ZDAJ + 20, vse=True)
    assert len(klici) == 2
    assert baza.execute("SELECT COUNT(*) FROM telo").fetchone()[0] == 1
    v = baza.execute("SELECT vsebina FROM telo").fetchone()[0]
    assert json.loads(zlib.decompress(v)) == {"voznja": "a"}


def test_ura_vira_in_mirovanje_za_vse_vire_enako(baza):
    assert dosje.STARA_LEGA_S == collector.POSITION_FRESH_S
    _opazi(vozilo="stara", ts=ZDAJ - dosje.STARA_LEGA_S - 1)
    _opazi(vozilo="naprej", ts=ZDAJ + dosje.URA_NAPREJ_S + 1)
    for i in (0, 1):
        _opazi(vozilo="stoji", ts=ZDAJ + i * dosje.MIRUJE_S, zdaj=ZDAJ + i * dosje.MIRUJE_S,
               lat=46.0 + i / 100000, trip_id="T1", dan=DAN)
    dosje.izprazni(baza, ZDAJ + dosje.MIRUJE_S, vse=True)
    razlogi = {r[0]: r[1] for r in baza.execute(
        "SELECT vozilo, razlogi FROM stanje WHERE razlogi != ''")}
    assert razlogi == {"stara": "stara_lega", "naprej": "ura_naprej", "stoji": "miruje"}


def test_mirovanje_brez_voznje_ni_razlog(baza):
    """Vozilo v garaži brez vožnje stoji po pravici."""
    for i in (0, 1):
        _opazi(vozilo="garaza", ts=ZDAJ + i * dosje.MIRUJE_S, zdaj=ZDAJ + i * dosje.MIRUJE_S)
    dosje.izprazni(baza, ZDAJ + dosje.MIRUJE_S, vse=True)
    assert baza.execute("SELECT COUNT(*) FROM stanje WHERE razlogi != ''").fetchone()[0] == 0


def test_oznaka_iz_preverjanja_velja_dokler_se_obnavlja(baza):
    dosje.oznaci("1302014", "brez_zamude", ZDAJ)
    _opazi(zdaj=ZDAJ + 10)
    _opazi(ts=ZDAJ + 500, zdaj=ZDAJ + 500)
    dosje.izprazni(baza, ZDAJ + 600, vse=True)
    assert [r[0] for r in baza.execute("SELECT razlogi FROM stanje ORDER BY ts")] == ["brez_zamude", ""]


def test_kos_se_zapre_sele_po_svojem_casu(baza):
    _opazi()
    assert dosje.izprazni(baza, ZDAJ + dosje.KOS_S - 1)["kosov"] == 0
    assert dosje.izprazni(baza, ZDAJ + dosje.KOS_S)["kosov"] == 1


def test_napaka_v_telesu_ne_doseze_vira():
    def pokvarjeno():
        raise ValueError("x")
    _opazi(telo=pokvarjeno)
    assert dosje._stevci["napak"] == 1


def test_medpomnilnik_je_zamejen():
    for i in range(dosje.NAJVEC_TOCK + 3):
        _opazi(ts=ZDAJ + i, zdaj=ZDAJ + i)
    assert len(dosje._vozila[("nap", "1302014")].tocke) == dosje.NAJVEC_TOCK
    assert dosje._stevci["izgubljenih"] == 3


def test_obrez_samo_tock_in_zamud(baza):
    _opazi(zdaj=ZDAJ)
    dosje.izprazni(baza, ZDAJ, vse=True)
    baza.execute("INSERT INTO zamude VALUES('x', 'derp', ?, 't', x'00')", (ZDAJ,))
    baza.commit()
    dosje.obrezi(baza, ZDAJ + 400 * 86400)
    assert baza.execute("SELECT COUNT(*) FROM tocke").fetchone()[0] == 0
    assert baza.execute("SELECT COUNT(*) FROM zamude").fetchone()[0] == 0
    assert baza.execute("SELECT COUNT(*) FROM stanje").fetchone()[0] == 1
    assert baza.execute("SELECT COUNT(*) FROM vozilo_dan").fetchone()[0] >= 1


def test_surova_napoved_samo_za_vozilo_z_razlogom_in_na_svoj_razmik(baza):
    feed = pb.FeedMessage()
    for vozilo in ("slabo", "dobro"):
        e = feed.entity.add()
        e.id = vozilo
        e.trip_update.trip.trip_id = f"T-{vozilo}"
        e.trip_update.vehicle.id = vozilo
    _opazi(vozilo="slabo", razlogi=("brez_dneva",))
    _opazi(vozilo="dobro")
    dosje.zamude("derp", feed, ZDAJ)
    dosje.zamude("derp", feed, ZDAJ + 30)
    dosje.izprazni(baza, ZDAJ + 40, vse=True)
    vrstice = baza.execute("SELECT vozilo, trip_id, vsebina FROM zamude").fetchall()
    assert [(r[0], r[1]) for r in vrstice] == [("slabo", "T-slabo")]
    tu = pb.TripUpdate()
    tu.ParseFromString(zlib.decompress(vrstice[0][2]))
    assert tu.vehicle.id == "slabo"


# ---------------------------------------------------------------- viri

def _vp(vozilo="V1", trip="T1", ts=ZDAJ, tablica="", pozicija=True):
    v = pb.VehiclePosition()
    v.vehicle.id = vozilo
    v.vehicle.license_plate = tablica
    v.trip.trip_id = trip
    v.trip.start_date = DAN.replace("-", "")
    v.timestamp = ts
    if pozicija:
        v.position.latitude, v.position.longitude, v.position.bearing = 46.0, 14.0, 90.0
    return v


def test_gtfs_telo_brez_sprotnega_oznaka_po_tablici(baza):
    v = _vp(tablica="LJ 123")
    v.current_stop_sequence = 4
    v.stop_id = "S4"
    dosje.opazi_gtfs("lpp", v, "T1", DAN, zdaj=ZDAJ)
    v2 = _vp(ts=ZDAJ + 10, tablica="LJ 123")
    v2.current_stop_sequence = 5
    dosje.opazi_gtfs("lpp", v2, "T1", DAN, zdaj=ZDAJ + 10)
    dosje.izprazni(baza, ZDAJ + 20, vse=True)
    assert baza.execute("SELECT COUNT(*) FROM stanje").fetchone()[0] == 1
    telo = json.loads(zlib.decompress(baza.execute("SELECT vsebina FROM telo").fetchone()[0]))
    assert telo["trip"]["trip_id"] == "T1" and telo["vehicle"]["license_plate"] == "LJ 123"
    assert "position" not in telo and "stop_id" not in telo
    assert [t[3]["seq"] for t in _tocke(baza, "V1")] == [4, 5]
    assert baza.execute("SELECT oznaka, vozilo FROM oznaka").fetchone()[:] == ("LJ 123", "V1")


def _ingest_conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (DAN,))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network, agency, "
              "start_s, end_s, first_seq, last_seq) "
              "VALUES('T1', 'r', 'A1', 'S1', 'bus', 'avtobus', '1123', 45000, 49000, 1, 3)")
    return c


def test_ingest_positions_pove_brez_voznje_in_vozilo_brez_lege(baza):
    feed = pb.FeedMessage()
    for i, v in enumerate((_vp("A"), _vp("B", "neznana"), _vp("C", pozicija=False))):
        e = feed.entity.add()
        e.id = str(i)
        e.vehicle.CopyFrom(v)
    collector.ingest_positions(_ingest_conn(), feed)
    dosje.izprazni(baza, time.time() + 1, vse=True)
    vrstice = {r[0]: (r[1], r[2]) for r in baza.execute("SELECT vozilo, trip_id, razlogi FROM stanje")}
    assert vrstice["A"][0] == "T1"
    assert vrstice["B"][0] is None and "brez_voznje" in vrstice["B"][1]
    assert vrstice["C"][0] is None and "brez_lege" in vrstice["C"][1]


_SIRI = """<Siri xmlns="http://www.siri.org.uk/siri"><ServiceDelivery>
<ResponseTimestamp>{odgovor}</ResponseTimestamp><VehicleMonitoringDelivery>{vozila}
</VehicleMonitoringDelivery></ServiceDelivery></Siri>"""
_VA = """<VehicleActivity><RecordedAtTime>{cas}</RecordedAtTime><ValidUntilTime>x</ValidUntilTime>
<MonitoredVehicleJourney><LineRef>L1</LineRef><PublishedLineName>Bled</PublishedLineName>
<VehicleLocation><Longitude>14.1</Longitude><Latitude>46.3</Latitude></VehicleLocation>
<Bearing>76</Bearing>{ref}<VehicleRef>{vozilo}</VehicleRef>
<JourneyParts><JourneyPartInfo><JourneyPartRef>P1</JourneyPartRef></JourneyPartInfo>
<JourneyPartInfo><JourneyPartRef>P2</JourneyPartRef></JourneyPartInfo></JourneyParts>
</MonitoredVehicleJourney></VehicleActivity>"""


def _iso(ts):
    return datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%dT%H:%M:%S")


def _siri(*vozila):
    return _SIRI.format(odgovor=_iso(ZDAJ), vozila="".join(
        _VA.format(cas=_iso(ts), vozilo=v, ref=(
            f"<VehicleJourneyRef>SI:SI0:ServiceJourney:00000000-1177-0008-0000-{ref:012x}:IJPP"
            "</VehicleJourneyRef>" if ref else ""))
        for v, ts, ref in vozila)).encode()


def test_nap_izpuscena_vozila_so_v_dosjeju(baza):
    """Prav vozilo, ki ga `razberi` izpusti, je tisto, s katerim je kaj narobe
    (1302136: RecordedAtTime 3. 11., 1. 11. 2026)."""
    surovo: dict = {}
    vozila, st = nap.razberi(_siri(("ok", ZDAJ - 5, 1001), ("naprej", ZDAJ + 2 * 86400, 1001),
                                   ("staro", ZDAJ - 900, 1001), ("brezid", ZDAJ - 5, 0)),
                             ZDAJ, surovo)
    assert [v["vozilo"] for v in vozila] == ["ok"] and set(surovo) == {"ok"}
    assert (st["naprej"], st["starih"], st["brez_id"]) == (1, 1, 1)
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    razlogi = {r[0]: r[1] for r in baza.execute("SELECT vozilo, razlogi FROM stanje")}
    assert razlogi == {"naprej": "ura_naprej", "staro": "stara_lega", "brezid": "brez_id"}


def test_nap_brez_vklopa_razbor_ostane_isti():
    dosje.pocisti()
    vozila, _ = nap.razberi(_siri(("ok", ZDAJ - 5, 1001)), ZDAJ)
    assert set(vozila[0]) == {"vozilo", "ijpp", "ts", "lat", "lon", "smer", "nacin"}


def test_nap_vzrok_iz_pripenjanja_in_razlika_z_derp(baza):
    surovo: dict = {}
    vozila, _ = nap.razberi(_siri(("a", ZDAJ - 5, 1001), ("b", ZDAJ - 5, 1002), ("c", ZDAJ - 5, 1003)),
                            ZDAJ, surovo)
    pripeta = [{**vozila[0], "trip_id": "T1", "dan": DAN}]
    za_senco = [(vozila[0], "T1", "pred_odhodom"), (vozila[1], "1002", "brez_dneva")]
    nap._v_dosje(vozila, pripeta, za_senco, surovo, {"a": ("9999", 0, 0, 0)}, ZDAJ)
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    razlogi = {r[0]: (r[1], r[2]) for r in baza.execute("SELECT vozilo, trip_id, razlogi FROM stanje")}
    assert razlogi == {"a": ("T1", "pred_odhodom,vira_razlicna"), "b": (None, "brez_dneva"),
                       "c": (None, "ni_avtobus")}
    telo = {json.loads(zlib.decompress(r[0]))["VehicleRef"]: json.loads(zlib.decompress(r[0]))
            for r in baza.execute("SELECT vsebina FROM telo")}
    assert telo["a"]["JourneyParts"] == ["P1", "P2"] and telo["a"]["PublishedLineName"] == "Bled"
    assert "VehicleLocation" not in telo["a"]


def test_marprom_vse_iz_odgovora_vzrok_in_oznaka(baza):
    x = {"DeviceId": 472, "BusCode": "184", "RouteId": 6970, "LineId": 73, "Lat": 46.567,
         "Lon": 15.632, "NextStopPointId": 91, "Predicted": 1, "ETA": 2,
         "DirectionDescription": "Kamnica"}
    v = marprom.razberi({"Vehicles": [x]})[0]
    s = marprom.Vozilo(zakaj="ni_prihoda")
    marprom._v_dosje(v, s, ZDAJ, "marprom-472", ZDAJ)
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    assert baza.execute("SELECT razlogi FROM stanje").fetchone()[0] == "brez_voznje,ni_prihoda,ni_ziva"
    telo = json.loads(zlib.decompress(baza.execute("SELECT vsebina FROM telo").fetchone()[0]))
    assert telo["BusCode"] == "184" and "Lat" not in telo and "NextStopPointId" not in telo
    assert _tocke(baza, "marprom-472")[0][3]["NextStopPointId"] == 91
    assert baza.execute("SELECT oznaka FROM oznaka").fetchone()[0] == "184"


def test_kranj_razberi_nosi_sporocilo_za_dosje(baza):
    feed = pb.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    e = feed.entity.add()
    e.id = "1"
    e.vehicle.CopyFrom(_vp("KRJN601", "neznana", ZDAJ - 5))
    vozila, _ = kranj.razberi(feed.SerializeToString())
    c = _ingest_conn()
    st = kranj.korak(c, vozila, ZDAJ)
    assert st["brez_voznje"] == 1
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    assert baza.execute("SELECT vozilo, razlogi FROM stanje").fetchone()[:] == (
        "kranj-KRJN601", "brez_voznje")


VRSTICA = {"St_vlaka": "4203", "St": 1, "Postaja_SZ_OD": "42400", "Relacija": "Jesenice-Nova Gorica",
           "St_postaje": "44710", "Postaja": "Solkan", "Odhod": "08:46",
           "Koordinate": "13.6497,45.9689", "Vrsta": 1, "Zamuda_cas": 50, "Predviden_prihod": 7,
           "Vrsta_vlaka": "V", "Rang": "LP"}


def test_vlak_je_vozilo_po_stevilki(baza):
    druga = {**VRSTICA, "St_vlaka": "4204", "Koordinate": ""}
    stoji = {**VRSTICA, "St_vlaka": "4205", "Vrsta": 0}
    zamude_sz._v_dosje([VRSTICA, druga, stoji], {"T1": "4203"},
                       [("T1", DAN, 3, 3000, False)], [], ZDAJ)
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    vrstice = {r[0]: (r[1], r[2]) for r in baza.execute("SELECT vozilo, trip_id, razlogi FROM stanje")}
    assert vrstice == {"vlak-4203": ("T1", ""), "vlak-4204": (None, "nepripet"), "vlak-4205": (None, "")}
    t = _tocke(baza, "vlak-4203")[0]
    assert (t[1], t[2]) == (45.9689, 13.6497) and t[3]["Zamuda_cas"] == 50
    telo = [json.loads(zlib.decompress(r[0])) for r in baza.execute("SELECT vsebina FROM telo")]
    assert all("Zamuda_cas" not in x and "St" not in x and x["Rang"] == "LP" for x in telo)


def test_vlak_isti_odgovor_ni_nova_tocka(baza):
    zamude_sz._v_dosje([VRSTICA], {"T1": "4203"}, [("T1", DAN, 3, 3000, False)], [], ZDAJ)
    zamude_sz._v_dosje([VRSTICA], {"T1": "4203"}, [("T1", DAN, 3, 3000, False)], [], ZDAJ + 15)
    zamude_sz._v_dosje([{**VRSTICA, "Zamuda_cas": 51}], {"T1": "4203"},
                       [("T1", DAN, 3, 3000, False)], [], ZDAJ + 30)
    dosje.izprazni(baza, ZDAJ + 40, vse=True)
    assert [t[3]["Zamuda_cas"] for t in _tocke(baza, "vlak-4203")] == [50, 51]


# ---------------------------------------------------------------- branje

def _glavna(tmp_path):
    pot = tmp_path / "glavna.sqlite"
    c = db.connect(pot)
    db.init(c)
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode, network,"
              " agency, first_seq, last_seq) "
              "VALUES('T1', 'r', 'A6376', 'Ljubljana - Bled', 'S1', 'bus', 'avtobus', '1123', 1, 3)")
    c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon, vozilo) "
              "VALUES(?, 'T1', ?, 46.0, 14.0, '1302014')", (DAN, ZDAJ))
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('T1', ?, 2, 120, 180, ?)", (DAN, ZDAJ))
    c.commit()
    c.close()
    return pot


def test_porocilo_zdruzi_dosje_in_glavno_bazo(baza, tmp_path):
    _opazi(razlogi=("brez_dneva",), oznaka="LJ 123", sprotno={"smer": 76})
    _opazi(ts=ZDAJ + 10, zdaj=ZDAJ + 10, trip_id="T1", dan=DAN, sprotno={"smer": 80})
    dosje.izprazni(baza, ZDAJ + 20, vse=True)
    izpis = dosje.porocilo("1302014", dosje_db=config.DOSJE_DB, glavna_db=_glavna(tmp_path),
                           tocke=True, surovo=True)
    for del_ in ("VOZILO 1302014  (LJ 123)", f"{DAN}  nap ×2", "NAROBE nap:brez_dneva ×1",
                 "brez vožnje", "A6376 → Ljubljana - Bled", "[brez_dneva]", 'telo: {"voznja":"a"}',
                 "lega 1", "run 1 postankov do 2", "zadnja zamuda 180 s", "točke: 2 v 1 kosih",
                 '{"smer": 80}'):
        assert del_ in izpis, del_


def test_porocilo_najde_po_tablici_in_brez_predpone(baza):
    _opazi(vozilo="marprom-472", oznaka="184")
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    for iskano in ("184", "472", "marprom-472"):
        assert "VOZILO marprom-472" in dosje.porocilo(iskano, dosje_db=config.DOSJE_DB,
                                                      glavna_db=config.DOSJE_DB)
    assert "ni v dosjeju" in dosje.porocilo("nič", dosje_db=config.DOSJE_DB)


def test_porocilo_ni_baze(tmp_path):
    assert "dosjeja ni" in dosje.porocilo("x", dosje_db=tmp_path / "ni.sqlite")
    assert "dosjeja ni" in dosje.seznam(dosje_db=tmp_path / "ni.sqlite")


def test_seznam_vozil_z_razlogi(baza):
    _opazi(vozilo="a", razlogi=("brez_dneva",))
    _opazi(vozilo="b", razlogi=("miruje",))
    _opazi(vozilo="c")
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    izpis = dosje.seznam(dosje_db=config.DOSJE_DB)
    assert f"{DAN}: vozil 3, z razlogom 2" in izpis and "nap:brez_dneva ×1" in izpis
    samo = dosje.seznam(razlog="miruje", dosje_db=config.DOSJE_DB)
    assert "z razlogom 1" in samo and "nap:brez_dneva" not in samo


def test_teci_izprazni_ob_ustavitvi_in_zapise_povzetek(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DOSJE_DB", tmp_path / "dosje.sqlite")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "glavna.sqlite")
    monkeypatch.setattr(dosje, "IZPRAZNI_S", 0.01)
    c = db.connect(tmp_path / "glavna.sqlite")
    db.init(c)
    c.close()
    stop = threading.Event()
    nit = threading.Thread(target=dosje.teci, args=(stop, print))
    nit.start()
    _opazi(zdaj=time.time())
    deadline = time.time() + 5
    while time.time() < deadline:
        c = db.connect(tmp_path / "glavna.sqlite")
        m = db.get_meta(c, "dosje")
        c.close()
        if m:
            break
        time.sleep(0.02)
    stop.set()
    nit.join(5)
    assert json.loads(m)["vzorcev"] == 1
    d = sqlite3.connect(tmp_path / "dosje.sqlite")
    assert d.execute("SELECT COUNT(*) FROM tocke").fetchone()[0] == 1


# ---------------------------------------------------------------- zdravje

@pytest.mark.parametrize("molk, razred", [(60, zdravje.DOBRA), (zdravje.DOSJE_MOLK_S, zdravje.MLACNA),
                                          (zdravje.VIR_ORANZNO_S, zdravje.ORANZNA)])
def test_vrstica_zdravja_nikoli_rdeca(molk, razred):
    """Dosje je za diagnozo: potnik ne vidi nič. Popravi ga le zagon, zato oranžno, ko traja."""
    z = {"dosje": {"ts": ZDAJ - molk}}
    assert zdravje.ocena(z, {}, ZDAJ)["dosje"][0] == razred


# ---------------------------------------------------------------- /admin

def _zahteva(piskotek: str | None = None) -> Request:
    glave = [(b"host", b"kajros.app")]
    if piskotek:
        glave.append((b"cookie", f"{api.ADMIN_PISKOTEK}={piskotek}".encode()))
    return Request({"type": "http", "method": "GET", "path": "/admin/vozila",
                    "raw_path": b"/admin/vozila", "query_string": b"", "headers": glave,
                    "scheme": "https", "server": ("kajros.app", 443)})


def test_admin_poti_samo_z_zetonom_in_samo_get(baza, monkeypatch):
    """Dosje ima id-je in lege vozil, ne potnikov -- a je pogled skrbnika, kot vse v /admin."""
    _opazi(razlogi=("miruje",))
    dosje.izprazni(baza, ZDAJ + 1, vse=True)
    monkeypatch.setattr(config, "ADMIN_TOKEN", "pravi")
    klici = (lambda z: api.admin_vozila(z, None, None),
             lambda z: api.admin_vozilo(z, "1302014", None, False, False))
    for klic in klici:
        with pytest.raises(HTTPException) as e:
            klic(_zahteva())
        assert e.value.status_code == 404
        assert b"1302014" in klic(_zahteva("pravi")).body
    poti = [r for r in api.app.routes
            if getattr(r, "path", "") in ("/admin/vozila", "/admin/vozilo/{vozilo}")]
    assert len(poti) == 2 and all(r.methods == {"GET", "HEAD"} for r in poti)


def test_povezava_iz_vrstice_zdravja_na_dosje():
    z = {"lega_brez_zamude_primeri": {"Arriva": [{"trip_id": "T1", "vozilo": "13/02", "lat": 46.0,
                                                  "lon": 14.0, "oznaka": "A1"}]}}
    assert zdravje.primeri(z)["lega_brez_zamude"][0]["dosje"] == "/admin/vozilo/13%2F02"
