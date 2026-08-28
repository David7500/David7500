"""Nastavitve. Vse se da povoziti prek okoljskih spremenljivk."""
from __future__ import annotations

import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("SZ_DATA_DIR", "data")).resolve()
DB_PATH = Path(os.environ.get("SZ_DB", DATA_DIR / "sz.sqlite"))

# Statični vozni red (~41 MB, regeneriran priblizno enkrat dnevno).
GTFS_URL = os.environ.get(
    "SZ_GTFS_URL",
    "https://gitlab.com/api/v4/projects/derp-si%2Fgtfs-generators"
    "/packages/generic/IJPP/latest/ijpp_gtfs.zip",
)
# Zamude (~250 KB, osvezeno vsakih 30 s).
TRIP_UPDATES_URL = os.environ.get(
    "SZ_TRIP_UPDATES_URL", "https://rt.gtfs.derp.si/sources/ijpp/trip_updates"
)
SERVICE_ALERTS_URL = os.environ.get(
    "SZ_SERVICE_ALERTS_URL", "https://rt.gtfs.derp.si/sources/ijpp/service_alerts"
)

# SŽ potniški promet. Poleg vlakov (GTFS route_type 2) uvozimo tudi njihove
# **nadomestne prevoze** (route_type 3): avgusta 2026 je bilo teh 56 voženj in
# na relacijah, kjer vlak ne vozi (Ljubljana - Logatec, Divača - Koper), so
# edina dejanska povezava. Brez njih iskalnik ponuja vlak, ki ne pelje.
RAIL_AGENCY_ID = os.environ.get("SZ_AGENCY_ID", "1161")
RAIL_ROUTE_TYPE = "2"
BUS_ROUTE_TYPE = "3"
# Ostale agencije (LPP, Arriva, Nomago, AP Murska Sobota) so v istem zipu in
# so zaenkrat izpuscene -- 20 000 voznj proti 800.
INCLUDE_REPLACEMENT_BUS = os.environ.get("SZ_REPLACEMENT_BUS", "1") != "0"

POLL_SECONDS = int(os.environ.get("SZ_POLL_SECONDS", "30"))
USER_AGENT = os.environ.get("SZ_USER_AGENT", "sztrack/0.1 (+https://github.com/David7500)")
TIMEZONE = "Europe/Ljubljana"

# Postaja, ki je od proge oddaljena vec kot toliko metrov, se ne projicira nanjo.
MAX_STATION_OFFSET_M = 1500.0
