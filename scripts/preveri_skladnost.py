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
import urllib.parse
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


def ovire_povsod_isto():
    """Ista beseda mora povsod pomeniti isto število.

    `health.alerts_active` je štel VSE shranjene ovire, ne le veljavnih:
    62 proti 16, ki jih kaže stran. Tri mesta, dve številki.
    """
    # `/api/alerts` odslej vraca TUDI napovedane (glej `alerts.active`), števca
    # pa štejeta samo veljavne — to je namerno. Primerjamo veljavni del.
    al = json.load(urllib.request.urlopen(f"{BASE}/api/alerts", timeout=20))
    vrstice = al if isinstance(al, list) else al.get("alerts", [])
    n = sum(1 for x in vrstice if not x.get("napovedana"))
    ov = json.load(urllib.request.urlopen(f"{BASE}/api/overview", timeout=20))["disruptions"]
    he = json.load(urllib.request.urlopen(f"{BASE}/api/health", timeout=20))["alerts_active"]
    if not (n == ov == he):
        return f"/api/alerts (veljavnih) {n}, overview {ov}, health {he}"
    # In da napovedane sploh pridejo skozi -- sicer bi stran spet molcala.
    if not any(x.get("napovedana") for x in vrstice):
        return "med ovirami ni nobene napovedane — ali jih endpoint spet izpušča?"
    return None


def tabla_in_okno_isto():
    """Ista vožnja, ista postaja, dve strani -- ena številka.

    Odhodna tabla in okno vožnje računata mejo med meritvijo in napovedjo
    vsak po svoje: tabla vidi en sam postanek, okno pa celo vožnjo. Ko je
    okno dobilo pravilo o neskladnih urah (`stats.oznaci_neskladne`), je
    tabla lahko za isti postanek še vedno kazala ostanek kot „izmerjeno".
    Tu se preveri, da se nista razšla.

    Vzorec je odvisen od ure dneva -- ponoči izmerjenih vrstic skoraj ni --
    zato premalo vrstic ni napaka, ampak molk.
    """
    postaje = (("Ljubljana", "zeleznica"), ("Maribor", "zeleznica"),
               ("Celje", "zeleznica"), ("Bavarski dvor", "avtobus"),
               ("Ljubljana AP", "avtobus"), ("Celje AP", "avtobus"))
    ujema = 0
    for ime, net in postaje:
        q = urllib.parse.urlencode({"station": ime, "network": net, "limit": 40})
        d = json.load(urllib.request.urlopen(f"{BASE}/api/departures?{q}", timeout=30))
        for r in d["board"]:
            if r.get("delay_s") is None or r.get("delay_kind") != "izmerjeno":
                continue
            q2 = urllib.parse.urlencode({"trip": r["trip_id"], "date": d["date"]})
            no = urllib.parse.quote(r["train_no"])
            run = json.load(urllib.request.urlopen(f"{BASE}/api/train/{no}/run?{q2}", timeout=30))
            s = next((x for x in run["stops"] if x["stop_seq"] == r["stop_seq"]), None)
            if s is None:
                return f'{r["train_no"]}: table pozna postanek {r["stop_seq"]}, okno ne'
            z = s.get("zamuda")
            if z is not None and z["vrsta"] == "neskladno":
                return (f'{r["train_no"]} na {ime}: tabla „izmerjeno" '
                        f'{r["delay_s"]} s, okno „neskladno"')
            if z is None:
                if not r.get("delay_from"):
                    return f'{r["train_no"]} na {ime}: tabla ima zamudo, okno nima'
                continue
            if abs(z["s"] - r["delay_s"]) > 60:
                return (f'{r["train_no"]} na {ime}: tabla {r["delay_s"]} s, '
                        f'okno {z["s"]} s')
            ujema += 1
    print(f"       (primerjanih vrstic: {ujema})")
    return None


for opis, fn in (
    ("brez osirotelih meritev", brez_sirot),
    ("delež točnih = vsota razredov", vsota_razredov),
    ("razred zamude po zaokroženi minuti", razred_po_minuti),
    ("health je hiter (pod 200 ms)", health_je_hiter),
    ("prestop pod ničlo z besedo", prestop_brez_minusa),
    ("ovire povsod ista številka", ovire_povsod_isto),
    ("tabla in okno vožnje ista številka", tabla_in_okno_isto),
):
    preveri(opis, fn)

sys.exit(1 if napake else 0)
