"""Zapore tira in vlak pred tabo: kje lahko vlak danes izgubi čas.

Dvoje, kar napoved zamude ne ve, potnik pa bi rad vedel:

* **Zapora enega tira** iz obvestila SŽ (`SZ-OVIRA`). Dneve in uro ima
  obvestilo samo v besedilu -- "Na progi Zagorje - Sava (19. - 20. in 26. ter
  27. september in 1., 2. ter 5. - 8. oktober, 7.00 - 13.30)" -- `start_ts`
  in `end_ts` pa pokrivata vse obdobje. Zato so obvestila doslej veljala za
  neuporabna: med dnevi niso ločila ničesar.
* **Vlak pred tabo**, ki je na istem odseku v isti smeri v zadnji uri izgubil
  vsaj deset minut.

Napovedi se ne dotikamo. Izmerjeno 5. 10. 2026 (`docs/MERITVE.md`): ob
delavnikih z zaporo Zagorje - Sava je vlak tam izgubil 5 min ali več pri 28 %
prehodov, sicer pri manj kot odstotku; za vlakom, ki je izgubil 10 min ali več,
naslednji pri 17,9 % (osnova 2,3 %). Mediana izgube je v obeh primerih 0 --
kateri vlak bo čakal na križanje, se ne ve. Višja številka bi trem od štirih
potnikov vlak odpeljala pred nosom, zato je to opozorilo z izmerjenim
tveganjem, ne popravek napovedi.
"""
from __future__ import annotations

import heapq
import re
import sqlite3
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, db, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Od koliko izgube naprej je vlak pred tabo vreden omembe, in kako dolgo
#: nazaj šteje. Prag in okno sta ista kot v meritvi (17,9 % proti 2,3 %).
IZGUBA_PRED_TABO_S = 600
PRED_TABO_OKNO_S = 3600

#: Izguba, ki se šteje v tveganje zapore. Pod tem je šum zaokroževanja feeda.
IZGUBA_STEJE_S = 300

#: Pod toliko prehodi iz prejšnjih dni zapore številke ne povemo: "1 od 2" ni
#: tveganje, ampak naključje.
NAJMANJ_PREHODOV = 10

#: Zgornja meja zamude ob zapori: ta delež izgub na prejšnjih dneh iste
#: zapore, z ničlami. Izmerjeno na senci 5. 9.-5. 10. 2026 (4 233 napovedi z
#: zaporo na poti): resnica pod mejo pri p75 73,3 %, p80 79,2 %, p85 84,1 %,
#: **p90 89,7 %** (širina mediana 8 min), p95 93,7 % (11 min). Vlak pred njim
#: prispeva svojo izgubo: 94,9 % (2 942), oboje 93,3 % (506).
ZGORNJA_MEJA_DELEZ = 0.9

_MESECI = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "maj": 5, "jun": 6, "jul": 7,
           "avg": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12}

_TOK = re.compile(
    r"(?P<ura>(?:od\s+)?\d{1,2}[.:]\d{2}\s*(?:-|do)\s*\d{1,2}[.:]\d{2})"
    r"|(?P<nep>neprekinjeno(?:\s+do\s+\d{1,2}[.:]\d{2})?)"
    r"|(?P<cas>\d{1,2}[.:]\d{2})"
    r"|(?P<dan>\d{1,2})\."
    r"|(?P<crta>-|\bdo\b)"
    r"|(?P<loc>,)"
    r"|(?P<beseda>[a-zčšž]+)")
_URA = re.compile(r"(\d{1,2})[.:](\d{2})\s*(?:-|do)\s*(\d{1,2})[.:](\d{2})")


def _normaliziraj(besedilo: str) -> str:
    t = besedilo.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t)


def _mesec(beseda: str) -> int | None:
    return _MESECI.get(beseda[:3]) if len(beseda) >= 3 else None


def _okna(notranje: str, zacetek: date, konec: date) -> list[tuple[date, int, int]] | None:
    """[(dan, od_min, do_min)] iz besedila v oklepaju, ali None, ce ni jasno.

    Dnevi se nabirajo, dokler jih ne zapre ura ("7.00 - 13.30") ali
    "neprekinjeno" (ves dan). Mesec velja za vse prejšnje dneve brez meseca;
    stevilka takoj za stevilko je mesec ("11. 9.").
    """
    okna: list[tuple[date, int, int]] = []
    cakajo: list[list] = []          # [[d0, m0, d1, m1]] -- razpon ali en dan
    razpon = False
    prejsnji = None
    zadnje_okno: tuple[int, int] | None = None

    def zapri(od_min: int, do_min: int) -> bool:
        for d0, m0, d1, m1 in cakajo:
            if m0 is None or m1 is None:
                return False
            for x in _dnevi(d0, m0, d1, m1, zacetek):
                okna.append((x, od_min, do_min))
        cakajo.clear()
        return True

    for m in _TOK.finditer(notranje.lower()):
        vrsta = m.lastgroup
        if vrsta == "ura":
            h0, m0, h1, m1 = map(int, _URA.search(m.group()).groups())
            zadnje_okno = (h0 * 60 + m0, h1 * 60 + m1)
            if not zapri(*zadnje_okno):
                return None
            razpon = False
        elif vrsta == "nep":
            zadnje_okno = (0, 24 * 60)
            if not zapri(*zadnje_okno):
                return None
            razpon = False
        elif vrsta == "dan":
            d = int(m.group("dan"))
            if prejsnji == "dan" and d <= 12 and cakajo:
                # "11. 9." -- druga stevilka je mesec
                for x in cakajo:
                    x[1] = x[1] or d
                    x[3] = x[3] or d
            elif razpon and cakajo:
                cakajo[-1][2], cakajo[-1][3] = d, None
            else:
                cakajo.append([d, None, d, None])
            razpon = False
        elif vrsta == "crta":
            razpon = True
        elif vrsta == "beseda":
            mes = _mesec(m.group())
            if mes:
                for x in cakajo:
                    x[1] = x[1] or mes
                    x[3] = x[3] or mes
            elif m.group() != "od":
                razpon = False
        prejsnji = vrsta if vrsta in ("dan", "beseda", "crta") else "drugo"
    # Kar ostane za "neprekinjeno", velja ves dan; za uro pa ni jasno, kam sodi.
    if cakajo and zadnje_okno == (0, 24 * 60):
        if not zapri(0, 24 * 60):
            return None
    # Varovalka pred napačnim branjem: dan zunaj veljavnosti obvestila ni zapora.
    okna = [o for o in okna if zacetek - timedelta(days=1) <= o[0] <= konec + timedelta(days=1)]
    return okna or None


def _dnevi(d0: int, m0: int, d1: int, m1: int, zacetek: date):
    leto = zacetek.year
    a = date(leto, m0, d0)
    if a < zacetek - timedelta(days=60):
        a = date(leto + 1, m0, d0)
    b = date(a.year, m1, d1)
    if b < a:
        b = date(a.year + 1, m1, d1)
    if (b - a).days > 62:
        return []
    return [a + timedelta(days=i) for i in range((b - a).days + 1)]


def razberi(opis: str, zacetek: date, konec: date) -> list[dict]:
    """Zapore iz besedila obvestila: [{"odseki": [(od, do)], "okna": [...]}].

    Odsek je kos pred oklepajem ("Na progi Zagorje - Sava (...)", "... in
    Krško - Brestanica (...)"). Kadar oklepaj sam našteva odseke ("26. 8.
    Kresnice - Laze ..."), ga izpustimo -- branj je preveč in napačna zapora
    je slabša od nobene.
    """
    t = _normaliziraj(opis or "")
    out = []
    for m in re.finditer(r"\(([^()]*)\)", t):
        notranje = m.group(1)
        if not (_URA.search(notranje) or "neprekinjeno" in notranje):
            continue
        if re.search(r"[A-Za-zčšžČŠŽ]\s+-\s+[A-ZČŠŽ]", notranje):
            continue
        kos = re.split(r"Na progi|\bin\b|\bter\b|,|\)|\.\s", t[:m.start()].rstrip(" ."))[-1]
        imena = [x.strip(" .") for x in kos.split(" - ")]
        if len(imena) < 2 or not all(imena):
            continue
        odseki = []
        for a, b in zip(imena, imena[1:]):
            for x in a.split("/"):
                for y in b.split("/"):
                    if x.strip() and y.strip():
                        odseki.append((x.strip(), y.strip()))
        okna = _okna(notranje, zacetek, konec)
        if odseki and okna:
            out.append({"odseki": odseki, "okna": okna})
    return out


# ---------------------------------------------------------------- proga

_GRAF: dict = {}


def _graf(conn: sqlite3.Connection) -> dict:
    """Elementarni odseki železnice: sosedi in ime -> stop_id."""
    kljuc = db.cache_key(conn)
    if kljuc is not None and _GRAF.get("kljuc") == kljuc:
        return _GRAF
    sosedi: dict[str, list[tuple[str, float]]] = {}
    for r in conn.execute("SELECT from_id, to_id, km FROM edge WHERE elementary = 1"):
        sosedi.setdefault(r[0], []).append((r[1], r[2]))
        sosedi.setdefault(r[1], []).append((r[0], r[2]))
    ime = {}
    if sosedi:
        marks = ",".join("?" * len(sosedi))
        ime = {r[1].lower(): r[0] for r in conn.execute(
            f"SELECT stop_id, name FROM station WHERE stop_id IN ({marks})", list(sosedi))}
    g = {"kljuc": kljuc, "sosedi": sosedi, "ime": ime, "poti": {}}
    if kljuc is not None:
        _GRAF.clear()
        _GRAF.update(g)
    return g


def pot(g: dict, a: str, b: str) -> tuple[tuple[str, str], ...]:
    """Elementarni odseki od postaje a do b, v smeri vožnje (najkrajša pot)."""
    k = (a, b)
    if k in g["poti"]:
        return g["poti"][k]
    sosedi = g["sosedi"]
    razdalja, prej = {a: 0.0}, {}
    vrsta = [(0.0, a)]
    while vrsta:
        d, x = heapq.heappop(vrsta)
        if x == b:
            break
        if d > razdalja[x]:
            continue
        for y, km in sosedi.get(x, ()):
            if d + km < razdalja.get(y, float("inf")):
                razdalja[y], prej[y] = d + km, x
                heapq.heappush(vrsta, (d + km, y))
    out: list[tuple[str, str]] = []
    if b in prej or a == b:
        x = b
        while x != a:
            out.append((prej[x], x))
            x = prej[x]
    g["poti"][k] = tuple(reversed(out))
    return g["poti"][k]


# ---------------------------------------------------------------- zapore dneva

_RAZBRANO: dict = {}
_ZAPORE: dict = {}


def zapore(conn: sqlite3.Connection, dan: date | None = None) -> list[dict]:
    """Zapore iz obvestil, z odseki kot elementarnimi odseki proge.

    `dan` omeji na zapore, ki imajo ta dan vsaj eno okno. Besedilo se razbere
    enkrat na obvestilo; seznam se drži minuto, ker ga tabla rabi za vsako
    vrstico.
    """
    kljuc = (db.cache_key(conn), dan, int(time.time()) // 60)
    if kljuc[0] is not None and kljuc in _ZAPORE:
        return _ZAPORE[kljuc]
    g = _graf(conn)
    out = []
    for r in conn.execute(
            "SELECT alert_id, start_ts, end_ts, description FROM alert "
            "WHERE kind = 'ovira' AND lang = 'sl' AND description LIKE '%zapora%tira%'"):
        kr = (r["alert_id"], r["description"])
        if kr not in _RAZBRANO:
            zacetek = datetime.fromtimestamp(r["start_ts"] or 0, TZ).date()
            konec = datetime.fromtimestamp(r["end_ts"] or 0, TZ).date()
            _RAZBRANO[kr] = razberi(r["description"], zacetek, konec)
        for z in _RAZBRANO[kr]:
            okna = [o for o in z["okna"] if dan is None or o[0] == dan]
            if not okna:
                continue
            robovi, imena = set(), []
            for a, b in z["odseki"]:
                ia, ib = g["ime"].get(a.lower()), g["ime"].get(b.lower())
                p = pot(g, ia, ib) if ia and ib else ()
                if p:
                    robovi |= {frozenset(e) for e in p}
                    imena.append(f"{a} – {b}")
            if robovi:
                out.append({"alert_id": r["alert_id"], "robovi": robovi,
                            "odsek": ", ".join(imena), "okna": okna,
                            "vsa_okna": z["okna"]})
    if kljuc[0] is not None:
        _ZAPORE.clear()
        _ZAPORE[kljuc] = out
    return out


def _v_oknu(okna, ts: int) -> tuple | None:
    t = datetime.fromtimestamp(ts, TZ)
    m = t.hour * 60 + t.minute
    for o in okna:
        if o[0] == t.date() and o[1] <= m <= o[2]:
            return o
    return None


def _prehodi(conn: sqlite3.Connection, g: dict, dnevi: list[str]):
    """Vsak par zaporednih izmerjenih postankov iste vožnje teh dni.

    (dan, trip_id, train_no, od, do, seq_od, seq_do, ts_od, ts_do, izguba_s,
    robovi) -- robovi so elementarni odseki med postankoma v smeri vožnje.
    """
    for dan in dnevi:
        polnoc = stats.polnoc(dan)
        # Od voženj k meritvam (CROSS JOIN določi vrstni red), ne od dneva:
        # `run` ima za dan tudi vse avtobuse. Na arwenu 0,75 s -> 0,06 s na
        # dan; Ljubljana - Zalog ima 13 dni zapore in prva tabla je čakala 20 s.
        vrstice = conn.execute(
            "SELECT r.trip_id, t.train_no, s.stop_seq, s.stop_id, st.name, "
            "       COALESCE(s.dep_s, s.arr_s) AS t_s, "
            "       COALESCE(r.delay_dep, r.delay_arr) AS d "
            "FROM trip t CROSS JOIN run r ON r.trip_id = t.trip_id AND r.service_date = ? "
            "JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
            "JOIN station st ON st.stop_id = s.stop_id "
            "WHERE t.network = 'zeleznica' AND d IS NOT NULL "
            f"  AND ABS(d) <= {stats.MAX_REALNA_ZAMUDA_S} "
            "ORDER BY r.trip_id, s.stop_seq", (dan,)).fetchall()
        for x, y in zip(vrstice, vrstice[1:]):
            if x["trip_id"] != y["trip_id"] or x["t_s"] is None or y["t_s"] is None:
                continue
            yield (dan, x["trip_id"], x["train_no"], x["name"], y["name"],
                   x["stop_seq"], y["stop_seq"],
                   polnoc + x["t_s"] + x["d"], polnoc + y["t_s"] + y["d"],
                   y["d"] - x["d"], pot(g, x["stop_id"], y["stop_id"]))


_TVEGANJE: dict = {}


def tveganje(conn: sqlite3.Connection, z: dict, danes: date) -> dict | None:
    """Kaj je ta zapora vlake stala na prejšnjih dneh, ko je že veljala.

    Samo dnevi te zapore pred danes (nekaj jih je) in enkrat na dan -- ni
    agregat čez vso zgodovino. Pod `NAJMANJ_PREHODOV` vrne None.
    """
    kljuc = (db.cache_key(conn), z["alert_id"], z["odsek"], danes)
    if kljuc[0] is not None and kljuc in _TVEGANJE:
        return _TVEGANJE[kljuc]
    g = _graf(conn)
    dnevi = sorted({o[0].isoformat() for o in z["vsa_okna"] if o[0] < danes})
    vse, dni = [], set()
    for p in _prehodi(conn, g, dnevi):
        if not ({frozenset(e) for e in p[10]} & z["robovi"]) or not _v_oknu(z["vsa_okna"], p[7]):
            continue
        vse.append(p[9])
        dni.add(p[0])
    izgube = [x for x in vse if x >= IZGUBA_STEJE_S]
    out = ({"dni": len(dni), "prehodov": len(vse), "izgubilo": len(izgube),
            "najmanj_s": min(izgube) if izgube else None,
            "najvec_s": max(izgube) if izgube else None,
            # Z ničlami vred: devet od desetih vlakov je izgubilo največ toliko.
            "p90_s": max(0, round(stats._pct(vse, ZGORNJA_MEJA_DELEZ)))}
           if len(vse) >= NAJMANJ_PREHODOV else None)
    if len(_TVEGANJE) > 500:
        _TVEGANJE.clear()
    _TVEGANJE[kljuc] = out
    return out


def ogrej(conn: sqlite3.Connection, dan: str) -> int:
    """Današnje zapore in njihovo tveganje vnaprej, v niti za ogrevanje.

    Na arwenu je prvi klic dneva stal ~3 s (tveganje Ljubljana - Zalog bere
    13 dni); brez tega ga plača prva tabla po polnoči ali po zagonu.
    """
    d = date.fromisoformat(dan)
    zap = zapore(conn, d)
    for z in zap:
        tveganje(conn, z, d)
    return len(zap)


_DANES: dict = {}


def izgube_danes(conn: sqlite3.Connection, dan: str, zdaj: int) -> list[tuple]:
    """Odseki, kjer je vlak v zadnji uri izgubil vsaj `IZGUBA_PRED_TABO_S`.

    Samo prevoženi postanki (`stats.last_measured`): feed SŽ postanke pred
    vlakom odšteva po uri s staro zamudo, prava izguba pride šele z besedo
    za postanek nazaj. Predpomnjeno na minuto.
    """
    kljuc = (db.cache_key(conn), dan, zdaj // 60)
    if kljuc[0] is not None and _DANES.get("kljuc") == kljuc:
        return _DANES["izgube"]
    g = _graf(conn)
    vse = [p for p in _prehodi(conn, g, [dan])
           if p[9] >= IZGUBA_PRED_TABO_S and zdaj - PRED_TABO_OKNO_S <= p[8] <= zdaj]
    meje = (stats.last_measured(conn, dan, list({p[1] for p in vse}),
                                zdaj - stats.polnoc(dan)) if vse else {})
    izgube = [p for p in vse if p[1] in meje and p[6] <= meje[p[1]]["stop_seq"]]
    _DANES.update({"kljuc": kljuc, "izgube": izgube})
    return izgube


def za_voznjo(conn: sqlite3.Connection, trip_id: str, dan: str, od_seq: int | None,
              do_seq: int | None, zamuda_s: int, zdaj: int | None = None) -> list[dict]:
    """Opozorila za vožnjo med postankoma `od_seq` (zadnji prevoženi ali
    izhodišče) in `do_seq` (potnikova postaja ali konec).

    Čas prehoda zapore = vozni red + `zamuda_s`; za okno ur dovolj natančno.
    """
    zdaj = zdaj or int(time.time())
    danes = datetime.fromtimestamp(zdaj, TZ).date().isoformat()
    zap = zapore(conn, date.fromisoformat(dan))
    izg = izgube_danes(conn, dan, zdaj) if dan == danes else []
    if not zap and not izg:
        return []
    g = _graf(conn)
    vrstice = [r for r in conn.execute(
        "SELECT stop_seq, stop_id, COALESCE(dep_s, arr_s) AS t_s FROM sched "
        "WHERE trip_id = ? ORDER BY stop_seq", (trip_id,))
        if (od_seq is None or r["stop_seq"] >= od_seq)
        and (do_seq is None or r["stop_seq"] <= do_seq)]
    odseki = [(x, pot(g, x["stop_id"], y["stop_id"]), y["stop_seq"])
              for x, y in zip(vrstice, vrstice[1:])]
    if not odseki:
        return []
    polnoc = stats.polnoc(dan)
    najdene = []
    for z in zap:
        for i, (x, p, _) in enumerate(odseki):
            okno = (x["t_s"] is not None and {frozenset(e) for e in p} & z["robovi"]
                    and _v_oknu(z["okna"], polnoc + x["t_s"] + zamuda_s))
            if okno:
                # Od katerega postanka naprej velja: konec odseka, na katerem je zapora.
                najdene.append((i, {"vrsta": "zapora", "alert_id": z["alert_id"],
                                    "odsek": z["odsek"], "od_seq": odseki[i][2],
                                    "do_ure": f"{okno[2] // 60}.{okno[2] % 60:02d}",
                                    "tveganje": tveganje(conn, z, date.fromisoformat(dan))}))
                break
    # Po vrsti, kot jih vlak sreča.
    out = [o for _, o in sorted(najdene, key=lambda x: x[0])]
    # Vlak pred njim šteje, če je izgubil čas na odseku, ki ga bo ta vlak
    # prevozil CELEGA, in v uri pred tem, ko bo tam. Samo stik ni dovolj:
    # EN 415 je med Ljubljano in Zidanim Mostom (brez postanka) izgubil
    # 43 min -- verjetno na zapori pri Savi, ne med Ljubljano in Litijo, kjer
    # bi ga sicer pripisali LPV 2261.
    na_poti = {ed: (x, seq) for x, e, seq in odseki for ed in e}
    pred = []
    for p in izg:
        if p[1] == trip_id or not p[10] or not all(ed in na_poti for ed in p[10]):
            continue
        x0 = na_poti[p[10][0]][0]
        if x0["t_s"] is not None and polnoc + x0["t_s"] + zamuda_s - PRED_TABO_OKNO_S <= p[8]:
            pred.append((p, na_poti[p[10][-1]][1]))
    if pred:
        p, kje = max(pred, key=lambda x: x[0][8])
        out.append({"vrsta": "pred_tabo", "vlak": p[2], "odsek": f"{p[3]} – {p[4]}",
                    "od_seq": kje, "izguba_s": p[9],
                    "ob": datetime.fromtimestamp(p[8], TZ).isoformat()})
    return out


def dodatek(opozorila: list[dict], seq: int) -> int:
    """Koliko nad našo oceno je lahko zamuda na postanku `seq` -- zgornja meja.

    Ocena sama ostane: premik navzgor je na senci dražji za potnika (zapora:
    strošek 10,12 min pri +0, 10,46 pri +1, 11,54 pri +2; vlak pred njim
    13,23 / 14,38 / 15,65), ker večina vlakov tam ne izgubi nič. Meja pa pove, do kod je treba računati: vsota zapor
    na poti (`ZGORNJA_MEJA_DELEZ` njihovih izgub), ali izguba vlaka pred njim,
    kar je več.
    """
    zap = sum(o["tveganje"]["p90_s"] for o in opozorila
              if o["vrsta"] == "zapora" and o["tveganje"] and o["od_seq"] <= seq)
    pred = max((o["izguba_s"] for o in opozorila
                if o["vrsta"] == "pred_tabo" and o["od_seq"] <= seq), default=0)
    return max(zap, pred)


def dopolni(conn: sqlite3.Connection, rows: list[dict], dan: str, do: str,
            kje: str, zdaj: datetime | None = None) -> None:
    """`opozorila` k vrsticam table ali iskalnika (od vlaka do postanka `do`)
    in `do_s`, zgornja meja zamude na postanku `kje` (`dodatek`).

    Samo železnica in samo danes ali naprej. Za vlak, ki je postajo že
    prevozil, nič.
    """
    zdaj = zdaj or datetime.now(TZ)
    ts = int(zdaj.timestamp())
    danes = zdaj.date().isoformat()
    vlaki = [r for r in rows if r.get("trip_id") and r.get("network") == "zeleznica"
             and r.get("service_date", dan) >= danes]
    if not vlaki:
        return
    po_dnevih: dict[str, list[dict]] = {}
    for r in vlaki:
        po_dnevih.setdefault(r.get("service_date", dan), []).append(r)
    for d, vrste in po_dnevih.items():
        meje = (stats.last_measured(conn, d, [r["trip_id"] for r in vrste], ts - stats.polnoc(d))
                if d == danes else {})
        for r in vrste:
            lm = meje.get(r["trip_id"])
            if lm and lm["stop_seq"] >= r[do]:
                continue
            o = za_voznjo(conn, r["trip_id"], d, lm["stop_seq"] if lm else None, r[do],
                          (lm["delay_s"] or 0) if lm else 0, ts)
            if not o:
                continue
            r["opozorila"] = o
            # Osnova je številka, ki jo vrstica pokaže: ocena ali "običajno".
            osnova = r.get("delay_s")
            if osnova is None:
                osnova = (r.get("typical") or r.get("typical_dep") or {}).get("median_s")
            dod = dodatek(o, r[kje])
            if osnova is not None and dod >= 60:
                r["do_s"] = round(osnova) + dod
