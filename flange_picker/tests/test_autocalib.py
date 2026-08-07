"""Testi autokalibracije: detekcija dna, f iz dveh ravnin, ocena odmika roba."""

from __future__ import annotations

import math

import cv2
import numpy as np
import pytest

from flange_picker.autocalib import (_rim_geometry_valid, box_frame_points, detect_box_quad,
                                     f_from_box_rim, k_from_f, refine_quad_with_edges)
from flange_picker.edges import detect_edges
from flange_picker.ellipse import Ellipse, EllipsePair, apply_edge_bias, estimate_edge_bias
from flange_picker.pipeline import process_image
from flange_picker.preprocess import preprocess, to_gray
from flange_picker.synth import render_scene

from .conftest import flat_flange


def _ordered_gt_quad(scene):
    from flange_picker.autocalib import _order_quad
    return _order_quad(np.array(scene.ground_truth["box"]["corners_px"], dtype=float))


def _detect(cfg, scene):
    pre = preprocess(to_gray(scene.image), cfg)
    edges = detect_edges(pre.gray, cfg, pre.specular_mask, gradient_image=pre.raw_gray)
    quad, diag = detect_box_quad(pre.gray, cfg, raw_gray=pre.raw_gray)
    return quad, diag, edges, pre


def test_box_bottom_is_detected_accurately(cfg):
    scene = render_scene(cfg, seed=200, n_flanges=5, camera_tilt_deg=5.0)
    quad, _, edges, _ = _detect(cfg, scene)
    assert quad is not None, "dna zaboja ni bilo mogoce najti"
    refined, _ = refine_quad_with_edges(quad, edges.points, cfg)
    error = float(np.mean(np.linalg.norm(refined - _ordered_gt_quad(scene), axis=1)))
    assert error < 3.0, f"vogali dna so zgreseni za {error:.1f} px"


def test_corner_refinement_converges_from_coarse_start(cfg):
    """Groba zacetna ocena (npr. iz konveksne ovojnice) mora konvergirati."""
    scene = render_scene(cfg, seed=201, n_flanges=4, camera_tilt_deg=5.0)
    _, _, edges, _ = _detect(cfg, scene)
    gt = _ordered_gt_quad(scene)
    centre = gt.mean(axis=0)
    coarse = centre + (gt - centre) * 1.04          # napihnjen za 4 %
    refined, diag = refine_quad_with_edges(coarse, edges.points, cfg)
    before = float(np.mean(np.linalg.norm(coarse - gt, axis=1)))
    after = float(np.mean(np.linalg.norm(refined - gt, axis=1)))
    assert before > 8.0, "testna zacetna ocena ni dovolj groba"
    assert after < 3.0, f"izostritev ni konvergirala: {before:.1f} -> {after:.1f} px"


def test_box_found_when_flange_touches_bottom_edge(cfg):
    """Kos ob robu prekine konturo dna; segmentacija po obmocjih mora to prezivet."""
    flanges = [flat_flange(200.0, 150.0), flat_flange(22.0, 150.0), flat_flange(200.0, 20.0)]
    scene = render_scene(cfg, seed=202, camera_tilt_deg=5.0, flanges=flanges)
    quad, diag, edges, _ = _detect(cfg, scene)
    assert quad is not None, f"dno ni najdeno (diagnostika: {diag})"
    refined, _ = refine_quad_with_edges(quad, edges.points, cfg)
    error = float(np.mean(np.linalg.norm(refined - _ordered_gt_quad(scene), axis=1)))
    assert error < 5.0, f"vogali dna zgreseni za {error:.1f} px"


@pytest.mark.parametrize("seed", [203, 204, 205])
def test_f_from_two_planes_is_accurate(cfg, seed):
    """Dno in zgornji rob na znani visini dasta f tudi pri navpicni kameri."""
    walls = cfg.with_overrides({"box": {"wall_height_mm": float(cfg["synth.wall_height_mm"]),
                                        "wall_thickness_mm": float(cfg["synth.wall_thickness_mm"])}})
    scene = render_scene(walls, seed=seed, n_flanges=5, camera_tilt_deg=0.0)
    result = process_image(scene.image, walls)
    data = result.to_json(walls)
    f_true = float(scene.ground_truth["f_px"])
    rel = abs(data["calibration"]["f_px"] - f_true) / f_true
    assert data["calibration"]["method"] == "box_rim_two_planes", (
        f"pricakovana metoda dveh ravnin, dobil {data['calibration']['method']} "
        f"({result.calibration.diagnostics.get('box_rim')})")
    assert rel < 0.10, f"napaka f = {rel:.1%}"


def test_two_plane_method_beats_no_information(cfg):
    """Brez podatka o steni pri navpicni kameri f ni dolocljiv; s podatkom je."""
    walls = cfg.with_overrides({
        "camera": {"working_distance_mm": None},
        "box": {"wall_height_mm": float(cfg["synth.wall_height_mm"]),
                "wall_thickness_mm": float(cfg["synth.wall_thickness_mm"])}})
    blind = cfg.with_overrides({"camera": {"working_distance_mm": None}})
    scene = render_scene(walls, seed=209, n_flanges=5, camera_tilt_deg=0.0)
    f_true = float(scene.ground_truth["f_px"])
    with_walls = process_image(scene.image, walls).to_json(walls)["calibration"]
    without = process_image(scene.image, blind).to_json(blind)["calibration"]
    err_with = abs(with_walls["f_px"] - f_true) / f_true
    err_without = abs(without["f_px"] - f_true) / f_true
    assert with_walls["method"] == "box_rim_two_planes"
    assert without["method"] == "fallback_f_px"
    assert err_with < err_without


def test_rim_gate_rejects_non_coaxial_rectangle():
    """Pravokotnik, ki ni soosen z dnom, ni zgornji rob - ocena f mora pasti."""
    from flange_picker.config import load_config
    cfg = load_config()
    principal = (640.0, 480.0)
    k_mat = k_from_f(1300.0, principal)
    corners = np.array([[0.0, 0, 0], [400.0, 0, 0], [400.0, 300.0, 0], [0, 300.0, 0]])
    rot = np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]])
    from flange_picker.pose import project_points
    bottom = project_points((rot @ corners.T).T + np.array([-200.0, 150.0, 700.0]), k_mat)
    rim_pts = np.array([[-8.0, -8, 60], [408.0, -8, 60], [408.0, 308.0, 60], [-8.0, 308.0, 60]])
    rim_ok = project_points((rot @ rim_pts.T).T + np.array([-200.0, 150.0, 700.0]), k_mat)
    shifted = project_points((rot @ (rim_pts + np.array([40.0, 0, 0])).T).T
                             + np.array([-200.0, 150.0, 700.0]), k_mat)
    dims = (416.0, 316.0)
    ok, _ = _rim_geometry_valid(bottom, rim_ok, dims, 1300.0, principal, cfg)
    bad, check = _rim_geometry_valid(bottom, shifted, dims, 1300.0, principal, cfg)
    assert ok, "pravi rob je bil po krivem zavrnjen"
    assert not bad, f"zamaknjen pravokotnik bi moral pasti ({check})"


def test_edge_bias_estimator_recovers_common_offset(cfg):
    """Skupni odmik obeh robov je izracunljiv iz znanega razmerja premerov."""
    ratio = float(cfg["flange.d_out_mm"]) / float(cfg["flange.d_in_mm"])
    true_bias = 0.35
    pairs = []
    for a_true in (30.0, 34.0, 38.0, 42.0):
        outer = Ellipse(cx=100.0, cy=100.0, a=a_true + true_bias, b=a_true + true_bias, theta=0.0)
        inner = Ellipse(cx=100.0, cy=100.0, a=a_true / ratio + true_bias,
                        b=a_true / ratio + true_bias, theta=0.0)
        pairs.append(EllipsePair(outer=outer, inner=inner, score=1.0, role="outer"))
    enabled = cfg.with_overrides({"ellipse": {"estimate_edge_bias": True,
                                              "edge_bias_min_samples": 4}})
    bias, diag = estimate_edge_bias(pairs, enabled)
    assert bias == pytest.approx(true_bias, abs=0.02), diag
    apply_edge_bias([pairs[0].outer, pairs[0].inner], bias)
    assert pairs[0].outer.a == pytest.approx(30.0, abs=0.02)


def test_edge_bias_is_ignored_when_too_large(cfg):
    """Nesmiselna ocena se ne sme uporabiti."""
    enabled = cfg.with_overrides({"ellipse": {"estimate_edge_bias": True,
                                              "edge_bias_min_samples": 4}})
    pairs = [EllipsePair(outer=Ellipse(cx=0, cy=0, a=40.0, b=40.0, theta=0.0),
                         inner=Ellipse(cx=0, cy=0, a=35.0, b=35.0, theta=0.0),
                         score=1.0, role="outer") for _ in range(4)]
    bias, diag = estimate_edge_bias(pairs, enabled)
    assert bias == 0.0
    assert "reason" in diag


def test_frame_is_available_on_ordinary_scenes(cfg):
    for seed in (206, 207, 208):
        scene = render_scene(cfg, seed=seed, n_flanges=6, camera_tilt_deg=4.0)
        result = process_image(scene.image, cfg)
        assert result.calibration.frame_reliable, (
            f"seed {seed}: okvir zaboja bi moral biti na voljo "
            f"({result.warnings})")
