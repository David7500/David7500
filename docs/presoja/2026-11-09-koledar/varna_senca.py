# Senca varne napovedi samo na vrsticah po popravku zajema (7. 11. 11.36).
import sqlite3, json, sys
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/opt/kajros")
from kajros import ocena, stats
TZ = ZoneInfo("Europe/Ljubljana")
meja = int(datetime(2026, 11, 7, 11, 36, tzinfo=TZ).timestamp())
c = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
c.row_factory = sqlite3.Row
rows = c.execute(
    "SELECT * FROM napoved WHERE network='zeleznica' AND actual_s IS NOT NULL "
    f"AND ABS(actual_s) <= {stats.MAX_REALNA_ZAMUDA_S} AND made_ts >= ?", (meja,)).fetchall()
na_poti = [r for r in rows if r["from_seq"] is not None]
pred = [r for r in rows if r["from_seq"] is None]
def m(rr, col):
    return ocena._meritve([(r[col], r["actual_s"]) for r in rr if r[col] is not None], "zeleznica")
out = {"vrstic": len(rows), "na_poti": len(na_poti), "pred_odhodom": len(pred),
       "dnevi": sorted({r["service_date"] for r in rows})}
# Isti vzorec za vse: samo vrstice, kjer imajo vrednost nasa, varna in prenos.
par = [r for r in na_poti if r["varna_s"] is not None and r["ours_s"] is not None and r["carry_s"] is not None]
out["na_poti_parno_n"] = len(par)
for col in ("ours_s", "varna_s", "carry_s"):
    out["na_poti_" + col] = m(par, col)
po_dnevu = {}
for d in out["dnevi"]:
    p = [r for r in par if r["service_date"] == d]
    po_dnevu[d] = {col: m(p, col) for col in ("ours_s", "varna_s", "carry_s")}
out["po_dnevu"] = po_dnevu
for col in ("ours_s", "varna_s"):
    out["pred_" + col] = m(pred, col)
print(json.dumps(out, ensure_ascii=False, indent=1))
