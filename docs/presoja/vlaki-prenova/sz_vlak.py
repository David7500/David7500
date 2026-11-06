import json, sqlite3, sys, zlib
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
v, od, do = sys.argv[1], sys.argv[2], sys.argv[3]
db = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
xs = []
for (vs,) in db.execute("SELECT vsebina FROM tocke WHERE vir='sz' AND vozilo=?", (v,)):
    xs += json.loads(zlib.decompress(vs))
xs.sort(key=lambda x: x[0])
for ts, lat, lon, sp in xs:
    t = datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d %H:%M:%S")
    if od <= t <= do and sp:
        print(t[11:], sp.get("Vrsta"), sp.get("Postaja"), sp.get("Zamuda_cas"), sp.get("Odhod"), sp.get("Predviden_prihod"), f"{lat:.4f},{lon:.4f}" if lat else "")
