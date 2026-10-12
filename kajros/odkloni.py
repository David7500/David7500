"""Kje vozila ne vozijo po trasi: odkloni iz `iz_lege` (tabela `odklon`) po
odsekih med dvema zaporednima postankoma.

Zakaj: 11. 10. 2026 so Arriva, Nomago in AP MS zgrešili 3 % vmesnih
postankov (Brnik letališče 15 od 17, Koper 7 od 9), ker vozilo tam ne vozi po
trasi -- trasa zavije na postajo, letališče ali v krak, vozilo ne, ali
obratno. Trasa je prevoznikova (GTFS DUJPP), pripeta na OSM (`pripni.py`);
kar vozila res vozijo, se vanjo ne vrne. Ohlapnejše meje prehoda tam dajo
slab čas (mediana 83 s proti 29 s), zato se bo popravljala trasa.

Ta pregled pove, kje je odklon stalen (vsi prevozi odseka, več dni) in kje
občasen: iz prvega naj nastane trasa po legah, drugi ostane. Meja med njima
se določi po nekaj dneh beleženja (docs/MERITVE.md, 11. 10. 2026).
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict

from . import config, deljenje


def po_odsekih(conn: sqlite3.Connection, od_ts: int, do_ts: int,
               prevozniki=None) -> list[dict]:
    """Odseki z vsaj enim odklonom v [od_ts, do_ts): koliko prevozov in koliko
    odklonjenih, najprej najbolj odklonjeni.

    Šteje samo prevoznike, pri katerih zamuda pride iz leg
    (`config.NAP_PREVOZNIKI`): tam `run` pove, do kam je vožnja prišla, in
    odsek je prevožen, kadar ima vožnja meritev na njegovem koncu ali pred in
    za njim. Kadar NAP molči, `run` piše derp.si z napovedmi za vse postanke
    -- takrat je prevozov preveč.
    """
    # Prevoz pred prvim zapisanim odklonom (beleženje od 11. 10. 2026) ni mogel
    # biti zapisan kot odklonjen in bi delež znižal.
    zacetek = conn.execute("SELECT MIN(od_ts) FROM odklon").fetchone()[0]
    if zacetek is None:
        return []
    od_ts = max(od_ts, zacetek)
    prevozniki = sorted(prevozniki or config.NAP_PREVOZNIKI)
    ph = ",".join("?" * len(prevozniki))
    odseki: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"odklonjene": set(), "preskoki": set(), "dnevi": set(), "leg": 0, "odmik_max": 0})
    stop_id: dict[str, dict[int, str]] = {}
    for o in conn.execute(
            f"SELECT o.* FROM odklon o JOIN trip t USING (trip_id) "
            f"WHERE o.od_ts >= ? AND o.od_ts < ? AND t.agency IN ({ph})",
            (od_ts, do_ts, *prevozniki)).fetchall():
        v = deljenje.voznja(conn, o["trip_id"])
        if v is None:
            continue
        if o["trip_id"] not in stop_id:
            stop_id[o["trip_id"]] = dict(conn.execute(
                "SELECT stop_seq, stop_id FROM sched WHERE trip_id = ?", (o["trip_id"],)).fetchall())
        sid, post = stop_id[o["trip_id"]], v.postanki
        # Od zadnjega postanka pred sidrom na trasi do prvega za drugim sidrom.
        i = max((k for k, p in enumerate(post) if p["along"] <= o["along_pred"]), default=0)
        j = (len(post) - 1 if o["along_za"] is None else
             min((k for k, p in enumerate(post) if p["along"] >= o["along_za"]), default=len(post) - 1))
        for k in range(i, min(max(i + 1, j), len(post) - 1)):
            d = odseki[(sid[post[k]["stop_seq"]], sid[post[k + 1]["stop_seq"]])]
            d["odklonjene"].add((o["trip_id"], o["service_date"]))
            if o["vrsta"] == "preskok":
                d["preskoki"].add((o["trip_id"], o["service_date"]))
            d["dnevi"].add(o["service_date"])
            d["leg"] += o["leg"]
            d["odmik_max"] = max(d["odmik_max"], o["odmik_max"])
    if not odseki:
        return []
    pari = list(odseki)
    prevozi: dict[tuple[str, str], set] = defaultdict(set)
    for a, b, trip_id, dan in conn.execute(
            f"WITH odsek(a, b) AS (VALUES {','.join('(?, ?)' for _ in pari)}), "
            "pokritost AS ("
            "  SELECT r.trip_id, r.service_date, MIN(r.stop_seq) AS lo, MAX(r.stop_seq) AS hi "
            "  FROM run r JOIN trip t USING (trip_id) "
            f"  WHERE r.feed_ts >= ? AND r.feed_ts < ? AND t.agency IN ({ph}) "
            "  GROUP BY r.trip_id, r.service_date), "
            "zaporedni AS ("
            "  SELECT s.trip_id, s.stop_id AS a, LEAD(s.stop_id) OVER w AS b, "
            "         LEAD(s.stop_seq) OVER w AS b_seq "
            "  FROM sched s WHERE s.trip_id IN (SELECT trip_id FROM pokritost) "
            "  WINDOW w AS (PARTITION BY s.trip_id ORDER BY s.stop_seq)) "
            "SELECT z.a, z.b, p.trip_id, p.service_date FROM zaporedni z "
            "JOIN odsek USING (a, b) JOIN pokritost p USING (trip_id) "
            "WHERE p.lo <= z.b_seq AND p.hi >= z.b_seq",
            (*(x for par in pari for x in par), od_ts, do_ts, *prevozniki)):
        prevozi[(a, b)].add((trip_id, dan))
    imena = dict(conn.execute(
        f"SELECT stop_id, name FROM station WHERE stop_id IN ({','.join('?' * (2 * len(pari)))})",
        [x for par in pari for x in par]).fetchall())
    out = []
    for (a, b), d in odseki.items():
        n = len(prevozi[(a, b)] | d["odklonjene"])
        out.append({"od": a, "do": b, "od_ime": imena.get(a, a), "do_ime": imena.get(b, b),
                    "prevozov": n, "odklonjenih": len(d["odklonjene"]), "preskokov": len(d["preskoki"]),
                    "delez": len(d["odklonjene"]) / n, "dni": len(d["dnevi"]),
                    "leg": d["leg"], "odmik_max": d["odmik_max"]})
    out.sort(key=lambda r: (-r["delez"], -r["odklonjenih"]))
    return out
