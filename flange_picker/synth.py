"""Generator sinteticnih scen z znano ground truth pozo.

To je primarni testni set: brez njega ni nacina, da bi izmerili RMSE po Z, tilt
in XY ali natancnost ocene f_px. Renderira perspektivo, spekularne odseve, sum
in delno prekrivanje kosov.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .config import Config, load_config
from .pose import circle_points_3d, project_points

# fillPoly rasterizira trdo (brez glajenja robov) in tako sistematicno napihne
# polmer za ~0.5 px, kar bi se v meritvah kazalo kot lazna pristranskost Z.
# Zato renderiramo nadvzorceno in sele nato zmanjsamo - tako dobimo pravo
# pokritost piksla. Fiksna vejica (shift) poskrbi se za subpixel geometrijo.
_SHIFT = 5
_SCALE = 1 << _SHIFT


def _poly(points: np.ndarray) -> np.ndarray:
    return np.round(np.asarray(points, dtype=float) * _SCALE).astype(np.int32)


@dataclass
class Scene:
    image: np.ndarray
    ground_truth: Dict
    meta: Dict = field(default_factory=dict)


def _look_down_camera(box_w: float, box_h: float, distance_mm: float,
                      tilt_deg: float, roll_deg: float, offset_mm: Tuple[float, float],
                      rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
    """Vrne (R_wc, t_wc): kamera gleda navpicno navzdol z majhnim nagibom.

    Osnovna orientacija: x_cam ~ +X zaboja, y_cam ~ -Y zaboja, z_cam ~ -Z zaboja.
    """
    base = np.array([[1.0, 0.0, 0.0],
                     [0.0, -1.0, 0.0],
                     [0.0, 0.0, -1.0]])
    ax = rng.normal(size=3)
    ax /= np.linalg.norm(ax)
    ang = math.radians(tilt_deg)
    kmat = np.array([[0.0, -ax[2], ax[1]], [ax[2], 0.0, -ax[0]], [-ax[1], ax[0], 0.0]])
    r_small = np.eye(3) + math.sin(ang) * kmat + (1 - math.cos(ang)) * (kmat @ kmat)
    cr, sr = math.cos(math.radians(roll_deg)), math.sin(math.radians(roll_deg))
    r_roll = np.array([[cr, -sr, 0.0], [sr, cr, 0.0], [0.0, 0.0, 1.0]])
    rot = r_roll @ r_small @ base
    eye = np.array([box_w / 2.0 + offset_mm[0], box_h / 2.0 + offset_mm[1], distance_mm])
    t = -rot @ eye
    return rot, t


def _place_flanges_dense(cfg: Config, rng: np.random.Generator, n: int) -> List[Dict]:
    """Poln zaboj: kosi v vec plasteh, dno ni vec vidno.

    Realna slika iz proizvodnje je taka - zaboj je poln, dna ni videti, zato
    koordinatnega sistema iz dna ni mogoce dobiti. To je kljucen testni primer.
    """
    d_out = float(cfg["flange.d_out_mm"])
    thick = 0.5 * (float(cfg["flange.thickness_min_mm"]) + float(cfg["flange.thickness_max_mm"]))
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])
    margin = float(cfg["synth.dense_wall_margin_mm"])
    max_tilt = float(cfg["synth.dense_tilt_deg_max"])
    placed: List[Dict] = []
    for _ in range(n):
        x = float(rng.uniform(margin, w_mm - margin))
        y = float(rng.uniform(margin, h_mm - margin))
        below = [p for p in placed if math.hypot(p["x_mm"] - x, p["y_mm"] - y) < d_out * 0.9]
        z = (max(p["z_mm"] for p in below) + thick) if below else thick / 2.0
        tilt = float(abs(rng.normal(0.0, max_tilt / 2.0))) if below else \
            abs(float(rng.normal(0.0, float(cfg["synth.flat_tilt_deg_sigma"]))))
        placed.append({"x_mm": x, "y_mm": y, "z_mm": z,
                       "tilt_deg": min(tilt, max_tilt),
                       "azimuth_deg": float(rng.uniform(0.0, 360.0))})
    return placed


def _place_flanges(cfg: Config, rng: np.random.Generator, n: int) -> List[Dict]:
    d_out = float(cfg["flange.d_out_mm"])
    thick = 0.5 * (float(cfg["flange.thickness_min_mm"]) + float(cfg["flange.thickness_max_mm"]))
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])
    margin = float(cfg["synth.wall_margin_mm"])
    stack_tilt = float(cfg["synth.stacked_tilt_deg_max"])
    flat_tilt = float(cfg["synth.flat_tilt_deg_sigma"])

    placed: List[Dict] = []
    for _ in range(n):
        for _try in range(int(cfg["synth.placement_attempts"])):
            x = float(rng.uniform(margin, w_mm - margin))
            y = float(rng.uniform(margin, h_mm - margin))
            near = [p for p in placed
                    if math.hypot(p["x_mm"] - x, p["y_mm"] - y) < d_out]
            if near and rng.random() > float(cfg["synth.stack_probability"]):
                continue
            if near:
                base = max(p["z_mm"] for p in near)
                z = base + thick
                tilt = float(rng.uniform(stack_tilt * 0.2, stack_tilt))
            else:
                z = thick / 2.0
                tilt = abs(float(rng.normal(0.0, flat_tilt)))
            az = float(rng.uniform(0.0, 360.0))
            placed.append({"x_mm": x, "y_mm": y, "z_mm": z,
                           "tilt_deg": tilt, "azimuth_deg": az})
            break
    return placed


def _annotate_visibility(entries: List[Dict], r_out: float, k_mat: np.ndarray,
                         image_size: Tuple[int, int], n_samples: int = 180) -> None:
    """Doda vsakemu kosu delez oboda, ki ga ne prekriva noben blizji kos."""
    width, height = image_size
    discs = []
    for e in entries:
        centre = np.array(e["center_cam"])
        normal = np.array(e["normal_cam"])
        poly = project_points(circle_points_3d(centre, normal, r_out, 96), k_mat)
        discs.append((float(e["depth_mm"]), poly.astype(np.float32)))
        e["centre_px"] = project_points(centre[None, :], k_mat)[0].tolist()
    for e, (depth, _) in zip(entries, discs):
        centre = np.array(e["center_cam"])
        normal = np.array(e["normal_cam"])
        rim = project_points(circle_points_3d(centre, normal, r_out, n_samples), k_mat)
        visible = 0
        for pt in rim:
            if not (0 <= pt[0] < width and 0 <= pt[1] < height):
                continue
            blocked = False
            for other_depth, poly in discs:
                if other_depth >= depth - 1e-9:
                    continue
                if cv2.pointPolygonTest(poly, (float(pt[0]), float(pt[1])), False) >= 0:
                    blocked = True
                    break
            if not blocked:
                visible += 1
        e["visible_fraction"] = float(visible) / float(n_samples)


def _plane_axes(normal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    helper = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(n, helper)
    u /= np.linalg.norm(u)
    return u, np.cross(n, u)


def _normal_from_angles(tilt_deg: float, az_deg: float) -> np.ndarray:
    t, a = math.radians(tilt_deg), math.radians(az_deg)
    return np.array([math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t)])


def render_scene(cfg: Optional[Config] = None, seed: int = 0,
                 n_flanges: Optional[int] = None,
                 camera_tilt_deg: Optional[float] = None,
                 f_px: Optional[float] = None,
                 specular: Optional[bool] = None,
                 flanges: Optional[List[Dict]] = None) -> Scene:
    cfg = cfg or load_config()
    rng = np.random.default_rng(seed)

    width = int(cfg["synth.image_width"])
    height = int(cfg["synth.image_height"])
    if f_px is None:
        f_px = float(rng.uniform(float(cfg["synth.f_px_min"]), float(cfg["synth.f_px_max"])))
    if camera_tilt_deg is None:
        camera_tilt_deg = float(rng.uniform(0.0, float(cfg["synth.camera_tilt_deg_max"])))
    if n_flanges is None:
        n_flanges = int(rng.integers(int(cfg["synth.n_flanges_min"]),
                                     int(cfg["synth.n_flanges_max"]) + 1))
    if specular is None:
        specular = bool(cfg["synth.specular_enabled"])

    k_mat = np.array([[f_px, 0.0, width / 2.0], [0.0, f_px, height / 2.0], [0.0, 0.0, 1.0]])
    ss = max(1, int(cfg["synth.supersample"]))
    k_render = np.diag([float(ss), float(ss), 1.0]) @ k_mat
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])
    distance = float(rng.uniform(float(cfg["synth.distance_mm_min"]),
                                 float(cfg["synth.distance_mm_max"])))
    offs = float(cfg["synth.camera_offset_mm"])
    rot, tvec = _look_down_camera(w_mm, h_mm, distance, camera_tilt_deg,
                                  float(rng.uniform(-float(cfg["synth.camera_roll_deg_max"]),
                                                    float(cfg["synth.camera_roll_deg_max"]))),
                                  (float(rng.uniform(-offs, offs)), float(rng.uniform(-offs, offs))),
                                  rng)

    def to_cam(pts_box: np.ndarray) -> np.ndarray:
        return (rot @ np.asarray(pts_box, dtype=float).reshape(-1, 3).T).T + tvec

    def project(pts_box: np.ndarray) -> np.ndarray:
        return project_points(to_cam(pts_box), k_render)

    img = np.full((height * ss, width * ss), float(cfg["synth.background_level"]),
                  dtype=np.float32)

    # stene in dno zaboja
    wall_h = float(cfg["synth.wall_height_mm"])
    bottom = np.array([[0.0, 0.0, 0.0], [w_mm, 0.0, 0.0], [w_mm, h_mm, 0.0], [0.0, h_mm, 0.0]])
    rim = np.array([[-0.0, -0.0, wall_h], [w_mm, -0.0, wall_h],
                    [w_mm, h_mm, wall_h], [0.0, h_mm, wall_h]])
    rim = rim + np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]) * float(
        cfg["synth.wall_thickness_mm"])
    bottom_px = project(bottom)
    rim_px = project(rim)
    bottom_px_img = bottom_px / ss
    for i in range(4):
        quad = _poly(np.array([bottom_px[i], bottom_px[(i + 1) % 4],
                               rim_px[(i + 1) % 4], rim_px[i]]))
        cv2.fillPoly(img, [quad], float(cfg["synth.wall_level"]), shift=_SHIFT)
    cv2.fillPoly(img, [_poly(bottom_px)], float(cfg["synth.bottom_level"]), shift=_SHIFT)

    if flanges is not None:
        specs = flanges
    elif bool(cfg.get("synth.dense_fill", False)):
        specs = _place_flanges_dense(cfg, rng, n_flanges)
    else:
        specs = _place_flanges(cfg, rng, n_flanges)
    r_out = float(cfg["flange.d_out_mm"]) / 2.0
    r_in = float(cfg["flange.d_in_mm"]) / 2.0
    light = np.array(cfg["synth.light_direction"], dtype=float)
    light /= np.linalg.norm(light)

    entries = []
    for spec in specs:
        normal = _normal_from_angles(spec["tilt_deg"], spec["azimuth_deg"])
        center_box = np.array([spec["x_mm"], spec["y_mm"], spec["z_mm"]])
        center_cam = to_cam(center_box)[0]
        normal_cam = rot @ normal
        entries.append({**spec, "normal": normal.tolist(),
                        "center_cam": center_cam.tolist(),
                        "normal_cam": normal_cam.tolist(),
                        "depth_mm": float(center_cam[2])})

    order = np.argsort([-e["depth_mm"] for e in entries])   # slikarjev algoritem
    for idx in order:
        entry = entries[int(idx)]
        center_cam = np.array(entry["center_cam"])
        normal_cam = np.array(entry["normal_cam"])
        outer = project_points(circle_points_3d(center_cam, normal_cam, r_out, 360), k_render)
        inner = project_points(circle_points_3d(center_cam, normal_cam, r_in, 240), k_render)
        lam = abs(float(np.dot(normal_cam / np.linalg.norm(normal_cam), light)))
        shade = float(cfg["synth.metal_level_min"]) + lam * (
            float(cfg["synth.metal_level_max"]) - float(cfg["synth.metal_level_min"]))
        # Senca pod kosom se nariše pred kosom, da ne premakne navideznega
        # obrisa navznoter - sicer je ocena polmera (in s tem Z) pristranska.
        shadow = project_points(
            circle_points_3d(center_cam, normal_cam,
                             r_out * float(cfg["synth.shadow_expand"]), 360), k_render)
        cv2.fillPoly(img, [_poly(shadow)],
                     float(cfg["synth.bottom_level"]) * float(cfg["synth.shadow_darkening"]),
                     shift=_SHIFT)
        before = img.copy()
        cv2.fillPoly(img, [_poly(outer)], shade, shift=_SHIFT)
        hole = np.zeros(img.shape, dtype=np.uint8)
        cv2.fillPoly(hole, [_poly(inner)], 255, shift=_SHIFT)
        n_bolts = int(cfg.get("synth.bolt_hole_count", 0) or 0)
        if n_bolts:
            # Vijacne luknje na kolobarju: v resnicnih kosih jih je vec in so
            # dodaten vir kroznih robov, ki lahko zmedejo parjenje.
            r_bolt_circle = 0.5 * (r_out + r_in) * float(cfg["synth.bolt_circle_factor"])
            r_bolt = 0.5 * float(cfg["synth.bolt_hole_diameter_mm"])
            base_ang = float(rng.uniform(0.0, 2.0 * math.pi))
            u_vec, v_vec = _plane_axes(normal_cam)
            for k in range(n_bolts):
                ang = base_ang + 2.0 * math.pi * k / n_bolts
                centre = (center_cam + r_bolt_circle
                          * (math.cos(ang) * u_vec + math.sin(ang) * v_vec))
                poly = project_points(circle_points_3d(centre, normal_cam, r_bolt, 48), k_render)
                cv2.fillPoly(hole, [_poly(poly)], 255, shift=_SHIFT)
        img[hole > 0] = before[hole > 0]
        # Vzorcek (perforacija) na kolobarju: resnicni kosi ga imajo gostega in
        # je glavni vir laznih robov - brez njega je sinteticna scena prelahka.
        n_dots = int(cfg.get("synth.texture_dot_count", 0) or 0)
        if n_dots:
            r_dot = 0.5 * float(cfg["synth.texture_dot_diameter_mm"])
            u_vec, v_vec = _plane_axes(normal_cam)
            rings = max(1, int(round(math.sqrt(n_dots / 6.0))))
            drawn = 0
            for ring in range(rings):
                rr = r_in * 1.18 + (r_out * 0.92 - r_in * 1.18) * (ring + 0.5) / rings
                per_ring = max(6, int(2.0 * math.pi * rr / (2.6 * r_dot)))
                for k in range(per_ring):
                    if drawn >= n_dots:
                        break
                    ang = 2.0 * math.pi * (k + 0.5 * (ring % 2)) / per_ring
                    centre_dot = center_cam + rr * (math.cos(ang) * u_vec + math.sin(ang) * v_vec)
                    poly = project_points(circle_points_3d(centre_dot, normal_cam, r_dot, 12),
                                          k_render)
                    cv2.fillPoly(img, [_poly(poly)],
                                 shade * float(cfg["synth.texture_darkening"]), shift=_SHIFT)
                    drawn += 1
        if specular and rng.random() < float(cfg["synth.specular_probability"]):
            theta = float(rng.uniform(0, 2 * math.pi))
            r_spec = float(rng.uniform(r_in * 1.15, r_out * 0.92))
            pt = circle_points_3d(center_cam, normal_cam, r_spec, 64)
            k_idx = int((theta / (2 * math.pi)) * 64) % 64
            px = project_points(pt[k_idx][None, :], k_render)[0]
            axes = (int(rng.integers(3, 9)) * ss, int(rng.integers(2, 6)) * ss)
            cv2.ellipse(img, (int(px[0]), int(px[1])), axes,
                        float(rng.uniform(0, 180)), 0, 360, 255.0, -1)

    if ss > 1:                                   # pravilno glajenje robov
        img = img.reshape(height, ss, width, ss).mean(axis=(1, 3))
    blur = float(cfg["synth.blur_sigma"])
    if blur > 0:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    noise = float(cfg["synth.noise_sigma"])
    if noise > 0:
        img = img + rng.normal(0.0, noise, img.shape).astype(np.float32)
    image = np.clip(img, 0, 255).astype(np.uint8)

    # Resnicna vidnost oboda vsakega kosa: delez tock zunanjega kroga, ki jih ne
    # prekriva noben blizji kos. To je merilo, proti kateremu se primerjajo
    # razlicne mere podprtosti obrisa.
    _annotate_visibility(entries, r_out, k_mat, (width, height))

    gt = {
        "f_px": float(f_px),
        "image_size": [width, height],
        "camera": {"R_wc": rot.tolist(), "t_wc": tvec.tolist(),
                   "distance_mm": distance, "tilt_deg": float(camera_tilt_deg)},
        "box": {"w_mm": w_mm, "h_mm": h_mm,
                "corners_px": bottom_px_img.tolist()},
        "flanges": [{k: e[k] for k in
                     ("x_mm", "y_mm", "z_mm", "tilt_deg", "azimuth_deg", "normal", "depth_mm",
                      "visible_fraction", "centre_px")}
                    for e in entries],
        "seed": int(seed),
    }
    return Scene(image=image, ground_truth=gt, meta={"n_flanges": len(entries)})


def generate_dataset(out_dir: str, n_scenes: int, cfg: Optional[Config] = None,
                     seed: int = 0) -> List[str]:
    cfg = cfg or load_config()
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i in range(n_scenes):
        scene = render_scene(cfg, seed=seed + i)
        img_path = os.path.join(out_dir, f"scene_{i:03d}.png")
        gt_path = os.path.join(out_dir, f"scene_{i:03d}.json")
        cv2.imwrite(img_path, scene.image)
        with open(gt_path, "w", encoding="utf-8") as handle:
            json.dump(scene.ground_truth, handle, indent=2)
        paths.append(img_path)
    return paths


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generator sinteticnih scen")
    parser.add_argument("out_dir")
    parser.add_argument("-n", "--n-scenes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    paths = generate_dataset(args.out_dir, args.n_scenes, cfg, args.seed)
    print(f"zapisano {len(paths)} scen v {args.out_dir}")


if __name__ == "__main__":
    main()
