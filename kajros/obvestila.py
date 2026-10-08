"""Obvestila skrbnika potnikom — kar vemo, pa ga podatki sami ne povedo.

28. 9. 2026 je DUJPP objavil vozni red brez vlakov in s pomešanimi trasami
avtobusov. Vlaki so za pol dneva izginili, zemljevid je risal avtobuse po
tujih progah, in potnik ni imel kje prebrati, da ni kriv on ali njegov
telefon. Zato ta modul: skrbnik v `/admin` napiše obvestilo, stran ga
pokaže na vrhu, dokler ne poteče ali ga potnik ne zapre.

Obvestilo ni ovira: ovire (`alerts.py`) so obvestila prevoznika o progi,
ta so naša, o tem, kaj kajros ta hip ve in česa ne.

**Vsako obvestilo poteče.** Brez roka bi ostalo viseti, ko razlog že zdavnaj
ni več res -- in obvestilo, ki laže, je slabše od nobenega. Najdlje
`NAJDLJE_S`; kar mora veljati dlje, se objavi znova.

Piše samo skrbnik (`POST /admin/obvestila`, isti žeton kot pregled), zato tu
ni varovalk pred neznancem kot v `stik.py` -- le meje, ki varujejo stran
pred tipkarsko napako.

Eno obvestilo na omrežje nastane samo (`samodejna`): vlaki ali avtobusi po
voznem redu vozijo, podatkov o njih pa ni. Skrbnik ob 5. uri zjutraj ne bdi.
"""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Obvestilo je pasica nad vsebino strani, ne članek. Na telefonu je 280
#: znakov približno šest vrstic -- več bi potisnilo iskalnik pod rob zaslona.
NAJDALJSE = 280
NAJKRAJSE = 5
#: Kar mora veljati dlje od tega, naj skrbnik objavi znova: rok je varovalka
#: pred pozabljenim obvestilom, ne omejitev vsebine.
NAJDLJE_S = 30 * 86400
#: Več hkrati jih stran ne pokaže. Tri pasice druga pod drugo so že tabla.
NAJVEC_NA_STRANI = 3

OMREZJA = ("zeleznica", "avtobus")

#: Spremeni se ob vsakem zapisu. `api` z njim razveljavi predpomnjen odgovor
#: takoj, ko skrbnik kaj objavi -- ne šele, ko poteče ura predpomnilnika.
razlicica = 0


class Zavrnjeno(Exception):
    """Obvestila nismo sprejeli. Besedilo je za skrbnika."""


def _zdaj() -> int:
    return int(time.time())


def rok(niz: str, zdaj: int | None = None) -> int:
    """„2026-09-29T03:00“ iz obrazca -> epoha. Ura je slovenska, ne strežnikova.

    `datetime-local` pošlje čas brez območja; brez `TZ` bi ga strežnik v
    UTC premaknil za dve uri in obvestilo „do 3:00“ bi poteklo ob petih.
    """
    t = zdaj if zdaj is not None else _zdaj()
    try:
        do = datetime.fromisoformat((niz or "").strip())
    except ValueError:
        raise Zavrnjeno("Rok ni datum in ura.") from None
    if do.tzinfo is None:
        do = do.replace(tzinfo=TZ)
    do_ts = int(do.timestamp())
    if do_ts <= t + 60:
        raise Zavrnjeno("Rok je že mimo.")
    if do_ts > t + NAJDLJE_S:
        raise Zavrnjeno(f"Najdlje {NAJDLJE_S // 86400} dni; potem ga objavi znova.")
    return do_ts


def objavi(conn: sqlite3.Connection, besedilo: str, omrezje: str | None,
           do_ts: int, zdaj: int | None = None) -> int:
    """Shrani obvestilo in vrne njegov `id`. `omrezje` None = obe omrežji."""
    global razlicica
    besedilo = (besedilo or "").strip()
    if len(besedilo) < NAJKRAJSE:
        raise Zavrnjeno("Obvestilo je prekratko.")
    if len(besedilo) > NAJDALJSE:
        raise Zavrnjeno(f"Obvestilo je predolgo (največ {NAJDALJSE} znakov).")
    omrezje = omrezje or None
    if omrezje is not None and omrezje not in OMREZJA:
        raise Zavrnjeno("Neznano omrežje.")
    t = zdaj if zdaj is not None else _zdaj()
    cur = conn.execute(
        "INSERT INTO obvestilo(besedilo, omrezje, od_ts, do_ts) VALUES(?, ?, ?, ?)",
        (besedilo, omrezje, t, do_ts))
    conn.commit()
    razlicica += 1
    return int(cur.lastrowid)


def umakni(conn: sqlite3.Connection, id_: int, zdaj: int | None = None) -> bool:
    """Obvestilo poteče zdaj. Ostane na seznamu v pregledu, da se ve, kaj je
    bilo potnikom rečeno in do kdaj."""
    global razlicica
    t = zdaj if zdaj is not None else _zdaj()
    n = conn.execute("UPDATE obvestilo SET do_ts = ? WHERE id = ? AND do_ts > ?",
                     (t, id_, t)).rowcount
    conn.commit()
    razlicica += 1
    return n > 0


def izbrisi(conn: sqlite3.Connection, id_: int) -> bool:
    global razlicica
    n = conn.execute("DELETE FROM obvestilo WHERE id = ?", (id_,)).rowcount
    conn.commit()
    razlicica += 1
    return n > 0


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, TZ).isoformat(timespec="seconds")


def _vrstica(v) -> dict:
    return {"id": v["id"], "besedilo": v["besedilo"], "omrezje": v["omrezje"],
            "objavljeno": _iso(v["od_ts"]), "velja_do": _iso(v["do_ts"]),
            "do_ts": v["do_ts"]}


def veljavna(conn: sqlite3.Connection, zdaj: int | None = None) -> list[dict]:
    """Vsa veljavna obvestila, najnovejše prvo. Omrežje izbere `za_omrezje`."""
    t = zdaj if zdaj is not None else _zdaj()
    return [_vrstica(v) for v in conn.execute(
        "SELECT id, besedilo, omrezje, od_ts, do_ts FROM obvestilo "
        "WHERE od_ts <= ? AND do_ts > ? ORDER BY od_ts DESC, id DESC", (t, t))]


def za_omrezje(vsa: list[dict], omrezje: str, zdaj: int | None = None) -> list[dict]:
    """Kar sodi na stran omrežja `omrezje` (`vse` = domača, zemljevid, pot).

    Rok se preveri tudi tu, ne le v poizvedbi: `vsa` je lahko predpomnjen
    seznam, v katerem je obvestilo medtem poteklo.
    """
    t = zdaj if zdaj is not None else _zdaj()
    return [o for o in vsa
            if o["do_ts"] > t
            and (omrezje == "vse" or o["omrezje"] in (None, omrezje))
            ][:NAJVEC_NA_STRANI]


def seznam(conn: sqlite3.Connection, limit: int = 30,
           zdaj: int | None = None) -> list[dict]:
    """Za pregled: veljavna in zadnja potekla, najnovejše prvo."""
    t = zdaj if zdaj is not None else _zdaj()
    return [{**_vrstica(v), "velja": v["do_ts"] > t} for v in conn.execute(
        "SELECT id, besedilo, omrezje, od_ts, do_ts FROM obvestilo "
        "ORDER BY do_ts > ? DESC, od_ts DESC, id DESC LIMIT ?", (t, limit))]


# --- samodejno: omrežje brez podatkov ----------------------------------------
#
# 7. 10. 2026 sta oba vira zamud vlakov (derp.si in zemljevid SŽ prek
# api.modra.ninja) ob 1:40 hkrati utihnila. Zjutraj je bil zemljevid brez
# vlakov, tabla brez zamud, pika ob uri zelena -- in potnik je bral, da
# aplikacija ne dela. `/admin` je bil rdeč, a skrbnik ob 5. uri ne bdi.
#
# 8. 10. 2026 od 16:00 isto pri avtobusih: strežnik RT derp.si ni sprejemal
# povezav, na avtobusnih straneh pa ni bilo nobenega obvestila.

#: Toliko molka omrežja, medtem ko po voznem redu vozi, je okvara vira in ne
#: tišina prometa. Pri vlakih preverjeno na arwenu za 6. 9.--7. 10. 2026,
#: vsakih 5 min ob živem zajemu: tri epizode, vse prave -- 28. 9. (zip DUJPP
#: brez vlakov, 275 min), 3. 10. od 18:17 (85 min) in 7. 10. od 1:24 (230 min
#: do meritve). Najdaljša vrzel zdravega zajema je bila 15,6 min (25. 9. ob
#: 19:06, na progi 26 vlakov). Isto pri pragu 3, 5 ali 10 vlakov.
#:
#: Pri avtobusih preverjeno na arwenu za 24. 9.--8. 10. 2026 (`obs`, vsaki
#: 2 min, 10 428 korakov zdravega zajema): ob vsaj 3 avtobusih na poti je bil
#: najdaljši molk 7,2 min (8. 10. ob 15:08, tik pred izpadom), ena sama
#: epizoda nad 20 min -- izpad derp.si 8. 10. od 16:00. Ponoči med 1. in 3.
#: uro vozijo 0--2 avtobusa; pri enem samem je bil molk tudi 208 min.
MOLCI_S = 1200
#: Najmanj voženj na poti, da je molk dokaz okvare. Kot `zdravje.MIN_VOZENJ`:
#: ponoči en sam nočni vlak ali avtobus ni dokaz okvare.
VSAJ = {"zeleznica": 3, "avtobus": 3}
_IME = {"zeleznica": ("vlakih", "vlakov"), "avtobus": ("avtobusih", "avtobusov")}
#: Vlak in avtobus utihneta ob istem branju derp.si, torej z istim časom
#: zadnjega podatka. Brez odmika bi imeli obvestili isti `id` in potnik bi z
#: enim zaprl obe. Epoha je ~1,8e9, odmik jo dvigne nad vse vlakovne.
_ODMIK_ID = {"zeleznica": 0, "avtobus": 10**10}


def brez_podatkov(omrezje: str, vozi: int, zadnji_ts: int | None,
                  zdaj: int) -> dict | None:
    """Obvestilo, kadar po voznem redu vozi vsaj `VSAJ[omrezje]` voženj,
    zadnji podatek o katerikoli pa je starejši od `MOLCI_S`. Sicer None.

    `id` je čas zadnjega podatka (pri avtobusih z odmikom): ista okvara ima
    isti id, zato jo potnik zapre enkrat, nova pa se pokaže znova. Epoha je
    daleč nad id-ji iz baze; brez vsakega podatka je id dan.
    """
    if vozi < VSAJ[omrezje]:
        return None
    if zadnji_ts is not None and zdaj - zadnji_ts < MOLCI_S:
        return None
    od = "Ta hip"
    if zadnji_ts is not None:
        z, d = datetime.fromtimestamp(zadnji_ts, TZ), datetime.fromtimestamp(zdaj, TZ)
        ura = f"{z:%H:%M}"
        if z.date() == d.date():
            od = f"Od {ura}"
        elif z.date() == d.date() - timedelta(days=1):
            od = f"Od včeraj ob {ura}"
    o_kom, koga = _IME[omrezje]
    besedilo = (f"{od} ne dobivamo podatkov o {o_kom}, zato ne vemo, koliko zamujajo. "
                f"Odhodi so le po voznem redu, {koga} na zemljevidu pa ne moremo "
                "pokazati. Ko podatki spet pridejo, se vse pokaže samo.")
    # `do_ts` le do naslednjega preverjanja: pogoj se računa znova, ne poteče.
    return {"id": (zadnji_ts or zdaj - zdaj % 86400) + _ODMIK_ID[omrezje],
            "besedilo": besedilo, "omrezje": omrezje,
            "objavljeno": _iso(zdaj), "velja_do": _iso(zdaj + 300), "do_ts": zdaj + 300}


def _zadnji_podatek(conn: sqlite3.Connection, omrezje: str, danes) -> int | None:
    if omrezje == "avtobus":
        # Nazaj po `run_feed_ts`: avtobusov je v `run` večina, prva vrstica je
        # skoraj vedno avtobusna. Na arwenu 8. 10. 2026 pod 10 ms, vlakovna
        # ista poizvedba pa 1,8 s -- zato vlaki po svoji poti spodaj.
        r = conn.execute(
            "SELECT r.feed_ts FROM run r CROSS JOIN trip t ON t.trip_id = r.trip_id "
            "WHERE t.network = 'avtobus' ORDER BY r.feed_ts DESC LIMIT 1").fetchone()
        return r[0] if r else None
    # Od voženj k `run`, po prvotnem ključu: pregled `run_feed_ts` nazaj bi ob
    # okvari prebral vse avtobuse od zadnjega vlaka -- prav takrat, ko štejemo.
    return conn.execute(
        "SELECT MAX(r.feed_ts) FROM trip t "
        "CROSS JOIN run r ON r.trip_id = t.trip_id AND r.service_date IN (?, ?) "
        "WHERE t.network = 'zeleznica'",
        ((danes - timedelta(days=1)).isoformat(), danes.isoformat())).fetchone()[0]


def samodejna(conn: sqlite3.Connection, zdaj: int | None = None) -> list[dict]:
    """Obvestila, ki jih napišejo podatki sami. Na arwenu ~85 ms (vozni red
    58 ms, zadnji podatek vlakov 27 ms), zato jih `api` predpomni za minuto."""
    t = zdaj if zdaj is not None else _zdaj()
    danes = datetime.fromtimestamp(t, TZ).date()
    vozi = stats.vozi_zdaj(conn, t)
    out = []
    for omrezje in ("zeleznica", "avtobus"):
        if vozi.get(omrezje, 0) < VSAJ[omrezje]:
            continue
        o = brez_podatkov(omrezje, vozi[omrezje], _zadnji_podatek(conn, omrezje, danes), t)
        if o:
            out.append(o)
    return out
