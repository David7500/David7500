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


def trains(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            "SELECT t.train_no, t.trip_id, t.headsign, COUNT(s.stop_seq) AS stops, "
            "       MIN(s.dep_s) AS first_dep_s "
            "FROM trip t JOIN sched s USING (trip_id) "
            "GROUP BY t.trip_id ORDER BY t.train_no"
        )
    ]


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
    """
    if trip_id:
        row = conn.execute(
            "SELECT trip_id FROM trip WHERE trip_id = ? AND train_no = ?",
            (trip_id, train_no),
        ).fetchone()
        if row:
            return row["trip_id"]
    rows = conn.execute(
        "SELECT t.trip_id, "
        "       (SELECT COUNT(*) FROM service_day sd WHERE sd.service_id = t.service_id) AS days, "
        "       (SELECT COUNT(*) FROM service_day sd WHERE sd.service_id = t.service_id "
        "        AND sd.date = ?) AS runs_today "
        "FROM trip t WHERE t.train_no = ? "
        "ORDER BY runs_today DESC, days DESC, t.trip_id",
        (service_date, train_no),
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
        "SELECT s.stop_seq, st.name, s.arr_s, s.dep_s, r.delay_arr, r.delay_dep "
        "FROM sched s JOIN station st ON st.stop_id = s.stop_id "
        "LEFT JOIN run r ON r.trip_id = s.trip_id AND r.stop_seq = s.stop_seq "
        "                AND r.service_date = ? "
        "WHERE s.trip_id = ? ORDER BY s.stop_seq",
        (service_date, trip_id),
    )
    out = []
    for r in rows:
        d = dict(r)
        d["sched_arr"] = _abs_time(service_date, r["arr_s"])
        d["sched_dep"] = _abs_time(service_date, r["dep_s"])
        # Feed nosi samo zamudo -- dejanski cas je vozni red + zamuda.
        d["actual_arr"] = _abs_time(service_date, (r["arr_s"] or 0) + r["delay_arr"]) \
            if r["arr_s"] is not None and r["delay_arr"] is not None else None
        d["actual_dep"] = _abs_time(service_date, (r["dep_s"] or 0) + r["delay_dep"]) \
            if r["dep_s"] is not None and r["delay_dep"] is not None else None
        out.append(d)
    return out


def history(conn: sqlite3.Connection, train_no: str, days: int = 90,
            exclude_date: str | None = None) -> dict:
    """Zgodovina zamud enega vlaka: po dnevih in po postajah.

    `exclude_date` izpusti en prometni dan. Rabi ga prikaz tekoce voznje:
    "povprecje preteklih voznj" ne sme vsebovati voznje, ki jo risemo zraven,
    sicer bi krivulja delno primerjala podatek sam s seboj.
    """
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT r.service_date, r.stop_seq, st.name, r.delay_arr, r.delay_dep "
        "FROM run r JOIN trip t USING (trip_id) JOIN sched s "
        "       ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
        "JOIN station st ON st.stop_id = s.stop_id "
        "WHERE t.train_no = ? AND r.service_date >= ? "
        "  AND (? IS NULL OR r.service_date <> ?) "
        "ORDER BY r.service_date, r.stop_seq",
        (train_no, since, exclude_date, exclude_date),
    ).fetchall()

    by_day: dict[str, list] = {}
    by_stop: dict[int, dict] = {}
    for r in rows:
        delay = r["delay_arr"] if r["delay_arr"] is not None else r["delay_dep"]
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
            "on_time_share": (round(sum(1 for f in finals if f <= 300) / len(finals), 3)
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
LAST_STOP_SQL = """
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
)
"""


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
    out = [
        {
            "train_no": k, "runs": len(v),
            "median_s": _pct(v, 0.5), "p90_s": _pct(v, 0.9), "max_s": max(v),
            "on_time_share": round(sum(1 for x in v if x <= 300) / len(v), 3),
        }
        for k, v in grouped.items()
    ]
    out.sort(key=lambda r: (-(r["median_s"] or 0), r["train_no"]))
    return out


# Kolikokrat mora biti vozjna zajeta, da o njej sploh kaj recemo. Pri dveh
# voznjah je "mediana" samo povprecje dveh stevilk in bralec ji bo verjel bolj,
# kot zasluzi.
MIN_RUNS_FOR_TYPICAL = 3


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
            "on_time_share": round(sum(1 for v in vals if v <= 300) / len(vals), 2),
        }
    return out


# Meja "tocnosti". Pet minut je obicajen prag pri zeleznicah in isti prag
# uporablja `history()`; ce ga kdaj spremenis, spremeni na obeh mestih.
ON_TIME_S = 300


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

    buckets = {"točno": 0, "1–5 min": 0, "5–15 min": 0, "nad 15 min": 0}
    for v in vals:
        if v <= 60:
            buckets["točno"] += 1
        elif v <= 300:
            buckets["1–5 min"] += 1
        elif v <= 900:
            buckets["5–15 min"] += 1
        else:
            buckets["nad 15 min"] += 1
    return {
        "date": service_date,
        "runs": len(vals),
        "median_s": _pct(vals, 0.5),
        "p90_s": _pct(vals, 0.9),
        "worst_s": max(vals),
        "on_time_share": round(sum(1 for v in vals if v <= ON_TIME_S) / len(vals), 3),
        "buckets": buckets,
    }


def _bucket_counts(values: list[int]) -> dict:
    out = {"točno": 0, "1–5 min": 0, "5–15 min": 0, "nad 15 min": 0}
    for v in values:
        if v <= 60:
            out["točno"] += 1
        elif v <= 300:
            out["1–5 min"] += 1
        elif v <= 900:
            out["5–15 min"] += 1
        else:
            out["nad 15 min"] += 1
    return out


def _group_stats(groups: dict[str, list[int]], min_n: int) -> list[dict]:
    out = []
    for key, vals in groups.items():
        if len(vals) < min_n:
            continue
        out.append({
            "key": key, "n": len(vals),
            "median_s": _pct(vals, 0.5), "p90_s": _pct(vals, 0.9),
            "on_time_share": round(sum(1 for v in vals if v <= ON_TIME_S) / len(vals), 3),
            "buckets": _bucket_counts(vals),
        })
    return out


# GTFS `agency_id` -> ime, kot ga clovek pozna. Surova stevilka v prikazu
# ("avtobus 1118") ne pove nikomur nicesar.
AGENCY_NAMES = {
    "1161": "SŽ", "1118": "LPP", "1123": "Arriva",
    "1119": "Nomago", "1121": "AP Murska Sobota",
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
        "SELECT t.train_no, t.mode, t.network, t.agency, l.service_date, l.d, "
        "       (SELECT MIN(COALESCE(s.dep_s, s.arr_s)) FROM sched s"
        "        WHERE s.trip_id = l.trip_id) AS start_s "
        "FROM last l JOIN trip t USING (trip_id)",
        {"network": network, "since": since},
    ).fetchall()

    by_kind: dict[str, list[int]] = {}
    by_hour: dict[str, list[int]] = {}
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
        if r["start_s"] is not None:
            by_hour.setdefault(f"{(r['start_s'] // 3600) % 24:02d}", []).append(d)
        day = date.fromisoformat(r["service_date"])
        by_dow.setdefault(dow_names[day.weekday()], []).append(d)
        by_day.setdefault(r["service_date"], []).append(d)

    return {
        "runs": len(rows),
        "days": sorted(by_day),
        "by_kind": sorted(_group_stats(by_kind, MIN_RUNS_FOR_GROUP),
                          key=lambda x: -(x["median_s"] or 0)),
        "by_hour": sorted(_group_stats(by_hour, MIN_RUNS_FOR_GROUP), key=lambda x: x["key"]),
        "by_weekday": sorted(_group_stats(by_dow, MIN_RUNS_FOR_GROUP),
                             key=lambda x: dow_names.index(x["key"])),
        "by_day": sorted(_group_stats(by_day, 1), key=lambda x: x["key"]),
    }


def segment_speeds(conn: sqlite3.Connection, train_no: str | None = None) -> list[dict]:
    """Hitrosti po odsekih: voznoredna in dejansko izmerjena.

    Pozor: zamude imajo ločljivost 60 s, zato so hitrosti na kratkih odsekih
    zelo grobe. Odseki pod 5 km so izpuščeni.

    Filtra po omrežju tu ni in ga ne rabi: `edge` nastane samo iz železniških
    shapeov, zato avtobusni par postaj vanj ne more zadeti. Preverjeno na
    zajetih podatkih -- 0 avtobusnih parov v `edge`, 0 avtobusnih linij med
    14 132 izmerjenimi odseki. Če bi kdaj v `edge` prišle ceste, to preneha
    veljati in filter je treba dodati.
    """
    sql = (
        "SELECT t.train_no, r1.service_date, a.name AS from_name, b.name AS to_name, "
        "       s1.dep_s, s2.arr_s, r1.delay_dep, r2.delay_arr, e.km "
        "FROM sched s1 "
        "JOIN sched s2 ON s2.trip_id = s1.trip_id AND s2.stop_seq = s1.stop_seq + 1 "
        "JOIN trip t ON t.trip_id = s1.trip_id "
        "JOIN station a ON a.stop_id = s1.stop_id JOIN station b ON b.stop_id = s2.stop_id "
        "JOIN edge e ON e.from_id = MIN(s1.stop_id, s2.stop_id) "
        "           AND e.to_id = MAX(s1.stop_id, s2.stop_id) "
        "JOIN run r1 ON r1.trip_id = s1.trip_id AND r1.stop_seq = s1.stop_seq "
        "JOIN run r2 ON r2.trip_id = s2.trip_id AND r2.stop_seq = s2.stop_seq "
        "            AND r2.service_date = r1.service_date "
        "WHERE e.km >= 5 AND s1.dep_s IS NOT NULL AND s2.arr_s IS NOT NULL "
        "  AND r1.delay_dep IS NOT NULL AND r2.delay_arr IS NOT NULL"
    )
    params: tuple = ()
    if train_no:
        sql += " AND t.train_no = ?"
        params = (train_no,)

    out = []
    for r in conn.execute(sql, params):
        sched_s = r["arr_s"] - r["dep_s"]
        actual_s = sched_s + (r["delay_arr"] - r["delay_dep"])
        if sched_s <= 0 or actual_s <= 0:
            continue
        out.append({
            "train_no": r["train_no"], "service_date": r["service_date"],
            "from": r["from_name"], "to": r["to_name"], "km": r["km"],
            "sched_kmh": round(r["km"] / (sched_s / 3600), 1),
            "actual_kmh": round(r["km"] / (actual_s / 3600), 1),
        })
    return out


def last_measured(conn: sqlite3.Connection, service_date: str,
                  trip_ids: list[str], now_s: int | None) -> dict[str, dict]:
    """Zadnji postanek vsake vozjne, ki ga je vozilo res ze prevozilo.

    Meja med meritvijo in napovedjo. Vse, kar je za njo, je feedova vrednost
    za se nedosezen postanek -- in ta je izmerjeno slaba (`sztrack backtest
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


def predict(conn: sqlite3.Connection, train_no: str, stop_seq: int,
            current_delay_s: int, days: int = 90,
            exclude_date: str | None = None) -> list[dict]:
    """Napoved zamude na nadaljnjih postajah.

    Osnovni model: zamuda se prenaša naprej, popravljena za historično mediano
    spremembe zamude na tem odseku pri tem vlaku. Enostavno, a je pri vlakih
    presenetljivo trdna izhodiščna točka -- dokler ne nabereš nekaj mesecev
    podatkov, kompleksnejši model nima česa izkoristiti.
    """
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    # Dan, ki ga prikazujemo, ne sme biti v svoji lastni ucni mnozici. Pri
    # tekoci voznji naprej po progi meritev tako ali tako ni, pri ogledu
    # koncanega dne pa bi model deloma napovedoval iz odgovora.
    rows = conn.execute(
        "SELECT r.service_date, r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) AS d "
        "FROM run r JOIN trip t USING (trip_id) "
        "WHERE t.train_no = ? AND r.service_date >= ? AND d IS NOT NULL "
        "  AND (? IS NULL OR r.service_date <> ?) "
        "ORDER BY r.service_date, r.stop_seq",
        (train_no, since, exclude_date, exclude_date),
    ).fetchall()

    by_day: dict[str, dict[int, int]] = {}
    for r in rows:
        by_day.setdefault(r["service_date"], {})[r["stop_seq"]] = r["d"]

    stops = timetable(conn, train_no)
    names = {t["stop_seq"]: t["name"] for t in stops}
    # Rezerva voznega reda: presezek postanka nad najkrajsim, ki ga vozilo se
    # zmore. To je edini vhod v napoved, ki ni statistika -- rezerva je znana
    # vnaprej in obstaja ne glede na to, ali smo jo kdaj videli porabljeno.
    dwell = {t["stop_seq"]: max(0, (t["dep_s"] or 0) - (t["arr_s"] or 0) - MIN_DWELL_S)
             for t in stops if t["arr_s"] is not None and t["dep_s"] is not None}
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
        out.append({
            "stop_seq": seq,
            "name": names[seq],
            "n_samples": len(ostanki),
            "same_class": len(podobni) >= MIN_PREDICT_SAMPLES,
            "slack_s": slack,
            "slack_here_s": tu,
            "predicted_delay_s": osnova + (round(statistics.median(ostanki)) if ostanki else 0),
            "p90_delay_s": (osnova + round(_pct(ostanki, 0.9)) if ostanki else None),
            "basis": "rezerva + historicni ostanek" if ostanki else "rezerva voznega reda",
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
    SELECT r.trip_id, r.stop_seq, s.stop_id,
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
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_max
    FROM t
),
passed AS (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY stop_seq DESC) AS rn
    FROM ranked r
    WHERE r.t_s + COALESCE(r.delay_s, 0) <= ?
      AND NOT (COALESCE(r.delay_s, 0) = 0 AND r.prev_max >= 300)
)
SELECT p.trip_id, p.stop_seq, p.delay_s, st.name
FROM passed p JOIN station st ON st.stop_id = p.stop_id
WHERE p.rn = 1
"""


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
            d["delay_s"] = lm["delay_s"]
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
    payload = builder(conn, days, network)
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
        if age <= max_age_s:
            return {**json.loads(row["payload"]), "runs": row["runs"],
                    "computed_at": row["computed_at"], "through": row["through"],
                    "took_ms": row["took_ms"], "cached": True}

    with _SUMMARY_LOCK:
        # Med cakanjem na kljucavnico ga je morda ze izracunal nekdo drug.
        again = _summary_row(conn, kind, network, days)
        if again is not None and (again["computed_at"] != (row["computed_at"] if row else None)):
            return {**json.loads(again["payload"]), "runs": again["runs"],
                    "computed_at": again["computed_at"], "through": again["through"],
                    "took_ms": again["took_ms"], "cached": True}
        return summary_build(conn, kind, network, days)


def refresh_summaries(conn: sqlite3.Connection, windows=SUMMARY_WINDOWS,
                      networks=SUMMARY_NETWORKS) -> list[dict]:
    """Znova izracunaj vse razreze. To pozene dnevno opravilo in `sztrack summarize`."""
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
