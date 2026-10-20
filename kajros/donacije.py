"""Donacije s Ko-fi -- pot, ki piše iz zahteve tujega strežnika.

Ko-fi za vsako plačilo pošlje `POST` na naš naslov (webhook, nastavitev na
ko-fi.com/manage/webhooks): obrazec z enim poljem `data`, v njem JSON.
Bralnega API-ja Ko-fi nima, stran ko-fi.com/kajros pa je za Cloudflarom
(curl 20. 10. 2026: 403) -- zato je to edina pot do zbranega zneska, ki ne
rabi brskalnika.

**Neznanec ne sme nič.** Edino, kar loči plačilo od kogarkoli, ki pozna
naslov, je `verification_token`, ki ga Ko-fi pokaže v istih nastavitvah.
Napačen ali manjkajoč: 403. Brez nastavljenega žetona poti ni (404).

**Hranimo samo znesek, valuto in čas.** Ko-fi pošlje tudi ime, e-naslov in
sporočilo darovalca. Ne shranimo jih, ker jih nič na strani ne rabi --
potrdilo, vračilo in stik z darovalcem tečejo pri Ko-fi.

Ko-fi pošiljanje ponovi, kadar ne dobi 200, zato isto plačilo
(`kofi_transaction_id`) ne šteje dvakrat. **Vračil Ko-fi ne javlja**: vrnjena
donacija ostane v vsoti, dokler je skrbnik ne izbriše iz baze.
"""
from __future__ import annotations

import hmac
import json
import re
import sqlite3
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs

from . import config

#: Naslov, ki se vpiše v nastavitve Ko-fi: `https://kajros.app/donacije/ko-fi`.
#: Točno ta: `www.` in `http://` vrneta preusmeritev 308 (`api._en_naslov`),
#: in ali ji Ko-fi sledi, ni izmerjeno.
POT = "/donacije/ko-fi"

SHEMA = """
-- Plačila s Ko-fi. Brez imena, e-naslova in sporočila darovalca.
CREATE TABLE IF NOT EXISTS donacija (
    id       TEXT    PRIMARY KEY,       -- kofi_transaction_id
    placano  INTEGER NOT NULL,          -- epoha, čas plačila po Ko-fi
    prejeto  INTEGER NOT NULL,          -- epoha, ko je sporočilo prišlo k nam
    vrsta    TEXT    NOT NULL,          -- Donation | Subscription | Shop Order | Commission
    centi    INTEGER NOT NULL,
    valuta   TEXT    NOT NULL,
    preizkus INTEGER NOT NULL DEFAULT 0 -- gumb za preizkus v nastavitvah Ko-fi
);
"""

#: Id plačila, ki ga nosi preizkusno sporočilo Ko-fi (vzorec v vtičnikih
#: activepieces in fleetyards). Prvi preizkus z gumba to potrdi ali ovrže --
#: zato se v `/admin` pokaže posebej, ne v vsoti.
PREIZKUS_ID = "00000000-1111-2222-3333-444444444444"

#: Več od tega ni donacija, ampak tipkarska napaka ali okvara pri Ko-fi.
#: Preverjen žeton pove, od kod je sporočilo, ne da je znesek smiseln.
NAJVEC = Decimal(100_000)

_VALUTA = re.compile(r"^[A-Z]{3}$")

#: Zadnja zavrnjena zahteva, samo v pomnilniku. Ob prvi nastavitvi je
#: tipkarska napaka v žetonu najverjetnejša okvara; ta vrstica v `/admin`
#: loči „ni prišlo do nas“ (Cloudflare, naslov) od „prišlo, a z napačnim“.
zavrnjeno: dict = {"ts": None, "razlog": ""}


class Zavrnjeno(Exception):
    """Zahteve nismo sprejeli: ne pride od Ko-fi ali je ne razumemo."""


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SHEMA)
    conn.commit()


def zeton() -> str:
    """`KAJROS_KOFI_ZETON` ali `.kofi-zeton` v podatkovnem imeniku.

    Bere se ob vsaki zahtevi, ne ob zagonu, kot `.nap-prijava`: `deploy/kofi.sh`
    ga zapiše brez sudota in restarta. Zahtev je nekaj na mesec.
    """
    iz_okolja = config.okolje("KOFI_ZETON", "") or ""
    if iz_okolja:
        return iz_okolja.strip()
    try:
        return (config.DATA_DIR / ".kofi-zeton").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def razberi(telo: str, pricakovan: str) -> dict:
    """Telo zahteve -> podatki Ko-fi, a samo s pravim žetonom.

    Vse, česar ni mogoče preveriti, je ista napaka: kdor ne pozna žetona,
    naj ne izve, kateri del zahteve je bil narobe.
    """
    try:
        podatki = json.loads((parse_qs(telo).get("data") or [""])[0])
    except (ValueError, RecursionError):
        podatki = None
    dano = podatki.get("verification_token") if isinstance(podatki, dict) else None
    # `compare_digest` nad nizi z ne-ASCII znaki vrže TypeError -- zato bajti.
    if not (pricakovan and isinstance(dano, str)
            and hmac.compare_digest(dano.encode(), pricakovan.encode())):
        # Prazno telo pošlje `deploy/kofi.sh`, da vidi, ali strežnik žeton
        # bere (403 proti 404) -- to ni poskus sporočila in ne sme v `/admin`
        # zakriti, ali je Ko-fi sploh kdaj kaj poslal.
        if telo.strip():
            zavrnjeno.update(ts=int(time.time()),
                             razlog="napačen žeton" if isinstance(dano, str) else "ni sporočilo Ko-fi")
        raise Zavrnjeno("Napačen žeton.")
    return podatki


def _centi(znesek) -> int | None:
    """„3.00“ -> 300. Ko-fi pošlje niz; plavajoča vejica bi 0,1 + 0,2 zaokrožila narobe."""
    try:
        d = Decimal(str(znesek))
    except InvalidOperation:
        return None
    if not d.is_finite() or not 0 < d <= NAJVEC:
        return None
    return int((d * 100).to_integral_value())


def _epoha(niz, privzeto: int) -> int:
    """`2026-10-20T13:04:30Z` -> epoha. Brez območja ali neberljivo: `privzeto`."""
    try:
        t = datetime.fromisoformat(str(niz))
    except ValueError:
        return privzeto
    return int(t.timestamp()) if t.tzinfo else privzeto


def sprejmi(conn: sqlite3.Connection, podatki: dict, zdaj: float | None = None) -> str:
    """Zapiše preverjeno plačilo. Vrne `nova`, `ponovljena`, `preizkus` ali `prezrto`.

    Za vse vrne Ko-fi 200: ponovljeno pošiljanje istega plačila je pričakovano,
    sporočilo brez zneska pa z drugim poskusom ne bo nič boljše.
    """
    prejeto = int(zdaj if zdaj is not None else time.time())
    id_ = str(podatki.get("kofi_transaction_id") or podatki.get("message_id") or "")[:100]
    centi = _centi(podatki.get("amount"))
    if not id_ or centi is None:
        return "prezrto"
    valuta = str(podatki.get("currency") or "").strip().upper()
    # Preizkus nosi ali vzorčni id ali naslov na example.com (RFC 2606: ta
    # domena ne sprejema pošte, pravi darovalec potrdila nanjo ne bi dobil).
    preizkus = (id_ == PREIZKUS_ID
                or str(podatki.get("email") or "").lower().endswith("@example.com"))
    kurzor = conn.execute(
        "INSERT INTO donacija (id, placano, prejeto, vrsta, centi, valuta, preizkus) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        # Preizkus sme priti večkrat in vsakič pove, da povezava dela;
        # pravo plačilo ostane, kot je prišlo prvič.
        "ON CONFLICT(id) DO UPDATE SET prejeto = excluded.prejeto "
        "WHERE donacija.preizkus = 1",
        (id_, _epoha(podatki.get("timestamp"), prejeto), prejeto,
         str(podatki.get("type") or "?")[:40],
         centi, valuta if _VALUTA.match(valuta) else "?", int(preizkus)))
    conn.commit()
    if preizkus:
        return "preizkus"
    return "nova" if kurzor.rowcount else "ponovljena"


def pregled(conn: sqlite3.Connection) -> dict:
    """Za `/admin`: ali povezava stoji in kaj je prišlo, po valutah.

    Valute se ne seštevajo: tečaj bi bil nov vir, Ko-fi pa plačila pošlje
    v valuti strani.
    """
    valute = [dict(r) for r in conn.execute(
        "SELECT valuta, SUM(centi) AS centi, COUNT(*) AS stevilo FROM donacija "
        "WHERE preizkus = 0 GROUP BY valuta ORDER BY SUM(centi) DESC")]
    zadnja, preizkus = conn.execute(
        "SELECT MAX(CASE WHEN preizkus = 0 THEN placano END), "
        "       MAX(CASE WHEN preizkus = 1 THEN prejeto END) FROM donacija").fetchone()
    return {"vklopljeno": bool(zeton()), "valute": valute, "zadnja": zadnja,
            "preizkus": preizkus, "zavrnjeno": dict(zavrnjeno)}
