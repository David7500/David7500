"""Senčno merjenje napovedi — iz oči potnika.

Backtest meri model na zgodovini in z izpuščanjem enega dne. To je pošteno do
modela, ni pa pošteno do **prikaza**: potnik ne vpraša „kakšna bo zamuda na
postanku j, če vem zamudo na i“, ampak pogleda v aplikacijo **preden gre od
doma** in prebere eno številko. Vprašanje je torej:

    Kar je aplikacija pokazala 25 minut pred vlakom (15 pred avtobusom),
    kako daleč je bilo od tega, kar se je zgodilo?

Zato ta modul ob strežniku teče kot senca: vsakih nekaj minut posname, kaj bi
prikaz **ta hip** povedal za postanke, ki so v potnikovem oknu, in shrani tri
številke — našo oceno, prevoznikovo in prenos trenutne zamude (referenca, ki
jo mora vsak model premagati). Ko vozilo tisti postanek res prevozi, se v isto
vrstico dopiše resnica.

Trije modeli v isti vrstici so bistvo: primerjava je **parna**. Kdor meri vsak
model na svojem vzorcu, meri tudi razliko med vzorci.

Kar ta zapis namenoma **ni**:

* ni model in ne vpliva na prikaz — samo bere;
* ne meri voženj, ki se še niso začele. Takrat naše ocene ni (nimamo trenutne
  zamude) in tudi prevoznikova je praviloma ničla. Koliko je takih, se šteje
  posebej (`brez_meritve`), ker je to samo po sebi ugotovitev: to je okno,
  v katerem potniku ne znamo povedati ničesar.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, stats

TZ = ZoneInfo(config.TIMEZONE)

#: Koliko pred voznorednim odhodom potnik pogleda. Vlak je dlje od doma in
#: se ga ne lovi tekoc; mestni avtobus se lovi. Vrednosti sta dogovor, ne
#: meritev -- zato se v vsako vrstico zapise TUDI dejanski horizont
#: (`horizon_s`), da se da analizirati po njem in ta dogovor kdaj popraviti.
HORIZONT_S = {"zeleznica": 25 * 60, "avtobus": 15 * 60}

#: Kako sirok pas okoli horizonta se se steje. Postanek pride v okno enkrat
#: (kljuc tabele je (voznja, dan, postanek)), zato je prvi posnetek tisti, ki
#: obvelja -- pas mora biti vsaj tako sirok kot razmik med obhodi, sicer
#: postanek okno preskoci.
PAS_S = 240

#: Vrstice brez resnice po tem casu ne bodo nikoli resene: vozilo je izginilo
#: iz feeda ali pa postanka ni nikoli prevozilo.
ZASTARA_S = 36 * 3600


SHEMA = """
CREATE TABLE IF NOT EXISTS napoved (
    trip_id      TEXT NOT NULL,
    service_date TEXT NOT NULL,
    stop_seq     INTEGER NOT NULL,
    network      TEXT NOT NULL,
    made_ts      INTEGER NOT NULL,   -- kdaj je bil posnetek
    horizon_s    INTEGER NOT NULL,   -- koliko pred voznorednim casom
    current_s    INTEGER,            -- zamuda ob pogledu (zadnji izmerjeni postanek)
    from_seq     INTEGER,            -- kje je bilo vozilo takrat
    ours_s       INTEGER,            -- kar bi pokazal prikaz
    ours_own_s   INTEGER,            -- nasa vrednost brez pravila "prevoznik ve vec"
    ours_samples INTEGER,            -- na koliko dneh zgodovine stoji
    operator_s   INTEGER,            -- kar je takrat trdil feed za ta postanek
    carry_s      INTEGER,            -- referenca: prenos trenutne zamude
    actual_s     INTEGER,            -- resnica, dopisana kasneje
    resolved_ts  INTEGER,
    PRIMARY KEY (trip_id, service_date, stop_seq)
);
CREATE INDEX IF NOT EXISTS napoved_nerazrezena
    ON napoved(service_date) WHERE actual_s IS NULL;
"""


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SHEMA)
    conn.commit()


# ---------------------------------------------------------------- posnetek

def _dnevi(now: datetime) -> list[tuple[str, int]]:
    """Obratovalni dnevi, ki tecejo zdaj, s sekundami od svoje polnoci.

    Voznja, ki se je zacela vceraj ob 23:40, ima ob 00:20 `sched` vrednosti
    cez 86 400 -- zato vceraj z zamikom enega dne, ne samo danes.
    """
    s = now.hour * 3600 + now.minute * 60 + now.second
    vceraj = (now.date() - timedelta(days=1)).isoformat()
    return [(now.date().isoformat(), s), (vceraj, s + 86400)]


# Kandidati so vse voznje, ki bi se PO VOZNEM REDU zdaj vozile -- ne samo
# tiste z meritvijo. Razlika je sama po sebi ugotovitev: voznja brez izmerjenega
# postanka je voznja, o kateri potniku ne znamo povedati nicesar, in prav
# pogostost tega je stvar, ki jo hocemo videti (`brez_meritve`).
_KANDIDATI_SQL = """
SELECT t.trip_id, t.train_no, t.network
FROM trip t
JOIN service_day d ON d.service_id = t.service_id AND d.date = :day
WHERE t.start_s <= :now_s
  AND t.end_s >= :now_s - :grace
"""

# Cel stavek enega sloga: sqlite ob mesanju `?` in `:ime` veze po vrstnem
# redu pojavitve in tiho vrne napacne vrstice.
_TARCE_SQL = """
SELECT s.trip_id, s.stop_seq, COALESCE(s.dep_s, s.arr_s) AS t_s
FROM sched s
WHERE s.trip_id IN (%s)
  AND COALESCE(s.dep_s, s.arr_s) BETWEEN ? AND ?
"""


def _v_vzorcu(trip_id: str, network: str) -> bool:
    """Ali to vožnjo sploh spremljamo.

    Vsak avtobusni postanek bi bil ~135 000 vrstic na dan; vzorec vsake pete
    vožnje jih da 27 000 in mediana se na tem ne premakne. Vzorči se po
    `trip_id` in ne po postanku: vožnja mora biti cela ali nobena, sicer se
    razrez po zamudi meri na kosih poti.
    """
    n = config.OCENA_BUS_VZOREC
    if network != "avtobus" or n <= 1:
        return True
    # Vgrajeni `hash` je med procesi nakljucno solen (PYTHONHASHSEED), zato bi
    # se vzorec ob vsakem zagonu zamenjal -- in vzorec, ki se spreminja, ni
    # vzorec. Vsota bajtov je stabilna in za to dovolj.
    return sum(trip_id.encode()) % n == 0


def snapshot(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    """Posname, kaj bi prikaz povedal potniku, ki gleda ta hip.

    Vrne stevce, ne vrstic -- zapisuje v `napoved`.
    """
    now = now or datetime.now(TZ)
    made_ts = int(now.timestamp())
    zapisano = brez_meritve = 0
    pogledanih = 0

    for day, now_s in _dnevi(now):
        kandidati = conn.execute(_KANDIDATI_SQL, {
            "day": day, "now_s": now_s, "grace": 3 * 3600,
        }).fetchall()
        if not kandidati:
            continue
        po_id = {r["trip_id"]: r for r in kandidati}
        lm = stats.last_measured(conn, day, list(po_id), now_s)

        # Postanki v potnikovem oknu. Okno je po omrezju razlicno, zato dve
        # poizvedbi -- ali ena, kadar je v bazi samo eno omrezje.
        for network, h in HORIZONT_S.items():
            ids = [tid for tid, r in po_id.items()
                   if r["network"] == network and tid in lm and _v_vzorcu(tid, network)]
            brez_meritve += sum(1 for tid, r in po_id.items()
                                if r["network"] == network and tid not in lm)
            if not ids:
                continue
            sql = _TARCE_SQL % ",".join("?" * len(ids))
            tarce = conn.execute(sql, (*ids, now_s + h - PAS_S, now_s + h)).fetchall()
            if not tarce:
                continue

            po_voznji: dict[str, list[sqlite3.Row]] = {}
            for t in tarce:
                if t["stop_seq"] > lm[t["trip_id"]]["stop_seq"]:
                    po_voznji.setdefault(t["trip_id"], []).append(t)

            for trip_id, seznam in po_voznji.items():
                zadnji = lm[trip_id]
                trenutna = zadnji["delay_s"] or 0
                # Prevoznikova vrednost za te postanke -- kar bi feed rekel,
                # ce bi ga bral naravnost. Za se nedosezen postanek je pogosto
                # sploh ni (drsece okno), in prav to je del ugotovitve.
                seqs = [t["stop_seq"] for t in seznam]
                feed = {r["stop_seq"]: r["d"] for r in conn.execute(
                    "SELECT stop_seq, COALESCE(delay_dep, delay_arr) AS d FROM run "
                    f"WHERE service_date = ? AND trip_id = ? AND stop_seq IN "
                    f"({','.join('?' * len(seqs))})",
                    (day, trip_id, *seqs))}
                # `predict` enkrat na voznjo, ne enkrat na postanek: vrne vse
                # postanke naprej in klic je isti.
                napoved = {x["stop_seq"]: x for x in stats.predict(
                    conn, po_id[trip_id]["train_no"], zadnji["stop_seq"], trenutna,
                    exclude_date=day, service_date=day, trip_id=trip_id)}

                for t in seznam:
                    seq = t["stop_seq"]
                    p = napoved.get(seq)
                    cur = conn.execute(
                        "INSERT OR IGNORE INTO napoved(trip_id, service_date, stop_seq,"
                        " network, made_ts, horizon_s, current_s, from_seq, ours_s,"
                        " ours_own_s, ours_samples, operator_s, carry_s)"
                        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (trip_id, day, seq, network, made_ts, t["t_s"] - now_s,
                         trenutna, zadnji["stop_seq"],
                         p["predicted_delay_s"] if p else None,
                         p["own_delay_s"] if p else None,
                         p["n_samples"] if p else None,
                         feed.get(seq), trenutna))
                    zapisano += cur.rowcount
                    pogledanih += 1

    conn.commit()
    return {"pogledanih": pogledanih, "zapisanih": zapisano,
            "brez_meritve": brez_meritve}


# ---------------------------------------------------------------- resnica

def resolve(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    """Dopiše dejansko zamudo vrsticam, katerih postanek je vozilo prevozilo.

    Meja „prevozil“ je ista kot v prikazu (`stats.last_measured`), ne golo
    „obstaja vrstica v `run`“: feed za še nedosežen postanek objavi vrednost,
    ki ni meritev, in prav ta razlika je tisto, kar tu merimo.
    """
    now = now or datetime.now(TZ)
    resene = 0
    cakajo = 0

    for day, now_s in _dnevi(now):
        vrstice = conn.execute(
            "SELECT trip_id, stop_seq FROM napoved "
            "WHERE service_date = ? AND actual_s IS NULL", (day,)).fetchall()
        if not vrstice:
            continue
        ids = sorted({r["trip_id"] for r in vrstice})
        lm = stats.last_measured(conn, day, ids, now_s)
        prevozeni = [r for r in vrstice
                     if r["trip_id"] in lm and r["stop_seq"] <= lm[r["trip_id"]]["stop_seq"]]
        cakajo += len(vrstice) - len(prevozeni)
        if not prevozeni:
            continue

        po_voznji: dict[str, list[int]] = {}
        for r in prevozeni:
            po_voznji.setdefault(r["trip_id"], []).append(r["stop_seq"])
        ts = int(now.timestamp())
        for trip_id, seqs in po_voznji.items():
            for row in conn.execute(
                    "SELECT stop_seq, COALESCE(delay_dep, delay_arr) AS d FROM run "
                    f"WHERE service_date = ? AND trip_id = ? AND stop_seq IN "
                    f"({','.join('?' * len(seqs))})", (day, trip_id, *seqs)):
                if row["d"] is None:
                    continue
                conn.execute(
                    "UPDATE napoved SET actual_s = ?, resolved_ts = ? "
                    "WHERE trip_id = ? AND service_date = ? AND stop_seq = ?",
                    (row["d"], ts, trip_id, day, row["stop_seq"]))
                resene += 1

    # Vrstice, ki jih ni resil nihce: vozilo je izginilo iz feeda. Brisemo jih,
    # sicer bi jih `resolve` prebiral vsak obhod do konca casa.
    meja = int(now.timestamp()) - ZASTARA_S
    opuscene = conn.execute(
        "DELETE FROM napoved WHERE actual_s IS NULL AND made_ts < ?", (meja,)).rowcount
    conn.commit()
    return {"resenih": resene, "cakajo": cakajo, "opuscenih": opuscene}


def prune(conn: sqlite3.Connection, days: int | None = None) -> int:
    """Pobriše stare vrstice. `run` je zgodovina, ta zapis pa merilo — in
    merilo, staro pol leta, meri model, ki ga ni več."""
    days = days if days is not None else config.OCENA_KEEP_DAYS
    meja = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    n = conn.execute("DELETE FROM napoved WHERE service_date < ?", (meja,)).rowcount
    conn.commit()
    return n


def tick(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    """En obhod: posnemi, kar velja zdaj, in dopiši, kar se je medtem zgodilo."""
    now = now or datetime.now(TZ)
    a = snapshot(conn, now)
    b = resolve(conn, now)
    return {**a, **b}


# ---------------------------------------------------------------- porocilo

def _meritve(vals: list[tuple[int, int]]) -> dict:
    """MAE in deleža v dveh in petih minutah za pare (napoved, resnica)."""
    if not vals:
        return {"n": 0}
    napake = [abs(a - b) for a, b in vals]
    n = len(napake)
    return {
        "n": n,
        "mae_min": round(sum(napake) / n / 60, 2),
        "v2min": round(sum(1 for x in napake if x <= 120) / n * 100, 1),
        "v5min": round(sum(1 for x in napake if x <= 300) / n * 100, 1),
        "podcenjenih": round(sum(1 for a, b in vals if a < b - 300) / n * 100, 1),
        # Predznacena napaka: pove SMER. MAE 3 min iz same podcenjenosti in
        # MAE 3 min okoli nicle sta za potnika dve razlicni stvari.
        "odklon_min": round(sum(a - b for a, b in vals) / n / 60, 2),
    }


def report(conn: sqlite3.Connection, days: int = 30,
           network: str | None = None) -> dict:
    """Kako dobre so bile napovedi, ki jih je potnik res videl.

    `podcenjenih` je delež primerov, ko je napoved kazala **manj** od resnice
    za več kot pet minut. Ta napaka ni simetrična: kdor pride na peron in
    vlaka ni, čaka; kdor pride in je vlak že šel, ga je zamudil.
    """
    od = (datetime.now(TZ).date() - timedelta(days=days)).isoformat()
    vrstice = conn.execute(
        "SELECT * FROM napoved WHERE actual_s IS NOT NULL AND service_date >= ?"
        + (" AND network = ?" if network else ""),
        (od, network) if network else (od,)).fetchall()

    def rez(rows: list[sqlite3.Row]) -> dict:
        # Prevoznik za postanek v potnikovem oknu pogosto nima vrednosti. Ce
        # ga merimo samo tam, kjer jo ima, ga merimo na LAZJEM vzorcu -- in
        # primerjava dveh modelov na dveh vzorcih meri tudi razliko med
        # vzorcema. Zato dve tabeli: vse vrstice (kjer prevoznika ni) in
        # parni izrez, kjer imajo vrednost vsi trije.
        parne = [r for r in rows if r["operator_s"] is not None]
        return {
            "nasa": _meritve([(r["ours_s"], r["actual_s"]) for r in rows
                              if r["ours_s"] is not None]),
            "prevoznik": _meritve([(r["operator_s"], r["actual_s"]) for r in rows
                                   if r["operator_s"] is not None]),
            "prenos": _meritve([(r["carry_s"], r["actual_s"]) for r in rows
                                if r["carry_s"] is not None]),
            # Nasa vrednost BREZ pravila "prevoznik ve vec" (`_with_operator`).
            # Pravilo je izmerjeno na zgodovini; tu se vidi, ali drzi tudi v
            # potnikovem oknu, kjer je horizont krajsi.
            "nasa_brez_prevoznika": _meritve([(r["ours_own_s"], r["actual_s"])
                                              for r in rows if r["ours_own_s"] is not None]),
            # Kolikokrat feed za postanek v potnikovem oknu sploh ni imel
            # vrednosti. Brez tega bi bila prevoznikova stevilka videti boljsa,
            # kot je: merjena bi bila samo tam, kjer je nekaj povedal.
            "prevoznik_molci": round(
                sum(1 for r in rows if r["operator_s"] is None) / len(rows) * 100, 1)
            if rows else None,
            "parno": {
                "nasa": _meritve([(r["ours_s"], r["actual_s"]) for r in parne
                                  if r["ours_s"] is not None]),
                "nasa_brez_prevoznika": _meritve([(r["ours_own_s"], r["actual_s"])
                                                  for r in parne if r["ours_own_s"] is not None]),
                "prevoznik": _meritve([(r["operator_s"], r["actual_s"]) for r in parne]),
                "prenos": _meritve([(r["carry_s"], r["actual_s"]) for r in parne
                                    if r["carry_s"] is not None]),
            },
        }

    izid = {"od": od, "vrstic": len(vrstice), "skupaj": rez(vrstice)}

    po_omrezju = {}
    for net in sorted({r["network"] for r in vrstice}):
        po_omrezju[net] = rez([r for r in vrstice if r["network"] == net])
    izid["po_omrezju"] = po_omrezju

    # Razrez po trenutni zamudi ob pogledu: tam, kjer je vlak ze pozen, se
    # modeli razlikujejo najbolj -- pri tocnem vlaku napove pravilno vsakdo.
    meje = [(0, 120, "0-2 min"), (120, 600, "2-10 min"),
            (600, 1800, "10-30 min"), (1800, 10**9, "nad 30 min")]
    razrezi = {}
    for lo, hi, ime in meje:
        del_ = [r for r in vrstice if lo <= (r["current_s"] or 0) < hi]
        if del_:
            razrezi[ime] = rez(del_)
    izid["po_zamudi"] = razrezi

    cakajo = conn.execute(
        "SELECT COUNT(*) FROM napoved WHERE actual_s IS NULL").fetchone()[0]
    izid["cakajo"] = cakajo
    return izid
