#!/usr/bin/env python3
"""Preverja, da si številke na zaslonu ne nasprotujejo.

Vsaka od teh je bila 4. 9. 2026 resnična napaka, najdena z ročnim pregledom.
Tu ostanejo, da jih ne bi bilo treba iskati znova.

    ./venv/bin/python scripts/preveri_skladnost.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

sys.path.insert(0, ".")
from kajros import db, stats                       # noqa: E402

BASE = "http://127.0.0.1:8001"
napake: list[str] = []


def preveri(opis: str, fn) -> None:
    try:
        razlog = fn()
    except Exception as e:                          # noqa: BLE001
        razlog = f"{type(e).__name__}: {e}"
    if razlog:
        napake.append(opis)
        print(f"  PADE {opis:<44} {razlog}")
    else:
        print(f"  ok   {opis}")


def brez_sirot():
    """Meritev brez svoje vožnje je nevidna vsaki poizvedbi.

    Vse gredo skozi `JOIN trip`, ker je omrežje tam. Nastane, ko uvoz voznega
    reda izbriše vožnjo, ki ima meritve.
    """
    n = db.connect().execute(
        "SELECT COUNT(*) FROM run r LEFT JOIN trip t USING (trip_id) "
        "WHERE t.trip_id IS NULL").fetchone()[0]
    return None if n == 0 else f"{n} osirotelih meritev — glej `kajros repair`"


def vsota_razredov():
    """„točno“ + „1–5 min“ se mora sešteti v izpisani delež točnih.

    Prag je bil v sekundah (300), razred pa v zaokroženih minutah (330):
    553 voženj se ni ujelo in bralec, ki sešteje, je dobil drugo številko.
    """
    o = json.load(urllib.request.urlopen(f"{BASE}/api/overview", timeout=20))["today"]
    if not o.get("runs"):
        return None                                  # prazen dan ni napaka
    b = o["buckets"]
    v_pragu = b["točno"] + b["1–5 min"]
    pricakovano = round(v_pragu / o["runs"], 3)
    if abs(pricakovano - o["on_time_share"]) > 0.001:
        return (f"vsota razredov da {pricakovano}, izpisano pa je "
                f"{o['on_time_share']}")
    return None


def razred_po_minuti():
    """Razred mora slediti izpisani minuti, ne sekundam.

    `common.delayLabel()` izpiše `Math.round(s/60)`, zato mora biti 30 s že
    „1–5 min“ — sicer je vrstica siva in piše „+1“.
    """
    pari = [(29, "točno"), (30, "1–5 min"), (300, "1–5 min"),
            (330, "5–15 min"), (900, "5–15 min"), (930, "nad 15 min")]
    slabi = [f"{s} s -> {stats._razred_zamude(s)} (pričakoval {p})"
             for s, p in pari if stats._razred_zamude(s) != p]
    return "; ".join(slabi) or None


def health_je_hiter():
    """`/api/health` je delal sekundo dela z bazo na klic; stran ga kliče
    vsakih 30 s. Če kdo odstrani predpomnilnik, naj se vidi tu."""
    t = time.monotonic()
    urllib.request.urlopen(f"{BASE}/api/health", timeout=20).read()
    d = time.monotonic() - t
    return None if d < 0.2 else f"{d*1000:.0f} ms — je predpomnilnik odstranjen?"


def prestop_brez_minusa():
    """Preostanek pod ničlo se pove z besedo, ne z minusom.

    „−1 min za prestop“ je uganka in nastopi natanko takrat, ko zveza ne drži.
    """
    from pathlib import Path
    js = Path("kajros/static/connections.js").read_text()
    # Ne iščemo golega niza -- ta je legitimno v `prestopText()` za pozitivne
    # minute. Iščemo, ali gre ŽETON skozi to funkcijo.
    if "prestopText(mins)" not in js:
        return "žeton ne gre skozi `prestopText()` — negativna minuta bo gola"
    if "zmanjka " not in js or "brez rezerve" not in js:
        return "manjka beseda za negativno oziroma ničelno rezervo"
    return None


for opis, fn in (
    ("brez osirotelih meritev", brez_sirot),
    ("delež točnih = vsota razredov", vsota_razredov),
    ("razred zamude po zaokroženi minuti", razred_po_minuti),
    ("health je hiter (pod 200 ms)", health_je_hiter),
    ("prestop pod ničlo z besedo", prestop_brez_minusa),
):
    preveri(opis, fn)

sys.exit(1 if napake else 0)
