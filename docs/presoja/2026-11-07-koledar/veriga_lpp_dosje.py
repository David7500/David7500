"""Veriga LPP: ponovitev pravila (razdelek 9) na legah iz dosje.sqlite (od 1. 11. 2026).

Pravilo ob t = T-10/5/1 min: lega vozila prejšnje (vir derp ali lpp) sveža <= 180 s,
ta vožnja brez lastne lege (stanje: zadnji zapis vozila ta vožnje s trip_id = ta),
vozilo > 200 m od končne prejšnje. Resnica: prejšnja še vozi (vozilo pride <= 100 m
od njene končne po polovici vožnje šele po t) in to vožnjo vozi isto vozilo.
Opozorilo: "še vozi" se meri iz iste lege, zato je neodvisen samo preizkus vozila.
Baza samo za branje. Uporaba: python3 veriga_lpp_dosje.py 2026-11-02 5
"""
import collections, json, math, sqlite3, sys, zlib
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Ljubljana")
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
dj = sqlite3.connect("file:/var/lib/kajros/dosje.sqlite?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()
polnoc = lambda d: int(datetime.combine(d, dtime(12), TZ).timestamp()) - 43200

def razd(a, b, x, y):
    k = math.pi / 180
    return 6371000 * math.hypot((y - b) * k * math.cos((a + x) / 2 * k), (x - a) * k)

_cache = {}
def serija(voz, vir, od, do):
    k = (voz, vir, od // 86400)
    if k not in _cache:
        pts = []
        for blob, in dj.execute("SELECT vsebina FROM tocke WHERE vozilo=? AND vir=? AND do_ts>=? AND od_ts<=?",
                                (voz, vir, od - 3600, do + 3600)):
            pts += [(p[0], p[1], p[2]) for p in json.loads(zlib.decompress(blob)) if p[1] is not None and p[2] is not None]
        pts.sort(); _cache[k] = pts
    return _cache[k]

d0 = date.fromisoformat(sys.argv[1]); n = int(sys.argv[2])
S = collections.defaultdict(lambda: [0, 0])      # (skupina, odmik) -> [prikazano, prav]
LIN = collections.defaultdict(lambda: [0, 0]); RAZ = []
S2 = collections.defaultdict(lambda: [0, 0]); NAP2 = collections.Counter()
V = collections.Counter(); PRAV = collections.Counter(); NAP = collections.Counter()
for i in range(n):
    ds = (d0 + timedelta(i)).isoformat(); P = polnoc(d0 + timedelta(i))
    rows = q("""SELECT t.trip_id, t.block_id, t.start_s, t.end_s, t.agency, t.train_no, t.first_seq, t.last_seq FROM trip t
      JOIN service_day sd ON sd.service_id=t.service_id AND sd.date=?
      WHERE t.network='avtobus' AND t.block_id IS NOT NULL AND t.agency IN ('1118','lpp')""", ds)
    byb = collections.defaultdict(list)
    for r in rows: byb[r[1]].append(r)
    pari = []
    for L in byb.values():
        for x in L:
            if x[2] is None: continue
            kand = [p for p in L if p[0] != x[0] and p[3] is not None and p[3] <= x[2]]
            if kand: pari.append((max(kand, key=lambda p: p[3]), x))
    tocka = {}
    for tid, seq, lat, lon in q("""SELECT s.trip_id, s.stop_seq, st.lat, st.lon FROM sched s JOIN station st ON st.stop_id=s.stop_id
            JOIN trip t ON t.trip_id=s.trip_id AND (s.stop_seq=t.first_seq OR s.stop_seq=t.last_seq)
            JOIN service_day sd ON sd.service_id=t.service_id AND sd.date=?
            WHERE t.block_id IS NOT NULL AND t.agency IN ('1118','lpp')""", ds):
        tocka[(tid, seq)] = (lat, lon)
    sv = collections.defaultdict(dict)
    for vir, voz, t, vz in q("SELECT vir, vozilo, trip_id, vzorcev FROM straza_opazeno WHERE dan=? AND vir IN ('derp','lpp')", ds):
        o = sv[(vir, t)]; o[voz] = o.get(voz, 0) + vz
    dom = lambda vir, t: (lambda o: max(o, key=o.get) if o else None)(sv.get((vir, t)))
    for p, x in pari:
        ag = x[4]; vir = "derp" if ag == "1118" else "lpp"
        vp, vx = dom(vir, p[0]), dom(vir, x[0])
        if not vp or not vx: continue
        konec = tocka.get((p[0], p[7])); zac = tocka.get((x[0], x[6]))
        if not konec: continue
        T = P + x[2]; pol = P + (p[2] + p[3]) // 2
        pts = serija(vp, vir, P, P + 86400)
        # prihod prejsnje: prva tocka <= 100 m od koncne po polovici voznje
        prih = next((t for t, la, lo in pts if t >= pol and razd(la, lo, *konec) <= 100), None)
        grupe = ["LPP prim" if ag == "1118" else "LPP mestni"] + (["LPP 25"] if ag == "1118" and x[5] == "25" else [])
        for o in (600, 300, 60):
            t = T - o
            if not any(a <= t for a, _, _ in pts[:1]): continue
            vozi = prih is None or prih > t
            pravo = vozi and vp == vx
            g = [pt for pt in pts if pt[0] <= t]
            sveza = bool(g) and t - g[-1][0] <= 180
            svoja = dj.execute("SELECT 1 FROM stanje WHERE vozilo=? AND vir=? AND trip_id=? AND ts BETWEEN ? AND ? LIMIT 1",
                               (vx, vir, x[0], t - 180, t)).fetchone() is not None
            dc = razd(g[-1][1], g[-1][2], *konec) if g else None
            kaze = sveza and not svoja and dc is not None and dc > 200
            # kot v zivo: prihod prejsnje na koncno ze zapisan v feedu (run, zadnji postanek) -> brez trditve
            rz = c.execute("SELECT feed_ts FROM run WHERE trip_id=? AND service_date=? AND stop_seq=?", (p[0], ds, p[7])).fetchone()
            zapisan = rz is not None and rz[0] is not None and rz[0] <= t
            kaze2 = kaze and not zapisan
            for gg in grupe:
                V[(gg, o)] += 1; PRAV[(gg, o)] += pravo
                if kaze2:
                    S2[(gg, o)][0] += 1; S2[(gg, o)][1] += pravo
                    if not pravo: NAP2[(gg, o, "prejsnja ze na cilju" if not vozi else "drugo vozilo")] += 1
                if kaze2 and gg == "LPP prim" and o == 300:
                    K = ("zvečer" if T - P >= 18 * 3600 else "dan", x[5])
                    LIN[K][0] += 1; LIN[K][1] += pravo
                    if not pravo and vozi: RAZ.append(((x[2] - p[3]) // 60, K[0], x[5], vp, vx))
                if kaze:
                    S[(gg, o)][0] += 1; S[(gg, o)][1] += pravo
                    if not pravo: NAP[(gg, o, "prejsnja ze na cilju" if not vozi else "drugo vozilo")] += 1
    print(ds, len(pari), file=sys.stderr, flush=True)
for (gg, o), nn in sorted(V.items()):
    s = S[(gg, o)]
    print(f"{gg:11s} T-{o//60:2d} min: parov {nn:5d}, trditev prava pri {100*PRAV[(gg,o)]/nn:3.0f} %; novo kaže {s[0]:5d} ({100*s[0]/nn:3.0f} %) "
          f"prav {100*s[1]/max(1,s[0]):5.1f} % | napak: ze na cilju {NAP[(gg,o,'prejsnja ze na cilju')]}, drugo vozilo {NAP[(gg,o,'drugo vozilo')]}")
    s = S2[(gg, o)]
    print(f"{'':11s}   + brez zapisanega prihoda v feedu: kaže {s[0]:5d} ({100*s[0]/nn:3.0f} %) prav {100*s[1]/max(1,s[0]):5.1f} % | napak: ze na cilju {NAP2[(gg,o,'prejsnja ze na cilju')]}, drugo vozilo {NAP2[(gg,o,'drugo vozilo')]}")

print("\nLPP prim T-5, po obdobju (kaže, prav):", {k: tuple(v) for k, v in sorted(LIN.items(), key=lambda kv: -kv[1][0])[:0]})
for per in ("dan", "zvečer"):
    a = sum(v[0] for k, v in LIN.items() if k[0] == per); b = sum(v[1] for k, v in LIN.items() if k[0] == per)
    print(f"  {per}: kaže {a} prav {100*b/max(1,a):.1f} %")
top = sorted(((v[0] - v[1], k, v) for k, v in LIN.items()), reverse=True)[:8]
print("  linije z največ napakami:", [(k, v[0], v[0] - v[1]) for _, k, v in top])
raz = sorted(r[0] for r in RAZ)
print("  drugo vozilo: n", len(raz), "razmik konec prejšnje -> začetek te (min), mediana", raz[len(raz)//2] if raz else None, "p90", raz[9*len(raz)//10] if raz else None)
