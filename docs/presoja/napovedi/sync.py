"""Sinhroni krog: lega vozila in okno ISTEGA trenutka, zemljevid proti oknu, tabla proti oknu.

Rabi: python sync.py <izhod.json>
"""
import json
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import snap  # noqa: E402

get, q = snap.get, snap.q


def run_pot(no, tid, dan):
    p = f"/api/train/{q(no)}/run?trip={q(tid)}"
    return p + (f"&date={dan}" if dan else "")


def napoved_okna(run):
    """Napoved, ki jo okno kaže za postanke za mejo: ista zahteva kot
    `common.fetchRunAndForecast` (od meje ali prvega postanka z zamudo)."""
    st = run["stops"]
    meja = run.get("last_measured_seq")
    cur = next((s for s in st if s["stop_seq"] == meja), None) if meja is not None else None

    def zam(s):
        return s["zamuda"]["s"] if s.get("zamuda") else (
            s["delay_dep"] if s.get("delay_dep") is not None else s.get("delay_arr"))
    base = cur or next((s for s in st if zam(s) is not None), None)
    if not base or base["stop_seq"] >= st[-1]["stop_seq"]:
        return None
    d = run["trenutna"]["zamuda"]["s"] if cur and run.get("trenutna") else zam(base)
    if d is None:
        return None
    k, pr, _ = get(f"/api/train/{q(run['train_no'])}/predict?stop_seq={base['stop_seq']}"
                   f"&delay_s={int(d)}&exclude_date={run['service_date']}&trip={q(run['trip_id'])}")
    return pr if k == 200 else None


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
    # (i) tabla postaje proti oknu: naslednji postanek za mejo. Postanek izbere
    # SVEŽE okno: okno para je do 12 min staro in 2. 11. je vozilo 26 od 40
    # izbranih postankov že prevozilo (tabla jih pravilno ni imela). Izbor
    # razpršen čez vse pare, ne prvih 30 (same mestne linije 1–14).
    pari_z = [p for p in out["pari"] if p["run"]]
    izbrane = pari_z[::max(1, len(pari_z) // 30)][:30] + [
        z for z in out["zemljevid"] if z["run"] and z["live"].get("network") == "zeleznica"][:10]
    for p in izbrane:
        run = p["run"]
        pot = run_pot(run["train_no"], run["trip_id"], run["service_date"])
        k0, run0, _ = get(pot)
        if k0 != 200:
            continue
        meja = run0.get("last_measured_seq")
        nasl = next((s for s in run0["stops"] if meja is None or s["stop_seq"] > meja), None)
        if not nasl:
            continue
        omr = run0.get("network") or "zeleznica"
        k, tabla, _ = get(f"/api/departures?station={q(nasl['name'])}&network={omr}&window=120")
        t0 = time.time()
        k2, run2, _ = get(pot)
        out["table"].append({"t": t0, "postanek": nasl["name"], "seq": nasl["stop_seq"],
                             "trip_id": run["trip_id"], "tabla": tabla if k == 200 else None,
                             "run": run2 if k2 == 200 else None,
                             "predict": napoved_okna(run2) if k2 == 200 else None})
    json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False)
    # Trase za preverbe z lego (sync_analiza.py, drugi argument = imenik izhoda): po
    # vožnji enkrat, za okni, da ne zamaknejo para. Brez njih (d) in (c) ne tečeta.
    trase = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "trase")
    os.makedirs(trase, exist_ok=True)
    for p in out["pari"]:
        tid = (p["run"] or {}).get("trip_id")
        f = os.path.join(trase, q(tid)[:200] + ".json") if tid else None
        if f and not os.path.exists(f):
            k, telo, _ = get(f"/api/trip/{q(tid)}/shape")
            json.dump(telo if k == 200 else {"napaka": k}, open(f, "w"))
    print("zahtev", snap.st_zahtev, "parov", len(out["pari"]), "tabel", len(out["table"]))


if __name__ == "__main__":
    main()
