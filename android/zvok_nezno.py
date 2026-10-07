#!/usr/bin/env python3
"""Zvok nežnega začetka budilke: `app/src/main/res/raw/nezno.mid`.

    python3 zvok_nezno.py
    ./zvok_meri.sh app/src/main/res/raw/nezno.mid    # izmeri na telefonu

Budilka najprej 20 s zvoni nežno, šele nato glasno kot prej (David, 6. 10.
2026; do 1.10 45 s, 7. 10.: „največ 20 s“). Datoteka traja 45 s: če bi glasni
del zamudil, zvok raste naprej, namesto da bi se ponovil od šepeta. Zvok predvaja sistem prek kanala obvestila, zato glasnosti med
zvonjenjem ne moremo spreminjati sami -- naraščanje mora biti v datoteki.
MIDI to zmore z jakostjo udarca (velocity) in je pod 1 kB; enak posnetek v
Vorbisu bi bil ~150 kB. MIDI predvaja Sonivox, ki je del AOSP, torej tudi na
telefonih brez Googla.

**Harfa** (GM 47), razloženi akordi C–Am–F–G, vsak 2 s. Izbral jo je David
7. 10. 2026 med osmimi predlogi (skrinjica, postajni gong, vibrafon, harfa,
kalimba, električni klavir, blazina, prihod vlaka): „taka nežna in ni
piskajoča“. Do 1.10 je bila glasbena skrinjica.

**Glasnost je zapisana kot krivulja v dBFS, kot jo izmeri `zvok_meri.sh`**
(RMS v oknu 2,5 s, Sonivox na telefonu). Jakost udarca se izračuna iz
izmerjene tabele [KALIBRACIJA], ne iz formule: Sonivox pod jakostjo ~16 skoraj
ne tiša več, in tudi „tišina“ ima šum pri -65 dBFS. Formula s kvadratom jakosti
je pri skrinjici začetek cenila na -67, izmerjeno je bilo -61.

Krivulja je tista, ki jo je David potrdil na skrinjici (Volla, glasnost
budilke 6/7, 7. 10. 2026): -46 na začetku je bilo „preglasno“, nato „še čisto
malo preglasno“, -61 pa „dobro“.
"""
from pathlib import Path

TRAJANJE_S = 45
RAZMIK_S = 2.0
TICKS = 480                 # na četrtinko; tempo 120 = 0,5 s na četrtinko
HARFA = 46                  # GM program 47, šteto od 0
C, D, E, F, G, A, H = 72, 74, 76, 77, 79, 81, 83
#: Akordi po vrsti, vsak razložen čez dve oktavi.
AKORDI = ((C, E, G), (A - 12, C, E), (F - 12, A - 12, C), (G - 12, H - 12, D))
ZAMIK_S = 0.16              # med notami razloženega akorda
DOLZINA_S = 1.8

#: Ciljna glasnost (s, dBFS RMS v oknu 2,5 s), vmes linearno. Konec je strop
#: harfe pri jakosti 127.
KRIVULJA = ((0, -61), (8, -54), (15, -42), (20, -34), (30, -27), (45, -24.5))

#: Jakost udarca → izmerjena glasnost tega vzorca (dBFS RMS, glasnost kanala
#: 127). Volla 22, Android 16, `zvok_meri.sh`, 7. 10. 2026. Pod 16 krivulja
#: skoraj obstane: tam je Sonivoxov spodnji rob, ne harfa.
KALIBRACIJA = ((4, -63.2), (6, -61.8), (8, -61.2), (10, -60.9), (12, -60.5),
               (16, -59.0), (20, -56.7), (25, -53.4), (32, -49.1), (40, -45.0),
               (50, -41.1), (64, -36.1), (80, -32.5), (100, -28.5), (127, -24.3))


def cilj_db(t: float) -> float:
    for (t0, d0), (t1, d1) in zip(KRIVULJA, KRIVULJA[1:]):
        if t <= t1:
            return d0 + (d1 - d0) * (t - t0) / (t1 - t0)
    return KRIVULJA[-1][1]


def jakost(t: float) -> int:
    """Najmanjša jakost, ki po tabeli doseže cilj; vmes linearno."""
    cilj = cilj_db(t)
    if cilj <= KALIBRACIJA[0][1]:
        return KALIBRACIJA[0][0]
    for (v0, d0), (v1, d1) in zip(KALIBRACIJA, KALIBRACIJA[1:]):
        if cilj <= d1:
            return round(v0 + (v1 - v0) * (cilj - d0) / (d1 - d0))
    return 127


def _vlq(n: int) -> bytes:
    """Število v MIDI-jevem zapisu s spremenljivo dolžino."""
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def _tick(s: float) -> int:
    return round(s / 0.5 * TICKS)


def dogodki() -> list[tuple[int, bytes]]:
    d = [(0, bytes([0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20])),     # 500 000 µs na četrtinko
         (0, bytes([0xC0, HARFA])),
         (0, bytes([0xB0, 7, 127]))]                          # glasnost kanala; privzeta je 100
    t, i = 0.0, 0
    while t < TRAJANJE_S - 0.01:
        v = jakost(t)
        a = AKORDI[i % len(AKORDI)]
        for j, nota in enumerate(a + tuple(n + 12 for n in a)):
            z = t + j * ZAMIK_S
            d.append((_tick(z), bytes([0x90, nota, v])))
            d.append((_tick(z + DOLZINA_S), bytes([0x80, nota, 0])))
        t += RAZMIK_S
        i += 1
    d.sort(key=lambda x: (x[0], x[1][0] == 0x90))   # ob istem času najprej izklop
    return d


def midi() -> bytes:
    sled, prej = b"", 0
    for tick, dog in dogodki():
        sled += _vlq(tick - prej) + dog
        prej = tick
    sled += _vlq(0) + bytes([0xFF, 0x2F, 0x00])
    glava = b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big") + (1).to_bytes(2, "big") \
        + TICKS.to_bytes(2, "big")
    return glava + b"MTrk" + len(sled).to_bytes(4, "big") + sled


if __name__ == "__main__":
    cilj = Path(__file__).resolve().parent / "app" / "src" / "main" / "res" / "raw" / "nezno.mid"
    cilj.parent.mkdir(parents=True, exist_ok=True)
    cilj.write_bytes(midi())
    print(f"{cilj}: {cilj.stat().st_size} B")
