"""Ponovitev zapisov zemljevida SŽ po objavi 88ec114 s PRAVO kodo `zamude_sz.zapisi`.

Zaporedje potrjenih stanj (vožnja, dan, postanek, zamuda) se sestavi iz izvlečka
z arwena (`obs` vrstice zemljevida: `observed_at - feed_ts < 5`; prvi zapis, ki v
`obs` ni šel, iz `sz_zamuda.prvic_ts` z vrednostjo zadnje vrstice derp.si) in gre
po času skozi `zapisi` na prazni bazi v pomnilniku. Postanki brez zapisa
zemljevida (derp.si) se prepišejo iz `run`. Mere kot `ponovi.py`.

    python -I ponovi_zapisi.py IZVLECEK.sqlite KOREN_KAJROSA

KOREN_KAJROSA = imenik s paketom `kajros` (stara ali nova koda).
Ne vidi stanj, ki jih je stara koda zavrnila kot „nazaj“ (v `obs` jih ni).
"""
import sqlite3
import sys
from collections import Counter, defaultdict

izvlecek, koren = sys.argv[1], sys.argv[2]
sys.path.insert(0, koren)
from kajros import db, zamude_sz  # noqa: E402

REL = 1793972735                       # zamude_sz.POPRAVI_DO_TS, objava 88ec114
x = sqlite3.connect(izvlecek)
ime = {r[0]: r[1:] for r in x.execute("SELECT trip_id, train_no, first_seq, last_seq FROM trip")}
sch = {(r[0], r[1]): (r[2], r[3]) for r in x.execute("SELECT trip_id, stop_seq, arr_s, dep_s FROM sched")}
run = defaultdict(dict)
for t, d, s, da, dd, f in x.execute(
        "SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts FROM run"):
    run[(t, d)][s] = (da, dd, f)
obs = defaultdict(list)
for t, d, s, da, dd, fts, oa in x.execute(
        "SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts, observed_at "
        "FROM obs ORDER BY observed_at, feed_ts"):
    obs[(t, d)].append((oa, fts, s, da, dd, oa - fts < 5))
prv = defaultdict(dict)
for t, d, s, p in x.execute("SELECT trip_id, service_date, stop_seq, prvic_ts FROM sz_zamuda"):
    prv[(t, d)][s] = p


def mere(tid, st):
    """(ura nazaj >= 2 min, stal >= 10 min pri postanku <= 2 min, prihod po odhodu)."""
    _, f, l = ime[tid]
    t, stal, ppo = [], 0, 0
    for seq in sorted(st):
        da, dd = st[seq]
        if seq == f or (tid, seq) not in sch:
            continue
        arr, dep = sch[(tid, seq)]
        a = arr + da if da is not None else None
        p = dep + dd if dd is not None and seq != l else None
        if a is not None and p is not None and a - p >= 120:
            ppo = 1
        if a is not None and p is not None and p - a >= 600 and dep - arr <= 120:
            stal = 1
        t += [(seq, v) for v in (a, p) if v is not None]
    nz = any(t[i][1] - t[j][1] >= 120 for i in range(len(t))
             for j in range(i + 1, len(t)) if t[j][0] > t[i][0])
    return int(nz), stal, ppo


c = db.connect(":memory:")
db.init(c)
for tab in ("station", "trip", "sched", "service_day"):
    stolpci = [r[1] for r in x.execute(f"PRAGMA table_info({tab})")]
    imajo = {r[1] for r in c.execute(f"PRAGMA table_info({tab})")}
    sk = [s for s in stolpci if s in imajo]
    vrste = x.execute(f"SELECT {', '.join(sk)} FROM {tab}").fetchall()
    c.executemany(f"INSERT OR IGNORE INTO {tab}({', '.join(sk)}) VALUES({', '.join('?' * len(sk))})",
                  vrste)
c.commit()

res = defaultdict(Counter)
for (tid, d), r in sorted(run.items()):
    if min(v[2] for v in r.values()) < REL or tid not in ime:
        continue
    sk = "a 6.11 po objavi" if d == "2026-11-06" else "b 7.11"
    ev, po_postanku = [], defaultdict(list)
    for oa, fts, s, da, dd, zem in obs[(tid, d)]:
        po_postanku[s].append((fts, dd))
        if zem and oa >= REL and dd is not None:
            ev.append((fts, s, dd))
    for s, p in prv[(tid, d)].items():
        if p < REL:
            continue
        if not any(ss == s and abs(ts - p) <= 1 for ts, ss, _ in ev):
            # Ni šel v obs: enak zadnji vrstici dnevnika pred njim (`worth_logging`).
            pred = [dd for fts, dd in sorted(po_postanku[s]) if fts <= p and dd is not None]
            v = pred[-1] if pred else r.get(s, (None, None, 0))[1]
            if v is not None:
                ev.append((p, s, v))
    ev.sort()
    sz = {s for s in prv[(tid, d)]}
    for s, (da, dd, f) in r.items():         # postanki brez zemljevida ostanejo
        if s not in sz:
            c.execute("INSERT INTO run(trip_id, service_date, stop_seq, delay_arr, delay_dep, "
                      "feed_ts) VALUES(?,?,?,?,?,?)", (tid, d, s, da, dd, f))
    zadnji = ime[tid][2]
    for ts, s, v in ev:
        izid = zamude_sz.zapisi(c, [(tid, d, s, v, s == zadnji)], ts)
        res[sk]["preklicanih"] += izid.get("preklicanih", 0)
    nova = {q: (a, b) for q, a, b in c.execute(
        "SELECT stop_seq, delay_arr, delay_dep FROM run WHERE trip_id = ? AND service_date = ?",
        (tid, d))}
    zdaj = {s: (v[0], v[1]) for s, v in r.items()}
    k = res[sk]
    k["voženj"] += 1
    k["postankov"] += len(zdaj)
    k["izgubljenih"] += len(set(zdaj) - set(nova))
    for oznaka, st in (("run arwen", zdaj), ("ponovitev", nova)):
        m = mere(tid, st)
        k[oznaka + " ura_nazaj"] += m[0]
        k[oznaka + " stal"] += m[1]
        k[oznaka + " ppo"] += m[2]
for sk, k in sorted(res.items()):
    n = k["voženj"]
    print(sk, n, "; ".join(f"{a}: {b}" + (f" ({100 * b / n:.1f} %)" if a.endswith(("nazaj", "stal", "ppo")) else "")
                           for a, b in sorted(k.items()) if a != "voženj"))
