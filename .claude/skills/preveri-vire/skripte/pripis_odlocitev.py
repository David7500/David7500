"""Odločitev o priklopu pripisa NAP iz `pripis_senca` (samo branje). Dopolnilo k `pripis_nap.py`.

Enota = niz: (vozilo, naša vožnja, dan) zaporednih parov, ne vrstica (vrstice istega vozila niso neodvisne).
Vsak niz dobi natanko eno oznako; napačni in nepotrjeni se izpišejo vsi, ne prvih šest.

Argumenti: DAN [--baza POT] [--od URA] [--do URA] [--seznam N]
Zagon: scp na arwen, nato ssh david@192.168.1.46 '/opt/kajros/.venv/bin/python -I /tmp/pripis_odlocitev.py 2026-11-01'
"""
import argparse
import collections
import math
import sqlite3
import os
import time

os.environ["TZ"] = "Europe/Ljubljana"
time.tzset()

ap = argparse.ArgumentParser()
ap.add_argument("dan")
ap.add_argument("--baza", default="/var/lib/kajros/kajros.sqlite")
ap.add_argument("--od", type=float, default=0.0, help="samo vrstice od te ure (lokalno)")
ap.add_argument("--do", type=float, default=24.0)
ap.add_argument("--seznam", type=int, default=40)
ap.add_argument("--stoji-m", type=float, default=150.0)
a = ap.parse_args()
conn = sqlite3.connect(f"file:{a.baza}?mode=ro", uri=True)
OBSEG = ("brez_dneva", "prezgodaj")     # koledar: napačen dan, vožnja daleč naprej; pred_odhodom, po_koncu, brez_voznje se ne priklopijo


def razd(la1, lo1, la2, lo2):
    return math.hypot((la1 - la2) * 111195, (lo1 - lo2) * 111195 * math.cos(math.radians(la1)))


def ura(ts):
    return time.strftime("%H:%M", time.localtime(ts))


okno = {r[0]: (r[1], r[2]) for r in conn.execute(
    "SELECT trip_id, start_s, end_s FROM trip WHERE start_s IS NOT NULL")}


def oknos(t):
    if t in okno:
        z, k = okno[t]
        return f"{t} {z // 3600:02d}:{z % 3600 // 60:02d}-{k // 3600:02d}:{k % 3600 // 60:02d}"
    return f"{t} (ni voznega reda)"


vrst = conn.execute(
    "SELECT ts, vozilo, vzrok, nap_voznja, nasa_voznja, nas_dan, razlog, zamuda_s, derp_voznja, lat, lon "
    "FROM pripis_senca WHERE dan = ? ORDER BY vozilo, ts", (a.dan,)).fetchall()
if not vrst:
    print(f"{a.dan}: v pripis_senca ni vrstic")
    raise SystemExit(0)


def v_oknu(ts):
    h = time.localtime(ts)
    u = h.tm_hour + h.tm_min / 60
    return a.od <= u < a.do


po_vozilu = collections.defaultdict(list)
for r in vrst:
    po_vozilu[r[1]].append(r)
nizi = []
for voz, vs in po_vozilu.items():
    tek = None
    for r in vs:
        if r[4] is None or not v_oknu(r[0]):
            continue
        if tek and tek["nasa"] == r[4] and tek["nd"] == r[5] and r[0] - tek["vr"][-1][0] <= 200:
            tek["vr"].append(r)
        else:
            tek = {"voz": voz, "nasa": r[4], "nd": r[5], "vr": [r]}
            nizi.append(tek)


def cilj(t):
    return conn.execute("SELECT st.lat, st.lon FROM sched s JOIN station st USING (stop_id) "
                        "WHERE s.trip_id = ? ORDER BY s.stop_seq DESC LIMIT 1", (t,)).fetchone()


ozn = collections.Counter()
po_oznaki = collections.defaultdict(list)
for n in nizi:
    vs = n["vr"]
    t1, t2 = vs[0][0], vs[-1][0]
    okol = [r for r in po_vozilu[n["voz"]] if t1 - 130 <= r[0] <= t2 + 130]
    span = okol[-1][0] - okol[0][0]
    md = max(razd(okol[0][9], okol[0][10], r[9], r[10]) for r in okol)
    stoji = md < a.stoji_m and span >= 120
    kraj = (vs[-1][0] - vs[-1][7]) - (vs[0][0] - vs[0][7])
    drugi = conn.execute("SELECT COUNT(DISTINCT vozilo) FROM lega WHERE service_date = ? AND trip_id = ? "
                         "AND vozilo != ? AND ts BETWEEN ? AND ?",
                         (n["nd"], n["nasa"], n["voz"], t1 - 600, t2 + 600)).fetchone()[0]
    isti = conn.execute("SELECT COUNT(*) FROM lega WHERE service_date = ? AND trip_id = ? AND vozilo = ?",
                        (n["nd"], n["nasa"], n["voz"])).fetchone()[0]
    ci = cilj(n["nasa"])
    na_koncu = bool(ci) and razd(vs[-1][9], vs[-1][10], ci[0], ci[1]) <= 200
    enako = all(r[3] == n["nasa"] for r in vs)
    derp_isto = any(r[8] == n["nasa"] for r in vs)
    if drugi:
        o = "NAROBE drugo vozilo na vožnji"
    elif stoji and na_koncu and isti:
        o = "stoji na končni svoje vožnje"
    elif stoji and enako:
        o = "stoji pred NAP-ovo vožnjo"
    elif stoji:
        o = "NAROBE stoji"
    elif kraj < -60:
        o = "NAROBE vozi nazaj"
    elif enako and not isti:
        o = "NAP-ov id, vozi (mimo koledarja)"
    elif enako:
        o = "NAP-ov id, vozi"
    elif isti:
        o = "potrjen: NAP ga je imel na njej"
    elif derp_isto:
        o = "potrjen: derp ima isto, NAP ne"
    else:
        o = "NEPOTRJEN (premika se, drugače od NAP, nihče ne potrdi)"
    n["o"] = o
    n["md"] = round(md)
    n["kraj"] = round(kraj)
    n["vzrok"] = vs[0][2]
    obs = "obseg" if n["vzrok"] in OBSEG else "zunaj"
    ozn[(obs, o)] += 1
    ozn[("vrstic", obs, o)] += len(vs)
    po_oznaki[o].append(n)
print(f"{a.dan}: {len(vrst)} vrstic, {len(po_vozilu)} vozil, {len(nizi)} nizov parov")
print(f"{'':6} {'oznaka':58} {'nizov':>6} {'vrstic':>7}")
for obs in ("obseg", "zunaj"):
    for (x, o), m in sorted(((k, v) for k, v in ozn.items() if len(k) == 2 and k[0] == obs), key=lambda z: z[0][1]):
        print(f"{obs:6} {o:58} {m:6} {ozn[('vrstic', obs, o)]:7}")
vsi = [n for n in nizi if n["vzrok"] in OBSEG]
nar = [n for n in vsi if n["o"].startswith("NAROBE")]
nep = [n for n in vsi if n["o"].startswith("NEPOTRJEN")]
print(f"\nobseg (neverjetna prijava {OBSEG}): {len(vsi)} nizov, {len({n['voz'] for n in vsi})} vozil, "
      f"napačnih {len(nar)}, nepotrjenih {len(nep)}")
bd = collections.Counter()
for voz, vs in po_vozilu.items():
    for r in vs:
        if r[2] == "brez_dneva":
            bd[(r[6] or "par")] += 1
print("brez_dneva, računi po izidu:", dict(sorted(bd.items())))
# Zakaj brez_dneva: koledar res nima ali je okno daleč; dvojček (ista proga, odhod, prihod) na koledarju da razlog vec.
vz = collections.Counter()
for voz, t in {(r[1], r[3]) for r in vrst if r[2] == "brez_dneva"}:
    x = conn.execute("SELECT route_id, start_s, end_s, EXISTS(SELECT 1 FROM service_day sd WHERE sd.service_id = t.service_id "
                     "AND sd.date = ?) FROM trip t WHERE trip_id = ?", (a.dan, t)).fetchone()
    if x is None or x[1] is None:
        vz["vožnje ni ali nagrobnik"] += 1
    elif x[3]:
        vz["koledar ima, okno daleč"] += 1
    else:
        dv = conn.execute("SELECT COUNT(*) FROM trip t JOIN service_day sd ON sd.service_id = t.service_id AND sd.date = ? "
                          "WHERE t.route_id = ? AND t.start_s = ? AND t.end_s = ? AND t.trip_id != ?",
                          (a.dan, x[0], x[1], x[2], t)).fetchone()[0]
        vz["koledar nima, dvojček na koledarju" if dv else "koledar nima, brez dvojčka"] += 1
print("brez_dneva, (vozilo, NAP-ova vožnja):", dict(sorted(vz.items())))
if vsi:
    print(f"zgornja meja 95 %, če je napačnih 0: {100 * 3 / len(vsi):.1f} % nizov")
dovolj = len(vsi) >= 30 and len({n['voz'] for n in vsi}) >= 10
if nar:
    izid = "NE: napačen niz v obsegu; senca do 7. 11."
elif not dovolj:
    izid = "NE DANES: premalo nizov (rabimo >= 30 nizov z >= 10 vozil); senca do 7. 11."
elif nep:
    izid = f"PREGLED: {len(nep)} nepotrjenih nizov po enega na zemljevidu; brez napačnega odloči David"
else:
    izid = "GO: na odobritev Davidu"
print("ODLOČITEV:", izid)
for naslov, seznam in (("NAROBE v obsegu", nar), ("NEPOTRJENI v obsegu", nep),
                       ("NAROBE zunaj obsega", [n for n in nizi if n not in vsi and n["o"].startswith("NAROBE")])):
    if seznam:
        print(f"\n{naslov} ({len(seznam)}):")
        korak = max(1, len(seznam) // max(1, a.seznam))  # enakomerno po dnevu, ne prvih N
        for n in sorted(seznam, key=lambda x: x["vr"][0][0])[::korak][:a.seznam]:
            v0 = n["vr"][0]
            print(f"  {n['voz']:10} {ura(v0[0])}-{ura(n['vr'][-1][0])} {n['vzrok']:12} vrstic {len(n['vr']):3} "
                  f"premik {n['md']:5} m kraj {n['kraj']:+5} s · NAP {oknos(v0[3])} · naša {oknos(n['nasa'])} · "
                  f"derp {v0[8]!r} · {n['o']} · {v0[9]:.5f},{v0[10]:.5f}")
