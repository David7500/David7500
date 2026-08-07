"""Orkestracija cevovoda in JSON izhod.

Vsak korak vrne diagnostiko namesto izjeme; prazna slika da prazno listo
kandidatov, ne napake.
"""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cv2
import numpy as np

from . import autocalib as autocalib_mod
from .config import Config, load_config
from .edges import detect_edges
from .ellipse import (compute_polarity, compute_support, deduplicate, fit_contour,
                      pair_ellipses)
from .pose import build_flange_pose
from .preprocess import preprocess, to_gray
from .scoring import Candidate, score_candidates

LOG = logging.getLogger("flange_picker")


@dataclass
class Result:
    calibration: autocalib_mod.Calibration
    candidates: List[Candidate]
    diagnostics: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    rejected: List[Dict] = field(default_factory=list)

    def to_json(self, cfg: Config) -> Dict:
        nd = int(cfg["output.round_decimals"])
        limit = int(cfg["output.max_candidates"])

        def r(value) -> float:
            return round(float(value), nd)

        out_candidates = []
        for cand in self.candidates[:limit]:
            pose = cand.pose
            center = pose.center_box if pose.center_box is not None else pose.center_cam
            normal = pose.normal_box if pose.normal_box is not None else pose.normal_cam
            grasp = cand.grasp_point_mm
            out_candidates.append({
                "x_mm": r(center[0]), "y_mm": r(center[1]), "z_mm": r(center[2]),
                "tilt_deg": r(pose.tilt_deg), "azimuth_deg": r(pose.azimuth_deg),
                "normal": [r(normal[0]), r(normal[1]), r(normal[2])],
                "grasp_point_mm": None if grasp is None else [r(grasp[0]), r(grasp[1]), r(grasp[2])],
                "occlusion_ratio": r(cand.occlusion_ratio),
                "score": r(cand.score),
                "confidence": r(pose.confidence),
                "free_arc_deg": r(cand.free_arc_deg),
                "cup_fit_ratio": r(cand.cup_fit_ratio),
                "wall_margin_mm": None if math.isnan(cand.wall_margin_mm) else r(cand.wall_margin_mm),
                "paired": bool(pose.paired),
                "ellipse_px": {k: r(v) if isinstance(v, float) else v
                               for k, v in cand.pair.outer.to_dict().items()},
                "notes": pose.reasons + cand.notes,
            })
        return {
            "frame": "box" if self.calibration.frame_reliable else "camera",
            "frame_reliable": bool(self.calibration.frame_reliable),
            "calibration": self.calibration.to_dict(),
            "candidates": out_candidates,
            "warnings": self.warnings,
            "rejected": self.rejected,
            "diagnostics": self.diagnostics,
        }


def process_image(image: np.ndarray, cfg: Optional[Config] = None, debug: bool = False,
                  debug_dir: Optional[str] = None, debug_prefix: str = "step") -> Result:
    cfg = cfg or load_config()
    warnings: List[str] = []
    diagnostics: Dict = {}

    if image is None or getattr(image, "size", 0) == 0:
        calib = autocalib_mod.Calibration(
            k_mat=np.eye(3), f_px=float(cfg["autocalib.fallback_f_px"]),
            principal_point=(0.0, 0.0), method="degraded_relative_only", confidence=0.0,
            warnings=["prazna slika"])
        return Result(calibration=calib, candidates=[], diagnostics={"empty_image": True},
                      warnings=["prazna slika - prazna lista kandidatov"])

    gray_raw = to_gray(image)
    pre = preprocess(gray_raw, cfg)
    diagnostics["preprocess"] = pre.diagnostics

    edge_map = detect_edges(pre.gray, cfg, exclude_mask=pre.specular_mask,
                            gradient_image=pre.raw_gray)
    diagnostics["edges"] = edge_map.diagnostics

    raw_ellipses = []
    for contour in edge_map.contours:
        raw_ellipses.extend(fit_contour(contour, cfg))
    ellipses = deduplicate(raw_ellipses, cfg)
    compute_support(ellipses, edge_map.points, cfg)
    compute_polarity(ellipses, edge_map.gx, edge_map.gy, cfg)
    min_support = float(cfg["ellipse.min_support_ratio"])
    weak = [e for e in ellipses if e.support_ratio < min_support]
    ellipses = [e for e in ellipses if e.support_ratio >= min_support]
    diagnostics["ellipses"] = {
        "n_raw": len(raw_ellipses), "n_after_dedup": len(ellipses) + len(weak),
        "n_kept": len(ellipses), "n_low_support": len(weak),
    }

    pairs, pair_rejected = pair_ellipses(ellipses, cfg)
    diagnostics["pairs"] = {
        "n_pairs": sum(1 for p in pairs if p.paired),
        "n_unpaired": sum(1 for p in pairs if not p.paired),
        "rejected": pair_rejected[:20],
    }

    calib = autocalib_mod.calibrate(pre.gray, pairs, cfg, edge_points=edge_map.points)
    diagnostics["autocalib"] = calib.diagnostics
    warnings.extend(calib.warnings)

    candidates: List[Candidate] = []
    rejected: List[Dict] = []
    for pair in pairs:
        pose = build_flange_pose(pair, calib.k_mat, cfg, calib.rot_box, calib.t_box)
        if pose is None:
            rejected.append({"center_px": [round(pair.outer.cx, 1), round(pair.outer.cy, 1)],
                             "reason": "poze iz elipse ni bilo mogoce izracunati"})
            continue
        candidates.append(Candidate(pair=pair, pose=pose))

    scale_check = autocalib_mod.scale_consistency_check(candidates, calib, cfg)
    diagnostics["scale_check"] = scale_check
    if scale_check.get("ok") is False:
        # Merilo dna in izmerjeni premeri si nasprotujeta: detektirani pravokotnik
        # skoraj gotovo ni dno zaboja. Lazen okvir je slabsi od nobenega - raje se
        # degradiramo na relativno rangiranje, kot da bi vrnili napacne koordinate.
        warnings.append("preverjanje merila: " + str(scale_check.get("reason", ""))
                        + " - koordinatni sistem zaboja zavrnjen, ostaja relativno rangiranje")
        calib.frame_reliable = False
        calib.rot_box = None
        calib.t_box = None
        calib.confidence = 0.0
        calib.method = "degraded_relative_only"
        candidates = []
        for pair in pairs:
            pose = build_flange_pose(pair, calib.k_mat, cfg, None, None)
            if pose is not None:
                candidates.append(Candidate(pair=pair, pose=pose))

    ranked, score_rejected = score_candidates(candidates, calib, cfg, gray_raw.shape[:2])
    rejected.extend(score_rejected)

    cup_d = float(cfg["gripper.suction_cup_diameter_mm"])
    ring_width = (float(cfg["flange.d_out_mm"]) - float(cfg["flange.d_in_mm"])) / 2.0
    if cup_d > ring_width:
        warnings.append(
            f"sesalna cascica ({cup_d:g} mm) je sirsa od kolobarja prirobnice "
            f"({ring_width:g} mm) - polnega naleganja ni mogoce doseci")

    result = Result(calibration=calib, candidates=ranked, diagnostics=diagnostics,
                    warnings=warnings, rejected=rejected)

    if debug:
        write_debug(image, pre, edge_map, ellipses, ranked, calib, cfg,
                    debug_dir or cfg["debug.dir"], debug_prefix)
    return result


def process_file(path: str, cfg: Optional[Config] = None, debug: bool = False,
                 debug_dir: Optional[str] = None) -> Result:
    cfg = cfg or load_config()
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        calib = autocalib_mod.Calibration(k_mat=np.eye(3),
                                          f_px=float(cfg["autocalib.fallback_f_px"]),
                                          principal_point=(0.0, 0.0),
                                          method="degraded_relative_only", confidence=0.0)
        return Result(calibration=calib, candidates=[],
                      diagnostics={"read_error": path},
                      warnings=[f"slike ni bilo mogoce prebrati: {path}"])
    prefix = os.path.splitext(os.path.basename(path))[0]
    return process_image(image, cfg, debug=debug, debug_dir=debug_dir, debug_prefix=prefix)


# --------------------------------------------------------------------------
# debug overlay-i
# --------------------------------------------------------------------------
def write_debug(image, pre, edge_map, ellipses, candidates, calib, cfg: Config,
                out_dir: str, prefix: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    thick = int(cfg["debug.overlay_thickness"])

    def save(name: str, img) -> None:
        cv2.imwrite(os.path.join(out_dir, f"{prefix}_{name}.png"), img)

    save("1_preprocess", pre.gray)
    save("2_specular", pre.specular_mask)
    save("3_canny", edge_map.mask)

    color = cv2.cvtColor(pre.raw_gray, cv2.COLOR_GRAY2BGR)
    for pt in edge_map.points[::3]:
        cv2.circle(color, (int(round(pt[0])), int(round(pt[1]))), 0, (0, 180, 255), -1)
    save("4_subpixel_edges", color)

    color = cv2.cvtColor(pre.raw_gray, cv2.COLOR_GRAY2BGR)
    for ell in ellipses:
        cv2.ellipse(color, (int(ell.cx), int(ell.cy)), (int(ell.a), int(ell.b)),
                    math.degrees(ell.theta), 0, 360, (0, 255, 0), thick)
    save("5_ellipses", color)

    color = cv2.cvtColor(pre.raw_gray, cv2.COLOR_GRAY2BGR)
    if calib.quad_px is not None:
        quad = calib.quad_px.astype(np.int32)
        cv2.polylines(color, [quad], True, (255, 0, 255), max(2, thick))
        for i, pt in enumerate(quad):
            cv2.putText(color, str(i), tuple(pt), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 0, 255), 2)
    cv2.putText(color, f"f={calib.f_px:.0f}px conf={calib.confidence:.2f} {calib.method}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    save("6_autocalib", color)

    color = cv2.cvtColor(pre.raw_gray, cv2.COLOR_GRAY2BGR)
    for rank, cand in enumerate(candidates):
        ell = cand.pair.outer
        shade = (0, 255, 0) if rank == 0 else (0, 165, 255)
        cv2.ellipse(color, (int(ell.cx), int(ell.cy)), (int(ell.a), int(ell.b)),
                    math.degrees(ell.theta), 0, 360, shade, max(2, thick))
        if cand.pair.inner is not None:
            inner = cand.pair.inner
            cv2.ellipse(color, (int(inner.cx), int(inner.cy)), (int(inner.a), int(inner.b)),
                        math.degrees(inner.theta), 0, 360, (255, 200, 0), thick)
        if cand.grasp_point_px is not None:
            gp = cand.grasp_point_px
            cv2.drawMarker(color, (int(gp[0]), int(gp[1])), (0, 0, 255),
                           cv2.MARKER_CROSS, 16, 2)
        cv2.putText(color, f"#{rank} s={cand.score:.2f} t={cand.pose.tilt_deg:.0f}",
                    (int(ell.cx - ell.a), int(ell.cy - ell.a - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, shade, 1)
    save("7_candidates", color)


def result_to_json_string(result: Result, cfg: Config) -> str:
    return json.dumps(result.to_json(cfg), indent=2, ensure_ascii=False)
