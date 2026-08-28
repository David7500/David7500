"""Enotni testi čistih funkcij.

Namenoma brez omrežja in brez baze na disku: vse, kar se da preveriti brez
zajema, naj se preveri hitro. Poizvedbe nad shemo so v `test_poizvedbe.py`.

    ./venv/bin/python -m pytest tests/ -q
"""
from __future__ import annotations

from sztrack import weather
from sztrack.alerts import parse_delay_text
from sztrack.collector import is_zero_blip
from sztrack.journey import _fold


# ---------------------------------------------------------------- prehodne nicle

def _row(arr, dep=None):
    """Posnema sqlite3.Row: dostop po imenu stolpca."""
    return {"delay_arr": arr, "delay_dep": dep if dep is not None else arr}


def test_nicla_po_veliki_zamudi_je_sumljiva():
    # 20 minut zamude, cez pol minute tocno -- fizikalno nemogoce.
    assert is_zero_blip(_row(1200), _row(1200), 0, 0)


def test_nicla_po_majhni_zamudi_ni_sumljiva():
    # Dve minuti zamude, ki izgineta, so vsakdanji dogodek.
    assert not is_zero_blip(_row(120), _row(120), 0, 0)


def test_potrjena_nicla_se_sprejme():
    # Ce je ze prejsnji zapis v dnevniku govoril niclo, to ni blip, ampak
    # potrditev -- sicer bi `run` obtical na stari vrednosti za vedno.
    assert not is_zero_blip(_row(1200), _row(0), 0, 0)


def test_brez_prejsnje_vrednosti_ni_blipa():
    assert not is_zero_blip(None, None, 0, 0)


def test_nenicelna_vrednost_ni_blip():
    assert not is_zero_blip(_row(1200), _row(1200), 60, 60)


def test_obe_vrednosti_prazni_nista_blip():
    # Manjkajoc podatek ni isto kot porocana nicla.
    assert not is_zero_blip(_row(1200), _row(1200), None, None)


# ---------------------------------------------------------------- besedilo obvestil

def test_razclenitev_navadne_zamude():
    got = parse_delay_text("Vlak LPV 2616 ima zamudo 5 min ob prihodu na postajo Postojna.")
    assert got == {"train_no": "LPV 2616", "delay_min": 5, "station": "Postojna",
                   "severe": False, "event": "prihod"}


def test_razclenitev_izjemne_zamude():
    got = parse_delay_text(
        "Vlak LP 3224 ima izjemno zamudo 42 min ob prihodu na postajo Ljubljana Rakovnik.")
    assert got["severe"] is True
    assert got["station"] == "Ljubljana Rakovnik"      # vecbesedno ime
    assert got["delay_min"] == 42


def test_razclenitev_brez_koncne_pike():
    got = parse_delay_text("Vlak RG 1604 ima zamudo 8 min ob prihodu na postajo Zagorje")
    assert got is not None and got["station"] == "Zagorje"


def test_neznana_oblika_vrne_none():
    # Tiho ugibanje bi bilo slabse od priznanja, da oblike ne poznamo.
    assert parse_delay_text("Vlak vozi po nadomestni progi.") is None
    assert parse_delay_text("") is None


# ---------------------------------------------------------------- iskanje postaj

def test_zlozitev_odstrani_sumnike():
    assert _fold("Šentjur") == "sentjur"
    assert _fold("Bohinjska Bistrica") == "bohinjska bistrica"
    assert _fold("Ljubljana Črnuče") == "ljubljana crnuce"


# ---------------------------------------------------------------- stopnja razmer

def test_mirno_vreme_je_nic():
    s = weather.severity({"temp_c": 18.0, "precip_mm": 0.0, "snowfall_cm": 0.0,
                          "wind_gust_kmh": 10.0, "code": 0})
    assert s["score"] == 0 and s["label"] == "mirne"


def test_sneg_in_mraz_se_sestejeta():
    s = weather.severity({"temp_c": -8.0, "precip_mm": 0.0, "snowfall_cm": 3.5,
                          "wind_gust_kmh": 10.0, "code": 73})
    assert {p["what"] for p in s["parts"]} == {"sneg", "mraz"}
    assert s["score"] == 9 and s["label"] == "hude"


def test_stopnja_je_omejena_na_deset():
    s = weather.severity({"temp_c": -10.0, "precip_mm": 30.0, "snowfall_cm": 10.0,
                          "wind_gust_kmh": 120.0, "code": 95})
    assert s["score"] == 10


def test_barva_sledi_stopnji():
    # Semafor mora biti monoton: vsaka stopnja svoja barva, brez preskokov.
    seen = [weather.severity_color(n) for n in (0, 2, 5, 9)]
    assert seen == [weather.SEVERITY_STYLE[k] for k in weather.SEVERITY_ORDER]
