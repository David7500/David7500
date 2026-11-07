"""Za zadetke iz drsi_teden.py: vozilo in njegove točke iz dosje.sqlite, premik
med drsenjem in po njem, razdalja do postanka; obs po drsenju (ali je vožnja
nato prevozila postanke z isto zamudo). Samo branje."""
import sqlite3, json, math, zlib, collections
g = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
d = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
z = json.load(open("/var/tmp/drsi_zadetki.json"))


def razd(a, b):
    k = math.cos(math.radians(a[0]))
    return math.hypot((a[0] - b[0]) * 111195, (a[1] - b[1]) * 111195 * k)


trips = {o["trip"] for o in z}
lo, hi = min(o["od"] for o in z) - 900, max(o["konec"] for o in z) + 900
voz = collections.defaultdict(list)
q = "SELECT trip_id, dan, vozilo, vir, ts FROM stanje WHERE ts BETWEEN ? AND ? AND trip_id IN (%s)" % ",".join("?" * len(trips))
for t, dan, v, vir, ts in d.execute(q, (lo, hi, *trips)):
    voz[t].append((ts, v, vir))
for o in z:
    st = g.execute("SELECT s.lat, s.lon FROM sched x JOIN station s USING(stop_id) WHERE x.trip_id=? AND x.stop_seq=?",
                   (o["trip"], o["seq"])).fetchone()
    kand = collections.Counter((v, vir) for ts, v, vir in voz.get(o["trip"], [])
                               if o["od"] - 900 <= ts <= o["konec"] + 900)
    o["vozila"] = [f"{v}@{vir}" for (v, vir), _ in kand.most_common(3)]
    r = g.execute("SELECT COUNT(DISTINCT stop_seq), MAX(stop_seq), MIN(feed_ts), MAX(feed_ts) FROM obs "
                  "WHERE trip_id=? AND service_date=? AND feed_ts > ?", (o["trip"], o["dan"], o["konec"])).fetchone()
    o["obs_po"] = list(r)
    o["last_seq"] = g.execute("SELECT last_seq FROM trip WHERE trip_id=?", (o["trip"],)).fetchone()[0]
    o["lpp_zasloni"] = g.execute(
        "SELECT COUNT(*), MIN(stop_seq), MAX(stop_seq), MIN(delay_s)/60, MAX(delay_s)/60 FROM lpp_zamuda "
        "WHERE trip_id=? AND service_date=? AND zadnjic_ts >= ? AND prvic_ts <= ?",
        (o["trip"], o["dan"], o["od"], o["konec"] + 1800)).fetchone()
    # zamuda na zadnjem zapisanem postanku vožnje (končni izid)
    o["run_zadnji"] = g.execute("SELECT stop_seq, COALESCE(delay_dep, delay_arr)/60 FROM run WHERE trip_id=? "
                                "AND service_date=? ORDER BY stop_seq DESC LIMIT 1", (o["trip"], o["dan"])).fetchone()
    if not kand:
        continue
    v, vir = kand.most_common(1)[0][0]
    tk = []
    for (b,) in d.execute("SELECT vsebina FROM tocke WHERE vozilo=? AND vir=? AND od_ts <= ? AND do_ts >= ?",
                          (v, vir, o["konec"] + 3600, o["od"] - 120)):
        tk += json.loads(zlib.decompress(b))
    tk = sorted(p for p in tk if p[1] is not None and p[2] is not None)
    med = [p for p in tk if o["od"] <= p[0] <= o["konec"]]
    po = [p for p in tk if o["konec"] < p[0] <= o["konec"] + 3600]
    o["d_n_med"] = len(med)
    if med:
        o["d_premik_med"] = int(max(razd(med[0][1:3], p[1:3]) for p in med))
        o["d_od_postanka"] = int(razd(med[-1][1:3], st)) if st else None
        o["d_kje"] = [round(med[-1][1], 5), round(med[-1][2], 5)]
    if med and po:
        o["d_premik_po"] = int(max(razd(med[-1][1:3], p[1:3]) for p in po))
json.dump(z, open("/var/tmp/drsi_zadetki2.json", "w"), ensure_ascii=False)
print("zadetkov", len(z), "z vozilom", sum(1 for o in z if o.get("vozila")),
      "s točkami", sum(1 for o in z if o.get("d_n_med")))
