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

import json
import sqlite3
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, db, stats

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
VSAJ = 3
#: LPP-jevi zasloni (`zamude_lpp`) so živi, kadar je nit zapisala obhod v toliko
#: (kot `zdravje.LPP_STOJI_S`). Tedaj tabla mestnega LPP kaže LPP-jeve prihode.
ZASLONI_ZIVI_S = 900

#: Kdo molči -> (o kom, kaj vidi potnik). Mestni LPP ima drugi vir: kadar
#: derp.si utihne, LPP-jevi zasloni pa ne, molčijo samo medkrajevni.
_BESEDILO = {
    "zeleznica": ("o vlakih", "Odhodi so le po voznem redu, vlakov na zemljevidu "
                  "pa ne moremo pokazati."),
    "avtobus": ("o avtobusih", "Odhodi so le po voznem redu, avtobusov na zemljevidu "
                "pa ne moremo pokazati."),
    "medkrajevni": ("o medkrajevnih avtobusih", "Njihovi odhodi so le po voznem redu, "
                    "na zemljevidu jih ne moremo pokazati."),
    "mestni": ("o mestnih avtobusih LPP", "Njihovi odhodi so le po voznem redu, "
               "na zemljevidu jih ne moremo pokazati."),
}
#: Vlak in avtobus utihneta ob istem branju derp.si, torej z istim časom
#: zadnjega podatka. Brez odmika bi imela obvestila isti `id` in potnik bi z
#: enim zaprl vse. Epoha je ~1,8e9, odmiki jo ločijo za 2e9.
_ODMIK_ID = {"zeleznica": 0, "avtobus": 10**10, "medkrajevni": 12 * 10**9,
             "mestni": 14 * 10**9}


def molci(vozi: int, zadnji_ts: int | None, zdaj: int) -> bool:
    """Po voznem redu vozi vsaj `VSAJ` voženj, zadnji podatek o katerikoli pa
    je starejši od `MOLCI_S` (ali ga ni)."""
    return vozi >= VSAJ and (zadnji_ts is None or zdaj - zadnji_ts >= MOLCI_S)


def obvestilo(vrsta: str, zadnji_ts: int | None, zdaj: int) -> dict:
    """Besedilo za vrsto iz `_BESEDILO`.

    `id` je čas zadnjega podatka z odmikom vrste: ista okvara ima isti id,
    zato jo potnik zapre enkrat, nova pa se pokaže znova. Epoha je daleč nad
    id-ji iz baze; brez vsakega podatka je id dan.
    """
    od = "Ta hip"
    if zadnji_ts is not None:
        z, d = datetime.fromtimestamp(zadnji_ts, TZ), datetime.fromtimestamp(zdaj, TZ)
        ura = f"{z:%H:%M}"
        if z.date() == d.date():
            od = f"Od {ura}"
        elif z.date() == d.date() - timedelta(days=1):
            od = f"Od včeraj ob {ura}"
    o_kom, vidi = _BESEDILO[vrsta]
    besedilo = (f"{od} ne dobivamo podatkov {o_kom}, zato ne vemo, koliko zamujajo. "
                f"{vidi} Ko podatki spet pridejo, se vse pokaže samo.")
    # `do_ts` le do naslednjega preverjanja: pogoj se računa znova, ne poteče.
    return {"id": (zadnji_ts or zdaj - zdaj % 86400) + _ODMIK_ID[vrsta],
            "besedilo": besedilo,
            "omrezje": "zeleznica" if vrsta == "zeleznica" else "avtobus",
            "objavljeno": _iso(zdaj), "velja_do": _iso(zdaj + 300), "do_ts": zdaj + 300}


def brez_podatkov(vrsta: str, vozi: int, zadnji_ts: int | None, zdaj: int) -> dict | None:
    """Obvestilo, kadar vrsta `molci`, sicer None."""
    return obvestilo(vrsta, zadnji_ts, zdaj) if molci(vozi, zadnji_ts, zdaj) else None


def _zadnji_podatek(conn: sqlite3.Connection, skupina: str, danes) -> int | None:
    """Zadnji `feed_ts` v `run`: `zeleznica`, `avtobus` (brez mestnega LPP) ali `lpp`."""
    if skupina != "zeleznica":
        # Nazaj po `run_feed_ts`: avtobusov je v `run` večina, prva vrstica je
        # skoraj vedno prava. Na arwenu 8. 10. 2026 pod 10 ms, vlakovna
        # ista poizvedba pa 1,8 s -- zato vlaki po svoji poti spodaj.
        pogoj = ("t.agency = 'lpp'" if skupina == "lpp"
                 else "t.network = 'avtobus' AND t.agency IS NOT 'lpp'")
        r = conn.execute(
            "SELECT r.feed_ts FROM run r CROSS JOIN trip t ON t.trip_id = r.trip_id "
            f"WHERE {pogoj} ORDER BY r.feed_ts DESC LIMIT 1").fetchone()
        return r[0] if r else None
    # Od voženj k `run`, po prvotnem ključu: pregled `run_feed_ts` nazaj bi ob
    # okvari prebral vse avtobuse od zadnjega vlaka -- prav takrat, ko štejemo.
    return conn.execute(
        "SELECT MAX(r.feed_ts) FROM trip t "
        "CROSS JOIN run r ON r.trip_id = t.trip_id AND r.service_date IN (?, ?) "
        "WHERE t.network = 'zeleznica'",
        ((danes - timedelta(days=1)).isoformat(), danes.isoformat())).fetchone()[0]


def _zasloni_zivi(conn: sqlite3.Connection, zdaj: int) -> bool:
    if not config.LPP_ZAMUDE:
        return False
    try:
        ts = json.loads(db.get_meta(conn, "zamude_lpp") or "{}").get("ts") or 0
    except ValueError:
        return False
    return zdaj - ts <= ZASLONI_ZIVI_S


def samodejna(conn: sqlite3.Connection, zdaj: int | None = None) -> list[dict]:
    """Obvestila, ki jih napišejo podatki sami. Na arwenu ~85 ms (vozni red
    58 ms, zadnji podatek vlakov 27 ms), zato jih `api` predpomni za minuto."""
    t = zdaj if zdaj is not None else _zdaj()
    danes = datetime.fromtimestamp(t, TZ).date()
    vozi = stats.vozi_zdaj(conn, t, lpp_posebej=True)

    def zadnji(skupina):
        return _zadnji_podatek(conn, skupina, danes) if vozi[skupina] >= VSAJ else None

    out = []
    vlaki = zadnji("zeleznica")
    if molci(vozi["zeleznica"], vlaki, t):
        out.append(obvestilo("zeleznica", vlaki, t))
    medkrajevni, mestni = zadnji("avtobus"), zadnji("lpp")
    tiho_m = molci(vozi["avtobus"], medkrajevni, t)
    # Mestni LPP ne molči, dokler kažemo LPP-jeve prihode (`lpp.na_tablo`).
    tiho_l = molci(vozi["lpp"], mestni, t) and not _zasloni_zivi(conn, t)
    if tiho_m and tiho_l:
        out.append(obvestilo("avtobus", max(medkrajevni or 0, mestni or 0) or None, t))
    elif tiho_m:
        out.append(obvestilo("medkrajevni", medkrajevni, t))
    elif tiho_l:
        out.append(obvestilo("mestni", mestni, t))
    return out
