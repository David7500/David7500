import csv, sqlite3, collections, statistics as st
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
rows = [r for r in csv.DictReader(open("/tmp/veriga_pari.csv")) if r["ag"] in ("1118", "1119", "1121", "1123")]
I = lambda v: int(float(v)) if v not in ("", None) else None
fs = {t: f for t, f in c.execute("SELECT trip_id, first_seq FROM trip WHERE agency IN ('1118','1119','1121','1123')")}
lastf = {}; x2 = {}
for d in sorted({r["dan"] for r in rows}):
    for t, m in c.execute("""SELECT r.trip_id, MAX(r.feed_ts) FROM run r JOIN trip t ON t.trip_id=r.trip_id AND t.agency IN ('1118','1119','1121','1123')
                             WHERE r.service_date=? GROUP BY r.trip_id""", (d,)):
        lastf[(d, t)] = m
    for t, seq, z in c.execute("""SELECT r.trip_id, r.stop_seq, COALESCE(r.delay_dep, r.delay_arr) FROM run r JOIN trip t ON t.trip_id=r.trip_id AND t.agency='1118'
                                  WHERE r.service_date=? AND r.stop_seq = t.first_seq + 1""", (d,)):
        x2[(d, t)] = z
# 1. preverba posrednika: zadnja beseda feeda o prejsnji proti GPS prihodu na cilj
dif = [lastf[(r["dan"], r["p"])] - I(r["p_arr"]) for r in rows if r["ag"] != "1118" and r["p_arr"] and (r["dan"], r["p"]) in lastf]
dif.sort(); n = len(dif)
print(f"zadnja beseda feeda - GPS prihod (medkrajevni): n={n} p10 {dif[n//10]/60:.1f} med {dif[n//2]/60:.1f} p90 {dif[9*n//10]/60:.1f} min, v 3 min {100*sum(abs(x)<=180 for x in dif)/n:.0f}%")
A = collections.Counter(); lay = collections.defaultdict(list); kand = []
for r in rows:
    d, T = r["dan"], int(r["T"]); eve = datetime.fromtimestamp(T, TZ).hour >= 18
    g = ("LPP 25" if r["ag"] == "1118" and r["x_no"] == "25" else {"1118": "LPP prim", "1119": "Nomago", "1121": "AP MS", "1123": "Arriva"}[r["ag"]]) + (" zvečer" if eve else " dan")
    A[g, "pari"] += 1; lay[g].append((int(float(r["x_start"])) - int(float(r["p_end"]))) / 60)
    lf = lastf.get((d, r["p"]))
    if lf is None: A[g, "prejsnja brez feeda"] += 1; continue
    A[g, "s feedom"] += 1
    A[g, "tece T-5"] += lf > T - 300; A[g, "tece T"] += lf > T
    if g.startswith("LPP 25 zvečer") and lf > T + 60 and d >= "2026-10-24":
        kand.append((d, datetime.fromtimestamp(T, TZ).strftime("%H:%M"), datetime.fromtimestamp(lf, TZ).strftime("%H:%M"),
                     None if x2.get((d, r["x"])) is None else round(x2[(d, r["x"])] / 60), r["sd_p"] == r["sd_x"] if r["sd_p"] and r["sd_x"] else None))
pc = lambda a, b: f"{100*a/b:.0f}%" if b else "-"
for g in sorted({k[0] for k in A}):
    L = sorted(lay[g]); s = A[g, "s feedom"]
    print(f"{g:16s} pari {A[g,'pari']:5d} | brez feeda prejsnje {pc(A[g,'prejsnja brez feeda'], A[g,'pari'])} | prejsnja se v feedu ob T-5 {pc(A[g,'tece T-5'], s)}, ob T {pc(A[g,'tece T'], s)} | postanek med {L[len(L)//2]:.0f} min, p25 {L[len(L)//4]:.0f}")
print("LPP 25 zvečer 24.-30.10, prejsnja v feedu se po T+1 (dan, T, zadnja beseda o prejsnji, zamuda te na 2. postanku, isto vozilo derp):")
for k in sorted(kand): print(" ", k)
