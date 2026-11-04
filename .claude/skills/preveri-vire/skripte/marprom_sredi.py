"""Marprom: izpadi sredi vožnje -- ali je vozilo staro vožnjo res vozilo naprej?

Sledi `NextStopPointId` iz dosjeja (`tocke`) med izpadom. Samo branje; zagon kot
`marprom_izpadi.py`, enaka argumenta.
"""
import sqlite3, json, collections, sys, zlib
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
OD = int(datetime.fromisoformat(sys.argv[1]).replace(tzinfo=TZ).timestamp())
DO = int(datetime.fromisoformat(sys.argv[2]).replace(tzinfo=TZ).timestamp())
d = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True, timeout=30)
k = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True, timeout=30)
polnoc = lambda dan: int(datetime.fromisoformat(dan + " 12:00").replace(tzinfo=TZ).timestamp()) - 43200
trip = {r[0]: r[1:] for r in k.execute(
    "SELECT trip_id, route_id, shape_id, train_no, start_s, end_s FROM trip WHERE agency='marprom'")}
stops = collections.defaultdict(list)
for t, q, sid in k.execute(
        "SELECT s.trip_id, s.stop_seq, s.stop_id FROM sched s JOIN trip t USING(trip_id) "
        "WHERE t.agency='marprom' ORDER BY 1, 2"):
    stops[t].append((q, sid))
po_vozilu = collections.defaultdict(list)
for r in d.execute("SELECT vozilo, ts, trip_id, dan, razlogi, sprotno FROM stanje "
                   "WHERE vir='marprom' AND ts BETWEEN ? AND ? ORDER BY vozilo, ts", (OD, DO)):
    po_vozilu[r[0]].append(r[1:])

def tocke(voz, t0, t1):
    out = []
    for od, do, blob in d.execute("SELECT od_ts, do_ts, vsebina FROM tocke WHERE vozilo=? AND vir='marprom' "
                                  "AND do_ts>=? AND od_ts<=? ORDER BY od_ts", (voz, t0, t1)):
        for ts, lat, lon, spr in json.loads(zlib.decompress(blob)):
            if t0 <= ts <= t1 + 20:
                out.append((ts, (spr or {}).get("NextStopPointId"), (spr or {}).get("Predicted")))
    return sorted(out, key=lambda x: x[0])

sk = collections.Counter(); izgubljeno = collections.Counter(); prim = collections.defaultdict(list)
zaseda = 0
for voz, vr in po_vozilu.items():
    i = 0
    while i < len(vr) - 1:
        if not (vr[i][1] and not vr[i + 1][1]):
            i += 1; continue
        z = vr[i + 1]
        j = i + 1
        while j < len(vr) and not vr[j][1]:
            j += 1
        konec = vr[j][0] if j < len(vr) else None
        a, dan = vr[i][1], vr[i][2]
        raz = [x for x in z[3].split(",") if x in ("ni_prihoda", "ni_v_voznem_redu", "zasedena", "vec")]
        raz = raz[0] if raz else "-"
        nasl = str(json.loads(z[4] or "{}").get("NextStopPointId") or "")
        seqs = dict((sid, q) for q, sid in reversed(stops[a])) if a in stops else {}
        q0 = seqs.get("mp-" + nasl)
        if a not in trip or q0 is None or (konec is None):
            i = j; continue
        ena = polnoc(dan) + trip[a][4]
        q_last = stops[a][-1][0]
        do_konca = (ena - z[0]) / 60
        if q0 >= q_last - 1 or do_konca < 2:
            i = j; continue                 # zadnja dva postanka: menjava je blizu, ni "sredi"
        if ena < z[0] - 1800:
            i = j; continue
        # do konca izpada ali najdlje do konca A + 30 min
        do = min(konec, ena + 1800)
        tt = tocke(voz, z[0], do)
        pot = [t for t in tt if t[1]]
        prejsnji = q0; zapustil = None; maks = q0
        for ts, n, _ in pot:
            q = seqs.get("mp-" + str(n))
            if q is None or q < prejsnji:
                zapustil = ts; break
            prejsnji = q; maks = max(maks, q)
        if zapustil is None:
            vrsta = "ostal_na_A"
        elif maks > q0:
            vrsta = "nekaj_napredka_nato_ven"
        else:
            vrsta = "takoj_ven"
        ista = (vr[j][1], vr[j][2]) == (a, dan)
        sk[(raz, vrsta, "ista" if ista else "druga")] += 1
        izgubljeno[(raz, vrsta)] += (konec - z[0])
        prim[(raz, vrsta)].append((voz, z[0], konec, a, vr[j][1], q0, maks, q_last))
        i = j
print("razlog | kaj je vozilo naredilo | po izpadu | n")
for ky, n in sorted(sk.items()):
    print(" ", ky, n)
print("izgubljene minute po (razlog, vrsta):")
for ky, n in sorted(izgubljeno.items()):
    print(" ", ky, round(n / 60))
for ky in prim:
    if ky[1] != "ostal_na_A":
        for x in prim[ky][:3]:
            print(ky, x[0], datetime.fromtimestamp(x[1], TZ).strftime("%d.%m %H:%M:%S"), x[2]-x[1], trip[x[3]][2], x[3], "->", x[4], "q", x[5], x[6], x[7])
