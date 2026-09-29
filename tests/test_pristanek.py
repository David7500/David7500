"""Pristajalne strani: naslovi, števila in izbor relacij.

Zakaj je to vredno testa: te strani so edini del aplikacije, ki ga bere
**iskalnik**, in njegove napake se ne vidijo. Naslov, ki se zlomi na šumniku,
ali relacija, ki pride na seznam, ker sta postajališči na isti ulici, se na
zaslonu ne poznata -- poznata se tri mesece pozneje v obisku.

    ./venv/bin/python -m pytest tests/test_pristanek.py -q
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from kajros import db, pristanek, stats


# ---------------------------------------------------------------- naslovi

def test_naslov_zlozi_sumnike_in_presledke():
    assert pristanek.slug("Ljubljana Železna") == "ljubljana-zelezna"
    assert pristanek.slug("Šentjur") == "sentjur"
    assert pristanek.slug("Polje (Tolmin)") == "polje-tolmin"


def test_naslov_nima_ne_vodilnih_ne_zaporednih_crtic():
    """„Ljubljana - AP" in „Ljubljana AP" morata dati isti naslov, sicer sta
    isti vsebini dva naslova in iskalnik ju šteje za podvojeno stran."""
    assert pristanek.slug("Ljubljana - AP") == "ljubljana-ap"
    assert pristanek.slug("  Vič / Glince  ") == "vic-glince"


def test_pot_nosi_omrezje():
    assert pristanek.pot_relacije("zeleznica", "Celje", "Maribor") == "/vlak/celje/maribor"
    assert pristanek.pot_relacije("avtobus", "Celje", "Maribor") == "/avtobus/celje/maribor"
    assert pristanek.pot_postaje("zeleznica", "Celje") == "/postaja/celje"
    assert pristanek.pot_postaje("avtobus", "Bavarski dvor") == "/postajalisce/bavarski-dvor"


def test_pot_vozje_zakodira_navpicnice_lpp():
    """`trip_id` mestnega LPP nosi navpičnice; v naslovu morajo biti zakodirane,
    sicer se povezava na eno vožnjo razlomi."""
    assert pristanek.pot_vozje("avtobus", "3G", "a|b") == "/app/bus/3G?trip=a%7Cb"


# ---------------------------------------------------------------- besede ob številih

@pytest.mark.parametrize("n, pricakovano", [
    (1, "vožnja"), (2, "vožnji"), (3, "vožnje"), (4, "vožnje"),
    (5, "voženj"), (11, "voženj"), (39, "voženj"),
    # 21 je „enaindvajset" -- ena beseda, ki se konča na -dvajset, zato
    # rodilnik. Pri 101 pa je „ena" samostojna beseda: „sto ena vožnja".
    (21, "voženj"), (101, "vožnja"), (102, "vožnji"),
])
def test_stevnik_sklanja_po_zadnjih_dveh_stevkah(n, pricakovano):
    assert pristanek.stevnik(n, "vožnja", "vožnji", "vožnje", "voženj") == pricakovano


def test_prezgodnja_voznja_dobi_besedo_in_ne_minusa():
    """Pravilo iz `.claude/rules/oznake.md`: minus pred številko je uganka."""
    assert pristanek.besedilo(stats.opis_zamude(-180)) == "3 min prej"
    assert pristanek.besedilo(stats.opis_zamude(0)) == "0 min"
    assert pristanek.besedilo(stats.opis_zamude(300)) == "+5 min"
    assert pristanek.besedilo(None) == "ni podatka"


def test_trajanje_ure_izpise_sele_ko_so():
    assert pristanek.trajanje(2880) == "48 min"
    assert pristanek.trajanje(3630) == "1 h 0 min"
    assert pristanek.trajanje(None) == ""


def test_razdalja_in_tisocice_so_slovenske():
    assert pristanek.km(17.6) == "17,6 km"
    assert pristanek.stevilo(1671) == "1 671"


# ---------------------------------------------------------------- kvantil

def test_kvantil_iz_histograma_je_isti_kot_iz_seznama():
    """Dve definiciji kvantila bi pomenili, da „p90 20 min" na lestvici in
    „p90 20 min" na relaciji nista primerljiva -- in bralec tega ne more vedeti.
    """
    vrednosti = [0, 0, 1, 1, 1, 3, 5, 5, 12, 40]
    hist: dict[int, int] = {}
    for v in vrednosti:
        hist[v] = hist.get(v, 0) + 1
    minute = sorted(hist)
    for q in (0.5, 0.9):
        assert (pristanek._kvantil(minute, hist, len(vrednosti), q)
                == stats._pct(vrednosti, q))


# ---------------------------------------------------------------- izbor relacij

def _vcerajsnji() -> str:
    """Meritve gredo na včerajšnji dan: trd datum bi test čez tri mesece podrl,
    ker `zgradi()` gleda samo zadnjih 90 dni."""
    return (date.today() - timedelta(days=1)).isoformat()


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init(c)
    # Dve daljni postaji in eno tik ob izhodišču: zadnja preverja mejo razdalje.
    c.executemany(
        "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
        [("A", "Ajdovščina", 45.887, 13.905),
         ("C", "Celje", 46.229, 15.266),
         ("S", "Sosednja", 45.889, 13.907)])
    dan = _vcerajsnji()
    c.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S1', ?)", (dan,))
    for i in range(6):
        tid = f"t{i}"
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                  "                 network, agency) "
                  "VALUES(?,?,?,?, 'S1', 'zeleznica', '1161')",
                  (tid, f"r{i}", f"IC {i}", "A - C"))
        c.executemany(
            "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
            [(tid, 1, "A", None, 28800), (tid, 2, "S", 28900, 29000),
             (tid, 3, "C", 36000, None)])
        # Zamuda ob prihodu v Celje: pet minut pri vsaki vožnji razen ene.
        c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr,"
                  "                delay_dep, feed_ts) VALUES(?,?,3,?,?,4102444800)",
                  (tid, dan, 300, 300))
    db.fill_trip_window(c)
    c.commit()
    return c


def test_relacija_pod_mejo_razdalje_ne_dobi_strani(conn):
    """Postajališči iste ulice nista relacija -- glej `MIN_RAZDALJA_M`."""
    got = pristanek.zgradi(conn, 90, "zeleznica")
    pari = {(r["od"], r["cilj"]) for r in got["relacije"]}
    assert ("Ajdovščina", "Celje") in pari
    assert ("Ajdovščina", "Sosednja") not in pari


def test_relacija_nosi_izmerjeno_zamudo_in_vzorec(conn):
    got = pristanek.zgradi(conn, 90, "zeleznica")
    rel = next(r for r in got["relacije"]
               if (r["od"], r["cilj"]) == ("Ajdovščina", "Celje"))
    assert rel["meritev"] == 6
    assert rel["median_min"] == 5.0
    assert rel["zamuda"]["razred"] == "1-5"
    # Vozni red: 08:00 -> 10:00.
    assert rel["trajanje_s"] == 7200


def test_kazalo_najde_postajo_samo_po_tocnem_naslovu(conn):
    """`/postaja/karkoli` ne sme postreči najbližje postaje: iskalniku bi to
    odprlo neskončen prostor naslovov, obiskovalcu pa napačen odgovor."""
    stats.summary_build(conn, "pristanek", "zeleznica", 90)
    kaz = pristanek.kazalo(conn, "zeleznica")
    assert pristanek.ime_postaje(conn, kaz, "ajdovscina", "zeleznica") == "Ajdovščina"
    assert pristanek.ime_postaje(conn, kaz, "ajdov", "zeleznica") is None


def _voznje(c, predpona: str, n: int, postaje: list[str], network="zeleznica",
            agency="1161") -> None:
    for i in range(n):
        tid = f"{predpona}{i}"
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign,"
                  "  service_id, network, agency) VALUES(?,?,?,?, 'S1', ?, ?)",
                  (tid, f"r{tid}", f"LP {tid}", "x", network, agency))
        c.executemany(
            "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
            [(tid, k + 1, s, 28800 + 600 * k, 28800 + 600 * k)
             for k, s in enumerate(postaje)])


def test_velika_kraja_pred_pogosto_primestno_relacijo(conn, monkeypatch):
    """Ljubljana -> Maribor (13 voženj) je bila za Ljubljana -> Kresnice (28),
    ker je izbor štel vožnje -- in najbolj iskana relacija je dobila `noindex`.
    Tu: med Mali1 in Mali2 vozi deset vlakov, med Velika1 in Velika2 šest,
    a skozi veliki postaji pelje še štirideset drugih."""
    conn.executemany(
        "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
        [("M1", "Mali1", 46.0, 14.0), ("M2", "Mali2", 46.1, 14.0),
         ("V1", "Velika1", 46.0, 15.0), ("V2", "Velika2", 46.5, 15.5),
         ("O1", "Ob Veliki1", 46.001, 15.001), ("O2", "Ob Veliki2", 46.501, 15.501)])
    _voznje(conn, "m", 10, ["M1", "M2"])
    _voznje(conn, "v", 6, ["V1", "V2"])
    _voznje(conn, "a", 20, ["V1", "O1"])
    _voznje(conn, "b", 20, ["O2", "V2"])
    conn.commit()
    monkeypatch.setitem(pristanek.NAJVEC_RELACIJ, "zeleznica", 1)
    got = pristanek.zgradi(conn, 90, "zeleznica")
    assert [(r["od"], r["cilj"]) for r in got["relacije"]] == [("Velika1", "Velika2")]


def test_mestni_promet_ne_steje_v_tezo(conn, monkeypatch):
    """Bavarski dvor ima 14 215 postankov, od tega 1 137 medkrajevnih: z
    mestnimi vred bi bil vsak par z njim težji od Maribora."""
    conn.executemany(
        "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
        [("B", "Mesto", 46.05, 14.50), ("B2", "Mestna ulica", 46.052, 14.502),
         ("K", "Kraj", 46.30, 14.20), ("L", "Ljubljana AP", 46.06, 14.51),
         ("R", "Maribor AP", 46.56, 15.65), ("Q", "Ljubljana Center", 46.07, 14.52)])
    _voznje(conn, "x", 5, ["B", "K"], "avtobus", "1118")
    _voznje(conn, "l", 100, ["B", "B2"], "avtobus", "lpp")
    _voznje(conn, "y", 5, ["L", "R"], "avtobus", "1118")
    _voznje(conn, "z", 10, ["L", "Q"], "avtobus", "1118")   # blizu: ni relacija
    conn.commit()
    monkeypatch.setitem(pristanek.NAJVEC_RELACIJ, "avtobus", 1)
    got = pristanek.zgradi(conn, 90, "avtobus")
    assert [(r["od"], r["cilj"]) for r in got["relacije"]] == [("Ljubljana AP", "Maribor AP")]


def test_mestni_lpp_v_relacijah_ne_nastopa(conn):
    """Mestne „relacije" so postajališče do postajališča znotraj mesta. Stran
    postajališča ostane, relacija ne."""
    conn.executemany(
        "INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)",
        [("M1", "Medvode", 46.142, 14.412), ("M2", "Tivoli", 46.058, 14.495)])
    for i in range(40):
        tid = f"m{i}"
        conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign,"
                     "  service_id, network, agency) "
                     "VALUES(?,?,?,?, 'S1', 'avtobus', 'lpp')",
                     (tid, f"rm{i}", "3G", "M1 - M2"))
        conn.executemany(
            "INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
            [(tid, 1, "M1", None, 28800), (tid, 2, "M2", 30000, None)])
    db.fill_trip_window(conn)
    conn.commit()
    got = pristanek.zgradi(conn, 90, "avtobus")
    assert got["relacije"] == []
    assert [p["ime"] for p in got["postaje"]] == ["Medvode", "Tivoli"]


def test_stran_ne_skrije_vlaka_z_zamudo():
    """Vlak z zamudo je po voznem redu že mimo, a še ni odpeljal."""
    from datetime import datetime
    zdaj = datetime.fromisoformat("2026-09-22T16:27:00+02:00")
    assert pristanek._se_ni_odpeljal("2026-09-22T16:15:00+02:00",
                                     "2026-09-22T16:35:00+02:00", zdaj)
    assert not pristanek._se_ni_odpeljal("2026-09-22T16:15:00+02:00",
                                         "2026-09-22T16:20:00+02:00", zdaj)
    # Prezgodnji avtobus ostane do voznoredne ure, kot doslej.
    assert pristanek._se_ni_odpeljal("2026-09-22T16:30:00+02:00",
                                     "2026-09-22T16:25:00+02:00", zdaj)
    assert not pristanek._se_ni_odpeljal(None, None, zdaj)


def test_odhodi_po_pricakovani_uri():
    """Vožnja z veliko zamudo gre na svoje mesto, ne na vrh strani."""
    o = [
        {"id": "pozna", "sched": "2026-09-25T12:46:00+02:00",
         "expected": "2026-09-25T13:34:00+02:00"},
        {"id": "brez", "sched": "2026-09-25T13:20:00+02:00", "expected": None},
        {"id": "hitra", "sched": "2026-09-25T13:14:00+02:00",
         "expected": "2026-09-25T13:16:00+02:00"},
        {"id": "ista", "sched": "2026-09-25T13:10:00+02:00",
         "expected": "2026-09-25T13:16:00+02:00"},
    ]
    assert [x["id"] for x in pristanek._po_pricakovani(o)] == [
        "ista", "hitra", "brez", "pozna"]


def test_izpisana_je_ura_po_kateri_je_vrstni_red():
    """Z voznoredno uro bi tekle ure nazaj: 17:55, 17:57, 17:50 (+10), 18:15."""
    assert pristanek.ura_odhoda(
        {"sched": "2026-09-25T17:50:00+02:00",
         "expected": "2026-09-25T18:00:00+02:00"}) == ("18:00", "17:50")
    # Brez zamude ali z zamudo pod minuto ni česa prečrtati.
    assert pristanek.ura_odhoda(
        {"sched": "2026-09-25T18:15:00+02:00", "expected": None}) == ("18:15", None)
    assert pristanek.ura_odhoda(
        {"sched": "2026-09-25T18:15:00+02:00",
         "expected": "2026-09-25T18:15:40+02:00"}) == ("18:15", None)
