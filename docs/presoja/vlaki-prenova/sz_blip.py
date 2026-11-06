import json, sqlite3, zlib
from collections import Counter, defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
db = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
dn = defaultdict(list)
for vozilo, vs in db.execute("SELECT vozilo, vsebina FROM tocke WHERE vir='sz' AND vozilo LIKE 'vlak-%'"):
    for ts, lat, lon, sp in json.loads(zlib.decompress(vs)):
        if sp: dn[(vozilo, datetime.fromtimestamp(ts, TZ).date().isoformat())].append((ts, sp))
def odh(ts, hhmm):
    try: h, m = map(int, hhmm.split(":"))
    except Exception: return None
    d = datetime.fromtimestamp(ts, TZ).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() + h*3600 + m*60
    while d - ts > 43200: d -= 86400
    while ts - d > 43200: d += 86400
    return d
tip = Counter(); blip_ts = Counter(); ev = []; v0 = []; kljuc = lambda sp: (sp.get("Vrsta"), sp.get("Postaja"), sp.get("Zamuda_cas"))
for k, xs in dn.items():
    xs.sort(key=lambda x: x[0])
    # odstrani enojne odklone A,B,A (po jedru)
    ok = [True]*len(xs)
    for i in range(1, len(xs)-1):
        a, b, c = xs[i-1][1], xs[i][1], xs[i+1][1]
        if a.get("Zamuda_cas") == c.get("Zamuda_cas") and b.get("Zamuda_cas") != a.get("Zamuda_cas") and a.get("Vrsta") == c.get("Vrsta"):
            za, zb = a.get("Zamuda_cas") or 0, b.get("Zamuda_cas") or 0
            tip["0" if zb == 0 else "višja" if zb > za else "nižja"] += 1
            blip_ts[xs[i][0]] += 1; ok[i] = False
    ys = [x for x, o in zip(xs, ok) if o]
    prej = None; prvi1 = None; zad0 = None
    for ts, sp in ys:
        if sp.get("Vrsta") == 0: zad0 = sp.get("Zamuda_cas")
        if sp.get("Vrsta") == 1 and prvi1 is None: prvi1 = (ts, sp)
        if prej and prej[1].get("Vrsta") == 1 and sp.get("Vrsta") == 1 and prej[1].get("Zamuda_cas") != sp.get("Zamuda_cas"):
            o = odh(ts, sp.get("Odhod") or "")
            ev.append((sp["Zamuda_cas"] - prej[1]["Zamuda_cas"], None if o is None else ts - o, sp["Zamuda_cas"], prej[1].get("Postaja") == sp.get("Postaja")))
        prej = (ts, sp)
    if zad0 is not None and prvi1: v0.append((zad0, prvi1[1].get("Zamuda_cas")))
print("enojnih odklonov:", dict(tip), "na voženj-dan:", round(sum(tip.values())/len(dn), 2))
po = Counter(blip_ts.values()); print("koliko vlakov naenkrat odkloni (ts -> n):", sorted(po.items())[:12])
print("pravih sprememb:", len(ev), "na voženj-dan:", round(len(ev)/len(dn), 2))
b = Counter("?" if e[1] is None else "<=75" if abs(e[1]) <= 75 else "75-180" if abs(e[1]) <= 180 else ">180" for e in ev); print("|ts-Odhod|:", dict(b))
b2 = Counter(("gor" if e[0] > 0 else "dol", "<=75" if e[1] is not None and abs(e[1]) <= 75 else "drugo") for e in ev); print("smer x registracija:", dict(b2))
nic = sum(1 for e in ev if e[2] == 0 and e[0] <= -3); print("pravih padcev na 0 z >=3:", nic)
print("ista postaja ob spremembi:", Counter(e[3] for e in ev))
dd = Counter(max(-6, min(6, e[0])) for e in ev); print("sprememba min:", sorted(dd.items()))
# Vrsta 0 zamuda proti prvi zamudi v vožnji
r = Counter(); 
for z0, z1 in v0:
    r[("0" if not z0 else ">0", "isto±1" if abs((z0 or 0)-(z1 or 0)) <= 1 else "višje" if (z0 or 0) > (z1 or 0) else "nižje")] += 1
print("Vrsta0 zadnja zamuda proti prvi vožnji:", dict(r))
