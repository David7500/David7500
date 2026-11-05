"""Načrt in čas: `(:network IS NULL OR x)` proti `x`, razvojna baza mode=ro."""
import os, sqlite3, sys, time
from datetime import date, timedelta
sys.path.insert(0, os.getcwd())
from kajros import api, journey, stats
PATH = sys.argv[1]
c = sqlite3.connect(f"file:{PATH}?mode=ro", uri=True)
c.row_factory = sqlite3.Row
c.execute("PRAGMA query_only=ON")
print("sqlite", sqlite3.sqlite_version, "stat1:", c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='sqlite_stat1'").fetchone()[0])
print("trip po omrezju:", [tuple(r) for r in c.execute("SELECT network, COUNT(*) FROM trip GROUP BY 1")])
dan = c.execute("SELECT MAX(service_date) FROM run").fetchone()[0]
print("dan", dan)

def tek(sql, par, meja=20.0):
    best = None; n = None
    for _ in range(3):
        t0 = time.perf_counter()
        konec = t0 + meja
        c.set_progress_handler(lambda: 1 if time.perf_counter() > konec else 0, 100000)
        try:
            n = len(c.execute(sql, par).fetchall())
        except sqlite3.OperationalError:
            return f">{meja:.0f} s"
        finally:
            c.set_progress_handler(None, 0)
        d = time.perf_counter() - t0
        best = d if best is None else min(best, d)
    return f"{best*1000:.1f} ms, {n} vrstic"

def nacrt(sql, par):
    return " | ".join(r["detail"] for r in c.execute("EXPLAIN QUERY PLAN " + sql, par))[:420]

def primerjaj(ime, sql, stari, novi, par):
    assert stari in sql, stari
    nov = sql.replace(stari, novi)
    print(f"== {ime}: staro {tek(sql, par)} | novo {tek(nov, par)}")
    print("   staro:", nacrt(sql, par))
    print("   novo :", nacrt(nov, par))

for net in ("zeleznica", "avtobus"):
    print("#####", net)
    st = "Ljubljana" if net == "zeleznica" else "Bavarski dvor"
    cilj = "Maribor" if net == "zeleznica" else "Kolodvor"
    primerjaj("_BOARD_SQL", journey._BOARD_SQL, "(:network IS NULL OR t.network = :network)", "t.network = :network",
              {"station": st, "day": dan, "network": net})
    primerjaj("_CONNECTIONS_SQL", stats._CONNECTIONS_SQL, "(:network IS NULL OR t.network = :network)", "t.network = :network",
              {"a": st, "b": cilj, "day": dan, "network": net})
    primerjaj("LAST_STOP", stats.LAST_STOP_SQL + "SELECT t.train_no, l.service_date, l.d FROM last l JOIN trip t ON t.trip_id = l.trip_id",
              "(:network IS NULL OR t.network = :network)", "t.network = :network",
              {"network": net, "since": (date.fromisoformat(dan) - timedelta(days=30)).isoformat()})
    primerjaj("znano_do", "SELECT MAX(s.date) FROM service_day s JOIN trip t ON t.service_id = s.service_id "
              "WHERE (? IS NULL OR t.network = ?) AND (? IS NULL OR t.agency = ?)".replace("?", ":n", 2).replace("?", ":a", 2),
              "(:n IS NULL OR t.network = :n)", "t.network = :n", {"n": net, "a": None})
    primerjaj("last_sched_s", "SELECT MAX(end_s) FROM trip WHERE (:n IS NULL OR network = :n)",
              "(:n IS NULL OR network = :n)", "network = :n", {"n": net})
