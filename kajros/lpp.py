"""Živi prihodi mestnega LPP iz njihovega lastnega API-ja (`data.lpp.si`).

**Zakaj poleg derp.si, s katerega isti promet že beremo.** derp.si naredi nov
posnetek vsakih ~90 s in lega je v njem stara že mediano 35 s; ta vir se
spremeni vsakih 10–30 s. Izmerjeno 7. 9. 2026, razrez v `docs/MERITVE.md`.
Cena je zaokroževanje na **celo minuto** (±30 s) — zato ta vir ne nadomesti
meritve, ampak samo **napoved za postanke naprej**.

**Nič od tega ne gre v bazo.** Zgodovina mora ostati iz enega vira, sicer
`backtest` in `ocena` primerjata dve merili in tega ne vesta. Ta modul je
samo za prikaz, na zahtevo, in ob vsaki napaki molči.

Trije podatki, brez katerih se ta vir ne da uporabiti (vsi izmerjeni):

* **Njihov `trip_id` ni vožnja, ampak vzorec proge.** 19 163 naših voženj LPP
  ima le 85 različnih tretjih komponent id-ja, najpogostejša 993-krat. Zato
  `arrivals-on-route` vrne prihode **vseh** vozil na tem vzorcu.
* **Pravo vozilo izbere `vehicle_id`**, ki je v obeh virih iz istega prostora
  (preverjeno: naš `vehicle_now.vehicle_id` se pojavi v njihovem odgovoru).
  Brez žive lege torej ne vemo, katero vozilo je naše — in takrat molčimo.
* **Postanke spajamo po koordinati, ne po vrstnem redu.** Postajališča so ista
  do 0,0 m (704 od 714 se ujema na manj kot 5 m), vzorec pa je lahko daljši od
  naše vožnje in takrat bi vrstni red tiho zamaknil vse postanke.
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime

import requests

from . import config, db, geo, stats
from .naslovi import fold

_URL = "https://data.lpp.si/api/route/arrivals-on-route"

# Predpomnilnik po VZORCU, ne po vozilu: dva potnika, ki gledata dva avtobusa
# iste linije, sprozita eno zahtevo. Vsebina se spremeni na 10-30 s.
_TTL_S = 10
_predpomnilnik: dict[str, tuple[float, list]] = {}

# Kratka meja namenoma: to je postranski vir na poti do odgovora, ki ga potnik
# ceka. Boljse je odgovoriti brez njega kot cakati nanj.
_TIMEOUT_S = 2.0

# Koliko metrov se sme postajalisce razlikovati, da je se isto. Merjeno:
# mediana razlike je 0,0 m, 704 od 714 pod 5 m -- 25 m je zato ohlapno dovolj
# in vseeno prevec tesno, da bi zamenjalo dve sosednji postajalisci.
_UJEMANJE_M = 25


def _vzorec(trip_id: str) -> str | None:
    """Tretja komponenta našega trojnega id-ja je njihov `trip-id`."""
    deli = trip_id.split("|")
    return deli[2] if len(deli) == 3 else None


def _prinesi(vzorec: str) -> list | None:
    zdaj = time.monotonic()
    v = _predpomnilnik.get(vzorec)
    if v and zdaj - v[0] < _TTL_S:
        return v[1]
    try:
        r = requests.get(_URL, params={"trip-id": vzorec}, timeout=_TIMEOUT_S)
        r.raise_for_status()
        podatki = r.json().get("data") or []
    except Exception:
        # Tih izpad je namenoma: brez tega vira stran deluje naprej z derp.si.
        return None
    _predpomnilnik[vzorec] = (zdaj, podatki)
    return podatki


def eta_po_postankih(conn: sqlite3.Connection, trip_id: str,
                     vehicle_id: str | None) -> dict[int, int] | None:
    """`{stop_seq: eta_min}` za TO vozilo, ali `None`, če vira ni.

    `eta_min` je cela minuta do prihoda, kot jo pove LPP.
    """
    if not config.LPP_ZIVO or not vehicle_id:
        return None
    vzorec = _vzorec(trip_id)
    if not vzorec:
        return None
    podatki = _prinesi(vzorec)
    if not podatki:
        return None

    nasi = [dict(r) for r in conn.execute(
        "SELECT s.stop_seq, st.lat, st.lon FROM sched s "
        "JOIN station st ON st.stop_id = s.stop_id "
        "WHERE s.trip_id = ? ORDER BY s.stop_seq", (trip_id,))]
    if not nasi:
        return None

    out: dict[int, int] = {}
    for postaja in podatki:
        prihodi = [a for a in postaja.get("arrivals", [])
                   if a.get("vehicle_id") == vehicle_id]
        if not prihodi:
            continue
        lat, lon = postaja.get("latitude"), postaja.get("longitude")
        if lat is None or lon is None:
            continue
        naj, najd = None, _UJEMANJE_M
        for n in nasi:
            d = geo.haversine(lat, lon, n["lat"], n["lon"])
            if d < najd:
                najd, naj = d, n
        if naj is not None:
            # Isto postajalisce je lahko na vozji dvakrat (krozna linija);
            # velja PRVI prihod, ker je to tisti, ki potnika zanima.
            out.setdefault(naj["stop_seq"], min(a["eta_min"] for a in prihodi))
    return out or None


# ---------------------------------------------------------------------------
# Tabla za linije, ki vozijo mimo voznega reda
#
# LPP-jev živi sistem vozi vožnje pod id-ji, ki jih objavljeni vozni red nima:
# 1. 10. 2026 17 % voženj šestih linij, 2. 10. (kolesarsko prvenstvo, zaprta
# Slovenska) 38 od 44 voženj linije 1. Feed zamude ni mogel pripeti nobeni,
# in tabla je na Tivoliju kazala
# 15 odhodov linije 1 na uro „brez podatka“, LPP-jev zaslon na istem
# postajališču pa prihode čez 3, 4, 31, 38, 51 in 58 min. Zato za take linije
# tabla pokaže tisto, kar pokaže LPP, in ne vozni red, ki mu nobena živa
# vožnja ne pripada.

_POSTAJE_URL = "https://data.lpp.si/api/station/station-details"
_PRIHODI_URL = "https://data.lpp.si/api/station/arrival"

#: Linija vozi mimo voznega reda, kadar ima feed vsaj toliko njenih voženj,
#: ki jih vozni red ne pozna, IN tolikšen delež. 2. 10. 2026 ob 15h: linija 1
#: 38 od 44, 27 4 od 21, 11 3 od 26. Liniji z eno samo tujo vožnjo bi menjava
#: vzela meritve vseh drugih.
BREZ_VOZNJE_VSAJ = 3
BREZ_VOZNJE_DELEZ = 0.2

#: Starejši podatek zajema ne velja: feed se je morda vmes popravil.
BREZ_VOZNJE_SVEZE_S = 600

#: Vrste prihoda po dokumentaciji LPP (`data.lpp.si/doc`, polje `type`).
VRSTE = {0: "napoved", 1: "po načrtu", 2: "prihaja", 3: "obvoz"}

#: Seznam postajališč se spreminja z voznim redom, ne s tablo.
_POSTAJE_TTL_S = 24 * 3600
#: Prihodi na postajališču se pri LPP spremenijo na 30 s (izmerjeno 7. 9. 2026).
_PRIHODI_TTL_S = 15
_postaje: tuple[float, list] | None = None
_prihodi: dict[str, tuple[float, list]] = {}


def je_brez_voznje(neznanih: int, vseh: int) -> bool:
    return neznanih >= BREZ_VOZNJE_VSAJ and vseh > 0 and neznanih / vseh >= BREZ_VOZNJE_DELEZ


def linije_brez_voznje(conn: sqlite3.Connection, zdaj: float) -> set[str]:
    """Linije, ki jih zadnji zajem kaže kot vožene mimo voznega reda."""
    try:
        zapis = json.loads(db.get_meta(conn, "lpp_linije_brez_voznje") or "{}")
    except ValueError:
        return set()
    if zdaj - (zapis.get("ts") or 0) > BREZ_VOZNJE_SVEZE_S:
        return set()
    return {ime for ime, (n, vseh) in (zapis.get("linije") or {}).items()
            if je_brez_voznje(n, vseh)}


def _get(url: str, params: dict | None, timeout: float) -> list | dict | None:
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json().get("data")
    except Exception:
        return None


def _postaje_lpp() -> list | None:
    global _postaje
    zdaj = time.monotonic()
    if _postaje and zdaj - _postaje[0] < _POSTAJE_TTL_S:
        return _postaje[1]
    podatki = _get(_POSTAJE_URL, None, _TIMEOUT_S)
    if not podatki:
        return None
    _postaje = (zdaj, podatki)
    return podatki


def _prihodi_postaje(koda: str) -> list | None:
    zdaj = time.monotonic()
    v = _prihodi.get(koda)
    if v and zdaj - v[0] < _PRIHODI_TTL_S:
        return v[1]
    podatki = _get(_PRIHODI_URL, {"station-code": koda}, _TIMEOUT_S)
    if podatki is None:
        return None
    seznam = (podatki.get("arrivals") or []) if isinstance(podatki, dict) else []
    _prihodi[koda] = (zdaj, seznam)
    return seznam


def kode_postaj(nasa: list[dict], lpp: list[dict]) -> dict[str, str]:
    """LPP-jeva koda postajališča -> naš `stop_id`, po koordinati.

    Isto ujemanje kot pri prihodih na vožnji: postajališča se ujemajo na
    0,0 m, obe strani ceste pa sta narazen 40 m in več (Tivoli 801011 in
    801012: 45 m).
    """
    out: dict[str, str] = {}
    for n in nasa:
        naj, najd = None, _UJEMANJE_M
        for p in lpp:
            if p.get("latitude") is None or p.get("longitude") is None:
                continue
            d = geo.haversine(n["lat"], n["lon"], p["latitude"], p["longitude"])
            if d < najd:
                najd, naj = d, p
        if naj is not None and naj.get("ref_id"):
            out.setdefault(str(naj["ref_id"]), n["stop_id"])
    return out


def vrstice_prihodov(prihodi: list[dict], stop_id: str, linije: set[str],
                     zdaj: float, dan: str, odhodi: bool, postaja: str) -> list[dict]:
    """Prihodi z LPP-jevega zaslona kot vrstice table.

    Vrstica nima `trip_id`: vožnje, ki ji pripada, v voznem redu ni, in
    povezava na vožnjo iz voznega reda bi odprla napačno. Ura je LPP-jeva
    `eta_min` (cela minuta), zato ni ne zamude ne voznoredne ure.
    """
    out = []
    domaca = fold(postaja)
    for a in prihodi:
        linija = str(a.get("route_name") or "")
        if linija not in linije or a.get("depot") or a.get("eta_min") is None:
            continue
        ime = a.get("trip_name") or ""
        konec = (a.get("stations") or {}).get("arrival") or ime.rpartition(" - ")[2]
        zacetek = (a.get("stations") or {}).get("departure") or ime.partition(" - ")[0]
        # Na končni se z avtobusom nikamor ne pelje, na izhodišču nihče ne pride.
        if fold(konec if odhodi else zacetek) == domaca:
            continue
        kdaj = int(zdaj) + int(a["eta_min"]) * 60
        ura = datetime.fromtimestamp(kdaj, stats.TZ).isoformat()
        out.append({
            "train_no": linija, "headsign": ime, "towards": konec if odhodi else zacetek,
            "mode": "bus", "agency": "lpp", "network": "avtobus",
            "stop_id": stop_id, "service_date": dan,
            "t_s": kdaj - stats.polnoc(dan), "sched": ura, "expected": ura,
            "delay_s": None, "delay_kind": None, "delay_from": None, "zamuda": None,
            "typical": None, "is_terminus": False, "is_origin": False,
            "lpp_vrsta": VRSTE.get(a.get("type"), "napoved"),
        })
    return out


def na_tablo(conn: sqlite3.Connection, rows: list[dict], zdaj: datetime,
             odhodi: bool, postaja: str) -> tuple[list[dict], list[str]]:
    """Današnjo tablo za linije, ki vozijo mimo voznega reda, napolni z LPP.

    Vrne (vrstice, zamenjane linije). Ob kakršni koli napaki vira tabla
    ostane, kot je -- vozni red je slabši odgovor, a ni prazen.

    Vrstice voznega reda teh linij gredo ven le do zadnjega LPP-jevega
    prihoda: dlje LPP ne napove, in vozni red je za tisti čas edino, kar
    imamo -- na Tivoliju 2. 10. ob 15h se je z LPP-jevim ujemal do minute,
    1. 10. na liniji 14 pa le v 47 od 66 odhodov.
    """
    if not config.LPP_ZIVO:
        return rows, []
    linije = linije_brez_voznje(conn, zdaj.timestamp()) & {
        r["train_no"] for r in rows if r.get("agency") == "lpp"}
    if not linije:
        return rows, []
    sids = sorted({r["stop_id"] for r in rows
                   if r.get("agency") == "lpp" and r["train_no"] in linije})
    postaje = _postaje_lpp()
    if not postaje or not sids:
        return rows, []
    nasa = [dict(r) for r in conn.execute(
        f"SELECT stop_id, lat, lon FROM station WHERE stop_id IN ({','.join('?' * len(sids))}) "
        "AND lat IS NOT NULL", sids)]
    kode = kode_postaj(nasa, postaje)
    if not kode:
        return rows, []
    dan = zdaj.date().isoformat()
    novi: list[dict] = []
    for koda, sid in kode.items():
        prihodi = _prihodi_postaje(koda)
        if prihodi is None:
            return rows, []
        novi += vrstice_prihodov(prihodi, sid, linije, zdaj.timestamp(), dan, odhodi, postaja)
    # Smer z istim imenom kot v voznem redu: LPP piše „DOLGI MOST P+R“, naš
    # vozni red pa končno postajališče „D. MOST P+R“ -- dve imeni za isto smer
    # na isti tabli bi bili videti kot dve liniji.
    imena = {(r["train_no"], r.get("headsign")): r.get("towards") for r in rows}
    for r in novi:
        r["towards"] = imena.get((r["train_no"], r["headsign"])) or r["towards"]
    # Po epohi, ne po `t_s`: po polnoči so na tabli tudi včerajšnje vožnje,
    # njihove sekunde pa štejejo od druge polnoči.
    def kdaj(r):
        return stats.polnoc(r["service_date"]) + r["t_s"]

    meja: dict[str, int] = {}
    for r in novi:
        meja[r["train_no"]] = max(meja.get(r["train_no"], 0), kdaj(r))
    if not meja:
        return rows, []
    ostane = [r for r in rows
              if not (r.get("agency") == "lpp" and r["train_no"] in meja
                      and kdaj(r) <= meja[r["train_no"]])]
    return ostane + novi, sorted(meja)
