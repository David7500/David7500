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
from dataclasses import dataclass
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

#: Ko Chrome ne pride skozi Cloudflare, poskusi znova šele po
#: `PO_NAPAKI_ZAGONA_S`, poskus sam pa traja do zagona, izziva in zahteve --
#: `napaka_ts` je čas začetka poskusa. 14. 10. 2026 od 1:39 do 3:59 je bila
#: napaka vsakih 6,5 min, starejša od `SZ_STOJI_S`, in vrstica je kazala
#: „nit ne piše“ (pošta), čeprav je nit pisala napake po pravici.
SZ_NAPAKA_S = (brskalnik.PO_NAPAKI_ZAGONA_S
               + 2 * (brskalnik.ZAGON_S + brskalnik.PREBOJ_S + brskalnik.ZAHTEVA_S))

#: Zemljevid SŽ se ob vlakih na poti spremeni ob vsakem branju (10. 10. 2026:
#: 93 od 93 zaporednih branj po 15 s -- odšteva čas do prihoda). Deset minut
#: brez spremembe je zamrznjen odgovor, ne miren promet.
SZ_ZAMRZNJEN_S = 600

#: Straža zemljevida SŽ (`zamude_sz.skladnost`): delež ustaljenih primerjav,
#: pri katerih je meja meritve od SŽ za 3 min ali več. Stara koda 2,3--4,1 %,
#: nova 0 (glej `ocena`). Pod `SKLADNOST_NAJMANJ` primerjav (ponoči, po
#: zagonu) ne sodimo: podnevi jih je v pol ure ~4 000.
SKLADNOST_RDECE, SKLADNOST_RUMENO = 0.01, 0.003
SKLADNOST_NAJMANJ = 300

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
#: Včerajšnji dan se obdela ponoči; dva dni nazaj je ena izpadla noč.
OPAZOVANO_NAJVEC_DNI = 2

#: Niti mestnih virov (Marprom, Kranj) pišeta na 10 s; pet minut tišine ni
#: več zamujeno branje.
MARPROM_STOJI_S = 300
#: Vozila brez vožnje v mestu: rumeno od toliko vozil in deleža. 27. 10.
#: 2026 ob 11:00 4 od 36 (3 brez prihoda, 1 brez ure v voznem redu).
MARPROM_BREZ, MARPROM_BREZ_DELEZ = 5, 0.3


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


def _skladnost(sk: dict, n: int, mimo: int) -> str:
    return (f"prikaz se s SŽ ne ujema pri {100 * mimo / n:.1f} % primerjav "
            f"({mimo} od {n}, {sk.get('vlakov', 0)} vlakov, prenizko {sk.get('prenizko', 0)}, "
            f"previsoko {sk.get('previsoko', 0)}): " + ", ".join(sk.get("primeri") or []))


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

    # Zjutraj molk šteje šele od začetka prometa (`stats.promet_od`), ne od
    # zadnjega nočnega zapisa: ob 3:58 je bil zadnji zapis vlakov iz 1:22 in
    # vrstica rdeča, čeprav prvi vlaki po voznem redu vozijo šele od 3:20.
    jutro = z.get("promet_od") or {}

    ts = z.get("last_feed_ts")
    # Feed je karkoli: šteje začetek omrežja, ki je začelo prvo.
    zacetek = min(jutro.values(), default=0)
    out["feed"] = (("", "") if ponoci
                   else (SLABA, "nobene zamude iz feeda") if not ts
                   else (SLABA, f"zadnja zamuda iz feeda pred {_min(zdaj - ts)}")
                   if zdaj - max(ts, zacetek) > FEED_STALE_S else (DOBRA, ""))

    # Sveže iz `svezina`, kadar je omrežje v zadnji uri kaj zapisalo; sicer iz
    # predpomnjenih števcev, ki pa takrat ne morejo biti novejši od ure.
    # Meja 20 min je ostala od časa, ko so bili števci edini vir.
    svezina = z.get("svezina") or {}
    for kljuc, ime in (("zeleznica", "vlaki"), ("avtobus", "avtobusi")):
        ts = svezina.get(kljuc) or (mreze.get(kljuc) or {}).get("last_feed_ts")
        if vozi is not None and vozi.get(kljuc, 0) < MIN_VOZENJ:
            out[kljuc] = ("", "")
        elif not ts:
            out[kljuc] = (SLABA, f"{ime}: nobenega zapisa")
        elif (molk := zdaj - max(ts, jutro.get(kljuc, 0))) < 1200:
            out[kljuc] = (DOBRA, "")
        else:
            out[kljuc] = (MLACNA if molk < 3600 else SLABA,
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
    #
    # Rumena vrstica pove obe števili, vsako le, kadar ni nič. Do 14. 10. 2026
    # je kazala samo prvo, ki je pri prevoznikih NAP vedno 0 (vir zamud je
    # lega sama), prižgalo pa jo je drugo: „Nomago 0 od 160“.
    lbz = z.get("lega_brez_zamude")
    if lbz is not None:
        vidni = {ime: v for ime, v in lbz.items() if v[0] > 0 or v[1] > 0}
        slabi = [f"{ime} {nz} od {vseh}" for ime, (_, nz, vseh) in vidni.items()
                 if nz >= 3 and vseh and nz / vseh >= 0.05]

        def stevilo(i: int) -> str:
            return ", ".join(f"{ime} {v[i]} od {v[2]}" for ime, v in vidni.items() if v[i])
        brez, mimo = stevilo(1), stevilo(0)
        out["lega_brez_zamude"] = (
            (SLABA, "vozila brez vsake zamude: " + ", ".join(slabi)) if slabi
            else (MLACNA, "; ".join(x for x in (
                brez and "vozila brez zamude: " + brez,
                mimo and "feed zamud jih ne nosi, zamudo meri lega: " + mimo) if x))
            if vidni else (DOBRA, ""))

    # Zemljevid SŽ (`zamude_sz`) vodi zamude vlakov. Rdeče, kadar stoji NIT:
    # ko vir ne odgovarja, nit ob vsakem poskusu zapiše `napaka_ts`; 1. 10. 2026
    # je obstala v transakciji in ni mogla zapisati ničesar -- 4,3 h je bila
    # vrstica le rumena. Ko vir ne odgovarja, je rumeno: vlake medtem piše
    # derp.si, kolikor jih ima, vrstica „vlaki · zadnji zapis“ pa pove, ali sploh.
    # Ponoči, ko vlaki ne vozijo, je tudi obstala nit le rumena: zamud ni
    # komu kazati, zjutraj pa je z voznim redom spet rdeča.
    zs = z.get("zamude_sz")
    if zs:
        zadnji = zs.get("ts") or 0
        vozijo = vozi is None or vozi.get("zeleznica", 0) >= MIN_VOZENJ
        if zdaj - zadnji > SZ_STOJI_S:
            napaka = zs.get("napaka_ts") or 0
            out["zamude_sz"] = (
                (MLACNA, f"zemljevid SŽ ne odgovarja od pred {_min(zdaj - zadnji)}"
                         + (f": {zs['napaka']}" if zs.get("napaka") else ""))
                if zdaj - napaka <= SZ_NAPAKA_S
                else ((SLABA if vozijo else MLACNA),
                      f"nit zemljevida SŽ ne piše od pred {_min(zdaj - zadnji)}"))
        elif vozijo and zdaj - (zs.get("spremenjeno_ts") or zadnji) > SZ_ZAMRZNJEN_S:
            out["zamude_sz"] = (MLACNA, "zemljevid SŽ se ne spreminja od pred "
                                        f"{_min(zdaj - zs['spremenjeno_ts'])}")
        elif vozijo and vozi is not None and not zs.get("vlakov"):
            out["zamude_sz"] = (MLACNA, f"zemljevid SŽ je prazen, po voznem redu "
                                        f"vozi {vozi['zeleznica']} vlakov")
        else:
            out["zamude_sz"] = (DOBRA, "")

        # Straža (`zamude_sz.skladnost`): ali to, kar kažemo, drži s tem, kar
        # SŽ pravi. Vir je od 11. do 16. 10. 2026 odgovarjal in vrstica zgoraj
        # je bila zelena, prikaz pa je bil pri 611 od 1 444 voženj z zamudo
        # prenizek. Ponovitev 25 min zemljevida skozi staro kodo: mimo 2,3 do
        # 4,1 % ustaljenih primerjav, skozi novo 0 od 3 381. Rdeče pri 1 % in
        # treh vlakih -- en sam vlak je posebnost, ne okvara zajema.
        sk = zs.get("skladnost") or {}
        n = sk.get("primerjav") or 0
        mimo = (sk.get("prenizko") or 0) + (sk.get("previsoko") or 0)
        if n < SKLADNOST_NAJMANJ:
            out["skladnost_sz"] = ("", "")
        elif mimo / n >= SKLADNOST_RDECE and (sk.get("vlakov") or 0) >= 3:
            out["skladnost_sz"] = (SLABA, _skladnost(sk, n, mimo))
        elif mimo / n >= SKLADNOST_RUMENO:
            out["skladnost_sz"] = (MLACNA, _skladnost(sk, n, mimo))
        else:
            out["skladnost_sz"] = (DOBRA, "")

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

    # Mestna vira v živo (`marprom.py`, `kranj.py`). Rumeno, ko vir ne
    # odgovarja (drugega ni) ali ko velik del vozil ostane brez vožnje -- vozni
    # red se z njihovimi vožnjami ne ujema; rdeče samo, ko stoji nit.
    for kljuc, ime in (("marprom", "Marprom"), ("kranj", "Kranj")):
        mm = z.get(kljuc)
        if not mm:
            continue
        po_vr = mm.get("po_voznem_redu") or 0
        vozil, brez = mm.get("vozil") or 0, mm.get("brez_voznje") or 0
        if zdaj - (mm.get("ts") or 0) > MARPROM_STOJI_S:
            napaka = mm.get("napaka_ts") or 0
            out[kljuc] = (
                (MLACNA, f"{ime} ne odgovarja od pred {_min(zdaj - (mm.get('ts') or 0))}")
                if zdaj - napaka <= MARPROM_STOJI_S
                else (SLABA, f"nit ({ime}) ne piše od pred {_min(zdaj - (mm.get('ts') or 0))}"))
        elif po_vr < MIN_VOZENJ and not vozil:
            out[kljuc] = ("", "")
        elif not vozil:
            out[kljuc] = (MLACNA, f"{ime}: nobenega vozila, po voznem redu jih vozi {po_vr}")
        elif brez >= MARPROM_BREZ and brez >= MARPROM_BREZ_DELEZ * vozil:
            out[kljuc] = (MLACNA, f"vozila brez vožnje: {brez} od {vozil}")
        else:
            out[kljuc] = (DOBRA, "")

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

    # Mestni vozni redi (`gtfs.download_mestni`): do kdaj velja zip, ki ga
    # uvoz res vzame, in ali je to izvirnik. Uradni zip Marproma od 5. 10. 2026
    # ne pokrije tedna -- uvoz vzame kopijo, potnik ne izgubi nič; rumeno, da
    # skrbnik ve, komu pisati. `rok` = kdaj se konča prva vrsta dne: pri kopiji
    # delavniki 31. 12. 2026, `do` pa šele 20. 6. 2027.
    danes = datetime.fromtimestamp(zdaj, TZ).date()
    for kljuc, mv in (z.get("mestni_vozni_red") or {}).items():
        vrstica, viri_ = f"vozni_red_{kljuc}", mv.get("viri") or []
        d = None
        if mv.get("do"):
            d = date.fromisoformat(mv.get("rok") or mv["do"])
            dni = (d - danes).days
            if dni < VOZNI_RED_RDECE_DNI:
                out[vrstica] = (SLABA, f"vozni red {_do(dni, d)}")
                continue
            if dni < VOZNI_RED_RUMENO_DNI:
                out[vrstica] = (MLACNA, f"vozni red {_do(dni, d)}")
                continue
        uradni = viri_[0] if viri_ else None
        if uradni and not uradni.get("sprejet"):
            zakaj = (uradni["napaka"] if uradni.get("napaka") else
                     f"{sum(1 for n in uradni.get('pokrito') or () if not n)} od "
                     f"{len(uradni.get('pokrito') or ())} dni brez voženj")
            kopija = any(v.get("sprejet") for v in viri_[1:])
            out[vrstica] = (MLACNA, f"uradni zip ne pokrije tedna ({zakaj}); "
                            + ("velja kopija" if kopija else "ostane zadnji sprejeti")
                            + (f", del voznih redov se konča {d.day}. {d.month}."
                               if d and mv.get("rok") and mv["rok"] != mv["do"] else ""))
        elif mv.get("do"):
            out[vrstica] = (DOBRA, "")

    # Prikaz bere nočni račun (`opazovano.py`). Stare trditve po tednu odpadejo same,
    # skrbnik naj izve prej. Samo rumeno: potnik ne dobi napačnega, le zastarelo.
    if z.get("opazovano_dan"):
        dni = (danes - date.fromisoformat(z["opazovano_dan"])).days
        out["opazovano"] = ((MLACNA, f"nočni račun stoji, zadnji dan {dni} dni nazaj")
                            if dni > OPAZOVANO_NAJVEC_DNI else (DOBRA, ""))

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


# --- pošta: samo kar rabi skrbnikov poseg ----------------------------------
#
# Rdeča vrstica pove, da potnik nekaj izgubi; pošta mora povedati, da mora
# skrbnik nekaj NAREDITI. Ni isto: od 1. do 17. 10. 2026 je šlo 67 pošt
# „stoji“, od tega 31 „vozila brez vsake zamude“ (3–8 vozil, nihanje),
# 11 „vlaki: zadnji zapis“ ob 3:58 (nočni povzetki), 7 „vožnje brez voznega
# reda“ LPP (obvozi za maraton) in 2 „prikaz proti SŽ“ (SŽ je vlak risal po
# voznem redu) -- pri nobeni od teh skrbnik ni mogel nič. David, 17. 10.:
# „na mail moram dobiti le, kadar stoji in rabim jaz posredovati“.

#: Imena vrstic v pošti (pregled ima svoja, ob vrsticah tabel).
IMENA = {
    "feed": "zajem · zadnja zamuda v bazi",
    "zeleznica": "vlaki · zadnji zapis",
    "avtobus": "avtobusi · zadnji zapis",
    "neznane": "vožnje brez voznega reda",
    "lega_brez_zamude": "vozila brez zamude",
    "zamude_sz": "zemljevid SŽ",
    "skladnost_sz": "vlaki · prikaz proti SŽ",
    "derp_ijpp": "derp.si · IJPP",
    "derp_lpp": "derp.si · mestni LPP",
    "zamude_lpp": "LPP · zasloni postajališč",
    "nap": "NAP · lege SIRI",
    "vozni_red": "vozni red IJPP",
    "vozni_red_lpp": "vozni red LPP",
    "marprom": "Marprom · vozila",
    "kranj": "Kranj · vozila",
    "vozni_red_marprom": "vozni red Marprom",
    "vozni_red_kranj": "vozni red Kranj",
    "vozni_red_ms": "vozni red MS (mestni)",
    "opazovano": "opazovano · nočni račun",
    "disk": "disk",
    "wal": "WAL",
}


def ime(kljuc: str) -> str:
    if kljuc.startswith("nit:"):
        return f"nit {kljuc[4:]}"
    if kljuc.startswith("vir:"):
        v = viri.po_kljucu().get(kljuc[4:])
        return v.ime if v else kljuc
    return IMENA.get(kljuc, kljuc)


@dataclass(frozen=True)
class Okvara:
    razlog: str
    #: Kaj naj skrbnik naredi -- brez tega pošta ni ukrep, ampak novica.
    ukrep: str
    #: Toliko mora okvara trajati, preden gre pošta.
    po_s: int = 600


_RESTART = "Na arwenu `sudo systemctl restart kajros.service`, vzrok v `journalctl -u kajros.service`."
_ZAJEM = ("Spodaj piše, ali viri odgovarjajo. Če odgovarjajo, stoji pri nas: " + _RESTART
          + " Če ne, je izpad pri viru; obvestilo potnikom nastane samo po 20 min.")

#: Vrstica -> (ukrep, po koliko sekund rdečega). Vrstic, ki jih tu ni, v
#: pošti ni: izpad zunanjega vira, ki ima rezervo, kakovost, ki je skrbnik
#: ne more popraviti, splošno pravilo virov (`vir:*`).
_POSTA: dict[str, tuple[str, int]] = {
    "feed": (_ZAJEM, 600),
    "zeleznica": (_ZAJEM + " Pri vlakih poglej še vrstico „zemljevid SŽ“ in brskalnik.", 600),
    "avtobus": (_ZAJEM, 600),
    "zamude_sz": ("Nit zemljevida SŽ ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "zamude_lpp": ("Nit LPP-jevih zaslonov ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "nap": ("Nit NAP ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "marprom": ("Nit Marproma ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "kranj": ("Nit Kranja ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    # Straža prikaza proti SŽ: vlakov, ki jih SŽ riše po voznem redu, ne šteje
    # (`zamude_sz.skladnost`), zato pol ure rdečega pomeni napako pri nas --
    # potnik vidi napačno zamudo in to popravi samo koda.
    "skladnost_sz": ("Prikaz zamud vlakov se pri več vlakih ne ujema s SŽ. Napaka je pri "
                     "nas (meja meritve, zapis v `run`), ne pri SŽ; primeri so v vrstici. "
                     "Za popravek odpri sejo s Claude.", 1800),
    "disk": ("Na arwenu `df -h /var/lib/kajros`; največ prostora vzameta `promet.sqlite` "
             "in varnostne kopije.", 600),
    "wal": ("Prepis WAL v bazo ne teče -- kdo drži star posnetek. " + _RESTART, 600),
}
_NIT = ("Nit je umrla in ne vstane do ponovnega zagona. " + _RESTART, 600)

#: Vrstice, ki ponoči (nič ne vozi) nimajo ocene. Takrat pošta ne ve, ali je
#: okvara mimo, zato ne pošlje ne „stoji“ ne „spet dela“: obstala nit ob
#: 23:50 bi sicer ob 0:35 dobila „spet dela“ in ob 4:00 znova „stoji“.
_PO_VOZNEM_REDU = frozenset({"feed", "zeleznica", "avtobus", "zamude_sz", "zamude_lpp", "nap",
                             "marprom", "kranj", "skladnost_sz"})

#: Vožnje IJPP brez voznega reda gredo v pošto šele, ko jih je veliko:
#: 22. 9. 2026 (nov vozni red, stari id-ji v feedu) 16 od 662 = 2,4 %,
#: popravilo je rabilo kodo (`zamenjava`). Mestni LPP nikoli: njegov živi
#: sistem vozi mimo objavljenega voznega reda (1. in 2. 10. 2026, maraton
#: 16. 10.), skrbnik pri tem ne more nič.
NEZNANE_POSTA, NEZNANE_POSTA_DELEZ = 5, 0.02

#: Vozila brez vsake zamude: pošta šele, ko izpeljava zamud iz leg odpove za
#: velik del prevoznika. Ponovitev 14.–17. 10. 2026 po minutah: pri sedanji
#: rdeči (3 vozila, 5 %) 5 pošt v treh dneh, vse zaradi resnice na cesti
#: (odhod 30–120 min pozno, zastoj ob zapori za maraton, izpad interneta);
#: pri 10 vozilih in 25 % nobene, prava okvara (prehod ne piše) pa doseže
#: prag v 9–24 min. Vrhovi po vrzeli leg NAP (do 71 %) trajajo do 5 min.
BREZ_ZAMUDE_POSTA, BREZ_ZAMUDE_POSTA_DELEZ = 10, 0.25

#: derp.si ima za vse rezervo (NAP, LPP-jevi zasloni, zemljevid SŽ), razen
#: primestnega LPP. Izpad pri njih skrbnik ne popravi; dan molka pa je lahko
#: trajna sprememba, o kateri je treba odločiti.
DERP_DOLGO_S = 86400

#: NAP, ki zavrača prijavo, se ne popravi sam: novo geslo ali odobritev.
NAP_PRIJAVA_S = 3600


def posta(z: dict, m: dict, ocena: dict[str, tuple[str, str]],
          zdaj: float | None = None) -> dict[str, Okvara | None]:
    """Vrstica -> okvara, ki gre v pošto, ali None, kadar se je ta hip ne
    da oceniti (ponoči nič ne vozi). Vrstic, ki so v redu ali niso za pošto,
    ni. `ocena` je izid `ocena(z, m, zdaj)`.
    """
    zdaj = time.time() if zdaj is None else zdaj
    out: dict[str, Okvara | None] = {}
    for k, (raz, razlog) in ocena.items():
        pravilo = _POSTA.get(k) or (_NIT if k.startswith("nit:") else None)
        if pravilo is None:
            continue
        if raz == SLABA:
            out[k] = Okvara(razlog, *pravilo)
        elif k in _PO_VOZNEM_REDU and raz != DOBRA and (
                raz == "" or k == "zamude_sz" and not _vozijo(z, "zeleznica")):
            out[k] = None

    # Vozni red, ki se konča: uvoz ne teče ali vir nima novega.
    for k, vir in (("vozni_red", "gtfs_ijpp"), ("vozni_red_lpp", "gtfs_lpp"),
                   *((f"vozni_red_{m}", f"gtfs_{m}") for m in z.get("mestni_vozni_red") or {})):
        raz, razlog = ocena.get(k, ("", ""))
        if raz == SLABA:
            out[k] = Okvara(razlog, viri.po_kljucu()[vir].ukrep)

    nez = (z.get("rt_neznanih") or {}).get("ijpp")
    if nez and nez[0] >= NEZNANE_POSTA and nez[1] and nez[0] / nez[1] >= NEZNANE_POSTA_DELEZ:
        out["neznane"] = Okvara(
            f"vožnje brez voznega reda: IJPP {nez[0]} od {nez[1]}",
            "Feed nosi vožnje, ki jih vozni red nima -- verjetno nov vozni red s "
            "starimi id-ji. `KAJROS_AGENCIES=1118,1119,1121,1123 kajros update`; če "
            "ostane, `kajros zamenjave` (zajem.md, „Nov vozni red, stari id-ji“).", 1800)

    hudi = [f"{ime_} {nz} od {vseh}" for ime_, (_, nz, vseh)
            in (z.get("lega_brez_zamude") or {}).items()
            if nz >= BREZ_ZAMUDE_POSTA and vseh and nz / vseh >= BREZ_ZAMUDE_POSTA_DELEZ]
    if hudi:
        out["lega_brez_zamude"] = Okvara(
            "vozila brez vsake zamude: " + ", ".join(hudi),
            "Iz leg se zamude ne izpeljejo za velik del prevoznika -- poglej kartico "
            "NAP v /admin (prehodov, vozil brez vožnje) in `journalctl -u kajros.service`.")

    nm = z.get("nap")
    if nm and nm.get("http") in (401, 403) and zdaj - (nm.get("ts") or 0) >= NAP_PRIJAVA_S:
        out["nap"] = Okvara(
            f"NAP zavrača prijavo (HTTP {nm['http']}) že {_min(zdaj - (nm.get('ts') or 0))}",
            viri.po_kljucu()["nap"].ukrep)

    for vir, ts in (z.get("derp_prebran") or {}).items():
        if zdaj - ts >= DERP_DOLGO_S:
            out[f"derp_{vir}"] = Okvara(
                f"derp.si ({vir.upper()}) ne odgovarja že {_min(zdaj - ts)}",
                "Rezerve tečejo same (NAP, LPP-jevi zasloni, zemljevid SŽ); brez "
                "podatkov je primestni LPP. Preveri, ali je sprememba pri derp.si "
                "trajna (gitlab.com/derp-si), in se odloči za drug vir.")
    return out


def _vozijo(z: dict, omr: str) -> bool:
    vozi = z.get("vozi_zdaj")
    return vozi is None or vozi.get(omr, 0) >= MIN_VOZENJ
