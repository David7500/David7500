"""Straža po prevoznikih: dnevna vrstica, ki pokaže, koga sprememba poslabša.

Zakaj (`docs/OPAZOVANO.md`): popravek za enega prevoznika je večkrat tiho
pokvaril drugega, ker ni bilo številke, ki bi to pokazala. Vrstica `straza_dan`
se ne obrezuje, računa se ponoči in se primerja med dnevoma ali med dvema
bazama (`kajros straza`).

**Tu ni pogoja po prevozniku.** Vir samo pove, katero vozilo je videl in na
kateri vožnji (`vzorec`, na vhodu vira); vse drugo je isti račun za vse.

Lege se hranijo 14 dni (`lega`), dnevnik avtobusov tudi (`obs`), vozila brez
vožnje pa so bila do zdaj samo trenutno stanje. Zato `straza_opazeno`: šteje od
prvega zagona naprej, nazaj jih ni mogoče prešteti (`vozila` je tam prazno).
"""
from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Toliko zadnjih dni se vsako noč prepiše: včerajšnji prometni dan se ob 3:30
#: še vozi, meritve se dopisujejo (`statistika.PREPISI_DNI`).
PREPISI_DNI = 3

#: Surova opažanja: toliko dni. Vrstica `straza_dan` ostane.
OPAZENO_DNI = 14

#: Medpomnilnik se izprazni tako poredko: 600 vozil na 10 s bi bilo sicer 60
#: upsertov na sekundo za števec, ki ga bere samo nočni račun. Ob ponovnem
#: zagonu gre v izgubo največ toliko vzorcev.
IZPRAZNI_S = 300

#: Prometni dan se začne ob treh: nočna vožnja po polnoči šteje k prejšnjemu.
ZACETEK_DNE_S = 3 * 3600

#: Trasa z manj različnimi točkami nima črte (krožna, stisnjena na dve enaki
#: točki: 86 tras, arwen 30. 10. 2026).
NAJMANJ_TOCK = 2

#: Postajališče dlje od trase: na zemljevidu vožnja ne pride do njega.
DALEC_OD_TRASE_M = 200

#: Pri zadnjem postanku: `|voznored + zamuda - feed_ts|` pod tem pomeni, da
#: feed napoveduje prihod "zdaj" (`collector.URA_NA_KONCNI_S`).
URA_NA_KONCNI_S = 45

#: Rep na končni šteje, če je zamuda na njem zrasla za več od tega.
REP_NAD_S = 120

_zaklep = threading.Lock()
_vzorci: dict[tuple[str, str, str, str], int] = defaultdict(int)
_izpraznjeno = [0.0]


def _dan(ts: float) -> str:
    return datetime.fromtimestamp(ts - ZACETEK_DNE_S, TZ).date().isoformat()


def vzorec(vir: str, vozilo: str | None, trip_id: str | None,
           zdaj: float | None = None) -> None:
    """Vir je videl vozilo; `trip_id` None = vozilo brez naše vožnje."""
    if not vozilo:
        return
    dan = _dan(time.time() if zdaj is None else zdaj)
    with _zaklep:
        _vzorci[(dan, vir, str(vozilo), trip_id or "")] += 1


def izprazni(conn: sqlite3.Connection, zdaj: float | None = None,
             vsakih_s: float = IZPRAZNI_S) -> int:
    """Medpomnilnik v `straza_opazeno`. Kliče ga zajemna zanka ob vsakem krogu."""
    zdaj = time.time() if zdaj is None else zdaj
    if zdaj - _izpraznjeno[0] < vsakih_s:
        return 0
    with _zaklep:
        vrstice = [(*k, n) for k, n in _vzorci.items()]
        _vzorci.clear()
        _izpraznjeno[0] = zdaj
    if not vrstice:
        return 0
    conn.executemany(
        "INSERT INTO straza_opazeno(dan, vir, vozilo, trip_id, vzorcev) VALUES(?,?,?,?,?) "
        "ON CONFLICT(dan, vir, vozilo, trip_id) DO UPDATE SET vzorcev = vzorcev + excluded.vzorcev",
        vrstice)
    meja = (datetime.fromtimestamp(zdaj, TZ).date() - timedelta(days=OPAZENO_DNI)).isoformat()
    conn.execute("DELETE FROM straza_opazeno WHERE dan < ?", (meja,))
    conn.commit()
    return len(vrstice)


def stevec(conn: sqlite3.Connection, dan: str, trip_id: str, ime: str) -> None:
    """Dogodek v zajemu, po prevozniku vožnje. Commit naredi klicatelj."""
    conn.execute(
        "INSERT INTO straza_stevec(dan, prevoznik, ime, n) "
        "SELECT ?, COALESCE(agency, '?'), ?, 1 FROM trip WHERE trip_id = ? "
        "ON CONFLICT(dan, prevoznik, ime) DO UPDATE SET n = n + 1", (dan, ime, trip_id))


# ---------------------------------------------------------------- merila dneva

def _ima_tabelo(conn: sqlite3.Connection, ime: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                        (ime,)).fetchone() is not None


def _osnova(conn: sqlite3.Connection) -> tuple[dict[str, str], dict[str, int]]:
    """Prevoznik in število postankov po vožnji; enako za vse dni izračuna."""
    return ({r[0]: r[1] or "?" for r in conn.execute("SELECT trip_id, agency FROM trip")},
            dict(conn.execute("SELECT trip_id, COUNT(*) FROM sched GROUP BY trip_id").fetchall()))


def _po_prevozniku(ids, agencije: dict[str, str]) -> dict[str, set]:
    out: dict[str, set] = defaultdict(set)
    for t in ids:
        a = agencije.get(t)
        if a is not None:       # sirota brez vožnje: ni je mogoče pripisati
            out[a].add(t)
    return out


def _rep_na_koncni(conn: sqlite3.Connection, dan: str,
                   agencije: dict[str, str]) -> dict[str, dict]:
    """Koliko voženj ima na koncu dnevnika končne rep, ko je zamuda samo ura.

    Iz `obs`, ki hrani tudi, kar varovalka zavrne (`run` ne): merilo kaže, kaj
    feed objavlja, pred popravkom in po njem enako, za vse prevoznike. Izmerjeno
    na arwenu 20.-30. 10. 2026 (vsi dnevi skupaj 15 s). Prihod na cilj: `delay_arr` prvi
    (CLAUDE.md, namenoma obratno).
    """
    polnoc = stats.polnoc(dan)
    out: dict[str, dict] = defaultdict(lambda: {"voznje": 0, "nad": 0})
    for trip_id, seq, t_s in conn.execute(
            "SELECT r.trip_id, r.stop_seq, COALESCE(s.arr_s, s.dep_s) FROM run r "
            "JOIN trip t ON t.trip_id = r.trip_id AND t.last_seq = r.stop_seq "
            "JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
            "WHERE r.service_date = ?", (dan,)).fetchall():
        if t_s is None:
            continue
        v = out[agencije.get(trip_id, "?")]
        v["voznje"] += 1
        konec = zacetek = None
        for d, ts in conn.execute(
                "SELECT COALESCE(delay_arr, delay_dep), feed_ts FROM obs "
                "WHERE trip_id = ? AND service_date = ? AND stop_seq = ? "
                "ORDER BY feed_ts DESC", (trip_id, dan, seq)):
            if d is None or abs(polnoc + t_s + d - ts) > URA_NA_KONCNI_S:
                break
            konec = d if konec is None else konec
            zacetek = d
        if konec is not None and konec - zacetek > REP_NAD_S:
            v["nad"] += 1
    return dict(out)


def _vozila(conn: sqlite3.Connection, dan: str, agencije: dict[str, str]) -> dict[str, dict]:
    """{prevoznik: {vir: štetje}}. Vozilo brez vožnje šteje pod vir: prevoznika
    pri medkrajevnih ne poznamo, ker ga pove šele vožnja."""
    z: dict[tuple, set] = defaultdict(set)
    brez: dict[tuple, set] = defaultdict(set)
    vzorcev: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    if not _ima_tabelo(conn, "straza_opazeno"):
        return {}
    for vir, vozilo, trip_id, n in conn.execute(
            "SELECT vir, vozilo, trip_id, vzorcev FROM straza_opazeno WHERE dan = ?", (dan,)):
        if trip_id:
            k = (agencije.get(trip_id, vir), vir)
            z[k].add(vozilo)
            vzorcev[k][0] += n
        else:
            k = (vir, vir)
            brez[k].add(vozilo)
            vzorcev[k][1] += n
    out: dict[str, dict] = defaultdict(dict)
    for k in set(z) | set(brez):
        out[k[0]][k[1]] = {"z": len(z[k]), "brez": len(brez[k]),
                           "vzorcev_z": vzorcev[k][0], "vzorcev_brez": vzorcev[k][1]}
    return dict(out)


def merila_dneva(conn: sqlite3.Connection, dan: str, osnova=None) -> dict[str, dict]:
    """Merila za en prometni dan, po prevozniku. Samo bere."""
    agencije, postankov = osnova or _osnova(conn)
    nacrt: dict[str, set] = defaultdict(set)
    for trip_id, agency in conn.execute(
            "SELECT t.trip_id, t.agency FROM trip t "
            "JOIN service_day d ON d.service_id = t.service_id WHERE d.date = ?", (dan,)):
        nacrt[agency or "?"].add(trip_id)
    lega = _po_prevozniku((r[0] for r in conn.execute(
        "SELECT DISTINCT trip_id FROM lega WHERE service_date = ?", (dan,))), agencije)
    opazeno: dict[str, set] = {}
    if _ima_tabelo(conn, "straza_opazeno"):
        opazeno = _po_prevozniku((r[0] for r in conn.execute(
            "SELECT DISTINCT trip_id FROM straza_opazeno WHERE dan = ? AND trip_id != ''",
            (dan,))), agencije)
    ima_opazeno = bool(opazeno)

    meritev = dict(conn.execute("SELECT trip_id, COUNT(*) FROM run WHERE service_date = ? "
                                "GROUP BY trip_id", (dan,)).fetchall())
    prehodov = dict(conn.execute("SELECT trip_id, COUNT(*) FROM gps_prehod WHERE service_date = ? "
                                 "GROUP BY trip_id", (dan,)).fetchall())
    z_meritvijo = _po_prevozniku(meritev, agencije)
    vozila = _vozila(conn, dan, agencije)
    rep = _rep_na_koncni(conn, dan, agencije)
    stevci: dict[str, dict] = defaultdict(dict)
    if _ima_tabelo(conn, "straza_stevec"):
        for prevoznik, ime, n in conn.execute(
                "SELECT prevoznik, ime, n FROM straza_stevec WHERE dan = ?", (dan,)):
            stevci[prevoznik][ime] = n

    out = {}
    for a in set(nacrt) | set(lega) | set(opazeno) | set(z_meritvijo) | set(vozila) | set(stevci):
        n = nacrt.get(a, set())
        z_lego = lega.get(a, set()) | opazeno.get(a, set())
        meritve = z_meritvijo.get(a, set())
        voz = z_lego | meritve
        # Načrt preteklega dne je lahko že izbrisan (mestni LPP ima vožnje po
        # datumu, `statistika._dan_prevozniki`): deleža takrat ne poznamo.
        znan_nacrt = len(n) >= len(meritve)
        out[a] = {
            "nacrt": len(n) if znan_nacrt else None,
            # Brez leg in brez opažanj je to „ne vemo“, ne 0 %: za nazaj vir
            # svojih leg ni hranil. Od prvega zagona `vzorec` velja za vse.
            "z_lego": (len(z_lego & n) if znan_nacrt else len(z_lego))
            if z_lego or ima_opazeno else None,
            "z_meritvijo": len(meritve),
            "postankov": sum(postankov.get(t, 0) for t in voz),
            "s_prehodom": sum(prehodov.get(t, 0) for t in voz),
            "postankov_z_meritvijo": sum(meritev.get(t, 0) for t in voz),
            "vozila": vozila.get(a, {}),
            "rep_voznje": rep.get(a, {}).get("voznje", 0),
            "rep_nad": rep.get(a, {}).get("nad", 0),
            "stevci": stevci.get(a, {}),
        }
    return out


# ---------------------------------------------------------------- vozni red in trase

def _vrsta_dne(d: date) -> str:
    return ("delavnik", "delavnik", "delavnik", "delavnik", "delavnik",
            "sobota", "nedelja")[d.weekday()]


def vozni_red(conn: sqlite3.Connection, od: date) -> dict[str, dict]:
    """Do kdaj ima prevoznik vožnje, po vrsti dne.

    `do` čez vse storitve skrije, da delavnikov ni več: Marprom 20. 6. 2027,
    delavniki pa do 31. 12. 2026. `prvi_brez` = prvi dan te vrste brez vožnje,
    lahko tudi praznik; `do` = zadnji z vožnjo.
    """
    po_dnevih: dict[str, dict[str, int]] = defaultdict(dict)
    for agency, dan, n in conn.execute(
            "SELECT t.agency, d.date, COUNT(*) FROM trip t "
            "JOIN service_day d ON d.service_id = t.service_id "
            "WHERE d.date >= ? GROUP BY 1, 2", (od.isoformat(),)):
        po_dnevih[agency or "?"][dan] = n
    out = {}
    for a, dnevi in po_dnevih.items():
        konec = date.fromisoformat(max(dnevi))
        vrste = {v: {"do": None, "prvi_brez": None, "voznje": None}
                 for v in ("delavnik", "sobota", "nedelja")}
        # Teden čez zadnji dan: vsaka vrsta dobi svoj prvi prazen dan.
        for i in range((konec - od).days + 8):
            d = od + timedelta(days=i)
            v = vrste[_vrsta_dne(d)]
            n = dnevi.get(d.isoformat(), 0)
            if n:
                v["do"] = d.isoformat()
                v["voznje"] = v["voznje"] or n
            elif v["prvi_brez"] is None:
                v["prvi_brez"] = d.isoformat()
        out[a] = {**vrste, "do": konec.isoformat()}
    return out


def _odmik_od_trase(kosi: list, postanki: list) -> tuple[int, float]:
    """(koliko postankov je dlje od `DALEC_OD_TRASE_M`, največji odmik v m).

    `kosi` = seznam kosov črte, `shape.points` in `osm` imata obliko
    `[[[lat,lon],...],...]` (vseh 3 505 tras, arwen 30. 10. 2026). Odseka
    med dvema kosoma ni: vožnja, ki skoči čez vrzel, ne sme skriti odmika.

    Ravninski približek zadošča za prag 200 m. Iskanje začne pri zadetku
    prejšnjega odseka: postanki si sledijo po trasi, zato dobra trasa ne
    pregleda vseh odsekov za vsak postanek (3 500 tras × 30 × 500).
    """
    kx = 111320 * math.cos(math.radians(kosi[0][0][0]))
    odseki = []
    for kos in kosi:
        xy = [(lon * kx, lat * 110540) for lat, lon in kos]
        odseki += list(zip(xy, xy[1:]))
    if not odseki:
        return 0, 0
    n = len(odseki)
    meja2 = DALEC_OD_TRASE_M ** 2
    zacni = dalec = 0
    naj = 0.0
    for lat, lon in postanki:
        px, py = lon * kx, lat * 110540
        best = math.inf
        for j in range(n):
            i = (zacni + j) % n
            (ax, ay), (bx, by) = odseki[i]
            dx, dy = bx - ax, by - ay
            d2 = dx * dx + dy * dy
            u = 0.0 if d2 == 0 else min(1.0, max(0.0, ((px - ax) * dx + (py - ay) * dy) / d2))
            r2 = (ax + u * dx - px) ** 2 + (ay + u * dy - py) ** 2
            best = min(best, r2)
            if r2 <= meja2:
                zacni = i
                break
        if best > meja2:
            dalec += 1
            naj = max(naj, math.sqrt(best))
    return dalec, round(naj)


def trase(conn: sqlite3.Connection, od: date) -> dict[str, dict]:
    """Slabe trase voženj, ki še pridejo; črta, kot jo vidi prikaz (pripeta,
    sicer surova). Za vsako najdaljša vožnja: skrajšana bi skrila odrezan del
    (LPP 18, 30. 10. 2026)."""
    out: dict[str, dict] = defaultdict(lambda: {
        "tras": 0, "premalo_tock": 0, "dalec_od_postaje": 0, "voznje_brez_trase": 0, "primeri": []})
    izbor = conn.execute(
        "SELECT t.agency, t.shape_id, t.trip_id, MAX(t.last_seq - t.first_seq) FROM trip t "
        "WHERE EXISTS (SELECT 1 FROM service_day d WHERE d.service_id = t.service_id "
        "              AND d.date >= ?) GROUP BY t.agency, t.shape_id", (od.isoformat(),)).fetchall()
    for agency, shape_id, trip_id, _ in izbor:
        a = out[agency or "?"]
        if shape_id is None:
            a["voznje_brez_trase"] = conn.execute(
                "SELECT COUNT(*) FROM trip t WHERE t.agency IS ? AND t.shape_id IS NULL AND EXISTS "
                "(SELECT 1 FROM service_day d WHERE d.service_id = t.service_id AND d.date >= ?)",
                (agency, od.isoformat())).fetchone()[0]
            continue
        a["tras"] += 1
        r = conn.execute("SELECT COALESCE(osm, points) FROM shape WHERE shape_id = ?",
                         (shape_id,)).fetchone()
        kosi = [k for k in (json.loads(r[0]) if r else []) if k]
        razlicnih = len({tuple(p) for k in kosi for p in k})
        if razlicnih < NAJMANJ_TOCK:
            a["premalo_tock"] += 1
            if len(a["primeri"]) < 5:
                a["primeri"].append({"shape_id": shape_id, "tock": razlicnih})
            continue
        postanki = conn.execute(
            "SELECT st.lat, st.lon FROM sched s JOIN station st ON st.stop_id = s.stop_id "
            "WHERE s.trip_id = ? ORDER BY s.stop_seq", (trip_id,)).fetchall()
        dalec, naj = _odmik_od_trase(kosi, [(p[0], p[1]) for p in postanki])
        if dalec:
            a["dalec_od_postaje"] += 1
            if len(a["primeri"]) < 5:
                a["primeri"].append({"shape_id": shape_id, "postankov": dalec, "m": naj})
    return dict(out)


def stanje(conn: sqlite3.Connection, od: date) -> dict[str, dict]:
    """Vozni red in trase, kakršni so zdaj. Ni meritev dneva, zato je tudi ni
    mogoče izračunati za nazaj: shrani se samo pri zadnjem dnevu."""
    vr, tr = vozni_red(conn, od), trase(conn, od)
    return {a: {"vozni_red": vr.get(a), "trase": tr.get(a)} for a in set(vr) | set(tr)}


# ---------------------------------------------------------------- nočni izračun

def dopolni(conn: sqlite3.Connection, danes: date | None = None) -> list[str]:
    """Izračunaj manjkajoče dni in prepiši zadnje. Vrne izračunane dni.

    Prvi dan v `lega` je lahko obrezan, zato začne dan za njim. Starih dni ne
    prepisuje: `lega` in `obs` jih čez 14 dni nimata več.
    """
    danes = danes or datetime.now(TZ).date()
    vceraj = danes - timedelta(days=1)
    najstarejsi = conn.execute("SELECT MIN(service_date) FROM lega").fetchone()[0]
    d = date.fromisoformat(najstarejsi) + timedelta(days=1) if najstarejsi else vceraj
    imamo = {r[0] for r in conn.execute("SELECT DISTINCT dan FROM straza_dan")}
    dnevi = []
    while d <= vceraj:
        if d.isoformat() not in imamo or (vceraj - d).days < PREPISI_DNI:
            dnevi.append(d.isoformat())
        d += timedelta(days=1)
    if not dnevi:
        return []
    zdaj = int(time.time())
    osnova = _osnova(conn)
    zadnje = stanje(conn, danes) if vceraj.isoformat() in dnevi else {}
    for dan in dnevi:
        merila = merila_dneva(conn, dan, osnova)
        vrstice = {a: (json.dumps(m, separators=(",", ":")), None) for a, m in merila.items()}
        if dan == vceraj.isoformat():
            for a, s in zadnje.items():
                vrstice[a] = (vrstice[a][0] if a in vrstice else "{}",
                              json.dumps(s, separators=(",", ":")))
        conn.executemany(
            "INSERT INTO straza_dan(dan, prevoznik, merila, stanje, izracunano) "
            "VALUES(?,?,?,?,?) ON CONFLICT(dan, prevoznik) DO UPDATE SET "
            "merila = excluded.merila, izracunano = excluded.izracunano, "
            "stanje = COALESCE(excluded.stanje, straza_dan.stanje)",
            [(dan, a, m, s, zdaj) for a, (m, s) in vrstice.items()])
        conn.commit()
    return dnevi


def beri(conn: sqlite3.Connection, dan: str | None = None,
         racunaj: bool = False) -> tuple[str | None, dict[str, dict]]:
    """(dan, {prevoznik: merila + stanje}). Česar baza nima, izračuna brez
    pisanja: tako dela tudi na kopiji in na `mode=ro`, pred prvim nočnim računom."""
    shranjeno = _ima_tabelo(conn, "straza_dan")
    if dan is None:
        if shranjeno:
            dan = conn.execute("SELECT MAX(dan) FROM straza_dan").fetchone()[0]
        dan = dan or (datetime.now(TZ).date() - timedelta(days=1)).isoformat()
    if shranjeno and not racunaj:
        vrstice = conn.execute("SELECT prevoznik, merila, stanje FROM straza_dan WHERE dan = ?",
                               (dan,)).fetchall()
        if vrstice:
            return dan, {p: {**json.loads(m), **(json.loads(s) if s else {})}
                         for p, m, s in vrstice}
    merila = merila_dneva(conn, dan)
    tu = stanje(conn, date.fromisoformat(dan) + timedelta(days=1))
    return dan, {a: {**merila.get(a, {}), **tu.get(a, {})} for a in set(merila) | set(tu)}


# ---------------------------------------------------------------- izpis in primerjava

def _delez(a, b) -> float | None:
    return round(100 * a / b, 1) if a is not None and b else None


def _vozila_vsota(v: dict, kaj: str) -> int:
    return sum(x.get(kaj, 0) for x in (v.get("vozila") or {}).values())


def _trasa(v: dict, kaj: str) -> int | None:
    return (v.get("trase") or {}).get(kaj)


#: Številčna merila: ime, račun, ali je več bolje, od katere razlike je to sprememba.
MERILA = (
    ("% voženj z lego", lambda v: _delez(v.get("z_lego"), v.get("nacrt")), True, 1.0),
    ("% voženj z meritvijo", lambda v: _delez(v.get("z_meritvijo"), v.get("nacrt")), True, 1.0),
    ("% postankov s prehodom", lambda v: _delez(v.get("s_prehodom"), v.get("postankov")), True, 1.0),
    ("% vzorcev vozil z vožnjo", lambda v: _delez(
        _vozila_vsota(v, "vzorcev_z"),
        _vozila_vsota(v, "vzorcev_z") + _vozila_vsota(v, "vzorcev_brez")), True, 1.0),
    ("vozil brez vožnje", lambda v: _vozila_vsota(v, "brez") if v.get("vozila") else None, False, 1),
    ("% repov na končni", lambda v: _delez(v.get("rep_nad"), v.get("rep_voznje")), False, 0.2),
    # Kaj je varovalka zavrnila (`collector.ura_na_koncni`), ne kakšen je feed:
    # šteje samo tam, kjer varovalka teče (zdaj mestni LPP), pri drugih je None.
    # Primerljivo med prevozniki je `% repov na končni` zgoraj, iz surovega `obs`.
    ("ura na končni, zavrnjeno", lambda v: (v.get("stevci") or {}).get("ure_na_koncni"), False, 1),
    ("trase premalo točk", lambda v: _trasa(v, "premalo_tock"), False, 1),
    ("trase daleč od postaje", lambda v: _trasa(v, "dalec_od_postaje"), False, 1),
)

VRSTE_DNE = ("delavnik", "sobota", "nedelja")


def _do(v: dict, vrsta: str) -> str | None:
    return ((v.get("vozni_red") or {}).get(vrsta) or {}).get("do")


def _st(x) -> str:
    return "–" if x is None else str(x)


def izpis(dan: str, vrstice: dict[str, dict]) -> str:
    """Tabela za terminal, prevozniki po abecedi."""
    glava = (f"{'prevoznik':10} {'načrt':>6} {'z lego':>6} {'%':>6} {'meritev':>7} "
             f"{'postankov':>9} {'% prehod':>8} {'vozil z/brez':>12} {'rep>2min':>10} "
             f"{'trase':>5} {'slabe':>5} {'delavnik do':>11} {'sobota do':>11} {'nedelja do':>11}")
    out = [f"straža {dan}", glava]
    for a in sorted(vrstice):
        v = vrstice[a]
        z, brez = _vozila_vsota(v, "z"), _vozila_vsota(v, "brez")
        slabe = None if v.get("trase") is None else (
            _trasa(v, "premalo_tock") + _trasa(v, "dalec_od_postaje"))
        out.append(
            f"{a:10} {_st(v.get('nacrt')):>6} {_st(v.get('z_lego')):>6} "
            f"{_st(_delez(v.get('z_lego'), v.get('nacrt'))):>6} {_st(v.get('z_meritvijo')):>7} "
            f"{_st(v.get('postankov')):>9} "
            f"{_st(_delez(v.get('s_prehodom'), v.get('postankov'))):>8} "
            f"{(f'{z}/{brez}' if v.get('vozila') else '–'):>12} "
            f"{str(v.get('rep_nad', 0)) + '/' + str(v.get('rep_voznje', 0)):>10} "
            f"{_st(_trasa(v, 'tras')):>5} {_st(slabe):>5} "
            f"{_st(_do(v, 'delavnik')):>11} {_st(_do(v, 'sobota')):>11} {_st(_do(v, 'nedelja')):>11}")
    return "\n".join(out)


def primerjaj(a: dict[str, dict], b: dict[str, dict]) -> list[dict]:
    """Kaj se je spremenilo od `a` do `b`, po prevozniku in merilu. Neznano
    (`None`) na eni strani ni sprememba: za nazaj vozil ni, to ni poslabšanje."""
    out = []
    for p in sorted(set(a) | set(b)):
        va, vb = a.get(p, {}), b.get(p, {})
        for ime, f, vec_bolje, prag in MERILA:
            x, y = f(va), f(vb)
            if x is None or y is None or abs(y - x) < prag:
                continue
            out.append({"prevoznik": p, "merilo": ime, "a": x, "b": y,
                        "slabse": (y < x) == vec_bolje})
        for vrsta in VRSTE_DNE:
            x, y = _do(va, vrsta), _do(vb, vrsta)
            if x and y and x != y:
                out.append({"prevoznik": p, "merilo": f"{vrsta} do", "a": x, "b": y,
                            "slabse": y < x})
    return out


def izpis_primerjave(ime_a: str, ime_b: str, razlike: list[dict]) -> str:
    slabsi = sorted({r["prevoznik"] for r in razlike if r["slabse"]})
    boljsi = sorted({r["prevoznik"] for r in razlike if not r["slabse"]})
    out = [f"primerjava {ime_a} -> {ime_b}",
           f"poslabšano: {', '.join(slabsi) or 'nihče'}",
           f"izboljšano: {', '.join(boljsi) or 'nihče'}"]
    out += [f"{'SLABŠE' if r['slabse'] else 'bolje ':6} {r['prevoznik']:10} {r['merilo']:26} "
            f"{r['a']} -> {r['b']}" for r in razlike]
    return "\n".join(out)
