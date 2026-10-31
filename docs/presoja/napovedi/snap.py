"""Posnetek prikaza produkcije: vse žive vožnje, okno vsake, lege, trase.

Rabi: python snap.py <izhodni_imenik> <krogov> <razmik_s>
Obziren: ~2,7 zahteve/s, skupaj največ MAX_ZAHTEV.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

BASE = "https://kajros.app"
UA = "kajros-presoja/1.0 (pregled napovedi, David)"
PAVZA = 0.37
MAX_ZAHTEV = 2400
st_zahtev = 0


def get(pot):
    global st_zahtev
    if st_zahtev >= MAX_ZAHTEV:
        raise SystemExit("meja zahtev")
    st_zahtev += 1
    time.sleep(PAVZA)
    req = urllib.request.Request(BASE + pot, headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read()), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, None, time.time() - t0
    except Exception as e:  # noqa: BLE001 -- posnetek ne sme pasti
        return -1, str(e), time.time() - t0


def q(s):
    return urllib.parse.quote(s, safe="")


def main():
    out, krogov, razmik = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    os.makedirs(os.path.join(out, "trase"), exist_ok=True)
    for k in range(krogov):
        zac = time.time()
        rnd = {"ts": int(zac), "cas": datetime.now().isoformat(timespec="seconds")}
        for ime, pot in (("live_z", "/api/live?network=zeleznica"),
                         ("live_b", "/api/live?network=avtobus"),
                         ("veh", "/api/vehicles")):
            rnd[ime] = get(pot)[1]
        voznje = {}
        for ime in ("live_z", "live_b", "veh"):
            for x in rnd[ime] or []:
                if x.get("trip_id") and x.get("train_no"):
                    voznje.setdefault(x["trip_id"], (x["train_no"], x.get("service_date")))
        rnd["runs"], rnd["napake"] = {}, {}
        for tid, (no, dan) in voznje.items():
            pot = f"/api/train/{q(no)}/run?trip={q(tid)}"
            if dan:
                pot += f"&date={dan}"
            kod, telo, cas = get(pot)
            if kod == 200:
                telo["_t"] = int(time.time())
                telo["_cas_s"] = round(cas, 2)
                rnd["runs"][tid] = telo
            else:
                rnd["napake"][tid] = [kod, no, telo if kod == -1 else None]
        # Trase avtobusov z lego: samo enkrat na vožnjo.
        for x in rnd["veh"] or []:
            tid = x.get("trip_id")
            if not tid:
                continue
            f = os.path.join(out, "trase", q(tid)[:200] + ".json")
            if os.path.exists(f):
                continue
            kod, telo, _ = get(f"/api/trip/{q(tid)}/shape")
            with open(f, "w") as fh:
                json.dump(telo if kod == 200 else {"napaka": kod}, fh)
        with open(os.path.join(out, f"krog{k:02d}.json"), "w") as fh:
            json.dump(rnd, fh, ensure_ascii=False)
        print(f"krog {k}: {len(voznje)} voženj, {len(rnd['napake'])} napak, "
              f"{time.time() - zac:.0f} s, zahtev {st_zahtev}", flush=True)
        if k < krogov - 1:
            time.sleep(max(0, razmik - (time.time() - zac)))


if __name__ == "__main__":
    main()
