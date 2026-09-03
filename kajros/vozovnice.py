"""Povezava na nakup vozovnice pri SŽ.

Dve poti, ker sta dve možnosti:

* **Z relacijo** -- `potniski.sz.si/vozni-redi-results/` sprejme `GET` z
  `entry-station` in `exit-station`. To sta **SŽ številki postaje**, ki sta
  UIC koda brez državne predpone `79` (Ljubljana UIC 7942300 -> `42300`).
  Potrjeno na naslovu, ki ga je uporabnik prilepil iz svojega brskalnika.
* **Brez relacije** -- `eshop.sz.si`. Obrazec trgovine je `POST` z internimi
  ID-ji in `GET` parametri se tiho ignorirajo (preizkušeno 3. 9. 2026).

Zakaj samo peščica postaj: kod ni v GTFS in `potniski.sz.si` je za
Cloudflarom, tako da seznama ni mogoče prebrati (403 tudi iz brskalnika brez
zaslona). Spodnje so iz odprtega nabora postaj `trainline-eu/stations` prek
polja `uic`. **Preverjena je samo Ljubljana**, ker je edina, za katero imamo
naslov iz prve roke; ostale so iz nabora in jih je treba potrditi s klikom.
Postaja brez kode ni napaka -- takrat gre povezava na trgovino brez relacije,
kar je slabše, a ne narobe.
"""
from __future__ import annotations

from .journey import _fold

#: ime postaje (kot v `station.name`) -> SŽ številka postaje
KODE: dict[str, str] = {
    "Borovnica": "44004",
    "Celje": "43100",
    "Dobova": "42001",
    "Divača": "44200",
    "Jesenice": "42400",
    "Koper": "44352",
    "Kranj": "42307",
    "Lesce-Bled": "42313",
    "Ljubljana": "42300",
    "Logatec": "44006",
    "Maribor": "43400",
    "Metlika": "42502",
    "Murska Sobota": "43704",
    "Pivka": "44100",
    "Postojna": "44009",
    "Pragersko": "43300",
    "Rakek": "44008",
    "Sežana": "44500",
    "Zidani Most": "42200",
}

_PO_IMENU = {_fold(k): v for k, v in KODE.items()}

TRGOVINA = "https://eshop.sz.si/"


def koda(ime: str | None) -> str | None:
    return _PO_IMENU.get(_fold(ime)) if ime else None


def povezava(od: str | None, do: str | None, datum: str | None) -> dict:
    """URL za nakup in ali nosi relacijo.

    `datum` je `YYYY-MM-DD`; SŽ ga pričakuje kot `DD.MM.YYYY`.
    """
    a, b = koda(od), koda(do)
    if not (a and b and datum):
        return {"url": TRGOVINA, "z_relacijo": False}
    try:
        l, m, d = datum.split("-")
    except ValueError:
        return {"url": TRGOVINA, "z_relacijo": False}
    return {
        "url": ("https://potniski.sz.si/vozni-redi-results/"
                f"?action=timetables_search&current-language=sl"
                f"&departure-date={d}.{m}.{l}"
                f"&entry-station={a}&exit-station={b}&remember=on"),
        "z_relacijo": True,
    }
