"""Tiri s številko iz OSM: vlak na postaji stoji na tiru s table SŽ.

    ./venv/bin/python -m pytest tests/test_tiri.py -q
"""
from __future__ import annotations

import json

from kajros import config, tiri


def _izvoz(pot, tiri_):
    """geojsonseq kot ga da `osmium export` (z ločilom RS na začetku)."""
    with open(pot, "w", encoding="utf-8") as f:
        for ref, crta in tiri_:
            f.write("\x1e" + json.dumps({
                "type": "Feature",
                "properties": {"railway": "rail", **({"railway:track_ref": ref} if ref else {})},
                "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in crta]},
            }) + "\n")


def test_stevilka_s_table():
    assert tiri.stevilka("6-A") == "6"
    assert tiri.stevilka(" 12 ") == "12"
    assert tiri.stevilka("1a") == "1A"
    assert tiri.stevilka("03") == "3"
    assert tiri.stevilka("") is None and tiri.stevilka(None) is None


def test_na_tiru(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    # Dva vzporedna tira vzhod-zahod, 4,4 m narazen, in tir brez številke.
    _izvoz(tmp_path / "izvoz", [
        ("3", [[46.05850, 14.505], [46.05850, 14.515]]),
        ("4", [[46.05854, 14.505], [46.05854, 14.515]]),
        (None, [[46.05860, 14.505], [46.05860, 14.515]]),
    ])
    izid = tiri.zgradi(tmp_path / "izvoz", tiri.pot())
    assert izid["tirov"] == 2

    # Vlak na trasi med tiroma, proti vzhodu, s table „4-B“.
    lega = tiri.na_tiru(46.05852, 14.510, "4-B", 92)
    assert abs(lega["lat"] - 46.05854) < 1e-6 and abs(lega["lon"] - 14.510) < 1e-6
    assert abs(lega["smer"] - 90) < 1
    # Proti zahodu: tir ostane isti, smer se obrne.
    assert abs(tiri.na_tiru(46.05852, 14.510, "4", 268)["smer"] - 270) < 1
    # Tira s to številko ni ali je predaleč (drugo mesto): nič.
    assert tiri.na_tiru(46.05852, 14.510, "7", 90) is None
    assert tiri.na_tiru(46.07, 14.510, "4", 90) is None
    assert tiri.na_tiru(46.05852, 14.510, None, 90) is None


def test_brez_datoteke(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    assert tiri.na_tiru(46.0585, 14.51, "3", 90) is None
