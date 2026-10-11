"""Zamude vlakov z zemljevida SŽ, prebrane naravnost s potniski.sz.si.

Zakaj: zemljevid vlakov na potniski.sz.si (`admin-ajax.php?action=aktivni_vlaki`)
je izvor vseh zamud vlakov, ki smo jih kdaj imeli. derp.si jih je bral z
`api.modra.ninja/sz/lokacije` (8. 10. 2026, `szService.js`), ta pa s tega
naslova -- polja so ista, le preimenovana. 7. 10. 2026 ob 1:24 sta posrednika
utihnila, ker jima Cloudflare strani ni več odprl; mi jo beremo s Chromom
(`brskalnik.py`). Od 10. 10. 2026 ta vir **vodi** zamude vlakov: zajem derp.si
vlakov ne piše, dokler je zemljevid prebran (`iz_lege.sz_vodi`) -- isti
podatek prek dveh posrednikov je le starejši.

Vlak tam nosi številko, ne id vožnje iz zipa, zato ga pokvarjen zip DUJPP ne
prizadene (28. 9. 2026 je derp.si izgubil vse vlake, zemljevid ne).

Kaj vrstica pove, po polju `Vrsta` (izmerjeno 10. 10. 2026, 84 branj po 15 s):

* **1 -- vozi.** `Postaja` je naslednja postaja, `Odhod` voznoredni odhod s
  postaje PRED njo plus `Zamuda_cas` (izmerjeno na 12 vlakih 28. 9. 2026, ko
  je isto bral modra.ninja). Zamuda je torej odhodna zamuda zadnjega
  prevoženega postanka; enakost je hkrati preizkus, da je vlak pripet na
  pravo vožnjo in dan.
* **0 -- še stoji na izhodišču.** `Odhod` je voznoredni odhod. Ni meritev.
* **2 -- na cilju.** `Postaja` je prazna, `Odhod` prihod na cilj, `Zamuda_cas`
  zamuda ob prihodu. Ostane 1--2 min, nato ga SŽ ponastavi na zamudo 0 ob
  voznorednem prihodu (1897: +7, dve minuti pozneje 0; 3287: +8, nato 0).
  Šteje zato samo prvi prihod.

Vsaka vrednost gre v `sz_zamuda` (zadnje stanje na postanek, s časom prvega in
zadnjega branja) in v `run` in `obs`.

Tabla zamud SŽ (`/pomoc-uporabnikom-in-stanje-v-prometu/`) se ne bere: v senci
11. 10. 2026 je isto minuto na 246 parih pokazala le nekaj sekund pred
zemljevidom, pripeti pa bi se dala tretjina njenih vrstic (docs/MERITVE.md).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

from . import brskalnik, collector, config, db, iz_lege, stats, viri
from .peroni import _kljuc_imena, stevilka

TZ = ZoneInfo(config.TIMEZONE)

#: Zemljevid vlakov SŽ. Isti naslov bere njihova stran vsakih 15 s
#: (`setInterval(…, 15e3)` v `main-*.js`), toliko je tudi takt odgovora.
AKTIVNI = "/wp-admin/admin-ajax.php?action=aktivni_vlaki"

#: Toliko sme `Odhod` odstopati od voznega reda plus zamude. Oboje je v
#: celih minutah, zato ena minuta za zaokroževanje.
ODSTOPA_ODHOD_S = 60
#: Odhod, starejši od tega, ni odhod te vožnje, ampak ista številka drug dan.
NAJSTAREJSI_ODHOD_S = 6 * 3600
#: Prihod z zamudo 0 po vožnji z več kot toliko zamude je SŽ-jeva ponastavitev
#: vrstice na cilju, ne prihod (glava modula).
PONASTAVITEV_S = 180


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


def je_avtobus(vrstica: dict) -> bool:
    return (str(vrstica.get("Vrsta_vlaka") or "").upper() == "B"
            or str(vrstica.get("Rang") or "").upper() == "BUS")


def _ujema(dan: str, t_s: int | None, zamuda_min: int, odhod_min: int,
           zdaj: float) -> float | None:
    """Koliko je minilo od voznega reda plus zamude, kadar se ura ujema z
    `Odhod`; sicer None."""
    if t_s is None:
        return None
    kdaj = stats.polnoc(dan) + t_s + zamuda_min * 60
    if not (-ODSTOPA_ODHOD_S <= zdaj - kdaj <= NAJSTAREJSI_ODHOD_S):
        return None
    # Ura z zemljevida je lokalna ura dneva; primerjava po modulu dneva,
    # ker vlak čez polnoč odpelje ob 00:10 prometnega dne včeraj.
    ura = _minute(_ura(kdaj))
    if min((ura - odhod_min) % 1440, (odhod_min - ura) % 1440) * 60 > ODSTOPA_ODHOD_S:
        return None
    return zdaj - kdaj


def pripni(vrstica: dict, voznje: list[dict], zdaj: float) -> tuple | None:
    """Vrstica zemljevida -> (trip_id, dan, stop_seq, zamuda_s, je_prihod) ali None.

    Vozi: postanek je zadnji prevoženi, torej tisti PRED `Postaja`. Na cilju:
    zadnji postanek vožnje. Od več voženj z isto številko (sezonske različice,
    včeraj in danes) velja tista, pri kateri se `Odhod` ujema z voznim redom
    plus zamudo; kadar se ne ujema nobena, vlaka ne pripnemo -- raje nič kot na
    napačno vožnjo.
    """
    zamuda = vrstica.get("Zamuda_cas")
    odhod = _minute(vrstica.get("Odhod"))
    vrsta = vrstica.get("Vrsta")
    if zamuda is None or odhod is None or vrsta not in (1, 2):
        return None
    naslednja = _kljuc_imena(vrstica.get("Postaja") or "")
    if vrsta == 1 and not naslednja:
        return None
    najboljsa, razmik = None, None
    for v in voznje:
        p = v["postanki"]
        if vrsta == 2:
            seq, _, arr, dep = p[-1]
            kandidati = [(seq, arr if arr is not None else dep)]
        else:
            kandidati = [(p[i - 1][0], p[i - 1][3] if p[i - 1][3] is not None else p[i - 1][2])
                         for i in range(1, len(p)) if p[i][1] == naslednja]
        for seq, t_s in kandidati:
            r = _ujema(v["dan"], t_s, zamuda, odhod, zdaj)
            if r is not None and (razmik is None or r < razmik):
                najboljsa, razmik = (v["trip_id"], v["dan"], seq, zamuda * 60, vrsta == 2), r
    return najboljsa


def razberi(vrstice: list[dict], po_stevilki: dict[str, list[dict]],
            zdaj: float) -> tuple[list[tuple], dict]:
    """Vse vrstice zemljevida -> (pripete, števci)."""
    pripete = []
    stevci = {"vlakov": 0, "pred_odhodom": 0, "na_cilju": 0, "nepripetih": 0}
    for r in vrstice:
        if je_avtobus(r):
            continue
        stevci["vlakov"] += 1
        if r.get("Vrsta") == 0:
            stevci["pred_odhodom"] += 1
            continue
        stevci["na_cilju"] += r.get("Vrsta") == 2
        p = pripni(r, po_stevilki.get(stevilka(str(r.get("St_vlaka") or "")), []), zdaj)
        if p is None:
            stevci["nepripetih"] += 1
        else:
            pripete.append(p)
    return pripete, stevci


def zapisi(conn: sqlite3.Connection, pripete: list[tuple], zdaj: float) -> dict:
    """Pripete zamude v `sz_zamuda`, `run` in `obs`.

    Dve varovali, obe izmerjeni na zemljevidu 10. 10. 2026:

    * **Vlak ne gre nazaj.** LPV 2616 je ob 22:35 po Brezovici spet pisal
      „naslednja Ljubljana Tivoli, +9“ in se ujemal z odhodom iz Ljubljane --
      postaje, ki jo je s +0 zapustil 10 min prej. Postanek pred zadnjim
      zapisanim se zato ne prepiše.
    * **Na cilju šteje prvi prihod** (glava modula), in ničla po zamudi nad
      `PONASTAVITEV_S` ni prihod, ampak ponastavitev.
    """
    ts = int(zdaj)
    izid = {"zapisanih": 0, "nazaj": 0, "ponastavljenih": 0}
    for trip_id, dan, seq, zamuda, je_prihod in pripete:
        zadnji = conn.execute(
            "SELECT stop_seq, delay_s FROM sz_zamuda WHERE trip_id = ? AND service_date = ? "
            "ORDER BY stop_seq DESC LIMIT 1", (trip_id, dan)).fetchone()
        if zadnji and seq < zadnji[0]:
            izid["nazaj"] += 1
            continue
        if je_prihod and zadnji:
            if seq == zadnji[0]:
                continue                       # prihod je že zapisan
            if zamuda == 0 and zadnji[1] > PONASTAVITEV_S:
                izid["ponastavljenih"] += 1
                continue
        iz_lege.zapisi_meritev(conn, trip_id, dan, seq, zamuda if je_prihod else None,
                               None if je_prihod else zamuda, ts, ohrani=True)
        conn.execute(
            "INSERT INTO sz_zamuda(trip_id, service_date, stop_seq, delay_s, "
            "                      prvic_ts, zadnjic_ts, v_run) VALUES(?,?,?,?,?,?,1) "
            "ON CONFLICT(trip_id, service_date, stop_seq) DO UPDATE SET "
            "  delay_s = excluded.delay_s, zadnjic_ts = excluded.zadnjic_ts, v_run = 1",
            (trip_id, dan, seq, zamuda, ts, ts))
        izid["zapisanih"] += 1
    conn.commit()
    return izid


#: Odtis zadnjega odgovora: nespremenjen zemljevid je v /admin opomba, dolgo
#: nespremenjen ob vlakih na poti pa opozorilo (`zdravje.ocena`).
_odtis: str | None = None


def _get() -> list[dict]:
    global _odtis
    with viri.branje("zamude_sz") as b:
        besedilo = brskalnik.zahtevaj(AKTIVNI)
        b.http, b.bajtov = 200, len(besedilo.encode())
        try:
            vrstice = json.loads(besedilo)
        except ValueError:
            raise RuntimeError("zemljevid SŽ ni vrnil JSON") from None
        # Ko ne vozi noben vlak, SŽ vrne `null`, ne prazen seznam (izmerjeno
        # 10. 10. 2026 ob 23:58).
        if vrstice is None:
            vrstice = []
        if not isinstance(vrstice, list):
            raise RuntimeError("zemljevid SŽ ni vrnil seznama vlakov")
        odtis = hashlib.blake2s(besedilo.encode(), digest_size=8).hexdigest()
        b.nespremenjeno = odtis == _odtis
        _odtis = odtis
        return vrstice


def korak(conn: sqlite3.Connection, vrstice: list[dict], zdaj: float,
          nespremenjeno: bool = False) -> dict:
    """En odgovor zemljevida: pripni, zapiši, povzemi v `meta` za pregled.

    Nespremenjen odgovor (dve od treh branj, ker beremo na 5 s, SŽ pa
    preračuna na 15) samo potrdi, da vir živi: znova zapisan bi vsaki vrednosti
    premaknil čas zadnjega podatka, čeprav SŽ ni povedal nič novega.
    """
    prej = json.loads(db.get_meta(conn, "zamude_sz") or "{}")
    if nespremenjeno and prej.get("odtis") == _odtis and "vlakov" in prej:
        prej["ts"] = int(zdaj)
        prej.pop("napaka", None)
        prej.pop("napaka_ts", None)
        db.set_meta(conn, "zamude_sz", json.dumps(prej, sort_keys=True))
        conn.commit()
        return prej
    po_stevilki = vozni_red(conn, datetime.fromtimestamp(zdaj, TZ).date())
    pripete, stevci = razberi(vrstice, po_stevilki, zdaj)
    stevci.update(zapisi(conn, pripete, zdaj))
    odtis = _odtis or ""
    stevci["odtis"] = odtis
    stevci["spremenjeno_ts"] = (prej.get("spremenjeno_ts") if prej.get("odtis") == odtis
                                else None) or int(zdaj)
    stevci["ts"] = int(zdaj)
    db.set_meta(conn, "zamude_sz", json.dumps(stevci, sort_keys=True))
    conn.commit()
    return stevci


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: brskalnik zna obviseti (izziv do 90 s) -- v zajemni zanki bi
    to zamaknilo zamude avtobusov."""
    conn = db.connect()
    napak, prvic = 0, True
    try:
        while not stop.is_set():
            zdaj = time.time()
            try:
                prej = _odtis
                vrstice = _get()
                s = korak(conn, vrstice, zdaj, nespremenjeno=prej is not None and _odtis == prej)
                iz_lege.sz_prebran(zdaj)
                if napak or prvic:
                    log(f"zemljevid SŽ {'spet ' if napak else ''}odgovarja"
                        f"{f' (po {napak} napakah)' if napak else ''}: {s['vlakov']} vlakov, "
                        f"{s['zapisanih']} zapisanih, {s['nepripetih']} nepripetih; "
                        "zamude vlakov vodi zemljevid SŽ")
                napak, prvic = 0, False
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
                    log(f"zemljevid SŽ ne odgovarja: {exc}; zamude vlakov spet piše "
                        f"derp.si, ko mine {iz_lege.SZ_VODI_S} s")
                # Zadnji uspešni števci ostanejo; pregled po `napaka_ts`
                # vidi, da so stari in zakaj.
                try:
                    s = json.loads(db.get_meta(conn, "zamude_sz") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(zdaj))
                    db.set_meta(conn, "zamude_sz", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            # Takt od začetka branja, ne od konca: branje (0,5--0,8 s, dlje,
            # ko brskalnik bere tablo postaje) bi ga sicer raztegnilo.
            stop.wait(max(0.5, config.SZ_ZAMUDE_SECONDS - (time.time() - zdaj),
                          brskalnik.pocitek_s() if napak else 0.0))
    finally:
        conn.close()
