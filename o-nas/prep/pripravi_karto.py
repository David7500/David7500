"""Iz izvoza s strežnika in javnih virov naredi datoteke za Pogl. 3 v
kajros/static/o-nas/:

  relief.png          višine Slovenije (R,G = 16 bitov, B = maska države)
  karta.json          opis: razsežnosti, imena, odmiki v karta-podatki.png
  karta-podatki.png   omrežje, eno jutro voženj, zamude IC 351 po dnevih
                      (int16 v R in G; PNG, ker ga strežnik streže povsod)

Vhodi (niso v gitu, v tej mapi): karta-surovo.json.gz iz izvoz_karte.py,
dem/t_X_Y.png (Terrain Tiles, Mapzen/AWS, terrarium z9), slovenija.json
(meja iz Natural Earth).
"""
import gzip
import io
import json
import math
import statistics
import struct
from pathlib import Path

from PIL import Image

TU = Path(__file__).parent
IZHOD = TU.parent.parent / 'kajros' / 'static' / 'o-nas'
d = json.load(gzip.open(TU / 'karta-surovo.json.gz'))
LAT0, LON0 = d['lat0'], d['lon0']
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0


def P(lat, lon):
    return ((lon - LON0) * KX, (LAT0 - lat) * KY)


# ---- relief: mozaik terrarium z9, preslikan v lokalne metre ----
X0, X1, Z0, Z1 = -128000, 152000, -96000, 90000
KORAK = 500
NX, NZ = (X1 - X0) // KORAK, (Z1 - Z0) // KORAK
mozaik = {}
for p in (TU / 'dem').glob('t_*.png'):
    _, x, y = p.stem.split('_')
    mozaik[(int(x), int(y))] = Image.open(p).convert('RGB').load()
Z = 9
n = 2 ** Z


def visina(lat, lon):
    fx = (lon + 180) / 360 * n
    lr = math.radians(lat)
    fy = (1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n
    tx, ty = int(fx), int(fy)
    px = min(255, int((fx - tx) * 256)); py = min(255, int((fy - ty) * 256))
    t = mozaik.get((tx, ty))
    if t is None:
        return 0.0
    r, g, b = t[px, py]
    return max(0.0, (r * 256 + g + b / 256) - 32768)


# meja Slovenije v lokalnih metrih (za masko in obris)
meja = json.load(open(TU / 'slovenija.json'))
obroc = meja['coordinates'][0] if meja['type'] == 'Polygon' else max(meja['coordinates'], key=lambda p: len(p[0]))[0]
obris = [P(lat, lon) for lon, lat in obroc]


def notri(x, z):
    c = False
    j = len(obris) - 1
    for i in range(len(obris)):
        xi, zi = obris[i]; xj, zj = obris[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            c = not c
        j = i
    return c


img = Image.new('RGB', (NX, NZ))
px = img.load()
for j in range(NZ):
    z = Z0 + (j + 0.5) * KORAK
    lat = LAT0 - z / KY
    for i in range(NX):
        x = X0 + (i + 0.5) * KORAK
        lon = LON0 + x / KX
        h = visina(lat, lon)
        v = int(min(65535, h * 16))       # 1/16 m
        px[i, j] = (v >> 8, v & 255, 255 if notri(x, z) else 0)
img.save(IZHOD / 'relief.png', optimize=True)
print('relief', NX, NZ, (IZHOD / 'relief.png').stat().st_size)

# ---- omrežje ----
def i16(v):
    return max(-32768, min(32767, int(round(v))))


ENOTA = 20.0   # m na enoto
proge = []
for pl in d['proge']:
    pts = list(zip(pl[0::2], pl[1::2]))
    proge.append(pts)
# avtobusi: na mrežo 240 m, brez podvojenih odsekov
M0 = d['avtobusi_mreza']
seg = set()
a = d['avtobusi']
for k in range(0, len(a), 4):
    p = (round(a[k] * M0 / 240), round(a[k + 1] * M0 / 240))
    q = (round(a[k + 2] * M0 / 240), round(a[k + 3] * M0 / 240))
    if p != q:
        seg.add((min(p, q), max(p, q)))
print('avtobusni odseki', len(seg))

# ---- vožnje enega jutra ----
voznje = []
for v in d['voznje']:
    vrsta, ime, kl = v[0], v[1], v[2:]
    k = [tuple(kl[i:i + 4]) for i in range(0, len(kl), 4)]
    if len(k) < 2:
        continue
    voznje.append((vrsta, ime, k))

# ---- zamude IC 351 po dnevih ----
vr = d['vrsta']
dnevi = vr['dnevi']
konec = [x[1][-1] for x in dnevi if x[1][-1] is not None]
st = {
    'dni': len(dnevi),
    'mediana_min': round(statistics.median(konec) / 60, 1),
    'p90_min': round(sorted(konec)[int(0.9 * (len(konec) - 1))] / 60, 1),
    'v5': round(100 * sum(1 for x in konec if x < 5 * 60 + 30) / len(konec)),
    'nad11': sum(1 for x in konec if x >= 10 * 60 + 30), 'n': len(konec),
    'od': dnevi[0][0], 'do': dnevi[-1][0],
}
print('IC 351', st)

# mesta za oznake: železniške postaje po imenu
MESTA = ['Ljubljana', 'Maribor', 'Celje', 'Kranj', 'Koper', 'Novo mesto', 'Nova Gorica', 'Murska Sobota',
         'Jesenice', 'Ptuj', 'Postojna', 'Zidani Most', 'Sežana', 'Kamnik Graben', 'Dobova', 'Črnomelj']
po_imenu = {n: (x, z) for n, x, z in d['postaje']}
mesta = [[m.replace(' Graben', ''), *po_imenu[m]] for m in MESTA if m in po_imenu]

meta = {
    'dan': d['dan'], 'enota': ENOTA,
    'relief': {'x0': X0, 'x1': X1, 'z0': Z0, 'z1': Z1, 'nx': NX, 'nz': NZ, 'skala': 1 / 16},
    'obris': [v for p in obris[::2] for v in (round(p[0]), round(p[1]))],
    'mesta': mesta,
    'stevilo': {'vlaki_7_8': d['zapisanih_zeleznica'], 'vlaki_vr_7_8': d['po_voznem_redu_zeleznica'],
                'avtobusi_7_8': d['zapisanih_avtobus'], 'avtobusi_vr_7_8': d['po_voznem_redu_avtobus']},
    'vrsta': {'ime': vr['train_no'], 'smer': vr['headsign'], 'postaje': vr['postaje'], 'pot': vr['pot'],
              'dnevi': [[x[0], [None if v is None else round(v) for v in x[1]]] for x in dnevi], 'stat': st},
    'n_prog': len(proge), 'n_bus': len(seg), 'n_vozenj': len(voznje),
}
buf = io.BytesIO()
# proge: [n, x, z, x, z, ...] v enotah po 20 m
arr = []
for pts in proge:
    arr.append(len(pts))
    for x, z in pts:
        arr += [i16(x / ENOTA), i16(z / ENOTA)]
meta['dolzina_prog'] = len(arr)
buf.write(struct.pack(f'<{len(arr)}h', *arr))
# avtobusi: odseki v enotah po 240 m
arr = [v for p, q in seg for v in (*p, *q)]
buf.write(struct.pack(f'<{len(arr)}h', *arr))
# vožnje: [vrsta, n, (t, x, z, zamuda_s/10) * n]
arr = []
for vrsta, ime, k in voznje:
    arr += [vrsta, len(k)]
    for t, x, z, dz in k:
        arr += [i16(t), i16(x / ENOTA), i16(z / ENOTA), i16(dz / 10)]
meta['dolzina_vozenj'] = len(arr)
buf.write(struct.pack(f'<{len(arr)}h', *arr))
# Strežnik artefaktov ne streže surovih binarnih datotek: vrednosti int16 gredo
# v PNG (R = zgornji, G = spodnji bajt vrednosti + 32768), opis v JSON.
podatki = buf.getvalue()
n = len(podatki) // 2
vred = struct.unpack(f'<{n}h', podatki)
SIR = 1024
vis = (n + SIR - 1) // SIR
slika = Image.new('RGB', (SIR, vis))
pix = []
for v in vred:
    u = v + 32768
    pix.append((u >> 8, u & 255, 0))
pix += [(128, 0, 0)] * (SIR * vis - n)
slika.putdata(pix)
slika.save(IZHOD / 'karta-podatki.png', optimize=True)
meta['n_int16'] = n
(IZHOD / 'karta.json').write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
print('karta-podatki.png', (IZHOD / 'karta-podatki.png').stat().st_size, 'karta.json', (IZHOD / 'karta.json').stat().st_size, meta['stevilo'])
