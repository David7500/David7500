"""Zamude vlakov z zemljevida SŽ: pripenjanje na vožnjo, varovala, vodenje.

    ./venv/bin/python -m pytest tests/test_zamude_sz.py -q
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import date

import pytest
from google.transit import gtfs_realtime_pb2

from kajros import collector, db, iz_lege, stats, zamude_sz, zdravje

DAN = "2026-09-15"
POLNOC = stats.polnoc(DAN)


def _ura(h, m):
    return h * 3600 + m * 60


def _pozabi():
    iz_lege._v_feedu.clear()
    iz_lege._prvic = None
    iz_lege._sz_ts = 0.0
    zamude_sz._odtis = None


@pytest.fixture(autouse=True)
def _cist_spomin(monkeypatch):
    _pozabi()
    # Preizkus nikoli ne sme zagnati pravega Chroma.
    monkeypatch.setattr(zamude_sz.brskalnik, "zahtevaj",
                        lambda pot: pytest.fail("potniski.sz.si brez nadomestka"))
    yield
    _pozabi()


def _baza():
    """LP 4203 Jesenice - Nova Gorica, zadnji trije postanki, in njegova
    sezonska različica z isto številko uro prej."""
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("P", "Plave(Železniški)", 46.06, 13.58), ("S", "Solkan", 45.97, 13.65),
                   ("N", "Nova Gorica", 45.95, 13.64)])
    for tid, zamik in (("t1", 0), ("t2", -3600)):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network) VALUES(?, 'r', 'LP 4203', 's1', 'vlak', '1161', 'zeleznica')", (tid,))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)",
                      [(tid, 20, "P", _ura(7, 55) + zamik, _ura(7, 56) + zamik),
                       (tid, 21, "S", _ura(8, 7) + zamik, _ura(8, 7) + zamik),
                       (tid, 22, "N", _ura(8, 12) + zamik, None)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s1', ?)", (DAN,))
    db.fill_trip_window(c)
    c.commit()
    return c


# Vrstica v obliki, kot jo zemljevid SŽ vrača 10. 10. 2026 (`aktivni_vlaki`),
# z vrednostmi z 28. 9. 2026 ob 08:56, ko ga je za nas bral še modra.ninja.
VRSTICA = {"St_vlaka": "4203", "St": 1, "Postaja_SZ_OD": "42400", "Postaja_SZ_DO": "44700",
           "Relacija": "Jesenice-Nova Gorica", "St_postaje": "44710", "Postaja": "Solkan",
           "Odhod": "08:46", "Koordinate": "13.6497,45.9689", "Vrsta": 1, "Zamuda_cas": 50,
           "Predviden_prihod": 7, "Vrsta_vlaka": "V", "Rang": "LP"}
ZDAJ = POLNOC + _ura(8, 56)


def _vr(c):
    return zamude_sz.vozni_red(c, date.fromisoformat(DAN))


def test_zamuda_gre_na_zadnji_prevozeni_postanek():
    """Odhod z zemljevida = vozni red postanka PRED naslednjo postajo + zamuda.

    Enakost izbere tudi pravo od dveh voženj z isto številko: različica, ki
    vozi uro prej, bi dala odhod 07:46.
    """
    assert zamude_sz.pripni(VRSTICA, _vr(_baza())["4203"], ZDAJ) == ("t1", DAN, 20, 3000, False)


def test_neujemanje_odhoda_ne_pripne():
    """Raje nič kot napačna vožnja: odhod, ki se z voznim redom ne ujema."""
    assert zamude_sz.pripni({**VRSTICA, "Odhod": "08:30"}, _vr(_baza())["4203"], ZDAJ) is None


def test_pred_odhodom_in_brez_postaje_ni_meritve():
    """Na izhodišču ni prevoženega postanka; `Vrsta` 0 pomeni, da vlak še stoji
    -- `Odhod` je tedaj vozni red, ne meritev."""
    vr = _vr(_baza())["4203"]
    assert zamude_sz.pripni({**VRSTICA, "Postaja": "Plave"}, vr, ZDAJ) is None
    assert zamude_sz.pripni({**VRSTICA, "Postaja": ""}, vr, ZDAJ) is None
    assert zamude_sz.pripni({**VRSTICA, "Vrsta": 0}, vr, ZDAJ) is None


def test_prihod_na_cilj():
    """`Vrsta` 2: prazna postaja, `Odhod` je prihod na cilj z zamudo."""
    na_cilju = {**VRSTICA, "Vrsta": 2, "Postaja": "", "Odhod": "08:20", "Zamuda_cas": 8}
    assert (zamude_sz.pripni(na_cilju, _vr(_baza())["4203"], POLNOC + _ura(8, 21))
            == ("t1", DAN, 22, 480, True))


def test_avtobus_in_vlak_pred_odhodom_nista_nepripeta():
    """Zemljevid kaže nadomestni avtobus z zamudo 0 v točki postaje -- to ni
    meritev; vlak pred odhodom ni napaka pripenjanja."""
    vrstice = [{**VRSTICA, "Vrsta_vlaka": "B", "Rang": "BUS"}, {**VRSTICA, "Vrsta": 0}, VRSTICA]
    pripete, stevci = zamude_sz.razberi(vrstice, _vr(_baza()), ZDAJ)
    assert len(pripete) == 1
    assert stevci == {"vlakov": 2, "pred_odhodom": 1, "na_cilju": 0, "nepripetih": 0}


def test_zapis_v_run_ohrani_prihod():
    """Zemljevid pove le odhod; prihod, ki je v `run` od prej, ostane."""
    c = _baza()
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('t1', ?, 20, 2900, NULL, ?)", (DAN, ZDAJ - 300))
    izid = zamude_sz.zapisi(c, [("t1", DAN, 20, 3000, False)], ZDAJ)
    assert izid == {"zapisanih": 1, "nazaj": 0, "ponastavljenih": 0}
    assert c.execute("SELECT delay_arr, delay_dep, feed_ts FROM run WHERE stop_seq = 20"
                     ).fetchone()[:] == (2900, 3000, int(ZDAJ))
    assert c.execute("SELECT delay_s, v_run FROM sz_zamuda").fetchone()[:] == (3000, 1)
    assert c.execute("SELECT COUNT(*) FROM obs").fetchone()[0] == 1


def test_vlak_ne_gre_nazaj():
    """10. 10. 2026: LPV 2616 je po Brezovici spet pisal „naslednja Ljubljana
    Tivoli, +9“ -- in se ujemal z odhodom iz Ljubljane, ki jo je zapustil s +0."""
    c = _baza()
    zamude_sz.zapisi(c, [("t1", DAN, 21, 0, False)], ZDAJ)
    izid = zamude_sz.zapisi(c, [("t1", DAN, 20, 540, False)], ZDAJ + 30)
    assert izid["nazaj"] == 1
    assert c.execute("SELECT COUNT(*) FROM run WHERE stop_seq = 20").fetchone()[0] == 0
    # Popravek na istem odseku pa velja.
    assert zamude_sz.zapisi(c, [("t1", DAN, 21, 60, False)], ZDAJ + 60)["zapisanih"] == 1


def test_na_cilju_velja_prvi_prihod_nicla_po_zamudi_ni_prihod():
    """SŽ vrstico na cilju po 1--2 min ponastavi na zamudo 0 (1897: +7 -> 0)."""
    c = _baza()
    zamude_sz.zapisi(c, [("t1", DAN, 21, 480, False)], ZDAJ)
    assert zamude_sz.zapisi(c, [("t1", DAN, 22, 420, True)], ZDAJ + 30)["zapisanih"] == 1
    assert zamude_sz.zapisi(c, [("t1", DAN, 22, 0, True)], ZDAJ + 150)["zapisanih"] == 0
    assert c.execute("SELECT delay_arr, delay_dep FROM run WHERE stop_seq = 22"
                     ).fetchone()[:] == (420, None)
    # Ponastavitev, ki je prvi prihod, ki ga vidimo (zamudili smo pravega).
    zamude_sz.zapisi(c, [("t2", DAN, 21, 480, False)], ZDAJ)
    assert zamude_sz.zapisi(c, [("t2", DAN, 22, 0, True)], ZDAJ + 150)["ponastavljenih"] == 1
    # Točen prihod po točni vožnji pa je prihod.
    c2 = _baza()
    zamude_sz.zapisi(c2, [("t1", DAN, 21, 60, False)], ZDAJ)
    assert zamude_sz.zapisi(c2, [("t1", DAN, 22, 0, True)], ZDAJ + 30)["zapisanih"] == 1


def _feed_zamud(trip_id, zamuda):
    f = gtfs_realtime_pb2.FeedMessage()
    f.header.gtfs_realtime_version = "2.0"
    e = f.entity.add()
    e.id = "1"
    e.trip_update.trip.trip_id = trip_id
    e.trip_update.trip.start_date = DAN.replace("-", "")
    stu = e.trip_update.stop_time_update.add()
    stu.stop_sequence = 21
    stu.departure.delay = zamuda
    return f


def test_sz_vodi_le_dokler_je_zemljevid_prebran():
    assert not iz_lege.sz_vodi(ZDAJ)
    iz_lege.sz_prebran(ZDAJ)
    assert iz_lege.sz_vodi(ZDAJ + iz_lege.SZ_VODI_S)
    assert not iz_lege.sz_vodi(ZDAJ + iz_lege.SZ_VODI_S + 1)


def test_zajem_derp_vlakov_ne_pise_dokler_vodi_zemljevid():
    """Isti podatek prek dveh posrednikov ne sme prepisati izvirnika; ko
    zemljevid obmolkne, derp.si vlake spet piše."""
    c = _baza()
    iz_lege.sz_prebran()
    izid = collector.ingest(c, _feed_zamud("t1", 240))
    assert izid["sz_prevzel"] == 1 and izid["trips"] == 1
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
    iz_lege._sz_ts = 0.0
    assert collector.ingest(c, _feed_zamud("t1", 240))["sz_prevzel"] == 0
    assert c.execute("SELECT delay_dep FROM run").fetchone()[0] == 240


def test_nadomestni_avtobus_ostane_derp(monkeypatch):
    """Avtobusov na zemljevidu ni (le točka postaje): njihove zamude piše derp.si."""
    c = _baza()
    c.execute("UPDATE trip SET mode = 'bus' WHERE trip_id = 't1'")
    c.commit()
    iz_lege.sz_prebran()
    assert collector.ingest(c, _feed_zamud("t1", 240))["sz_prevzel"] == 0


def test_korak_zapise_kdaj_se_je_zemljevid_nazadnje_spremenil():
    c = _baza()
    zamude_sz._odtis = "a"
    s = zamude_sz.korak(c, [VRSTICA], ZDAJ)
    assert (s["vlakov"], s["zapisanih"], s["spremenjeno_ts"]) == (1, 1, int(ZDAJ))
    s = zamude_sz.korak(c, [VRSTICA], ZDAJ + 30)
    assert s["spremenjeno_ts"] == int(ZDAJ), "isti odgovor"
    zamude_sz._odtis = "b"
    assert zamude_sz.korak(c, [VRSTICA], ZDAJ + 60)["spremenjeno_ts"] == int(ZDAJ + 60)
    assert json.loads(db.get_meta(c, "zamude_sz"))["ts"] == int(ZDAJ + 60)


def test_nespremenjen_odgovor_ne_premakne_casa_podatka():
    """Branje na 5 s, SŽ preračuna na 15: isti odgovor samo potrdi, da vir
    živi -- vrednosti ostanejo s časom, ko jih je SŽ prvič povedal."""
    c = _baza()
    zamude_sz._odtis = "a"
    zamude_sz.korak(c, [VRSTICA], ZDAJ)
    feed_ts = c.execute("SELECT feed_ts FROM obs").fetchall()
    sz = c.execute("SELECT zadnjic_ts FROM sz_zamuda").fetchall()
    s = zamude_sz.korak(c, [VRSTICA], ZDAJ + 5, nespremenjeno=True)
    assert (s["ts"], s["zapisanih"], s["vlakov"]) == (int(ZDAJ + 5), 1, 1)
    assert c.execute("SELECT feed_ts FROM obs").fetchall() == feed_ts
    assert c.execute("SELECT zadnjic_ts FROM sz_zamuda").fetchall() == sz
    # Drug odtis kot v meta (npr. po napaki) se obdela, kot bi bil nov.
    zamude_sz._odtis = "b"
    assert zamude_sz.korak(c, [VRSTICA], ZDAJ + 10, nespremenjeno=True)["odtis"] == "b"


def test_zdravje_zemljevida():
    z = {"vozi_zdaj": {"zeleznica": 20, "avtobus": 300}}
    T = ZDAJ

    def ocena(zs):
        return zdravje.ocena({**z, "zamude_sz": zs}, {}, T)["zamude_sz"]

    assert ocena({"ts": T - 30, "vlakov": 20, "spremenjeno_ts": T - 30})[0] == zdravje.DOBRA
    assert ocena({"ts": T - 30, "vlakov": 20, "spremenjeno_ts": T - 700})[0] == zdravje.MLACNA
    assert ocena({"ts": T - 30, "vlakov": 0, "spremenjeno_ts": T - 30})[0] == zdravje.MLACNA
    r = ocena({"ts": T - 900, "vlakov": 20, "napaka": "ni Chroma", "napaka_ts": T - 20})
    assert r[0] == zdravje.MLACNA and "ni Chroma" in r[1]
    assert ocena({"ts": T - 900, "vlakov": 20, "napaka_ts": T - 900})[0] == zdravje.SLABA
    # Ponoči zemljevid ne sme biti ne prazen ne zamrznjen.
    z["vozi_zdaj"] = {"zeleznica": 1, "avtobus": 2}
    assert ocena({"ts": T - 30, "vlakov": 0, "spremenjeno_ts": T - 3600})[0] == zdravje.DOBRA


def test_nit_po_zaklenjeni_bazi_ne_obstane(tmp_path, monkeypatch):
    """1. 10. 2026: nočno vzdrževanje je drlo pisanje dlje od čakanja, nit je
    ostala v napol odprti transakciji z zamrznjenim posnetkom in nato 4 h na
    vsako pisanje dobivala „database is locked“, WAL pa je rasel."""
    pot = tmp_path / "k.sqlite"
    c = db.connect(pot)
    db.init(c)
    c.commit()
    pravi = db.connect

    def hitra(path=None):
        conn = pravi(pot)
        conn.execute("PRAGMA busy_timeout = 50")
        return conn

    monkeypatch.setattr(db, "connect", hitra)
    monkeypatch.setattr(zamude_sz, "_get", lambda: [])
    monkeypatch.setattr(zamude_sz.config, "SZ_ZAMUDE_SECONDS", 0)

    # Drugi pisec iz glavne niti, korak pa ga sprosti iz zajemne.
    vzdrzevanje = sqlite3.connect(pot, timeout=0.05, check_same_thread=False)
    vzdrzevanje.execute("BEGIN IMMEDIATE")
    vzdrzevanje.execute("INSERT INTO meta(key, value) VALUES('vzdrzevanje', '1')")
    stop, uspelih, klicev = threading.Event(), [], []

    def korak(conn, vrstice, zdaj, nespremenjeno=False):
        klicev.append(1)
        if len(klicev) == 2:
            # Vzdrževanje konča, zajem medtem zapiše svoje.
            vzdrzevanje.commit()
            vzdrzevanje.execute("INSERT INTO meta(key, value) VALUES('zajem', '1')")
            vzdrzevanje.commit()
        db.get_meta(conn, "zamude_sz")
        db.set_meta(conn, "zamude_sz", '{"ts": 1}')
        conn.commit()
        uspelih.append(len(klicev))
        stop.set()
        return {"vlakov": 0, "zapisanih": 0, "nepripetih": 0}

    monkeypatch.setattr(zamude_sz, "korak", korak)
    nit = threading.Thread(target=zamude_sz.teci, args=(stop, lambda _: None))
    nit.start()
    nit.join(5)
    stop.set()
    nit.join()
    assert uspelih, f"po {len(klicev)} poskusih nit še vedno ne more pisati"
    assert iz_lege.sz_vodi(), "uspešno branje prevzame vlake"


def test_napaka_vira_se_zapise_in_vlakov_ne_vodi(monkeypatch, tmp_path):
    """Brez Chroma nit zapiše razlog (pregled ga pokaže), vlake pa piše derp.si."""
    pot = tmp_path / "k.sqlite"
    pravi = db.connect
    c = pravi(pot)
    db.init(c)
    c.commit()
    monkeypatch.setattr(db, "connect", lambda path=None: pravi(pot))
    stop = threading.Event()

    def get():
        stop.set()
        raise RuntimeError("ni Chroma: namesti Google Chrome (deploy/brskalnik.sh)")

    monkeypatch.setattr(zamude_sz, "_get", get)
    dnevnik = []
    zamude_sz.teci(stop, dnevnik.append)
    meta = json.loads(db.get_meta(pravi(pot), "zamude_sz"))
    assert "ni Chroma" in meta["napaka"] and meta["napaka_ts"]
    assert not iz_lege.sz_vodi()
    assert "derp.si" in dnevnik[0]


def test_brez_vlakov_sz_vrne_null(monkeypatch):
    """Ob polnoči, ko ne vozi noben vlak, je odgovor `null` -- prazen zemljevid,
    ne napaka (10. 10. 2026 ob 23:58, po ponovnem zagonu arwena)."""
    monkeypatch.setattr(zamude_sz.brskalnik, "zahtevaj", lambda pot: "null")
    assert zamude_sz._get() == []
    monkeypatch.setattr(zamude_sz.brskalnik, "zahtevaj", lambda pot: '{"napaka": 1}')
    with pytest.raises(RuntimeError, match="seznama vlakov"):
        zamude_sz._get()
