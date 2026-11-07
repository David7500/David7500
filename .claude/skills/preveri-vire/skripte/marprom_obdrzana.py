"""Marprom: ali obdržana vožnja drži (`obdrzana` v dosjeju, od fc2bde6), samo branje.

Za vsak niz vzorcev `obdrzana` istega vozila pove, kako se konča: Marprom vozilu
spet pokaže isto vožnjo (potrjena), drugo vozilo jo prevzame (`izpodrinjena`),
izpuščena po meji `OBDRZI_PO_KONCU_S` ali druga vožnja. Med nizom: ali je
naslednje postajališče na obdržani vožnji, ali vozilo stoji na končni. Zagon kot
`marprom_izpadi.py`, enaka argumenta.
"""
import sqlite3, json, collections, sys
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
OD = int(datetime.fromisoformat(sys.argv[1]).replace(tzinfo=TZ).timestamp())
DO = int(datetime.fromisoformat(sys.argv[2]).replace(tzinfo=TZ).timestamp())
d = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True, timeout=30)
k = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True, timeout=30)
polnoc = lambda dan: int(datetime.fromisoformat(dan + " 12:00").replace(tzinfo=TZ).timestamp()) - 43200
trip = {r[0]: r[1:] for r in k.execute(
    "SELECT trip_id, train_no, start_s, end_s FROM trip WHERE agency='marprom'")}
stops = collections.defaultdict(list)
for t, sid in k.execute("SELECT s.trip_id, s.stop_id FROM sched s JOIN trip t USING(trip_id) "
                        "WHERE t.agency='marprom' ORDER BY s.trip_id, s.stop_seq"):
    stops[t].append(sid)
po_vozilu = collections.defaultdict(list)
for r in d.execute("SELECT vozilo, ts, trip_id, dan, razlogi, sprotno FROM stanje "
                   "WHERE vir='marprom' AND ts BETWEEN ? AND ? ORDER BY vozilo, ts", (OD, DO + 3600)):
    po_vozilu[r[0]].append(r[1:])

def nasl(row):
    return "mp-" + str(json.loads(row[4] or "{}").get("NextStopPointId") or "")

izid = collections.Counter(); minute = collections.Counter()
na_voznji = collections.Counter(); na_koncni = collections.Counter(); potem = collections.Counter()
po_koncu = collections.Counter(); primeri = collections.defaultdict(list)
for voz, vr in po_vozilu.items():
    i = 0
    while i < len(vr):
        if "obdrzana" not in vr[i][3].split(",") or vr[i][0] > DO:
            i += 1; continue
        a, dan = vr[i][1], vr[i][2]
        j = i
        while j < len(vr) and "obdrzana" in vr[j][3].split(",") and vr[j][1] == a:
            j += 1
        if j == len(vr):
            izid["odprto"] += 1; break
        konec = vr[j]
        trajanje = konec[0] - vr[i][0]
        if konec[1] == a:
            vrsta = "potrjena"
        elif konec[1] is None and "izpodrinjena" in konec[3]:
            vrsta = "izpodrinjena"
        elif konec[1] is None:
            r = [x for x in konec[3].split(",") if x in ("ni_prihoda", "ni_v_voznem_redu", "zasedena")]
            vrsta = "izpuscena_" + (r[0] if r else "-")
        else:
            vrsta = "druga_voznja"
        izid[vrsta] += 1; minute[vrsta] += trajanje
        sl = stops.get(a, [])
        for row in vr[i:j]:
            ns = nasl(row)
            na_voznji["na" if ns in sl else "ni_na"] += 1
        ns_k = nasl(vr[j - 1])
        koncna = bool(sl) and ns_k in sl[-2:]
        na_koncni[(vrsta, "koncna" if koncna else "sredi",
                   "miruje" if "miruje" in vr[j - 1][3] else "vozi")] += 1
        if a in trip:
            po_koncu[(vrsta, "pred_koncem_vr" if konec[0] <= polnoc(dan) + trip[a][2] else "po_koncu_vr")] += 1
        # kam vozilo gre v 30 min po koncu niza
        nasl_v = next((row for row in vr[j:] if row[1] and row[0] <= konec[0] + 1800), None)
        potem[(vrsta, "brez" if nasl_v is None else ("ista" if nasl_v[1] == a else "druga"))] += 1
        primeri[vrsta].append((voz, vr[i][0], trajanje, a, trip.get(a, ("?",))[0], ns_k, koncna))
        i = j
print("nizov obdrzana", sum(izid.values()), dict(izid))
print("minute", {x: round(y / 60) for x, y in minute.items()})
print("vzorci med nizom, naslednje postajalisce na obdrzani voznji", dict(na_voznji))
print("konec niza (vrsta, kje, gibanje)"); [print(" ", x, n) for x, n in sorted(na_koncni.items())]
print("konec glede na konec po voznem redu"); [print(" ", x, n) for x, n in sorted(po_koncu.items())]
print("v 30 min po koncu niza vozilo na voznji"); [print(" ", x, n) for x, n in sorted(potem.items())]
for vrsta in ("izpodrinjena", "druga_voznja"):
    for p in primeri.get(vrsta, [])[:8]:
        print(vrsta, p[0], datetime.fromtimestamp(p[1], TZ).strftime("%d.%m %H:%M"), p[2], "s", p[3], p[4], p[5], "koncna" if p[6] else "")
