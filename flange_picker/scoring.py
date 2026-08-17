"""Rangiranje kandidatov in dolocitev prijemne tocke.

Sesek ne sme na geometrijsko sredisce (tam je luknja), ampak na kolobar med
D_in in D_out - in sicer na tisti del kolobarja, ki ni prekrit s sosednjimi kosi.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .autocalib import _homography_scale
from .config import Config
from .ellipse import EllipsePair
from .pose import FlangePose, project_points


@dataclass
class Candidate:
    pair: EllipsePair
    pose: FlangePose
    occlusion_ratio: float = 0.0
    free_arc_deg: float = 0.0
    cup_fit_ratio: float = 0.0
    wall_margin_mm: float = float("nan")
    grasp_point_mm: Optional[np.ndarray] = None
    grasp_point_px: Optional[np.ndarray] = None
    visibility_raw: float = 0.0
    score: float = 0.0
    terms: dict = field(default_factory=dict)
    rejected: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    @property
    def depth(self) -> float:
        return float(self.pose.center_cam[2])


def _conic_inside(conic: np.ndarray, center: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Bool maska: katere tocke lezijo znotraj elipse (predznak neodvisen od fita)."""
    hom = np.concatenate([np.asarray(points, dtype=float),
                          np.ones((len(points), 1))], axis=1)
    vals = np.einsum("ij,jk,ik->i", hom, conic, hom)
    c = np.array([center[0], center[1], 1.0])
    ref = float(c @ conic @ c)
    if abs(ref) < 1e-18:
        return np.zeros(len(points), dtype=bool)
    return (vals * ref) > 0


def _plane_basis(normal: np.ndarray, ref_dir: Optional[np.ndarray] = None
                 ) -> Tuple[np.ndarray, np.ndarray]:
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    if ref_dir is not None:
        u = np.asarray(ref_dir, dtype=float) - n * float(np.dot(ref_dir, n))
        if np.linalg.norm(u) < 1e-6:
            u = None
    else:
        u = None
    if u is None:
        helper = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u = np.cross(n, helper)
    u = u / np.linalg.norm(u)
    v = np.cross(n, u)
    return u, v


def analyse_ring(cand: Candidate, others: Sequence[Candidate], calib, cfg: Config,
                 image_shape: Tuple[int, int]) -> None:
    """Poisce najsirsi prost lok kolobarja in prijemno tocko na njegovi sredini."""
    r_out = float(cfg["flange.d_out_mm"]) / 2.0
    r_in = float(cfg["flange.d_in_mm"]) / 2.0
    r_mid = 0.5 * (r_out + r_in)
    cup_d = float(cfg["gripper.suction_cup_diameter_mm"])
    n_samples = int(cfg["scoring.ring_samples"])

    ring_width = r_out - r_in
    cand.cup_fit_ratio = float(min(1.0, ring_width / cup_d)) if cup_d > 0 else 1.0

    ref_dir = None
    if calib.rot_box is not None:
        ref_dir = calib.rot_box[:, 0]          # X os zaboja, da je azimut primerljiv
    u, v = _plane_basis(cand.pose.normal_cam, ref_dir)
    angles = np.linspace(0.0, 2.0 * math.pi, n_samples, endpoint=False)
    pts3 = (cand.pose.center_cam[None, :]
            + r_mid * (np.cos(angles)[:, None] * u[None, :]
                       + np.sin(angles)[:, None] * v[None, :]))
    pix = project_points(pts3, calib.k_mat)

    h, w = image_shape
    free = (pix[:, 0] >= 0) & (pix[:, 0] < w) & (pix[:, 1] >= 0) & (pix[:, 1] < h)

    min_conf = float(cfg["scoring.occluder_min_confidence"])
    same_piece = float(cfg["scoring.same_piece_distance_mm"])
    for other in others:
        if other is cand or other.pose is None:
            continue
        if other.depth >= cand.depth:          # samo blizji kosi lahko prekrivajo
            continue
        if other.pose.confidence < min_conf:
            continue                           # dvomljiva detekcija ne sme vetirati trdne
        if float(np.linalg.norm(other.pose.center_cam - cand.pose.center_cam)) < same_piece:
            continue                           # ista prirobnica, detektirana dvakrat
        inside = _conic_inside(other.pair.outer.matrix(), other.pair.outer.center, pix)
        free &= ~inside

    # tangencialna rezerva za premer cascice
    half_span = math.asin(min(1.0, (cup_d / 2.0) / max(r_mid, 1e-6)))
    pad = int(math.ceil(half_span / (2.0 * math.pi / n_samples)))
    if pad > 0 and not free.all():
        blocked = ~free
        eroded = blocked.copy()
        for shift in range(1, pad + 1):
            eroded |= np.roll(blocked, shift) | np.roll(blocked, -shift)
        free = ~eroded

    if not free.any():
        cand.free_arc_deg = 0.0
        # najmanj slaba tocka: najdaljsi lok pred sirjenjem
        cand.grasp_point_mm = None
        cand.grasp_point_px = None
        cand.notes.append("kolobar je v celoti prekrit ali izven slike")
        return

    best_len, best_start = 0, 0
    idx = 0
    doubled = np.concatenate([free, free])
    while idx < n_samples:
        if doubled[idx]:
            j = idx
            while j < idx + n_samples and doubled[j]:
                j += 1
            if j - idx > best_len:
                best_len, best_start = j - idx, idx
            idx = j
        else:
            idx += 1
    cand.free_arc_deg = float(360.0 * best_len / n_samples)
    mid = (best_start + best_len / 2.0) % n_samples
    theta = 2.0 * math.pi * mid / n_samples
    grasp_cam = cand.pose.center_cam + r_mid * (math.cos(theta) * u + math.sin(theta) * v)
    cand.grasp_point_px = project_points(grasp_cam[None, :], calib.k_mat)[0]
    if calib.rot_box is not None and calib.t_box is not None:
        cand.grasp_point_mm = calib.rot_box.T @ (grasp_cam - calib.t_box)
    else:
        cand.grasp_point_mm = grasp_cam


def score_candidates(candidates: List[Candidate], calib, cfg: Config,
                     image_shape: Tuple[int, int]) -> Tuple[List[Candidate], List[dict]]:
    rejected: List[dict] = []
    if not candidates:
        return [], rejected

    for cand in candidates:
        cand.occlusion_ratio = float(cand.pair.outer.support_ratio)
        cand.visibility_raw = float(cand.pair.outer.support_ratio)

    # Normiranje na najbolje viden kos v sceni (glej opombo v config.yaml).
    if bool(cfg["scoring.occlusion_normalise"]):
        solid = [c.visibility_raw for c in candidates if c.pair.paired]
        pool = solid if solid else [c.visibility_raw for c in candidates]
        reference = float(np.percentile(pool, float(cfg["scoring.occlusion_reference_percentile"]))) \
            if pool else 0.0
        if reference >= float(cfg["scoring.occlusion_reference_floor"]):
            for cand in candidates:
                cand.occlusion_ratio = float(np.clip(cand.visibility_raw / reference, 0.0, 1.0))
            normalisation = {"reference": round(reference, 3), "applied": True}
        else:
            normalisation = {"reference": round(reference, 3), "applied": False,
                             "reason": "tudi najbolje viden kos ima presibek kontrast - "
                                       "normiranje bi napihnilo vse vidnosti"}
    else:
        normalisation = {"applied": False, "reason": "izklopljeno v configu"}

    for cand in candidates:
        analyse_ring(cand, candidates, calib, cfg, image_shape)

    w_mm = float(cfg["box.w_mm"])
    h_mm = float(cfg["box.h_mm"])
    for cand in candidates:
        if calib.frame_reliable and cand.pose.center_box is not None:
            x, y = float(cand.pose.center_box[0]), float(cand.pose.center_box[1])
            cand.wall_margin_mm = float(min(x, w_mm - x, y, h_mm - y))
        else:
            cand.wall_margin_mm = float("nan")

    heights = []
    for cand in candidates:
        if calib.frame_reliable and cand.pose.center_box is not None:
            heights.append(float(cand.pose.center_box[2]))
        else:
            heights.append(-cand.depth)        # blizje kameri = visje
    heights = np.asarray(heights, dtype=float)
    h_lo, h_hi = float(heights.min()), float(heights.max())
    span = h_hi - h_lo

    weights = dict(cfg.section("scoring.weights").as_dict())
    if not calib.frame_reliable:
        # Brez okvira zaboja visina izhaja iz globine, ta pa ima pri 1-2 mm
        # debelih kosih vecjo negotovost od razmika plasti - clen je cist sum.
        # Enako velja za oddaljenost od sten. Rangiranje takrat nosita vidnost
        # in zaupanje.
        weights.pop("height", None)
        weights.pop("wall_margin", None)
    w_sum = sum(float(v) for v in weights.values()) or 1.0
    tilt_full = float(cfg["scoring.tilt_full_penalty_deg"])
    wall_good = float(cfg["scoring.wall_margin_good_mm"])
    min_arc = float(cfg["scoring.min_free_arc_deg"])
    max_tilt = float(cfg["pose.max_tilt_deg"])
    require_cup = bool(cfg["gripper.require_full_cup_clearance"])

    z_lo = float(cfg["scoring.z_min_mm"])
    z_hi = float(cfg["scoring.z_max_mm"])
    # Ko je okvir zaboja znan, je znana tudi pricakovana velikost kosa v sliki.
    # Referenca mora biti NEODVISNA od elipse: merilo dna iz homografije. (Globina,
    # izpeljana iz iste elipse, da razmerje 1 po konstrukciji in ne pove nicesar.)
    # Kos visje v kupu je videti vecji, zato je zgornja meja ohlapna; zlepek kontur
    # vec dotikajocih se kosov pa je vecji za faktor 2 in vec.
    size_lo = float(cfg["scoring.size_ratio_min"])
    size_hi = float(cfg["scoring.size_ratio_max"])
    r_out_mm = float(cfg["flange.d_out_mm"]) / 2.0
    h_inv = None
    if calib.homography is not None:
        try:
            h_inv = np.linalg.inv(calib.homography)
        except np.linalg.LinAlgError:
            h_inv = None
    max_occ = float(cfg["scoring.max_occlusion"])
    kept: List[Candidate] = []
    for cand, height in zip(candidates, heights):
        size_ratio = None
        if h_inv is not None and cand.pair.role == "outer":
            hom = h_inv @ np.array([cand.pair.outer.cx, cand.pair.outer.cy, 1.0])
            if abs(hom[2]) > 1e-12:
                scale = _homography_scale(calib.homography, hom[:2] / hom[2])
                if scale and scale > 0:
                    size_ratio = cand.pair.outer.a / (scale * r_out_mm)
        if cand.occlusion_ratio < 1.0 - max_occ:
            cand.rejected = (f"prekritih {100.0 * (1.0 - cand.occlusion_ratio):.0f} % oboda, "
                             f"dovoljeno je {100.0 * max_occ:.0f} % - kos ni na vrhu")
        elif size_ratio is not None and not (size_lo <= size_ratio <= size_hi):
            cand.rejected = (f"velikost elipse ne ustreza kosu: izmerjena je {size_ratio:.2f}-krat "
                             "pricakovana za ta polozaj (najbrz zlepek kontur vec kosov)")
        elif calib.frame_reliable and cand.pose.center_box is not None and not (
                z_lo <= float(cand.pose.center_box[2]) <= z_hi):
            cand.rejected = (f"visina {float(cand.pose.center_box[2]):.1f} mm nad dnom je izven "
                             f"verjetnega obsega [{z_lo:.0f}, {z_hi:.0f}] mm - elipsa najbrz "
                             "ni obris prirobnice")
        elif cand.pose.tilt_deg > max_tilt:
            cand.rejected = f"naklon {cand.pose.tilt_deg:.1f} deg presega mejo {max_tilt:.0f} deg"
        elif cand.free_arc_deg < min_arc:
            cand.rejected = (f"prost lok kolobarja {cand.free_arc_deg:.0f} deg je manjsi od "
                             f"{min_arc:.0f} deg")
        elif require_cup and cand.cup_fit_ratio < 1.0:
            cand.rejected = ("cascica sirine "
                             f"{cfg['gripper.suction_cup_diameter_mm']} mm ne nalega v kolobar "
                             f"sirine {(float(cfg['flange.d_out_mm']) - float(cfg['flange.d_in_mm'])) / 2.0:.1f} mm")
        if cand.rejected:
            rejected.append({"center_px": [round(float(cand.pair.outer.cx), 1),
                                           round(float(cand.pair.outer.cy), 1)],
                             "reason": cand.rejected})
            continue

        t_height = 1.0 if span < 1e-6 else float((height - h_lo) / span)
        t_tilt = float(np.clip(1.0 - cand.pose.tilt_deg / max(tilt_full, 1e-6), 0.0, 1.0))
        t_occl = float(np.clip(cand.occlusion_ratio, 0.0, 1.0))
        t_wall = 0.5 if math.isnan(cand.wall_margin_mm) else float(
            np.clip(cand.wall_margin_mm / max(wall_good, 1e-6), 0.0, 1.0))
        t_cup = float(np.clip(cand.free_arc_deg / 360.0, 0.0, 1.0)) * cand.cup_fit_ratio
        t_conf = float(np.clip(cand.pose.confidence, 0.0, 1.0))
        cand.terms = {"height": t_height, "tilt": t_tilt, "occlusion": t_occl,
                      "wall_margin": t_wall, "cup_clearance": t_cup,
                      "confidence": t_conf}
        cand.score = float(sum(float(w) * cand.terms[k] for k, w in weights.items()) / w_sum)
        kept.append(cand)

    for cand in candidates:
        cand.notes.append(f"vidnost surova={cand.visibility_raw:.2f}")
    kept.sort(key=lambda c: -c.score)

    # Potlacitev podvojenih: vec fitov istega kosa (iz razlicnih virov ali lokov)
    # se v sliki prekriva. Obdrzimo najbolje ocenjenega.
    nms_frac = float(cfg["scoring.duplicate_centre_frac"])
    if nms_frac > 0:
        survivors: List[Candidate] = []
        for cand in kept:
            duplicate = False
            for other in survivors:
                dist = float(np.linalg.norm(cand.pair.outer.center - other.pair.outer.center))
                if dist < nms_frac * max(cand.pair.outer.a, other.pair.outer.a):
                    duplicate = True
                    break
            if duplicate:
                cand.rejected = "podvojena detekcija istega kosa"
                rejected.append({"center_px": [round(float(cand.pair.outer.cx), 1),
                                               round(float(cand.pair.outer.cy), 1)],
                                 "reason": cand.rejected})
            else:
                survivors.append(cand)
        kept = survivors

    min_score = float(cfg["scoring.min_score"])
    final = []
    for cand in kept:
        if cand.score < min_score:
            cand.rejected = f"ocena {cand.score:.3f} pod pragom {min_score:.3f}"
            rejected.append({"center_px": [round(float(cand.pair.outer.cx), 1),
                                           round(float(cand.pair.outer.cy), 1)],
                             "reason": cand.rejected})
            continue
        final.append(cand)
    return final, rejected
