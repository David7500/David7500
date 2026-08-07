"""Autokalibracija iz same scene.

Kalibracija kamere ni na voljo, zato jo izpeljemo iz zaboja in prirobnic:

1. detekcija notranjega pravokotnika (dna) zaboja,
2. homografija ravnine dna iz stirih vogalov in znanih dimenzij,
3. f_px iz dveh izginjajocih tock (kvadratni piksli, opticno sredisce v
   sredini slike),
4. preverjanje/izboljsava f_px na koncentricnih parih elips - dva koncentricna
   kroga znanih polmerov sta neodvisna omejitev na f in delujeta tudi tam, kjer
   je perspektiva presibka za izginjajoce tocke,
5. razcep homografije v pozo dna => koordinatni sistem zaboja,
6. degradacija na "samo relativno rangiranje", ce zaboja ni mogoce najti.

Popacenje lece ni modelirano; pri kakovostni optiki je to napaka reda 1 %.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .config import Config
from .pose import circle_pose_solutions, pair_consistency_cost


@dataclass
class Calibration:
    k_mat: np.ndarray
    f_px: float
    principal_point: Tuple[float, float]
    method: str
    confidence: float
    rot_box: Optional[np.ndarray] = None      # box -> kamera
    t_box: Optional[np.ndarray] = None
    homography: Optional[np.ndarray] = None   # box mm -> px
    quad_px: Optional[np.ndarray] = None
    frame_reliable: bool = False
    f_confidence: float = 0.0                 # zaupanje v absolutno merilo (f_px)
    diagnostics: dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "f_px": round(float(self.f_px), 3),
            "confidence": round(float(self.confidence), 3),
            "method": self.method,
            # Locimo zaupanje v okvir (X, Y, naklon) od zaupanja v absolutno
            # merilo globine (f_px). Prvo je skoraj vedno mnogo boljse.
            "frame_confidence": round(1.0 if self.frame_reliable else 0.0, 3),
            "f_confidence": round(float(self.f_confidence), 3),
        }


# --------------------------------------------------------------------------
# detekcija zaboja
# --------------------------------------------------------------------------
def _quad_angles_ok(quad: np.ndarray, cfg: Config) -> bool:
    lo = float(cfg["box.detect.min_corner_angle_deg"])
    hi = float(cfg["box.detect.max_corner_angle_deg"])
    for i in range(4):
        a = quad[(i - 1) % 4] - quad[i]
        b = quad[(i + 1) % 4] - quad[i]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-6 or nb < 1e-6:
            return False
        ang = math.degrees(math.acos(float(np.clip(a @ b / (na * nb), -1.0, 1.0))))
        if ang < lo or ang > hi:
            return False
    return True


def _aspect_plausible(quad: np.ndarray, cfg: Config) -> bool:
    """Ali se razmerje stranic v sliki vsaj priblizno ujema z dimenzijami zaboja.

    Pri skoraj navpicni kameri perspektiva razmerja ne more mocno spremeniti,
    zato to poceni odstrani nesmiselne kandidate (npr. iz Houghove rezerve).
    """
    side_a = 0.5 * (np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[3] - quad[2]))
    side_b = 0.5 * (np.linalg.norm(quad[2] - quad[1]) + np.linalg.norm(quad[0] - quad[3]))
    if min(side_a, side_b) < 1e-6:
        return False
    observed = max(side_a, side_b) / min(side_a, side_b)
    expected = max(float(cfg["box.w_mm"]), float(cfg["box.h_mm"])) / min(
        float(cfg["box.w_mm"]), float(cfg["box.h_mm"]))
    return abs(observed - expected) / expected <= float(cfg["box.detect.max_aspect_deviation"])


def _order_quad(quad: np.ndarray) -> np.ndarray:
    """Uredi vogale ciklicno; izhodisce = vogal najblizje zgornjemu levemu kotu slike."""
    pts = np.asarray(quad, dtype=float).reshape(4, 2)
    centroid = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
    pts = pts[np.argsort(ang)]                       # v smeri urinega kazalca v sliki
    start = int(np.argmin(np.linalg.norm(pts, axis=1)))
    return np.roll(pts, -start, axis=0)


def detect_box_quad(gray: np.ndarray, cfg: Config) -> Tuple[Optional[np.ndarray], dict]:
    """Poisce notranji pravokotnik dna zaboja. Vrne (4x2 vogali, diagnostika)."""
    diag: dict = {"source": None, "n_candidates": 0}
    manual = cfg.get("box.corners_px", None)
    if manual:
        quad = np.asarray(manual, dtype=float).reshape(4, 2)
        diag["source"] = "config"
        return _order_quad(quad), diag

    h, w = gray.shape[:2]
    area_img = float(h * w)
    ksize = int(cfg["box.detect.blur_ksize"]) | 1
    blur = cv2.GaussianBlur(gray, (ksize, ksize), 0)
    edges = cv2.Canny(blur, int(cfg["box.detect.canny_low"]), int(cfg["box.detect.canny_high"]),
                      L2gradient=True)
    ck = int(cfg["box.detect.close_kernel_px"])
    if ck > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ck, ck))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    min_area = float(cfg["box.detect.min_area_frac"]) * area_img
    max_area = float(cfg["box.detect.max_area_frac"]) * area_img
    eps_frac = float(cfg["box.detect.approx_eps_frac"])

    cands: List[Tuple[float, np.ndarray]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        approx = cv2.approxPolyDP(cnt, eps_frac * cv2.arcLength(cnt, True), True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue
        quad = _order_quad(approx.reshape(4, 2).astype(float))
        if not _quad_angles_ok(quad, cfg) or not _aspect_plausible(quad, cfg):
            continue
        cands.append((float(cv2.contourArea(approx)), quad))

    diag["n_candidates"] = len(cands)
    if not cands:
        quad, hough_diag = _quad_from_hough(edges, cfg)
        diag.update(hough_diag)
        if quad is not None:
            diag["source"] = "hough"
            return quad, diag
        return None, diag

    # Zunanji rob zaboja je vecji kvadrilateral, ki vsebuje notranjega -
    # zanima nas notranji (dno).
    cands.sort(key=lambda c: -c[0])
    inner_ratio = float(cfg["box.detect.nested_inner_ratio"])
    chosen = None
    for area, quad in cands:
        contains_inner = False
        for other_area, other in cands:
            if other is quad or other_area >= area:
                continue
            if other_area < inner_ratio * area:
                continue
            centers_inside = all(
                cv2.pointPolygonTest(quad.astype(np.float32), (float(p[0]), float(p[1])), False) >= 0
                for p in other)
            if centers_inside:
                contains_inner = True
                break
        if not contains_inner:
            chosen = quad
            break
    if chosen is None:
        chosen = cands[-1][1]
    diag["source"] = "contour"
    diag["candidates"] = [quad for _, quad in cands]
    return chosen, diag


def select_quad_by_flange_scale(candidates: List[np.ndarray], pairs, cfg: Config
                                ) -> Tuple[Optional[int], dict]:
    """Izmed kandidatnih pravokotnikov izbere tistega, ki je skladen s premeri prirobnic.

    Zgornji rob zaboja je vecji pravokotnik nekaj cm nad dnom; ce ga zamenjamo z
    dnom, je merilo napacno za nekaj odstotkov, prirobnice pa "padejo" pod dno.
    Spodnja plast prirobnic dejansko lezi na dnu, zato mora biti nizji kvantil
    razmerja med izmerjenim in napovedanim premerom enak 1.
    """
    diag: dict = {"ratios": []}
    r_out = float(cfg["flange.d_out_mm"]) / 2.0
    usable = [p for p in pairs if p.outer is not None]
    if not candidates or len(usable) < int(cfg["box.detect.scale_select_min_flanges"]):
        diag["reason"] = "premalo prirobnic za izbiro po merilu"
        return None, diag
    _, obj = box_frame_points(candidates[0], cfg)
    quantile = float(cfg["box.detect.scale_select_quantile"])

    best_idx, best_err = None, None
    for idx, quad in enumerate(candidates):
        quad_o, obj_o = box_frame_points(quad, cfg)
        h_mat, _ = cv2.findHomography(obj_o.astype(np.float32), quad_o.astype(np.float32), 0)
        if h_mat is None:
            diag["ratios"].append(None)
            continue
        try:
            h_inv = np.linalg.inv(h_mat)
        except np.linalg.LinAlgError:
            diag["ratios"].append(None)
            continue
        ratios = []
        for pair in usable:
            hom = h_inv @ np.array([pair.outer.cx, pair.outer.cy, 1.0])
            if abs(hom[2]) < 1e-12:
                continue
            scale = _homography_scale(h_mat, hom[:2] / hom[2])
            if not scale or scale <= 0:
                continue
            ratios.append(pair.outer.a / (scale * r_out))
        if not ratios:
            diag["ratios"].append(None)
            continue
        value = float(np.percentile(ratios, quantile))
        diag["ratios"].append(round(value, 4))
        err = abs(value - 1.0)
        if best_err is None or err < best_err:
            best_idx, best_err = idx, err
    diag["chosen"] = best_idx
    diag["error"] = None if best_err is None else round(best_err, 4)
    if best_err is not None and best_err > float(cfg["box.detect.scale_select_max_error"]):
        diag["reason"] = ("noben kandidat ni skladen s premeri prirobnic - preveri dimenzije "
                          "zaboja ali premer prirobnice")
    return best_idx, diag


def refine_quad_with_edges(quad: np.ndarray, edge_points: Optional[np.ndarray], cfg: Config
                           ) -> Tuple[np.ndarray, dict]:
    """Izostri vogale z ortogonalno regresijo stranic na subpixel robnih tockah.

    Lega izginjajoce tocke je izjemno obcutljiva na kot stranice, approxPolyDP pa
    da vogale le na piksel natancno. Fit celotne stranice cez stotine tock ta kot
    bistveno stabilizira.
    """
    diag: dict = {"sides_fitted": 0}
    if edge_points is None or len(edge_points) < 4:
        diag["reason"] = "ni robnih tock"
        return quad, diag
    band = float(cfg["box.detect.side_band_px"])
    corner_frac = float(cfg["box.detect.side_corner_skip_frac"])
    min_pts = int(cfg["box.detect.side_min_points"])
    pts = np.asarray(edge_points, dtype=float)

    lines = []
    for i in range(4):
        p0, p1 = quad[i], quad[(i + 1) % 4]
        vec = p1 - p0
        length = float(np.linalg.norm(vec))
        if length < 1e-6:
            lines.append(None)
            continue
        u = vec / length
        normal = np.array([-u[1], u[0]])
        rel = (pts - p0) @ u
        perp = (pts - p0) @ normal
        sel = (rel > corner_frac * length) & (rel < (1.0 - corner_frac) * length) & (np.abs(perp) < band)
        chosen = pts[sel]
        if len(chosen) < min_pts:
            lines.append(None)
            continue
        for _ in range(int(cfg["box.detect.side_trim_iterations"])):
            mean = chosen.mean(axis=0)
            _, _, vt = np.linalg.svd(chosen - mean, full_matrices=False)
            direction = vt[0]
            nrm = np.array([-direction[1], direction[0]])
            resid = (chosen - mean) @ nrm
            sigma = float(np.std(resid))
            if sigma < 1e-6:
                break
            keep = np.abs(resid) < 2.0 * sigma
            if keep.sum() < min_pts:
                break
            chosen = chosen[keep]
        mean = chosen.mean(axis=0)
        _, _, vt = np.linalg.svd(chosen - mean, full_matrices=False)
        direction = vt[0]
        nrm = np.array([-direction[1], direction[0]])
        lines.append((nrm, float(nrm @ mean), len(chosen)))
        diag["sides_fitted"] += 1

    if any(line is None for line in lines):
        diag["reason"] = "vseh stirih stranic ni bilo mogoce fitati"
        return quad, diag

    refined = []
    for i in range(4):
        n_a, c_a, _ = lines[(i - 1) % 4]
        n_b, c_b, _ = lines[i]
        mat = np.stack([n_a, n_b])
        if abs(np.linalg.det(mat)) < 1e-9:
            diag["reason"] = "sosednji stranici sta skoraj vzporedni"
            return quad, diag
        refined.append(np.linalg.solve(mat, np.array([c_a, c_b])))
    refined = np.asarray(refined, dtype=float)
    shift = float(np.max(np.linalg.norm(refined - quad, axis=1)))
    if shift > float(cfg["box.detect.side_max_shift_px"]):
        diag["reason"] = f"izostritev bi vogale premaknila za {shift:.1f} px - zavrnjeno"
        return quad, diag
    diag["max_corner_shift_px"] = shift
    diag["n_side_points"] = [line[2] for line in lines]
    return refined, diag


def _quad_from_hough(edges: np.ndarray, cfg: Config) -> Tuple[Optional[np.ndarray], dict]:
    """Rezervna pot: Hough linije, dve orientacijski skupini, presecisca skrajnih linij."""
    diag = {"hough_lines": 0}
    h, w = edges.shape[:2]
    min_len = float(cfg["box.detect.hough_min_line_frac"]) * min(h, w)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 360.0,
                            int(cfg["box.detect.hough_threshold"]),
                            minLineLength=min_len,
                            maxLineGap=float(cfg["box.detect.hough_max_gap_px"]))
    if lines is None:
        return None, diag
    lines = lines.reshape(-1, 4)
    diag["hough_lines"] = int(len(lines))
    angles = np.arctan2(lines[:, 3] - lines[:, 1], lines[:, 2] - lines[:, 0]) % math.pi
    group_a = np.abs(np.sin(angles)) < math.sin(math.radians(45.0))
    if group_a.sum() < 2 or (~group_a).sum() < 2:
        return None, diag

    def extremes(subset: np.ndarray, axis: int) -> Tuple[np.ndarray, np.ndarray]:
        mids = 0.5 * (subset[:, [0, 1]] + subset[:, [2, 3]])
        lo = subset[int(np.argmin(mids[:, axis]))]
        hi = subset[int(np.argmax(mids[:, axis]))]
        return lo, hi

    horiz = lines[group_a]
    vert = lines[~group_a]
    h_lo, h_hi = extremes(horiz, 1)
    v_lo, v_hi = extremes(vert, 0)

    def to_line(seg: np.ndarray) -> np.ndarray:
        p1 = np.array([seg[0], seg[1], 1.0])
        p2 = np.array([seg[2], seg[3], 1.0])
        return np.cross(p1, p2)

    corners = []
    for hl in (h_lo, h_hi):
        for vl in (v_lo, v_hi):
            p = np.cross(to_line(hl), to_line(vl))
            if abs(p[2]) < 1e-9:
                return None, diag
            corners.append(p[:2] / p[2])
    quad = np.asarray(corners, dtype=float)
    if np.any(~np.isfinite(quad)):
        return None, diag
    margin = 0.5 * max(h, w)
    if np.any(quad[:, 0] < -margin) or np.any(quad[:, 0] > w + margin):
        return None, diag
    if np.any(quad[:, 1] < -margin) or np.any(quad[:, 1] > h + margin):
        return None, diag
    quad = _order_quad(quad)
    if not _quad_angles_ok(quad, cfg) or not _aspect_plausible(quad, cfg):
        diag["reason"] = "Houghov kandidat nima verjetnega razmerja stranic"
        return None, diag
    return quad, diag


# --------------------------------------------------------------------------
# homografija in izginjajoce tocke
# --------------------------------------------------------------------------
def box_frame_points(quad: np.ndarray, cfg: Config) -> Tuple[np.ndarray, np.ndarray]:
    """Vrne (zasukan quad, mm koordinate) tako, da stranica P0->P1 ustreza box.w_mm.

    S tem je os X vedno vzdolz w_mm in os Y vzdolz h_mm. Preostane 2-kratna
    dvoumnost (zasuk za 180 stopinj), ki je iz same slike ni mogoce razresiti -
    zaboj je pravokotnik brez oznak. Ce robot potrebuje absolutno orientacijo,
    je treba dodati oznako na enem vogalu ali podati box.corners_px.
    """
    w_mm = float(cfg["box.w_mm"])
    h_mm = float(cfg["box.h_mm"])
    side_a = 0.5 * (np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[3] - quad[2]))
    side_b = 0.5 * (np.linalg.norm(quad[2] - quad[1]) + np.linalg.norm(quad[0] - quad[3]))
    if (side_a >= side_b) != (w_mm >= h_mm):
        quad = np.roll(quad, -1, axis=0)
    obj = np.array([[0.0, 0.0], [w_mm, 0.0], [w_mm, h_mm], [0.0, h_mm]], dtype=float)
    return quad, obj


def f_from_vanishing_points(quad: np.ndarray, principal: Tuple[float, float], cfg: Config
                            ) -> Tuple[Optional[float], dict]:
    """f_px iz ortogonalnosti dveh izginjajocih tock (kvadratni piksli)."""
    diag: dict = {}
    pts = [np.array([p[0], p[1], 1.0]) for p in quad]
    l0 = np.cross(pts[0], pts[1])
    l1 = np.cross(pts[3], pts[2])
    l2 = np.cross(pts[1], pts[2])
    l3 = np.cross(pts[0], pts[3])
    v1 = np.cross(l0, l1)
    v2 = np.cross(l2, l3)
    diag_len = float(np.hypot(*(quad.max(axis=0) - quad.min(axis=0))))
    max_dist = float(cfg["autocalib.vanishing.max_vp_distance_diag"]) * max(diag_len, 1.0)

    def finite(v: np.ndarray) -> Optional[np.ndarray]:
        if abs(v[2]) < 1e-12:
            return None
        p = v[:2] / v[2]
        if not np.all(np.isfinite(p)) or np.linalg.norm(p - np.asarray(principal)) > max_dist:
            return None
        return p

    p1, p2 = finite(v1), finite(v2)
    diag["vp1"] = None if p1 is None else [float(p1[0]), float(p1[1])]
    diag["vp2"] = None if p2 is None else [float(p2[0]), float(p2[1])]
    if p1 is None or p2 is None:
        diag["reason"] = "izginjajoci tocki sta prakticno v neskoncnosti (premalo perspektive)"
        return None, diag
    c = np.asarray(principal, dtype=float)
    val = -float((p1 - c) @ (p2 - c))
    diag["f_squared"] = val
    if val <= 0:
        diag["reason"] = "negativen f^2 - opticno sredisce ali detekcija zaboja nista skladna"
        return None, diag
    f = math.sqrt(val)
    if not (float(cfg["autocalib.vanishing.min_f_px"]) <= f
            <= float(cfg["autocalib.vanishing.max_f_px"])):
        diag["reason"] = f"f={f:.1f} px izven dovoljenega obsega"
        return None, diag
    # obcutljivost: blizje kot sta VP, mocnejsa je perspektiva in ocena
    diag["vp_distance_ratio"] = float(min(np.linalg.norm(p1 - c), np.linalg.norm(p2 - c))
                                      / max(diag_len, 1.0))
    return f, diag


def k_from_f(f: float, principal: Tuple[float, float]) -> np.ndarray:
    return np.array([[f, 0.0, principal[0]], [0.0, f, principal[1]], [0.0, 0.0, 1.0]])


def decompose_plane_homography(h_mat: np.ndarray, k_mat: np.ndarray
                               ) -> Tuple[np.ndarray, np.ndarray]:
    """Iz homografije ravnine in K dobi pozo ravnine (R: box -> kamera, t)."""
    m = np.linalg.inv(k_mat) @ h_mat
    scale = 2.0 / (np.linalg.norm(m[:, 0]) + np.linalg.norm(m[:, 1]))
    m = m * scale
    if m[2, 2] < 0:                       # ravnina mora biti pred kamero
        m = -m
    r1, r2, t = m[:, 0], m[:, 1], m[:, 2]
    r3 = np.cross(r1, r2)
    rot = np.column_stack([r1, r2, r3])
    u, _, vt = np.linalg.svd(rot)
    rot = u @ vt
    if np.linalg.det(rot) < 0:
        u[:, 2] *= -1
        rot = u @ vt
    return rot, t


def _flip_quad_handedness(quad: np.ndarray) -> np.ndarray:
    """Zrcali ciklicni vrstni red vogalov (menja levo/desno sucnost sistema)."""
    return quad[[0, 3, 2, 1]]


# --------------------------------------------------------------------------
# izboljsava f na koncentricnih parih
# --------------------------------------------------------------------------
def plane_consensus_cost(pairs, h_mat: np.ndarray, principal: Tuple[float, float],
                         f: float, cfg: Config) -> Optional[float]:
    """Kako zelo se normale prirobnic razhajajo od normale dna pri danem f [deg].

    Prirobnice, ki lezijo plosko na dnu, morajo imeti normalo vzporedno z
    normalo dna. Pri napacnem f se rekonstruirani krogi ne dajo veckrat
    koplanarno uleci v rekonstruirano ravnino in razlika naraste. Ucinek je
    prvega reda v ekscentricnosti v sliki, torej mnogo mocnejsi od nesoglasja
    koncentricnega para (drugi red v r/Z).
    """
    k_mat = k_from_f(float(f), principal)
    rot, _ = decompose_plane_homography(h_mat, k_mat)
    n_plane = rot[:, 2] / np.linalg.norm(rot[:, 2])
    if n_plane[2] > 0:
        n_plane = -n_plane
    r_out = float(cfg["flange.d_out_mm"]) / 2.0
    angles = []
    for pair in pairs:
        sols = circle_pose_solutions(pair.outer.matrix(), k_mat, r_out)
        if not sols:
            continue
        angles.append(min(math.degrees(math.acos(float(np.clip(abs(s.normal @ n_plane), -1, 1))))
                          for s in sols))
    if len(angles) < int(cfg["autocalib.refine.min_flanges"]):
        return None
    return float(np.percentile(angles, float(cfg["autocalib.refine.plane_percentile"])))


def refine_f(pairs, h_mat: Optional[np.ndarray], principal: Tuple[float, float],
             f_init: Optional[float], cfg: Config) -> Tuple[Optional[float], dict]:
    """Izboljsa f_px z izbrano cenilko (glej autocalib.refine.method)."""
    method = str(cfg["autocalib.refine.method"])
    diag: dict = {"method": method,
                  "n_pairs": sum(1 for p in pairs if p.inner is not None),
                  "n_ellipses": len(pairs)}
    if not bool(cfg["autocalib.refine.enabled"]) or method == "none":
        diag["reason"] = "izklopljeno v configu"
        return None, diag

    if method == "plane_consensus":
        if h_mat is None:
            diag["reason"] = "brez homografije dna kriterij ravnine ni definiran"
            return None, diag

        def cost(f: float) -> float:
            value = plane_consensus_cost(pairs, h_mat, principal, float(f), cfg)
            return float("inf") if value is None else value
    elif method == "pair_consistency":
        if diag["n_pairs"] < int(cfg["autocalib.refine.min_pairs"]):
            diag["reason"] = "premalo parov elips"
            return None, diag

        def cost(f: float) -> float:
            value = pair_consistency_cost(pairs, k_from_f(float(f), principal), cfg)
            return float("inf") if value is None else value
    else:
        diag["reason"] = f"neznana metoda '{method}'"
        return None, diag

    base = f_init if f_init else float(cfg["autocalib.fallback_f_px"])
    lo = max(float(cfg["autocalib.vanishing.min_f_px"]),
             base * float(cfg["autocalib.refine.f_lo_factor"]))
    hi = min(float(cfg["autocalib.vanishing.max_f_px"]),
             base * float(cfg["autocalib.refine.f_hi_factor"]))
    if hi <= lo:
        diag["reason"] = "prazen interval iskanja"
        return None, diag

    grid = np.geomspace(lo, hi, int(cfg["autocalib.refine.grid_points"]))
    costs = np.array([cost(f) for f in grid])
    if not np.any(np.isfinite(costs)):
        diag["reason"] = "cenilke ni bilo mogoce izracunati"
        return None, diag
    idx = int(np.nanargmin(costs))
    f_best = float(grid[idx])
    c_best = float(costs[idx])

    # lokalna izostritev
    left = grid[max(idx - 1, 0)]
    right = grid[min(idx + 1, len(grid) - 1)]
    if right > left:
        from scipy.optimize import minimize_scalar
        res = minimize_scalar(cost, bounds=(left, right), method="bounded",
                              options={"xatol": max(0.5, 1e-4 * f_best)})
        if res.success and np.isfinite(res.fun) and res.fun <= c_best:
            f_best, c_best = float(res.x), float(res.fun)

    delta = float(cfg["autocalib.refine.sensitivity_delta"])
    c_lo = cost(f_best * (1.0 - delta))
    c_hi = cost(f_best * (1.0 + delta))
    sensitivity = float(0.5 * (min(c_lo, 1e6) + min(c_hi, 1e6)) - c_best)
    diag.update({"f_grid_best": f_best, "residual": c_best, "sensitivity": sensitivity,
                 "search": [lo, hi]})
    if sensitivity < float(cfg["autocalib.refine.min_sensitivity"]):
        diag["reason"] = "degeneriran problem (cenilka je po f skoraj ravna)"
        return None, diag
    return f_best, diag


# --------------------------------------------------------------------------
# glavna funkcija
# --------------------------------------------------------------------------
def calibrate(gray: np.ndarray, pairs, cfg: Config,
              edge_points: Optional[np.ndarray] = None) -> Calibration:
    """Vrne kalibracijo; nikoli ne vrze izjeme in nikoli ne odpove tiho.

    Kljucna locnica: koordinatni sistem zaboja (in s tem X, Y ter naklon) je
    odvisen le od detekcije zaboja, ne od natancnosti f_px. Napacen f namrec
    skoraj natanko skalira globino scene - lateralne koordinate na dnu ostanejo
    prave, skalira se le visina nad dnom. Zato se sistem degradira sele takrat,
    ko zaboja ni mogoce najti.
    """
    h, w = gray.shape[:2]
    pp_cfg = cfg.get("camera.principal_point_px", None)
    principal = (float(pp_cfg[0]), float(pp_cfg[1])) if pp_cfg else (w / 2.0, h / 2.0)
    warnings: List[str] = []
    diag: dict = {"principal_point": list(principal)}

    quad, quad_diag = detect_box_quad(gray, cfg)
    quad_candidates = quad_diag.pop("candidates", None)
    diag["box_detect"] = quad_diag

    if quad is not None and quad_candidates and len(quad_candidates) > 1:
        best_idx, select_diag = select_quad_by_flange_scale(quad_candidates, pairs, cfg)
        diag["quad_select"] = select_diag
        if best_idx is not None and "reason" not in select_diag:
            quad = quad_candidates[best_idx]
        elif "reason" in select_diag and select_diag.get("chosen") is not None:
            warnings.append("izbira pravokotnika zaboja po merilu: " + str(select_diag["reason"]))

    obj: Optional[np.ndarray] = None
    homography: Optional[np.ndarray] = None
    f_vp: Optional[float] = None
    vp_ratio: Optional[float] = None
    if quad is not None:
        if quad_diag.get("source") != "config":
            quad, refine_diag_quad = refine_quad_with_edges(quad, edge_points, cfg)
            diag["quad_refine"] = refine_diag_quad
        quad, obj = box_frame_points(quad, cfg)
        homography, _ = cv2.findHomography(obj.astype(np.float32), quad.astype(np.float32), 0)
        f_vp, vp_diag = f_from_vanishing_points(quad, principal, cfg)
        diag["vanishing"] = vp_diag
        vp_ratio = vp_diag.get("vp_distance_ratio")
        if f_vp is None:
            warnings.append("izginjajoci tocki neuporabni: "
                            + str(vp_diag.get("reason", "neznano")))
    else:
        warnings.append("zaboja ni bilo mogoce detektirati")

    f_refined, refine_diag = refine_f(pairs, homography, principal, f_vp, cfg)
    diag["refine"] = refine_diag

    prior = cfg.get("camera.f_px_prior", None)
    wd = cfg.get("camera.working_distance_mm", None)
    f_wd: Optional[float] = None
    if wd and homography is not None and obj is not None:
        scale = _homography_scale(homography, obj.mean(axis=0))
        if scale and scale > 0:
            f_wd = float(scale * float(wd))
            diag["f_from_working_distance"] = f_wd

    # Prioriteta virov za f_px: eksplicitni prior > delovna razdalja >
    # izostritev na sceni > izginjajoce tocke > rezerva.
    f_px: Optional[float] = None
    method = "unknown"
    f_confidence = 0.0
    if prior:
        f_px, method, f_confidence = float(prior), "config_prior", 0.9
    elif f_wd is not None:
        f_px, method, f_confidence = f_wd, "working_distance_prior", 0.75
    elif f_refined is not None:
        f_px, method, f_confidence = float(f_refined), \
            "scene_refine_" + str(cfg["autocalib.refine.method"]), 0.6
    elif f_vp is not None:
        f_px, method = float(f_vp), "box_vanishing_points"
        # blizje kot sta izginjajoci tocki, mocnejsa je perspektiva in ocena
        f_confidence = 0.6 if vp_ratio is None else float(np.clip(6.0 / max(vp_ratio, 1e-6), 0.1, 0.8))

    if f_vp is not None and f_refined is not None:
        rel = abs(f_refined - f_vp) / f_vp
        diag["vp_vs_refine_rel_diff"] = float(rel)
        if rel > float(cfg["autocalib.max_f_disagreement"]):
            warnings.append(f"oceni f_px iz izginjajocih tock in iz scene se razlikujeta za {rel:.0%}")
            f_confidence *= 0.5

    rot_box = t_box = None
    frame_reliable = False
    if f_px is None:
        f_px = float(cfg["autocalib.fallback_f_px"])
        method = "fallback_f_px"
        f_confidence = 0.0
        warnings.append(
            "f_px ni bilo mogoce izpeljati iz scene (premalo perspektive) - uporabljena je "
            "rezervna vrednost; visine nad dnom so skalirane z neznanim faktorjem. "
            "Podaj camera.working_distance_mm ali camera.f_px_prior.")

    if quad is not None and homography is not None and obj is not None:
        rot_box, t_box = decompose_plane_homography(homography, k_from_f(f_px, principal))
        if rot_box[2, 2] > 0:      # Z zaboja mora gledati proti kameri
            quad = _flip_quad_handedness(quad)
            quad, obj = box_frame_points(quad, cfg)
            homography, _ = cv2.findHomography(obj.astype(np.float32),
                                               quad.astype(np.float32), 0)
            rot_box, t_box = decompose_plane_homography(homography, k_from_f(f_px, principal))
        frame_reliable = True
    else:
        method = "degraded_relative_only"
        warnings.append("koordinatni sistem zaboja ni na voljo - koordinate so v kamerinem "
                        "sistemu; uporabno je le relativno rangiranje")

    # Zaupanje v kalibracijo kot celoto: okvir je vreden vec kot absolutno merilo,
    # ker X, Y in naklon od f skoraj niso odvisni.
    confidence = (0.5 + 0.5 * f_confidence) if frame_reliable else 0.0
    calib = Calibration(k_mat=k_from_f(f_px, principal), f_px=float(f_px), principal_point=principal,
                        method=method, confidence=float(confidence), rot_box=rot_box, t_box=t_box,
                        homography=homography, quad_px=quad, frame_reliable=frame_reliable,
                        diagnostics=diag, warnings=warnings)
    calib.f_confidence = float(f_confidence)
    return calib


def _homography_scale(h_mat: np.ndarray, at_mm: np.ndarray) -> Optional[float]:
    """Lokalno merilo px/mm ravnine v dani tocki (koren determinante Jacobijeve matrike)."""
    x, y = float(at_mm[0]), float(at_mm[1])
    p = h_mat @ np.array([x, y, 1.0])
    if abs(p[2]) < 1e-12:
        return None
    eps = 1e-3
    jac = np.zeros((2, 2))
    for i, d in enumerate(((eps, 0.0), (0.0, eps))):
        q = h_mat @ np.array([x + d[0], y + d[1], 1.0])
        if abs(q[2]) < 1e-12:
            return None
        jac[:, i] = (q[:2] / q[2] - p[:2] / p[2]) / eps
    det = abs(np.linalg.det(jac))
    return math.sqrt(det) if det > 0 else None


def scale_consistency_check(candidates, calib: Calibration, cfg: Config) -> dict:
    """Prirobnica, ki lezi plosko na dnu, mora imeti projicirani premer skladen z D_out.

    Merilo na dnu je doloceno s homografijo, zato to preverja skladnost
    detekcije zaboja in podanih dimenzij (ne f_px neposredno).
    """
    out = {"n_flat": 0, "median_ratio": None, "ok": None}
    if calib.homography is None or not candidates:
        out["reason"] = "ni homografije ali kandidatov"
        return out
    flat_max = float(cfg["autocalib.scale_check.flat_tilt_deg_max"])
    d_out = float(cfg["flange.d_out_mm"])
    ratios = []
    for cand in candidates:
        pose = cand.pose
        if pose.center_box is None or pose.tilt_deg > flat_max:
            continue
        scale = _homography_scale(calib.homography, pose.center_box[:2])
        if not scale:
            continue
        d_pred_px = scale * d_out
        d_meas_px = 2.0 * cand.pair.outer.a
        if d_pred_px > 1e-6:
            ratios.append(d_meas_px / d_pred_px)
    out["n_flat"] = len(ratios)
    if not ratios:
        out["reason"] = "ni plosko lezecih prirobnic"
        return out
    med = float(np.median(ratios))
    tol = float(cfg["autocalib.scale_check.ratio_tolerance"])
    out["median_ratio"] = med
    out["ok"] = bool(abs(med - 1.0) <= tol)
    if not out["ok"]:
        out["reason"] = ("izmerjeni premeri se ne ujemajo z merilom dna - preveri dimenzije "
                         "zaboja ali detekcijo vogalov")
    return out
