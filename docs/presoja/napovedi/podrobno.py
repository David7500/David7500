import json, sys, glob, os
sys.path.insert(0, os.path.dirname(__file__))
import analiza as A
imenik = sys.argv[1]
trase = {}
import urllib.parse
for f in glob.glob(os.path.join(imenik, "trase", "*.json")):
    trase[urllib.parse.unquote(os.path.basename(f)[:-5])] = json.load(open(f))
# Simulacija popravka in podrobnosti živih
sim = {"voženj z živim": 0, "živih postankov": 0, "za vozilom (argmin)": 0, "voženj prizadetih": 0,
       "prizadetih brez meje": 0, "prizadetih z mejo": 0, "največ_min": 0}
for f in sorted(glob.glob(os.path.join(imenik, "krog*.json"))):
    k = json.load(open(f)); kid = os.path.basename(f)[4:6]
    vpo = {v["trip_id"]: v for v in k["veh"] or [] if v.get("trip_id")}
    for tid, run in k["runs"].items():
        st = [s for s in run["stops"] if (s.get("zamuda") or {}).get("vrsta") == "živo"]
        if not st:
            continue
        sim["voženj z živim"] += 1
        sim["živih postankov"] += len(st)
        zac = min(st, key=lambda s: (s["eta_min"], s["stop_seq"]))["stop_seq"]
        slabi = [s for s in st if s["stop_seq"] < zac]
        if slabi:
            sim["za vozilom (argmin)"] += len(slabi)
            sim["voženj prizadetih"] += 1
            sim["prizadetih brez meje" if run["last_measured_seq"] is None else "prizadetih z mejo"] += 1
            mx = max(s["zamuda"]["min"] - (st[-1]["zamuda"]["min"]) for s in slabi)
            sim["največ_min"] = max(sim["največ_min"], max(s["zamuda"]["min"] for s in slabi))
            if len(sys.argv) > 2:
                print(kid, run["train_no"], tid[37:45], "meja", run["last_measured_seq"], "zac", zac,
                      [(s["stop_seq"], s["eta_min"], s["zamuda"]["min"]) for s in slabi][:4])
print(json.dumps(sim, ensure_ascii=False))
