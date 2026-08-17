"""Vecprehodna detekcija: ista slika, vec razlicnih obdelav, nato analiza.

Zakaj: kandidatne elipse so ozko grlo. Ena sama obdelava slike ima eno samo
delovno tocko - CLAHE, ki dvigne slabo osvetljene kose ob robu zaboja, hkrati
napihne sum na dobro osvetljenih; prag gradienta, ki najde zabrisan obris,
pobere tudi teksturo povrsine. Izmerjeno na resnicni fotografiji: noben posamezen
nabor parametrov ne najde vseh kosov, ki jih clovek vidi.

Zato tece detekcija v vec prehodih (razlicen CLAHE, gama, glajenje, merilo,
pragovi EdgeDrawing). Kandidati vseh prehodov se zdruzijo v gruce, gruca pa
nosi podatek, koliko prehodov jo je naslo - to je neodvisen dokaz. Nakljucna
elipsa, sestavljena iz lokov razlicnih kosov, prezivi eno obdelavo, redko pa
vec razlicnih; pravi obris prezivi vecino.

Vidnost obrisa se meri v VSEH prehodih polne locljivosti in se vzame najboljsa:
enakomerno a slabse osvetljen kos ob robu zaboja ima dober kontrast sele po
mocnem CLAHE, in ravno to je prehod, ki mu pripada.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from .config import Config
from .edges import EdgeMap, detect_edges
from .ellipse import (Ellipse, compute_polarity, compute_support,
                      compute_support_gradient, detect_ellipses_edge_drawing,
                      fit_contour)
from .preprocess import Preprocessed, preprocess


@dataclass
class PassOutput:
    """Rezultat enega prehoda. Koordinate elips so ze v polni locljivosti."""
    name: str
    scale: float
    pre: Preprocessed
    edges: EdgeMap
    ellipses: List[Ellipse] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)

    @property
    def full_scale(self) -> bool:
        return abs(self.scale - 1.0) < 1e-6


# --------------------------------------------------------------------------
# posamezen prehod
# --------------------------------------------------------------------------
def _rescale_to_full(ell: Ellipse, scale: float) -> None:
    """Prenese elipso iz pomanjsane slike nazaj v polno locljivost."""
    if abs(scale - 1.0) < 1e-9:
        return
    inv = 1.0 / scale
    ell.cx *= inv
    ell.cy *= inv
    ell.a *= inv
    ell.b *= inv
    ell.rms_px *= inv
    ell.conic = None            # parametri so se spremenili
    ell.points = None if ell.points is None else ell.points * inv


def run_pass(gray_raw: np.ndarray, cfg: Config, spec: dict) -> PassOutput:
    """Izvede eno obdelavo slike in vrne njene kandidatne elipse."""
    name = str(spec.get("name", "pass"))
    scale = float(spec.get("scale", 1.0))
    pass_cfg = cfg.with_overrides(dict(spec.get("overrides", {}) or {}))

    src = gray_raw
    if abs(scale - 1.0) > 1e-6:
        src = cv2.resize(gray_raw, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC)

    pre = preprocess(src, pass_cfg)
    edges = detect_edges(pre.gray, pass_cfg, exclude_mask=pre.specular_mask,
                         gradient_image=pre.raw_gray)

    detector = str(pass_cfg["ellipse.detector"])
    ellipses: List[Ellipse] = []
    n_contour = 0
    diag: dict = {"scale": scale, "detector": detector}
    if detector in ("contours", "both"):
        for contour in edges.contours:
            ellipses.extend(fit_contour(contour, pass_cfg))
        n_contour = len(ellipses)
    if detector in ("edge_drawing", "both"):
        ed_ellipses, ed_diag = detect_ellipses_edge_drawing(pre.gray, pass_cfg)
        diag["edge_drawing"] = ed_diag
        ellipses.extend(ed_ellipses)

    for ell in ellipses:
        _rescale_to_full(ell, scale)
        ell.meta["pass"] = name
        if abs(scale - 1.0) > 1e-6:
            ell.meta["scaled"] = True

    diag.update({"n_from_contours": n_contour,
                 "n_from_edge_drawing": len(ellipses) - n_contour,
                 "n_total": len(ellipses),
                 "n_edge_points": int(len(edges.points))})
    return PassOutput(name=name, scale=scale, pre=pre, edges=edges,
                      ellipses=ellipses, diagnostics=diag)


def run_passes(gray_raw: np.ndarray, cfg: Config) -> Tuple[List[PassOutput], dict]:
    specs = cfg["multipass.passes"]
    if not specs:
        raise ValueError("multipass.passes je prazen - vsaj en prehod mora biti definiran")
    outputs = [run_pass(gray_raw, cfg, spec) for spec in specs]
    diag = {"n_passes": len(outputs),
            "per_pass": {p.name: p.diagnostics for p in outputs}}
    return outputs, diag


# --------------------------------------------------------------------------
# zdruzevanje kandidatov cez prehode
# --------------------------------------------------------------------------
def _same_ellipse(a: Ellipse, b: Ellipse, center_tol: float, axis_tol: float) -> bool:
    if float(np.linalg.norm(a.center - b.center)) > center_tol:
        return False
    if abs(a.a - b.a) > axis_tol * max(a.a, b.a):
        return False
    if abs(a.b - b.b) > axis_tol * max(a.b, b.b) + 1.0:
        return False
    return True


def _circular_mean_angle(angles: Sequence[float]) -> float:
    """Povprecje kotov po modulu pi (os elipse nima smeri)."""
    doubled = 2.0 * np.asarray(angles, dtype=float)
    mean = math.atan2(float(np.sin(doubled).mean()), float(np.cos(doubled).mean())) / 2.0
    return mean % math.pi


def _member_quality(ell: Ellipse, geometry_pass: str) -> tuple:
    """Ureditev clanov gruce po kakovosti fita.

    Fit na subpixel robnih tockah polne locljivosti je merilno boljsi od
    zdruzevanja lokov (EdgeDrawing vrne celostevilcne polosi) in od fita na
    pomanjsani sliki. Zato ne povprecimo - vzamemo NAJBOLJSEGA clana.

    Med enakovrednimi ima prednost referencni prehod: njegovi pragovi so
    umerjeni na natancnost lege roba, medtem ko so ostali prehodi tam zato, da
    kos sploh NAJDEJO.
    """
    scaled = bool(ell.meta.get("scaled"))
    preferred = str(ell.meta.get("pass", "")) == geometry_pass
    return (0 if scaled else 1, 1 if preferred else 0, ell.n_points, -ell.rms_px)


def _representative(members: List[Ellipse], geometry_pass: str = "") -> Ellipse:
    """Predstavnik gruce: najboljsi fit; mediana le kot rezerva brez robnih tock.

    Izmerjeno: mediana parametrov cez clane poslabsa RMSE naklona z 0.8 na 3.0
    stopinje - grobi clani (EdgeDrawing, pomanjsana slika) potegnejo dober fit
    stran. Gruca je tu zato, da presteje glasove, ne da glada geometrijo.
    """
    best = max(members, key=lambda m: _member_quality(m, geometry_pass))
    if best.n_points > 0:
        cx, cy, a, b, theta = best.cx, best.cy, best.a, best.b, best.theta
        rms = best.rms_px
    else:
        cx = float(np.median([m.cx for m in members]))
        cy = float(np.median([m.cy for m in members]))
        a = float(np.median([m.a for m in members]))
        b = float(np.median([m.b for m in members]))
        theta = _circular_mean_angle([m.theta for m in members])
        rms = float(np.median([m.rms_px for m in members]))
    rep = Ellipse(cx=cx, cy=cy, a=a, b=b, theta=theta, rms_px=rms,
                  n_points=best.n_points, points=best.points)
    passes = sorted({str(m.meta.get("pass", "?")) for m in members})
    sources = sorted({str(m.meta.get("source", "contours")) for m in members})
    centers = np.array([[m.cx, m.cy] for m in members], dtype=float)
    rep.meta = {
        "passes": passes,
        "votes": len(passes),
        "sources": sources,
        "n_members": len(members),
        "center_spread_px": float(np.max(np.linalg.norm(centers - [cx, cy], axis=1)))
        if len(members) > 1 else 0.0,
        "axis_spread": float(np.max([abs(m.a - a) for m in members]) / max(a, 1e-6))
        if len(members) > 1 else 0.0,
    }
    return rep


def consolidate(passes: Sequence[PassOutput], cfg: Config) -> Tuple[List[Ellipse], dict]:
    """Zdruzi kandidate vseh prehodov v gruce in vrne po enega predstavnika.

    Gruca nosi stevilo prehodov, ki so jo nasli. To je edini podatek, ki ga en
    sam prehod ne more dati: ali je elipsa stabilna glede na obdelavo slike.
    """
    pooled: List[Ellipse] = [e for p in passes for e in p.ellipses]
    center_frac = float(cfg["multipass.cluster_center_frac"])
    center_floor = float(cfg["multipass.cluster_center_floor_px"])
    axis_tol = float(cfg["multipass.cluster_axis_ratio"])

    # Vecji in bolje podprti fiti prvi - manjsi se pripnejo nanje, ne obratno.
    order = sorted(pooled, key=lambda e: (-e.a, e.rms_px))
    clusters: List[List[Ellipse]] = []
    seeds: List[Ellipse] = []
    # Prostorsko kazalo: brez njega je zdruzevanje kvadraticno in pri nekaj tisoc
    # kandidatih traja dlje kot vsi prehodi skupaj. Celica je enaka najvecji
    # mozni toleranci, zato zadosca pregled 3x3 sosescine.
    a_max = max((e.a for e in pooled), default=1.0)
    cell = max(center_floor, center_frac * a_max, 1.0)
    grid: Dict[Tuple[int, int], List[int]] = {}
    for ell in order:
        gx0, gy0 = int(ell.cx // cell), int(ell.cy // cell)
        placed = False
        for dx in (-1, 0, 1):
            if placed:
                break
            for dy in (-1, 0, 1):
                for idx in grid.get((gx0 + dx, gy0 + dy), ()):
                    seed = seeds[idx]
                    tol = max(center_floor, center_frac * max(seed.a, ell.a))
                    if _same_ellipse(seed, ell, tol, axis_tol):
                        clusters[idx].append(ell)
                        placed = True
                        break
                if placed:
                    break
        if not placed:
            grid.setdefault((gx0, gy0), []).append(len(seeds))
            clusters.append([ell])
            seeds.append(ell)

    geometry_pass = str(cfg["multipass.geometry_pass"])
    reps = [_representative(members, geometry_pass) for members in clusters]
    votes = [r.meta["votes"] for r in reps] or [0]
    diag = {
        "n_pooled": len(pooled),
        "n_clusters": len(reps),
        "votes_histogram": {int(v): int(sum(1 for r in reps if r.meta["votes"] == v))
                            for v in sorted(set(votes))},
    }
    return reps, diag


# --------------------------------------------------------------------------
# meritve cez prehode
# --------------------------------------------------------------------------
def measure_across_passes(ellipses: Sequence[Ellipse], passes: Sequence[PassOutput],
                          cfg: Config) -> dict:
    """Vidnost in polariteta se izmerita v vsakem prehodu; obvelja najboljsa.

    Namenoma NE povprecimo: kos, ki ga en prehod prikaze s cistim kontrastom,
    drugi pa ga poplavi s sumom, je viden - povprecje bi ga po nepotrebnem
    kaznovalo. Zanima nas, ali OBSTAJA obdelava, v kateri je obris cel.
    """
    if not ellipses:
        return {"n_measured": 0}
    gradient = str(cfg["ellipse.support_method"]) == "gradient"
    usable = [p for p in passes if p.full_scale and p.edges.gx is not None]
    if not usable:
        usable = list(passes)

    best_support = {id(e): -1.0 for e in ellipses}
    best_polarity = {id(e): 0.0 for e in ellipses}
    best_pass = {id(e): "" for e in ellipses}
    for p in usable:
        if gradient:
            compute_support_gradient(ellipses, p.edges.gx, p.edges.gy, cfg)
        else:
            compute_support(ellipses, p.edges.points, cfg)
        compute_polarity(ellipses, p.edges.gx, p.edges.gy, cfg)
        for ell in ellipses:
            ell.meta.setdefault("support_by_pass", {})[p.name] = round(ell.support_ratio, 3)
            if ell.support_ratio > best_support[id(ell)]:
                best_support[id(ell)] = float(ell.support_ratio)
                best_polarity[id(ell)] = float(ell.polarity)
                best_pass[id(ell)] = p.name

    for ell in ellipses:
        ell.support_ratio = max(0.0, best_support[id(ell)])
        ell.polarity = best_polarity[id(ell)]
        ell.meta["best_pass"] = best_pass[id(ell)]
    return {"n_measured": len(ellipses),
            "passes_used": [p.name for p in usable]}
