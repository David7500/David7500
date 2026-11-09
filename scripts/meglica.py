"""Meglica: vsaka pot GET z grdimi vrednostmi parametrov; šteje 500 in počasne.

    ./venv/bin/python scripts/meglica.py [naslov] [izpis.json]

Poti in parametri iz `kajros.api.app` (tudi strani, ki jih OpenAPI ne kaže).
Ena mutacija naenkrat, ostali parametri smiselni, vzorci (vlak, vožnja,
linija) iz razvojne baze. Samo GET, proti razvojnemu strežniku (~17 000
zahtev, ~2 min): **ne proti kajros.app**. Izhodna koda 1 ob odgovoru 500 ali
zahtevi brez odgovora v 30 s; 503 (OSRM v razvoju ne teče) se samo izpiše.

Prvi zagon 9. 11. 2026: trije 500 (datum `0001-01-01`, `stop_seq` nad 2^63)
in razrez čez zgodovino, ki ga je sprožil vsak `?fresh=1` ali `?days=7`
(`docs/MERITVE.md`, „Meglica“).
"""
import json
import pathlib
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from kajros import config          # noqa: E402
from kajros.api import app         # noqa: E402

c = sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True)
def ena(sql, *a):
    r = c.execute(sql, a).fetchone()
    return r[0] if r else None
vlak = ena("SELECT train_no FROM trip WHERE network='zeleznica' AND mode!='bus' AND train_no LIKE 'LP%' LIMIT 1") or "LP 2400"
trip_v = ena("SELECT trip_id FROM trip WHERE train_no=?", vlak) or "x"
bus = ena("SELECT train_no FROM trip WHERE network='avtobus' LIMIT 1") or "6"
trip_b = ena("SELECT trip_id FROM trip WHERE network='avtobus' AND train_no=?", bus) or "x"
danes = date.today().isoformat()
print("vzorci:", vlak, trip_v, bus, trip_b, danes, file=sys.stderr)

DOBRE = {"train_no": vlak, "no": vlak, "trip": trip_v, "trip_id": trip_v, "network": "zeleznica",
         "date": danes, "dan": danes, "exclude_date": danes, "datum": danes, "days": "7",
         "od_lat": "46.058", "od_lon": "14.511", "do_lat": "46.562", "do_lon": "15.657", "lat": "46.058",
         "lon": "14.511", "kmh": "5", "q": "Ljublj", "limit": "5", "lang": "sl", "station": "Ljubljana",
         "postaja": "Ljubljana", "from": "Ljubljana", "to": "Maribor", "od": "Ljubljana", "do": "Maribor",
         "cilj": "maribor", "ime": "ljubljana", "mesec": "2026-10", "window": "120", "kind": "dep",
         "stop_seq": "2", "delay_s": "300", "ob": "08:00", "hoje": "1", "prevoznik": "sz", "st": vlak,
         "stevilka": vlak, "smer": "", "k": "x", "id": "1", "vozilo": "x"}
GRDE = ["", " ", "%", "_", "'", '"', "\\", "ž" * 300, "a" * 5000, "0", "-1", "1", "99999999999999999999",
        "1e309", "NaN", "inf", "-inf", "null", "None", "true", "2026-02-30", "2026-13-01", "9999-12-31",
        "0000-00-00", "0001-01-01", "1969-12-31", "2026-03-29", "2027-03-28", "\x00", "a\x00b", "🚆",
        "../../etc/passwd", "Ljubljana\n", "{}", "[]", "<script>", "%s%s%n", "1;DROP", "' OR 1=1 --",
        "25:61", "24:00", "-08:00", "08:00:00", "1.5", "180.1", "-90.5", "46,05", "0x10", "١٢٣", " Ljubljana ",
        "ljubljana/maribor", "?", "#", "&a=b", "+", "LP 2400", "lp2400", "BUS", "IC", "zeleznica", "avtobus",
        "vlak", "*", "a" * 199, "a" * 201, "Šmarje pri Jelšah", "SMARJE", "Ž"]

def url(pot, pp, qp):
    for k, v in pp.items():
        pot = pot.replace("{" + k + "}", urllib.parse.quote(v, safe="")).replace("{" + k + ":path}", urllib.parse.quote(v, safe="/"))
    q = urllib.parse.urlencode(qp)
    return BASE + pot + ("?" + q if q else "")

naloge = []
for r in app.routes:
    if "GET" not in (getattr(r, "methods", None) or ()) or not hasattr(r, "dependant"):
        continue
    if r.path.startswith(("/prenos", "/docs", "/redoc", "/openapi")):
        continue
    pp = [p.name for p in r.dependant.path_params]
    qp = [(p.name, p.field_info.is_required()) for p in r.dependant.query_params]
    for net in ("zeleznica", "avtobus"):
        if net == "avtobus" and "network" not in [n for n, _ in qp] and "/bus" not in r.path and "avtobus" not in r.path:
            continue
        dobre = dict(DOBRE)
        if net == "avtobus" or "/bus" in r.path or "avtobus" in r.path or "postajalisc" in r.path:
            dobre.update(network="avtobus", train_no=bus, no=bus, trip=trip_b, trip_id=trip_b)
        osn_p = {k: dobre.get(k, "x") for k in pp}
        osn_q = {k: dobre.get(k, "x") for k, req in qp if req}
        if "network" in [n for n, _ in qp]:
            osn_q["network"] = dobre["network"]
        naloge.append((r.path, "-", "(osnova)", url(r.path, osn_p, osn_q)))
        # vsi neobvezni hkrati s smiselnimi
        vsi_q = {k: dobre.get(k, "x") for k, _ in qp if dobre.get(k, "x") != ""}
        naloge.append((r.path, "-", "(vsi)", url(r.path, osn_p, vsi_q)))
        for k in pp:
            for g in GRDE:
                if g == "" : continue
                naloge.append((r.path, k, g, url(r.path, {**osn_p, k: g}, osn_q)))
        for k, _ in qp:
            for g in GRDE:
                naloge.append((r.path, k, g, url(r.path, osn_p, {**osn_q, k: g})))
                naloge.append((r.path, k, g, url(r.path, osn_p, {**vsi_q, k: g})))
naloge = list(dict.fromkeys(naloge))
print("zahtev:", len(naloge), file=sys.stderr)

def klic(n):
    pot, k, g, u = n
    t = time.monotonic()
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "kajros-meglica", "Accept": "text/html,application/json"})
        with urllib.request.urlopen(req, timeout=30) as o:
            o.read(); koda = o.status
    except urllib.error.HTTPError as e:
        koda = e.code
    except Exception as e:
        koda = "X:" + type(e).__name__
    return pot, k, g, u, koda, time.monotonic() - t

with ThreadPoolExecutor(4) as p:
    izidi = list(p.map(klic, naloge))
kode = Counter(str(i[4]) for i in izidi)
print("kode:", dict(kode))
osnove = sorted({(pot, str(koda)) for pot, k, g, u, koda, dt in izidi if g in ("(osnova)", "(vsi)") and koda != 200})
print("osnova ni 200 (mutacije tam ne pridejo do kode):", len(osnove))
for pot, koda in osnove:
    print(f"  {koda} {pot}")
slabe = defaultdict(list)
for pot, k, g, u, koda, dt in izidi:
    if str(koda).startswith(("5", "X")):
        slabe[(pot, k, str(koda))].append(g if len(g) < 30 else g[:12] + f"…({len(g)})")
print("5xx/izjeme po (pot, parameter):", len(slabe))
for (pot, k, koda), gs in sorted(slabe.items()):
    print(f"  {koda} {pot} [{k}] {len(gs)}×: {json.dumps(sorted(set(gs))[:8], ensure_ascii=False)}")
pocasne = sorted((i for i in izidi if i[5] > 3), key=lambda i: -i[5])
print("počasne > 3 s:", len(pocasne))
vid = set()
for pot, k, g, u, koda, dt in pocasne:
    if (pot, k) in vid: continue
    vid.add((pot, k)); print(f"  {dt:5.1f} s {koda} {pot} [{k}={g[:30]!r}]")
    if len(vid) >= 15: break
if len(sys.argv) > 2:
    json.dump([i for i in izidi if str(i[4]).startswith(("5", "X")) or i[5] > 3],
              open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
sys.exit(1 if any(str(i[4]) == "500" or str(i[4]).startswith("X") for i in izidi) else 0)
