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


def history(conn: sqlite3.Connection, train_no: str, days: int = 90) -> dict:
    """Zgodovina zamud enega vlaka: po dnevih in po postajah."""
    since = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT r.service_date, r.stop_seq, st.name, r.delay_arr, r.delay_dep "
        "FROM run r JOIN trip t USING (trip_id) JOIN sched s "
        "       ON s.trip_id = r.trip_id AND s.stop_seq = r.stop_seq "
        "JOIN station st ON st.stop_id = s.stop_id "
        "WHERE t.train_no = ? AND r.service_date >= ? "
        "ORDER BY r.service_date, r.stop_seq",
        (train_no, since),
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
            "median_s": _pct(v["delays"], 0.5),
            "p90_s": _pct(v["delays"], 0.9),
            "max_s": max(v["delays"]),
        }
        for seq, v in sorted(by_stop.items())
    ]
    return {
        "train_no": train_no,
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
