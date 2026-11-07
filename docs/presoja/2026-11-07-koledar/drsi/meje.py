"""Koliko epizod bi dala vrstica pokritost pri danih mejah. Argumenti: csv N POL TRAJA_S"""
import csv, sys, collections, datetime as dt, zoneinfo
TZ = zoneinfo.ZoneInfo("Europe/Ljubljana")
vrst = [(int(r[0]), r[1], *map(int, r[2:])) for r in csv.reader(open(sys.argv[1]))]
N, POL, TRAJA = int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
VLAKI = "1161"
po = collections.defaultdict(list)
for ts, ag, a, l, z, k in vrst:
    po[ag].append((ts, a, l, z, k))


def razmerji(ag, x):
    a = x[1]
    zam = (x[3] if ag == VLAKI else x[4]) / a
    return (zam,) if ag == VLAKI else (x[2] / a, zam)


izh = {}
for ag, v in po.items():
    rs = [razmerji(ag, x) for x in v if x[1] >= N]
    izh[ag] = tuple(sorted(r[i] for r in rs)[len(rs) // 2] for i in range(len(rs[0])))
f = lambda ts: dt.datetime.fromtimestamp(ts, TZ).strftime("%a %d.%m %H:%M")
print("izhodišča", {ag: tuple(round(x, 2) for x in v) for ag, v in sorted(izh.items())})
skupaj_r = skupaj_o = 0
for ag, v in sorted(po.items()):
    ep, cur = [], None
    for x in v:
        if x[1] < N:
            cur = None  # premalo voženj: pogoj ne velja (tudi sled se ponastavi)
            continue
        slab = any(r < POL * i for r, i in zip(razmerji(ag, x), izh[ag]))
        if slab and cur and x[0] - cur[1] <= 600:
            cur[1] = x[0]
        elif slab:
            cur = [x[0], x[0]]; ep.append(cur)
        else:
            cur = None
    dolge = [e for e in ep if e[1] - e[0] >= TRAJA]
    skupaj_r += len(ep); skupaj_o += len(dolge)
    if ep:
        print(f"{ag:8s} rumena {len(ep):3d}  oranžna {len(dolge)}:",
              "; ".join(f"{f(e[0])} {(e[1]-e[0])//60} min" for e in dolge[:6]))
print("skupaj rumena", skupaj_r, "oranžna", skupaj_o)
