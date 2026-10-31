"""Ponovitev varovala collector.ura_namesto_zamude (prvi napovedani postanek, brez
končne) na obs. Argumenti: dnevi. Za odločitev KAJROS_DRSI senca -> vodi.

Zagon (samo branje): scp na arwen, nato
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python /tmp/fantom_ponovitev.py ARGUMENTI'
"""
import sqlite3, sys, collections
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
NAGIB, NAJVEC = 0.8, 900
zadnji = dict(conn.execute("SELECT trip_id, last_seq FROM trip WHERE agency IN ('lpp','1118')").fetchall())
for dan in sys.argv[1:]:
    vrst = conn.execute("SELECT o.trip_id, o.feed_ts, MIN(o.stop_seq), COALESCE(o.delay_arr, o.delay_dep) FROM obs o "
                        "CROSS JOIN trip t ON t.trip_id=o.trip_id WHERE t.agency IN ('lpp','1118') AND o.service_date=? "
                        "GROUP BY o.trip_id, o.feed_ts ORDER BY o.trip_id, o.feed_ts", (dan,)).fetchall()
    po = collections.defaultdict(list)
    for t, ts, seq, z in vrst:
        if z is not None: po[t].append((ts, seq, z))
    flag, maxz = 0, []
    for t, v in po.items():
        p = None; ujet = False
        for ts, seq, z in v:
            if seq == zadnji.get(t):
                p = None; continue
            if (p is None or p[4] != seq or ts - p[2] > 300 or z < p[3] - 60
                    or ts - p[0] >= 120 and z - p[1] < NAGIB * (ts - p[0])):
                p = [ts, z, ts, z, seq]; continue
            p[2], p[3] = ts, z
            if ts - p[0] >= NAJVEC: ujet = True; break
        if ujet:
            flag += 1
            maxz.append(max(z for _, _, z in v) // 60)
    print(dan, "voženj", len(po), "zavrnjenih", flag, "max zamude (min):", sorted(maxz))
