"""Tir vlaka s table SŽ: razbiranje table, vrstni red branja, prikaz.

    ./venv/bin/python -m pytest tests/test_peroni.py -q
"""
from __future__ import annotations

from kajros import db, peroni

ZDAJ = 1_790_000_000
DAN = "2026-09-25"

# Oblika, kot jo vrne `/sz/postaje/{st}/prihodi_raw` (25. 9. 2026, Ljubljana).
TABLA = {
    "departures": [
        {"Načrtovano": "12:50", "Št. vlaka": "2010", "Tir": "6-A", "Zamude*": ""},
        {"Načrtovano": "12:56", "Št. vlaka": "2408", "Tir": "", "Zamude*": ""},
        {"Načrtovano": "13:03", "Št. vlaka": "Bus", "Tir": "", "Zamude*": ""},
    ],
    "arrivals": [
        {"Načrtovano": "12:39", "Št. vlaka": "3212", "Tir": "2-A", "Zamude*": "32 min"},
        {"Načrtovano": "12:40", "Št. vlaka": "2010", "Tir": "5-A", "Zamude*": ""},
        {"Načrtovano": "12:41", "Št. vlaka": "2408", "Tir": "12-A", "Zamude*": ""},
        {"Načrtovano": "12:42", "Št. vlaka": "0715", "Tir": "3", "Zamude*": ""},
    ],
}


def _baza():
    c = db.connect(":memory:")
    db.init(c)
    return c


def test_razberi_odhod_pred_prihodom_prazen_ne_prekrije():
    tiri, vlakov = peroni.razberi(TABLA)
    assert tiri == {"2010": "6-A", "2408": "12-A", "3212": "2-A", "715": "3"}
    # Nadomestni avtobus ni vlak in ne šteje.
    assert vlakov == 4


def test_stevilka_brez_vrste_in_vodilnih_nicel():
    assert peroni.stevilka("LPV 2010") == "2010"
    assert peroni.stevilka("2010") == "2010"
    assert peroni.stevilka("LP 0715") == "715"


def test_zapis_in_prikaz_s_spremembo_tira():
    c = _baza()
    c.execute("INSERT INTO peron_postaja(st, postaja) VALUES('42300', 'Ljubljana')")
    assert peroni.zapisi(c, "42300", "Ljubljana", DAN, TABLA, ZDAJ) == 4
    # Drugo branje: 2010 je dobil drug tir, 2408 je odpeljal in ga ni več.
    druga = {"departures": [{"Št. vlaka": "2010", "Tir": "7-A"}],
             "arrivals": [{"Št. vlaka": "3212", "Tir": "2-A"}]}
    peroni.zapisi(c, "42300", "Ljubljana", DAN, druga, ZDAJ + 60)

    vrstice = [{"train_no": "LPV 2010", "sched": f"{DAN}T12:50:00+02:00"},
               {"train_no": "LP 3212", "sched": f"{DAN}T12:39:00+02:00"},
               {"train_no": "IC 502", "sched": f"{DAN}T13:00:00+02:00"},
               {"train_no": "LPV 2408", "sched": f"{DAN}T12:56:00+02:00"}]
    peroni.dopolni(c, vrstice, lambda r: (r["train_no"], "Ljubljana", r["sched"]),
                   zdaj=ZDAJ + 120)
    assert vrstice[0]["tir"] == "7-A" and vrstice[0]["tir_prej"] == "6-A"
    assert vrstice[1]["tir"] == "2-A" and "tir_prej" not in vrstice[1]
    assert "tir" not in vrstice[2]
    # Vlak, ki ga zadnja tabla ne nosi več, je odpeljal: njegov tir ne velja.
    assert "tir" not in vrstice[3]


def test_tir_zamujene_postaje_se_ne_pokaze():
    # Vir je obstal: postaja bi morala biti prebrana že dvakrat.
    c = _baza()
    c.execute("INSERT INTO peron_postaja(st, postaja, promet) VALUES('42300', 'Ljubljana', 280)")
    peroni.zapisi(c, "42300", "Ljubljana", DAN, TABLA, ZDAJ)
    v = [{"train_no": "LPV 2010", "sched": f"{DAN}T12:50:00+02:00"}]
    kako = lambda r: (r["train_no"], "Ljubljana", r["sched"])  # noqa: E731
    peroni.dopolni(c, v, kako, zdaj=ZDAJ + 2 * peroni.OBHOD_S)
    assert v[0]["tir"] == "6-A"
    del v[0]["tir"]
    peroni.dopolni(c, v, kako, zdaj=ZDAJ + 2 * peroni.OBHOD_S + 1)
    assert "tir" not in v[0]


def test_datum_je_koledarski_dan_ure():
    # Vlak ob 00:30 pripada včerajšnjemu prometnemu dnevu, na tabli SŽ pa je
    # pod današnjim datumom.
    c = _baza()
    c.execute("INSERT INTO peron_postaja(st, postaja) VALUES('42300', 'Ljubljana')")
    peroni.zapisi(c, "42300", "Ljubljana", "2026-09-26",
                  {"departures": [{"Št. vlaka": "1604", "Tir": "8-B"}]}, ZDAJ)
    v = [{"train_no": "RG 1604", "sched": "2026-09-26T00:30:00+02:00"}]
    peroni.dopolni(c, v, lambda r: (r["train_no"], "Ljubljana", r["sched"]), zdaj=ZDAJ)
    assert v[0]["tir"] == "8-B"


def test_prazna_tabla_ne_spremeni_znanja_o_postaji():
    c = _baza()
    c.execute("INSERT INTO peron_postaja(st, postaja, ima_tir) VALUES('42300', 'Ljubljana', 1)")
    peroni.zapisi(c, "42300", "Ljubljana", DAN, {"departures": [], "arrivals": []}, ZDAJ)
    assert tuple(c.execute("SELECT ima_tir, vlakov FROM peron_postaja").fetchone()) == (1, 0)
    brez = {"departures": [{"Št. vlaka": "2432", "Tir": ""}]}
    peroni.zapisi(c, "42300", "Ljubljana", DAN, brez, ZDAJ)
    assert c.execute("SELECT ima_tir FROM peron_postaja").fetchone()[0] == 0


def test_vrstni_red_branja():
    c = _baza()
    c.executemany(
        "INSERT INTO peron_postaja(st, postaja, ima_tir, vlakov, promet, preverjeno)"
        " VALUES(?,?,?,?,?,?)",
        [("a", "A", 1, 10, 300, ZDAJ - peroni.OBHOD_S + 5),  # skoraj na vrsti
         ("b", "B", 0, 10, 300, ZDAJ - 3600),                 # brez tira: čez dan
         ("c", "C", 1, 0, 300, ZDAJ - 600),                   # prazna tabla: čez uro
         ("m", "M", 1, 10, 5, ZDAJ - 3 * peroni.OBHOD_S),     # majhna: redkeje
         ("d", "D", 1, 10, 300, ZDAJ - peroni.OBHOD_S - 60)]) # zamujena
    assert peroni.na_vrsti(c, ZDAJ)["st"] == "d"
    assert peroni.na_vrsti(c, ZDAJ, odlozene=["d"]) is None
    c.execute("UPDATE peron_postaja SET preverjeno = ? WHERE st = 'd'", (ZDAJ,))
    assert peroni.na_vrsti(c, ZDAJ) is None
    assert peroni.na_vrsti(c, ZDAJ + 5)["st"] == "a"
    # Promet 5 je trideseti del polnega; razmik se ustavi pri NAJDLJE_S.
    m = ZDAJ - 3 * peroni.OBHOD_S + peroni.NAJDLJE_S
    assert peroni.na_vrsti(c, m - 1, odlozene=["a", "d", "c"]) is None
    assert peroni.na_vrsti(c, m, odlozene=["a", "d", "c"])["st"] == "m"
    c.executemany("INSERT INTO peron_postaja(st, postaja, promet) VALUES(?, ?, ?)",
                  [("e", "E", 10), ("f", "F", 900)])
    assert peroni.na_vrsti(c, ZDAJ)["st"] == "f"             # neznana: najprometnejša
    # Zamujena znana ima prednost pred neznanimi, sicer prvo branje vseh
    # postaj (ura in pol) izstrada Ljubljano.
    assert peroni.na_vrsti(c, ZDAJ + 10)["st"] == "a"


def test_seznam_postaj_po_nasih_imenih(monkeypatch):
    c = _baza()
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,46,14)",
                  [("1", "Ljubljana"), ("2", "Lavrica(Železniški)"), ("3", "Ljubljana AP")])
    c.executemany("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id,"
                  " mode, agency, network) VALUES(?,?,?,?,?,?,?,?)",
                  [("t", "r", "LP 1", "x", "S", "rail", "1161", "zeleznica"),
                   ("b", "r", "N1", "x", "S", "bus", "1119", "avtobus")])
    c.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,0,0)",
                  [("t", 1, "1"), ("t", 2, "2"), ("b", 1, "3")])
    monkeypatch.setattr(peroni, "_get", lambda pot: [
        {"st": "42300", "naziv": "Ljubljana"}, {"st": "42320", "naziv": "Lavrica"},
        {"st": "99999", "naziv": "Ljubljana AP"}, {"st": "11111", "naziv": "Villach"}])
    assert peroni.osvezi_postaje(c) == 2
    assert {r[0]: (r[1], r[2]) for r in c.execute(
        "SELECT st, postaja, promet FROM peron_postaja")} == {
        "42300": ("Ljubljana", 1), "42320": ("Lavrica(Železniški)", 1)}
