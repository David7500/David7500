"""Koliko časa hodiš. Ena funkcija, dva vira — nihče drug ne ve, kateri je bil.

**Zakaj ne zračna razdalja s faktorjem.** Izmerjeno na 1 080 poteh (naključne
točke po Sloveniji do njihovih najbližjih postajališč, primerjava s pravo
pešpotjo): mediana obvoza 1,43, p75 1,83, p90 2,63, **največji 7,86**. Obvoz ni
šum, ampak ovire — Sava, proga, avtocesta. Postajališče 300 m stran po zraku je
lahko 1 400 m hoje. Ena konstanta ne more biti hkrati varna in uporabna:
1,45 podceni pot v 48 % primerov, 2,63 pa bi iz 500 m naredila 15 minut.

**Zakaj svoj OSRM in ne javni.** Javni `router.project-osrm.org` bi ob vsakem
iskanju izvedel, kje potnik stoji in kam gre. Je tudi izrecno „samo za demo".
Program je odprta koda in naš strežnik vrne **isto pot do decimalke** (412,8 m
na preizkusni poti) — omejitev je bila gostiteljeva, ne programova.
Postavitev: `deploy/osrm.sh`.

**Zakaj je hitrost samo ena.** OSRM-ov peš profil hodi 5,00 km/h (izmerjeno na
1 080 poteh), kar je natanko hitrost, s katero računa zasilna pot. Vira se
torej razlikujeta v dolžini poti, ne v hitrosti hoje.
"""

from __future__ import annotations

import time

import requests

from . import config, geo

#: Hitrost hoje. Ista v obeh virih -- glej opombo v glavi modula.
HITROST_MS = 5000 / 3600

#: Zasilni faktor obvoza, kadar usmerjevalnika ni. To je **p75** izmerjene
#: porazdelitve, ne mediana: brez usmerjevalnika ne vemo, kako dolga je pot, in
#: takrat velja isto pravilo kot pri budilki -- potnik ne sme zamuditi, raje
#: kaj rezerve. Z mediano (1,43) bi bila vsaka druga hoja podcenjena in potnik
#: bi avtobus zamudil; s p75 se v najslabšem primeru pokaže malo poznejša
#: povezava, kar je nesreča drugega reda.
FAKTOR = 1.85

#: Hoja je na kritični poti odgovora, ne postranski vir. Izmerjeno je matrika
#: 1 x 70 ciljev 32 ms, torej je ta meja stokratna rezerva -- postavljena je
#: proti obvisenju, ne proti počasnosti.
_TIMEOUT_S = 3.0

#: Ko usmerjevalnik pade, ne poskušamo znova ob vsaki zahtevi: dva klica na
#: iskanje x 3 s pomenita 6 s čakanja na odgovor, ki bo tako ali tako zasilen.
_NAPAKA_MIRUJ_S = 30.0
_zadnja_napaka = 0.0

OSRM = "osrm"
ZRAK = "zrak"


def doseg_zracno(sekund: float) -> float:
    """Polmer v metrih, ki ga v danem času ni mogoče preseči — za predfilter.

    Faktorja tu **ne sme biti**. Zračna črta je vedno krajša ali enaka pravi
    poti, zato ta polmer ne izpusti ničesar dosegljivega; z faktorjem bi tiho
    odrezal postajališča, ki so v resnici v dosegu, in tega ne bi nihče opazil.
    """
    return sekund * HITROST_MS


def _zracno(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    return round(geo.haversine(lat1, lon1, lat2, lon2) * FAKTOR / HITROST_MS)


def _tabela(lat: float, lon: float, cilji: list[tuple[float, float]],
            smer: str) -> list[int | None] | None:
    """Klic OSRM; `None`, kadar vira ni ali ni odgovoril."""
    global _zadnja_napaka
    if not config.OSRM_URL:
        return None
    if time.monotonic() - _zadnja_napaka < _NAPAKA_MIRUJ_S:
        return None

    # Točka je vedno koordinata 0; cilji ji sledijo.
    koord = ";".join([f"{lon:.6f},{lat:.6f}"]
                     + [f"{b:.6f},{a:.6f}" for a, b in cilji])
    # Smer je pomembna: peš profil sicer ne pozna enosmernih cest, a `oneway:foot`
    # obstaja in simetrije ne gre privzeti, kadar je ni treba.
    kljuc = "sources" if smer == "od" else "destinations"
    try:
        r = requests.get(f"{config.OSRM_URL}/table/v1/foot/{koord}",
                         params={kljuc: "0", "annotations": "duration"},
                         timeout=_TIMEOUT_S)
        r.raise_for_status()
        vrstice = r.json()["durations"]
        sekunde = vrstice[0] if smer == "od" else [v[0] for v in vrstice]
    except Exception:
        _zadnja_napaka = time.monotonic()
        return None
    # Prva je pot do sebe; ostale so cilji po vrsti.
    sekunde = sekunde[1:]
    if len(sekunde) != len(cilji):
        _zadnja_napaka = time.monotonic()
        return None
    return [None if s is None else round(s) for s in sekunde]


def matrika(lat: float, lon: float, cilji: list[tuple[float, float]],
            smer: str = "od") -> tuple[list[int | None], str]:
    """Sekunde hoje med točko in vsakim ciljem, ter vir številke.

    `smer="od"` je od točke do ciljev (pot na postajo), `"do"` obratno (pot s
    postaje na cilj). Vir je `"osrm"` ali `"zrak"` in mora priti na zaslon:
    zasilna številka je ocena in se tako tudi imenuje.

    `None` pri posameznem cilju pomeni, da tja peš ni poti.
    """
    if not cilji:
        return [], ZRAK
    sekunde = _tabela(lat, lon, cilji, smer)
    if sekunde is not None:
        return sekunde, OSRM
    return [_zracno(lat, lon, a, b) for a, b in cilji], ZRAK


def sekunde(lat1: float, lon1: float, lat2: float, lon2: float,
            smer: str = "od") -> tuple[int | None, str]:
    """Ena pot; za več ciljev vzemi `matrika()`, ki jih zna v enem klicu."""
    vrsta, vir = matrika(lat1, lon1, [(lat2, lon2)], smer)
    return vrsta[0], vir
