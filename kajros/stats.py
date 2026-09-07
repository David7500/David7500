"""Poizvedbe nad zajetimi podatki: zgodovina, porazdelitve, hitrosti, napoved."""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import threading
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, geo

TZ = ZoneInfo(config.TIMEZONE)


# Zakaj povsod `COALESCE(delay_dep, delay_arr)` in ne obratno.
#
# Feed pri avtobusih pogosto poslje `arrival` BREZ polja `delay` -- namesto
# zamude da absolutni cas. Protobuf za manjkajoce polje vrne 0, zato je zajem
# to zapisoval kot "tocno". Izmerjeno: 11 906 od 20 523 avtobusnih vrstic
# (58 %) ima `delay_arr = 0` ob nenicelnem `delay_dep`; pri zeleznici tega ni
# v NOBENI vrstici, ker vlaki vedno posljejo obe polji.
#
# Posledica je bila 13 odstotnih tock razlike: delez tocnih avtobusov je bral
# 84,3 % namesto 71,2 %. `departure.delay` je izpolnjen pri vseh prevoznikih
# stoodstotno, zato je merodajen on.
#
# Zajem od zdaj naprej pise NULL namesto lazne nicle (`collector.ingest`),
# stare vrstice pa ostanejo -- iz njih se prava vrednost ne da izvleci, ker
# surovega feeda ne hranimo.
def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def _abs_time(service_date: str, seconds: int | None) -> str | None:
    """Voznoredna sekunda od polnoči -> absolutni čas (zna čez polnoč)."""
    if seconds is None:
        return None
    base = datetime.combine(date.fromisoformat(service_date), datetime.min.time(), tzinfo=TZ)
    return (base + timedelta(seconds=seconds)).isoformat()


# Javno ime za isto pretvorbo -- uporablja ga tudi api.py za /api/live.
abs_time = _abs_time


def stations(conn: sqlite3.Connection, network: str | None = None) -> list[dict]:
    """Postaje, po želji samo tiste na danem omrežju.

    Rabi se, ko so v bazi tudi avtobusi: LPP prinese tisoč postajališč in
    zemljevid železniške mreže bi jih narisal vsa. Postajališče ni lastnost
    postaje, ampak tega, kdo tam ustavlja -- zato pogoj in ne stolpec.
    """
    if not network:
        return [dict(r) for r in conn.execute("SELECT * FROM station ORDER BY name")]
    return [
        dict(r)
        for r in conn.execute(
            "SELECT st.* FROM station st WHERE EXISTS ("
            "  SELECT 1 FROM sched s JOIN trip t ON t.trip_id = s.trip_id "
            "  WHERE s.stop_id = st.stop_id AND t.network = ?) ORDER BY st.name",
            (network,),
        )
    ]


def network_geojson(conn: sqlite3.Connection, elementary_only: bool = True) -> dict:
    sql = "SELECT e.*, a.name AS from_name, b.name AS to_name FROM edge e " \
          "JOIN station a ON a.stop_id = e.from_id JOIN station b ON b.stop_id = e.to_id"
    if elementary_only:
        sql += " WHERE e.elementary = 1"
    feats = [
        {
            "type": "Feature",
            "properties": {
                "from_id": r["from_id"], "from": r["from_name"],
                "to_id": r["to_id"], "to": r["to_name"],
                "km": r["km"], "elementary": bool(r["elementary"]), "trips": r["trips"],
            },
            "geometry": json.loads(r["geojson"]),
        }
        for r in conn.execute(sql)
    ]
    return {"type": "FeatureCollection", "features": feats}


def resolve_trip(conn: sqlite3.Connection, train_no: str,
                 service_date: str | None = None,
                 trip_id: str | None = None) -> str | None:
    """Ena vožnja izmed tistih, ki nosijo to številko.

    Številka vlaka **ni** ključ. Devet vlakov v zajetem voznem redu ima dva ali
    tri tripe -- sezonske različice iste poti z različnimi obdobji veljavnosti
    (npr. 4292 Nova Gorica--Jesenice, 68 dni in 24 dni). Poizvedba brez tega
    izbora je vrnila vse skupaj: vozni red vlaka 4292 je imel 38 postankov
    namesto 19, vsako postajo dvakrat.

    Pri avtobusih je isto pravilo nujno: `route_short_name` je številka linije
    in LPP linija 3G ima 388 voženj.

    Izbira: trip, ki vozi na dani dan; med več takimi tisti z največ
    obratovalnimi dnevi (glavna različica, ne sezonska izjema).

    `trip_id` to izbiro povozi -- odhodna tabla in iskalnik vesta, katero
    vožnjo je človek kliknil, in je ni treba uganiti. Preverimo, da res nosi
    to številko, sicer bi naslov lahko pokazal tujo vožnjo.

    **Ce dan `trip_id` ne obstaja ali ne nosi te stevilke, vrnemo None**, ne
    druge voznje. Prej je preverjanje bilo, a je ob neujemanju tiho padlo na
    izbiro po dnevih: `/api/train/3G?trip=999999999` je vrnil 200 in vozni red
    POVSEM DRUGE voznje, neobstojeci id pa odzvanjal nazaj. Kdor odpre
    zastarelo deljeno povezavo, mora dobiti napako, ne tujega voznega reda.
    """
    if trip_id:
        row = conn.execute(
            "SELECT trip_id FROM trip WHERE trip_id = ? AND train_no = ?",
            (trip_id, train_no),
        ).fetchone()
        return row["trip_id"] if row else None
    # Najmocnejsi dokaz, KATERA voznja danes res pelje, ni vozni red, ampak
    # meritev. LP 4208 ima tri tripe; danes pelje 465938 (30 meritev), izbira
    # po dnevih veljavnosti pa je vzela 456511 (232 dni, NIC meritev) -- kdor
    # je vlak kliknil na zivem seznamu, je pristal na strani, ki o njem ne ve
    # nicesar, ceprav je vlak vozil 8 minut pozno. Zato meritev odloca prva.
    rows = conn.execute(
        "SELECT t.trip_id, "
        "       EXISTS(SELECT 1 FROM run r WHERE r.trip_id = t.trip_id "
        "              AND r.service_date = ?) AS ima_meritve, "
        "       (SELECT COUNT(*) FROM service_day sd WHERE sd.service_id = t.service_id) AS days, "
        "       (SELECT COUNT(*) FROM service_day sd WHERE sd.service_id = t.service_id "
        "        AND sd.date = ?) AS runs_today "
        "FROM trip t WHERE t.train_no = ? "
        "ORDER BY ima_meritve DESC, runs_today DESC, days DESC, t.trip_id",
        (service_date, service_date, train_no),
    ).fetchall()
    return rows[0]["trip_id"] if rows else None


def timetable(conn: sqlite3.Connection, train_no: str,
              service_date: str | None = None,
              trip_id: str | None = None) -> list[dict]:
    trip_id = resolve_trip(conn, train_no, service_date, trip_id)
    if not trip_id:
        return []
    return [
        dict(r)
        for r in conn.execute(
            "SELECT s.stop_seq, s.stop_id, st.name, st.lat, st.lon, s.arr_s, s.dep_s "
            "FROM sched s JOIN station st ON st.stop_id = s.stop_id "
            "WHERE s.trip_id = ? ORDER BY s.stop_seq",
            (trip_id,),
        )
    ]


def trip_identity(conn: sqlite3.Connection, train_no: str,
                  trip_id: str | None = None) -> dict:
    """Kaj ta vožnja sploh je: vrsta vozila, omrežje, prevoznik.

    Prikaz brez tega govori o vlaku tudi tam, kjer vozi mestni avtobus --
    "vlak je od takrat verjetno že pripeljal" pod linijo 47 ni le netočno,
    ampak zveni kot napaka programa.
    """
    sql = "SELECT mode, network, agency FROM trip WHERE train_no = ?"
    params: tuple = (train_no,)
    if trip_id:
        sql += " AND trip_id = ?"
        params = (train_no, trip_id)
    row = conn.execute(sql + " LIMIT 1", params).fetchone()
    if not row:
        return {"mode": "vlak", "network": "zeleznica", "agency": None}
    return {"mode": row["mode"], "network": row["network"], "agency": row["agency"]}


def trip_mode(conn: sqlite3.Connection, train_no: str) -> str:
    """Samo vrsta vozila. Za celotno sliko glej `trip_identity`."""
    return trip_identity(conn, train_no)["mode"]


def run_detail(conn: sqlite3.Connection, train_no: str, service_date: str,
               trip_id: str | None = None) -> list[dict]:
    """Ena konkretna vožnja: vozni red + zamuda + izračunani dejanski čas."""
    trip_id = resolve_trip(conn, train_no, service_date, trip_id)
    if not trip_id:
        return []
    rows = conn.execute(
        # `lat`/`lon` rabi zemljevid ene voznje v oknu: postanke narise kot
        # crto in pike. Poizvedba postajo ze pridruzuje, zato je to zastonj.
        "SELECT s.stop_seq, st.name, st.lat, st.lon, s.arr_s, s.dep_s, "
        "       r.delay_arr, r.delay_dep, r.feed_ts "
        "FROM sched s JOIN station st ON st.stop_id = s.stop_id "
        "LEFT JOIN run r ON r.trip_id = s.trip_id AND r.stop_seq = s.stop_seq "
        "                AND r.service_date = ? "
        "WHERE s.trip_id = ? ORDER BY s.stop_seq",
        (service_date, trip_id),
    )
    typ = typical_dwell(conn, train_no)
    out = []
    for r in rows:
        d = dict(r)
        if r["arr_s"] is not None and r["dep_s"] is not None:
            d["sched_dwell_s"] = r["dep_s"] - r["arr_s"]
        t = typ.get(r["stop_seq"])
        if t:
            d["typical_dwell_s"] = t["typical_dwell_s"]
            d["dwell_samples"] = t["n_samples"]
        d["sched_arr"] = _abs_time(service_date, r["arr_s"])
        d["sched_dep"] = _abs_time(service_date, r["dep_s"])
        # Feed nosi samo zamudo -- dejanski cas je vozni red + zamuda.
        d["actual_arr"] = _abs_time(service_date, (r["arr_s"] or 0) + r["delay_arr"]) \
            if r["arr_s"] is not None and r["delay_arr"] is not None else None
        d["actual_dep"] = _abs_time(service_date, (r["dep_s"] or 0) + r["delay_dep"]) \
            if r["dep_s"] is not None and r["delay_dep"] is not None else None
        # `COALESCE(delay_dep, delay_arr)` in NE obratno -- `departure.delay`
        # je izpolnjen pri vseh prevoznikih, `arrival.delay` ne. To pravilo je
        # bilo doslej zapisano tudi v `common.stopDelay()`; drugi odjemalec bi
        # ga moral uganiti tretjic. Vrsta se doda spodaj, ko je znana meja.
        d["zamuda"] = opis_zamude(
            r["delay_dep"] if r["delay_dep"] is not None else r["delay_arr"])
        out.append(d)
    oznaci_zastarele(out)
    return out


def oznaci_zastarele(rows: list[dict]) -> None:
    """Označi postanke, ki jih feed po nekem trenutku ni več osvežil.

    `run` hrani ZADNJE stanje postanka. Kadar feed postanek nekaj časa
    pošilja, potem pa neha, ostane v bazi vrednost iz tistega trenutka --
    napoved, ki ni bila nikoli potrjena. Na zaslonu je bila videti kot
    meritev in je delala **nemogoče vozne rede**: RG 310 je imel Litostroj
    ob 18:01 in naslednjo postajo Ljubljana Stegne ob 17:35.

    Razpoznavni znak je mehanski, ne ugib: postanek, ki je bil nazadnje
    osvežen **prej kot kateri od prejšnjih**, je ostanek. Izmerjeno
    7. 9. 2026: pri železnici to razloži **451 od 452** skokov ure nazaj
    (100 %) ob 0,7 % vseh postankov, pri avtobusih 43 % ob 3,7 %.
    Spreminja `rows` na mestu.
    """
    najvecji = None
    for d in rows:
        ts = d.get("feed_ts")
        if ts is None:
            continue
        if najvecji is not None and ts < najvecji:
            d["zastarelo"] = True
        else:
            najvecji = ts


def history(conn: sqlite3.Connection, train_no: str, days: int = 90,
            exclude_date: str | None = None, trip_id: str | None = None) -> dict:
    """Zgodovina zamud ene voznje: po dnevih in po postajah.

    `exclude_date` izpusti en prometni dan. Rabi ga prikaz tekoce voznje:
    "povprecje preteklih voznj" ne sme vsebovati voznje, ki jo risemo zraven,
    sicer bi krivulja delno primerjala podatek sam s seboj.

    **`trip_id` ni okras.** Brez njega poizvedba zdruzi vse voznje te
    stevilke, in pri avtobusu je to katastrofa: LPP linija 25 ima 217 voznj
    in profil se gradi po `stop_seq`, torej po **zaporedni stevilki** postanka.
    Pod "postanek 2" se je zato sestalo Medvode novo naselje (drugi postanek
    v smeri proti Zadobrovi, povprecje +7 min) in **Novo Polje** (drugi
    postanek v NASPROTNI smeri, +1 min) -- dva razlicna kraja pod eno oznako.
    V grafu je bilo to videti kot devet postaj pri +14 in nato padec za
    petnajst minut v enem koraku; v resnici se je tam koncala ena smer in
    zacela druga. Isto velja za devet vlakov s sezonskimi razlicicami.

    `trip_id` je med regeneracijami GTFS stabilen, zato isti `trip_id` na
    drugem dnevu je res isti odhod.
    """
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    kje = "t.train_no = ?" if trip_id is None else "r.trip_id = ?"
    rows = conn.execute(
        "SELECT r.service_date, r.stop_seq, st.name, r.delay_arr, r.delay_dep "
        "FROM run r JOIN trip t USING (trip_id) JOIN sched s "
        "       ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
        "JOIN station st ON st.stop_id = s.stop_id "
        f"WHERE {kje} AND r.service_date >= ? "
        "  AND (? IS NULL OR r.service_date <> ?) "
        "ORDER BY r.service_date, r.stop_seq",
        (trip_id or train_no, since, exclude_date, exclude_date),
    ).fetchall()

    by_day: dict[str, list] = {}
    by_stop: dict[int, dict] = {}
    for r in rows:
        # Odhodna vrednost je izpolnjena pri vseh prevoznikih stoodstotno,
        # prihodna pri avtobusih le v 31-61 %. Tu je bilo obratno in je bralo
        # niclo tam, kjer je feed odhod povedal -- edina taka poizvedba.
        delay = r["delay_dep"] if r["delay_dep"] is not None else r["delay_arr"]
        if delay is None:
            continue
        by_day.setdefault(r["service_date"], []).append((r["stop_seq"], delay))
        slot = by_stop.setdefault(r["stop_seq"], {"name": r["name"], "delays": []})
        slot["delays"].append(delay)

    runs = []
    for day, items in sorted(by_day.items()):
        items.sort()
        delays = [d for _, d in items]
        runs.append({
            "service_date": day,
            "stops_observed": len(items),
            "final_delay_s": items[-1][1],
            "max_delay_s": max(delays),
        })

    finals = [r["final_delay_s"] for r in runs]
    profile = [
        {
            "stop_seq": seq, "name": v["name"], "n": len(v["delays"]),
            # Mediana je odpornejsa, povprecje je tisto, kar clovek pricakuje --
            # zato oboje, da prikaz ne rabi izbirati na slepo.
            "mean_s": round(statistics.mean(v["delays"]), 1),
            "median_s": _pct(v["delays"], 0.5),
            "p90_s": _pct(v["delays"], 0.9),
            "max_s": max(v["delays"]),
        }
        for seq, v in sorted(by_stop.items())
    ]
    return {
        "train_no": train_no,
        "excluded_date": exclude_date,
        "runs_observed": len(runs),
        "summary": {
            "median_final_s": _pct(finals, 0.5),
            "p90_final_s": _pct(finals, 0.9),
            "worst_final_s": max(finals) if finals else None,
            "on_time_share": (round(sum(1 for f in finals if _je_pravocasna(f)) / len(finals), 3)
                              if finals else None),
        },
        "runs": runs,
        "by_stop": profile,
    }


# Zadnji postanek vsake vožnje vsakega dne -- torej končna zamuda.
#
# Prvotno je bilo to `ROW_NUMBER() OVER (PARTITION BY ...)` nad `run` s samim
# pogojem `service_date >= ?`, omrežje pa se je filtriralo šele po tem. Pri
# 52 milijonih vrstic je to pomenilo okensko funkcijo in razvrščanje čez
# 12,6 milijona vrstic **tudi za poizvedbo o železnici**, ki jih ima 700 000:
# 38 sekund.
#
# Zdaj se najprej zožimo na vožnje izbranega omrežja (železnica jih ima 789 od
# 21 000) in šele nato beremo `run`. Ključ `run` je (trip_id, service_date,
# stop_seq), zato je to za vsako vožnjo obseg po indeksu, ne pregled tabele.
# `MAX(stop_seq)` namesto ROW_NUMBER pa odpravi razvrščanje.
# Nad to mejo vrednost ni zamuda, ampak feedova zamenjava prometnega dne --
# ista napaka, ki jo pri prikazu lovi `api.MAX_LIVE_DELAY_S` (6 h). Za
# STATISTIKO je meja nižja in izmerjena, ne izbrana:
#
#   * železnica nima **nobene** vrstice nad 3 h v 69 803 meritvah, torej strop
#     iz nje ne vzame ničesar (0,00 %);
#   * pri avtobusih odpade 2 614 vrstic (0,49 %), mediana se komaj premakne
#     (2,18 → 2,15 min), **povprečje pa pade s 7,25 na 4,86 min** in p99 s
#     73,4 na 59,0. Mediana stabilna, povprečje sesuto -- to je podpis
#     izstopajočih vrednosti, ne repa prave porazdelitve.
#
# Podatki se NE brišejo; to je filter branja. Zajem hrani vse.
# Meja "tocnosti": pet minut, obicajen prag pri zeleznicah.
#
# **V MINUTAH in ne v sekundah**, ker je poleg nje na zaslonu razrez po
# razredih in bralec sme obe stevilki sesteti. Dokler je bila 300 s, razred
# "1-5 min" pa je segal do zaokrozenih pet minut (330 s), se 553 vozenj
# (1,23 % od 45 043) ni ujelo: bila so v razredu, a ne med "tocnimi", in
# vsota razredov ni dala izpisanega odstotka.
#
# Prej je stala nizje v datoteki in jo je uporabljalo le dvoje mest, stiri
# druga pa so imela trdo zapisano 300 -- komentar je trdil "spremeni na obeh
# mestih" in to ze takrat ni drzalo. Zdaj gre skoznjo vse.
#
# POZOR: to NI isto kot zeton "tocno" v `DELAY_RAMP`, ki pomeni zaokrozeno
# NIC minut. Prikaz mora prag povedati z besedo ("69 % v 5 min"), sicer sta
# v istem okvirju dve stevilki z isto besedo in razlicnim pragom -- 81 od 162
# je 50 %, ne 69 %, in bralec tega ne more spraviti skupaj.
ON_TIME_MIN = 5


def _minute(v: int) -> int:
    """Zamuda v minutah, zaokrozena tako kot `common.delayLabel()`.

    `floor(x + 0.5)` in ne `round()`: JS `Math.round` zaokrozi pol navzgor,
    Pythonov `round` pa bancno (`round(0.5) == 0`), zato bi se pri natanko
    30 s prikaz in izracun razsla.
    """
    return math.floor(v / 60 + 0.5)


def _je_pravocasna(v: int) -> bool:
    """Ali je vozjna "tocna" -- po ISTI zaokrozeni minuti, kot jo prikaz izpise."""
    return _minute(v) <= ON_TIME_MIN

def _razred_zamude(v: int) -> str:
    """Razred zamude iz ZAOKROZENE minute -- tako kot `common.delayLabel()`.

    Prej je bila meja sekundna (`v <= 60` = "tocno"). To je natanko past, ki
    jo `oznake.md` opisuje kot ze enkrat popravljeno: razred se doloca iz
    zaokrozene minute, ne iz sekund, sicer ista izpisana stevilka dobi dve
    barvi. Popravljena je bila na odjemalcu, tu pa ne -- in razlika ni majhna:
    **3 280 voznj (7,29 % od 45 015)** pade v rezo 30-60 s, kjer je streznik
    rekel "tocno" (sivo), barvna lestvica pa "1-5 min" (oranzno).

    `floor(x + 0.5)` in ne `round()`: JS `Math.round` zaokrozi pol navzgor,
    Pythonov `round` pa bancno (`round(0.5) == 0`), zato bi se razreda pri
    natanko 30 s razsla.
    """
    m = _minute(v)
    if m <= 0:
        return "točno"
    if m <= 5:
        return "1–5 min"
    if m <= 15:
        return "5–15 min"
    return "nad 15 min"


#: Strojni kljuc razreda. `_razred_zamude()` vraca **prikazno** ime ("1–5 min"),
#: ki je slovensko in ima pomisljaj -- za odjemalca, ki po njem veja logiko, je
#: to slab kljuc. Prikazna imena ostanejo, ker jih nosi `povzetek`.
_KLJUC_RAZREDA = {"točno": "tocno", "1–5 min": "1-5",
                  "5–15 min": "5-15", "nad 15 min": "nad-15"}

#: Od kod je zamuda. Iste vrednosti kot `delay_kind`, na enem mestu.
VRSTE_ZAMUDE = ("izmerjeno", "ocena", "napoved prevoznika", "običajno")


def opis_zamude(v: int | None, vrsta: str | None = None) -> dict | None:
    """Odločitev o zamudi, da je odjemalcu ni treba izpeljati samemu.

    **Zakaj to sploh obstaja.** Doslej je strežnik poslal `delay_s` v sekundah,
    brskalnik pa je sam sklepal troje: koliko je to minut, v kateri razred
    spada in ali je vožnja prezgodnja. Vsa tri pravila so bila zapisana dvakrat
    -- tu in v `common.js`. Dokler je odjemalec en, se to ne pozna; ko jih je
    več (Android), se prej ali slej razideta, razlika pa je tiha. Ta projekt
    to napako pozna: `stats.last_measured()` in `common.lastMeasured()` sta se
    razšla in prikaz je feedovo napoved kazal kot izmerjeno zamudo.

    Meja je namenoma tu: **strežnik pove, kaj stvar JE, odjemalec, kako je
    VIDETI.** Barve tu zato ni -- ta je oblikovanje in sme biti drugačna na
    telefonu kot v brskalniku. Razred, minuta in vrsta pa so pravilo.

    `min` je zaokrozen z `floor(x + 0.5)`. JS `Math.round` dela isto, Javin
    `Math.round` tudi, a `kotlin.math.round` NE -- in prav zato te vrednosti
    odjemalec ne sme racunati sam.
    """
    if v is None:
        return None
    m = _minute(v)
    return {
        "s": v,
        "min": m,
        "razred": _KLJUC_RAZREDA[_razred_zamude(v)],
        "vrsta": vrsta,
        # "-5 min" je uganka, "5 min prej" ni -- prag pa je na zaokrozeni
        # minuti in ne na sekundah, sicer ista minuta dobi dva zapisa.
        "prezgodaj": m <= -1,
        "pravocasna": _je_pravocasna(v),
    }


MAX_REALNA_ZAMUDA_S = 3 * 3600

LAST_STOP_SQL = f"""
WITH mx AS (
    SELECT r.trip_id, r.service_date, MAX(r.stop_seq) AS stop_seq
    FROM trip t JOIN run r ON r.trip_id = t.trip_id
    WHERE (:network IS NULL OR t.network = :network) AND r.service_date >= :since
    GROUP BY r.trip_id, r.service_date
),
last AS (
    SELECT mx.trip_id, mx.service_date, mx.stop_seq,
           COALESCE(r.delay_dep, r.delay_arr) AS d
    FROM mx JOIN run r ON r.trip_id = mx.trip_id
                      AND r.service_date = mx.service_date
                      AND r.stop_seq = mx.stop_seq
    WHERE COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL
      AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {MAX_REALNA_ZAMUDA_S}
)
"""


# Koliko zajetih voznj mora imeti vozjna, da sme na lestvico.
MIN_RUNS_FOR_RANK = 5


def network_stats(conn: sqlite3.Connection, days: int = 90,
                  network: str | None = "zeleznica") -> list[dict]:
    """Lestvica voženj po zamudi na koncu poti."""
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(LAST_STOP_SQL + "SELECT t.train_no, l.service_date, l.d "
                        "FROM last l JOIN trip t USING (trip_id)",
                        {"network": network, "since": since}).fetchall()
    grouped: dict[str, list[int]] = {}
    for r in rows:
        grouped.setdefault(r["train_no"], []).append(r["d"])
    # Vozjna z dvema zajemoma na vrhu lestvice ni "najslabsi vlak", ampak
    # najmanjsi vzorec. Brez tega praga je bila prva vrstica pri avtobusih
    # N6223 z mediano 654 min na DVEH voznjah.
    out = [
        {
            "train_no": k, "runs": len(v),
            "median_s": _pct(v, 0.5), "p90_s": _pct(v, 0.9), "max_s": max(v),
            "on_time_share": round(sum(1 for x in v if _je_pravocasna(x)) / len(v), 3),
        }
        for k, v in grouped.items() if len(v) >= MIN_RUNS_FOR_RANK
    ]
    out.sort(key=lambda r: (-(r["median_s"] or 0), r["train_no"]))
    return out


# Kolikokrat mora biti vozjna zajeta, da o njej sploh kaj recemo. Pri dveh
# voznjah je "mediana" samo povprecje dveh stevilk in bralec ji bo verjel bolj,
# kot zasluzi.
MIN_RUNS_FOR_TYPICAL = 3


def typical_na_izhodisce(rows: list[dict]) -> None:
    """Prvim postankom brez zgodovine prepiše `typical` naslednjega.

    Izhodišča **železniški** feed ne poroča nikoli -- izmerjeno 7. 9. 2026:
    od 716 voženj z meritvami jih ima 0 kdaj meritev na prvem postanku, pri
    avtobusih pa 14 555 od 16 671 (87 %). Tam je torej to prazen tek.
    Zgodovine tam torej ne bo, koliko dni pa zajemamo. Ker je odhodna zamuda
    ravno tista, ki jo naslednji postanek izmeri minuto zatem, jo tja
    prepišemo -- in **označimo** (`od_seq`, `od_ime`), da prikaz ne trdi, da
    je merjeno tu. Spreminja `rows` na mestu.
    """
    for i, s in enumerate(rows):
        if s.get("typical") is not None:
            return
        sosed = rows[i + 1].get("typical") if i + 1 < len(rows) else None
        if sosed is not None:
            s["typical"] = {**sosed, "od_seq": rows[i + 1]["stop_seq"],
                            "od_ime": rows[i + 1]["name"]}
            return


def typical_at_stops(conn: sqlite3.Connection, pairs: list[tuple[str, int]],
                     days: int = 90) -> dict[tuple[str, int], dict]:
    """Običajna zamuda na danih (trip_id, stop_seq) iz zajete zgodovine.

    Rabi jo prikaz za dan, ki še ni prišel: brez tega je ob vsaki vožnji
    v prihodnjem voznem redu napisano "brez podatka", čeprav o tem vlaku
    nekaj vemo -- pravkar ne tega, kar bi radi. Vrednost NI napoved za tisti
    dan; je opis preteklih voženj in prikaz jo mora tako tudi imenovati.
    """
    if not pairs:
        return {}
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    wanted = sorted(set(pairs))

    grouped: dict[tuple[str, int], list[int]] = {}
    # Ena poizvedba na svezenj, ne ena na trip: odhodna tabla velike postaje
    # ima cez cel dan sto in vec voznj, pri avtobusih pa bo tega desetkrat vec.
    # Meja spremenljivk v sqlite je 32766; 400 parov (800 vezav) je varno tudi
    # na starejsih razlicicah.
    for i in range(0, len(wanted), 400):
        chunk = wanted[i:i + 400]
        values = ",".join(["(?,?)"] * len(chunk))
        params = [x for pair in chunk for x in pair]
        rows = conn.execute(
            f"WITH want(trip_id, stop_seq) AS (VALUES {values}) "
            f"SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) AS d "
            f"FROM run r JOIN want w ON w.trip_id = r.trip_id AND w.stop_seq = r.stop_seq "
            f"WHERE r.service_date >= ? AND d IS NOT NULL",
            (*params, since),
        ).fetchall()
        for r in rows:
            grouped.setdefault((r["trip_id"], r["stop_seq"]), []).append(r["d"])

    out: dict[tuple[str, int], dict] = {}
    for key, vals in grouped.items():
        if len(vals) < MIN_RUNS_FOR_TYPICAL:
            continue
        out[key] = {
            "n": len(vals),
            "median_s": _pct(vals, 0.5),
            "p90_s": _pct(vals, 0.9),
            "on_time_share": round(sum(1 for v in vals if _je_pravocasna(v)) / len(vals), 2),
        }
    return out




def day_summary(conn: sqlite3.Connection, service_date: str,
                network: str | None = "zeleznica") -> dict:
    """Kako je mreža vozila ta dan: porazdelitev končnih zamud po vožnjah.

    Ena vožnja = en vzorec, ne en postanek. Sicer bi vlak s tridesetimi
    postanki tridesetkrat glasoval, kratki lokalni pa enkrat, in "delež
    točnih" bi meril dolžino poti namesto točnosti.
    """
    rows = conn.execute(
        "WITH last AS ("
        "  SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) AS d,"
        "         ROW_NUMBER() OVER (PARTITION BY r.trip_id ORDER BY r.stop_seq DESC) AS rn"
        "  FROM run r JOIN trip t USING (trip_id)"
        "  WHERE r.service_date = ? AND (? IS NULL OR t.network = ?)"
        ") SELECT d FROM last WHERE rn = 1 AND d IS NOT NULL",
        (service_date, network, network),
    ).fetchall()
    vals = [r["d"] for r in rows]
    if not vals:
        return {"date": service_date, "runs": 0}

    buckets = _bucket_counts(vals)
    return {
        "date": service_date,
        "runs": len(vals),
        "median_s": _pct(vals, 0.5),
        "p90_s": _pct(vals, 0.9),
        "worst_s": max(vals),
        "on_time_share": round(sum(1 for v in vals if _je_pravocasna(v)) / len(vals), 3),
        "buckets": buckets,
    }


def _bucket_counts(values: list[int]) -> dict:
    out = {"točno": 0, "1–5 min": 0, "5–15 min": 0, "nad 15 min": 0}
    for v in values:
        out[_razred_zamude(v)] += 1
    return out


def _group_stats(groups: dict[str, list[int]], min_n: int) -> list[dict]:
    out = []
    for key, vals in groups.items():
        if len(vals) < min_n:
            continue
        out.append({
            "key": key, "n": len(vals),
            "median_s": _pct(vals, 0.5), "p90_s": _pct(vals, 0.9),
            "on_time_share": round(sum(1 for v in vals if _je_pravocasna(v)) / len(vals), 3),
            "buckets": _bucket_counts(vals),
        })
    return out


# GTFS `agency_id` -> ime, kot ga clovek pozna. Surova stevilka v prikazu
# ("avtobus 1118") ne pove nikomur nicesar.
# Imena prevoznikov za STATISTIKO. Na zetonu linije pise samo "LPP" -- to je
# tisto, kar je napisano na avtobusu -- tu pa morata biti loceno.
#
# **Mestni in primestni LPP nista ista storitev in ju ni dovoljeno sesteti.**
# Izmerjeno 7. 9. 2026 na istem dnevu: mestni ima mediano zamude 0 min in
# p90 3 min, primestni 3 in 11 min. Skupna vrstica "LPP" je opisovala nobenega
# od njiju -- prav to je oblika napake, ki jo ta projekt lovi: ena beseda,
# dve stevilki.
AGENCY_NAMES = {
    "1161": "SŽ", "1123": "Arriva",
    "1119": "Nomago", "1121": "AP Murska Sobota",
    "1118": "LPP primestni",
    # Drug vir, besedni `agency_id` -- glej `config.LPP_*`.
    "lpp": "LPP mestni",
}


# Koliko voznj mora imeti skupina, da jo sploh pokazemo. Pri desetih je
# "delez tocnih" se vedno grob, a razlike med vrstami vlakov so ze vidne;
# pri treh bi risali sum.
MIN_RUNS_FOR_GROUP = 10


def breakdowns(conn: sqlite3.Connection, days: int = 90,
               network: str | None = "zeleznica") -> dict:
    """Končne zamude, razrezane po vrsti vlaka, uri odhoda in dnevu v tednu.

    Enota je **ena vožnja**, ne en postanek: sicer bi vlak s tridesetimi
    postanki glasoval tridesetkrat in "delež točnih" bi meril dolžino poti.

    Vsak rez pove tudi, koliko voženj stoji za njim. Pri devetih dneh zajema
    je dan v tednu še vedno ena ali dve vožnji na vlak in prikaz mora to
    povedati, ne pa risati krivulje čez šum.
    """
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        LAST_STOP_SQL +
        "SELECT t.train_no, t.mode, t.network, t.agency, l.service_date, l.d "
        "FROM last l JOIN trip t USING (trip_id)",
        {"network": network, "since": since},
    ).fetchall()

    by_kind: dict[str, list[int]] = {}
    by_dow: dict[str, list[int]] = {}
    by_day: dict[str, list[int]] = {}
    dow_names = ("ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja")

    for r in rows:
        d = r["d"]
        # Predpona stevilke je vrsta vlaka (LP, LPV, IC, EC, MV, RG, EN ...).
        # Pri avtobusih predpone ni -- "3G" ni vrsta -- zato skupina po
        # prevozniku. Nadomestni prevoz SZ je svoja skupina, ker to ni linija.
        if r["mode"] == "vlak":
            kind = r["train_no"].split(" ")[0] or "?"
        elif r["network"] == "zeleznica":
            kind = "nadomestni prevoz"
        else:
            kind = AGENCY_NAMES.get(r["agency"], r["agency"] or "neznan prevoznik")
        by_kind.setdefault(kind, []).append(d)
        day = date.fromisoformat(r["service_date"])
        by_dow.setdefault(dow_names[day.weekday()], []).append(d)
        by_day.setdefault(r["service_date"], []).append(d)

    # `by_stop_hour` je edini rez, ki NI po vožnji, ampak po postanku -- in to
    # je namerno. "Ura odhoda vožnje" odgovarja na drugo vprašanje, kot ga
    # potnik ima: vlak, ki odpelje ob 05:00 in nabira zamudo do 09:00, jo v
    # tistem rezu vso pripiše peti uri, ko na omrežju ni bilo še nič narobe.
    # Izmerjeno na železnici: ob 04:00 da rez po odhodu 4 min, rez po postanku
    # pa 0 min; ob 23:00 10 min proti 3 min.
    #
    # Drugi dobiček je vzorec, ki je desetkrat večji (ob 06:00 5 051 postankov
    # proti 367 vožnjam), zato nobena ura ne pade pod prag in nočna ura s
    # trinajstimi vožnjami ne določa merila cele slike.
    #
    # Tu vlak s tridesetimi postanki res "glasuje" tridesetkrat -- kar je pri
    # vprašanju "kako zamuja omrežje ob tej uri" pravilno, saj je vsak postanek
    # ena resnična priložnost za vstop. Pri ostalih rezih bi bilo narobe in
    # tam ostaja enota ena vožnja.
    #
    # Samo pretekli dnevi: v `run` je za zadnjim prevoženim postankom feedova
    # napoved, ne meritev, in ta bi današnje ure popačila.
    by_stop_hour: dict[str, list[int]] = {}
    for r in conn.execute(
        "SELECT (COALESCE(s.dep_s, s.arr_s) / 3600) % 24 AS h, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS d "
        "FROM run r JOIN trip t ON t.trip_id = r.trip_id "
        "JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
        "WHERE t.network = :network AND r.service_date >= :since "
        "  AND r.service_date < :danes "
        "  AND COALESCE(r.delay_dep, r.delay_arr) IS NOT NULL "
        f"  AND ABS(COALESCE(r.delay_dep, r.delay_arr)) <= {MAX_REALNA_ZAMUDA_S}",
        {"network": network, "since": since,
         "danes": datetime.now(TZ).date().isoformat()},
    ):
        by_stop_hour.setdefault(f"{r['h']:02d}", []).append(r["d"])

    # Sidro za lestvico najhujsih. Brez njega je "EC 211 - 46 min" videti kot
    # opis omrezja, ceprav je vrh lestvice, ki je urejena padajoce; mediana
    # vseh zeleznickih vozenj je 3 min in p90 20 min (6 472 vozenj, 4. 9.
    # 2026). Prvi, ki je to prebral narobe, sem bil jaz, in koda mi je bila
    # pred nosom -- potnik nima niti te prednosti.
    #
    # Racuna se tu, ker so `vse` prav tiste vrstice, ki jih razrezi ze berejo:
    # nobene nove poizvedbe in nobenega agregata v zahtevi.
    vse = [r["d"] for r in rows]

    return {
        "runs": len(rows),
        "days": sorted(by_day),
        "median_s": _pct(vse, 0.5),
        "p90_s": _pct(vse, 0.9),
        "on_time_share": (round(sum(1 for d in vse if _je_pravocasna(d)) / len(vse), 3)
                          if vse else None),
        "by_kind": sorted(_group_stats(by_kind, MIN_RUNS_FOR_GROUP),
                          key=lambda x: -(x["median_s"] or 0)),
        "by_stop_hour": sorted(_group_stats(by_stop_hour, MIN_RUNS_FOR_GROUP),
                               key=lambda x: x["key"]),
        "by_weekday": sorted(_group_stats(by_dow, MIN_RUNS_FOR_GROUP),
                             key=lambda x: dow_names.index(x["key"])),
        "by_day": sorted(_group_stats(by_day, 1), key=lambda x: x["key"]),
    }


def last_measured(conn: sqlite3.Connection, service_date: str,
                  trip_ids: list[str], now_s: int | None) -> dict[str, dict]:
    """Zadnji postanek vsake vozjne, ki ga je vozilo res ze prevozilo.

    Meja med meritvijo in napovedjo. Vse, kar je za njo, je feedova vrednost
    za se nedosezen postanek -- in ta je izmerjeno slaba (`kajros backtest
    --operator`: MAE 7,9 min proti 1,3 min za prenos trenutne zamude).
    Prikaz je zato ne sme kazati kot meritev.
    """
    if now_s is None or not trip_ids:
        return {}
    ids = list(dict.fromkeys(trip_ids))
    # Vsi vezani parametri morajo biti istega sloga: sqlite jih ob mesanju
    # `?` in `:ime` veze po vrstnem redu pojavitve, kar tiho zamenja vrednosti.
    sql = _LAST_MEASURED_SQL % ",".join("?" * len(ids))
    return {r["trip_id"]: dict(r)
            for r in conn.execute(sql, (service_date, *ids, now_s))}


#: Koliko dni s podobno zamudo mora biti, da jim verjamemo mediano. Merjeno:
#: pri 1 ali 2 je model slabsi od nepogojenega (MAE 2,19 in 2,11 proti 2,00),
#: pri 3 boljsi (1,99). Ista meja kot v `backtest.MIN_SAMPLES`.
MIN_PREDICT_SAMPLES = 3

#: Meje razredov zamude v sekundah. Ista delitev kot `backtest._bucket`.
DELAY_BUCKETS = (120, 600, 1800)

#: Najkrajsi postanek, ki ga vozilo se zmore; vse cez to je rezerva voznega
#: reda, ki jo zamujajoc vlak lahko porabi. Izmerjeno: mediana dejanskega
#: postanka na slovenski zeleznici je 1,0 min (43 680 postankov), LP 4219 na
#: Mostu na Soci pa se pri +16 min ni sel pod 2 min. Backtest je med 60 in
#: 180 s raven (MAE 1,932 / 1,924 / 1,928), zato velja izmerjeni prag.
MIN_DWELL_S = 120


def delay_bucket(delay_s: int) -> int:
    """Razred trenutne zamude: okrevanje pri +1 in pri +40 min ni isto."""
    return sum(1 for meja in DELAY_BUCKETS if delay_s >= meja)


def _after_slack(delay_s: int, slack_s: int) -> int:
    """Zamuda, potem ko je vozilo porabilo rezervo voznega reda.

    Porabi lahko najvec toliko, kolikor je zamuja -- in nikoli toliko, da bi
    prisel pred vozni red. Prehiter vlak ostane prehiter (pri zeleznici tega
    ni nikoli, pri avtobusih pa je vsakdanje).
    """
    return delay_s - min(max(delay_s, 0), slack_s)


#: Od kod naprej je postanek vreden razlage. Pod tem je vsak postanek eno- ali
#: dvominuten in "obicajno stoji 1 min" ni podatek, ampak sum.
DWELL_WORTH_SHOWING_S = 300

#: Koliko dni s pozno voznjo mora biti, da o obicajnem postanku sploh govorimo.
MIN_DWELL_SAMPLES = 3


def typical_dwell(conn: sqlite3.Connection, train_no: str, days: int = 90) -> dict:
    """stop_seq -> koliko ta vlak na tej postaji RES stoji, kadar zamuja.

    Model tega ne uporablja -- preverjeno je, da natancnosti ne izboljsa
    (MAE 1,911 proti 1,912 min): rezervo in historicni popravek se sestejeta,
    zato premikanje predpostavke med njima vsote ne spremeni.

    Prikazu pa **je** namenjeno. `MIN_DWELL_S` (2 min) je skrita predpostavka,
    ki je nihce ne vidi in ki zna biti mocno mimo: RG 1604 ima v Ljubljani 21
    minut postanka in model racuna z dvema, v resnici pa tam stoji sedem.
    "Vozni red tu caka 21 min, ta vlak obicajno stoji 7" je stavek, ki ga
    potnik lahko preveri.

    Steje samo dneve, ko je vlak prisel pozen (>= 5 min): takrat je postanek
    izbira in ne vozni red. Kadar pride tocen, stoji predpisano in to o
    njegovi sposobnosti nadoknaditi ne pove nicesar.
    """
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    vzorci: dict[int, list[int]] = {}
    sched: dict[int, int] = {}
    # Odhodni zamudi na dolgem postanku se ne da verjeti kar tako: feed jo
    # objavi kot nicelno napoved, se preden vlak pride, in je pogosto ne
    # popravi. Izmerjeno v zivo 29. 8.: RG 1604 je imel v Ljubljani zapisan
    # odhod 0 (torej dve minuti stanja), na Zalogu osem minut pozneje pa +5
    # (torej sedem). Oboje hkrati ne drzi.
    #
    # Zato dan steje samo, ce sta NASLEDNJA dva postanka skladna med sabo --
    # takrat vemo, s kaksno zamudo je vlak s postaje res odpeljal, in postanek
    # izracunamo iz tega, ne iz odhodne vrednosti.
    for r in conn.execute(
        "SELECT r.stop_seq, r.service_date, s.dep_s - s.arr_s AS red, "
        "       r.delay_arr, "
        "       (SELECT COALESCE(n.delay_arr, n.delay_dep) FROM run n "
        "         WHERE n.trip_id = r.trip_id AND n.service_date = r.service_date "
        "           AND n.stop_seq = r.stop_seq + 1) AS naslednji, "
        "       (SELECT COALESCE(n.delay_arr, n.delay_dep) FROM run n "
        "         WHERE n.trip_id = r.trip_id AND n.service_date = r.service_date "
        "           AND n.stop_seq = r.stop_seq + 2) AS naslednji2 "
        "FROM run r JOIN trip t USING (trip_id) "
        "JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
        "WHERE t.train_no = ? AND r.service_date >= ? "
        "  AND r.delay_arr IS NOT NULL AND r.delay_arr >= 300 "
        "  AND s.arr_s IS NOT NULL AND s.dep_s IS NOT NULL "
        "  AND s.dep_s - s.arr_s >= ?",
        (train_no, since, DWELL_WORTH_SHOWING_S),
    ):
        a, b = r["naslednji"], r["naslednji2"]
        if a is None or b is None or abs(a - b) > 120:
            continue                       # zaporedje si ni skladno -- dan izpustimo
        vzorci.setdefault(r["stop_seq"], []).append(r["red"] + a - r["delay_arr"])
        sched[r["stop_seq"]] = r["red"]
    return {
        seq: {"sched_dwell_s": sched[seq],
              "typical_dwell_s": round(statistics.median(v)),
              "n_samples": len(v)}
        for seq, v in vzorci.items() if len(v) >= MIN_DWELL_SAMPLES
    }


def dwell_at(slack_list, stop_seq: int) -> int:
    """Voznoredni postanek na tem postanku, iz tabele `_slack_ahead`.

    Tam so samo postanki nad `MIN_DWELL_S`; kar ni v seznamu, je kratko in za
    presojo "vlak se stoji" nezanimivo.
    """
    for seq, w in slack_list or ():
        if seq == stop_seq:
            return w + MIN_DWELL_S
    return 0


def _slack_ahead(conn: sqlite3.Connection, trip_ids: list[str]) -> dict:
    """trip_id -> [(stop_seq, rezerva)] za postanke, ki rezervo sploh imajo.

    Vrne samo postanke z zadrzevanjem nad `MIN_DWELL_S` -- teh je na vsej
    slovenski zeleznici 406 od 10 019, zato je seznam kratek in vsota po njem
    poceni. Postanki brez rezerve za racun nic ne pomenijo.
    """
    ids = list(dict.fromkeys(trip_ids))
    out: dict[str, list] = {}
    for i in range(0, len(ids), 400):
        kos = ids[i:i + 400]
        marks = ",".join("?" * len(kos))
        for r in conn.execute(
            f"SELECT trip_id, stop_seq, dep_s - arr_s AS w FROM sched "
            f"WHERE trip_id IN ({marks}) AND arr_s IS NOT NULL AND dep_s IS NOT NULL "
            f"  AND dep_s - arr_s > ? ORDER BY trip_id, stop_seq",
            (*kos, MIN_DWELL_S),
        ):
            out.setdefault(r["trip_id"], []).append((r["stop_seq"], r["w"] - MIN_DWELL_S))
    return out


#: Prevoznikova napoved za se nedosezen postanek je izmerjeno slaba -- MAE
#: 8,25 min proti 1,37 min za naso oceno -- a napaka je **enosmerna**. Merjeno
#: na 12 026 primerih z znano prevoznikovo vrednostjo:
#:
#:   napove VEC kot mi (10 % primerov):  prevoznik MAE 0,21 min, mi 2,66 min
#:   napove manj ali enako   (90 %):     prevoznik MAE 9,17 min, mi 1,22 min
#:
#: Nizka vrednost je namrec privzeta nicla za postanek, ki ga feed se ni
#: razrešil; visoka pa pomeni, da prevoznik VE nekaj, cesar iz zgodovine ni
#: mogoce vedeti -- okvaro, zaporo, krizanje. Zato: `max(nasa ocena, njegova)`.
#: Nikoli navzdol, vedno navzgor.
def _with_operator(ocena: int, prevoznik: int | None) -> int:
    return ocena if prevoznik is None else max(ocena, prevoznik)


#: Postanek, od katerega naprej velja, da vozilo na postaji "stoji dlje casa".
STANDING_DWELL_S = 300


def _operator_is_stale(prevoznik: int | None, arr_i: int | None, dep_i: int,
                       dwell_i: int) -> bool:
    """Je prevoznikova vrednost samo prenos zamude z ze doseZene postaje?

    Izjema od pravila "prevoznik navzgor". Dokler vlak stoji na postaji z
    dolgim postankom, prevoznik za naprej objavi zamudo, s katero je vlak
    PRISEL -- ne ve se, koliko postanka bo skrajsal. Ko odpelje, jo popravi.

    Ujeto v zivo 29. 8.: RG 1604 je stal v Ljubljani (21 min postanka, prisel
    +19). Ob 23:04 je prevoznik za Ljubljano Zalog objavil +19, ob 23:12 pa
    to popravil na +5. Vlak je prisel +5.

    Merjeno na 63 967 primerih (vsak poll, ne le eden na nalogo): podpis se
    pojavi 926-krat in tam je pravilo "vzemi vecjo" **slabse** -- MAE 4,19
    proti 3,31 min, delez v petih minutah 71,2 proti 81,4 %. Skupno izpustitev
    teh primerov pomeni 1,189 -> 1,177 min in 94,27 -> 94,42 %.
    """
    return (prevoznik is not None and arr_i is not None
            and dwell_i >= STANDING_DWELL_S
            and abs(prevoznik - arr_i) <= 60
            and prevoznik > dep_i + 60)


#: Najvecji ostanek, ki mu se verjamemo -- v sekundah in kot delez trenutne
#: zamude, kar je vecje. Mediana ostanka je pri 69 % napovedi v potnikovem
#: oknu narejena iz ENEGA samega dne (izmerjeno na 8 214 nalogah sence), in en
#: dan zna biti poljubno velik. Brez te meje je rep teh vrednosti gnal napako:
#: pri devetih do desetih postankih naprej je bil model slabsi od golega
#: prenosa zamude.
#:
#: Delez pusti velikim zamudam prostor -- vlak s +25 min lahko izgubi se
#: deset, tocen pa ne. Izmerjeno na nalogah sence (`scripts/preizkusi_model.py`):
#:
#:   meja                MAE    v 5 min   podcenjenih   9-10 postankov
#:   brez (prej)        3,59 min  84,7 %      7,2 %        4,30 min
#:   600 s              3,15      84,7        8,4          2,96
#:   **600 s + 1x**     **3,13**  **84,9**    **8,1**      **2,96**
#:   900 s + 1x         3,16      84,8        7,7          2,99
OMEJI_OSTANEK_S = 600
OMEJI_OSTANEK_DELEZ = 1.0


def _omejen_ostanek(ostanek: float, current_delay_s: int,
                    omeji_s: int | None = None,
                    omeji_delez: float | None = None) -> float:
    """Ostanek, omejen na to, kolikor mu smemo verjeti.

    Mediana enega dneva ni mediana. Meja je `max(OMEJI_OSTANEK_S, delez x
    trenutna zamuda)` -- absolutna zato, da tocnemu vozilu ne pripisemo
    velike spremembe, sorazmerna pa zato, da mocno zamujajocemu ne odrezemo
    prave.
    """
    meja = max(omeji_s if omeji_s is not None else OMEJI_OSTANEK_S,
               abs(current_delay_s) * (omeji_delez if omeji_delez is not None
                                       else OMEJI_OSTANEK_DELEZ))
    return max(-meja, min(meja, ostanek))


def predict(conn: sqlite3.Connection, train_no: str, stop_seq: int,
            current_delay_s: int, days: int = 90,
            exclude_date: str | None = None,
            service_date: str | None = None,
            trip_id: str | None = None,
            omeji_s: int | None = None,
            omeji_delez: float | None = None) -> list[dict]:
    """Napoved zamude na nadaljnjih postajah.

    Osnovni model: zamuda se prenaša naprej, popravljena za historično mediano
    spremembe zamude na tem odseku pri tej vožnji. Enostavno, a je pri vlakih
    presenetljivo trdna izhodiščna točka -- dokler ne nabereš nekaj mesecev
    podatkov, kompleksnejši model nima česa izkoristiti.

    **Ključ je vožnja, ne številka.** Pri železnici je to isto (0 od 663
    številk z meritvami ima več kot eno vožnjo), pri avtobusu pa nikakor:
    LPP linija 25 ima 217 voženj obeh smeri, in ker se model uči po
    `stop_seq`, bi se „postanek 2" naučil mediane spremembe med dvema
    krajema, ki nista sosednja in nista niti v isti smeri.
    """
    trip_id = resolve_trip(conn, train_no, service_date, trip_id)
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    # Dan, ki ga prikazujemo, ne sme biti v svoji lastni ucni mnozici. Pri
    # tekoci voznji naprej po progi meritev tako ali tako ni, pri ogledu
    # koncanega dne pa bi model deloma napovedoval iz odgovora.
    rows = conn.execute(
        f"SELECT r.service_date, r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) AS d "
        f"FROM run r JOIN trip t USING (trip_id) "
        f"WHERE {'r.trip_id = ?' if trip_id else 't.train_no = ?'} "
        f"  AND r.service_date >= ? AND d IS NOT NULL "
        f"  AND (? IS NULL OR r.service_date <> ?) "
        f"ORDER BY r.service_date, r.stop_seq",
        (trip_id or train_no, since, exclude_date, exclude_date),
    ).fetchall()

    by_day: dict[str, dict[int, int]] = {}
    for r in rows:
        by_day.setdefault(r["service_date"], {})[r["stop_seq"]] = r["d"]

    stops = timetable(conn, train_no, service_date, trip_id)
    names = {t["stop_seq"]: t["name"] for t in stops}
    # Kaj o teh postankih pravi feed prav zdaj. Za se nedosezen postanek je to
    # prevoznikova napoved -- uporabimo jo samo navzgor (glej `_with_operator`).
    feed: dict[int, int] = {}
    arr_i = None
    if service_date:
        kje = "r.trip_id = ?" if trip_id else "t.train_no = ?"
        kdo = trip_id or train_no
        feed = {r["stop_seq"]: r["d"] for r in conn.execute(
            f"SELECT r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) AS d "
            f"FROM run r JOIN trip t USING (trip_id) "
            f"WHERE {kje} AND r.service_date = ? AND r.stop_seq > ? AND d IS NOT NULL",
            (kdo, service_date, stop_seq))}
        row = conn.execute(
            f"SELECT r.delay_arr FROM run r JOIN trip t USING (trip_id) "
            f"WHERE {kje} AND r.service_date = ? AND r.stop_seq = ?",
            (kdo, service_date, stop_seq)).fetchone()
        arr_i = row["delay_arr"] if row else None
    # Rezerva voznega reda: presezek postanka nad najkrajsim, ki ga vozilo se
    # zmore. To je edini vhod v napoved, ki ni statistika -- rezerva je znana
    # vnaprej in obstaja ne glede na to, ali smo jo kdaj videli porabljeno.
    dwell = {t["stop_seq"]: max(0, (t["dep_s"] or 0) - (t["arr_s"] or 0) - MIN_DWELL_S)
             for t in stops if t["arr_s"] is not None and t["dep_s"] is not None}
    # Postanek na izhodiscu -- za presojo, ali vlak tam se stoji.
    dwell_i = next((( t["dep_s"] or 0) - (t["arr_s"] or 0) for t in stops
                    if t["stop_seq"] == stop_seq
                    and t["arr_s"] is not None and t["dep_s"] is not None), 0)
    razred = delay_bucket(current_delay_s)
    out = []
    slack = 0
    for seq in sorted(s for s in names if s > stop_seq):
        prej = _after_slack(current_delay_s, slack)
        slack += dwell.get(seq, 0)
        osnova = _after_slack(current_delay_s, slack)
        # Koliko rezerve se porabi PRAV TU. Prikaz iz tega nariše padec na
        # postaji namesto na odseku -- padec se zgodi med prihodom in odhodom.
        tu = prej - osnova
        # Ostanek: kar se je zgodilo POLEG rezerve -- zamude, ki nastanejo, in
        # rezerva, ki je v resnici ni bilo. Loceno po razredu zamude, ker
        # postanek vlaku z 11 minutami vzame dve, tocnemu pa nic.
        pari = [(day[stop_seq], day[seq] - _after_slack(day[stop_seq], slack))
                for day in by_day.values()
                if stop_seq in day and seq in day]
        podobni = [r for d0, r in pari if delay_bucket(d0) == razred]
        ostanki = podobni if len(podobni) >= MIN_PREDICT_SAMPLES else [r for _, r in pari]
        # Mediana iz enega dneva ni mediana. Krcenje jo potegne proti nic
        # sorazmerno s tem, koliko dni stoji za njo -- brez praga, ki bi pri
        # dveh dneh delal skok.
        nasa = osnova + (round(_omejen_ostanek(
            statistics.median(ostanki), current_delay_s, omeji_s, omeji_delez))
            if ostanki else 0)
        prevoznik = feed.get(seq)
        if _operator_is_stale(prevoznik, arr_i, current_delay_s, dwell_i):
            prevoznik = None            # samo prenos zamude, ne napoved
        out.append({
            "stop_seq": seq,
            "name": names[seq],
            "n_samples": len(ostanki),
            "same_class": len(podobni) >= MIN_PREDICT_SAMPLES,
            "slack_s": slack,
            "slack_here_s": tu,
            "own_delay_s": nasa,
            "operator_delay_s": prevoznik,
            "from_operator": prevoznik is not None and prevoznik > nasa,
            "predicted_delay_s": _with_operator(nasa, prevoznik),
            "p90_delay_s": (_with_operator(osnova + round(_pct(ostanki, 0.9)), prevoznik)
                            if ostanki else None),
            "basis": ("prevoznik ve več" if prevoznik is not None and prevoznik > nasa
                      else "rezerva + historicni ostanek" if ostanki
                      else "rezerva voznega reda"),
        })
    return out


# ---------------------------------------------------------------- povezave A -> B

_CONNECTIONS_SQL = """
SELECT t.trip_id, t.train_no, t.headsign, t.mode, t.agency, t.network,
       sa.stop_seq AS from_seq, COALESCE(sa.dep_s, sa.arr_s) AS dep_s,
       sb.stop_seq AS to_seq,   COALESCE(sb.arr_s, sb.dep_s) AS arr_s,
       COALESCE(ra.delay_dep, ra.delay_arr) AS from_delay_s,
       COALESCE(rb.delay_arr, rb.delay_dep) AS to_delay_s
FROM trip t
JOIN sched sa   ON sa.trip_id = t.trip_id
JOIN station za ON za.stop_id = sa.stop_id AND za.name = :a
JOIN sched sb   ON sb.trip_id = t.trip_id AND sb.stop_seq > sa.stop_seq
JOIN station zb ON zb.stop_id = sb.stop_id AND zb.name = :b
JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = :day
                   AND (:network IS NULL OR t.network = :network)
LEFT JOIN run ra ON ra.trip_id = t.trip_id AND ra.service_date = :day AND ra.stop_seq = sa.stop_seq
LEFT JOIN run rb ON rb.trip_id = t.trip_id AND rb.service_date = :day AND rb.stop_seq = sb.stop_seq
ORDER BY dep_s
"""

# Zadnja postaja vsake voznje, katere (voznored + zamuda) cas je ze minil.
# Ista logika kot pri /api/live: kar je naprej, je napoved, ne meritev.
_LAST_MEASURED_SQL = """
WITH t AS (
    SELECT r.trip_id, r.stop_seq, s.stop_id, r.delay_arr, r.feed_ts,
           COALESCE(r.delay_dep, r.delay_arr) AS delay_s,
           COALESCE(s.dep_s, s.arr_s) AS t_s
    FROM run r
    JOIN sched s ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq
    WHERE r.service_date = ? AND r.trip_id IN (%s)
),
-- Isto varovalo kot v /api/live: nicla za se nedosezen postanek ne sme
-- pomeniti, da je vlak tam ze bil.
ranked AS (
    SELECT t.*, MAX(COALESCE(t.delay_s, 0)) OVER (
               PARTITION BY t.trip_id ORDER BY t.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_max,
           MAX(t.feed_ts) OVER (
               PARTITION BY t.trip_id ORDER BY t.stop_seq
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_ts
    FROM t
),
passed AS (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY stop_seq DESC) AS rn
    FROM ranked r
    WHERE r.t_s + COALESCE(r.delay_s, 0) <= ?
      AND NOT (COALESCE(r.delay_s, 0) = 0 AND r.prev_max >= 300)
      -- Ostanek, ki ga feed ni vec osvezil, ni prevozen postanek: meja med
      -- meritvijo in napovedjo bi sicer padla nanj. Glej oznaci_zastarele().
      AND NOT (r.feed_ts IS NOT NULL AND r.prev_ts IS NOT NULL AND r.feed_ts < r.prev_ts)
)
SELECT p.trip_id, p.stop_seq, p.delay_s, p.delay_arr, st.name
FROM passed p JOIN station st ON st.stop_id = p.stop_id
WHERE p.rn = 1
"""


def estimate_at(conn: sqlite3.Connection, train_no: str, trip_id: str | None,
                from_stop_seq: int, current_delay_s: int, target_seq: int,
                service_date: str | None = None) -> int | None:
    """Ocena zamude na `target_seq` po ISTEM modelu kot okno vožnje.

    Iskalnik zvez in odhodna tabla sta prej računala samo prenos zamude minus
    rezervo voznega reda. Okno vožnje pa isti postanek računa s `predict()`,
    torej z rezervo **in** historičnim ostankom -- in ta je izmerjeno boljši
    (`kajros backtest`: prenos 2,94 min MAE in 82,7 % v petih minutah,
    rezerva + razred 1,92 min in 91,0 %).

    Posledica razhajanja je bila vidna: RG 318 je 1. 9. ob 06:46 v iskalniku
    za Ljubljano Polje pisal **+11 min**, v oknu iste vožnje pa **+24**, in
    LPV 2250 +3 proti +18. Dve številki o istem vlaku na isti postaji, obe
    označeni „ocena".

    Vrne `None`, kadar modela ni mogoče uporabiti (postanka ni v napovedi);
    klicatelj takrat ostane pri prenosu z rezervo.
    """
    for x in predict(conn, train_no, from_stop_seq, current_delay_s,
                     exclude_date=service_date, service_date=service_date,
                     trip_id=trip_id):
        if x["stop_seq"] == target_seq:
            return x["predicted_delay_s"]
    return None


def connections(conn: sqlite3.Connection, from_name: str, to_name: str,
                service_date: str, now_s: int | None = None,
                network: str | None = None) -> list[dict]:
    """Vse vožnje, ki na dani dan peljejo od `from_name` do `to_name`.

    Relacija ni v številki vlaka in ne v `route_id` -- ta je v tem feedu
    ena-na-ena s tripom. Edini vir je zaporedje postaj: izhodišče mora imeti
    manjši `stop_seq` od cilja.
    """
    rows = conn.execute(_CONNECTIONS_SQL,
                        {"a": from_name, "b": to_name, "day": service_date,
                         "network": network}).fetchall()

    # Vlak lahko isto postajo obišče dvakrat (obrat) -- obdrži najzgodnejši par.
    best: dict[str, dict] = {}
    for r in rows:
        d = dict(r)
        prev = best.get(d["trip_id"])
        if prev is None or d["dep_s"] < prev["dep_s"]:
            best[d["trip_id"]] = d
    out = sorted(best.values(), key=lambda d: d["dep_s"])
    if not out:
        return []

    # Zadnja meritev vsake voznje -- za vlake, ki so ze na poti.
    last = last_measured(conn, service_date, [d["trip_id"] for d in out], now_s)
    slack = _slack_ahead(conn, [d["trip_id"] for d in out])

    for d in out:
        d["stops_between"] = d["to_seq"] - d["from_seq"]
        d["sched_dep"] = _abs_time(service_date, d["dep_s"])
        d["sched_arr"] = _abs_time(service_date, d["arr_s"])
        d["duration_s"] = d["arr_s"] - d["dep_s"]

        lm = last.get(d["trip_id"])
        # Kaj potnik res rabi: zamudo na SVOJI postaji, ce je ze izmerjena;
        # sicer zadnjo znano zamudo in kje je bila izmerjena.
        if lm and lm["stop_seq"] >= d["from_seq"]:
            d["delay_s"] = d["from_delay_s"] if d["from_delay_s"] is not None else lm["delay_s"]
            d["delay_at"] = from_name if d["from_delay_s"] is not None else lm["name"]
            d["delay_kind"] = "izmerjeno"
        elif lm:
            # Vozilo je se pred izhodiscno postajo potnika: to je prenos
            # njegove trenutne zamude, torej OCENA za to postajo. Ista beseda
            # kot na odhodni tabli -- dve imeni za isto stvar na dveh straneh
            # iste aplikacije sta dve razlicni stvari za bralca.
            #
            # Prej rezerva voznega reda, isto kot na tabli: vlak, ki stoji na
            # vmesni postaji dvajset minut, do potnika zamude ne prinese.
            vrsta = slack.get(d["trip_id"], ())
            rez = sum(w for seq, w in vrsta
                      if lm["stop_seq"] < seq <= d["from_seq"])
            # Prevoznikova vrednost samo navzgor: nizka je nerazresena nicla,
            # visoka pa pomeni, da ve nekaj, cesar iz zgodovine ni mogoce vedeti.
            # Izjema: dokler vlak stoji na dolgem postanku, je njegova vrednost
            # le prenos prihodne zamude (glej `_operator_is_stale`).
            prev = d["from_delay_s"]
            if _operator_is_stale(prev, lm["delay_arr"], lm["delay_s"],
                                  dwell_at(vrsta, lm["stop_seq"])):
                prev = None
            ocena = estimate_at(conn, d["train_no"], d["trip_id"], lm["stop_seq"],
                                lm["delay_s"], d["from_seq"], service_date)
            d["delay_s"] = (ocena if ocena is not None
                            else _with_operator(_after_slack(lm["delay_s"], rez), prev))
            d["delay_at"] = lm["name"]
            d["delay_kind"] = "ocena"
        elif d["from_delay_s"] is not None:
            # Feed ima vrednost, a cas se ni minil -- to je napoved prevoznika.
            d["delay_s"] = d["from_delay_s"]
            d["delay_at"] = from_name
            d["delay_kind"] = "napoved prevoznika"
        else:
            d["delay_s"] = None
            d["delay_at"] = None
            d["delay_kind"] = "brez podatka"

        d["expected_dep"] = (_abs_time(service_date, d["dep_s"] + d["delay_s"])
                             if d["delay_s"] is not None else None)
        # Odlocitev o zamudi gre z vrstico vred -- glej `opis_zamude()`.
        d["zamuda"] = opis_zamude(d["delay_s"], d["delay_kind"])
        # Kaj je o tej postaji rekel feed. Kadar je vozilo se pred njo, je to
        # napoved prevoznika in prikaz je ne uporablja -- a je tudi ne skriva.
        d["feed_delay_s"] = d["from_delay_s"]
        d.pop("from_delay_s", None)
        d.pop("to_delay_s", None)

    # Obicajna zamuda iz zgodovine. Za dan, ki se ni prisel, je to edino, kar
    # o vlaku sploh vemo -- brez tega je vsaka vrstica "brez podatka".
    typ = typical_at_stops(conn, [(d["trip_id"], d["from_seq"]) for d in out]
                                 + [(d["trip_id"], d["to_seq"]) for d in out])
    for d in out:
        d["typical_dep"] = typ.get((d["trip_id"], d["from_seq"]))
        d["typical_arr"] = typ.get((d["trip_id"], d["to_seq"]))
    return out


# ---------------------------------------------------------------- vreme ob vožnji

def run_weather(conn: sqlite3.Connection, train_no: str, service_date: str,
                trip_id: str | None = None) -> list[dict]:
    """Vreme na vsaki postaji te vožnje.

    Ura se vzame po dejanskem času (vozni red + zamuda), kadar ga imamo, sicer
    po voznorednem -- vreme mora opisovati trenutek, ko je vlak tam, ne ure
    odhoda z izhodišča. Vrednost je modelska za celico 8 x 8 km, ne meritev na
    peronu, in prikaz mora to povedati.
    """
    from . import weather as weather_mod

    trip_id = resolve_trip(conn, train_no, service_date, trip_id)
    if not trip_id:
        return []
    rows = conn.execute(
        "SELECT s.stop_seq, st.name, st.lat, st.lon, "
        "       COALESCE(s.dep_s, s.arr_s) AS t_s, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS delay_s "
        "FROM sched s JOIN station st ON st.stop_id = s.stop_id "
        "LEFT JOIN run r ON r.trip_id = s.trip_id AND r.stop_seq = s.stop_seq "
        "                AND r.service_date = ? "
        "WHERE s.trip_id = ? ORDER BY s.stop_seq",
        (service_date, trip_id),
    ).fetchall()
    if not rows:
        return []

    base = datetime.combine(date.fromisoformat(service_date), datetime.min.time(), tzinfo=TZ)
    wanted = []
    for r in rows:
        if r["t_s"] is None:
            wanted.append(None)
            continue
        when = base + timedelta(seconds=r["t_s"] + (r["delay_s"] or 0))
        hour_ts = int(when.timestamp()) // 3600 * 3600
        wanted.append((weather_mod.cell_key(r["lat"], r["lon"]), hour_ts))

    keys = {k for k in wanted if k}
    found: dict[tuple, dict] = {}
    if keys:
        # Ena poizvedba za vse pare -- po postajah bi jih bilo do 30 na vožnjo.
        clause = " OR ".join(["(cell = ? AND hour_ts = ?)"] * len(keys))
        params = [v for pair in keys for v in pair]
        for w in conn.execute(f"SELECT * FROM weather WHERE {clause}", params):
            found[(w["cell"], w["hour_ts"])] = dict(w)

    out = []
    for r, key in zip(rows, wanted):
        w = found.get(key) if key else None
        sev = weather_mod.severity(w) if w else None
        out.append({
            "stop_seq": r["stop_seq"],
            "name": r["name"],
            "severity": sev["score"] if sev else None,
            "severity_label": sev["label"] if sev else None,
            "severity_parts": sev["parts"] if sev else None,
            "at": _abs_time(service_date, (r["t_s"] or 0) + (r["delay_s"] or 0))
                 if r["t_s"] is not None else None,
            "cell": key[0] if key else None,
            "temp_c": w["temp_c"] if w else None,
            "precip_mm": w["precip_mm"] if w else None,
            "snowfall_cm": w["snowfall_cm"] if w else None,
            "wind_gust_kmh": w["wind_gust_kmh"] if w else None,
            "code": w["code"] if w else None,
            "source": w["source"] if w else None,
        })
    return out


# ---------------------------------------------------------------- dnevni povzetek
#
# Statistika cez vso zgodovino je agregat, ki mora prebrati vsako meritev v
# oknu. Pri devetih dneh zajema je to 70 000 vrstic in traja 40 ms; pri letu
# dni vseh prevoznikov je 12 milijonov vrstic in traja sekunde. Izmerjeno na
# sinteticni bazi z letom zajema (52 M vrstic `run`, 5,9 GB):
#
#     breakdowns 90 dni, avtobusi ..... 17,3 s
#     breakdowns 90 dni, vlaki .........  3,0 s
#
# Racunati to ob vsakem obisku strani ni smiselno, ker se odgovor med obiskoma
# skoraj ne spremeni: en nov dan je 1/90 vzorca. Zato se izracuna enkrat na dan,
# shrani cel in postreze iz baze. Stran ob tem **pove cas izracuna** -- brez
# njega bralec ne loci vceraj izracunane stevilke od zdajsnje.
#
# Dvakratno racunanje istega ob hkratnih zahtevah prepreci `_SUMMARY_LOCK`:
# brez njega dva obiska ob praznem predpomnilniku pozeneta dva 17-sekundna
# agregata na isti bazi.

SUMMARY_BUILDERS = {
    "network_stats": lambda conn, days, network: {
        "rows": network_stats(conn, days, network)},
    "breakdowns": breakdowns,
}

# Katera okna vzdrzujemo. Sirse okno ni drazje od ozjega toliko, kolikor je
# sirse -- glavnina stroska je pregled `run` -- zato jih ni smiselno imeti vec.
SUMMARY_WINDOWS = (90,)
SUMMARY_NETWORKS = ("zeleznica", "avtobus")

# Kdaj velja predpomnjeni odgovor za prestar, ce dnevno opravilo ni teklo.
SUMMARY_MAX_AGE_S = 36 * 3600

#: Oblika IN pomen shranjenega povzetka. **Povecaj ob vsaki spremembi polj
#: ali njihovega izracuna**, ki ju vraca `breakdowns()` ali `network_stats()`.
#: Ni dovolj misliti na obliko: v3 je nastal, ker so se spremenile meje
#: razredov (`_razred_zamude`), oblika pa je ostala ista -- shranjeni
#: stevci bi bili do 36 ur tihi ostanek starega pravila.
#:
#: Brez tega je stara OBLIKA enako skodljiva kot star podatek, le tise:
#: predpomnilnik se do 36 ur strezel payload brez novega polja, stran ga je
#: izpustila in videti je bilo, kot da sprememba ne dela. Zgodilo se je pri
#: dodajanju `median_s` (4. 9. 2026) -- API je vrnil `cached=true` in polja
#: ni bilo, cetudi je bila koda pravilna.
SUMMARY_VERSION = 4

_SUMMARY_LOCK = threading.Lock()


def _summary_row(conn: sqlite3.Connection, kind: str, network: str, days: int):
    return conn.execute(
        "SELECT computed_at, through, took_ms, runs, payload FROM povzetek "
        "WHERE kind = ? AND network = ? AND days = ?", (kind, network, days)
    ).fetchone()


def summary_build(conn: sqlite3.Connection, kind: str, network: str,
                  days: int = 90) -> dict:
    """Izracunaj razrez in ga shrani. Vrne shranjeni odgovor."""
    builder = SUMMARY_BUILDERS[kind]
    started = time.monotonic()
    payload = {**builder(conn, days, network), "v": SUMMARY_VERSION}
    took_ms = int((time.monotonic() - started) * 1000)
    computed_at = datetime.now(TZ).isoformat(timespec="seconds")
    days_seen = payload.get("days") or []
    through = days_seen[-1] if days_seen else None
    runs = payload.get("runs")
    if runs is None:
        runs = sum(r["runs"] for r in payload.get("rows", []))
    conn.execute(
        "INSERT INTO povzetek (kind, network, days, computed_at, through,"
        "                      took_ms, runs, payload) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(kind, network, days) DO UPDATE SET "
        "  computed_at = excluded.computed_at, through = excluded.through,"
        "  took_ms = excluded.took_ms, runs = excluded.runs,"
        "  payload = excluded.payload",
        (kind, network, days, computed_at, through, took_ms, runs,
         json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    return {**payload, "runs": runs, "computed_at": computed_at,
            "through": through, "took_ms": took_ms, "cached": False}


def summary_get(conn: sqlite3.Connection, kind: str, network: str, days: int = 90,
                max_age_s: int = SUMMARY_MAX_AGE_S) -> dict:
    """Predpomnjeni razrez; ce ga ni ali je prestar, ga izracuna zdaj.

    Sveze racunanje v zahtevi je zasilni izhod, ne pot: prvi obisk po namestitvi
    in dan, ko dnevno opravilo ni teklo. Sicer to opravi ozadnja nit.
    """
    row = _summary_row(conn, kind, network, days)
    if row is not None:
        age = (datetime.now(TZ) - datetime.fromisoformat(row["computed_at"])).total_seconds()
        shranjeno = json.loads(row["payload"])
        if age <= max_age_s and shranjeno.get("v") == SUMMARY_VERSION:
            return {**shranjeno, "runs": row["runs"],
                    "computed_at": row["computed_at"], "through": row["through"],
                    "took_ms": row["took_ms"], "cached": True}

    with _SUMMARY_LOCK:
        # Med cakanjem na kljucavnico ga je morda ze izracunal nekdo drug.
        again = _summary_row(conn, kind, network, days)
        if (again is not None
                and again["computed_at"] != (row["computed_at"] if row else None)
                and json.loads(again["payload"]).get("v") == SUMMARY_VERSION):
            return {**json.loads(again["payload"]), "runs": again["runs"],
                    "computed_at": again["computed_at"], "through": again["through"],
                    "took_ms": again["took_ms"], "cached": True}
        return summary_build(conn, kind, network, days)


def refresh_summaries(conn: sqlite3.Connection, windows=SUMMARY_WINDOWS,
                      networks=SUMMARY_NETWORKS) -> list[dict]:
    """Znova izracunaj vse razreze. To pozene dnevno opravilo in `kajros summarize`."""
    out = []
    with _SUMMARY_LOCK:
        for network in networks:
            for days in windows:
                for kind in SUMMARY_BUILDERS:
                    got = summary_build(conn, kind, network, days)
                    out.append({"kind": kind, "network": network, "days": days,
                                "runs": got.get("runs"), "took_ms": got["took_ms"]})
    return out


# ---------------------------------------------------------------- veriga vozila

#: Koliko casa je GPS lega se uporabna. Feed osvezuje na 30 s; cetrt ure
#: pomeni, da je vozilo od takrat prevozilo kilometre in "je pri X" ne drzi.
VEHICLE_STALE_S = 15 * 60

_BLOCK_SQL = """
SELECT t.trip_id, t.train_no, t.headsign, t.start_s, t.end_s
FROM trip t
JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = :date
WHERE t.block_id = :block AND t.trip_id <> :self AND %s
ORDER BY %s
LIMIT 1
"""


def _block_neighbour(conn: sqlite3.Connection, block_id: str, service_date: str,
                     trip_id: str, at_s: int, back: bool) -> dict | None:
    """Sosednja voznja istega vozila: prejsnja (back) ali naslednja."""
    if at_s is None:
        return None
    where = "t.end_s <= :at" if back else "t.start_s >= :at"
    order = "t.end_s DESC" if back else "t.start_s ASC"
    row = conn.execute(_BLOCK_SQL % (where, order),
                       {"date": service_date, "block": block_id,
                        "self": trip_id, "at": at_s}).fetchone()
    return dict(row) if row else None


def vehicle_chain(conn: sqlite3.Connection, train_no: str, service_date: str,
                  trip_id: str | None = None, now_ts: int | None = None,
                  now_s: int | None = None) -> dict:
    """Kje je vozilo te voznje in kam gre potem -- po GTFS `block_id`.

    Odgovarja na vprasanje, ki ga zamuda ne more: **kje je moj avtobus, ki se
    se ni zacel**. Vozilo je takrat na prejsnji voznji v bloku in tam ima GPS
    lego, ker avtobusi lego posiljajo (vlaki ne). Ob 20:22 je 13 od 20 voznj,
    ki so se zacenjale v naslednji uri, imelo prejsnjo voznjo v bloku, in 9 od
    teh svezo lego.

    **Zamude prejsnje voznje NE prenasamo naprej in prikaz je ne sme sesteti
    z odhodom.** Izmerjeno na 195 parih zajetih voznj: prenos zamude na
    naslednjo voznjo ima MAE 4,53 min, "predpostavi tocno" pa 2,29 min --
    torej je slabsi od tega, da o prejsnji voznji ne vemo nic. Vozilo zamudo
    med voznjama nadoknadi: kadar prejsnja zamuja >= 5 min (mediana 12 min) in
    ima vmes 15-60 min postanka, se na naslednjo prenese 11 %. To je fizikalno
    razumljivo -- postanek med voznjama je rezerva prav za to.

    Zato je prejsnja voznja tu **dejstvo o vozilu**, ne napoved: "vozilo je
    zdaj pri Vicu, na prejsnji voznji zamuja 12 min". Potnik iz tega vidi, da
    avtobus obstaja in se blizja; sklep o svojem odhodu naredi sam.

    Vlaki tu ne dobijo nicesar: `block_id` ima v celotnem GTFS samo avtobusni
    del in tudi tam le tretjina voznj.
    """
    tid = resolve_trip(conn, train_no, service_date, trip_id)
    if not tid:
        return {}
    me = conn.execute(
        "SELECT block_id, start_s, end_s FROM trip WHERE trip_id = ?", (tid,)
    ).fetchone()
    if not me or not me["block_id"]:
        return {}

    prev = _block_neighbour(conn, me["block_id"], service_date, tid,
                            me["start_s"], back=True)
    nxt = _block_neighbour(conn, me["block_id"], service_date, tid,
                           me["end_s"], back=False)

    if prev:
        prev["layover_s"] = (me["start_s"] - prev["end_s"]
                             if me["start_s"] is not None else None)
        _add_live_state(conn, prev, service_date, now_ts, now_s)
    if nxt:
        nxt["layover_s"] = (nxt["start_s"] - me["end_s"]
                            if me["end_s"] is not None else None)

    return {"block_id": me["block_id"], "trip_id": tid,
            "prev": prev, "next": nxt}


def _add_live_state(conn: sqlite3.Connection, leg: dict, service_date: str,
                    now_ts: int | None, now_s: int | None) -> None:
    """Voznji pripise, koliko zamuja in kje je -- oboje samo, ce je res znano."""
    lm = last_measured(conn, service_date, [leg["trip_id"]],
                       now_s if now_s is not None else 48 * 3600)
    m = lm.get(leg["trip_id"])
    if m:
        leg["delay_s"] = m["delay_s"]
        leg["delay_stop"] = m["name"]
        leg["delay_stop_seq"] = m["stop_seq"]

    gps = conn.execute(
        "SELECT v.seen_ts, v.lat, v.lon, v.speed_ms, st.name "
        "FROM vehicle_now v "
        "LEFT JOIN sched s ON s.trip_id = v.trip_id AND s.stop_seq = v.stop_seq "
        "LEFT JOIN station st ON st.stop_id = s.stop_id "
        "WHERE v.trip_id = ?", (leg["trip_id"],)
    ).fetchone()
    if gps and now_ts is not None and now_ts - gps["seen_ts"] <= VEHICLE_STALE_S:
        pos = {
            "lat": gps["lat"], "lon": gps["lon"], "seen_ts": gps["seen_ts"],
            "at_stop": gps["name"],
            "speed_kmh": (round(gps["speed_ms"] * 3.6)
                          if gps["speed_ms"] is not None else None),
        }
        # `current_stop_sequence` posilja le 17 od 128 vozil, zato ime kraja
        # skoraj vedno pride od tod, ne iz feeda.
        if not pos["at_stop"]:
            near = nearest_station(conn, gps["lat"], gps["lon"])
            if near:
                pos["near_stop"], pos["near_m"] = near
        leg["gps"] = pos


def nearest_station(conn: sqlite3.Connection, lat: float, lon: float,
                    max_m: float = 5000) -> tuple[str, int] | None:
    """Najblizje postajalisce in zracna razdalja do njega, ali None.

    Zracna, ne cestna -- vozilo je lahko onstran reke. Zato jo prikaz pove kot
    "pri X", ne kot "N minut do X": drugo bi bila trditev, ki je nimamo s cim
    podpreti.
    """
    d = max_m / 111_320                      # stopinje sirine, groba omejitev
    dlon = d / max(math.cos(math.radians(lat)), 0.1)
    rows = conn.execute(
        "SELECT name, lat, lon FROM station "
        "WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
        (lat - d, lat + d, lon - dlon, lon + dlon),
    ).fetchall()
    best = None
    for r in rows:
        m = geo.haversine(lat, lon, r["lat"], r["lon"])
        if m <= max_m and (best is None or m < best[1]):
            best = (r["name"], m)
    return (best[0], round(best[1])) if best else None
