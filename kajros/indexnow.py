"""IndexNow: iskalnikom povemo, katere strani obstajajo, ne čakamo, da jih najdejo.

Bing (z njim iskanje v ChatGPT, Copilotu in DuckDuckGo), Yandex, Seznam,
Naver in Yep sprejmejo seznam naslovov z enim klicem, brez računa. Dokaz, da
naslove pošilja lastnik, je ključ na `/<ključ>.txt` (`config.INDEXNOW_KLJUC`,
javen po zasnovi). Google IndexNow ne podpira; zanj je Search Console.

Pošilja se ročno (`kajros indexnow`), ne samodejno: strežnik ne ve, ali teče
na `kajros.app` ali v razvoju, kjer je `BASE_URL` isti, in iskalniku ni treba
vsak dan povedati istih dva tisoč naslovov. Pošlji po objavi, ki doda ali
preimenuje strani.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

import requests

from . import config

TOCKA = "https://api.indexnow.org/indexnow"
#: Največ naslovov v enem klicu po specifikaciji.
NAJVEC = 10_000

_LOC = re.compile(r"<loc>([^<]+)</loc>")


def naslovi_iz_zemljevida(url: str | None = None) -> list[str]:
    """Naslovi iz živega zemljevida strani -- isti, kot jih vidi iskalnik."""
    r = requests.get(url or f"{config.BASE_URL}/sitemap.xml", timeout=120)
    r.raise_for_status()
    return _LOC.findall(r.text)


def poslji(naslovi: list[str]) -> list[int]:
    """Pošlje naslove v kosih po `NAJVEC`. Vrne kode odgovorov.

    200 in 202 sta uspeh (202 = ključ se še preverja). 403 pomeni, da
    iskalnik ključa na strani ni našel -- objava s tem ključem še ni živa.
    """
    gost = urlsplit(config.BASE_URL).hostname
    kode = []
    for i in range(0, len(naslovi), NAJVEC):
        r = requests.post(TOCKA, timeout=60, json={
            "host": gost,
            "key": config.INDEXNOW_KLJUC,
            "keyLocation": f"{config.BASE_URL}/{config.INDEXNOW_KLJUC}.txt",
            "urlList": naslovi[i:i + NAJVEC],
        })
        kode.append(r.status_code)
    return kode
