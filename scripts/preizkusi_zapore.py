"""Ali opozorilo o zapori tira in o vlaku pred tabo kaj pove?

Dve vprašanji, obe na isti kodi, kot jo streže `kajros/zapore.py`:

  odseki  Koliko vlak izgubi na zaprtem odseku v oknu zapore -- proti istemu
          odseku ob isti uri na dneve brez zapore.
  senca   Pri napovedih, ki jih je potnik videl (`napoved`), bi opozorilo
          viselo -- kako pogosto je bila naša številka tam prenizka za več kot
          5 min (vlak je prišel pozneje), proti napovedim brez opozorila.

Vlak pred tabo v senci vzame končne vrednosti `run`, ne stanja ob pogledu:
izguba, ki se je zgodila pred pogledom, je morda feed sporočil šele po njem.

Zagon: KAJROS_DB=... ./venv/bin/python scripts/preizkusi_zapore.py
"""
import statistics as st
import sys
from collections import defaultdict
from datetime import date, datetime

sys.path.insert(0, ".")
from kajros import db, zapore                             # noqa: E402

conn = db.connect()
g = zapore._graf(conn)
vse = zapore.zapore(conn)
dnevi = [r[0] for r in conn.execute(
    "SELECT DISTINCT service_date FROM run ORDER BY 1")]
print(f"zapor (odsekov z okni): {len(vse)}, dni v bazi: {len(dnevi)} ({dnevi[0]} - {dnevi[-1]})")

prehodi = defaultdict(list)
for p in zapore._prehodi(conn, g, dnevi):
    prehodi[p[0]].append(p)


def zaprt(p):
    robovi = {frozenset(e) for e in p[10]}
    return any(robovi & z["robovi"] and zapore._v_oknu(z["okna"], p[7]) for z in vse)


def odsek_ure(p):
    """Isti odsek in ura, kot ju ima kaka zapora -- za primerjalno skupino."""
    robovi = {frozenset(e) for e in p[10]}
    t = datetime.fromtimestamp(p[7], zapore.TZ)
    m = t.hour * 60 + t.minute
    return any(robovi & z["robovi"] and any(o[1] <= m <= o[2] for o in z["okna"]) for z in vse)


def opis(ime, izgube):
    n = len(izgube)
    if not n:
        print(f"{ime:44} n=0")
        return
    print(f"{ime:44} n={n:6}  ≥5 min {sum(x >= 300 for x in izgube) / n * 100:5.1f} %"
          f"  ≥10 {sum(x >= 600 for x in izgube) / n * 100:5.1f} %"
          f"  povp. {st.mean(izgube) / 60:5.2f}  mediana {st.median(izgube) / 60:4.1f} min")


def odseki():
    print("\n== izguba na odseku (prehod med zaporednima izmerjenima postankoma)")
    skupine = defaultdict(list)
    for dan, ps in prehodi.items():
        vikend = date.fromisoformat(dan).weekday() >= 5
        for p in ps:
            if not p[10]:
                continue
            if zaprt(p):
                skupine[("zapora", vikend)].append(p[9])
            elif odsek_ure(p):
                skupine[("isti odsek in ura, brez zapore", vikend)].append(p[9])
    for (ime, vikend), izgube in sorted(skupine.items()):
        opis(f"{ime}, {'vikend' if vikend else 'delavnik'}", izgube)


def senca():
    """Za vsak pogled iz sence pokliče `zapore.za_voznjo`, kot bi ga strežnik."""
    vrstice = conn.execute(
        "SELECT n.trip_id, n.service_date, n.stop_seq, n.from_seq, n.current_s, n.made_ts, "
        "       n.ours_s, n.actual_s "
        "FROM napoved n WHERE n.network = 'zeleznica' AND n.actual_s IS NOT NULL "
        "  AND n.from_seq IS NOT NULL AND n.ours_s IS NOT NULL "
        "  AND ABS(n.actual_s) <= 10800").fetchall()
    velike = {dan: [p for p in ps if p[9] >= zapore.IZGUBA_PRED_TABO_S]
              for dan, ps in prehodi.items()}
    # Končno stanje `run` namesto stanja ob pogledu (glej zgoraj).
    zapore.izgube_danes = lambda _c, dan, zdaj: [
        p for p in velike.get(dan, ()) if zdaj - zapore.PRED_TABO_OKNO_S <= p[8] <= zdaj]
    skupine = defaultdict(list)
    for r in vrstice:
        o = zapore.za_voznjo(conn, r["trip_id"], r["service_date"], r["from_seq"],
                             r["stop_seq"], r["current_s"] or 0, r["made_ts"])
        vrste = {x["vrsta"] for x in o}
        par = (r["ours_s"], r["actual_s"])
        skupine["vse"].append(par)
        skupine["zapora" if "zapora" in vrste else "brez zapore"].append(par)
        skupine["vlak pred tabo" if "pred_tabo" in vrste else "brez vlaka pred tabo"].append(par)
        skupine["katerokoli opozorilo" if vrste else "brez opozorila"].append(par)
    print("\n== senca: ali je bila naša številka prenizka, kjer bi viselo opozorilo")
    for ime in ("vse", "brez opozorila", "katerokoli opozorilo", "zapora", "brez zapore",
                "vlak pred tabo", "brez vlaka pred tabo"):
        pari = skupine[ime]
        n = len(pari)
        if not n:
            print(f"{ime:24} n=0")
            continue
        razlika = [b - a for a, b in pari]
        print(f"{ime:24} n={n:6}  prišel ≥5 min pozneje {sum(x > 300 for x in razlika) / n * 100:5.1f} %"
              f"  ≥10 {sum(x > 600 for x in razlika) / n * 100:5.1f} %"
              f"  MAE {st.mean(abs(x) for x in razlika) / 60:4.2f}"
              f"  povp. (resnica - naša) {st.mean(razlika) / 60:+5.2f} min")


if __name__ == "__main__":
    odseki()
    senca()
