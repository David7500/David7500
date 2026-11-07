"""`kajros popravi-vlake` (preklic skokov nazaj) na kopiji izvlečka z arwena.

    python -I popravi_skoke_suho.py IZVLECEK.sqlite KOREN_KAJROSA

Izvleček kot v `ponovi_zapisi.py` (trip, sched, station, service_day, run, obs,
sz_zamuda za dneve od 6. 11.). Kopija v pomnilniku: suho štetje, zapis, mere
`ponovi_zapisi.mere` pred in po (vse vožnje-dni in tiste z `run` samo po objavi).
"""
import sqlite3
import sys
from collections import Counter, defaultdict

izvlecek, koren = sys.argv[1], sys.argv[2]
sys.path.insert(0, koren)
from kajros import db, zamude_sz  # noqa: E402

REL = zamude_sz.POPRAVI_DO_TS
x = sqlite3.connect(izvlecek)
c = db.connect(":memory:")
db.init(c)
for tab in ("station", "trip", "sched", "service_day", "run", "obs", "sz_zamuda"):
    imajo = {r[1] for r in c.execute(f"PRAGMA table_info({tab})")}
    sk = [r[1] for r in x.execute(f"PRAGMA table_info({tab})") if r[1] in imajo]
    c.executemany(f"INSERT OR IGNORE INTO {tab}({', '.join(sk)}) VALUES({', '.join('?' * len(sk))})",
                  x.execute(f"SELECT {', '.join(sk)} FROM {tab}").fetchall())
c.commit()
ime = {r[0]: r[1:] for r in c.execute("SELECT trip_id, first_seq, last_seq FROM trip")}
sch = {(r[0], r[1]): (r[2], r[3]) for r in c.execute("SELECT trip_id, stop_seq, arr_s, dep_s FROM sched")}


def mere():
    run = defaultdict(dict)
    for t, d, s, da, dd, f in c.execute("SELECT r.trip_id, r.service_date, r.stop_seq, r.delay_arr, "
                                        "r.delay_dep, r.feed_ts FROM run r JOIN trip t USING(trip_id) "
                                        "WHERE t.mode = 'vlak'"):
        run[(t, d)][s] = (da, dd, f)
    k = Counter()
    for (tid, d), r in run.items():
        po = min(v[2] for v in r.values()) >= REL
        f, l = ime[tid]
        t, stal = [], 0
        for seq in sorted(r):
            da, dd, _ = r[seq]
            if seq == f or (tid, seq) not in sch:
                continue
            arr, dep = sch[(tid, seq)]
            a = arr + da if da is not None else None
            p = dep + dd if dd is not None and seq != l else None
            if a is not None and p is not None and p - a >= 600 and dep - arr <= 120:
                stal = 1
            t += [(seq, v) for v in (a, p) if v is not None]
        nz = any(t[i][1] - t[j][1] >= 120 for i in range(len(t))
                 for j in range(i + 1, len(t)) if t[j][0] > t[i][0])
        for sk in ([d, d + " po objavi"] if po else [d]):
            k[sk + " voženj"] += 1
            k[sk + " ura_nazaj"] += nz
            k[sk + " stal"] += stal
    return k


pred = mere()
suho = zamude_sz.popravi_vlake(c, zamude_sz.PREKLIC_OD)
print("suho", {d: {k: v for k, v in i.items() if k.startswith("preklic")} for d, i in suho["dnevi"].items()})
print("skupaj", {k: suho[k] for k in suho if k.startswith("preklic") or k in ("postankov", "napovedi", "zastarelih")})
zamude_sz.popravi_vlake(c, zamude_sz.PREKLIC_OD, zapisi=True)
po = mere()
for k in sorted(k for k in pred if k.endswith("voženj")):
    s = k[:-len(" voženj")]
    n = pred[k]
    print(s, n, " ".join(f"{m}: {pred[s + ' ' + m]} ({100 * pred[s + ' ' + m] / n:.1f} %) -> "
                         f"{po[s + ' ' + m]} ({100 * po[s + ' ' + m] / n:.1f} %)" for m in ("ura_nazaj", "stal")))
print("ponovno suho", {k: v for k, v in zamude_sz.popravi_vlake(c, zamude_sz.PREKLIC_OD).items()
                       if k.startswith("preklic")})
