"""Kazalo naslovov: gradnja iz izvoza OSM in iskanje po njem.

Izvoz je tu droben in napisan na roko -- preverja se ravnanje (dvojniki,
kraj brez naslova, razvrščanje po bližini), ne podatki.
"""
from __future__ import annotations

import json

import pytest

from kajros import config, naslovi


def _tocka(lat, lon, **lastnosti):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": lastnosti}


@pytest.fixture()
def kazalo(tmp_path, monkeypatch):
    zapisi = [
        _tocka(46.0569, 14.5058, place="city", name="Ljubljana"),
        _tocka(46.2397, 14.3556, place="town", name="Kranj"),
        _tocka(46.0700, 14.5300, place="village", name="Hrastje"),
        _tocka(46.0515, 14.5063, **{"addr:street": "Trubarjeva cesta",
                                    "addr:housenumber": "5", "addr:city": "Ljubljana",
                                    "addr:postcode": "1000"}),
        # Isti naslov še enkrat brez kraja (stavba in točka v OSM).
        _tocka(46.0516, 14.5064, **{"addr:street": "Trubarjeva cesta",
                                    "addr:housenumber": "5"}),
        _tocka(46.2400, 14.3560, **{"addr:street": "Trubarjeva ulica",
                                    "addr:housenumber": "5", "addr:city": "Kranj"}),
        _tocka(46.0660, 14.5420, name="BTC City", shop="mall"),
        # Postaja ni točka kazala: postaje ima stran svoje.
        _tocka(46.0580, 14.5100, name="Ljubljana potniška", railway="station",
               public_transport="station"),
    ]
    vir = tmp_path / "izbor.geojsonseq"
    vir.write_text("".join("\x1e" + json.dumps(z) + "\n" for z in zapisi), encoding="utf-8")
    cilj = tmp_path / "naslovi.sqlite"
    izid = naslovi.zgradi(vir, cilj, javi=lambda *_: None)
    monkeypatch.setattr(config, "okolje",
                        lambda ime, privzeto=None: str(cilj) if ime == "NASLOVI" else privzeto)
    naslovi._POVEZAVA.clear()
    yield izid
    naslovi._POVEZAVA.clear()


def test_gradnja_steje_in_zavrze_postaje(kazalo):
    assert kazalo["krajev"] == 3
    assert kazalo["tock"] == 1, "postaja ne sme v kazalo"


def test_blizji_naslov_prvi(kazalo):
    """„Trubarjeva 5" je v obeh mestih; kdor išče iz Ljubljane, misli
    ljubljansko -- in obratno."""
    lj = naslovi.isci("trubarjeva 5", (46.0569, 14.5058))
    kr = naslovi.isci("trubarjeva 5", (46.2397, 14.3556))
    assert lj[0]["pod"].endswith("Ljubljana")
    assert kr[0]["pod"].endswith("Kranj")


def test_dvojnik_naslova_je_en_zadetek(kazalo):
    z = [x for x in naslovi.isci("trubarjeva cesta 5", (46.0569, 14.5058))
         if x["vrsta"] == "naslov"]
    assert len(z) == 1


def test_tocka_brez_kraja_dobi_mesto_okrog(kazalo):
    """BTC nima kraja v naslovu in najbližja vas je Hrastje; človek pa reče
    „BTC v Ljubljani"."""
    z = naslovi.isci("btc")
    assert z[0]["ime"] == "BTC City" and z[0]["pod"] == "Ljubljana"


def test_brez_stevilke_ne_isce_naslovov(kazalo):
    """Ulica brez številke je ulica, ne sto naslovov na njej."""
    assert all(x["vrsta"] != "naslov" for x in naslovi.isci("trubarjeva"))


def test_brez_kazala_prazno(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "okolje",
                        lambda ime, privzeto=None: str(tmp_path / "ni.sqlite")
                        if ime == "NASLOVI" else privzeto)
    naslovi._POVEZAVA.clear()
    assert naslovi.isci("trubarjeva 5") == []
