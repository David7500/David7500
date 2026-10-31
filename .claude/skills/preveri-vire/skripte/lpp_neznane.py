"""Žive vožnje mestnega LPP brez voznega reda (zdaj v feedu derp.si) in objavljene
kandidatke iste proge: zamik, ali vozi pod svojim id-jem, ali je že v paru.
Primer 31. 10. 2026: linija 2, kandidatka z dvojnikom -> par po uri dvoumen.

Zagon (samo branje): scp na arwen, nato
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python /tmp/lpp_neznane.py ARGUMENTI'
"""
import sqlite3, statistics, requests
from datetime import datetime
from zoneinfo import ZoneInfo
from google.transit import gtfs_realtime_pb2
TZ = ZoneInfo("Europe/Ljubljana")
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
f = gtfs_realtime_pb2.FeedMessage()
f.ParseFromString(requests.get("https://rt.gtfs.derp.si/sources/lpp/all", timeout=30).content)
tus = {e.trip_update.trip.trip_id: e.trip_update for e in f.entity if e.HasField("trip_update")}
veh = {e.vehicle.trip.trip_id: e.vehicle for e in f.entity if e.HasField("vehicle")}
znane = {t for t in tus if conn.execute("SELECT 1 FROM trip WHERE trip_id=?", (t,)).fetchone()}
pari = {r["ziva"]: dict(r) for r in conn.execute("SELECT * FROM ziva_voznja WHERE service_date >= date('now','localtime','-1 day')")}
nasa_v_paru = {p["nasa"]: z for z, p in pari.items()}
nm = {}
def name(sid):
    if sid not in nm:
        r = conn.execute("SELECT name FROM station WHERE stop_id=?", (sid,)).fetchone(); nm[sid] = r[0] if r else "?"
    return nm[sid]
danes = datetime.now(TZ).date().isoformat()
polnoc = int(datetime.fromisoformat(danes + "T12:00:00").replace(tzinfo=TZ).timestamp()) - 12*3600
print("feed", datetime.fromtimestamp(f.header.timestamp, TZ).strftime("%H:%M:%S"), "trip_updates", len(tus), "znanih", len(znane), "vozil", len(veh))
hm = lambda ts: datetime.fromtimestamp(ts, TZ).strftime("%H:%M") if ts else "--"
for t, tu in tus.items():
    if t in znane: continue
    route = tu.trip.route_id
    ln = conn.execute("SELECT train_no, headsign FROM trip WHERE route_id=? LIMIT 1", (route,)).fetchone()
    v = veh.get(t)
    print(f"\n=== NEZNANA ...{t[-12:]} vzorec ...{t.split('|')[2][-8:]} linija {ln and ln[0]} vozilo {(tu.vehicle.id or (v and v.vehicle.id) or '-')[:8]} lega {'da' if v else 'ne'} par {pari.get(t, {}).get('nasa','-')[-12:] if t in pari else '-'}")
    napo = {s.stop_id: (s.departure.time or s.arrival.time) for s in tu.stop_time_update if (s.departure.time or s.arrival.time)}
    stus = list(tu.stop_time_update)
    print("   postankov", len(stus), "z uro", len(napo), "prvi", name(stus[0].stop_id) if stus else "-", hm(napo.get(stus[0].stop_id)) if stus else "", "zadnji", name(stus[-1].stop_id) if stus else "-", hm(napo.get(stus[-1].stop_id)) if stus else "")
    # objavljene istega dne in proge
    kand = []
    for r in conn.execute("SELECT t.trip_id, t.start_s, t.headsign FROM trip t JOIN service_day d ON d.service_id=t.service_id AND d.date=? WHERE t.route_id=?", (danes, route)):
        s = {x["stop_id"]: COALESCE for x in []} if False else None
        sch = {x[0]: x[1] for x in conn.execute("SELECT stop_id, COALESCE(dep_s, arr_s) FROM sched WHERE trip_id=?", (r["trip_id"],))}
        skup = [napo[k] - (polnoc + sch[k]) for k in napo if k in sch]
        if not skup: continue
        med = statistics.median(skup)
        if -900 <= med <= 2400:
            kand.append((med, len(skup), r["trip_id"], r["start_s"], r["headsign"], len(sch)))
    kand.sort(key=lambda x: abs(x[0]))
    for med, n, tid, st, hs, ns in kand[:4]:
        vf = tid in tus
        nap = len([1 for s in tus[tid].stop_time_update if (s.departure.time or s.arrival.time)]) if vf else 0
        print(f"   kand ...{tid[-12:]} vzorec ...{tid.split('|')[2][-8:]} start {st//3600:02d}:{st%3600//60:02d} {hs} skupnih {n}/{ns} zamik {med/60:+.1f} min | v feedu pod svojim id {vf} (z uro {nap}) vozilo {'da' if tid in veh else 'ne'} | v paru z {nasa_v_paru.get(tid,'-')[-12:]}")
