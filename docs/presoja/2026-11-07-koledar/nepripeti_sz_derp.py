import json, sqlite3, collections, datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Ljubljana")
k = sqlite3.connect("file:/var/lib/kajros/kajros.sqlite?mode=ro", uri=True)
E = [e for e in json.load(open("/var/tmp/koledar-nepripeti.json")) if e["postaja"] == "Slivnica" and e["trajanje"]]
c = collections.Counter(); prim = []
for e in E:
    ts = datetime.datetime.strptime("2026-" + e["cas"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ).timestamp()
    dan = datetime.datetime.fromtimestamp(ts, TZ).date().isoformat()
    for t in dict.fromkeys(e["kand"]):
        p = k.execute("SELECT x.stop_seq, s.name, x.dep_s FROM sched x JOIN station s USING(stop_id) WHERE trip_id=? ORDER BY stop_seq", (t,)).fetchall()
        i = next((i for i, r in enumerate(p) if r[1] == "Spodnja Slivnica"), None)
        if not i: continue
        seq = p[i-1][0]
        rows = k.execute("SELECT delay_arr, delay_dep, feed_ts, observed_at FROM obs WHERE trip_id=? AND service_date=? AND stop_seq=? ORDER BY observed_at", (t, dan, seq)).fetchall()
        v_ep = [r for r in rows if ts <= r[3] <= ts + e["trajanje"] + 30]
        pred = [r for r in rows if r[3] < ts]
        c["epizod"] += 1
        c["obs_v_epizodi"] += bool(v_ep)
        c["obs_pred_epizodo"] += bool(pred)
        c["trajanje>120"] += e["trajanje"] > 120
        c["trajanje>150_brez_obs"] += e["trajanje"] > 150 and not v_ep
        if v_ep:
            m = (e["zamuda"] or 0) * 60
            c["obs_v_ep=zemljevid"] += abs((v_ep[-1][1] if v_ep[-1][1] is not None else v_ep[-1][0]) - m) < 60
            # feed_ts derp proti uri voznega reda + zamuda (napoved_vlaka)
            c["obs_v_ep_feedts_za_observed_s_med"] = 0
            prim.append((e["n"], e["cas"], e["zamuda"], [(r[0], r[1], r[3]-r[2]) for r in v_ep][:3]))
        if pred and not v_ep:
            last = pred[-1]; m = (e["zamuda"] or 0) * 60
            c["brez_v_ep_zadnja_obs_pred=zemljevid"] += abs((last[1] if last[1] is not None else last[0]) - m) < 60
print(dict(c))
for x in prim[:6]: print(x)
