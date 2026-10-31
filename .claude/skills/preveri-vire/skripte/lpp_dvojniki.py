"""Enaki dvojniki v objavljenem voznem redu LPP po dnevih (ista proga, vzorec,
ure; blok). Argumenti: dnevi YYYY-MM-DD. Primer 31. 10. 2026: 75 skupin.

Zagon (samo branje): scp na arwen, nato
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python /tmp/lpp_dvojniki.py ARGUMENTI'
"""
import sqlite3, collections, requests
from google.transit import gtfs_realtime_pb2
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
f = gtfs_realtime_pb2.FeedMessage()
f.ParseFromString(requests.get("https://rt.gtfs.derp.si/sources/lpp/all", timeout=30).content)
v_feedu = {e.trip_update.trip.trip_id for e in f.entity if e.HasField("trip_update")}
import sys
for dan in sys.argv[1:]:
    g = collections.defaultdict(list)
    for tid, route, no, st in conn.execute("SELECT t.trip_id, t.route_id, t.train_no, t.start_s FROM trip t JOIN service_day d ON d.service_id=t.service_id WHERE d.date=? AND t.agency='lpp'", (dan,)):
        g[(route, tid.split("|")[2], st)].append((tid, no))
    enaki = razl = 0; vf = collections.Counter(); blok = collections.Counter()
    for k, v in g.items():
        if len(v) < 2: continue
        s = [tuple(conn.execute("SELECT stop_id, arr_s, dep_s FROM sched WHERE trip_id=? ORDER BY stop_seq", (t,)).fetchall()) for t, _ in v]
        if all(x == s[0] for x in s): enaki += 1
        else: razl += 1
        vf[sum(t in v_feedu for t, _ in v)] += 1
        b = [conn.execute("SELECT block_id, headsign, service_id FROM trip WHERE trip_id=?", (t,)).fetchone() for t, _ in v]
        blok["isti blok" if len({x[0] for x in b}) == 1 else "razl blok"] += 1
    print(dan, "dvojnikov enakih", enaki, "različnih", razl, "koliko od para v feedu", dict(vf), dict(blok))
