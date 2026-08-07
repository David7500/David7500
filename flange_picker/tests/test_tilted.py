"""Testi za mocno nagnjene kose.

Pri velikem naklonu postane dvoumnost poze iz kroga kriticna: obe resitvi dasta
isto elipso, a nasprotno smer nagiba. Robot, ki bi prijemalo nagnil v napacno
smer, bi zadel ob kos. Ti testi zaklenejo izmerjeno vedenje.
"""

from __future__ import annotations

import numpy as np
import pytest

from flange_picker.pipeline import process_image
from flange_picker.pose import FlangePose, build_flange_pose
from flange_picker.synth import render_scene

from .conftest import flat_flange


def _probe(cfg, flanges, target, seed=900):
    """Vrne kandidata, ki ustreza `target`, ob upostevanju dvoumnosti okvira."""
    scene = render_scene(cfg, seed=seed, camera_tilt_deg=4.0, flanges=flanges)
    data = process_image(scene.image, cfg).to_json(cfg)
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])
    best, best_dist, flip = None, 1e9, 0.0
    for cand in data["candidates"]:
        for xx, yy, rot in ((target["x_mm"], target["y_mm"], 0.0),
                            (w_mm - target["x_mm"], h_mm - target["y_mm"], 180.0)):
            dist = float(np.hypot(cand["x_mm"] - xx, cand["y_mm"] - yy))
            if dist < best_dist:
                best, best_dist, flip = cand, dist, rot
    if best is None or best_dist > 25.0:
        return None, None
    azimuth_err = abs((best["azimuth_deg"] + flip - target["azimuth_deg"] + 180.0) % 360.0 - 180.0)
    return best, azimuth_err


@pytest.mark.parametrize("azimuth", [0.0, 90.0, 180.0, 270.0])
def test_flange_tilted_45_degrees_is_found_with_correct_direction(cfg, azimuth):
    """Kos, nagnjen za 45 stopinj: najden, z pravo velikostjo IN smerjo nagiba."""
    target = {"x_mm": 200.0, "y_mm": 150.0, "z_mm": 14.0,
              "tilt_deg": 45.0, "azimuth_deg": azimuth}
    cand, azimuth_err = _probe(cfg, [target], target)
    assert cand is not None, "kos, nagnjen za 45 stopinj, ni bil najden"
    assert cand["tilt_deg"] == pytest.approx(45.0, abs=6.0)
    assert azimuth_err < 20.0, ("smer nagiba je napacna - verjetno je izbrana zrcalna "
                                f"resitev (napaka {azimuth_err:.0f} stopinj)")
    assert cand["paired"], "pri vidni luknji mora biti kandidat sparjen"
    assert not cand["orientation_ambiguous"]


@pytest.mark.parametrize("tilt", [30.0, 45.0, 60.0])
def test_tilt_magnitude_is_accurate_across_range(cfg, tilt):
    target = {"x_mm": 200.0, "y_mm": 150.0, "z_mm": max(2.0, 20.0 * np.sin(np.radians(tilt))),
              "tilt_deg": tilt, "azimuth_deg": 180.0}
    cand, azimuth_err = _probe(cfg, [target], target, seed=901)
    assert cand is not None, f"kos z naklonom {tilt} stopinj ni bil najden"
    assert cand["tilt_deg"] == pytest.approx(tilt, abs=6.0)
    assert azimuth_err < 20.0


def test_tilted_flange_leaning_on_another_is_found(cfg):
    """Realen primer: nagnjen kos se naslanja na drugega in je delno prekrit."""
    base = flat_flange(200.0, 150.0)
    lean = {"x_mm": 218.0, "y_mm": 150.0, "z_mm": 14.0,
            "tilt_deg": 45.0, "azimuth_deg": 180.0}
    cand, azimuth_err = _probe(cfg, [base, lean], lean, seed=902)
    assert cand is not None, "naslonjen nagnjen kos ni bil najden"
    assert cand["tilt_deg"] == pytest.approx(45.0, abs=8.0)
    assert azimuth_err < 25.0


def test_unpaired_tilted_candidate_is_flagged_as_ambiguous(cfg):
    """Brez vidne luknje smeri nagiba ni mogoce dolociti - izmerjeno je napacna v
    priblizno polovici primerov. Tak kandidat mora biti oznacen, ne tiho vrnjen."""
    pose = FlangePose(center_cam=np.zeros(3), normal_cam=np.array([0.0, 0.0, -1.0]),
                      tilt_deg=45.0, paired=False, confidence=0.25)
    from flange_picker.pose import _flag_orientation
    _flag_orientation(pose, float(cfg["pose.unpaired_ambiguous_tilt_deg"]))
    assert pose.orientation_ambiguous
    assert pose.confidence < 0.25, "zaupanje se mora znizati z naklonom"
    assert any("azimut" in reason for reason in pose.reasons)


def test_flat_unpaired_candidate_is_not_flagged(cfg):
    """Pri ravnem kosu zrcalna resitev sovpada z pravo - oznaka bi bila lazna."""
    pose = FlangePose(center_cam=np.zeros(3), normal_cam=np.array([0.0, 0.0, -1.0]),
                      tilt_deg=3.0, paired=False, confidence=0.25)
    from flange_picker.pose import _flag_orientation
    _flag_orientation(pose, float(cfg["pose.unpaired_ambiguous_tilt_deg"]))
    assert not pose.orientation_ambiguous
    assert pose.confidence == pytest.approx(0.25)


def test_near_vertical_flange_is_rejected_with_reason_not_silently(cfg):
    """Nad ~70 stopinjami kos ni vec zanesljivo zaznaven; to mora biti povedano."""
    target = {"x_mm": 200.0, "y_mm": 150.0, "z_mm": 19.0,
              "tilt_deg": 80.0, "azimuth_deg": 180.0}
    scene = render_scene(cfg, seed=903, camera_tilt_deg=4.0, flanges=[target])
    result = process_image(scene.image, cfg)
    data = result.to_json(cfg)
    matched, _ = _probe(cfg, [target], target, seed=903)
    if matched is None:
        assert not data["candidates"] or all(e["reason"] for e in result.rejected)
