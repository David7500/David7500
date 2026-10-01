"""Zamude vlakov z zemljevida SŽ -- drugi vir poleg derp.si.

Zakaj: 28. 9. 2026 je DUJPP objavil vozni red brez voženj SŽ in derp.si je
čez noč ostal brez vseh vlakov -- zamud, leg in obvestil `SZ-DELAY`. Zemljevid
vlakov na potniski.sz.si (prek `api.modra.ninja/sz/lokacije`, isti posrednik
kot pri tiru) je ob istem času nosil 41 vlakov z zamudo, med njimi vseh 31, ki
so po voznem redu vozili. Vlak tam nosi številko, ne id vožnje iz zipa, zato ga
pokvarjen zip DUJPP ne prizadene.

Kaj vrstica pove (izmerjeno na 12 vlakih istega jutra): `raw_odhod` je vedno
voznoredni odhod s postaje PRED `naslednja_postaja` plus `zamuda_min`, na minuto
natančno. Zamuda je torej odhodna zamuda zadnjega prevoženega postanka, in ta
enakost je hkrati preizkus, da smo vlak pripeli na pravo vožnjo in dan.

Vira se primerjata, ne zamenjata. Vsaka vrednost gre v `sz_zamuda`; v `run`
gre le, kadar feed derp.si te vožnje ne nosi (`iz_lege.brez_feeda`) -- tedaj
ima `v_run = 1` in ne šteje v primerjavo, ker bi primerjala vir sam s sabo.
Kadar nosita oba, `primerjava()` pove, kako se razhajata; kdo ima prav, se
odloči šele na izmerjenih razhajanjih.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

import requests

from . import collector, config, db, iz_lege, stats
from .peroni import _kljuc_imena, stevilka

TZ = ZoneInfo(config.TIMEZONE)

#: Toliko sme `raw_odhod` odstopati od voznega reda plus zamude. Oboje je v
#: celih minutah, zato ena minuta za zaokroževanje.
ODSTOPA_ODHOD_S = 60
#: Odhod, starejši od tega, ni odhod te vožnje, ampak ista številka drug dan.
NAJSTAREJSI_ODHOD_S = 6 * 3600


def vozni_red(conn: sqlite3.Connection, danes: date) -> dict[str, list[dict]]:
    """Številka vlaka -> vožnje, ki bi lahko zdaj vozile (včeraj ali danes).

    Nadomestni avtobusi ne: zemljevid SŽ jih kaže z zamudo 0 v točki postaje
    (pregled 25. 9. 2026) -- izračun, ne meritev.
    """
    dnevi = ((danes - timedelta(days=1)).isoformat(), danes.isoformat())

    def build():
        out: dict[str, dict[tuple, dict]] = defaultdict(dict)
        for r in conn.execute(
            "SELECT t.trip_id, t.train_no, d.date, s.stop_seq, st.name, s.arr_s, s.dep_s "
            "FROM trip t JOIN service_day d USING (service_id) "
            "JOIN sched s USING (trip_id) JOIN station st USING (stop_id) "
            "WHERE t.network = 'zeleznica' AND t.mode != 'bus' AND d.date IN (?, ?) "
            "ORDER BY t.trip_id, d.date, s.stop_seq", dnevi):
            v = out[stevilka(r["train_no"])].setdefault(
                (r["trip_id"], r["date"]),
                {"trip_id": r["trip_id"], "dan": r["date"], "postanki": []})
            v["postanki"].append((r["stop_seq"], _kljuc_imena(r["name"]),
                                  r["arr_s"], r["dep_s"]))
        return {st: list(v.values()) for st, v in out.items()}

    return collector._cached(conn, "vozni_red_sz", dnevi, build)


def _ura(ts: float) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M")


def _minute(hhmm: str) -> int | None:
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except (AttributeError, ValueError):
        return None


def pripni(vrstica: dict, voznje: list[dict], zdaj: float) -> tuple | None:
    """Vrstica zemljevida -> (trip_id, dan, stop_seq, zamuda_s) ali None.

    Postanek je zadnji prevoženi, torej tisti PRED `naslednja_postaja`. Od več
    voženj z isto številko (sezonske različice, včeraj in danes) velja tista,
    pri kateri se `raw_odhod` ujema z voznim redom plus zamudo; kadar se ne
    ujema nobena, vlaka ne pripnemo -- raje nič kot na napačno vožnjo.
    """
    naslednja = _kljuc_imena(vrstica.get("naslednja_postaja") or "")
    zamuda = vrstica.get("zamuda_min")
    odhod = _minute(vrstica.get("raw_odhod"))
    if not naslednja or zamuda is None or odhod is None:
        return None
    najboljsa, razmik = None, None
    for v in voznje:
        p = v["postanki"]
        for i in range(1, len(p)):
            if p[i][1] != naslednja:
                continue
            seq, _, arr, dep = p[i - 1]
            t = dep if dep is not None else arr
            if t is None:
                continue
            kdaj = stats.polnoc(v["dan"]) + t + zamuda * 60
            if not (-ODSTOPA_ODHOD_S <= zdaj - kdaj <= NAJSTAREJSI_ODHOD_S):
                continue
            # Ura z zemljevida je lokalna ura dneva; primerjava po modulu dneva,
            # ker vlak čez polnoč odpelje ob 00:10 prometnega dne včeraj.
            ura = _minute(_ura(kdaj))
            if min((ura - odhod) % 1440, (odhod - ura) % 1440) * 60 > ODSTOPA_ODHOD_S:
                continue
            if razmik is None or zdaj - kdaj < razmik:
                najboljsa, razmik = (v["trip_id"], v["dan"], seq, zamuda * 60), zdaj - kdaj
    return najboljsa


def razberi(vrstice: list[dict], po_stevilki: dict[str, list[dict]],
            zdaj: float) -> tuple[list[tuple], dict]:
    """Vse vrstice zemljevida -> (pripete, števci)."""
    pripete, stevci = [], {"vlakov": 0, "nepripetih": 0}
    for r in vrstice:
        if r.get("bus"):
            continue
        stevci["vlakov"] += 1
        p = pripni(r, po_stevilki.get(stevilka(str(r.get("st_vlaka") or "")), []), zdaj)
        if p is None:
            stevci["nepripetih"] += 1
        else:
            pripete.append(p)
    return pripete, stevci


def zapisi(conn: sqlite3.Connection, pripete: list[tuple], zdaj: float,
           vlaki: set[str] = frozenset()) -> dict:
    """Pripete zamude v `sz_zamuda`; v `run` samo tiste, ki jih derp.si nima.

    `vlaki` so vse vožnje vlakov voznega reda: med njimi `samo_derp` prešteje
    tiste, ki jih derp.si nosi, zemljevid pa ne -- obratna vrzel.
    """
    ts = int(zdaj)
    samo_sz = oba = 0
    for trip_id, dan, seq, zamuda in pripete:
        v_run = iz_lege.brez_feeda(trip_id, zdaj)
        if v_run:
            iz_lege.zapisi_meritev(conn, trip_id, dan, seq, None, zamuda, ts)
            samo_sz += 1
        else:
            oba += 1
        conn.execute(
            "INSERT INTO sz_zamuda(trip_id, service_date, stop_seq, delay_s, "
            "                      prvic_ts, zadnjic_ts, v_run) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id, service_date, stop_seq) DO UPDATE SET "
            "  delay_s = excluded.delay_s, zadnjic_ts = excluded.zadnjic_ts, "
            "  v_run = MAX(v_run, excluded.v_run)",
            (trip_id, dan, seq, zamuda, ts, ts, int(v_run)))
    conn.commit()
    samo_derp = len((iz_lege.v_feedu(zdaj) & vlaki) - {p[0] for p in pripete})
    return {"samo_sz": samo_sz, "oba": oba, "samo_derp": samo_derp}


def primerjava(conn: sqlite3.Connection, od_ts: int, najvec: int = 0) -> dict:
    """Kako se zemljevid SŽ in derp.si razhajata na istih postankih.

    Samo postanki, kjer je `run` od derp.si (`v_run = 0`). `mediana_s` je
    zemljevid minus derp.si, v sekundah.
    """
    vrstice = conn.execute(
        "SELECT z.trip_id, z.service_date, z.stop_seq, z.delay_s AS sz, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS derp, z.zadnjic_ts, t.train_no, "
        "       st.name AS postaja "
        "FROM sz_zamuda z "
        "JOIN run r ON r.trip_id = z.trip_id AND r.service_date = z.service_date "
        "          AND r.stop_seq = z.stop_seq "
        "JOIN trip t ON t.trip_id = z.trip_id "
        "LEFT JOIN sched s ON s.trip_id = z.trip_id AND s.stop_seq = z.stop_seq "
        "LEFT JOIN station st ON st.stop_id = s.stop_id "
        "WHERE z.zadnjic_ts >= ? AND z.v_run = 0 "
        "  AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL", (od_ts,)).fetchall()
    razlike = sorted(r["sz"] - r["derp"] for r in vrstice)
    out = {
        "parov": len(razlike),
        "v_minuti": sum(abs(d) <= 60 for d in razlike),
        "nad_5_min": sum(abs(d) > 300 for d in razlike),
        "mediana_s": razlike[len(razlike) // 2] if razlike else None,
        "samo_sz": conn.execute(
            "SELECT COUNT(*) FROM sz_zamuda WHERE zadnjic_ts >= ? AND v_run = 1",
            (od_ts,)).fetchone()[0],
    }
    if najvec:
        out["najvecje"] = [
            {"vlak": r["train_no"], "dan": r["service_date"], "postaja": r["postaja"],
             "sz_min": round(r["sz"] / 60), "derp_min": round(r["derp"] / 60),
             "ob": _ura(r["zadnjic_ts"])}
            for r in sorted(vrstice, key=lambda r: -abs(r["sz"] - r["derp"]))[:najvec]
            if r["sz"] != r["derp"]]
    return out


def _get() -> list[dict]:
    r = requests.get(f"{config.PERONI_URL}/lokacije",
                     headers={"User-Agent": config.USER_AGENT}, timeout=30)
    r.raise_for_status()
    return r.json()


def korak(conn: sqlite3.Connection, vrstice: list[dict], zdaj: float) -> dict:
    """En odgovor zemljevida: pripni, zapiši, povzemi v `meta` za pregled."""
    po_stevilki = vozni_red(conn, datetime.fromtimestamp(zdaj, TZ).date())
    pripete, stevci = razberi(vrstice, po_stevilki, zdaj)
    vlaki = {v["trip_id"] for vv in po_stevilki.values() for v in vv}
    stevci.update(zapisi(conn, pripete, zdaj, vlaki))
    stevci["ts"] = int(zdaj)
    stevci["primerjava"] = primerjava(conn, int(zdaj) - 86400)
    db.set_meta(conn, "zamude_sz", json.dumps(stevci, sort_keys=True))
    conn.commit()
    return stevci


def _stanje(s: dict) -> str:
    """Kateri vir nosi vlake -- za dnevnik ob spremembi, ne ob vsakem branju."""
    if not s.get("vlakov"):
        return "zemljevid SŽ brez vlakov"
    if s["samo_sz"] and not s["oba"]:
        return "derp.si brez vlakov, zamude z zemljevida SŽ"
    if s["samo_derp"] and not s["oba"]:
        return "zemljevid SŽ brez vlakov, ki jih ima derp.si"
    return "oba vira"


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: vir je tretja oseba in zna obviseti (25. 9. 2026 deset minut
    samih timeoutov) -- v zajemni zanki bi to zamaknilo zamude."""
    conn = db.connect()
    napak, stanje = 0, None
    try:
        while not stop.is_set():
            # Dokler zajem feeda derp.si ni prebral, ne vemo, katere vlake
            # nosi -- vsak bi bil „samo SŽ“ in šel v `run` mimo derp.si.
            if not iz_lege.feed_prebran():
                stop.wait(10)
                continue
            zdaj = time.time()
            try:
                s = korak(conn, _get(), zdaj)
                if napak:
                    log(f"zemljevid SŽ spet odgovarja (po {napak} napakah)")
                napak = 0
                if _stanje(s) != stanje:
                    stanje = _stanje(s)
                    log(f"zamude vlakov: {stanje} ({s['vlakov']} vlakov na zemljevidu, "
                        f"{s['oba']} v obeh, {s['samo_sz']} samo SŽ, "
                        f"{s['samo_derp']} samo derp.si, {s['nepripetih']} nepripetih)")
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                # Brez tega je nit obstala za vedno. 1. 10. 2026 ob 3:30 je
                # nočno vzdrževanje drlo pisanje dlje od 30 s, `korak` je
                # odnehal sredi transakcije, `get_meta` spodaj je v njej
                # zamrznil posnetek in vsako nadaljnje pisanje je vrnilo
                # „database is locked“ (SQLITE_BUSY_SNAPSHOT, čakanje ne
                # pomaga). Zemljevid SŽ 4 h brez zapisa, WAL zrasel na 5,4 GB,
                # ker ga za odprtim posnetkom ni mogoče prepisati.
                conn.rollback()
                napak += 1
                if napak == 1:
                    log(f"zemljevid SŽ ne odgovarja: {exc}")
                # Zadnji uspešni števci ostanejo; pregled po `napaka_ts`
                # vidi, da so stari in zakaj.
                try:
                    s = json.loads(db.get_meta(conn, "zamude_sz") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(zdaj))
                    db.set_meta(conn, "zamude_sz", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            stop.wait(config.SZ_ZAMUDE_SECONDS)
    finally:
        conn.close()
