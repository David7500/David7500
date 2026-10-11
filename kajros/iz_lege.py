"""Zamuda iz lege vozila -- za vožnje, ki jih feed zamud ne nosi.

Zakaj: od 21. 9. 2026 IJPP `trip_updates` nima nobene vožnje z veljavnostjo
od 21. 9. (Nomago ~430 na dan, Arriva 51), `vehicle_positions` pa ista vozila
da. Tabla je pri njih pisala „brez podatka“, četudi je bil avtobus na
zemljevidu. Števec `collector.lega_brez_zamude` to pokaže; ta modul zapolni.

Kako: vsaka lega se projicira na traso vožnje (`deljenje.Voznja`). Kadar dve
zaporedni legi, največ `NAJVEC_RAZMIK_S` narazen, oklepata postanek, je čas
prehoda linearno vmes, zamuda pa ta čas minus vozni red. Zapiše se v `run` in
`obs` kot vrednost iz feeda, z `feed_ts` = časom lege PO prehodu -- torej je
prehod potrjen (`stats.potrjen_prehod`) in vse, kar bere `run`, dela naprej
brez sprememb.

Izmerjeno 25. 9. 2026 s to kodo na vožnjah, ki imajo oboje (lege 11:40-12:04,
1 551 prehodov; Arriva, Nomago, LPP primestni, AP Murska Sobota): razlika
proti feedu mediana -4 s, absolutna mediana 5 s, p90 54 s, 92 % v 60 s in
96 % v 120 s. Brez okna voznega reda za prvo lego in brez meje hitrosti je bil
p90 759 s: krožna linija se je projicirala na napačen krak, lega pa je med
dvema točkama skočila čez osem postajališč. Cena: 0,13 ms na lego (mediana).

Izhodišča ne merimo: vozilo pred odhodom kroži po postajališču in „prehod“
izhodišča je bil v meritvi 10 min prezgodaj.

**Kjer vozilo ne vozi po trasi, prehoda ni.** 11. 10. 2026 so Arriva, Nomago
in AP MS zgrešili 3 % vmesnih postankov (Brnik letališče 15 od 17, Koper 7
od 9): trasa zavije na postajo, letališče ali v krak, vozilo ne -- ali
obratno --, in lega je več kot `ODMIK_MAX_M` od trase. Ohlapnejše meje tam
dajo slab čas (mediana 83 s proti 29 s), zato se popravlja trasa: vsak
odklon se zapiše v tabelo `odklon` (lege izven trase s sidroma na njej), iz
katere se po nekaj dneh vidi, kje vozila trase stalno ne vozijo
(`kajros odkloni`, docs/MERITVE.md).
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time

# `collector` uvozi ta modul, zato ga tu beremo šele ob klicu.
from . import collector, config, deljenje, stats


#: Dve legi dlje narazen ne povesta, kdaj je vozilo prevozilo postanek vmes.
NAJVEC_RAZMIK_S = 60
#: Hitreje vzdolž trase avtobus ne vozi; tak skok je napačna projekcija.
NAJVEC_HITROST_MS = 30
#: Lega dlje od trase ni na tej vožnji (ali pa je GPS slab).
ODMIK_MAX_M = 150
#: Kje na trasi sme biti prva lega: od toliko zamude ...
OKNO_ZAMUDA_S = 3600
#: ... do toliko prehitevanja. Brez okna se krožna linija ujame na napačen krak.
OKNO_PREHITEVA_S = 1200
#: Kako dolgo po zadnji omembi v feedu zamud vožnja še velja za pokrito.
FEED_POZABI_S = 300
#: Sled vožnje, o kateri toliko časa ni bilo lege, se pozabi.
SLED_POZABI_S = 3600
#: Odklon, po katerem toliko časa ni bilo nove lege izven trase, vozilo pa se
#: na traso ni vrnilo (vožnja končana drugje, izpad lege), se zapiše brez
#: sidra za njim.
ODKLON_ZAPRI_S = 600
#: Sled tako blizu konca trase je vožnja, ki je prispela: kar sledi, je pot v
#: garažo ali na naslednjo vožnjo, ne odklon.
ODKLON_KONEC_M = 200

_zaklep = threading.Lock()
#: trip_id -> kdaj ga je feed zamud nazadnje omenil (time.time()).
_v_feedu: dict[str, float] = {}
#: Kdaj je feed zamud prvič prebran. Pred tem ne vemo, katere vožnje nosi.
_prvic: float | None = None
#: Zagon procesa: feed, ki od zagona ni odgovoril, po `FEED_POZABI_S` ne nosi
#: ničesar (`feed_prebran`).
_zagon = time.time()
#: Vir -> vožnje iz zadnje vsebine feeda. Ob 304 je vsebina ista in te
#: vožnje so še vedno v njem.
_zadnji_nabor: dict[str, list[str]] = {}
#: (trip_id, dan) -> (t_s, along, zadnji zapisani stop_seq, kdaj osveženo)
_sled: dict[tuple[str, str], tuple[float, float, int, float]] = {}
#: (trip_id, dan) -> zadnja lega na trasi (ts, lat, lon, along): sidro odklona.
_zadnja: dict[tuple[str, str], tuple[int, float, float, float]] = {}
#: (trip_id, dan) -> odklon v teku: {"pred": sidro, "tocke": [(ts, lat, lon)],
#: "odmik": največji}.
_odklon: dict[tuple[str, str], dict] = {}
#: Kdaj je nit NAP nazadnje uspešno prebrala lege (`nap.korak`).
_nap_ts = 0.0
#: Toliko po zadnjem branju NAP še vodi zamude svojih prevoznikov, potem jih
#: spet piše feed derp.si. NAP se bere na 10 s: minuta je šest zgrešenih.
NAP_VODI_S = 60
#: Kdaj je nit zemljevida SŽ nazadnje uspešno prebrala vlake (`zamude_sz`).
_sz_ts = 0.0
#: Toliko po zadnjem branju zemljevid SŽ še vodi zamude vlakov. Bere se na
#: 30 s; dve minuti so štiri zgrešena branja, prebijanje izziva traja do 90 s.
SZ_VODI_S = 120


def zabelezi_feed(trip_ids, zdaj: float | None = None, vir: str = "ijpp") -> None:
    """Vožnje, ki jih je feed zamud pravkar nosil. Kliče `collector.ingest`."""
    global _prvic
    zdaj = time.time() if zdaj is None else zdaj
    trip_ids = list(trip_ids)
    with _zaklep:
        if _prvic is None:
            _prvic = zdaj
        for t in trip_ids:
            _v_feedu[t] = zdaj
        _zadnji_nabor[vir] = trip_ids


def nap_prebran(zdaj: float | None = None) -> None:
    """Nit NAP je pravkar prebrala lege. Kliče `nap.korak`."""
    global _nap_ts
    _nap_ts = time.time() if zdaj is None else zdaj


def nap_vodi(agency: str | None, zdaj: float | None = None) -> bool:
    """Ali zamude tega prevoznika ta hip računamo iz leg NAP, ne iz derp.si.

    Odločeno 9. 10. 2026: medkrajevni (`config.NAP_PREVOZNIKI`) gredo na NAP,
    izvirnik leg, iz katerih derp.si zamude tudi sam računa. Feed derp.si se
    za njihove vožnje ne bere, dokler NAP odgovarja; ko obmolkne, ga zajem
    spet bere sam -- izpad enega vira ne pusti avtobusov brez zamud.
    """
    zdaj = time.time() if zdaj is None else zdaj
    return agency in config.NAP_PREVOZNIKI and zdaj - _nap_ts <= NAP_VODI_S


def sz_prebran(zdaj: float | None = None) -> None:
    """Nit zemljevida SŽ je pravkar prebrala vlake. Kliče `zamude_sz.teci`."""
    global _sz_ts
    _sz_ts = time.time() if zdaj is None else zdaj


def sz_vodi(zdaj: float | None = None) -> bool:
    """Ali zamude vlakov ta hip piše zemljevid SŽ, ne feed derp.si.

    Odločeno 10. 10. 2026: derp.si vlake bere z istega zemljevida prek
    `api.modra.ninja`, torej isti podatek z dvema posrednikoma več in 15--45 s
    pozneje. Ko zemljevid ni prebran `SZ_VODI_S`, zajem derp.si vlake spet
    piše sam.
    """
    zdaj = time.time() if zdaj is None else zdaj
    return zdaj - _sz_ts <= SZ_VODI_S


def izpusti(trip_ids) -> None:
    """Feed te vožnje nosi, a jih ne beremo (`nap_vodi`): za `brez_feeda`
    niso v njem, zato jih zamuda iz lege vzame takoj, ne šele čez 5 min."""
    with _zaklep:
        for t in trip_ids:
            _v_feedu.pop(t, None)


def feed_nespremenjen(vir: str, zdaj: float | None = None) -> None:
    """Feed je odgovoril 304: vožnje zadnje vsebine so še v njem.

    Brez tega je nespremenjen feed po `FEED_POZABI_S` veljal za prazen in
    `iz_feeda` bi zamudo iz lege pisal tudi vožnjam, ki jih feed nosi.
    """
    with _zaklep:
        nabor = _zadnji_nabor.get(vir, [])
    zabelezi_feed(nabor, zdaj, vir)


def brez_feeda(trip_id: str, zdaj: float | None = None) -> bool:
    """Ali feed zamud to vožnjo res izpušča -- in ne le še ni bil prebran.

    Po zagonu počakamo, da sta prebrana oba vira (IJPP in LPP, oba na 30 s):
    sicer bi prve lege vožnje, ki jo feed nosi, šle v `run` kot iz lege.
    """
    zdaj = time.time() if zdaj is None else zdaj
    if not feed_prebran(zdaj):
        return False
    with _zaklep:
        return zdaj - _v_feedu.get(trip_id, 0.0) > FEED_POZABI_S


def feed_prebran(zdaj: float | None = None) -> bool:
    """Ali sta od zagona prebrana oba vira, torej `brez_feeda` kaj pomeni.

    Feed, ki od zagona sploh ni odgovoril, po `FEED_POZABI_S` velja za
    prebran in prazen. 8. 10. 2026 je bil derp.si ob ponovnem zagonu mrtev:
    drugi viri (`zamude_sz`, `zamude_lpp`) bi čakali do konca izpada -- prav
    takrat, ko so edini.
    """
    zdaj = time.time() if zdaj is None else zdaj
    with _zaklep:
        if _prvic is None:
            return zdaj - _zagon > FEED_POZABI_S
        return zdaj - _prvic >= 2 * config.POLL_SECONDS


def v_feedu(zdaj: float | None = None) -> set[str]:
    """Vožnje, ki jih je feed zamud omenil v zadnjih `FEED_POZABI_S`."""
    zdaj = time.time() if zdaj is None else zdaj
    with _zaklep:
        return {t for t, kdaj in _v_feedu.items() if zdaj - kdaj <= FEED_POZABI_S}


def _cas(p: dict) -> float:
    return p["dep_s"] if p["dep_s"] is not None else p["arr_s"]


def prehodi(v: deljenje.Voznja, prej: tuple[float, float] | None,
            t_s: float, along: float, zapisan_seq: int) -> list[tuple[dict, float]]:
    """Postanki, ki jih je vozilo prevozilo med `prej` in to lego, s časom prehoda.

    `zapisan_seq` je zadnji že zapisani postanek: tresenje lege naprej in nazaj
    ob postajališču ne sme dati dveh prehodov istega postanka.
    """
    if prej is None:
        return []
    t0, a0 = prej
    if not (0 < t_s - t0 <= NAJVEC_RAZMIK_S) or along <= a0:
        return []
    if (along - a0) / (t_s - t0) > NAJVEC_HITROST_MS:
        return []
    out = []
    for i, p in enumerate(v.postanki):
        if i == 0 or p["stop_seq"] <= zapisan_seq:
            continue
        if a0 < p["along"] <= along:
            out.append((p, t0 + (p["along"] - a0) / (along - a0) * (t_s - t0)))
    return out


def opazuj(conn: sqlite3.Connection, trip_id: str, dan: str, ts: int,
           lat: float, lon: float) -> int:
    """Ena lega vožnje brez zamud. Vrne število zapisanih prehodov."""
    v = deljenje.voznja(conn, trip_id)
    if v is None:
        return 0
    polnoc = stats.polnoc(dan)
    t_s = ts - polnoc
    kljuc = (trip_id, dan)
    sled = _sled.get(kljuc)
    if sled is None:
        od, do = v.okno(t_s, OKNO_ZAMUDA_S, OKNO_PREHITEVA_S)
    else:
        od, do = sled[1] - deljenje.NAZAJ_MAX_M, float("inf")
    along, odmik = v.trasa.projiciraj(lat, lon, od_m=od, do_m=do)
    if odmik > ODMIK_MAX_M:
        _lega_izven(kljuc, v, t_s, ts, lat, lon, odmik)
        return 0
    if kljuc in _odklon:
        zapisi_odklon(conn, kljuc, (ts, lat, lon, along))
    _zadnja[kljuc] = (ts, lat, lon, along)
    zapisan = sled[2] if sled else 0
    pari = prehodi(v, (sled[0], sled[1]) if sled else None, t_s, along, zapisan)
    zadnji = len(v.postanki) - 1
    for p, t_prehod in pari:
        zamuda = round(t_prehod - _cas(p))
        je_konec = p is v.postanki[zadnji]
        zapisi_meritev(conn, trip_id, dan, p["stop_seq"],
                zamuda if je_konec else None, None if je_konec else zamuda, ts)
        zapisan = p["stop_seq"]
    # Lega nazaj po trasi (tresenje) ne premakne sledi nazaj.
    if sled is None or along >= sled[1]:
        _sled[kljuc] = (t_s, along, zapisan, time.time())
    else:
        _sled[kljuc] = (sled[0], sled[1], zapisan, time.time())
    return len(pari)


def _lega_izven(kljuc: tuple[str, str], v: deljenje.Voznja, t_s: float, ts: int,
                lat: float, lon: float, odmik: float) -> None:
    """Lega več kot `ODMIK_MAX_M` od trase: del odklona, ki se zapiše, ko se
    vozilo vrne nanjo (`zapisi_odklon`)."""
    pred = _zadnja.get(kljuc)
    # Pred voznorednim odhodom vozilo pelje v prazno do izhodišča, po prihodu
    # pa v garažo: to ni odklon trase.
    if (pred is None or t_s < _cas(v.postanki[0])
            or pred[3] >= v.postanki[-1]["along"] - ODKLON_KONEC_M):
        return
    o = _odklon.setdefault(kljuc, {"pred": pred, "tocke": [], "odmik": 0.0})
    o["tocke"].append((ts, round(lat, 5), round(lon, 5)))
    o["odmik"] = max(o["odmik"], odmik)


def zapisi_odklon(conn: sqlite3.Connection, kljuc: tuple[str, str],
                  za: tuple[int, float, float, float] | None) -> None:
    """Odklon v `odklon`: lege izven trase s sidroma na njej (`za` je None,
    kadar se vozilo ni vrnilo)."""
    o = _odklon.pop(kljuc, None)
    if o is None:
        return
    pred = o["pred"]
    tocke = [list(pred[:3]), *map(list, o["tocke"])] + ([list(za[:3])] if za else [])
    oblika = conn.execute("SELECT shape_id FROM trip WHERE trip_id = ?", (kljuc[0],)).fetchone()
    conn.execute(
        "INSERT OR IGNORE INTO odklon(trip_id, service_date, shape_id, od_ts, do_ts, along_pred,"
        "                             along_za, leg, odmik_max, tocke) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (kljuc[0], kljuc[1], oblika[0] if oblika else None, o["tocke"][0][0], o["tocke"][-1][0],
         round(pred[3]), None if za is None else round(za[3]), len(o["tocke"]),
         round(o["odmik"]), json.dumps(tocke)))


def zapisi_meritev(conn: sqlite3.Connection, trip_id: str, dan: str, seq: int,
            arr: int | None, dep: int | None, ts: int, ohrani: bool = False) -> None:
    """Isto kot zapis iz feeda v `collector.ingest`, brez varoval za feedove
    napake (ničla, odpoklic prehoda) -- prehod iz lege je opažen, ne sporočen.

    Isto pot uporablja `zamude_sz`, ki pove eno samo od obeh zamud postanka
    (odhod na poti, prihod na cilju); z `ohrani` druga v `run` ostane."""
    last = conn.execute(
        "SELECT delay_arr, delay_dep FROM obs WHERE trip_id=? AND service_date=? "
        "AND stop_seq=? ORDER BY feed_ts DESC LIMIT 1", (trip_id, dan, seq)).fetchone()
    if collector.worth_logging(last, arr, dep):
        conn.execute(
            "INSERT OR IGNORE INTO obs"
            "(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts,observed_at) "
            "VALUES(?,?,?,?,?,?,?)", (trip_id, dan, seq, arr, dep, ts, int(time.time())))
    nastavi = ("delay_arr=COALESCE(excluded.delay_arr, run.delay_arr), "
               "delay_dep=COALESCE(excluded.delay_dep, run.delay_dep), " if ohrani else
               "delay_arr=excluded.delay_arr, delay_dep=excluded.delay_dep, ")
    conn.execute(
        "INSERT INTO run(trip_id,service_date,stop_seq,delay_arr,delay_dep,feed_ts) "
        "VALUES(?,?,?,?,?,?) "
        f"ON CONFLICT(trip_id,service_date,stop_seq) DO UPDATE SET {nastavi}"
        "feed_ts=excluded.feed_ts WHERE excluded.feed_ts >= run.feed_ts",
        (trip_id, dan, seq, arr, dep, ts))


def iz_feeda(conn: sqlite3.Connection, feed) -> int:
    """Vse lege iz `vehicle_positions` za vožnje, ki jih feed zamud ne nosi.

    Vrne število zapisanih prehodov.
    """
    okna = collector._rail_trip_windows(conn)
    zamenjave = collector._zamenjave(conn)
    agencije = collector._agencije(conn)
    n = 0
    for e in feed.entity:
        v = e.vehicle
        tid = v.trip.trip_id
        if tid not in okna and tid in zamenjave:
            tid = zamenjave[tid][0]
        dan = v.trip.start_date
        if (tid not in okna or len(dan) != 8 or not v.timestamp
                or not v.HasField("position") or not brez_feeda(tid)):
            continue
        # Vožnje prevoznikov NAP vodi nit NAP; ista sled v dveh nitih bi se
        # prepletala.
        if nap_vodi(agencije.get(tid)):
            continue
        n += opazuj(conn, tid, f"{dan[:4]}-{dan[4:6]}-{dan[6:]}", v.timestamp,
                    v.position.latitude, v.position.longitude)
    pospravi(conn=conn)
    conn.commit()
    return n


def pospravi(zdaj: float | None = None, conn: sqlite3.Connection | None = None) -> None:
    """Pozabi sledi voženj brez lege in vožnje, ki jih feed ne nosi več; z
    `conn` zapiše odklone, iz katerih se vozilo ni vrnilo."""
    zdaj = time.time() if zdaj is None else zdaj
    # `list()` najprej: sledi piše tudi nit NAP (`nap.zapisi`), in slovar, ki
    # se med obhodom spremeni, vrže napako. `list(d.items())` je en klic v C.
    if conn is not None:
        for k in [k for k, o in list(_odklon.items())
                  if zdaj - o["tocke"][-1][0] > ODKLON_ZAPRI_S]:
            zapisi_odklon(conn, k, None)
    for k in [k for k, s in list(_sled.items()) if zdaj - s[3] > SLED_POZABI_S]:
        _sled.pop(k, None)
        _zadnja.pop(k, None)
        _odklon.pop(k, None)
    with _zaklep:
        for t in [t for t, kdaj in _v_feedu.items() if zdaj - kdaj > SLED_POZABI_S]:
            del _v_feedu[t]
