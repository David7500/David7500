"""Ponovitev collector.ura_namesto_zamude na obs za vse avtobuse (ne vlaki),
za vsak zadetek lega vozila: ali se je premaknilo. Samo branje."""
import sqlite3, sys, collections, math, json
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
NAGIB, NAJVEC = 0.8, 900


def razd(a, b):
    k = math.cos(math.radians(a[0]))
    return math.hypot((a[0] - b[0]) * 111195, (a[1] - b[1]) * 111195 * k)


def premik(ls):
    return int(max((razd(ls[0][1:3], l[1:3]) for l in ls), default=0)) if ls else None


info = {r[0]: r[1:] for r in conn.execute(
    "SELECT trip_id, agency, train_no, headsign, last_seq, first_seq FROM trip WHERE network='avtobus'")}
out = []
for dan in sys.argv[1:]:
    vrst = conn.execute(
        "SELECT o.trip_id, o.feed_ts, MIN(o.stop_seq), COALESCE(o.delay_arr, o.delay_dep) FROM obs o "
        "CROSS JOIN trip t ON t.trip_id=o.trip_id WHERE t.network='avtobus' AND o.service_date=? "
        "GROUP BY o.trip_id, o.feed_ts ORDER BY o.trip_id, o.feed_ts", (dan,)).fetchall()
    po = collections.defaultdict(list)
    for t, ts, seq, z in vrst:
        if z is not None:
            po[t].append((ts, seq, z))
    n_po_ag = collections.Counter(info[t][0] for t in po)
    for t, v in po.items():
        p = None
        ujet = None
        for ts, seq, z in v:
            if seq == info[t][3]:
                p = None
                continue
            if (p is None or p[4] != seq or ts - p[2] > 300 or z < p[3] - 60
                    or ts - p[0] >= 120 and z - p[1] < NAGIB * (ts - p[0])):
                p = [ts, z, ts, z, seq]
                continue
            p[2], p[3] = ts, z
            if ts - p[0] >= NAJVEC:
                ujet = ts
                break
        if ujet is None:
            continue
        od, z0, seq = p[0], p[1], p[4]
        konec = ujet
        for ts2, s2, z2 in v:
            if ts2 <= ujet:
                continue
            if s2 == seq and z2 >= p[3] - 60:
                konec, p[3] = ts2, max(p[3], z2)
            else:
                break
        leg = conn.execute("SELECT ts, lat, lon, vozilo FROM lega WHERE service_date=? AND trip_id=? "
                           "AND ts BETWEEN ? AND ? ORDER BY ts", (dan, t, od - 60, konec + 7200)).fetchall()
        st = conn.execute("SELECT s.lat, s.lon, s.name FROM sched x JOIN station s USING(stop_id) "
                          "WHERE x.trip_id=? AND x.stop_seq=?", (t, seq)).fetchone()
        vdrs = [l for l in leg if od <= l[0] <= konec]
        po_d = [l for l in leg if l[0] > konec]
        seq_po = sorted({s for ts3, s, _ in v if ts3 > konec})
        out.append({"dan": dan, "trip": t, "ag": info[t][0], "no": info[t][1], "hs": info[t][2],
                    "od": od, "konec": konec, "min": round((konec - od) / 60), "z0": z0 // 60,
                    "zkonec": p[3] // 60, "zmax": max(z for _, _, z in v) // 60, "seq": seq,
                    "first_seq": info[t][4], "postanek": st and st[2],
                    "n_leg": len(vdrs), "premik_med": premik(vdrs),
                    "od_postanka_m": int(razd(vdrs[-1][1:3], st[:2])) if vdrs and st else None,
                    "premik_po": premik([vdrs[-1]] + po_d) if vdrs and po_d else None,
                    "n_leg_po": len(po_d), "vozilo": (vdrs or leg or [[None] * 4])[-1][3],
                    "seq_po": [seq_po[0], seq_po[-1], len(seq_po)] if seq_po else None})
    print(dan, "voženj po prevozniku", dict(n_po_ag), "zadetkov",
          sum(1 for o in out if o["dan"] == dan), flush=True)
json.dump(out, open("/var/tmp/drsi_zadetki.json", "w"), ensure_ascii=False)
print("skupaj", len(out))
