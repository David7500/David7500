"""Predobdelava: CLAHE, bilateralni filter, maska spekularnih odsevov.

Spekularni odsevi na svetleci plocevini so nasiceni piksli - njihovi robovi so
lazni robovi. Zaznamo jih in maskiramo, namesto da bi jih obravnavali kot rob.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from .config import Config


@dataclass
class Preprocessed:
    gray: np.ndarray            # uint8, po CLAHE + bilateralnem filtru
    raw_gray: np.ndarray        # uint8, original v sivini
    specular_mask: np.ndarray   # uint8 0/255, 255 = odsev
    diagnostics: dict


def to_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("slika je None")
    if image.ndim == 3:
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.dtype != np.uint8:
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return image


def specular_mask(gray: np.ndarray, cfg: Config) -> np.ndarray:
    abs_thr = float(cfg["preprocess.specular_abs_threshold"])
    pct = float(cfg["preprocess.specular_percentile"])
    pct_thr = float(np.percentile(gray, pct)) if gray.size else 255.0
    thr = min(abs_thr, max(pct_thr, abs_thr - 25.0))
    mask = (gray >= thr).astype(np.uint8) * 255
    min_blob = int(cfg["preprocess.specular_min_blob_px"])
    if min_blob > 1 and mask.any():
        num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        keep = np.zeros(num, dtype=bool)
        for i in range(1, num):
            keep[i] = stats[i, cv2.CC_STAT_AREA] >= min_blob
        mask = np.where(keep[labels], 255, 0).astype(np.uint8)
    dil = int(cfg["preprocess.specular_dilate_px"])
    if dil > 0 and mask.any():
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dil + 1, 2 * dil + 1))
        mask = cv2.dilate(mask, kernel)
    return mask


def preprocess(image: np.ndarray, cfg: Config) -> Preprocessed:
    raw = to_gray(image)
    clahe = cv2.createCLAHE(clipLimit=float(cfg["preprocess.clahe_clip"]),
                            tileGridSize=(int(cfg["preprocess.clahe_grid"]),) * 2)
    enhanced = clahe.apply(raw)
    filtered = cv2.bilateralFilter(enhanced,
                                   int(cfg["preprocess.bilateral_d"]),
                                   float(cfg["preprocess.bilateral_sigma_color"]),
                                   float(cfg["preprocess.bilateral_sigma_space"]))
    mask = specular_mask(raw, cfg)
    diag = {
        "shape": [int(raw.shape[1]), int(raw.shape[0])],
        "mean_intensity": float(raw.mean()) if raw.size else 0.0,
        "specular_fraction": float(mask.mean() / 255.0) if mask.size else 0.0,
    }
    return Preprocessed(gray=filtered, raw_gray=raw, specular_mask=mask, diagnostics=diag)
