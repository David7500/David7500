"""Mesečno poročilo statistike (`statistika.mesecno_porocilo`, `/statistika/2026-09`).

Zakaj je to vredno testa: stran je zamrznjena in se sklicuje nanjo novinar,
čez leto pa je ne bo nihče več preračunal -- napaka v vsoti, v razredu ali v
tem, kdo je bil zajet cel mesec, bi ostala za vedno. September 2026 je v
testih zato, ker ima 30 dni: okno zadnjih 30 dni na `danes = 1. 10.` je
natanko ta mesec in se mora ujemati s stranjo `/statistika`.

    ./venv/bin/python -m pytest tests/test_statistika_mesec.py -q
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from datetime import date

import pytest

from kajros import api, cli, config, db, markdown, pristanek, server, stats, statistika

MESEC = "2026-09"
#: Dan, ko je september zaključen (zadnji dan + 2).
KONEC = date(2026, 10, 2)


def _hist(rnd: random.Random, n: int) -> Counter:
    h: Counter = Counter()
    for _ in range(n):
        h[rnd.choice((-2, 0, 0, 0, 1, 2, 3, 5, 6, 9, 12, 16, 25, 70))] += 1
    return h


def _vrstica(h: Counter, nacrt: int) -> dict:
    n = sum(h.values())
    return {"nacrt": nacrt, "z_meritvijo": n, "z_lego": None, "s_ciljem": n,
            "hist": {str(m): c for m, c in sorted(h.items())}, "ure": {},
            "vmesnih": 0, "prej1": 0, "prej2": 0, "prej3": 0}


def _vstavi(c, dan: str, kljuc: str, v: dict, ob: int = 1_000) -> None:
    c.execute("INSERT OR REPLACE INTO stat_dan(dan, vrsta, kljuc, podatki, izracunano) "
              "VALUES (?, 'prevoznik', ?, ?, ?)", (dan, kljuc, json.dumps(v), ob))


def _napolni(c, mesec: str = MESEC, ob: int = 1_000) -> dict[str, Counter]:
    """Mesec dnevnih agregatov, kakršne piše `dopolni`; vrne surove histograme
    po ključu, da test prešteje številke neodvisno od modula."""
    rnd = random.Random(11)
    surovo: dict[str, Counter] = {}

    def dodaj(dan: str, kljuc: str, h: Counter, nacrt: int) -> None:
        surovo.setdefault(kljuc, Counter()).update(h)
        _vstavi(c, dan, kljuc, _vrstica(h, nacrt), ob)

    for d in range(1, 31):
        dan = f"{mesec}-{d:02d}"
        # Vlaki: 5. in 6. zajem ni deloval (2 meritvi od 100 načrtovanih).
        dodaj(dan, "zeleznica|1161|vlak", _hist(rnd, 2 if d in (5, 6) else 100), 100)
        dodaj(dan, "zeleznica|1161|nadomestni", Counter(), 20)       # feed ne poroča
        dodaj(dan, "avtobus|1123|avtobus", _hist(rnd, 60), 60)
        # Marprom: do 19. samo vozni red, zajem od 20.
        dodaj(dan, "avtobus|marprom|avtobus", _hist(rnd, 40 if d >= 20 else 0), 40)
        # Kranj: od 25. in ne vsak dan (nedelje brez vrstice -- ni voženj, ni izpad).
        if d >= 25 and d != 28:
            dodaj(dan, "avtobus|kranj|avtobus", _hist(rnd, 15), 15)
    c.commit()
    return surovo


@pytest.fixture()
def baza():
    c = db.connect(":memory:")
    db.init(c)
    surovo = _napolni(c)
    return c, surovo


def _zahteva(pot: str):
    from starlette.requests import Request
    return Request({"type": "http", "method": "GET", "path": pot, "raw_path": pot.encode(),
                    "query_string": b"", "headers": [(b"host", b"kajros.app")],
                    "scheme": "https", "server": ("kajros.app", 443)})


# ---------------------------------------------------------------- meseci in zapis

def test_meje_in_imena_meseca():
    assert statistika.meje_meseca("2026-02") == ("2026-02-01", "2026-02-28")
    assert statistika.meje_meseca("2028-02") == ("2028-02-01", "2028-02-29")
    assert statistika.meje_meseca("2026-12") == ("2026-12-01", "2026-12-31")
    assert statistika.ime_meseca("2026-10") == "oktober 2026"
    for slab in ("", "abc", "2026-13", "2026-00", "2026-1", "0000-01", "2026-10x", "2026-10/"):
        assert not statistika.je_mesec(slab), slab
    assert statistika.je_mesec("2026-10")


def test_obsegi_dni_zlije_zaporedne():
    assert statistika.obsegi_dni([]) == ""
    assert statistika.obsegi_dni(["2026-10-10", "2026-10-08", "2026-10-07", "2026-10-09"]) == "7.–10. 10."
    assert statistika.obsegi_dni(["2026-10-31"]) == "31. 10."
    assert statistika.obsegi_dni(["2026-10-07", "2026-10-31"]) == "7. 10., 31. 10."
    assert statistika.obsegi_dni(["2026-10-31", "2026-11-01"]) == "31. 10.–1. 11."


# ---------------------------------------------------------------- številke

def test_mesec_je_vsota_dni_in_razredi_so_po_zaokrozeni_minuti(baza):
    """Število voženj in razredi so prešteti iz surovih histogramov
    neodvisno od modula; razred po isti minuti kot zaslon."""
    c, surovo = baza
    p = statistika.mesecno_porocilo(c, MESEC)
    po = {x["kljuc"]: x for x in p["prevozniki"]}
    for kljuc, h in surovo.items():
        n = sum(h.values())
        cilj = po[kljuc]["cilj"]
        assert cilj.get("n", 0) == n, kljuc
        if not n:
            continue
        minute = [m for m, k in h.items() for _ in range(k)]
        assert cilj["v5min"] == round(sum(m <= 5 for m in minute) / n * 100, 1)
        assert cilj["nad15"] == round(sum(m > 15 for m in minute) / n * 100, 1)
        assert cilj["mediana_min"] == stats._pct(minute, 0.5)
        assert cilj["p90_min"] == stats._pct(minute, 0.9)
        razred = Counter(stats._KLJUC_RAZREDA[stats._razred_zamude(m * 60)] for m in minute)
        for k, delez in cilj["razredi"].items():
            assert delez == round(razred[k] / n * 100, 1), (kljuc, k)
        assert cilj["nad60_n"] == sum(k for m, k in h.items() if m >= 60)
    # Omrežje avtobusov = vsota prevoznikov (Marprom in Kranj tudi, čeprav pod črto).
    bus = p["omrezja"]["avtobus"]["cilj"]
    assert bus["n"] == sum(sum(h.values()) for k, h in surovo.items() if k.startswith("avtobus|"))
    assert p["omrezja"]["avtobus"]["prevoznikov"] == 3
    assert p["omrezja"]["zeleznica"]["cilj"]["n"] == sum(surovo["zeleznica|1161|vlak"].values())


@pytest.mark.parametrize("net", ["zeleznica", "avtobus"])
def test_mesec_je_isto_kot_okno_na_strani_statistika(baza, net):
    """September ima 30 dni: okno zadnjih 30 dni na 1. 10. je natanko ta mesec.
    Dve poti do iste številke bi bili dve resnici."""
    c, _ = baza
    p = statistika.mesecno_porocilo(c, MESEC)
    okno = statistika.prevozniki(c, 90, net, danes=date(2026, 10, 1))
    assert (okno["od"], okno["do"]) == statistika.meje_meseca(MESEC)
    po_mesecu = {x["kljuc"]: x for x in p["prevozniki"]}
    assert {x["kljuc"] for x in okno["prevozniki"]} == {k for k, x in po_mesecu.items() if x["network"] == net}
    for x in okno["prevozniki"]:
        assert x["cilj"] == po_mesecu[x["kljuc"]]["cilj"], x["kljuc"]
        assert x["voznje"] == po_mesecu[x["kljuc"]]["voznje"]


def test_razredi_cela_so_100_in_se_ujemajo_z_deležem_v_5_min():
    """Bralec, ki sešteje razrede, mora dobiti 100 in „točno“ + „1–5 min“ =
    izpisani delež v 5 min (isto kot `preveri_skladnost.py`)."""
    rnd = random.Random(5)
    for _ in range(400):
        h = _hist(rnd, rnd.randint(1, 80))
        cilj = statistika.iz_histograma({str(m): c for m, c in h.items()})
        cela = statistika.razredi_cela(cilj)
        assert sum(cela.values()) == 100, (dict(h), cela)
        assert cela["tocno"] + cela["1-5"] == int(statistika.odstotek(cilj["v5min"])[:-2])
        assert cela["nad-15"] == int(statistika.odstotek(cilj["nad15"])[:-2])
        assert min(cela.values()) >= 0


# ---------------------------------------------------------------- pokritost

def test_pokritost_je_iz_podatkov_ne_iz_kode(baza):
    c, _ = baza
    p = statistika.mesecno_porocilo(c, MESEC)
    po = {x["kljuc"]: x for x in p["prevozniki"]}
    vlak, marprom, kranj, avtobus = (po["zeleznica|1161|vlak"], po["avtobus|marprom|avtobus"],
                                     po["avtobus|kranj|avtobus"], po["avtobus|1123|avtobus"])
    # Vlaki: izpad dveh dni je vrzel, ne začetek.
    assert vlak["dnevi_brez"] == ["2026-09-05", "2026-09-06"]
    assert vlak["dni_zajema"] == 28 and vlak["zajem_zacet"] is None
    assert p["omrezja"]["zeleznica"]["dnevi_brez"] == vlak["dnevi_brez"]
    # Marprom: dnevi pred zajemom so začetek, ne dnevi brez podatka.
    assert marprom["zajem_zacet"] == "2026-09-20"
    assert marprom["dni_zajema"] == 11 and marprom["dnevi_brez"] == []
    # Kranj: nedelja brez vrstice ni izpad.
    assert kranj["zajem_zacet"] == "2026-09-25"
    assert kranj["dni_zajema"] == 5 and kranj["dnevi_brez"] == []
    assert avtobus["dni_zajema"] == 30 and avtobus["zajem_zacet"] is None
    assert [statistika.primerljiv_mesec(x) for x in (vlak, avtobus, marprom, kranj)] == [
        True, True, False, False]


def test_pod_mejo_vzorca_ni_v_lestvici_in_je_noindex(baza, monkeypatch):
    c, _ = baza
    statistika.zamrzni_mesece(c, KONEC)
    monkeypatch.setattr(api, "_conn", lambda: c)
    stran = statistika.stran_mesec(c, MESEC)
    assert [x["ime"] for x in stran["primerljivi"]] == ["SŽ", "Arriva"]
    assert [x["ime"] for x in stran["premalo"]] == ["Marprom", "Kranj (MOK)"]
    assert stran["indeksiraj"] is True
    assert 'name="robots"' not in api.statistika_mesec(_zahteva("/statistika/" + MESEC), MESEC).body.decode()
    # Premalo dni zajema za celo omrežje: stran ostane, iskalnik je ne dobi.
    monkeypatch.setattr(statistika, "MIN_DNI_PRIMERJAVA", 99)
    html = api.statistika_mesec(_zahteva("/statistika/" + MESEC), MESEC).body.decode()
    assert 'name="robots" content="noindex' in html
    assert "/statistika/" + MESEC not in [p for p, _ in statistika.poti_za_iskalnik(c)]


# ---------------------------------------------------------------- zamrznitev

def test_mesec_se_zamrzne_sele_ko_je_zakljucen(baza):
    c, _ = baza
    assert statistika.zamrzni_mesece(c, date(2026, 9, 30)) == []       # mesec še teče
    assert statistika.zamrzni_mesece(c, date(2026, 10, 1)) == []       # zadnji dan še ni sklenjen
    assert statistika.zamrzni_mesece(c, KONEC) == [MESEC]
    with pytest.raises(ValueError):
        statistika.zamrzni_mesece(c, date(2026, 9, 30), mesec=MESEC)
    with pytest.raises(ValueError):
        statistika.zamrzni_mesece(c, KONEC, mesec="ni-mesec")


def test_zamrznitev_je_idempotentna_in_se_ne_preracuna(baza):
    c, _ = baza
    assert statistika.zamrzni_mesec(c, MESEC, zdaj=1_790_000_000)["zamrznjeno"].startswith("2026-09-2")
    vrstica = [tuple(r) for r in c.execute("SELECT podatki, zamrznjeno FROM stat_mesec")]
    assert len(vrstica) == 1 and vrstica[0][1] == 1_790_000_000
    # Dnevne vrstice se potem spremenijo (nova različica, popravek): mesec ne.
    c.execute("UPDATE stat_dan SET podatki = replace(podatki, '\"0\":', '\"1\":') WHERE vrsta = 'prevoznik'")
    c.commit()
    for danes in (KONEC, date(2026, 11, 3), date(2027, 1, 1)):
        assert statistika.zamrzni_mesece(c, danes) == []
    assert statistika.zamrzni_mesec(c, MESEC, zdaj=2_000_000_000) is None
    assert [tuple(r) for r in c.execute("SELECT podatki, zamrznjeno FROM stat_mesec")] == vrstica


def test_vsak_zaklucen_mesec_se_zamrzne_tudi_ko_koda_pride_pozneje(baza):
    """Objava po koncu meseca: nobena noč ni bila „1. v mesecu“, a ob prvem
    klicu se zamrznejo vsi zaključeni meseci; odprt in prazen ne."""
    c, _ = baza
    rnd = random.Random(2)
    for dan in ("2026-08-30", "2026-08-31"):
        _vstavi(c, dan, "zeleznica|1161|vlak", _vrstica(_hist(rnd, 100), 100))
    _vstavi(c, "2026-12-01", "zeleznica|1161|vlak", _vrstica(_hist(rnd, 100), 100))
    c.commit()
    assert statistika.zamrzni_mesece(c, date(2026, 12, 3)) == ["2026-08", "2026-09"]
    assert [m["mesec"] for m in statistika.seznam_mesecev(c)] == ["2026-09", "2026-08"]
    assert statistika.mesecno_porocilo(c, "2026-07") is None


def test_skladnost_ujame_razhajanje(baza):
    c, _ = baza
    statistika.zamrzni_mesece(c, KONEC)
    assert statistika.skladnost_meseca(c, MESEC) == []
    assert statistika.skladnost_meseca(c, "2026-07") == ["2026-07 ni zamrznjen"]
    # Zamrznjeno število, ki ni vsota dni.
    p = statistika.zamrznjen_mesec(c, MESEC)
    arriva = next(x for x in p["prevozniki"] if x["kljuc"] == "avtobus|1123|avtobus")
    arriva["cilj"]["n"] += 7
    c.execute("UPDATE stat_mesec SET podatki = ? WHERE mesec = ?", (json.dumps(p), MESEC))
    napake = statistika.skladnost_meseca(c, MESEC)
    assert any("dnevne vrstice" in n for n in napake), napake
    # Razredi, ki bi se sešli v 103 %.
    arriva["cilj"]["n"] -= 7
    p["omrezja"]["avtobus"]["cilj"]["razredi"]["tocno"] += 3
    c.execute("UPDATE stat_mesec SET podatki = ? WHERE mesec = ?", (json.dumps(p), MESEC))
    assert any("razredi dajo" in n for n in statistika.skladnost_meseca(c, MESEC))
    # Dnevne vrstice se po zamrznitvi spremenijo (npr. nova različica `stat_dan`).
    c.execute("DELETE FROM stat_mesec")
    statistika.zamrzni_mesec(c, MESEC)
    _vstavi(c, "2026-09-10", "zeleznica|1161|vlak", _vrstica(Counter({0: 5}), 100))
    napake = statistika.skladnost_meseca(c, MESEC)
    assert any("zeleznica|1161|vlak" in n for n in napake), napake


# ---------------------------------------------------------------- strani in API

def test_stran_meseca_je_200_z_vzorcem_in_casom_zamrznitve(baza, monkeypatch):
    c, _ = baza
    statistika.zamrzni_mesec(c, MESEC, zdaj=1_790_000_000)       # 2026-09-21
    monkeypatch.setattr(api, "_conn", lambda: c)
    odgovor = api.statistika_mesec(_zahteva("/statistika/" + MESEC), MESEC)
    assert odgovor.status_code == 200
    html = odgovor.body.decode()
    assert "September 2026" in html and "zamrznjeno 21. 9. 2026" in html
    n_vlaki = statistika.zamrznjen_mesec(c, MESEC)["omrezja"]["zeleznica"]["cilj"]["n"]
    assert f"Na {pristanek.stevilo(n_vlaki)}&nbsp;vožnjah" in html          # vzorec ob številki
    assert "zajem od 20. 9." in html and "še premalo za primerjavo" in html   # Marprom
    assert "zajema ni bilo 5.–6. 9." in html                                  # vlaki
    assert "SŽ (vlaki)" in html and "Arriva" in html
    from fastapi import HTTPException
    for slab in ("2026-11", "2026-13", "abc"):
        with pytest.raises(HTTPException) as e:
            api.statistika_mesec(_zahteva("/statistika/" + slab), slab)
        assert e.value.status_code == 404


def test_stran_meseca_za_agente_ima_tabelo_in_stevilke(baza, monkeypatch):
    """`Accept: text/markdown` pretvori HTML: številke morajo biti v besedilu
    in tabeli, ne samo v trakovih."""
    c, _ = baza
    statistika.zamrzni_mesec(c, MESEC)
    monkeypatch.setattr(api, "_conn", lambda: c)
    html = api.statistika_mesec(_zahteva("/statistika/" + MESEC), MESEC).body.decode()
    md = markdown.iz_html(html, "https://kajros.app/statistika/" + MESEC)
    p = statistika.zamrznjen_mesec(c, MESEC)
    vlak = p["omrezja"]["zeleznica"]["cilj"]
    assert "# September 2026" in md
    assert f"| SŽ (vlaki) | {statistika.odstotek(vlak['v5min'])}".replace(" ", " ") in md.replace(" ", " ")
    assert "še premalo za primerjavo" in md


def test_api_meseca_vrne_zamrznjeno_in_404(baza, monkeypatch):
    c, _ = baza
    statistika.zamrzni_mesec(c, MESEC)
    monkeypatch.setattr(api, "_conn", lambda: c)
    p = api.api_statistika_mesec(MESEC)
    assert p["mesec"] == MESEC and p["omrezja"]["zeleznica"]["cilj"]["n"] > 0
    assert p == statistika.zamrznjen_mesec(c, MESEC)
    assert [m["mesec"] for m in api.api_statistika_meseci()["meseci"]] == [MESEC]
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        api.api_statistika_mesec("2026-11")


def test_zemljevid_strani_ima_zamrznjen_mesec_in_pregled_povezavo(baza, monkeypatch):
    c, _ = baza
    assert statistika.poti_za_iskalnik(c) == []
    statistika.zamrzni_mesec(c, MESEC, zdaj=1_790_000_000)
    assert statistika.poti_za_iskalnik(c) == [("/statistika/" + MESEC, "2026-09-21")]
    monkeypatch.setattr(api, "_conn", lambda: c)
    html = api.statistika_pregled(_zahteva("/statistika")).body.decode()
    assert "Kakšen je bil september 2026?" in html and "/statistika/" + MESEC in html


def test_mesecne_poti_so_samo_get():
    """Nova pot ne sme biti pisalna (`test_pisalne_poti_so_nastete`)."""
    poti = [(r.path, r.methods) for r in api.app.routes
            if "statistika" in getattr(r, "path", "") and "mesec" in getattr(r, "path", "")]
    assert poti and all(m <= {"GET", "HEAD"} for _, m in poti)


# ---------------------------------------------------------------- nočno opravilo in ukaz

def _datoteka(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "k.sqlite")
    c = db.connect()
    db.init(c)
    _napolni(c)
    c.close()


def _brez_drugih_opravil(monkeypatch):
    for modul, ime in ((stats, "refresh_summaries"), (server.opazovano, "dopolni"),
                       (server.straza, "dopolni")):
        monkeypatch.setattr(modul, ime, lambda *a, **k: [])


def test_nocno_opravilo_zamrzne_mesec(tmp_path, monkeypatch):
    _datoteka(tmp_path, monkeypatch)
    _brez_drugih_opravil(monkeypatch)
    server._povzetki()
    c = db.connect()
    assert [r[0] for r in c.execute("SELECT mesec FROM stat_mesec")] == [MESEC]
    server._povzetki()                                    # drugič: nič novega, nič napake
    assert c.execute("SELECT COUNT(*) FROM stat_mesec").fetchone()[0] == 1
    assert json.loads(db.get_meta(c, "nocno") or "{}").get("mesecno_porocilo") is None


def test_napaka_zamrznitve_se_zapise_in_ne_ustavi_ostalih_opravil(tmp_path, monkeypatch):
    _datoteka(tmp_path, monkeypatch)
    _brez_drugih_opravil(monkeypatch)
    klici = []
    monkeypatch.setattr(server.opazovano, "dopolni", lambda c: klici.append("opazovano") or [])

    def pade(*a, **k):
        raise RuntimeError("baza se je zaprla")

    monkeypatch.setattr(statistika, "zamrzni_mesece", pade)
    server._povzetki()
    assert klici == ["opazovano"]
    korak = json.loads(db.get_meta(db.connect(), "nocno"))["mesecno_porocilo"]
    assert korak["zapored"] == 1 and "baza se je zaprla" in korak["napaka"]


def test_ukaz_mesec_zamrzne_in_odkloni_nezakljucen(tmp_path, monkeypatch, capsys):
    _datoteka(tmp_path, monkeypatch)
    cli.cmd_mesec(argparse.Namespace(mesec=None))
    izpis = capsys.readouterr().out
    assert f"zamrznjeno {MESEC}" in izpis and MESEC in izpis.splitlines()[-1]
    cli.cmd_mesec(argparse.Namespace(mesec=None))
    assert "nič novega" in capsys.readouterr().out
    with pytest.raises(SystemExit) as e:
        cli.cmd_mesec(argparse.Namespace(mesec="2099-01"))
    assert "še ni zaključen" in str(e.value)
