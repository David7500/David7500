"""Ponovi naloge iz sence z drugačno mejo ostanka.

Senca (`ocena.py`) hrani natanko tiste naloge, ki jih je videl potnik: kje je
bilo vozilo, koliko je zamujalo, kateri postanek je gledal in kaj se je na
koncu zgodilo. Tu iste naloge preračunamo z drugimi vrednostmi
`stats.OMEJI_OSTANEK_S` in `OMEJI_OSTANEK_DELEZ` — merilo je torej isto
vprašanje, ne bližji približek.

Zagon: ./venv/bin/python scripts/preizkusi_model.py [sekunde:delez ...]
Primer: ./venv/bin/python scripts/preizkusi_model.py 0:0 600:0 600:1 900:1
        (`0:0` pomeni brez meje)
"""
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, ".")
from sztrack import db, stats                                    # noqa: E402

RAZLICICE = [tuple(float(x) for x in a.split(":")) for a in sys.argv[1:]] \
    or [(0, 0), (300, 0), (600, 0), (600, 1), (900, 1), (1200, 1)]


def oceni(pari):
    e = [abs(a - b) for a, b in pari]
    n = len(e)
    return (st.mean(e) / 60, sum(1 for x in e if x <= 300) / n * 100,
            sum(1 for a, b in pari if a < b - 300) / n * 100,
            sum(a - b for a, b in pari) / n / 60, n)


def main():
    conn = db.connect()
    vrstice = [dict(r) for r in conn.execute(
        "SELECT * FROM napoved WHERE actual_s IS NOT NULL")]
    if not vrstice:
        print("sencno merjenje še nima razrešenih vrstic -- pusti strežnik teči")
        return

    # Ena napoved na (vožnja, dan, izhodišče, zamuda): `predict` vrne vse
    # postanke naprej naenkrat, zato bi klic na postanek delo podeseteril.
    skupine = defaultdict(list)
    for r in vrstice:
        skupine[(r["trip_id"], r["service_date"], r["from_seq"], r["current_s"])].append(r)
    tn = {}
    for tid in {r["trip_id"] for r in vrstice}:
        row = conn.execute("SELECT train_no FROM trip WHERE trip_id = ?", (tid,)).fetchone()
        tn[tid] = row["train_no"] if row else None

    print(f"nalog iz sence: {len(vrstice)} · klicev predict na različico: {len(skupine)}")
    print(f"\n{'meja':>12}{'MAE':>9}{'v 5 min':>9}{'podcenj.':>10}{'odklon':>9}"
          f"{'9-10 post.':>12}")
    for om, delez in RAZLICICE:
        vidno, dolge = [], []
        for (tid, dan, od, zam), rows in skupine.items():
            if not tn[tid]:
                continue
            nap = {x["stop_seq"]: x for x in stats.predict(
                conn, tn[tid], od, zam or 0, exclude_date=dan, service_date=dan,
                trip_id=tid, omeji_s=int(om) or 10**9, omeji_delez=delez)}
            for r in rows:
                p = nap.get(r["stop_seq"])
                if not p:
                    continue
                # Kar bi potnik RES videl -- s pravilom "prevoznik ve več",
                # in sicer z vrednostjo, ki jo je feed imel TAKRAT (iz sence),
                # ne z današnjo.
                v = (max(p["own_delay_s"], r["operator_s"])
                     if r["operator_s"] is not None else p["own_delay_s"])
                vidno.append((v, r["actual_s"]))
                if 9 <= r["stop_seq"] - r["from_seq"] <= 10:
                    dolge.append((v, r["actual_s"]))
        mae, v5, pod, odk, n = oceni(vidno)
        ime = "brez" if not om else f"{int(om)} s + {delez:g}x"
        print(f"{ime:>12}{mae:>8.2f}m{v5:>8.1f}%{pod:>9.1f}%{odk:>8.2f}m"
              f"{oceni(dolge)[0]:>11.2f}m")

    prenos = oceni([(r["carry_s"], r["actual_s"]) for r in vrstice
                    if r["carry_s"] is not None])
    print(f"\nreferenca — prenos zamude: {prenos[0]:.2f}m · v 5 min {prenos[1]:.1f} %"
          f" · podcenjenih {prenos[2]:.1f} % · odklon {prenos[3]:+.2f}m")


if __name__ == "__main__":
    main()
