"""Vožnje mestnega LPP z zamudo nad 40 min v run in koliko jih raste z uro
(nagib > 0,8 v obs). Argument: dan YYYY-MM-DD, drugi argument izpiše vožnje.

Zagon (samo branje): scp na arwen, nato
  ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python /tmp/fantom.py ARGUMENTI'
"""
import sqlite3, sys
conn = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
dan = sys.argv[1]
trips = [r[0] for r in conn.execute(
    "SELECT DISTINCT r.trip_id FROM run r CROSS JOIN trip t ON t.trip_id=r.trip_id "
    "WHERE t.agency='lpp' AND r.service_date=? AND COALESCE(r.delay_dep,r.delay_arr) > 2400", (dan,))]
ura = drugo = 0
for tid in trips:
    no, = conn.execute("SELECT train_no FROM trip WHERE trip_id=?", (tid,)).fetchone()
    # za vsak postanek: zaporedje (feed_ts, zamuda) v obs; nagib zadnjih vrednosti
    nagibi = []
    for (seq,) in conn.execute("SELECT DISTINCT stop_seq FROM obs WHERE trip_id=? AND service_date=?", (tid, dan)):
        v = conn.execute("SELECT feed_ts, COALESCE(delay_dep,delay_arr) FROM obs WHERE trip_id=? AND service_date=? AND stop_seq=? ORDER BY feed_ts", (tid, dan, seq)).fetchall()
        v = [x for x in v if x[1] is not None]
        big = [x for x in v if x[1] > 1200]
        if len(big) >= 3:
            dt = big[-1][0] - big[0][0]
            if dt > 0:
                nagibi.append((big[-1][1] - big[0][1]) / dt)
    if not nagibi: continue
    nagibi.sort(); med = nagibi[len(nagibi)//2]
    if med > 0.8: ura += 1
    else: drugo += 1
    if len(sys.argv) > 2: print(no, tid.split("|")[1][:8], "postankov z rastjo", len(nagibi), "mediana nagiba", round(med, 2))
print(dan, "voženj nad 40 min", len(trips), "raste z uro (nagib>0,8)", ura, "drugo", drugo)
