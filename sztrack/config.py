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

# SŽ potniški promet; samo vlaki (GTFS route_type 2).
RAIL_AGENCY_ID = os.environ.get("SZ_AGENCY_ID", "1161")
RAIL_ROUTE_TYPE = "2"

POLL_SECONDS = int(os.environ.get("SZ_POLL_SECONDS", "30"))
USER_AGENT = os.environ.get("SZ_USER_AGENT", "sztrack/0.1 (+https://github.com/David7500)")
TIMEZONE = "Europe/Ljubljana"

# Postaja, ki je od proge oddaljena vec kot toliko metrov, se ne projicira nanjo.
MAX_STATION_OFFSET_M = 1500.0
