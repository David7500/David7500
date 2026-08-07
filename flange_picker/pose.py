"""Monokularna ocena poze iz projekcije kroga znanega premera.

Izpeljava (v lastnem sistemu stozca):
  Elipsa v sliki doloca stozec X^T Q X = 0 v kamerinem sistemu, Q = K^T A K.
  Q razcepimo na lastne vrednosti in jih uredimo tako, da velja
  l1 >= l2 > 0 > l3. Ravnina, ki stozec preseka v krogu, ima normalo v ravnini
  lastnih vektorjev v1, v3:

      n = (s_n * h, 0, g),   h = sqrt((l1-l2)/(l1-l3)),  g = sqrt((l2-l3)/(l1-l3))

  Sredisce kroga polmera r na tej ravnini je

      C = s_d * r * (-s_n * h * sqrt(|l3|/l1), 0, g * sqrt(l1/|l3|))

  s_n = +-1 da dve fizikalno razlicni resitvi (klasicna dvoumnost), s_d = +-1 pa
  izbere resitev pred kamero. Za h = 0 (l1 = l2) sta resitvi enaki.

Dvoumnost razresimo z zahtevo, da se pozi notranje in zunanje elipse ujemata.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .config import Config
from .ellipse import Ellipse, EllipsePair


@dataclass
class CirclePose:
    normal: np.ndarray      # enotska normala v kamerinem sistemu (proti kameri)
    center: np.ndarray      # sredisce kroga v kamerinem sistemu [mm]

    @property
    def depth(self) -> float:
        return float(self.center[2])


@dataclass
class FlangePose:
    center_cam: np.ndarray
    normal_cam: np.ndarray
    center_box: Optional[np.ndarray] = None
    normal_box: Optional[np.ndarray] = None
    tilt_deg: float = 0.0
    azimuth_deg: float = 0.0
    pair_normal_angle_deg: float = 0.0
    pair_center_ratio: float = 0.0
    confidence: float = 0.0
    paired: bool = False
    orientation_ambiguous: bool = False   # smeri nagiba (azimuta) ni mogoce zanesljivo dolociti
    reasons: List[str] = field(default_factory=list)


def circle_pose_solutions(conic_px: np.ndarray, k_mat: np.ndarray, radius_mm: float
                          ) -> List[CirclePose]:
    """Obe resitvi poze kroga polmera radius_mm, ki se projicira v dano koniko."""
    q = k_mat.T @ np.asarray(conic_px, dtype=float) @ k_mat
    q = 0.5 * (q + q.T)
    if not np.all(np.isfinite(q)):
        return []
    evals, evecs = np.linalg.eigh(q)
    if np.count_nonzero(evals > 0) == 1:      # zelimo dve pozitivni, eno negativno
        evals, q = -evals, -q
    if np.count_nonzero(evals > 0) != 2:
        return []
    order = np.argsort(-evals)                # l1 >= l2 > 0 > l3
    evals = evals[order]
    evecs = evecs[:, order]
    l1, l2, l3 = (float(v) for v in evals)
    if not (l1 >= l2 > 0.0 > l3):
        return []
    denom = l1 - l3
    if denom <= 0:
        return []
    h = math.sqrt(max(0.0, (l1 - l2) / denom))
    g = math.sqrt(max(0.0, (l2 - l3) / denom))
    ca = math.sqrt(abs(l3) / l1)
    cb = math.sqrt(l1 / abs(l3))

    out: List[CirclePose] = []
    seen: List[np.ndarray] = []
    for s_n in (1.0, -1.0):
        n_eig = np.array([s_n * h, 0.0, g])
        for s_d in (1.0, -1.0):
            c_eig = s_d * radius_mm * np.array([-s_n * h * ca, 0.0, g * cb])
            center = evecs @ c_eig
            if center[2] <= 0:                # krog mora biti pred kamero
                continue
            normal = evecs @ n_eig
            nrm = np.linalg.norm(normal)
            if nrm < 1e-12:
                continue
            normal = normal / nrm
            if float(normal @ center) > 0:    # normala naj gleda proti kameri
                normal = -normal
            if any(np.linalg.norm(center - s.center) < 1e-6 and
                   np.linalg.norm(normal - s.normal) < 1e-6 for s in out):
                continue
            out.append(CirclePose(normal=normal, center=center))
        seen.append(n_eig)
        if h < 1e-9:                          # degeneriran primer: ena sama resitev
            break
    return out


def project_circle_to_conic(center_cam: np.ndarray, normal_cam: np.ndarray,
                            radius_mm: float, k_mat: np.ndarray) -> np.ndarray:
    """Konika (v pikslih) projekcije kroga - inverz zgornje operacije.

    Uporabljena v sintezi in testih.
    """
    normal = np.asarray(normal_cam, dtype=float)
    normal = normal / np.linalg.norm(normal)
    helper = np.array([1.0, 0.0, 0.0]) if abs(normal[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(normal, helper)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    h_mat = k_mat @ np.column_stack([u, v, np.asarray(center_cam, dtype=float)])
    h_inv = np.linalg.inv(h_mat)
    circle = np.diag([1.0, 1.0, -radius_mm * radius_mm])
    conic = h_inv.T @ circle @ h_inv
    return conic / np.linalg.norm(conic)


def circle_points_3d(center_cam: np.ndarray, normal_cam: np.ndarray, radius_mm: float,
                     n: int = 128) -> np.ndarray:
    normal = np.asarray(normal_cam, dtype=float)
    normal = normal / np.linalg.norm(normal)
    helper = np.array([1.0, 0.0, 0.0]) if abs(normal[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(normal, helper)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    return (np.asarray(center_cam, dtype=float)[None, :]
            + radius_mm * (np.cos(t)[:, None] * u[None, :] + np.sin(t)[:, None] * v[None, :]))


def project_points(points_cam: np.ndarray, k_mat: np.ndarray) -> np.ndarray:
    pts = np.asarray(points_cam, dtype=float)
    z = np.where(np.abs(pts[:, 2]) < 1e-9, 1e-9, pts[:, 2])
    img = (k_mat @ (pts / z[:, None]).T).T
    return img[:, :2]


# --------------------------------------------------------------------------
# ujemanje notranje/zunanje elipse
# --------------------------------------------------------------------------
def _pair_disagreement(sol_a: CirclePose, sol_b: CirclePose, radius_ref: float
                       ) -> Tuple[float, float]:
    """(kot med normalama [rad], relativna razdalja sredisc)."""
    cos_a = float(np.clip(abs(sol_a.normal @ sol_b.normal), -1.0, 1.0))
    angle = math.acos(cos_a)
    dist = float(np.linalg.norm(sol_a.center - sol_b.center)) / max(radius_ref, 1e-6)
    return angle, dist


def solve_pair(pair: EllipsePair, k_mat: np.ndarray, cfg: Config
               ) -> Optional[Tuple[CirclePose, float, float]]:
    """Razresi dvoumnost s soglasjem notranje in zunanje elipse.

    Vrne (poza zunanjega kroga, kot neujemanja [deg], relativni odmik sredisc)
    ali None, ce poze sploh ni mogoce izracunati.
    """
    r_out = float(cfg["flange.d_out_mm"]) / 2.0
    r_in = float(cfg["flange.d_in_mm"]) / 2.0
    # Pri nesparjeni elipsi polariteta roba pove, ali gledamo obris ali luknjo -
    # zamenjava bi dala 2.5-krat napacno globino.
    radius_main = r_in if getattr(pair, "role", "outer") == "inner" else r_out
    outer_sols = circle_pose_solutions(pair.outer.matrix(), k_mat, radius_main)
    if not outer_sols:
        return None
    if pair.inner is None:
        best = max(outer_sols, key=lambda s: float(-s.normal[2]))
        return best, float("nan"), float("nan")
    inner_sols = circle_pose_solutions(pair.inner.matrix(), k_mat, r_in)
    if not inner_sols:
        best = max(outer_sols, key=lambda s: float(-s.normal[2]))
        return best, float("nan"), float("nan")
    best_cost = None
    best: Optional[Tuple[CirclePose, float, float]] = None
    r_out = radius_main
    for so in outer_sols:
        for si in inner_sols:
            angle, dist = _pair_disagreement(so, si, r_out)
            cost = angle + dist
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best = (so, math.degrees(angle), dist)
    return best


def pair_consistency_cost(pairs, k_mat: np.ndarray, cfg: Config) -> Optional[float]:
    """Cenilka za autokalibracijo: koliko se pozi obeh koncentricnih krogov
    razhajata pri danem K. Pri pravem f je (do suma) enaka nic.
    """
    w_n = float(cfg["autocalib.refine.normal_weight"])
    w_c = float(cfg["autocalib.refine.center_weight"])
    costs = []
    for pair in pairs:
        if pair.inner is None:
            continue
        res = solve_pair(pair, k_mat, cfg)
        if res is None:
            continue
        _, angle_deg, dist = res
        if not math.isfinite(angle_deg) or not math.isfinite(dist):
            continue
        costs.append(w_n * (math.radians(angle_deg)) + w_c * dist)
    if not costs:
        return None
    return float(np.median(costs))


def build_flange_pose(pair: EllipsePair, k_mat: np.ndarray, cfg: Config,
                      rot_box: Optional[np.ndarray] = None,
                      t_box: Optional[np.ndarray] = None) -> Optional[FlangePose]:
    res = solve_pair(pair, k_mat, cfg)
    if res is None:
        return None
    sol, angle_deg, center_ratio = res
    reasons: List[str] = []
    confidence = 1.0
    paired = pair.inner is not None
    if not paired:
        confidence *= float(cfg["pose.unpaired_confidence"])
        role = getattr(pair, "role", "outer")
        reasons.append("elipsa brez para (dvoumnost razresena hevristicno, "
                       + ("interpretirana kot luknja)" if role == "inner"
                          else "interpretirana kot obris)"))
    else:
        max_angle = float(cfg["pose.max_pair_normal_angle_deg"])
        max_ratio = float(cfg["pose.max_pair_center_ratio"])
        if math.isfinite(angle_deg):
            if angle_deg > max_angle:
                confidence *= 0.3
                reasons.append(f"normali notranje/zunanje elipse se razhajata za {angle_deg:.1f} deg")
            else:
                confidence *= float(np.clip(1.0 - angle_deg / max(max_angle, 1e-6), 0.15, 1.0))
        if math.isfinite(center_ratio):
            if center_ratio > max_ratio:
                confidence *= 0.3
                reasons.append(f"sredisci se razhajata za {center_ratio:.2f} r_out")
            else:
                confidence *= float(np.clip(1.0 - center_ratio / max(max_ratio, 1e-6), 0.15, 1.0))

    confidence *= float(np.clip(pair.outer.support_ratio, 0.05, 1.0))
    pose = FlangePose(center_cam=sol.center, normal_cam=sol.normal,
                      pair_normal_angle_deg=float(angle_deg) if math.isfinite(angle_deg) else -1.0,
                      pair_center_ratio=float(center_ratio) if math.isfinite(center_ratio) else -1.0,
                      confidence=float(max(confidence, float(cfg["pose.min_confidence"]))),
                      paired=paired, reasons=reasons)

    # Dvoumnost poze iz kroga razresi soglasje notranje in zunanje elipse. Brez
    # para te opore ni: obe resitvi dasta isto elipso, zato je smer nagiba pri
    # izrazito nagnjenem kosu (izmerjeno) priblizno met kovanca. Velikost naklona
    # ostane pravilna, napacna je lahko le smer - zato to oznacimo posebej,
    # namesto da bi kandidata tiho izpustili.
    ambiguous_tilt = float(cfg["pose.unpaired_ambiguous_tilt_deg"])

    if rot_box is not None and t_box is not None:
        pose.center_box = rot_box.T @ (sol.center - t_box)
        pose.normal_box = rot_box.T @ sol.normal
        if pose.normal_box[2] < 0:
            pose.normal_box = -pose.normal_box
        nz = float(np.clip(pose.normal_box[2], -1.0, 1.0))
        pose.tilt_deg = math.degrees(math.acos(nz))
        pose.azimuth_deg = math.degrees(math.atan2(float(pose.normal_box[1]),
                                                   float(pose.normal_box[0]))) % 360.0
        _flag_orientation(pose, ambiguous_tilt)
    else:
        n_cam = sol.normal
        # brez zaboja: tilt glede na opticno os
        nz = float(np.clip(abs(n_cam[2]), -1.0, 1.0))
        pose.tilt_deg = math.degrees(math.acos(nz))
        pose.azimuth_deg = math.degrees(math.atan2(float(n_cam[1]), float(n_cam[0]))) % 360.0
        _flag_orientation(pose, ambiguous_tilt)
    return pose


def _flag_orientation(pose: FlangePose, ambiguous_tilt_deg: float) -> None:
    """Oznaci nesparjene kandidate, katerim smeri nagiba ni mogoce zaupati."""
    if pose.paired or pose.tilt_deg <= ambiguous_tilt_deg:
        return
    pose.orientation_ambiguous = True
    pose.reasons.append(
        f"smer nagiba (azimut) ni zanesljiva: kos je nagnjen za {pose.tilt_deg:.0f} deg, "
        "luknja pa ni vidna, zato zrcalne resitve ni mogoce izlociti - "
        "azimut je lahko zasukan za 180 deg")
    # Napaka smeri je nicelna pri ravnem kosu in najvecja pri mocnem naklonu.
    pose.confidence *= float(np.clip(ambiguous_tilt_deg / max(pose.tilt_deg, 1e-6), 0.1, 1.0))
