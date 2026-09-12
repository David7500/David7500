"""Sporočila obiskovalcev — edina pot v tej aplikaciji, ki piše iz zahteve.

Do 12. 9. 2026 je bilo v `api.py` samo `GET` in nobenega pisanja v bazo iz
zahteve; v `.claude/rules/objava.md` je bilo to zapisano kot razlog, zakaj je
javna izpostavitev varna. Ta modul to spremeni in zato nosi vso varovalko na
enem mestu, da je mogoče v enem branju videti, kaj neznanec sme.

**Naslova IP ne shranimo niti tu.** Omejevanje po pošiljatelju teče v
pomnilniku nad zgoščeno vrednostjo in po restartu izgine. To je zavestna
menjava: raje pustimo, da po restartu kdo pošlje nekaj sporočil več, kot da
bi zaradi neželene pošte začeli voditi dnevnik naslovov.

Kaj mora spam prebiti, preden pride do baze:

1. **podpisan žeton** v obrazcu — preprečuje pošiljanje mimo naše strani in
   ponovno rabo istega obrazca v nedogled;
2. **časovna past** — obrazec, izpolnjen v manj kot `NAJHITREJE_S`, ni
   človek; človek potrebuje za e-pošto in stavek več kot štiri sekunde;
3. **vaba** — polje, ki je za človeka skrito in ga izpolni samodejni robot;
4. **omejitev na pošiljatelja** — `NA_URO` in `NA_DAN` v pomnilniku;
5. **dnevni strop čez vse** — `VSEH_NA_DAN` iz baze, da porazdeljena kampanja
   ne more napolniti diska z bazo meritev vred.

Zadnji je tisti, ki šteje: prvi štirje ustavijo preprost robot, peti pa
omeji škodo, kadar jih kdo prebije.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config

TZ = ZoneInfo(config.TIMEZONE)

#: Obrazec, izpolnjen hitreje od tega, ni človek.
NAJHITREJE_S = 4
#: Po tem času je žeton pretečen. Dovolj dolgo za premislek, prekratko za
#: to, da bi si ga kdo shranil in z njim streljal še jutri.
NAJPOZNEJE_S = 2 * 3600

NA_URO = 3
NA_DAN = 5
#: Strop čez vse pošiljatelje skupaj. Pri ročnem odgovarjanju je petdeset
#: sporočil na dan tako ali tako več, kot je mogoče prebrati.
VSEH_NA_DAN = 50

NAJDALJSE = 4000
NAJKRAJSE = 10
#: RFC 5321 dovoljuje 254 znakov za cel naslov.
NAJDALJSI_EMAIL = 254

SHEMA = """
-- Sporočila obiskovalcev. Brez naslova IP: ta se ne shrani niti tu, tako
-- kot se ne shrani pri štetju obiska.
CREATE TABLE IF NOT EXISTS sporocilo (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    prispelo TEXT    NOT NULL,          -- ISO 8601 z območjem
    email    TEXT    NOT NULL,
    besedilo TEXT    NOT NULL,
    drzava   TEXT,                      -- dvočrkovna, iz Cloudflarove glave
    naprava  TEXT,                      -- telefon | računalnik | ...
    prebrano INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_sporocilo_cas ON sporocilo(prispelo DESC);
"""

# Naslov mora imeti ena @ in za njo piko. Strožje preverjanje je znana
# slepa ulica -- vsak tak vzorec zavrne kakšen veljaven naslov, resnično
# preverjanje pa je odgovor na poslano pošto in tega ne delamo.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_zaklep = threading.Lock()
#: `kljuc -> [časi pošiljanj]`. Samo v pomnilniku, glej opis modula.
_poslana: dict[str, list[float]] = {}

#: Skrivnost za podpis obrazca. Izpeljana iz skrbniškega žetona, da preživi
#: restart -- odprt obrazec bi sicer ob vsaki objavi postal neveljaven.
#: Brez žetona (razvoj) je naključna in to zadošča, ker traja proces.
_SKRIVNOST = (hashlib.blake2s((config.ADMIN_TOKEN or "").encode(),
                              person=b"stik", digest_size=32).digest()
              if config.ADMIN_TOKEN else secrets.token_bytes(32))


class Zavrnjeno(Exception):
    """Sporočila nismo sprejeli. Besedilo je namenjeno obiskovalcu."""


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SHEMA)
    conn.commit()


def _zdaj() -> datetime:
    return datetime.now(TZ)


# ---------------------------------------------------------------- žeton

def zeton(zdaj: float | None = None) -> str:
    """Podpisan žeton za v obrazec. Nosi čas izdaje, da je past merljiva."""
    t = int(zdaj if zdaj is not None else time.time())
    podpis = hmac.new(_SKRIVNOST, str(t).encode(), "sha256").hexdigest()[:32]
    return f"{t}.{podpis}"


def _preveri_zeton(dano: str, zdaj: float | None = None) -> None:
    t_zdaj = zdaj if zdaj is not None else time.time()
    izdan, _, podpis = (dano or "").partition(".")
    if not podpis or not izdan.isdigit():
        raise Zavrnjeno("Obrazec ni veljaven. Osveži stran in poskusi znova.")
    if not hmac.compare_digest(podpis,
                               hmac.new(_SKRIVNOST, izdan.encode(),
                                        "sha256").hexdigest()[:32]):
        raise Zavrnjeno("Obrazec ni veljaven. Osveži stran in poskusi znova.")
    starost = t_zdaj - int(izdan)
    if starost < NAJHITREJE_S:
        # Namenoma ne pove, da je bilo prehitro: robotu bi to povedalo,
        # koliko naj počaka.
        raise Zavrnjeno("Obrazec ni veljaven. Osveži stran in poskusi znova.")
    if starost > NAJPOZNEJE_S:
        raise Zavrnjeno("Obrazec je potekel. Osveži stran in poskusi znova.")


# ---------------------------------------------------------- omejevanje

def kljuc_posiljatelja(glave) -> str:
    """Zgoščena vrednost naslova, ki nikamor ne gre — samo v pomnilnik.

    Brez soli dneva, drugače kot pri štetju obiska: tu vrednost ne preživi
    procesa in je nihče nikoli ne zapiše, zato sol ne bi ničesar dodala.
    """
    za = (glave.get("cf-connecting-ip")
          or glave.get("x-forwarded-for", "").split(",")[0].strip()
          or "?")
    return hashlib.blake2s(za.encode(), digest_size=16).hexdigest()


def _preveri_pogostost(kljuc: str, zdaj: float | None = None) -> None:
    t = zdaj if zdaj is not None else time.time()
    with _zaklep:
        casi = [c for c in _poslana.get(kljuc, []) if t - c < 86400]
        if len([c for c in casi if t - c < 3600]) >= NA_URO:
            raise Zavrnjeno("Preveč sporočil v kratkem času. "
                            "Poskusi čez kakšno uro.")
        if len(casi) >= NA_DAN:
            raise Zavrnjeno("Danes si poslal že več sporočil. "
                            "Poskusi jutri.")
        _poslana[kljuc] = casi
        # Redčenje: brez tega slovar raste s številom različnih naslovov.
        if len(_poslana) > 5000:
            for k in [k for k, v in _poslana.items()
                      if not v or t - max(v) > 86400]:
                _poslana.pop(k, None)


def _zabelezi_poslano(kljuc: str, zdaj: float | None = None) -> None:
    with _zaklep:
        _poslana.setdefault(kljuc, []).append(
            zdaj if zdaj is not None else time.time())


def _preveri_dnevni_strop(conn: sqlite3.Connection) -> None:
    dan = _zdaj().date().isoformat()
    (n,) = conn.execute("SELECT COUNT(*) FROM sporocilo WHERE prispelo >= ?",
                        (dan,)).fetchone()
    if n >= VSEH_NA_DAN:
        raise Zavrnjeno("Danes je nabiralnik poln. Poskusi jutri.")


# ------------------------------------------------------------- sprejem

def preveri_vsebino(email: str, besedilo: str) -> tuple[str, str]:
    """Pospravi in preveri, kar je vpisal človek. Vrne očiščeno."""
    email = (email or "").strip()
    besedilo = (besedilo or "").strip()
    if not email:
        raise Zavrnjeno("Vpiši svoj e-naslov, sicer ti ne moremo odgovoriti.")
    if len(email) > NAJDALJSI_EMAIL or not _EMAIL.match(email):
        raise Zavrnjeno("Ta e-naslov ni videti pravi.")
    if len(besedilo) < NAJKRAJSE:
        raise Zavrnjeno("Sporočilo je prekratko — napiši, za kaj gre.")
    if len(besedilo) > NAJDALJSE:
        raise Zavrnjeno(f"Sporočilo je predolgo (največ {NAJDALJSE} znakov).")
    return email, besedilo


def sprejmi(conn: sqlite3.Connection, *, email: str, besedilo: str,
            zeton_iz_obrazca: str, vaba: str, kljuc: str,
            drzava: str = "", naprava: str = "",
            zdaj: float | None = None) -> int:
    """Preveri vse varovalke in shrani. Vrne `id` sporočila.

    Vrstni red ni poljuben: **najprej poceni preverbe brez baze**, šele nato
    poizvedba za dnevni strop. Robot, ki tolče po obrazcu, tako ne povzroči
    poizvedbe na vsak poskus.
    """
    # Vaba je za človeka skrita; izpolni jo samo tisti, ki bere HTML.
    # Odgovor je enak kot ob uspehu -- robot ne sme izvedeti, da je ujet.
    if (vaba or "").strip():
        return 0
    _preveri_zeton(zeton_iz_obrazca, zdaj)
    email, besedilo = preveri_vsebino(email, besedilo)
    _preveri_pogostost(kljuc, zdaj)
    _preveri_dnevni_strop(conn)

    cur = conn.execute(
        "INSERT INTO sporocilo(prispelo, email, besedilo, drzava, naprava) "
        "VALUES(?, ?, ?, ?, ?)",
        (_zdaj().isoformat(timespec="seconds"), email, besedilo,
         (drzava or "")[:2].upper() or None, (naprava or "")[:20] or None))
    conn.commit()
    _zabelezi_poslano(kljuc, zdaj)
    return int(cur.lastrowid)


# -------------------------------------------------------------- branje

def seznam(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    vrstice = conn.execute(
        "SELECT id, prispelo, email, besedilo, drzava, naprava, prebrano "
        "FROM sporocilo ORDER BY prispelo DESC, id DESC LIMIT ?",
        (limit,)).fetchall()
    return [dict(v) for v in vrstice]


def stevec(conn: sqlite3.Connection) -> dict:
    vseh, neprebranih = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(prebrano = 0), 0) FROM sporocilo"
    ).fetchone()
    return {"vseh": int(vseh), "neprebranih": int(neprebranih)}


def oznaci_prebrano(conn: sqlite3.Connection, id_: int, prebrano: bool) -> None:
    conn.execute("UPDATE sporocilo SET prebrano = ? WHERE id = ?",
                 (1 if prebrano else 0, id_))
    conn.commit()


def izbrisi(conn: sqlite3.Connection, id_: int) -> bool:
    """Odstrani sporočilo. Vrne, ali je kaj odstranil.

    Nabiralnik brez brisanja se zapolni z neželeno pošto, ki jo je treba
    odslej gledati vsak dan. Brisanje je tudi edini način, kako izpolniti
    prošnjo „izbrišite moje sporočilo“ — računa, prek katerega bi človek
    to storil sam, namenoma nimamo.
    """
    n = conn.execute("DELETE FROM sporocilo WHERE id = ?", (id_,)).rowcount
    conn.commit()
    return n > 0
