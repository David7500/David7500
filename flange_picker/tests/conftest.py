"""Skupne testne pripomocke.

Testi tecejo na manjsih slikah kot produkcijska konfiguracija, da so hitri;
geometrija in vsi pragovi ostanejo isti.
"""

from __future__ import annotations

import numpy as np
import pytest

from flange_picker.config import load_config


@pytest.fixture(scope="session")
def cfg():
    """Konfiguracija z manjso sinteticno sliko (hitrejsi testi).

    Podana je tudi delovna razdalja - tako kot v resnicni celici, kjer je znana
    vsaj na nekaj odstotkov. Brez nje absolutna visina ni dolocljiva (glej
    ROADMAP: f_px pri navpicni kameri ni opazljiv) in testi visine ne bi merili
    algoritma, ampak nakljucje rezervne vrednosti.
    """
    return load_config().with_overrides({
        "camera": {"working_distance_mm": 590.0},   # resnicna je 560-620 mm
        # Goriscna razdalja in delovna razdalja sta izbrani tako, da je zaboj z
        # vred robom v celoti v kadru - sicer se meri kadriranje, ne algoritem.
        "synth": {"image_width": 800, "image_height": 600, "supersample": 3,
                  "f_px_min": 700.0, "f_px_max": 780.0,
                  "distance_mm_min": 560.0, "distance_mm_max": 620.0},
    })


@pytest.fixture(scope="session")
def cfg_full():
    """Nespremenjena produkcijska konfiguracija."""
    return load_config()


def flat_flange(x_mm: float, y_mm: float, z_mm: float = 0.75, tilt_deg: float = 0.0,
                azimuth_deg: float = 0.0) -> dict:
    return {"x_mm": x_mm, "y_mm": y_mm, "z_mm": z_mm,
            "tilt_deg": tilt_deg, "azimuth_deg": azimuth_deg}


def match_to_gt(candidates, gt_flanges, cfg, max_dist_mm: float = 25.0):
    """Pari kandidate z ground truth ob upostevanju 2-kratne dvoumnosti okvira."""
    w_mm, h_mm = float(cfg["box.w_mm"]), float(cfg["box.h_mm"])
    gt = np.array([[f["x_mm"], f["y_mm"]] for f in gt_flanges], dtype=float)
    pred = np.array([[c["x_mm"], c["y_mm"]] for c in candidates], dtype=float).reshape(-1, 2)
    best = []
    for rot, off in ((np.eye(2), np.zeros(2)),
                     (np.array([[-1.0, 0.0], [0.0, -1.0]]), np.array([w_mm, h_mm]))):
        moved = (rot @ pred.T).T + off if len(pred) else pred
        pairs = []
        for i, p in enumerate(moved):
            if not len(gt):
                break
            j = int(np.argmin(np.linalg.norm(gt - p, axis=1)))
            d = float(np.linalg.norm(gt[j] - p))
            if d <= max_dist_mm:
                pairs.append((i, j, d))
        if len(pairs) > len(best):
            best = pairs
    return best
