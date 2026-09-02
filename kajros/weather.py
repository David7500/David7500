"""Vreme ob zamudah.

Zakaj sploh gre: zamuda brez konteksta pove samo, da je vlak zamujal.
Vprašanje "zakaj" rabi dejavnike, in vreme je edini, ki je zastonj in
pokriva ves čas nazaj.

Ključna lastnost vira: Open-Meteo ima **arhiv za nazaj**, svež do včeraj.
Vremena torej ni treba začeti zbirati vnaprej -- za že zajete zamude ga
lahko dopolnimo kadarkoli. Zato ta modul ni del zajema v realnem času,
ampak dnevno opravilo, ki gleda nazaj.

Ločljivost: mreža 0,1 stopinje (~8 km) in ena ura. 267 postaj se zloži
na ~111 celic, kar gre v tri zahtevke.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone

import requests

from . import config

# Vremenska celica. Manjse od tega nima smisla: modeli, iz katerih arhiv
# racuna, imajo mrezo nekaj kilometrov, zato bi finejsa delitev le podvojila
# zahtevke za iste vrednosti.
CELL_DEG = 0.1

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,precipitation,snowfall,wind_gusts_10m,weather_code"
# Arhiv `visibility` vrne prazno (enota "undefined"), zato je ni na seznamu.

CHUNK = 40          # lokacij na zahtevek -- da URL ostane obvladljiv
TIMEOUT = 60


def cell_key(lat: float, lon: float) -> str:
    """Ime celice: sredisce zaokrozeno na CELL_DEG, da je stabilno in berljivo."""
    return f"{round(lat / CELL_DEG) * CELL_DEG:.1f},{round(lon / CELL_DEG) * CELL_DEG:.1f}"


def station_cells(conn: sqlite3.Connection) -> dict[str, tuple[float, float]]:
    """Vse celice, v katerih leži vsaj ena postaja -> koordinati sredisca."""
    out: dict[str, tuple[float, float]] = {}
    for r in conn.execute("SELECT lat, lon FROM station"):
        key = cell_key(r["lat"], r["lon"])
        if key not in out:
            lat_s, lon_s = key.split(",")
            out[key] = (float(lat_s), float(lon_s))
    return out


def _chunks(items: list, n: int):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def _request(url: str, cells: list[tuple[str, float, float]], params: dict) -> list[dict]:
    """En zahtevek za vec lokacij hkrati. Open-Meteo vrne seznam, kadar je
    lokacij vec, in en sam objekt, kadar je ena -- oboje zvedemo na seznam."""
    q = {
        "latitude": ",".join(f"{lat:.4f}" for _, lat, _ in cells),
        "longitude": ",".join(f"{lon:.4f}" for _, _, lon in cells),
        "hourly": HOURLY,
        "timezone": "UTC",
        **params,
    }
    resp = requests.get(url, params=q, timeout=TIMEOUT,
                        headers={"User-Agent": config.USER_AGENT})
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else [data]


def _rows(cells: list[tuple[str, float, float]], payloads: list[dict],
          source: str, fetched_at: int) -> list[tuple]:
    rows = []
    for (key, _, _), payload in zip(cells, payloads):
        h = payload.get("hourly") or {}
        times = h.get("time") or []
        for i, t in enumerate(times):
            # Open-Meteo vrne cas brez oznake cone, ker smo zahtevali timezone=UTC.
            ts = int(datetime.fromisoformat(t).replace(tzinfo=timezone.utc).timestamp())
            rows.append((
                key, ts,
                h["temperature_2m"][i], h["precipitation"][i], h["snowfall"][i],
                h["wind_gusts_10m"][i], h["weather_code"][i],
                source, fetched_at,
            ))
    return rows


_UPSERT = """
INSERT INTO weather(cell, hour_ts, temp_c, precip_mm, snowfall_cm,
                    wind_gust_kmh, code, source, fetched_at)
VALUES(?,?,?,?,?,?,?,?,?)
ON CONFLICT(cell, hour_ts) DO UPDATE SET
    temp_c=excluded.temp_c, precip_mm=excluded.precip_mm,
    snowfall_cm=excluded.snowfall_cm, wind_gust_kmh=excluded.wind_gust_kmh,
    code=excluded.code, source=excluded.source, fetched_at=excluded.fetched_at
-- Arhiv (reanaliza) je boljsi od napovedi za isto uro; obratno nikoli ne prepisuj.
WHERE excluded.source = 'archive' OR weather.source = excluded.source
"""


def fetch_days(conn: sqlite3.Connection, start: date, end: date) -> dict:
    """Napolni vreme za dneve [start, end]. Za pretekle dneve vzame arhiv
    (reanaliza), za danes napoved -- in ju loci s stolpcem `source`, da
    kasnejsi zagon lahko napoved zamenja z arhivom."""
    cells = [(k, lat, lon) for k, (lat, lon) in sorted(station_cells(conn).items())]
    if not cells:
        return {"cells": 0, "rows": 0, "days": 0}

    today = datetime.now(timezone.utc).date()
    fetched_at = int(datetime.now(timezone.utc).timestamp())
    written = 0
    days = 0

    # Arhiv zna cel razpon naenkrat; napoved rabi svoj zahtevek.
    arch_end = min(end, today - timedelta(days=1))
    if start <= arch_end:
        days += (arch_end - start).days + 1
        for group in _chunks(cells, CHUNK):
            payloads = _request(ARCHIVE_URL, group, {
                "start_date": start.isoformat(), "end_date": arch_end.isoformat()})
            rows = _rows(group, payloads, "archive", fetched_at)
            conn.executemany(_UPSERT, rows)
            written += len(rows)

    if end >= today:
        days += 1
        for group in _chunks(cells, CHUNK):
            payloads = _request(FORECAST_URL, group,
                                {"past_days": 0, "forecast_days": 1})
            rows = _rows(group, payloads, "forecast", fetched_at)
            conn.executemany(_UPSERT, rows)
            written += len(rows)

    conn.commit()
    return {"cells": len(cells), "rows": written, "days": days}


def backfill(conn: sqlite3.Connection, days: int = 7) -> dict:
    """Zadnjih `days` dni do danes. Ponovni zagon je varen in celo zazelen:
    napoved za danes se naslednji dan zamenja z arhivsko vrednostjo."""
    end = datetime.now(timezone.utc).date()
    return fetch_days(conn, end - timedelta(days=days - 1), end)


def covered_days(conn: sqlite3.Connection) -> list[dict]:
    """Kaj imamo -- za sanity check in za ukazno vrstico."""
    return [dict(r) for r in conn.execute(
        "SELECT DATE(hour_ts, 'unixepoch') AS day, source,"
        "       COUNT(*) AS rows_n, COUNT(DISTINCT cell) AS cells "
        "FROM weather GROUP BY day, source ORDER BY day")]


# ---------------------------------------------------------------- stopnja razmer

# Surove stevilke (mm, °C, km/h) so za potnika prevec. Indeks 0-10 pove,
# kako hude so razmere -- a mora ostati preverljiv, zato vsak prispevek
# potuje zraven in prikaz ga pokaze ob dotiku.
#
# Ni napoved zamude in ne trdi vzrocnosti: opisuje vreme, nic drugega.

_PRECIP_STEPS = ((10.0, 8), (5.0, 6), (2.0, 4), (0.5, 2), (0.1, 1))
_SNOW_STEPS = ((3.0, 7), (1.0, 5), (0.1, 3))
_GUST_STEPS = ((90.0, 7), (70.0, 5), (50.0, 3), (30.0, 1))


def _step(value: float | None, steps) -> int:
    if value is None:
        return 0
    for threshold, points in steps:
        if value >= threshold:
            return points
    return 0


def severity(row: dict) -> dict:
    """Indeks razmer 0-10 z razclenitvijo, iz katere je sestavljen."""
    parts = []

    p = _step(row.get("precip_mm"), _PRECIP_STEPS)
    if p:
        parts.append({"what": "padavine", "points": p})
    s = _step(row.get("snowfall_cm"), _SNOW_STEPS)
    if s:
        parts.append({"what": "sneg", "points": s})
    g = _step(row.get("wind_gust_kmh"), _GUST_STEPS)
    if g:
        parts.append({"what": "sunki vetra", "points": g})

    code = row.get("code")
    if code in (45, 48):
        parts.append({"what": "megla", "points": 2})
    if code in (95, 96, 99):
        parts.append({"what": "nevihta", "points": 3})

    t = row.get("temp_c")
    if t is not None and t <= -5:
        parts.append({"what": "mraz", "points": 2})
    elif t is not None and t >= 32:
        # Vrocina pomeni omejitve hitrosti zaradi tirnic, ne udobja.
        parts.append({"what": "vročina", "points": 1})

    score = min(10, sum(x["points"] for x in parts))
    if score == 0:
        label = "mirne"
    elif score <= 3:
        label = "blage"
    elif score <= 6:
        label = "zahtevne"
    else:
        label = "hude"
    return {"score": score, "label": label, "parts": parts}


# Semafor, ne lestvica enega odtenka: stopnje se morajo lociti na prvi pogled.
# Tople barve tu ne trkajo z lestvico zamud, ker je v pogledu Vreme zamuda
# narisana nevtralno -- lestvica zamud zivi v pogledu Zamude.
#
# Preverjeno z validatorjem palete na temni podlagi: najslabsi par med sabo je
# #d1495b <-> #6b7480 (protan ΔE 6,1), kar je dovoljeno le ob dodatnem zapisu --
# zato stopnja povsod nosi tudi stevilko in ime.
SEVERITY_STYLE = {
    "mirne":    "#6b7480",
    "blage":    "#5aa87d",
    "zahtevne": "#d9b33c",
    "hude":     "#d1495b",
}
SEVERITY_ORDER = ("mirne", "blage", "zahtevne", "hude")


def severity_color(score: int) -> str:
    if score <= 0:
        return SEVERITY_STYLE["mirne"]
    if score <= 3:
        return SEVERITY_STYLE["blage"]
    if score <= 6:
        return SEVERITY_STYLE["zahtevne"]
    return SEVERITY_STYLE["hude"]
