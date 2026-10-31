"""Preverbe posnetka prikaza (snap.py). Rabi: python analiza.py <imenik_posnetka> <izhod.json>

Vse iz odgovorov javnega API-ja; lega -> zamuda po trasi kot `iz_lege`.
"""
import glob
import json
import math
import os
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime

IME = {"1161": "SŽ", "1123": "Arriva", "1119": "Nomago", "1121": "AP MS",
       "1118": "LPP primestni", "lpp": "LPP mestni", "marprom": "Marprom", "kranj": "Kranj"}


def hav(a, b, c, d):
    r = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def ts(iso):
    return datetime.fromisoformat(iso).timestamp() if iso else None


def tocke(trasa):
    p = trasa.get("points") or []
    if p and isinstance(p[0][0], list):
        out = []
        for kos in p:
            out.extend(kos)
        return out
    return p


def kumulativa(pts):
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + hav(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]))
    return c


def kandidati(pts, cums, lat, lon, od_i=0):
    """Vse projekcije (along, off, i) na odseke od indeksa od_i naprej."""
    k = math.cos(math.radians(lat))
    out = []
    for i in range(od_i, len(pts) - 1):
        ay, ax = pts[i]
        by, bx = pts[i + 1]
        vx, vy = (bx - ax) * k, by - ay
        wx, wy = (lon - ax) * k, lat - ay
        l2 = vx * vx + vy * vy
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / l2))
        off = hav(lat, lon, ay + t * (by - ay), ax + t * (bx - ax))
        out.append((cums[i] + t * (cums[i + 1] - cums[i]), off, i))
    return out


def postanki_na_trasi(pts, cums, stops):
    """Monotona projekcija postankov: vsak naslednji ne pred prejšnjim."""
    along, prej_i = [], 0
    for s in stops:
        c = kandidati(pts, cums, s["lat"], s["lon"], max(0, prej_i - 3))
        if not c:
            along.append(None)
            continue
        a, off, i = min(c, key=lambda x: x[1])
        if off > 150:
            along.append(None)
            continue
        along.append(a)
        prej_i = i
    return along


def gps_zamuda(run, veh, trasa):
    """Zamuda iz lege: čas lege minus vozni red na tisti točki trase."""
    pts = tocke(trasa)
    if len(pts) < 2:
        return {"razlog": "brez trase"}
    cums = kumulativa(pts)
    stops = run["stops"]
    al = postanki_na_trasi(pts, cums, stops)
    if sum(a is not None for a in al) < 0.8 * len(al):
        return {"razlog": "postanki niso na trasi"}
    c = [x for x in kandidati(pts, cums, veh["lat"], veh["lon"]) if x[1] <= 80]
    if not c:
        return {"razlog": "vozilo > 80 m od trase"}
    # Krožne / tja-nazaj trase: več mest blizu. Loči lokalne minimume po dolžini.
    c.sort(key=lambda x: x[0])
    skupine, zadnji = [], None
    for a, off, i in c:
        if zadnji is None or a - zadnji > 250:
            skupine.append([a, off])
        elif off < skupine[-1][1]:
            skupine[-1] = [a, off]
        zadnji = a
    if len(skupine) > 1:
        # Dvoumno: izberi po času voznega reda najbližje (brez prikazane zamude,
        # da preverba ne sledi temu, kar preverja), sicer zavrzi.
        return {"razlog": "dvoumna lega na trasi", "n": len(skupine)}
    av = skupine[0][0]
    t = veh["seen_ts"]
    # Kje med postanki
    pari = [(j, al[j]) for j in range(len(al)) if al[j] is not None]
    if av < pari[0][1] - 60:
        s0 = stops[pari[0][0]]
        dep0 = ts(s0["sched_dep"] or s0["sched_arr"])
        return {"pred_zacetkom": True, "along": av, "naslednji_i": pari[0][0],
                "spodnja_meja_s": t - dep0}
    if av > pari[-1][1] + 60:
        return {"razlog": "za ciljem", "along": av}
    for (j1, a1), (j2, a2) in zip(pari, pari[1:]):
        if a1 - 30 <= av <= a2 + 30 or (av >= a1 and av <= a2):
            if av > a2 + 30:
                continue
            s1, s2 = stops[j1], stops[j2]
            t1 = ts(s1["sched_dep"] or s1["sched_arr"])
            t2 = ts(s2["sched_arr"] or s2["sched_dep"])
            if a2 - a1 < 1:
                f = 0.0
            else:
                f = max(0.0, min(1.0, (av - a1) / (a2 - a1)))
            na = None
            if abs(av - a1) < 30:
                na = j1
            elif abs(av - a2) < 30:
                na = j2
            return {"along": av, "prejsnji_i": j1, "naslednji_i": j2, "na_postanku_i": na,
                    "zamuda_s": t - (t1 + f * (t2 - t1)), "f": f,
                    "along_post": al}
    return {"razlog": "ni odseka"}


def zamuda(s):
    z = s.get("zamuda")
    return z if z else None


def ura(s):
    """Prikazana ura: vozni red + zaokrožena minuta (oznake.md)."""
    z = zamuda(s)
    sched = s.get("sched_dep") or s.get("sched_arr")
    if not z or not sched:
        return None
    return ts(sched) + z["min"] * 60


def povezava(run):
    no = run["train_no"]
    pot = "train" if run.get("network") == "zeleznica" else "bus"
    return (f"/app/{pot}/{urllib.parse.quote(no)}"
            + (f"?trip={urllib.parse.quote(run['trip_id'], safe='')}" if pot == "bus" else ""))


def main():
    imenik, izhod = sys.argv[1], sys.argv[2]
    krogi = sorted(glob.glob(os.path.join(imenik, "krog*.json")))
    trase = {}
    for f in glob.glob(os.path.join(imenik, "trase", "*.json")):
        tid = urllib.parse.unquote(os.path.basename(f)[:-5])
        trase[tid] = json.load(open(f))
    R = defaultdict(list)          # vrsta -> primeri
    stevci = Counter()
    po_voznji = defaultdict(set)   # vrsta -> set(trip)
    for f in krogi:
        k = json.load(open(f))
        kid = os.path.basename(f)[4:6]
        runs = k["runs"]
        veh = k["veh"] or []
        live = {x["trip_id"]: x for x in (k["live_z"] or []) + (k["live_b"] or [])}
        stevci["krogov"] += 1
        stevci["voženj (okna)"] += len(runs)
        stevci["vozil z lego"] += len(veh)
        # (g) dve vozili na eni vožnji / eno vozilo na dveh
        po_trip = defaultdict(list)
        po_vozilu = defaultdict(list)
        for v in veh:
            po_trip[v.get("trip_id")].append(v)
            if v.get("vehicle_id"):
                po_vozilu[v["vehicle_id"]].append(v)
        for tid, vs in po_trip.items():
            if tid and len(vs) > 1:
                d = max(hav(a["lat"], a["lon"], b["lat"], b["lon"]) for a in vs for b in vs)
                po_voznji["g_dve_vozili"].add(tid)
                R["g_dve_vozili"].append({"krog": kid, "trip": tid, "no": vs[0]["train_no"],
                                          "agency": vs[0].get("agency"), "vozil": len(vs),
                                          "razmik_m": round(d), "vozila": [v.get("vehicle_id") for v in vs]})
        for vid, vs in po_vozilu.items():
            if len(vs) > 1:
                po_voznji["g_vozilo_na_dveh"].add(vid)
                R["g_vozilo_na_dveh"].append({"krog": kid, "vozilo": vid,
                                              "voznje": [(v["train_no"], v["trip_id"]) for v in vs]})
        vpo = {v["trip_id"]: v for v in veh if v.get("trip_id")}
        for tid, run in runs.items():
            ag = run.get("agency") or ""
            omr = run.get("network")
            stops = run["stops"]
            meja = run.get("last_measured_seq")
            byseq = {s["stop_seq"]: s for s in stops}
            stevci[f"okna {IME.get(ag, ag)}"] += 1
            # (a) ure padajo
            prej = None
            for s in stops:
                u = ura(s)
                if u is None or zamuda(s)["vrsta"] == "neskladno":
                    if u is not None:
                        stevci["neskladnih postankov"] += 1
                    continue
                if prej is not None and u < prej[1] - 60:
                    a, b = zamuda(prej[0])["vrsta"], zamuda(s)["vrsta"]
                    vrsta = f"{a} → {b}"
                    key = "a_ura_nazaj"
                    po_voznji[key].add(tid)
                    po_voznji[f"a_ura_nazaj[{IME.get(ag, ag)}|{vrsta}]"].add(tid)
                    R[key].append({"krog": kid, "agency": IME.get(ag, ag), "no": run["train_no"],
                                   "trip": tid, "od": prej[0]["name"], "do": s["name"],
                                   "seq": (prej[0]["stop_seq"], s["stop_seq"]),
                                   "pade_min": round((prej[1] - u) / 60), "vrsti": vrsta,
                                   "meja": meja, "zivi": run.get("zivi_vir"),
                                   "url": povezava(run)})
                prej = (s, u)
            # (b) zamuda nad 30 min (kar okno pokaže na meji ali prvem z zamudo)
            zm = byseq.get(meja) if meja is not None else None
            if zm is None:
                zm = next((s for s in stops if zamuda(s)), None)
            dz = zamuda(zm)["s"] if zm is not None and zamuda(zm) else None
            if run.get("trenutna"):
                dz = run["trenutna"]["zamuda"]["s"]
            # (h) zemljevid (live) proti oknu
            lv = live.get(tid)
            if lv and lv.get("zamuda") and zm is not None and zamuda(zm) and meja is not None:
                dl = lv["zamuda"]["s"]
                dw = zamuda(byseq[meja])["s"] if zamuda(byseq.get(meja, {})) else None
                if dw is not None and abs(dl - dw) >= 60 and not run.get("trenutna"):
                    po_voznji["h_zemljevid_proti_oknu"].add(tid)
                    R["h_zemljevid_proti_oknu"].append({"krog": kid, "agency": IME.get(ag, ag),
                        "no": run["train_no"], "live": dl, "live_seq": lv.get("stop_seq"),
                        "okno": dw, "meja": meja, "dt_s": run["_t"] - k["ts"],
                        "url": povezava(run)})
            v = vpo.get(tid)
            if v and v.get("delay_s") is not None and meja is not None and zamuda(byseq.get(meja, {})):
                dw = zamuda(byseq[meja])["s"]
                if abs(v["delay_s"] - dw) >= 60 and v.get("vir") != "potniki":
                    po_voznji["h_kartica_vozila_proti_oknu"].add(tid)
                    R["h_kartica_vozila_proti_oknu"].append({"krog": kid, "agency": IME.get(ag, ag),
                        "no": run["train_no"], "kartica": v["delay_s"], "kartica_seq": v.get("measured_seq"),
                        "okno": dw, "meja": meja, "url": povezava(run)})
            # (f) vozilo z lego brez zamude
            if v and v.get("delay_s") is None:
                kaj = ("brez meje, živo LPP" if run.get("zivi_vir") else
                       "brez meje, napoved prevoznika" if any(zamuda(s) for s in stops) else
                       "okno brez vsake zamude")
                po_voznji[f"f_brez_zamude[{IME.get(ag, ag)}|{kaj}]"].add(tid)
            if dz is not None and abs(dz) > 1800:
                po_voznji["b_nad_30"].add(tid)
            # GPS
            if not v or omr != "avtobus" or v.get("vir") == "potniki":
                if dz is not None and abs(dz) > 1800:
                    R["b_nad_30"].append({"krog": kid, "agency": IME.get(ag, ag), "no": run["train_no"],
                                          "zamuda_min": round(dz / 60), "gps": None, "url": povezava(run)})
                continue
            tr = trase.get(tid)
            if not tr or tr.get("napaka"):
                stevci["gps: brez trase"] += 1
                continue
            g = gps_zamuda(run, v, tr)
            if "razlog" in g:
                stevci[f"gps: {g['razlog']}"] += 1
                if dz is not None and abs(dz) > 1800:
                    R["b_nad_30"].append({"krog": kid, "agency": IME.get(ag, ag), "no": run["train_no"],
                                          "zamuda_min": round(dz / 60), "gps": g["razlog"], "url": povezava(run)})
                continue
            stevci["gps: izmerjeno"] += 1
            if v.get("delay_s") is None:
                prvi = ts(stops[0].get("sched_dep") or stops[0].get("sched_arr"))
                R["f_podrobno"].append({"krog": kid, "agency": IME.get(ag, ag), "no": run["train_no"],
                    "pred_zacetkom": bool(g.get("pred_zacetkom")),
                    "gps_pri": None if g.get("pred_zacetkom") else stops[g["prejsnji_i"]]["stop_seq"],
                    "gps_min": None if g.get("pred_zacetkom") else round(g["zamuda_s"] / 60),
                    "od_odhoda_min": round((v["seen_ts"] - prvi) / 60), "meja": meja,
                    "zivi": run.get("zivi_vir"), "url": povezava(run)})
            if g.get("pred_zacetkom"):
                stevci["gps: pred začetkom"] += 1
                # (e) živo/izmerjeno pred vozilom, ki še ni začel
                if meja is not None:
                    po_voznji["d_prevozeno_pred_vozilom"].add(tid)
                    R["d_prevozeno_pred_vozilom"].append({"krog": kid, "agency": IME.get(ag, ag),
                        "no": run["train_no"], "meja": meja, "vozilo": "pred prvim postankom",
                        "url": povezava(run)})
                continue
            gz = g["zamuda_s"]
            nxt = g["naslednji_i"]
            if g["prejsnji_i"] == 0 and g["along"] - g["along_post"][0] < 250 and gz < 60:
                stevci["gps: čaka na izhodišču"] += 1
                continue
            # prikaz na naslednjem postanku pred vozilom
            sn = stops[nxt]
            dn = zamuda(sn)["s"] if zamuda(sn) else None
            # (b)
            if dz is not None and abs(dz) > 1800:
                R["b_nad_30"].append({"krog": kid, "agency": IME.get(ag, ag), "no": run["train_no"],
                                      "zamuda_min": round(dz / 60), "gps_min": round(gz / 60),
                                      "url": povezava(run)})
                if abs(gz - dz) > 600:
                    po_voznji["b_nad_30_gps_ne_potrdi"].add(tid)
            # (c) prikazana zamuda proti GPS
            dmeja = zamuda(byseq[meja])["s"] if meja is not None and zamuda(byseq.get(meja, {})) else None
            if dmeja is not None and run.get("trenutna"):
                dmeja = run["trenutna"]["zamuda"]["s"]
            for ime_, val in (("meja", dmeja), ("naslednji", dn)):
                if val is None:
                    continue
                stevci[f"c_primerjav_{ime_}"] += 1
                razl = val - gz
                stevci[f"c_razlika_{ime_}_vsota_abs"] += abs(razl)
                if abs(razl) > 300:
                    key = f"c_gps_{ime_}"
                    po_voznji[key].add(tid)
                    po_voznji[f"{key}[{IME.get(ag, ag)}]"].add(tid)
                    R[key].append({"krog": kid, "agency": IME.get(ag, ag), "no": run["train_no"],
                                   "prikaz_min": round(val / 60), "gps_min": round(gz / 60),
                                   "vrsta": (zamuda(byseq[meja]) or {}).get("vrsta") if ime_ == "meja" else (zamuda(sn) or {}).get("vrsta"),
                                   "meja": meja, "vozilo_med": (stops[g["prejsnji_i"]]["stop_seq"], sn["stop_seq"]),
                                   "zivi": run.get("zivi_vir"), "age_s": v.get("age_s"),
                                   "url": povezava(run)})
            # (d) meja proti legi
            vs_seq = stops[g["prejsnji_i"]]["stop_seq"]  # zadnji postanek, ki ga je vozilo doseglo
            if g.get("na_postanku_i") is not None:
                vs_seq = stops[g["na_postanku_i"]]["stop_seq"]
            if meja is not None:
                if meja > vs_seq + 1:
                    po_voznji["d_prevozeno_pred_vozilom"].add(tid)
                    R["d_prevozeno_pred_vozilom"].append({"krog": kid, "agency": IME.get(ag, ag),
                        "no": run["train_no"], "meja": meja, "vozilo_pri": vs_seq,
                        "url": povezava(run)})
                lag = vs_seq - meja
                if lag >= 3:
                    po_voznji["d_meja_zaostaja_3"].add(tid)
                    R["d_meja_zaostaja_3"].append({"krog": kid, "agency": IME.get(ag, ag),
                        "no": run["train_no"], "meja": meja, "vozilo_pri": vs_seq, "zaostanek": lag,
                        "url": povezava(run)})
            # (e) živo na prevoženem
            for s in stops:
                z = zamuda(s)
                if z and z.get("vrsta") == "živo" and s["stop_seq"] < vs_seq:
                    po_voznji["e_zivo_na_prevozenem"].add(tid)
                    R["e_zivo_na_prevozenem"].append({"krog": kid, "agency": IME.get(ag, ag),
                        "no": run["train_no"], "seq": s["stop_seq"], "postanek": s["name"],
                        "vozilo_pri": vs_seq, "eta_min": s.get("eta_min"), "zamuda_min": z["min"],
                        "meja": meja, "url": povezava(run)})
                    break
            # napoved prevoznika na prevoženem (feed zaostaja)
            for s in stops:
                z = zamuda(s)
                if z and z.get("vrsta") == "napoved prevoznika" and s["stop_seq"] < vs_seq - 1:
                    po_voznji["e_napoved_na_prevozenem"].add(tid)
                    break
    izid = {"stevci": dict(stevci),
            "voznje": {k: len(v) for k, v in sorted(po_voznji.items())},
            "primeri": {k: v for k, v in R.items()}}
    json.dump(izid, open(izhod, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(izid["stevci"], ensure_ascii=False, indent=0))
    print(json.dumps(izid["voznje"], ensure_ascii=False, indent=0))


if __name__ == "__main__":
    main()
