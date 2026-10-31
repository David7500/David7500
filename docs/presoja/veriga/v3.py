import sqlite3, collections, csv, time
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
c.row_factory = sqlite3.Row
q = lambda s, *a: c.execute(s, a).fetchall()
print("LPP 25 kandidati 30.10:", [tuple(r) for r in q("""SELECT t.agency, t.train_no, COUNT(*), SUM(t.block_id IS NOT NULL) FROM trip t JOIN service_day sd ON sd.service_id=t.service_id AND sd.date='2026-10-30'
 WHERE t.network='avtobus' AND (t.train_no IN ('25','LPP 25') OR t.headsign LIKE '%Medvode%') GROUP BY 1,2 ORDER BY 3 DESC LIMIT 8""")])
print("bloki z vec agencijami:", q("SELECT COUNT(*) FROM (SELECT block_id FROM trip WHERE block_id IS NOT NULL GROUP BY block_id HAVING COUNT(DISTINCT agency)>1)")[0][0])
def polnoc(d):
    return int(datetime.combine(d, dtime(12), TZ).timestamp()) - 43200
d0 = date(2026,10,17); dni = [d0 + timedelta(i) for i in range(15)]
out = open("/tmp/veriga_pari.csv", "w", newline=""); w = csv.writer(out)
w.writerow(["dan","ag","p","x","x_no","p_end","x_start","T","lega_p","lega_x","n_p","n_x","p_last","x_first","p_arr","x_dep","x_dep_z","p_arr_z","sd_p","sd_x","sn_p","sn_x","sl_p","sl_x"])
t0 = time.time()
for d in dni:
    ds = d.isoformat(); P = polnoc(d)
    rows = q("""SELECT t.trip_id, t.block_id, t.start_s, t.end_s, t.agency, t.train_no, t.first_seq FROM trip t
      JOIN service_day sd ON sd.service_id=t.service_id AND sd.date=? WHERE t.network='avtobus' AND t.block_id IS NOT NULL""", ds)
    byb = collections.defaultdict(list)
    for r in rows: byb[r["block_id"]].append(r)
    pairs = []
    for L in byb.values():
        for x in L:
            if x["start_s"] is None: continue
            cand = [p for p in L if p["trip_id"] != x["trip_id"] and p["end_s"] is not None and p["end_s"] <= x["start_s"]]
            if cand: pairs.append((max(cand, key=lambda p: p["end_s"]), x))
    # lega: prevladujoce vozilo, prva/zadnja lega
    dom = {}; first = {}; last = {}
    best = {}
    for r in q("SELECT trip_id, vozilo, COUNT(*) n, MIN(ts) a, MAX(ts) b FROM lega WHERE service_date=? GROUP BY trip_id, vozilo", ds):
        t = r["trip_id"]
        if r["n"] > best.get(t, (0,))[0]: best[t] = (r["n"], r["vozilo"])
        first[t] = min(first.get(t, r["a"]), r["a"]); last[t] = max(last.get(t, r["b"]), r["b"])
    # gps_prehod: odhod s prvega, prihod na cilj
    dep = {}; arr = {}
    for r in q("""SELECT g.trip_id, g.stop_seq, g.prehod_ts, g.zamuda_s, g.je_cilj, t.first_seq FROM gps_prehod g JOIN trip t ON t.trip_id=g.trip_id
                  WHERE g.service_date=? AND (g.je_cilj=1 OR g.stop_seq=t.first_seq)""", ds):
        if r["je_cilj"]: arr[r["trip_id"]] = (r["prehod_ts"], r["zamuda_s"])
        elif r["stop_seq"] == r["first_seq"]: dep[r["trip_id"]] = (r["prehod_ts"], r["zamuda_s"])
    sv = collections.defaultdict(dict)
    for r in q("SELECT vir, vozilo, trip_id, vzorcev FROM straza_opazeno WHERE dan=?", ds):
        k = (r["vir"], r["trip_id"]); o = sv[k]
        o[r["vozilo"]] = o.get(r["vozilo"], 0) + r["vzorcev"]
    def sdom(vir, t):
        o = sv.get((vir, t)); return max(o, key=o.get) if o else ""
    for p, x in pairs:
        pt, xt = p["trip_id"], x["trip_id"]
        w.writerow([ds, x["agency"], pt, xt, x["train_no"], P + p["end_s"], P + x["start_s"], P + x["start_s"],
                    best.get(pt, (0, ""))[1], best.get(xt, (0, ""))[1], best.get(pt, (0,))[0], best.get(xt, (0,))[0],
                    last.get(pt, ""), first.get(xt, ""),
                    arr.get(pt, ("",))[0], dep.get(xt, ("",))[0], dep.get(xt, ("", ""))[1], arr.get(pt, ("", ""))[1],
                    sdom("derp", pt), sdom("derp", xt), sdom("nap", pt), sdom("nap", xt), sdom("lpp", pt), sdom("lpp", xt)])
    print(ds, "parov", len(pairs), "lega voznj", len(best), "prehod dep/arr", len(dep), len(arr), "%.0fs" % (time.time() - t0), flush=True)
out.close()
