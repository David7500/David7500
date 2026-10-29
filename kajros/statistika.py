"""Statistika za strani `/statistika`: dnevni agregati in nočna okna.

**Zakaj dnevni agregati (`stat_dan`).** Senca (`napoved`) živi 30 dni
(`config.OCENA_KEEP_DAYS`), lege 14. Kar se izračuna iz njih, mora v bazo še
isti teden, sicer trenda čez mesec ni. `run` se sicer ne obreže, načrtovane
vožnje preteklega dne pa ob uvozu novega voznega reda izginejo (mestni LPP ima
za vsak dan svoje vožnje) -- zato gre v `stat_dan` tudi pokritost, isti večer.

**Vse je seštevljivo**: število, vsota napak, histogram po zaokroženi minuti.
Okno katere koli širine je vsota dni, brez ponovnega branja surovih vrstic, in
kvantil iz histograma ima ISTO definicijo kot `stats._pct`
(`pristanek._kvantil`).

**Dan je sklenjen šele dva dni pozneje**: avtobusi včerajšnjega prometnega dne
vozijo do 09:48 (`stats.se_vozi_vceraj`), resnica sence se dopiše do 36 h po
pogledu (`ocena.ZASTARA_S`). Zadnji dnevi se zato vsako noč prepišejo
(`PREPISI_DNI`), starejši manjkajoči se dopolnijo, kolikor vir še sega.

Okna (`napovedi`, `prevozniki`) gredo v `povzetek` prek
`stats.SUMMARY_BUILDERS`, ponoči v `server._povzetki`; strani jih samo berejo.
"""
from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, ocena, pristanek, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Toliko zadnjih dni se ob vsakem nočnem izračunu prepiše (glej zgoraj).
PREPISI_DNI = 3

#: Dan, izračunan pred manj kot toliko, se ne računa znova: okna kliče
#: `refresh_summaries` štirikrat zapored (dve vrsti × dve omrežji).
SVEZE_S = 6 * 3600

#: Okno številk na straneh. Mesec da večini linij vsaj nekaj deset voženj in je
#: dovolj kratek, da pove, kako je zdaj, ne kako je bilo poleti.
OKNO_DNI = 30

#: Pod tem vzorcem stran številke ne pokaže kot ugotovitve -- isti prag kot
#: `MIN_VZOREC` stare strani statistike (`strani.md`).
MIN_VZOREC = 30

#: Na lestvico pride vožnja ali linija z vsaj toliko dnevi v oknu. Pri desetih
#: je delež v 5 min še grob, a red velikosti drži (`stats.MIN_RUNS_FOR_GROUP`).
MIN_DNI_LESTVICA = 10
LESTVICA_N = 5

#: Meje histograma zamude v minutah; kar je zunaj, gre v robni razred. Strop
#: `stats.MAX_REALNA_ZAMUDA_S` (3 h) je zgoraj že pri branju.
HIST_OD, HIST_DO = -30, 180

_MODELI_VSE = ("nasa", "prenos", "vozni_red")
_MODELI_PARNO = ("nasa", "prevoznik", "prenos", "vozni_red")
_POLJA = ("n", "abs", "napaka", "v1", "v2", "v3", "v5", "prec", "podc", "strosek")


# ---------------------------------------------------------------- vsote napovedi

def _vsote() -> dict[str, int]:
    return dict.fromkeys(_POLJA, 0)


def _pristej(v: dict, napoved: int, resnica: int, razmik_s: int) -> None:
    """Ena napoved v vsote, z ISTIMI definicijami kot `ocena._meritve`.

    Precenitev in podcenitev pri istem pragu (potnikova rezerva), strošek po
    `ocena._strosek`: precenitev nad rezervo stane cel razmik do naslednjega.
    """
    e = napoved - resnica
    a = abs(e)
    r = ocena.POTNIKOVA_REZERVA_S
    v["n"] += 1
    v["abs"] += a
    v["napaka"] += e
    v["v1"] += a <= 60
    v["v2"] += a <= 120
    v["v3"] += a <= 180
    v["v5"] += a <= 300
    v["prec"] += napoved > resnica + r
    v["podc"] += napoved < resnica - r
    prihod = napoved - r
    v["strosek"] += (resnica - prihod) if prihod <= resnica else razmik_s


def _sestej(cilj: dict, vir: dict) -> None:
    for k in _POLJA:
        cilj[k] += vir.get(k, 0)


def meritve(v: dict) -> dict:
    """Vsote v številke strani. Imena in zaokrožitve kot `ocena._meritve`."""
    n = v.get("n", 0)
    if not n:
        return {"n": 0}

    def delez(k: str) -> float:
        return round(v[k] / n * 100, 1)

    return {
        "n": n,
        "mae_min": round(v["abs"] / n / 60, 2),
        "v1min": delez("v1"), "v2min": delez("v2"),
        "v3min": delez("v3"), "v5min": delez("v5"),
        "odklon_min": round(v["napaka"] / n / 60, 2),
        "precenjenih": delez("prec"), "podcenjenih": delez("podc"),
        "strosek_min": round(v["strosek"] / n / 60, 2),
    }


def _prazna_napoved() -> dict:
    return {"vse": {m: _vsote() for m in _MODELI_VSE},
            "parno": {m: _vsote() for m in _MODELI_PARNO}}


def _dnevi_napovedi(conn: sqlite3.Connection, dnevi: list[str]) -> dict[str, dict]:
    """`{dan: {kljuc: vsote}}` iz sence, ključ `omrežje|prevoznik|skupina`.

    Skupina `na_poti` (vozilo ob pogledu že izmerjeno) in `pred_odhodom` (še
    ni nobene meritve) se ne mešata: prva meri model, druga „običajno“, in
    mešanica bi merila razmerje med vrstama pogledov (`ocena.report`).

    Dve primerjavi, obe parni: `vse` na vrsticah, kjer ima prikaz vrednost,
    `parno` le tam, kjer je imel vrednost tudi prevoznik -- prevoznika na
    njegovih vrsticah in nas na vseh bi merilo tudi razliko med vzorcema
    (MERITVE 2. 9. 2026: tako je prevoznik „zmagal“ 3,39 proti 3,63).
    Prenos brez trenutne zamude (pred odhodom) je ničla: tako aplikacija, ki
    nese trenutno zamudo naprej, pokaže vožnjo brez meritve -- po voznem redu.

    Ena poizvedba za vse dni: `napoved` nima kazala po dnevu.
    """
    if not dnevi:
        return {}
    ocena.init(conn)   # tabela sence nastane ob zagonu zajema; `kajros summarize` ga nima
    vprasaji = ",".join("?" * len(dnevi))
    out: dict[str, dict] = defaultdict(dict)
    for dan, net, agency, na_poti, ours, prev, prenos, res in conn.execute(f"""
            SELECT n.service_date, n.network, t.agency, n.from_seq IS NOT NULL,
                   n.ours_s, n.operator_s, n.carry_s, n.actual_s
            FROM napoved n JOIN trip t ON t.trip_id = n.trip_id
            WHERE n.service_date IN ({vprasaji})
              AND n.actual_s IS NOT NULL AND n.ours_s IS NOT NULL
              AND ABS(n.actual_s) <= {stats.MAX_REALNA_ZAMUDA_S}""", dnevi):
        razmik = ocena.RAZMIK_S.get(net)
        if razmik is None:
            continue
        kljuc = f"{net}|{agency}|{'na_poti' if na_poti else 'pred_odhodom'}"
        g = out[dan].setdefault(kljuc, _prazna_napoved())
        prenos = prenos or 0
        for model, vrednost in (("nasa", ours), ("prenos", prenos), ("vozni_red", 0)):
            _pristej(g["vse"][model], vrednost, res, razmik)
        if prev is not None:
            for model, vrednost in (("nasa", ours), ("prevoznik", prev),
                                    ("prenos", prenos), ("vozni_red", 0)):
                _pristej(g["parno"][model], vrednost, res, razmik)
    return out


# ---------------------------------------------------------------- prevozniki po dnevu

def _skupina(network: str, mode: str | None) -> str:
    """Nadomestni prevoz SŽ je svoja skupina: zanj feed zamud ne poroča nikoli
    (0 od 777 voženj, 11.–28. 10. 2026) in bi vlakom znižal pokritost."""
    if network == "zeleznica":
        return "nadomestni" if mode == "bus" else "vlak"
    return "avtobus"


def _ura_postanka(t_s: int | None) -> int | None:
    # Voznoredne sekunde so od poldneva minus 12 h: ura dneva je celi del.
    return None if t_s is None else (t_s // 3600) % 24


def _dan_prevozniki(conn: sqlite3.Connection, dan: str) -> dict[str, dict]:
    """Pokritost in končna zamuda po prevozniku za en prometni dan.

    Končna zamuda = zadnji opaženi postanek vožnje (kot `stats.LAST_STOP_SQL`,
    `breakdowns`, pristajalne), da je številka na vseh straneh ista. Histogram
    po zaokroženi minuti (`stats._minute`): razred in „v 5 min“ se iz njega
    določita z istim pravilom kot na zaslonu (`oznake.md`).
    """
    out: dict[str, dict] = {}

    def g(net: str, agency: str, mode: str | None) -> dict:
        return out.setdefault(f"{net}|{agency}|{_skupina(net, mode)}", {
            "nacrt": 0, "z_meritvijo": 0, "z_lego": 0, "s_ciljem": 0,
            "hist": Counter(), "ure": defaultdict(lambda: [0, 0]),
            "vmesnih": 0, "prej1": 0, "prej2": 0, "prej3": 0})

    ima_lege = conn.execute(
        "SELECT 1 FROM lega WHERE service_date = ? LIMIT 1", (dan,)).fetchone() is not None
    for net in stats.SUMMARY_NETWORKS:
        # Omrežje v poizvedbi, ne za njo (CLAUDE.md: 1,7 s proti 6 ms).
        for agency, mode, k in conn.execute(
                "SELECT t.agency, t.mode, COUNT(*) FROM trip t "
                "JOIN service_day d ON d.service_id = t.service_id "
                "WHERE d.date = ? AND t.network = ? GROUP BY 1, 2", (dan, net)):
            g(net, agency, mode)["nacrt"] += k
        for agency, mode, k in conn.execute(
                "SELECT t.agency, t.mode, COUNT(DISTINCT r.trip_id) FROM run r "
                "JOIN trip t ON t.trip_id = r.trip_id "
                "WHERE r.service_date = ? AND t.network = ? GROUP BY 1, 2", (dan, net)):
            g(net, agency, mode)["z_meritvijo"] += k
        if ima_lege:
            for agency, mode, k in conn.execute(
                    "SELECT t.agency, t.mode, COUNT(DISTINCT l.trip_id) FROM lega l "
                    "JOIN trip t ON t.trip_id = l.trip_id "
                    "WHERE l.service_date = ? AND t.network = ? GROUP BY 1, 2", (dan, net)):
                g(net, agency, mode)["z_lego"] += k
        for agency, mode, d, t_s in conn.execute(f"""
                WITH mx AS (
                    SELECT r.trip_id, MAX(r.stop_seq) AS stop_seq
                    FROM run r JOIN trip t ON t.trip_id = r.trip_id
                    WHERE r.service_date = :dan AND t.network = :net
                    GROUP BY r.trip_id)
                SELECT t.agency, t.mode, COALESCE(r.delay_dep, r.delay_arr),
                       COALESCE(s.arr_s, s.dep_s)
                FROM mx JOIN run r ON r.trip_id = mx.trip_id AND r.service_date = :dan
                                  AND r.stop_seq = mx.stop_seq
                JOIN trip t ON t.trip_id = mx.trip_id
                LEFT JOIN sched s ON s.trip_id = mx.trip_id AND s.stop_seq = mx.stop_seq
                WHERE COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
                  AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {stats.MAX_REALNA_ZAMUDA_S}""",
                {"dan": dan, "net": net}):
            v = g(net, agency, mode)
            m = min(max(stats._minute(d), HIST_OD), HIST_DO)
            v["s_ciljem"] += 1
            v["hist"][m] += 1
            ura = _ura_postanka(t_s)
            if ura is not None:
                v["ure"][ura][0] += 1
                v["ure"][ura][1] += stats._je_pravocasna(d)
        # Prezgodnji odhod z vmesnega postanka, po ISTI zaokroženi minuti kot
        # zaslon: „1 min prej“ je d <= -31 s, „2 min prej“ d <= -91 s.
        for agency, mode, n, p1, p2, p3 in conn.execute(f"""
                SELECT t.agency, t.mode, COUNT(*),
                       SUM(COALESCE(r.delay_dep, r.delay_arr) <= -31),
                       SUM(COALESCE(r.delay_dep, r.delay_arr) <= -91),
                       SUM(COALESCE(r.delay_dep, r.delay_arr) <= -151)
                FROM run r JOIN trip t ON t.trip_id = r.trip_id
                WHERE r.service_date = ? AND t.network = ?
                  AND r.stop_seq > t.first_seq AND r.stop_seq < t.last_seq
                  AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
                  AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {stats.MAX_REALNA_ZAMUDA_S}
                GROUP BY 1, 2""", (dan, net)):
            v = g(net, agency, mode)
            v["vmesnih"] += n
            v["prej1"] += p1 or 0
            v["prej2"] += p2 or 0
            v["prej3"] += p3 or 0

    for v in out.values():
        # Načrt preteklega dne je lahko že izbrisan (mestni LPP ima vožnje po
        # datumu, uvoz pobriše stare): več izmerjenih kot načrtovanih pomeni,
        # da načrta za ta dan ne poznamo, ne 140-odstotne pokritosti.
        if v["z_meritvijo"] > v["nacrt"]:
            v["nacrt"] = None
        # Ostane v `stat_dan`, na strani ne: `lega` hrani samo lege z NAP, mestni
        # LPP in Marprom bi imela „0 %“, čeprav ju na zemljevidu vidiš.
        if not ima_lege:
            v["z_lego"] = None
        v["hist"] = {str(m): c for m, c in sorted(v["hist"].items())}
        v["ure"] = {str(h): c for h, c in sorted(v["ure"].items())}
    return out


# ---------------------------------------------------------------- dopolnjevanje

def _vir_od(conn: sqlite3.Connection) -> str | None:
    """Prvi dan, ki ga vir še ima. `run` sega najdlje."""
    return conn.execute("SELECT MIN(service_date) FROM run").fetchone()[0]


def dopolni(conn: sqlite3.Connection, danes: date | None = None,
            prepisi: int = PREPISI_DNI) -> list[str]:
    """Izračunaj manjkajoče dni in prepiši zadnje. Vrne izračunane dneve.

    Dnevi iz prihodnosti in današnji se ne računajo: dan še teče.
    """
    danes = danes or datetime.now(TZ).date()
    vceraj = danes - timedelta(days=1)
    od = _vir_od(conn)
    if od is None:
        return []
    zdaj = int(time.time())
    obstojece = {d: ob for d, ob in conn.execute(
        "SELECT dan, MIN(izracunano) FROM stat_dan GROUP BY dan")}
    dnevi = []
    d = date.fromisoformat(od)
    while d <= vceraj:
        dan = d.isoformat()
        nedavno = (vceraj - d).days < prepisi
        if dan not in obstojece or (nedavno and zdaj - obstojece[dan] > SVEZE_S):
            dnevi.append(dan)
        d += timedelta(days=1)
    if not dnevi:
        return []
    napovedi = _dnevi_napovedi(conn, dnevi)
    for dan in dnevi:
        vrstice = [(dan, "napoved", k, json.dumps(v, separators=(",", ":")), zdaj)
                   for k, v in napovedi.get(dan, {}).items()]
        vrstice += [(dan, "prevoznik", k, json.dumps(v, separators=(",", ":")), zdaj)
                    for k, v in _dan_prevozniki(conn, dan).items()]
        # Prazen dan dobi vrstico, sicer bi se vsako noč računal znova.
        if not vrstice:
            vrstice = [(dan, "prazno", "", "{}", zdaj)]
        conn.execute("DELETE FROM stat_dan WHERE dan = ?", (dan,))
        conn.executemany(
            "INSERT INTO stat_dan (dan, vrsta, kljuc, podatki, izracunano) "
            "VALUES (?, ?, ?, ?, ?)", vrstice)
        conn.commit()
    return dnevi


def _beri(conn: sqlite3.Connection, vrsta: str, od: str, do: str,
          network: str) -> list[tuple[str, str, dict]]:
    return [(dan, kljuc, json.loads(p)) for dan, kljuc, p in conn.execute(
        "SELECT dan, kljuc, podatki FROM stat_dan "
        "WHERE vrsta = ? AND dan BETWEEN ? AND ? AND kljuc LIKE ? ORDER BY dan",
        (vrsta, od, do, network + "|%"))]


def _okno(danes: date | None = None, dni: int = OKNO_DNI) -> tuple[str, str]:
    """Zadnjih `dni` sklenjenih dni, do včeraj."""
    danes = danes or datetime.now(TZ).date()
    do = danes - timedelta(days=1)
    return (do - timedelta(days=dni - 1)).isoformat(), do.isoformat()


# ---------------------------------------------------------------- okno: napovedi

def napovedi(conn: sqlite3.Connection, days: int, network: str,
             danes: date | None = None) -> dict:
    """Stran napovedi: naša proti prevozniku, prenosu in voznemu redu.

    Zadnjih `OKNO_DNI` po prevozniku in skupaj, in po tednih čez vse, kar je
    v `stat_dan` -- tam senca živi dlje od svojih 30 dni.
    """
    dopolni(conn, danes)
    od, do = _okno(danes)
    vrstice = _beri(conn, "napoved", "0000-00-00", do, network)

    def zdruzi(izbor) -> dict:
        g = _prazna_napoved()
        for _, _, v in izbor:
            for blok, modeli in g.items():
                for model, vsote in modeli.items():
                    _sestej(vsote, v.get(blok, {}).get(model, {}))
        return {blok: {m: meritve(s) for m, s in modeli.items()} for blok, modeli in g.items()}

    v_oknu = [r for r in vrstice if r[0] >= od]
    skupine = ("na_poti", "pred_odhodom")
    skupaj = {s: zdruzi(r for r in v_oknu if r[1].endswith("|" + s)) for s in skupine}
    prevozniki = sorted({r[1].split("|")[1] for r in v_oknu})
    po_prevozniku = {
        a: {s: zdruzi(r for r in v_oknu if r[1] == f"{network}|{a}|{s}") for s in skupine}
        for a in prevozniki}

    tedni: dict[str, list] = defaultdict(list)
    for r in vrstice:
        if r[1].endswith("|na_poti"):
            leto, teden, _ = date.fromisoformat(r[0]).isocalendar()
            tedni[f"{leto}-T{teden:02d}"].append(r)
    po_tednih = [{"teden": t, "od": min(r[0] for r in rs), "do": max(r[0] for r in rs),
                  **zdruzi(rs)["vse"]} for t, rs in sorted(tedni.items())]

    dnevi = sorted({r[0] for r in v_oknu})
    return {
        "okno_dni": OKNO_DNI, "od": od, "do": do, "days": dnevi,
        "runs": sum(skupaj[s]["vse"]["nasa"]["n"] for s in skupine),
        "skupaj": skupaj,
        "po_prevozniku": po_prevozniku,
        "imena": {a: stats.AGENCY_NAMES.get(a, a) for a in prevozniki},
        "po_tednih": po_tednih,
        "horizont_min": ocena.HORIZONT_S[network] // 60,
        "min_vzorec": MIN_VZOREC,
    }


# ---------------------------------------------------------------- okno: prevozniki

def iz_histograma(hist: dict) -> dict:
    """Mediana, p90, delež v 5 min in razredi iz histograma minut.

    Razredi po `stats._razred_zamude` (ista zaokrožena minuta kot zaslon), da
    se vsota razredov ujema z deležem točnih (`preveri_skladnost.py`).
    """
    h = {int(m): c for m, c in hist.items() if c}
    n = sum(h.values())
    if not n:
        return {"n": 0}
    minute = sorted(h)
    razredi = Counter()
    for m, c in h.items():
        razredi[stats._KLJUC_RAZREDA[stats._razred_zamude(m * 60)]] += c
    v5 = sum(c for m, c in h.items() if m <= stats.ON_TIME_MIN)
    nad15 = razredi["nad-15"]
    return {
        "n": n,
        "mediana_min": pristanek._kvantil(minute, h, n, 0.5),
        "p90_min": pristanek._kvantil(minute, h, n, 0.9),
        "v5min": round(v5 / n * 100, 1),
        "nad15": round(nad15 / n * 100, 1),
        "razredi": {k: round(razredi[k] / n * 100, 1)
                    for k in ("tocno", "1-5", "5-15", "nad-15")},
    }


def _lestvica(conn: sqlite3.Connection, network: str, od: str, do: str) -> dict:
    """Najbolj in najmanj točne vožnje ali linije po prevozniku, v oknu.

    Ključ je `train_no`: pri vlaku in medkrajevnem avtobusu ena vožnja čez
    dneve (LPV 2010, A6346), pri mestnem prometu linija (LPP 6). Enota je
    vožnja-dan, kot povsod v statistiki (`breakdowns`): sicer bi vožnja s
    tridesetimi postanki glasovala tridesetkrat.
    """
    po: dict[tuple, list] = defaultdict(list)
    smer: dict[tuple, Counter] = defaultdict(Counter)
    for agency, no, cilj, start, d in conn.execute(f"""
            WITH mx AS (
                SELECT r.trip_id, r.service_date, MAX(r.stop_seq) AS stop_seq
                FROM run r JOIN trip t ON t.trip_id = r.trip_id
                WHERE r.service_date BETWEEN :od AND :do AND t.network = :net
                GROUP BY r.trip_id, r.service_date)
            SELECT t.agency, t.train_no, t.headsign, t.start_s,
                   COALESCE(r.delay_dep, r.delay_arr)
            FROM mx JOIN run r ON r.trip_id = mx.trip_id
                              AND r.service_date = mx.service_date
                              AND r.stop_seq = mx.stop_seq
            JOIN trip t ON t.trip_id = mx.trip_id
            WHERE (t.mode != 'bus' OR t.network = 'avtobus')
              AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
              AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {stats.MAX_REALNA_ZAMUDA_S}""",
            {"od": od, "do": do, "net": network}):
        if d is None or abs(d) > stats.MAX_REALNA_ZAMUDA_S or not no:
            continue
        k = (agency, no)
        po[k].append(d)
        smer[k][(cilj or "", start)] += 1

    po_prevozniku: dict[str, list] = defaultdict(list)
    for (agency, no), vals in po.items():
        if len(vals) < MIN_DNI_LESTVICA:
            continue
        (cilj, start), _ = smer[(agency, no)].most_common(1)[0]
        po_prevozniku[agency].append({
            "st": no, "cilj": cilj, "start_s": start, "n": len(vals),
            "v5min": round(sum(stats._je_pravocasna(v) for v in vals) / len(vals) * 100, 1),
            "mediana_min": stats._pct([stats._minute(v) for v in vals], 0.5),
        })
    out = {}
    for agency, vrste in po_prevozniku.items():
        # Enak delež loči mediana, nato vzorec: pri istem deležu je zanesljivejša
        # številka tista z več dnevi.
        vrste.sort(key=lambda x: (-x["v5min"], x["mediana_min"], -x["n"]))
        out[agency] = {"najboljse": vrste[:LESTVICA_N],
                       "najslabse": list(reversed(vrste[-LESTVICA_N:])),
                       "vseh": len(vrste)}
    return out


def prevozniki(conn: sqlite3.Connection, days: int, network: str,
               danes: date | None = None) -> dict:
    """Stran prevoznikov: točnost, pokritost, prezgodnji odhodi, napoved.

    Številke za zadnjih `OKNO_DNI`, potek po dnevih za `days` (90).
    """
    dopolni(conn, danes)
    od, do = _okno(danes)
    od_dolgo, _ = _okno(danes, days)
    vrstice = _beri(conn, "prevoznik", od_dolgo, do, network)
    napoved = _beri(conn, "napoved", od, do, network)

    kljuci = sorted({k for _, k, _ in vrstice})
    out = []
    for kljuc in kljuci:
        _, agency, skupina = kljuc.split("|")
        dnevi = [(dan, v) for dan, k, v in vrstice if k == kljuc]
        v_oknu = [v for dan, v in dnevi if dan >= od]
        if not v_oknu:
            continue
        hist: Counter = Counter()
        ure: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for v in v_oknu:
            hist.update({int(m): c for m, c in v["hist"].items()})
            for h, (n, ok) in v["ure"].items():
                ure[h][0] += n
                ure[h][1] += ok
        # Pokritost od prvega dne z meritvijo: vozni red Marproma (zajem od
        # 27. 10. 2026) sega v začetek meseca, in dnevi pred zajemom niso
        # vožnje brez podatka, ampak dnevi, ko vira še nismo brali.
        # Nikoli izmerjen (nadomestni prevoz SŽ: feed zanj ne poroča) pa je 0 %
        # čez vse dni, ne „neznano“.
        prvi = next((i for i, v in enumerate(v_oknu) if v["z_meritvijo"]), 0)
        znan = [v for v in v_oknu[prvi:] if v["nacrt"] is not None]
        nacrt = [v["nacrt"] for v in znan]
        z_meritvijo_kjer_nacrt = [v["z_meritvijo"] for v in znan]
        vmesnih = sum(v["vmesnih"] for v in v_oknu)
        nap = _prazna_napoved()
        for _, k, v in napoved:
            if k == f"{network}|{agency}|na_poti" and skupina != "nadomestni":
                for blok, modeli in nap.items():
                    for model, vsote in modeli.items():
                        _sestej(vsote, v.get(blok, {}).get(model, {}))
        out.append({
            "kljuc": kljuc, "agency": agency, "skupina": skupina,
            "ime": stats.AGENCY_NAMES.get(agency, agency),
            "dni": len(v_oknu),
            "voznje": sum(v["z_meritvijo"] for v in v_oknu),
            # Pokritost samo na dneh, ko je načrt znan -- sicer bi delila
            # vožnje vseh dni z načrtom nekaterih.
            "pokritost": (round(sum(z_meritvijo_kjer_nacrt) / sum(nacrt) * 100, 1)
                          if sum(nacrt) else None),
            "nacrt": sum(nacrt) if nacrt else None,
            "zajem_od": next((dan for dan, v in dnevi if v["z_meritvijo"]), None),
            "cilj": iz_histograma(hist),
            "po_urah": {h: {"n": n, "v5min": round(ok / n * 100, 1)}
                        for h, (n, ok) in sorted(ure.items(), key=lambda x: int(x[0])) if n},
            "prezgodaj": {"vmesnih": vmesnih, **{
                k: (round(sum(v[k] for v in v_oknu) / vmesnih * 100, 1) if vmesnih else None)
                for k in ("prej1", "prej2", "prej3")}},
            "po_dnevih": [{"dan": dan, **{k: x for k, x in iz_histograma(v["hist"]).items()
                                         if k in ("n", "v5min", "mediana_min")}}
                          for dan, v in dnevi],
            "napoved": {"vse": {m: meritve(s) for m, s in nap["vse"].items()},
                        "parno": {m: meritve(s) for m, s in nap["parno"].items()}},
        })
    lestvica = _lestvica(conn, network, od, do)
    for p in out:
        if p["skupina"] != "nadomestni":
            p["lestvica"] = lestvica.get(p["agency"])
    return {
        "okno_dni": OKNO_DNI, "od": od, "do": do,
        "days": sorted({dan for dan, _, _ in vrstice if dan >= od}),
        "runs": sum(p["cilj"]["n"] for p in out),
        "prevozniki": out,
        "min_vzorec": MIN_VZOREC,
        "min_dni_lestvica": MIN_DNI_LESTVICA,
    }
