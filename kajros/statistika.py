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
import math
import sqlite3
import threading
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, db, journey, ocena, pristanek, stats

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

#: Prevozniki, pri katerih je `train_no` linija (mestni promet in LPP
#: primestni), ne ena vožnja: na lestvici je enota linija.
LINIJSKI = frozenset({"lpp", "1118", "marprom", "kranj"})

#: Prevoznikova napoved se pokaže le, kadar jo je objavil vsaj pri tolikšnem
#: deležu pogledov. SŽ jo ima pri 0,5 % (429 od 87 055): to ni napoved, ki bi
#: jo potnik videl, in primerjava na tem izrezu bi bila anekdota.
MIN_DELEZ_PREVOZNIKA = 0.2

#: Od tega dne vodi naš bralec zemljevida SŽ (`zamude_sz`); prej so zamude
#: vlakov prihajale prek posrednikov z zamikom in serija popravkov v `obs`
#: ni opis zemljevida SŽ.
SZ_VODI_OD = "2026-10-11"

#: Različica dnevnih agregatov. Ob novi vrsti ali spremembi pomena jo povečaj:
#: `dopolni` takrat izračuna vse dni znova, kolikor viri še segajo.
STAT_DAN_VERZIJA = 2

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


# ---------------------------------------------------------------- SŽ po dnevu

def _dan_sz(conn: sqlite3.Connection, dan: str) -> dict | None:
    """Kako zemljevid SŽ pokaže odhod in kako ga pozneje popravi, en dan.

    Vrstica zemljevida SŽ nosi naslednjo postajo in odhodno zamudo zadnje
    prevožene (`zamude_sz`). Prvi zapis postanka v `obs` je trenutek, ko je
    zemljevid vlak premaknil čez postajo; če se njegova zamuda nato dvigne,
    je SŽ odhod pozneje popravil -- vmes je vlak kazal na poti, ko je stal
    (MERITVE 29. 10. 2026: mediana popravek/trajanje 0,88 -- minuto na minuto).
    Resnica, kjer je: prehod potnika (`deljenje_prehod`, GPS telefona).
    """
    if dan < SZ_VODI_OD:
        return None
    vrste = conn.execute("""
        SELECT o.trip_id, o.stop_seq, o.observed_at, COALESCE(o.delay_dep, o.delay_arr),
               t.first_seq, t.last_seq, t.train_no
        FROM obs o JOIN trip t ON t.trip_id = o.trip_id
        WHERE o.service_date = ? AND t.network = 'zeleznica' AND t.mode != 'bus'
          AND COALESCE(o.delay_dep, o.delay_arr) IS NOT NULL
        ORDER BY o.trip_id, o.stop_seq, o.observed_at""", (dan,)).fetchall()
    if not vrste:
        return None
    serije: dict[tuple, list] = defaultdict(list)
    meja: dict[str, tuple] = {}
    for trip, seq, ts, d, prvi, zadnji, no in vrste:
        serije[(trip, seq)].append((ts, d))
        meja[trip] = (prvi, zadnji, no)
    v = {"postankov": 0, "dvig1": 0, "dvig2": 0, "dvig5": 0, "dvig10": 0, "dvig_hist": Counter(),
         "izhodisc": 0, "izhodisce_lazno": 0, "potniki": []}
    for (trip, seq), sr in serije.items():
        prvi, zadnji, _ = meja[trip]
        if seq == zadnji:
            continue    # cilj: SŽ zamudo ob prihodu ponastavi, prva šteje (`zamude_sz`)
        dvig = sr[-1][1] - sr[0][1]
        v["postankov"] += 1
        for prag, k in ((60, "dvig1"), (120, "dvig2"), (300, "dvig5"), (600, "dvig10")):
            v[k] += dvig >= prag
        if dvig >= 60:
            v["dvig_hist"][min(stats._minute(dvig), HIST_DO)] += 1
        if seq == prvi:
            v["izhodisc"] += 1
            v["izhodisce_lazno"] += sr[0][1] <= 30 and sr[-1][1] >= 120
    # Tabelo deljenja ustvari `deljenje.init` ob zagonu strežnika; `kajros
    # summarize` na golem stroju je nima.
    ima_deljenje = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                                "AND name = 'deljenje_prehod'").fetchone()
    for trip, seq, odhod, dep_s, ime in [] if not ima_deljenje else conn.execute("""
            SELECT d.trip_id, d.stop_seq, d.odhod_ts, s.dep_s, st.name
            FROM deljenje_prehod d JOIN trip t ON t.trip_id = d.trip_id
            JOIN sched s ON s.trip_id = d.trip_id AND s.stop_seq = d.stop_seq
            JOIN station st ON st.stop_id = s.stop_id
            WHERE d.service_date = ? AND t.network = 'zeleznica' AND t.mode != 'bus'
              AND d.odhod_ts IS NOT NULL AND s.dep_s IS NOT NULL""", (dan,)):
        sr = serije.get((trip, seq))
        if not sr:
            continue
        v["potniki"].append({"st": meja[trip][2], "postaja": ime, "dan": dan,
                             # > 0: zemljevid je vlak pokazal na poti, preden je odpeljal
                             "prej_s": odhod - sr[0][0],
                             "zamuda_s": odhod - (stats.polnoc(dan) + dep_s)})
    v["dvig_hist"] = {str(m): c for m, c in sorted(v["dvig_hist"].items())}
    return v


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
    # Nova različica (nova vrsta, spremenjen pomen) = vsi dnevi znova -- a
    # brez brisanja: vrsta, katere vir je že obrezan (senca po 30 dneh),
    # obdrži staro vrstico (`_zapisi_dan`).
    znova = db.get_meta(conn, "stat_dan_verzija") != str(STAT_DAN_VERZIJA)
    obstojece = {d: ob for d, ob in conn.execute(
        "SELECT dan, MIN(izracunano) FROM stat_dan GROUP BY dan")}
    dnevi = []
    d = date.fromisoformat(od)
    while d <= vceraj:
        dan = d.isoformat()
        nedavno = (vceraj - d).days < prepisi
        if znova or dan not in obstojece or (nedavno and zdaj - obstojece[dan] > SVEZE_S):
            dnevi.append(dan)
        d += timedelta(days=1)
    if not dnevi:
        return []
    napovedi = _dnevi_napovedi(conn, dnevi)
    for dan in dnevi:
        sz = _dan_sz(conn, dan)
        _zapisi_dan(conn, dan, zdaj, {
            "napoved": napovedi.get(dan, {}),
            "prevoznik": _dan_prevozniki(conn, dan),
            "sz": {"zeleznica|1161": sz} if sz is not None else {},
        })
    if znova:
        db.set_meta(conn, "stat_dan_verzija", str(STAT_DAN_VERZIJA))
        conn.commit()
    return dnevi


def _zapisi_dan(conn: sqlite3.Connection, dan: str, zdaj: int,
                po_vrsti: dict[str, dict]) -> None:
    """Zamenja vrste dneva, ki jih vir še ima; prazne pusti pri miru.

    Senca živi 30 dni: ponoven izračun starega dne vrne prazno `napoved`, in
    brisanje bi za vedno izgubilo, kar se je shranilo, dokler je vir bil.
    """
    for vrsta, vrstice in po_vrsti.items():
        if not vrstice:
            continue
        conn.execute("DELETE FROM stat_dan WHERE dan = ? AND vrsta = ?", (dan, vrsta))
        conn.executemany(
            "INSERT INTO stat_dan (dan, vrsta, kljuc, podatki, izracunano) "
            "VALUES (?, ?, ?, ?, ?)",
            [(dan, vrsta, k, json.dumps(v, separators=(",", ":")), zdaj)
             for k, v in vrstice.items()])
    # Dan brez vsega dobi oznako, sicer bi se vsako noč računal znova.
    conn.execute("INSERT OR REPLACE INTO stat_dan (dan, vrsta, kljuc, podatki, izracunano) "
                 "VALUES (?, 'oznaka', '', '{}', ?)", (dan, zdaj))
    conn.commit()


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


def pot_voznje(network: str, agency: str, st: str) -> str:
    """Naslov strani ene vožnje ali linije. Prevoznik je v poti pri avtobusih,
    ker ima ista številka linije pri dveh prevoznikih dva pomena (LPP 6)."""
    if network == "zeleznica":
        return f"/statistika/vlak/{pristanek.slug(st)}"
    return (f"/statistika/linija/{pristanek.slug(stats.AGENCY_NAMES.get(agency, agency))}"
            f"/{pristanek.slug(st)}")


def _koncne(conn: sqlite3.Connection, network: str, od: str, do: str) -> list[tuple]:
    """Končna zamuda vsake vožnje v oknu: (prevoznik, št., cilj, odhod, dan, d).

    Ena poizvedba za lestvico in strani voženj. Končna = zadnji opaženi
    postanek, kot povsod (`stats.LAST_STOP_SQL`). Nadomestni prevoz SŽ ni
    vlak; brez meritev itak ne bi prišel noter.
    """
    return [r for r in conn.execute(f"""
            WITH mx AS (
                SELECT r.trip_id, r.service_date, MAX(r.stop_seq) AS stop_seq
                FROM run r JOIN trip t ON t.trip_id = r.trip_id
                WHERE r.service_date BETWEEN :od AND :do AND t.network = :net
                GROUP BY r.trip_id, r.service_date)
            SELECT t.agency, t.train_no, t.headsign, t.start_s, mx.service_date,
                   COALESCE(r.delay_dep, r.delay_arr)
            FROM mx JOIN run r ON r.trip_id = mx.trip_id
                              AND r.service_date = mx.service_date
                              AND r.stop_seq = mx.stop_seq
            JOIN trip t ON t.trip_id = mx.trip_id
            WHERE (t.mode != 'bus' OR t.network = 'avtobus')
              AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
              AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {stats.MAX_REALNA_ZAMUDA_S}""",
            {"od": od, "do": do, "net": network}) if r[1]]


def _lestvica(koncne: list[tuple], network: str) -> dict:
    """Najbolj in najmanj točne vožnje ali linije po prevozniku, v oknu.

    Ključ je `train_no`: pri vlaku ena vožnja čez dneve (LPV 2010), pri
    mestnem prometu linija (LPP 6). Medkrajevna šifra (A6343) je lahko več
    odhodov na dan (84 v 30 dneh): tam je vožnja šele šifra + ura odhoda.
    Enota je vožnja-dan, kot povsod v statistiki (`breakdowns`): sicer bi
    vožnja s tridesetimi postanki glasovala tridesetkrat.
    """
    po: dict[tuple, list] = defaultdict(list)
    smer: dict[tuple, Counter] = defaultdict(Counter)
    for agency, no, cilj, start, _dan, d in koncne:
        k = (agency, no, None if agency in LINIJSKI else start)
        po[k].append(d)
        smer[k][(cilj or "", start)] += 1

    po_prevozniku: dict[str, list] = defaultdict(list)
    for k, vals in po.items():
        agency, no, _ = k
        if len(vals) < MIN_DNI_LESTVICA:
            continue
        (cilj, start), _ = smer[k].most_common(1)[0]
        po_prevozniku[agency].append({
            "st": no, "cilj": cilj, "start_s": start, "n": len(vals),
            "linija": agency in LINIJSKI, "pot": pot_voznje(network, agency, no),
            "v5min": round(sum(stats._je_pravocasna(v) for v in vals) / len(vals) * 100, 1),
            "mediana_min": stats._pct([stats._minute(v) for v in vals], 0.5),
        })
    out = {}
    for agency, vrste in po_prevozniku.items():
        # Pri istem deležu je točnejša tista, ki pride bliže voznemu redu
        # (ne prej: −5 min na cilju je rezerva voznega reda, ne točnost).
        vrste.sort(key=lambda x: (-x["v5min"], abs(x["mediana_min"]), -x["n"]))
        out[agency] = {"najboljse": vrste[:LESTVICA_N],
                       "najslabse": list(reversed(vrste[-LESTVICA_N:])),
                       "vseh": len(vrste)}
    return out


def _razrez(minute_po: dict) -> list[dict]:
    """`{ključ: [minute]}` -> vrstice z n, deležem v 5 min in mediano."""
    out = []
    for k, mins in minute_po.items():
        if mins:
            out.append({"k": k, "n": len(mins),
                        "v5min": round(sum(m <= stats.ON_TIME_MIN for m in mins) / len(mins) * 100, 1),
                        "mediana_min": stats._pct(mins, 0.5)})
    return out


def _voznje(koncne: list[tuple], network: str, od: str) -> dict[str, dict]:
    """Stran vsake vožnje ali linije, ki je v zadnjih `OKNO_DNI` vozila.

    Številke za 30 dni, potek po dnevih in dnevi v tednu za vse okno (90).
    """
    po: dict[tuple, list] = defaultdict(list)
    for agency, no, cilj, start, dan, d in koncne:
        po[(agency, no)].append((dan, stats._minute(d), start, cilj or ""))
    out = {}
    for (agency, no), vrste in po.items():
        v30 = [v for v in vrste if v[0] >= od]
        if len(v30) < 3:
            continue
        hist = Counter(min(max(m, HIST_OD), HIST_DO) for _, m, _, _ in v30)
        po_dnevih: dict[str, list] = defaultdict(list)
        po_tednu: dict[int, list] = defaultdict(list)
        for dan, m, _, _ in vrste:
            po_dnevih[dan].append(m)
            po_tednu[date.fromisoformat(dan).weekday()].append(m)
        po_odhodih: dict[int, list] = defaultdict(list)
        cilj_odhoda: dict[int, Counter] = defaultdict(Counter)
        for _, m, start, cilj in v30:
            if start is not None:
                po_odhodih[start].append(m)
                cilj_odhoda[start][cilj] += 1
        odhodi = []
        for x in _razrez(po_odhodih):
            start = x.pop("k")
            odhodi.append({**x, "start_s": start,
                           "cilj": cilj_odhoda[start].most_common(1)[0][0]})
        pot = pot_voznje(network, agency, no)
        out[pot] = {
            "pot": pot, "network": network, "agency": agency, "st": no,
            "ime": stats.AGENCY_NAMES.get(agency, agency),
            "linija": agency in LINIJSKI,
            "cilji": [c for c, _ in Counter(v[3] for v in v30).most_common(2)],
            "cilj": iz_histograma(hist),
            "dnevi": sorted(({"dan": x.pop("k"), **x} for x in _razrez(po_dnevih)),
                            key=lambda x: x["dan"]),
            "po_odhodih": sorted((o for o in odhodi if o["n"] >= 3), key=lambda x: x["start_s"]),
            "po_dnevu": sorted(({"dan": x.pop("k"), **x} for x in _razrez(po_tednu)),
                               key=lambda x: x["dan"]),
        }
    return out


def _zapisi_voznje(conn: sqlite3.Connection, network: str, voznje: dict[str, dict]) -> None:
    zdaj = int(time.time())
    conn.execute("DELETE FROM stat_voznja WHERE network = ?", (network,))
    conn.executemany(
        "INSERT OR REPLACE INTO stat_voznja (pot, network, agency, st, podatki, izracunano) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(pot, network, v["agency"], v["st"], json.dumps(v, separators=(",", ":")), zdaj)
         for pot, v in voznje.items()])
    conn.commit()


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
            # Surovi histogram gre zraven: pregled sešteje avtobuse vseh
            # prevoznikov v eno porazdelitev (mediana iz median ne gre).
            "cilj": {**iz_histograma(hist),
                     "hist": {str(m): c for m, c in sorted(hist.items())}},
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
    koncne = _koncne(conn, network, od_dolgo, do)
    lestvica = _lestvica([r for r in koncne if r[4] >= od], network)
    _zapisi_voznje(conn, network, _voznje(koncne, network, od))
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


# ---------------------------------------------------------------- strani

def odstotek(x: float | None) -> str:
    """58.2 -> „58 %“: cel odstotek z nedeljivim presledkom, zaokrožen
    `floor(x + 0.5)` kot vse drugo (`oznake.md`)."""
    return "" if x is None else f"{math.floor(x + 0.5)}\u00a0%"


def decimalno(x: float | None, mest: int = 1) -> str:
    """2.58 -> „2,6“. Pika je angleška."""
    return "" if x is None else f"{x:.{mest}f}".replace(".", ",")


def minute(x: float | None) -> str:
    """Mediana v minutah za stavek: 4.0 -> „4 min“, 2.5 -> „2,5 min“."""
    if x is None:
        return ""
    return (f"{int(x)}" if float(x).is_integer() else decimalno(x)) + "\u00a0min"


def zamuda_min(x: float | None) -> str:
    """Mediana zamude za vrstico: „+22,5 min“, „5,5 min prej“, „točno“.

    Beseda namesto minusa (`oznake.md`: minus je uganka), na pol minute kot
    `stats._pct` vrne mediano.
    """
    if x is None:
        return ""
    if x == 0:
        return "točno"
    st = f"{int(abs(x))}" if float(x).is_integer() else decimalno(abs(x))
    return f"{st}\u00a0min prej" if x < 0 else f"+{st}\u00a0min"


def ura_vr(t_s: int | None) -> str:
    """Voznoredne sekunde -> „06:35“ (od poldneva minus 12 h, kot GTFS)."""
    return "" if t_s is None else f"{(t_s // 3600) % 24:02d}:{(t_s % 3600) // 60:02d}"


#: Prevoznik pride v primerjavo šele s toliko vožnjami in toliko dnevi zajema
#: v oknu. Manjši so omenjeni posebej („še premalo“): sicer bi lestvica dva
#: dneva Marproma postavila ob mesec Arrive.
MIN_VOZENJ_PRIMERJAVA = 1000
MIN_DNI_PRIMERJAVA = 14


def _dni_zajema(x: dict, do: str) -> int:
    if not x.get("zajem_od"):
        return 0
    return min(OKNO_DNI, (date.fromisoformat(do) - date.fromisoformat(x["zajem_od"])).days + 1)


def primerljiv(x: dict, do: str) -> bool:
    return (x["skupina"] != "nadomestni"
            and x["cilj"].get("n", 0) >= MIN_VOZENJ_PRIMERJAVA
            and _dni_zajema(x, do) >= MIN_DNI_PRIMERJAVA)


def poti_za_iskalnik(conn: sqlite3.Connection) -> list[tuple[str, str | None]]:
    """Strani statistike za zemljevid strani, z dnem izračuna.

    Bere samo shranjene povzetke, nikoli ne računa: zemljevid strani mora
    odgovoriti takoj, in strani brez povzetka še ni smiselno ponujati.
    """
    poti: list[tuple[str, str | None]] = []
    for net in stats.SUMMARY_NETWORKS:
        vrstica = conn.execute(
            "SELECT computed_at, payload FROM povzetek "
            "WHERE kind = 'stat_prevozniki' AND network = ? AND days = 90", (net,)).fetchone()
        if vrstica is None:
            continue
        dan = (vrstica[0] or "")[:10] or None
        if not poti:
            poti += [(p, dan) for p in ("/statistika", "/statistika/napovedi",
                                        "/statistika/prevozniki", "/statistika/sz",
                                        "/statistika/relacije")]
        for x in json.loads(vrstica[1]).get("prevozniki", []):
            if x["skupina"] != "nadomestni" and x["cilj"].get("n"):
                poti.append((f"/statistika/prevoznik/{pristanek.slug(x['ime'])}", dan))
        # Vlaki in mestne linije; medkrajevnih šifer je na tisoče in jih ne
        # išče nihče (A6343) -- dosegljive ostanejo, `noindex`.
        mestni = ",".join("?" * len(LINIJSKI))
        poti += [(pot, dan) for (pot,) in conn.execute(
            f"SELECT pot FROM stat_voznja WHERE network = ? "
            f"AND (network = 'zeleznica' OR agency IN ({mestni})) ORDER BY pot",
            (net, *sorted(LINIJSKI)))]
    return poti


def vsi_prevozniki(conn: sqlite3.Connection) -> tuple[list[dict], dict]:
    """Prevozniki obeh omrežij iz nočnih povzetkov, s potjo strani."""
    out, glava = [], {}
    for net in stats.SUMMARY_NETWORKS:
        p = stats.summary_get(conn, "stat_prevozniki", net)
        glava = {"od": p["od"], "do": p["do"], "izracunano": p.get("computed_at")}
        for x in p["prevozniki"]:
            out.append({**x, "network": net, "slug": pristanek.slug(x["ime"]),
                        "dni_zajema": _dni_zajema(x, p["do"])})
    return out, glava


def spark(dnevi: list[dict], dni: int = OKNO_DNI) -> list[dict]:
    """Stolpci po dnevih: višina = delež v 5 min; dan z malo vožnjami sivo,
    nizek -- izpad zajema ni slab dan (7.–10. 10. 2026 vlaki brez vira)."""
    out = []
    for d in dnevi[-dni:]:
        n = d.get("n") or 0
        malo = n < MIN_VZOREC
        out.append({"dan": d["dan"], "n": n, "v5": d.get("v5min"), "malo": malo,
                    "visina": 4 if malo or d.get("v5min") is None else max(4, round(d["v5min"]))})
    return out


def stran_pregled(conn: sqlite3.Connection) -> dict:
    """Vse, kar pokaže `/statistika`: eno vprašanje, ena številka na kartico."""
    vsi, glava = vsi_prevozniki(conn)
    do = glava.get("do")
    vlak = next((x for x in vsi if x["kljuc"] == "zeleznica|1161|vlak"), None)
    busi = [x for x in vsi if x["network"] == "avtobus"]
    hist: Counter = Counter()
    for x in busi:
        hist.update({int(m): c for m, c in x["cilj"].get("hist", {}).items()})
    lestvica = sorted((x for x in vsi if do and primerljiv(x, do)),
                      key=lambda x: -x["cilj"]["v5min"])
    premalo = [x for x in vsi if x["skupina"] != "nadomestni" and x["cilj"].get("n")
               and not (do and primerljiv(x, do))]
    prej = sorted((x for x in busi if do and primerljiv(x, do)
                   and x["prezgodaj"].get("prej2") is not None),
                  key=lambda x: -x["prezgodaj"]["prej2"])
    nap = stats.summary_get(conn, "stat_napovedi", "zeleznica")
    rel = stran_relacije(conn)["kartice"]
    return {
        **glava,
        "sz": stats.summary_get(conn, "stat_sz", "zeleznica"),
        "relacija": rel[0] if rel else None,
        "vlak": vlak, "vlak_dnevi": spark(vlak["po_dnevih"]) if vlak else [],
        "bus": iz_histograma(hist), "bus_prevoznikov": len(busi),
        "lestvica": lestvica, "premalo": premalo,
        "prezgodaj": prej[:3], "vlak_prezgodaj": vlak["prezgodaj"] if vlak else None,
        "napoved": nap["skupaj"]["na_poti"]["vse"],
        "napoved_od": nap.get("od"), "napoved_do": nap.get("do"),
        "horizont_min": nap.get("horizont_min"),
        "min_vzorec": MIN_VZOREC, "min_prehodov": MIN_PREHODOV,
    }


def stran_prevozniki(conn: sqlite3.Connection) -> dict:
    """`/statistika/prevozniki`: primerljivi po deležu v 5 min, ostali pod črto."""
    vsi, glava = vsi_prevozniki(conn)
    do = glava.get("do")
    return {**glava, "min_vozenj": MIN_VOZENJ_PRIMERJAVA, "min_dni": MIN_DNI_PRIMERJAVA,
            "primerljivi": sorted((x for x in vsi if do and primerljiv(x, do)),
                                  key=lambda x: -x["cilj"]["v5min"]),
            "premalo": [x for x in vsi if x["skupina"] != "nadomestni" and x["cilj"].get("n")
                        and not (do and primerljiv(x, do))]}


def stran_sz(conn: sqlite3.Connection) -> dict:
    """`/statistika/sz`: nočni povzetek in čas izračuna."""
    p = stats.summary_get(conn, "stat_sz", "zeleznica")
    return {**p, "izracunano": p.get("computed_at")}


def stran_napovedi(conn: sqlite3.Connection) -> dict:
    """`/statistika/napovedi`: vlaki na poti in pred odhodom, avtobusi parno."""
    vlaki = stats.summary_get(conn, "stat_napovedi", "zeleznica")
    busi = stats.summary_get(conn, "stat_napovedi", "avtobus")
    parno = []
    for agency, sk in busi["po_prevozniku"].items():
        p = sk["na_poti"]["parno"]
        if p["prevoznik"]["n"] >= MIN_VZOREC:
            parno.append({"ime": busi["imena"].get(agency, agency),
                          "nasa": p["nasa"], "prevoznik": p["prevoznik"]})
    parno.sort(key=lambda x: x["prevoznik"]["mae_min"] - x["nasa"]["mae_min"], reverse=True)
    tedni = [t for t in vlaki["po_tednih"] if t["nasa"]["n"] >= MIN_VZOREC]
    najvec = max([t["prenos"]["mae_min"] for t in tedni] + [t["nasa"]["mae_min"] for t in tedni] + [0.01])
    return {
        "od": vlaki["od"], "do": vlaki["do"], "izracunano": vlaki.get("computed_at"),
        "vlaki": vlaki["skupaj"], "horizont_vlak": vlaki["horizont_min"],
        "horizont_bus": busi["horizont_min"], "parno": parno,
        "tedni": [{**t, "visina_nasa": round(t["nasa"]["mae_min"] / najvec * 100),
                   "visina_prenos": round(t["prenos"]["mae_min"] / najvec * 100)}
                  for t in tedni[-8:]],
        "min_vzorec": MIN_VZOREC,
    }


def stran_prevoznik(conn: sqlite3.Connection, slug: str) -> dict | None:
    """`/statistika/prevoznik/{slug}`; nadomestni prevoz SŽ gre k SŽ kot opomba."""
    vsi, glava = vsi_prevozniki(conn)
    izbrani = [x for x in vsi if x["slug"] == slug]
    glavni = next((x for x in izbrani if x["skupina"] != "nadomestni"), None)
    if glavni is None:
        return None
    nadomestni = next((x for x in izbrani if x["skupina"] == "nadomestni"), None)
    ure = [{"ura": int(h), **v} for h, v in glavni["po_urah"].items()
           if v["n"] >= MIN_VZOREC]
    # Stolpec = delež z zamudo nad 5 min, merilo postavi najslabša ura.
    najvec = max((100 - u["v5min"] for u in ure), default=0) or 1
    for u in ure:
        u["visina"] = max(4, round((100 - u["v5min"]) / najvec * 100))
    nap = glavni["napoved"]
    vse_n = nap["vse"]["nasa"].get("n", 0)
    return {**glava, "p": glavni, "nadomestni": nadomestni,
            "dnevi": spark(glavni["po_dnevih"], 90),
            "ure": ure,
            "napove_sam": bool(vse_n) and nap["parno"]["prevoznik"].get("n", 0) >= max(
                MIN_VZOREC, MIN_DELEZ_PREVOZNIKA * vse_n),
            "delez_prevoznika": (round(nap["parno"]["prevoznik"].get("n", 0) / vse_n * 100, 1)
                                 if vse_n else None),
            "primerljiv": bool(glava.get("do")) and primerljiv(glavni, glava["do"]),
            "min_vzorec": MIN_VZOREC, "min_dni_lestvica": MIN_DNI_LESTVICA}


DNEVI_TEDNA = ("ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja")


def stran_voznja(conn: sqlite3.Connection, pot: str) -> dict | None:
    """`/statistika/vlak/…` in `/statistika/linija/…`: ena vrstica `stat_voznja`.

    Pri vlaku še profil po postajah (`stats.history`, ista zgodovina kot okno
    vožnje): en vlak je ~600 vrstic `run`, to gre v zahtevi.
    """
    r = conn.execute("SELECT podatki, izracunano FROM stat_voznja WHERE pot = ?",
                     (pot,)).fetchone()
    if r is None:
        return None
    v = json.loads(r[0])
    od, do = _okno()
    out = {"v": v, "od": od, "do": do, "min_vzorec": MIN_VZOREC,
           "izracunano": datetime.fromtimestamp(r[1], TZ).isoformat(timespec="seconds"),
           "indeksiraj": v["network"] == "zeleznica" or v["linija"]}
    dnevi = v["dnevi"][-3 * OKNO_DNI:]
    na_dan = sum(d["n"] for d in dnevi) / len(dnevi) if dnevi else 0
    # Malo voženj na dan (vlak, medkrajevna šifra): stolpec = mediana zamude
    # tistega dne v barvi razreda; delež v 5 min treh voženj je 0, 33 ali
    # 100 % in pove manj. Merilo postavi slabši od 15 min in p90, da en
    # izreden dan ne splošči vseh. Mestna linija s sto vožnjami: delež.
    out["dnevi_zamuda"] = na_dan <= 10
    if out["dnevi_zamuda"]:
        meja = max(15, v["cilj"].get("p90_min") or 0)
        out["dnevi"] = [{**d, "razred": stats._KLJUC_RAZREDA[stats._razred_zamude(round(d["mediana_min"] * 60))],
                         "visina": max(4, round(min(max(d["mediana_min"], 0), meja) / meja * 100))}
                        for d in dnevi]
    else:
        out["dnevi"] = spark(dnevi, 3 * OKNO_DNI)
    if v["network"] == "zeleznica":
        trip = stats.resolve_trip(conn, v["st"])
        h = stats.history(conn, v["st"], days=OKNO_DNI, trip_id=trip)
        postaje = [p for p in h["by_stop"] if p["n"] >= 3 and p["name"]]
        najvec = max([p["p90_s"] for p in postaje] + [300])
        out["postaje"] = [{
            "ime": p["name"], "n": p["n"],
            "mediana": stats.opis_zamude(round(p["median_s"])),
            "p90": stats.opis_zamude(round(p["p90_s"])),
            "sirina": max(0, p["median_s"]) / najvec * 100,
        } for p in postaje]
    po_dnevu = [{**d, "ime": DNEVI_TEDNA[d["dan"]]} for d in v["po_dnevu"] if d["n"] >= 4]
    # Dneve pokaži le, kadar se razlikujejo: sedem vrstic „0 %“ (IC 503) ali
    # sedemkrat isto ne pove ničesar, kar ne bi že povedala prva kartica.
    razlika = (len(po_dnevu) >= 5 and (
        max(d["v5min"] for d in po_dnevu) - min(d["v5min"] for d in po_dnevu) >= 10
        or max(d["mediana_min"] for d in po_dnevu) - min(d["mediana_min"] for d in po_dnevu) >= 2))
    out["po_dnevu"] = po_dnevu if razlika else []
    return out


# ---------------------------------------------------------------- okno: SŽ

#: Odsek pride na seznam „vozni red ne drži“ z vsaj toliko vožnjami v oknu.
MIN_VOZENJ_ODSEK = 100

#: Potnikov odhod iz GPS je trenutek, ko je vlak 200 m za postajo
#: (`deljenje.NA_POSTAJI_M`); speljevanje do tja traja 20--30 s. Toliko
#: štejemo v korist SŽ: „prezgodaj“ je šele, kar ostane po tem zamiku.
POTNIK_ZAMIK_S = 30

#: Prehodov potnikov je malo (61 v mesecu, 30. 9.–29. 10. 2026), a vsak je
#: opažanje, ne sklep. Kartica pride od toliko naprej.
MIN_PREHODOV = 20


def _odseki(conn: sqlite3.Connection, od: str, do: str) -> list[dict]:
    """Odseki, kjer vlak redno izgubi čas: prirast zamude od odhoda z X do
    prihoda na naslednji postanek Y (MERITVE 29. 10. 2026, „Odseki, kjer
    vozni red ne drži“). Vzroka (dela, enotirnost) podatki ne povedo."""
    prirast: dict[tuple, list] = defaultdict(list)
    prej = None
    for trip, dan, seq, za, zd, ime in conn.execute("""
            SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep, st.name
            FROM run r JOIN trip t ON t.trip_id = r.trip_id
            JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
            JOIN station st ON st.stop_id = s.stop_id
            WHERE t.network = 'zeleznica' AND t.mode != 'bus'
              AND r.service_date BETWEEN ? AND ?
            ORDER BY r.trip_id, r.service_date, r.stop_seq""", (od, do)):
        if prej and prej[0] == trip and prej[1] == dan and prej[2] == seq - 1:
            z_od = prej[3]
            z_do = za if za is not None else zd
            if z_od is not None and z_do is not None and abs(z_do - z_od) < 3600:
                prirast[(prej[4], ime)].append(z_do - z_od)
        prej = (trip, dan, seq, zd if zd is not None else za, ime)
    out = []
    for (a, b), v in prirast.items():
        if len(v) >= MIN_VOZENJ_ODSEK:
            out.append({"od": a, "do": b, "n": len(v),
                        "izguba2": round(sum(x >= 120 for x in v) / len(v) * 100, 1),
                        "mediana_min": stats._pct([stats._minute(x) for x in v], 0.5)})
    out.sort(key=lambda x: (-x["izguba2"], -x["n"]))
    return out


def sz(conn: sqlite3.Connection, days: int, network: str,
       danes: date | None = None) -> dict:
    """Stran `/statistika/sz`: kaj kaže zemljevid SŽ in kaj je res.

    Samo za železnico; avtobusno okno je prazno (`SUMMARY_BUILDERS` kliče
    vsako vrsto za obe omrežji).
    """
    if network != "zeleznica":
        return {"days": [], "runs": 0}
    dopolni(conn, danes)
    od, do = _okno(danes)
    od_sz = max(od, SZ_VODI_OD)
    v = {"postankov": 0, "dvig1": 0, "dvig2": 0, "dvig5": 0, "dvig10": 0,
         "izhodisc": 0, "izhodisce_lazno": 0}
    hist: Counter = Counter()
    potniki = []
    dnevi = []
    for dan, _, x in _beri(conn, "sz", od_sz, do, "zeleznica"):
        dnevi.append(dan)
        for k in v:
            v[k] += x.get(k, 0)
        hist.update({int(m): c for m, c in x.get("dvig_hist", {}).items()})
        potniki += x.get("potniki", [])
    # Prehodi potnikov so redki (61 v mesecu): okno zanje je vsa zgodovina.
    for dan, _, x in _beri(conn, "sz", SZ_VODI_OD, od_sz, "zeleznica"):
        if dan < od_sz:
            potniki += x.get("potniki", [])
    n = v["postankov"]
    prej = sorted(p["prej_s"] - POTNIK_ZAMIK_S for p in potniki)
    # En primer na vožnjo: LPV 2423 je zaostal na dveh postajah zapored.
    najhujsi: dict[tuple, dict] = {}
    for p in potniki:
        k = (p["st"], p["dan"])
        if k not in najhujsi or p["prej_s"] > najhujsi[k]["prej_s"]:
            najhujsi[k] = p
    nadomestni = [x for _, k, x in _beri(conn, "prevoznik", od, do, "zeleznica")
                  if k == "zeleznica|1161|nadomestni"]
    napoved = _prazna_napoved()
    for _, k, x in _beri(conn, "napoved", od, do, "zeleznica"):
        if k == "zeleznica|1161|na_poti":
            for blok, modeli in napoved.items():
                for model, vsote in modeli.items():
                    _sestej(vsote, x.get(blok, {}).get(model, {}))
    vse_n = napoved["vse"]["nasa"]["n"]

    def delez(a: int, b: int) -> float | None:
        return round(a / b * 100, 1) if b else None

    return {
        "od": od_sz, "do": do, "days": dnevi, "runs": n,
        "popravki": {"postankov": n, **{k: delez(v[k], n) for k in ("dvig1", "dvig2", "dvig5", "dvig10")},
                     "mediana_min": pristanek._kvantil(sorted(hist), hist, sum(hist.values()), 0.5)
                     if hist else None},
        "izhodisca": {"n": v["izhodisc"], "lazno": delez(v["izhodisce_lazno"], v["izhodisc"])},
        "potniki": {
            "n": len(prej), "voznj": len({(p["st"], p["dan"]) for p in potniki}),
            "od": min((p["dan"] for p in potniki), default=None),
            "do": max((p["dan"] for p in potniki), default=None),
            "prej2": delez(sum(x >= 120 for x in prej), len(prej)),
            "prej5": delez(sum(x >= 300 for x in prej), len(prej)),
            "prej10": delez(sum(x >= 600 for x in prej), len(prej)),
            "kasneje1": sum(x <= -60 for x in prej),
            "mediana_min": round(stats._pct(prej, 0.5) / 60, 1) if prej else None,
            "najhujsi": [{**p, "stal_min": round((p["prej_s"] - POTNIK_ZAMIK_S) / 60)}
                         for p in sorted(najhujsi.values(), key=lambda p: -p["prej_s"])[:3]],
            "zamik_s": POTNIK_ZAMIK_S,
        },
        "odseki": _odseki(conn, od, do)[:6],
        "nadomestni": {"nacrt": sum(x["nacrt"] or 0 for x in nadomestni),
                       "z_meritvijo": sum(x["z_meritvijo"] for x in nadomestni)},
        "napoved": {"delez_prevoznika": delez(napoved["parno"]["prevoznik"]["n"], vse_n),
                    "nasa": meritve(napoved["vse"]["nasa"]),
                    "prenos": meritve(napoved["vse"]["prenos"])},
        "min_vzorec": MIN_VZOREC, "min_prehodov": MIN_PREHODOV,
    }


# ---------------------------------------------------------------- okno: relacije

#: Pari, ki jih ljudje iščejo (MERITVE „Iskalniki“: vlak ljubljana koper,
#: maribor, celje, kranj) in kjer vozita vlak in avtobus. Zadnji: odsek
#: avtoceste DARS (`promet.ac`, od priključka do priključka) tja in nazaj.
RELACIJE = (
    ("Ljubljana", "Maribor", "Ljubljana AP", "Maribor AP", ("LJ - MB", "MB - LJ")),
    ("Ljubljana", "Koper", "Ljubljana AP", "Koper", ("LJ - KP", "KP - LJ")),
    ("Ljubljana", "Jesenice", "Ljubljana AP", "Jesenice", ("LJ - Karavanke", "Karavanke - LJ")),
    ("Ljubljana", "Celje", "Ljubljana AP", "Celje AP", None),
    ("Ljubljana", "Kranj", "Ljubljana AP", "Kranj AP", None),
    ("Ljubljana", "Novo mesto", "Ljubljana AP", "Novo mesto", None),
)


def _par(conn: sqlite3.Connection, network: str, od: str, cilj: str,
         od_dan: str, do_dan: str) -> dict | None:
    """Vožnje, ki ustavijo na `od` in nato na `cilj`: trajanje po voznem redu,
    dejansko (vozni red + zamuda na obeh koncih) in zamuda na cilju."""
    # Najprej pari postankov iz voznega reda (kazali po imenu in `stop_id`),
    # nato `run` po ključu vožnje. Brez tega reda je planer začel pri `run`
    # po dnevu: 411 s za šest parov na arwenu (29. 10. 2026).
    vrste = conn.execute(f"""
        WITH par AS MATERIALIZED (
            SELECT s1.trip_id, s1.stop_seq AS q1, s1.dep_s, s2.stop_seq AS q2,
                   s2.arr_s, t.agency
            FROM station a JOIN sched s1 ON s1.stop_id = a.stop_id
            JOIN sched s2 ON s2.trip_id = s1.trip_id AND s2.stop_seq > s1.stop_seq
            JOIN station b ON b.stop_id = s2.stop_id AND b.name = :cilj
            JOIN trip t ON t.trip_id = s1.trip_id
            WHERE a.name = :od AND t.network = :net
              AND (t.network = 'avtobus' OR t.mode != 'bus'))
        SELECT r2.service_date, p.dep_s, COALESCE(r1.delay_dep, r1.delay_arr),
               p.arr_s, COALESCE(r2.delay_arr, r2.delay_dep), p.agency
        FROM par p
        JOIN run r2 ON r2.trip_id = p.trip_id AND r2.stop_seq = p.q2
                   AND r2.service_date BETWEEN :od_dan AND :do_dan
        LEFT JOIN run r1 ON r1.trip_id = p.trip_id AND r1.stop_seq = p.q1
                        AND r1.service_date = r2.service_date
        WHERE COALESCE(r2.delay_arr, r2.delay_dep) IS NOT NULL
          AND ABS(COALESCE(r2.delay_arr, r2.delay_dep)) <= {stats.MAX_REALNA_ZAMUDA_S}""",
        {"od": od, "cilj": cilj, "net": network, "od_dan": od_dan, "do_dan": do_dan}).fetchall()
    if not vrste:
        return None
    vr = [(arr - dep) / 60 for _, dep, _, arr, _, _ in vrste if dep is not None and arr is not None]
    dej = [((arr + z2) - (dep + z1)) / 60 for _, dep, z1, arr, z2, _ in vrste
           if dep is not None and arr is not None and z1 is not None]
    zam = [z2 for *_, z2, _ in vrste]
    return {
        "n": len(vrste),
        "prevozniki": [stats.AGENCY_NAMES.get(a, a) for a, _ in
                       Counter(v[5] for v in vrste).most_common(2)],
        "trajanje_vr": stats._pct(vr, 0.5),
        "trajanje": stats._pct(dej, 0.5) if len(dej) >= MIN_VZOREC else None,
        "v5min": round(sum(stats._je_pravocasna(z) for z in zam) / len(zam) * 100, 1),
        "mediana_min": stats._pct([stats._minute(z) for z in zam], 0.5),
    }


def _avto(relacija: str, od_dan: str, do_dan: str) -> dict | None:
    """Avto po avtocesti iz `promet.sqlite` (DARS prek NAP), delavniki.

    Baza je samo na stroju, ki promet zajema (arwen); drugje kartica avta
    izpade, ne pokaže ničle.
    """
    if not config.PROMET_DB.exists():
        return None
    od_ts = int(datetime.fromisoformat(od_dan).replace(tzinfo=TZ).timestamp())
    do_ts = int((datetime.fromisoformat(do_dan) + timedelta(days=1)).replace(tzinfo=TZ).timestamp())
    try:
        pc = sqlite3.connect(f"file:{config.PROMET_DB}?mode=ro", uri=True)
        vrste = pc.execute("SELECT ts, cas_s FROM ac WHERE relacija = ? AND ts BETWEEN ? AND ? "
                           "AND cas_s IS NOT NULL", (relacija, od_ts, do_ts)).fetchall()
        pc.close()
    except sqlite3.Error:
        return None
    po_uri: dict[int, list] = defaultdict(list)
    for ts, cas in vrste:
        d = datetime.fromtimestamp(ts, TZ)
        if d.weekday() < 5:
            po_uri[d.hour].append(cas / 60)
    vse = [x for v in po_uri.values() for x in v]
    if len(vse) < MIN_VZOREC:
        return None
    ure = {h: stats._pct(v, 0.5) for h, v in po_uri.items() if len(v) >= 10}
    najhujsa = max(ure, key=ure.get)
    return {"n": len(vse), "trajanje": stats._pct(vse, 0.5),
            "konica_ura": najhujsa, "konica": ure[najhujsa],
            "konica_p90": stats._pct(po_uri[najhujsa], 0.9)}


def relacije(conn: sqlite3.Connection, days: int, network: str,
             danes: date | None = None) -> dict:
    """Stran `/statistika/relacije`: vlak, avtobus in avto na istih parih.

    Avto je odsek avtoceste od priključka do priključka (brez mesta in
    parkiranja) -- stran to pove. Samo za železnico (en izračun za oboje).
    """
    if network != "zeleznica":
        return {"days": [], "runs": 0}
    od, do = _okno(danes)
    out = []
    for vlak_od, vlak_do, bus_od, bus_do, ac in RELACIJE:
        for smer in (0, 1):
            a, b = (vlak_od, vlak_do) if smer == 0 else (vlak_do, vlak_od)
            ba, bb = (bus_od, bus_do) if smer == 0 else (bus_do, bus_od)
            out.append({
                "od": a, "do": b,
                "vlak": _par(conn, "zeleznica", a, b, od, do),
                "avtobus": _par(conn, "avtobus", ba, bb, od, do),
                "avto": _avto(ac[smer], od, do) if ac else None,
            })
    return {"od": od, "do": do, "days": [do], "runs": sum((r["vlak"] or {}).get("n", 0) for r in out),
            "relacije": out, "min_vzorec": MIN_VZOREC}



def stran_relacije(conn: sqlite3.Connection) -> dict:
    """`/statistika/relacije`: na vsak par možnosti po trajanju, najhitrejša prva.

    Vlak in avtobus le z vsaj `MIN_VZOREC` vožnjami; trajanje je dejansko
    (vozni red + zamuda), kjer je odhod izmerjen pri dovolj vožnjah, sicer
    vozni red -- stran pove, katero.
    """
    p = stats.summary_get(conn, "stat_relacije", "zeleznica")
    kartice = []
    for r in p.get("relacije", []):
        moznosti = _moznosti(r, MIN_VZOREC)
        if len(moznosti) >= 2:
            kartice.append({"od": r["od"], "do": r["do"], "moznosti": moznosti})
    return {"od": p.get("od"), "do": p.get("do"), "izracunano": p.get("computed_at"),
            "kartice": kartice}


def _moznosti(r: dict, min_n: int) -> list[dict]:
    """Avto, avtobus in vlak enega para po trajanju, najhitrejši prvi."""
    moznosti = []
    if r.get("avto"):
        moznosti.append({"kaj": "avto", "t": r["avto"]["trajanje"], "x": r["avto"]})
    for kaj in ("avtobus", "vlak"):
        x = r.get(kaj)
        if x and x["n"] >= min_n:
            moznosti.append({"kaj": kaj, "t": x["trajanje"] or x["trajanje_vr"], "x": x,
                             "pot": r.get("pot_" + kaj)})
    moznosti.sort(key=lambda m: m["t"])
    najvec = max((m["t"] for m in moznosti), default=0) or 1
    for m in moznosti:
        m["sirina"] = round(m["t"] / najvec * 100)
    return moznosti


#: Iskanje poljubnega para (David, 29. 10. 2026: „za čisto vsako relacijo,
#: tudi male“). Parov postankov iste vožnje je za nočni izračun preveč, en
#: par pa je poizvedba po kazalih (~10 ms): ob zahtevi, v predpomnilniku do
#: konca okna. Pod `MIN_ISKANJE` vožnjami številke ne pokažemo, pod
#: `MIN_VZOREC` jo pokažemo z opozorilom -- mala relacija ima malo voženj.
MIN_ISKANJE = 10
ISKANJE_NAJVEC = 500
_iskanja: dict[tuple, dict] = {}
_iskanja_zaklep = threading.Lock()


def iskanje_relacije(conn: sqlite3.Connection, od_vnos: str, do_vnos: str,
                     danes: date | None = None) -> dict:
    """Vpisana para imen -> možnosti kot na `/statistika/relacije`.

    Ime se razreši po omrežju (vlak „Ljubljana“, avtobus „Ljubljana AP“).
    Avto le, kjer je par v `RELACIJE` (odsek avtoceste DARS).
    """
    od, do = _okno(danes)
    imena = {net: (journey.resolve_station(conn, od_vnos, net),
                   journey.resolve_station(conn, do_vnos, net))
             for net in ("zeleznica", "avtobus")}
    kljuc = (imena["zeleznica"], imena["avtobus"], do)
    with _iskanja_zaklep:
        r = _iskanja.get(kljuc)
    if r is None:
        r = {}
        for net, kaj in (("zeleznica", "vlak"), ("avtobus", "avtobus")):
            a, b = imena[net]
            if a and b and a != b:
                r[kaj] = _par(conn, net, a, b, od, do)
                r["pot_" + kaj] = f"{a} – {b}"
        for vlak_od, vlak_do, bus_od, bus_do, ac in RELACIJE:
            for smer, (a, b, ba, bb) in enumerate(((vlak_od, vlak_do, bus_od, bus_do),
                                                    (vlak_do, vlak_od, bus_do, bus_od))):
                if ac and (imena["zeleznica"] == (a, b) or imena["avtobus"] == (ba, bb)):
                    r["avto"] = _avto(ac[smer], od, do)
        with _iskanja_zaklep:
            if len(_iskanja) >= ISKANJE_NAJVEC:
                _iskanja.pop(next(iter(_iskanja)))
            _iskanja[kljuc] = r
    glavna = next((imena[n] for n in ("zeleznica", "avtobus") if all(imena[n])),
                  (od_vnos, do_vnos))
    return {"od": glavna[0], "do": glavna[1], "moznosti": _moznosti(r, MIN_ISKANJE),
            "malo": {kaj: r[kaj]["n"] for kaj in ("vlak", "avtobus")
                     if r.get(kaj) and r[kaj]["n"] < MIN_ISKANJE},
            "neznano": [v for i, v in enumerate((od_vnos, do_vnos))
                        if not imena["zeleznica"][i] and not imena["avtobus"][i]],
            "ista": glavna[0] == glavna[1], "okno_od": od, "okno_do": do,
            "omrezje": "zeleznica" if all(imena["zeleznica"]) else "avtobus",
            "min_vzorec": MIN_VZOREC}
