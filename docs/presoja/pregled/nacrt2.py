"""_LIVE_SQL in več postaj, staro proti novo; razvojna baza mode=ro."""
import os, sqlite3, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.getcwd())
from kajros import api, journey, stats
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
c.row_factory = sqlite3.Row
c.execute("PRAGMA query_only=ON")
dan = c.execute("SELECT MAX(service_date) FROM run").fetchone()[0]
now = datetime.now(ZoneInfo("Europe/Ljubljana"))
def tek(sql, par, meja=25.0):
    best, n = None, None
    for _ in range(3):
        t0 = time.perf_counter(); konec = t0 + meja
        c.set_progress_handler(lambda: 1 if time.perf_counter() > konec else 0, 100000)
        try:
            n = len(c.execute(sql, par).fetchall())
        except sqlite3.OperationalError:
            return f">{meja:.0f} s"
        finally:
            c.set_progress_handler(None, 0)
        d = time.perf_counter() - t0
        best = d if best is None else min(best, d)
    return f"{best*1000:.1f} ms/{n}"
S = "(:network IS NULL OR t.network = :network)"
for net, postaje in (("avtobus", ("Bavarski dvor", "Kolodvor", "Ljubljana AP", "Celje AP", "Maribor AP", "Koper AP")),
                     ("zeleznica", ("Ljubljana", "Maribor", "Zidani Most"))):
    for p in postaje:
        par = {"station": p, "day": dan, "network": net}
        print(net, p, "staro", tek(journey._BOARD_SQL, par), "| novo", tek(journey._BOARD_SQL.replace(S, "t.network = :network"), par),
              "| +t", tek(journey._BOARD_SQL.replace(S, "+t.network = :network"), par))
S2 = "(:network IS NULL OR tn.network = :network)"
for net in ("zeleznica", "avtobus"):
    for ure in (now.hour, 8):
        ns = ure*3600 + now.minute*60
        par = {"day": dan, "now_s": ns, "grace": api._LIVE_GRACE_S, "network": net, "polnoc": stats.polnoc(dan),
               "overnight_only": 0, "sveze_porocilo": stats.SVEZE_POROCILO_S, "max_delay": api.MAX_LIVE_DELAY_S}
        print("_LIVE_SQL", net, ure, "h staro", tek(api._LIVE_SQL, par), "| novo", tek(api._LIVE_SQL.replace(S2, "tn.network = :network"), par))
