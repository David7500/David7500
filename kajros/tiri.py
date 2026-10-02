"""Tiri na postajah iz OpenStreetMap: kje stoji vlak, ki mu SŽ objavi tir.

Tabla SŽ pove tir (`peroni.py`, npr. „6-A“ = tir 6, sektor A), OSM pa ima
številko tira (`railway:track_ref`) na 1 678 tirih v Sloveniji (2. 10. 2026);
ljubljanska glavna postaja na tirih 3, 4 in 8–13. Od tirov, ki jih tabla
objavi, jih OSM na tisti postaji pozna 32 %. Kjer sta oba, vlak na
zemljevidu stoji na svojem tiru, ne na tistem, po katerem gre pripeta trasa
(`pripni.py`).

Vir je izvoz OSM (`deploy/osrm.sh`, osmium -> geojsonseq), ki ga `kajros
tiri` zgosti v `${KAJROS_DATA_DIR}/tiri.json`. Datoteka, ne tabela: tako jo
lahko zgradi kdorkoli z dostopom do mape, brez pisanja v živo bazo, in
strežnik novo opazi sam (`mtime`). Brez nje je vse kot prej.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from . import config
from .deljenje import Trasa

#: Kako daleč od postaje (točke na trasi) iščemo tir s to številko. Perone
#: velikih postaj so dolgi 300--400 m, tir je od osi pripete trase do
#: nekaj deset metrov.
ISCI_M = 500.0

#: Tir, ki je od vlakove lege dlje od tega, ni tir te postaje.
NAJVEC_M = 120.0

_zaklep = threading.Lock()
_stanje: dict = {"mtime": None, "po_tiru": {}}


def pot() -> Path:
    return Path(config.DATA_DIR) / "tiri.json"


def stevilka(tir: str | None) -> str | None:
    """Številka tira s table: „6-A“ -> „6“, „12“ -> „12“, „1A“ -> „1A“."""
    if not tir:
        return None
    t = tir.strip().upper().split("-")[0].strip()
    t = re.sub(r"^0+(?=\d)", "", t)
    return t or None


def zgradi(vir: Path, cilj: Path) -> dict:
    """Iz izvoza OSM (geojsonseq) obdrži tire s številko in jih zapiše."""
    tiri = []
    with open(vir, encoding="utf-8") as f:
        for vrstica in f:
            vrstica = vrstica.lstrip("\x1e").strip()
            if not vrstica:
                continue
            o = json.loads(vrstica)
            p = o.get("properties") or {}
            g = o.get("geometry") or {}
            ref = stevilka(p.get("railway:track_ref"))
            if p.get("railway") != "rail" or not ref or g.get("type") != "LineString":
                continue
            tiri.append({"ref": ref,
                         "c": [[round(lat, 6), round(lon, 6)] for lon, lat in g["coordinates"]]})
    tmp = Path(cilj).with_suffix(".tmp")
    tmp.write_text(json.dumps(tiri, separators=(",", ":")), encoding="utf-8")
    tmp.replace(cilj)
    return {"tirov": len(tiri), "bajtov": Path(cilj).stat().st_size}


def _po_tiru() -> dict[str, list[Trasa]]:
    """{številka: [tiri]} iz datoteke; prebere znova, ko se spremeni."""
    p = pot()
    try:
        kljuc = (str(p), p.stat().st_mtime_ns)
    except OSError:
        return {}
    with _zaklep:
        if _stanje["mtime"] != kljuc:
            po_tiru: dict[str, list[Trasa]] = {}
            for t in json.loads(p.read_text(encoding="utf-8")):
                if len(t["c"]) >= 2:
                    po_tiru.setdefault(t["ref"], []).append(Trasa([[tuple(x) for x in t["c"]]]))
            _stanje.update(mtime=kljuc, po_tiru=po_tiru)
        return _stanje["po_tiru"]


def na_tiru(lat: float, lon: float, tir: str | None, smer: float | None) -> dict | None:
    """{lat, lon, smer} na tiru s to številko ob tej točki, ali None.

    Smer tira je dvoumna (tir nima smeri vožnje); vzamemo tisto, ki je bliže
    smeri vlaka na trasi.
    """
    ref = stevilka(tir)
    if ref is None:
        return None
    naj = None
    for t in _po_tiru().get(ref, ()):
        if not t.blizu(lat, lon, ISCI_M):
            continue
        along, odmik = t.projiciraj(lat, lon, najvec_m=NAJVEC_M)
        if odmik <= NAJVEC_M and (naj is None or odmik < naj[2]):
            naj = (t, along, odmik)
    if naj is None:
        return None
    t, along, _ = naj
    t_lat, t_lon = t.tocka(along)
    s = t.smer(along, 40)
    if s is not None and smer is not None and abs((s - smer + 180) % 360 - 180) > 90:
        s = (s + 180) % 360
    return {"lat": round(t_lat, 6), "lon": round(t_lon, 6),
            "smer": s if s is not None else smer}
