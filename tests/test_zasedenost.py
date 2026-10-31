"""Zasedenost po poročilih potnikov: varovalke, en glas na odhod, povzetek.

Šesta pisalna pot (21. 10. 2026), zato kot pri `test_stik.py` varujemo
predvsem, kaj neznanec sme in česa ne shranimo. Sintetično omrežje okoli
Ljubljana AP z vožnjami v dve smeri; vsi datumi so trdi (petek 23. 10. 2026)
in vsak klic dobi svoj `zdaj` -- računan današnji datum ob trdem v pripravi
je v tem projektu že podrl teste (CLAUDE.md).

    ./venv/bin/python -m pytest tests/test_zasedenost.py -q
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from kajros import db, stats, stik, zasedenost

PETEK = "2026-10-23"
#: Petki pred tem, za povzetek „običajno“.
PETKI = [(date(2026, 10, 23) - timedelta(weeks=k)).isoformat() for k in range(1, 8)]
NAPRAVA = "a" * 32


def _s(ura: str) -> int:
    h, m = map(int, ura.split(":"))
    return h * 3600 + m * 60


@pytest.fixture()
def conn():
    zasedenost._glasovi.clear()
    zasedenost._soli.clear()
    zasedenost._poslana.clear()
    stik._poslana.clear()
    c = db.connect(":memory:")
    db.init(c)
    stik.init(c)
    zasedenost.init(c)
    c.executemany("INSERT INTO station(stop_id, name, lat, lon) VALUES(?,?,?,?)", [
        ("LJ", "Ljubljana AP", 46.05, 14.51), ("ST", "Ljubljana Stadion", 46.06, 14.52),
        ("MB", "Maribor AP", 46.56, 15.65), ("MS", "Murska Sobota AP", 46.66, 16.16),
        ("KA", "Kamnik AP", 46.22, 14.61)])
    for d in [PETEK, *PETKI, "2026-10-22"]:
        c.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S', ?)", (d,))
    voznje = [
        # trip, številka, prevoznik, smer, postanki (postaja, ura)
        ("a1530", "A2527", "1123", "Ljubljana AP - Maribor AP",
         [("LJ", "15:30"), ("MB", "17:20")]),
        ("m1620", "M2123", "1121", "Ljubljana AP - Murska Sobota AP",
         [("LJ", "16:20"), ("ST", "16:25"), ("MB", "18:05"), ("MS", "19:00")]),
        ("k1600", "A5210", "1123", "Ljubljana AP - Kamnik AP",
         [("LJ", "16:00"), ("ST", "16:05"), ("KA", "16:50")]),
        ("r1500", "A2527", "1123", "Maribor AP - Ljubljana AP",
         [("MB", "15:00"), ("LJ", "16:50")]),
        ("lpp", "6", "lpp", "Črnuče", [("LJ", "16:10"), ("ST", "16:20")]),
    ]
    for trip, st, ag, smer, postanki in voznje:
        c.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
                  " agency, network) VALUES(?,?,?,?, 'S', 'bus', ?, 'avtobus')",
                  (trip, trip, st, smer, ag))
        for i, (p, u) in enumerate(postanki, 1):
            c.execute("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s)"
                      " VALUES(?,?,?,?,?)", (trip, i, p, _s(u), _s(u)))
    db.fill_trip_window(c)
    c.commit()
    yield c
    c.close()


def _ob(datum: str, ura: str) -> float:
    return stats.polnoc(datum) + _s(ura)


def _javi(conn, stopnja, ura="16:10", trip="m1620", datum=PETEK, postaja="Ljubljana AP",
          naprava=NAPRAVA, kljuc="ip", **kw):
    return zasedenost.sprejmi(conn, {"trip_id": trip, "service_date": datum,
                                     "postaja": postaja, "stopnja": stopnja,
                                     "naprava": naprava, **kw}, kljuc, _ob(datum, ura))


def _vrstice(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM zasedenost ORDER BY id")]


# ------------------------------------------------------------ tip dneva

def test_tip_dneva():
    assert zasedenost.tip_dneva("2026-10-19") == "pon"
    assert zasedenost.tip_dneva("2026-10-21") == "tor-cet"
    assert zasedenost.tip_dneva(PETEK) == "pet"
    assert zasedenost.tip_dneva("2026-10-24") == "sob"
    # Praznik vozi kot nedelja, tudi na petek in velikonočni ponedeljek.
    assert zasedenost.tip_dneva("2026-12-25") == "ned"
    assert zasedenost.tip_dneva("2026-04-06") == "ned"
    assert zasedenost.tip_dneva("2026-04-07") == "tor-cet"


# ------------------------------------------------------------ sprejem

def test_porocilo_se_zapise_po_odhodu_ne_po_tripu(conn):
    r = _javi(conn, 4)
    assert r["stopnja"] == 4 and r["postaja"] == "Ljubljana AP" and r["ura"] == "16:10"
    v = _vrstice(conn)[0]
    assert (v["agency"], v["train_no"], v["start_s"]) == ("1121", "M2123", _s("16:20"))
    assert json.loads(v["naprej"]) == ["Ljubljana Stadion", "Maribor AP", "Murska Sobota AP"]


def test_identitete_ni_v_shemi(conn):
    """Najpomembnejši test modula: ne naprave ne naslova v bazi."""
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(zasedenost)")}
    assert not stolpci & {"naprava", "ip", "kljuc", "obiskovalec", "glas"}
    _javi(conn, 3)
    assert NAPRAVA not in json.dumps(_vrstice(conn))


def test_ista_naprava_popravi_ne_doda(conn):
    _javi(conn, 3, ura="16:05")
    _javi(conn, 5, ura="16:21")
    v = _vrstice(conn)
    assert len(v) == 1 and v[0]["stopnja"] == 5
    # `prejeto` je prvo „polno“: tu prehod s 3 na 5 ob 16:21.
    assert v[0]["prejeto"] == int(_ob(PETEK, "16:21"))


def test_prejeto_ostane_ob_prvem_polnem(conn):
    _javi(conn, 4, ura="16:05")
    _javi(conn, 5, ura="16:21")
    assert _vrstice(conn)[0]["prejeto"] == int(_ob(PETEK, "16:05"))


def test_druga_postaja_je_drugo_opazanje(conn):
    """Popravek z druge postaje ne sme vzeti `prejeto` s prve (pregled e955c1a)."""
    _javi(conn, 4, ura="16:15")
    _javi(conn, 4, ura="18:00", postaja="Maribor AP")
    v = _vrstice(conn)
    assert [r["postaja"] for r in v] == ["Ljubljana AP", "Maribor AP"]
    assert v[1]["prejeto"] == int(_ob(PETEK, "18:00"))


def test_preklic_po_popravku(conn):
    _javi(conn, 4, ura="16:05")
    _javi(conn, 5, ura="16:12")
    assert _javi(conn, None, ura="16:17", preklic=True) == {"preklicano": True}
    assert _vrstice(conn) == []


def test_glas_cez_polnoc(conn):
    """Vožnja ob 23:50 je ista po polnoči: popravek ne sme biti drug potnik."""
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
                 " agency, network) VALUES('n', 'n', 'A9', 'Ljubljana AP - Maribor AP', 'S',"
                 " 'bus', '1123', 'avtobus')")
    conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                     [("n", 1, "LJ", _s("23:50"), _s("23:50")), ("n", 2, "MB", _s("25:30"), _s("25:30"))])
    db.fill_trip_window(conn)
    _javi(conn, 4, trip="n", ura="23:45")
    _javi(conn, 5, trip="n", ura="24:05")
    assert len(_vrstice(conn)) == 1


def test_druga_naprava_je_drug_potnik(conn):
    _javi(conn, 4)
    _javi(conn, 4, naprava="b" * 32)
    assert len(_vrstice(conn)) == 2


def test_preklic_samo_kmalu(conn):
    _javi(conn, 4, ura="16:00")
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, None, ura="16:15", preklic=True)
    assert len(_vrstice(conn)) == 1
    _javi(conn, 4, ura="16:00", naprava="c" * 32)
    assert _javi(conn, None, ura="16:05", naprava="c" * 32, preklic=True) == {"preklicano": True}
    assert len(_vrstice(conn)) == 1


@pytest.mark.parametrize("ura,stopnja", [("15:10", 4), ("19:30", 4), ("16:00", 5)])
def test_cas_porocila(conn, ura, stopnja):
    """Od ure pred odhodom do treh ur po njem; „vrsta zunaj“ od 10 min pred odhodom."""
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, stopnja, ura=ura)
    if stopnja == 5:
        assert _javi(conn, 5, ura="16:10")["stopnja"] == 5


@pytest.mark.parametrize("stopnja", [0, 6, True, "4", None])
def test_stopnja_mora_biti_stevilka(conn, stopnja):
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, stopnja)


def test_mestni_lpp_in_tuja_postaja(conn):
    """Mestni LPP je zraven kot vsi: prej je bil LPP 25 iz IJPP vklopljen, 11 ne."""
    assert _javi(conn, 4, trip="lpp", ura="16:05")["stopnja"] == 4
    # Id mestnega LPP so trije UUID-ji: dolg id je „ne poznam“, ne napaka oblike.
    with pytest.raises(zasedenost.Zavrnjeno, match="ne poznam"):
        _javi(conn, 4, trip="|".join(["5075f5b4-daea-425d-b3fe-c4807ebf11c7"] * 3))
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, 4, postaja="Kamnik AP")
    # Na zadnji postaji se ne vstopa.
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, 4, postaja="Murska Sobota AP", ura="18:50")
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, 4, datum="2026-10-25")          # ta dan ne vozi


def test_naprava_brez_oblike(conn):
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, 4, naprava="nekaj")


def test_strop_na_uro(conn):
    for i in range(zasedenost.NA_URO):
        _javi(conn, 4, naprava=f"{i:032x}")
    with pytest.raises(zasedenost.Zavrnjeno) as e:
        _javi(conn, 4, naprava="f" * 32)
    assert e.value.status == 429


def test_dnevni_strop(conn, monkeypatch):
    monkeypatch.setattr(zasedenost, "VSEH_NA_DAN", 2)
    _javi(conn, 4, kljuc="x")
    _javi(conn, 4, kljuc="y", naprava="b" * 32)
    with pytest.raises(zasedenost.Zavrnjeno):
        _javi(conn, 4, kljuc="z", naprava="c" * 32)


# ------------------------------------------------------------ pregled

def _zgodovina(conn, trip, datumi, stopnja, ura_porocila="16:08", postaja="Ljubljana AP"):
    for i, d in enumerate(datumi):
        _javi(conn, stopnja, trip=trip, datum=d, ura=ura_porocila, postaja=postaja,
              naprava=f"{i + 1:032x}")


def test_ista_smer():
    assert zasedenost._ista_smer(["Ljubljana Stadion", "Maribor AP", "Murska Sobota AP"],
                                 ["Maribor AP"])
    assert not zasedenost._ista_smer(["Ljubljana Stadion", "Maribor AP"],
                                     ["Ljubljana Stadion", "Kamnik AP"])


def test_obicajno_sele_od_petih(conn):
    _zgodovina(conn, "m1620", PETKI[:4], 4)
    p = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))
    assert p["obicajno"] is None
    assert p["zadnjic"]["datum"] == PETKI[0]
    _zgodovina(conn, "m1620", PETKI[4:5], 5, ura_porocila="16:11")
    o = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))["obicajno"]
    assert o["kdaj"] == "ob petkih" and o["porocil"] == 5
    assert o["stopnje"] == [0, 0, 0, 4, 1] and o["mediana"] == 4
    # Poln je bil 12 min pred odhodom (poročilo ob 16:08), en petek 9 min.
    assert o["prej"] == {"dni": 5, "od_min": 9, "do_min": 12, "nasvet_min": 15}
    assert zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))["zadnjic"] is None


def _zadnjic(conn):
    return zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))["zadnjic"]


def test_zadnjic_isti_odhod_z_nasvetom(conn):
    """Eno poročilo „polno“ 12 min pred odhodom: dovolj za „pridi 15 min prej“."""
    _zgodovina(conn, "m1620", PETKI[:1], 4)
    z = _zadnjic(conn)
    assert (z["datum"], z["dan"], z["stopnja"]) == (PETKI[0], "pet", 4)
    assert z["isti_odhod"] and z["prej"] == {"nasvet_min": 15}


def test_zadnjic_javljeno_po_odhodu_brez_nasveta(conn):
    """Polno, a javljeno po odhodu: kako prej priti, tega ne pove."""
    _zgodovina(conn, "m1620", PETKI[:1], 4, ura_porocila="16:21")
    assert _zadnjic(conn)["prej"] is None


def test_zadnjic_predolgo_pred_odhodom_brez_nasveta(conn):
    """Polno 55 min prej je en potnik pri prejšnjem avtobusu, ne nasvet."""
    _zgodovina(conn, "m1620", PETKI[:1], 4, ura_porocila="15:25")
    assert _zadnjic(conn)["prej"] is None


def test_zadnjic_pol_polno_brez_nasveta(conn):
    _zgodovina(conn, "m1620", PETKI[:1], 2)
    z = _zadnjic(conn)
    assert (z["stopnja"], z["prej"]) == (2, None)


def test_zadnjic_z_druge_postaje_brez_nasveta(conn):
    """Isti odhod, a polno na Stadionu ne pove, kdaj priti na Ljubljana AP."""
    _zgodovina(conn, "m1620", PETKI[:1], 4, ura_porocila="16:15", postaja="Ljubljana Stadion")
    z = _zadnjic(conn)
    assert z["postaja"] == "Ljubljana Stadion" and z["isti_odhod"] and z["prej"] is None


def test_zadnjic_primerljiv_samo_isti_tip_dneva(conn):
    """Drug odhod v isto smer šteje le na isti tip dneva, in pove svojo uro."""
    _javi(conn, 3, trip="a1530", datum="2026-10-22", ura="15:20")
    assert _zadnjic(conn) is None
    _zgodovina(conn, "a1530", PETKI[:1], 2, ura_porocila="15:20")
    z = _zadnjic(conn)
    assert (z["datum"], z["ura"], z["stopnja"], z["isti_odhod"]) == (PETKI[0], "15:30", 2, False)


def test_zadnjic_isti_odhod_pred_novejsim_primerljivim(conn):
    """Isti odhod šteje na kateri koli dan, tudi starejši od primerljivega."""
    _zgodovina(conn, "a1530", PETKI[:1], 2, ura_porocila="15:20")
    _javi(conn, 1, datum=PETKI[1])
    z = _zadnjic(conn)
    assert (z["datum"], z["stopnja"], z["isti_odhod"]) == (PETKI[1], 1, True)


def test_obicajno_zdruzi_prevoznike_v_isti_smeri(conn):
    """A2527 ob 15:30 v Maribor šteje za M2123 ob 16:20, Kamnik ne."""
    _zgodovina(conn, "a1530", PETKI[:5], 5, ura_porocila="15:31")
    _zgodovina(conn, "k1600", PETKI[:5], 1, ura_porocila="15:55")
    o = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))["obicajno"]
    assert o["stopnje"] == [0, 0, 0, 0, 5]


def test_en_dan_ni_obicajno(conn):
    """Pet potnikov istega avtobusa (ali en z petimi id-ji) je en dan, ne navada."""
    for i in range(6):
        _javi(conn, 5, trip="m1620", datum=PETKI[0], ura="16:21", naprava=f"{i + 1:032x}")
    p = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))
    assert p["obicajno"] is None


def test_vlak_in_avtobus_se_ne_mesata(conn):
    """Ista postaja, ista smer, drugo omrežje: pri vlaku „polno“ pomeni stojijo."""
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
                 " agency, network) VALUES('v', 'v', 'IC 1', 'Ljubljana AP - Maribor AP', 'S',"
                 " 'vlak', '1161', 'zeleznica')")
    conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                     [("v", 1, "LJ", _s("16:00"), _s("16:00")), ("v", 2, "MB", _s("17:50"), _s("17:50"))])
    db.fill_trip_window(conn)
    _zgodovina(conn, "v", PETKI[:5], 4, ura_porocila="15:55")
    p = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))
    assert p["obicajno"] is None


def test_lpp_samo_ista_linija(conn):
    """LPP 6 do Stadiona ni v smeri Maribora; druga linija LPP ni ta linija."""
    conn.execute("INSERT INTO trip(trip_id, route_id, train_no, headsign, service_id, mode,"
                 " agency, network) VALUES('lpp2', 'lpp2', '11', 'Črnuče', 'S', 'bus', 'lpp',"
                 " 'avtobus')")
    conn.executemany("INSERT INTO sched(trip_id, stop_seq, stop_id, arr_s, dep_s) VALUES(?,?,?,?,?)",
                     [("lpp2", 1, "LJ", _s("16:00"), _s("16:00")), ("lpp2", 2, "ST", _s("16:08"), _s("16:08"))])
    db.fill_trip_window(conn)
    _zgodovina(conn, "lpp", PETKI[:5], 5, ura_porocila="16:05")
    p = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))
    assert p["obicajno"] is None
    p = zasedenost.pregled(conn, "lpp2", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))
    assert p["obicajno"] is None
    p = zasedenost.pregled(conn, "lpp", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))
    assert p["obicajno"]["stopnje"] == [0, 0, 0, 0, 5]


def test_drugi_dnevi_tipa_ko_istega_dne_ni_dovolj(conn):
    """Ponedeljek ni torek: tip dneva, ne cel teden (vozni red ima ob ponedeljkih ojačitve)."""
    srede = ["2026-10-07", "2026-10-14", "2026-10-21"]
    cetrtki = ["2026-10-08", "2026-10-15"]
    for d in [*srede, *cetrtki, "2026-10-19"]:
        conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S', ?)", (d,))
    _zgodovina(conn, "m1620", [*srede, *cetrtki], 3)
    _zgodovina(conn, "m1620", ["2026-10-19"], 5, ura_porocila="16:11")
    o = zasedenost.pregled(conn, "m1620", "2026-10-22", "Ljubljana AP",
                           _ob("2026-10-22", "15:00"))["obicajno"]
    assert o["kdaj"] == "od torka do četrtka" and o["stopnje"] == [0, 0, 5, 0, 0]


def test_danes_prejsnji_in_te_ni_vzel(conn):
    _javi(conn, 5, trip="a1530", ura="15:34", naprava="d" * 32)
    p = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:50"))
    assert p["prejsnji"]["ura"] == "15:30" and p["prejsnji"]["stopnja"] == 5
    assert p["prejsnji"]["javljeno"] == "15:34"
    # Prejšnji v isto smer, ki je pravkar odpeljal, je 15:30 -- Kamnik ob 16:00 ne.
    assert p["te_ni_vzel"]["trip_id"] == "a1530" and p["te_ni_vzel"]["oznaka"] == "Arriva"
    p = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "16:15"))
    assert p["te_ni_vzel"] is None                     # odpeljal pred več kot 30 min


def test_brez_postaje_prva(conn):
    p = zasedenost.pregled(conn, "m1620", PETEK, None, _ob(PETEK, "15:00"))
    assert p["postaja"] == "Ljubljana AP" and p["odhod"] == "16:20"
    assert [x["ime"] for x in p["postaje"]] == ["Ljubljana AP", "Ljubljana Stadion", "Maribor AP"]


# ------------------------------------------------------------ komentarji

@pytest.mark.parametrize("besedilo", [
    "glej https://primer.si", "pišite na ana@primer.si", "pokliči 041 123 456"])
def test_opomba_brez_povezav_in_osebnih_podatkov(conn, besedilo):
    with pytest.raises(zasedenost.Zavrnjeno):
        zasedenost.preveri_opombo(conn, "m1620", PETEK, "Ljubljana AP", besedilo,
                                  _ob(PETEK, "16:30"))


def test_opomba_skozi_nabiralnik_do_objave(conn):
    besedilo, kontekst = zasedenost.preveri_opombo(
        conn, "m1620", PETEK, "Ljubljana AP", "Vrsta do konca perona že ob 16:00.",
        _ob(PETEK, "16:30"))
    id_ = stik.sprejmi(conn, email="", besedilo=besedilo, anonimno=True,
                       zeton_iz_obrazca=stik.zeton(_ob(PETEK, "16:29")), vaba="",
                       kljuc="k", zdaj=_ob(PETEK, "16:30"), opomba=kontekst,
                       meje=(zasedenost.OPOMBA_NAJKRAJSE, zasedenost.OPOMBA_NAJDALJSE))
    seznam = zasedenost.oznaci_objavljene(conn, stik.seznam(conn))
    assert seznam[0]["opomba"]["oznaka"] == "AP MS · 16:20 · Ljubljana AP"
    assert seznam[0]["objavljeno"] is False
    teden = (date(2026, 10, 30)).isoformat()
    conn.execute("INSERT OR IGNORE INTO service_day(service_id, date) VALUES('S', ?)", (teden,))
    # Ni objavljena: drugi je ne vidijo.
    assert zasedenost.pregled(conn, "m1620", teden, "Ljubljana AP", _ob(teden, "15:00"))["opombe"] == []
    assert zasedenost.objavi(conn, id_, _ob(PETEK, "17:00"))
    op = zasedenost.pregled(conn, "a1530", teden, "Ljubljana AP", _ob(teden, "15:00"))["opombe"]
    assert [o["besedilo"] for o in op] == ["Vrsta do konca perona že ob 16:00."]
    assert zasedenost.umakni(conn, id_)
    assert zasedenost.pregled(conn, "m1620", teden, "Ljubljana AP", _ob(teden, "15:00"))["opombe"] == []


def test_opomba_o_tem_odhodu_pred_novejso_o_podobnem(conn):
    """Prva je na vrhu okna: o tem odhodu, sicer najnovejša; drug odhod pove svojo uro."""
    for trip, datum, besedilo in (("m1620", PETKI[2], "Ta odhod, starejša."),
                                  ("m1620", PETKI[1], "Ta odhod, novejša."),
                                  ("a1530", PETKI[0], "Podoben odhod.")):
        zdaj = _ob(datum, "16:30")
        tekst, kontekst = zasedenost.preveri_opombo(conn, trip, datum, "Ljubljana AP", besedilo, zdaj)
        id_ = conn.execute("INSERT INTO sporocilo(prispelo, email, besedilo, opomba) VALUES(?, '', ?, ?)",
                           (f"{datum}T16:30:00+02:00", tekst, kontekst)).lastrowid
        assert zasedenost.objavi(conn, id_, zdaj)
    op = zasedenost.pregled(conn, "m1620", PETEK, "Ljubljana AP", _ob(PETEK, "15:00"))["opombe"]
    assert [o["besedilo"] for o in op] == ["Ta odhod, novejša.", "Ta odhod, starejša.", "Podoben odhod."]
    assert op[0]["isti_odhod"] and not op[2]["isti_odhod"] and op[2]["ura"] == "15:30"


def test_opombe_imajo_svoj_strop(conn, monkeypatch):
    """Opombe si z nabiralnikom delijo `stik.VSEH_NA_DAN`; ne smejo ga zapolniti."""
    monkeypatch.setattr(zasedenost, "OPOMB_NA_DAN", 1)
    zdaj = _ob(PETEK, "16:30")
    besedilo, kontekst = zasedenost.preveri_opombo(conn, "m1620", PETEK, "Ljubljana AP",
                                                   "Polno.", zdaj)
    conn.execute("INSERT INTO sporocilo(prispelo, email, besedilo, opomba) VALUES(?, '', ?, ?)",
                 (f"{PETEK}T16:30:00+02:00", besedilo, kontekst))
    with pytest.raises(zasedenost.Zavrnjeno):
        zasedenost.preveri_opombo(conn, "m1620", PETEK, "Ljubljana AP", "Še vedno polno.", zdaj)


def test_opomba_samo_za_danes_in_vceraj(conn):
    with pytest.raises(zasedenost.Zavrnjeno):
        zasedenost.preveri_opombo(conn, "m1620", PETKI[1], "Ljubljana AP",
                                  "Polno.", _ob(PETEK, "16:30"))


def test_pocisti(conn):
    _zgodovina(conn, "m1620", PETKI[:1], 4)
    assert zasedenost.pocisti(conn, _ob(PETEK, "12:00")) == 0
    assert zasedenost.pocisti(conn, _ob(PETEK, "12:00") + 400 * 86400) == 1


# ------------------------------------------------------------ API

def test_api_brez_stikala_ni_poti(conn, monkeypatch):
    from fastapi import HTTPException

    from kajros import api, config
    monkeypatch.setattr(config, "ZASEDENOST", False)
    with pytest.raises(HTTPException) as e:
        api.api_zasedenost("m1620", PETEK, None)
    assert e.value.status_code == 404


def test_api_pregled_in_mestni_lpp(conn, monkeypatch):
    from kajros import api, config
    monkeypatch.setattr(config, "ZASEDENOST", True)
    monkeypatch.setattr(api, "_conn", lambda: conn)
    p = api.api_zasedenost("m1620", PETEK, "Ljubljana AP")
    assert p["vklopljeno"] and p["zeton"]
    assert api.api_zasedenost("lpp", PETEK, None)["vklopljeno"] is True


def test_skrbnik_objavi_in_brisanje_umakne(conn, monkeypatch):
    from kajros import api
    monkeypatch.setattr(api, "_conn", lambda: conn)
    besedilo, kontekst = zasedenost.preveri_opombo(
        conn, "m1620", PETEK, "Ljubljana AP", "Poln že ob 16:05.", _ob(PETEK, "16:30"))
    id_ = stik.sprejmi(conn, email="", besedilo=besedilo, anonimno=True,
                       zeton_iz_obrazca=stik.zeton(_ob(PETEK, "16:29")), vaba="",
                       kljuc="k", zdaj=_ob(PETEK, "16:30"), opomba=kontekst, meje=(3, 280))
    assert api._admin_sporocilo(id_, {"akcija": ["objavi"]}) == {"id": id_, "objavljeno": True}
    assert conn.execute("SELECT COUNT(*) FROM opomba").fetchone()[0] == 1
    # Izbrisano sporočilo ne sme ostati javno.
    api._admin_sporocilo(id_, {"akcija": ["brisi"]})
    assert conn.execute("SELECT COUNT(*) FROM opomba").fetchone()[0] == 0
