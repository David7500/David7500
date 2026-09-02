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

from . import stats

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
    """(voznja, dan) -> {stop_seq: zamuda}. Iz `run`, torej zadnje znano stanje.

    Kljuc je `trip_id`, ne `train_no`. Pri zeleznici je to isto -- 0 od 663
    stevilk z meritvami ima vec kot eno voznjo -- pri avtobusu pa nikakor:
    LPP linija 25 ima 217 voznj obeh smeri in "postanek 2" bi zdruzil dva
    razlicna kraja. Model bi se ucil mediano spremembe med krajema, ki nista
    sosednja in nista niti v isti smeri.
    """
    rows = conn.execute(
        "SELECT r.trip_id AS train_no, r.service_date, r.stop_seq, "
        "       COALESCE(r.delay_dep, r.delay_arr) AS d "
        "FROM run r JOIN trip t USING (trip_id) "
        "WHERE d IS NOT NULL AND t.network = ? "
        "ORDER BY r.trip_id, r.service_date, r.stop_seq",
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
        "SELECT t.trip_id AS train_no, s.stop_seq, s.stop_id "
        "FROM trip t JOIN sched s USING (trip_id) "
        "WHERE t.network = ?",
        (network,),
    )
    return {(r["train_no"], r["stop_seq"]): r["stop_id"] for r in rows}


#: Najkrajsi postanek, ki ga vlak se zmore -- skupen s `stats`, sicer bi
#: merili en model in uporabljali drugega.
MIN_DWELL_S = stats.MIN_DWELL_S


def _dwells(conn: sqlite3.Connection, network: str = NETWORK) -> dict[str, dict[int, int]]:
    """train_no -> {stop_seq: voznoredno zadrzevanje v sekundah}.

    Iz voznega reda, ne iz meritev: rezerva je lastnost voznega reda in je
    znana vnaprej -- to je edini vhod v napoved, ki ni statistika.
    """
    out: dict[str, dict[int, int]] = defaultdict(dict)
    for r in conn.execute(
        "SELECT t.trip_id AS train_no, s.stop_seq, s.dep_s - s.arr_s AS w "
        "FROM trip t JOIN sched s USING (trip_id) "
        "WHERE t.network = ? AND s.arr_s IS NOT NULL AND s.dep_s IS NOT NULL",
        (network,),
    ):
        out[r["train_no"]][r["stop_seq"]] = r["w"]
    return out


def build_tasks(conn: sqlite3.Connection, network: str = NETWORK) -> list[dict]:
    """Vse naloge (voznja, dan, i, j, zamuda_i, zamuda_j)."""
    by_day = _delays_by_day(conn, network)
    stops = _stop_ids(conn, network)
    dwells = _dwells(conn, network)
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
                # Rezerva med i in j: vsota presezkov voznorednih postankov
                # na VSEH vmesnih postajah, tudi tistih, ki jih feed ni
                # porocal -- rezerva obstaja ne glede na to, ali smo jo videli.
                w = dwells.get(train_no, {})
                slack = sum(max(0, v - MIN_DWELL_S)
                            for k, v in w.items() if i < k <= j)     # rezerva
                tasks.append({
                    "train_no": train_no, "day": day,
                    "i": i, "j": j, "horizon": j - i,
                    "d_i": delays[i], "d_j": delays[j],
                    "seg": (si, sj), "slack": slack,
                })
    return tasks


# ---------------------------------------------------------------- modeli
#
# Vsak model dobi ucne naloge (brez ocenjevanega dne) in vrne funkcijo, ki
# napove d_j iz ene naloge. Tako je protokol za vse enak in primerjava postena.


def _bucket(d_i: int) -> int:
    """Razred trenutne zamude. Okrevanje ni enako pri +1 in pri +40 minutah:
    vlak z veliko zamudo del nadoknadi na rezervi v voznem redu, tocen vlak
    pa je nima kaj nadoknaditi. Ena sama mediana to razliko zabrise.

    Delitev je skupna s `stats.delay_bucket`, sicer bi merili en model in
    uporabljali drugega -- razlika, ki je meritev ne bi pokazala.
    """
    return stats.delay_bucket(d_i)


def model_prenos(train_tasks):
    """Referenca: zamuda se ne spremeni."""
    return lambda t: t["d_i"]


def model_vlak(train_tasks):
    """Historicna mediana spremembe pri TEM vlaku, brez pogojevanja."""
    table = defaultdict(list)
    for t in train_tasks:
        table[(t["train_no"], t["i"], t["j"])].append(t["d_j"] - t["d_i"])
    table = _medians(table)

    def predict(t):
        e = table.get((t["train_no"], t["i"], t["j"]))
        if not e or e[1] < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + e[0]
    return predict


def _medians(table: dict) -> dict:
    """Iz {kljuc: [vrednosti]} naredi {kljuc: (mediana, koliko)}.

    Mediano izracunamo ENKRAT ob ucenju, ne ob vsaki napovedi. Pri zeleznici
    je bila razlika nevidna -- seznam po odseku je kratek. Pri mestnem
    avtobusu isti fizicni odsek vozi vec linij, seznam zraste na desettisoce
    in `statistics.median` se je klical enkrat na napoved: `odsek+razred` je
    za en dan porabil 6,5 minute namesto 0,3 sekunde in meritev avtobusov
    sploh ni bilo mogoce pognati. Rezultat je do zadnje decimalke isti.
    """
    return {k: (statistics.median(v), len(v)) for k, v in table.items()}


def model_odsek(train_tasks):
    """Zdruzeno po fizicnem odseku cez vse vlake -- vec vzorcev, manj sluma."""
    table = defaultdict(list)
    for t in train_tasks:
        table[t["seg"]].append(t["d_j"] - t["d_i"])
    table = _medians(table)

    def predict(t):
        e = table.get(t["seg"])
        if not e or e[1] < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + e[0]
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
    table, fallback = _medians(table), _medians(fallback)

    def predict(t):
        b = _bucket(t["d_i"])
        e = table.get((t["seg"], b))
        if not e or e[1] < MIN_SAMPLES:
            e = fallback.get(b)
        if not e or e[1] < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + e[0]
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

    per_train = _medians(per_train)
    per_seg, per_bucket = _medians(per_seg), _medians(per_bucket)
    K = 4.0

    def predict(t):
        b = _bucket(t["d_i"])
        seg = per_seg.get((t["seg"], b)) or per_bucket.get(b)
        base = seg[0] if seg and seg[1] >= MIN_SAMPLES else 0.0
        own = per_train.get((t["train_no"], t["i"], t["j"]))
        if not own:
            return t["d_i"] + base
        w = own[1] / (own[1] + K)
        return t["d_i"] + w * own[0] + (1 - w) * base
    return predict


def model_vlak_razred(train_tasks):
    """SEDANJI model: mediana spremembe pri tem vlaku po razredu zamude.

    Zamisel je fizikalna: postanek s pol minute rezerve v voznem redu vlaku,
    ki zamuja 11 minut, vzame dve minuti, tocnemu pa nic -- ker nima cesa
    nadoknaditi. Mediana cez oba primera opisuje nobenega od njiju.
    """
    razred = defaultdict(list)
    skupno = defaultdict(list)
    for t in train_tasks:
        delta = t["d_j"] - t["d_i"]
        razred[(t["train_no"], t["i"], t["j"], _bucket(t["d_i"]))].append(delta)
        skupno[(t["train_no"], t["i"], t["j"])].append(delta)
    razred, skupno = _medians(razred), _medians(skupno)

    def predict(t):
        e = razred.get((t["train_no"], t["i"], t["j"], _bucket(t["d_i"])))
        if not e or e[1] < MIN_SAMPLES:
            e = skupno.get((t["train_no"], t["i"], t["j"]))
        if not e or e[1] < MIN_SAMPLES:
            return t["d_i"]
        return t["d_i"] + e[0]
    return predict


def model_vlak_premica(train_tasks):
    """Premica d_j = a + b*d_i, prilagojena na zgodovino tega para postankov.

    Sedanji model je poseben primer s trdim b = 1 -- zamudo prestavi za
    konstanto. Kadar postanek zamudo POBRISE (Most na Soci: osem dni od
    devetih konca na 0, ne glede na prihod), je pravi b blizu 0 in konstantni
    premik tega ne zna izraziti.

    b krcimo proti 1 z utezjo n/(n+K): pri treh vzorcih premici ne verjamemo,
    pri dvajsetih ji. Omejitev na [0, 1.5] je fizikalna -- zamuda se na odseku
    ne obrne v prednost in se ne podvoji.
    """
    pari = defaultdict(list)
    for t in train_tasks:
        pari[(t["train_no"], t["i"], t["j"])].append((t["d_i"], t["d_j"]))

    K = 6.0

    def predict(t):
        xy = pari.get((t["train_no"], t["i"], t["j"]))
        if not xy or len(xy) < MIN_SAMPLES:
            return t["d_i"]
        xs = [x for x, _ in xy]
        ys = [y for _, y in xy]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        var = sum((x - mx) ** 2 for x in xs)
        premik = t["d_i"] + statistics.median([y - x for x, y in xy])
        if var == 0:
            return premik
        b = sum((x - mx) * (y - my) for x, y in xy) / var
        b = min(max(b, 0.0), 1.5)
        n = len(xy)
        w = n / (n + K)
        b = w * b + (1 - w) * 1.0
        return (my - b * mx) + b * t["d_i"]
    return predict


def model_fizika(train_tasks):
    """Samo rezerva, brez ucenja: d_j = d_i - min(d_i, rezerva).

    Brez ucenja -- vhod je samo vozni red. Sluzi kot dokaz, da rezerva sploh
    kaj pove; sama zase ne zna napovedati, da zamuda tudi NASTAJA.
    """
    return lambda t: stats._after_slack(t["d_i"], t["slack"])


def model_fizika_mediana(train_tasks):
    """Najprej fizika, nato historicni ostanek -- brez razreda zamude."""
    table = defaultdict(list)
    for t in train_tasks:
        table[(t["train_no"], t["i"], t["j"])].append(
            t["d_j"] - stats._after_slack(t["d_i"], t["slack"]))
    table = _medians(table)

    def predict(t):
        osnova = stats._after_slack(t["d_i"], t["slack"])
        e = table.get((t["train_no"], t["i"], t["j"]))
        if not e or e[1] < MIN_SAMPLES:
            return osnova
        return osnova + e[0]
    return predict


def model_fizika_razred(train_tasks):
    """SEDANJI model: rezerva voznega reda, nato ostanek po razredu zamude.

    Vlak najprej porabi REZERVO -- presezek voznorednega postanka nad
    najkrajsim, ki ga se zmore. To ni statistika, ampak vozni red, in je
    edini vhod v napoved, ki ga poznamo vnaprej. LP 4219 ima na Mostu na Soci
    devet minut postanka in v devetih dneh zajema ni nikoli nadoknadil vec kot
    sedem minut niti stal manj kot dve: +16 -> +9, +11 -> +4, +10 -> +3.
    Konstantna mediana spremembe tega ne more izraziti, ker je okrevanje
    odvisno od tega, koliko zamude sploh je.

    Kar rezerva ne pojasni, popravi mediana ostanka pri tem vlaku na tem
    odseku, locena po razredu trenutne zamude.
    """
    razred = defaultdict(list)
    skupno = defaultdict(list)
    for t in train_tasks:
        o = t["d_j"] - stats._after_slack(t["d_i"], t["slack"])
        razred[(t["train_no"], t["i"], t["j"], _bucket(t["d_i"]))].append(o)
        skupno[(t["train_no"], t["i"], t["j"])].append(o)
    razred, skupno = _medians(razred), _medians(skupno)

    def predict(t):
        osnova = stats._after_slack(t["d_i"], t["slack"])
        e = razred.get((t["train_no"], t["i"], t["j"], _bucket(t["d_i"])))
        if not e or e[1] < MIN_SAMPLES:
            e = skupno.get((t["train_no"], t["i"], t["j"]))
        if not e:
            return osnova
        # Isti dve pravili kot `stats.predict`, sicer bi merili en model in
        # uporabljali drugega. Prag `MIN_SAMPLES` je veljal TUDI za nepogojeno
        # mediano -- tu, ne pa v strezeni kodi; razlika je bila vidna sele v
        # senci (v petih minutah 80,8 % s pragom proti 84,7 % brez).
        return osnova + round(stats._omejen_ostanek(e[0], t["d_i"]))
    return predict


def model_fizika_razred_brez_meje(train_tasks):
    """Kar je streznik delal do 2. 9. 2026: brez praga in brez meje ostanka.

    Obdrzan zato, da se vidi, koliko prispeva sama meja. Backtest ga komaj
    loci od sedanjega, senca pa mocno (MAE 3,59 proti 3,14 min) -- razlika je
    v repu, ki ga zgodovinska naloga s kratkim skokom skoraj ne vsebuje.
    """
    razred = defaultdict(list)
    skupno = defaultdict(list)
    for t in train_tasks:
        o = t["d_j"] - stats._after_slack(t["d_i"], t["slack"])
        razred[(t["train_no"], t["i"], t["j"], _bucket(t["d_i"]))].append(o)
        skupno[(t["train_no"], t["i"], t["j"])].append(o)
    razred, skupno = _medians(razred), _medians(skupno)

    def predict(t):
        osnova = stats._after_slack(t["d_i"], t["slack"])
        e = razred.get((t["train_no"], t["i"], t["j"], _bucket(t["d_i"])))
        if not e or e[1] < MIN_SAMPLES:
            e = skupno.get((t["train_no"], t["i"], t["j"]))
        return osnova + e[0] if e else osnova
    return predict


def model_fizika_razred_prag(train_tasks):
    """Kar je backtest meril PREJ: ostanek sele od treh dni naprej.

    Obdrzan zato, da je razlika merljiva. V potnikovem oknu je slabsi
    (MAE 3,63 proti 3,14 min, v petih minutah 80,8 proti 84,9 %) -- prag
    zavrze prav tiste primere, kjer je zgodovine malo, teh pa je vecina.
    """
    razred = defaultdict(list)
    skupno = defaultdict(list)
    for t in train_tasks:
        o = t["d_j"] - stats._after_slack(t["d_i"], t["slack"])
        razred[(t["train_no"], t["i"], t["j"], _bucket(t["d_i"]))].append(o)
        skupno[(t["train_no"], t["i"], t["j"])].append(o)
    razred, skupno = _medians(razred), _medians(skupno)

    def predict(t):
        osnova = stats._after_slack(t["d_i"], t["slack"])
        e = razred.get((t["train_no"], t["i"], t["j"], _bucket(t["d_i"])))
        if not e or e[1] < MIN_SAMPLES:
            e = skupno.get((t["train_no"], t["i"], t["j"]))
        if not e or e[1] < MIN_SAMPLES:
            return osnova
        return osnova + e[0]
    return predict


MODELS = {
    "prenos": model_prenos,
    "vlak": model_vlak,
    "odsek": model_odsek,
    "odsek+razred": model_odsek_razred,
    "združen": model_zdruzen,
    "vlak+razred": model_vlak_razred,
    "vlak premica": model_vlak_premica,
    "rezerva sama": model_fizika,
    "rezerva+mediana": model_fizika_mediana,
    "rezerva+razred (sedanji)": model_fizika_razred,
    "rezerva+razred, prag 3 dni": model_fizika_razred_prag,
    "rezerva+razred, brez meje": model_fizika_razred_brez_meje,
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


def evaluate(conn: sqlite3.Connection, by_horizon: bool = False,
             network: str = NETWORK) -> dict:
    """Primerja modele z izpuščanjem enega dne."""
    tasks = build_tasks(conn, network)
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
                    "train_no": trip_id, "day": day,
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

    # Nas model na istih nalogah, z izpuscanjem enega dne. Rezervo voznega
    # reda mu je treba dodati posebej -- te naloge jo nimajo.
    dwells = _dwells(conn)
    for t in tasks:
        w = dwells.get(t["train_no"], {})
        t["slack"] = sum(max(0, v - MIN_DWELL_S) for k, v in w.items() if t["i"] < k <= t["j"])
    vse = build_tasks(conn)
    nase, skupaj = {}, {}
    for day in sorted({t["day"] for t in tasks}):
        predict = model_fizika_razred([t for t in vse if t["day"] != day])
        for t in tasks:
            if t["day"] != day:
                continue
            k = (t["train_no"], t["day"], t["i"], t["j"])
            nase[k] = predict(t)
            skupaj[k] = stats._with_operator(nase[k], t["operator"])

    def kljuc(t):
        return (t["train_no"], t["day"], t["i"], t["j"])

    return {
        "tasks": len(tasks),
        "models": {
            "prenos": _score([t["d_i"] - t["d_j"] for t in tasks]),
            "prevoznik": _score([t["operator"] - t["d_j"] for t in tasks]),
            "nas model": _score([nase[kljuc(t)] - t["d_j"] for t in tasks]),
            "nas + prevoznik navzgor": _score([skupaj[kljuc(t)] - t["d_j"] for t in tasks]),
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
