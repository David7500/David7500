"""Testi izračuna hoje: kaj se zgodi z usmerjevalnikom in kaj brez njega.

Pravega OSRM tu ni — testi ne smejo biti odvisni od tega, ali na tem računalniku
teče vsebnik. Preverja se **ravnanje**: kateri vir se uporabi, kako se prebere
odgovor in kaj se zgodi ob izpadu.
"""
from __future__ import annotations

import pytest

from kajros import config, geo, hoja


@pytest.fixture(autouse=True)
def brez_spomina_na_napako():
    """Varovalka po napaki je modulna; brez tega bi en test okužil naslednjega."""
    hoja._zadnja_napaka = 0.0
    yield
    hoja._zadnja_napaka = 0.0


class _Odgovor:
    def __init__(self, telo):
        self._telo = telo

    def raise_for_status(self):
        pass

    def json(self):
        return self._telo


def test_doseg_zracno_je_spodnja_meja():
    """Predfilter ne sme uporabiti faktorja obvoza.

    Prava pot je vedno daljša ali enaka zračni črti. Če bi polmer množili s
    faktorjem, bi tiho izpustil postajališča, ki so v resnici v dosegu — in
    tega ne bi nihče opazil, ker manjkajočega odgovora ni videti.
    """
    for sekund in (300, 900, 1500):
        assert hoja.doseg_zracno(sekund) == pytest.approx(sekund * hoja.HITROST_MS)
    # 25 minut pri 5 km/h je 2 083 m -- toliko kandidatov gre v matriko.
    assert hoja.doseg_zracno(25 * 60) == pytest.approx(2083, abs=1)


def test_brez_usmerjevalnika_zracna_razdalja_krat_faktor(monkeypatch):
    monkeypatch.setattr(config, "OSRM_URL", "")
    sek, vir = hoja.matrika(46.0698, 14.5747, [(46.0713, 14.5766)])
    assert vir == hoja.ZRAK
    zrak = geo.haversine(46.0698, 14.5747, 46.0713, 14.5766)
    assert sek[0] == round(zrak * hoja.FAKTOR / hoja.HITROST_MS)


def test_faktor_je_p75_in_ne_mediana():
    """Brez usmerjevalnika velja pravilo budilke: potnik ne sme zamuditi.

    Mediana izmerjenega obvoza je 1,43; s tako oceno bi bila vsaka druga hoja
    prekratka. p75 (1,83) se zaokroži navzgor.
    """
    assert hoja.FAKTOR > 1.43


def test_bere_matriko_od_tocke(monkeypatch):
    poslano = {}

    def fake_get(url, params=None, timeout=None):
        poslano["url"], poslano["params"] = url, params
        return _Odgovor({"durations": [[0, 120, 300]]})

    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get", fake_get)
    sek, vir = hoja.matrika(46.0, 14.5, [(46.01, 14.51), (46.02, 14.52)])
    assert (sek, vir) == ([120, 300], hoja.OSRM)
    # Točka je koordinata 0 in je vir; pot do sebe se zavrže.
    assert poslano["params"]["sources"] == "0"
    assert poslano["url"].startswith("http://x:5000/table/v1/foot/14.500000,46.000000;")


def test_bere_matriko_do_tocke(monkeypatch):
    """Smer „s postaje na cilj" je stolpec, ne vrstica.

    Peš profil enosmernih cest večinoma ne pozna, a `oneway:foot` obstaja;
    simetrije ne privzemamo, kadar je ni treba.
    """
    poslano = {}

    def fake_get(url, params=None, timeout=None):
        poslano["params"] = params
        return _Odgovor({"durations": [[0], [240], [60]]})

    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get", fake_get)
    sek, vir = hoja.matrika(46.0, 14.5, [(46.01, 14.51), (46.02, 14.52)], smer="do")
    assert (sek, vir) == ([240, 60], hoja.OSRM)
    assert poslano["params"]["destinations"] == "0"


def test_nedosegljiv_cilj_je_none(monkeypatch):
    """`null` v matriki pomeni, da tja peš ni poti — ne nič sekund."""
    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get",
                        lambda *a, **k: _Odgovor({"durations": [[0, None, 90]]}))
    sek, vir = hoja.matrika(46.0, 14.5, [(46.01, 14.51), (46.02, 14.52)])
    assert (sek, vir) == ([None, 90], hoja.OSRM)


def test_ob_napaki_zasilna_pot(monkeypatch):
    def pade(*a, **k):
        raise OSError("ni povezave")

    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get", pade)
    sek, vir = hoja.matrika(46.0, 14.5, [(46.01, 14.51)])
    assert vir == hoja.ZRAK
    assert sek[0] > 0


def test_po_napaki_ne_poskusa_takoj_znova(monkeypatch):
    """Dva klica na iskanje krat 3 s meje bi pomenila 6 s čakanja na odgovor,
    ki bo tako ali tako zasilen."""
    klici = []

    def pade(*a, **k):
        klici.append(1)
        raise OSError("ni povezave")

    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get", pade)
    hoja.matrika(46.0, 14.5, [(46.01, 14.51)])
    hoja.matrika(46.0, 14.5, [(46.01, 14.51)])
    assert len(klici) == 1


def test_okrnjen_odgovor_ni_tiho_sprejet(monkeypatch):
    """Matrika s premalo stolpci bi zamaknila vsa postajališča za eno."""
    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get",
                        lambda *a, **k: _Odgovor({"durations": [[0, 120]]}))
    sek, vir = hoja.matrika(46.0, 14.5, [(46.01, 14.51), (46.02, 14.52)])
    assert vir == hoja.ZRAK
    assert len(sek) == 2


def test_prazen_seznam_ne_kliche_niti_usmerjevalnika(monkeypatch):
    def pade(*a, **k):
        raise AssertionError("brez ciljev ni česa vprašati")

    monkeypatch.setattr(config, "OSRM_URL", "http://x:5000")
    monkeypatch.setattr(hoja.requests, "get", pade)
    assert hoja.matrika(46.0, 14.5, []) == ([], hoja.ZRAK)
