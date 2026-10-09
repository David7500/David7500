"""Zamude mestnega LPP z LPP-jevih zaslonov: izbor postajališč, pripenjanje
prek derp-ovega vozila in primerjava z derp.si.

    ./venv/bin/python -m pytest tests/test_zamude_lpp.py -q
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime

import pytest

from kajros import db, iz_lege, lpp, obvestila, stats, zamude_lpp, zdravje

DAN = "2026-10-08"
POLNOC = stats.polnoc(DAN)
VZOREC = "9ad53738-9b0c-4544-bb44-4d102b2b283a"
ZDAJ = POLNOC + 16 * 3600 + 30 * 60          # 16:30


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
    """Linija 9, trije postanki, vožnje ob 16:00, 16:10 in 16:20."""
    c = db.connect(":memory:")
    db.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  [("A", "Barje", 46.03, 14.50), ("B", "Hajdrihova", 46.05, 14.49),
                   ("C", "Štepanjsko nas.", 46.04, 14.54)])
    for i, zacetek in enumerate((_ura(16, 0), _ura(16, 10), _ura(16, 20))):
        tid = f"d|v{i}|{VZOREC.upper() if i == 2 else VZOREC}"
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, agency, "
                  "network) VALUES(?, 'r9', '9', 's', 'bus', 'lpp', 'avtobus')", (tid,))
        c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
                      "VALUES(?,?,?,?,?)",
                      [(tid, 1, "A", None, zacetek), (tid, 2, "B", zacetek + 600, zacetek + 600),
                       (tid, 3, "C", zacetek + 1200, None)])
    c.execute("INSERT INTO service_day(service_id, date) VALUES('s', ?)", (DAN,))
    db.fill_trip_window(c)
    c.commit()
    return c


def _prihod(eta, vozilo="bus-7", tip=0, vzorec=VZOREC):
    return {"trip_id": vzorec.upper(), "vehicle_id": vozilo, "eta_min": eta,
            "type": tip, "depot": 0, "route_name": "9"}


def test_izbor_pokrije_vsak_vzorec_na_korak():
    """Med izbranimi ima vsak vzorec največ `korak - 1` neizbranih zapored;
    skupno postajališče dveh vzorcev pride prvo."""
    vzorci = {"x": list("abcdefgh"), "y": list("pqrsdtuv")}
    izbrane = zamude_lpp.izberi(vzorci, {"x": 10, "y": 1}, 3)
    for p in vzorci.values():
        zapored = 0
        for s in p:
            zapored = 0 if s in izbrane else zapored + 1
            assert zapored < 3
    assert "d" in izbrane
    assert zamude_lpp.izberi(vzorci, {}, 9) == set()


def test_vozilo_iz_derp_pove_vožnjo_vozni_red_sam_je_dvoumen():
    """Avtobus na Hajdrihovi čez 3 min (16:33): derp.si ga vodi kot vožnjo ob
    16:10, torej +13 min. Po voznem redu bi bili kandidatki dve (16:30 +3 in
    16:20 +13), zato ugibanja ni."""
    c = _baza()
    _, po = zamude_lpp.vozni_red(c, ("2026-10-07", DAN), 1)
    derp = {"bus-7": ("d|v1|" + VZOREC, DAN, 720)}
    po_derp, po_vr, n = zamude_lpp.pripni(_prihod(3), "B", ZDAJ, po, derp)
    assert po_derp == ("d|v1|" + VZOREC, DAN, 2, 780, False)
    assert (po_vr, n) == (None, 2)
    # Brez derp.si vozilo ni pripeto. Lega mestnega LPP dneva ne nosi.
    assert zamude_lpp.pripni(_prihod(3), "B", ZDAJ, po, {})[0] is None
    assert zamude_lpp.pripni(_prihod(3), "B", ZDAJ, po,
                             {"bus-7": ("d|v1|" + VZOREC, None, 720)})[0] == po_derp
    # Vira se ne ujemata (derp.si zadnjič +1 min, LPP +13): to ni ista vožnja.
    assert zamude_lpp.pripni(_prihod(3), "B", ZDAJ, po,
                             {"bus-7": ("d|v1|" + VZOREC, DAN, 60)})[0] is None
    # Zamude derp.si za vožnjo ni: nič, s čimer bi se ujemala.
    assert zamude_lpp.pripni(_prihod(3), "B", ZDAJ, po,
                             {"bus-7": ("d|v1|" + VZOREC, DAN, None)})[0] is None


def test_vozilo_na_novi_vožnji_ne_vzame_stare():
    """derp.si je vozilo zadnjič videl na vožnji ob 16:00; zdaj ga LPP kaže na
    Hajdrihovi čez 50 min -- to je naslednja vožnja, ne +60 min stare."""
    c = _baza()
    _, po = zamude_lpp.vozni_red(c, ("2026-10-07", DAN), 1)
    derp = {"bus-7": ("d|v0|" + VZOREC, DAN, 120)}
    assert zamude_lpp.pripni(_prihod(80), "B", ZDAJ, po, derp)[0] is None


def test_razberi_zive_pripne_ostale_presteje():
    c = _baza()
    _, po = zamude_lpp.vozni_red(c, ("2026-10-07", DAN), 1)
    derp = {"bus-7": ("d|v1|" + VZOREC, DAN, 780), "bus-8": ("d|v2|" + VZOREC.upper(), DAN, 700)}
    odgovori = [("600101", ZDAJ, [
        _prihod(3),                                  # v1 po derp, vozni red dvoumen
        _prihod(12, vozilo="bus-8"),                 # v2 po derp, po voznem redu edina
        _prihod(9, vozilo="bus-9", tip=1),           # po voznem redu: ni meritev
        _prihod(4, vozilo="bus-x", vzorec="neznan-vzorec"),
    ])]
    pripete, st = zamude_lpp.razberi(odgovori, {"600101": "B"}, po, derp)
    assert sorted(p[:4] for p in pripete) == [
        ("d|v1|" + VZOREC, DAN, 2, 780), ("d|v2|" + VZOREC.upper(), DAN, 2, 720)]
    assert st == {"prihodov": 4, "zivih": 3, "pripetih": 2, "brez_voznega_reda": 1,
                  "po_voznem_redu": [1, 0, 1, 0]}


def test_brez_derp_gre_v_run_z_derp_samo_v_primerjavo():
    """Kot pri zemljevidu SŽ: vožnja, ki je derp.si ne nosi, gre v `run`;
    ki jo nosi, ostane derp-ova in se primerja."""
    c = _baza()
    v1, v2 = "d|v1|" + VZOREC, "d|v2|" + VZOREC.upper()
    iz_lege.zabelezi_feed([], zdaj=ZDAJ - 1000)      # feed prebran, vožnje ni
    izid = zamude_lpp.zapisi(c, [(v1, DAN, 2, 780, False), (v1, DAN, 3, 840, True)], ZDAJ)
    assert izid == {"samo_lpp": 2, "oba": 0}
    assert [tuple(r) for r in c.execute(
        "SELECT delay_arr, delay_dep FROM run WHERE trip_id=? ORDER BY stop_seq", (v1,))
    ] == [(None, 780), (840, None)]
    assert zamude_lpp.primerjava(c, ZDAJ - 60)["parov"] == 0, "vir se ne primerja sam s sabo"

    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES(?, ?, 2, NULL, 840, ?)", (v2, DAN, ZDAJ))
    iz_lege.zabelezi_feed([v2], zdaj=ZDAJ)
    assert zamude_lpp.zapisi(c, [(v2, DAN, 2, 900, False)], ZDAJ) == {"samo_lpp": 0, "oba": 1}
    assert c.execute("SELECT delay_dep FROM run WHERE trip_id=? AND stop_seq=2",
                     (v2,)).fetchone()[0] == 840, "derp-ova vrednost ostane"
    p = zamude_lpp.primerjava(c, ZDAJ - 60, najvec=3)
    assert (p["parov"], p["v_minuti"], p["mediana_s"], p["samo_lpp"]) == (1, 1, 60, 2)


def test_korak_zapise_pregled(monkeypatch):
    c = _baza()
    v1 = "d|v1|" + VZOREC
    c.execute("INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, vehicle_id) "
              "VALUES(?, NULL, ?, 46.05, 14.49, 'BUS-7')", (v1, ZDAJ - 1200))
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts) "
              "VALUES(?, ?, 1, NULL, 700, ?)", (v1, DAN, ZDAJ - 1200))
    monkeypatch.setattr(zamude_lpp.config, "LPP_POSTAJ_KORAK", 1)
    iz_lege.zabelezi_feed([], zdaj=ZDAJ - 1000)
    s = zamude_lpp.korak(c, [("600101", ZDAJ, [_prihod(3)])], {"600101": "B"}, ZDAJ, napak=2)
    assert (s["pripetih"], s["samo_lpp"], s["napak_zahtev"], s["postaj"]) == (1, 1, 2, 1)
    assert json.loads(db.get_meta(c, "zamude_lpp"))["ts"] == int(ZDAJ)


def test_obhod_ob_izpadu_vira_vrze_napako(monkeypatch):
    """Polovica postajališč brez odgovora je izpad, ne prazen promet."""
    class Seja:
        headers: dict = {}

        def get(self, url, params, timeout):
            raise zamude_lpp.requests.ConnectionError("x")

    monkeypatch.setattr(zamude_lpp.requests, "Session", Seja)
    with pytest.raises(RuntimeError):
        zamude_lpp._obhod({"1": "A", "2": "B"})


def test_nit_ponoci_ne_bere(monkeypatch, tmp_path):
    """Ponoči vozita 0-2 avtobusa: obhod postajališč bi bil zaman."""
    pot = tmp_path / "k.sqlite"
    c = db.connect(pot)
    db.init(c)
    c.close()
    pravi = db.connect
    monkeypatch.setattr(db, "connect", lambda path=None: pravi(pot))
    monkeypatch.setattr(iz_lege, "feed_prebran", lambda: True)
    monkeypatch.setattr(zamude_lpp.stats, "vozi_zdaj", lambda c, t: {"avtobus": 1})
    klici = []
    monkeypatch.setattr(zamude_lpp, "_obhod", lambda kode: klici.append(1) or ([], 0))
    stop = threading.Event()
    monkeypatch.setattr(zamude_lpp.config, "LPP_ZAMUDE_SECONDS", 0)
    nit = threading.Thread(target=zamude_lpp.teci, args=(stop, lambda _: None))
    nit.start()
    time.sleep(0.2)
    stop.set()
    nit.join(5)
    assert not klici


def test_tabla_ob_molku_derp_vzame_vse_linije(monkeypatch):
    """8. 10. 2026: derp.si mrtev, LPP-jev zaslon živ -- tabla za vse linije
    LPP kaže LPP-jeve prihode, ne voznega reda brez zamud."""
    c = _baza()
    zdaj = datetime.fromtimestamp(ZDAJ, stats.TZ)
    assert not lpp.derp_molci(c, ZDAJ), "brez zapisa ne vemo nič"
    db.set_meta(c, "lpp_rt_fetched", str(int(ZDAJ) - 60))
    assert not lpp.derp_molci(c, ZDAJ)
    db.set_meta(c, "lpp_rt_fetched", str(int(ZDAJ) - lpp.DERP_MOLCI_S - 1))
    assert lpp.derp_molci(c, ZDAJ)

    monkeypatch.setattr(lpp, "_postaje_lpp", lambda: [
        {"ref_id": "600101", "latitude": 46.05, "longitude": 14.49}])
    monkeypatch.setattr(lpp, "_prihodi_postaje", lambda koda: [
        {"route_name": "9", "eta_min": 3, "type": 0, "depot": 0,
         "trip_name": "BARJE P+R - ŠTEPANJSKO NASELJE",
         "stations": {"departure": "BARJE P+R", "arrival": "ŠTEPANJSKO NAS."}}])
    rows = [{"trip_id": "d|v2|x", "train_no": "9", "agency": "lpp", "stop_id": "B",
             "service_date": DAN, "t_s": _ura(16, 30)}]
    assert lpp.na_tablo(c, list(rows), zdaj, True, "Hajdrihova") == (rows, [])
    nove, mimo = lpp.na_tablo(c, list(rows), zdaj, True, "Hajdrihova", vse=True)
    assert mimo == ["9"] and [r.get("lpp_vrsta") for r in nove] == ["napoved"]


def test_zdravje_derp_in_lpp():
    """derp.si po viru: rdeče, kadar ne odgovarja, četudi `run` pišejo drugi
    viri. Nit LPP: rumeno ob napaki vira, rdeče, kadar stoji."""
    z = {"vozi_zdaj": {"zeleznica": 10, "avtobus": 300},
         "derp_prebran": {"ijpp": ZDAJ - 30, "lpp": ZDAJ - 30},
         "zamude_lpp": {"ts": ZDAJ - 100, "oba": 40, "samo_lpp": 0}}
    o = zdravje.ocena(z, {}, ZDAJ)
    assert o["derp_ijpp"][0] == o["derp_lpp"][0] == zdravje.DOBRA
    assert o["zamude_lpp"][0] == zdravje.DOBRA
    z["derp_prebran"]["ijpp"] = ZDAJ - 3600
    o = zdravje.ocena(z, {}, ZDAJ)
    assert o["derp_ijpp"] == (zdravje.SLABA, "derp.si (IJPP) ne odgovarja od pred 60 min")
    assert o["derp_lpp"][0] == zdravje.DOBRA, "vsak vir svoja vrstica"
    z["zamude_lpp"] = {"ts": ZDAJ - 3600, "napaka_ts": ZDAJ - 60}
    assert zdravje.ocena(z, {}, ZDAJ)["zamude_lpp"][0] == zdravje.MLACNA
    z["zamude_lpp"] = {"ts": ZDAJ - 3600, "napaka_ts": ZDAJ - 3600}
    assert zdravje.ocena(z, {}, ZDAJ)["zamude_lpp"][0] == zdravje.SLABA
    z["vozi_zdaj"]["avtobus"] = 1                    # noč
    o = zdravje.ocena(z, {}, ZDAJ)
    assert "derp_ijpp" not in o and o["zamude_lpp"] == ("", "")


def test_vozi_zdaj_loci_mestni_lpp():
    c = _baza()
    vozi = stats.vozi_zdaj(c, ZDAJ, vsaj_s=0, lpp_posebej=True)
    # Ob 16:30 vozita vožnji ob 16:10 in 16:20; tista ob 16:00 je končala.
    assert (vozi["avtobus"], vozi["lpp"]) == (0, 2)
    assert stats.vozi_zdaj(c, ZDAJ, vsaj_s=0)["avtobus"] == 2
    assert obvestila.VSAJ == zdravje.MIN_VOZENJ
