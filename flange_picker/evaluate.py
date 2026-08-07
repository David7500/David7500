"""Meritev natancnosti na sinteticnem setu: RMSE po Z, tilt, XY in napaka f_px.

Koordinatni sistem zaboja ima iz same slike neizogibno 2-kratno dvoumnost
(zasuk za 180 stopinj okoli sredisca dna - pravokotnik brez oznak). Pri
primerjavi z ground truth zato preizkusimo obe poravnavi in vzamemo boljso;
uporabljena poravnava je del izpisa.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import Config, load_config
from .pipeline import process_image
from .pose import project_points
from .synth import render_scene


def _alignments(w_mm: float, h_mm: float) -> List[Tuple[str, np.ndarray, np.ndarray]]:
    """Obe mozni poravnavi: identiteta in zasuk za 180 stopinj v ravnini dna."""
    ident = (np.eye(2), np.zeros(2))
    rot180 = (np.array([[-1.0, 0.0], [0.0, -1.0]]), np.array([w_mm, h_mm]))
    return [("identiteta", *ident), ("zasuk_180", *rot180)]


def _match(pred: np.ndarray, gt: np.ndarray, max_dist_mm: float
           ) -> List[Tuple[int, int, float]]:
    """Pozresno parjenje po najblizji 3D razdalji.

    Parjenje mora upostevati tudi visino: zlozeni kosi imajo skoraj isti XY in
    bi se sicer parili narobe, kar bi se kazalo kot lazna napaka naklona.
    """
    if len(pred) == 0 or len(gt) == 0:
        return []
    dist = np.linalg.norm(pred[:, None, :] - gt[None, :, :], axis=2)
    pairs = []
    used_p, used_g = set(), set()
    order = np.dstack(np.unravel_index(np.argsort(dist, axis=None), dist.shape))[0]
    for i, j in order:
        i, j = int(i), int(j)
        if i in used_p or j in used_g or dist[i, j] > max_dist_mm:
            continue
        used_p.add(i)
        used_g.add(j)
        pairs.append((i, j, float(dist[i, j])))
    return pairs


@dataclass
class SceneMetrics:
    seed: int
    n_gt: int
    n_pred: int
    n_matched: int
    n_detected_px: int = 0        # detekcija v sliki - neodvisna od kalibracije
    frame_reliable: bool = False
    f_px_gt: float = 0.0
    f_px_est: float = 0.0
    calib_method: str = ""
    calib_confidence: float = 0.0
    alignment: str = ""
    xy_rmse_mm: float = float("nan")
    z_rmse_mm: float = float("nan")
    z_bias_mm: float = float("nan")
    tilt_rmse_deg: float = float("nan")
    top1_correct: bool = False
    warnings: List[str] = field(default_factory=list)

    @property
    def f_rel_error(self) -> float:
        return abs(self.f_px_est - self.f_px_gt) / self.f_px_gt if self.f_px_gt else float("nan")


def evaluate_scene(cfg: Config, seed: int, working_distance_rel_error: Optional[float] = None,
                   **scene_kwargs) -> SceneMetrics:
    scene = render_scene(cfg, seed=seed, **scene_kwargs)
    if working_distance_rel_error is not None:
        # Simulira realno stanje: uporabnik pozna delovno razdaljo le priblizno.
        true_wd = float(scene.ground_truth["camera"]["distance_mm"])
        cfg = cfg.with_overrides({"camera": {
            "working_distance_mm": true_wd * (1.0 + working_distance_rel_error)}})
    result = process_image(scene.image, cfg)
    data = result.to_json(cfg)

    gt = scene.ground_truth["flanges"]
    gt_xy = np.array([[f["x_mm"], f["y_mm"]] for f in gt], dtype=float)
    gt_z = np.array([f["z_mm"] for f in gt], dtype=float)
    gt_tilt = np.array([f["tilt_deg"] for f in gt], dtype=float)

    cands = data["candidates"]
    pred_xy_raw = np.array([[c["x_mm"], c["y_mm"]] for c in cands], dtype=float).reshape(-1, 2)
    pred_z = np.array([c["z_mm"] for c in cands], dtype=float)
    pred_tilt = np.array([c["tilt_deg"] for c in cands], dtype=float)

    max_dist = float(cfg["flange.d_out_mm"]) * float(cfg["evaluate.match_radius_factor"])
    gt_xyz = np.concatenate([gt_xy, gt_z[:, None]], axis=1)
    best = None
    for name, rot, off in _alignments(float(cfg["box.w_mm"]), float(cfg["box.h_mm"])):
        pred_xy = (rot @ pred_xy_raw.T).T + off if len(pred_xy_raw) else pred_xy_raw
        pred_xyz = (np.concatenate([pred_xy, pred_z[:, None]], axis=1)
                    if len(pred_xy) else np.zeros((0, 3)))
        matches = _match(pred_xyz, gt_xyz, max_dist)
        if best is None or len(matches) > len(best[1]) or (
                len(matches) == len(best[1]) and matches
                and np.mean([m[2] for m in matches]) < np.mean([m[2] for m in best[1]])):
            best = (name, matches, pred_xy)
    alignment, matches, pred_xy = best

    if matches:
        idx_p = [m[0] for m in matches]
        idx_g = [m[1] for m in matches]
        xy_err = np.linalg.norm(pred_xy[idx_p] - gt_xy[idx_g], axis=1)
        z_err = pred_z[idx_p] - gt_z[idx_g]
        tilt_err = pred_tilt[idx_p] - gt_tilt[idx_g]
        xy_rmse = float(np.sqrt(np.mean(xy_err ** 2)))
        z_rmse = float(np.sqrt(np.mean(z_err ** 2)))
        z_bias = float(np.mean(z_err))
        tilt_rmse = float(np.sqrt(np.mean(tilt_err ** 2)))
        # ali je prvi kandidat res eden od najvisjih kosov?
        top_pred = 0
        top_match = [m for m in matches if m[0] == top_pred]
        if top_match:
            gt_idx = top_match[0][1]
            top1_correct = bool(gt_z[gt_idx] >= np.percentile(gt_z, 70) - 1e-6)
        else:
            top1_correct = False
    else:
        xy_rmse = z_rmse = z_bias = tilt_rmse = float("nan")
        top1_correct = False

    # Detekcija v sliki: primerjava sredisc elips s projiciranimi GT srediscmi.
    # Neodvisna od kalibracije, zato loci "nisem nasel kosa" od "nimam okvira".
    rot_gt = np.array(scene.ground_truth["camera"]["R_wc"], dtype=float)
    t_gt = np.array(scene.ground_truth["camera"]["t_wc"], dtype=float)
    gt_cam = (rot_gt @ np.array([[f["x_mm"], f["y_mm"], f["z_mm"]] for f in gt],
                                dtype=float).T).T + t_gt
    gt_px = project_points(gt_cam, np.array(
        [[scene.ground_truth["f_px"], 0, scene.ground_truth["image_size"][0] / 2.0],
         [0, scene.ground_truth["f_px"], scene.ground_truth["image_size"][1] / 2.0],
         [0, 0, 1.0]]))
    pred_px = np.array([[c["ellipse_px"]["cx"], c["ellipse_px"]["cy"]] for c in cands],
                       dtype=float).reshape(-1, 2)
    px_tol = float(cfg["evaluate.detection_tolerance_px"])
    n_detected_px = len(_match(pred_px, gt_px, px_tol))

    return SceneMetrics(
        seed=seed, n_gt=len(gt), n_pred=len(cands), n_matched=len(matches),
        n_detected_px=n_detected_px, frame_reliable=bool(data["frame_reliable"]),
        f_px_gt=float(scene.ground_truth["f_px"]),
        f_px_est=float(data["calibration"]["f_px"]),
        calib_method=data["calibration"]["method"],
        calib_confidence=float(data["calibration"]["confidence"]),
        alignment=alignment, xy_rmse_mm=xy_rmse, z_rmse_mm=z_rmse, z_bias_mm=z_bias,
        tilt_rmse_deg=tilt_rmse, top1_correct=top1_correct,
        warnings=data["warnings"])


def evaluate_set(cfg: Optional[Config] = None, n_scenes: int = 12, seed0: int = 100,
                 working_distance_rel_error: Optional[float] = None, **scene_kwargs) -> Dict:
    cfg = cfg or load_config()
    per_scene = [evaluate_scene(cfg, seed0 + i, working_distance_rel_error, **scene_kwargs)
                 for i in range(n_scenes)]

    def agg(values: Sequence[float]) -> Optional[float]:
        vals = [v for v in values if v is not None and not math.isnan(v)]
        return float(np.mean(vals)) if vals else None

    n_gt = sum(m.n_gt for m in per_scene)
    n_pred = sum(m.n_pred for m in per_scene)
    n_det = sum(m.n_detected_px for m in per_scene)
    framed = [m for m in per_scene if m.frame_reliable]
    n_gt_f = sum(m.n_gt for m in framed)
    n_matched_f = sum(m.n_matched for m in framed)
    summary = {
        "n_scenes": len(per_scene),
        # detekcija v sliki (neodvisno od kalibracije)
        "detection_recall": round(n_det / n_gt, 4) if n_gt else None,
        "detection_precision": round(n_det / n_pred, 4) if n_pred else None,
        # koordinatni sistem
        "frame_available": round(len(framed) / len(per_scene), 4) if per_scene else None,
        # natancnost poze - le na scenah z veljavnim okvirom zaboja
        "pose_recall": round(n_matched_f / n_gt_f, 4) if n_gt_f else None,
        "xy_rmse_mm": _round(agg([m.xy_rmse_mm for m in framed])),
        "z_rmse_mm": _round(agg([m.z_rmse_mm for m in framed])),
        "z_bias_mm": _round(agg([m.z_bias_mm for m in framed])),
        "tilt_rmse_deg": _round(agg([m.tilt_rmse_deg for m in framed])),
        "f_px_rel_error": _round(agg([m.f_rel_error for m in framed])),
        "top1_is_top_layer": (round(float(np.mean([m.top1_correct for m in framed])), 3)
                              if framed else None),
        "calib_methods": _histogram([m.calib_method for m in per_scene]),
    }
    return {"summary": summary, "scenes": [vars(m) for m in per_scene]}


def _round(value: Optional[float], nd: int = 4) -> Optional[float]:
    return None if value is None else round(float(value), nd)


def _histogram(values: Sequence[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return out


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Metrike na sinteticnem setu")
    parser.add_argument("-n", "--n-scenes", type=int, default=12)
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--config", default=None)
    parser.add_argument("--camera-tilt-deg", type=float, default=None)
    parser.add_argument("--working-distance-rel-error", type=float, default=None,
                        help="poda camera.working_distance_mm z dano relativno napako")
    parser.add_argument("--json", default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    kwargs = {}
    if args.camera_tilt_deg is not None:
        kwargs["camera_tilt_deg"] = args.camera_tilt_deg
    report = evaluate_set(cfg, args.n_scenes, args.seed,
                          working_distance_rel_error=args.working_distance_rel_error, **kwargs)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
