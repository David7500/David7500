"""Predelava modela napovedi za vlake: jedrni model, veriga odsekov, hibrid.

Raziskovalna skripta (9. 11. 2026, zapis.md). V kodo je šel `hibrid+ pol=21`
kot `stats.mesanice_naprej` (mediana in kvantil 0,30); merilo zanj za naprej
je `kajros backtest --varne --modeli 'podobni;podobni varna'`.

Protokol NAPREJ: model za dan D vidi samo dni pred D (do 90 dni), kot produkcija.
Ucenje iz ociscenih postankov (`stats.ocisti_dan`), ocena na nalogah, kjer oba
postanka prezivita ciscenje. Raba:

  python modeli2.py <baza> [--vzorec N] [--od DAN] [--modeli a,b] [--loo]
"""
import argparse
import math
import statistics
import sys
import time
import zlib
from collections import defaultdict
from datetime import date

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from kajros import backtest, db, ocena, stats  # noqa: E402

AS = stats._after_slack
BUCKET = stats.delay_bucket
MAXH = backtest.MAX_HORIZON
R = ocena.POTNIKOVA_REZERVA_S
RAZMIK = ocena.RAZMIK_S["zeleznica"]


def wq(pari, q):
    """Utezen kvantil z linearno interpolacijo (sredine utezi)."""
    pari.sort()
    W = sum(w for _, w in pari)
    if W <= 0:
        return None
    t = q * W
    c = 0.0
    pv = pp = None
    for v, w in pari:
        pos = c + w / 2
        if pos >= t:
            if pv is None or pos == pp:
                return v
            return pv + (v - pv) * (t - pp) / (pos - pp)
        pv, pp = v, pos
        c += w
    return pv


# ------------------------------------------------------------------ modeli
# napovej(H, rez, postanki, i, d, cilji) -> {j: napoved}
# H = [(starost_dni, {seq: zamuda})], cilji = [(j, rezerva i..j)]

def _pari(H, i, j, sl):
    return [(g[i], g[j] - AS(g[i], sl), st) for st, g in H if i in g and j in g]


def m_prenos(H, rez, postanki, i, d, cilji):
    return {j: d for j, _ in cilji}


def m_fizika(H, rez, postanki, i, d, cilji):
    return {j: AS(d, sl) for j, sl in cilji}


def m_sedanji(H, rez, postanki, i, d, cilji):
    out, b = {}, BUCKET(d)
    for j, sl in cilji:
        p = _pari(H, i, j, sl)
        raz = [o for d0, o, _ in p if BUCKET(d0) == b]
        ost = raz if len(raz) >= 3 else [o for _, o, _ in p]
        o = stats._omejen_ostanek(statistics.median(ost), d) if ost else 0
        out[j] = AS(d, sl) + round(o)
    return out


def m_varna(q):
    def f(H, rez, postanki, i, d, cilji):
        out, b = {}, BUCKET(d)
        for j, sl in cilji:
            p = _pari(H, i, j, sl)
            raz = [o for d0, o, _ in p if BUCKET(d0) == b]
            o = stats.varni_ostanek(raz, [o for _, o, _ in p], d, "zeleznica", q=q)
            out[j] = AS(d, sl) + (o or 0)
        return out
    return f


def _utezi(vzorci, d, n0, h0, hk, pol):
    """vzorci = [(d0, vrednost, starost)] -> [(vrednost, utez)].

    Utez = starost x (jedro podobnosti zamude + predhodnik n0, razdeljen po dneh).
    """
    h = h0 + hk * abs(d)
    a = [0.5 ** (st / pol) if pol else 1.0 for _, _, st in vzorci]
    A = sum(a)
    if A <= 0:
        return []
    out = []
    for (d0, v, _), ag in zip(vzorci, a):
        x = (d - d0) / h
        out.append((v, ag * (math.exp(-0.5 * x * x) + n0 / A)))
    return out


def m_jedro(q=0.5, n0=3.0, h0=90, hk=0.25, pol=0, omeji=True, dno=True):
    def f(H, rez, postanki, i, d, cilji):
        out = {}
        for j, sl in cilji:
            osnova = AS(d, sl)
            u = _utezi(_pari(H, i, j, sl), d, n0, h0, hk, pol)
            o = wq(u, q) if u else None
            if o is None:
                out[j] = osnova
                continue
            if omeji:
                o = stats._omejen_ostanek(o, d)
            v = osnova + round(o)
            out[j] = max(v, min(d, 0)) if dno else v
        return out
    return f


def _korak(P, H, a, b, sl, n0, h0, hk, pol, mreza):
    """Porazdelitev zamude na b iz porazdelitve na a (en clen verige)."""
    vz = _pari(H, a, b, sl)
    Q = defaultdict(float)
    if len(vz) < 3:
        for v, p in P.items():
            Q[AS(v, sl)] += p
        return Q
    for v, p in P.items():
        osnova = AS(v, sl)
        u = _utezi(vz, v, n0, h0, hk, pol)
        W = sum(w for _, w in u)
        dno = min(v, 0)
        for o, w in u:
            x = max(osnova + o, dno)
            Q[int(round(x / mreza)) * mreza] += p * w / W
    if len(Q) > 60:
        Q = {v: p for v, p in Q.items() if p >= 0.002}
        s = sum(Q.values())
        Q = {v: p / s for v, p in Q.items()}
    return Q


def _veriga(H, rez, postanki, i, d, cilji, n0, h0, hk, pol, mreza=60):
    """{j: porazdelitev {zamuda: verjetnost}} po verigi hrbtenice.

    Hrbtenica = postanki, izmerjeni v vsaj polovici dni zgodovine. Cilj zunaj
    hrbtenice je stranska veja od zadnjega clena pred njim.
    """
    n = len(H)
    stej = defaultdict(int)
    for _, g in H:
        for s in g:
            stej[s] += 1
    zadnji = cilji[-1][0]
    hrbet = [s for s in postanki if i < s <= zadnji and stej[s] * 2 >= n]
    cilj = {j for j, _ in cilji}

    def rezerva(a, b):
        return sum(rez.get(k, 0) for k in postanki if a < k <= b)

    out = {}
    P, pos = {d: 1.0}, i
    cakajo = sorted(cilj)
    for s in hrbet:
        for j in [c for c in cakajo if pos < c < s]:
            out[j] = _korak(P, H, pos, j, rezerva(pos, j), n0, h0, hk, pol, mreza)
        P = _korak(P, H, pos, s, rezerva(pos, s), n0, h0, hk, pol, mreza)
        pos = s
        if s in cilj:
            out[s] = P
    for j in [c for c in cakajo if c > pos]:
        out[j] = _korak(P, H, pos, j, rezerva(pos, j), n0, h0, hk, pol, mreza)
    return out


def m_veriga(q=0.5, n0=3.0, h0=90, hk=0.25, pol=0):
    def f(H, rez, postanki, i, d, cilji):
        if not H:
            return {j: AS(d, sl) for j, sl in cilji}
        D = _veriga(H, rez, postanki, i, d, cilji, n0, h0, hk, pol)
        return {j: round(wq(list(D[j].items()), q)) for j, _ in cilji}
    return f


def m_hibrid(q=0.5, nv=4.0, h0=90, hk=0.25, pol=0, n0v=3.0, omeji=False):
    """Neposredni podobni dnevi (jedro) + veriga kot predhodnik z utezjo nv."""
    def f(H, rez, postanki, i, d, cilji):
        if not H:
            return {j: AS(d, sl) for j, sl in cilji}
        D = _veriga(H, rez, postanki, i, d, cilji, n0v, h0, hk, pol)
        out = {}
        for j, sl in cilji:
            osnova = AS(d, sl)
            u = [(osnova + o, w) for o, w in
                 _utezi(_pari(H, i, j, sl), d, 0.0, h0, hk, pol)]
            u += [(v, p * nv) for v, p in D[j].items()]
            v = wq(u, q)
            if omeji:
                v = osnova + stats._omejen_ostanek(v - osnova, d)
            out[j] = max(round(v), min(d, 0))
        return out
    return f


MODELI = {
    "prenos": m_prenos,
    "fizika": m_fizika,
    "sedanji": m_sedanji,
    "varna_q25": m_varna(0.25),
    "jedro": m_jedro(),
    "jedro brez meje": m_jedro(omeji=False),
    "jedro n0=1.5": m_jedro(n0=1.5),
    "jedro n0=6": m_jedro(n0=6),
    "jedro ozko": m_jedro(h0=60, hk=0.15),
    "jedro siroko": m_jedro(h0=150, hk=0.4),
    "jedro pol=21": m_jedro(pol=21),
    "jedro pol=45": m_jedro(pol=45),
    "jedro q25": m_jedro(q=0.25),
    "jedro q35": m_jedro(q=0.35),
    "veriga": m_veriga(),
    "veriga q25": m_veriga(q=0.25),
    "veriga pol=21": m_veriga(pol=21),
    "hibrid": m_hibrid(),
    "hibrid nv=8": m_hibrid(nv=8),
    "hibrid q25": m_hibrid(q=0.25),
    "hibrid q35": m_hibrid(q=0.35),
    "hibrid pol=21": m_hibrid(pol=21),
}


def okno(model, dni):
    """Isti model, zgodovina samo zadnjih N dni."""
    def f(H, rez, postanki, i, d, cilji):
        return model([x for x in H if x[0] <= dni], rez, postanki, i, d, cilji)
    return f


MODELI.update({
    "sedanji okno=21": okno(m_sedanji, 21),
    "sedanji okno=30": okno(m_sedanji, 30),
    "sedanji okno=45": okno(m_sedanji, 45),
    "varna_q25 okno=30": okno(m_varna(0.25), 30),
    "jedro pol=7": m_jedro(pol=7),
    "jedro pol=14": m_jedro(pol=14),
    "jedro pol=30": m_jedro(pol=30),
    "jedro q25 pol=21": m_jedro(q=0.25, pol=21),
    "jedro q30 pol=21": m_jedro(q=0.30, pol=21),
    "jedro q35 pol=21": m_jedro(q=0.35, pol=21),
    "hibrid+ pol=21": m_hibrid(pol=21, omeji=True),
    "hibrid+ pol=14": m_hibrid(pol=14, omeji=True),
    "hibrid+ q25 pol=21": m_hibrid(q=0.25, pol=21, omeji=True),
    "hibrid+ q30 pol=21": m_hibrid(q=0.30, pol=21, omeji=True),
    "hibrid+ q35 pol=21": m_hibrid(q=0.35, pol=21, omeji=True),
    "veriga q30 pol=21": m_veriga(q=0.30, pol=21),
})


def m_produkcija(q):
    """Koda iz `kajros/stats.py` (kar streže senca), za preverbo enakosti."""
    def f(H, rez, postanki, i, d, cilji):
        mes = stats.mesanice_naprej(H, rez, postanki, i, d, [j for j, _ in cilji])
        return {j: stats.iz_mesanice(o, m, d, q) for j, (o, m) in mes.items()}
    return f


MODELI.update({
    "produkcija": m_produkcija(0.5),
    "produkcija varna": m_produkcija(stats.KVANTIL_VARNE_PODOBNI),
})


# ------------------------------------------------------------------ podatki

SUROVO = False


def nalozi(pot):
    conn = db.connect(pot)
    enote, ok, _ = backtest.ocisti_enote(conn, "zeleznica", "")
    rez = {v: {s: max(0, x - backtest.MIN_DWELL_S) for s, x in d.items()}
           for v, d in backtest._dwells(conn).items()}
    postanki = defaultdict(list)
    for (v, s) in backtest._stop_ids(conn):
        postanki[v].append(s)
    for v in postanki:
        postanki[v].sort()
    dnevi = defaultdict(list)       # voznja -> [(dan, {seq: d} ocisceno)]
    for (v, dan), m in sorted(enote.items()):
        g = {s: x[0] for s, x in m.items() if s in ok[(v, dan)]}
        if g:
            # --surovo: ucenje iz neociscenih dni, ocena ostane na ociscenih
            dnevi[v].append((dan, g, {s: x[0] for s, x in m.items()} if SUROVO else g))
    return dnevi, rez, postanki


def ord_(dan):
    return date.fromisoformat(dan).toordinal()


def meri(pari):
    n = len(pari)
    if not n:
        return None
    return (n,
            sum(abs(a - b) for a, b in pari) / n / 60,
            sum(1 for a, b in pari if abs(a - b) <= 120) / n * 100,
            sum(1 for a, b in pari if a < b - R) / n * 100,
            sum(1 for a, b in pari if a > b + R) / n * 100,
            sum(ocena.strosek_para(a, b, RAZMIK) for a, b in pari) / n / 60,
            sum(a - b for a, b in pari) / n / 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baza")
    ap.add_argument("--vzorec", type=int, default=8)
    ap.add_argument("--od", default="2026-10-17")
    ap.add_argument("--do", default="9999")
    ap.add_argument("--modeli", default="")
    ap.add_argument("--loo", action="store_true")
    ap.add_argument("--surovo", action="store_true")
    ap.add_argument("--rezi", action="store_true", help="razrez po horizontu in razredu")
    a = ap.parse_args()
    imena = [m.strip() for m in a.modeli.split(",") if m.strip()] or list(MODELI)
    t0 = time.time()
    global SUROVO
    SUROVO = a.surovo
    dnevi, rez, postanki = nalozi(a.baza)
    print(f"# nalozeno {sum(len(x) for x in dnevi.values())} voženj-dni, {time.time()-t0:.0f} s",
          flush=True)

    pari = {m: [] for m in imena}                 # (napoved, resnica)
    rezi = {m: defaultdict(list) for m in imena}  # razrez
    zvez = {m: [] for m in imena}                 # |skok| pri sosednjih izhodiscih
    enot_skok = {m: 0 for m in imena}
    cas = {m: 0.0 for m in imena}
    enot = 0
    for v, seznam in dnevi.items():
        ords = [ord_(x[0]) for x in seznam]
        for k, (dan, g, _) in enumerate(seznam):
            if not (a.od <= dan < a.do) or zlib.crc32(f"{v}|{dan}".encode()) % a.vzorec:
                continue
            if a.loo:
                H = [(abs(ords[k] - ords[x]), seznam[x][2]) for x in range(len(seznam))
                     if x != k and abs(ords[k] - ords[x]) <= 90]
            else:
                H = [(ords[k] - ords[x], seznam[x][2]) for x in range(k)
                     if ords[k] - ords[x] <= 90]
            enot += 1
            seqs = sorted(g)
            r, ps = rez.get(v, {}), postanki[v]
            napovedi = {m: {} for m in imena}
            for ai, i in enumerate(seqs):
                cilji = [(j, sum(r.get(x, 0) for x in ps if i < x <= j))
                         for j in seqs[ai + 1:] if j - i <= MAXH]
                if not cilji:
                    continue
                for m in imena:
                    t1 = time.time()
                    out = MODELI[m](H, r, ps, i, g[i], cilji)
                    cas[m] += time.time() - t1
                    napovedi[m][i] = out
                    for j, _ in cilji:
                        pari[m].append((out[j], g[j]))
                        if a.rezi:
                            hz = "h1-3" if j - i <= 3 else "h4-8" if j - i <= 8 else "h9-12"
                            rezi[m][hz].append((out[j], g[j]))
                            rezi[m][f"razred{BUCKET(g[i])}"].append((out[j], g[j]))
            for m in imena:
                naj = 0
                for x, y in zip(seqs, seqs[1:]):
                    if abs(g[y] - g[x]) > 60 or y not in napovedi[m] or x not in napovedi[m]:
                        continue
                    for j, pv in napovedi[m][y].items():
                        if j not in napovedi[m][x]:
                            continue
                        s = abs(pv - napovedi[m][x][j])
                        zvez[m].append(s)
                        naj = max(naj, s)
                enot_skok[m] += naj > 300
    print(f"# {enot} enot, {time.time()-t0:.0f} s; protokol {'LOO' if a.loo else 'naprej'}, "
          f"od {a.od} do {a.do}, vzorec 1/{a.vzorec}")
    print("model | n | MAE | v 2 min | podc. | prec. | strošek | odklon | zveznost | skok>5 | enot s skokom | s")
    print("---|---|---|---|---|---|---|---|---|---|---|---")
    for m in imena:
        x = meri(pari[m])
        z = zvez[m]
        print(f"{m} | {x[0]} | {x[1]:.3f} | {x[2]:.1f} | {x[3]:.1f} | {x[4]:.2f} | {x[5]:.2f} | "
              f"{x[6]:+.2f} | {sum(z)/len(z)/60:.2f} | {sum(1 for s in z if s > 300)/len(z)*100:.2f} | "
              f"{enot_skok[m]/enot*100:.1f} | {cas[m]:.0f}")
    if a.rezi:
        for kljuc in ("h1-3", "h4-8", "h9-12", "razred0", "razred1", "razred2", "razred3"):
            print(f"\n{kljuc}: model | n | MAE | prec. | strošek | odklon")
            for m in imena:
                x = meri(rezi[m][kljuc])
                if x:
                    print(f"  {m} | {x[0]} | {x[1]:.3f} | {x[4]:.2f} | {x[5]:.2f} | {x[6]:+.2f}")


if __name__ == "__main__":
    main()
