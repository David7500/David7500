"""Poizvedbe nad zajetimi podatki: zgodovina, porazdelitve, hitrosti, napoved."""
from __future__ import annotations

import json
import sqlite3
import statistics
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config

TZ = ZoneInfo(config.TIMEZONE)


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


def stations(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM station ORDER BY name")]


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


def timetable(conn: sqlite3.Connection, train_no: str) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            "SELECT s.stop_seq, s.stop_id, st.name, st.lat, st.lon, s.arr_s, s.dep_s "
            "FROM trip t JOIN sched s USING (trip_id) JOIN station st ON st.stop_id = s.stop_id "
            "WHERE t.train_no = ? ORDER BY s.stop_seq",
            (train_no,),
        )
    ]


def trip_mode(conn: sqlite3.Connection, train_no: str) -> str:
    """'vlak' ali 'bus'. Nadomestni prevoz je v istem iskalniku, a potnik mora
    vedeti, na kaj čaka -- na peronu ali na postajališču."""
    row = conn.execute("SELECT mode FROM trip WHERE train_no = ? LIMIT 1",
                       (train_no,)).fetchone()
    return row["mode"] if row else "vlak"


def run_detail(conn: sqlite3.Connection, train_no: str, service_date: str) -> list[dict]:
    """Ena konkretna vožnja: vozni red + zamuda + izračunani dejanski čas."""
    rows = conn.execute(
        "SELECT s.stop_seq, st.name, s.arr_s, s.dep_s, r.delay_arr, r.delay_dep "
        "FROM trip t JOIN sched s USING (trip_id) JOIN station st ON st.stop_id = s.stop_id "
        "LEFT JOIN run r ON r.trip_id = t.trip_id AND r.stop_seq = s.stop_seq "
        "                AND r.service_date = ? "
        "WHERE t.train_no = ? ORDER BY s.stop_seq",
        (service_date, train_no),
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


def network_stats(conn: sqlite3.Connection, days: int = 90) -> list[dict]:
    """Lestvica vlakov po zamudi na koncu vožnje."""
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "WITH last AS ("
        "  SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep,"
        "         ROW_NUMBER() OVER (PARTITION BY r.trip_id, r.service_date"
        "                            ORDER BY r.stop_seq DESC) AS rn"
        "  FROM run r WHERE r.service_date >= ?"
        ") "
        "SELECT t.train_no, l.service_date, COALESCE(l.delay_arr, l.delay_dep) AS d "
        "FROM last l JOIN trip t USING (trip_id) WHERE l.rn = 1 AND d IS NOT NULL",
        (since,),
    ).fetchall()
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
            f"SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_arr, r.delay_dep) AS d "
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


def day_summary(conn: sqlite3.Connection, service_date: str) -> dict:
    """Kako je mreža vozila ta dan: porazdelitev končnih zamud po vožnjah.

    Ena vožnja = en vzorec, ne en postanek. Sicer bi vlak s tridesetimi
    postanki tridesetkrat glasoval, kratki lokalni pa enkrat, in "delež
    točnih" bi meril dolžino poti namesto točnosti.
    """
    rows = conn.execute(
        "WITH last AS ("
        "  SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_arr, r.delay_dep) AS d,"
        "         ROW_NUMBER() OVER (PARTITION BY r.trip_id ORDER BY r.stop_seq DESC) AS rn"
        "  FROM run r WHERE r.service_date = ?"
        ") SELECT d FROM last WHERE rn = 1 AND d IS NOT NULL",
        (service_date,),
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


def segment_speeds(conn: sqlite3.Connection, train_no: str | None = None) -> list[dict]:
    """Hitrosti po odsekih: voznoredna in dejansko izmerjena.

    Pozor: zamude imajo ločljivost 60 s, zato so hitrosti na kratkih odsekih
    zelo grobe. Odseki pod 5 km so izpuščeni.
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


def predict(conn: sqlite3.Connection, train_no: str, stop_seq: int,
            current_delay_s: int, days: int = 90) -> list[dict]:
    """Napoved zamude na nadaljnjih postajah.

    Osnovni model: zamuda se prenaša naprej, popravljena za historično mediano
    spremembe zamude na tem odseku pri tem vlaku. Enostavno, a je pri vlakih
    presenetljivo trdna izhodiščna točka -- dokler ne nabereš nekaj mesecev
    podatkov, kompleksnejši model nima česa izkoristiti.
    """
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT r.service_date, r.stop_seq, COALESCE(r.delay_arr, r.delay_dep) AS d "
        "FROM run r JOIN trip t USING (trip_id) "
        "WHERE t.train_no = ? AND r.service_date >= ? AND d IS NOT NULL "
        "ORDER BY r.service_date, r.stop_seq",
        (train_no, since),
    ).fetchall()

    by_day: dict[str, dict[int, int]] = {}
    for r in rows:
        by_day.setdefault(r["service_date"], {})[r["stop_seq"]] = r["d"]

    names = {t["stop_seq"]: t["name"] for t in timetable(conn, train_no)}
    out = []
    for seq in sorted(s for s in names if s > stop_seq):
        deltas = [
            day[seq] - day[stop_seq]
            for day in by_day.values()
            if stop_seq in day and seq in day
        ]
        out.append({
            "stop_seq": seq,
            "name": names[seq],
            "n_samples": len(deltas),
            "predicted_delay_s": current_delay_s + (round(statistics.median(deltas)) if deltas else 0),
            "p90_delay_s": (current_delay_s + round(_pct(deltas, 0.9)) if deltas else None),
            "basis": "historicna mediana" if deltas else "prenos trenutne zamude",
        })
    return out


# ---------------------------------------------------------------- povezave A -> B

_CONNECTIONS_SQL = """
SELECT t.trip_id, t.train_no, t.headsign, t.mode,
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
                service_date: str, now_s: int | None = None) -> list[dict]:
    """Vse vožnje, ki na dani dan peljejo od `from_name` do `to_name`.

    Relacija ni v številki vlaka in ne v `route_id` -- ta je v tem feedu
    ena-na-ena s tripom. Edini vir je zaporedje postaj: izhodišče mora imeti
    manjši `stop_seq` od cilja.
    """
    rows = conn.execute(_CONNECTIONS_SQL,
                        {"a": from_name, "b": to_name, "day": service_date}).fetchall()

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
    if now_s is not None:
        ids = [d["trip_id"] for d in out]
        # Vsi vezani parametri morajo biti istega sloga: sqlite jih ob mesanju
        # `?` in `:ime` veze po vrstnem redu pojavitve, kar tiho zamenja vrednosti.
        sql = _LAST_MEASURED_SQL % ",".join("?" * len(ids))
        last = {r["trip_id"]: dict(r)
                for r in conn.execute(sql, (service_date, *ids, now_s))}
    else:
        last = {}

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
            d["delay_s"] = lm["delay_s"]
            d["delay_at"] = lm["name"]
            d["delay_kind"] = "izmerjeno"
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

def run_weather(conn: sqlite3.Connection, train_no: str, service_date: str) -> list[dict]:
    """Vreme na vsaki postaji te vožnje.

    Ura se vzame po dejanskem času (vozni red + zamuda), kadar ga imamo, sicer
    po voznorednem -- vreme mora opisovati trenutek, ko je vlak tam, ne ure
    odhoda z izhodišča. Vrednost je modelska za celico 8 x 8 km, ne meritev na
    peronu, in prikaz mora to povedati.
    """
    from . import weather as weather_mod

    rows = conn.execute(
        "SELECT s.stop_seq, st.name, st.lat, st.lon, "
        "       COALESCE(s.dep_s, s.arr_s) AS t_s, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS delay_s "
        "FROM trip t JOIN sched s USING (trip_id) JOIN station st ON st.stop_id = s.stop_id "
        "LEFT JOIN run r ON r.trip_id = t.trip_id AND r.stop_seq = s.stop_seq "
        "                AND r.service_date = ? "
        "WHERE t.train_no = ? ORDER BY s.stop_seq",
        (service_date, train_no),
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
