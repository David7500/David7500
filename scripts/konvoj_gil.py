"""Ali niti strežnika zadržujejo zahteve (konvoj GIL), izmerjeno na arwenu.

Strežnik, zajem in niti virov so en proces z enim GIL-om. Zahteva, ki bere
bazo, GIL ob vsakem koraku SQLite spusti in ga za vrnitev čaka do
`switchinterval` (0,5 ms), kadar druga nit računa v čistem Pythonu. Skripta
vsako sekundo pošlje težko (tabla Ljubljana, ~1 450 korakov) in lahko zahtevo
(`/api/svezina`) ter zraven prebere CPE vsake niti iz `/proc`. Rep, ki pade v
sekundo, ko je ena nit porabila skoraj vso sekundo, je konvoj.

    ssh david@192.168.1.46 'python3 - $(systemctl show -p MainPID --value kajros.service) 180' \
        < scripts/konvoj_gil.py

Niti v `/proc` nimajo imen (Python 3.12). Vrstni red id-jev je vrstni red
zagona v `server.lifespan`: obisk, zajem, peroni, zamude SŽ, ovire SŽ, zamude
LPP, NAP, promet, opozorila, vozila; poznejši id-ji so niti zahtev in ogrevanja.
Prva meritev in izid: `docs/MERITVE.md`, 19. 10. 2026.
"""
import os
import statistics
import sys
import time
import urllib.request

pid, trajanje = int(sys.argv[1]), float(sys.argv[2])
HZ = os.sysconf("SC_CLK_TCK")
ZAHTEVE = (("tabla", "http://127.0.0.1:8000/api/departures?station=Ljubljana&network=zeleznica"),
           ("svezina", "http://127.0.0.1:8000/api/svezina"))


def niti() -> dict[int, float]:
    out = {}
    for tid in os.listdir(f"/proc/{pid}/task"):
        try:
            f = open(f"/proc/{pid}/task/{tid}/stat").read().rsplit(")", 1)[1].split()
            out[int(tid)] = (int(f[11]) + int(f[12])) / HZ
        except OSError:
            pass
    return out


zacetek = time.time()
prej = niti()
vzorci = []
while time.time() - zacetek < trajanje:
    t = time.time()
    lat = {}
    for ime, url in ZAHTEVE:
        s = time.perf_counter()
        urllib.request.urlopen(url, timeout=60).read()
        lat[ime] = (time.perf_counter() - s) * 1000
    zdaj = niti()
    vzorci.append((t, lat, {k: zdaj[k] - prej.get(k, 0) for k in zdaj}))
    prej = zdaj
    time.sleep(max(0, 1.0 - (time.time() - t)))

trajalo = vzorci[-1][0] - vzorci[0][0] + 1
print(f"{len(vzorci)} vzorcev v {trajalo:.0f} s")
for ime, _ in ZAHTEVE:
    x = sorted(v[1][ime] for v in vzorci)
    print(f"{ime:8} p50 {statistics.median(x):6.1f} ms  p90 {x[int(len(x) * 0.9)]:6.1f}  "
          f"najdlje {x[-1]:6.1f}")
skupaj: dict[int, float] = {}
for _, _, cpe in vzorci:
    for k, c in cpe.items():
        skupaj[k] = skupaj.get(k, 0) + c
print("niti po CPE:", ", ".join(f"{k} {100 * c / trajalo:.0f} %"
                                for k, c in sorted(skupaj.items(), key=lambda x: -x[1])[:8]))
print("najpočasnejše table in najbolj zaposlena nit v tisti sekundi:")
for t, lat, cpe in sorted(vzorci, key=lambda v: -v[1]["tabla"])[:6]:
    k, c = max(cpe.items(), key=lambda x: x[1])
    print(f"  {time.strftime('%H:%M:%S', time.localtime(t))}  tabla {lat['tabla']:6.1f} ms  "
          f"svezina {lat['svezina']:5.1f} ms  nit {k} {c:.2f} s CPE")
