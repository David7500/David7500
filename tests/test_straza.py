"""Straža po prevoznikih (`straza.py`): ista merila za vse, brez pogoja po prevozniku.

    ./venv/bin/python -m pytest tests/test_straza.py -q
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from kajros import db, stats, straza

D = "2026-10-29"


@pytest.fixture(autouse=True)
def _prazen_medpomnilnik():
    """Drugi testi (zajem) kličejo `straza.vzorec`: medpomnilnik je globalen."""
    straza._vzorci.clear()
    straza._izpraznjeno[0] = 0.0
    yield
    straza._vzorci.clear()


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    c.execute("INSERT INTO service_day(service_id, date) VALUES('S1', ?)", (D,))
    for i, (lat, lon) in enumerate([(46.0, 14.0), (46.0, 14.01), (46.0, 14.02)]):
        c.execute("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
                  (f"P{i}", f"Postaja {i}", lat, lon))
    return c


def _vozni(c, trip_id, agency, shape_id=None, service="S1", postankov=3):
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network, agency, "
              "shape_id, first_seq, last_seq) VALUES(?, 'r', ?, ?, 'bus', 'avtobus', ?, ?, 1, ?)",
              (trip_id, trip_id, service, agency, shape_id, postankov))
    for seq in range(1, postankov + 1):
        c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                  (trip_id, seq, f"P{seq - 1}", 8 * 3600 + 600 * seq, 8 * 3600 + 600 * seq))


def _lega(c, trip_id, dan=D):
    c.execute("INSERT INTO lega(service_date, trip_id, ts, lat, lon, vozilo) VALUES(?,?,?,46,14,'V')",
              (dan, trip_id, 1))


def test_merila_so_ista_za_vse_prevoznike(conn):
    """A ima lego pri 2 od 4 voženj, B pri 1 od 1: delež se računa po prevozniku
    iz `trip.agency`, brez posebne veje."""
    for t in ("a1", "a2", "a3", "a4"):
        _vozni(conn, t, "A")
    _vozni(conn, "b1", "B")
    _lega(conn, "a1")
    _lega(conn, "a2")
    _lega(conn, "b1")
    conn.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_dep, feed_ts) "
                 "VALUES('a1', ?, 1, 60, 1)", (D,))
    for seq in (1, 2):
        conn.execute("INSERT INTO gps_prehod VALUES(?, 'a1', ?, 0, 1, 0, 0, 1)", (D, seq))
    m = straza.merila_dneva(conn, D)
    assert (m["A"]["nacrt"], m["A"]["z_lego"], m["A"]["z_meritvijo"]) == (4, 2, 1)
    assert (m["B"]["nacrt"], m["B"]["z_lego"], m["B"]["z_meritvijo"]) == (1, 1, 0)
    # postanki voženj z lego ali meritvijo: a1 + a2
    assert (m["A"]["postankov"], m["A"]["s_prehodom"]) == (6, 2)


def test_nagrobnik_ni_v_nacrtu(conn):
    """Vožnja brez `sched` (nov zip je nima, meritve jo držijo v bazi) z
    `service_id`, ki ga nov zip rabi za ta dan, ni načrtovana vožnja."""
    _vozni(conn, "a1", "A")
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network, "
                 "agency) VALUES('a0', 'r', 'a0', 'S1', 'bus', 'avtobus', 'A')")
    assert straza.merila_dneva(conn, D)["A"]["nacrt"] == 1
    assert straza.vozni_red(conn, date.fromisoformat(D))["A"]["delavnik"]["voznje"] == 1


def test_brez_leg_je_neznano_ne_nic(conn):
    """Za nazaj vir leg ni hranil: 0 % bi bilo poslabšanje, ki ga ni."""
    _vozni(conn, "a1", "A")
    m = straza.merila_dneva(conn, D)
    assert m["A"]["z_lego"] is None
    assert straza.primerjaj({"A": {"nacrt": 1, "z_lego": 1}}, {"A": m["A"]}) == []


def test_opazena_vozila_z_voznjo_in_brez(conn):
    _vozni(conn, "a1", "A")
    t0 = 1_793_000_000                      # 26. 10. 2026
    dan = straza._dan(t0)
    straza.vzorec("nap", "V1", "a1", t0)
    straza.vzorec("nap", "V1", "a1", t0 + 10)
    straza.vzorec("nap", "V2", None, t0)
    straza.vzorec("nap", None, "a1", t0)    # brez id-ja vozila ni kaj šteti
    assert straza.izprazni(conn, t0 + 1000) == 2
    assert straza.izprazni(conn, t0 + 1001) == 0        # medpomnilnik je prazen
    vrstice = conn.execute("SELECT vozilo, trip_id, vzorcev FROM straza_opazeno "
                           "ORDER BY vozilo").fetchall()
    assert [tuple(r) for r in vrstice] == [("V1", "a1", 2), ("V2", "", 1)]
    # Vožnja pove prevoznika, vozilo brez nje šteje pod vir.
    conn.execute("UPDATE straza_opazeno SET dan = ?", (D,))
    v = straza._vozila(conn, D, {"a1": "A"})
    assert v["A"]["nap"] == {"z": 1, "brez": 0, "vzorcev_z": 2, "vzorcev_brez": 0}
    assert v["nap"]["nap"]["brez"] == 1
    assert dan == "2026-10-26"


def test_izpraznjevanje_je_poredko(conn):
    straza._izpraznjeno[0] = 0.0
    straza.vzorec("derp", "V1", None, 1_793_000_000)
    assert straza.izprazni(conn, 1_793_000_000, vsakih_s=300) == 1
    straza.vzorec("derp", "V1", None, 1_793_000_100)
    assert straza.izprazni(conn, 1_793_000_100, vsakih_s=300) == 0
    assert straza.izprazni(conn, 1_793_000_400, vsakih_s=300) == 1
    assert conn.execute("SELECT vzorcev FROM straza_opazeno").fetchone()[0] == 2


def _rep(c, trip_id, d_konec, dan=D):
    """Dnevnik na končni: zamuda je ura (voznored + zamuda = feed_ts), raste
    od 60 s do `d_konec`."""
    polnoc = stats.polnoc(dan)
    t_s = 8 * 3600 + 1800                   # prihod na 3. postanek
    for i, d in enumerate(range(60, d_konec + 1, 60)):
        c.execute("INSERT INTO obs(trip_id, service_date, stop_seq, delay_arr, delay_dep, "
                  "feed_ts, observed_at) VALUES(?,?,3,?,NULL,?,?)",
                  (trip_id, dan, d, polnoc + t_s + d, i))
    c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, feed_ts) "
              "VALUES(?,?,3,?,1)", (trip_id, dan, d_konec))


def test_rep_na_koncni_je_isto_merilo_za_vse(conn):
    _vozni(conn, "a1", "A")
    _vozni(conn, "a2", "A")
    _vozni(conn, "b1", "B")
    _rep(conn, "a1", 600)                   # raste z uro 9 min: rep
    _rep(conn, "b1", 600)
    polnoc = stats.polnoc(D)
    # a2: zamuda na končni stalna in ne sovpada z uro: poštena meritev
    for i, ts in enumerate((100, 200)):
        conn.execute("INSERT INTO obs VALUES('a2', ?, 3, 300, NULL, ?, ?)", (D, polnoc + ts, i))
    conn.execute("INSERT INTO run VALUES('a2', ?, 3, 300, NULL, 1)", (D,))
    r = straza._rep_na_koncni(conn, D, {"a1": "A", "a2": "A", "b1": "B"})
    assert r["A"] == {"voznje": 2, "nad": 1}
    assert r["B"] == {"voznje": 1, "nad": 1}


def test_vozni_red_po_vrsti_dne_pokaze_manjkajoce_delavnike(conn):
    """Marprom 30. 10. 2026: sobote in nedelje do 20. 6. 2027, delavniki do
    31. 12. 2026. `do` čez vse dni bi pokazal le prvo."""
    for d in ("2026-10-30", "2026-12-31", "2027-06-19", "2027-06-20"):
        conn.execute("INSERT INTO service_day(service_id, date) VALUES('M', ?)", (d,))
    # Teden delavnikov ne zaobjame po dnevih, zato samo še en delavnik vmes:
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('M', '2026-12-30')")
    _vozni(conn, "m1", "marprom", service="M")
    _vozni(conn, "m2", "marprom", service="M")
    v = straza.vozni_red(conn, date(2026, 10, 30))["marprom"]
    assert v["delavnik"]["do"] == "2026-12-31"
    assert v["delavnik"]["prvi_brez"] == "2026-11-02"        # prvi delavnik brez voženj
    assert v["sobota"]["do"] == "2027-06-19"
    assert v["nedelja"]["do"] == "2027-06-20"
    assert v["do"] == "2027-06-20"
    assert v["delavnik"]["voznje"] == 2


def test_vozni_red_vsak_prevoznik_svoj(conn):
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S2', '2026-11-02')")
    _vozni(conn, "a1", "A")
    _vozni(conn, "b1", "B", service="S2")
    v = straza.vozni_red(conn, date(2026, 10, 29))
    assert v["A"]["delavnik"]["do"] == "2026-10-29"
    assert v["B"]["delavnik"]["do"] == "2026-11-02"
    assert v["B"]["sobota"]["do"] is None


def _oblika(c, shape_id, kosi):
    c.execute("INSERT INTO shape(shape_id, points) VALUES(?, ?)", (shape_id, json.dumps(kosi)))


def test_trase_beremo_kot_kose(conn):
    """`shape.points` je seznam kosov `[[[lat,lon],...]]` (vseh 3 505 tras
    na arwenu); seznam točk bi tu padel pri `tuple(p)`."""
    ok = [[[46.0, 14.0], [46.0, 14.01]], [[46.0, 14.01], [46.0, 14.02]]]
    krozna = [[[46.0, 14.0], [46.0, 14.0]]]
    stran = [[[46.1, 14.0], [46.1, 14.02]]]         # 11 km severno od postankov
    for i, kosi in enumerate((ok, krozna, stran)):
        _oblika(conn, f"s{i}", kosi)
        _vozni(conn, f"a{i}", "A", shape_id=f"s{i}")
    _vozni(conn, "a9", "A")                         # vožnja brez trase
    t = straza.trase(conn, date(2026, 10, 29))["A"]
    assert (t["tras"], t["premalo_tock"], t["dalec_od_postaje"]) == (3, 1, 1)
    assert t["voznje_brez_trase"] == 1
    s2 = next(p for p in t["primeri"] if p["shape_id"] == "s2")
    assert s2["postankov"] == 3 and 10_000 < s2["m"] < 12_000


def test_odmik_ne_skoci_cez_vrzel_med_kosoma():
    kosi = [[[46.0, 14.0], [46.0, 14.001]], [[46.0, 14.05], [46.0, 14.051]]]
    # Postanek na sredi vrzeli: do obeh kosov > 1 km, daljica med njima ne šteje.
    dalec, naj = straza._odmik_od_trase(kosi, [(46.0, 14.025)])
    assert dalec == 1 and naj > 1500


def test_vsak_prevoznik_ima_vrstico_in_se_ponovi(conn):
    """`dopolni` izračuna dan, ponovitev ga prepiše, ne podvoji."""
    conn.execute("INSERT INTO service_day(service_id, date) VALUES('S1', '2026-10-30')")
    _vozni(conn, "a1", "A")
    _vozni(conn, "b1", "B")
    _lega(conn, "a1")
    _lega(conn, "b1", "2026-10-28")
    dnevi = straza.dopolni(conn, date(2026, 10, 30))
    assert dnevi == [D]                     # prvi dan `lega` je lahko obrezan
    assert straza.dopolni(conn, date(2026, 10, 30)) == [D]   # zadnje dni prepiše
    vrstice = conn.execute("SELECT prevoznik FROM straza_dan WHERE dan = ? ORDER BY 1",
                           (D,)).fetchall()
    assert [r[0] for r in vrstice] == ["A", "B"]
    dan, b = straza.beri(conn)
    assert dan == D and b["A"]["nacrt"] == 1
    assert b["A"]["vozni_red"]["delavnik"]["do"] == "2026-10-30"


def test_beri_brez_tabel_deluje_na_kopiji_samo_za_branje(conn, tmp_path):
    """`kajros straza --baza` na arwenu: tabel straže tam še ni."""
    import sqlite3
    pot = tmp_path / "k.sqlite"
    c = sqlite3.connect(pot)
    c.executescript("".join(r[0] + ";" for r in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'straza%' "
        "AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL")))
    c.execute("INSERT INTO service_day VALUES('S1', ?)", (D,))
    c.execute("INSERT INTO trip(trip_id, route_id, train_no, service_id, mode, network, agency) "
              "VALUES('a1','r','a1','S1','bus','avtobus','A')")
    c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) "
              "VALUES('a1', 1, 'P0', 28800, 28800)")
    c.commit()
    c.close()
    ro = sqlite3.connect(f"file:{pot}?mode=ro", uri=True)
    dan, b = straza.beri(ro, D)
    assert dan == D and b["A"]["nacrt"] == 1 and b["A"]["z_lego"] is None
    assert "A" in straza.izpis(dan, b)


def test_stevec_po_prevozniku_vozni(conn):
    _vozni(conn, "a1", "A")
    straza.stevec(conn, D, "a1", "ure_na_koncni")
    straza.stevec(conn, D, "a1", "ure_na_koncni")
    straza.stevec(conn, D, "ni_je", "ure_na_koncni")        # vožnje ni: nič ne zapiše
    assert [tuple(r) for r in conn.execute(
        "SELECT prevoznik, ime, n FROM straza_stevec")] == [("A", "ure_na_koncni", 2)]


def test_primerjava_pokaze_koga_poslabsa():
    a = {"A": {"nacrt": 100, "z_lego": 90, "rep_voznje": 100, "rep_nad": 1,
               "vozni_red": {"delavnik": {"do": "2026-12-31"}}},
         "B": {"nacrt": 100, "z_lego": 80}}
    b = {"A": {"nacrt": 100, "z_lego": 95, "rep_voznje": 100, "rep_nad": 5,
               "vozni_red": {"delavnik": {"do": "2026-12-31"}}},
         "B": {"nacrt": 100, "z_lego": 70}}
    r = straza.primerjaj(a, b)
    slabse = {(x["prevoznik"], x["merilo"]) for x in r if x["slabse"]}
    assert slabse == {("A", "% repov na končni"), ("B", "% voženj z lego")}
    assert ("A", "% voženj z lego") in {(x["prevoznik"], x["merilo"]) for x in r if not x["slabse"]}
    assert "poslabšano: A, B" in straza.izpis_primerjave("pred", "po", r)


def test_krajsi_vozni_red_je_poslabsanje():
    a = {"M": {"vozni_red": {"delavnik": {"do": "2026-12-31"}, "sobota": {"do": "2027-06-19"}}}}
    b = {"M": {"vozni_red": {"delavnik": {"do": "2026-10-31"}, "sobota": {"do": "2027-06-19"}}}}
    r = straza.primerjaj(a, b)
    assert [(x["merilo"], x["slabse"]) for x in r] == [("delavnik do", True)]
