"""Sinhroni krog: lega vozila in okno ISTEGA trenutka, zemljevid proti oknu, tabla proti oknu.

Rabi: python sync.py <izhod.json>
"""
import json
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import snap  # noqa: E402

get, q = snap.get, snap.q


def run_pot(no, tid, dan):
    p = f"/api/train/{q(no)}/run?trip={q(tid)}"
    return p + (f"&date={dan}" if dan else "")


def main():
    out = {"ts": int(time.time()), "pari": [], "zemljevid": [], "table": []}
    _, veh, _ = get("/api/vehicles")
    veh = veh or []
    # (c,d,e,h) lega in okno v istem trenutku
    for v in veh:
        tid = v.get("trip_id")
        if not tid or v.get("network") != "avtobus":
            continue
        k1, vv, _ = get(f"/api/vehicles?trip={q(tid)}")
        t1 = time.time()
        k2, run, _ = get(run_pot(v["train_no"], tid, v.get("service_date")))
        par = {"t_veh": t1, "t_run": time.time(), "veh": vv, "run": run if k2 == 200 else None}
        # Dolg odsek za mejo: kaj okno pokaže za naslednji postanek (naša ocena).
        if k2 == 200 and run.get("last_measured_seq") is not None:
            st = run["stops"]
            i = next(i for i, s in enumerate(st) if s["stop_seq"] == run["last_measured_seq"])
            if i + 1 < len(st) and (st[i].get("zamuda") or {}).get("s") is not None:
                a = st[i].get("sched_dep") or st[i].get("sched_arr")
                b = st[i + 1].get("sched_arr") or st[i + 1].get("sched_dep")
                from datetime import datetime as _d
                if a and b and (_d.fromisoformat(b) - _d.fromisoformat(a)).total_seconds() >= 900:
                    kp, pr, _ = get(f"/api/train/{q(run['train_no'])}/predict?stop_seq={st[i]['stop_seq']}"
                                    f"&delay_s={st[i]['zamuda']['s']}&exclude_date={run['service_date']}"
                                    f"&trip={q(tid)}")
                    par["predict"] = pr if kp == 200 else None
        out["pari"].append(par)
    # (h) /api/live proti oknu: takoj za seznamom deset oken, trikrat
    for omr in ("avtobus", "zeleznica", "avtobus"):
        _, live, _ = get(f"/api/live?network={omr}")
        t0 = time.time()
        for x in (live or [])[:10]:
            k, run, _ = get(run_pot(x["train_no"], x["trip_id"], x.get("service_date")))
            out["zemljevid"].append({"t_live": t0, "t_run": time.time(), "live": x,
                                     "run": run if k == 200 else None})
    # (i) tabla postaje proti oknu: naslednji postanek za mejo
    izbrane = [p for p in out["pari"] if p["run"]][:30] + [
        z for z in out["zemljevid"] if z["run"] and z["live"].get("network") == "zeleznica"][:10]
    for p in izbrane:
        run = p["run"]
        meja = run.get("last_measured_seq")
        nasl = next((s for s in run["stops"] if meja is None or s["stop_seq"] > meja), None)
        if not nasl:
            continue
        omr = run.get("network") or "zeleznica"
        k, tabla, _ = get(f"/api/departures?station={q(nasl['name'])}&network={omr}&window=120")
        t0 = time.time()
        k2, run2, _ = get(run_pot(run["train_no"], run["trip_id"], run["service_date"]))
        out["table"].append({"t": t0, "postanek": nasl["name"], "seq": nasl["stop_seq"],
                             "trip_id": run["trip_id"], "tabla": tabla if k == 200 else None,
                             "run": run2 if k2 == 200 else None})
    json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False)
    print("zahtev", snap.st_zahtev, "parov", len(out["pari"]), "tabel", len(out["table"]))


if __name__ == "__main__":
    main()
