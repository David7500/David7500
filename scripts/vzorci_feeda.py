#!/usr/bin/env python
"""Vzorči sestavo GTFS-RT feedov skozi dan.

Vprašanje, na katero odgovarja: **katere agencije sploh imajo realtime?**
Ponoči vozi pet vlakov in nič drugega, zato en sam pogled ne pove ničesar.
Skript teče v ozadju in vsakih nekaj minut zapiše, koliko voženj katere
agencije je v `trip_updates` in koliko vozil v `vehicle_positions`.

Rezultat je vhod v odločitev, ali se avtobusov sploh splača lotiti in katerih.
Zapisuje v JSONL, da se da brati tudi med tekom.

    ./venv/bin/python scripts/vzorci_feeda.py --minutes 720 --every 300
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from google.transit import gtfs_realtime_pb2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sztrack import config  # noqa: E402

AGENCY_NAMES = {
    "1123": "Arriva", "1121": "AP Murska Sobota", "1118": "LPP",
    "1119": "Nomago", "1161": "SŽ",
}
VEHICLE_URL = "https://rt.gtfs.derp.si/sources/ijpp/vehicle_positions"


def trip_index(zip_path: Path) -> dict[str, tuple[str, str]]:
    """trip_id -> (agency_id, route_type). Iz zipa, ki ga imamo na disku."""
    with zipfile.ZipFile(zip_path) as zf:
        def rows(name):
            with zf.open(name) as fh:
                yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
        routes = {r["route_id"]: (r["agency_id"], r["route_type"]) for r in rows("routes.txt")}
        return {t["trip_id"]: routes[t["route_id"]]
                for t in rows("trips.txt") if t["route_id"] in routes}


def fetch(url: str):
    resp = requests.get(url, timeout=60, headers={"User-Agent": config.USER_AGENT})
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def sample(index: dict[str, tuple[str, str]]) -> dict:
    out: dict = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for key, url, trip_of in (
        ("trip_updates", config.TRIP_UPDATES_URL, lambda e: e.trip_update.trip.trip_id),
        ("vehicle_positions", VEHICLE_URL, lambda e: e.vehicle.trip.trip_id),
    ):
        try:
            feed = fetch(url)
        except Exception as exc:
            out[key] = {"napaka": str(exc)[:120]}
            continue
        counts: collections.Counter = collections.Counter()
        unknown = 0
        for entity in feed.entity:
            info = index.get(trip_of(entity))
            if info is None:
                unknown += 1
                continue
            counts[f"{AGENCY_NAMES.get(info[0], info[0])}/{info[1]}"] += 1
        out[key] = {"skupaj": len(feed.entity), "neznano": unknown, **dict(counts)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=int, default=720, help="koliko časa vzorčiti")
    ap.add_argument("--every", type=int, default=300, help="sekund med vzorci")
    ap.add_argument("--out", default=str(ROOT / "data" / "vzorci_feeda.jsonl"))
    ap.add_argument("--zip", default=str(config.DATA_DIR / "ijpp_gtfs.zip"))
    args = ap.parse_args()

    index = trip_index(Path(args.zip))
    print(f"kazalo: {len(index)} voženj", flush=True)

    deadline = time.monotonic() + args.minutes * 60
    with open(args.out, "a", encoding="utf-8") as fh:
        while time.monotonic() < deadline:
            row = sample(index)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            print(row["at"], row.get("trip_updates"), flush=True)
            time.sleep(args.every)


if __name__ == "__main__":
    main()
