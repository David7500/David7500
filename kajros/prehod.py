"""Prehod postanka iz GPS, brez trase: kdaj je bilo vozilo postanku najbližje.

Zakaj: `iz_lege` lego postavi na traso in prehod prizna, ko gre čez točko
postanka. Kjer trasa ni pot vozila -- zavije na postajo, letališče ali v
krak, vozilo pa ne, ali obratno --, lega skoči čez postanek ali pade s trase
in postanek ostane brez meritve: 12. 10. 2026 3,9 % vmesnih postankov pri
Arrivi, Nomagu in AP MS. Popravek tras bi rabil dneve podatkov in obvoza ne
bi ujel; ohlapnejše meje na trasi so dale slab čas.

Tu trase ni. Postanek je obiskan, ko pride vozilo v `POLMER_M` do njega
(tetiva med zaporednima legama, do `RAZMIK_S` narazen). Čas je **odhod** --
zadnji trenutek v `ODHOD_M` od najbližje točke --, na cilju prihod (prvi tak
trenutek). Na posnetku leg 11. 10. 2026 (186 voženj) 97,6 % vmesnih
postankov namesto 91,1 %, na skupnih isti čas (mediana 0 s, 98 % v 30 s),
proti naslednjemu postanku enako skladno kot doslej (mediana 29 s). Ostanek
so večinoma postanki, ki jim vozilo ni prišlo bližje od 300 m.

Postanki se iščejo po vrstnem redu vožnje: dokler ni potrjen nobeden, med
vsemi razen cilja, nato med naslednjimi `NAPREJ`. Preskok čez postanke velja,
če se zamuda ne spremeni za več kot `SKOK_S`; preskočene se nato poišče v
sledi med sosednjima potrjenima (`_dopolni`) -- sproti sam je na posnetku dal
94,3 %. Izhodišča ne merimo: vozilo pred odhodom kroži (proti drugemu
postanku mediana 39 s namesto 29 s).

Sled vožnje je v pomnilniku; lege so tudi v tabeli `lega` (zadnjih
`HRANI_DNI` dni), da se sled po ponovnem zagonu obnovi in da se da vsak
način merjenja ponoviti na pravih podatkih. Prehodi gredo v `gps_prehod`, v
`run` pa samo s `KAJROS_PREHOD_GPS=vodi` (`iz_lege.opazuj`).
"""
from __future__ import annotations

import math
import sqlite3
import threading
import time
from datetime import date, timedelta

from . import geo, stats

#: Vozilo je pri postanku, ko pride tako blizu. 50--150 m je na posnetku dalo
#: 96,2--97,5 %; perone ima postaja tudi ~100 m od točke v voznem redu.
POLMER_M = 100.0
#: Dve legi dlje narazen ne povesta, kod je vozilo vozilo. Na posnetku 60 s
#: 97,4 %, 300 s 97,8 %.
RAZMIK_S = 120
#: Lega, do katere bi vozilo vozilo hitreje, je napaka GPS.
SUM_MS = 45.0
#: Odhod = zadnji trenutek v toliko od najbližje točke: pri vožnji mimo
#: nekaj sekund za njo, pri stanju izhod s postanka (posnetek: mediana 7 s,
#: p90 42 s za najbližjo točko).
ODHOD_M = 50.0
#: Med toliko naslednjimi postanki se išče, ko je kateri že potrjen.
NAPREJ = 8
#: Preskok z večjo spremembo zamude ni vožnja, ampak drug kraj na poti blizu
#: kasnejšega postanka.
SKOK_S = 1200
#: Obisk mora biti v tem oknu okoli voznega reda.
OKNO_PREJ_S = 1200
OKNO_POZNEJE_S = 4 * 3600
#: Obisk cilja je končan, ko vozilo iz kroga odpelje ali ko se mu toliko
#: časa ne približa več ali ko toliko časa ni lege: na cilju vozilo stoji,
#: dobi naslednjo vožnjo ali se ugasne.
CILJ_S = RAZMIK_S
#: Sled brez lege toliko časa se pozabi.
POZABI_S = 3600
#: Lege in prehodi toliko dni; brišejo se po toliko voženj naenkrat, da
#: brisanje dneva ne zaklene baze.
HRANI_DNI = 14
BRISI_VOZENJ = 50

_M = geo.EARTH_R * math.pi / 180


class Sled:
    """Lege ene vožnje in njeni postanki v krajevni ravnini (metri)."""

    __slots__ = ("trip_id", "dan", "polnoc", "kx", "postanki", "k", "tocke",
                 "odprti", "cakajoci", "zadnja", "t_zadnji", "osvezeno")

    def __init__(self, trip_id: str, dan: str, postanki: list[tuple]):
        """`postanki` = [(stop_seq, lat, lon, voznoredni čas)] v vrstnem redu
        vožnje, z izhodiščem; čas v s od polnoči prometnega dne."""
        self.trip_id, self.dan = trip_id, dan
        self.polnoc = stats.polnoc(dan)
        self.kx = math.cos(math.radians(postanki[0][1])) * _M
        self.postanki = [(seq, lon * self.kx, lat * _M, cas) for seq, lat, lon, cas in postanki]
        self.k = 1                          # izhodišča ne merimo
        self.tocke: list[tuple[float, float, float]] = []
        self.odprti: dict[int, dict] = {}   # indeks postanka -> obisk, ki še traja
        self.cakajoci: tuple | None = None  # (indeks, obisk, zamuda) preskoka
        self.zadnja: float | None = None    # zamuda zadnjega potrjenega
        self.t_zadnji: float | None = None  # najbližja točka zadnjega potrjenega
        self.osvezeno = time.time()


def _blizina(tetiva: tuple, sx: float, sy: float) -> tuple[float, float]:
    """Razdalja in čas najbližje točke tetive do postanka."""
    t1, x1, y1, t2, x2, y2 = tetiva
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    f = 0.0 if L2 == 0 else max(0.0, min(1.0, ((sx - x1) * dx + (sy - y1) * dy) / L2))
    return math.hypot(x1 + f * dx - sx, y1 + f * dy - sy), t1 + f * (t2 - t1)


def _obisci(o: dict | None, tetiva: tuple, d: float, t: float, sx: float, sy: float) -> dict:
    """Obisk, podaljšan s tetivo v krogu."""
    t1, x1, y1, t2, x2, y2 = tetiva
    if o is None:
        o = {"t": t, "d": d, "odhod": t, "tetive": []}
    elif d < o["d"]:
        o["t"], o["d"] = t, d
    o["tetive"].append(tetiva)
    # Odhod: zadnji trenutek v d_min + ODHOD_M, linearno po tetivi.
    meja = o["d"] + ODHOD_M
    d1, d2 = math.hypot(x1 - sx, y1 - sy), math.hypot(x2 - sx, y2 - sy)
    if d2 <= meja:
        o["odhod"] = t2
    else:
        o["odhod"] = max(o["odhod"], t if d1 > meja else
                         t1 + (t2 - t1) * max(0.0, min(1.0, (meja - d1) / max(1e-6, d2 - d1))))
    return o


def _prihod(o: dict, sx: float, sy: float) -> float:
    """Prvi trenutek v d_min + ODHOD_M."""
    meja = o["d"] + ODHOD_M
    for t1, x1, y1, t2, x2, y2 in o["tetive"]:
        d1, d2 = math.hypot(x1 - sx, y1 - sy), math.hypot(x2 - sx, y2 - sy)
        if d1 <= meja:
            return t1
        if d2 <= meja:
            return t1 + (t2 - t1) * max(0.0, min(1.0, (d1 - meja) / max(1e-6, d1 - d2)))
    return o["t"]


def _v_oknu(sled: Sled, i: int, t: float) -> bool:
    return -OKNO_PREJ_S <= t - sled.postanki[i][3] <= OKNO_POZNEJE_S


def _cas(sled: Sled, i: int, o: dict) -> float:
    """Odhod s postanka, na cilju prihod."""
    if i < len(sled.postanki) - 1:
        return o["odhod"]
    _, sx, sy, _ = sled.postanki[i]
    return _prihod(o, sx, sy)


def _potrdi(sled: Sled, i: int, o: dict, dopolnjen: bool) -> tuple:
    seq, _, _, cas = sled.postanki[i]
    t = _cas(sled, i, o)
    return seq, round(t - cas), i == len(sled.postanki) - 1, dopolnjen, t


def _dopolni(sled: Sled, do_i: int, t_do: float) -> list[tuple]:
    """Postanki med zadnjim potrjenim in `do_i`, ki jih sproti ni ujelo
    (obisk prejšnjega je še trajal, ko se je ta končal, ali je bil dlje od
    `NAPREJ`): poišči jih v sledi med najbližjima točkama sosedov, po vrsti."""
    out, t_prej = [], sled.tocke[0][0] if sled.t_zadnji is None else sled.t_zadnji
    for i in range(sled.k, do_i):
        _, sx, sy, _ = sled.postanki[i]
        o = None
        for (t1, x1, y1), (t2, x2, y2) in zip(sled.tocke, sled.tocke[1:]):
            if t2 <= t_prej:
                continue
            if t1 >= t_do or t2 - t1 > RAZMIK_S and o is not None:
                break
            if t2 - t1 > RAZMIK_S:
                continue
            tetiva = (t1, x1, y1, t2, x2, y2)
            d, t = _blizina(tetiva, sx, sy)
            if d <= POLMER_M:
                o = _obisci(o, tetiva, d, t, sx, sy)
            elif o is not None:
                break
        if o is None or not _v_oknu(sled, i, o["t"]) or not t_prej <= o["t"] <= t_do:
            continue
        out.append(_potrdi(sled, i, o, True))
        t_prej = o["t"]
    return out


def _premakni(sled: Sled, i: int, o: dict) -> list[tuple]:
    """Potrdi postanek `i`, preskočene pred njim poišči v sledi."""
    out = _dopolni(sled, i, o["t"]) if i > sled.k else []
    out.append(_potrdi(sled, i, o, False))
    sled.zadnja, sled.t_zadnji, sled.k = _cas(sled, i, o) - sled.postanki[i][3], o["t"], i + 1
    sled.odprti = {j: v for j, v in sled.odprti.items() if j >= sled.k}
    return out


def _zakljuci(sled: Sled, koncani: list[int]) -> list[tuple]:
    """Končani obiski po vrsti: potrdi tiste, pred katerimi ni odprtega
    obiska in ki zamude ne spremenijo za več kot `SKOK_S`.

    Obisk, ki preskoči postanke, počaka na potrditev: velja, ko se konča
    obisk kasnejšega postanka (ali ko vozilo utihne), in odpade, ko se konča
    obisk katerega pred njim. Na posnetku je sicer vozilo na izletu tja in
    nazaj ob prvem postanku „obiskalo“ zadnjega na istem mestu in preskočilo
    vse vmes (dve vožnji, 5 in 3 postanki)."""
    out = []
    for i in sorted(koncani):
        o = sled.odprti.pop(i, None)
        if o is None or i < sled.k or any(j in sled.odprti for j in range(sled.k, i)):
            continue
        zamuda = _cas(sled, i, o) - sled.postanki[i][3]
        c = sled.cakajoci
        if c is not None and i <= c[0]:
            sled.cakajoci = c = None
        prej = sled.zadnja if c is None else c[2]
        if prej is not None and abs(zamuda - prej) > SKOK_S:
            continue
        if c is not None:
            sled.cakajoci = None
            out += _premakni(sled, c[0], c[1])
        if i == sled.k:
            out += _premakni(sled, i, o)
        else:
            sled.cakajoci = (i, o, zamuda)
    return out


def dodaj(sled: Sled, t_s: float, lat: float, lon: float) -> list[tuple]:
    """Ena lega (`t_s` v s od polnoči prometnega dne). Vrne nove prehode
    [(stop_seq, zamuda_s, je_cilj, dopolnjen, čas)]."""
    sled.osvezeno = time.time()
    x, y = lon * sled.kx, lat * _M
    if sled.tocke:
        t0, x0, y0 = sled.tocke[-1]
        if t_s <= t0 or math.hypot(x - x0, y - y0) / (t_s - t0) > SUM_MS:
            return []
    sled.tocke.append((t_s, x, y))
    n = len(sled.postanki)
    if len(sled.tocke) < 2 or sled.k >= n:
        return []
    t1, x1, y1 = sled.tocke[-2]
    if t_s - t1 > RAZMIK_S:
        sled.odprti = {}
        return []
    tetiva = (t1, x1, y1, t_s, x, y)
    # Brez potrjenega postanka cilja ne iščemo: krožna vožnja je ob odhodu
    # na cilju.
    if sled.zadnja is None and sled.cakajoci is None:
        hi = n - 1
    else:
        hi = min(n, max(sled.k, sled.cakajoci[0] + 1 if sled.cakajoci else 0) + NAPREJ)
    # Obisk daleč naprej, ki je bil odprt pred prvim potrjenim, je zanka
    # poti mimo kasnejšega postanka, ne obisk.
    for j in [j for j in sled.odprti if j >= hi]:
        del sled.odprti[j]
    koncani = []
    for i in range(sled.k, hi):
        _, sx, sy, _ = sled.postanki[i]
        d, t = _blizina(tetiva, sx, sy)
        o = sled.odprti.get(i)
        if d <= POLMER_M and _v_oknu(sled, i, t):
            o = sled.odprti[i] = _obisci(o, tetiva, d, t, sx, sy)
            if (math.hypot(x - sx, y - sy) > POLMER_M
                    or i == n - 1 and t_s - o["t"] >= CILJ_S):
                koncani.append(i)
        elif o is not None:
            koncani.append(i)
    return _zakljuci(sled, koncani)


def tiho(sled: Sled, zdaj: float) -> list[tuple]:
    """Vsaj `CILJ_S` brez lege: obisk cilja je končan in obisk, ki čaka na
    potrditev, velja."""
    if (not sled.tocke or zdaj - (sled.polnoc + sled.tocke[-1][0]) < CILJ_S
            or len(sled.postanki) - 1 not in sled.odprti and sled.cakajoci is None):
        return []
    out = _zakljuci(sled, list(sled.odprti)) if len(sled.postanki) - 1 in sled.odprti else []
    if sled.cakajoci is not None:
        i, o, _ = sled.cakajoci
        sled.cakajoci = None
        out += _premakni(sled, i, o)
    return out


# ------------------------------------------------------------ v strežniku

#: (trip_id, dan) -> Sled. Sledi pišeta nit NAP in zajem derp.si, vsaka za
#: svoje vožnje; zaklep le okoli pomnilnika, nikoli okoli baze (dve niti s
#: pisalnim prometom bi se zaklenili druga ob drugo).
_sledi: dict[tuple[str, str], Sled] = {}
_zaklep = threading.Lock()
#: Od zagona, za /admin.
stevci = {"leg": 0, "prehodov": 0, "dopolnjenih": 0, "obnovljenih": 0}
_brisi_po = 0.0


def _nova(conn: sqlite3.Connection, trip_id: str, dan: str) -> Sled | None:
    postanki = conn.execute(
        "SELECT s.stop_seq, st.lat, st.lon, COALESCE(s.dep_s, s.arr_s) FROM sched s "
        "JOIN station st USING (stop_id) WHERE s.trip_id = ? ORDER BY s.stop_seq",
        (trip_id,)).fetchall()
    return Sled(trip_id, dan, postanki) if len(postanki) >= 2 else None


def lega(conn: sqlite3.Connection, trip_id: str, dan: str, ts: int, lat: float,
         lon: float) -> list[tuple]:
    """Lega vožnje: v `lega`, v sled; vrne nove prehode. Sled, ki je ta proces
    še nima, se najprej obnovi iz `lega` -- po ponovnem zagonu bi se sicer
    izgubil obisk, ki je ravno trajal, in vsi postanki do naslednjega."""
    conn.execute("INSERT OR IGNORE INTO lega(service_date, trip_id, ts, lat, lon) "
                 "VALUES(?,?,?,?,?)", (dan, trip_id, ts, round(lat, 6), round(lon, 6)))
    kljuc = (trip_id, dan)
    prej = []
    if kljuc not in _sledi:
        sled = _nova(conn, trip_id, dan)
        if sled is None:
            return []
        prej = conn.execute("SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? "
                            "AND ts < ? ORDER BY ts", (dan, trip_id, ts)).fetchall()
        with _zaklep:
            _sledi.setdefault(kljuc, sled)
    out = []
    with _zaklep:
        sled = _sledi[kljuc]
        for t, la, lo in prej:
            out += dodaj(sled, t - sled.polnoc, la, lo)
        out += dodaj(sled, ts - sled.polnoc, lat, lon)
    stevci["leg"] += 1
    stevci["obnovljenih"] += bool(prej)
    return out


def zapisi(conn: sqlite3.Connection, trip_id: str, dan: str, prehodi: list[tuple],
           ts: int) -> None:
    """Prehodi v `gps_prehod`, za primerjavo z `run`."""
    polnoc = stats.polnoc(dan)
    for seq, zamuda, je_cilj, dopolnjen, t in prehodi:
        conn.execute(
            "INSERT INTO gps_prehod(service_date, trip_id, stop_seq, zamuda_s, prehod_ts,"
            "                       je_cilj, dopolnjen, zapisano_ts) VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(service_date, trip_id, stop_seq) DO UPDATE SET "
            "  zamuda_s = excluded.zamuda_s, prehod_ts = excluded.prehod_ts,"
            "  dopolnjen = excluded.dopolnjen, zapisano_ts = excluded.zapisano_ts",
            (dan, trip_id, seq, zamuda, round(polnoc + t), int(je_cilj), int(dopolnjen), ts))
    stevci["prehodov"] += len(prehodi)
    stevci["dopolnjenih"] += sum(p[3] for p in prehodi)


def pospravi(conn: sqlite3.Connection, zdaj: float | None = None) -> list[tuple]:
    """Zaključi obiske cilja brez lege, pozabi stare sledi in pobriše po
    `BRISI_VOZENJ` voženj, starejših od `HRANI_DNI`. Vrne zaključene
    prehode kot [(trip_id, dan, prehodi, ts zadnje lege)]."""
    global _brisi_po
    zdaj = time.time() if zdaj is None else zdaj
    out = []
    with _zaklep:
        for k, s in list(_sledi.items()):
            if s.tocke and (p := tiho(s, zdaj)):
                out.append((s.trip_id, s.dan, p, round(s.polnoc + s.tocke[-1][0])))
            if zdaj - s.osvezeno > POZABI_S:
                del _sledi[k]
    if zdaj >= _brisi_po:
        meja = (date.fromtimestamp(zdaj) - timedelta(days=HRANI_DNI)).isoformat()
        n = sum(conn.execute(
            f"DELETE FROM {t} WHERE (service_date, trip_id) IN (SELECT DISTINCT "
            f"service_date, trip_id FROM {t} WHERE service_date < ? LIMIT ?)",
            (meja, BRISI_VOZENJ)).rowcount for t in ("lega", "gps_prehod"))
        if n == 0:
            _brisi_po = zdaj + 3600
    return out


def _opis(x: list[float]) -> dict | None:
    if not x:
        return None
    x = sorted(abs(v) for v in x)
    return {"n": len(x), "mediana": x[len(x) // 2], "p90": x[int(0.9 * (len(x) - 1))],
            "v30": sum(v <= 30 for v in x) / len(x), "v60": sum(v <= 60 for v in x) / len(x)}


def primerjava(conn: sqlite3.Connection, od_dan: str, do_dan: str) -> dict:
    """Brez trase (`gps_prehod`) proti `run` na vožnjah z legami v `lega`.

    Šteti so vmesni postanki med prvim in zadnjim, ki ga je izmeril kdorkoli,
    in ne pred prvo lego (vožnja, ki je tekla že pred zagonom, nima sledi za
    začetek). Skladnost = razlika zamude med zaporednima izmerjenima vmesnima
    postankoma; meritev, ki laže, jo poveča."""
    vozenj, vmesnih = 0, 0
    st = {"star": 0, "nov": 0, "dopolnjenih": 0, "samo_star": 0, "samo_nov": 0}
    razlike, cilj_razl, sosed = [], [], {"star": [], "nov": []}
    cilj = {"star": 0, "nov": 0, "vozenj": 0}
    po_prevozniku: dict[str, list[int]] = {}
    for dan, tid, prva, agency in conn.execute(
            "SELECT l.service_date, l.trip_id, MIN(l.ts), t.agency FROM lega l "
            "JOIN trip t USING (trip_id) WHERE l.service_date BETWEEN ? AND ? "
            "GROUP BY l.service_date, l.trip_id", (od_dan, do_dan)).fetchall():
        sched = conn.execute("SELECT stop_seq, COALESCE(dep_s, arr_s) FROM sched "
                             "WHERE trip_id = ? ORDER BY stop_seq", (tid,)).fetchall()
        if len(sched) < 3:
            continue
        star = {r[0]: r[1] for r in conn.execute(
            "SELECT stop_seq, COALESCE(delay_dep, delay_arr) FROM run WHERE trip_id = ? "
            "AND service_date = ? AND COALESCE(delay_dep, delay_arr) IS NOT NULL", (tid, dan))}
        nov = {r[0]: (r[1], r[2]) for r in conn.execute(
            "SELECT stop_seq, zamuda_s, dopolnjen FROM gps_prehod WHERE service_date = ? "
            "AND trip_id = ?", (dan, tid))}
        seqs = [r[0] for r in sched]
        izm = [s for s in seqs[1:-1] if s in star or s in nov]
        if not izm:
            continue
        vozenj += 1
        zacetek = prva - stats.polnoc(dan)
        vmes = [s for s, cas in sched[1:-1] if izm[0] <= s <= izm[-1] and cas >= zacetek]
        pp = po_prevozniku.setdefault(agency or "?", [0, 0, 0])
        for s in vmes:
            a, b = s in star, s in nov
            st["star"] += a
            st["nov"] += b
            st["dopolnjenih"] += b and nov[s][1]
            st["samo_star"] += a and not b
            st["samo_nov"] += b and not a
            pp[0] += 1
            pp[1] += a
            pp[2] += b
            if a and b:
                razlike.append(nov[s][0] - star[s])
        vmesnih += len(vmes)
        for ime, m in (("star", star), ("nov", {s: v[0] for s, v in nov.items()})):
            ze = [s for s in vmes if s in m]
            for x, y in zip(ze, ze[1:]):
                if seqs.index(y) == seqs.index(x) + 1:
                    sosed[ime].append(m[y] - m[x])
        konec = seqs[-1]
        if sched[-1][1] >= zacetek:
            cilj["vozenj"] += 1
            cilj["star"] += konec in star
            cilj["nov"] += konec in nov
            if konec in star and konec in nov:
                cilj_razl.append(nov[konec][0] - star[konec])
    return {"vozenj": vozenj, "vmesnih": vmesnih, **st, "razlika": _opis(razlike),
            "sosed_star": _opis(sosed["star"]), "sosed_nov": _opis(sosed["nov"]),
            "cilj": {**cilj, "razlika": _opis(cilj_razl)},
            "po_prevozniku": po_prevozniku}
