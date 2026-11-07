import sqlite3, json, collections, datetime
from zoneinfo import ZoneInfo
d = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
k = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
kl = lambda i: i.replace("(Železniški)", "").strip().casefold()
nase = {kl(n) for (n,) in k.execute("SELECT DISTINCT s.name FROM station s JOIN sched x USING(stop_id) JOIN trip t USING(trip_id) WHERE t.network='zeleznica' AND t.mode!='bus'")}
c = collections.Counter(); vl = collections.defaultdict(set)
od = datetime.datetime(2026,10,31,tzinfo=ZoneInfo("Europe/Ljubljana")).timestamp()
for v, spr in d.execute("SELECT vozilo, sprotno FROM stanje WHERE vir='sz' AND vozilo LIKE 'vlak-%' AND ts>=?", (od,)):
    s = json.loads(spr) if spr else {}
    p = s.get("Postaja")
    if p and s.get("Vrsta") == 1:
        c[p] += 1
        if kl(p) not in nase: vl[p].add(v)
print("imen", len(c), "stanj", sum(c.values()))
for p in vl: print("NI:", p, c[p], "vlakov", len(vl[p]), sorted(vl[p])[:6])
