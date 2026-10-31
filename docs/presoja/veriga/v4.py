import csv, sqlite3, collections, statistics as st
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
rows = list(csv.DictReader(open("/tmp/veriga_pari.csv")))
I = lambda v: int(float(v)) if v not in ("", None) else None
fs = dict(c.execute("SELECT trip_id, first_seq FROM trip WHERE network='avtobus'").fetchall())
dep = {}
for d in sorted({r["dan"] for r in rows}):
    for t, s, ts, z in c.execute("SELECT trip_id, MIN(stop_seq), prehod_ts, zamuda_s FROM gps_prehod WHERE service_date=? AND je_cilj=0 GROUP BY trip_id", (d,)):
        f = fs.get(t)
        if f is not None and s - f <= 2: dep[(d, t)] = (ts, z)
N = {"1118": "LPP prim", "1119": "Nomago", "1121": "AP MS", "1123": "Arriva", "lpp": "LPP mestni"}
def grp(r):
    g = [N.get(r["ag"], r["ag"])]
    if r["ag"] == "1118" and r["x_no"] == "25": g.append("LPP 25")
    return g
A = collections.defaultdict(collections.Counter); Z = collections.defaultdict(list); XF = collections.defaultdict(list)
for r in rows:
    T = int(r["T"]); eve = datetime.fromtimestamp(T, TZ).hour >= 18
    for g in grp(r):
        for gg in (g, g + (" zvečer" if eve else " dan")):
            a = A[gg]; a["pari"] += 1
            # 1. lega (NAP, 14 dni)
            lk = r["lega_p"] and r["lega_x"] and int(r["n_p"]) >= 5 and int(r["n_x"]) >= 5
            if lk:
                same = r["lega_p"] == r["lega_x"]; a["L_zn"] += 1; a["L_dr"] += (not same)
            # straza 30.-31.10 po viru
            for vir, kp, kx in (("derp", "sd_p", "sd_x"), ("nap", "sn_p", "sn_x"), ("lpp", "sl_p", "sl_x")):
                if r[kp] and r[kx]:
                    a[vir + "_zn"] += 1; a[vir + "_dr"] += r[kp] != r[kx]
            if r["sd_p"] and r["sd_x"] and r["sn_p"] and r["sn_x"]:
                a["dn_oba"] += 1; a["dn_nesoglasje"] += (r["sd_p"] == r["sd_x"]) != (r["sn_p"] == r["sn_x"])
            if not lk: continue
            # 2. cas: prejsnja na cilju (GPS prehod, sicer zadnja lega) proti odhodu te
            p_arr = I(r["p_arr"]) or I(r["p_last"]); xd = dep.get((r["dan"], r["x"]))
            if p_arr and xd:
                a["t_zn"] += 1
                if xd[0] < p_arr - 60:
                    a["odpelje_pred_prihodom"] += 1; a["opp_lega_dr"] += (not same)
                if p_arr > T + 60:          # prejsnja pride na cilj po uri odhoda te
                    a["pozna"] += 1; a["pozna_dr"] += (not same)
                    if not same:
                        a["pozna_dr_tocna"] += xd[1] <= 120; Z[gg + " pozna/drugo"].append(xd[1])
                    else:
                        Z[gg + " pozna/isto"].append(xd[1])
            # 3. pilula ob T-10, T-5, T-1 min
            pl = I(r["p_last"]); xf = I(r["x_first"])
            if xf: XF[gg].append(xf - T)
            for m in (10, 5, 1):
                t = T - 60 * m
                pil = pl is not None and pl >= t - 900 and (xf is None or xf > t)
                if pil:
                    a[f"pil{m}"] += 1; a[f"pil{m}_dr"] += (not same)
                    a[f"pil{m}_tece"] += pl > t
                # glava: vedno pred odhodom; prav = isto vozilo in prejsnja se vozi
                a[f"gl{m}_prav"] += same and pl is not None and pl > t
                a[f"gl{m}_caka"] += same and not (pl is not None and pl > t)
                a[f"gl{m}_dr"] += not same
pc = lambda a, b: f"{100*a/b:.0f}%" if b else "-"
for g in sorted(A):
    a = A[g]
    print(f"{g:20s} pari {a['pari']:5d} | lega {a['L_zn']:5d} drugo {pc(a['L_dr'],a['L_zn'])} | derp {a['derp_zn']} dr {pc(a['derp_dr'],a['derp_zn'])} nap {a['nap_zn']} dr {pc(a['nap_dr'],a['nap_zn'])} lpp {a['lpp_zn']} dr {pc(a['lpp_dr'],a['lpp_zn'])} | derp/nap nesogl {a['dn_nesoglasje']}/{a['dn_oba']}")
    if a["t_zn"]:
        print(f"{'':20s} cas {a['t_zn']} odpelje pred prihodom prejsnje {a['odpelje_pred_prihodom']} (lega drugo {a['opp_lega_dr']}) | prejsnja po uri {a['pozna']} drugo {pc(a['pozna_dr'],a['pozna'])} drugo&tocna(<=2min) {a['pozna_dr_tocna']}")
        print(f"{'':20s} pilula T-10/5/1: {a['pil10']} ({pc(a['pil10_dr'],a['pil10'])} drugo) {a['pil5']} ({pc(a['pil5_dr'],a['pil5'])} dr, {pc(a['pil5_tece'],a['pil5'])} prejsnja tece) {a['pil1']} ({pc(a['pil1_dr'],a['pil1'])} dr) | glava T-5 prav {pc(a['gl5_prav'],a['L_zn'])} caka {pc(a['gl5_caka'],a['L_zn'])} drugo {pc(a['gl5_dr'],a['L_zn'])}")
    if XF[g]:
        x = sorted(XF[g]); print(f"{'':20s} prva lega te vs T: p25 {x[len(x)//4]//60} med {x[len(x)//2]//60} p75 {x[3*len(x)//4]//60} min (n={len(x)})")
for k in sorted(Z):
    v = Z[k]
    if len(v) >= 5: print(f"  zamuda odhoda {k}: n={len(v)} mediana {st.median(v)/60:.1f} min, <=2 min {pc(sum(z<=120 for z in v), len(v))}")
