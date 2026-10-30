"""Opazovano: pri katerih postajališčih vozila zadnje čase ne ustavijo.

Zakaj (`docs/OPAZOVANO.md`): objavljeni podatki povedo, kaj naj bi vozilo
delalo, ne kaj dela. Obvoz G2 mimo Focheve (Maribor) je potnik izvedel iz časopisa.
Tu **ni pogoja po prevozniku**: vir pove le lege in prehode (`lega`,
`gps_prehod`), pomen izračuna ta koda. Zaenkrat samo senca, prikaz tega ne bere.

Pravilo, izmerjeno na 14 dneh (`docs/MERITVE.md`, „Opazovano, del 2“):

* **Dokaz** = obkrožena vožnja (prehod pred postankom in za njim) brez prehoda,
  v sledi ni luknje, najbližja točka vsaj `PRAG_M` od postajališča.
* **Odpre**: vsaj `ODPRE_DOKAZOV` zaporednih dokazov, med prvim in zadnjim vsaj
  `ODPRE_RAZPON_S`.
* **Zapre**: prvi prehod ali dokaz bliže od `PRAG_M`. **Pozabi**: `POZABI_S` po
  zadnjem dokazu.

Ključ je (prevoznik, linija, smer, `stop_id`), ne `shape_id` in ne `trip_id`:
oba se ob uvozu voznega reda zamenjata (Marprom 27. 10. 2026) in stanje bi
izgubilo zgodovino. Dan se obdela **enkrat**, po vrsti, stanje in meja
(`opazovano_dan`) gresta v isti commit: stanje je rezultat vseh dni do meje, ne
računa se iz `lega`, ki izgine po 14 dneh.

„Ne ustavi“ iz leg še ni trditev: pri 1119 so med ničlami pogoste napake
koordinate. Zato vrstica hrani neodvisen dokaz, da je postajališče res tam
(`_neodvisno`), in `oznaka` iz njega.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import statistics
import time
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from . import db, stats
from .naslovi import fold
from .straza import TZ, ZACETEK_DNE_S

PRAG_M = 250            # DMIN 400 zgreši Focheva (315 in 328 m), 150 doda 3 napačne
ODPRE_DOKAZOV = 10
ODPRE_RAZPON_S = 24 * 3600
POZABI_S = 7 * 86400

#: Vrzel nad tem = luknja v sledi, tam ni mogoče reči ničesar (34 % obkroženih
#: voženj pri kandidatih, Orešje/Bizeljsko 396 od 398).
LUKNJA_S = 120
#: Vrzel okoli najbližje točke: tetiva čez daljšo bi obvoz izmislila.
VRZEL_S = 40

#: Mediana iz zadnjih toliko dokazov.
TOCK = 30

#: OSM postajališče je „na koordinati“ ali „ob poti vozila“ tako blizu.
OSM_M = 60
#: Druge linije potrdijo koordinato: vsaj toliko obkroženih voženj, tolikšen delež
#: prehodov. Vozilo tja torej pride, koordinata ni zgrešena.
DRUGE_VOZENJ = 10
DRUGE_DELEZ = 0.2
#: Toliko dni nazaj štejejo obiski, kolikor hrani `lega`.
OBISKI_DNI = 14

OSM_DATOTEKA = Path(__file__).with_name("osm_postajalisca.json")

#: Besede, ki pri primerjavi imen postajališč nič ne povedo.
_POLNILA = ("pri", "bus", "pos", "ulica", "cesta")
_M_NA_STOPINJO = 111194.9
_POLJA = ("prevoznik", "linija", "smer", "stop_id", "prvi_ts", "zadnji_ts", "dokazov",
          "stanje", "odprto_ts", "zaprto_ts", "vzrok", "dmin_m", "lat", "lon", "tocke",
          "osm_ime", "osm_blizu", "osm_ob_poti", "druge_obkrozenih", "druge_prehodov",
          "oznaka", "preverjeno_ts")


# ---------------------------------------------------------------- ena vožnja

def _najblizja(lega: list[tuple], lat: float, lon: float, od: int, do: int):
    """Najbližja točka sledi med dvema prehodoma: (dmin, lat, lon, ts) ali None,
    če sled ni zanesljiva. Razdalja do tetive med legama, ne do same lege: pri
    legi na 20 s bi bil avtobus pri 50 km/h 280 m stran že med točkama."""
    kx = math.cos(math.radians(lat)) * _M_NA_STOPINJO
    sx, sy = lon * kx, lat * _M_NA_STOPINJO
    naj = None
    vrzel = 0
    for i in range(max(0, bisect_left(lega, (od,)) - 1), len(lega) - 1):
        (t1, la1, lo1), (t2, la2, lo2) = lega[i], lega[i + 1]
        if t2 < od:
            continue
        if t1 > do:
            break
        if t2 - t1 > LUKNJA_S:
            return None
        x1, y1 = lo1 * kx, la1 * _M_NA_STOPINJO
        dx, dy = lo2 * kx - x1, la2 * _M_NA_STOPINJO - y1
        d2 = dx * dx + dy * dy
        f = 0.0 if d2 == 0 else max(0.0, min(1.0, ((sx - x1) * dx + (sy - y1) * dy) / d2))
        x, y = x1 + f * dx, y1 + f * dy
        d = math.hypot(x - sx, y - sy)
        if naj is None or d < naj[0]:
            naj = (d, y / _M_NA_STOPINJO, x / kx, t1 + f * (t2 - t1))
            vrzel = t2 - t1
    if naj is None or vrzel > VRZEL_S:
        return None
    return round(naj[0]), round(naj[1], 5), round(naj[2], 5), int(naj[3])


# ---------------------------------------------------------------- dogodki dneva

def _vozni(conn: sqlite3.Connection) -> dict[str, tuple]:
    """{trip_id: (prevoznik, linija, smer)}. Nagrobnik obdrži vrstico v `trip`,
    `sched` pa ne: tam stop_id ni znan in vožnja odpade."""
    return {r[0]: (r[1] or "?", r[2], r[3] or "") for r in conn.execute(
        "SELECT trip_id, agency, train_no, headsign FROM trip")}


def _dogodki_dneva(conn: sqlite3.Connection, dan: str, vozni: dict, zivi: set) -> dict:
    """Urejeni dogodki enega prometnega dne.

    Preskoči, česar stanje ne more videti: nedokazana vožnja pred zadnjim
    prehodom dneva nima vpliva (prehod jo pretrga), odprt niz pa zapre že prvi
    prehod. Zato se sled bere pri 13 % voženj (1 239 od 9 560, 29. 10. 2026), dan
    pa traja 3 s.
    """
    prehodi: dict[str, dict] = defaultdict(dict)
    for trip_id, seq, ts in conn.execute(
            "SELECT trip_id, stop_seq, prehod_ts FROM gps_prehod WHERE service_date = ?", (dan,)):
        prehodi[trip_id][seq] = ts
    p_prvi: dict[tuple, int] = {}
    p_zadnji: dict[tuple, int] = {}
    kandidati: dict[tuple, list] = defaultdict(list)
    brez_sched = 0
    for trip_id, seqs in prehodi.items():
        meta = vozni.get(trip_id)
        postanki = conn.execute("SELECT stop_seq, stop_id FROM sched WHERE trip_id = ? "
                                "ORDER BY stop_seq", (trip_id,)).fetchall()
        if meta is None or not postanki:
            brez_sched += 1
            continue
        po_vrsti = sorted(seqs)
        for seq, stop_id in postanki[1:]:      # izhodišča ne merimo: tam vožnja šele začne
            k = (*meta, stop_id)
            ts = seqs.get(seq)
            if ts is not None:
                p_prvi[k] = min(p_prvi.get(k, ts), ts)
                p_zadnji[k] = max(p_zadnji.get(k, ts), ts)
            elif po_vrsti[0] < seq < po_vrsti[-1]:
                i = bisect_left(po_vrsti, seq)
                kandidati[k].append((seqs[po_vrsti[i - 1]], seqs[po_vrsti[i]], trip_id))

    izbrani: dict[str, list] = defaultdict(list)
    for k, voznje in kandidati.items():
        prvi, zadnji = p_prvi.get(k), p_zadnji.get(k)
        for od, do, trip_id in voznje:
            if zadnji is None or od >= zadnji or (k in zivi and od < prvi):
                izbrani[trip_id].append((k, od, do))

    koord = {}
    dogodki = []
    for trip_id, cilji in izbrani.items():
        lega = conn.execute("SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? "
                            "ORDER BY ts", (dan, trip_id)).fetchall()
        lega = [tuple(r) for r in lega]
        for k, od, do in cilji:
            s = k[3]
            if s not in koord:
                koord[s] = conn.execute("SELECT lat, lon FROM station WHERE stop_id = ?",
                                        (s,)).fetchone()
            if koord[s] is None:
                continue
            r = _najblizja(lega, koord[s][0], koord[s][1], od, do)
            if r is not None:
                dogodki.append((r[3], k, "dokaz", r[0], r[1], r[2]))
    dokazov = len(dogodki)
    for k in {d[1] for d in dogodki} | (zivi & set(p_prvi)):
        for ts in {p_prvi[k], p_zadnji[k]} if k in p_prvi else ():
            dogodki.append((ts, k, "prehod", None, None, None))
    dogodki.sort(key=lambda d: d[0])
    return {"dogodki": dogodki, "voznje": len(prehodi), "brez_sched": brez_sched,
            "sledi": len(izbrani), "dokazov": dokazov}


# ---------------------------------------------------------------- stanje

def _uporabi(zivi: dict, zaprti: list, dogodki: list) -> None:
    """Dogodke po času na stanje; edino mesto s pravilom odpre, zapre, pozabi."""
    for ts, k, vrsta, d, lat, lon in dogodki:
        v = zivi.get(k)
        if v and ts - v["zadnji_ts"] > POZABI_S:
            _koncaj(zivi, zaprti, k, "zastarelo", v["zadnji_ts"] + POZABI_S)
            v = None
        if vrsta == "prehod" or d < PRAG_M:
            if v:
                _koncaj(zivi, zaprti, k, "prehod" if vrsta == "prehod" else "blizu", ts)
            continue
        if v is None:
            v = zivi[k] = dict.fromkeys(_POLJA) | {
                "prevoznik": k[0], "linija": k[1], "smer": k[2], "stop_id": k[3],
                "prvi_ts": ts, "dokazov": 0, "stanje": "niz", "tocke": []}
        v["dokazov"] += 1
        v["zadnji_ts"] = ts
        v["tocke"] = (v["tocke"] + [[d, lat, lon]])[-TOCK:]
        if (v["stanje"] == "niz" and v["dokazov"] >= ODPRE_DOKAZOV
                and ts - v["prvi_ts"] >= ODPRE_RAZPON_S):
            v["stanje"] = "ne_ustavi"
            v["odprto_ts"] = ts


def _koncaj(zivi: dict, zaprti: list, k: tuple, vzrok: str, ts: int) -> None:
    """Odprta vrstica ostane kot zgodovina; niz, ki ni nikoli odprl, izgine."""
    v = zivi.pop(k)
    if v["stanje"] == "ne_ustavi":
        v.update(stanje="zaprto", zaprto_ts=ts, vzrok=vzrok)
        zaprti.append(v)


def _konec_dneva(dan: str) -> int:
    return stats.polnoc(dan) + 24 * 3600 + ZACETEK_DNE_S


def _pozabi(zivi: dict, zaprti: list, zdaj: int) -> None:
    """Stanje brez novih dokazov: vožnje so izginile (sezonska linija), o
    postajališču ne vemo več ničesar."""
    for k, v in list(zivi.items()):
        if zdaj - v["zadnji_ts"] > POZABI_S:
            _koncaj(zivi, zaprti, k, "zastarelo", v["zadnji_ts"] + POZABI_S)


def _zapis(v: dict) -> dict:
    t = v["tocke"]
    return v | {"tocke": json.dumps(t, separators=(",", ":")),
                "dmin_m": round(statistics.median(x[0] for x in t)),
                "lat": round(statistics.median(x[1] for x in t), 5),
                "lon": round(statistics.median(x[2] for x in t), 5)}


def _shrani(conn: sqlite3.Connection, zivi: dict, zaprti: list) -> None:
    """Brez commita: mejo dneva zapiše klicatelj v isti transakciji."""
    conn.execute("DELETE FROM opazovano WHERE stanje IN ('niz', 'ne_ustavi')")
    ukaz = (f"INSERT OR REPLACE INTO opazovano({', '.join(_POLJA)}) "
            f"VALUES({', '.join(':' + p for p in _POLJA)})")
    conn.executemany(ukaz, [_zapis(v) for v in (*zivi.values(), *zaprti)])


def _nalozi(conn: sqlite3.Connection) -> dict:
    zivi = {}
    for r in conn.execute(f"SELECT {', '.join(_POLJA)} FROM opazovano "
                          "WHERE stanje IN ('niz', 'ne_ustavi')"):
        v = dict(zip(_POLJA, r))
        v["tocke"] = json.loads(v["tocke"])
        zivi[(v["prevoznik"], v["linija"], v["smer"], v["stop_id"])] = v
    return zivi


# ---------------------------------------------------------------- neodvisen dokaz

@lru_cache(maxsize=1)
def _osm() -> dict | None:
    """Mreža OSM postajališč; None brez posnetka: „ne vem“, ne „ni postajališča“."""
    try:
        vrstice = json.loads(OSM_DATOTEKA.read_text(encoding="utf-8"))["postajalisca"]
    except (OSError, ValueError, KeyError):
        return None
    mreza: dict[tuple, list] = defaultdict(list)
    for lat, lon, ime in vrstice:
        mreza[(int(lat * 1000), int(lon * 1000))].append((lat, lon, ime))
    return dict(mreza)


def _ime(s: str) -> frozenset:
    return frozenset(t for t in re.split(r"[^a-z0-9]+", fold(s))
                     if len(t) > 2 and t not in _POLNILA)


def _osm_blizu(mreza: dict, lat: float, lon: float) -> list[str]:
    """Imena OSM postajališč v `OSM_M`; neimenovano = prazno ime."""
    kx = math.cos(math.radians(lat)) * _M_NA_STOPINJO
    out = []
    a, b = int(lat * 1000), int(lon * 1000)
    for i in range(a - 1, a + 2):
        for j in range(b - 1, b + 2):
            for la, lo, ime in mreza.get((i, j), ()):
                if math.hypot((lo - lon) * kx, (la - lat) * _M_NA_STOPINJO) < OSM_M:
                    out.append(ime)
    return out


def _obiski(conn: sqlite3.Connection, stop_id: str, dnevi: list[str]) -> dict[tuple, list]:
    """{(prevoznik, linija, smer): [obkroženih voženj, od tega s prehodom]} pri postanku."""
    voznje = conn.execute(
        "SELECT s.trip_id, s.stop_seq, t.agency, t.train_no, t.headsign FROM sched s "
        "JOIN trip t ON t.trip_id = s.trip_id WHERE s.stop_id = ?", (stop_id,)).fetchall()
    ids = json.dumps(sorted({r[0] for r in voznje}))
    out: dict[tuple, list] = defaultdict(lambda: [0, 0])
    for dan in dnevi:
        seqs: dict[str, set] = defaultdict(set)
        for trip_id, seq in conn.execute(
                "SELECT trip_id, stop_seq FROM gps_prehod WHERE service_date = ? "
                "AND trip_id IN (SELECT value FROM json_each(?))", (dan, ids)):
            seqs[trip_id].add(seq)
        for trip_id, seq, agency, no, smer in voznje:
            s = seqs.get(trip_id)
            if s and min(s) < seq < max(s):
                v = out[(agency or "?", no, smer or "")]
                v[0] += 1
                v[1] += seq in s
    return dict(out)


def oznaka(v: dict) -> str:
    """Kaj vrstica pomeni potniku, iz dokaza, ki ni iz sledi te vožnje.

    `pravi`: postajališče je res tam in vozilo ne ustavi pri istoimenskem drugje.
    `napacen`: istoimensko ob poti vozila, koordinata nepotrjena: najbrž zgrešena.
    `dvoumen`: oboje; „ne ustavi tu“ drži, potnik rabi napotek.
    `neznan`: koordinate ni potrdilo nič.
    """
    druge = ((v["druge_obkrozenih"] or 0) >= DRUGE_VOZENJ
             and (v["druge_prehodov"] or 0) >= DRUGE_DELEZ * v["druge_obkrozenih"])
    potrjena = bool(v["osm_ime"]) or druge
    if v["osm_ob_poti"]:
        return "dvoumen" if potrjena else "napacen"
    return "pravi" if potrjena else "neznan"


def dovolj_za_prikaz(v: dict) -> bool:
    """Predlog za del 3, prikaz tega še ne bere (`docs/OPAZOVANO.md`).

    Napaka tu pošlje potnika stran od avtobusa, zato mora biti na koordinati
    nekaj, kar ni sled te vožnje. `neznan` z `osm_blizu` (OSM ima postajališče
    tam, ime manjka ali je drugo) je Ormož bolnica, ročno preverjen pravi primer;
    pri 1119 je med neznanimi to 0 od 16.
    """
    return v["stanje"] == "ne_ustavi" and (
        v["oznaka"] == "pravi" or (v["oznaka"] == "neznan" and bool(v["osm_blizu"])))


def _neodvisno(conn: sqlite3.Connection, danes: date, zdaj: int) -> int:
    """Osveži odprte in vse še nepreverjene: zaprta vrstica obdrži, kar je veljalo."""
    vrstice = [dict(zip(_POLJA, r)) for r in conn.execute(
        f"SELECT {', '.join(_POLJA)} FROM opazovano WHERE stanje = 'ne_ustavi' "
        "OR (stanje = 'zaprto' AND preverjeno_ts IS NULL)")]
    if not vrstice:
        return 0
    mreza = _osm()
    dnevi = [(danes - timedelta(days=i)).isoformat() for i in range(1, OBISKI_DNI + 1)]
    obiski: dict[str, dict] = {}
    for v in vrstice:
        s = conn.execute("SELECT name, lat, lon FROM station WHERE stop_id = ?",
                         (v["stop_id"],)).fetchone()
        if s is None:
            continue
        if mreza is not None:
            ime = _ime(s[0])
            blizu = _osm_blizu(mreza, s[1], s[2])
            v["osm_blizu"] = int(bool(blizu))
            v["osm_ime"] = int(bool(ime) and any(_ime(n) == ime for n in blizu))
            v["osm_ob_poti"] = int(bool(ime) and any(
                _ime(n) == ime for n in _osm_blizu(mreza, v["lat"], v["lon"])))
        if v["stop_id"] not in obiski:
            obiski[v["stop_id"]] = _obiski(conn, v["stop_id"], dnevi)
        k = (v["prevoznik"], v["linija"], v["smer"])
        drugi = [o for kk, o in obiski[v["stop_id"]].items() if kk != k]
        v["druge_obkrozenih"] = sum(o[0] for o in drugi)
        v["druge_prehodov"] = sum(o[1] for o in drugi)
        v["oznaka"] = oznaka(v)
        v["preverjeno_ts"] = zdaj
    conn.executemany(
        "UPDATE opazovano SET osm_ime = :osm_ime, osm_blizu = :osm_blizu, "
        "osm_ob_poti = :osm_ob_poti, druge_obkrozenih = :druge_obkrozenih, "
        "druge_prehodov = :druge_prehodov, oznaka = :oznaka, preverjeno_ts = :preverjeno_ts "
        "WHERE prevoznik = :prevoznik AND linija = :linija AND smer = :smer "
        "AND stop_id = :stop_id AND prvi_ts = :prvi_ts", vrstice)
    conn.commit()
    return len(vrstice)


# ---------------------------------------------------------------- nočni izračun

def obdelaj_dan(conn: sqlite3.Connection, dan: str, vozni: dict) -> dict:
    """En dan: stanje, meja in številke gredo v isti commit."""
    zacetek = time.perf_counter()
    zivi = _nalozi(conn)
    zaprti: list[dict] = []
    r = _dogodki_dneva(conn, dan, vozni, set(zivi))
    _uporabi(zivi, zaprti, r["dogodki"])
    _pozabi(zivi, zaprti, _konec_dneva(dan))
    _shrani(conn, zivi, zaprti)
    ms = round(1000 * (time.perf_counter() - zacetek))
    conn.execute("INSERT OR REPLACE INTO opazovano_dan(dan, izracunano, voznje, brez_sched, "
                 "sledi, dokazov, ms) VALUES(?,?,?,?,?,?,?)",
                 (dan, int(time.time()), r["voznje"], r["brez_sched"], r["sledi"], r["dokazov"], ms))
    conn.commit()
    return {"dan": dan, "ms": ms, **{k: r[k] for k in ("voznje", "brez_sched", "sledi", "dokazov")}}


def _dnevi(conn: sqlite3.Connection, danes: date) -> list[str]:
    """Od meje do včeraj. Prvi dan v `lega` je lahko obrezan, zato začne dan za njim."""
    zadnji = conn.execute("SELECT MAX(dan) FROM opazovano_dan").fetchone()[0]
    if zadnji:
        d = date.fromisoformat(zadnji) + timedelta(days=1)
    else:
        najstarejsi = conn.execute("SELECT MIN(service_date) FROM lega").fetchone()[0]
        if not najstarejsi:
            return []
        d = date.fromisoformat(najstarejsi) + timedelta(days=1)
    out = []
    while d < danes:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def dopolni(conn: sqlite3.Connection, danes: date | None = None) -> list[str]:
    """Obdelaj dneve od meje do včeraj in osveži neodvisen dokaz. Vrne dneve.

    Vožnja, ki ob računu še vozi, v svoj dan ne pride. Izguba je majhna: ob 3:30
    avtobusov skoraj ni, zamujeni prehod pa zapre stanje naslednji dan.
    """
    danes = danes or datetime.now(TZ).date()
    dnevi = _dnevi(conn, danes)
    if dnevi:
        vozni = _vozni(conn)
        for dan in dnevi:
            obdelaj_dan(conn, dan, vozni)
    _neodvisno(conn, danes, int(time.time()))
    return dnevi


def senca(conn: sqlite3.Connection) -> None:
    """Tabele v `temp`: isti račun na bazi z `mode=ro`, nič se ne zapiše. `temp`
    ima prednost pred `main`, zato dela tudi, kjer tabela že obstaja."""
    conn.executescript(db.OPAZOVANO.replace("CREATE TABLE IF NOT EXISTS ", "CREATE TEMP TABLE "))


# ---------------------------------------------------------------- izpis

def _cas(ts: int | None) -> str:
    return "–" if ts is None else datetime.fromtimestamp(ts, TZ).strftime("%d. %m. %H:%M")


def beri(conn: sqlite3.Connection, vsa: bool = False) -> list[dict]:
    pogoj = "stanje != 'niz'" if vsa else "stanje = 'ne_ustavi'"
    return [dict(zip(_POLJA, r)) for r in conn.execute(
        f"SELECT {', '.join(_POLJA)} FROM opazovano WHERE {pogoj} "
        "ORDER BY prevoznik, linija, stop_id, prvi_ts")]


def izpis(conn: sqlite3.Connection, vsa: bool = False) -> str:
    """Vsota po prevozniku in oznaki, nato vrstice."""
    vrstice = beri(conn, vsa)
    imena = dict(conn.execute("SELECT stop_id, name FROM station WHERE stop_id IN "
                              "(SELECT value FROM json_each(?))",
                              (json.dumps(sorted({v['stop_id'] for v in vrstice})),)).fetchall())
    po: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    for v in vrstice:
        if v["stanje"] == "ne_ustavi":
            po[v["prevoznik"]]["odprtih"] += 1
            po[v["prevoznik"]][v["oznaka"] or "neznan"] += 1
            po[v["prevoznik"]]["prikaz"] += dovolj_za_prikaz(v)
    out = [f"{'prevoznik':10} {'odprtih':>7} {'pravi':>5} {'dvoumen':>7} {'napacen':>7} "
           f"{'neznan':>6} {'za prikaz':>9}"]
    for p in sorted(po):
        c = po[p]
        out.append(f"{p:10} {c['odprtih']:>7} {c['pravi']:>5} {c['dvoumen']:>7} "
                   f"{c['napacen']:>7} {c['neznan']:>6} {c['prikaz']:>9}")
    out.append("")
    for v in vrstice:
        konec = f" do {_cas(v['zaprto_ts'])} ({v['vzrok']})" if v["stanje"] == "zaprto" else ""
        out.append(f"{v['prevoznik']:8} {v['linija'] or '':8} {imena.get(v['stop_id'], v['stop_id'])} "
                   f"[{v['stop_id']}] -> {v['smer']}: od {_cas(v['odprto_ts'])}{konec}, "
                   f"{v['dokazov']} dokazov, {v['dmin_m']} m, {v['oznaka'] or '?'}")
    return "\n".join(out)
