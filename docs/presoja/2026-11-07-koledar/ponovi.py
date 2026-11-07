"""Ponovitev zapisov zemljevida po objavi s predlaganim pravilom:
skok nazaj z višjo zamudo pobriše postanke od skoka naprej (niso bili prevoženi),
zato je naslednji zapis spet prvi (prihod = odhod). Primerja s tem, kar je v run."""
import sqlite3, sys
PRAVILO = sys.argv[1:] != ['brez']
from collections import Counter, defaultdict
REL = 1793972735
db = sqlite3.connect("/var/tmp/koledar-vlaki.sqlite")
ime = {r[0]: r[1:] for r in db.execute("SELECT trip_id, train_no, first_seq, last_seq FROM trip")}
sch = {(r[0], r[1]): (r[2], r[3]) for r in db.execute("SELECT trip_id, stop_seq, arr_s, dep_s FROM sched")}
run = defaultdict(dict)
for t, d, s, da, dd, f in db.execute("SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts FROM run"):
    run[(t, d)][s] = (da, dd, f)
obs = defaultdict(list)
for t, d, s, da, dd, fts, oa in db.execute("SELECT trip_id, service_date, stop_seq, delay_arr, delay_dep, feed_ts, observed_at FROM obs ORDER BY observed_at"):
    obs[(t, d)].append((oa, s, da, dd, oa - fts < 5))
prv = defaultdict(dict)
for t, d, s, p in db.execute("SELECT trip_id, service_date, stop_seq, prvic_ts FROM sz"): prv[(t, d)][s] = p
def mere(no_f_l, tid, st):
    no, f, l = no_f_l; t = []; stal = ppo = 0
    for seq in sorted(st):
        da, dd = st[seq]
        if seq == f or (tid, seq) not in sch: continue
        arr, dep = sch[(tid, seq)]
        a = arr + da if da is not None else None
        p = dep + dd if dd is not None and seq != l else None
        if a is not None and p is not None and a - p >= 120: ppo = 1
        if a is not None and p is not None and p - a >= 600 and dep - arr <= 120: stal = 1
        t += [(seq, x) for x in (a, p) if x is not None]
    nz = any(t[i][1] - t[j][1] >= 120 for i in range(len(t)) for j in range(i+1, len(t)) if t[j][0] > t[i][0])
    return nz, stal, ppo
res = defaultdict(Counter)
for (tid, d), r in run.items():
    if min(x[2] for x in r.values()) < REL: continue
    sk = "a 6.11 po objavi" if d == "2026-11-06" else "b 7.11"
    ev = []                                     # (čas, seq, vrednost) zapisov zemljevida
    zadnja = {}
    for oa, s, da, dd, zem in obs[(tid, d)]:
        if not zem: zadnja[s] = dd; continue
        ev.append((oa, s, dd))
        zadnja[s] = dd
    # prvi zapis, ki ni šel v obs (enak prejšnji vrednosti derp.si)
    imajo = {s for _, s, _ in ev}
    prej = {}
    for oa, s, da, dd, zem in obs[(tid, d)]:
        if not zem and s not in prej: prej[s] = dd
    for s, p in prv[(tid, d)].items():
        prvi_obs = min((oa for oa, ss, _ in ev if ss == s), default=None)
        if prvi_obs is None or prvi_obs > p + 5:
            ev.append((p, s, prej.get(s, r.get(s, (None, None, 0))[1])))
    ev.sort()
    st = {}; maxs = None
    for oa, s, v in ev:
        if v is None: continue
        if PRAVILO and maxs is not None and s < maxs and v > st[maxs][1]:
            for k in [k for k in st if k >= s]: del st[k]
            maxs = max(st) if st else None
        if s in st: st[s] = (st[s][0], v)
        else: st[s] = (v, v)
        maxs = s if maxs is None or s > maxs else maxs
    zdaj = {s: (x[0], x[1]) for s, x in r.items()}
    nova = dict(zdaj)
    for s in [k for k in nova if prv[(tid, d)].get(k)]: del nova[s]
    nova.update(st)
    c = res[sk]; c["voženj"] += 1; c["izgubljenih postankov"] += len(set(zdaj) - set(nova)); c["postankov"] += len(zdaj)
    for ime_, m in (("zdaj", mere(ime[tid], tid, zdaj)), ("predlog", mere(ime[tid], tid, nova))):
        c[ime_ + " ura_nazaj"] += m[0]; c[ime_ + " stal"] += m[1]; c[ime_ + " ppo"] += m[2]
for sk, c in sorted(res.items()):
    n = c["voženj"]; print(sk, n, {k: f"{v} ({100*v/n:.1f} %)" for k, v in sorted(c.items()) if k != "voženj"})
