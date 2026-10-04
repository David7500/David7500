"""Kdaj je zajem zdrav: barve vrstic „Zdravje“ v `/admin` in opozorila po pošti.

Pravila so tu in ne v `admin.js`, ker jih bereta dva: prikaz in nit, ki
skrbniku pošlje opozorilo (`opozorila.py`). Dve kopiji istih mej bi se
razšli -- in opozorilo, ki ne pove istega kot pregled, je slabše od nobenega.

Razredi so imena razredov CSS: `je-slaba` (rdeče, gre v pošto), `je-mlacna`
(rumeno), `je-dobra`, prazno = brez barve.
"""
from __future__ import annotations

import shutil
import time

from . import config

SLABA, MLACNA, DOBRA = "je-slaba", "je-mlacna", "je-dobra"

#: Ista meja kot v nogi potniških strani (`common.FEED_STALE_S`): zajem bere
#: vsakih 30 s, zato je 90 s že tretji zgrešeni obhod.
FEED_STALE_S = 90

#: Nit zemljevida SŽ bere vsako minuto; po petih minutah brez odgovora je vir
#: obstal.
SZ_STOJI_S = 300

#: Toliko voženj po voznem redu mora teči, da je molk feeda okvara.
MIN_VOZENJ = 3


def stroj() -> dict:
    """Disk in WAL -- tisto, česar baza sama o sebi ne ve."""
    raba = shutil.disk_usage(config.DATA_DIR)
    try:
        wal = config.DB_PATH.with_name(config.DB_PATH.name + "-wal").stat().st_size
    except OSError:
        wal = None
    return {"disk_prostih": raba.free, "disk_vseh": raba.total, "wal_bajtov": wal}


def _min(s: float) -> str:
    s = max(0, round(s))
    return f"{s // 60} min" if s < 5400 else f"{s / 3600:.1f} h".replace(".", ",")


def ocena(z: dict, m: dict, zdaj: float | None = None) -> dict[str, tuple[str, str]]:
    """Vrstica -> (razred, razlog). `z` je `/api/health`, `m` je `stroj()`.

    Razlog je ena vrstica za pošto; pri zdravi vrstici prazen.
    """
    zdaj = time.time() if zdaj is None else zdaj
    out: dict[str, tuple[str, str]] = {}
    mreze = z.get("by_network") or {}

    # Feed in omrežji molčijo po pravici, kadar po voznem redu nič ne vozi:
    # ponoči od ~23:30 do ~4:30 so bili trije rdeči vrstici in do 10 mailov.
    # Ena ali dve vožnji ne štejeta (kot pri `neznane` spodaj): 3. 10. 2026
    # ob 2:30 vozi po voznem redu en sam avtobus, ki ga feed ne nosi nujno.
    # `vozi_zdaj` manjka pri starem odgovoru -- takrat velja kot prej.
    vozi = z.get("vozi_zdaj")
    ponoci = vozi is not None and sum(vozi.values()) < MIN_VOZENJ

    ts = z.get("last_feed_ts")
    out["feed"] = (("", "") if ponoci
                   else (SLABA, "nobene zamude iz feeda") if not ts
                   else (SLABA, f"zadnja zamuda iz feeda pred {_min(zdaj - ts)}")
                   if zdaj - ts > FEED_STALE_S else (DOBRA, ""))

    # Po omrežjih je `/api/health` predpomnjen do 10 min, zato meja 20 min --
    # sicer bi predpomnilnik sam prižgal rdečo.
    for kljuc, ime in (("zeleznica", "vlaki"), ("avtobus", "avtobusi")):
        ts = (mreze.get(kljuc) or {}).get("last_feed_ts")
        if vozi is not None and vozi.get(kljuc, 0) < MIN_VOZENJ:
            out[kljuc] = ("", "")
        elif not ts:
            out[kljuc] = (SLABA, f"{ime}: nobenega zapisa")
        elif zdaj - ts < 1200:
            out[kljuc] = (DOBRA, "")
        else:
            out[kljuc] = (MLACNA if zdaj - ts < 3600 else SLABA,
                          f"{ime}: zadnji zapis pred {_min(zdaj - ts)}")

    # Vožnje iz feeda, ki jih vozni red ne pozna, zajem zavrže. 22. 9. 2026 jih
    # je bilo 16 od 662 (2,4 %) -- tri linije LPP brez vsake zamude; ostanek
    # po popravku na arwenu 5 od 538 (0,9 %).
    #
    # Rdeče šele pri vsaj treh vožnjah IN 2 %, kot spodaj pri legi. 28. 9. 2026
    # ob 23:42 je bila vsa stran rdeča zaradi ene same vožnje: Nomagov N0152,
    # nagrobnik brez voznega reda, ki ga feed še nosi -- 1 od 29, ker ponoči
    # vozi malo voženj. Podnevi bi bila ista vožnja 1 od ~600.
    nez = z.get("rt_neznanih") or {}
    if nez:
        slabi = [f"{vir.upper()} {n} od {vseh}" for vir, (n, vseh) in nez.items()
                 if n >= 3 and vseh and n / vseh >= 0.02]
        out["neznane"] = ((SLABA, "vožnje brez voznega reda: " + ", ".join(slabi)) if slabi
                          else (MLACNA, "") if any(n > 0 for n, _ in nez.values())
                          else (DOBRA, ""))

    # Obratno: vozilo vozi in ima lego, feed zamud pa ga ne nosi. Od 21. do
    # 25. 9. 2026 ~430 Nomagovih voženj na dan, števec zgoraj pa zelen. Na
    # vožnjah, ki jih feed nosi, je bilo takih 0 od 295. Trojka je [ne v feedu,
    # brez zamude, vseh]: `iz_lege` vrzel zapolni, zato je napaka vira rumena,
    # rdeče pa je šele to, kar vidi potnik -- vozilo brez vsake zamude.
    #
    # Rdeče šele pri vsaj treh vozilih IN 5 % prevoznika. Po zapolnitvi ostane
    # nekaj voženj, ki so odpeljale pozno in še niso prevozile drugega
    # postanka (izhodišča `iz_lege` ne meri): 25. 9. po objavi Nomago 1-2 od
    # ~100, takoj po restartu 5 od 104 (4,8 %), preden je `iz_lege` dohitel.
    # Samo z deležem 2 % je bila vrstica -- in s tem vsa stran -- rdeča zaradi
    # dveh avtobusov. Pred zapolnitvijo je bilo 8 od 91 (8,8 %).
    lbz = z.get("lega_brez_zamude")
    if lbz is not None:
        vidni = {ime: v for ime, v in lbz.items() if v[0] > 0 or v[1] > 0}
        slabi = [f"{ime} {nz} od {vseh}" for ime, (_, nz, vseh) in vidni.items()
                 if nz >= 3 and vseh and nz / vseh >= 0.05]
        out["lega_brez_zamude"] = (
            (SLABA, "vozila brez vsake zamude: " + ", ".join(slabi)) if slabi
            else (MLACNA, "") if vidni else (DOBRA, ""))

    # Dva vira zamud vlakov (`zamude_sz`). 28. 9. 2026 je derp.si z voznim
    # redom DUJPP izgubil vse vlake, zemljevid SŽ jih je imel. Rumeno, kadar
    # manjka eden od virov -- zamude so, a le iz enega; kadar ni nobenega,
    # je rdeča že vrstica „vlaki · zadnji zapis“.
    #
    # Rdeče pa, kadar stoji NIT, ne vir. Ko vir ne odgovarja, nit ob vsakem
    # poskusu zapiše `napaka_ts`; 1. 10. 2026 je obstala v transakciji in ni
    # mogla zapisati ničesar -- 4,3 h je bila vrstica le rumena.
    zs = z.get("zamude_sz")
    if zs:
        zadnji = zs.get("ts") or 0
        if zdaj - zadnji > SZ_STOJI_S:
            napaka = zs.get("napaka_ts") or 0
            out["zamude_sz"] = (
                (MLACNA, "") if zdaj - napaka <= SZ_STOJI_S
                else (SLABA, f"nit zemljevida SŽ ne piše od pred {_min(zdaj - zadnji)}"))
        elif not zs.get("oba") and (zs.get("samo_sz") or zs.get("samo_derp")):
            out["zamude_sz"] = (MLACNA, "")
        else:
            out["zamude_sz"] = (DOBRA, "") if zs.get("oba") else ("", "")

    if m.get("disk_vseh"):
        delez = m["disk_prostih"] / m["disk_vseh"]
        out["disk"] = ((SLABA, f"prostora na disku le {100 * delez:.0f} %") if delez < 0.08
                       else (MLACNA, "") if delez < 0.2 else (DOBRA, ""))

    # Z `journal_size_limit` (db.connect) se WAL po vsakem prepisu skrči na
    # 64 MB. Večji pomeni, da prepisa ni bilo -- kdo drži star posnetek. Tako
    # je 1. 10. 2026 zrasel na 5,4 GB.
    wal = m.get("wal_bajtov")
    if wal is not None:
        mb = wal / 2**20
        out["wal"] = ((SLABA, f"WAL {mb:.0f} MB -- prepis v bazo ne teče") if mb > 1024
                      else (MLACNA, "") if mb > 256 else (DOBRA, ""))
    return out
