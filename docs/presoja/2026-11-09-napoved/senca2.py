"""Drugo merilo: kandidati na vrsticah sence (`napoved`), kot jih je videl potnik.

Za vsako vrstico na poti (from_seq, current_s -> stop_seq) izracuna kandidate z
zgodovino pred tem dnem in jih primerja z resnico iz `run` (popravljena) ter s
tem, kar je senca zapisala takrat (ours_s, ours_own_s, carry_s, varna_s).

  python senca2.py <baza> [--od DAN] [--modeli a,b]
"""
import argparse
import sys
import time
from collections import defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import modeli2 as M  # noqa: E402
from kajros import db, stats  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baza")
    ap.add_argument("--od", default="2026-10-17")
    ap.add_argument("--do", default="9999")
    ap.add_argument("--modeli", default="sedanji,varna_q25,hibrid+ pol=21,hibrid+ q30 pol=21")
    a = ap.parse_args()
    imena = [m.strip() for m in a.modeli.split(",")]
    t0 = time.time()
    dnevi, rez, postanki = M.nalozi(a.baza)
    conn = db.connect(a.baza)
    voznja = {r[0]: r[1] for r in conn.execute(
        f"SELECT trip_id, {db.voznja_sql('t')} FROM trip t")}
    resnica = {(r[0], r[1], r[2]): r[3] for r in conn.execute(
        "SELECT trip_id, service_date, stop_seq, COALESCE(delay_dep, delay_arr) FROM run "
        "WHERE service_date >= ?", (a.od,))}
    skupine = defaultdict(list)
    for r in conn.execute(
            "SELECT trip_id, service_date, stop_seq, from_seq, current_s, ours_s, ours_own_s, "
            "       carry_s, varna_s, actual_s FROM napoved "
            "WHERE network = 'zeleznica' AND from_seq IS NOT NULL AND current_s IS NOT NULL "
            "  AND actual_s IS NOT NULL AND service_date >= ? AND service_date < ? "
            "  AND stop_seq > from_seq", (a.od, a.do)):
        skupine[(r["trip_id"], r["service_date"], r["from_seq"], r["current_s"])].append(dict(r))
    stolpci = ["ours_s", "ours_own_s", "carry_s", "varna_s"]
    pari = {k: [] for k in stolpci + imena}
    pari_v = {k: [] for k in ["ours_s", "carry_s", "varna_s"] + imena}   # samo vrstice z varna_s
    razlika = n = 0
    for (trip_id, dan, i, d), vrste in skupine.items():
        v = voznja.get(trip_id)
        seznam = dnevi.get(v, [])
        do = M.ord_(dan)
        H = [(do - M.ord_(x), g) for x, g, _ in seznam if 0 < do - M.ord_(x) <= 90]
        r, ps = rez.get(v, {}), postanki.get(v, [])
        cilji = sorted({x["stop_seq"] for x in vrste})
        cilji = [(j, sum(r.get(k, 0) for k in ps if i < k <= j)) for j in cilji]
        izidi = {m: M.MODELI[m](H, r, ps, i, d, cilji) for m in imena}
        for x in vrste:
            res = resnica.get((trip_id, dan, x["stop_seq"]))
            if res is None or abs(res) > stats.MAX_REALNA_ZAMUDA_S:
                continue
            n += 1
            razlika += res != x["actual_s"]
            for k in stolpci:
                if x[k] is not None:
                    pari[k].append((x[k], res))
            for m in imena:
                pari[m].append((izidi[m][x["stop_seq"]], res))
            if x["varna_s"] is not None:
                for k in ("ours_s", "carry_s", "varna_s"):
                    pari_v[k].append((x[k], res))
                for m in imena:
                    pari_v[m].append((izidi[m][x["stop_seq"]], res))
    print(f"# {n} vrstic na poti od {a.od} do {a.do}, {len(skupine)} skupin, "
          f"resnica zdaj != zapisana pri {razlika}; {time.time()-t0:.0f} s")
    for naslov, p in (("vse vrstice", pari), ("samo vrstice z varna_s (od 6. 11.)", pari_v)):
        print(f"\n{naslov}\nmodel | n | MAE | v 2 min | podc. | prec. | strošek | odklon")
        print("---|---|---|---|---|---|---|---")
        for k, x in p.items():
            y = M.meri(x)
            if y:
                print(f"{k} | {y[0]} | {y[1]:.3f} | {y[2]:.1f} | {y[3]:.1f} | {y[4]:.2f} | "
                      f"{y[5]:.2f} | {y[6]:+.2f}")


if __name__ == "__main__":
    main()
