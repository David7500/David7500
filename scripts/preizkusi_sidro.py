"""Prevoznikova višja vrednost: samo na svojem postanku ali tudi naprej?

Ponovi napovedi naprej po progi z več pravili in jih primerja z resnico. Okno
prevoznika (kaj je feed trdil o postankih pred vlakom) se obnovi iz `obs` --
`run` hrani samo zadnje stanje in bi prevoznika ocenjeval z njegovo zadnjo,
ne takratno besedo.

Dve merili:
  senca  naloge iz `napoved`: kaj je potnik videl ~25 min pred vlakom
  poll   vsak zapis v `obs` posebej: stanje ob T, meja meritve po pravilu
         `_LAST_MEASURED_SQL`, cilji = postanki, ki jih vlak ob T še ni
         dosegel, do 60 min naprej

Pravila:
  A   vsak postanek zase: max(naša, prevoznikova) (do 5. 10. 2026)
  B1  zamuda ne pade razen za rezervo postanka
  B2  presežek prevoznika se nese naprej, troši ga le rezerva postankov
  C   kjer prevoznik ve več, model od tam računa naprej (novo izhodišče)
  CT  C in čas, ki ne teče nazaj (`stats.SIDRO_PREVOZNIKA`, v uporabi)

Zagon: KAJROS_DB=... ./venv/bin/python scripts/preizkusi_sidro.py [senca|poll] [največ voženj]
Rail del baze z arwena: glej spomin „analiza-baze-arwen“; senca 2 min, poll 5 min.
"""
import sys
import time
from collections import defaultdict

sys.path.insert(0, ".")
from kajros import db, ocena, stats                       # noqa: E402

NET = "zeleznica"
# `predict` naj vrne golo lastno oceno; pravila sestavlja ta skript.
stats.SIDRO_PREVOZNIKA = set()
conn = db.connect()

_lastna: dict = {}


def lastna(tn, tid, day, a, d_a):
    """Naš model brez feeda od izhodišča (a, d_a): {seq: (ocena, rezerva tu)}."""
    k = (tid, day, a, d_a)
    if k not in _lastna:
        out, prej = {}, 0
        for x in stats.predict(conn, tn, a, d_a, exclude_date=day, trip_id=tid):
            out[x["stop_seq"]] = (x["own_delay_s"], x["slack_s"] - prej)
            prej = x["slack_s"]
        _lastna[k] = out
    return _lastna[k]


def napoved(pravilo, tn, tid, day, a, d_a, stanje, postanek, cas):
    """{seq: napoved} za vse postanke za `a`.

    stanje: seq -> (zamuda, prihodna zamuda, feed_ts) -- kar je feed vedel ob T.
    """
    own = lastna(tn, tid, day, a, d_a)
    seqs = sorted(own)
    arr_a = stanje.get(a, (None, None, None))[1]

    def prevoznik(k):
        v = stanje.get(k)
        if v is None or stats._operator_is_stale(v[0], arr_a, d_a, postanek.get(a, 0)):
            return None
        return v[0]

    out = {}
    if pravilo == "A":
        for k in seqs:
            out[k] = stats._with_operator(own[k][0], prevoznik(k), NET)
    elif pravilo in ("B1", "B2"):
        prej, e = d_a, 0
        for k in seqs:
            ow, w = own[k]
            p = stats._with_operator(ow, prevoznik(k), NET)
            if pravilo == "B1":
                p = max(p, stats._after_slack(prej, w))
                prej = p
            else:
                e = max(p - ow, stats._after_slack(e, w))
                p = ow + e
            out[k] = p
    elif pravilo == "C":
        sa, sd = a, d_a
        for k in seqs:
            ow = lastna(tn, tid, day, sa, sd)[k][0]
            p = stats._with_operator(ow, prevoznik(k), NET)
            out[k] = p
            if p > ow:
                sa, sd = k, p
    elif pravilo == "CT":
        c = napoved("C", tn, tid, day, a, d_a, stanje, postanek, cas)
        prej = cas.get(a, 0) + d_a
        for k in seqs:
            out[k] = max(c[k], prej - cas.get(k, 0))
            prej = cas.get(k, 0) + out[k]
    return out


PRAVILA = ("A", "B1", "B2", "C", "CT")


def nazaj(nap, a, d_a, cas):
    """Ali v pogledu vlak odpelje s postaje, preden odpelje s prejšnje?"""
    prej = cas.get(a, 0) + d_a
    for k in sorted(nap):
        t = cas.get(k, 0) + nap[k]
        if t < prej - 30:
            return True
        prej = t
    return False


def nalozi_obs(kljuci):
    log = defaultdict(list)
    for r in conn.execute(
            "SELECT o.trip_id, o.service_date, o.stop_seq, o.delay_arr, "
            "       COALESCE(o.delay_dep, o.delay_arr) AS d, o.feed_ts, o.observed_at "
            "FROM obs o JOIN trip t USING (trip_id) WHERE t.network = ? "
            "ORDER BY o.observed_at, o.stop_seq", (NET,)):
        k = (r["trip_id"], r["service_date"])
        if kljuci is None or k in kljuci:
            log[k].append((r["observed_at"], r["stop_seq"], r["d"], r["delay_arr"], r["feed_ts"]))
    return log


def stanje_ob(dnevnik, T):
    st = {}
    for videno, seq, d, arr, fts in dnevnik:
        if videno > T:
            break
        if d is not None:
            st[seq] = (d, arr, fts)
    return st


def vozni_red(tid):
    rows = conn.execute("SELECT stop_seq, arr_s, dep_s FROM sched WHERE trip_id = ?",
                        (tid,)).fetchall()
    cas = {r["stop_seq"]: r["dep_s"] if r["dep_s"] is not None else r["arr_s"] for r in rows}
    postanek = {r["stop_seq"]: r["dep_s"] - r["arr_s"] for r in rows
                if r["arr_s"] is not None and r["dep_s"] is not None}
    return cas, postanek


def porocilo(pari, naslov):
    print(f"\n== {naslov}")
    print(f"{'':6}{'n':>9}{'MAE':>7}{'v5':>7}{'podc':>7}{'prec':>7}{'odkl':>7}{'strošek':>9}")
    for v, p in pari.items():
        m = ocena._meritve(p, NET)
        if m["n"]:
            print(f"{v:6}{m['n']:>9}{m['mae_min']:>7.2f}{m['v5min']:>7.1f}"
                  f"{m['podcenjenih']:>7.1f}{m['precenjenih']:>7.1f}{m['odklon_min']:>7.2f}"
                  f"{m['strosek_min']:>9.2f}")


def zapisi(pari, razlicni, pogledi, kaj):
    for v, (n, z) in pogledi.items():
        print(f"  {v}: pogledov s časom nazaj {z}/{n} = {z / n * 100:.2f} %")
    porocilo(pari, f"{kaj}, vse")
    porocilo(razlicni, f"{kaj}, kjer se pravila razlikujejo")


def oceni(rez, cilji, pari, razlicni):
    for k, resnica, *dodatno in cilji:
        vals = {v: rez[v][k] for v in rez}
        for v, p in vals.items():
            pari[v].append((p, resnica))
            for d in dodatno:
                d[v].append((p, resnica))
        if len(set(vals.values())) > 1:
            for v, p in vals.items():
                razlicni[v].append((p, resnica))


def senca(najvec):
    vrstice = [dict(r) for r in conn.execute(
        "SELECT n.*, t.train_no FROM napoved n JOIN trip t USING (trip_id) "
        "WHERE n.network = ? AND n.actual_s IS NOT NULL AND n.from_seq IS NOT NULL "
        "  AND ABS(n.actual_s) <= ?", (NET, stats.MAX_REALNA_ZAMUDA_S))]
    skupine = defaultdict(list)
    for r in vrstice:
        skupine[(r["trip_id"], r["service_date"], r["made_ts"], r["from_seq"],
                 r["current_s"] or 0)].append(r)
    kljuci = {(k[0], k[1]) for k in skupine}
    if najvec:
        kljuci = set(sorted(kljuci)[:najvec])
    log = nalozi_obs(kljuci)
    print(f"vrstic sence: {len(vrstice)}, pogledov {len(skupine)}, voženj {len(kljuci)}")
    pari, razlicni = defaultdict(list), defaultdict(list)
    pogledi = defaultdict(lambda: [0, 0])
    for (tid, day, made, a, d_a), rows in skupine.items():
        if (tid, day) not in kljuci:
            continue
        cas, postanek = vozni_red(tid)
        st = stanje_ob(log.get((tid, day), []), made)
        rez = {v: napoved(v, rows[0]["train_no"], tid, day, a, d_a, st, postanek, cas)
               for v in PRAVILA}
        for v in rez:
            pogledi[v][0] += 1
            pogledi[v][1] += nazaj(rez[v], a, d_a, cas)
        oceni(rez, [(r["stop_seq"], r["actual_s"]) for r in rows if r["stop_seq"] in rez["A"]],
              pari, razlicni)
    zapisi(pari, razlicni, pogledi, "senca")


def poll(najvec):
    log = nalozi_obs(None)
    kljuci = sorted(log)[:najvec or None]
    stevilka = {r["trip_id"]: r["train_no"] for r in conn.execute(
        "SELECT trip_id, train_no FROM trip WHERE network = ?", (NET,))}
    print(f"voženj-dni: {len(kljuci)}")
    pari, razlicni = defaultdict(list), defaultdict(list)
    po_cilju = defaultdict(lambda: defaultdict(list))
    pogledi = defaultdict(lambda: [0, 0])
    t0 = time.time()
    for n, (tid, day) in enumerate(kljuci):
        dnevnik = log[(tid, day)]
        cas, postanek = vozni_red(tid)
        polnoc = stats.polnoc(day)
        resnica = {seq: d for _, seq, d, _, _ in dnevnik if d is not None}
        for T in sorted({o[0] for o in dnevnik}):
            st = stanje_ob(dnevnik, T)
            if not st:
                continue
            zadnji_ts = max(v[2] for v in st.values())
            # Meja meritve: isto kot `_LAST_MEASURED_SQL`.
            a, prev_max, prev_ts = None, 0, None
            for seq in sorted(st):
                d, _, fts = st[seq]
                if (seq in cas and polnoc + cas[seq] + d <= min(T, zadnji_ts)
                        and not (d == 0 and prev_max >= 300)
                        and not (prev_ts is not None and fts < prev_ts)):
                    a = seq
                prev_max = max(prev_max, d)
                prev_ts = max(prev_ts or 0, fts)
            if a is None or abs(st[a][0]) > stats.MAX_REALNA_ZAMUDA_S:
                continue
            cilji = [(k, resnica[k], po_cilju[(polnoc + cas[k] + resnica[k] - T) // 900])
                     for k in resnica if k > a and k in cas
                     and abs(resnica[k]) <= stats.MAX_REALNA_ZAMUDA_S
                     and 0 < polnoc + cas[k] + resnica[k] - T <= 3600]
            if not cilji:
                continue
            rez = {v: napoved(v, stevilka[tid], tid, day, a, st[a][0], st, postanek, cas)
                   for v in PRAVILA}
            for v in rez:
                pogledi[v][0] += 1
                pogledi[v][1] += nazaj(rez[v], a, st[a][0], cas)
            oceni(rez, [c for c in cilji if c[0] in rez["A"]], pari, razlicni)
        if n % 2000 == 0:
            print(f"  {n}/{len(kljuci)} {time.time() - t0:.0f} s", flush=True)
    zapisi(pari, razlicni, pogledi, "poll, cilj do 60 min")
    for h in sorted(po_cilju):
        porocilo(po_cilju[h], f"poll, cilj čez {h * 15}-{h * 15 + 15} min")


if __name__ == "__main__":
    kaj = sys.argv[1] if len(sys.argv) > 1 else "senca"
    {"senca": senca, "poll": poll}[kaj](int(sys.argv[2]) if len(sys.argv) > 2 else 0)
