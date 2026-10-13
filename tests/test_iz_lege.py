"""Zamuda iz lege vozila za vožnje, ki jih feed zamud ne nosi.

Proga je ravna črta vzhodno od (46, 14): postajališča A, B, C, D so 0,01°
(~773 m) narazen, vozni red na pet minut. Vozilo, ki je ob 10:12:00 malo pred
C in ob 10:12:20 malo za njim, je C prevozilo ob 10:12:10 -- torej +130 s.

    ./venv/bin/python -m pytest tests/test_iz_lege.py -q
"""
from __future__ import annotations

import json
import time
from datetime import date

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import config, db, deljenje, iz_lege, odkloni, prehod, stats

DAN = date.today().isoformat()
POLNOC = stats.polnoc(DAN)
LON = {"A": 14.00, "B": 14.01, "C": 14.02, "D": 14.03}


@pytest.fixture(autouse=True)
def _cist_spomin(monkeypatch):
    # Lega na traso je od 13. 10. 2026 rezerva (`KAJROS_PREHOD_GPS=0`);
    # prehod brez trase preizkuša tests/test_prehod.py.
    monkeypatch.setattr(config, "PREHOD_GPS", "0")
    for s in (iz_lege._v_feedu, iz_lege._sled, iz_lege._zadnja, iz_lege._odklon,
              iz_lege._zadnji_nabor, deljenje._predpomnilnik, deljenje._trase,
              prehod._sledi):
        s.clear()
    iz_lege._prvic = None
    yield
    for s in (iz_lege._v_feedu, iz_lege._sled, iz_lege._zadnja, iz_lege._odklon,
              iz_lege._zadnji_nabor, deljenje._predpomnilnik, deljenje._trase,
              prehod._sledi):
        s.clear()
    iz_lege._prvic = None


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46.0,?)",
                  [(k, k, v) for k, v in LON.items()])
    tocke = [[46.0, 14.0 + i * 0.001] for i in range(31)]
    c.execute("INSERT INTO shape(shape_id, points) VALUES('sh', ?)", (json.dumps([tocke]),))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id,"
              " mode, agency, network) VALUES('n', 'r', 'N1', 'D', 'S', 'sh', 'bus', '1119', 'avtobus')")
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('n',?,?,?,?)",
                  [(1, "A", None, 36000), (2, "B", 36300, 36300),
                   (3, "C", 36600, 36600), (4, "D", 36900, None)])
    db.fill_trip_window(c)
    c.commit()
    return c


def _ts(ura_s):
    return int(POLNOC + ura_s)


def _run(c):
    return [tuple(r) for r in c.execute(
        "SELECT stop_seq, delay_arr, delay_dep FROM run ORDER BY stop_seq")]


def test_prehod_postanka_da_zamudo():
    c = _baza()
    assert iz_lege.opazuj(c, "n", DAN, _ts(36720), 46.0, 14.019) == 0
    assert iz_lege.opazuj(c, "n", DAN, _ts(36740), 46.0, 14.021) == 1
    assert _run(c) == [(3, None, 130)]
    # Prehod je potrjen: vrednost nosi čas lege PO prehodu.
    assert c.execute("SELECT feed_ts FROM run").fetchone()[0] == _ts(36740)


def test_koncna_postaja_je_prihod():
    """Za D je vozni red samo prihod (36 900); lega za koncem trase je na njem."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(37000), 46.0, 14.029)
    iz_lege.opazuj(c, "n", DAN, _ts(37020), 46.0, 14.0305)
    assert _run(c) == [(4, 120, None)]


def test_izhodisca_ne_merimo():
    """Pred odhodom vozilo kroži po postajališču; prehod izhodišča laže."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(35400), 46.0, 13.9995)
    iz_lege.opazuj(c, "n", DAN, _ts(35420), 46.0, 14.0005)
    assert _run(c) == []


def test_skok_lege_ni_prehod():
    """Dva kilometra v 20 s je napačna projekcija, ne vožnja."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36400), 46.0, 14.001)
    iz_lege.opazuj(c, "n", DAN, _ts(36420), 46.0, 14.027)
    assert _run(c) == []
    # Zapiše se kot preskok: trasa ima tu lahko zanko, ki je vozilo ne vozi.
    (o,) = [dict(r) for r in c.execute("SELECT * FROM odklon")]
    assert (o["vrsta"], o["od_ts"], o["do_ts"], o["leg"]) == ("preskok", _ts(36400), _ts(36420), 0)
    assert o["along_za"] - o["along_pred"] > 1900


def test_predolg_razmik_ni_prehod():
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36500), 46.0, 14.019)
    iz_lege.opazuj(c, "n", DAN, _ts(36500 + iz_lege.NAJVEC_RAZMIK_S + 1), 46.0, 14.021)
    assert _run(c) == []


def test_tresenje_ob_postajaliscu_da_en_prehod():
    c = _baza()
    for ura, lon in ((36720, 14.019), (36740, 14.021), (36760, 14.0195), (36780, 14.0212)):
        iz_lege.opazuj(c, "n", DAN, _ts(ura), 46.0, lon)
    assert _run(c) == [(3, None, 130)]


def test_lega_dalec_od_trase_se_ne_steje():
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36720), 46.0, 14.019)
    iz_lege.opazuj(c, "n", DAN, _ts(36740), 46.01, 14.021)      # 1,1 km severno
    assert _run(c) == []


def _odkloni(c):
    return [dict(r) for r in c.execute("SELECT * FROM odklon ORDER BY od_ts")]


def test_odklon_se_zapise_s_sidroma():
    """Vozilo zapelje 1,1 km s trase in se vrne: ena vrstica z legama na trasi
    pred odklonom in za njim -- iz takih se vidi, kod vozilo res vozi."""
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36500), 46.0, 14.012)
    iz_lege.opazuj(c, "n", DAN, _ts(36520), 46.01, 14.014)
    iz_lege.opazuj(c, "n", DAN, _ts(36540), 46.01, 14.016)
    assert _odkloni(c) == [], "zapiše se, ko se vrne"
    iz_lege.opazuj(c, "n", DAN, _ts(36560), 46.0, 14.018)
    (o,) = _odkloni(c)
    assert (o["trip_id"], o["service_date"], o["shape_id"], o["leg"], o["vrsta"]) == ("n", DAN, "sh", 2, "izven")
    assert (o["od_ts"], o["do_ts"]) == (_ts(36520), _ts(36540))
    assert o["along_pred"] < o["along_za"] and 1000 < o["odmik_max"] < 1200
    assert json.loads(o["tocke"]) == [[_ts(36500), 46.0, 14.012], [_ts(36520), 46.01, 14.014],
                                      [_ts(36540), 46.01, 14.016], [_ts(36560), 46.0, 14.018]]


def test_pot_na_izhodisce_in_v_garazo_ni_odklon():
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(35900), 46.0, 14.0005)       # čaka na izhodišču
    iz_lege.opazuj(c, "n", DAN, _ts(35920), 46.01, 14.001)       # pred odhodom drugam
    iz_lege.opazuj(c, "n", DAN, _ts(36920), 46.0, 14.0299)       # prispel na D
    iz_lege.opazuj(c, "n", DAN, _ts(36940), 46.01, 14.031)       # v garažo
    iz_lege.pospravi(_ts(36940) + iz_lege.ODKLON_ZAPRI_S + 1, c)
    assert _odkloni(c) == []


def test_odklon_brez_vrnitve_zapise_pospravi():
    c = _baza()
    iz_lege.opazuj(c, "n", DAN, _ts(36500), 46.0, 14.012)
    iz_lege.opazuj(c, "n", DAN, _ts(36520), 46.01, 14.014)
    iz_lege.pospravi(_ts(36520) + iz_lege.ODKLON_ZAPRI_S, c)
    assert _odkloni(c) == [], "še lahko pride nazaj"
    iz_lege.pospravi(_ts(36520) + iz_lege.ODKLON_ZAPRI_S + 1, c)
    (o,) = _odkloni(c)
    assert (o["leg"], o["along_za"]) == (1, None)
    assert len(json.loads(o["tocke"])) == 2


def test_odkloni_po_odsekih():
    """Vožnja n zapelje s trase med B in C, vožnja m isti odsek prevozi po
    njej: odsek B -> C je odklonjen pri enem od dveh prevozov."""
    c = _baza()
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, shape_id,"
              " mode, agency, network) VALUES('m', 'r', 'N2', 'D', 'S', 'sh', 'bus', '1119', 'avtobus')")
    c.execute("INSERT INTO sched SELECT 'm', stop_seq, stop_id, arr_s, dep_s FROM sched WHERE trip_id = 'n'")
    c.executemany("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts) VALUES('m', ?, ?, 0, ?)",
                  [(DAN, 2, _ts(36300)), (DAN, 3, _ts(36600))])
    for ura, lat, lon in ((36290, 46.0, 14.0095), (36310, 46.0, 14.0105),       # prehod B
                          (36500, 46.0, 14.012), (36520, 46.01, 14.014), (36540, 46.01, 14.016),
                          (36560, 46.0, 14.018), (36610, 46.0, 14.0195), (36630, 46.0, 14.0205)):
        iz_lege.opazuj(c, "n", DAN, _ts(ura), lat, lon)
    assert [r[0] for r in c.execute("SELECT stop_seq FROM run WHERE trip_id = 'n' ORDER BY 1")] == [2, 3]
    (o,) = odkloni.po_odsekih(c, 0, _ts(86400))
    assert (o["od"], o["do"], o["prevozov"], o["odklonjenih"], o["delez"]) == ("B", "C", 2, 1, 0.5)
    assert (o["od_ime"], o["dni"], o["leg"]) == ("B", 1, 2)
    assert odkloni.po_odsekih(c, _ts(36600), _ts(86400)) == [], "odklon je bil prej"


def _lege(*tocke):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    for i, (ura, lon) in enumerate(tocke):
        e = f.entity.add()
        e.id = str(i)
        e.vehicle.trip.trip_id = "n"
        e.vehicle.trip.start_date = DAN.replace("-", "")
        e.vehicle.timestamp = _ts(ura)
        e.vehicle.position.latitude, e.vehicle.position.longitude = 46.0, lon
    return f


def test_nespremenjen_feed_se_nosi_iste_voznje():
    """304 pomeni isto vsebino: vožnja, ki jo je feed nosil, je še v njem --
    ne pa "izpuščena", ko mine `FEED_POZABI_S`."""
    zdaj = time.time()
    iz_lege.zabelezi_feed(["n"], zdaj - 1000, vir="lpp")
    iz_lege.zabelezi_feed(["m"], zdaj - 1000, vir="ijpp")
    assert iz_lege.brez_feeda("n", zdaj) and iz_lege.brez_feeda("m", zdaj)
    iz_lege.feed_nespremenjen("lpp", zdaj)
    assert not iz_lege.brez_feeda("n", zdaj)
    assert iz_lege.brez_feeda("m", zdaj)          # drug vir ni potrjen


def test_iz_feeda_samo_za_vozje_ki_jih_feed_zamud_ne_nosi():
    c = _baza()
    iz_lege.zabelezi_feed(["n"], time.time() - 120)             # feed jo nosi
    iz_lege.iz_feeda(c, _lege((36720, 14.019)))
    iz_lege.iz_feeda(c, _lege((36740, 14.021)))
    assert _run(c) == []

    iz_lege._v_feedu.clear()                                     # feed jo izpušča
    iz_lege.iz_feeda(c, _lege((36720, 14.019)))
    assert iz_lege.iz_feeda(c, _lege((36740, 14.021))) == 1
    assert _run(c) == [(3, None, 130)]


def test_pred_prvim_branjem_feeda_nic():
    """Po zagonu še ne vemo, katere vožnje feed nosi -- ne ugibamo."""
    c = _baza()
    iz_lege.iz_feeda(c, _lege((36720, 14.019)))
    iz_lege.iz_feeda(c, _lege((36740, 14.021)))
    assert _run(c) == []


def test_feed_ki_od_zagona_ne_odgovori_je_po_casu_prazen(monkeypatch):
    """8. 10. 2026: derp.si ob zagonu mrtev. Brez meje bi drugi viri čakali
    na prvo branje do konca izpada in nobena vožnja ne bi bila „brez feeda“."""
    zdaj = time.time()
    monkeypatch.setattr(iz_lege, "_zagon", zdaj)
    assert not iz_lege.brez_feeda("x", zdaj + 60)
    assert iz_lege.brez_feeda("x", zdaj + iz_lege.FEED_POZABI_S + 1)
