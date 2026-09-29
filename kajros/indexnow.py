"""IndexNow: iskalnikom povemo, katere strani obstajajo, ne čakamo, da jih najdejo.

Bing (z njim iskanje v ChatGPT, Copilotu in DuckDuckGo), Yandex, Seznam,
Naver in Yep sprejmejo seznam naslovov z enim klicem, brez računa. Dokaz, da
naslove pošilja lastnik, je ključ na `/<ključ>.txt` (`config.INDEXNOW_KLJUC`,
javen po zasnovi). Google IndexNow ne podpira; zanj je Search Console.

Pošilja se ob objavi na arwen (`deploy/posodobi.sh`, `kajros indexnow
--stanje`) in samo, kadar se je nabor naslovov spremenil -- ne iz strežnika:
ta ne ve, ali teče na `kajros.app` ali v razvoju, kjer je `BASE_URL` isti.

**Prvi dan je ključ „v preverjanju“** (izmerjeno 29. 9. 2026): klic s 100
naslovi dobi 202, s 500 pa 403 `SiteVerificationNotCompleted`. Stanje se ob
neuspehu ne zapiše, zato naslednja objava poskusi znova.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
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


def poslji(naslovi: list[str]) -> list[tuple[int, str]]:
    """Pošlje naslove v kosih po `NAJVEC`. Vrne (koda, telo) za vsak kos.

    200 in 202 sta uspeh (202 = ključ se še preverja). 403 pomeni, da ključa
    ni na strani ali da preverjanje še ni končano -- telo pove, kaj.
    """
    gost = urlsplit(config.BASE_URL).hostname
    odgovori = []
    for i in range(0, len(naslovi), NAJVEC):
        r = requests.post(TOCKA, timeout=60, json={
            "host": gost,
            "key": config.INDEXNOW_KLJUC,
            "keyLocation": f"{config.BASE_URL}/{config.INDEXNOW_KLJUC}.txt",
            "urlList": naslovi[i:i + NAJVEC],
        })
        odgovori.append((r.status_code, r.text[:300]))
    return odgovori


def odtis(naslovi: list[str]) -> str:
    """Odtis nabora: isti naslovi v drugem vrstnem redu so isti nabor."""
    return hashlib.sha256("\n".join(sorted(naslovi)).encode()).hexdigest()


def poslji_ce_spremenjeno(naslovi: list[str], stanje: Path) -> str:
    """Pošlje, če se nabor razlikuje od zadnjega uspešno poslanega.

    Vrne kratko poročilo za dnevnik objave.
    """
    novo = odtis(naslovi)
    if stanje.exists() and stanje.read_text().strip() == novo:
        return f"nabor {len(naslovi)} naslovov nespremenjen, ne pošiljam"
    odgovori = poslji(naslovi)
    if all(k in (200, 202) for k, _ in odgovori):
        stanje.write_text(novo + "\n")
        return f"poslanih {len(naslovi)} naslovov: {[k for k, _ in odgovori]}"
    return f"NI POSLANO ({len(naslovi)} naslovov): {odgovori}"
