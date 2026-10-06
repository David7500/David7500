#!/usr/bin/env python3
"""Zvok nežnega začetka budilke: `app/src/main/res/raw/nezno.mid`.

    python3 zvok_nezno.py

Budilka najprej 45 s zvoni nežno, šele nato glasno kot prej (David, 6. 10.
2026). Zvok predvaja sistem prek kanala obvestila, zato glasnosti med
zvonjenjem ne moremo spreminjati sami -- naraščanje mora biti v datoteki.
MIDI to zmore z jakostjo udarca (velocity) in je pod 1 kB; enak posnetek v
Vorbisu bi bil ~150 kB, aplikacija jih ima 111. MIDI predvaja Sonivox, ki je
del AOSP, torej tudi na telefonih brez Googla.

Glasbena skrinjica (GM 11), razloženi akord E–G–C vsakih 2,5 s, jakost od
komaj slišne do skoraj polne: če se glasni del iz kakršnegakoli razloga ne
bi začel, je konec tega zvoka že dovolj glasen, da zbudi.
"""
from pathlib import Path

TRAJANJE_S = 45
RAZMIK_S = 2.5
TICKS = 480                 # na četrtinko; tempo 120 = 0,5 s na četrtinko
GLASBENA_SKRINJICA = 10     # GM program 11, šteto od 0
NOTE = (76, 79, 84)         # E5, G5, C6
ZAMIK_S = 0.22              # med notami razloženega akorda
DOLZINA_S = 1.8
JAKOST = (14, 112)          # od, do


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
         (0, bytes([0xC0, GLASBENA_SKRINJICA]))]
    t = 0.0
    while t < TRAJANJE_S - 0.01:
        f = t / TRAJANJE_S
        jakost = round(JAKOST[0] + (JAKOST[1] - JAKOST[0]) * f ** 1.4)
        for i, nota in enumerate(NOTE):
            z = t + i * ZAMIK_S
            d.append((_tick(z), bytes([0x90, nota, jakost])))
            d.append((_tick(z + DOLZINA_S), bytes([0x80, nota, 0])))
        t += RAZMIK_S
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
