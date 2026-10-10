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
from datetime import date, datetime
from zoneinfo import ZoneInfo

from . import brskalnik, config, viri

TZ = ZoneInfo(config.TIMEZONE)

SLABA, MLACNA, DOBRA = "je-slaba", "je-mlacna", "je-dobra"

#: Ista meja kot v nogi potniških strani (`common.FEED_STALE_S`): zajem bere
#: vsakih 30 s, zato je 90 s že tretji zgrešeni obhod.
FEED_STALE_S = 90

#: Nit zemljevida SŽ bere na 30 s; po petih minutah brez odgovora je vir
#: obstal.
SZ_STOJI_S = 300

#: Zemljevid SŽ se ob vlakih na poti spremeni ob vsakem branju (10. 10. 2026:
#: 93 od 93 zaporednih branj po 15 s -- odšteva čas do prihoda). Deset minut
#: brez spremembe je zamrznjen odgovor, ne miren promet.
SZ_ZAMRZNJEN_S = 600

#: Toliko voženj po voznem redu mora teči, da je molk feeda okvara.
MIN_VOZENJ = 3

#: derp.si se bere na 30 s; pet minut brez odgovora je deset zgrešenih branj.
DERP_MOLCI_S = 300

#: Nit LPP-jevih zaslonov obhod začne vsaki 2 min, obhod sam traja do ~1 min
#: (8. 10. 2026: 75 postajališč 36 s). Četrt ure brez zapisa je obstala nit.
LPP_STOJI_S = 900

#: Nit NAP bere na 10 s, ob zavrnjeni prijavi na 10 min (`nap.NI_DOSTOPA_CAKAJ_S`):
#: v tem času mora zapisati vsaj napako, sicer stoji.
NAP_STOJI_S = 900

#: Vozni red IJPP sega mesece naprej; teden pred koncem je čas, da se ve,
#: dva dni pred koncem je okvara (jutri ali pojutrišnjem ni voženj).
VOZNI_RED_RUMENO_DNI, VOZNI_RED_RDECE_DNI = 7, 2


def _rss() -> int | None:
    """Pomnilnik procesa v bajtih (Linux). Malina in arwen imata ga malo."""
    try:
        with open("/proc/self/status", encoding="ascii") as fh:
            for vrstica in fh:
                if vrstica.startswith("VmRSS:"):
                    return int(vrstica.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def stroj() -> dict:
    """Tisto, česar baza sama o sebi ne ve: disk, WAL, pomnilnik, niti,
    dnevnik branj virov (`viri.py`) in Chrome za potniski.sz.si -- vse to
    živi le v tem procesu."""
    raba = shutil.disk_usage(config.DATA_DIR)
    try:
        wal = config.DB_PATH.with_name(config.DB_PATH.name + "-wal").stat().st_size
    except OSError:
        wal = None
    return {"disk_prostih": raba.free, "disk_vseh": raba.total, "wal_bajtov": wal,
            "rss_bajtov": _rss(), "niti": viri.niti(),
            "pricakovane_niti": viri.pricakovane_niti(), "viri": viri.dnevnik(),
            "brskalnik": brskalnik.stanje()}


def _min(s: float) -> str:
    s = max(0, round(s))
    return f"{s // 60} min" if s < 5400 else f"{s / 3600:.1f} h".replace(".", ",")


def _ura(ts: float) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M")


def _do(dni: int, d: date) -> str:
    return (f"se je končal {d.day}. {d.month}." if dni < 0
            else f"znan le do {d.day}. {d.month}.")


def ocena(z: dict, m: dict, zdaj: float | None = None) -> dict[str, tuple[str, str]]:
    """Vrstica -> (razred, razlog). `z` je `/api/health`, `m` je `stroj()`.

    Razlog je ena vrstica: pri rdeči gre v pošto, pri rumeni ga pokaže le
    pregled, pri zdravi je prazen.
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
        vse = [f"{vir.upper()} {n} od {vseh}" for vir, (n, vseh) in nez.items() if n > 0]
        out["neznane"] = ((SLABA, "vožnje brez voznega reda: " + ", ".join(slabi)) if slabi
                          else (MLACNA, "vožnje brez voznega reda: " + ", ".join(vse)) if vse
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
            else (MLACNA, "vozila brez feeda zamud, zamudo meri lega: " + ", ".join(
                f"{ime} {nf} od {vseh}" for ime, (nf, _, vseh) in vidni.items()))
            if vidni else (DOBRA, ""))

    # Zemljevid SŽ (`zamude_sz`) vodi zamude vlakov. Rdeče, kadar stoji NIT:
    # ko vir ne odgovarja, nit ob vsakem poskusu zapiše `napaka_ts`; 1. 10. 2026
    # je obstala v transakciji in ni mogla zapisati ničesar -- 4,3 h je bila
    # vrstica le rumena. Ko vir ne odgovarja, je rumeno: vlake medtem piše
    # derp.si, kolikor jih ima, vrstica „vlaki · zadnji zapis“ pa pove, ali sploh.
    zs = z.get("zamude_sz")
    if zs:
        zadnji = zs.get("ts") or 0
        vozijo = vozi is None or vozi.get("zeleznica", 0) >= MIN_VOZENJ
        if zdaj - zadnji > SZ_STOJI_S:
            napaka = zs.get("napaka_ts") or 0
            out["zamude_sz"] = (
                (MLACNA, f"zemljevid SŽ ne odgovarja od pred {_min(zdaj - zadnji)}"
                         + (f": {zs['napaka']}" if zs.get("napaka") else ""))
                if zdaj - napaka <= SZ_STOJI_S
                else (SLABA, f"nit zemljevida SŽ ne piše od pred {_min(zdaj - zadnji)}"))
        elif vozijo and zdaj - (zs.get("spremenjeno_ts") or zadnji) > SZ_ZAMRZNJEN_S:
            out["zamude_sz"] = (MLACNA, "zemljevid SŽ se ne spreminja od pred "
                                        f"{_min(zdaj - zs['spremenjeno_ts'])}")
        elif vozijo and vozi is not None and not zs.get("vlakov"):
            out["zamude_sz"] = (MLACNA, f"zemljevid SŽ je prazen, po voznem redu "
                                        f"vozi {vozi['zeleznica']} vlakov")
        else:
            out["zamude_sz"] = (DOBRA, "")

    # derp.si po viru. 8. 10. 2026 je od 16:00 zavračal povezave; vrstici
    # zgoraj sta ostali zeleni, kolikor sta `zamude_lpp` in `zamude_sz` pisala
    # v `run` -- zato posebej, kdaj je derp.si sam nazadnje odgovoril. Vsak
    # vir svoja vrstica: pregled ju kaže na dveh karticah (`viri.py`).
    dp = z.get("derp_prebran")
    if dp is not None and not (vozi is not None and vozi.get("avtobus", 0) < MIN_VOZENJ):
        for vir, ts in sorted(dp.items()):
            out[f"derp_{vir}"] = (
                (SLABA, f"derp.si ({vir.upper()}) ne odgovarja od pred {_min(zdaj - ts)}")
                if zdaj - ts > DERP_MOLCI_S else (DOBRA, ""))

    # Mestni LPP z LPP-jevih zaslonov (`zamude_lpp`), kot zemljevid SŽ zgoraj:
    # rdeče, kadar stoji nit, rumeno, kadar ne odgovarja vir.
    zl = z.get("zamude_lpp")
    if zl:
        if vozi is not None and vozi.get("avtobus", 0) < MIN_VOZENJ:
            out["zamude_lpp"] = ("", "")
        elif zdaj - (zl.get("ts") or 0) > LPP_STOJI_S:
            napaka = zl.get("napaka_ts") or 0
            out["zamude_lpp"] = (
                (MLACNA, f"LPP-jevi zasloni ne odgovarjajo od pred "
                         f"{_min(zdaj - (zl.get('ts') or 0))}")
                if zdaj - napaka <= LPP_STOJI_S
                else (SLABA, f"nit LPP-jevih zaslonov ne piše od pred {_min(zdaj - (zl.get('ts') or 0))}"))
        else:
            out["zamude_lpp"] = (DOBRA, "") if zl.get("oba") or zl.get("samo_lpp") else ("", "")

    # Lege IJPP z NAP (`nap.py`). Zavrnjena prijava je rumena: dostop čaka
    # na odobritev ali novo geslo, pošta tu ne pomaga. Rdeče, kadar stoji nit.
    nm = z.get("nap")
    if nm:
        if nm.get("http") and zdaj - (nm.get("napaka_ts") or 0) <= NAP_STOJI_S:
            out["nap"] = (MLACNA, f"NAP zavrnil prijavo (HTTP {nm['http']})")
        elif vozi is not None and vozi.get("avtobus", 0) < MIN_VOZENJ:
            out["nap"] = ("", "")
        elif zdaj - (nm.get("ts") or 0) > NAP_STOJI_S:
            napaka = nm.get("napaka_ts") or 0
            out["nap"] = (
                (MLACNA, f"NAP ne odgovarja od pred {_min(zdaj - (nm.get('ts') or 0))}")
                if zdaj - napaka <= NAP_STOJI_S
                else (SLABA, f"nit NAP ne piše od pred {_min(zdaj - (nm.get('ts') or 0))}"))
        else:
            out["nap"] = (DOBRA, "")

    # Vozni red, ki se konča. Uvoz ob 4:20 premakne okno LPP vsak dan za dan
    # naprej (`config.LPP_DAYS`); če ne teče, mestne linije čez teden dni
    # izginejo z vseh strani brez ene same napake v dnevniku -- tako je bilo
    # na razvojnem računalniku. Brez meritve: meja je posledica, ne šum.
    vr = z.get("vozni_red")
    if vr:
        danes = datetime.fromtimestamp(zdaj, TZ).date()
        for kljuc, deli, rumeno in (
                ("vozni_red", (("zeleznica", "vlakov"), ("avtobus", "avtobusov")),
                 VOZNI_RED_RUMENO_DNI),
                ("vozni_red_lpp", (("lpp", "mestnega LPP"),), config.LPP_DAYS - 2)):
            slabi, mlacni = [], []
            for omr, ime in deli:
                if not vr.get(omr):
                    continue
                d = date.fromisoformat(vr[omr])
                dni = (d - danes).days
                if dni < VOZNI_RED_RDECE_DNI:
                    slabi.append(f"vozni red {ime} {_do(dni, d)}")
                elif dni < rumeno:
                    mlacni.append(f"vozni red {ime} {_do(dni, d)}")
            if any(vr.get(omr) for omr, _ in deli):
                out[kljuc] = ((SLABA, ", ".join(slabi)) if slabi
                              else (MLACNA, ", ".join(mlacni)) if mlacni else (DOBRA, ""))

    # Nit, ki je umrla, ne vstane do ponovnega zagona: izjema mimo `except`
    # v zanki ali napaka ob zagonu. Vir je bil tedaj viden le posredno („ne
    # piše“), tir s table SŽ pa sploh ne.
    zive = set(m.get("niti") or ())
    for nit, kljuci in (m.get("pricakovane_niti") or {}).items():
        out[f"nit:{nit}"] = ((DOBRA, "") if nit in zive
                             else (SLABA, f"nit {nit} ne teče ({', '.join(kljuci)})"))

    # Viri brez svojega pravila: rumeno, kadar zadnjih nekaj branj ni uspelo.
    # Samo rumeno -- teh meja nismo merili, pošta pa mora pomeniti okvaro.
    for v in viri.vsi():
        d = (m.get("viri") or {}).get(v.kljuc)
        if v.zdravje or not v.vklopljen or not d:
            continue
        if d["zaporednih"] >= v.prag_napak:
            out[f"vir:{v.kljuc}"] = (MLACNA, f"{v.ime}: {d['napaka']} "
                                             f"(od {_ura(d['izpad_od'] or d['napaka_ts'])})")
        elif d["uspeh_ts"]:
            out[f"vir:{v.kljuc}"] = (DOBRA, "")

    if m.get("disk_vseh"):
        delez = m["disk_prostih"] / m["disk_vseh"]
        out["disk"] = ((SLABA, f"prostora na disku le {100 * delez:.0f} %") if delez < 0.08
                       else (MLACNA, f"prostora na disku {100 * delez:.0f} %") if delez < 0.2
                       else (DOBRA, ""))

    # Z `journal_size_limit` (db.connect) se WAL po vsakem prepisu skrči na
    # 64 MB. Večji pomeni, da prepisa ni bilo -- kdo drži star posnetek. Tako
    # je 1. 10. 2026 zrasel na 5,4 GB.
    wal = m.get("wal_bajtov")
    if wal is not None:
        mb = wal / 2**20
        out["wal"] = ((SLABA, f"WAL {mb:.0f} MB -- prepis v bazo ne teče") if mb > 1024
                      else (MLACNA, f"WAL {mb:.0f} MB") if mb > 256 else (DOBRA, ""))
    return out
