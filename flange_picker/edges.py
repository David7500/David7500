"""Robovi s subpixel natancnostjo.

Canny da robne piksle, nato vsako tocko premaknemo vzdolz gradienta na vrh
parabole skozi tri vzorce gradientne magnitude (Devernayjev pristop). Brez tega
je fit elipse omejen s celoinstevilcno mrezo in ocena Z sistematicno sumna.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np

from .config import Config


@dataclass
class EdgeMap:
    points: np.ndarray            # (N,2) subpixel robne tocke
    contours: List[np.ndarray]    # verige subpixel tock
    mask: np.ndarray              # uint8 Canny maska
    diagnostics: dict
    gx: Optional[np.ndarray] = None   # gradient, na katerem je merjena lega robov
    gy: Optional[np.ndarray] = None


def _bilinear(img: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    h, w = img.shape
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 2)
    fx = np.clip(xs - x0, 0.0, 1.0)
    fy = np.clip(ys - y0, 0.0, 1.0)
    v00 = img[y0, x0]
    v10 = img[y0, x0 + 1]
    v01 = img[y0 + 1, x0]
    v11 = img[y0 + 1, x0 + 1]
    return (v00 * (1 - fx) * (1 - fy) + v10 * fx * (1 - fy)
            + v01 * (1 - fx) * fy + v11 * fx * fy)


def detect_edges(gray: np.ndarray, cfg: Config, exclude_mask: Optional[np.ndarray] = None,
                 gradient_image: Optional[np.ndarray] = None) -> EdgeMap:
    """Canny na `gray` odloci, KJE je rob; subpixel lega se meri na `gradient_image`.

    CLAHE in bilateralni filter pomagata robove sploh najti, a ob sumu prestavita
    vrh gradienta - izmerjeno za +0.28 px, kar je pri premeru 35 px ze 0.8 %
    napake v Z. Zato se lega robov meri na surovi sliki z blagim glajenjem.
    """
    ksize = int(cfg["edges.sobel_ksize"])
    if gradient_image is None:
        grad_src = gray
    else:
        sigma = float(cfg["edges.gradient_blur_sigma"])
        grad_src = (cv2.GaussianBlur(gradient_image, (0, 0), sigma) if sigma > 0
                    else gradient_image)
    gx = cv2.Sobel(grad_src, cv2.CV_32F, 1, 0, ksize=ksize)
    gy = cv2.Sobel(grad_src, cv2.CV_32F, 0, 1, ksize=ksize)
    mag = cv2.magnitude(gx, gy)

    canny = cv2.Canny(gray, int(cfg["edges.canny_low"]), int(cfg["edges.canny_high"]),
                      L2gradient=True)
    if exclude_mask is not None and exclude_mask.shape == canny.shape:
        canny = cv2.bitwise_and(canny, cv2.bitwise_not(exclude_mask))

    chains, _ = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    step = float(cfg["edges.subpixel_step_px"])
    max_shift = float(cfg["edges.subpixel_max_shift_px"])
    min_pts = int(cfg["edges.min_contour_points"])

    refined: List[np.ndarray] = []
    for chain in chains:
        pts = chain.reshape(-1, 2).astype(np.float64)
        if len(pts) < min_pts:
            continue
        xs, ys = pts[:, 0], pts[:, 1]
        yi = np.clip(ys.astype(int), 0, gray.shape[0] - 1)
        xi = np.clip(xs.astype(int), 0, gray.shape[1] - 1)
        dx, dy = gx[yi, xi], gy[yi, xi]
        norm = np.sqrt(dx * dx + dy * dy)
        ok = norm > 1e-6
        dirx = np.where(ok, dx / np.where(ok, norm, 1.0), 0.0)
        diry = np.where(ok, dy / np.where(ok, norm, 1.0), 0.0)
        m0 = _bilinear(mag, xs, ys)
        mm = _bilinear(mag, xs - step * dirx, ys - step * diry)
        mp = _bilinear(mag, xs + step * dirx, ys + step * diry)
        denom = mm - 2.0 * m0 + mp
        delta = np.where(np.abs(denom) > 1e-9, 0.5 * (mm - mp) / np.where(np.abs(denom) > 1e-9, denom, 1.0), 0.0)
        delta = np.clip(delta, -max_shift, max_shift) * step
        sub = np.stack([xs + delta * dirx, ys + delta * diry], axis=1)
        refined.append(sub)

    points = np.concatenate(refined, axis=0) if refined else np.zeros((0, 2), dtype=float)
    diag = {
        "n_contours": len(refined),
        "n_edge_points": int(len(points)),
        "canny_fraction": float(canny.mean() / 255.0) if canny.size else 0.0,
    }
    return EdgeMap(points=points, contours=refined, mask=canny, diagnostics=diag, gx=gx, gy=gy)
