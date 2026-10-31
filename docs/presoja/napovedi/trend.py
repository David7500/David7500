"""Zamuda, ki raste z uro (ura namesto zamude), in skoki prikaza med krogi.
Rabi: python trend.py <imenik_posnetka>"""
import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import analiza as A  # noqa: E402

vrste = defaultdict(list)  # trip -> [(ts, seq, delay_s, vrsta, run)]
for f in sorted(glob.glob(os.path.join(sys.argv[1], "krog*.json"))):
    k = json.load(open(f))
    for tid, run in k["runs"].items():
        meja = run.get("last_measured_seq")
        st = {s["stop_seq"]: s for s in run["stops"]}
        z = (st.get(meja) or {}).get("zamuda") if meja is not None else None
        if run.get("trenutna"):
            z = run["trenutna"]["zamuda"]
        if z is None:
            continue
        vrste[tid].append((run["_t"], meja, z["s"], z.get("vrsta"), run))
drsi, skoki = [], []
for tid, v in vrste.items():
    if len(v) < 3:
        continue
    # rast skoraj minuto na minuto v treh zaporednih krogih
    for a, b, c in zip(v, v[1:], v[2:]):
        r1 = (b[2] - a[2]) / max(1, b[0] - a[0])
        r2 = (c[2] - b[2]) / max(1, c[0] - b[0])
        if r1 >= 0.7 and r2 >= 0.7 and c[2] >= 600:
            drsi.append((A.IME.get(c[4].get("agency"), c[4].get("agency")), c[4]["train_no"],
                         [round(x[2] / 60) for x in v], [x[1] for x in v], A.povezava(c[4])))
            break
    for a, b in zip(v, v[1:]):
        if abs(b[2] - a[2]) >= 600:
            skoki.append((A.IME.get(b[4].get("agency"), b[4].get("agency")), b[4]["train_no"],
                          round(a[2] / 60), round(b[2] / 60), a[1], b[1], a[3], b[3],
                          A.povezava(b[4])))
print("voženj s ≥ 3 krogi:", sum(len(v) >= 3 for v in vrste.values()))
print("== zamuda raste z uro", len(drsi))
for x in drsi:
    print("  ", json.dumps(x, ensure_ascii=False)[:300])
print("== skok ≥ 10 min med krogoma", len(skoki))
for x in skoki[:15]:
    print("  ", json.dumps(x, ensure_ascii=False)[:300])
