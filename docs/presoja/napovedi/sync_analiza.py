"""Analiza sinhronega kroga. Rabi: python sync_analiza.py <sync.json> <imenik_posnetka>"""
import glob
import json
import os
import sys
import urllib.parse
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import analiza as A  # noqa: E402

d = json.load(open(sys.argv[1]))
trase = {}
for f in glob.glob(os.path.join(sys.argv[2], "trase", "*.json")):
    trase[urllib.parse.unquote(os.path.basename(f)[:-5])] = json.load(open(f))
st = Counter()
primeri = {"c": [], "d": [], "e": [], "h_kartica": [], "h_zemljevid": [], "i_tabla": []}


def zam(s):
    return (s or {}).get("zamuda")


for p in d["pari"]:
    run, vv = p["run"], p["veh"] or []
    if not run or not vv:
        st["par brez okna ali lege"] += 1
        continue
    v = vv[0]
    if len(vv) > 1:
        st["več leg na vožnjo"] += 1
    ag = A.IME.get(run.get("agency"), run.get("agency"))
    byseq = {s["stop_seq"]: s for s in run["stops"]}
    meja = run.get("last_measured_seq")
    # (h) kartica vozila proti oknu v istem trenutku
    if v.get("vir") != "potniki" and meja is not None and zam(byseq.get(meja)):
        st["h kartica primerjav"] += 1
        dw = zam(byseq[meja])["s"]
        if v.get("measured_seq") != meja or v.get("delay_s") is None or abs(v["delay_s"] - dw) >= 60:
            st["h kartica razlika"] += 1
            primeri["h_kartica"].append((ag, run["train_no"], v.get("measured_seq"), v.get("delay_s"),
                                         meja, dw, round(p["t_run"] - p["t_veh"], 1), A.povezava(run)))
    tr = trase.get(run["trip_id"])
    if not tr or tr.get("napaka"):
        st["gps brez trase (nova vožnja)"] += 1
        continue
    g = A.gps_zamuda(run, v, tr)
    if "razlog" in g or g.get("pred_zacetkom"):
        st["gps " + g.get("razlog", "pred začetkom")] += 1
        continue
    if g["prejsnji_i"] == 0 and g["along"] - g["along_post"][0] < 250 and g["zamuda_s"] < 60:
        st["gps čaka na izhodišču"] += 1
        continue
    st["gps izmerjeno"] += 1
    stops = run["stops"]
    vs_seq = stops[g["na_postanku_i"] if g.get("na_postanku_i") is not None else g["prejsnji_i"]]["stop_seq"]
    # Pot, ki jo vozilo naredi, odkar je bila lega izmerjena: ~ starost × 8 m/s.
    zamik = (p["t_run"] - v["seen_ts"]) * 8.0
    # (d) meja pred vozilom: postanek ≤ meja, ki je po trasi dlje od lege + zamik + 150 m
    al = g["along_post"]
    if meja is not None:
        i_meja = next(i for i, s in enumerate(stops) if s["stop_seq"] == meja)
        if al[i_meja] is not None and al[i_meja] > g["along"] + zamik + 150:
            st["d meja pred vozilom"] += 1
            primeri["d"].append((ag, run["train_no"], meja, vs_seq, round(al[i_meja] - g["along"]),
                                 v.get("age_s"), A.povezava(run)))
        nas = [i for i, s in enumerate(stops) if s["stop_seq"] > meja and al[i] is not None
               and al[i] < g["along"] - 150]
        if len(nas) >= 3:
            st["d meja zaostaja ≥ 3 postanke"] += 1
            primeri["d"].append((ag, run["train_no"], meja, vs_seq, -len(nas), v.get("age_s"),
                                 A.povezava(run)))
    # (e) živo / napoved prevoznika za vozilom
    for s, a in zip(stops, al):
        z = zam(s)
        if z and z.get("vrsta") == "živo" and a is not None and a < g["along"] - 150:
            st["e živo za vozilom"] += 1
            primeri["e"].append((ag, run["train_no"], s["stop_seq"], s.get("eta_min"), z["min"],
                                 vs_seq, A.povezava(run)))
            break
    # (c) zadnja meritev in naslednji postanek proti GPS
    gz = g["zamuda_s"]
    dm = zam(byseq.get(meja))["s"] if meja is not None and zam(byseq.get(meja)) else None
    sn = stops[g["naslednji_i"]]
    dn = zam(sn)["s"] if zam(sn) else None
    for ime, val, vrsta in (("meja", dm, (zam(byseq.get(meja)) or {}).get("vrsta")),
                            ("naslednji", dn, (zam(sn) or {}).get("vrsta"))):
        if val is None:
            continue
        st[f"c {ime} primerjav"] += 1
        if abs(val - gz) > 300:
            st[f"c {ime} > 5 min"] += 1
            st[f"c {ime} > 5 min [{ag}]"] += 1
            primeri["c"].append((ime, ag, run["train_no"], vrsta, round(val / 60), round(gz / 60),
                                 vs_seq, round(g["f"], 2), v.get("speed_kmh"), v.get("age_s"),
                                 A.povezava(run)))
# (h) /api/live proti oknu, takoj za seznamom
for z in d["zemljevid"]:
    run, x = z["run"], z["live"]
    if not run:
        continue
    st["h zemljevid primerjav"] += 1
    meja = run.get("last_measured_seq")
    byseq = {s["stop_seq"]: s for s in run["stops"]}
    dw = run["trenutna"]["zamuda"]["s"] if run.get("trenutna") else (
        zam(byseq.get(meja))["s"] if meja is not None and zam(byseq.get(meja)) else None)
    dl = (x.get("zamuda") or {}).get("s")
    if x.get("stop_seq") != meja or dw is None or dl is None or abs(dl - dw) >= 60:
        st["h zemljevid razlika"] += 1
        primeri["h_zemljevid"].append((x["train_no"], x.get("stop_seq"), dl, meja, dw,
                                       round(z["t_run"] - z["t_live"], 1), x.get("age_s"),
                                       A.povezava(run)))
# (i) tabla proti oknu
for t in d["table"]:
    run, tabla = t["run"], t["tabla"]
    if not run or not tabla:
        st["tabla brez odgovora"] += 1
        continue
    vrst = [r for r in tabla.get("board", []) if r.get("trip_id") == t["trip_id"]]
    s = next((s for s in run["stops"] if s["stop_seq"] == t["seq"]), None)
    if not vrst:
        st["tabla nima vožnje"] += 1
        primeri["i_tabla"].append(("ni na tabli", run["train_no"], t["postanek"], A.povezava(run)))
        continue
    r = vrst[0]
    st["tabla primerjav"] += 1
    zt = (r.get("zamuda") or {})
    zo = zam(s) or {}
    if zt.get("s") != zo.get("s") or zt.get("vrsta") != zo.get("vrsta"):
        st["tabla drugače"] += 1
        primeri["i_tabla"].append((run["train_no"], t["postanek"], zt.get("min"), zt.get("vrsta"),
                                   zo.get("min"), zo.get("vrsta"),
                                   {k: r.get(k) for k in ("typical", "napoved", "ocena") if r.get(k)},
                                   A.povezava(run)))
print(json.dumps(dict(sorted(st.items())), ensure_ascii=False, indent=0))
for k, v in primeri.items():
    print("==", k, len(v))
    for x in v[:12]:
        print("  ", json.dumps(x, ensure_ascii=False)[:330])
