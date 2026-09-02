"""Geodetski pripomočki: razdalje, projekcija postaj na progo, poenostavljanje."""
from __future__ import annotations

import math

EARTH_R = 6371008.8


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Razdalja v metrih."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlambda = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def cumulative(points: list[tuple[float, float]]) -> list[float]:
    """Kumulativna dolžina polilinije [(lat, lon), ...] v metrih."""
    out = [0.0]
    for i in range(1, len(points)):
        out.append(out[-1] + haversine(*points[i - 1], *points[i]))
    return out


def project(points: list[tuple[float, float]], cums: list[float], lat: float, lon: float):
    """Najbližja točka na poliliniji.

    Vrne (razdalja vzdolž proge v m, odmik postaje od proge v m).
    Odmik je merilo zaupanja -- velik odmik pomeni, da postaja ne pripada tej progi.
    """
    best_off, best_along = float("inf"), 0.0
    k = math.cos(math.radians(lat))  # lokalna ravninska aproksimacija
    for i in range(len(points) - 1):
        ay, ax = points[i]
        by, bx = points[i + 1]
        vx, vy = (bx - ax) * k, by - ay
        wx, wy = (lon - ax) * k, lat - ay
        len2 = vx * vx + vy * vy
        t = 0.0 if len2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / len2))
        off = haversine(lat, lon, ay + t * (by - ay), ax + t * (bx - ax))
        if off < best_off:
            best_off = off
            best_along = cums[i] + t * (cums[i + 1] - cums[i])
    return best_along, best_off


def slice_between(points, cums, along_a: float, along_b: float):
    """Izreže del polilinije med dvema razdaljama vzdolž proge."""
    lo, hi = sorted((along_a, along_b))
    out = [p for p, c in zip(points, cums) if lo - 1 <= c <= hi + 1]
    if along_a > along_b:
        out.reverse()
    return out


def simplify(points, eps: float = 1e-4):
    """Douglas-Peucker; eps je v stopinjah (1e-4 ~ 10 m)."""
    if len(points) < 3:
        return points
    y1, x1 = points[0]
    y2, x2 = points[-1]
    dmax, idx = 0.0, 0
    den = math.hypot(x2 - x1, y2 - y1) or 1.0
    for i in range(1, len(points) - 1):
        y, x = points[i]
        d = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1)) / den
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return simplify(points[: idx + 1], eps)[:-1] + simplify(points[idx:], eps)
    return [points[0], points[-1]]
