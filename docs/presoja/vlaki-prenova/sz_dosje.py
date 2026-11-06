"""Analiza vzorcev zemljevida SŽ iz dosjeja: dvojniki, dogodki spremembe zamude."""
import json, sqlite3, sys, zlib
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
db = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
vz = defaultdict(list)
for vozilo, vsebina in db.execute("SELECT vozilo, vsebina FROM tocke WHERE vir='sz' AND vozilo LIKE 'vlak-%'"):
    for ts, lat, lon, sp in json.loads(zlib.decompress(vsebina)):
        if sp:
            vz[vozilo].append((ts, lat, lon, sp))
def dan(ts): return datetime.fromtimestamp(ts, TZ).date().isoformat()
def polnoc(ts):
    d = datetime.fromtimestamp(ts, TZ); return d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
def odhod_ts(ts, hhmm):
    try: h, m = map(int, hhmm.split(":"))
    except Exception: return None
    t = polnoc(ts) + h*3600 + m*60
    while t - ts > 43200: t -= 86400
    while ts - t > 43200: t += 86400
    return t
dnevi = defaultdict(list)
for v, xs in vz.items():
    for x in xs: dnevi[(v, dan(x[0]))].append(x)
print("voženj-dni:", len(dnevi))
# 1) dvojniki: isti ts, dva različna vzorca istega vlaka
gh = {}
for k, xs in dnevi.items():
    po = defaultdict(set)
    for ts, lat, lon, sp in xs:
        po[ts].add((sp.get("Vrsta"), sp.get("St_postaje"), sp.get("Zamuda_cas")))
    dv = [(ts, s) for ts, s in po.items() if len(s) > 1]
    if dv: gh[k] = dv
print("voženj-dni z dvojnikom:", len(gh), "po dnevih:", sorted(Counter(k[1] for k in gh).items()))
razl = Counter(); vrste = Counter(); trajanje = []
for k, dv in gh.items():
    dv.sort(); trajanje.append((dv[-1][0]-dv[0][0])/60)
    for ts, s in dv:
        z = sorted(x[2] or 0 for x in s); razl[min(30, z[-1]-z[0])//5*5] += 1
        vrste[tuple(sorted(str(x[0]) for x in s))] += 1
print("razlika zamud v dvojniku (5-min koši):", sorted(razl.items()))
print("Vrsta para:", vrste.most_common(6))
trajanje.sort(); print("trajanje dvojnika min (p50,p90,max):", trajanje[len(trajanje)//2] if trajanje else None, trajanje[int(len(trajanje)*.9)] if trajanje else None, trajanje[-1] if trajanje else None)
print("primeri:", [f"{k[0]} {k[1]} n={len(v)}" for k, v in list(gh.items())[:25]])
# 2) dogodki spremembe zamude (samo dnevi brez dvojnika, Vrsta 1)
ev = []; post_dni = Counter(); nazaj = Counter()
for k, xs in dnevi.items():
    if k in gh: continue
    xs.sort(key=lambda x: x[0]); prej = None; videne = []
    for ts, lat, lon, sp in xs:
        if sp.get("Vrsta") != 1: prej = None; continue
        p = sp.get("Postaja")
        if not videne or videne[-1] != p:
            if p in videne: nazaj[(prej or {}).get("Zamuda_cas", 0) < (sp.get("Zamuda_cas") or 0)] += 1
            videne.append(p)
        if prej and prej.get("Zamuda_cas") != sp.get("Zamuda_cas") and sp.get("Zamuda_cas") is not None and prej.get("Zamuda_cas") is not None:
            o = odhod_ts(ts, sp.get("Odhod") or "")
            ev.append((k, ts, prej["Zamuda_cas"], sp["Zamuda_cas"], prej.get("Postaja"), p, None if o is None else ts - o))
        prej = sp
    for p in set(videne): post_dni[p] += 1
print("dogodkov spremembe:", len(ev), "nazaj (z večjo zamudo True):", dict(nazaj))
d = Counter(); 
for e in ev:
    x = e[6]
    d["brez" if x is None else "<=60" if abs(x) <= 60 else "<=120" if abs(x) <= 120 else "<=300" if abs(x) <= 300 else ">300"] += 1
print("|ts - Odhod| po spremembi:", dict(d))
dl = Counter(max(-10, min(10, e[3]-e[2])) for e in ev); print("sprememba (min):", sorted(dl.items()))
nicla = sum(1 for e in ev if e[3] == 0 and e[2] >= 3); print("skok na 0 iz >=3:", nicla)
ppo = Counter(e[5] for e in ev); ista = Counter(e[5] for e in ev if e[4] == e[5])
print("postaja po spremembi: dogodkov / dni s postajo / delež sprememb brez menjave postaje")
for p, n in ppo.most_common(60):
    print(f"  {p}: {n} / {post_dni[p]} / {ista[p]}")
