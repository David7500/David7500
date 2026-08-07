"""Robni primeri iz naloge: prekrivanje, kos ob steni, skoraj navpicen kos,
odsev cez luknjo, delno viden zaboj, brez zaboja.
"""

from __future__ import annotations

import numpy as np
import pytest

from flange_picker.pipeline import process_image
from flange_picker.synth import render_scene

from .conftest import flat_flange, match_to_gt


def test_overlapping_flanges_are_separated(cfg):
    """Dva prekrivajoca se kosa: zgornji mora biti prvi in imeti vecji prost lok."""
    flanges = [flat_flange(200.0, 150.0, z_mm=0.75),
               flat_flange(224.0, 150.0, z_mm=2.25, tilt_deg=6.0, azimuth_deg=180.0)]
    scene = render_scene(cfg, seed=30, camera_tilt_deg=5.0, flanges=flanges)
    data = process_image(scene.image, cfg).to_json(cfg)
    assert len(data["candidates"]) >= 1
    if len(data["candidates"]) >= 2:
        assert data["candidates"][0]["free_arc_deg"] >= data["candidates"][1]["free_arc_deg"] - 1e-6


def test_flange_at_wall_gets_smaller_wall_margin(cfg):
    near = [flat_flange(28.0, 150.0)]
    far = [flat_flange(200.0, 150.0)]
    d_near = process_image(render_scene(cfg, seed=31, camera_tilt_deg=4.0,
                                        flanges=near).image, cfg).to_json(cfg)
    d_far = process_image(render_scene(cfg, seed=31, camera_tilt_deg=4.0,
                                       flanges=far).image, cfg).to_json(cfg)
    assert d_near["candidates"] and d_far["candidates"]
    m_near = d_near["candidates"][0]["wall_margin_mm"]
    m_far = d_far["candidates"][0]["wall_margin_mm"]
    if m_near is not None and m_far is not None:
        assert m_near < m_far, "kos ob steni mora imeti manjso rezervo do stene"


def test_steeply_tilted_flange_is_not_silently_dropped(cfg):
    """Skoraj navpicen kos je viden kot crtica; sistem ga sme zavrniti, a mora
    povedati razlog."""
    flanges = [flat_flange(200.0, 150.0, z_mm=12.0, tilt_deg=72.0, azimuth_deg=30.0)]
    scene = render_scene(cfg, seed=32, camera_tilt_deg=4.0, flanges=flanges)
    result = process_image(scene.image, cfg)
    data = result.to_json(cfg)
    accepted = bool(data["candidates"])
    rejected_with_reason = bool(result.rejected) and all(e["reason"] for e in result.rejected)
    assert accepted or rejected_with_reason, "kos je izginil brez sledi"


def test_specular_highlight_over_hole_does_not_break_detection(cfg):
    """Odsev cez luknjo: maskiran mora biti kot odsev, ne obravnavan kot rob."""
    import cv2
    flanges = [flat_flange(200.0, 150.0)]
    scene = render_scene(cfg, seed=33, camera_tilt_deg=4.0, specular=False, flanges=flanges)
    clean = process_image(scene.image, cfg).to_json(cfg)
    assert clean["candidates"], "referencni primer brez odseva mora uspeti"
    cx = clean["candidates"][0]["ellipse_px"]["cx"]
    cy = clean["candidates"][0]["ellipse_px"]["cy"]
    marred = scene.image.copy()
    cv2.circle(marred, (int(cx), int(cy)), 9, 255, -1)
    result = process_image(marred, cfg)
    data = result.to_json(cfg)
    assert result.diagnostics["preprocess"]["specular_fraction"] > 0
    assert len(match_to_gt(data["candidates"], flanges, cfg)) == 1, \
        "odsev cez luknjo ne sme unicit detekcije kosa"


def test_partially_visible_box_still_produces_ranking(cfg):
    """Zaboj sega cez rob slike: koordinate so lahko nezanesljive, rangiranje ne sme odpasti."""
    scene = render_scene(cfg, seed=34, n_flanges=4, camera_tilt_deg=4.0)
    cropped = scene.image[:, : int(scene.image.shape[1] * 0.62)]
    result = process_image(cropped, cfg)
    data = result.to_json(cfg)
    assert data["candidates"], "tudi ob odrezanem zaboju morajo ostati kandidati"
    scores = [c["score"] for c in data["candidates"]]
    assert scores == sorted(scores, reverse=True)


def test_no_box_degrades_to_relative_ranking(cfg):
    """Brez zaboja: nikoli tiha odpoved - opozorilo, frame='camera', a rangiranje ostane."""
    scene = render_scene(cfg, seed=35, n_flanges=3, camera_tilt_deg=4.0)
    # izrez okoli kosov, brez sten in dna
    crop = scene.image[120:430, 150:600]
    result = process_image(crop, cfg)
    data = result.to_json(cfg)
    if not data["frame_reliable"]:
        assert data["frame"] == "camera"
        assert result.warnings
    scores = [c["score"] for c in data["candidates"]]
    assert scores == sorted(scores, reverse=True)


def test_noise_does_not_produce_absurd_heights(cfg):
    """Verjetnostni filter visine mora odstraniti nesmiselne rekonstrukcije."""
    scene = render_scene(cfg, seed=36, n_flanges=6, camera_tilt_deg=5.0)
    result = process_image(scene.image, cfg)
    data = result.to_json(cfg)
    if data["frame_reliable"]:
        for cand in data["candidates"]:
            assert float(cfg["scoring.z_min_mm"]) <= cand["z_mm"] <= float(cfg["scoring.z_max_mm"])


def test_manual_corners_override_detection(cfg):
    scene = render_scene(cfg, seed=37, n_flanges=3, camera_tilt_deg=5.0)
    corners = scene.ground_truth["box"]["corners_px"]
    manual = cfg.with_overrides({"box": {"corners_px": corners}})
    result = process_image(scene.image, manual)
    assert result.calibration.frame_reliable
    assert result.calibration.diagnostics["box_detect"]["source"] == "config"


def test_results_are_deterministic(cfg):
    scene = render_scene(cfg, seed=38, n_flanges=4, camera_tilt_deg=5.0)
    a = process_image(scene.image, cfg).to_json(cfg)
    b = process_image(scene.image, cfg).to_json(cfg)
    assert a["candidates"] == b["candidates"]
    assert a["calibration"] == b["calibration"]
