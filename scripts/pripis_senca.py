#!/usr/bin/env python
"""Senca pripisa vozila na vožnjo (`kajros/pripis.py`). V `run` ne piše ničesar.

Trije koraki, ista merila za vsako ponovitev (`docs/OPAZOVANO.md`, del 4):

  vzorci    posname Marpromov API: 1 + največ 7 branj na krog, krog 30 s
  zivo      ponovi `marprom.razresi` na posnetih krogih in primerja predloge
  simuliraj vozilu z znano vožnjo (`lega`) vožnjo skrije, primerja predlog, vsi viri

Baza samo za branje: `file:/var/lib/kajros/kajros.sqlite?mode=ro`, `nice -n 19`.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import gzip
import hashlib
import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kajros import collector, marprom, pripis, stats, straza  # noqa: E402
from kajros.pripis import Napredek  # noqa: E402

TZ = collector.TZ
MP = marprom.MP
#: Prvih toliko sekund vzorca se ne šteje: prihode beremo po postajališčih, vožnjo
#: dobi vsako vozilo šele v nekaj krogih in zasedene še niso znane.
OGREVANJE_S = 1200
#: Vožnja s časom toliko pred zdaj ni vožnja, ki jo vozilo pelje: Marprom je
#: prihod zanjo dal, ko je vozilo že za postajališčem (bus 148 ob 16:02, vožnja 17:30).
SPORNO_MIN = -30


def _baza(pot: str) -> sqlite3.Connection:
    conn = sqlite3.connect(pot, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------------- posnetek

def vzorci(izhod: str, ure: float) -> None:
    bralnik = marprom.Bralnik()
    konec = time.time() + 3600 * ure
    nazadnje: dict[int, float] = {}
    polj_v = ("DeviceId", "BusCode", "RouteId", "LineId", "Lat", "Lon", "NextStopPointId",
              "ETA", "Predicted")
    polj_p = ("LineId", "ArrivalTime", "ETAMin", "DelayMin", "BusCode")
    with gzip.open(izhod, "at", compresslevel=6) as f:
        while time.time() < konec:
            z = time.time()
            try:
                vozila = bralnik._get("GetActiveDeviceDetails").get("Vehicles") or []
                postaje = {v.get("NextStopPointId") for v in vozila if v.get("NextStopPointId")}
                prihodi = {}
                for p in sorted(postaje, key=lambda x: nazadnje.get(x, 0))[:7]:
                    prihodi[str(p)] = [{k: a.get(k) for k in polj_p}
                                       for a in bralnik.prihodi(str(p))]
                    nazadnje[p] = time.time()
                f.write(json.dumps({"ts": z, "v": [{k: x.get(k) for k in polj_v} for x in vozila],
                                    "p": prihodi}, separators=(",", ":")) + "\n")
                f.flush()
            except Exception as exc:    # noqa: BLE001 -- vir ni naš, krog izpustimo
                print(f"krog: {exc}", flush=True)
            time.sleep(max(1.0, 30 - (time.time() - z)))


def _krogi(poti: list[str]):
    """Tudi nedokončan posnetek: gzip brez konca da, kar je zapisano."""
    for pot in poti:
        try:
            with gzip.open(pot, "rt") as f:
                for vrstica in f:
                    yield json.loads(vrstica)
        except EOFError:
            pass


# ------------------------------------------------------------------- ponovitev

def _casi(idx: dict) -> dict[tuple[str, str], float]:
    return {(k[1], v.trip_id): v.cas for k, vs in idx.items() for v in vs}


def zivo(pot: str, poti: list[str], postajalisca: dict) -> None:
    """Ponovitev obhoda Marproma s pravimi `potrebuje`/`razresi` in predlog ob vsakem krogu."""
    conn = _baza(pot)
    stanje: dict[str, marprom.Vozilo] = {}
    napredek = Napredek()
    sosedi = marprom.sosedi_iz(postajalisca)
    zapisi = []
    prej: dict[str, set] = collections.defaultdict(set)
    videne: set[tuple[str, str]] = set()
    pripisi: dict[str, list] = collections.defaultdict(list)
    razlogi: dict[str, str] = {}
    idx_dan: dict = {}
    agencija = marprom.gtfs.MARPROM_AGENCIJA
    postanki = marprom._postanki(conn)
    okna = collector._rail_trip_windows(conn)
    prvi = None
    for r in _krogi(poti):
        zdaj = r["ts"]
        prvi = prvi or zdaj
        dan = datetime.fromtimestamp(zdaj, TZ).date().isoformat()
        if dan not in idx_dan:
            idx_dan[dan] = (marprom.indeks(conn, zdaj), pripis.indeks(conn, zdaj, agencija))
        idx_ura, idx = idx_dan[dan]
        vozila = marprom.razberi({"Vehicles": r["v"]})
        vidni = {v["naprava"] for v in vozila}
        napredek.pozabi(vidni)
        for k in [k for k in stanje if k not in vidni]:
            del stanje[k]
        zasedene = {(s.trip_id, s.dan): k for k, s in stanje.items() if s.trip_id}
        for v in vozila:
            s = stanje.setdefault(v["naprava"], marprom.Vozilo())
            prihodi = r["p"].get(v["naslednja"])
            if prihodi is None or not v["naslednja"]:
                continue        # ta krog nismo brali: vožnja ostane, kot je
            if not marprom.potrebuje(s, v, zdaj, postanki, okna, sosedi):
                continue
            s.poskus_ts = zdaj
            if s.trip_id:
                zasedene.pop((s.trip_id, s.dan), None)
            najdena, zakaj, _ = marprom.razresi(v, prihodi, idx_ura, zasedene, sosedi)
            razlogi[v["naprava"]] = zakaj
            if najdena is None:
                s.trip_id = s.dan = None
                continue
            s.trip_id, s.dan, s.seq = najdena
            s.linija, s.varianta, s.razreseno_ts = v["linija"], v["varianta"], zdaj
            zasedene[najdena[:2]] = v["naprava"]
            pripisi[v["naprava"]].append((zdaj, najdena[0], v["varianta"]))
            prej[v["naprava"]].add(najdena[:2])
        videne |= {(s.trip_id, s.dan) for s in stanje.values() if s.trip_id}
        for v in vozila:
            if not v["linija"]:
                continue
            s = stanje[v["naprava"]]
            gre = napredek.opazi(v["naprava"], v["varianta"], v["naslednja"])
            postaje = [MP + p for p in [v["naslednja"], *sosedi.get(v["naslednja"], ())]]
            kand = pripis.kandidati(idx, MP + v["varianta"], postaje)
            # Tudi vozilo z vožnjo dobi predlog, kot da je nima: to je primerjava.
            # Svojih voženj vozilo ne more zasesti samo sebi.
            pr = pripis.predlagaj(kand, zdaj, videne - prej[v["naprava"]], gre) if v["zivo"] else None
            zapisi.append((zdaj, v["naprava"], v["varianta"], v["naslednja"], v["zivo"],
                           s.trip_id, razlogi.get(v["naprava"], ""), pr))
    _porocilo(zapisi, pripisi, idx_dan, prvi, conn)


def _porocilo(zapisi, pripisi, idx_dan, prvi, conn) -> None:
    casi: dict = {}
    for _, idx in idx_dan.values():
        casi.update(_casi(idx))

    def resnica(nap, ts, var):
        """Marpromov prihod v 30 min pred predlogom in za njim, ista varianta."""
        vrsta = [x for x in pripisi[nap] if x[2] == var and abs(x[0] - ts) <= 1800]
        pred = [x[1] for x in vrsta if x[0] <= ts]
        po = [x[1] for x in vrsta if x[0] > ts]
        return (pred[-1] if pred else None), (po[0] if po else None)

    n = collections.Counter()
    vozil_brez, vozil_par = set(), set()
    a = {"z": set(), "brez": set(), "vzorcev_z": 0, "vzorcev_brez": 0, "voznje": set()}
    b = {"z": set(), "brez": set(), "vzorcev_z": 0, "vzorcev_brez": 0, "voznje": set()}
    for ts, nap, var, sto, ziv, trip, razlog, pr in zapisi:
        ima = bool(trip)
        par = bool(pr and pr.voznja and not ima)
        for x, je in ((a, ima), (b, ima or par)):
            x["z" if je else "brez"].add(nap)
            x["vzorcev_z" if je else "vzorcev_brez"] += 1
        if ima:
            a["voznje"].add(trip)
            b["voznje"].add(trip)
        elif par:
            b["voznje"].add(pr.voznja.trip_id)
        if ts < prvi + OGREVANJE_S or not ziv:
            continue
        predlog = pr.voznja.trip_id if pr.voznja else None
        if ima:
            c = casi.get((MP + sto, trip))
            if c is None:
                n["z zastarela"] += 1       # ponovitev: prihodov tega kroga nismo brali
            elif (ts - c) / 60 < SPORNO_MIN:
                n["z sporna"] += 1
                n["z sporna s predlogom"] += predlog is not None
            elif predlog is None:
                n[f"z brez {pr.razlog}"] += 1
            elif predlog == trip:
                n["z prav"] += 1
            else:
                n["z narobe"] += 1
        elif razlog:    # brez `razlog` vožnje še ni iskal nihče
            n["brez vozil_vzorcev"] += 1
            vozil_brez.add(nap)
            n[f"brez razlog {razlog}"] += 1
            if predlog is None:
                n[f"brez brez {pr.razlog}"] += 1
                continue
            vozil_par.add(nap)
            pred, po = resnica(nap, ts, var)
            if po == predlog:
                n["brez prav po"] += 1
            elif pred == predlog:
                n["brez prav prej"] += 1
            elif po is None and pred is None:
                n["brez nepreverjeno"] += 1
            else:
                n["brez narobe"] += 1
    for k in sorted(n):
        print(f"{k:32} {n[k]}")
    print(f"vozil brez vožnje {len(vozil_brez)}, od teh s predlogom {len(vozil_par)}")
    dan = zapisi[0] and datetime.fromtimestamp(zapisi[0][0], TZ).date().isoformat()
    nacrt = conn.execute(
        "SELECT COUNT(*) FROM trip t JOIN service_day d ON d.service_id = t.service_id "
        "WHERE d.date = ? AND t.agency = ?", (dan, marprom.gtfs.MARPROM_AGENCIJA)).fetchone()[0]

    def vrstica(x):
        return {"nacrt": nacrt, "z_lego": len(x["voznje"]),
                "vozila": {"marprom": {"z": len(x["z"]), "brez": len(x["brez"]),
                                       "vzorcev_z": x["vzorcev_z"],
                                       "vzorcev_brez": x["vzorcev_brez"]}}}
    print(straza.izpis_primerjave("zdaj", "s predlogi", straza.primerjaj(
        {"marprom": vrstica(a)}, {"marprom": vrstica(b)})))


# ------------------------------------------------------------------ simulacija

def _skrito(s: str, delez: float) -> bool:
    return delez > 0 and int(hashlib.md5(s.encode()).hexdigest()[:8], 16) / 2**32 < delez


def simuliraj(pot: str, dan: str, skrij: list[float]) -> None:
    conn = _baza(pot)
    agencije = {}
    vlak = {}
    for r in conn.execute("SELECT trip_id, agency, shape_id, route_id, train_no, start_s FROM trip "
                          "WHERE trip_id IN (SELECT DISTINCT trip_id FROM lega WHERE service_date = ?)",
                          (dan,)):
        agencije[r[0]] = r[1]
        vlak[r[0]] = (r[2], r[3], r[4])
    postanki: dict[str, list] = collections.defaultdict(list)
    for t, q, st in conn.execute(
            "SELECT s.trip_id, s.stop_seq, s.stop_id FROM sched s WHERE s.trip_id IN "
            "(SELECT DISTINCT trip_id FROM lega WHERE service_date = ?) "
            "ORDER BY s.trip_id, s.stop_seq", (dan,)):
        postanki[t].append((q, st))
    prehodi: dict[str, list] = collections.defaultdict(list)
    for t, q, ts in conn.execute("SELECT trip_id, stop_seq, prehod_ts FROM gps_prehod "
                                 "WHERE service_date = ? ORDER BY prehod_ts", (dan,)):
        prehodi[t].append((ts, q))
    prisotna: dict[str, dict] = collections.defaultdict(dict)
    vzorec = []
    zadnji = {}
    for t, vz, ts in conn.execute("SELECT trip_id, vozilo, ts FROM lega WHERE service_date = ?",
                                  (dan,)):
        k = (t, vz)
        prisotna[t].setdefault(vz, ts)
        if zadnji.get(k) != ts // 120:      # en vzorec na 2 min, kot je krog prihodov
            zadnji[k] = ts // 120
            vzorec.append((t, vz, ts))
    polnoc = stats.polnoc(dan)
    indeksi = {a: pripis.indeks(conn, polnoc + 43200, a)
               for a in {x for x in agencije.values() if x}}
    print(f"{dan}, vzorcev {len(vzorec)}")
    for delez in skrij:
        izid = collections.defaultdict(collections.Counter)
        for t, vz, ts in vzorec:
            a = agencije.get(t)
            if a is None or not postanki.get(t):
                continue
            pv = prehodi.get(t, [])
            i = bisect.bisect_right(pv, (ts, 10**9))
            zadnji_seq = pv[i - 1][1] if i else None
            naslednji = next((p for p in postanki[t]
                              if zadnji_seq is None or p[0] > zadnji_seq), None)
            if naslednji is None:
                continue
            kand = [k for k in indeksi[a].get((vlak[t][0], naslednji[1]), ()) if k.dan == dan]
            # Druga vozila, ki so na kandidatu že bila. Del jih skrijemo: v živo
            # tudi niso vsa pripeta.
            zas = {(k.trip_id, k.dan) for k in kand
                   if any(od <= ts and (k.trip_id, v2) != (t, vz)
                          and not _skrito(f"{k.trip_id}{v2}", delez)
                          for v2, od in prisotna.get(k.trip_id, {}).items())}
            pr = pripis.predlagaj(kand, ts, zas, zadnji_seq is not None)
            r = izid[a]
            r["n"] += 1
            if pr.voznja is None:
                r[pr.razlog] += 1
            elif pr.voznja.trip_id == t:
                r["prav"] += 1
            else:
                r["narobe"] += 1
                prava = next((k for k in kand if k.trip_id == t), None)
                r["dvojnik"] += bool(
                    prava and vlak.get(pr.voznja.trip_id, (0, 0, 0))[2] == vlak[t][2]
                    and abs(prava.cas - pr.voznja.cas) <= 60)
        print(f"skritih drugih vozil {delez:.0%}")
        for a in sorted(izid):
            r = izid[a]
            predlogov = r["prav"] + r["narobe"]
            print(f"  {a:8} n={r['n']:7} prav={r['prav']:7} ({100 * r['prav'] / r['n']:5.1f} %) "
                  f"narobe={r['narobe']:5} ({100 * r['narobe'] / max(predlogov, 1):5.2f} % predlogov, "
                  f"dvojnikov {r['dvojnik']}) miruje={r['miruje']} ni_prosta={r['ni_prosta']} "
                  f"vec={r['vec']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = p.add_subparsers(dest="ukaz", required=True)
    v = sub.add_parser("vzorci")
    v.add_argument("izhod")
    v.add_argument("--ure", type=float, default=4)
    z = sub.add_parser("zivo")
    z.add_argument("--baza", required=True)
    z.add_argument("--postajalisca", help="JSON iz Bralnik.postajalisca(); sicer z API-ja")
    z.add_argument("vzorci", nargs="+")
    s = sub.add_parser("simuliraj")
    s.add_argument("--baza", required=True)
    s.add_argument("--dan", required=True)
    s.add_argument("--skrij", type=float, nargs="+", default=[0.0, 0.25, 1.0])
    a = p.parse_args()
    if a.ukaz == "vzorci":
        vzorci(a.izhod, a.ure)
    elif a.ukaz == "zivo":
        zivo(a.baza, a.vzorci, json.loads(Path(a.postajalisca).read_text()) if a.postajalisca
             else marprom.Bralnik().postajalisca())
    else:
        simuliraj(a.baza, a.dan, a.skrij)


if __name__ == "__main__":
    main()
