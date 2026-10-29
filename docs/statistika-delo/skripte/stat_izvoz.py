import sys, json
sys.path.insert(0, "/var/tmp/kajros-dev")
from kajros import db, stats
conn = db.connect(); db.init(conn)
out = []
for kind in ("stat_napovedi", "stat_prevozniki", "stat_sz", "stat_relacije"):
    for net in ("zeleznica", "avtobus"):
        stats.summary_build(conn, kind, net, 90)
        r = conn.execute("SELECT kind, network, days, computed_at, through, took_ms, runs, payload FROM povzetek WHERE kind=? AND network=? AND days=90", (kind, net)).fetchone()
        out.append(list(r))
json.dump(out, open("/var/tmp/stat_izvoz.json", "w"))
print("ok", [(r[0], r[1], r[5]) for r in out])
voz = [list(r) for r in conn.execute("SELECT pot, network, agency, st, podatki, izracunano FROM stat_voznja")]
json.dump(voz, open("/var/tmp/stat_voznja.json", "w"))
print("voženj", len(voz), "bajtov", sum(len(r[4]) for r in voz))
