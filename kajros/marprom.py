"""Mestni avtobusi Marproma (Maribor) v živo, naravnost z Marpromovega API-ja.

Zakaj sami in ne derp.si: `rt.gtfs.derp.si/sources/marprom` sestavi DERP iz
dveh posrednikov -- pretvornika istega API-ja (`derp-si/marprom-rt`) in
OnTrack (`ontrack.baguette.pirnet.si`), ki vožnjo in zamudo SKLEPA iz lege.
Marpromov API `vozniredi.marprom.si/OBA/` je odprt in brez ključa (27. 10.
2026); beremo izvirnik.

Kaj API da:

* `GetActiveDeviceDetails`: vozila z lego, linijo (`LineId` = GTFS
  `route_id`), varianto (`RouteId` = GTFS `shape_id`) in naslednjim
  postajališčem (`NextStopPointId` = GTFS `stop_id`). Ure lege ni.
  `Predicted: 1` = lega ni živa: 255 od 287 takih vzorcev se ni premaknilo,
  trije avtobusi po 460 s na istem mestu 85-343 m od postajališča, ETA pa je
  tekel naprej (27. 10. 2026, 47 vzorcev po 10 s). Živim (`Predicted: 0`)
  se lega spremeni v 75 % vzorcev.
* `GetArrivalsForStopPoint?StopPointId=`: prihodi na postajališču z uro po
  voznem redu (`ArrivalTime`, HH:MM), vozilom (`BusCode`) in zamudo
  (`DelayMin`).
* `GetAllStopPoints`: postajališča z imenom in skupino (`StopID`). Vozilo
  pred končno na avtobusni postaji ima za naslednje 457 („Mlinska ulica 2“),
  vozni red pa vožnjo konča na 192 -- oba v skupini 5480. Brez skupine so
  ostala brez vožnje vsa vozila pred končno (3 od 34, 27. 10. 2026).

Vožnje API ne pove. **Vozilo -> vožnja**: ura, ki jo Marprom na naslednjem
postajališču za to vozilo pričakuje, z linijo in varianto da natanko eno
vožnjo voznega reda (27. 10. 2026: 32 od 36 vozil; OnTrack, ki sklepa iz
lege, pri 28 od 28 skupnih isto). Prihode beremo samo za vozila, ki vožnjo
šele začnejo, zamenjajo varianto ali jih preverjamo (`PREVERI_S`).

**Zamudo merimo sami iz leg** (`iz_lege.opazuj`, prehod brez trase), kot
pri NAP, in le iz živih leg. Marpromova `DelayMin` je primerjava
(`meta.marprom.primerjava`), v bazo ne gre.
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import requests

from . import collector, config, db, dosje, geo, gtfs, iz_lege, stats, straza, viri

TZ = collector.TZ
MP = gtfs.MP

TIMEOUT_S = (5, 15)
#: Pripisana vožnja se po tem času preveri znova: napačna se ne vleče do konca.
PREVERI_S = 600
#: `potrebuje`: vožnja je mimo (nova, menjava variante, za koncem) ali je samo
#: čas za preverjanje. Samo pri preverjanju odgovor brez prihoda vožnje ne vzame.
NOVA, PREVERI = "nova", "preveri"
#: Odgovor `razresi`, ki o pripeti vožnji nič ne pove. API da en prihod na
#: linijo, zato ga vozilo za drugim avtobusom nima; 1.--4. 11. 2026 je od 377
#: takih izpadov sredi vožnje vozilo v 364 vozilo isto vožnjo naprej (1 663 min
#: brez lege in zamude), v 13 je naslednje postajališče vožnjo zapustilo, kar
#: `potrebuje` opazi samo. Ura, ki je vozni red nima: 18 od 19.
BREZ_DOKAZA = frozenset({"ni_prihoda", "ni_v_voznem_redu"})
#: Vožnje, ki je po voznem redu končana toliko časa, preverjanje brez prihoda ne
#: obdrži: od 17 izpadov po +5 min se nobeno vozilo ni vrnilo na isto vožnjo,
#: stoji na končni (brez meje bi jo imelo še do `PO_KONCU_S`).
OBDRZI_PO_KONCU_S = 300
#: Vozilo, ki mu vožnje ni bilo mogoče določiti, se vpraša znova čez toliko.
ZNOVA_S = 60
#: Največ toliko branj prihodov na obhod. Ob zagonu ~35 vozil: pet obhodov,
#: nato le vozila, ki začnejo novo vožnjo (vsako 10 min še preverjanje).
KLICEV_NA_OBHOD = 8
#: Vožnja je končana toliko po zadnjem prihodu po voznem redu.
PO_KONCU_S = 1800
#: Pod tem premikom smer vozila ostane prejšnja (tresenje GPS na postaji).
SMER_PREMIK_M = 20
#: Hitreje mestni avtobus ne vozi; tak premik je skok lege, ne hitrost.
NAJVEC_HITROST_MS = 30
#: Toliko zadnjih primerjav naše zamude z Marpromovo hrani pregled.
PRIMERJAV = 300
#: Naša meritev je za primerjavo dovolj sveža toliko časa.
PRIMERJAVA_SVEZE_S = 180
#: Seznam postajališč (imena, skupine) se osveži enkrat na dan.
POSTAJALISCA_S = 86400


@dataclass
class Vozilo:
    """Kar o vozilu vemo med obhodi. Samo nit Marproma ga bere in piše."""
    trip_id: str | None = None
    dan: str | None = None
    linija: str = ""
    varianta: str = ""
    #: Zaporedje naslednjega postajališča na vožnji: ko gre nazaj, se je
    #: začela nova vožnja iste variante.
    seq: int = 0
    razreseno_ts: float = 0.0
    poskus_ts: float = 0.0
    lega: tuple[float, float] | None = None
    #: Kdaj se je lega nazadnje spremenila -- starost mrtve lege.
    lega_ts: float = 0.0
    smer: float | None = None
    #: Iz premika od prejšnjega branja; API hitrosti ne pošlje.
    hitrost: float | None = None
    #: Kdaj je bilo vozilo nazadnje v odgovoru (za hitrost).
    videno_ts: float = 0.0
    #: Zakaj zadnjič ni bilo vožnje (`razresi`), za dosje.
    zakaj: str | None = None
    #: Preverjanje vožnje ni potrdilo in je ni ovrglo (`BREZ_DOKAZA`). Drugo
    #: vozilo, ki mu Marprom to vožnjo pokaže, jo prevzame.
    obdrzana: bool = False


_vozila: dict[str, Vozilo] = {}
_primerjave: deque = deque(maxlen=PRIMERJAV)


def razberi(odgovor: dict) -> list[dict]:
    """Odgovor `GetActiveDeviceDetails` -> vozila. Brez lege v Sloveniji ven."""
    out = []
    for x in odgovor.get("Vehicles") or []:
        try:
            lat, lon = float(x["Lat"]), float(x["Lon"])
            naprava = str(int(x["DeviceId"]))
        except (KeyError, TypeError, ValueError):
            continue
        if not (45.3 < lat < 47.0 and 13.3 < lon < 16.7):
            continue
        out.append({
            "naprava": naprava, "bus": str(x.get("BusCode") or "").strip(),
            "linija": str(x.get("LineId") or ""), "varianta": str(x.get("RouteId") or ""),
            "naslednja": str(x.get("NextStopPointId") or ""),
            "lat": lat, "lon": lon, "zivo": not x.get("Predicted"),
            "smer_opis": " ".join(str(x.get("DirectionDescription") or "").split()),
            "surovo": x,
        })
    return out


def _hhmm(polnoc: int, t_s: int) -> str:
    return datetime.fromtimestamp(polnoc + t_s, TZ).strftime("%H:%M")


def indeks(conn: sqlite3.Connection, zdaj: float) -> dict[tuple, list[tuple]]:
    """(linija, varianta, postajališče, HH:MM) -> [(trip_id, dan, stop_seq)].

    Za danes in za včerajšnje vožnje po polnoči. Ura je ura stene prek
    `stats.polnoc`, ker jo tako piše Marprom -- tudi na dan premika ure.
    """
    danes = datetime.fromtimestamp(zdaj, TZ).date()
    dnevi = ((danes - timedelta(days=1)).isoformat(), danes.isoformat())

    def build():
        out: dict[tuple, list[tuple]] = {}
        for i, dan in enumerate(dnevi):
            polnoc = stats.polnoc(dan)
            for r in conn.execute(
                    "SELECT t.trip_id, t.route_id, t.shape_id, s.stop_id, s.stop_seq, "
                    "       s.arr_s, s.dep_s "
                    "FROM trip t "
                    "JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
                    "JOIN sched s ON s.trip_id = t.trip_id "
                    "WHERE t.agency = ?", (dan, gtfs.MARPROM_AGENCIJA)):
                casi = {c for c in (r["arr_s"], r["dep_s"]) if c is not None}
                if i == 0:      # včerajšnje le po polnoči
                    casi = {c for c in casi if c >= 86400}
                for c in casi:
                    out.setdefault((r["route_id"], r["shape_id"], r["stop_id"],
                                    _hhmm(polnoc, c)), []).append(
                        (r["trip_id"], dan, r["stop_seq"]))
        return out
    return collector._cached(conn, "marprom_indeks", dnevi, build)


def _postanki(conn: sqlite3.Connection) -> dict[str, dict[str, list[int]]]:
    """trip_id -> postajališče -> zaporedja (krožna linija ima isto dvakrat)."""
    def build():
        out: dict[str, dict[str, list[int]]] = {}
        for r in conn.execute(
                "SELECT s.trip_id, s.stop_id, s.stop_seq FROM sched s JOIN trip t "
                "USING (trip_id) WHERE t.agency = ? ORDER BY s.trip_id, s.stop_seq",
                (gtfs.MARPROM_AGENCIJA,)):
            out.setdefault(r[0], {}).setdefault(r[1], []).append(r[2])
        return out
    return collector._cached(conn, "marprom_postanki", None, build)


def _proge(conn: sqlite3.Connection) -> dict[str, str]:
    """route_id -> oznaka linije (G1, P7)."""
    def build():
        return {r[0]: r[1] for r in conn.execute(
            "SELECT DISTINCT route_id, train_no FROM trip WHERE agency = ?",
            (gtfs.MARPROM_AGENCIJA,))}
    return collector._cached(conn, "marprom_proge", None, build)


def potrebuje(s: Vozilo, v: dict, zdaj: float, postanki: dict, okna: dict,
              sosedi: dict[str, list[str]] | None = None) -> str | None:
    """Ali vozilu vožnjo določimo (znova): `NOVA`, `PREVERI` ali None.
    Premakne `s.seq` naprej.

    Naslednje postajališče, ki ga vožnja nima, se išče še v skupini: pred
    končno na avtobusni postaji (457 za 192) je bilo sicer vsako branje
    nova razrešitev -- prihodi vsakih 10 s za isto vozilo, in v primerjavi z
    Marpromovo zamudo samo vozila pred končno (mediana +130 s namesto +39).
    """
    if s.trip_id is None:
        return NOVA if zdaj - s.poskus_ts >= ZNOVA_S else None
    if (v["linija"], v["varianta"]) != (s.linija, s.varianta):
        return NOVA
    na_voznji = postanki.get(s.trip_id, {})
    seqs = None
    for postaja in [v["naslednja"], *(sosedi or {}).get(v["naslednja"], ())]:
        seqs = na_voznji.get(MP + postaja)
        if seqs:
            break
    naprej = [q for q in seqs or () if q >= s.seq]
    if not naprej:
        # Naslednjega postajališča vožnja nima ali je za njim: nova vožnja.
        return NOVA
    s.seq = naprej[0]
    okno = okna.get(s.trip_id)
    if okno and zdaj > stats.polnoc(s.dan) + okno[1] + PO_KONCU_S:
        return NOVA
    return PREVERI if zdaj - s.razreseno_ts >= PREVERI_S else None


def obdrzi(s: Vozilo, zakaj: str, okna: dict, zdaj: float) -> bool:
    """Ali vozilo po preverjanju brez vožnje obdrži, kar ima (`BREZ_DOKAZA`)."""
    okno = okna.get(s.trip_id)
    return (zakaj in BREZ_DOKAZA and okno is not None
            and zdaj <= stats.polnoc(s.dan) + okno[1] + OBDRZI_PO_KONCU_S)


def razresi(v: dict, prihodi: list[dict], idx: dict, zasedene: dict[tuple, str],
            sosedi: dict[str, list[str]] | None = None
            ) -> tuple[tuple | None, str, dict | None]:
    """Vozilo + prihodi na njegovem naslednjem postajališču -> vožnja.

    Vrne (`(trip_id, dan, stop_seq)` ali None, razlog, Marpromov prihod).
    Vožnja, ki jo ima že drugo vozilo, ni na voljo: dve vozili na eni vožnji
    pomenita, da je eno pripisano narobe -- ostane prvo, dokler ga
    preverjanje ne izpusti. Kadar naslednjega postajališča vozni red nima,
    velja postajališče iste skupine (`sosedi`).
    """
    moji = [p for p in prihodi if str(p.get("BusCode") or "").strip() == v["bus"]
            and str(p.get("LineId") or "") == v["linija"] and p.get("ArrivalTime")]
    if not moji:
        return None, "ni_prihoda", None
    p = min(moji, key=lambda x: (x.get("ETAMin") is None, x.get("ETAMin") or 0,
                                 x["ArrivalTime"]))
    kandidati = []
    for postaja in [v["naslednja"], *(sosedi or {}).get(v["naslednja"], ())]:
        kandidati = idx.get((MP + v["linija"], MP + v["varianta"], MP + postaja,
                             p["ArrivalTime"]), [])
        if kandidati:
            break
    proste = [k for k in kandidati if zasedene.get(k[:2], v["naprava"]) == v["naprava"]]
    if len(proste) == 1:
        return proste[0], "", p
    if proste:
        return None, "vec", p
    return None, ("zasedena" if kandidati else "ni_v_voznem_redu"), p


def _smer(s: Vozilo, lat: float, lon: float) -> float | None:
    if s.lega is None:
        return s.smer
    if geo.haversine(s.lega[0], s.lega[1], lat, lon) < SMER_PREMIK_M:
        return s.smer
    p1, p2 = math.radians(s.lega[0]), math.radians(lat)
    dl = math.radians(lon - s.lega[1])
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return round((math.degrees(math.atan2(y, x)) + 360) % 360)


def _zadnja_nasa(conn: sqlite3.Connection, trip_id: str, dan: str,
                 zdaj: float) -> int | None:
    """Zadnja naša zamuda vožnje (iz leg), če je sveža -- za primerjavo."""
    r = conn.execute(
        "SELECT COALESCE(delay_dep, delay_arr), feed_ts FROM run "
        "WHERE trip_id = ? AND service_date = ? ORDER BY stop_seq DESC LIMIT 1",
        (trip_id, dan)).fetchone()
    if r is None or r[0] is None or zdaj - (r[1] or 0) > PRIMERJAVA_SVEZE_S:
        return None
    return r[0]


def primerjava() -> dict:
    """Naša zamuda iz leg proti Marpromovi `DelayMin` (minute)."""
    razlike = list(_primerjave)
    if not razlike:
        return {"n": 0}
    abs_ = sorted(abs(x) for x in razlike)
    return {"n": len(razlike),
            "mediana_s": round(statistics.median(razlike)),
            "abs_mediana_s": round(statistics.median(abs_)),
            "v_90s": round(100 * sum(1 for x in abs_ if x <= 90) / len(abs_), 1)}


_po_voznem_redu: list = [0.0, 0]


def po_voznem_redu(conn: sqlite3.Connection, zdaj: float) -> int:
    """Koliko voženj Marproma bi po voznem redu ta hip vozilo (na minuto)."""
    if zdaj - _po_voznem_redu[0] < 60:
        return _po_voznem_redu[1]
    n = 0
    danes = datetime.fromtimestamp(zdaj, TZ).date()
    for o in (-1, 0):
        dan = (danes + timedelta(days=o)).isoformat()
        t = zdaj - stats.polnoc(dan)
        n += conn.execute(
            "SELECT COUNT(*) FROM trip t JOIN service_day sd "
            "ON sd.service_id = t.service_id AND sd.date = ? "
            "WHERE t.agency = ? AND t.start_s <= ? AND t.end_s >= ?",
            (dan, gtfs.MARPROM_AGENCIJA, t, t)).fetchone()[0]
    _po_voznem_redu[:] = [zdaj, n]
    return n


def sosedi_iz(postajalisca: dict[str, dict]) -> dict[str, list[str]]:
    """Postajališče -> druga postajališča iste skupine (`StopID`)."""
    po_skupini: dict[str, list[str]] = {}
    for pid, p in postajalisca.items():
        if p.get("skupina"):
            po_skupini.setdefault(p["skupina"], []).append(pid)
    return {pid: [x for x in po_skupini[p["skupina"]] if x != pid]
            for pid, p in postajalisca.items() if p.get("skupina")}


def korak(conn: sqlite3.Connection, vozila: list[dict], zdaj: float,
          prihodi_za: Callable[[str], list[dict]],
          postajalisca: dict[str, dict] | None = None) -> dict:
    """En obhod: vožnje vozilom, lege v `vehicle_now`, zamude iz leg."""
    postajalisca = postajalisca or {}
    sosedi = sosedi_iz(postajalisca)
    idx = indeks(conn, zdaj)
    postanki = _postanki(conn)
    okna = collector._rail_trip_windows(conn)
    st = {"vozil": len(vozila), "zivih": sum(v["zivo"] for v in vozila), "pripetih": 0,
          "klicev": 0, "preklopov": 0, "prehodov": 0, "brez": {}}
    vidni = {v["naprava"] for v in vozila}
    for k in [k for k in _vozila if k not in vidni]:
        del _vozila[k]
    zasedene = {(s.trip_id, s.dan): k for k, s in _vozila.items()
                if s.trip_id and not s.obdrzana}

    # Vožnje določimo najprej vozilom, ki jo potrebujejo; prihode beremo po
    # postajališču, enkrat za vsa vozila, ki jih tam čakajo.
    # Brez Marpromovega voznega reda za danes je vsako branje prihodov zaman
    # (prvi zagon pred uvozom: 31 vozil, branje na vozilo vsako minuto).
    cakajo: dict[str, list[tuple[dict, str]]] = {}
    if not idx:
        st["brez"]["ni_voznega_reda"] = len(vozila)
    for v in vozila:
        s = _vozila.setdefault(v["naprava"], Vozilo())
        zakaj = potrebuje(s, v, zdaj, postanki, okna, sosedi) if idx else None
        if zakaj and v["naslednja"]:
            cakajo.setdefault(v["naslednja"], []).append((v, zakaj))
    for postaja in list(cakajo)[:KLICEV_NA_OBHOD]:
        try:
            prihodi = prihodi_za(postaja)
        except Exception:               # noqa: BLE001 -- poskusimo naslednji obhod
            continue
        st["klicev"] += 1
        for v, namen in cakajo[postaja]:
            s = _vozila[v["naprava"]]
            s.poskus_ts = zdaj
            if s.trip_id:
                zasedene.pop((s.trip_id, s.dan), None)
            najdena, zakaj, p = razresi(v, prihodi, idx, zasedene, sosedi)
            if najdena is None:
                if s.trip_id and namen == PREVERI and obdrzi(s, zakaj, okna, zdaj):
                    # Znova čez minuto, ne čez 10: naslednje postajališče ima
                    # svoj prihod, in vrsta za drugim avtobusom se razpusti.
                    s.obdrzana, s.zakaj = True, zakaj
                    s.razreseno_ts = zdaj - PREVERI_S + ZNOVA_S
                    continue
                _izpusti(conn, s, v["naprava"], zakaj)
                st["brez"][zakaj] = st["brez"].get(zakaj, 0) + 1
                continue
            trip_id, dan, seq = najdena
            if s.trip_id and (s.trip_id, s.dan) != (trip_id, dan):
                st["preklopov"] += 1
                _odstrani(conn, s, v["naprava"])
            for k, o in _vozila.items():
                if o is not s and o.obdrzana and (o.trip_id, o.dan) == (trip_id, dan):
                    _izpusti(conn, o, k, "izpodrinjena")
            s.trip_id, s.dan, s.seq = trip_id, dan, seq
            s.linija, s.varianta, s.razreseno_ts = v["linija"], v["varianta"], zdaj
            s.obdrzana = False
            zasedene[(trip_id, dan)] = v["naprava"]
            nasa = _zadnja_nasa(conn, trip_id, dan, zdaj)
            if nasa is not None and isinstance(p.get("DelayMin"), (int, float)):
                _primerjave.append(nasa - 60 * p["DelayMin"])

    brez_voznje = []
    proge = _proge(conn)
    for v in vozila:
        s = _vozila[v["naprava"]]
        lega = (v["lat"], v["lon"])
        if lega != s.lega or not s.lega_ts:
            if s.lega is not None and s.videno_ts and zdaj > s.videno_ts:
                ms = geo.haversine(*s.lega, *lega) / (zdaj - s.videno_ts)
                s.hitrost = round(ms, 1) if ms <= NAJVEC_HITROST_MS else None
            s.smer = _smer(s, *lega)
            s.lega, s.lega_ts = lega, zdaj
        elif v["zivo"]:
            s.hitrost = 0.0         # živa lega brez premika: stoji
        s.videno_ts = zdaj
        # Živa lega je zdajšnja, tudi kadar vozilo stoji; mrtva je stara od
        # zadnjega premika -- prikaz to pove in jo po 3 min skrije.
        ts = int(zdaj if v["zivo"] else s.lega_ts)
        vozilo_id = f"marprom-{v['naprava']}"
        dosje.varno(_v_dosje, v, s, ts, vozilo_id, zdaj)
        if s.trip_id is None:
            if v["linija"]:
                straza.vzorec("marprom", vozilo_id, None, zdaj)
                brez_voznje.append({
                    "vehicle_id": vozilo_id, "lat": v["lat"], "lon": v["lon"],
                    "bearing": s.smer, "seen_ts": ts,
                    "speed_ms": s.hitrost if v["zivo"] else None,
                    "train_no": proge.get(MP + v["linija"], v["linija"]),
                    "headsign": v["smer_opis"] or None,
                    "naslednja_id": v["naslednja"] or None})
            continue
        st["pripetih"] += 1
        straza.vzorec("marprom", vozilo_id, s.trip_id, zdaj)
        conn.execute(
            "INSERT INTO vehicle_now(trip_id, service_date, seen_ts, lat, lon, bearing,"
            "                        speed_ms, vehicle_id) VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(trip_id) DO UPDATE SET "
            "  service_date=excluded.service_date, seen_ts=excluded.seen_ts,"
            "  lat=excluded.lat, lon=excluded.lon, bearing=excluded.bearing,"
            "  speed_ms=excluded.speed_ms, stop_seq=NULL, status=NULL,"
            "  vehicle_id=excluded.vehicle_id "
            "WHERE excluded.seen_ts >= vehicle_now.seen_ts",
            (s.trip_id, s.dan, ts, v["lat"], v["lon"], s.smer,
             s.hitrost if v["zivo"] else None, vozilo_id))
        if (v["zivo"] and config.ZAMUDA_IZ_LEGE
                and iz_lege.brez_feeda(s.trip_id, zdaj)):
            st["prehodov"] += iz_lege.opazuj(conn, s.trip_id, s.dan, ts, v["lat"],
                                             v["lon"], vozilo_id)
    _zapisi_brez_voznje(conn, brez_voznje, zdaj, postajalisca)
    st["brez_voznje"] = len(brez_voznje)
    st["obdrzanih"] = sum(s.obdrzana for s in _vozila.values())
    st["primerjava"] = primerjava()
    return st


def _odstrani(conn: sqlite3.Connection, s: Vozilo, naprava: str) -> None:
    """Vozilo ne vozi več te vožnje: njena lega ne sme ostati na zemljevidu
    do konca svežine -- avtobus bi bil narisan dvakrat."""
    conn.execute("DELETE FROM vehicle_now WHERE trip_id = ? AND vehicle_id = ?",
                 (s.trip_id, f"marprom-{naprava}"))


def _izpusti(conn: sqlite3.Connection, s: Vozilo, naprava: str, zakaj: str) -> None:
    """Vozilo ostane brez vožnje; `zakaj` gre v dosje."""
    if s.trip_id:
        _odstrani(conn, s, naprava)
    s.trip_id = s.dan = None
    s.obdrzana = False
    s.zakaj = zakaj


#: Kar Marprom o vozilu pove sproti; drugo gre v telo dosjeja.
_SPROTNO = frozenset({"Lat", "Lon", "NextStopPointId", "LKStopPointId", "ETA", "Predicted"})


def _v_dosje(v: dict, s: Vozilo, ts: int, vozilo_id: str, zdaj: float) -> None:
    """Vzorec v `dosje`, z vsem, kar je Marprom poslal."""
    if not dosje.vklopljen():
        return
    x = v["surovo"]
    stalno = {k: y for k, y in x.items() if k not in _SPROTNO}
    razlogi = []
    if s.trip_id is None:
        razlogi += ["brez_voznje"] + ([s.zakaj] if s.zakaj else [])
    elif s.obdrzana:
        razlogi += ["obdrzana", s.zakaj]
    if not v["zivo"]:
        razlogi.append("ni_ziva")
    if not v["linija"]:
        razlogi.append("brez_linije")
    dosje.opazi("marprom", vozilo_id, ts, v["lat"], v["lon"], trip_id=s.trip_id, dan=s.dan,
                razlogi=razlogi, kljuc=tuple(sorted(stalno.items())), telo=stalno,
                sprotno={k: x[k] for k in _SPROTNO if k in x}, oznaka=v["bus"] or None, zdaj=zdaj)


def _zapisi_brez_voznje(conn: sqlite3.Connection, vozila: list[dict], zdaj: float,
                        postajalisca: dict[str, dict]) -> None:
    """Vozila brez vožnje za zemljevid, kot pri LPP (`api._vozila_brez_voznje`):
    linija in smer ju povesta, zamude ni. Ime naslednjega postajališča iz
    voznega reda, sicer Marpromovo."""
    ids = {MP + v["naslednja_id"] for v in vozila if v["naslednja_id"]}
    imena = dict(conn.execute(
        f"SELECT stop_id, name FROM station WHERE stop_id IN ({','.join('?' * len(ids))})",
        sorted(ids)).fetchall()) if ids else {}
    for v in vozila:
        pid = v.pop("naslednja_id")
        v["naslednja"] = (imena.get(MP + pid) or (postajalisca.get(pid) or {}).get("ime")
                          if pid else None)
        v["naslednja_ts"] = None
    db.set_meta(conn, "marprom_vozila_brez_voznje",
                json.dumps({"ts": int(zdaj), "vozila": vozila}, ensure_ascii=False))


class Bralnik:
    """Klici na Marpromov API, vsi skozi `viri.branje("marprom")`."""

    def __init__(self) -> None:
        self.seja = requests.Session()
        self.seja.headers["User-Agent"] = config.USER_AGENT

    def _get(self, pot: str, **params) -> dict:
        with viri.branje("marprom") as b:
            r = self.seja.get(f"{config.MARPROM_API}/{pot}", params=params or None,
                              timeout=TIMEOUT_S)
            b.http = r.status_code
            r.raise_for_status()
            b.bajtov = len(r.content)
            d = r.json()
        odgovor = d.get("Response") or {}
        if odgovor.get("Status") not in (None, 1):
            raise RuntimeError(f"Marprom: {odgovor.get('Message') or odgovor}")
        return d

    def vozila(self) -> list[dict]:
        return razberi(self._get("GetActiveDeviceDetails"))

    def prihodi(self, postaja: str) -> list[dict]:
        return self._get("GetArrivalsForStopPoint",
                         StopPointId=postaja).get("ArrivalsForStopPoints") or []

    def postajalisca(self) -> dict[str, dict]:
        """StopPointId -> ime in skupina (`StopID`)."""
        out = {}
        for p in self._get("GetAllStopPoints").get("StopPoints") or []:
            try:
                out[str(int(p["StopPointId"]))] = {
                    "ime": " ".join(str(p.get("Name") or "").split()) or None,
                    "skupina": str(p["StopID"]) if p.get("StopID") else None}
            except (KeyError, TypeError, ValueError):
                continue
        return out


def teci(stop: threading.Event, log: Callable[[str], None]) -> None:
    """Svoja nit: tuj strežnik ne sme zamikati zajema."""
    conn = db.connect()
    bralnik = Bralnik()
    napak = 0
    postajalisca, postajalisca_ts = {}, 0.0
    try:
        while not stop.is_set():
            zacetek = time.time()
            try:
                if zacetek - postajalisca_ts > POSTAJALISCA_S:
                    try:
                        postajalisca, postajalisca_ts = bralnik.postajalisca(), zacetek
                    except Exception as exc:    # noqa: BLE001 -- brez skupin gre naprej
                        postajalisca_ts = zacetek - POSTAJALISCA_S + 600
                        log(f"Marprom: postajališča: {exc}")
                vozila = bralnik.vozila()
                zdaj = time.time()
                st = korak(conn, vozila, zdaj, bralnik.prihodi, postajalisca)
                st.update(ts=int(zdaj), po_voznem_redu=po_voznem_redu(conn, zdaj))
                db.set_meta(conn, "marprom", json.dumps(st, sort_keys=True))
                # Ključ predpomnilnika `/api/vehicles` (glej `nap.korak`).
                db.set_meta(conn, "positions_fetched", str(int(zdaj)))
                conn.commit()
                if napak:
                    log(f"Marprom spet odgovarja (po {napak} napakah)")
                napak = 0
            except Exception as exc:        # noqa: BLE001 -- vir ni naš
                conn.rollback()             # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"Marprom: {exc}")
                try:
                    s = json.loads(db.get_meta(conn, "marprom") or "{}")
                    s.update(napaka=str(exc)[:200], napaka_ts=int(time.time()))
                    db.set_meta(conn, "marprom", json.dumps(s, sort_keys=True))
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            stop.wait(max(1.0, config.MARPROM_SECONDS - (time.time() - zacetek)))
    finally:
        conn.close()
