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

import sqlite3
import time

import requests

from . import config, geo

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
