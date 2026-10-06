"""Kje ustavi nadomestni avtobus SŽ na posamezni železniški postaji.

Vozni red tega ne pove: nadomestne vožnje v GTFS stojijo na legi železniške
postaje (18 od 22 postajališč, izmerjeno 6. 10. 2026), obvestila pa lokacijo
napišejo samo za Ljubljano. Za vse proge jo SŽ objavlja na svoji strani
(`VIR`: 274 postaj na 19 progah) -- to je edini vir in ga drugi nimajo.

Posnetek strani je `nadomestna_postajalisca.json` ob tem modulu, naredi ga
`scripts/nadomestna_postajalisca.py`; lega je samo, kjer je prestala preverjanje
z razdaljo do postaje. Seznam se ne spreminja iz dneva v dan, zato datoteka v
gitu, ne zajem: SŽ ga je nazadnje popravila ob selitvi ljubljanske avtobusne
postaje (24. 8. 2026).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .naslovi import fold

VIR = "https://potniski.sz.si/vozni-redi/lokacije-postankov-nadomestnih-prevozov/"
DATOTEKA = Path(__file__).with_name("nadomestna_postajalisca.json")

#: Imena, ki jih SŽ na tej strani piše drugače kot vozni red (levo stran SŽ).
PREIMENOVANJA = {"hrplje kozina": "hrpelje kozina"}


def kljuc(ime: str) -> str:
    """Isti ključ za „Lesce Bled“ (SŽ), „Lesce-Bled“ (vozni red) in
    „Lavrica(Železniški)“ (postajališče nadomestne vožnje)."""
    k = re.sub(r"\(\s*zelezniski\s*\)", " ", fold(ime))
    k = re.sub(r"[^a-z0-9]+", " ", k).strip()
    return PREIMENOVANJA.get(k, k)


@lru_cache(maxsize=1)
def _vse() -> dict[str, dict]:
    try:
        p = json.loads(DATOTEKA.read_text())
    except FileNotFoundError:
        return {}
    return {kljuc(x["postaja"]): {"opis": x["opis"], "lat": x["lat"], "lon": x["lon"],
                                  "pregledano": p["pregledano"]}
            for x in p["postaje"]}


def za_postajo(ime: str | None) -> dict | None:
    """`{opis, lat, lon, pregledano}` za postajo ali None. `lat`/`lon` sta
    None, kadar točka s strani SŽ ni prestala preverjanja -- opis ostane."""
    return _vse().get(kljuc(ime)) if ime else None


def je_nadomestni(row: dict) -> bool:
    return row.get("mode") == "bus" and row.get("network") == "zeleznica"


def dopolni(rows: list[dict], postaja: str | None) -> None:
    """`nadomestni_postanek` k vrsticam nadomestnih voženj, ki ustavijo na
    `postaja` (tabla, iskalnik): potnik mora vedeti, kam iti, ne le kdaj."""
    p = za_postajo(postaja)
    if not p:
        return
    for r in rows:
        if je_nadomestni(r):
            r["nadomestni_postanek"] = p
