"""Enotski testi geometrije: konike, poza iz kroga, fit elipse."""

from __future__ import annotations

import math

import numpy as np
import pytest

from flange_picker.autocalib import (box_frame_points, decompose_plane_homography,
                                     f_from_vanishing_points, k_from_f)
from flange_picker.ellipse import (conic_from_params, fit_ellipse_direct, params_from_conic,
                                   sampson_residuals)
from flange_picker.pose import (circle_points_3d, circle_pose_solutions,
                                project_circle_to_conic, project_points)


def test_conic_params_round_trip():
    for cx, cy, a, b, theta in [(100.0, 50.0, 30.0, 20.0, 0.3),
                                (0.0, 0.0, 5.0, 5.0, 0.0),
                                (640.0, 480.0, 120.0, 15.0, 2.1)]:
        conic = conic_from_params(cx, cy, a, b, theta)
        ell = params_from_conic(conic)
        assert ell is not None
        assert ell.cx == pytest.approx(cx, abs=1e-6)
        assert ell.cy == pytest.approx(cy, abs=1e-6)
        assert ell.a == pytest.approx(a, rel=1e-9)
        assert ell.b == pytest.approx(b, rel=1e-9)
        if abs(a - b) > 1e-9:
            assert math.sin(ell.theta - theta) == pytest.approx(0.0, abs=1e-6)


def test_circle_pose_recovers_exact_pose():
    """Poza iz kroga mora ena od dveh resitev natanko zadeti resnico."""
    k_mat = k_from_f(1200.0, (640.0, 480.0))
    rng = np.random.default_rng(0)
    worst = 0.0
    for _ in range(150):
        normal = rng.normal(size=3)
        normal /= np.linalg.norm(normal)
        if normal[2] > 0:
            normal = -normal
        center = np.array([rng.uniform(-150, 150), rng.uniform(-150, 150), rng.uniform(400, 900)])
        conic = project_circle_to_conic(center, normal, 20.0, k_mat)
        sols = circle_pose_solutions(conic, k_mat, 20.0)
        assert sols, "poze ni bilo mogoce izracunati"
        err = min(max(float(np.linalg.norm(s.center - center)),
                      math.degrees(math.acos(min(1.0, abs(float(s.normal @ normal))))))
                  for s in sols)
        worst = max(worst, err)
    assert worst < 1e-3


def test_circle_pose_has_two_solutions_when_tilted():
    k_mat = k_from_f(1200.0, (640.0, 480.0))
    tilt = math.radians(25.0)
    normal = np.array([math.sin(tilt), 0.0, -math.cos(tilt)])
    conic = project_circle_to_conic(np.array([0.0, 0.0, 600.0]), normal, 20.0, k_mat)
    sols = circle_pose_solutions(conic, k_mat, 20.0)
    assert len(sols) == 2
    angle = math.degrees(math.acos(min(1.0, abs(float(sols[0].normal @ sols[1].normal)))))
    assert angle > 10.0, "resitvi morata biti razlicni - to je ravno dvoumnost, ki jo resujemo"


def test_ellipse_fit_is_accurate_on_clean_points():
    conic = conic_from_params(300.0, 200.0, 40.0, 25.0, 0.7)
    ell_true = params_from_conic(conic)
    pts = ell_true.perimeter_points(120)
    fitted = fit_ellipse_direct(pts)
    assert fitted is not None
    assert fitted.a == pytest.approx(40.0, rel=1e-6)
    assert fitted.b == pytest.approx(25.0, rel=1e-6)
    assert fitted.rms_px < 1e-6


def test_ellipse_fit_tolerates_noise():
    conic = conic_from_params(300.0, 200.0, 40.0, 25.0, 0.7)
    pts = params_from_conic(conic).perimeter_points(200)
    rng = np.random.default_rng(3)
    noisy = pts + rng.normal(0.0, 0.3, pts.shape)
    fitted = fit_ellipse_direct(noisy)
    assert fitted is not None
    assert fitted.a == pytest.approx(40.0, abs=0.5)
    assert fitted.b == pytest.approx(25.0, abs=0.5)


def test_ellipse_fit_rejects_degenerate_input():
    line = np.stack([np.linspace(0, 100, 40), np.linspace(0, 50, 40)], axis=1)
    assert fit_ellipse_direct(line) is None
    assert fit_ellipse_direct(np.zeros((3, 2))) is None


def test_sampson_residual_zero_on_conic():
    conic = conic_from_params(10.0, 20.0, 30.0, 15.0, 0.2)
    pts = params_from_conic(conic).perimeter_points(50)
    assert float(np.max(sampson_residuals(conic, pts))) < 1e-6


def test_vanishing_point_focal_length_is_exact_for_synthetic_quad():
    """Pri natancnih vogalih mora f iz izginjajocih tock zadeti resnico."""
    from flange_picker.config import load_config
    cfg = load_config()
    f_true = 1300.0
    principal = (640.0, 480.0)
    k_mat = k_from_f(f_true, principal)
    # Nagib okoli dveh osi: pri nagibu le okoli ene ostane en par stranic v sliki
    # vzporeden in ena izginjajoca tocka pobegne v neskoncnost.
    import cv2 as _cv2
    rot = (_cv2.Rodrigues(np.array([math.radians(12.0), math.radians(9.0), 0.0]))[0]
           @ np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]]))
    corners = np.array([[0.0, 0, 0], [400.0, 0, 0], [400.0, 300.0, 0], [0, 300.0, 0]])
    cam = (rot @ corners.T).T + np.array([-200.0, 150.0, 700.0])
    quad = project_points(cam, k_mat)
    f_est, diag = f_from_vanishing_points(quad, principal, cfg)
    assert f_est is not None, diag
    assert f_est == pytest.approx(f_true, rel=1e-6)


def test_vanishing_points_need_two_finite_points():
    """Nagib okoli ene same osi pusti en par stranic vzporeden - f iz izginjajocih
    tock takrat ni izracunljiv in mora biti javljen kot razlog, ne kot napaka."""
    import cv2 as _cv2

    from flange_picker.config import load_config
    cfg = load_config()
    k_mat = k_from_f(1300.0, (640.0, 480.0))
    rot = (_cv2.Rodrigues(np.array([math.radians(12.0), 0.0, 0.0]))[0]
           @ np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]]))
    corners = np.array([[0.0, 0, 0], [400.0, 0, 0], [400.0, 300.0, 0], [0, 300.0, 0]])
    quad = project_points((rot @ corners.T).T + np.array([-200.0, 150.0, 700.0]), k_mat)
    f_est, diag = f_from_vanishing_points(quad, (640.0, 480.0), cfg)
    assert f_est is None
    assert "reason" in diag


def test_vanishing_points_report_degenerate_case():
    """Fronto-paralelna kamera: f iz izginjajocih tock ni izracunljiv - to je fizika,
    ne napaka, in mora biti javljeno z razlogom."""
    from flange_picker.config import load_config
    cfg = load_config()
    quad = np.array([[100.0, 100.0], [700.0, 100.0], [700.0, 550.0], [100.0, 550.0]])
    f_est, diag = f_from_vanishing_points(quad, (400.0, 300.0), cfg)
    assert f_est is None
    assert "reason" in diag


def test_homography_decomposition_recovers_plane_pose():
    import cv2
    from flange_picker.config import load_config
    cfg = load_config()
    f_true = 1300.0
    k_mat = k_from_f(f_true, (640.0, 480.0))
    rot = (cv2.Rodrigues(np.array([math.radians(8.0), math.radians(5.0), 0.0]))[0]
           @ np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]]))
    tvec = np.array([-200.0, 150.0, 700.0])
    corners = np.array([[0.0, 0, 0], [400.0, 0, 0], [400.0, 300.0, 0], [0, 300.0, 0]])
    quad = project_points((rot @ corners.T).T + tvec, k_mat)
    quad_o, obj = box_frame_points(quad, cfg)
    h_mat, _ = cv2.findHomography(obj.astype(np.float32), quad_o.astype(np.float32), 0)
    rot_est, t_est = decompose_plane_homography(h_mat, k_mat)
    assert np.allclose(t_est, tvec, atol=1.0)
    assert float(np.max(np.abs(rot_est - rot))) < 1e-3


def test_box_frame_points_puts_x_along_long_side():
    from flange_picker.config import load_config
    cfg = load_config()
    quad = np.array([[0.0, 0.0], [300.0, 0.0], [300.0, 400.0], [0.0, 400.0]])
    quad_o, obj = box_frame_points(quad, cfg)
    side_first = float(np.linalg.norm(quad_o[1] - quad_o[0]))
    side_second = float(np.linalg.norm(quad_o[2] - quad_o[1]))
    assert obj[1, 0] == pytest.approx(float(cfg["box.w_mm"]))
    assert side_first > side_second, "stranica P0->P1 mora ustrezati daljsi dimenziji zaboja"
