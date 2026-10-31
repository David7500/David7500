"""Opazovano: pri katerih postajališčih vozila zadnje čase ne ustavijo.

Zakaj (`docs/OPAZOVANO.md`): objavljeni podatki povedo, kaj naj bi vozilo
delalo, ne kaj dela. Obvoz G2 mimo Focheve (Maribor) je potnik izvedel iz časopisa.
Tu **ni pogoja po prevozniku**: vir pove le lege in prehode (`lega`,
`gps_prehod`), pomen izračuna ta koda, prikaz bere samo `za_prikaz`.

Vsako noč, po dnevih (`docs/MERITVE.md`, „Opazovano, del 3“):

* **Izid** vožnje na postanku (`opazovano_izid`): `mimo` = obkrožena vožnja (prehod
  pred postankom in za njim) brez prehoda, v sledi ni luknje, najbližja točka vsaj
  `PRAG_M` od postajališča, vozilo pa je prevozilo vsaj `DELEZ_POSTANKOV` postankov;
  `prišlo` = prehod ali najbližja točka bliže od `PRAG_M`; drugače nič.
* **Stanje** ključa (`presodi`) iz izidov zadnjih `OKNO_DNI`, ne iz niza, ki ga en
  prehod pretrga: niz je 22 od 131 ključev odpiral in zapiral znova (Idrija Likerca
  petkrat v 13 dneh), en sam prehod pa ni povedal, ali postajališče spet deluje.

Ključ je (prevoznik, linija, smer, `stop_id`), vožnja v njem `start_s`, ne `shape_id`
in ne `trip_id`: oba se ob uvozu voznega reda zamenjata (Marprom 27. 10. 2026) in
stanje bi izgubilo zgodovino. Dan se obdela **enkrat**, po vrsti, izidi, stanje in
meja (`opazovano_dan`) gredo v isti commit; `lega` izgine po 14 dneh.

„Ne ustavi“ iz leg še ni trditev: pri 1119 so med ničlami pogoste napake
koordinate. Zato vrstica hrani neodvisen dokaz, da je postajališče res tam
(`_neodvisno`), in `oznaka` iz njega; brez dokaza prikaz vrstice ne vidi.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import statistics
import threading
import time
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from . import config, db, geo, pripni, stats
from .naslovi import fold
from .straza import TZ, ZACETEK_DNE_S

PRAG_M = 250            # DMIN 400 zgreši Focheva (315 in 328 m), 150 doda 3 napačne
#: Vozilo, ki je prevozilo manj postankov vožnje, je ne vozi po objavljenem ali pa
#: ni ta vožnja (N6217: 36 %): o enem postanku tako ne pove nič.
DELEZ_POSTANKOV = 0.5
ODPRE_DOKAZOV = 10
ODPRE_RAZPON_S = 24 * 3600
POZABI_S = 7 * 86400
#: Izidi tako daleč nazaj. Vožnja enkrat na delavnik doseže `ODPRE_DOKAZOV` v 12 dneh,
#: okno mora biti dovolj daljše, da ena manjkajoča ne zapre stanja.
OKNO_DNI = 21
#: Med zadnjimi `ZADNJIH` izidi ključa vsaj toliko prihodov: postajališče deluje.
ZADNJIH = 10
ZADNJIH_PRISLO = 5
#: Vožnja, ki pride v vsaj polovici izidov, je izjema, ne naključje (A6227 Naklo ob
#: 5.50: 7 od 9, ostalih 11 voženj 0 od 73).
STALNA_DELEZ = 0.5
STALNA_IZIDOV = 3
#: Ključ, ki ga je ta dan vsaj tolikokrat več prevoženih, je samo spodrsljaj: sledi
#: ne beremo (1 354 ključev z vsaj enim dokazom, stanje pa doseže 150).
SPODRSLJAJ = 20

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

#: Kako poenostavljena je pot vozila na zemljevidu (stopinje, ~5 m).
POT_POENOSTAVI = 5e-5
#: Sled poti vozil sega toliko čez oba prehoda.
SLED_ROB_S = 30
#: Tako poredko prikaz preveri današnje prehode.
OSVEZI_S = 60
#: Postanek in konca poti vozil morajo biti tako blizu objavljene trase.
OB_TRASI_M = 150

OSM_DATOTEKA = Path(__file__).with_name("osm_postajalisca.json")

#: Besede, ki pri primerjavi imen postajališč nič ne povedo.
_POLNILA = ("pri", "bus", "pos", "ulica", "cesta")
_M_NA_STOPINJO = 111194.9
_ODPRTA = "('ne_ustavi', 'redko')"
_POLJA = ("prevoznik", "linija", "smer", "stop_id", "prvi_ts", "zadnji_ts", "dokazov", "prislo",
          "stanje", "voznje", "odprto_ts", "zaprto_ts", "vzrok", "dmin_m", "lat", "lon",
          "osm_ime", "osm_blizu", "osm_ob_poti", "druge_obkrozenih", "druge_prehodov",
          "oznaka", "preverjeno_ts", "pot")
_IZID = ("prevoznik", "linija", "smer", "stop_id", "dan", "start_s", "mimo", "ts", "dmin_m",
         "lat", "lon", "trip_id", "od_ts", "do_ts")


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


# ---------------------------------------------------------------- izidi dneva

def _vozni(conn: sqlite3.Connection) -> dict[str, tuple]:
    """{trip_id: (prevoznik, linija, smer, start_s)}. Nagrobnik obdrži vrstico v `trip`,
    `sched` pa ne: tam stop_id ni znan in vožnja odpade."""
    return {r[0]: (r[1] or "?", r[2], r[3] or "", r[4] or 0) for r in conn.execute(
        "SELECT trip_id, agency, train_no, headsign, start_s FROM trip")}


def _izidi_dneva(conn: sqlite3.Connection, dan: str, vozni: dict, zivi: set) -> dict:
    """Izidi enega prometnega dne. Prehodi samo za ključe z dokazom (danes ali v
    oknu, `zivi`): dan drugih je samo prehod, stanje pa se začne z dokazom."""
    prehodi: dict[str, dict] = defaultdict(dict)
    for trip_id, seq, ts in conn.execute(
            "SELECT trip_id, stop_seq, prehod_ts FROM gps_prehod WHERE service_date = ?", (dan,)):
        prehodi[trip_id][seq] = ts
    prisli: dict[tuple, list] = defaultdict(list)
    kandidati: dict[tuple, list] = defaultdict(list)
    delez: dict[str, float] = {}
    brez_sched = 0
    for trip_id, seqs in prehodi.items():
        meta = vozni.get(trip_id)
        postanki = conn.execute("SELECT stop_seq, stop_id FROM sched WHERE trip_id = ? "
                                "ORDER BY stop_seq", (trip_id,)).fetchall()
        if meta is None or not postanki:
            brez_sched += 1
            continue
        delez[trip_id] = len(seqs) / len(postanki)
        po_vrsti = sorted(seqs)
        for seq, stop_id in postanki[1:]:      # izhodišča ne merimo: tam vožnja šele začne
            k = (*meta[:3], stop_id)
            ts = seqs.get(seq)
            if ts is not None:
                prisli[k].append((meta[3], ts, trip_id))
            elif po_vrsti[0] < seq < po_vrsti[-1]:
                i = bisect_left(po_vrsti, seq)
                kandidati[k].append((meta[3], seqs[po_vrsti[i - 1]], seqs[po_vrsti[i]], trip_id))

    izbrani: dict[str, list] = defaultdict(list)
    for k, voznje in kandidati.items():
        if k in zivi or len(prisli.get(k, ())) < SPODRSLJAJ * len(voznje):
            for start, od, do, trip_id in voznje:
                izbrani[trip_id].append((k, start, od, do))

    koord = {}
    izidi: dict[tuple, tuple] = {}
    dokazov = 0
    for trip_id, cilji in izbrani.items():
        lega = [tuple(r) for r in conn.execute(
            "SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? "
            "ORDER BY ts", (dan, trip_id))]
        for k, start, od, do in cilji:
            s = k[3]
            if s not in koord:
                koord[s] = conn.execute("SELECT lat, lon FROM station WHERE stop_id = ?",
                                        (s,)).fetchone()
            if koord[s] is None:
                continue
            r = _najblizja(lega, koord[s][0], koord[s][1], od, do)
            if r is None:
                continue
            d, la, lo, ts = r
            if d < PRAG_M:
                izidi[(k, start)] = (*k, dan, start, 0, ts, d, la, lo, trip_id, od, do)
            elif delez[trip_id] >= DELEZ_POSTANKOV:
                izidi[(k, start)] = (*k, dan, start, 1, ts, d, la, lo, trip_id, od, do)
                dokazov += 1
    z_dokazom = zivi | {k for (k, _), v in izidi.items() if v[6]}
    for k in z_dokazom & prisli.keys():
        for start, ts, trip_id in prisli[k]:
            izidi[(k, start)] = (*k, dan, start, 0, ts, None, None, None, trip_id, None, None)
    return {"izidi": [v for (k, _), v in izidi.items() if k in z_dokazom],
            "voznje": len(prehodi), "brez_sched": brez_sched,
            "sledi": len(izbrani), "dokazov": dokazov}


# ---------------------------------------------------------------- stanje

def presodi(izidi: list[tuple], zdaj: int) -> tuple[str, list | None] | None:
    """Stanje ključa iz izidov okna, urejenih po času: (stanje, vožnje) ali None.

    `izidi` = (ts, start_s, mimo). Edino mesto s pravilom. Vožnje = `start_s`, na
    katere se stanje nanaša, None = vse vožnje ključa.

    * `ne_ustavi`: dokazi brez prihoda, tudi po voznem redu pred njimi, ko je
      postajališče prej delovalo (začetek zapore).
    * `ne_ustavi` z vožnjami: nekatere vožnje stalno pridejo, ostale nikoli
      (A6227 Naklo: samo prva zjutraj, ista trasa, isti postanki).
    * `redko`: pridejo tu in tam (N0173 Galicija 7 proti 80, N6217 Podroteja 6 od 172). Vožnja je
      lahko „po potrebi“; da je ni, ne moremo trditi, da redko ustavi, pa lahko.
    * None: premalo dokazov, predolgo nič ali postajališče spet deluje.
    """
    mimo = [x for x in izidi if x[2]]
    if (len(mimo) < ODPRE_DOKAZOV or mimo[-1][0] - mimo[0][0] < ODPRE_RAZPON_S
            or zdaj - izidi[-1][0] > POZABI_S):
        return None
    i = len(izidi)
    while i and izidi[i - 1][2]:
        i -= 1
    niz, prej = izidi[i:], izidi[:i]
    if (len(niz) >= ODPRE_DOKAZOV and niz[-1][0] - niz[0][0] >= ODPRE_RAZPON_S
            and sum(not x[2] for x in prej) >= STALNA_DELEZ * len(prej)):
        return "ne_ustavi", None
    if sum(not x[2] for x in izidi[-ZADNJIH:]) >= ZADNJIH_PRISLO:
        return None
    po_voznji: dict[int, list] = defaultdict(lambda: [0, 0])
    for _, start, m in izidi:
        po_voznji[start][m] += 1
    stalne = {s for s, (p, m) in po_voznji.items()
              if p + m >= STALNA_IZIDOV and p >= STALNA_DELEZ * (p + m)}
    voznje = sorted(s for s, (_, m) in po_voznji.items() if m and s not in stalne)
    if not voznje:
        return None
    vrsta = "redko" if any(p and s not in stalne for s, (p, _) in po_voznji.items()) else "ne_ustavi"
    return vrsta, voznje if stalne else None


def _konec_dneva(dan: str) -> int:
    return stats.polnoc(dan) + 24 * 3600 + ZACETEK_DNE_S


def _osvezi(conn: sqlite3.Connection, kljuci: set, zdaj: int) -> None:
    """Stanje vseh ključev z izidi ali odprto vrstico. Brez commita: mejo dneva
    zapiše klicatelj v isti transakciji. Stanje ene epizode se spreminja v vrstici
    (`ne_ustavi` <-> `redko`), zapre se samo, ko ni več ne enega ne drugega."""
    odprte = {(r[0], r[1], r[2], r[3]): r[4] for r in conn.execute(
        "SELECT prevoznik, linija, smer, stop_id, prvi_ts FROM opazovano "
        f"WHERE stanje IN {_ODPRTA}")}
    for k in kljuci | odprte.keys():
        vse = conn.execute(
            "SELECT ts, start_s, mimo, dmin_m, lat, lon FROM opazovano_izid WHERE prevoznik = ? "
            "AND linija = ? AND smer = ? AND stop_id = ? ORDER BY ts", k).fetchall()
        s = presodi([tuple(x[:3]) for x in vse], zdaj) if vse else None
        prvi = odprte.get(k)
        if s is None:
            if prvi is None:
                continue
            prehod = bool(vse) and not vse[-1][2]
            zadnji = conn.execute(
                "SELECT zadnji_ts FROM opazovano WHERE prevoznik = ? AND linija = ? AND smer = ? "
                "AND stop_id = ? AND prvi_ts = ?", (*k, prvi)).fetchone()[0]
            conn.execute(
                "UPDATE opazovano SET stanje = 'zaprto', vzrok = ?, zaprto_ts = ?, pot = NULL "
                "WHERE prevoznik = ? AND linija = ? AND smer = ? AND stop_id = ? AND prvi_ts = ?",
                ("prehod" if prehod else "zastarelo", vse[-1][0] if prehod else zadnji + POZABI_S,
                 *k, prvi))
            continue
        mimo = [x for x in vse if x[2]]
        zad = mimo[-TOCK:]
        polja = {"zadnji_ts": mimo[-1][0], "dokazov": len(mimo), "prislo": len(vse) - len(mimo),
                 "stanje": s[0], "voznje": None if s[1] is None else json.dumps(s[1]),
                 "dmin_m": round(statistics.median(x[3] for x in zad)),
                 "lat": round(statistics.median(x[4] for x in zad), 5),
                 "lon": round(statistics.median(x[5] for x in zad), 5)}
        if prvi is None:
            vrstica = dict.fromkeys(_POLJA) | polja | {
                "prevoznik": k[0], "linija": k[1], "smer": k[2], "stop_id": k[3],
                "prvi_ts": mimo[0][0], "odprto_ts": vse[-1][0]}
            conn.execute(f"INSERT OR REPLACE INTO opazovano({', '.join(_POLJA)}) "
                         f"VALUES({', '.join(':' + p for p in _POLJA)})", vrstica)
        else:
            conn.execute(
                f"UPDATE opazovano SET {', '.join(f'{p} = :{p}' for p in polja)} "
                "WHERE prevoznik = :a AND linija = :b AND smer = :c AND stop_id = :d AND prvi_ts = :e",
                polja | dict(zip("abcde", (*k, prvi))))


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
    """Napaka tu pošlje potnika stran od avtobusa, zato mora biti na koordinati
    nekaj, kar ni sled te vožnje. `neznan` z `osm_blizu` (OSM ima neimenovano
    postajališče tam) je Ormož bolnica, ročno preverjen pravi primer.
    """
    return v["stanje"] in ("ne_ustavi", "redko") and (
        v["oznaka"] == "pravi" or (v["oznaka"] == "neznan" and bool(v["osm_blizu"])))


def _neodvisno(conn: sqlite3.Connection, danes: date, zdaj: int) -> int:
    """Osveži odprte in vse še nepreverjene: zaprta vrstica obdrži, kar je veljalo."""
    vrstice = [dict(zip(_POLJA, r)) for r in conn.execute(
        f"SELECT {', '.join(_POLJA)} FROM opazovano WHERE stanje IN {_ODPRTA} "
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
            # Drugo ime ni potrditev, ampak dvom: „Krško Š“ na OSM „Krško - Resa“.
            v["osm_blizu"] = int(not all(blizu))
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


# ---------------------------------------------------------------- pot vozil

def _sled(conn: sqlite3.Connection, dan: str, trip_id: str, od: int, do: int) -> list:
    """Sled ene vožnje med dvema prehodoma, enega vozila: NAP pod isto vožnjo javi
    dve vozili pri ~0,5 % voženj. Z robom: pri legi na 20 s je zadnja točka pred
    prehodom še na obvozu (do 260 m od trase, 7 od 50 odsekov), pri kraku tja in
    nazaj sta prehoda ob isti uri (Artiče: vozilo na križišču velja za oba postanka)."""
    vrstice = conn.execute("SELECT lat, lon, vozilo FROM lega WHERE service_date = ? AND trip_id = ? "
                           "AND ts BETWEEN ? AND ? ORDER BY ts",
                           (dan, trip_id, min(od, do) - SLED_ROB_S, max(od, do) + SLED_ROB_S)).fetchall()
    if not vrstice:
        return []
    vozilo = Counter(r[2] for r in vrstice).most_common(1)[0][0]
    return [(r[0], r[1]) for r in vrstice if r[2] == vozilo]


def _poti(conn: sqlite3.Connection) -> int:
    """Kje vozila res vozijo, za odprte `ne_ustavi`: sled zadnje vožnje z dokazom
    med prehodoma, pripeta na ceste, kjer OSRM odgovori. Enaka za vse skrite postanke
    istega odseka, zato enkrat na odsek."""
    vrstice = conn.execute("SELECT prevoznik, linija, smer, stop_id, prvi_ts FROM opazovano "
                           "WHERE stanje = 'ne_ustavi'").fetchall()
    if not vrstice:
        return 0
    naslov = pripni._naslov("avtobus")
    osrm = pripni._dosegljiv(naslov)
    po_odseku: dict[tuple, str | None] = {}
    poti = []
    for k in vrstice:
        r = conn.execute(
            "SELECT dan, trip_id, od_ts, do_ts FROM opazovano_izid WHERE prevoznik = ? AND linija = ? "
            "AND smer = ? AND stop_id = ? AND mimo = 1 ORDER BY ts DESC LIMIT 1", tuple(k)[:4]).fetchone()
        odsek = tuple(r) if r else None
        if odsek not in po_odseku:
            po_odseku[odsek] = _pot_odseka(conn, odsek, naslov if osrm else None)
        poti.append((po_odseku[odsek], *k))
    # Pisanje šele zdaj: OSRM med odprto transakcijo bi držal zajem.
    conn.executemany("UPDATE opazovano SET pot = ? WHERE prevoznik = ? AND linija = ? AND smer = ? "
                     "AND stop_id = ? AND prvi_ts = ?", poti)
    conn.commit()
    return len(vrstice)


def _pot_odseka(conn: sqlite3.Connection, odsek: tuple | None, naslov: str | None) -> str | None:
    sled = _sled(conn, *odsek) if odsek else []
    if len(sled) < 2:
        return None
    gola = geo.simplify(sled, POT_POENOSTAVI)
    tocke, delez = pripni.pripni_kos(naslov, "avtobus", gola) if naslov else (None, 0.0)
    return json.dumps([[round(a, 5), round(b, 5)] for a, b in (tocke if delez >= 0.5 else gola)],
                      separators=(",", ":"))


# ---------------------------------------------------------------- nočni izračun

def obdelaj_dan(conn: sqlite3.Connection, dan: str, vozni: dict) -> dict:
    """En dan: izidi, stanje, meja in številke gredo v isti commit. Branje sledi
    (~2,5 s na delavnik) pred prvim pisanjem: zajem med njim piše naprej."""
    zacetek = time.perf_counter()
    od = (date.fromisoformat(dan) - timedelta(days=OKNO_DNI - 1)).isoformat()
    zivi = {tuple(r) for r in conn.execute(
        "SELECT DISTINCT prevoznik, linija, smer, stop_id FROM opazovano_izid WHERE dan >= ?", (od,))}
    r = _izidi_dneva(conn, dan, vozni, zivi)
    conn.execute("DELETE FROM opazovano_izid WHERE dan < ?", (od,))
    conn.executemany(f"INSERT OR REPLACE INTO opazovano_izid({', '.join(_IZID)}) "
                     f"VALUES({', '.join('?' * len(_IZID))})", r["izidi"])
    _osvezi(conn, zivi | {tuple(x[:4]) for x in r["izidi"]}, _konec_dneva(dan))
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
    """Obdelaj dneve od meje do včeraj, osveži neodvisen dokaz in poti. Vrne dneve.

    Vožnja, ki ob računu še vozi, v svoj dan ne pride. Izguba je majhna: ob 3:30
    avtobusov skoraj ni. Kar prikaz bere, je gotovo šele po `koncano`.
    """
    danes = danes or datetime.now(TZ).date()
    dnevi = _dnevi(conn, danes)
    if dnevi:
        vozni = _vozni(conn)
        for dan in dnevi:
            obdelaj_dan(conn, dan, vozni)
    _neodvisno(conn, danes, int(time.time()))
    _poti(conn)
    conn.execute("UPDATE opazovano_dan SET koncano = ? WHERE dan = (SELECT MAX(dan) FROM opazovano_dan)",
                 (int(time.time()),))
    conn.commit()
    return dnevi


def senca(conn: sqlite3.Connection) -> None:
    """Tabele v `temp`: isti račun na bazi z `mode=ro`, nič se ne zapiše. `temp`
    ima prednost pred `main`, zato dela tudi, kjer tabela že obstaja."""
    conn.executescript(db.OPAZOVANO.replace("CREATE TABLE IF NOT EXISTS ", "CREATE TEMP TABLE "))


# ---------------------------------------------------------------- prikaz

_ZAKLEP = threading.Lock()
_shramba: dict = {"znacka": None, "pari": {}, "ts": 0.0, "zdaj": {}}


def _pari(conn: sqlite3.Connection) -> dict[tuple[str, str], dict]:
    """(trip_id, stop_id) -> kaj o tem postanku povemo. Vožnje se izberejo šele tu:
    uvoz voznega reda jim zamenja id, ključ in `start_s` pa ostaneta."""
    out: dict[tuple[str, str], dict] = {}
    for v in beri(conn):
        if not dovolj_za_prikaz(v):
            continue
        voznje = None if v["voznje"] is None else set(json.loads(v["voznje"]))
        lega = conn.execute("SELECT lat, lon FROM station WHERE stop_id = ?", (v["stop_id"],)).fetchone()
        if lega is None:
            continue
        o = {"vrsta": v["stanje"], "dokazov": v["dokazov"], "prislo": v["prislo"],
             "dmin_m": v["dmin_m"], "zadnji_ts": v["zadnji_ts"], "lega": tuple(lega),
             "pot": json.loads(v["pot"]) if v["pot"] and v["stanje"] == "ne_ustavi" else None,
             "kljuc": (v["prevoznik"], v["linija"], v["smer"], v["stop_id"])}
        for trip_id, start_s, seq in conn.execute(
                "SELECT t.trip_id, t.start_s, s.stop_seq FROM sched s "
                "JOIN trip t ON t.trip_id = s.trip_id WHERE s.stop_id = ? AND t.train_no = ? "
                "AND COALESCE(t.agency, '?') = ? AND COALESCE(t.headsign, '') = ?",
                (v["stop_id"], v["linija"], v["prevoznik"], v["smer"])):
            if voznje is None or (start_s or 0) in voznje:
                out[(trip_id, v["stop_id"])] = o | {"seq": seq}
    return out


def _danes(conn: sqlite3.Connection, pari: dict, zdaj: float) -> dict:
    """Prvi današnji prehod `ne_ustavi` omili v `redko`, ne čaka na noč: zapora se je
    končala zjutraj, tabla pa bi do naslednje noči trdila, da avtobus tu ne ustavi.
    Če nočni račun stoji, stare trditve odpadejo same (`POZABI_S`)."""
    pari = {p: o for p, o in pari.items() if zdaj - o["zadnji_ts"] <= POZABI_S}
    ids = sorted({t for (t, _), o in pari.items() if o["vrsta"] == "ne_ustavi"})
    if not ids:
        return pari
    dan = datetime.fromtimestamp(zdaj - ZACETEK_DNE_S, TZ).date().isoformat()
    prehodi = {(r[0], r[1]) for r in conn.execute(
        "SELECT trip_id, stop_seq FROM gps_prehod WHERE service_date = ? "
        "AND trip_id IN (SELECT value FROM json_each(?))", (dan, json.dumps(ids)))}
    prisli = {o["kljuc"] for (t, _), o in pari.items() if (t, o["seq"]) in prehodi}
    if not prisli:
        return pari
    return {p: ({**o, "vrsta": "redko", "pot": None} if o["kljuc"] in prisli else o)
            for p, o in pari.items()}


def za_prikaz(conn: sqlite3.Connection, zdaj: float | None = None) -> dict:
    """(trip_id, stop_id) -> {vrsta: `ne_ustavi` | `redko`, dokazov, prislo, dmin_m, pot}.

    Edino, kar prikaz bere. Predpomnjeno na znački voznega reda in nočnega računa,
    današnji prehodi na `OSVEZI_S`; v zahtevi bere le ob spremembi (~5 ms).
    """
    if not config.OPAZOVANO_PRIKAZ:
        return {}
    zdaj = time.time() if zdaj is None else zdaj
    znacka = (db.znacka_reda(conn),
              conn.execute("SELECT MAX(koncano) FROM opazovano_dan").fetchone()[0])
    with _ZAKLEP:
        c = _shramba
        if znacka[0] is None or c["znacka"] != znacka:
            c.update(znacka=znacka, pari=_pari(conn), ts=0.0)
        if znacka[0] is None or zdaj - c["ts"] >= OSVEZI_S:
            c.update(zdaj=_danes(conn, c["pari"], zdaj), ts=zdaj)
        return c["zdaj"]


def ne_ustavi(conn: sqlite3.Connection, zdaj: float | None = None) -> set[tuple[str, str]]:
    """Isto kot `alerts.ne_ustavi`: pari, kjer vožnja zadnje dni tu ni ustavljala."""
    return {p for p, o in za_prikaz(conn, zdaj).items() if o["vrsta"] == "ne_ustavi"}


def za_voznjo(conn: sqlite3.Connection, trip_id: str | None, zdaj: float | None = None) -> dict[int, dict]:
    """`stop_seq` -> vrstica `za_prikaz` te vožnje."""
    if not trip_id:
        return {}
    return {o["seq"]: o for (t, _), o in za_prikaz(conn, zdaj).items() if t == trip_id}


def trasa_po_obvozih(kosi: list, obvozi: list[tuple[list, float, float]]) -> tuple[list, list]:
    """Trasa vožnje s potjo vozil namesto objavljenega odseka in objavljeni odseki.

    Vozilo na obvozu je tako na črti: ocena lege, razrez poti in razdalja do potnika
    delajo kot povsod, brez nove veje v prikazu, in vozilo ni videti, kot da je zašlo.
    `obvozi` = (pot, lat, lon skritega postanka). Odsek loči postanek: krak tja in nazaj
    ima oba konca poti na istem mestu trase (Artiče, 1,2 km stran od ceste). Pot, katere
    konca nista ob trasi, ostane zunaj: raje objavljena črta kot izmišljena.
    """
    kosi = [list(k) for k in kosi]
    objavljeni: list = []
    videne = set()
    for pot, lat, lon in obvozi:
        if json.dumps(pot) in videne:
            continue
        videne.add(json.dumps(pot))
        for i, kos in enumerate(kosi):
            if len(kos) < 2:
                continue
            d, s, _ = pripni._najblizje(kos, lat, lon, 0, len(kos) - 1)
            if d > OB_TRASI_M:
                continue
            da, a, ta = pripni._najblizje(kos, pot[0][0], pot[0][1], 0, s + 1)
            db_, b, tb = pripni._najblizje(kos, pot[-1][0], pot[-1][1], s, len(kos) - 1)
            if da > OB_TRASI_M or db_ > OB_TRASI_M:
                continue
            objavljeni.append([pripni._tocka(kos, a, ta), *kos[a + 1:b + 1], pripni._tocka(kos, b, tb)])
            kosi[i] = kos[:a + 1] + pot + kos[b + 1:]
            break
    return kosi, objavljeni


# ---------------------------------------------------------------- izpis

def _cas(ts: int | None) -> str:
    return "–" if ts is None else datetime.fromtimestamp(ts, TZ).strftime("%d. %m. %H:%M")


def beri(conn: sqlite3.Connection, vsa: bool = False) -> list[dict]:
    pogoj = "1" if vsa else f"stanje IN {_ODPRTA}"
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
        if v["stanje"] != "zaprto":
            c = po[v["prevoznik"]]
            c["odprtih"] += 1
            c["redko"] += v["stanje"] == "redko"
            c[v["oznaka"] or "neznan"] += 1
            c["prikaz"] += dovolj_za_prikaz(v)
    out = [f"{'prevoznik':10} {'odprtih':>7} {'redko':>5} {'pravi':>5} {'dvoumen':>7} {'napacen':>7} "
           f"{'neznan':>6} {'za prikaz':>9}"]
    for p in sorted(po):
        c = po[p]
        out.append(f"{p:10} {c['odprtih']:>7} {c['redko']:>5} {c['pravi']:>5} {c['dvoumen']:>7} "
                   f"{c['napacen']:>7} {c['neznan']:>6} {c['prikaz']:>9}")
    out.append("")
    for v in vrstice:
        konec = f" do {_cas(v['zaprto_ts'])} ({v['vzrok']})" if v["stanje"] == "zaprto" else ""
        izjema = "" if v["voznje"] is None else f", samo {len(json.loads(v['voznje']))} voženj"
        out.append(f"{v['prevoznik']:8} {v['linija'] or '':8} {imena.get(v['stop_id'], v['stop_id'])} "
                   f"[{v['stop_id']}] -> {v['smer']}: {v['stanje']} od {_cas(v['odprto_ts'])}{konec}, "
                   f"{v['dokazov']} dokazov, {v['prislo']} prišlo, {v['dmin_m']} m, "
                   f"{v['oznaka'] or '?'}{izjema}")
    return "\n".join(out)
