"""Zamuda na dolgem odseku iz lege: kaj vemo, preden vozilo pride do postanka.

Pri Arrivi, Nomagu in AP MS zamudo meri prehod postanka (`iz_lege`, `prehod.py`).
Na odseku, ki po voznem redu traja 15 min ali več, okno zato kaže staro meritev:
na odsekih nad 30 min se zamuda do naslednjega postanka v 45 % primerov spremeni
za več kot 5 min (`docs/presoja/2026-10-31-napovedi.md`, razdelek 2). Vozni red ima
na avtocesti rezervo, avtobus jo porabi in pride prej, kot kaže okno.

Lega pove, kje je vozilo, ne koliko zamuja: vozni red za sredino odseka ne obstaja.
Dve oceni zamude na naslednjem postanku:

* **profil**: zdaj + običajni ostanek časa od te točke do prehoda naslednjega
  postanka (mediana dni, `odsek_profil`). Ne rabi predpostavke o hitrosti.
* **razdalja**: vozni red, razporejen po razdalji po trasi. Sredi odseka je v
  mestu videti pozno, na avtocesti zgodaj (odklon od +2 do -2 min), zato ga
  velja šele od `RAZDALJA_OD` odseka naprej in le, kadar profila ni.

Ponovitev na `lega` 21. 10.--3. 11. 2026, izpuščen dan, 62 228 vzorcev, MAE proti
zamudi na naslednjem postanku: prenos 4,08 min, razdalja 3,09; kjer je profil
(29 098) prenos 3,27, profil 1,35, v 2 min 38 % -> 83 %. Skripta
`docs/presoja/dolg_odsek/ponovitev.py`.

**Zdaj je to senca**: `ocena.snapshot` zapiše `lega_s` in `ours_lega_s` ob prikaz,
prikaz je ne bere. Meja meritve se ne premakne, nič ne gre v `run`.
"""
from __future__ import annotations

import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from . import collector, config, db, deljenje, stats

TZ = collector.TZ

#: Odsek po voznem redu, od katerega okno kaže staro meritev.
DOLG_ODSEK_S = 900
#: Krajši odsek po trasi je postanek z dolgim čakanjem, ne vožnja.
NAJMANJ_M = 1000
#: Dolžina odseka v ključu: ista imena po drugi cesti so drug odsek.
KORAK_M = 500
#: Odsek razdeljen na toliko kosov (5 %).
KOSOV = 20
#: Lega dlje od trase ni na tem odseku (obvoz, napaka GPS).
ODMIK_M = 300
#: Med zaporednima vzorcema za profil. Lege so na 10 s, sosednji povedo isto.
VZOREC_S = 60
#: Profil velja od toliko dni naprej, kot model zgodovine (`MIN_PREDICT_SAMPLES`).
NAJMANJ_DNI = 3
#: Toliko dni hrani `odsek_profil`: vozni red in dela na cesti se spreminjajo.
PROFIL_DNI = 28
#: Razdalja velja od tega deleža odseka: pod njim je slabša od prenosa
#: (0--15 %: MAE 4,08 proti 3,82; 15--30 %: 3,91 proti 3,92; 30--50 %: 3,45 proti 4,23).
RAZDALJA_OD = 0.3

_profil: dict[tuple, float] = {}
_profil_znacka: str | None = None


def _cas_odhoda(p: dict) -> int | None:
    return p["dep_s"] if p["dep_s"] is not None else p["arr_s"]


def _cas_prihoda(p: dict) -> int | None:
    return p["arr_s"] if p["arr_s"] is not None else p["dep_s"]


def _kljuc(pa: dict, pb: dict) -> tuple[str, str, int]:
    return pa["name"], pb["name"], round((pb["along"] - pa["along"]) / KORAK_M)


def _dolg(pa: dict, pb: dict) -> bool:
    return (_cas_prihoda(pb) - _cas_odhoda(pa) >= DOLG_ODSEK_S
            and pb["along"] - pa["along"] >= NAJMANJ_M)


def _kos(delez: float) -> int:
    return min(int(delez * KOSOV), KOSOV - 1)


def _delez(pa: dict, pb: dict, along: float) -> float:
    return max(0.0, min(1.0, (along - pa["along"]) / (pb["along"] - pa["along"])))


def _voznje_z_dolgim_odsekom(conn: sqlite3.Connection) -> set[str]:
    """Pregled po voznem redu, da traso gradimo le, kjer jo rabimo (~1 od 10)."""
    pr = ",".join("?" * len(config.NAP_PREVOZNIKI))
    return {r[0] for r in conn.execute(
        f"SELECT DISTINCT trip_id FROM ("
        f"  SELECT s.trip_id, COALESCE(s.dep_s, s.arr_s) AS t, "
        f"         LEAD(COALESCE(s.arr_s, s.dep_s)) OVER "
        f"           (PARTITION BY s.trip_id ORDER BY s.stop_seq) AS naslednji "
        f"  FROM sched s JOIN trip t USING (trip_id) WHERE t.agency IN ({pr})"
        f") WHERE naslednji - t >= ?", (*sorted(config.NAP_PREVOZNIKI), DOLG_ODSEK_S))}


def izracun_dne(conn: sqlite3.Connection, dan: str, dolge: set[str]) -> dict[tuple, list[int]]:
    """(ključ odseka, kos) -> ostanek časa do prehoda naslednjega postanka."""
    prehodi: dict[str, dict[int, int]] = defaultdict(dict)
    for tid, seq, ts in conn.execute(
            "SELECT trip_id, stop_seq, prehod_ts FROM gps_prehod WHERE service_date = ?", (dan,)):
        if tid in dolge:
            prehodi[tid][seq] = ts
    out: dict[tuple, list[int]] = defaultdict(list)
    for tid, po_seq in prehodi.items():
        v = deljenje.voznja(conn, tid)
        if v is None:
            continue
        for pa, pb in zip(v.postanki, v.postanki[1:]):
            od, do = po_seq.get(pa["stop_seq"]), po_seq.get(pb["stop_seq"])
            if od is None or do is None or not _dolg(pa, pb):
                continue
            kljuc, zadnji = _kljuc(pa, pb), 0
            for ts, lat, lon in conn.execute(
                    "SELECT ts, lat, lon FROM lega WHERE service_date = ? AND trip_id = ? "
                    "AND ts > ? AND ts < ? ORDER BY ts", (dan, tid, od, do)):
                if ts - zadnji < VZOREC_S:
                    continue
                along, odmik = v.trasa.projiciraj(lat, lon, od_m=pa["along"] - ODMIK_M,
                                                  do_m=pb["along"] + ODMIK_M)
                if odmik <= ODMIK_M:
                    zadnji = ts
                    out[(*kljuc, _kos(_delez(pa, pb, along)))].append(do - ts)
    return out


def dopolni(conn: sqlite3.Connection, zdaj: datetime | None = None) -> list[str]:
    """Dnevi od zadnjega izračuna do včeraj, ponoči. Vrne izračunane dneve.

    `lega` izgine po `prehod.HRANI_DNI`, profil ostane `PROFIL_DNI`.
    """
    zdaj = zdaj or datetime.now(TZ)
    vceraj = zdaj.date() - timedelta(days=1)
    zadnji = db.get_meta(conn, "odsek_do")
    if zadnji:
        od = datetime.fromisoformat(zadnji).date() + timedelta(days=1)
    else:
        r = conn.execute("SELECT MIN(service_date) FROM lega").fetchone()[0]
        od = datetime.fromisoformat(r).date() if r else zdaj.date()
    dnevi = []
    dolge = _voznje_z_dolgim_odsekom(conn) if od <= vceraj else set()
    while od <= vceraj:
        dan = od.isoformat()
        vrstice = [(*k, dan, round(statistics.median(xs)), len(xs))
                   for k, xs in izracun_dne(conn, dan, dolge).items()]
        conn.execute("DELETE FROM odsek_profil WHERE dan = ?", (dan,))
        conn.executemany(
            "INSERT INTO odsek_profil(od_ime, do_ime, dolzina, kos, dan, ostanek_s, n) "
            "VALUES(?,?,?,?,?,?,?)", vrstice)
        db.set_meta(conn, "odsek_do", dan)
        conn.commit()
        dnevi.append(dan)
        od += timedelta(days=1)
    if dnevi:
        meja = (zdaj.date() - timedelta(days=PROFIL_DNI)).isoformat()
        conn.execute("DELETE FROM odsek_profil WHERE dan < ?", (meja,))
        conn.commit()
    return dnevi


def profil(conn: sqlite3.Connection) -> dict[tuple, float]:
    """(ključ odseka, kos) -> običajni ostanek; v pomnilniku do novega dne."""
    global _profil, _profil_znacka
    znacka = db.get_meta(conn, "odsek_do")
    if znacka != _profil_znacka:
        dnevi: dict[tuple, list[int]] = defaultdict(list)
        for od_ime, do_ime, dolzina, kos, ostanek in conn.execute(
                "SELECT od_ime, do_ime, dolzina, kos, ostanek_s FROM odsek_profil"):
            dnevi[(od_ime, do_ime, dolzina, kos)].append(ostanek)
        _profil = {k: statistics.median(xs) for k, xs in dnevi.items() if len(xs) >= NAJMANJ_DNI}
        _profil_znacka = znacka
    return _profil


def ocena(conn: sqlite3.Connection, trip_id: str, dan: str, meja_seq: int,
          zdaj_ts: int) -> dict | None:
    """Zamuda na naslednjem postanku iz lege, sredi dolgega odseka, sicer None.

    `meja_seq` je zadnji prevoženi postanek (`stats.last_measured`). Vrne
    `{"seq", "zamuda_s", "vir", "delez"}`; `vir` = `profil` ali `razdalja`.
    """
    v = deljenje.voznja(conn, trip_id)
    if v is None or v.agency not in config.NAP_PREVOZNIKI:
        return None
    i = next((j for j, p in enumerate(v.postanki) if p["stop_seq"] == meja_seq), None)
    if i is None or i + 1 >= len(v.postanki):
        return None
    pa, pb = v.postanki[i], v.postanki[i + 1]
    if not _dolg(pa, pb):
        return None
    lega = conn.execute("SELECT lat, lon, seen_ts FROM vehicle_now WHERE trip_id = ? AND seen_ts >= ?",
                        (trip_id, zdaj_ts - collector.POSITION_FRESH_S)).fetchone()
    if lega is None:
        return None
    along, odmik = v.trasa.projiciraj(lega["lat"], lega["lon"], od_m=pa["along"] - ODMIK_M,
                                      do_m=pb["along"] + ODMIK_M)
    if odmik > ODMIK_M:
        return None
    delez = _delez(pa, pb, along)
    t_s = lega["seen_ts"] - stats.polnoc(dan)
    ostanek = profil(conn).get((*_kljuc(pa, pb), _kos(delez)))
    if ostanek is not None:
        return {"seq": pb["stop_seq"], "zamuda_s": round(t_s + ostanek - _cas_odhoda(pb)),
                "vir": "profil", "delez": round(delez, 3)}
    if delez < RAZDALJA_OD:
        return None
    t0 = _cas_odhoda(pa)
    return {"seq": pb["stop_seq"],
            "zamuda_s": round(t_s - t0 - delez * (_cas_prihoda(pb) - t0)),
            "vir": "razdalja", "delez": round(delez, 3)}
