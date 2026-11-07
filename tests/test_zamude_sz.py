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
    zamude_sz._prejsnji = {}
    zamude_sz._trenutne = {}
    zamude_sz._ustaljene = {}
    zamude_sz._skladnost.clear()


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


def _dvakrat(c, vrstice, zdaj):
    """Isto stanje v dveh zaporednih spremenjenih odgovorih: potrjeno
    (`zamude_sz.potrdi`). Vrne števce drugega."""
    zamude_sz._odtis = f"{zdaj}a"
    zamude_sz.korak(c, vrstice, zdaj)
    zamude_sz._odtis = f"{zdaj}b"
    return zamude_sz.korak(c, vrstice, zdaj)


def _odgovor(c, pripete, zdaj, prihodnje=()):
    """En spremenjen odgovor na ravni stanj: potrdi in zapiši potrjeno."""
    p, _, nepotrjeni = zamude_sz.potrdi(c, list(pripete), list(prihodnje))
    izid = zamude_sz.zapisi(c, p, zdaj)
    izid["nepotrjenih"] = len(nepotrjeni)
    return izid


def test_zamuda_gre_na_zadnji_prevozeni_postanek():
    """Odhod z zemljevida = vozni red postanka PRED naslednjo postajo + zamuda.

    Enakost izbere tudi pravo od dveh voženj z isto številko: različica, ki
    vozi uro prej, bi dala odhod 07:46.
    """
    assert zamude_sz.pripni(VRSTICA, _vr(_baza())["4203"], ZDAJ) == ("t1", DAN, 20, 3000, False)


def test_neujemanje_odhoda_ne_pripne():
    """Raje nič kot napačna vožnja: odhod, ki se z voznim redom ne ujema."""
    assert zamude_sz.pripni({**VRSTICA, "Odhod": "08:30"}, _vr(_baza())["4203"], ZDAJ) is None


def test_slivnica_z_zemljevida_je_spodnja_slivnica():
    """Zemljevid piše „Slivnica“, vozni red IJPP „Spodnja Slivnica“ (station
    1120963, edina postaja vlakov s tem imenom, 32 vlakov LP 4491--4537). Brez
    preslikave je bil vlak med Grosupljem in Slivnico nepripet: 143 od 153
    epizod nepripetih v tednu 1.--7. 11. 2026, Grosuplje oz. Čušperk brez
    meritve v 124 od 143. LP 4501 6. 11.: „Slivnica, Odhod 04:38, +0“."""
    dan = "2026-11-06"
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,45.9,14.6)",
                  [("L", "Ljubljana"), ("G", "Grosuplje"), ("SS", "Spodnja Slivnica"),
                   ("C", "Čušperk")])
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
              "VALUES('453667', 'r', 'LP 4501', 's1', 'vlak', '1161', 'zeleznica')")
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                  "VALUES('453667',?,?,?,?)",
                  [(1, "L", _ura(4, 16), _ura(4, 16)), (2, "G", _ura(4, 37), _ura(4, 38)),
                   (3, "SS", _ura(4, 41), _ura(4, 41)), (4, "C", _ura(4, 48), _ura(4, 48))])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s1', ?)", (dan,))
    db.fill_trip_window(c)
    c.commit()
    vrstica = {"St_vlaka": "4501", "Vrsta": 1, "Postaja": "Slivnica", "Odhod": "04:38",
               "Zamuda_cas": 0}
    zdaj = stats.polnoc(dan) + _ura(4, 38) + 40
    pripete, stevci, _ = zamude_sz.razberi(
        [vrstica], zamude_sz.vozni_red(c, date.fromisoformat(dan)), zdaj)
    assert pripete == [("453667", dan, 2, 0, False)]
    assert stevci["nepripetih"] == 0


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
    pripete, stevci, prihodnje = zamude_sz.razberi(vrstice, _vr(_baza()), ZDAJ)
    assert len(pripete) == 1 and prihodnje == []
    assert stevci == {"vlakov": 2, "pred_odhodom": 1, "na_cilju": 0, "nepripetih": 0,
                      "prihodnjih": 0, "nepripeti": []}


# Ista vožnja 15 s pozneje: SŽ je zamudo z +50 povečal na +65, vlak pa je s
# Plav odpeljal ob 08:46 (LP 314 16. 10. 2026: +5 -> +10, odhod 2,5 min naprej).
POVECANA = {**VRSTICA, "Odhod": "09:01", "Zamuda_cas": 65}


def test_odhod_v_prihodnosti_ni_prevozen_postanek_je_trenutna_zamuda():
    """Postanek, s katerega je vlak že odpeljal, ne sme postati neprevožen:
    +65 na Plavah bi pomenilo odhod ob 09:01. Zamuda vlaka zdaj pa je +65."""
    c = _baza()
    _dvakrat(c, [VRSTICA], ZDAJ)
    s = _dvakrat(c, [POVECANA], ZDAJ + 15)
    assert (s["zapisanih"], s["prihodnjih"], s["nepripetih"]) == (0, 1, 0)
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 20").fetchone()[0] == 3000
    lm = stats.last_measured(c, DAN, ["t1"], int(ZDAJ + 15 - POLNOC))["t1"]
    assert (lm["stop_seq"], lm["delay_s"], lm["trenutna_s"], lm["trenutna_seq"]) == (20, 3000, 3900, 20)
    assert stats.trenutna_zamuda(lm) == 3900
    # Brez novega odgovora minuto pozneje ne velja več.
    lm = stats.last_measured(c, DAN, ["t1"], int(ZDAJ + 15 + 61 - POLNOC))["t1"]
    assert "trenutna_s" not in lm and stats.trenutna_zamuda(lm) == 3000


def test_trenutna_zamuda_samo_navzgor():
    """Nižja zamuda SŽ od meje ne velja (prevoznik šteje samo navzgor), ničla
    po zamudi, ki je SŽ še ni potrdil, pa trenutne zamude ne izbriše."""
    c = _baza()
    _dvakrat(c, [VRSTICA], ZDAJ)
    zamude_sz._trenutne[("t1", DAN)] = (2000, int(ZDAJ), 20)
    lm = stats.last_measured(c, DAN, ["t1"], int(ZDAJ - POLNOC))["t1"]
    assert "trenutna_s" not in lm and lm["sz_ts"] == int(ZDAJ)
    _dvakrat(c, [POVECANA], ZDAJ + 15)
    zamude_sz._odtis = "c"
    nicla = {**VRSTICA, "Postaja": "Nova Gorica", "Odhod": "08:07", "Zamuda_cas": 0}
    assert zamude_sz.korak(c, [nicla], ZDAJ + 30)["nepotrjenih"] == 1
    assert zamude_sz.trenutne(DAN, ["t1"], ZDAJ + 30)["t1"]["s"] == 3900


def test_zemljevid_kaze_trenutno_zamudo_kot_okno_voznje():
    """Kartica vlaka na zemljevidu in glava okna vožnje: ista številka."""
    from kajros import api
    zamude_sz._trenutne[("t1", DAN)] = (840, int(ZDAJ), 20)
    vrstice = [{"trip_id": "t1", "service_date": DAN, "network": "zeleznica", "delay_s": 60},
               {"trip_id": "t2", "service_date": DAN, "network": "zeleznica", "delay_s": 60}]
    out = api._s_trenutno(vrstice, ZDAJ + 20)
    assert (out[0]["delay_s"], out[0]["meja_delay_s"], out[0]["zamuda"]["vrsta"]) == (
        840, 60, stats.PO_SZ)
    assert out[1] is vrstice[1] and vrstice[0]["delay_s"] == 60, "predpomnilnik ostane cel"
    assert api._s_trenutno(vrstice, ZDAJ + 120) is vrstice, "stara trenutna ne velja"


def test_straza_vidi_prikaz_ki_ne_drzi():
    """16. 10. 2026: vir je odgovarjal, zdravje zeleno, prikaz pri 611 od 1 444
    voženj z zamudo prenizek. Straža primerja ustaljeno zamudo SŽ z mejo."""
    c = _baza()
    for i in range(11):         # prvi odgovor je nepotrjen: straža ga ne šteje
        zamude_sz._odtis = str(i)
        s = zamude_sz.korak(c, [VRSTICA], ZDAJ + 15 * i)["skladnost"]
    assert (s["primerjav"], s["prenizko"], s["previsoko"]) == (2, 0, 0), "ustaljena šele po 2 min"
    # Meja zaostane za SŽ (kot ob zaskočki): straža to vidi.
    c.execute("UPDATE run SET delay_dep = 600")
    zamude_sz._odtis = "x"
    s = zamude_sz.korak(c, [VRSTICA], ZDAJ + 165)["skladnost"]
    assert (s["primerjav"], s["prenizko"], s["vlakov"]) == (3, 0, 0), "korak je vrstico spet zapisal"
    c.execute("UPDATE run SET delay_dep = 600")
    s = zamude_sz.skladnost(c, zamude_sz.razberi([VRSTICA], _vr(c), ZDAJ + 180)[0], ZDAJ + 180)
    assert (s["primerjav"], s["prenizko"], s["vlakov"]) == (4, 1, 1)
    assert s["primeri"] == ["LP 4203 (SŽ +50, prikaz +10)"]
    # Okno je pol ure.
    s = zamude_sz.skladnost(c, [], ZDAJ + 180 + zamude_sz.SKLADNOST_OKNO_S - 10)
    assert s["primerjav"] == 1


def test_straza_ne_steje_vlaka_ki_ga_sz_rise_po_voznem_redu():
    """RG 210 17. 10. 2026: Brezovica +16, nato SŽ uro +0 (vlak je stal), nato
    +36. Prikaz ničle namenoma ne vzame -- straža je dvakrat lažno zvonila."""
    c = _baza()
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts) "
              "VALUES('t1', ?, 20, 3000, ?)", (DAN, ZDAJ))
    p = [("t1", DAN, 21, 0, False)]
    zamude_sz.skladnost(c, p, ZDAJ)
    s = zamude_sz.skladnost(c, p, ZDAJ + zamude_sz.USTALJENA_S)
    assert (s["primerjav"], s["previsoko"]) == (0, 0)
    # Kjer padec pojasni rezerva (dolg postanek), je to primerjava in neskladje.
    c.execute("UPDATE sched SET arr_s = dep_s - 3600 WHERE trip_id = 't1' AND stop_seq = 21")
    s = zamude_sz.skladnost(c, p, ZDAJ + zamude_sz.USTALJENA_S + 15)
    assert (s["primerjav"], s["previsoko"]) == (1, 1)


def test_prvi_zapis_nastavi_prihod_in_odhod_naslednji_samo_odhod():
    """Zemljevid pove eno zamudo. Prvi zapis postanka (v `sz_zamuda` ga še ni)
    nastavi prihod IN odhod -- zemljevid postanek preklopi ob prihodu, torej je
    prva vrednost prihodna -- in povozi napoved derp.si; naslednji samo odhod.
    Od 1. 11. 2026 671 postankov „stal >= 10 min“ pri postanku <= 2 min, v 664
    prihod 0 (napoved derp.si)."""
    c = _baza()
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('t1', ?, 20, 0, 0, ?)", (DAN, ZDAJ - 300))
    izid = zamude_sz.zapisi(c, [("t1", DAN, 20, 3000, False)], ZDAJ)
    assert izid == {"zapisanih": 1, "nazaj": 0, "ponastavljenih": 0, "porocil": 1,
                    "preklicanih": 0}
    assert c.execute("SELECT delay_arr, delay_dep, feed_ts FROM run WHERE stop_seq = 20"
                     ).fetchone()[:] == (3000, 3000, int(ZDAJ))
    assert c.execute("SELECT delay_arr, delay_dep FROM obs").fetchone()[:] == (3000, 3000)
    zamude_sz.zapisi(c, [("t1", DAN, 20, 3120, False)], ZDAJ + 30)
    assert c.execute("SELECT delay_arr, delay_dep FROM run WHERE stop_seq = 20"
                     ).fetchone()[:] == (3000, 3120)
    assert c.execute("SELECT delay_s, v_run FROM sz_zamuda").fetchone()[:] == (3120, 1)


def test_vlak_ne_gre_nazaj_z_manjso_zamudo():
    """Zemljevid je vozni red plus trenutna zamuda: vlak, ki zamudo nabira,
    se pomika naprej, ko poteče stara zamuda, in skoči nazaj, ko SŽ zamudo
    poveča. Nazaj z isto ali manjšo zamudo je samo nihanje (RG 615 16. 10.
    2026: „naslednja Šentjur“ / „naslednja Celje“ izmenoma, oboje +3)."""
    c = _baza()
    zamude_sz.zapisi(c, [("t1", DAN, 21, 180, False)], ZDAJ)
    izid = zamude_sz.zapisi(c, [("t1", DAN, 20, 180, False)], ZDAJ + 30)
    assert izid["nazaj"] == 1
    assert c.execute("SELECT COUNT(*) FROM run WHERE stop_seq = 20").fetchone()[0] == 0
    # Popravek na istem odseku pa velja.
    assert zamude_sz.zapisi(c, [("t1", DAN, 21, 60, False)], ZDAJ + 60)["zapisanih"] == 1


def test_nazaj_z_vecjo_zamudo_je_zvisana_zamuda():
    """16. 10. 2026: LPV 2907 je SŽ ob odhodu risal po voznem redu (+0, tri
    postaje naprej), nato s +7 nazaj na izhodišču. Staro varovalo je +7
    zavračalo 10 min, prikaz je kazal točen vlak. Na 13 min zemljevida je bila
    prikazana zamuda za 3 min ali več prenizka 63-krat, s tem pravilom enkrat.
    Vrstica naprej gre iz `run`: vlak tja ni prišel (7. 11. 2026: skok nazaj
    z večjo zamudo pri 73 od 78 voženj-dni s kršitvijo)."""
    c = _baza()
    zamude_sz.zapisi(c, [("t1", DAN, 21, 0, False)], ZDAJ)
    assert zamude_sz.zapisi(c, [("t1", DAN, 20, 420, False)], ZDAJ + 30)["zapisanih"] == 1
    lm = stats.last_measured(c, DAN, ["t1"], int(ZDAJ + 30 - POLNOC))["t1"]
    assert (lm["stop_seq"], lm["delay_s"]) == (20, 420)


DAN_2401 = "2026-11-07"
P_2401 = stats.polnoc(DAN_2401)


def _lpv2401():
    """LPV 2401 Jesenice - Ljubljana 7. 11. 2026, prvih devet postankov (do Kranja)."""
    c = db.connect(":memory:")
    db.init(c)
    postaje = [("Jesenice", 4, 24, 4, 24), ("Slovenski Javornik", 4, 27, 4, 28),
               ("Žirovnica", 4, 32, 4, 33), ("Lesce-Bled", 4, 36, 4, 37),
               ("Radovljica", 4, 39, 4, 40), ("Globoko", 4, 43, 4, 44),
               ("Otoče", 4, 46, 4, 46), ("Podnart", 4, 49, 4, 50), ("Kranj", 4, 58, 4, 59)]
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46.3,14.1)",
                  [(f"s{i}", ime) for i, (ime, *_) in enumerate(postaje, 1)])
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
              "VALUES('t2401', 'r', 'LPV 2401', 's1', 'vlak', '1161', 'zeleznica')")
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                  "VALUES('t2401',?,?,?,?)",
                  [(i, f"s{i}", _ura(ah, am), _ura(dh, dm))
                   for i, (_, ah, am, dh, dm) in enumerate(postaje, 1)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s1', ?)", (DAN_2401,))
    db.fill_trip_window(c)
    c.commit()
    return c


def test_skok_nazaj_z_vecjo_zamudo_preklice_neprevozene_postanke():
    """LPV 2401 7. 11. 2026 (arwen, `obs` in `sz_zamuda`): zemljevid je vlak od
    04.36 do 04.46 risal po voznem redu (postanki 4--7, zamuda 0), ob 04.47 ga
    je s +9 vrnil na postanek 4 in nato peljal po voznem redu + 9. Prvi zapis
    postankov 5--7 je bil izmišljen, a je postal prihod 0, poznejši je popravil
    le odhod: „stal 10 min“ na postankih po minuto in ura nazaj. Po objavi
    88ec114 6. 11. je imelo tak skok 73 od 78 voženj-dni s kršitvijo.

    Postanki za skokom niso bili prevoženi: iz `run` in `sz_zamuda` gredo,
    naslednji zapis je spet prvi (prihod = odhod). Dnevnik ostane, kot je bilo,
    in vidi vsak prvi zapis, tudi kadar je enak napovedi derp.si (ob 02.54 0/0
    na vseh postankih)."""
    c = _lpv2401()
    for seq in range(1, 10):                    # napoved derp.si ponoči, samo v obs
        c.execute("INSERT INTO obs VALUES('t2401', ?, ?, 0, 0, ?, ?)",
                  (DAN_2401, seq, P_2401 + _ura(2, 53), P_2401 + _ura(2, 54)))
    zaporedje = [(1, 0, (4, 24, 19)), (2, 0, (4, 27, 16)), (3, 0, (4, 32, 16)),
                 (4, 0, (4, 36, 16)), (5, 0, (4, 39, 16)), (6, 0, (4, 43, 16)),
                 (7, 0, (4, 46, 16)), (4, 540, (4, 47, 16)), (5, 540, (4, 48, 16)),
                 (6, 540, (4, 52, 21)), (7, 540, (4, 55, 16)), (8, 540, (4, 58, 16))]
    izidi = {}
    for seq, zamuda, (h, m, s) in zaporedje:
        izidi[(seq, zamuda)] = zamude_sz.zapisi(
            c, [("t2401", DAN_2401, seq, zamuda, False)], P_2401 + _ura(h, m) + s)
        if (seq, zamuda) == (4, 540):
            # Ob skoku: 5--7 niso bili prevoženi, 4 ima prihod = odhod +9.
            assert [tuple(r) for r in c.execute(
                "SELECT stop_seq, delay_arr, delay_dep FROM run "
                "WHERE stop_seq >= 4 ORDER BY 1").fetchall()] == [(4, 540, 540)]
            assert [r[0] for r in c.execute(
                "SELECT stop_seq FROM sz_zamuda ORDER BY 1")] == [1, 2, 3, 4]
            lm = stats.last_measured(c, DAN_2401, ["t2401"],
                                     _ura(4, 47) + 30)["t2401"]
            assert (lm["stop_seq"], lm["delay_s"]) == (4, 540)
    assert izidi[(4, 540)]["preklicanih"] == 3
    assert [tuple(r) for r in c.execute(
            "SELECT stop_seq, delay_arr, delay_dep FROM run ORDER BY 1")] == [
        (1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 540, 540), (5, 540, 540), (6, 540, 540),
        (7, 540, 540), (8, 540, 540)]
    # Dnevnik: napoved derp.si, prvi zapis zemljevida (0, enak napovedi), skok.
    assert [tuple(r) for r in c.execute(
            "SELECT delay_arr, delay_dep, feed_ts - ? FROM obs WHERE stop_seq = 4 "
            "ORDER BY feed_ts", (P_2401,))] == [
        (0, 0, _ura(2, 53)), (0, 0, _ura(4, 36) + 16), (540, 540, _ura(4, 47) + 16)]
    # Izmišljeni zapisi ostanejo v dnevniku: zemljevid jih je res kazal.
    assert c.execute("SELECT COUNT(*) FROM obs WHERE stop_seq BETWEEN 5 AND 7 "
                     "AND delay_dep = 0 AND feed_ts > ?", (P_2401 + _ura(4, 0),)).fetchone()[0] == 3


def test_popravi_vlake_preklice_skoke_nazaj_po_objavi(monkeypatch):
    """Zgodovina od objave 88ec114 (6. 11. 2026 14.45) do popravka: LPV 2401
    7. 11., kot je na arwenu (`obs`, `sz_zamuda`, `run` stare kode). Prihod
    4--7 je 0 iz izmišljenega prvega zapisa, odhod +9 po skoku nazaj ob 04.47."""
    c = _lpv2401()
    for seq in range(1, 10):                    # derp.si ob 02.54, zamik 60 s
        c.execute("INSERT INTO obs VALUES('t2401', ?, ?, 0, 0, ?, ?)",
                  (DAN_2401, seq, P_2401 + _ura(2, 53), P_2401 + _ura(2, 54)))
    prvic = {1: (4, 24, 19), 2: (4, 27, 16), 3: (4, 32, 16), 4: (4, 36, 16), 5: (4, 39, 16),
             6: (4, 43, 16), 7: (4, 46, 16), 8: (4, 58, 16)}
    for seq, (h, m, s) in prvic.items():
        z = 540 if seq >= 4 else 0
        c.execute("INSERT INTO sz_zamuda VALUES('t2401', ?, ?, ?, ?, ?, 1)",
                  (DAN_2401, seq, z, P_2401 + _ura(h, m) + s, P_2401 + _ura(5, 0)))
        c.execute("INSERT INTO run VALUES('t2401', ?, ?, ?, ?, ?)",
                  (DAN_2401, seq, 540 if seq == 8 else 0, z, P_2401 + _ura(5, 0)))
    # Zapisi zemljevida v dnevniku (zamik 1 s): osvežitve 0, skok, prvi zapis 8.
    for seq, arr, dep, (h, m, s) in [
            (1, None, 0, (4, 24, 31)), (2, None, 0, (4, 27, 31)), (3, None, 0, (4, 32, 31)),
            (4, None, 0, (4, 36, 31)), (5, None, 0, (4, 39, 31)), (6, None, 0, (4, 43, 31)),
            (7, None, 0, (4, 46, 31)), (4, None, 540, (4, 47, 16)), (5, None, 540, (4, 48, 16)),
            (6, None, 540, (4, 52, 21)), (7, None, 540, (4, 55, 16)), (8, 540, 540, (4, 58, 16)),
            (8, None, 540, (4, 58, 31))]:
        ts = P_2401 + _ura(h, m) + s
        c.execute("INSERT INTO obs VALUES('t2401', ?, ?, ?, ?, ?, ?)",
                  (DAN_2401, seq, arr, dep, ts, ts + 1))
    c.commit()
    izid = zamude_sz.popravi_vlake(c, "2026-11-06")
    assert (izid["preklic_prihodov"], izid["preklic_postankov"]) == (4, 0)
    assert c.execute("SELECT COUNT(*) FROM run WHERE delay_arr = 540").fetchone()[0] == 1
    zamude_sz.popravi_vlake(c, "2026-11-06", zapisi=True)
    assert [tuple(r) for r in c.execute(
        "SELECT stop_seq, delay_arr, delay_dep FROM run ORDER BY 1")] == [
        (1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 540, 540), (5, 540, 540), (6, 540, 540),
        (7, 540, 540), (8, 540, 540)]
    assert zamude_sz.popravi_vlake(c, "2026-11-06")["preklic_prihodov"] == 0
    # Kar je nova koda zapisala sama, se ponovi enako: nič za popravit.
    c2 = _lpv2401()
    ura = [0]                                   # zemljevid: observed_at = čas branja
    monkeypatch.setattr(iz_lege.time, "time", lambda: ura[0])
    for seq, zamuda, (h, m, s) in [(4, 0, (4, 36, 16)), (5, 0, (4, 39, 16)), (6, 0, (4, 43, 16)),
                                   (4, 540, (4, 47, 16)), (5, 540, (4, 48, 16))]:
        ura[0] = P_2401 + _ura(h, m) + s
        zamude_sz.zapisi(c2, [("t2401", DAN_2401, seq, zamuda, False)], ura[0])
    izid = zamude_sz.popravi_vlake(c2, "2026-11-06")
    assert (izid["preklic_prihodov"], izid["preklic_postankov"]) == (0, 0)


def test_zastarel_odgovor_ne_spremeni_vlaka():
    """Vzorec A, B, A (1.--6. 11. 2026 na 3 190 voženj-dneh: 10 689 ničel, 202
    višjih, 6 nižjih za en odgovor). LPV 2206 6. 11.: +15 namesto +2/+3, ob
    07:57:18 in 08:07:48; po starem pravilu „nazaj z večjo zamudo velja“ in s
    poročilom v `delay_report`."""
    c = _baza()
    pravo, zastarelo = ("t1", DAN, 20, 120, False), ("t1", DAN, 20, 900, False)
    assert _odgovor(c, [pravo], ZDAJ)["nepotrjenih"] == 1       # prvo stanje vlaka čaka
    assert _odgovor(c, [pravo], ZDAJ + 15)["zapisanih"] == 1
    izid = _odgovor(c, [zastarelo], ZDAJ + 30)
    assert (izid["nepotrjenih"], izid["zapisanih"]) == (1, 0)
    assert _odgovor(c, [pravo], ZDAJ + 45)["zapisanih"] == 1    # enako zadnjemu zapisanemu
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 20").fetchone()[0] == 120
    assert c.execute("SELECT COUNT(*) FROM delay_report").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM obs WHERE delay_dep = 900").fetchone()[0] == 0
    # Prava sprememba je v dveh odgovorih zapored potrjena.
    assert _odgovor(c, [zastarelo], ZDAJ + 60)["zapisanih"] == 0
    assert _odgovor(c, [zastarelo], ZDAJ + 75)["zapisanih"] == 1
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 20").fetchone()[0] == 900
    assert c.execute("SELECT COUNT(*) FROM delay_report").fetchone()[0] == 1


def test_nicla_po_zamudi_velja_sele_potrjena():
    """16. 10. 2026: SŽ na vsake 3--4 min za en odgovor del vlakov pokaže po
    voznem redu, z zamudo 0 in postajo naprej (RG 318: +0 od Zidanega Mosta do
    Ljubljane Polje, v resnici +12 do +18). Ničla je posebnost splošnega
    pravila: stanje velja šele, ko ga potrdi naslednji spremenjen odgovor."""
    c = _baza()
    _odgovor(c, [("t1", DAN, 20, 1260, False)], ZDAJ)
    _odgovor(c, [("t1", DAN, 20, 1260, False)], ZDAJ + 5)
    izid = _odgovor(c, [("t1", DAN, 21, 0, False)], ZDAJ + 15)
    assert (izid["nepotrjenih"], izid["zapisanih"]) == (1, 0)
    # Naslednji odgovor je spet pravi: vlak ni šel naprej ne nazaj.
    izid = _odgovor(c, [("t1", DAN, 20, 1260, False)], ZDAJ + 30)
    assert (izid["nazaj"], izid["zapisanih"], izid["nepotrjenih"]) == (0, 1, 0)
    assert c.execute("SELECT MAX(stop_seq) FROM run").fetchone()[0] == 20
    # Dve ničli zapored pa sta okrevanje, ne napaka.
    _odgovor(c, [("t1", DAN, 21, 0, False)], ZDAJ + 45)
    assert _odgovor(c, [("t1", DAN, 21, 0, False)], ZDAJ + 60)["zapisanih"] == 1
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 21").fetchone()[0] == 0


def test_kandidat_ki_ga_naslednji_odgovor_ne_ponovi_odpade():
    """Vlak, ki ga naslednji spremenjen odgovor ne kaže, ne potrdi nič; A, B, C
    ne zapiše ničesar razen A."""
    c = _baza()
    a, b, k = ("t1", DAN, 20, 120, False), ("t1", DAN, 20, 900, False), ("t1", DAN, 20, 600, False)
    _odgovor(c, [a], ZDAJ)
    _odgovor(c, [a], ZDAJ + 15)
    assert _odgovor(c, [b], ZDAJ + 30)["nepotrjenih"] == 1
    assert _odgovor(c, [], ZDAJ + 45)["nepotrjenih"] == 0          # vlaka ni v odgovoru
    assert _odgovor(c, [b], ZDAJ + 60)["zapisanih"] == 0           # b ni bil v prejšnjem
    assert _odgovor(c, [k], ZDAJ + 75)["zapisanih"] == 0
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 20").fetchone()[0] == 120


def test_nepotrjena_zamuda_ne_pride_v_trenutno_zamudo():
    """Isto za vlak z odhodom v prihodnosti (trenutna zamuda): zastarel odgovor
    je ne postavi, potrjen jo."""
    c = _baza()
    _dvakrat(c, [VRSTICA], ZDAJ)
    _dvakrat(c, [POVECANA], ZDAJ + 15)
    assert zamude_sz.trenutne(DAN, ["t1"], ZDAJ + 15)["t1"]["s"] == 3900
    zamude_sz._odtis = "x"
    zastarelo = {**VRSTICA, "Odhod": "09:59", "Zamuda_cas": 123}
    s = zamude_sz.korak(c, [zastarelo], ZDAJ + 30)
    assert (s["nepotrjenih"], s["prihodnjih"]) == (1, 1)
    assert zamude_sz.trenutne(DAN, ["t1"], ZDAJ + 30)["t1"]["s"] == 3900
    zamude_sz._odtis = "y"
    zamude_sz.korak(c, [zastarelo], ZDAJ + 45)
    assert zamude_sz.trenutne(DAN, ["t1"], ZDAJ + 45)["t1"]["s"] == 7380


def test_na_cilju_velja_prvi_prihod_nicla_po_zamudi_ni_prihod():
    """SŽ vrstico na cilju po 1--2 min ponastavi na zamudo 0 (1897: +7 -> 0)."""
    c = _baza()
    zamude_sz.zapisi(c, [("t1", DAN, 21, 480, False)], ZDAJ)
    assert zamude_sz.zapisi(c, [("t1", DAN, 22, 420, True)], ZDAJ + 30)["zapisanih"] == 1
    assert zamude_sz.zapisi(c, [("t1", DAN, 22, 0, True)], ZDAJ + 150)["zapisanih"] == 0
    assert c.execute("SELECT delay_arr, delay_dep FROM run WHERE stop_seq = 22"
                     ).fetchone()[:] == (420, 420)
    # Ponastavitev, ki je prvi prihod, ki ga vidimo (zamudili smo pravega).
    zamude_sz.zapisi(c, [("t2", DAN, 21, 480, False)], ZDAJ)
    assert zamude_sz.zapisi(c, [("t2", DAN, 22, 0, True)], ZDAJ + 150)["ponastavljenih"] == 1
    # Točen prihod po točni vožnji pa je prihod.
    c2 = _baza()
    zamude_sz.zapisi(c2, [("t1", DAN, 21, 60, False)], ZDAJ)
    assert zamude_sz.zapisi(c2, [("t1", DAN, 22, 0, True)], ZDAJ + 30)["zapisanih"] == 1


def test_prezgodnji_prihod_povozi_pravi_prihod():
    """SŽ obtičali vlak nariše na cilju ob voznem redu in stari zamudi, nato ga
    spet pokaže na progi z večjo. ICS 11 17. 10. 2026: „prihod“ +15 ob 07:57,
    nato ZM +44, +75; v `run` je ostalo +15 (32 od 360 prihodov, 8,9 %)."""
    c = _baza()
    zamude_sz.zapisi(c, [("t1", DAN, 21, 900, False)], ZDAJ)
    zamude_sz.zapisi(c, [("t1", DAN, 22, 900, True)], ZDAJ + 30)        # prezgodaj
    assert zamude_sz.zapisi(c, [("t1", DAN, 21, 3600, False)], ZDAJ + 60)["zapisanih"] == 1
    assert zamude_sz.zapisi(c, [("t1", DAN, 22, 3700, True)], ZDAJ + 300)["zapisanih"] == 1
    assert c.execute("SELECT delay_arr FROM run WHERE stop_seq = 22").fetchone()[0] == 3700
    # Ponastavitev po pravem prihodu ostane ponastavitev.
    assert zamude_sz.zapisi(c, [("t1", DAN, 22, 0, True)], ZDAJ + 400)["zapisanih"] == 0
    assert c.execute("SELECT delay_arr FROM run WHERE stop_seq = 22").fetchone()[0] == 3700


def test_porocilo_o_zamudi_za_naslednjo_postajo():
    """Do 7. 10. 2026 ga je iz istega zemljevida sestavljal derp.si (`SZ-DELAY`):
    zamuda ob prihodu na naslednjo postajo, od 5 min, izjemna od 30."""
    c = _baza()
    vrstice = lambda: c.execute(  # noqa: E731
        "SELECT train_no, delay_min, station, event, severe FROM delay_report "
        "ORDER BY seen_ts").fetchall()
    zamude_sz.zapisi(c, [("t1", DAN, 20, 240, False)], ZDAJ)
    assert vrstice() == []                                  # 4 min: točen vlak poročila nima
    zamude_sz.zapisi(c, [("t1", DAN, 20, 3000, False)], ZDAJ + 15)
    zamude_sz.zapisi(c, [("t1", DAN, 20, 3000, False)], ZDAJ + 30)   # nespremenjeno
    zamude_sz.zapisi(c, [("t1", DAN, 21, 1500, False)], ZDAJ + 45)
    zamude_sz.zapisi(c, [("t1", DAN, 22, 1500, True)], ZDAJ + 60)    # prihod na cilj ne
    assert [tuple(r) for r in vrstice()] == [
        ("LP 4203", 50, "Solkan", "prihod", 1), ("LP 4203", 25, "Nova Gorica", "prihod", 0)]


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


def test_derp_pise_vlak_ki_ga_zemljevid_kaze_a_ga_ne_pripnemo():
    """derp.si (isti zemljevid prek posrednika) piše vlak, ki ga zemljevid kaže,
    a ga naš vozni red ne pripne; vlaka, ki ga zemljevid ne kaže, ne -- tega
    derp.si ne pozna bolje (31. 10. 2026: 3 od 22, nobenega z meritvijo)."""
    import time
    c = _baza()
    zdaj = time.time()
    iz_lege.sz_prebran(zdaj)
    try:
        iz_lege.sz_stevilke(set(), ["4203"], zdaj)
        izid = collector.ingest(c, _feed_zamud("t1", 240))
        assert izid["sz_prevzel"] == 0
        assert c.execute("SELECT delay_dep FROM run").fetchone()[0] == 240
        iz_lege.sz_stevilke({"4203"}, [], zdaj)           # pripet: vodi zemljevid
        assert collector.ingest(c, _feed_zamud("t1", 300))["sz_prevzel"] == 1
        assert iz_lege.sz_vodi_vlak("4203", zdaj) and iz_lege.sz_vodi_vlak("9999", zdaj)
    finally:
        iz_lege._sz_pripete.clear()
        iz_lege._sz_nepripete.clear()
        iz_lege._sz_ts = 0.0


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
    assert (s["vlakov"], s["nepotrjenih"], s["spremenjeno_ts"]) == (1, 1, int(ZDAJ))
    s = zamude_sz.korak(c, [VRSTICA], ZDAJ + 30)
    assert s["spremenjeno_ts"] == int(ZDAJ), "isti odgovor"
    # Drug odgovor, a SŽ o vlaku ne pove nič novega (polje, ki teče z uro):
    # zemljevid se ni spremenil -- zamrznjen SŽ bi se sicer skril.
    zamude_sz._odtis = "b"
    s = zamude_sz.korak(c, [{**VRSTICA, "Predviden_prihod": 6}], ZDAJ + 60)
    assert s["spremenjeno_ts"] == int(ZDAJ)
    assert json.loads(db.get_meta(c, "zamude_sz"))["ts"] == int(ZDAJ + 60)
    zamude_sz._odtis = "c"
    s = zamude_sz.korak(c, [{**VRSTICA, "Zamuda_cas": 51}], ZDAJ + 75)
    assert s["spremenjeno_ts"] == int(ZDAJ + 75)


def test_nespremenjen_odgovor_ne_premakne_casa_podatka():
    """Branje na 5 s, SŽ preračuna na 15: isti odgovor samo potrdi, da vir
    živi -- vrednosti ostanejo s časom, ko jih je SŽ prvič povedal."""
    c = _baza()
    _dvakrat(c, [VRSTICA], ZDAJ)
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


def test_zdravje_straze():
    z = {"vozi_zdaj": {"zeleznica": 20, "avtobus": 300}}

    def ocena(**sk):
        zs = {"ts": ZDAJ - 10, "vlakov": 20, "spremenjeno_ts": ZDAJ - 10,
              "skladnost": {"vlakov": 0, "prenizko": 0, "previsoko": 0, "primeri": [], **sk}}
        return zdravje.ocena({**z, "zamude_sz": zs}, {}, ZDAJ)["skladnost_sz"]

    assert ocena(primerjav=100, prenizko=50, vlakov=10)[0] == "", "premalo primerjav"
    assert ocena(primerjav=4000)[0] == zdravje.DOBRA
    assert ocena(primerjav=4000, previsoko=20, vlakov=1)[0] == zdravje.MLACNA
    # En vlak, ki je pol ure mimo, ni okvara zajema.
    assert ocena(primerjav=4000, prenizko=110, vlakov=1)[0] == zdravje.MLACNA
    r = ocena(primerjav=4000, prenizko=90, vlakov=12, primeri=["RG 318 (SŽ +18, prikaz +12)"])
    # Napaka je pri nas in jo popravi koda: oranžno (pošta podnevi po pol ure).
    assert r[0] == zdravje.ORANZNA and "RG 318" in r[1] and "2.2 %" in r[1]


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
        return {"vlakov": 3, "zapisanih": 3, "nepripetih": 0}

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


def test_prazen_zemljevid_ne_utisa_derp(tmp_path, monkeypatch):
    """Presoja 31. 10. 2026: `null` ob vlakih po voznem redu je prej veljal za
    uspešno branje in derp.si vlakov ni pisal -- nobena zamuda vlaka nikjer.
    Vodi samo zemljevid, ki ima vlak, ki ga pripnemo."""
    import threading
    pot = tmp_path / "k.sqlite"
    pravi = db.connect
    monkeypatch.setattr(db, "connect", lambda path=None: pravi(pot))
    for izid, vodi in (({"vlakov": 0, "zapisanih": 0, "nepripetih": 0}, False),
                       ({"vlakov": 4, "zapisanih": 0, "nepripetih": 4}, False),
                       ({"vlakov": 4, "zapisanih": 2, "nepripetih": 1}, True)):
        monkeypatch.setattr(iz_lege, "_sz_ts", 0.0)
        stop = threading.Event()
        monkeypatch.setattr(zamude_sz, "_get", lambda: [])

        def korak(conn, vrstice, zdaj, nespremenjeno=False, izid=izid):
            stop.set()
            return izid
        monkeypatch.setattr(zamude_sz, "korak", korak)
        zamude_sz.teci(stop, lambda _: None)
        assert iz_lege.sz_vodi() is vodi, izid


def test_zamrznjen_zemljevid_ne_vodi():
    """Zemljevid vodi vlake le, dokler kaj da: pripet vlak in jedro, ki se
    spreminja. Zamrznjen je kot molk -- derp.si spet piše (`vodi`)."""
    from kajros import zdravje
    assert zamude_sz.ZAMRZNJEN_S == zdravje.SZ_ZAMRZNJEN_S
    zdaj = 1_800_000_000
    s = {"vlakov": 20, "nepripetih": 2, "spremenjeno_ts": zdaj - 60}
    assert zamude_sz.vodi(s, zdaj)
    s["spremenjeno_ts"] = zdaj - zamude_sz.ZAMRZNJEN_S - 1
    assert not zamude_sz.vodi(s, zdaj)
    assert not zamude_sz.vodi({"vlakov": 3, "nepripetih": 3, "spremenjeno_ts": zdaj}, zdaj)
    # Ponoči en ali dva vlaka lahko dolgo stojita: to ni zamrznitev.
    assert zamude_sz.vodi({"vlakov": 2, "nepripetih": 0, "spremenjeno_ts": zdaj - 3600}, zdaj)


def _feed_z_uro(trip_id, zamuda, ts):
    f = _feed_zamud(trip_id, zamuda)
    f.header.timestamp = int(ts)
    f.entity[0].trip_update.timestamp = int(ts)
    return f


def test_zemljevid_vodi_od_zagona(monkeypatch):
    """Ob zagonu je `_sz_ts` 0 in prvi poll derp.si je zapisal VSE vlake z
    napovedjo za vse postanke (6. 11. 2026 ob 7.38 122 vlakov, LPV 2206 +15 na
    vseh 12 postankih). Zdaj zemljevid dobi `SZ_VODI_S` priložnosti."""
    c = _baza()
    monkeypatch.setattr(iz_lege.config, "SZ_ZAMUDE", True)
    assert not iz_lege.sz_vodi()
    iz_lege.sz_pricakuj()
    assert iz_lege.sz_vodi()
    izid = collector.ingest(c, _feed_zamud("t1", 240))
    assert izid["sz_prevzel"] == 1
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
    # Zemljevid v SZ_VODI_S ne odgovori: derp.si prevzame kot doslej.
    iz_lege._sz_ts -= iz_lege.SZ_VODI_S + 1
    assert collector.ingest(c, _feed_zamud("t1", 240))["sz_prevzel"] == 0
    assert c.execute("SELECT delay_dep FROM run").fetchone()[0] == 240


def test_brez_niti_zemljevida_derp_pise_kot_prej(monkeypatch):
    """Namestitev brez zemljevida (`KAJROS_SZ_ZAMUDE=0`, malina) ne čaka."""
    monkeypatch.setattr(iz_lege.config, "SZ_ZAMUDE", False)
    iz_lege.sz_pricakuj()
    assert not iz_lege.sz_vodi()
    assert collector.ingest(_baza(), _feed_zamud("t1", 240))["sz_prevzel"] == 0


def test_napoved_vlaka_gre_v_obs_ne_v_run():
    """MV 247 6. 11. 2026 ob 7.49: 0/0 na vseh 16 postankih, odhod ob 9.15. Od
    1. 11. 671 postankov „stal >= 10 min“ pri postanku <= 2 min, v 664 prihod
    natanko 0. Vrednost, ki postanek postavlja v prihodnost, je napoved: v `obs`
    (backtest operaterja), v `run` ne."""
    c = _baza()
    # Solkan (21) odhod 08:07, feed ob 07:30 pove +0: postanek je čez 37 min.
    izid = collector.ingest(c, _feed_z_uro("t1", 0, POLNOC + _ura(7, 30)))
    assert izid["napovedi_vlakov"] == 1
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
    assert c.execute("SELECT delay_dep FROM obs").fetchone()[0] == 0
    # Ista vrednost, ko je postanek mimo (ali ob njem, v minuti): meritev.
    izid = collector.ingest(c, _feed_z_uro("t1", 0, POLNOC + _ura(8, 7) - 30))
    assert izid["napovedi_vlakov"] == 0
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 21").fetchone()[0] == 0
    # Zamuda premakne postanek v prihodnost: +10 min ob 08:10 je napoved.
    izid = collector.ingest(c, _feed_z_uro("t1", 600, POLNOC + _ura(8, 10)))
    assert izid["napovedi_vlakov"] == 1
    assert c.execute("SELECT delay_dep FROM run WHERE stop_seq = 21").fetchone()[0] == 0


def test_napoved_nadomestnega_avtobusa_ostane_v_run():
    """Pravilo je za vlake: nadomestni avtobus (`mode = 'bus'`, omrežje
    zeleznica) piše derp.si kot doslej."""
    c = _baza()
    c.execute("UPDATE trip SET mode = 'bus' WHERE trip_id = 't1'")
    c.commit()
    izid = collector.ingest(c, _feed_z_uro("t1", 0, POLNOC + _ura(7, 30)))
    assert izid["napovedi_vlakov"] == 0
    assert c.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 1


def _obs(c, t, seq, arr, dep, ts, dan=DAN):
    c.execute("INSERT INTO obs(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts, "
              "observed_at) VALUES(?,?,?,?,?,?,?)", (t, dan, seq, arr, dep, ts, ts))


def _run(c, t, seq, arr, dep, dan=DAN):
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES(?,?,?,?,?,?)", (t, dan, seq, arr, dep, 1))


def test_popravi_vlake_prihod_iz_zemljevida():
    """Prihod v `run` iz napovedi derp.si dobi najzgodnejšo vrednost zemljevida
    (zapis `delay_arr IS NULL AND delay_dep IS NOT NULL`), če se razlikuje za
    >= 60 s; cilj z zapisom zemljevida dobi odhod = prihod."""
    c = _baza()
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, network) "
              "VALUES('b1', 'r', 'BUS 1', 's1', 'bus', '1161', 'zeleznica')")
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES('b1',1,'P',1,1)")
    db.fill_trip_window(c)
    # Postanek 20: derp.si napoved 0/0, zemljevid +5 in pozneje +9 -> prvi šteje.
    _obs(c, "t1", 20, 0, 0, 100)
    _obs(c, "t1", 20, None, 300, 200)
    _obs(c, "t1", 20, None, 540, 300)
    _run(c, "t1", 20, 0, 540)
    # Postanek 21: razlika 30 s, pod mejo.
    _obs(c, "t1", 21, None, 30, 200)
    _run(c, "t1", 21, 0, 30)
    # Postanek 19 nima zapisa zemljevida (derp.si piše oba).
    _obs(c, "t1", 19, 0, 600, 100)
    _run(c, "t1", 19, 0, 600)
    # Cilj: prihod z zemljevida brez odhoda.
    _obs(c, "t1", 22, 420, None, 400)
    _run(c, "t1", 22, 420, 900)
    # Nadomestni avtobus se ne dotakne.
    _obs(c, "b1", 1, None, 300, 200)
    _run(c, "b1", 1, 0, 300)
    c.commit()

    izid = zamude_sz.popravi_vlake(c, "2026-09-01")
    assert (izid["postankov"], izid["cilj_postankov"], izid["voznj"]) == (1, 1, 1)
    assert izid["dnevi"][DAN] == {"postankov": 1, "cilj_postankov": 1, "voznj": 1,
                                  "zastarelih": 0, "zastarelih_voznj": 0, "napovedi": 0,
                                  "preklic_prihodov": 0, "preklic_postankov": 0,
                                  "preklic_voznj": 0}
    assert c.execute("SELECT delay_arr FROM run WHERE trip_id = 't1' AND stop_seq = 20"
                     ).fetchone()[0] == 0, "brez --zapisi se ne spremeni nič"
    assert zamude_sz.popravi_vlake(c, "2026-09-16")["postankov"] == 0, "dnevi od --od"

    izid = zamude_sz.popravi_vlake(c, "2026-09-01", zapisi=True)
    assert izid["postankov"] == 1 and izid["zapisano"]
    vrstice = {(t, q): (a, d) for t, q, a, d in c.execute(
        "SELECT trip_id, stop_seq, delay_arr, delay_dep FROM run")}
    assert vrstice[("t1", 20)] == (300, 540)
    assert vrstice[("t1", 21)] == (0, 30)
    assert vrstice[("t1", 19)] == (0, 600)
    assert vrstice[("t1", 22)] == (420, 420)
    assert vrstice[("b1", 1)] == (0, 300)
    # Idempotentno.
    assert zamude_sz.popravi_vlake(c, "2026-09-01")["postankov"] == 0


def test_ukaz_popravi_vlake(monkeypatch, capsys):
    from kajros import cli
    c = _baza()
    monkeypatch.setattr(cli.db, "connect", lambda *a, **k: c)
    monkeypatch.setattr(cli.db, "init", lambda conn: None)
    cli.main(["popravi-vlake", "--od", "2026-09-01"])
    izpis = capsys.readouterr().out
    assert '"postankov": 0' in izpis and "samo štetje" in izpis


def test_popravi_vlake_samo_pred_mejo():
    """Po objavi (6. 11. 2026 14:45:35) zemljevid ob prvem zapisu piše OBA polja,
    zato je zapis s samim odhodom osvežitev in bi prihod pokvaril. Preskoči se
    postanek, katerega prvi zapis zemljevida je po meji; zapis po meji ne šteje
    za prvega."""
    c = _baza()
    do = zamude_sz.POPRAVI_DO_TS
    # 20: prvi zapis zemljevida po meji (pred njim samo derp.si).
    _obs(c, "t1", 20, 0, 0, 100)
    _obs(c, "t1", 20, None, 900, do + 60)
    _run(c, "t1", 20, 0, 900)
    # 21: prvi zapis pred mejo, osvežitev po meji; šteje prvi.
    _obs(c, "t1", 21, None, 300, do - 60)
    _obs(c, "t1", 21, None, 1200, do + 60)
    _run(c, "t1", 21, 0, 1200)
    # Cilj: zapis zemljevida po meji ne dokazuje nič.
    _obs(c, "t1", 22, 420, None, do + 60)
    _run(c, "t1", 22, 420, 900)
    c.commit()
    izid = zamude_sz.popravi_vlake(c, "2026-09-01", zapisi=True)
    assert (izid["postankov"], izid["cilj_postankov"]) == (1, 0)
    vrstice = {q: (a, d) for q, a, d in c.execute(
        "SELECT stop_seq, delay_arr, delay_dep FROM run WHERE trip_id = 't1'")}
    assert vrstice == {20: (0, 900), 21: (300, 1200), 22: (420, 900)}


def _baza_lpv():
    """LPV 2206 6. 11. 2026 (skrajšano): Zidani Most - Hrastnik - Trbovlje -
    Zagorje - Sava - Litija - Ljubljana, postanki brez dolgega zadrževanja."""
    c = db.connect(":memory:")
    db.init(c)
    ime = ["Zidani Most", "Hrastnik", "Trbovlje", "Zagorje", "Sava", "Litija", "Ljubljana"]
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [(f"S{i}", n, 46.0 + i / 10, 15.0) for i, n in enumerate(ime, 1)])
    for tid in ("lpv", "ok", "dolg"):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network) VALUES(?, 'r', ?, 's1', 'vlak', '1161', 'zeleznica')",
                  (tid, "LPV 2206" if tid == "lpv" else tid))
        for i in range(1, 8):
            prihod = _ura(7, 30) + 300 * i
            zadrzi = 1500 if tid == "dolg" and i == 3 else 0       # 25 min križanja
            c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)", (tid, i, f"S{i}", prihod, prihod + zadrzi))
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s1', ?)", (DAN,))
    db.fill_trip_window(c)
    c.commit()
    return c


def test_popravi_vlake_zastareli_visji_zapisi():
    """LPV 2206 6. 11. 2026: Hrastnik (postanek 2) ob 07:57:18 in Zagorje (4)
    ob 08:07:48 sta ostala z odhodom 900 iz zastarelega odgovora, prava sta
    bila 120 in 180. Zapis je „nazaj“ (pred njim je zapisan višji postanek) in
    zastarel, ker je prvi naslednji zapis na kasnejšem postanku nižji za več
    kot rezerva + 120 s."""
    c = _baza_lpv()
    ob = lambda h, m, s: int(POLNOC + _ura(h, m) + s)       # noqa: E731
    zapisi = [(ob(7, 45, 49), 2, 120), (ob(7, 50, 0), 3, 120), (ob(7, 52, 0), 4, 180),
              (ob(7, 55, 0), 5, 180), (ob(7, 57, 18), 2, 900),     # zastarel
              (ob(7, 58, 30), 5, 180), (ob(8, 3, 0), 6, 60),
              (ob(8, 7, 48), 4, 900),                              # zastarel
              (ob(8, 8, 30), 6, 60)]
    for t, q, d in zapisi:
        _obs(c, "lpv", q, None, d, t)
    for q, d in ((2, 900), (3, 120), (4, 900), (5, 180), (6, 60)):
        _run(c, "lpv", q, d, d)
    # Vlak, ki res stoji in mu SŽ dviguje zamudo: naslednji postanki >= v.
    for t, q, d in ((ob(7, 50, 0), 3, 120), (ob(7, 52, 0), 2, 600), (ob(7, 55, 0), 4, 600)):
        _obs(c, "ok", q, None, d, t)
    _run(c, "ok", 2, 600, 600)
    # Dolg postanek vmes (rezerva 1380 s): padec 900 -> 180 ga pojasni.
    for t, q, d in ((ob(7, 50, 0), 4, 120), (ob(7, 52, 0), 2, 900), (ob(7, 55, 0), 4, 180)):
        _obs(c, "dolg", q, None, d, t)
    _run(c, "dolg", 2, 900, 900)
    c.commit()

    izid = zamude_sz.popravi_vlake(c, "2026-09-01")
    assert (izid["zastarelih"], izid["zastarelih_voznj"]) == (2, 1)
    assert izid["dnevi"][DAN]["zastarelih"] == 2
    assert c.execute("SELECT delay_dep FROM run WHERE trip_id = 'lpv' AND stop_seq = 2"
                     ).fetchone()[0] == 900, "brez --zapisi se ne spremeni nič"

    zamude_sz.popravi_vlake(c, "2026-09-01", zapisi=True)
    dep = {(t, q): d for t, q, d in c.execute("SELECT trip_id, stop_seq, delay_dep FROM run")}
    assert (dep[("lpv", 2)], dep[("lpv", 4)]) == (120, 180)
    assert (dep[("lpv", 3)], dep[("lpv", 5)], dep[("lpv", 6)]) == (120, 180, 60)
    assert dep[("ok", 2)] == 600 and dep[("dolg", 2)] == 900
    # Idempotentno; run, ki je od zapisa že drugačen, se ne dotakne.
    assert zamude_sz.popravi_vlake(c, "2026-09-01")["zastarelih"] == 0


def _tri_voznje(c):
    """Kopija t1 kot t3, t4 in t5 (isti vozni red, ista postaja 20 = izhodišče)."""
    for tid in ("t3", "t4", "t5"):
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network) VALUES(?, 'r', ?, 's1', 'vlak', '1161', 'zeleznica')",
                  (tid, f"LP {tid}"))
        c.execute("INSERT INTO sched SELECT ?, stop_seq, stop_id, arr_s, dep_s "
                  "FROM sched WHERE trip_id = 't1'", (tid,))
    db.fill_trip_window(c)


def test_dosled_vlakov_ura_nazaj_in_prihod_po_odhodu():
    """1.--6. 11. 2026: ura nazaj pri 6,9 % voženj-dni, „stal >= 10 min“ pri
    25,4 %: zemljevid je pisal samo odhod, prihod je ostal napoved derp.si."""
    c = _baza()
    _tri_voznje(c)
    # t1: dosledna; na izhodišču prihod/odhod ne šteje.
    _run(c, "t1", 20, 0, 3000)
    _run(c, "t1", 21, 0, 0)
    _run(c, "t1", 22, 60, None)
    # t3: odhod s Solkana +15 min, prihod v Novo Gorico točen: 10 min nazaj.
    _run(c, "t3", 21, 900, 900)
    _run(c, "t3", 22, 0, None)
    # t4: prihod v Solkan 5 min po odhodu.
    _run(c, "t4", 21, 300, 0)
    _run(c, "t4", 22, 300, None)
    # t5: samo en izmerjen postanek -- ne šteje.
    _run(c, "t5", 21, 900, 900)
    # Nadomestni avtobus tudi ne.
    c.execute("UPDATE trip SET mode = 'bus' WHERE trip_id = 't2'")
    _run(c, "t2", 21, 900, 0)
    _run(c, "t2", 22, 0, None)
    c.commit()
    d = zamude_sz.dosled(c, DAN)
    assert (d["voznj"], d["ura_nazaj"], d["prihod_po_odhodu"], d["nedoslednih"]) == (3, 1, 1, 2)
    assert d["primeri"] == ["LP t3", "LP t4"]
    assert zamude_sz.dosled(c, "2026-09-16")["voznj"] == 0


def _dosled(voznj, nedoslednih):
    return {"dosled_vlaki": {"voznj": voznj, "nedoslednih": nedoslednih, "ura_nazaj": nedoslednih,
                              "prihod_po_odhodu": 0, "primeri": ["LPV 2206"]}}


def test_zdravje_doslednosti_vlakov():
    """Rumeno od 1 %, rdeče od 5 % ob >= 50 vožnjah; pošta po pol ure samo ob
    rdečem."""
    from tests.test_opozorila import _posta, _zdravo
    z = _zdravo()
    z["vozi_zdaj"] = {"zeleznica": 30, "avtobus": 300}

    def ocena(voznj, slabih):
        return zdravje.ocena({**z, **_dosled(voznj, slabih)}, {}, ZDAJ)["dosled_vlaki"]

    assert ocena(49, 40)[0] == "", "premalo voženj za oceno"
    assert ocena(300, 2)[0] == zdravje.DOBRA
    assert ocena(300, 3)[0] == zdravje.MLACNA
    assert ocena(300, 14)[0] == zdravje.MLACNA
    r = ocena(300, 15)
    assert r[0] == zdravje.SLABA and "LPV 2206" in r[1] and "5.0 %" in r[1]
    assert "dosled_vlaki" not in _posta({**z, **_dosled(300, 3)})
    o = _posta({**z, **_dosled(300, 15)})["dosled_vlaki"]
    assert o.po_s == 1800 and o.nujno and "popravi-vlake" in o.ukrep


def test_popravi_vlake_nepotrjena_napoved_gre_iz_run():
    """LPV 2206 6. 11. 2026: derp.si je ob zagonu ob 07:37:37 zapisal Zidani
    Most +15 (vozni red 07:35), vlak je odpeljal +2 in tega postanka nihče ni
    prepisal. Vrstica, zapisana pred voznim redom + zamudo − 2 min, gre iz
    `run`; izmerjena ostane. Pred 10. 10. (`feed_ts` derp.si) se ne dotakne."""
    c = _baza()
    dan = "2026-11-06"
    pol = int(stats.polnoc(dan))
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('t1', ?, 20, 900, 900, ?)", (dan, pol + _ura(7, 37) + 37))
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES('t1', ?, 21, 120, 120, ?)", (dan, pol + _ura(8, 9) + 30))
    _run(c, "t1", 20, 900, 900)          # DAN = 15. 9.: obdobje derp.si
    c.commit()
    izid = zamude_sz.popravi_vlake(c, "2026-09-01")
    assert izid["napovedi"] == 1
    zamude_sz.popravi_vlake(c, "2026-09-01", zapisi=True)
    ostale = {(d, q) for d, q in c.execute("SELECT service_date, stop_seq FROM run")}
    assert ostale == {(dan, 21), (DAN, 20)}


def test_tabla_na_meji_vzame_dvig_sz_z_odhodom_s_te_postaje():
    """Pregled 5. 11. 2026, točka 6: `run` +50 na Plavah, SŽ +65 z odhodom s
    Plav ob 09:01. Tabla na Plavah je kazala +50 in vrstico skrila, ko je ura
    iz `run` minila, čeprav je SŽ vlak še imel pred odhodom."""
    from kajros import journey
    c = _baza()
    _dvakrat(c, [VRSTICA], ZDAJ)

    def plave(ts):
        vrste = journey.board(c, "Plave(Železniški)", DAN, int(ts - POLNOC) - 3 * 3600,
                              window_min=360, network="zeleznica", now_s=int(ts - POLNOC))
        return next(d for d in vrste if d["trip_id"] == "t1")

    pred = plave(ZDAJ)
    assert pred["delay_s"] == 3000 and pred["delay_kind"] != stats.PO_SZ
    _dvakrat(c, [POVECANA], ZDAJ + 15)
    po = plave(ZDAJ + 15)
    assert (po["delay_s"], po["delay_kind"], po["delay_from"]) == (3900, stats.PO_SZ, None)
    # Prihodna tabla ostane: vlak je na Plave po uri že prišel.
    prih = journey.board(c, "Plave(Železniški)", DAN, int(ZDAJ + 15 - POLNOC) - 3 * 3600,
                         window_min=360, kind="prihodi", network="zeleznica",
                         now_s=int(ZDAJ + 15 - POLNOC))
    assert all(d["delay_kind"] != stats.PO_SZ for d in prih)
