"""Fit elips z direktno metodo najmanjsih kvadratov (Fitzgibbon / Halir-Flusser)
na subpixel robnih tockah + parjenje notranje in zunanje elipse prirobnice.

Konvencija za konike: simetricna 3x3 matrika A, tako da za homogeno tocko x
velja x^T A x = 0. Iz algebraicnih koeficientov (a,b,c,d,e,f) za
a x^2 + b xy + c y^2 + d x + e y + f = 0 sledi
A = [[a, b/2, d/2], [b/2, c, e/2], [d/2, e/2, f]].
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

from .config import Config


@dataclass
class Ellipse:
    cx: float
    cy: float
    a: float          # velika polos [px]
    b: float          # mala polos [px]
    theta: float      # kot velike polosi [rad]
    rms_px: float = 0.0
    n_points: int = 0
    support_ratio: float = 0.0
    polarity: float = 0.0   # <0: svetlo znotraj (obris kosa), >0: temno znotraj (luknja/senca)
    conic: Optional[np.ndarray] = None
    points: Optional[np.ndarray] = None
    meta: dict = field(default_factory=dict)

    @property
    def axis_ratio(self) -> float:
        return float(self.b / self.a) if self.a > 0 else 0.0

    @property
    def center(self) -> np.ndarray:
        return np.array([self.cx, self.cy], dtype=float)

    @property
    def eccentricity(self) -> float:
        r = self.axis_ratio
        r = min(1.0, max(0.0, r))
        return math.sqrt(max(0.0, 1.0 - r * r))

    def matrix(self) -> np.ndarray:
        if self.conic is None:
            self.conic = conic_from_params(self.cx, self.cy, self.a, self.b, self.theta)
        return self.conic

    def perimeter_points(self, n: int) -> np.ndarray:
        t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        ct, st = math.cos(self.theta), math.sin(self.theta)
        x = self.a * np.cos(t)
        y = self.b * np.sin(t)
        return np.stack([self.cx + ct * x - st * y, self.cy + st * x + ct * y], axis=1)

    def outward_normals(self, n: int) -> np.ndarray:
        """Enotske zunanje normale vzdolz oboda (isti vzorec kot perimeter_points)."""
        t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        ct, st = math.cos(self.theta), math.sin(self.theta)
        nx = self.b * np.cos(t)
        ny = self.a * np.sin(t)
        vec = np.stack([ct * nx - st * ny, st * nx + ct * ny], axis=1)
        norm = np.linalg.norm(vec, axis=1, keepdims=True)
        return vec / np.where(norm < 1e-12, 1.0, norm)

    def to_dict(self) -> dict:
        return {
            "cx": self.cx, "cy": self.cy, "a": self.a, "b": self.b,
            "theta_deg": math.degrees(self.theta), "rms_px": self.rms_px,
            "n_points": self.n_points, "support_ratio": self.support_ratio,
            "polarity": self.polarity,
        }


# --------------------------------------------------------------------------
# konika <-> parametri
# --------------------------------------------------------------------------
def conic_from_params(cx: float, cy: float, a: float, b: float, theta: float) -> np.ndarray:
    """Konicna matrika elipse, normirana tako da je ||A||_F = 1."""
    c, s = math.cos(theta), math.sin(theta)
    rot = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
    trans = np.array([[1.0, 0.0, -cx], [0.0, 1.0, -cy], [0.0, 0.0, 1.0]])
    m = rot @ trans
    d = np.diag([1.0 / (a * a), 1.0 / (b * b), -1.0])
    conic = m.T @ d @ m
    return conic / np.linalg.norm(conic)


def params_from_conic(conic: np.ndarray) -> Optional[Ellipse]:
    """Vrne parametre elipse ali None, ce konika ni realna elipsa."""
    conic = np.asarray(conic, dtype=float)
    m = conic[:2, :2]
    det = np.linalg.det(m)
    if not np.isfinite(det) or abs(det) < 1e-14:
        return None
    try:
        center = np.linalg.solve(m, -conic[:2, 2])
    except np.linalg.LinAlgError:
        return None
    if not np.all(np.isfinite(center)):
        return None
    k = float(conic[0, 2] * center[0] + conic[1, 2] * center[1] + conic[2, 2])
    evals, evecs = np.linalg.eigh(m)
    if abs(k) < 1e-18:
        return None
    axes_sq = -k / evals
    if np.any(axes_sq <= 0) or not np.all(np.isfinite(axes_sq)):
        return None
    axes = np.sqrt(axes_sq)
    order = np.argsort(-axes)          # velika polos prva
    a_len, b_len = float(axes[order[0]]), float(axes[order[1]])
    vec = evecs[:, order[0]]
    theta = math.atan2(float(vec[1]), float(vec[0]))
    if theta < 0:
        theta += math.pi
    return Ellipse(cx=float(center[0]), cy=float(center[1]), a=a_len, b=b_len,
                   theta=theta, conic=conic / np.linalg.norm(conic))


def sampson_residuals(conic: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Priblizek geometrijske razdalje tock do konike [px]."""
    pts = np.asarray(points, dtype=float)
    hom = np.concatenate([pts, np.ones((len(pts), 1))], axis=1)
    val = np.einsum("ij,jk,ik->i", hom, conic, hom)
    grad = 2.0 * hom @ conic.T
    denom = np.linalg.norm(grad[:, :2], axis=1)
    denom = np.where(denom < 1e-12, 1e-12, denom)
    return np.abs(val) / denom


# --------------------------------------------------------------------------
# direktni fit (Halir-Flusser, numericno stabilna razlicica Fitzgibbona)
# --------------------------------------------------------------------------
def fit_ellipse_direct(points: np.ndarray) -> Optional[Ellipse]:
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 6:
        return None
    mean = pts.mean(axis=0)
    scale = float(np.sqrt((((pts - mean) ** 2).sum(axis=1)).mean()))
    if not np.isfinite(scale) or scale < 1e-9:
        return None
    norm = (pts - mean) / scale
    x, y = norm[:, 0], norm[:, 1]

    d1 = np.stack([x * x, x * y, y * y], axis=1)
    d2 = np.stack([x, y, np.ones_like(x)], axis=1)
    s1 = d1.T @ d1
    s2 = d1.T @ d2
    s3 = d2.T @ d2
    try:
        t = -np.linalg.solve(s3, s2.T)
    except np.linalg.LinAlgError:
        return None
    m = s1 + s2 @ t
    c1_inv = np.array([[0.0, 0.0, 0.5], [0.0, -1.0, 0.0], [0.5, 0.0, 0.0]])
    m = c1_inv @ m
    try:
        evals, evecs = np.linalg.eig(m)
    except np.linalg.LinAlgError:
        return None
    cond = 4.0 * evecs[0, :] * evecs[2, :] - evecs[1, :] ** 2
    idx = np.where((cond > 0) & np.isfinite(cond))[0]
    if len(idx) == 0:
        return None
    a1 = np.real(evecs[:, idx[0]])
    a2 = t @ a1
    coeffs = np.concatenate([a1, a2])           # a,b,c,d,e,f v normiranih koordinatah
    a_, b_, c_, d_, e_, f_ = [float(v) for v in coeffs]
    conic_n = np.array([[a_, b_ / 2.0, d_ / 2.0],
                        [b_ / 2.0, c_, e_ / 2.0],
                        [d_ / 2.0, e_ / 2.0, f_]])
    # razveljavi normalizacijo: x_n = (x - mean)/scale  =>  N = [[1/s,0,-mx/s],...]
    n_mat = np.array([[1.0 / scale, 0.0, -mean[0] / scale],
                      [0.0, 1.0 / scale, -mean[1] / scale],
                      [0.0, 0.0, 1.0]])
    conic = n_mat.T @ conic_n @ n_mat
    if not np.all(np.isfinite(conic)):
        return None
    conic = conic / np.linalg.norm(conic)
    ell = params_from_conic(conic)
    if ell is None:
        return None
    res = sampson_residuals(conic, pts)
    ell.rms_px = float(np.sqrt(np.mean(res ** 2)))
    ell.n_points = int(len(pts))
    ell.points = pts
    return ell


# --------------------------------------------------------------------------
# kontura -> kandidatne elipse
# --------------------------------------------------------------------------
def _acceptable(ell: Ellipse, cfg: Config) -> bool:
    if ell is None:
        return False
    if not np.isfinite([ell.cx, ell.cy, ell.a, ell.b]).all():
        return False
    if ell.a < cfg["ellipse.min_semi_major_px"] or ell.a > cfg["ellipse.max_semi_major_px"]:
        return False
    if ell.axis_ratio < cfg["ellipse.min_axis_ratio"]:
        return False
    return True


def fit_contour(points: np.ndarray, cfg: Config, depth: int = 0) -> List[Ellipse]:
    """Fita konturo; ce je residual previsok, jo rekurzivno razpolovi.

    Prekrivajoce prirobnice dajo konture, ki so unija vec lokov - delitev
    poskrbi, da tak lok se vedno rodi uporabno elipso.
    """
    min_pts = int(cfg["ellipse.min_points"])
    if len(points) < min_pts:
        return []
    ell = fit_ellipse_direct(points)
    max_rms = float(cfg["ellipse.max_rms_px"])
    if ell is not None and _acceptable(ell, cfg) and ell.rms_px <= max_rms:
        return [ell]
    if depth >= int(cfg["ellipse.max_split_depth"]) or len(points) < 2 * min_pts:
        return [ell] if (ell is not None and _acceptable(ell, cfg)) else []
    half = len(points) // 2
    out = fit_contour(points[:half], cfg, depth + 1)
    out += fit_contour(points[half:], cfg, depth + 1)
    return out


def detect_ellipses_edge_drawing(gray: np.ndarray, cfg: Config) -> Tuple[List[Ellipse], dict]:
    """Kandidatne elipse z EdgeDrawing (OpenCV contrib), po vzoru ELSD/Fornaciari.

    Namesto "vsaka kontura -> fit -> razpolovi" ta detektor gradi robne verige po
    ujemanju smeri gradienta, jih razbije na loke in loke iste elipse zdruzi.
    Ravno to manjka mojemu pristopu, kadar je obris kosa razbit na vec kratkih
    lokov - izmerjeno na resnicni fotografiji: 30 elips prave velikosti proti 11.

    Vrne kandidate; o tem, kateri so kosi, odlocajo sele polariteta, parjenje z
    luknjo in mera vidnosti.
    """
    diag: dict = {"available": hasattr(cv2, "ximgproc")}
    if not diag["available"]:
        diag["reason"] = "cv2.ximgproc ni na voljo (namesti opencv-contrib-python-headless)"
        return [], diag
    try:
        detector = cv2.ximgproc.createEdgeDrawing()
        params = cv2.ximgproc.EdgeDrawing.Params()
        params.PFmode = bool(cfg["ellipse.edge_drawing.pf_mode"])
        params.GradientThresholdValue = int(cfg["ellipse.edge_drawing.gradient_threshold"])
        params.AnchorThresholdValue = int(cfg["ellipse.edge_drawing.anchor_threshold"])
        params.MinPathLength = int(cfg["ellipse.edge_drawing.min_path_length"])
        params.NFAValidation = bool(cfg["ellipse.edge_drawing.nfa_validation"])
        params.Sigma = float(cfg["ellipse.edge_drawing.sigma"])
        detector.setParams(params)
        detector.detectEdges(gray)
        found = detector.detectEllipses()
    except cv2.error as exc:
        diag["reason"] = f"EdgeDrawing je odpovedal: {exc}"
        return [], diag
    if found is None:
        diag["n_found"] = 0
        return [], diag
    found = np.asarray(found, dtype=float).reshape(-1, 6)
    diag["n_found"] = int(len(found))
    out: List[Ellipse] = []
    for row in found:
        # Zapis OpenCV: krog ima polmer v row[2], elipsa pa polosi v row[3:5];
        # sestevek pokrije oba primera.
        axis_a = float(row[2] + row[3])
        axis_b = float(row[2] + row[4])
        if axis_a <= 0 or axis_b <= 0:
            continue
        major, minor = max(axis_a, axis_b), min(axis_a, axis_b)
        theta = math.radians(float(row[5]))
        if axis_b > axis_a:
            theta += math.pi / 2.0
        ell = Ellipse(cx=float(row[0]), cy=float(row[1]), a=major, b=minor,
                      theta=theta % math.pi, meta={"source": "edge_drawing"})
        if _acceptable(ell, cfg):
            out.append(ell)
    diag["n_accepted"] = len(out)
    return out, diag


def deduplicate(ellipses: Sequence[Ellipse], cfg: Config) -> List[Ellipse]:
    """Zdruzi skoraj enake fite (npr. notranja in zunanja stran istega roba)."""
    center_tol = float(cfg["ellipse.duplicate_center_px"])
    axis_tol = float(cfg["ellipse.duplicate_axis_ratio"])
    kept: List[Ellipse] = []
    for ell in sorted(ellipses, key=lambda e: (-e.n_points, e.rms_px)):
        dup = False
        for other in kept:
            if np.linalg.norm(ell.center - other.center) > center_tol:
                continue
            if abs(ell.a - other.a) > axis_tol * max(ell.a, other.a):
                continue
            if abs(ell.b - other.b) > axis_tol * max(ell.b, other.b) + center_tol:
                continue
            dup = True
            break
        if not dup:
            kept.append(ell)
    return kept


def compute_support(ellipses: Sequence[Ellipse], edge_points: np.ndarray, cfg: Config,
                    n_samples: int = 180) -> None:
    """Delez oboda elipse, dejansko podprt z detektiranimi robnimi tockami.

    To je hkrati occlusion metrika (occlusion_ratio = support_ratio).
    """
    from scipy.spatial import cKDTree

    if edge_points is None or len(edge_points) == 0:
        for ell in ellipses:
            ell.support_ratio = 0.0
        return
    tree = cKDTree(np.asarray(edge_points, dtype=float))
    tol = float(cfg["edges.subpixel_max_shift_px"]) + 1.5
    for ell in ellipses:
        samples = ell.perimeter_points(n_samples)
        dist, _ = tree.query(samples, k=1)
        ell.support_ratio = float(np.mean(dist <= tol))


def compute_support_gradient(ellipses: Sequence[Ellipse], gx: Optional[np.ndarray],
                             gy: Optional[np.ndarray], cfg: Config,
                             n_samples: int = 180) -> None:
    """Podprtost obrisa iz gradienta slike neposredno, brez robnih tock.

    Vzdolz oboda vzorcimo gradient in stejemo delez tock, kjer ta kaze navznoter
    z zadostno jakostjo (svetlo znotraj, temno zunaj). Kjer kos prekriva drug
    kos, tega skoka ni in tocka ne steje.

    Izmerjeno proti resnicni vidnosti na gostih sinteticnih scenah z vzorckom na
    povrsini (210 kosov): korelacija 0.992 proti 0.935 pri prejsnji meri, ki je
    stela zgolj blizino robnih tock. Ta je pri perforiranih kosih zavedena, ker
    robne tocke lezijo povsod po povrsini.
    """
    if gx is None or gy is None:
        for ell in ellipses:
            ell.support_ratio = 0.0
        return
    mag = np.hypot(gx, gy)
    pct = float(cfg["ellipse.support_scale_percentile"])
    strong = mag[mag > np.percentile(mag, pct)]
    global_scale = float(np.median(strong)) if strong.size else 1.0
    factor = float(cfg["ellipse.support_gradient_factor"])
    local = bool(cfg["ellipse.support_local_scale"])
    floor = float(cfg["ellipse.support_gradient_floor"])
    h, w = gx.shape[:2]
    for ell in ellipses:
        if local:
            # Merilo kontrasta iz OKOLICE kosa, ne iz cele slike. Enakomerno a
            # slabse osvetljen kos ima sibkejsi gradient povsod; z globalnim
            # merilom bi bil videti prekrit, ceprav je popolnoma viden.
            x0 = max(0, int(ell.cx - 1.3 * ell.a)); x1 = min(w, int(ell.cx + 1.3 * ell.a) + 1)
            y0 = max(0, int(ell.cy - 1.3 * ell.a)); y1 = min(h, int(ell.cy + 1.3 * ell.a) + 1)
            patch = mag[y0:y1, x0:x1]
            scale = (float(np.percentile(patch, pct)) if patch.size > 16 else global_scale)
        else:
            scale = global_scale
        # Spodnja meja iz kvantizacije (LSD: rho = q / sin(tau)) prepreci, da bi
        # se v ravnem, brezsumnem obmocju za rob steli sami zaokrozitveni ostanki.
        threshold = max(factor * scale, floor)
        pts = ell.perimeter_points(n_samples)
        nrm = ell.outward_normals(n_samples)
        # Rob iscemo v ozkem pasu vzdolz normale: fit elipse ni popoln in vzorec
        # tocno na njej lahko zgresi rob za piksel ali dva.
        band = float(cfg["ellipse.support_search_band_px"])
        radial = None
        offsets = np.arange(-band, band + 0.5, 1.0) if band > 0 else np.array([0.0])
        for offset in offsets:
            q = pts + nrm * offset
            xq = np.clip(np.round(q[:, 0]).astype(int), 0, w - 1)
            yq = np.clip(np.round(q[:, 1]).astype(int), 0, h - 1)
            r = gx[yq, xq] * nrm[:, 0] + gy[yq, xq] * nrm[:, 1]
            radial = r if radial is None else np.where(np.abs(r) > np.abs(radial), r, radial)
        inside_image = ((pts[:, 0] >= 0) & (pts[:, 0] < w)
                        & (pts[:, 1] >= 0) & (pts[:, 1] < h))
        # Predznak vzamemo iz same elipse: obris kosa je svetel znotraj
        # (radialni gradient negativen), luknja pa temna znotraj (pozitiven).
        # Brez tega bi mera zavrgla vse luknje in s tem podrla parjenje.
        sign = -1.0 if float(np.median(radial)) < 0 else 1.0
        ell.support_ratio = float(np.mean(inside_image & (radial * sign > threshold)))


def compute_polarity(ellipses: Sequence[Ellipse], gx: Optional[np.ndarray],
                     gy: Optional[np.ndarray], cfg: Config, n_samples: int = 180) -> None:
    """Predznacena polariteta roba: v katero smer pada svetlost cez obod.

    Fizikalno: obris kovinskega kosa je svetel znotraj in temen zunaj
    (polarity < 0), luknja in vrzena senca pa temna znotraj (polarity > 0).
    To loci pravo prirobnico od kolobarja sence okoli nje - loceva, ki je z
    velikostjo elipse ni mogoce dobiti, saj je kos visje v kupu videti vecji.
    """
    if gx is None or gy is None:
        for ell in ellipses:
            ell.polarity = 0.0
        return
    h, w = gx.shape[:2]
    for ell in ellipses:
        pts = ell.perimeter_points(n_samples)
        nrm = ell.outward_normals(n_samples)
        xi = np.clip(np.round(pts[:, 0]).astype(int), 0, w - 1)
        yi = np.clip(np.round(pts[:, 1]).astype(int), 0, h - 1)
        grad = np.stack([gx[yi, xi], gy[yi, xi]], axis=1)
        radial = np.einsum("ij,ij->i", grad, nrm)
        scale = float(np.mean(np.linalg.norm(grad, axis=1)))
        ell.polarity = float(np.mean(radial) / scale) if scale > 1e-9 else 0.0


def verify_virtual_hole(pairs: Sequence["EllipsePair"], gx: Optional[np.ndarray],
                        gy: Optional[np.ndarray], cfg: Config) -> None:
    """Za obris brez najdenega para preveri, ali je na mestu luknje sploh rob.

    Prava prirobnica ima luknjo na znanem polmeru (D_in/D_out) in soosno z
    obrisom. Ce fit luknje ni uspel, se rob luknje vseeno MORA videti. Navidezno
    elipso zato zgradimo iz geometrije in na njej izmerimo isto podprtost kot
    sicer: pri pravem kosu je visoka, pri nakljucnem krogu cez kup stakanih kosov
    pa tam ni nicesar. To je parjenje s sintetizirano luknjo - dokaz o kosu tudi
    takrat, ko detektor luknje odpove.
    """
    if gx is None or gy is None:
        return
    ratio = float(cfg["flange.d_in_mm"]) / float(cfg["flange.d_out_mm"])
    if ratio <= 1e-6:
        return
    todo = [p for p in pairs if not p.paired and p.role == "outer"]
    if not todo:
        return
    virtual = [Ellipse(cx=p.outer.cx, cy=p.outer.cy, a=p.outer.a * ratio,
                       b=p.outer.b * ratio, theta=p.outer.theta) for p in todo]
    compute_support_gradient(virtual, gx, gy, cfg)
    compute_polarity(virtual, gx, gy, cfg)
    for pair, ghost in zip(todo, virtual):
        # Predznaka NE zahtevamo. V polnem zaboju luknja ni temna - skoznjo se
        # vidi kos pod njo, ki je enako svetel ali svetlejsi. Izmerjeno na
        # resnicni fotografiji: pravi kos je imel polariteto luknje -0.35, torej
        # ravno nasprotno od pricakovane. Steje samo, da rob NA TEM POLMERU
        # obstaja; mera podprtosti predznak itak vzame iz same elipse.
        pair.virtual_hole_support = float(ghost.support_ratio)
        pair.reasons["virtual_hole"] = {
            "support": round(float(ghost.support_ratio), 3),
            "polarity": round(float(ghost.polarity), 3),
        }


def _sector_excess(hit: np.ndarray, valid: np.ndarray, n_sectors: int,
                   min_sector_frac: float) -> float:
    """Presezek zamasanosti nad najcistejsim izsekom istega kolobarja.

    Kolobar razdelimo na kotne izseke. Prost kos je enakomerno teksturiran, zato
    so vsi izseki podobni in presezek je blizu nic. Kos, cez katerega lezi drug
    kos, ima nekaj izsekov mocno umazanih - povprecje se dvigne, najcistejsi
    izsek pa ostane cist, in razlika to pokaze.
    """
    n_ang = hit.shape[1]
    if n_sectors < 2 or n_ang < n_sectors:
        return float("nan")
    per_sector = []
    bounds = np.linspace(0, n_ang, n_sectors + 1).astype(int)
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        n_valid = int(valid[:, lo:hi].sum())
        if n_valid < min_sector_frac * valid[:, lo:hi].size:
            continue                      # izsek je vecinoma izven slike
        per_sector.append(float(hit[:, lo:hi].sum()) / n_valid)
    if len(per_sector) < 3:
        return float("nan")
    values = np.sort(np.asarray(per_sector))
    # Izhodisce je najcistejsa cetrtina izsekov (ne absolutni minimum - ta je pri
    # majhnem vzorcu sum).
    baseline = float(np.mean(values[:max(1, len(values) // 4)]))
    return float(max(0.0, float(np.mean(values)) - baseline))


def measure_ring_clutter(pairs: Sequence["EllipsePair"], gx: Optional[np.ndarray],
                         gy: Optional[np.ndarray], cfg: Config) -> None:
    """Delez povrsine kolobarja, cez katerega tece tuj rob.

    Mera vidnosti obrisa gleda le OBOD. Kos, ki mu drug kos lezi cez sredino,
    ima lahko obod skoraj cel, a je vseeno neprijemljiv - in ravno taki so se
    prebijali med najbolje ocenjene kandidate. Zato tu vzorcimo POVRSINO
    kolobarja med luknjo in obrisom: gladka kovinska ploskev da sibek gradient,
    rob kosa, ki lezi cez njo, pa mocnega.

    Isto merilo kontrasta kot pri vidnosti (lokalni percentil + spodnja meja iz
    kvantizacije), zato je vrednost primerljiva med svetlimi in temnimi deli
    zaboja.

    Absolutna vrednost pove malo: perforirana povrsina in vijacne luknje dajo
    gradient tudi na povsem prostem kosu (izmerjeno: sinteticna scena s teksturo
    0.31 pri polni vidnosti, resnicna fotografija 0.03-0.05). Merodajen je zato
    PRESEZEK glede na NAJCISTEJSI IZSEK ISTEGA kolobarja (`pair.ring_clutter_excess`):
    prost kos je enakomerno teksturiran, kos s tujim kosom cez sebe pa ima nekaj
    izsekov mocno umazanih. Mera je s tem sama sebi referenca - ne potrebuje ne
    drugih kandidatov v sceni ne poznavanja povrsinske obdelave.
    """
    if gx is None or gy is None:
        return
    mag = np.hypot(gx, gy)
    pct = float(cfg["ellipse.support_scale_percentile"])
    factor = float(cfg["ellipse.ring_clutter_factor"])
    floor = float(cfg["ellipse.support_gradient_floor"])
    n_ang = int(cfg["ellipse.ring_clutter_angular_samples"])
    n_rad = int(cfg["ellipse.ring_clutter_radial_samples"])
    margin = float(cfg["ellipse.ring_clutter_margin"])
    n_sectors = int(cfg["ellipse.ring_clutter_sectors"])
    min_sector_frac = float(cfg["ellipse.ring_clutter_min_sector_fraction"])
    ratio = float(cfg["flange.d_in_mm"]) / float(cfg["flange.d_out_mm"])
    h, w = mag.shape[:2]

    strong = mag[mag > np.percentile(mag, pct)]
    global_scale = float(np.median(strong)) if strong.size else 1.0

    angles = np.linspace(0.0, 2.0 * math.pi, n_ang, endpoint=False)
    # Vzorcimo v NORMIRANIH koordinatah elipse in jih preslikamo z isto afino
    # preslikavo kot obod - tako pas ostane kolobar tudi pri mocnem naklonu.
    fracs = np.linspace(ratio + margin, 1.0 - margin, n_rad)
    for pair in pairs:
        if fracs[0] >= fracs[-1]:
            continue
        ell = pair.outer
        if pair.role == "inner":
            # Vidna je le luknja; obris kosa je znan po geometriji (D_out/D_in),
            # zato kolobar vseeno lahko preverimo - in ravno pri teh kandidatih je
            # to najbolj pomembno, saj obrisa ne vidimo ravno zato, ker je prekrit.
            if ratio <= 1e-6:
                continue
            ell = Ellipse(cx=ell.cx, cy=ell.cy, a=ell.a / ratio, b=ell.b / ratio,
                          theta=ell.theta)
        ct, st = math.cos(ell.theta), math.sin(ell.theta)
        x0 = max(0, int(ell.cx - 1.3 * ell.a)); x1 = min(w, int(ell.cx + 1.3 * ell.a) + 1)
        y0 = max(0, int(ell.cy - 1.3 * ell.a)); y1 = min(h, int(ell.cy + 1.3 * ell.a) + 1)
        patch = mag[y0:y1, x0:x1]
        scale = float(np.percentile(patch, pct)) if patch.size > 16 else global_scale
        threshold = max(factor * scale, floor)
        hit = np.zeros((len(fracs), n_ang), dtype=bool)
        valid = np.zeros((len(fracs), n_ang), dtype=bool)
        for k, frac in enumerate(fracs):
            ex = frac * ell.a * np.cos(angles)
            ey = frac * ell.b * np.sin(angles)
            px = ell.cx + ct * ex - st * ey
            py = ell.cy + st * ex + ct * ey
            inside = (px >= 0) & (px < w) & (py >= 0) & (py < h)
            xi = np.clip(np.round(px).astype(int), 0, w - 1)
            yi = np.clip(np.round(py).astype(int), 0, h - 1)
            valid[k] = inside
            hit[k] = inside & (mag[yi, xi] > threshold)
        total = int(valid.sum())
        pair.ring_clutter = float(hit.sum() / total) if total else float("nan")
        pair.ring_clutter_excess = _sector_excess(hit, valid, n_sectors, min_sector_frac)


def classify_role(ell: Ellipse, cfg: Config) -> Optional[str]:
    """'outer' (obris kosa), 'inner' (luknja) ali None, ce polariteta ni jasna."""
    thr = float(cfg["ellipse.polarity_threshold"])
    if ell.polarity <= -thr:
        return "outer"
    if ell.polarity >= thr:
        return "inner"
    return None


# --------------------------------------------------------------------------
# parjenje notranje in zunanje elipse
# --------------------------------------------------------------------------
@dataclass
class EllipsePair:
    outer: Ellipse
    inner: Optional[Ellipse]
    score: float
    reasons: dict = field(default_factory=dict)
    role: str = "outer"      # kaj predstavlja `outer`: 'outer' obris ali 'inner' luknja
    ring_clutter: float = float("nan")          # delez kolobarja s tujim robom cez njega
    ring_clutter_excess: float = float("nan")   # presezek nad najcistejsim izsekom istega kolobarja
    virtual_hole_support: float = float("nan")  # podprtost roba luknje, kadar para ni

    @property
    def paired(self) -> bool:
        return self.inner is not None


def estimate_edge_bias(pairs: Sequence["EllipsePair"], cfg: Config) -> Tuple[float, dict]:
    """Oceni sistematicni odmik lege roba [px] iz znanega razmerja premerov.

    Detekcija roba ima majhen sistematicni odmik (senca ob robu, kontrast,
    zaokrozitev roba kosa). Ker sta ZNANA oba premera, je ta odmik opazljiv:
    ce sta izmerjeni polosi a_out in a_in obe prevelike za d, potem njuno
    razmerje ni vec D_out/D_in. Iz

        (a_out - d) / (a_in - d) = R,   R = D_out / D_in

    sledi d = (R * a_in - a_out) / (R - 1).

    Odmik d se nato odsteje obema elipsama. Brez tega se prenese naravnost v
    oceno Z: 0.13 px pri polosi 35 px pomeni 0.4 % globine, kar je pri 700 mm
    ze 2.6 mm.
    """
    diag: dict = {"n_used": 0}
    if not bool(cfg["ellipse.estimate_edge_bias"]):
        diag["reason"] = "izklopljeno v configu"
        return 0.0, diag
    ratio = float(cfg["flange.d_out_mm"]) / float(cfg["flange.d_in_mm"])
    if abs(ratio - 1.0) < 1e-6:
        diag["reason"] = "premera sta enaka - odmika ni mogoce oceniti"
        return 0.0, diag
    estimates = []
    for pair in pairs:
        if pair.inner is None or pair.role != "outer":
            continue
        for a_out, a_in in ((pair.outer.a, pair.inner.a), (pair.outer.b, pair.inner.b)):
            if a_in <= 0 or a_out <= 0:
                continue
            estimates.append((ratio * a_in - a_out) / (ratio - 1.0))
    diag["n_used"] = len(estimates)
    if len(estimates) < int(cfg["ellipse.edge_bias_min_samples"]):
        diag["reason"] = "premalo parov za oceno odmika"
        return 0.0, diag
    bias = float(np.median(estimates))
    limit = float(cfg["ellipse.edge_bias_max_px"])
    spread = float(np.percentile(np.abs(np.array(estimates) - bias), 68))
    diag["raw_px"] = round(bias, 4)
    diag["spread_px"] = round(spread, 4)
    if abs(bias) > limit:
        diag["reason"] = f"ocenjeni odmik {bias:.2f} px presega mejo {limit} px - zavrnjeno"
        return 0.0, diag
    # Sumna ocena je slabsa od nobene: napacno skrcenje majhne notranje elipse
    # razbije ujemanje para in s tem pozo. Popravek zato zahteva, da je ocena
    # tudi natancna, ne le majhna.
    if spread > float(cfg["ellipse.edge_bias_max_spread_px"]):
        diag["reason"] = (f"razpsenost ocene {spread:.3f} px je prevelika - popravek bi bil "
                          "ugibanje")
        return 0.0, diag
    return bias, diag


def apply_edge_bias(ellipses: Sequence[Ellipse], bias_px: float) -> None:
    """Skrci vsako elipso za ocenjeni odmik roba (in razveljavi predpomnjeno koniko)."""
    if abs(bias_px) < 1e-9:
        return
    for ell in ellipses:
        new_a = ell.a - bias_px
        new_b = ell.b - bias_px
        if new_a <= 1e-6 or new_b <= 1e-6:
            continue
        ell.a, ell.b = new_a, new_b
        ell.conic = None


def pair_ellipses(ellipses: Sequence[Ellipse], cfg: Config) -> Tuple[List[EllipsePair], List[dict]]:
    """Poveze vsako notranjo elipso z zunanjo istega kosa.

    Par je mocen dokaz o pravi prirobnici; samostojna elipsa preostane kot
    sibek kandidat z nizko confidence (nikoli tiho ne izpade).
    """
    d_out = float(cfg["flange.d_out_mm"])
    d_in = float(cfg["flange.d_in_mm"])
    target_ratio = d_in / d_out
    max_off = float(cfg["ellipse.pairing.max_center_offset_ratio"])
    size_tol = float(cfg["ellipse.pairing.size_ratio_tolerance"])
    axis_tol = float(cfg["ellipse.pairing.axis_ratio_tolerance"])
    angle_tol = math.radians(float(cfg["ellipse.pairing.angle_tolerance_deg"]))
    ecc_min = float(cfg["ellipse.pairing.angle_check_min_eccentricity"])

    rejected: List[dict] = []
    roles = [classify_role(e, cfg) for e in ellipses]
    cands: List[Tuple[float, int, int]] = []
    for i, outer in enumerate(ellipses):
        if roles[i] == "inner":            # temno znotraj => ne more biti obris kosa
            continue
        for j, inner in enumerate(ellipses):
            if i == j or inner.a >= outer.a or roles[j] == "outer":
                continue
            off = float(np.linalg.norm(outer.center - inner.center)) / outer.a
            ratio = inner.a / outer.a
            size_err = abs(ratio - target_ratio) / target_ratio
            # Zavrnitve se belezijo - brez tega je pri gostih scenah nemogoce
            # ugotoviti, zakaj parjenje odpove.
            if off > max_off:
                rejected.append({"outer": i, "inner": j, "reason": "sredisci sta preveč narazen",
                                 "offset_ratio": round(off, 3)})
                continue
            if size_err > size_tol:
                rejected.append({"outer": i, "inner": j, "reason": "neujemanje velikosti",
                                 "size_ratio": round(ratio, 3), "target": round(target_ratio, 3)})
                continue
            axis_err = abs(inner.axis_ratio - outer.axis_ratio)
            if axis_err > axis_tol:
                rejected.append({"outer": i, "inner": j, "reason": "neujemanje sploscenosti",
                                 "axis_err": round(axis_err, 3)})
                continue
            if min(outer.eccentricity, inner.eccentricity) > ecc_min:
                d_ang = abs(outer.theta - inner.theta) % math.pi
                d_ang = min(d_ang, math.pi - d_ang)
                if d_ang > angle_tol:
                    rejected.append({"outer": i, "inner": j, "reason": "neujemanje orientacije",
                                     "angle_deg": round(math.degrees(d_ang), 2)})
                    continue
            quality = (1.0 - off / max_off) + (1.0 - size_err / size_tol) + (1.0 - axis_err / axis_tol)
            cands.append((quality / 3.0, i, j))

    cands.sort(key=lambda c: -c[0])
    used_outer, used_inner = set(), set()
    pairs: List[EllipsePair] = []
    for quality, i, j in cands:
        if i in used_outer or j in used_inner or i in used_inner or j in used_outer:
            continue
        used_outer.add(i)
        used_inner.add(j)
        pairs.append(EllipsePair(outer=ellipses[i], inner=ellipses[j], score=float(quality)))
    for k, ell in enumerate(ellipses):
        if k in used_outer or k in used_inner:
            continue
        if roles[k] == "inner":
            # Sama luknja brez obrisa: kos je tam, a njegovega oboda ne vidimo.
            pairs.append(EllipsePair(outer=ell, inner=None, score=0.0, role="inner",
                                     reasons={"unpaired": "sama luknja brez vidnega obrisa"}))
        else:
            pairs.append(EllipsePair(outer=ell, inner=None, score=0.0, role="outer",
                                     reasons={"unpaired": "brez ujemajoce druge elipse",
                                              "polarity_role": roles[k] or "nedolocena"}))
    return pairs, rejected
