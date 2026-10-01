"""Zamude vlakov z zemljevida SŽ: pripenjanje na vožnjo in primerjava z derp.si.

    ./venv/bin/python -m pytest tests/test_zamude_sz.py -q
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import date

import pytest

from kajros import db, iz_lege, stats, zamude_sz

DAN = "2026-09-15"
POLNOC = stats.polnoc(DAN)


def _ura(h, m):
    return h * 3600 + m * 60


@pytest.fixture(autouse=True)
def _cist_spomin():
    iz_lege._v_feedu.clear()
    iz_lege._prvic = None
    yield
    iz_lege._v_feedu.clear()
    iz_lege._prvic = None


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


# Vrstica, kot jo je zemljevid SŽ vrnil 28. 9. 2026 ob 08:56.
VRSTICA = {"st_vlaka": "4203", "rang_vlaka": "LP", "naslednja_postaja": "Solkan",
           "postaja_eta_min": 7, "zamuda_min": 50, "bus": False, "raw_odhod": "08:46"}
ZDAJ = POLNOC + _ura(8, 56)


def test_zamuda_gre_na_zadnji_prevozeni_postanek():
    """Odhod z zemljevida = vozni red postanka PRED naslednjo postajo + zamuda.

    Enakost izbere tudi pravo od dveh voženj z isto številko: različica, ki
    vozi uro prej, bi dala odhod 07:46.
    """
    c = _baza()
    vr = zamude_sz.vozni_red(c, date.fromisoformat(DAN))
    assert zamude_sz.pripni(VRSTICA, vr["4203"], ZDAJ) == ("t1", DAN, 20, 3000)


def test_neujemanje_odhoda_ne_pripne():
    """Raje nič kot napačna vožnja: odhod, ki se z voznim redom ne ujema."""
    c = _baza()
    vr = zamude_sz.vozni_red(c, date.fromisoformat(DAN))
    assert zamude_sz.pripni({**VRSTICA, "raw_odhod": "08:30"}, vr["4203"], ZDAJ) is None


def test_pred_odhodom_in_brez_postaje_ni_meritve():
    """Na izhodišču ni prevoženega postanka; prazna postaja = konec vožnje."""
    c = _baza()
    vr = zamude_sz.vozni_red(c, date.fromisoformat(DAN))
    assert zamude_sz.pripni({**VRSTICA, "naslednja_postaja": "Plave"}, vr["4203"], ZDAJ) is None
    assert zamude_sz.pripni({**VRSTICA, "naslednja_postaja": ""}, vr["4203"], ZDAJ) is None


def test_nadomestni_avtobus_se_ne_steje():
    """Zemljevid kaže avtobus z zamudo 0 v točki postaje -- to ni meritev."""
    c = _baza()
    vr = zamude_sz.vozni_red(c, date.fromisoformat(DAN))
    pripete, stevci = zamude_sz.razberi([{**VRSTICA, "bus": True}, VRSTICA], vr, ZDAJ)
    assert len(pripete) == 1 and stevci == {"vlakov": 1, "nepripetih": 0}


def test_brez_derp_gre_v_run_z_derp_samo_v_primerjavo():
    """Kadar derp.si vlaka nima, zemljevid zapolni `run`; kadar ga ima, se
    vira primerjata in `run` ostane derp.si-jev."""
    c = _baza()
    iz_lege.zabelezi_feed([], zdaj=ZDAJ - 1000)       # feed prebran, vlaka ni
    izid = zamude_sz.zapisi(c, [("t1", DAN, 20, 3000)], ZDAJ, {"t1", "t2"})
    assert izid == {"samo_sz": 1, "oba": 0, "samo_derp": 0}
    assert c.execute("SELECT delay_dep FROM run WHERE trip_id='t1' AND stop_seq=20"
                     ).fetchone()[0] == 3000
    assert zamude_sz.primerjava(c, ZDAJ - 60)["parov"] == 0, "vir se ne primerja sam s sabo"

    # derp.si nosi drugo vožnjo in zanjo pove +48 min na istem postanku.
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('t2', ?, 20, NULL, 2880, ?)", (DAN, ZDAJ))
    iz_lege.zabelezi_feed(["t2"], zdaj=ZDAJ)
    izid = zamude_sz.zapisi(c, [("t2", DAN, 20, 3000)], ZDAJ, {"t1", "t2"})
    assert izid == {"samo_sz": 0, "oba": 1, "samo_derp": 0}
    assert c.execute("SELECT delay_dep FROM run WHERE trip_id='t2' AND stop_seq=20"
                     ).fetchone()[0] == 2880, "derp.si-jeva vrednost se ne sme prepisati"
    p = zamude_sz.primerjava(c, ZDAJ - 60, najvec=5)
    assert (p["parov"], p["v_minuti"], p["mediana_s"], p["samo_sz"]) == (1, 0, 120, 1)
    assert p["najvecje"][0]["sz_min"] == 50 and p["najvecje"][0]["derp_min"] == 48


def test_vlak_samo_pri_derp_se_steje():
    """Obratna vrzel: derp.si nosi vlak, ki ga zemljevid nima."""
    c = _baza()
    iz_lege.zabelezi_feed(["t1"], zdaj=ZDAJ)
    assert zamude_sz.zapisi(c, [], ZDAJ, {"t1", "t2"})["samo_derp"] == 1


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
    monkeypatch.setattr(iz_lege, "feed_prebran", lambda: True)
    monkeypatch.setattr(zamude_sz, "_get", lambda: [])
    monkeypatch.setattr(zamude_sz.config, "SZ_ZAMUDE_SECONDS", 0)

    # Drugi pisec iz glavne niti, korak pa ga sprosti iz zajemne.
    vzdrzevanje = sqlite3.connect(pot, timeout=0.05, check_same_thread=False)
    vzdrzevanje.execute("BEGIN IMMEDIATE")
    vzdrzevanje.execute("INSERT INTO meta(key, value) VALUES('vzdrzevanje', '1')")
    stop, uspelih, klicev = threading.Event(), [], []

    def korak(conn, vrstice, zdaj):
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
        return {"vlakov": 0, "oba": 0, "samo_sz": 0, "samo_derp": 0, "nepripetih": 0}

    monkeypatch.setattr(zamude_sz, "korak", korak)
    nit = threading.Thread(target=zamude_sz.teci, args=(stop, lambda _: None))
    nit.start()
    nit.join(5)
    stop.set()
    nit.join()
    assert uspelih, f"po {len(klicev)} poskusih nit še vedno ne more pisati"
