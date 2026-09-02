"""Nastavitve. Vse se da povoziti prek okoljskih spremenljivk."""
from __future__ import annotations

import os
from pathlib import Path


def okolje(ime: str, privzeto: str | None = None) -> str | None:
    """Prebere `KAJROS_<ime>`; ce ga ni, se stari `SZ_<ime>`.

    Projekt se je 3. 9. 2026 preimenoval iz `sztrack` v `kajros`. Malina do
    prve ponovne namestitve tece s **staro** `systemd` enoto, ki nastavlja
    stara imena; brez tega zasilnega izhoda bi tam nova koda tiho vzela
    privzetke --
    torej brez avtobusov in z napačno potjo do baze, in to bi bilo videti kot
    izgubljen zajem, ne kot napaka nastavitve.

    **Odstrani po 1. 12. 2026**, ko bo malina zagotovo na novi enoti.
    """
    v = os.environ.get(f"KAJROS_{ime}")
    if v is None:
        v = os.environ.get(f"SZ_{ime}")
    return privzeto if v is None else v


DATA_DIR = Path(okolje("DATA_DIR", "data")).resolve()
DB_PATH = Path(okolje("DB", DATA_DIR / "kajros.sqlite"))

# Statični vozni red (~41 MB, regeneriran priblizno enkrat dnevno).
GTFS_URL = okolje("GTFS_URL",
    "https://gitlab.com/api/v4/projects/derp-si%2Fgtfs-generators"
    "/packages/generic/IJPP/latest/ijpp_gtfs.zip",
)
# Zamude (~250 KB, osvezeno vsakih 30 s).
TRIP_UPDATES_URL = okolje("TRIP_UPDATES_URL", "https://rt.gtfs.derp.si/sources/ijpp/trip_updates"
)
SERVICE_ALERTS_URL = okolje("SERVICE_ALERTS_URL", "https://rt.gtfs.derp.si/sources/ijpp/service_alerts"
)
# Lega vozil (~2 KB). Nosi SAMO avtobuse -- vlakov v njem ni, zato je za
# železnico brez pomena in se pobira le, kadar so uvožene tudi druge agencije.
VEHICLE_POSITIONS_URL = okolje("VEHICLE_POSITIONS_URL", "https://rt.gtfs.derp.si/sources/ijpp/vehicle_positions"
)

# SŽ potniški promet. Poleg vlakov (GTFS route_type 2) uvozimo tudi njihove
# **nadomestne prevoze** (route_type 3): avgusta 2026 je bilo teh 56 voženj in
# na relacijah, kjer vlak ne vozi (Ljubljana - Logatec, Divača - Koper), so
# edina dejanska povezava. Brez njih iskalnik ponuja vlak, ki ne pelje.
RAIL_AGENCY_ID = okolje("AGENCY_ID", "1161")
RAIL_ROUTE_TYPE = "2"
BUS_ROUTE_TYPE = "3"
INCLUDE_REPLACEMENT_BUS = okolje("REPLACEMENT_BUS", "1") != "0"

# Ostale agencije so v istem zipu: LPP 3060 voženj, Arriva 8914, Nomago 6864,
# AP Murska Sobota 965. Vse imajo realtime pokritost (izmerjeno z
# `scripts/vzorci_feeda.py`: ob 06:42 v soboto 100 % ali več), avtobusi pa
# imajo tudi GPS lego, ki je vlaki nimajo.
#
# `KAJROS_AGENCIES` je vejicami ločen seznam ID-jev. Privzeto samo SŽ.
#   1161 SŽ · 1118 LPP · 1123 Arriva · 1119 Nomago · 1121 AP Murska Sobota
EXTRA_AGENCIES = tuple(
    a.strip() for a in okolje("AGENCIES", "").split(",") if a.strip()
)

POLL_SECONDS = int(okolje("POLL_SECONDS", "30"))

# Lege imajo svoj, hitrejsi ritem od zamud -- feeda se ne spreminjata enako.
# Vozilo objavi novo lego vsakih 20 s (izmerjeno), zamuda pa se zapise sele ob
# spremembi nad 60 s. Branje obojega na 30 s je torej lege bralo prepocasi in
# zamude prepogosto. 10 s je pol vozilovega ritma; pod tem ni cesa dobiti.
POSITION_SECONDS = int(okolje("POSITION_SECONDS", "10"))
# Sencno merjenje napovedi (`ocena.py`). Tece ob strezniku in samo bere.
# Razmik 120 s: posnetek se zapise enkrat na postanek (kljuc tabele), zato
# gostejsi obhod ne da vec vrstic, le vec praznih poizvedb.
OCENA_SECONDS = int(okolje("OCENA_SECONDS", "120"))
# Vsak avtobusni postanek bi bil ~135 000 vrstic na dan (13 MB); vzorec vsake
# pete voznje jih da 27 000, kar je za mediano in delez vec kot dovolj.
# Vzorci se po `trip_id`, ne po postanku -- voznja mora biti cela ali nobena.
OCENA_BUS_VZOREC = int(okolje("OCENA_BUS_VZOREC", "5"))
OCENA_KEEP_DAYS = int(okolje("OCENA_KEEP_DAYS", "30"))

USER_AGENT = okolje("USER_AGENT", "kajros/0.1 (+https://github.com/David7500)")
TIMEZONE = "Europe/Ljubljana"

# Postaja, ki je od proge oddaljena vec kot toliko metrov, se ne projicira nanjo.
MAX_STATION_OFFSET_M = 1500.0
