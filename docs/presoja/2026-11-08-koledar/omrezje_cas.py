"""Vzorec omrežja na arwenovi velikosti (koledar 8. 11. 2026; pregled 5. 11., točka 5).

Kopija produkcije z `VACUUM INTO` (isti indeksi, brez `sqlite_stat1` kot produkcija).
`LAST_STOP_SQL` (nočni `network_stats` in `breakdowns`, 90 dni) in `_LIVE_SQL`
(zemljevid: današnji dan in včerajšnji ponoči) s tremi zapisi omrežja:
zdaj `(:network IS NULL OR t.network = :network)`, golo `t.network = :network`
in `+t.network = :network`. Najprej EXPLAIN QUERY PLAN, nato čas z mejo in
primerjava vrstic z zdajšnjim zapisom.

  cd /opt/kajros && .venv/bin/python -I omrezje_cas.py /var/tmp/kajros-omrezje.sqlite [MEJA_S]

Meri kodo pred spremembo (ab16f36, `LAST_STOP_SQL` je bil en niz); izid v
`omrezje.md`.
"""
import sqlite3
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, "/opt/kajros")
from kajros import api, stats  # noqa: E402

POT = sys.argv[1]
MEJA = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
c = sqlite3.connect(f"file:{POT}?mode=ro", uri=True)
c.execute("PRAGMA query_only=ON")
print("sqlite", sqlite3.sqlite_version, "| sqlite_stat1:",
      c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='sqlite_stat1'").fetchone()[0])
print("trip po omrežju:", c.execute("SELECT network, COUNT(*) FROM trip GROUP BY 1").fetchall())
print("run vrstic:", c.execute("SELECT MAX(rowid) FROM run").fetchone()[0], flush=True)


def nacrt(sql, par):
    return " | ".join(r[3] for r in c.execute("EXPLAIN QUERY PLAN " + sql, par))


def tek(sql, par, krat):
    best, rows = None, None
    for _ in range(krat):
        t0 = time.perf_counter()
        konec = t0 + MEJA
        c.set_progress_handler(lambda: 1 if time.perf_counter() > konec else 0, 100000)
        try:
            rows = c.execute(sql, par).fetchall()
        except sqlite3.OperationalError:
            return None, f"> {MEJA:.0f} s"
        finally:
            c.set_progress_handler(None, 0)
        d = time.perf_counter() - t0
        best = d if best is None else min(best, d)
    return sorted(rows, key=repr), f"{best * 1000:.1f} ms, {len(rows)} vrstic"


def primerjaj(ime, sql, staro, par, krat):
    assert staro in sql, staro
    pred = staro.split(" OR ")[1].split("network")[0]  # "t." ali "tn."
    variante = {"zdaj": sql,
                "golo": sql.replace(staro, f"{pred}network = :network"),
                "plus": sql.replace(staro, f"+{pred}network = :network")}
    print(f"== {ime}")
    for k, s in variante.items():
        print(f"   načrt {k}: {nacrt(s, par)[:600]}", flush=True)
    ref = None
    for k, s in variante.items():
        rows, cas = tek(s, par, krat)
        if k == "zdaj":
            ref = rows
        enako = "" if k == "zdaj" or rows is None or ref is None else (
            " | vrstice enake" if rows == ref else " | VRSTICE RAZLIČNE")
        print(f"   {k}: {cas}{enako}", flush=True)


danes = date(2026, 11, 8)
since = (danes - timedelta(days=90)).isoformat()
for net in ("zeleznica", "avtobus"):
    print("#####", net, flush=True)
    primerjaj("LAST_STOP_SQL + network_stats, 90 dni",
              stats.LAST_STOP_SQL + "SELECT t.train_no, l.service_date, l.d "
              "FROM last l JOIN trip t USING (trip_id)",
              "(:network IS NULL OR t.network = :network)",
              {"network": net, "since": since}, 2)
    # Delavnik (petek 6. 11.) ob konici in popoldne, nato včerajšnji dan ponoči.
    for dan, ura, nocni in (("2026-11-06", 8, 0), ("2026-11-06", 17, 0), ("2026-11-07", 24.5, 1)):
        par = {"day": dan, "now_s": int(ura * 3600), "grace": api._LIVE_GRACE_S,
               "network": net, "polnoc": stats.polnoc(dan), "overnight_only": nocni,
               "sveze_porocilo": stats.SVEZE_POROCILO_S, "max_delay": api.MAX_LIVE_DELAY_S}
        primerjaj(f"_LIVE_SQL {dan} ob {ura} h, overnight_only={nocni}", api._LIVE_SQL,
                  "(:network IS NULL OR tn.network = :network)", par, 3)
