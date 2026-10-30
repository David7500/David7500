#!/usr/bin/env python3
"""Posnetek avtobusnih postajališč iz OpenStreetMap, za `opazovano.py`.

  python scripts/osm_postajalisca.py              # prenese z Overpassa in zapiše
  python scripts/osm_postajalisca.py --iz odgovor.json

Neodvisen dokaz, da je postajališče res na koordinati iz voznega reda. Posnetek
v gitu kot `nadomestna_postajalisca.json`, ne klic ponoči: odgovor traja minute,
postajališča pa se redko selijo. Podatki © sodelavci OpenStreetMap, ODbL.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

CILJ = Path(__file__).resolve().parent.parent / "kajros" / "osm_postajalisca.json"
STREZNIKI = ("https://overpass-api.de/api/interpreter",
             "https://overpass.kumi.systems/api/interpreter")
POIZVEDBA = ('[out:json][timeout:240];area["ISO3166-1"="SI"][admin_level=2]->.s;'
             '(node(area.s)[highway=bus_stop];node(area.s)[public_transport=platform][bus=yes];);'
             'out body;')


def prenesi() -> dict:
    napaka = None
    for url in STREZNIKI:
        zahteva = urllib.request.Request(
            url, data=urllib.parse.urlencode({"data": POIZVEDBA}).encode(),
            headers={"User-Agent": "kajros-posnetek/1.0"})
        try:
            with urllib.request.urlopen(zahteva, timeout=280) as o:
                return json.load(o)
        except (OSError, ValueError) as exc:
            napaka = exc
            print(f"{url}: {exc}", file=sys.stderr)
    raise SystemExit(f"Overpass ni odgovoril: {napaka}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iz", type=Path, help="odgovor Overpassa, namesto prenosa")
    args = p.parse_args()
    odgovor = json.loads(args.iz.read_text(encoding="utf-8")) if args.iz else prenesi()
    vrstice = sorted([round(e["lat"], 5), round(e["lon"], 5), e.get("tags", {}).get("name", "")]
                     for e in odgovor["elements"])
    CILJ.write_text(json.dumps({
        "vir": "OpenStreetMap, ODbL",
        "posneto": odgovor.get("osm3s", {}).get("timestamp_osm_base"),
        "postajalisca": vrstice}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(vrstice)} postajališč v {CILJ}")


if __name__ == "__main__":
    main()
