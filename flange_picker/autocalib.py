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


def detect_box_quad(gray: np.ndarray, cfg: Config,
                    raw_gray: Optional[np.ndarray] = None) -> Tuple[Optional[np.ndarray], dict]:
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

    diag["n_contour_candidates"] = len(cands)
    # Drugi, neodvisen vir kandidatov: velika homogena obmocja. Deluje tudi
    # takrat, ko prirobnica ob robu prekine konturo dna.
    region_quads = _quad_from_regions(raw_gray if raw_gray is not None else gray, cfg)
    diag["n_region_candidates"] = len(region_quads)
    for quad in region_quads:
        area = float(cv2.contourArea(quad.astype(np.float32)))
        if any(np.mean(np.linalg.norm(quad - other, axis=1))
               < float(cfg["box.detect.candidate_merge_px"]) for _, other in cands):
            continue
        cands.append((area, quad))

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
    diag["source"] = "contour+region"
    diag["candidates"] = [quad for _, quad in cands]
    return chosen, diag


def _quad_from_regions(gray: np.ndarray, cfg: Config) -> List[np.ndarray]:
    """Kandidatni pravokotniki iz velikih homogenih obmocij, ne iz kontur.

    Kadar se prirobnica dotakne roba dna, se kontura dna prekine in fit
    kvadrilaterala po konturah odpove. Dno pa ostane veliko homogeno obmocje,
    zato ga poiscemo kot najvecjo povezano komponento Otsujeve segmentacije -
    v obeh polaritetah, ker dno ni nujno svetlejse od sten.

    Vhod mora biti SUROVA slika: CLAHE lokalno preslika nivoje in dno se zlije
    s steno, zato Otsu na izboljsani sliki zajame tudi steno.
    """
    out: List[np.ndarray] = []
    ksize = int(cfg["box.detect.blur_ksize"]) | 1
    blur = cv2.GaussianBlur(gray, (ksize, ksize), 0)
    area_img = float(gray.shape[0] * gray.shape[1])
    min_area = float(cfg["box.detect.min_area_frac"]) * area_img
    max_area = float(cfg["box.detect.max_area_frac"]) * area_img
    close = int(cfg["box.detect.region_close_px"])
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)) if close > 0 else None

    # Vec nivojev, ne le en Otsu: prizorisce ima tri sloje svetlosti (ozadje,
    # stena, dno), zato en sam prag lahko poda le eno od obeh meja. Z rekurzivnim
    # Otsujem dobimo tudi obris zaboja, ki je potreben za oceno f iz dveh ravnin.
    masks = []
    for thr in _recursive_otsu_thresholds(blur):
        _, mask = cv2.threshold(blur, thr, 255, cv2.THRESH_BINARY)
        masks.append(mask)
        masks.append(cv2.bitwise_not(mask))

    for mask in masks:
        if kernel is not None:
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if num <= 1:
            continue
        idx = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
        area = float(stats[idx, cv2.CC_STAT_AREA])
        if area < min_area or area > max_area:
            continue
        blob = (labels == idx).astype(np.uint8) * 255
        contours, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        hull = cv2.convexHull(max(contours, key=cv2.contourArea))
        quad = _hull_to_quad(hull, cfg)
        if quad is None:
            continue
        # Povrsino je treba preveriti na samem kvadrilateralu: konveksna ovojnica
        # razpotegnjene komponente je lahko mnogo vecja od nje (npr. cel kader).
        quad_area = float(cv2.contourArea(quad.astype(np.float32)))
        if quad_area < min_area or quad_area > max_area:
            continue
        if not (_quad_angles_ok(quad, cfg) and _aspect_plausible(quad, cfg)):
            continue
        merge = float(cfg["box.detect.candidate_merge_px"])
        if any(np.mean(np.linalg.norm(quad - other, axis=1)) < merge for other in out):
            continue
        out.append(quad)
    return out


def _recursive_otsu_thresholds(gray: np.ndarray) -> List[int]:
    """Otsu na celotni sliki in nato se na vsaki od obeh podpopulacij."""
    base, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    base = int(base)
    thresholds = [base]
    lower = gray[gray <= base]
    upper = gray[gray > base]
    for part in (lower, upper):
        if part.size < 64:
            continue
        thr, _ = cv2.threshold(part.reshape(-1, 1).astype(np.uint8), 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresholds.append(int(thr))
    return sorted(set(t for t in thresholds if 0 < t < 255))


def _hull_to_quad(hull: np.ndarray, cfg: Config) -> Optional[np.ndarray]:
    """Poisce stiri oglisca konveksne ovojnice s prilagodljivim approxPolyDP."""
    perim = cv2.arcLength(hull, True)
    if perim < 1e-6:
        return None
    lo, hi = 0.005, 0.12
    for _ in range(int(cfg["box.detect.hull_search_iterations"])):
        eps = 0.5 * (lo + hi)
        approx = cv2.approxPolyDP(hull, eps * perim, True)
        if len(approx) == 4:
            return _order_quad(approx.reshape(4, 2).astype(float))
        if len(approx) > 4:
            lo = eps
        else:
            hi = eps
    return None


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
    # Le trdni pari: merilo, izbrano po dvomljivih detekcijah, pokvari homografijo
    # in s tem vse, kar iz nje sledi (izmerjeno: pravi kos zavrnjen kot "3.7-krat
    # prevelik", ker je merilo prislo iz napacnega pravokotnika).
    usable = [p for p in pairs
              if p.outer is not None and p.paired and p.role == "outer"
              and p.outer.support_ratio >= float(cfg["ellipse.min_support_ratio"])]
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

    Lega izginjajoce tocke je izjemno obcutljiva na kot stranice, approxPolyDP in
    konveksna ovojnica pa dasta vogale le grobo. Fit celotne stranice cez stotine
    tock ta kot bistveno stabilizira.

    Postopek je grobo-fin: prvi prehod z siroko okolico pobere stranico tudi, ce
    je zacetna ocena zgresena za nekaj deset pikslov, drugi prehod z ozko okolico
    pa jo izostri. Izmerjeno: konvergira na ~0.5 px ne glede na zacetno lego.
    """
    diag: dict = {"sides_fitted": 0, "passes": []}
    if edge_points is None or len(edge_points) < 4:
        diag["reason"] = "ni robnih tock"
        return quad, diag
    bands = [float(cfg["box.detect.side_band_coarse_px"]), float(cfg["box.detect.side_band_px"])]
    current = quad
    for band in bands:
        refined, pass_diag = _refine_quad_once(current, edge_points, band, cfg)
        diag["passes"].append(pass_diag)
        if refined is None:
            break
        # Izostritev sprejmemo le, ce rezultat se vedno izgleda kot dno zaboja.
        if not _quad_angles_ok(refined, cfg) or not _aspect_plausible(refined, cfg):
            diag["reason"] = "izostren kvadrilateral ni vec verjeten - zavrnjeno"
            break
        current = refined
        diag["sides_fitted"] = pass_diag.get("sides_fitted", 0)
    diag["max_corner_shift_px"] = float(np.max(np.linalg.norm(current - quad, axis=1)))
    return current, diag


def _refine_quad_once(quad: np.ndarray, edge_points: np.ndarray, band: float, cfg: Config
                      ) -> Tuple[Optional[np.ndarray], dict]:
    diag: dict = {"band_px": band, "sides_fitted": 0}
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
        # V pasu je lahko vec vzporednih robov (dno in zgornji rob zaboja sta le
        # nekaj deset pikslov narazen). Navadna regresija bi ju povprecila, zato
        # najprej poiscemo prevladujoci nivo in obdrzimo le tocke ob njem.
        offsets = perp[sel]
        bin_px = float(cfg["box.detect.side_peak_bin_px"])
        hist, bin_edges = np.histogram(offsets, bins=max(3, int(2.0 * band / bin_px)),
                                       range=(-band, band))
        centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        strong = hist >= float(cfg["box.detect.side_peak_min_fraction"]) * hist.max()
        if strong.any():
            # Med dovolj mocnimi robovi vzamemo NAJBLIZJEGA zacetni oceni, ne
            # najmocnejsega: zacetna ocena je prior, mocnejsi rob pa je lahko
            # sosednji (npr. zgornji rob zaboja namesto dna).
            peak = float(centres[strong][int(np.argmin(np.abs(centres[strong])))])
            near_peak = np.abs(offsets - peak) < float(cfg["box.detect.side_peak_window_px"])
            if near_peak.sum() >= min_pts:
                chosen = chosen[near_peak]
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
        return None, diag

    refined = []
    for i in range(4):
        n_a, c_a, _ = lines[(i - 1) % 4]
        n_b, c_b, _ = lines[i]
        mat = np.stack([n_a, n_b])
        if abs(np.linalg.det(mat)) < 1e-9:
            diag["reason"] = "sosednji stranici sta skoraj vzporedni"
            return None, diag
        refined.append(np.linalg.solve(mat, np.array([c_a, c_b])))
    refined = np.asarray(refined, dtype=float)
    if not np.all(np.isfinite(refined)):
        diag["reason"] = "presecisca stranic niso koncna"
        return None, diag
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
def box_frame_points(quad: np.ndarray, cfg: Config,
                     dims_mm: Optional[Tuple[float, float]] = None
                     ) -> Tuple[np.ndarray, np.ndarray]:
    """Vrne (zasukan quad, mm koordinate) tako, da stranica P0->P1 ustreza box.w_mm.

    S tem je os X vedno vzdolz w_mm in os Y vzdolz h_mm. Preostane 2-kratna
    dvoumnost (zasuk za 180 stopinj), ki je iz same slike ni mogoce razresiti -
    zaboj je pravokotnik brez oznak. Ce robot potrebuje absolutno orientacijo,
    je treba dodati oznako na enem vogalu ali podati box.corners_px.
    """
    w_mm, h_mm = dims_mm if dims_mm else (float(cfg["box.w_mm"]), float(cfg["box.h_mm"]))
    side_a = 0.5 * (np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[3] - quad[2]))
    side_b = 0.5 * (np.linalg.norm(quad[2] - quad[1]) + np.linalg.norm(quad[0] - quad[3]))
    if (side_a >= side_b) != (w_mm >= h_mm):
        quad = np.roll(quad, -1, axis=0)
    obj = np.array([[0.0, 0.0], [w_mm, 0.0], [w_mm, h_mm], [0.0, h_mm]], dtype=float)
    return quad, obj


def _plane_scale_of_quad(quad: np.ndarray, dims_mm: Tuple[float, float], cfg: Config
                         ) -> Optional[float]:
    """Merilo px/mm ravnine, ki jo doloca pravokotnik znanih dimenzij."""
    quad_o, obj = box_frame_points(quad, cfg, dims_mm)
    h_mat, _ = cv2.findHomography(obj.astype(np.float32), quad_o.astype(np.float32), 0)
    if h_mat is None:
        return None
    return _homography_scale(h_mat, obj.mean(axis=0))


def f_from_box_rim(bottom_quad: np.ndarray, candidates: List[np.ndarray], cfg: Config,
                   principal: Tuple[float, float],
                   edge_points: Optional[np.ndarray] = None
                   ) -> Tuple[Optional[float], dict]:
    """f_px iz dveh vzporednih pravokotnikov na znani medsebojni visini.

    Dno in zgornji rob zaboja sta dve vzporedni ravnini, razmaknjeni za visino
    stene. Za vsako velja merilo s = f / Z, torej

        Z_dno - Z_rob = h   =>   f / s_dno - f / s_rob = h
        f = h * s_dno * s_rob / (s_rob - s_dno)

    To je edini vir absolutnega merila, ki deluje tudi pri strogo navpicni
    kameri, kjer sta izginjajoci tocki v neskoncnosti in je f iz ravninske
    scene nacelno neopazljiv. Zahteva le visino stene in njeno debelino -
    podatka, ki ju uporabnik o svojem zaboju ima.
    """
    diag: dict = {}
    wall_h = cfg.get("box.wall_height_mm", None)
    if not wall_h:
        diag["reason"] = "box.wall_height_mm ni podan"
        return None, diag
    wall_t = float(cfg.get("box.wall_thickness_mm", 0.0) or 0.0)
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])

    rim = None
    bottom_area = float(cv2.contourArea(bottom_quad.astype(np.float32)))
    for cand in candidates:
        area = float(cv2.contourArea(cand.astype(np.float32)))
        if area <= bottom_area * float(cfg["box.detect.rim_min_area_ratio"]):
            continue
        if all(cv2.pointPolygonTest(cand.astype(np.float32), (float(p[0]), float(p[1])), False) >= 0
               for p in bottom_quad):
            if rim is None or area < float(cv2.contourArea(rim.astype(np.float32))):
                rim = cand
    if rim is None:
        diag["reason"] = "zgornjega roba zaboja ni med kandidati"
        return None, diag

    # Relativna napaka f je ~ Z/h krat relativna napaka razmerja meril (pri
    # tipicni geometriji faktor ~12), zato morata biti OBA pravokotnika
    # izostrena na subpiksel - sicer ojacana napaka pozre celotno prednost.
    if edge_points is not None:
        rim, rim_refine = refine_quad_with_edges(rim, edge_points, cfg)
        bottom_quad, bottom_refine = refine_quad_with_edges(bottom_quad, edge_points, cfg)
        diag["rim_refine"] = rim_refine.get("max_corner_shift_px")
        diag["bottom_refine"] = bottom_refine.get("max_corner_shift_px")

    rim_w = cfg.get("box.rim_w_mm", None)
    rim_h = cfg.get("box.rim_h_mm", None)
    rim_dims = ((float(rim_w), float(rim_h)) if rim_w and rim_h
                else (w_mm + 2.0 * wall_t, h_mm + 2.0 * wall_t))
    diag["rim_dims_mm"] = list(rim_dims)
    s_bottom = _plane_scale_of_quad(bottom_quad, (w_mm, h_mm), cfg)
    s_rim = _plane_scale_of_quad(rim, rim_dims, cfg)
    diag["scale_bottom_px_per_mm"] = s_bottom
    diag["scale_rim_px_per_mm"] = s_rim
    if not s_bottom or not s_rim or s_rim <= s_bottom:
        diag["reason"] = ("merilo zgornjega roba ni vecje od merila dna - rob ni bil "
                          "pravilno prepoznan")
        return None, diag
    f = float(wall_h) * s_bottom * s_rim / (s_rim - s_bottom)
    if not (float(cfg["autocalib.vanishing.min_f_px"]) <= f
            <= float(cfg["autocalib.vanishing.max_f_px"])):
        diag["reason"] = f"f={f:.0f} px izven dovoljenega obsega"
        return None, diag
    diag["f_px"] = f
    # Obcutljivost: relativna napaka f je priblizno Z/h krat relativna napaka
    # razmerja meril, zato pri nizki steni ocena hitro razpade.
    diag["depth_over_wall_height"] = float((f / s_bottom) / float(wall_h))

    # Neodvisno preverjanje, da je najdeni pravokotnik res zgornji rob: dno in rob
    # sta soosna in vzporedna. Napacen kandidat (npr. notranji rob stene ali
    # ponesreceni fit) to takoj prekrsi, ocena f pa je takrat lahko povsem mimo.
    valid, check = _rim_geometry_valid(bottom_quad, rim, rim_dims, f, principal, cfg)
    diag.update(check)
    if not valid:
        diag["reason"] = ("najdeni pravokotnik ni soosen in vzporeden z dnom - "
                          "najbrz ni zgornji rob zaboja")
        return None, diag
    return f, diag


def _rim_geometry_valid(bottom_quad: np.ndarray, rim_quad: np.ndarray,
                        rim_dims: Tuple[float, float], f: float,
                        principal: Tuple[float, float], cfg: Config
                        ) -> Tuple[bool, dict]:
    """Ali sta rekonstruirani ravnini dna in roba vzporedni in soosni."""
    check: dict = {}
    k_mat = k_from_f(f, principal)
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])
    poses = []
    for quad, dims in ((bottom_quad, (w_mm, h_mm)), (rim_quad, rim_dims)):
        quad_o, obj = box_frame_points(quad, cfg, dims)
        h_mat, _ = cv2.findHomography(obj.astype(np.float32), quad_o.astype(np.float32), 0)
        if h_mat is None:
            return False, {"rim_check": "homografije ni bilo mogoce izracunati"}
        rot, tvec = decompose_plane_homography(h_mat, k_mat)
        poses.append((rot, tvec, obj))
    (rot_b, t_b, obj_b), (rot_r, t_r, obj_r) = poses

    angle = math.degrees(math.acos(float(np.clip(abs(rot_b[:, 2] @ rot_r[:, 2]), -1.0, 1.0))))
    centre_b = rot_b @ np.array([obj_b[:, 0].mean(), obj_b[:, 1].mean(), 0.0]) + t_b
    centre_r = rot_r @ np.array([obj_r[:, 0].mean(), obj_r[:, 1].mean(), 0.0]) + t_r
    normal = rot_b[:, 2] / np.linalg.norm(rot_b[:, 2])
    delta = centre_r - centre_b
    lateral = float(np.linalg.norm(delta - normal * float(delta @ normal)))
    check["rim_plane_angle_deg"] = round(angle, 3)
    check["rim_lateral_offset_mm"] = round(lateral, 2)
    ok = (angle <= float(cfg["box.detect.rim_max_plane_angle_deg"])
          and lateral <= float(cfg["box.detect.rim_max_lateral_offset_mm"]))
    return ok, check


def _rim_reference_frame(bottom_quad: Optional[np.ndarray], candidates: Optional[List[np.ndarray]],
                         cfg: Config):
    """Vrne (quad roba, mm koordinate roba, premik izhodisca na dno) ali None."""
    diag: dict = {}
    wall_h = cfg.get("box.wall_height_mm", None)
    if not wall_h:
        diag["reason"] = "box.wall_height_mm ni podan"
        return None, diag
    wall_t = float(cfg.get("box.wall_thickness_mm", 0.0) or 0.0)
    rim_w, rim_h = cfg.get("box.rim_w_mm", None), cfg.get("box.rim_h_mm", None)
    if rim_w and rim_h:
        dims = (float(rim_w), float(rim_h))
        offset = 0.5 * (float(dims[0]) - float(cfg["box.w_mm"]))
        offset_y = 0.5 * (float(dims[1]) - float(cfg["box.h_mm"]))
    else:
        dims = (float(cfg["box.w_mm"]) + 2.0 * wall_t, float(cfg["box.h_mm"]) + 2.0 * wall_t)
        offset = offset_y = wall_t
    pool = list(candidates or [])
    if bottom_quad is not None:
        pool.append(bottom_quad)
    if not pool:
        diag["reason"] = "ni kandidatnih pravokotnikov"
        return None, diag
    rim = max(pool, key=lambda q: float(cv2.contourArea(q.astype(np.float32))))
    quad_o, obj = box_frame_points(rim, cfg, dims)
    diag["rim_dims_mm"] = list(dims)
    diag["origin_shift_mm"] = [offset, offset_y, -float(wall_h)]
    return (quad_o, obj, (offset, offset_y, -float(wall_h))), diag


def _quad_area(quad: np.ndarray) -> float:
    return float(cv2.contourArea(np.asarray(quad, dtype=np.float32)))


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
              edge_points: Optional[np.ndarray] = None,
              raw_gray: Optional[np.ndarray] = None) -> Calibration:
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

    if str(cfg.get("box.reference_plane", "auto")) == "none":
        # Zaboj se namenoma ne uporablja. Smiselno pri koritastih zabojih s
        # posevnimi stenami, kjer noben viden pravokotnik ni ravnina dna:
        # lazen okvir tam popaci naklon in f_px, relativno rangiranje pa ostane
        # pravilno. Naklon se takrat meri glede na opticno os.
        diag["box_detect"] = {"source": "izklopljeno (box.reference_plane: none)"}
        f_prior = cfg.get("camera.f_px_prior", None)
        f_used = float(f_prior) if f_prior else float(cfg["autocalib.fallback_f_px"])
        if not f_prior:
            warnings.append("zaboj se namenoma ne uporablja in f_px ni podan - koordinate "
                            "niso v milimetrih, uporabno je relativno rangiranje")
        calib = Calibration(k_mat=k_from_f(f_used, principal), f_px=f_used,
                            principal_point=principal,
                            method="camera_frame_only" if f_prior else "degraded_relative_only",
                            confidence=0.0, frame_reliable=False,
                            f_confidence=0.6 if f_prior else 0.0,
                            diagnostics=diag, warnings=warnings)
        return calib

    quad, quad_diag = detect_box_quad(gray, cfg, raw_gray=raw_gray)
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

    f_rim: Optional[float] = None
    if quad is not None and quad_candidates:
        f_rim, rim_diag = f_from_box_rim(quad, quad_candidates, cfg, principal, edge_points)
        diag["box_rim"] = rim_diag

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
    elif f_rim is not None:
        f_px, method, f_confidence = f_rim, "box_rim_two_planes", 0.8
    elif f_wd is not None:
        f_px, method, f_confidence = f_wd, "working_distance_prior", 0.75
    elif f_refined is not None:
        f_px, method, f_confidence = float(f_refined), \
            "scene_refine_" + str(cfg["autocalib.refine.method"]), 0.6
    elif f_vp is not None:
        f_px, method = float(f_vp), "box_vanishing_points"
        # blizje kot sta izginjajoci tocki, mocnejsa je perspektiva in ocena
        f_confidence = 0.6 if vp_ratio is None else float(np.clip(6.0 / max(vp_ratio, 1e-6), 0.1, 0.8))

    if f_vp is not None and f_rim is not None:
        rel = abs(f_rim - f_vp) / f_vp
        diag["vp_vs_rim_rel_diff"] = float(rel)
        if rel > float(cfg["autocalib.max_f_disagreement"]):
            warnings.append(f"oceni f_px iz izginjajocih tock in iz roba zaboja se "
                            f"razlikujeta za {rel:.0%}")
            f_confidence *= 0.5
    if f_vp is not None and f_refined is not None:
        rel = abs(f_refined - f_vp) / f_vp
        diag["vp_vs_refine_rel_diff"] = float(rel)
        if rel > float(cfg["autocalib.max_f_disagreement"]):
            warnings.append(f"oceni f_px iz izginjajocih tock in iz scene se razlikujeta za {rel:.0%}")
            f_confidence *= 0.5

    # Poln zaboj: dna ni videti, zgornji rob pa je. Referencna ravnina je takrat
    # rob, koordinatni sistem dna pa iz njega dobimo s premikom za visino stene.
    reference = str(cfg.get("box.reference_plane", "auto"))
    rim_frame = None
    if reference == "rim":
        rim_frame, rim_frame_diag = _rim_reference_frame(quad, quad_candidates, cfg)
        diag["rim_reference"] = rim_frame_diag
        if rim_frame is not None:
            quad, obj, rim_shift = rim_frame
            homography, _ = cv2.findHomography(obj.astype(np.float32), quad.astype(np.float32), 0)
            f_vp, vp_diag = f_from_vanishing_points(quad, principal, cfg)
            diag["vanishing"] = vp_diag
        else:
            warnings.append("zgornjega roba zaboja ni bilo mogoce uporabiti kot referencne "
                            "ravnine: " + str(rim_frame_diag.get("reason", "")))

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
        if rim_frame is not None:
            # Izhodisce prestavimo z roba na dno: v ravnini roba je vogal dna pri
            # (t, t), dno pa lezi za visino stene nizje.
            t_box = rot_box @ np.array(rim_shift) + t_box
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
        # Le sparjeni kandidati: pri nesparjenem `pair.outer` sploh ni obris kosa
        # (lahko je luknja ali obroc sence), zato primerjava z D_out ni smiselna
        # in je preverjanje merila po nepotrebnem zavrnilo dober okvir.
        if not cand.pair.paired:
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
