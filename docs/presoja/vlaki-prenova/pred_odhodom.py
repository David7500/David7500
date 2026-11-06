"""Odhodna zamuda vlaka B z izhodišča iz odvisnosti od vlaka A (točka 5).

Vlak z izhodišča nikoli ne poroča, zato je "resnica" zamuda B na prvem
izmerjenem od 2. in 3. postanka (kot v povezave.py). Izpuščanje dneva: par
(A, B, S) velja, če v drugih dneh drži >= 70 % ob <= 20 % zamud B sicer.

    KAJROS_KOPIJA=/pot/do/kopije.sqlite ./venv/bin/python -I \
        docs/presoja/vlaki-prenova/pred_odhodom.py
"""
import os
import statistics
import sys
from collections import defaultdict

import sqlite3

sys.path.insert(0, os.getcwd())
from kajros import backtest  # noqa: E402

db = sqlite3.connect(f"file:{os.environ['KAJROS_KOPIJA']}?mode=ro", uri=True)
OD = os.environ.get("OD", "2026-09-01")
OBDOBJA = {"do 9. 10.": lambda d: d < "2026-10-10",
           "od 17. 10.": lambda d: d >= "2026-10-17", "vse": lambda d: True}

trips, ime = defaultdict(list), {}
for tid, no, seq, name, arr, dep in db.execute(
        "SELECT t.trip_id, t.train_no, s.stop_seq, st.name, s.arr_s, s.dep_s "
        "FROM trip t JOIN sched s ON s.trip_id=t.trip_id "
        "JOIN station st ON st.stop_id=s.stop_id "
        "WHERE t.network='zeleznica' AND t.mode='vlak' ORDER BY t.trip_id, s.stop_seq"):
    trips[tid].append((seq, name, arr, dep))
    ime[tid] = no
zam = defaultdict(dict)       # (trip, dan) -> {seq: (arr, dep)}
for tid, d, seq, da, dd in db.execute(
        "SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, r.delay_dep FROM run r "
        "JOIN trip t ON t.trip_id=r.trip_id AND t.network='zeleznica' AND t.mode='vlak' "
        "WHERE r.service_date >= ?", (OD,)):
    if (da is not None and abs(da) > 10800) or (dd is not None and abs(dd) > 10800):
        continue
    zam[(tid, d)][seq] = (da, dd)
dni = defaultdict(set)
for tid, d in zam:
    dni[tid].add(d)


def v(x):
    return None if x is None else (x[1] if x[1] is not None else x[0])


def odhod_b(tid, dan):
    z = zam.get((tid, dan), {})
    for seq, _, _, _ in trips[tid][1:3]:
        if seq in z and v(z[seq]) is not None:
            return v(z[seq])


def prihod_a(tid, dan, seq):
    z = zam.get((tid, dan), {}).get(seq)
    return None if z is None else (z[0] if z[0] is not None else z[1])


def zdaj_a(tid, dan, seq, do_ure):
    """Kar je o A znano pred B: zamuda na prejsnjem postanku, ce je A tam
    po voznem redu + zamudi odpeljal vsaj 5 min pred odhodom B."""
    st = trips[tid]
    k = next(i for i, p in enumerate(st) if p[0] == seq)
    if k == 0:
        return None
    pseq, _, parr, pdep = st[k - 1]
    d = v(zam.get((tid, dan), {}).get(pseq))
    cas = pdep if pdep is not None else parr
    if d is None or cas is None or cas + d > do_ure - 300:
        return None
    return d


po_postaji = defaultdict(list)
for tid, st in trips.items():
    for i, (seq, name, arr, dep) in enumerate(st):
        if arr is not None and i > 0:
            po_postaji[name].append((tid, seq, arr))

pari = []    # (A, seqA, B, razmik, {dan: (pres, dB, pres_zdaj)})
for B, st in trips.items():
    if len(st) < 3 or not dni[B]:
        continue
    S, tb = st[0][1], st[0][3]
    if tb is None:
        continue
    for A, seqA, ta in po_postaji[S]:
        if A == B or not (120 <= tb - ta <= 5400):
            continue
        skupni = dni[A] & dni[B]
        if len(skupni) < 8:
            continue
        podatki = {}
        for d in skupni:
            dA, dB = prihod_a(A, d, seqA), odhod_b(B, d)
            if dA is None or dB is None:
                continue
            zdaj = zdaj_a(A, d, seqA, tb)
            podatki[d] = (dA - (tb - ta), dB, None if zdaj is None else zdaj - (tb - ta))
        if len(podatki) >= 8:
            pari.append((A, seqA, B, tb - ta, podatki))


def odvisen(podatki, brez):
    late = hold = bn = bl = 0
    for d, (pres, dB, _) in podatki.items():
        if d == brez:
            continue
        if pres >= 300:
            late += 1
            hold += dB >= pres - 120
        elif pres < 0:
            bn += 1
            bl += dB >= 300
    return late >= 3 and hold / late >= 0.7 and (bn == 0 or bl / bn <= 0.2)


po_b = defaultdict(list)
for p in pari:
    po_b[p[2]].append(p)

test = []     # (dan, resnica, vozni red, obicajno, odvisnost zdaj, odvisnost A prispe)
for B, ps in po_b.items():
    for d in dni[B]:
        dB = odhod_b(B, d)
        if dB is None:
            continue
        zivi = [p for p in ps if d in p[4] and odvisen(p[4], d)]
        if not zivi:
            continue
        ostali = [x for x in (odhod_b(B, e) for e in dni[B] if e != d) if x is not None]
        obicajno = statistics.median(ostali) if len(ostali) >= 3 else 0
        zdaj = max([0] + [p[4][d][2] for p in zivi if p[4][d][2] is not None])
        prispe = max([0] + [p[4][d][0] for p in zivi])
        test.append((d, dB, 0, obicajno, zdaj, prispe))

print(f"vlakov B z odvisnostjo: {len({t for t in po_b if any(True for _ in po_b[t])})}, "
      f"parov: {len(pari)}, nalog (B, dan): {len(test)}")
for ob, pogoj in OBDOBJA.items():
    t = [x for x in test if pogoj(x[0])]
    print(f"\n{ob}: n = {len(t)}, od tega A zamuja >= 5 min po razmiku: "
          f"{sum(1 for x in t if x[4] >= 300)}")
    print(f"{'model':28s}{'n':>7}{'MAE':>7}{'v5':>7}{'pod':>6}{'pre':>6}{'strosek':>9}")
    for ime_m, k in (("vozni red", 2), ("obicajno", 3), ("odvisnost (znano pred B)", 4),
                     ("odvisnost (A prispe, zgornja meja)", 5)):
        m = backtest.metrike_napovedi([(x[k], x[1]) for x in t])
        if m["n"]:
            print(f"{ime_m:28s}{m['n']:>7d}{m['mae_min']:>7.2f}{m['v5min']:>7.1f}"
                  f"{m['podcenj']:>6.1f}{m['precenj']:>6.1f}{m['strosek_min']:>9.2f}")
