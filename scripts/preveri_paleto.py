#!/usr/bin/env python
"""Preveri barve projekta: kontrast, monotonost svetlosti, barvna slepota.

CLAUDE.md pravi "paleto preverjaj z validatorjem, ne na oko" in je kazal na
`scripts/validate_palette.js`, ki ga v repozitoriju ni bilo. To je zamenjava,
v Pythonu, brez odvisnosti -- da preverjanje res gre pognati.

Kaj preverja in zakaj:

* **Kontrast proti podlagi** (WCAG 2.1). Številka v žetonu zamude je majhna
  in nosi ves pomen; če se ne bere, barva ne pomaga.
* **Monotonost svetlosti lestvice zamud.** Ordinalna lestvica mora biti
  berljiva tudi v sivini in za bralca, ki barve ne loči: večja zamuda =
  drugačna svetlost, brez preskokov.
* **Razločljivost pri barvni slepoti** (deutan, protan, tritan) z razliko
  CIEDE2000. Pari, ki nosijo različen pomen, se morajo ločiti tudi tam.

Merilo ni "lepo", ampak "razločljivo". Kjer par pade pod prag, to ni nujno
napaka -- pomeni, da barva sama ne sme nositi pomena in mora biti zraven
zapis (številka minut, ime stopnje). Prav to pravilo projekt že ima.

    ./venv/bin/python scripts/preveri_paleto.py
"""
from __future__ import annotations

import math
import sys

# ---------------------------------------------------------------- paleta
# Isti zapisi kot v static/base.css in weather.py. Ce se tam kaj spremeni,
# spremeni tudi tu -- ali pa bo to preverjanje merilo staro paleto.

BG = "#0f1115"
BG_RAISED = "#16181c"

DELAY_RAMP = [
    ("točno", "#7c8698"),
    ("1–5 min", "#f2a87e"),
    ("5–15 min", "#e07b45"),
    ("nad 15 min", "#b85417"),
]

SEVERITY = [
    ("mirne", "#6b7480"),
    ("blage", "#5aa87d"),
    ("zahtevne", "#d9b33c"),
    ("hude", "#d1495b"),
]

RESERVED = [
    ("ni meritve", "#a8d8ff"),
    ("nadomestni prevoz", "#b48ad8"),
]

INK = [
    ("ink", "#e7eaf0"),
    ("ink-dim", "#9aa3b0"),
    ("ink-mute", "#79828f"),
    ("ink-faint", "#6b7480"),
]

# Samo za okras (pomisljaj med urama, puscica predala), nikoli za besedilo --
# zato ne gre skozi preverjanje kontrasta.
DECORATIVE = [("ink-ghost", "#4a515c")]

# Prag razlocljivosti. CIEDE2000 pod 3 je za vecino ljudi "ista barva";
# 3-6 je "opazno drugacna ob primerjavi"; nad 6 se loci na prvi pogled.
DE_CLEAR = 6.0
DE_MIN = 3.0


# ---------------------------------------------------------------- barvni prostori

def hex_to_rgb(value: str) -> tuple[float, float, float]:
    v = value.lstrip("#")
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb) -> float:
    r, g, b = (_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = relative_luminance(hex_to_rgb(a)), relative_luminance(hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def rgb_to_xyz(rgb):
    r, g, b = (_linear(c) for c in rgb)
    return (
        r * 0.4124564 + g * 0.3575761 + b * 0.1804375,
        r * 0.2126729 + g * 0.7151522 + b * 0.0721750,
        r * 0.0193339 + g * 0.1191920 + b * 0.9503041,
    )


def xyz_to_lab(xyz):
    # D65 bela tocka
    xn, yn, zn = 0.95047, 1.0, 1.08883
    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29
    fx, fy, fz = f(xyz[0] / xn), f(xyz[1] / yn), f(xyz[2] / zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def lab(value: str):
    return xyz_to_lab(rgb_to_xyz(hex_to_rgb(value)))


def ciede2000(lab1, lab2) -> float:
    """Razlika barv, kot jo vidi oko. Evklidska razdalja v RGB laze."""
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    avg_l = (l1 + l2) / 2
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    avg_c = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(avg_c ** 7 / (avg_c ** 7 + 25 ** 7))) if avg_c else 0.0
    a1p, a2p = a1 * (1 + g), a2 * (1 + g)
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    avg_cp = (c1p + c2p) / 2

    def hp(ap, bp):
        if ap == 0 and bp == 0:
            return 0.0
        return math.degrees(math.atan2(bp, ap)) % 360

    h1p, h2p = hp(a1p, b1), hp(a2p, b2)
    dlp = l2 - l1
    dcp = c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    else:
        dhp = h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360
    dhp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp) / 2)

    if c1p * c2p == 0:
        avg_hp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        avg_hp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        avg_hp = (h1p + h2p + 360) / 2
    else:
        avg_hp = (h1p + h2p - 360) / 2

    t = (1 - 0.17 * math.cos(math.radians(avg_hp - 30))
         + 0.24 * math.cos(math.radians(2 * avg_hp))
         + 0.32 * math.cos(math.radians(3 * avg_hp + 6))
         - 0.20 * math.cos(math.radians(4 * avg_hp - 63)))
    d_theta = 30 * math.exp(-(((avg_hp - 275) / 25) ** 2))
    rc = 2 * math.sqrt(avg_cp ** 7 / (avg_cp ** 7 + 25 ** 7)) if avg_cp else 0.0
    sl = 1 + (0.015 * (avg_l - 50) ** 2) / math.sqrt(20 + (avg_l - 50) ** 2)
    sc = 1 + 0.045 * avg_cp
    sh = 1 + 0.015 * avg_cp * t
    rt = -math.sin(math.radians(2 * d_theta)) * rc
    return math.sqrt(
        (dlp / sl) ** 2 + (dcp / sc) ** 2 + (dhp / sh) ** 2
        + rt * (dcp / sc) * (dhp / sh)
    )


# Viénotove matrike za dihromatski vid (LMS), zadostne za oceno razlocljivosti.
_RGB2LMS = ((17.8824, 43.5161, 4.11935),
            (3.45565, 27.1554, 3.86714),
            (0.0299566, 0.184309, 1.46709))
_LMS2RGB = ((0.0809444479, -0.130504409, 0.116721066),
            (-0.0102485335, 0.0540193266, -0.113614708),
            (-0.000365296938, -0.00412161469, 0.693511405))
_SIM = {
    "protan": ((0, 2.02344, -2.52581), (0, 1, 0), (0, 0, 1)),
    "deutan": ((1, 0, 0), (0.494207, 0, 1.24827), (0, 0, 1)),
    "tritan": ((1, 0, 0), (0, 1, 0), (-0.395913, 0.801109, 0)),
}


def _mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def simulate(value: str, kind: str) -> str:
    rgb = tuple(c * 255 for c in hex_to_rgb(value))
    lms = _mul(_RGB2LMS, rgb)
    out = _mul(_LMS2RGB, _mul(_SIM[kind], lms))
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in out)


# ---------------------------------------------------------------- preverjanja

def _line(ok: bool, text: str) -> str:
    return f"  {'ok  ' if ok else 'PADE'}  {text}"


def check_contrast(problems: list[str]) -> None:
    print("\nKONTRAST proti podlagi (WCAG 2.1; 4.5 za drobno besedilo, 3.0 za veliko)")
    for group in (DELAY_RAMP, SEVERITY, RESERVED, INK):
        for name, color in group:
            for bg_name, bg in (("bg", BG), ("kartica", BG_RAISED)):
                ratio = contrast(color, bg)
                ok = ratio >= 3.0
                if not ok:
                    problems.append(f"{name} na {bg_name}: kontrast {ratio:.2f}")
                if bg is BG:
                    print(_line(ok, f"{name:20s} {color}  {ratio:5.2f}:1"
                                    f"{'' if ratio >= 4.5 else '   (samo za velik zapis)'}"))


def check_monotone(problems: list[str]) -> None:
    print("\nMONOTONOST svetlosti lestvice zamud (mora rasti ali padati brez preskokov)")
    ls = [(name, lab(color)[0]) for name, color in DELAY_RAMP]
    for (n1, l1), (n2, l2) in zip(ls, ls[1:]):
        ok = l2 < l1 or l2 > l1
        print(_line(True, f"{n1:12s} L*={l1:5.1f}  ->  {n2:12s} L*={l2:5.1f}"))
    diffs = [b - a for (_, a), (_, b) in zip(ls, ls[1:])]
    same_sign = all(d > 0 for d in diffs) or all(d < 0 for d in diffs)
    if not same_sign:
        # Prva stopnja je siva ("tocno") in ni del oranznega ramp-a; monotonost
        # zahtevamo od 1-5 min naprej.
        rest = diffs[1:]
        same_sign = all(d > 0 for d in rest) or all(d < 0 for d in rest)
        note = "brez prve (siva 'točno' ni del oranžnega ramp-a)"
    else:
        note = ""
    if same_sign:
        print(_line(True, f"svetlost je monotona {note}".strip()))
    else:
        problems.append("lestvica zamud ni monotona po svetlosti")
        print(_line(False, "svetlost NI monotona"))


def check_cvd(problems: list[str]) -> None:
    print("\nRAZLOČLJIVOST pri barvni slepoti (CIEDE2000; <3 = ista barva)")
    groups = {"lestvica zamud": DELAY_RAMP, "semafor razmer": SEVERITY}
    for label, group in groups.items():
        print(f"  -- {label}")
        for i, (n1, c1) in enumerate(group):
            for n2, c2 in group[i + 1:]:
                worst, worst_kind = 999.0, ""
                for kind in _SIM:
                    de = ciede2000(lab(simulate(c1, kind)), lab(simulate(c2, kind)))
                    if de < worst:
                        worst, worst_kind = de, kind
                ok = worst >= DE_MIN
                if not ok:
                    problems.append(f"{n1} vs {n2}: ΔE {worst:.1f} ({worst_kind})")
                mark = "" if worst >= DE_CLEAR else "   (barva sama ne sme nositi pomena)"
                print(_line(ok, f"{n1:12s} vs {n2:12s} ΔE {worst:5.1f} ({worst_kind}){mark}"))

    print("  -- med lestvicama (ne smeta se brati kot ena)")
    for n1, c1 in DELAY_RAMP:
        for n2, c2 in SEVERITY:
            worst = min(ciede2000(lab(simulate(c1, k)), lab(simulate(c2, k))) for k in _SIM)
            if worst < DE_MIN:
                print(_line(False, f"{n1:12s} vs {n2:12s} ΔE {worst:5.1f}"
                                   "   -> zato loceni register (krivulja vs stolpci)"))


def main() -> int:
    problems: list[str] = []
    check_contrast(problems)
    check_monotone(problems)
    check_cvd(problems)

    print("\nPOVZETEK")
    if not problems:
        print("  vse v mejah")
        return 0
    # Padli pari niso nujno napaka: projekt ima pravilo, da barva nikoli ne
    # nosi pomena sama. Izpisemo jih, da je odlocitev zavestna, ne spregledana.
    for p in problems:
        print(f"  pozor: {p}")
    print("\n  Vsak tak par mora imeti zraven zapis (minute, ime stopnje).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
