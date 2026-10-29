"""Strani statistike: dnevni agregati in okna (`kajros/statistika.py`).

Zakaj je to vredno testa: številke teh strani bo bral vsak, ki hoče vedeti,
koliko zamujajo vlaki -- tudi novinar. Napaka v vsoti se na zaslonu ne vidi,
vidi se šele, ko nekdo isto prešteje sam in dobi drugo.

    ./venv/bin/python -m pytest tests/test_statistika.py -q
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

import pytest

from kajros import db, ocena, statistika, stats


def _danes():
    """Dan, kot ga vidi modul (Ljubljana), ne stroj: okoli polnoči UTC se razlikujeta."""
    return datetime.now(statistika.TZ).date()


# ---------------------------------------------------------------- vsote

@pytest.mark.parametrize("omrezje", ["zeleznica", "avtobus"])
def test_vsote_dajo_iste_stevilke_kot_kajros_ocena(omrezje):
    """Stran in `kajros ocena` morata za iste vrstice reči isto. Dve
    definiciji MAE ali precenitve na istih podatkih bi pomenili dve resnici."""
    rnd = random.Random(7)
    pari = [(rnd.randint(-300, 2400), rnd.randint(-300, 2400)) for _ in range(500)]
    v = statistika._vsote()
    for napoved, resnica in pari:
        statistika._pristej(v, napoved, resnica, ocena.RAZMIK_S[omrezje])
    nase = statistika.meritve(v)
    njihove = ocena._meritve(pari, omrezje)
    for kljuc in ("n", "mae_min", "v2min", "v5min", "precenjenih", "podcenjenih",
                  "odklon_min", "strosek_min"):
        assert nase[kljuc] == njihove[kljuc], kljuc


def test_vsota_dni_je_vsota_vrstic():
    """Okno je vsota dni: dva dneva posebej in skupaj morata dati isto."""
    a, b, skupaj = statistika._vsote(), statistika._vsote(), statistika._vsote()
    for i, (n, r) in enumerate([(60, 0), (400, 30), (-200, 100), (900, 900)]):
        statistika._pristej(a if i < 2 else b, n, r, 87 * 60)
        statistika._pristej(skupaj, n, r, 87 * 60)
    statistika._sestej(a, b)
    assert a == skupaj


# ---------------------------------------------------------------- histogram

def test_razredi_iz_histograma_se_ujemajo_z_delezem_v_5_min():
    """„v 5 min“ = točno + 1–5 min, po ISTI zaokroženi minuti kot zaslon
    (`preveri_skladnost.py` straži isto na drugih straneh)."""
    hist = {"-2": 3, "0": 10, "1": 4, "5": 2, "6": 5, "15": 1, "16": 2, "40": 1}
    r = statistika.iz_histograma(hist)
    assert r["n"] == 28
    v5 = 3 + 10 + 4 + 2
    assert r["v5min"] == round(v5 / 28 * 100, 1)
    assert r["razredi"]["tocno"] == round(13 / 28 * 100, 1)
    assert r["razredi"]["1-5"] == round(6 / 28 * 100, 1)
    # 15 min je še „5–15“, 16 že „nad 15“ (`stats._razred_zamude`).
    assert r["razredi"]["5-15"] == round(6 / 28 * 100, 1)
    assert r["nad15"] == r["razredi"]["nad-15"] == round(3 / 28 * 100, 1)


def test_kvantil_iz_histograma_je_isti_kot_iz_seznama():
    vrednosti = [0, 0, 1, 1, 1, 3, 5, 5, 12, 40]
    hist = {}
    for v in vrednosti:
        hist[str(v)] = hist.get(str(v), 0) + 1
    r = statistika.iz_histograma(hist)
    assert r["mediana_min"] == stats._pct(vrednosti, 0.5)
    assert r["p90_min"] == stats._pct(vrednosti, 0.9)


# ---------------------------------------------------------------- iz baze

def _baza(dnevi_nazaj=(1,)):
    """Dva vlaka in nadomestni avtobus SŽ, meritve na `dnevi_nazaj` dni pred
    današnjim. Dnevi računani, vstavki `OR IGNORE` (CLAUDE.md: trd datum v
    pripravi + računan v testu = bomba)."""
    c = db.connect(":memory:")
    db.init(c)
    ocena.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "Ajdovščina", 45.887, 13.905), ("B", "Branik", 45.85, 13.78),
                   ("C", "Celje", 46.229, 15.266)])
    voznje = [("v1", "LP 1", "vlak"), ("v2", "LP 2", "vlak"), ("bus1", "BUS 3", "bus")]
    for tid, no, mode in voznje:
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                  " mode, network, agency) VALUES(?,?,?,?, 'S1', ?, 'zeleznica', '1161')",
                  (tid, "r" + tid, no, "Celje", mode))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s)"
                      " VALUES(?,?,?,?,?)",
                      [(tid, 1, "A", None, 28800), (tid, 2, "B", 29400, 29460),
                       (tid, 3, "C", 30000, None)])
    for nazaj in dnevi_nazaj:
        dan = (_danes() - timedelta(days=nazaj)).isoformat()
        c.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S1', ?)", (dan,))
        # LP 1 pride 2 min pozno, LP 2 dvajset; vmes LP 2 odpelje minuto prej.
        c.executemany("INSERT OR IGNORE INTO run(trip_id, service_date, stop_seq,"
                      " delay_arr, delay_dep, feed_ts) VALUES(?,?,?,?,?, 4102444800)",
                      [("v1", dan, 2, 60, 60), ("v1", dan, 3, 120, None),
                       ("v2", dan, 2, -70, -70), ("v2", dan, 3, 1200, None)])
        # Senca: LP 1 25 min prej, naša 100 s, prenos 60 s, resnica 120 s;
        # LP 2 pred odhodom, naša 600 s, prevoznik 0, resnica 1200 s.
        c.executemany("INSERT OR IGNORE INTO napoved(trip_id, service_date, stop_seq,"
                      " network, made_ts, horizon_s, current_s, from_seq, ours_s,"
                      " ours_own_s, operator_s, carry_s, actual_s, resolved_ts)"
                      " VALUES(?,?,3,'zeleznica',0,1500,?,?,?,?,?,?,?,0)",
                      [("v1", dan, 60, 2, 100, 100, None, 60, 120),
                       ("v2", dan, None, None, 600, 600, 0, None, 1200)])
    db.fill_trip_window(c)
    c.commit()
    return c


def test_dopolni_racuna_le_sklenjene_dni_in_ne_dvakrat():
    c = _baza(dnevi_nazaj=(1, 2))
    izracunani = statistika.dopolni(c, _danes())
    vceraj = (_danes() - timedelta(days=1)).isoformat()
    assert vceraj in izracunani
    assert _danes().isoformat() not in izracunani
    # Drugi klic v isti noči ne računa znova (okna ga kličejo štirikrat).
    assert statistika.dopolni(c, _danes()) == []


def test_prevozniki_pokritost_tocnost_in_nadomestni_posebej():
    c = _baza()
    p = statistika.prevozniki(c, 90, "zeleznica", danes=_danes())
    po = {x["skupina"]: x for x in p["prevozniki"]}
    vlak = po["vlak"]
    assert vlak["ime"] == "SŽ"
    assert vlak["pokritost"] == 100.0           # dva od dveh vlakov z meritvijo
    assert vlak["cilj"]["n"] == 2
    assert vlak["cilj"]["v5min"] == 50.0       # LP 1 +2 min da, LP 2 +20 ne
    assert vlak["cilj"]["nad15"] == 50.0
    # Vmesni postanek: LP 2 −70 s = „1 min prej“, LP 1 +1 min ne.
    assert vlak["prezgodaj"]["vmesnih"] == 2
    assert vlak["prezgodaj"]["prej1"] == 50.0
    assert vlak["prezgodaj"]["prej2"] == 0.0
    # Nadomestni: načrtovan, brez meritve -- pokritost 0, ne „brez načrta“.
    assert po["nadomestni"]["pokritost"] == 0.0


def test_nacrt_neznan_ko_je_izmerjenih_vec_kot_nacrtovanih():
    """Mestni LPP: uvoz pobriše vožnje preteklih dni, meritve ostanejo. To ni
    150-odstotna pokritost, ampak neznan načrt."""
    c = _baza()
    vceraj = (_danes() - timedelta(days=1)).isoformat()
    c.execute("DELETE FROM service_day WHERE date = ?", (vceraj,))
    c.commit()
    p = statistika.prevozniki(c, 90, "zeleznica", danes=_danes())
    vlak = next(x for x in p["prevozniki"] if x["skupina"] == "vlak")
    assert vlak["nacrt"] is None and vlak["pokritost"] is None
    assert vlak["cilj"]["n"] == 2              # točnost ostane izmerjena


def test_napovedi_parno_in_po_skupinah():
    c = _baza()
    n = statistika.napovedi(c, 90, "zeleznica", danes=_danes())
    na_poti = n["skupaj"]["na_poti"]["vse"]
    assert na_poti["nasa"]["n"] == 1
    assert na_poti["nasa"]["mae_min"] == round(20 / 60, 2)
    assert na_poti["prenos"]["mae_min"] == 1.0
    assert na_poti["vozni_red"]["mae_min"] == 2.0
    # Pred odhodom ni prenosa: aplikacija s trenutno zamudo pokaže vozni red.
    pred = n["skupaj"]["pred_odhodom"]
    assert pred["vse"]["prenos"]["mae_min"] == pred["vse"]["vozni_red"]["mae_min"] == 20.0
    # Prevoznik le v parnem izrezu, kjer je imel vrednost (LP 2).
    assert pred["parno"]["prevoznik"]["n"] == 1
    assert na_poti.get("prevoznik") is None
    assert n["po_tednih"] and n["po_tednih"][-1]["nasa"]["n"] == 1


def test_lestvica_samo_z_dovolj_dnevi(monkeypatch):
    monkeypatch.setattr(statistika, "MIN_DNI_LESTVICA", 2)
    c = _baza(dnevi_nazaj=(1, 2, 3))
    p = statistika.prevozniki(c, 90, "zeleznica", danes=_danes())
    vlak = next(x for x in p["prevozniki"] if x["skupina"] == "vlak")
    lest = vlak["lestvica"]
    assert [x["st"] for x in lest["najboljse"]][0] == "LP 1"
    assert lest["najslabse"][0]["st"] == "LP 2"
    assert lest["najslabse"][0]["n"] == 3
    # Nadomestni avtobus ni na lestvici vlakov.
    assert all(x["st"] != "BUS 3" for x in lest["najboljse"] + lest["najslabse"])


def test_povzetek_gre_skozi_summary_build():
    """Okni sta v `SUMMARY_BUILDERS`: nočni izračun in API ju dobita sama."""
    c = _baza()
    for kind in ("stat_napovedi", "stat_prevozniki"):
        got = stats.summary_build(c, kind, "zeleznica", 90)
        assert got["v"] == stats.SUMMARY_VERSION
        assert got["through"] == (_danes() - timedelta(days=1)).isoformat()


def test_pokritost_od_prvega_dne_zajema():
    """Marprom: vozni red sega v začetek meseca, zajem šele od 27. 10. Dnevi
    pred zajemom niso vožnje brez podatka."""
    c = _baza(dnevi_nazaj=(1,))
    predvceraj = (_danes() - timedelta(days=2)).isoformat()
    c.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S1', ?)", (predvceraj,))
    c.commit()
    p = statistika.prevozniki(c, 90, "zeleznica", danes=_danes())
    vlak = next(x for x in p["prevozniki"] if x["skupina"] == "vlak")
    assert vlak["pokritost"] == 100.0
    assert vlak["zajem_od"] == (_danes() - timedelta(days=1)).isoformat()


# ---------------------------------------------------------------- strani

def test_zamuda_z_besedo_ne_z_minusom():
    """`oznake.md`: minus je uganka -- „5,5 min prej“, ničla je „točno“."""
    assert statistika.zamuda_min(-5.5) == "5,5 min prej"
    assert statistika.zamuda_min(0) == "točno"
    assert statistika.zamuda_min(22.5) == "+22,5 min"
    assert statistika.zamuda_min(4.0) == "+4 min"
    assert statistika.odstotek(58.5) == "59 %"      # floor(x + 0.5), ne bančno


def _zahteva(pot: str):
    from starlette.requests import Request
    return Request({"type": "http", "method": "GET", "path": pot, "raw_path": pot.encode(),
                    "query_string": b"", "headers": [(b"host", b"kajros.app")],
                    "scheme": "https", "server": ("kajros.app", 443)})


@pytest.fixture()
def strani(monkeypatch):
    """Majhna baza, meje vzorca na ena: izrišejo se vse kartice, tudi tiste,
    ki bi jih sicer skril premajhen vzorec -- napaka v predlogi pade tu."""
    from kajros import api
    c = _baza(dnevi_nazaj=(1, 2, 3))
    monkeypatch.setattr(api, "_conn", lambda: c)
    for ime in ("MIN_VZOREC", "MIN_VOZENJ_PRIMERJAVA", "MIN_DNI_PRIMERJAVA", "MIN_DNI_LESTVICA"):
        monkeypatch.setattr(statistika, ime, 1)
    return api


def test_strani_statistike_se_izrisejo(strani):
    api = strani
    for pot, klic in (("/statistika", lambda r: api.statistika_pregled(r)),
                      ("/statistika/napovedi", lambda r: api.statistika_napovedi(r)),
                      ("/statistika/prevozniki", lambda r: api.statistika_prevozniki(r)),
                      ("/statistika/prevoznik/sz", lambda r: api.statistika_prevoznik(r, "sz"))):
        odgovor = klic(_zahteva(pot))
        assert odgovor.status_code == 200, pot
        html = odgovor.body.decode()
        assert "st-k" in html or "st-seznam" in html, pot
    sz = api.statistika_prevoznik(_zahteva("/statistika/prevoznik/sz"), "sz").body.decode()
    assert "50 %" in sz                       # LP 1 v 5 min, LP 2 ne
    assert "Nadomestni avtobusi SŽ" in sz          # feed zanje ne poroča


def test_neznan_prevoznik_je_404(strani):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        strani.statistika_prevoznik(_zahteva("/statistika/prevoznik/x"), "x")
    assert e.value.status_code == 404


def test_zemljevid_strani_bere_samo_shranjeno():
    """Brez povzetka strani statistike ni v zemljevidu in nič se ne računa;
    s povzetkom so tam pregled, napovedi, prevozniki in vsak prevoznik."""
    c = _baza()
    assert statistika.poti_za_iskalnik(c) == []
    stats.summary_build(c, "stat_prevozniki", "zeleznica", 90)
    poti = [p for p, _ in statistika.poti_za_iskalnik(c)]
    assert "/statistika" in poti and "/statistika/prevoznik/sz" in poti


def test_stran_vlaka_in_preusmeritev(strani):
    """Stran vlaka nastane ob nočnem izračunu prevoznikov; „LP 1“ v naslovu
    gre s 301 na `lp-1`, neznan vlak je 404."""
    from fastapi import HTTPException
    api = strani
    stats.summary_build(api._conn(), "stat_prevozniki", "zeleznica", 90)
    odgovor = api.statistika_vlak(_zahteva("/statistika/vlak/lp-1"), "lp-1")
    assert odgovor.status_code == 200
    html = odgovor.body.decode()
    assert "LP 1" in html and "Kje nabere zamudo" in html
    assert api.statistika_vlak(_zahteva("/statistika/vlak/LP 1"), "LP 1").status_code == 301
    with pytest.raises(HTTPException):
        api.statistika_vlak(_zahteva("/statistika/vlak/lp-9"), "lp-9")


def test_sz_odhod_prezgodaj_in_popravek():
    """Zemljevid SŽ premakne LP 2 čez Branik ob voznem redu z zamudo 0, nato
    jo dvigne na 10 min; potnik z GPS je odpeljal 5 min po prvem zapisu."""
    from kajros import deljenje
    c = _baza(dnevi_nazaj=(1,))
    deljenje.init(c)
    dan = (_danes() - timedelta(days=1)).isoformat()
    prvic = stats.polnoc(dan) + 29460            # voznoredni odhod z Branika
    c.executemany("INSERT INTO obs(trip_id, service_date, stop_seq, delay_arr, delay_dep,"
                  " feed_ts, observed_at) VALUES('v2', ?, 2, NULL, ?, ?, ?)",
                  [(dan, 0, prvic, prvic), (dan, 600, prvic + 600, prvic + 600)])
    c.execute("INSERT INTO deljenje_prehod(deljenje, trip_id, service_date, stop_seq,"
              " prihod_ts, odhod_ts) VALUES(1, 'v2', ?, 2, NULL, ?)", (dan, prvic + 300))
    c.commit()
    p = statistika.sz(c, 90, "zeleznica", danes=_danes())
    assert p["popravki"]["postankov"] == 1
    assert p["popravki"]["dvig10"] == 100.0
    assert p["potniki"]["n"] == 1 and p["potniki"]["prej2"] == 100.0
    assert p["potniki"]["najhujsi"][0]["prej_s"] == 300
    assert statistika.sz(c, 90, "avtobus", danes=_danes())["runs"] == 0


def test_stran_sz_se_izrise(strani, monkeypatch):
    monkeypatch.setattr(statistika, "MIN_PREHODOV", 0)
    odgovor = strani.statistika_sz(_zahteva("/statistika/sz"))
    assert odgovor.status_code == 200
    assert "Kaj kažejo podatki SŽ" in odgovor.body.decode()


def test_relacija_vlak_trajanje_in_tocnost():
    """Ajdovščina → Celje: vozni red 20 min, LP 1 +2 min, LP 2 +20 min."""
    c = _baza(dnevi_nazaj=(1,))
    od, do = statistika._okno(_danes())
    p = statistika._par(c, "zeleznica", "Ajdovščina", "Celje", od, do)
    assert p["n"] == 2
    assert p["trajanje_vr"] == 20.0
    assert p["v5min"] == 50.0
    assert statistika._par(c, "zeleznica", "Celje", "Ajdovščina", od, do) is None   # obratna smer ne vozi
    assert statistika.relacije(c, 90, "avtobus")["runs"] == 0


def test_stran_relacij_se_izrise(strani):
    odgovor = strani.statistika_relacije(_zahteva("/statistika/relacije"))
    assert odgovor.status_code == 200
    assert "Vlak, avtobus ali avto?" in odgovor.body.decode()
