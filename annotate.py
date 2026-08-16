#!/usr/bin/env python3
"""Slika z oznacenim mestom seska in kotom prijema.

    python annotate.py slika.jpg --top 5 --out oznaceno.png

Za vsak kandidat narise:
  - obris kosa (zeleno = prvi, oranzno = ostali),
  - krog v PRAVI velikosti sesalne cascice na mestu prijema, projiciran v
    ravnino kosa (torej se vidi, ali cascica dejansko nalega),
  - puscico v smeri, v katero je kos nagnjen (kamor mora robot nagniti
    prijemalo); dolzina puscice je sorazmerna naklonu,
  - oznako z naklonom in azimutom.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import List, Optional

import cv2
import numpy as np

from flange_picker.config import load_config
from flange_picker.pipeline import process_file
from flange_picker.pose import project_points
from flange_picker.scoring import _plane_basis

GREEN = (60, 220, 60)
ORANGE = (0, 165, 255)
RED = (60, 60, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def _label(img, text, org, colour, scale=0.6, thick=2):
    """Besedilo s temno obrobo, da je berljivo na svetli in temni podlagi."""
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, BLACK, thick + 3, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, colour, thick, cv2.LINE_AA)


def annotate(image: np.ndarray, result, cfg, top: int) -> np.ndarray:
    out = image.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    overlay = out.copy()
    cup_r = float(cfg["gripper.suction_cup_diameter_mm"]) / 2.0
    flat_deg = float(cfg["pose.unpaired_ambiguous_tilt_deg"])
    calib = result.calibration

    for rank, cand in enumerate(result.candidates[:top]):
        pose = cand.pose
        colour = GREEN if rank == 0 else ORANGE
        ell = cand.pair.outer
        cv2.ellipse(out, (int(ell.cx), int(ell.cy)), (int(ell.a), int(ell.b)),
                    math.degrees(ell.theta), 0, 360, colour, 3 if rank == 0 else 2, cv2.LINE_AA)

        if cand.grasp_point_px is None:
            continue
        gp = cand.grasp_point_px

        # Cascica v pravi velikosti, projicirana v ravnino kosa.
        u, v = _plane_basis(pose.normal_cam,
                            calib.rot_box[:, 0] if calib.rot_box is not None else None)
        ring = []
        for t in np.linspace(0, 2 * math.pi, 48, endpoint=False):
            # krog polmera cup_r okoli prijemne tocke, v ravnini kosa
            pt = (_grasp_cam(cand, pose, calib) + cup_r * (math.cos(t) * u + math.sin(t) * v))
            ring.append(pt)
        cup_px = project_points(np.array(ring), calib.k_mat).astype(np.int32)
        cv2.fillPoly(overlay, [cup_px], colour)
        cv2.polylines(out, [cup_px], True, colour, 2, cv2.LINE_AA)
        cv2.drawMarker(out, (int(gp[0]), int(gp[1])), WHITE, cv2.MARKER_CROSS, 12, 2)

        # Smer nagiba: puscica kaze, kam je kos nagnjen (kamor se nagne prijemalo).
        tilt = pose.tilt_deg
        if tilt > flat_deg:
            normal = pose.normal_box if pose.normal_box is not None else pose.normal_cam
            # smer nagiba v ravnini kosa, projicirana v sliko
            down = np.array([float(normal[0]), float(normal[1])])
            if np.linalg.norm(down) > 1e-6:
                down = down / np.linalg.norm(down)
                if calib.rot_box is not None:
                    world_dir = calib.rot_box @ np.array([down[0], down[1], 0.0])
                else:
                    world_dir = np.array([down[0], down[1], 0.0])
                length_mm = float(cfg["flange.d_out_mm"]) * 0.5 * min(tilt / 45.0, 1.2)
                tip_cam = _grasp_cam(cand, pose, calib) + world_dir * length_mm
                tip = project_points(tip_cam[None, :], calib.k_mat)[0]
                cv2.arrowedLine(out, (int(gp[0]), int(gp[1])), (int(tip[0]), int(tip[1])),
                                RED, 3, cv2.LINE_AA, tipLength=0.3)

        text = f"#{rank + 1} naklon {tilt:.0f}"
        if pose.orientation_ambiguous:
            text += " (smer NEZANESLJIVA)"
        else:
            text += f" azimut {pose.azimuth_deg:.0f}"
        _label(out, text, (int(ell.cx - ell.a), int(ell.cy - ell.b - 12)), colour, 0.6, 2)

    out = cv2.addWeighted(overlay, 0.35, out, 0.65, 0)
    _panel(out, result, cfg, top)
    return out


def _grasp_cam(cand, pose, calib) -> np.ndarray:
    """Prijemna tocka nazaj v kamerinem sistemu."""
    if calib.rot_box is not None and calib.t_box is not None and cand.grasp_point_mm is not None:
        return calib.rot_box @ np.asarray(cand.grasp_point_mm, dtype=float) + calib.t_box
    if cand.grasp_point_mm is not None:
        return np.asarray(cand.grasp_point_mm, dtype=float)
    return pose.center_cam


def _panel(img, result, cfg, top: int) -> None:
    lines = [f"kosov najdenih: {len(result.candidates)}",
             f"okvir: {'zaboj' if result.calibration.frame_reliable else 'kamera (rel. rangiranje)'}",
             f"cascica {cfg['gripper.suction_cup_diameter_mm']:g} mm, "
             f"kos {cfg['flange.d_out_mm']:g}/{cfg['flange.d_in_mm']:g} mm"]
    for rank, cand in enumerate(result.candidates[:top]):
        pose = cand.pose
        pos = (f"x={pose.center_box[0]:.0f} y={pose.center_box[1]:.0f} z={pose.center_box[2]:.0f}"
               if pose.center_box is not None else "koordinate niso zanesljive")
        lines.append(f"#{rank + 1} {pos} naklon={pose.tilt_deg:.0f} "
                     f"azimut={pose.azimuth_deg:.0f} zaup={pose.confidence:.2f}")
    h = 26 * len(lines) + 16
    cv2.rectangle(img, (8, 8), (8 + 640, 8 + h), BLACK, -1)
    for i, line in enumerate(lines):
        cv2.putText(img, line, (18, 36 + 26 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    GREEN if i > 2 else WHITE, 2, cv2.LINE_AA)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Oznaci mesto seska in kot prijema")
    parser.add_argument("image")
    parser.add_argument("--config", default=None)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--out", default="oznaceno.png")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    result = process_file(args.image, cfg)
    image = cv2.imread(args.image, cv2.IMREAD_COLOR)
    if image is None:
        print(f"slike ni bilo mogoce prebrati: {args.image}", file=sys.stderr)
        return 1
    if not result.candidates:
        print("noben kandidat ni bil najden", file=sys.stderr)
        for w in result.warnings:
            print(f"  opozorilo: {w}", file=sys.stderr)
    cv2.imwrite(args.out, annotate(image, result, cfg, args.top))
    print(f"zapisano: {args.out}  ({len(result.candidates)} kandidatov)")
    for w in result.warnings:
        print(f"opozorilo: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
