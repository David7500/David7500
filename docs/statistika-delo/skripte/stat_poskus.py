import sys, time, json
sys.path.insert(0, "/var/tmp/kajros-dev")
from kajros import db, stats, statistika
conn = db.connect(); db.init(conn)
t = time.time(); dnevi = statistika.dopolni(conn); print("dopolni", len(dnevi), "dni", round(time.time() - t, 1), "s")
for kind in ("stat_napovedi", "stat_prevozniki"):
    for net in ("zeleznica", "avtobus"):
        t = time.time(); p = stats.summary_build(conn, kind, net, 90)
        print(kind, net, round(time.time() - t, 1), "s", "runs", p["runs"], "through", p["through"], "bajtov", len(json.dumps(p)))
n = stats.summary_get(conn, "stat_napovedi", "zeleznica")
print("vlaki na poti", {m: (x["n"], x["mae_min"], x["v1min"]) for m, x in n["skupaj"]["na_poti"]["vse"].items()})
for net in ("zeleznica", "avtobus"):
    p = stats.summary_get(conn, "stat_prevozniki", net)
    for x in p["prevozniki"]:
        c = x["cilj"]
        print(f'{x["ime"]:18s} {x["skupina"]:10s} pokr {x["pokritost"]} lega {x["z_lego"]} n {c.get("n")} v5 {c.get("v5min")} med {c.get("mediana_min")} nad15 {c.get("nad15")} prej2 {x["prezgodaj"]["prej2"]} nap {x["napoved"]["vse"]["nasa"].get("mae_min")}/{x["napoved"]["parno"]["prevoznik"].get("mae_min")} lest {(x.get("lestvica") or {}).get("vseh")}')
