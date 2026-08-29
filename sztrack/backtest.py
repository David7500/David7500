"""Merjenje napovedi zamude.

Napoved brez izmerjene napake je mnenje. Ta modul zgradi iz zajetih dni
naloge oblike *"vlak je na postanku i zamujal d sekund; koliko bo zamujal na
postanku j?"* in na njih primerja več modelov po istem merilu.

Postopek je izpuščanje enega dne (leave-one-day-out): model se uči na vseh
drugih zajetih dneh, napoveduje pa dan, ki ga ni videl. Brez tega bi vsak
model, ki si zapomni zgodovino, na svojih učnih podatkih dosegel odlično
oceno in ne bi povedal ničesar.

Merila:

* **MAE** -- povprečna absolutna napaka v sekundah. Občutljiva na izjeme,
  a je tisto, kar potnik čuti: pet minut napake je pet minut napake.
* **mediana napake** -- odpornejša; če se močno razlikuje od MAE, napako
  poganja peščica voženj.
* **delež v 5 min** -- kolikokrat je napoved uporabna za odločitev.

Referenčni model je `prenos` (zamuda ostane, kakršna je). Model, ki ga ne
premaga, ne zasluži, da ga aplikacija uporablja -- ne glede na to, kako je
zapleten.
"""
from __future__ import annotations

import sqlite3
import statistics
from collections import defaultdict

# Nalog s premikom cez vec kot toliko postankov ne sestavljamo: cez pol proge
# je "napoved" bolj opis voznega reda kot napoved.
MAX_HORIZON = 12

# Koliko vzorcev mora imeti skupina, da ji verjamemo mediano.
MIN_SAMPLES = 3

# Merimo napoved za zeleznico. Mestni avtobus se na svoji liniji obnasa
# drugace (kratki odseki, gneca, semaforji) in bi v isti meritvi zamegljal
# oboje -- stevilke ne bi opisovale ne enega ne drugega.
NETWORK = "zeleznica"


def _delays_by_day(conn: sqlite3.Connection,
                   network: str = NETWORK) -> dict[tuple[str, str], dict[int, int]]:
    """(train_no, dan) -> {stop_seq: zamuda}. Iz `run`, torej zadnje znano stanje."""
    rows = conn.execute(
        "SELECT t.train_no, r.service_date, r.stop_seq, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS d "
        "FROM run r JOIN trip t USING (trip_id) "
        "WHERE d IS NOT NULL AND t.network = ? "
        "ORDER BY t.train_no, r.service_date, r.stop_seq",
        (network,),
    )
    out: dict[tuple[str, str], dict[int, int]] = defaultdict(dict)
    for r in rows:
        out[(r["train_no"], r["service_date"])][r["stop_seq"]] = r["d"]
    return out


def _stop_ids(conn: sqlite3.Connection, network: str = NETWORK) -> dict[tuple[str, int], str]:
    """(train_no, stop_seq) -> stop_id. Rabi ga zdruzevanje po odsekih:
    isti fizicni odsek vozi vec vlakov in skupaj jih je dovolj za mediano."""
    rows = conn.execute(
        "SELECT t.train_no, s.stop_seq, s.stop_id FROM trip t JOIN sched s USING (trip_id) "
        "WHERE t.network = ?",
        (network,),
    )
    return {(r["train_no"], r["stop_seq"]): r["stop_id"] for r in rows}


def build_tasks(conn: sqlite3.Connection) -> list[dict]:
    """Vse naloge (vlak, dan, i, j, zamuda_i, zamuda_j)."""
    by_day = _delays_by_day(conn)
    stops = _stop_ids(conn)
    tasks = []
    for (train_no, day), delays in by_day.items():
        seqs = sorted(delays)
        for a_idx, i in enumerate(seqs):
            for j in seqs[a_idx + 1:]:
                if j - i > MAX_HORIZON:
                    break
                si, sj = stops.get((train_no, i)), stops.get((train_no, j))
                if not si or not sj:
                    continue
                tasks.append({
                    "train_no": train_no, "day": day,
                    "i": i, "j": j, "horizon": j - i,
                    "d_i": delays[i], "d_j": delays[j],
                    "seg": (si, sj),
                })
    return tasks


# ---------------------------------------------------------------- modeli
#
# Vsak model dobi ucne naloge (brez ocenjevanega dne) in vrne funkcijo, ki
# napove d_j iz ene naloge. Tako je protokol za vse enak in primerjava postena.


def _bucket(d_i: int) -> int:
    """Razred trenutne zamude. Okrevanje ni enako pri +1 in pri +40 minutah:
    vlak z veliko zamudo del nadoknadi na rezervi v voznem redu, tocen vlak
    pa je nima kaj nadoknaditi. Ena sama mediana to razliko zabrise."""
    if d_i < 120:
        return 0
    if d_i < 600:
        return 1
    if d_i < 1800:
        return 2
    return 3


def model_prenos(train_tasks):
    """Referenca: zamuda se ne spremeni."""
    return lambda t: t["d_i"]


def model_vlak(train_tasks):
    """Sedanji model: historicna mediana spremembe pri TEM vlaku."""
    table = defaultdict(list)
    for t in train_tasks:
        table[(t["train_no"], t["i"], t["j"])].append(t["d_j"] - t["d_i"])

    def predict(t):
        vals = table.get((t["train_no"], t["i"], t["j"]))
        if not vals or len(vals) < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + statistics.median(vals)
    return predict


def model_odsek(train_tasks):
    """Zdruzeno po fizicnem odseku cez vse vlake -- vec vzorcev, manj sluma."""
    table = defaultdict(list)
    for t in train_tasks:
        table[t["seg"]].append(t["d_j"] - t["d_i"])

    def predict(t):
        vals = table.get(t["seg"])
        if not vals or len(vals) < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + statistics.median(vals)
    return predict


def model_odsek_razred(train_tasks):
    """Po odseku IN razredu trenutne zamude: okrevanje je odvisno od tega,
    koliko zamude sploh je."""
    table = defaultdict(list)
    for t in train_tasks:
        table[(t["seg"], _bucket(t["d_i"]))].append(t["d_j"] - t["d_i"])
    fallback = defaultdict(list)
    for t in train_tasks:
        fallback[_bucket(t["d_i"])].append(t["d_j"] - t["d_i"])

    def predict(t):
        b = _bucket(t["d_i"])
        vals = table.get((t["seg"], b))
        if not vals or len(vals) < MIN_SAMPLES:
            vals = fallback.get(b)
        if not vals or len(vals) < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + statistics.median(vals)
    return predict


def model_zdruzen(train_tasks):
    """Vlak, kadar ga je dovolj, sicer odsek z razredom zamude.

    Utez je n/(n+k): pri malo vzorcih prevlada odsek, pri veliko vlak. To je
    obicajno krcenje proti skupini in edini nacin, da pri osmih dneh zajema
    uporabimo oboje, ne da bi zaupali mediani dveh voznj.
    """
    per_train = defaultdict(list)
    per_seg = defaultdict(list)
    per_bucket = defaultdict(list)
    for t in train_tasks:
        delta = t["d_j"] - t["d_i"]
        per_train[(t["train_no"], t["i"], t["j"])].append(delta)
        per_seg[(t["seg"], _bucket(t["d_i"]))].append(delta)
        per_bucket[_bucket(t["d_i"])].append(delta)

    K = 4.0

    def predict(t):
        b = _bucket(t["d_i"])
        seg = per_seg.get((t["seg"], b)) or per_bucket.get(b)
        base = statistics.median(seg) if seg and len(seg) >= MIN_SAMPLES else 0.0
        own = per_train.get((t["train_no"], t["i"], t["j"]))
        if not own:
            return t["d_i"] + base
        n = len(own)
        w = n / (n + K)
        return t["d_i"] + w * statistics.median(own) + (1 - w) * base
    return predict


MODELS = {
    "prenos": model_prenos,
    "vlak (sedanji)": model_vlak,
    "odsek": model_odsek,
    "odsek+razred": model_odsek_razred,
    "združen": model_zdruzen,
}


# ---------------------------------------------------------------- ocenjevanje

def _score(errors: list[float]) -> dict:
    if not errors:
        return {"n": 0}
    absolute = [abs(e) for e in errors]
    return {
        "n": len(errors),
        "mae_s": round(statistics.mean(absolute), 1),
        "median_s": round(statistics.median(absolute), 1),
        "within_5min": round(sum(1 for e in absolute if e <= 300) / len(absolute), 3),
        "bias_s": round(statistics.mean(errors), 1),
    }


def evaluate(conn: sqlite3.Connection, by_horizon: bool = False) -> dict:
    """Primerja modele z izpuščanjem enega dne."""
    tasks = build_tasks(conn)
    days = sorted({t["day"] for t in tasks})
    errors: dict[str, list[float]] = {name: [] for name in MODELS}
    per_h: dict[str, dict[int, list[float]]] = {n: defaultdict(list) for n in MODELS}

    for day in days:
        train = [t for t in tasks if t["day"] != day]
        test = [t for t in tasks if t["day"] == day]
        if not train or not test:
            continue
        for name, factory in MODELS.items():
            predict = factory(train)
            for t in test:
                err = predict(t) - t["d_j"]
                errors[name].append(err)
                if by_horizon:
                    per_h[name][t["horizon"]].append(err)

    out = {
        "days": days,
        "tasks": len(tasks),
        "models": {name: _score(errs) for name, errs in errors.items()},
    }
    if by_horizon:
        out["by_horizon"] = {
            name: {h: _score(v) for h, v in sorted(hs.items())}
            for name, hs in per_h.items()
        }
    return out


# ---------------------------------------------------------------- prevoznikova napoved
#
# Feed poslje vrednost tudi za postanke, ki jih vlak se ni dosegel. To ni
# meritev, ampak napoved prevoznika -- in je edini model, ki ve za stvari,
# ki jih iz zgodovine ni mogoce vedeti: okvaro, zaporo, krizanje vlakov.
# Ce je dobra, nas model ni potreben tam, kjer jo feed ima.


def operator_forecast_tasks(conn: sqlite3.Connection) -> list[dict]:
    """Naloge, pri katerih vemo, kaj je feed o cilju trdil v trenutku, ko je
    bila zamuda na izhodiscu zadnjic potrjena.

    Iz dnevnika `obs`: za vsak postanek vzamemo zadnji zapis pred tistim
    trenutkom. To je natanko tisto, kar bi prikaz takrat pokazal.
    """
    rows = conn.execute(
        "SELECT t.train_no, o.trip_id, o.service_date, o.stop_seq, o.feed_ts, "
        "       COALESCE(o.delay_arr, o.delay_dep) AS d "
        "FROM obs o JOIN trip t USING (trip_id) "
        "WHERE d IS NOT NULL AND t.network = ? "
        "ORDER BY o.trip_id, o.service_date, o.stop_seq, o.feed_ts",
        (NETWORK,),
    ).fetchall()

    log: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    final: dict[tuple, int] = {}
    for r in rows:
        key = (r["trip_id"], r["service_date"], r["stop_seq"])
        log[key].append((r["feed_ts"], r["d"]))
        final[key] = r["d"]

    names = {r["trip_id"]: r["train_no"]
             for r in conn.execute("SELECT trip_id, train_no FROM trip WHERE network = ?",
                                   (NETWORK,))}

    by_run: dict[tuple, list[int]] = defaultdict(list)
    for trip_id, day, seq in log:
        by_run[(trip_id, day)].append(seq)

    tasks = []
    for (trip_id, day), seqs in by_run.items():
        seqs.sort()
        for idx, i in enumerate(seqs):
            t_i = log[(trip_id, day, i)][-1][0]      # kdaj je bil i zadnjic potrjen
            d_i = final[(trip_id, day, i)]
            for j in seqs[idx + 1:]:
                if j - i > MAX_HORIZON:
                    break
                # Kaj je feed takrat trdil o j -- zadnji zapis pred t_i.
                said = None
                for ts, d in log[(trip_id, day, j)]:
                    if ts <= t_i:
                        said = d
                    else:
                        break
                if said is None:
                    continue        # o j takrat se ni povedal nicesar
                tasks.append({
                    "train_no": names.get(trip_id, "?"), "day": day,
                    "i": i, "j": j, "horizon": j - i,
                    "d_i": d_i, "d_j": final[(trip_id, day, j)],
                    "operator": said,
                })
    return tasks


def evaluate_operator(conn: sqlite3.Connection) -> dict:
    """Prevoznikova napoved proti prenosu zamude, na istih nalogah.

    Primerjava mora teci na ISTI mnozici nalog, sicer ne pove nicesar: naloge,
    pri katerih feed ze ima vrednost za cilj, so drugacne od povprecne naloge --
    vlak je takrat blizu in napoved lazja.
    """
    tasks = operator_forecast_tasks(conn)
    if not tasks:
        return {"tasks": 0}
    return {
        "tasks": len(tasks),
        "models": {
            "prenos": _score([t["d_i"] - t["d_j"] for t in tasks]),
            "prevoznik": _score([t["operator"] - t["d_j"] for t in tasks]),
        },
        "by_horizon": {
            "prevoznik": {
                h: _score([t["operator"] - t["d_j"] for t in tasks if t["horizon"] == h])
                for h in sorted({t["horizon"] for t in tasks})
            },
            "prenos": {
                h: _score([t["d_i"] - t["d_j"] for t in tasks if t["horizon"] == h])
                for h in sorted({t["horizon"] for t in tasks})
            },
        },
    }


def model_vlak_dan(train_tasks):
    """Vlak + popravek za stanje mreže na ta dan.

    Zamisel: če cel dan zamuja bolj kot običajno (nesreča, nevihta, zapora),
    bo tudi ta vlak zamujal bolj, kot pravi njegova zgodovina. Popravek je
    razlika med današnjo mediano spremembe zamude čez vso mrežo in mediano
    čez vse dni.

    Pozor na tisto, kar bi bilo goljufanje: popravek se računa iz **drugih
    voženj istega dne**, ne iz te. V resnici bi ga aplikacija poznala, ker so
    te vožnje že prevožene, ko gledaš svojo.

    **Izmerjeno: ne pomaga.** MAE 2,00 -> 2,06 min, delež v petih minutah
    90,2 % -> 89,1 %. Povprečna sprememba zamude se čez zajete dni giblje med
    115 in 142 s, torej pod pol minute -- premalo, da bi popravek česa rešil,
    dovolj, da doda šum. Zamisel je pustena tu z ukazom
    `sztrack backtest --day-offset`, da je ni treba znova preizkušati.
    """
    per_train = defaultdict(list)
    for t in train_tasks:
        per_train[(t["train_no"], t["i"], t["j"])].append(t["d_j"] - t["d_i"])
    base = statistics.mean([t["d_j"] - t["d_i"] for t in train_tasks]) if train_tasks else 0.0

    def predict_with(day_offset):
        def predict(t):
            own = per_train.get((t["train_no"], t["i"], t["j"]))
            delta = statistics.median(own) if own and len(own) >= MIN_SAMPLES else 0.0
            return t["d_i"] + delta + day_offset
        return predict

    predict_with.base = base
    return predict_with


def evaluate_day_offset(conn: sqlite3.Connection) -> dict:
    """Ali stanje mreže na ta dan izboljša napoved?

    Model brez popravka proti modelu s popravkom, na istih nalogah in po istem
    protokolu (izpuščanje enega dne). Popravek se za vsak dan izračuna iz
    voženj tistega dne, ki niso ocenjevana naloga.
    """
    tasks = build_tasks(conn)
    days = sorted({t["day"] for t in tasks})
    errs_plain: list[float] = []
    errs_offset: list[float] = []

    for day in days:
        train = [t for t in tasks if t["day"] != day]
        test = [t for t in tasks if t["day"] == day]
        if not train or not test:
            continue
        factory = model_vlak_dan(train)
        plain = factory(0.0)

        # Stanje dneva: POVPRECNA sprememba zamude na ta dan, minus povprecje
        # cez vse dni. Mediana je tu neuporabna -- pri vecini sosednjih
        # postankov se zamuda ne spremeni, zato je mediana vsak dan 0 in
        # popravek vedno nic. Povprecje se giblje med 115 in 142 s.
        day_mean = statistics.mean([t["d_j"] - t["d_i"] for t in test])
        offset = day_mean - factory.base
        adjusted = factory(offset)

        for t in test:
            errs_plain.append(plain(t) - t["d_j"])
            errs_offset.append(adjusted(t) - t["d_j"])

    return {
        "tasks": len(tasks),
        "models": {
            "vlak": _score(errs_plain),
            "vlak + stanje dneva": _score(errs_offset),
        },
    }
