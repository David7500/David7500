"""Podatki za Pogl. 3 strani O nas: omrežje, eno jutro voženj, zamude ene
vožnje po dnevih. Teče na strežniku nad bazo samo za branje in izpiše JSON.

    ssh -o BatchMode=yes david@192.168.1.46 'nice -n 19 python3 - | gzip -6' \
        < izvoz_karte.py > karta-surovo.json.gz

Koordinate: lokalna ekvidistantna projekcija okrog 46,12° S, 14,82° V v
metrih; x proti vzhodu, z proti jugu (kot v three.js).
"""
import json
import math
import sqlite3
import sys

DAN = '2026-10-01'
OD, DO = 6 * 3600 + 50 * 60, 8 * 3600 + 10 * 60
LAT0, LON0 = 46.12, 14.82
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0

c = sqlite3.connect('file:/var/lib/kajros/kajros.sqlite?mode=ro', uri=True)
c.row_factory = sqlite3.Row


def P(lat, lon):
    return ((lon - LON0) * KX, (LAT0 - lat) * KY)


def dp(pts, tol):
    """Douglas-Peucker v metrih."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz) or 1e-9
    i_max, d_max = 0, -1.0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = abs(dz * (p[0] - a[0]) - dx * (p[1] - a[1])) / L
        if d > d_max:
            i_max, d_max = i, d
    if d_max <= tol:
        return [a, b]
    return dp(pts[:i_max + 1], tol)[:-1] + dp(pts[i_max:], tol)


out = {'dan': DAN, 'lat0': LAT0, 'lon0': LON0}

# --- železniško omrežje: elementarni odseki ---
proge = []
geo_odseka = {}
for r in c.execute("SELECT from_id, to_id, elementary, COALESCE(osm, geojson) AS g FROM edge"):
    g = json.loads(r['g'])
    co = g['coordinates'] if g['type'] == 'LineString' else [p for l in g['coordinates'] for p in l]
    pts = [P(lat, lon) for lon, lat in co]
    geo_odseka[(r['from_id'], r['to_id'])] = pts
    if r['elementary']:
        proge.append([round(v) for p in dp(pts, 40) for v in p])
out['proge'] = proge

# --- postaje vlakov (za oznake) ---
post = {}
for r in c.execute("SELECT DISTINCT s.stop_id, st.name, st.lat, st.lon FROM sched s JOIN trip t ON t.trip_id = s.trip_id "
                   "JOIN station st ON st.stop_id = s.stop_id WHERE t.network = 'zeleznica'"):
    post[r['stop_id']] = (r['name'], *P(r['lat'], r['lon']))
out['postaje'] = [[n, round(x), round(z)] for n, x, z in post.values()]

# --- avtobusno omrežje: trase voženj tega dne, zaokrožene na mrežo 120 m ---
MREZA = 120.0
odseki = set()
oblike = [r['shape_id'] for r in c.execute(
    "SELECT DISTINCT t.shape_id FROM trip t JOIN service_day s ON s.service_id = t.service_id AND s.date = ? "
    "WHERE t.network = 'avtobus' AND t.shape_id IS NOT NULL", (DAN,))]
for sid in oblike:
    r = c.execute("SELECT COALESCE(osm, points) AS p, osm IS NOT NULL AS je_osm FROM shape WHERE shape_id = ?", (sid,)).fetchone()
    if not r:
        continue
    raw = json.loads(r['p'])
    if isinstance(raw, dict):
        co = raw['coordinates']
        pts = [P(lat, lon) for lon, lat in co]
    else:
        # [[lat, lon], ...] ali seznam delov [[[lat, lon], ...], ...]
        deli = raw if raw and isinstance(raw[0][0], list) else [raw]
        pts = [P(p[0], p[1]) for d in deli for p in d]
    prej = None
    for x, z in dp(pts, 60):
        k = (round(x / MREZA), round(z / MREZA))
        if prej is not None and k != prej:
            # vmesne celice, da so odseki kratki in se prekrivajoči zlijejo
            n = max(abs(k[0] - prej[0]), abs(k[1] - prej[1]))
            for i in range(1, n + 1):
                q = (round(prej[0] + (k[0] - prej[0]) * i / n), round(prej[1] + (k[1] - prej[1]) * i / n))
                p0 = (round(prej[0] + (k[0] - prej[0]) * (i - 1) / n), round(prej[1] + (k[1] - prej[1]) * (i - 1) / n))
                if q != p0:
                    odseki.add((min(p0, q), max(p0, q)))
        prej = k
out['avtobusi_mreza'] = MREZA
out['avtobusi'] = [v for a, b in odseki for v in (*a, *b)]

# --- eno jutro: vse vožnje med 6.50 in 8.10 z zapisano zamudo ---
voznje = []
st_vlakov = st_bus = 0
trips = c.execute(
    "SELECT t.trip_id, t.train_no, t.network, t.mode, t.agency, t.start_s, t.end_s FROM trip t "
    "JOIN service_day s ON s.service_id = t.service_id AND s.date = ? "
    "WHERE t.start_s < ? AND t.end_s > ?", (DAN, DO, OD)).fetchall()
lokacije = {r['stop_id']: P(r['lat'], r['lon']) for r in c.execute("SELECT stop_id, lat, lon FROM station")}
for t in trips:
    run = {r['stop_seq']: r for r in c.execute(
        "SELECT stop_seq, delay_arr, delay_dep FROM run WHERE trip_id = ? AND service_date = ?", (t['trip_id'], DAN))}
    if not run:
        continue
    sched = c.execute("SELECT stop_seq, stop_id, arr_s, dep_s FROM sched WHERE trip_id = ? ORDER BY stop_seq",
                      (t['trip_id'],)).fetchall()
    if len(sched) < 2:
        continue
    # zamuda na postanku: zapisana, sicer zadnja znana (napoved), pred prvo prva
    zad = None
    zamude = []
    prva = next((run[s['stop_seq']] for s in sched if s['stop_seq'] in run), None)
    for s in sched:
        r = run.get(s['stop_seq'])
        if r is not None:
            d_dep = r['delay_dep'] if r['delay_dep'] is not None else r['delay_arr']
            d_arr = r['delay_arr'] if r['delay_arr'] is not None else d_dep
            zad = d_dep
        else:
            base = zad if zad is not None else (prva['delay_dep'] if prva['delay_dep'] is not None else prva['delay_arr'])
            d_arr = d_dep = base
        zamude.append((d_arr or 0, d_dep or 0))
    zeleznica = t['network'] == 'zeleznica'
    kljuci = []
    for i, s in enumerate(sched):
        x, z = lokacije[s['stop_id']]
        da, dd = zamude[i]
        ta = (s['arr_s'] if s['arr_s'] is not None else s['dep_s']) + da
        td = (s['dep_s'] if s['dep_s'] is not None else s['arr_s']) + dd
        kljuci.append((ta, x, z, da))
        if td > ta:
            kljuci.append((td, x, z, dd))
        if i + 1 < len(sched) and zeleznica:
            g = geo_odseka.get((s['stop_id'], sched[i + 1]['stop_id']))
            if g and len(g) > 2:
                g = dp(g, 80)
                nx = sched[i + 1]
                ta2 = (nx['arr_s'] if nx['arr_s'] is not None else nx['dep_s']) + zamude[i + 1][0]
                dol = [0.0]
                for a, b in zip(g, g[1:]):
                    dol.append(dol[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
                for k in range(1, len(g) - 1):
                    f = dol[k] / dol[-1]
                    kljuci.append((td + (ta2 - td) * f, g[k][0], g[k][1], dd + (zamude[i + 1][0] - dd) * f))
    kljuci.sort(key=lambda k: k[0])
    # obreži na okno
    if kljuci[-1][0] < OD or kljuci[0][0] > DO:
        continue
    vrsta = 0 if zeleznica else (2 if t['agency'] == '1118' else 1)
    if zeleznica:
        st_vlakov += 1
    else:
        st_bus += 1
    voznje.append([vrsta, t['train_no']] + [v for k in kljuci if OD - 900 <= k[0] <= DO + 900
                                            for v in (round(k[0] - 7 * 3600), round(k[1]), round(k[2]), round(k[3]))])
out['voznje'] = voznje
out['stevilo'] = {'vlaki': st_vlakov, 'avtobusi': st_bus}

# po voznem redu aktivnih med 7. in 8. uro (za besedilo)
for net in ('zeleznica', 'avtobus'):
    out[f'po_voznem_redu_{net}'] = c.execute(
        "SELECT count(*) FROM trip t JOIN service_day s ON s.service_id = t.service_id AND s.date = ? "
        "WHERE t.network = ? AND t.start_s < ? AND t.end_s > ?", (DAN, net, 8 * 3600, 7 * 3600)).fetchone()[0]
    out[f'zapisanih_{net}'] = c.execute(
        "SELECT count(DISTINCT t.trip_id) FROM trip t JOIN service_day s ON s.service_id = t.service_id AND s.date = ? "
        "JOIN run r ON r.trip_id = t.trip_id AND r.service_date = ? "
        "WHERE t.network = ? AND t.start_s < ? AND t.end_s > ?", (DAN, DAN, net, 8 * 3600, 7 * 3600)).fetchone()[0]

# --- ena vožnja po dnevih: jutranji vlak v Ljubljano z največ zapisanimi dnevi ---
kand = c.execute("""
    SELECT t.trip_id, t.train_no, t.headsign, count(DISTINCT r.service_date) AS dni
    FROM trip t JOIN run r ON r.trip_id = t.trip_id
    WHERE t.network = 'zeleznica' AND t.end_s BETWEEN 7*3600 AND 8*3600+30*60
      AND t.headsign LIKE 'Ljubljana%'
    GROUP BY t.trip_id ORDER BY dni DESC LIMIT 8""").fetchall()
out['kandidati'] = [dict(k) for k in kand]
# IC 351 Ljubljana - Maribor: znana relacija, enako zapisanih dni kot prvi kandidat
VRSTA = '453053'
izbran = next((k for k in kand if k['trip_id'] == VRSTA), kand[0] if kand else None)
if izbran:
    tid = izbran['trip_id']
    sched = c.execute("SELECT s.stop_seq, st.name, st.lat, st.lon, s.arr_s, s.dep_s FROM sched s "
                      "JOIN station st ON st.stop_id = s.stop_id WHERE s.trip_id = ? ORDER BY s.stop_seq", (tid,)).fetchall()
    dni = [r['service_date'] for r in c.execute(
        "SELECT DISTINCT service_date FROM run WHERE trip_id = ? ORDER BY service_date", (tid,))]
    tab = []
    for d in dni:
        rr = {r['stop_seq']: r for r in c.execute(
            "SELECT stop_seq, delay_arr, delay_dep FROM run WHERE trip_id = ? AND service_date = ?", (tid, d))}
        vr = []
        for s in sched:
            r = rr.get(s['stop_seq'])
            v = None
            if r is not None:
                v = r['delay_dep'] if r['delay_dep'] is not None else r['delay_arr']
            vr.append(v)
        tab.append([d, vr])
    ids = [r['stop_id'] for r in c.execute("SELECT stop_id FROM sched WHERE trip_id = ? ORDER BY stop_seq", (tid,))]
    # pot po elementarnih odsekih (Dijkstra po dolžini), ker IC postaje preskakuje
    import heapq
    sosedi = {}
    for r in c.execute("SELECT from_id, to_id, km FROM edge WHERE elementary = 1"):
        sosedi.setdefault(r['from_id'], []).append((r['to_id'], r['km'], (r['from_id'], r['to_id']), False))
        sosedi.setdefault(r['to_id'], []).append((r['from_id'], r['km'], (r['from_id'], r['to_id']), True))

    def pot_med(a, b):
        dist, prej, q = {a: 0.0}, {}, [(0.0, a)]
        while q:
            d, u = heapq.heappop(q)
            if u == b:
                break
            if d > dist.get(u, 1e18):
                continue
            for v, km, k, obr in sosedi.get(u, []):
                nd = d + km
                if nd < dist.get(v, 1e18):
                    dist[v] = nd; prej[v] = (u, k, obr); heapq.heappush(q, (nd, v))
        if b not in prej:
            return None
        deli, u = [], b
        while u != a:
            pu, k, obr = prej[u]
            g = geo_odseka[k]
            deli.append(list(reversed(g)) if obr else g)
            u = pu
        out_ = []
        for g in reversed(deli):
            out_ += g if not out_ else g[1:]
        return out_

    pot = []
    for i in range(len(ids) - 1):
        g = geo_odseka.get((ids[i], ids[i + 1])) or pot_med(ids[i], ids[i + 1])
        if g is None:
            g = [lokacije[ids[i]], lokacije[ids[i + 1]]]
        g = dp(g, 60)
        pot += [round(v) for p in (g if not pot else g[1:]) for v in p]
    out['vrsta'] = {
        'pot': pot,
        'trip_id': tid, 'train_no': izbran['train_no'], 'headsign': izbran['headsign'],
        'postaje': [[s['name'], *[round(v) for v in P(s['lat'], s['lon'])], s['arr_s'] or s['dep_s']] for s in sched],
        'dnevi': tab,
    }

json.dump(out, sys.stdout, ensure_ascii=False, separators=(',', ':'))
