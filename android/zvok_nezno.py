#!/usr/bin/env python3
"""Zvok nežnega začetka budilke: `app/src/main/res/raw/nezno.mid`.

    python3 zvok_nezno.py

Budilka najprej 45 s zvoni nežno, šele nato glasno kot prej (David, 6. 10.
2026). Zvok predvaja sistem prek kanala obvestila, zato glasnosti med
zvonjenjem ne moremo spreminjati sami -- naraščanje mora biti v datoteki.
MIDI to zmore z jakostjo udarca (velocity) in je pod 1 kB; enak posnetek v
Vorbisu bi bil ~150 kB. MIDI predvaja Sonivox, ki je del AOSP, torej tudi na
telefonih brez Googla.

Glasbena skrinjica (GM 11), razloženi akord E–G–C vsakih 2,5 s.

**Glasnost je zapisana kot krivulja v dBFS, ne kot jakost udarca** (od 1.8).
1.7 je jakost dvigala od 1 s potenco 1,8 in prvih 20 s je bilo pod -53 dBFS:
David na telefonu ni slišal ničesar, samo tresenje, nato glasno. Kadar je ura
glasnega že mimo, nežni del traja samo 20 s -- in to je bil ravno ta del.
Želel si je „na začetku glasnost tihega šepetanja, počasi glasnejše
šepetanje, potem po 15–20 s glasneje“. Zato se začne pri -46 dBFS (najtišje,
kar je na zvočniku telefona še slišati) in je pri 20 s že -29.

Sonivox jakost udarca šteje v kvadratu (izmerjeno na namiznem Sonivoxu:
polovična jakost = -12 dB), zato je jakost 127 · 10^((cilj - L127) / 40).
Od 20 s naprej zveni še oktava niže -- zvok postane polnejši, ne le glasnejši.
"""
from pathlib import Path

TRAJANJE_S = 45
RAZMIK_S = 2.5
TICKS = 480                 # na četrtinko; tempo 120 = 0,5 s na četrtinko
GLASBENA_SKRINJICA = 10     # GM program 11, šteto od 0
NOTE = (76, 79, 84)         # E5, G5, C6
OKTAVA_NIZE = (64, 67, 72)  # E4, G4, C5
OKTAVA_OD_S = 20
ZAMIK_S = 0.22              # med notami razloženega akorda
DOLZINA_S = 1.8

#: Ciljna glasnost (s, dBFS RMS v oknu 2,5 s, kot jo naredi Androidov
#: Sonivox), vmes linearno.
KRIVULJA = ((0, -46), (8, -40), (15, -34), (20, -29), (30, -25), (45, -23))

#: Glasnost pri jakosti 127, z glasnostjo kanala 127. Izmerjeno z Androidovim
#: `MidiExtractor` na emulatorju; namizni Sonivox je za ~2,5 dB glasnejši.
#: Z oktavo je to tudi strop: glasneje od -23 dBFS skrinjica ne zna.
L127 = -26.7
L127_OKTAVA = -22.7


def cilj_db(t: float) -> float:
    for (t0, d0), (t1, d1) in zip(KRIVULJA, KRIVULJA[1:]):
        if t <= t1:
            return d0 + (d1 - d0) * (t - t0) / (t1 - t0)
    return KRIVULJA[-1][1]


def jakost(t: float) -> int:
    l127 = L127_OKTAVA if t >= OKTAVA_OD_S else L127
    return max(1, min(127, round(127 * 10 ** ((cilj_db(t) - l127) / 40))))


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
         (0, bytes([0xC0, GLASBENA_SKRINJICA])),
         (0, bytes([0xB0, 7, 127]))]                          # glasnost kanala; privzeta je 100
    t = 0.0
    while t < TRAJANJE_S - 0.01:
        v = jakost(t)
        akord = list(NOTE)
        if t >= OKTAVA_OD_S:
            akord = [n for par in zip(OKTAVA_NIZE, NOTE) for n in par]
        for i, nota in enumerate(akord):
            z = t + i * ZAMIK_S * len(NOTE) / len(akord)
            d.append((_tick(z), bytes([0x90, nota, v])))
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
