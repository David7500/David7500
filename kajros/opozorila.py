"""Opozorilo skrbniku po pošti, ko je v `/admin` kaj rdeče.

1. 10. 2026 je nit zemljevida SŽ 4,3 h stala, WAL je rasel na 5,4 GB, opazilo
pa se je šele, ko je skrbnik odprl pregled. Ob 3:30 nihče ne gleda.

Kaj gre v pošto, odloča `zdravje.posta()`: samo okvara, pri kateri mora
skrbnik kaj narediti (nit stoji, disk, zajem ne piše, vozni red se konča),
ne vsaka rdeča vrstica pregleda -- izpad vira z rezervo in kakovost, ki je
skrbnik ne popravi, ostaneta v /admin. Pošta gre, ko okvara traja (privzeto
`ZAMIK_S`; en zgrešen obhod ali ponovni zagon ni okvara), in še enkrat, ko
je vsaj `KONEC_S` spet v redu. Vmes nič: opozorilo, ki zvoni vsako minuto,
se neha brati.

Nastavitve so v `${KAJROS_DATA_DIR}/.opozorila` (vrstice `ime=vrednost`:
`za`, `od`, `geslo`, `streznik`, `vrata`), iz istega razloga kot
`.admin-zeton`: posodobitev strežnika je brez sudota in v enoto ne more
pisati. Brez datoteke opozoril ni -- tako v razvoju.
"""
from __future__ import annotations

import json
import smtplib
import ssl
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from typing import Callable
from zoneinfo import ZoneInfo

import requests

from . import config, db, viri, zdravje

TZ = ZoneInfo(config.TIMEZONE)

#: Toliko mora biti vrstica rdeča, preden gre pošta (kadar `zdravje.Okvara`
#: ne pove drugače). Po ponovnem zagonu je feed lahko do prvega branja star
#: ~1 min, `/api/health` po omrežjih pa je predpomnjen do 10 min.
ZAMIK_S = 600
#: Toliko mora biti spet v redu, preden gre „spet v redu“. Brez tega bi
#: vrstica, ki niha okoli meje, pošiljala par sporočil na vsako nihanje:
#: pri 5 min je „vozila brez vsake zamude“ 12. 10. 2026 poslala 14 pošt.
KONEC_S = 900
OBHOD_S = 60


def nastavitve() -> dict | None:
    try:
        vrstice = (config.DATA_DIR / ".opozorila").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    n = dict(v.split("=", 1) for v in (x.strip() for x in vrstice)
             if "=" in v and not v.startswith("#"))
    n = {k.strip(): v.strip() for k, v in n.items()}
    if not all(n.get(k) for k in ("za", "od", "geslo", "streznik")):
        return None
    n["vrata"] = int(n.get("vrata") or 465)
    return n


def _ura(ts: float) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M")


# --- vzrok: kdo ne odgovarja ----------------------------------------------
#
# 8. 10. 2026 je pošta ob 16:10 rekla „zadnja zamuda iz feeda pred 11 min“,
# vzrok pa je bilo treba iskati ročno: journal na strežniku, curl na vsak vir,
# isto še od zunaj. Odgovor je bil v vsakem od teh korakov isti -- strežnik
# RT derp.si ne sprejema povezav, naš internet dela. To zdaj naredi pošta.

#: Vrstice zdravja, ki pomenijo, da ne pride podatek od zunaj. Disk, WAL,
#: neznane vožnje in mrtva nit so naša stvar; tam preverjanje virov ne pove
#: ničesar.
ZAJEM = frozenset({"feed", "zeleznica", "avtobus", "derp_ijpp", "derp_lpp", "zamude_sz",
                   "zamude_lpp", "nap"})

#: Preverjanje je v `viri.py`, ker ga kliče tudi gumb v /admin; ime ostane,
#: da pošta in preizkusi berejo isto.
preveri_vir = viri.preveri


def vzrok(get: Callable = requests.get, zdaj: float | None = None) -> str:
    """Odstavek za pošto: kateri vir odgovarja in kaj iz tega sledi.

    Samo viri v živo (`zivo`, `izvirniki`): okvaro zajema povzroči eden od
    njih, vozni red in vreme ji ne morejo biti vzrok.
    """
    izid = viri.preveri_vire([v for v in viri.vsi() if v.skupina in ("zivo", "izvirniki")],
                             get, zdaj)
    vrstice = [f"• {r['ime']}: {r['opis']}" for r in izid["viri"]]
    vrstice.append(f"• {izid['kontrola']['ime']}: {izid['kontrola']['opis']}")
    ura = _ura(izid["ts"])
    return f"Vzrok (preverjeno ob {ura}):\n" + "\n".join(vrstice) + "\n" + izid["sklep"]


def _trajanje(s: float) -> str:
    m = round(s / 60)
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60} min"


def korak(stanje: dict, okvare: dict[str, zdravje.Okvara | None], zdaj: float,
          vzrok: Callable[[], str] | None = None, rumene: list[str] | None = None,
          ) -> tuple[dict, tuple[str, str] | None, list[str], list[str]]:
    """Novo stanje, sporočilo (zadeva, telo) ali None, ključi novih in rešenih.

    `okvare` je `zdravje.posta()`: vrstica -> okvara ali None, kadar se je ta
    hip ne da oceniti (ponoči) -- taka vrstica ne začne ne konča ničesar.
    `vzrok` se pokliče samo, kadar je med novimi okvarami zajem (`ZAJEM`):
    preverjanje virov traja do pol minute in pri polnem disku ne pove nič.
    `rumene` so razlogi rumenih vrstic: v pošti so samo ob novi okvari, za
    vedenje, kaj je bilo ob njej še narobe.

    Stanje je `{ključ: {od, poslano, razlog, dobro_od}}`. Ključ, ki ga ni v
    sporočilu, ostane, dokler pošta ne uspe -- zato klicatelj stanja ne
    potrdi, preden pošlje.
    """
    stanje = {k: dict(v) for k, v in stanje.items()}
    slabe = {k: o for k, o in okvare.items() if o is not None}
    for k, o in slabe.items():
        s = stanje.setdefault(k, {"od": zdaj, "poslano": 0})
        s["razlog"] = o.razlog
        s.pop("dobro_od", None)
    for k, s in stanje.items():
        if k in slabe:
            continue
        if k in okvare:                   # ne da se oceniti: nič ne teče
            s.pop("dobro_od", None)
        else:
            s.setdefault("dobro_od", zdaj)

    nove = [k for k, s in stanje.items()
            if k in slabe and not s["poslano"] and zdaj - s["od"] >= slabe[k].po_s]
    koncane = [k for k, s in stanje.items()
               if "dobro_od" in s and zdaj - s["dobro_od"] >= KONEC_S]
    resene = [k for k in koncane if stanje[k]["poslano"]]
    # Kar ni bilo nikoli sporočeno, ugasne tiho.
    for k in koncane:
        if not stanje[k]["poslano"]:
            del stanje[k]
    if not nove and not resene:
        return stanje, None, [], []

    se = [k for k, s in stanje.items() if k in slabe and s["poslano"]]
    deli = []
    if nove:
        deli.append("Stoji:\n" + "\n".join(
            f"• {zdravje.ime(k)}: {stanje[k]['razlog']} (od {_ura(stanje[k]['od'])})\n"
            f"  Kaj storiti: {slabe[k].ukrep}" for k in nove))
    if resene:
        deli.append("Spet v redu:\n" + "\n".join(
            f"• {zdravje.ime(k)} (stalo {_ura(stanje[k]['od'])}–"
            f"{_ura(stanje[k]['dobro_od'])}, {_trajanje(stanje[k]['dobro_od'] - stanje[k]['od'])}; "
            f"bilo: {stanje[k]['razlog']})" for k in resene))
    if se:
        deli.append("Še vedno stoji:\n" + "\n".join(
            f"• {zdravje.ime(k)}: {stanje[k]['razlog']} (od {_ura(stanje[k]['od'])})" for k in se))
    if nove and rumene:
        deli.append("Ob tem rumeno (samo za vedenje):\n" + "\n".join(f"• {r}" for r in rumene))
    if vzrok is not None and ZAJEM.intersection(nove):
        deli.append(vzrok())
    deli.append(f"{config.BASE_URL}/admin")
    zadeva = (f"kajros: stoji -- {stanje[nove[0]]['razlog']}" if nove
              else f"kajros: spet v redu -- {zdravje.ime(resene[0])}")
    return stanje, (zadeva, "\n\n".join(deli) + "\n"), nove, resene


def poslji(n: dict, zadeva: str, telo: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = n["od"], n["za"], zadeva
    msg.set_content(telo)
    with smtplib.SMTP_SSL(n["streznik"], n["vrata"], timeout=30,
                          context=ssl.create_default_context()) as srv:
        srv.login(n["od"], n["geslo"])
        srv.send_message(msg)


def _potrdi(stanje: dict, nove: list[str], resene: list[str], zdaj: float) -> dict:
    for k in nove:
        stanje[k]["poslano"] = zdaj
    for k in resene:
        del stanje[k]
    return stanje


def teci(stop: threading.Event, log: Callable[[str], None],
         beri_zdravje: Callable[[], dict]) -> None:
    """Svoja nit: pošta zna viseti 30 s, zajem pa ne sme čakati nanjo."""
    n = nastavitve()
    if n is None:
        return
    log(f"opozorila po pošti vklopljena (za {n['za']})")
    conn = db.connect()
    napak = 0
    try:
        stanje = json.loads(db.get_meta(conn, "opozorila") or "{}")
        while not stop.wait(OBHOD_S):
            zdaj = time.time()
            try:
                z, m = beri_zdravje(), zdravje.stroj()
                ocena = zdravje.ocena(z, m, zdaj)
                rumene = [r for raz, r in ocena.values() if raz == zdravje.MLACNA and r]
                novo, sporocilo, nove, resene = korak(
                    stanje, zdravje.posta(z, m, ocena, zdaj), zdaj, vzrok, rumene)
                if sporocilo:
                    poslji(n, *sporocilo)
                    novo = _potrdi(novo, nove, resene, zdaj)
                    log(f"opozorilo poslano: {sporocilo[0]}")
                stanje = novo
                napak = 0
            except Exception as exc:      # noqa: BLE001 -- nit ne sme umreti
                napak += 1
                if napak == 1:
                    log(f"opozorila ni bilo mogoče poslati: {exc}")
            # Stanje je v pomnilniku že novo; zapis v bazo je samo za ponovni
            # zagon. Ob nočnem vzdrževanju je baza zaklenjena dlje od čakanja
            # (3:30, 4:25 skoraj vsako noč) -- to ni napaka pošte.
            try:
                db.set_meta(conn, "opozorila", json.dumps(stanje, sort_keys=True))
                conn.commit()
            except Exception:             # noqa: BLE001 -- naslednji obhod zapiše
                conn.rollback()           # glej `zamude_sz.teci()`
    finally:
        conn.close()
