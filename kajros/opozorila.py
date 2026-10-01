"""Opozorilo skrbniku po pošti, ko je v `/admin` kaj rdeče.

1. 10. 2026 je nit zemljevida SŽ 4,3 h stala, WAL je rasel na 5,4 GB, opazilo
pa se je šele, ko je skrbnik odprl pregled. Ob 3:30 nihče ne gleda.

Kdaj je rdeče, odloča `zdravje.ocena()` -- isto kot barve v pregledu. Pošta
gre samo za to, kar je rdeče vsaj `ZAMIK_S` (en zgrešen obhod ali ponovni
zagon ni okvara), in še enkrat, ko je vsaj `KONEC_S` spet v redu. Vmes nič:
opozorilo, ki zvoni vsako minuto, se neha brati.

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

from . import config, db, zdravje

TZ = ZoneInfo(config.TIMEZONE)

#: Toliko mora biti vrstica rdeča, preden gre pošta. Po ponovnem zagonu je
#: feed lahko do prvega branja star ~1 min, `/api/health` po omrežjih pa je
#: predpomnjen do 10 min.
ZAMIK_S = 600
#: Toliko mora biti spet v redu, preden gre „spet dela“. Brez tega bi
#: vrstica, ki niha okoli meje (2 % voženj brez voznega reda), pošiljala
#: par sporočil na vsako nihanje.
KONEC_S = 300
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


def _trajanje(s: float) -> str:
    m = round(s / 60)
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60} min"


def korak(stanje: dict, ocena: dict[str, tuple[str, str]],
          zdaj: float) -> tuple[dict, tuple[str, str] | None, list[str], list[str]]:
    """Novo stanje, sporočilo (zadeva, telo) ali None, ključi novih in rešenih.

    Stanje je `{ključ: {od, poslano, razlog, dobro_od}}`. Ključ, ki ga ni v
    sporočilu, ostane, dokler pošta ne uspe -- zato klicatelj stanja ne
    potrdi, preden pošlje.
    """
    stanje = {k: dict(v) for k, v in stanje.items()}
    slabe = {k: razlog for k, (raz, razlog) in ocena.items() if raz == zdravje.SLABA}
    for k, razlog in slabe.items():
        s = stanje.setdefault(k, {"od": zdaj, "poslano": 0})
        s["razlog"] = razlog
        s.pop("dobro_od", None)
    for k, s in stanje.items():
        if k not in slabe:
            s.setdefault("dobro_od", zdaj)

    nove = [k for k, s in stanje.items()
            if k in slabe and not s["poslano"] and zdaj - s["od"] >= ZAMIK_S]
    koncane = [k for k, s in stanje.items()
               if k not in slabe and zdaj - s["dobro_od"] >= KONEC_S]
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
            f"• {stanje[k]['razlog']} (od {_ura(stanje[k]['od'])})" for k in nove))
    if resene:
        deli.append("Spet dela:\n" + "\n".join(
            f"• {stanje[k]['razlog']} (stalo {_ura(stanje[k]['od'])}–"
            f"{_ura(stanje[k]['dobro_od'])}, {_trajanje(stanje[k]['dobro_od'] - stanje[k]['od'])})"
            for k in resene))
    if se:
        deli.append("Še vedno stoji:\n" + "\n".join(
            f"• {stanje[k]['razlog']} (od {_ura(stanje[k]['od'])})" for k in se))
    deli.append(f"{config.BASE_URL}/admin")
    zadeva = (f"kajros: stoji -- {stanje[nove[0]]['razlog']}" if nove
              else f"kajros: spet dela -- {stanje[resene[0]]['razlog']}")
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
                ocena = zdravje.ocena(beri_zdravje(), zdravje.stroj(), zdaj)
                novo, sporocilo, nove, resene = korak(stanje, ocena, zdaj)
                if sporocilo:
                    poslji(n, *sporocilo)
                    novo = _potrdi(novo, nove, resene, zdaj)
                    log(f"opozorilo poslano: {sporocilo[0]}")
                stanje = novo
                db.set_meta(conn, "opozorila", json.dumps(stanje, sort_keys=True))
                conn.commit()
                napak = 0
            except Exception as exc:      # noqa: BLE001 -- nit ne sme umreti
                conn.rollback()           # glej `zamude_sz.teci()`
                napak += 1
                if napak == 1:
                    log(f"opozorila ni bilo mogoče poslati: {exc}")
    finally:
        conn.close()
