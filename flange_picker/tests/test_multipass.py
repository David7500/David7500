"""Vecprehodna detekcija in preverjanja kolobarja."""

from __future__ import annotations

import numpy as np
import pytest

from flange_picker.ellipse import (Ellipse, EllipsePair, measure_ring_clutter,
                                   verify_virtual_hole)
from flange_picker.multipass import consolidate, run_passes
from flange_picker.pipeline import process_image
from flange_picker.synth import render_scene

from .conftest import flat_flange


def _gradients(image: np.ndarray):
    import cv2
    from flange_picker.preprocess import to_gray
    gray = to_gray(image)
    return (cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3),
            cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))


def test_consolidation_counts_votes_per_pass(cfg):
    """Isti kos, najden v vec prehodih, da eno gruco z vec glasovi."""
    scene = render_scene(cfg, seed=42, camera_tilt_deg=4.0,
                         flanges=[flat_flange(200.0, 150.0)])
    from flange_picker.preprocess import to_gray
    passes, _ = run_passes(to_gray(scene.image), cfg)
    assert len(passes) == len(cfg["multipass.passes"])
    reps, diag = consolidate(passes, cfg)

    assert diag["n_clusters"] <= diag["n_pooled"]
    assert all(r.meta["votes"] == len(r.meta["passes"]) for r in reps)
    assert all(r.meta["votes"] <= len(passes) for r in reps)
    # Obris osamljenega kosa mora prezivet vec kot eno obdelavo slike.
    assert max(r.meta["votes"] for r in reps) >= 2


def test_representative_keeps_best_fit_not_median(cfg):
    """Predstavnik gruce je najboljsi fit; mediana bi poslabsala geometrijo."""
    good = Ellipse(cx=100.0, cy=100.0, a=50.0, b=50.0, theta=0.0,
                   rms_px=0.05, n_points=400, points=np.zeros((400, 2)),
                   meta={"pass": "osnovni"})
    coarse = Ellipse(cx=103.0, cy=97.0, a=52.0, b=48.0, theta=0.2,
                     rms_px=1.0, n_points=0, meta={"pass": "gladko"})

    class _Pass:
        full_scale = True

        def __init__(self, name, ellipses):
            self.name, self.ellipses = name, ellipses

    reps, _ = consolidate([_Pass("osnovni", [good]), _Pass("gladko", [coarse])], cfg)
    assert len(reps) == 1
    rep = reps[0]
    assert rep.meta["votes"] == 2
    assert rep.cx == pytest.approx(good.cx)
    assert rep.a == pytest.approx(good.a)


def test_ring_clutter_excess_rises_when_a_piece_lies_across(cfg):
    """Prost kos ima enakomeren kolobar, kos s tujim kosom cez sebe pa ne."""
    free = render_scene(cfg, seed=7, camera_tilt_deg=3.0,
                        flanges=[flat_flange(200.0, 150.0)])
    covered = render_scene(cfg, seed=7, camera_tilt_deg=3.0,
                           flanges=[flat_flange(200.0, 150.0),
                                    flat_flange(214.0, 150.0, z_mm=2.5)])

    def excess(scene, index=0):
        result = process_image(scene.image, cfg.with_overrides(
            {"scoring": {"max_ring_clutter_excess": 1.0, "max_occlusion": 1.0}}))
        assert result.candidates, "kos ni bil najden"
        return result.candidates[index].ring_clutter_excess

    assert excess(free) < excess(covered)


def test_virtual_hole_separates_flange_from_plain_disc(cfg):
    """Obris brez para: prava prirobnica ima rob na polmeru luknje, plosca ne."""
    import cv2
    scene = render_scene(cfg, seed=11, camera_tilt_deg=3.0,
                         flanges=[flat_flange(200.0, 150.0)])
    result = process_image(scene.image, cfg)
    assert result.candidates
    outer = result.candidates[0].pair.outer

    image = scene.image.copy()
    gx, gy = _gradients(image)
    flange = EllipsePair(outer=outer, inner=None, score=0.0, role="outer")
    verify_virtual_hole([flange], gx, gy, cfg)

    # Ista elipsa na sliki, kjer je luknja zapolnjena z okoliskim tonom.
    ratio = float(cfg["flange.d_in_mm"]) / float(cfg["flange.d_out_mm"])
    filled = image.copy()
    cv2.ellipse(filled, (int(outer.cx), int(outer.cy)),
                (int(outer.a * ratio * 1.4), int(outer.b * ratio * 1.4)),
                np.degrees(outer.theta), 0, 360, (170, 170, 170), -1)
    disc = EllipsePair(outer=outer, inner=None, score=0.0, role="outer")
    verify_virtual_hole([disc], *_gradients(filled), cfg)

    assert flange.virtual_hole_support > disc.virtual_hole_support


def test_lone_hole_is_measured_on_the_implied_outline(cfg):
    """Pri sami luknji se kolobar meri na obrisu, izpeljanem iz geometrije."""
    scene = render_scene(cfg, seed=23, camera_tilt_deg=3.0,
                         flanges=[flat_flange(200.0, 150.0)])
    gx, gy = _gradients(scene.image)
    result = process_image(scene.image, cfg)
    assert result.candidates
    outer = result.candidates[0].pair.outer
    ratio = float(cfg["flange.d_in_mm"]) / float(cfg["flange.d_out_mm"])

    as_outline = EllipsePair(outer=outer, inner=None, score=0.0, role="outer")
    hole = Ellipse(cx=outer.cx, cy=outer.cy, a=outer.a * ratio, b=outer.b * ratio,
                   theta=outer.theta)
    as_hole = EllipsePair(outer=hole, inner=None, score=0.0, role="inner")
    measure_ring_clutter([as_outline, as_hole], gx, gy, cfg)

    assert np.isfinite(as_hole.ring_clutter)
    assert as_hole.ring_clutter == pytest.approx(as_outline.ring_clutter, abs=0.05)


def test_lone_hole_is_rejected_by_the_gate(cfg):
    """Kandidat, ki mu je vidna le luknja, ne sme priti v izhod."""
    scene = render_scene(cfg, seed=31, camera_tilt_deg=4.0,
                         flanges=[flat_flange(200.0, 150.0)])
    strict = process_image(scene.image, cfg)
    assert all(c.pair.role != "inner" for c in strict.candidates)

    lenient = process_image(scene.image,
                            cfg.with_overrides({"scoring": {"reject_lone_hole": False}}))
    assert len(lenient.candidates) >= len(strict.candidates)
