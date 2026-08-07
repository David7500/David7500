"""Testi celotnega cevovoda na sinteticnih scenah."""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from flange_picker.pipeline import process_file, process_image, result_to_json_string
from flange_picker.synth import render_scene

from .conftest import flat_flange, match_to_gt


def test_output_schema(cfg):
    scene = render_scene(cfg, seed=11, n_flanges=4, camera_tilt_deg=5.0)
    data = process_image(scene.image, cfg).to_json(cfg)
    assert set(["frame", "calibration", "candidates"]).issubset(data)
    assert set(["f_px", "confidence", "method"]).issubset(data["calibration"])
    assert data["candidates"], "na jasni sceni mora biti vsaj en kandidat"
    for cand in data["candidates"]:
        for key in ("x_mm", "y_mm", "z_mm", "tilt_deg", "azimuth_deg", "normal",
                    "grasp_point_mm", "occlusion_ratio", "score", "confidence"):
            assert key in cand, f"manjka polje {key}"
        assert len(cand["normal"]) == 3
        assert 0.0 <= cand["occlusion_ratio"] <= 1.0
        assert 0.0 <= cand["confidence"] <= 1.0
        assert 0.0 <= cand["azimuth_deg"] < 360.0
    scores = [c["score"] for c in data["candidates"]]
    assert scores == sorted(scores, reverse=True), "kandidati morajo biti rangirani"
    json.loads(result_to_json_string(process_image(scene.image, cfg), cfg))


def test_finds_isolated_flanges_accurately(cfg):
    flanges = [flat_flange(120.0, 90.0), flat_flange(280.0, 90.0),
               flat_flange(120.0, 210.0), flat_flange(280.0, 210.0)]
    scene = render_scene(cfg, seed=12, camera_tilt_deg=5.0, flanges=flanges)
    data = process_image(scene.image, cfg).to_json(cfg)
    matches = match_to_gt(data["candidates"], flanges, cfg)
    assert len(matches) == 4, f"pricakovane 4 prirobnice, najdenih {len(matches)}"
    assert max(m[2] for m in matches) < 6.0, "XY napaka nad 6 mm"
    for cand in data["candidates"]:
        assert cand["tilt_deg"] < 20.0, "plosko lezec kos ne sme imeti velikega naklona"


def test_ranks_top_of_stack_first(cfg):
    """Kos na vrhu kupa mora biti prvi - to je bistvo rangiranja."""
    flanges = [flat_flange(200.0, 150.0, z_mm=0.75),
               flat_flange(212.0, 158.0, z_mm=2.25, tilt_deg=8.0, azimuth_deg=40.0),
               flat_flange(90.0, 80.0, z_mm=0.75)]
    scene = render_scene(cfg, seed=13, camera_tilt_deg=5.0, flanges=flanges)
    result = process_image(scene.image, cfg)
    data = result.to_json(cfg)
    assert data["candidates"]
    top = data["candidates"][0]
    heights = sorted(c["z_mm"] for c in data["candidates"])
    assert top["z_mm"] >= heights[-1] - 1.5, "prvi kandidat ni med najvisjimi"


def test_grasp_point_is_on_ring_not_at_centre(cfg):
    """Sesek mora na kolobar; v sredini je luknja."""
    flanges = [flat_flange(200.0, 150.0)]
    scene = render_scene(cfg, seed=14, camera_tilt_deg=4.0, flanges=flanges)
    data = process_image(scene.image, cfg).to_json(cfg)
    assert data["candidates"]
    cand = data["candidates"][0]
    grasp = np.array(cand["grasp_point_mm"], dtype=float)
    centre = np.array([cand["x_mm"], cand["y_mm"], cand["z_mm"]], dtype=float)
    dist = float(np.linalg.norm(grasp - centre))
    r_in = float(cfg["flange.d_in_mm"]) / 2.0
    r_out = float(cfg["flange.d_out_mm"]) / 2.0
    assert r_in < dist < r_out, f"prijemna tocka na r={dist:.1f} mm ni v kolobarju"
    assert dist == pytest.approx(0.5 * (r_in + r_out), abs=1.0)


def test_empty_image_returns_empty_list_without_raising(cfg):
    blank = np.full((240, 320), 40, dtype=np.uint8)
    result = process_image(blank, cfg)
    data = result.to_json(cfg)
    assert data["candidates"] == []
    assert result.warnings, "prazna slika mora sprozit opozorilo, ne tihe odpovedi"


def test_zero_size_image_is_handled(cfg):
    result = process_image(np.zeros((0, 0), dtype=np.uint8), cfg)
    assert result.to_json(cfg)["candidates"] == []
    assert result.warnings


def test_missing_file_is_reported(cfg, tmp_path):
    result = process_file(str(tmp_path / "ni-me.png"), cfg)
    assert result.to_json(cfg)["candidates"] == []
    assert any("prebrati" in w for w in result.warnings)


def test_empty_box_yields_no_candidates(cfg):
    scene = render_scene(cfg, seed=15, camera_tilt_deg=5.0, flanges=[])
    data = process_image(scene.image, cfg).to_json(cfg)
    assert data["candidates"] == []
    assert "diagnostics" in data


def test_single_flange(cfg):
    flanges = [flat_flange(200.0, 150.0)]
    scene = render_scene(cfg, seed=16, camera_tilt_deg=5.0, flanges=flanges)
    data = process_image(scene.image, cfg).to_json(cfg)
    assert len(data["candidates"]) >= 1
    assert len(match_to_gt(data["candidates"], flanges, cfg)) == 1


def test_debug_overlays_are_written(cfg, tmp_path):
    scene = render_scene(cfg, seed=17, n_flanges=3, camera_tilt_deg=5.0)
    process_image(scene.image, cfg, debug=True, debug_dir=str(tmp_path), debug_prefix="t")
    written = sorted(os.listdir(tmp_path))
    assert len(written) >= 6, f"pricakovani overlay-i za vsak korak, dobil {written}"
    assert any("candidates" in name for name in written)


def test_every_rejected_candidate_has_a_reason(cfg):
    scene = render_scene(cfg, seed=18, n_flanges=8, camera_tilt_deg=5.0)
    result = process_image(scene.image, cfg)
    for entry in result.rejected:
        assert entry.get("reason"), "vsaka zavrnitev mora imeti razlog"


def test_suction_cup_wider_than_ring_is_reported(cfg):
    """Pri D_out=40 in D_in=16 je kolobar sirok 12 mm, cascica pa 15 mm."""
    scene = render_scene(cfg, seed=19, n_flanges=2, camera_tilt_deg=4.0)
    result = process_image(scene.image, cfg)
    assert any("cascica" in w for w in result.warnings)
    data = result.to_json(cfg)
    for cand in data["candidates"]:
        assert cand["cup_fit_ratio"] < 1.0


def test_require_full_cup_clearance_rejects_everything(cfg):
    strict = cfg.with_overrides({"gripper": {"require_full_cup_clearance": True}})
    scene = render_scene(strict, seed=20, n_flanges=3, camera_tilt_deg=4.0)
    result = process_image(scene.image, strict)
    assert result.to_json(strict)["candidates"] == []
    assert result.rejected and all(e["reason"] for e in result.rejected)
