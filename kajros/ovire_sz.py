"""Ovire na progi naravnost s strani SŽ, brez posrednikov.

Zakaj: edini vir ovir, del in nadomestnih prevozov je bil `SZ-OVIRA` v feedu
derp.si. derp.si jih bere z `api.modra.ninja/sz/ovire_raw` (`szService.js`,
prebrano 11. 10. 2026), ta pa s strani `potniski.sz.si/pomoc-uporabnikom-in-
stanje-v-prometu/`, kjer so v HTML kot `var roadworks = [...]` -- isti zapis,
ista polja. Stran beremo s Chromom že za zemljevid in table (`brskalnik.py`);
11. 10. 2026 je imela 49 ovir, modra.ninja istih 49 z istimi id-ji. Dva
posrednika za stran, ki jo že znamo prebrati, in eden od njiju (modra.ninja)
je 7. 10. za zemljevid že utihnil.

Dokler je stran prebrana, slovenskih ovir derp.si ne piše
(`alerts.ovire_vodi_sz`); angleških stran nima, te ostanejo derp.si.

Obvestilo nastane natanko tako, kot ga je sestavil derp.si -- isti `alert_id`
(`SZ-OVIRA-<ID_ovire>`), vzrok in učinek, veljavnost od polnoči do 23:59:59,
besedilo brez oznak HTML in prelomov --, da se ob menjavi vira nič ne
spremeni: `zapore.py` bere besedilo, prikaz `alert_id`.

**Kateri vlaki so prizadeti**, je izračun, ne podatek: SŽ da le relacijo
(„Maribor / Dobova / Zidani Most - Ljubljana“). Pravilo je derp-ovo
(`parseAlertAffectedEntities`): proga je prizadeta, kadar ima vsaj dve od
naštetih postaj; relacija brez „ - “ našteva postaje. Groba, a preizkušena
izbira -- vse vezi do zdaj so nastale po njej. Drugače od derp.si le zapis
imen (vezaj, presledek), glej `_kljuc` in `_LOCILO`.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from google.transit import gtfs_realtime_pb2

from . import alerts, brskalnik, config, db, viri

TZ = ZoneInfo(config.TIMEZONE)

#: Stran s seznamom ovir; ista, s katero brskalnik prebije Cloudflare.
STRAN = "/pomoc-uporabnikom-in-stanje-v-prometu/"
URL = "https://potniski.sz.si/inf"
_SPREMENLJIVKA = "var roadworks"

_C = gtfs_realtime_pb2.Alert.Cause.Value
_E = gtfs_realtime_pb2.Alert.Effect.Value
#: `ID_vrste` -> (vzrok, učinek), kot v derp-ovem `SZ_OVIRA_CAUSE_MAPPING`.
VRSTE = {
    "0": (_C("UNKNOWN_CAUSE"), _E("UNKNOWN_EFFECT")),          # neznan razlog
    "1": (_C("TECHNICAL_PROBLEM"), _E("MODIFIED_SERVICE")),    # izpad vlaka
    "3": (_C("MAINTENANCE"), _E("MODIFIED_SERVICE")),          # dela na progi
    "4": (_C("MAINTENANCE"), _E("MODIFIED_SERVICE")),          # nadomestni prevozi
    "7": (_C("UNKNOWN_CAUSE"), _E("SIGNIFICANT_DELAYS")),      # zamuda vlaka
    "10": (_C("TECHNICAL_PROBLEM"), _E("MODIFIED_SERVICE")),   # izredna prekinitev
}
_NEZNANO = (_C("UNKNOWN_CAUSE"), _E("UNKNOWN_EFFECT"))

_OZNAKA = re.compile(r"<[^>]*>")


def seznam(html: str) -> list[dict]:
    """Skupine ovir iz HTML strani. Napaka, kadar spremenljivke ni: prazna
    stran ali stran brez seznama ni „nobene ovire“."""
    i = html.find(_SPREMENLJIVKA)
    j = html.find("[", i) if i >= 0 else -1
    if j < 0:
        raise RuntimeError("stran SŽ nima seznama ovir (var roadworks)")
    try:
        skupine, _ = json.JSONDecoder().raw_decode(html, j)
    except ValueError:
        raise RuntimeError("seznam ovir na strani SŽ ni JSON") from None
    if not isinstance(skupine, list):
        raise RuntimeError("seznam ovir na strani SŽ ni seznam")
    return skupine


def _vrstica(s) -> str:
    return (s or "").replace("\n", " ").replace("\r", " ").strip()


def _dan(niz: str, konec: bool) -> int | None:
    try:
        dan, mesec, leto = (int(x) for x in niz.strip().split(".")[:3])
        d = datetime(leto, mesec, dan, tzinfo=TZ)
    except ValueError:
        return None
    return int(d.timestamp()) + (86399 if konec else 0)


def razberi(skupine: list[dict]) -> list[dict]:
    """Skupine (po kraju) -> ena vrstica na oviro. Polja so vzporedni seznami."""
    out = []
    for g in skupine:
        for i, oid in enumerate(g.get("ID_ovire") or []):
            def polje(ime, i=i):
                v = g.get(ime) or []
                return v[i] if i < len(v) else None
            cas = (polje("Cas") or "").split("-")
            vzrok, ucinek = VRSTE.get(str(polje("ID_vrste")), _NEZNANO)
            out.append({
                "alert_id": f"SZ-OVIRA-{oid}",
                "cause": vzrok, "effect": ucinek,
                "start_ts": _dan(cas[0], False) if cas[0].strip() else None,
                "end_ts": _dan(cas[1], True) if len(cas) > 1 else None,
                "header": _vrstica(polje("Naslov")),
                # Vrstni red kot pri derp.si: najprej prelomi in robovi, nato
                # oznake -- sicer bi besedilo začelo s presledkom in vsako
                # obvestilo bi ob menjavi vira veljalo za spremenjeno.
                "description": _OZNAKA.sub("", _vrstica(polje("Opis"))),
                "relacija": polje("Relacija") or "",
            })
    return out


#: Ločilo relacije: vezaj s presledkom vsaj na eni strani. SŽ piše tudi
#: „Zidani Most -Hrastnik“; vezaj brez presledkov je del imena (Lesce-Bled).
_LOCILO = re.compile(r"\s+-\s*|\s*-\s+")


def _kljuc(ime: str) -> str:
    # Brez presledkov in vezajev: SŽ v relaciji piše „Lesce Bled“, vozni red
    # „Lesce-Bled“ (tako še Jarše-Mengeš, Šmarje-Sap, Hrpelje-Kozina ...).
    return ime.strip().lower().replace(" ", "").replace("-", "")


def proge(conn: sqlite3.Connection) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(route_id -> imena postaj, ime -> stop_id) vlakov SŽ, za vezi ovir."""
    poti: dict[str, set[str]] = {}
    postaje: dict[str, set[str]] = {}
    for r in conn.execute(
            "SELECT DISTINCT t.route_id, s.stop_id, st.name FROM trip t "
            "JOIN sched s USING (trip_id) JOIN station st USING (stop_id) "
            "WHERE t.network = 'zeleznica' AND t.mode != 'bus'"):
        k = _kljuc(r[2])
        poti.setdefault(r[0], set()).add(k)
        postaje.setdefault(k, set()).add(r[1])
    return poti, postaje


def vezi(relacija: str, poti: dict[str, set[str]],
         postaje: dict[str, set[str]]) -> set[tuple[str, str, str]]:
    """Relacija -> vrstice `alert_entity` (route_id, trip_id, stop_id)."""
    deli = _LOCILO.split(relacija.strip())
    if len(deli) > 1:
        imena = {_kljuc(p) for d in deli for p in d.split(" / ")}
        return {(rid, "", "") for rid, ime in poti.items() if len(imena & ime) >= 2}
    # Ena postaja ali več z „ / “; „Slovenija“ ne zadeva ničesar določenega.
    return {("", "", sid) for p in relacija.split(" / ") for sid in postaje.get(_kljuc(p), ())}


def zapisi(conn: sqlite3.Connection, ovire: list[dict], zdaj: float) -> dict:
    """Ovire v `alert` in njihove vezi v `alert_entity`."""
    seen_at = int(zdaj)
    poti, postaje = proge(conn)
    izid = {"ovir": 0, "novih": 0, "vezi_spremenjenih": 0, "brez_vezi": 0}
    for o in ovire:
        znana = alerts.zapisi(conn, o["alert_id"], "ovira", o["cause"], o["effect"],
                              o["start_ts"], o["end_ts"], o["header"], o["description"],
                              URL, "sl", seen_at)
        izid["ovir"] += 1
        izid["novih"] += not znana
        nove = vezi(o["relacija"], poti, postaje)
        izid["brez_vezi"] += not nove
        # Vezi se računajo ob vsakem branju (nov vozni red = nove proge), a
        # pišejo samo ob spremembi.
        stare = {tuple(r) for r in conn.execute(
            "SELECT route_id, trip_id, stop_id FROM alert_entity WHERE alert_id = ?",
            (o["alert_id"],))}
        if nove != stare:
            conn.execute("DELETE FROM alert_entity WHERE alert_id = ?", (o["alert_id"],))
            conn.executemany(
                "INSERT INTO alert_entity(alert_id, route_id, trip_id, stop_id) VALUES(?,?,?,?)",
                [(o["alert_id"], *v) for v in sorted(nove)])
            izid["vezi_spremenjenih"] += 1
    return izid


def korak(conn: sqlite3.Connection, html: str, zdaj: float) -> dict:
    """Ena prebrana stran: zapiši ovire, povzemi v `meta` za pregled."""
    s = zapisi(conn, razberi(seznam(html)), zdaj)
    s["ts"] = int(zdaj)
    db.set_meta(conn, "ovire_sz", json.dumps(s, sort_keys=True))
    conn.commit()
    return s


def _get() -> str:
    with viri.branje("ovire_sz") as b:
        html = brskalnik.zahtevaj(STRAN)
        b.http, b.bajtov = 200, len(html.encode())
        return html


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit, kot zemljevid in table: brskalnik zna obviseti."""
    conn = db.connect()
    napak, prvic = 0, True
    try:
        while not stop.is_set():
            zdaj = time.time()
            try:
                s = korak(conn, _get(), zdaj)
                alerts.ovire_sz_prebrane(zdaj)
                if napak or prvic or s["novih"]:
                    log(f"ovire SŽ{' spet' if napak else ''}: {s['ovir']} ovir, "
                        f"{s['novih']} novih, {s['brez_vezi']} brez vlakov; "
                        "slovenske ovire vodi stran SŽ")
                napak, prvic = 0, False
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"ovire SŽ ni bilo mogoče prebrati: {exc}; ovire spet piše "
                        f"derp.si, ko mine {alerts.OVIRE_VODI_OBHODOV} obhodov")
            stop.wait(max(config.OVIRE_SZ_SECONDS - (time.time() - zdaj),
                          brskalnik.pocitek_s() if napak else 0.0, 1.0))
    finally:
        conn.close()
