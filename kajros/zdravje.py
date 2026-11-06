"""Kdaj je zajem zdrav: stopnje vrstic „Zdravje“ v `/admin` in opozorila po pošti.

Pravila so tu in ne v `admin.js`, ker jih bereta dva: prikaz in nit, ki
skrbniku pošlje opozorilo (`opozorila.py`). Dve kopiji istih mej bi se
razšli -- in opozorilo, ki ne pove istega kot pregled, je slabše od nobenega.

Stopnje (David, 31. 10. 2026) so imena razredov CSS:

* `je-mlacna`, rumeno -- popravi se samo ali je samo za vedenje; samo v /admin;
* `je-oranzna`, oranžno -- ne popravi se samo: rabi sejo s Claude
  (`/preveri-vire`) ali skrbnikovo dejanje, ni pa nujno v minuti; pošta podnevi;
* `je-slaba`, rdeče -- takoj: nekaj stoji ali potnik ta hip ne dobi
  podatkov; pošta takoj, potnikom samodejno obvestilo (`obvestila.samodejna`);
* `je-dobra`, prazno = brez ocene (ponoči nič ne vozi).

Rumena, ki ne mine, je oranžna: kar se v dogovorjenem času ni popravilo
samo, se ne bo. Trajanje šteje `Sled`; brez nje (preizkusi, en klic) se ne
stopnjuje nič, kar je odvisno od trajanja.
"""
from __future__ import annotations

import shutil
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

from . import brskalnik, config, viri

TZ = ZoneInfo(config.TIMEZONE)

SLABA, ORANZNA, MLACNA, DOBRA = "je-slaba", "je-oranzna", "je-mlacna", "je-dobra"
#: Pas na vrhu /admin in zadeva pošte vzameta najhujšo.
RANG = {SLABA: 3, ORANZNA: 2, MLACNA: 1, DOBRA: 0, "": 0}

#: Vir, ki ne odgovarja, ima rezervo ali čaka sam na sebe (rumeno). Ko molči
#: tako dolgo, to ni več motnja, ampak sprememba pri viru (nov naslov, nova
#: zaščita, ukinjen dostop) -- to popravi koda, ne čakanje.
VIR_ORANZNO_S = 2 * 3600
#: Dnevni viri (vozni red, vreme) berejo enkrat na dan: dva zgrešena dneva.
DNEVNI_ORANZNO_S = 2 * 86400

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

#: Straža doslednosti `run` za vlake (`zamude_sz.dosled`): delež današnjih
#: voženj z uro nazaj ali prihodom po odhodu >= 2 min. 1.--6. 11. 2026 je bila
#: ura nazaj pri 6,9 % voženj-dni, „stal >= 10 min“ pri 25,4 % (do 31. 10.
#: 1,3 % in 2,0 %), ker prihod ni bil iz istega vira kot odhod. Pod
#: `DOSLED_NAJMANJ` voženj (zjutraj, ponoči) ne sodimo.
DOSLED_RDECE, DOSLED_RUMENO = 0.05, 0.01
DOSLED_NAJMANJ = 50

#: Toliko voženj po voznem redu mora teči, da je molk feeda okvara.
MIN_VOZENJ = 3

#: Omrežje brez zapisa toliko časa je okvara: ista meja kot samodejno
#: obvestilo potnikom (`obvestila.MOLCI_S`, preizkus to drži skupaj). Mesec
#: zgodovine: najdaljša zdrava vrzel 15,6 min.
OMREZJE_MOLCI_S = 1200

#: derp.si se bere na 30 s; pet minut brez odgovora je deset zgrešenih branj.
DERP_MOLCI_S = 300
#: Vsebina toliko časa ista = zamrznjen vir (`iz_lege.FEED_ZAMRZNJEN_S`, preizkus
#: ju veže; uvoz bi v nit pošte potegnil zajem).
DERP_ZAMRZNJEN_S = 600
#: Rezerve tečejo same; šest ur molka ni več motnja pri njih (8. 10. 2026 je
#: izpad trajal popoldne), ampak vprašanje, ali vir sploh še obstaja.
DERP_ORANZNO_S = 6 * 3600

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
#: Dosje piše na minuto.
DOSJE_MOLK_S = 600
#: Vozila brez vožnje v mestu: rumeno od toliko vozil in deleža. 27. 10.
#: 2026 ob 11:00 4 od 36 (3 brez prihoda, 1 brez ure v voznem redu).
MARPROM_BREZ, MARPROM_BREZ_DELEZ = 5, 0.3
#: Kar velja za vozila v mestu ali za prazen vir ob prometu, je ura dolgo
#: prej mestno pravilo kot nihanje: vozni red se z vožnjami ne ujema.
STANJE_ORANZNO_S = 3600

#: Vožnje mestnega LPP brez voznega reda so vsak dan (živi sistem vozi mimo
#: objave, `zive.py` jih pripne); rumeno. Oranžno, ko jih je veliko uro dolgo:
#: 1. 10. 2026 17 % (vse linije 1), takrat pomaga samo koda.
NEZNANE_LPP_VELIKO, NEZNANE_LPP_DELEZ = 5, 0.10

#: Vozila brez vsake zamude: oranžno takoj pri `BREZ_ZAMUDE_POSTA` in deležu
#: (prava okvara izpeljave iz leg, `posta` spodaj), sicer, ko rumena (3 vozila,
#: 5 %) traja `BREZ_ZAMUDE_ORANZNO_S`. Kratke rumene so resnica na cesti
#: (odhod 30--120 min pozno, zapora, izpad interneta; 14.--17. 10. 2026).
BREZ_ZAMUDE_ORANZNO_S = 90 * 60

#: Izjema v naši obdelavi (`collector.zapisi_korak`): ena ali dve zapored sta
#: lahko zaklenjena baza (17.--31. 10. 2026 na arwenu 22 „database is locked“,
#: vse posamič razen treh zapored v senčnem merjenju 30. 10. ob 7:12--7:16);
#: tri zapored je koda, ki pade vsakič -- popravi jo le seja s Claude.
KODA_ORANZNO = 3
#: Niz, ki se toliko ne ponovi, ne velja: korak morda ne teče več.
KODA_POZABI_S = 3600
#: Koraki zanke in vir, čigar branje obdelajo (`derp_*` spodaj).
KORAKI = {"zamude": "zamude IJPP", "lege": "lege IJPP", "lpp": "mestni LPP",
          "obvestila": "obvestila IJPP", "ocena": "senčno merjenje"}
DERP_KORAK = {"ijpp": ("zamude", "derp_zamude"), "lpp": ("lpp", "derp_lpp")}

#: Glavna zanka zajema (`meta.zanka_ts`, na `POLL_SECONDS`) je obstala, ko
#: utripa ni `ZANKA_STOJI_S`: obhod, v katerem vsi štirje klici derp.si
#: dosežejo časovno mejo (60 s), traja do 4 min in je molk vira, ne zanke.
#: Uvoza voznega reda zanka od 1. 11. 2026 ne čaka (`server.Uvoz`; prej 17.--31.
#: 10. 2026 4 min 05 s do 5 min 01 s); njegova faza pisanja zaklene bazo
#: ≥ 45--80 s, vsak zapis zanke počaka do 30 s (busy): utrip zamudi do ~3 min.
ZANKA_STOJI_S = 600
#: Uvoz, ki teče dvakrat dlje od najdaljšega izmerjenega, se ne bo končal sam
#: (podproces ubije časovna meja 30 min, `server.UVOZ_ROK_S`).
UVOZ_ORANZNO_S = 15 * 60
#: Začetek brez konca, starejši od dvojne časovne meje podprocesa, je uvoz,
#: ki ga je prekinil ponovni zagon -- ne teče več.
UVOZ_NAJDLJE_S = 2 * 1800


def uvoz_tece(uv: dict, zdaj: float) -> float | None:
    """Koliko sekund uvoz voznega reda teče (`meta.uvoz`: začetek brez konca),
    ali None. Začetek, starejši od `UVOZ_NAJDLJE_S`, ne teče več."""
    od = uv.get("od")
    return zdaj - od if od and not uv.get("do") and zdaj - od <= UVOZ_NAJDLJE_S else None

#: Nočni uvoz in opravila (`meta.uvoz`, `meta.nocno`): ena neuspela noč je
#: lahko vir (zavrnjen zip 28. 9. 2026 se je popravil sam), dve zapored ne.
#: 1.--31. 10. 2026 ni padlo nobeno: uvoz 31/31 noči koda 0, povzetki 32,
#: obrez 31, vreme 31.
NOCNO_ORANZNO = 2
#: Niz, ki se toliko ne ponovi, ne velja: opravilo morda ne teče več.
NOCNO_POZABI_S = 3 * 86400
#: Prevoznik, ki mu uvoz vzame toliko voženj, ni nihanje okna: 18.--31. 10.
#: 2026 mestni LPP 18 467--21 162 (okno osmih dni), Kranj 446 -> 309 (konec
#: meseca v zipu MOK), IJPP brez spremembe. Meja nič (`gtfs.izginuli_prevozniki`)
#: zavrne zip; LPP v IJPP je od 30. 8. do 28. 9. padel za 82 % in tega ni videl nihče.
PADEC_PREVOZNIKA, PADEC_NAJMANJ = 0.4, 50

#: Ure dneva, ko gre oranžna pošta: ni nujna, ponoči ne zvoni.
DAN_OD_H, DAN_DO_H = 7, 22


class Sled:
    """Koliko časa je pogoj neprekinjeno res -- trajanje za stopnjevanje.

    Bere jo nit pošte (vsako minuto) in /admin; oba računata isti pogoj na
    svežih podatkih, zato pogostejše branje le izboljša ločljivost. Ključ, ki
    ga nihče ne vpraša dan dolgo (vir izklopljen), odpade ob `stanje()`.
    """

    def __init__(self, stanje: dict | None = None):
        self._od: dict[str, list[float]] = {
            k: list(v) for k, v in (stanje or {}).items()
            if isinstance(v, (list, tuple)) and len(v) == 2}
        self._zaklep = threading.Lock()

    def koliko(self, kljuc: str, pogoj: bool, zdaj: float) -> float:
        """Sekunde, odkar je `pogoj` res brez presledka; 0, ko ni."""
        with self._zaklep:
            if not pogoj:
                self._od.pop(kljuc, None)
                return 0.0
            v = self._od.setdefault(kljuc, [zdaj, zdaj])
            v[1] = zdaj
            return zdaj - v[0]

    def stanje(self, zdaj: float) -> dict[str, list[float]]:
        """Za shranitev v `meta` (ponovni zagon ne sme trajanja začeti znova)."""
        with self._zaklep:
            for k in [k for k, v in self._od.items() if zdaj - v[1] > 86400]:
                del self._od[k]
            return {k: list(v) for k, v in self._od.items()}


#: Sled procesa: nit pošte jo shranjuje in ob zagonu obnovi (`opozorila.teci`).
SLED = Sled()


class _BrezSledi:
    """Ena ocena brez zgodovine: nobeno trajanje ni doseženo."""

    @staticmethod
    def koliko(kljuc: str, pogoj: bool, zdaj: float) -> float:
        return 0.0


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


def _dosled(dv: dict) -> str:
    return (f"{dv.get('nedoslednih', 0)} od {dv.get('voznj', 0)} voženj "
            f"({100 * dv.get('nedoslednih', 0) / max(dv.get('voznj', 0), 1):.1f} %): ura nazaj "
            f"{dv.get('ura_nazaj', 0)}, prihod po odhodu {dv.get('prihod_po_odhodu', 0)}: "
            + ", ".join(dv.get("primeri") or []))


def _skladnost(sk: dict, n: int, mimo: int) -> str:
    return (f"prikaz se s SŽ ne ujema pri {100 * mimo / n:.1f} % primerjav "
            f"({mimo} od {n}, {sk.get('vlakov', 0)} vlakov, prenizko {sk.get('prenizko', 0)}, "
            f"previsoko {sk.get('previsoko', 0)}): " + ", ".join(sk.get("primeri") or []))


def _do(dni: int, d: date) -> str:
    return (f"se je končal {d.day}. {d.month}." if dni < 0
            else f"znan le do {d.day}. {d.month}.")


def ocena(z: dict, m: dict, zdaj: float | None = None,
          sled: Sled | None = None) -> dict[str, tuple[str, str]]:
    """Vrstica -> (stopnja, razlog). `z` je `/api/health`, `m` je `stroj()`.

    Razlog je ena vrstica: pri rdeči in oranžni gre v pošto, pri rumeni ga
    pokaže le pregled, pri zdravi je prazen. `sled` šteje, kako dolgo pogoj
    traja (rumena, ki ne mine, je oranžna); brez nje trajanja ni.
    """
    zdaj = time.time() if zdaj is None else zdaj
    sled = _BrezSledi() if sled is None else sled
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
    # Omrežje, ki `OMREZJE_MOLCI_S` nič ne zapiše, ko po voznem redu vozi, je
    # okvara: potniki takrat že vidijo samodejno obvestilo (ista meja,
    # `obvestila.MOLCI_S`). Do 31. 10. 2026 je bilo do ure le rumeno in pošta
    # je prišla po 70 min molka.
    svezina = z.get("svezina") or {}
    for kljuc, ime in (("zeleznica", "vlaki"), ("avtobus", "avtobusi")):
        ts = svezina.get(kljuc) or (mreze.get(kljuc) or {}).get("last_feed_ts")
        if vozi is not None and vozi.get(kljuc, 0) < MIN_VOZENJ:
            out[kljuc] = ("", "")
        elif not ts:
            out[kljuc] = (SLABA, f"{ime}: nobenega zapisa")
        elif zdaj - max(ts, jutro.get(kljuc, 0)) < OMREZJE_MOLCI_S:
            out[kljuc] = (DOBRA, "")
        else:
            out[kljuc] = (SLABA, f"{ime}: zadnji zapis pred {_min(zdaj - ts)}")

    # Vožnje iz feeda, ki jih vozni red ne pozna, zajem zavrže. 22. 9. 2026 jih
    # je bilo 16 od 662 (2,4 %) -- nov vozni red, feed pa pod starimi id-ji;
    # popravila je koda (`zamenjava`), zato oranžno pri vsaj treh IN 2 % IJPP.
    # Meja treh: 28. 9. 2026 ob 23:42 je bila ena sama vožnja (Nomagov N0152,
    # nagrobnik, ki ga feed še nosi) 1 od 29, ker ponoči vozi malo voženj.
    #
    # Mestni LPP vsak dan vozi kaj mimo objave (`zive.py` pripne, kar zna):
    # rumeno. Oranžno, ko je takih veliko uro dolgo (1. 10. 2026 17 %): to
    # pripenjanje ne zmore in rabi kodo. 31. 10. 2026 (praznik) 2 od 105 --
    # objava ima enake dvojnike voženj, par po uri je bil zato dvoumen.
    nez = z.get("rt_neznanih") or {}
    if nez:
        vse = [f"{vir.upper()} {n} od {vseh}" for vir, (n, vseh) in nez.items() if n > 0]
        n, vseh = nez.get("ijpp") or (0, 0)
        ijpp = n >= 3 and vseh and n / vseh >= 0.02
        n, vseh = nez.get("lpp") or (0, 0)
        lpp = sled.koliko("neznane:lpp", bool(n >= NEZNANE_LPP_VELIKO and vseh
                                              and n / vseh >= NEZNANE_LPP_DELEZ),
                          zdaj) >= STANJE_ORANZNO_S
        besedilo = "vožnje v feedu brez voznega reda: " + ", ".join(vse)
        out["neznane"] = ((ORANZNA, besedilo) if ijpp or lpp
                          else (MLACNA, besedilo) if vse else (DOBRA, ""))

    # Obratno: vozilo vozi in ima lego, feed zamud pa ga ne nosi. Od 21. do
    # 25. 9. 2026 ~430 Nomagovih voženj na dan, števec zgoraj pa zelen. Na
    # vožnjah, ki jih feed nosi, je bilo takih 0 od 295. Trojka je [ne v feedu,
    # brez zamude, vseh]: `iz_lege` vrzel zapolni, zato je napaka vira rumena,
    # huje pa je šele to, kar vidi potnik -- vozilo brez vsake zamude.
    #
    # Rumeno pri vsaj treh vozilih IN 5 % prevoznika: po zapolnitvi ostane
    # nekaj voženj, ki so odpeljale pozno in še niso prevozile drugega
    # postanka (izhodišča `iz_lege` ne meri). Oranžno takoj pri desetih in
    # 25 % (izpeljava iz leg odpove za velik del prevoznika, `posta` spodaj)
    # ali ko rumena traja `BREZ_ZAMUDE_ORANZNO_S`.
    #
    # Vrstica pove obe števili, vsako le, kadar ni nič. Do 14. 10. 2026 je
    # kazala samo prvo, ki je pri prevoznikih NAP vedno 0 (vir zamud je lega
    # sama), prižgalo pa jo je drugo: „Nomago 0 od 160“.
    lbz = z.get("lega_brez_zamude")
    if lbz is not None:
        vidni = {ime: v for ime, v in lbz.items() if v[0] > 0 or v[1] > 0}
        rumeni = [ime for ime, (_, nz, vseh) in vidni.items()
                  if nz >= 3 and vseh and nz / vseh >= 0.05]
        hudi = [ime for ime, (_, nz, vseh) in vidni.items()
                if nz >= BREZ_ZAMUDE_POSTA and vseh and nz / vseh >= BREZ_ZAMUDE_POSTA_DELEZ]
        dolgo = sled.koliko("lega_brez_zamude", bool(rumeni), zdaj) >= BREZ_ZAMUDE_ORANZNO_S

        def stevilo(i: int) -> str:
            return ", ".join(f"{ime} {v[i]} od {v[2]}" for ime, v in vidni.items() if v[i])
        brez, mimo = stevilo(1), stevilo(0)
        besedilo = "; ".join(x for x in (
            brez and "vozila z lego, a brez zamude: " + brez,
            mimo and "feed zamud jih ne nosi, zamudo meri lega: " + mimo) if x)
        out["lega_brez_zamude"] = ((ORANZNA, besedilo) if hudi or dolgo
                                   else (MLACNA, besedilo) if vidni else (DOBRA, ""))

    # Zemljevid SŽ (`zamude_sz`) vodi zamude vlakov. Rdeče, kadar stoji NIT:
    # ko vir ne odgovarja, nit ob vsakem poskusu zapiše `napaka_ts`; 1. 10. 2026
    # je obstala v transakciji in ni mogla zapisati ničesar -- 4,3 h je bila
    # vrstica le rumena. Ko vir ne odgovarja, je rumeno: vlake medtem piše
    # derp.si, kolikor jih ima, vrstica „vlaki · zadnji zapis“ pa pove, ali sploh.
    # Ponoči, ko vlaki ne vozijo, je tudi obstala nit le rumena: zamud ni
    # komu kazati, zjutraj pa je z voznim redom spet rdeča. Vir, ki ne
    # odgovarja `VIR_ORANZNO_S`, je oranžen: Cloudflare je 7. 10. 2026 zaprl
    # pot brezglavim, takrat je pomagal le nov način branja.
    zs = z.get("zamude_sz")
    if zs:
        zadnji = zs.get("ts") or 0
        sprem = zs.get("spremenjeno_ts") or zadnji
        vozijo = vozi is None or vozi.get("zeleznica", 0) >= MIN_VOZENJ
        prazen = sled.koliko("zamude_sz:prazen", bool(
            zdaj - zadnji <= SZ_STOJI_S and vozijo and vozi is not None
            and zdaj - sprem <= SZ_ZAMRZNJEN_S and not zs.get("vlakov")), zdaj)
        if zdaj - zadnji > SZ_STOJI_S:
            napaka = zs.get("napaka_ts") or 0
            out["zamude_sz"] = (
                ((ORANZNA if zdaj - zadnji >= VIR_ORANZNO_S else MLACNA),
                 f"zemljevid SŽ ne odgovarja od pred {_min(zdaj - zadnji)}"
                 + (f": {zs['napaka']}" if zs.get("napaka") else ""))
                if zdaj - napaka <= SZ_NAPAKA_S
                else ((SLABA if vozijo else MLACNA),
                      f"nit zemljevida SŽ ne piše od pred {_min(zdaj - zadnji)}"))
        elif vozijo and zdaj - sprem > SZ_ZAMRZNJEN_S:
            out["zamude_sz"] = ((ORANZNA if zdaj - sprem >= STANJE_ORANZNO_S else MLACNA),
                                f"zemljevid SŽ se ne spreminja od pred {_min(zdaj - sprem)}")
        elif vozijo and vozi is not None and not zs.get("vlakov"):
            out["zamude_sz"] = ((ORANZNA if prazen >= STANJE_ORANZNO_S else MLACNA),
                                f"zemljevid SŽ je prazen, po voznem redu "
                                f"vozi {vozi['zeleznica']} vlakov")
        else:
            out["zamude_sz"] = (DOBRA, "")

        # Straža (`zamude_sz.skladnost`): ali to, kar kažemo, drži s tem, kar
        # SŽ pravi. Vir je od 11. do 16. 10. 2026 odgovarjal in vrstica zgoraj
        # je bila zelena, prikaz pa je bil pri 611 od 1 444 voženj z zamudo
        # prenizek. Ponovitev 25 min zemljevida skozi staro kodo: mimo 2,3 do
        # 4,1 % ustaljenih primerjav, skozi novo 0 od 3 381. Oranžno pri 1 % in
        # treh vlakih (napaka je pri nas, popravi jo koda) -- en sam vlak je
        # posebnost, ne okvara zajema.
        sk = zs.get("skladnost") or {}
        n = sk.get("primerjav") or 0
        mimo = (sk.get("prenizko") or 0) + (sk.get("previsoko") or 0)
        if n < SKLADNOST_NAJMANJ:
            out["skladnost_sz"] = ("", "")
        elif mimo / n >= SKLADNOST_RDECE and (sk.get("vlakov") or 0) >= 3:
            out["skladnost_sz"] = (ORANZNA, _skladnost(sk, n, mimo))
        elif mimo / n >= SKLADNOST_RUMENO:
            out["skladnost_sz"] = (MLACNA, _skladnost(sk, n, mimo))
        else:
            out["skladnost_sz"] = (DOBRA, "")

    # Doslednost `run` za vlake: ura ne gre nazaj, prihod ni po odhodu. Rdeče
    # pri 5 %: vsaka dvajseta vožnja kaže nemogoč potek, napaka je v zajemu
    # (pošta po pol ure, `_POSTA`); rumeno od 1 %.
    dv = z.get("dosled_vlaki") or {}
    nv = dv.get("voznj") or 0
    if nv < DOSLED_NAJMANJ:
        out["dosled_vlaki"] = ("", "")
    else:
        delez = (dv.get("nedoslednih") or 0) / nv
        out["dosled_vlaki"] = ((SLABA, _dosled(dv)) if delez >= DOSLED_RDECE
                               else (MLACNA, _dosled(dv)) if delez >= DOSLED_RUMENO
                               else (DOBRA, ""))

    # derp.si po viru. 8. 10. 2026 je od 16:00 zavračal povezave; vrstici
    # zgoraj sta ostali zeleni, kolikor sta `zamude_lpp` in `zamude_sz` pisala
    # v `run` -- zato posebej, kdaj je derp.si sam nazadnje odgovoril. Vsak
    # vir svoja vrstica: pregled ju kaže na dveh karticah (`viri.py`). Rumeno:
    # rezerve tečejo same (NAP, LPP-jevi zasloni, zemljevid SŽ), brez podatkov
    # ostane le primestni LPP. Oranžno po `DERP_ORANZNO_S`: tako dolg molk je
    # lahko trajna sprememba, o kateri je treba odločiti.
    # Odgovor z vsebino, ki je ista že `DERP_ZAMRZNJEN_S`, je isto kot molk:
    # zajem takrat vožnje izpusti in zamude pišejo rezerve (`iz_lege`).
    # Glavna zanka, ki obstane, derp.si ne bere: njegovih vrstic takrat ni
    # mogoče oceniti, resnico pove vrstica `zanka` -- samo po utripu. Med
    # uvozom zanka utripa in vrstice derp.si se ocenjujejo: zaklep faze pisanja
    # vzame 1--2 obhoda (≤ ~3 min), pod `DERP_MOLCI_S` in `DERP_ZAMRZNJEN_S`.
    # `KAJROS_REFRESH=inprocess` (ne teče nikjer) zanko ustavi: nad 10 min je
    # to rdeče kot vsak drug obstanek.
    zt = z.get("zanka_ts")
    stoji = zt is not None and zdaj - zt > ZANKA_STOJI_S
    if zt is not None:
        out["zanka"] = ((SLABA, f"zanka zajema stoji od pred {_min(zdaj - zt)}") if stoji
                        else (DOBRA, ""))

    # Izjema v naši obdelavi (`zajem_napake` spodaj) razveljavi zapis branja:
    # odgovor vira zato vzamemo iz dnevnika virov, vsebine pa takrat ne vemo.
    dp = z.get("derp_prebran")
    dv = z.get("derp_vsebina") or {}
    pade = {k for k, v in (z.get("zajem_napake") or {}).items()
            if v.get("zapored") and zdaj - (v.get("ts") or 0) <= KODA_POZABI_S}
    if dp is not None and not (vozi is not None and vozi.get("avtobus", 0) < MIN_VOZENJ):
        for vir, ts in sorted(dp.items()):
            if stoji:
                out[f"derp_{vir}"] = ("", "")
                continue
            korak, kljuc = DERP_KORAK.get(vir, ("", ""))
            molk = zdaj - max(ts, ((m.get("viri") or {}).get(kljuc) or {}).get("uspeh_ts") or 0)
            star = zdaj - dv[vir] if vir in dv and korak not in pade else 0
            if molk > DERP_MOLCI_S:
                out[f"derp_{vir}"] = ((ORANZNA if molk >= DERP_ORANZNO_S else MLACNA),
                                      f"derp.si ({vir.upper()}) ne odgovarja od pred {_min(molk)}")
            elif star > DERP_ZAMRZNJEN_S:
                out[f"derp_{vir}"] = ((ORANZNA if star >= DERP_ORANZNO_S else MLACNA),
                                      f"derp.si ({vir.upper()}) odgovarja, a vsebina se ni "
                                      f"spremenila od pred {_min(star)}; zamude pišejo rezerve")
            else:
                out[f"derp_{vir}"] = (DOBRA, "")

    # Izjema v NAŠI obdelavi po koraku zanke (`collector.zapisi_korak`), ne v
    # branju vira. Rumeno, dokler je lahko zaklenjena baza, oranžno od
    # `KODA_ORANZNO` zapored: vir odgovarja, pade naša koda.
    zn = {k: v for k, v in (z.get("zajem_napake") or {}).items() if k in pade}
    if z.get("zajem_napake") is not None:
        out["zajem_napake"] = (
            ((ORANZNA if any(v["zapored"] >= KODA_ORANZNO for v in zn.values()) else MLACNA),
             "; ".join(f"{KORAKI.get(k, k)}: {v['zapored']}× zapored od {_ura(v['od'])}, "
                       f"{v.get('napaka')} ({v.get('kje') or '?'})" for k, v in sorted(zn.items())))
            if zn else (DOBRA, ""))

    # Nočni uvoz voznega reda in nočna opravila: izid je bil do 31. 10. 2026
    # samo v dnevniku. Rumeno ena neuspela noč, oranžno dve zapored ali
    # prevoznik, ki mu je uvoz vzel več kot `PADEC_PREVOZNIKA` voženj. Uvoz,
    # ki teče `UVOZ_ORANZNO_S`, visi: oranžno (do 31. 10. 2026 v vrstici
    # `zanka`, ker ga je zanka čakala). Krajši je navaden in nima barve.
    uv, nocno = z.get("uvoz") or {}, z.get("nocno")
    uvoz_s = uvoz_tece(uv, zdaj)
    visi = uvoz_s is not None and uvoz_s >= UVOZ_ORANZNO_S
    if uv.get("izid") or nocno is not None or visi:
        slabe, noci = [], 0
        if visi:
            slabe.append(f"uvoz voznega reda teče {_min(uvoz_s)} "
                         f"(podproces ubije časovna meja 30 min)")
        if uv.get("izid") in ("zavrnjen", "napaka"):
            noci = uv.get("neuspelih") or 1
            slabe.append(f"uvoz voznega reda {uv['izid']} ({_ura(uv.get('do') or zdaj)}, "
                         f"{noci}. noč): {uv.get('razlog')}")
        for k, v in sorted((nocno or {}).items()):
            if v.get("zapored") and zdaj - (v.get("ts") or 0) <= NOCNO_POZABI_S:
                noci = max(noci, v["zapored"])
                slabe.append(f"{k}: {v['zapored']}. noč, {v.get('napaka')} ({v.get('kje') or '?'})")
        padci = [f"{ag} {st} → {nov}"
                 for ag, (st, nov) in sorted((uv.get("prevozniki") or {}).items())
                 if uv.get("izid") == "ok" and st >= PADEC_NAJMANJ
                 and nov < (1 - PADEC_PREVOZNIKA) * st]
        if padci:
            slabe.append("uvoz je vzel vožnje: " + ", ".join(padci))
        out["nocno"] = (((ORANZNA if noci >= NOCNO_ORANZNO or padci or visi else MLACNA),
                         "; ".join(slabe)) if slabe else (DOBRA, ""))

    # Mestni LPP z LPP-jevih zaslonov (`zamude_lpp`), kot zemljevid SŽ zgoraj:
    # rdeče, kadar stoji nit, rumeno, kadar ne odgovarja vir.
    zl = z.get("zamude_lpp")
    if zl:
        molk = zdaj - (zl.get("ts") or 0)
        if vozi is not None and vozi.get("avtobus", 0) < MIN_VOZENJ:
            out["zamude_lpp"] = ("", "")
        elif molk > LPP_STOJI_S:
            napaka = zl.get("napaka_ts") or 0
            out["zamude_lpp"] = (
                ((ORANZNA if molk >= VIR_ORANZNO_S else MLACNA),
                 f"LPP-jevi zasloni ne odgovarjajo od pred {_min(molk)}")
                if zdaj - napaka <= LPP_STOJI_S
                else (SLABA, f"nit LPP-jevih zaslonov ne piše od pred {_min(molk)}"))
        else:
            out["zamude_lpp"] = (DOBRA, "") if zl.get("oba") or zl.get("samo_lpp") else ("", "")

    # Lege IJPP z NAP (`nap.py`). Zavrnjena prijava je rumena, dokler ni
    # stara `NAP_PRIJAVA_S`: dostop čaka na odobritev ali novo geslo, kar se ne
    # zgodi samo -- potem oranžno. Rdeče, kadar stoji nit.
    nm = z.get("nap")
    if nm:
        molk = zdaj - (nm.get("ts") or 0)
        if nm.get("http") and zdaj - (nm.get("napaka_ts") or 0) <= NAP_STOJI_S:
            dolgo = (molk >= NAP_PRIJAVA_S if nm["http"] in (401, 403)
                     else molk >= VIR_ORANZNO_S)
            out["nap"] = ((ORANZNA if dolgo else MLACNA),
                          f"NAP zavrnil prijavo (HTTP {nm['http']})"
                          + (f", zadnji odgovor pred {_min(molk)}" if dolgo else ""))
        elif vozi is not None and vozi.get("avtobus", 0) < MIN_VOZENJ:
            out["nap"] = ("", "")
        elif molk > NAP_STOJI_S:
            napaka = nm.get("napaka_ts") or 0
            out["nap"] = (
                ((ORANZNA if molk >= VIR_ORANZNO_S else MLACNA),
                 f"NAP ne odgovarja od pred {_min(molk)}")
                if zdaj - napaka <= NAP_STOJI_S
                else (SLABA, f"nit NAP ne piše od pred {_min(molk)}"))
        else:
            out["nap"] = (DOBRA, "")

    # Mestna vira v živo (`marprom.py`, `kranj.py`). Rumeno, ko vir ne
    # odgovarja (drugega ni) ali ko velik del vozil ostane brez vožnje -- vozni
    # red se z njihovimi vožnjami ne ujema; oranžno, ko to traja; rdeče samo,
    # ko stoji nit.
    for kljuc, ime in (("marprom", "Marprom"), ("kranj", "Kranj")):
        mm = z.get(kljuc)
        if not mm:
            continue
        po_vr = mm.get("po_voznem_redu") or 0
        vozil, brez = mm.get("vozil") or 0, mm.get("brez_voznje") or 0
        molk = zdaj - (mm.get("ts") or 0)
        ziv = molk <= MARPROM_STOJI_S
        nobenega = sled.koliko(f"{kljuc}:nobenega", bool(
            ziv and not vozil and po_vr >= MIN_VOZENJ), zdaj)
        mnogo = bool(ziv and vozil and brez >= MARPROM_BREZ and brez >= MARPROM_BREZ_DELEZ * vozil)
        mnogo_s = sled.koliko(f"{kljuc}:brez_voznje", mnogo, zdaj)
        if not ziv:
            napaka = mm.get("napaka_ts") or 0
            out[kljuc] = (
                ((ORANZNA if molk >= VIR_ORANZNO_S else MLACNA),
                 f"{ime} ne odgovarja od pred {_min(molk)}")
                if zdaj - napaka <= MARPROM_STOJI_S
                else (SLABA, f"nit ({ime}) ne piše od pred {_min(molk)}"))
        elif po_vr < MIN_VOZENJ and not vozil:
            out[kljuc] = ("", "")
        elif not vozil:
            out[kljuc] = ((ORANZNA if nobenega >= STANJE_ORANZNO_S else MLACNA),
                          f"{ime}: nobenega vozila, po voznem redu jih vozi {po_vr}")
        elif mnogo:
            out[kljuc] = ((ORANZNA if mnogo_s >= STANJE_ORANZNO_S else MLACNA),
                          f"{ime}: vozila brez vožnje {brez} od {vozil}")
        else:
            out[kljuc] = (DOBRA, "")

    # Vozni red, ki se konča. Uvoz ob 4:20 premakne okno LPP vsak dan za dan
    # naprej (`config.LPP_DAYS`); če ne teče, mestne linije čez teden dni
    # izginejo z vseh strani brez ene same napake v dnevniku -- tako je bilo
    # na razvojnem računalniku. Teden prej oranžno (uvoz ne teče ali vir nima
    # novega -- samo se ne popravi), dva dni prej rdeče. Brez meritve: meja je
    # posledica, ne šum.
    vr = z.get("vozni_red")
    if vr:
        danes = datetime.fromtimestamp(zdaj, TZ).date()
        for kljuc, deli, rumeno in (
                ("vozni_red", (("zeleznica", "vlakov"), ("avtobus", "avtobusov")),
                 VOZNI_RED_RUMENO_DNI),
                ("vozni_red_lpp", (("lpp", "mestnega LPP"),), config.LPP_DAYS - 2)):
            slabi, kmalu = [], []
            for omr, ime in deli:
                if not vr.get(omr):
                    continue
                d = date.fromisoformat(vr[omr])
                dni = (d - danes).days
                if dni < VOZNI_RED_RDECE_DNI:
                    slabi.append(f"vozni red {ime} {_do(dni, d)}")
                elif dni < rumeno:
                    kmalu.append(f"vozni red {ime} {_do(dni, d)}")
            if any(vr.get(omr) for omr, _ in deli):
                out[kljuc] = ((SLABA, ", ".join(slabi)) if slabi
                              else (ORANZNA, ", ".join(kmalu)) if kmalu else (DOBRA, ""))

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
                out[vrstica] = (ORANZNA, f"vozni red {_do(dni, d)}")
                continue
        uradni = viri_[0] if viri_ else None
        if uradni and not uradni.get("sprejet"):
            zakaj = (uradni["napaka"] if uradni.get("napaka") else
                     f"{sum(1 for n in uradni.get('pokrito') or () if not n)} od "
                     f"{len(uradni.get('pokrito') or ())} dni brez voženj")
            if uradni.get("manj"):
                zakaj = f"{uradni['manj'][0]} voženj v tednu, zadnji sprejeti {uradni['manj'][1]}"
            kopija = any(v.get("sprejet") for v in viri_[1:])
            out[vrstica] = (MLACNA, f"uradni zip ne pokrije tedna ({zakaj}); "
                            + ("velja kopija" if kopija else "ostane zadnji sprejeti")
                            + (f", del voznih redov se konča {d.day}. {d.month}."
                               if d and mv.get("rok") and mv["rok"] != mv["do"] else ""))
        elif mv.get("do"):
            out[vrstica] = (DOBRA, "")

    # Avtobus, ki mu zamuda raste z uro (`collector.ura_namesto_zamude`): feed
    # ga drži na vožnji, ki je morda ne vozi (31. 10. 2026 LPP 2 +66 min pri
    # garaži). Do odločitve (`config.DRSI`) samo rumeno, s povezavami -- da
    # skrbnik pogleda, ali je vozilo res obstalo ali feed laže.
    fa = z.get("fantomi")
    if fa is not None:
        out["fantomi"] = ((MLACNA, f"zamuda raste z uro, vozilo morda ne vozi: "
                                   f"{fa['n']} voženj ({'v senci' if fa.get('nacin') != 'vodi' else 'ne pišemo'})")
                          if fa.get("n") else (DOBRA, ""))

    # Prikaz bere nočni račun (`opazovano.py`). Stare trditve po tednu odpadejo
    # same; račun, ki stoji, pa se sam ne zažene: oranžno.
    if z.get("opazovano_dan"):
        dni = (danes - date.fromisoformat(z["opazovano_dan"])).days
        out["opazovano"] = ((ORANZNA, f"nočni račun stoji, zadnji dan {dni} dni nazaj")
                            if dni > OPAZOVANO_NAJVEC_DNI else (DOBRA, ""))

    # Dosje vozil (`dosje.py`) je za diagnozo, potnik ne vidi nič: nikoli rdeče.
    # Popravi se le z zagonom, zato po urah oranžno; `napak` je na zadnjih branjih.
    dj = z.get("dosje")
    if dj:
        molk = zdaj - (dj.get("ts") or 0)
        out["dosje"] = (((ORANZNA if molk >= VIR_ORANZNO_S else MLACNA),
                         f"dosje vozil ne piše od pred {_min(molk)}")
                        if molk >= DOSJE_MOLK_S else (DOBRA, ""))

    # Nit, ki je umrla, ne vstane do ponovnega zagona: izjema mimo `except`
    # v zanki ali napaka ob zagonu. Vir je bil tedaj viden le posredno („ne
    # piše“), tir s table SŽ pa sploh ne.
    zive = set(m.get("niti") or ())
    for nit, kljuci in (m.get("pricakovane_niti") or {}).items():
        out[f"nit:{nit}"] = ((DOBRA, "") if nit in zive
                             else (SLABA, f"nit {nit} ne teče ({', '.join(kljuci)})"))

    # Viri brez svojega pravila: rumeno, kadar zadnjih nekaj branj ni uspelo;
    # oranžno, ko izpad traja (`VIR_ORANZNO_S`, dnevni `DNEVNI_ORANZNO_S`).
    # Nikoli rdeče -- teh meja nismo merili, pošta „takoj“ pa mora pomeniti okvaro.
    for v in viri.vsi():
        d = (m.get("viri") or {}).get(v.kljuc)
        if v.zdravje or not v.vklopljen or not d:
            continue
        if d["zaporednih"] >= v.prag_napak:
            od = d["izpad_od"] or d["napaka_ts"]
            meja = DNEVNI_ORANZNO_S if v.prag_napak == 1 else VIR_ORANZNO_S
            out[f"vir:{v.kljuc}"] = ((ORANZNA if od and zdaj - od >= meja else MLACNA),
                                     f"{v.ime}: {d['napaka']} (od {_ura(od)})")
        elif d["uspeh_ts"]:
            out[f"vir:{v.kljuc}"] = (DOBRA, "")

    if m.get("disk_vseh"):
        delez = m["disk_prostih"] / m["disk_vseh"]
        out["disk"] = ((SLABA, f"prostora na disku le {100 * delez:.0f} %") if delez < 0.08
                       else (ORANZNA, f"prostora na disku le {100 * delez:.0f} %") if delez < 0.12
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
# Pošta mora povedati, da mora skrbnik nekaj NAREDITI, ne le, da je nekaj
# narobe: od 1. do 17. 10. 2026 je šlo 67 pošt „stoji“, od tega 31 „vozila
# brez vsake zamude“ (3–8 vozil, nihanje), 11 „vlaki: zadnji zapis“ ob 3:58
# (nočni povzetki), 7 „vožnje brez voznega reda“ LPP (obvozi za maraton) in
# 2 „prikaz proti SŽ“ (SŽ je vlak risal po voznem redu) -- pri nobeni od teh
# skrbnik ni mogel nič. David, 17. 10.: „na mail moram dobiti le, kadar stoji
# in rabim jaz posredovati“. Od 31. 10. 2026 je to merilo stopnja: rdeča gre
# takoj (nekaj stoji), oranžna podnevi (rabi sejo s Claude), rumena nikoli.

#: Imena vrstic v pošti in v pasu /admin.
IMENA = {
    "feed": "zajem · zadnja zamuda v bazi",
    "zeleznica": "vlaki · zadnji zapis",
    "avtobus": "avtobusi · zadnji zapis",
    "neznane": "vožnje brez voznega reda",
    "lega_brez_zamude": "vozila brez zamude",
    "zamude_sz": "zemljevid SŽ",
    "skladnost_sz": "vlaki · prikaz proti SŽ",
    "dosled_vlaki": "vlaki · doslednost časov",
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
    "dosje": "dosje vozil",
    "fantomi": "avtobusi · zamuda raste z uro",
    "zajem_napake": "zajem · naša obdelava",
    "zanka": "zajem · glavna zanka",
    "nocno": "nočni uvoz in opravila",
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
    #: Rdeča gre takoj, oranžna samo podnevi (`podnevi`).
    nujno: bool = True


_RESTART = "Na arwenu `sudo systemctl restart kajros.service`, vzrok v `journalctl -u kajros.service`."
_ZAJEM = ("Spodaj piše, ali viri odgovarjajo. Če odgovarjajo, stoji pri nas: " + _RESTART
          + " Če ne, je izpad pri viru; potniki že vidijo samodejno obvestilo (po 20 min).")
#: Ukrep za oranžno, ki nima svojega: to je namen oranžne.
CLAUDE = ("Ne popravi se samo. V ~/Dokumenti/Projekti/sztrack odpri sejo s Claude "
          "in poženi /preveri-vire: prebere ta pregled, poišče vzrok in ga popravi.")

#: Rdeča vrstica -> (ukrep, po koliko sekund). Rdeča gre v pošto vedno;
#: vrstica brez vnosa dobi splošni ukrep.
_POSTA: dict[str, tuple[str, int]] = {
    "feed": (_ZAJEM, 600),
    "zeleznica": (_ZAJEM + " Pri vlakih poglej še vrstico „zemljevid SŽ“ in brskalnik.", 600),
    "avtobus": (_ZAJEM, 600),
    "zamude_sz": ("Nit zemljevida SŽ ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "zamude_lpp": ("Nit LPP-jevih zaslonov ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "nap": ("Nit NAP ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "marprom": ("Nit Marproma ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "kranj": ("Nit Kranja ne zapiše niti napake -- obstala je. " + _RESTART, 600),
    "disk": ("Na arwenu `df -h /var/lib/kajros`; največ prostora vzamejo `promet.sqlite`, "
             "`dosje.sqlite` in varnostne kopije.", 600),
    "wal": ("Prepis WAL v bazo ne teče -- kdo drži star posnetek. " + _RESTART, 600),
    "dosled_vlaki": ("Vsaka dvajseta današnja vožnja vlaka ima v `run` uro nazaj ali prihod po "
                     "odhodu (primeri so v vrstici). Napaka je pri nas: zapis zemljevida SŽ ali "
                     "napoved derp.si v `run` (`zamude_sz.zapisi`, `collector.napoved_vlaka`); "
                     "stare vrstice popravi `kajros popravi-vlake`. " + CLAUDE, 1800),
    "zanka": ("Glavna zanka zajema (derp.si, obvestila, senca) ne tiktaka, nit pa živi -- "
              "obtičala je v koraku. " + _RESTART, 600),
}
_NIT = ("Nit je umrla in ne vstane do ponovnega zagona. " + _RESTART, 600)

#: Oranžna vrstica -> (ukrep, po koliko sekund). Ostale dobijo `CLAUDE`.
_ORANZNO: dict[str, tuple[str, int]] = {
    # Vlakov, ki jih SŽ riše po voznem redu, straža ne šteje
    # (`zamude_sz.skladnost`), zato pol ure oranžnega pomeni napako pri nas --
    # potnik vidi napačno zamudo in to popravi samo koda.
    "skladnost_sz": ("Prikaz zamud vlakov se pri več vlakih ne ujema s SŽ. Napaka je pri "
                     "nas (meja meritve, zapis v `run`), ne pri SŽ; primeri so v vrstici. "
                     + CLAUDE, 1800),
    # 22. 9. 2026 (nov vozni red, stari id-ji v feedu) 16 od 662 = 2,4 %.
    "neznane": ("Feed nosi vožnje, ki jih vozni red nima -- pri IJPP verjetno nov vozni red "
                "s starimi id-ji (`kajros update`, nato `kajros zamenjave`, zajem.md), pri "
                "LPP žive vožnje, ki jih `zive.py` ne pripne. " + CLAUDE, 1800),
    "lega_brez_zamude": ("Iz leg se zamude ne izpeljejo -- kartica NAP v /admin (vozil brez "
                         "vožnje, brez dneva, prehodov), vozila so v povezavah ob vrstici. "
                         + CLAUDE, 600),
    "disk": ("Na arwenu `df -h /var/lib/kajros`; največ prostora vzamejo `promet.sqlite`, "
             "`dosje.sqlite` in varnostne kopije.", 600),
    "derp_ijpp": ("Rezerve tečejo same (NAP, zemljevid SŽ). Preveri, ali je sprememba pri "
                  "derp.si trajna (gitlab.com/derp-si), in se odloči za drug vir.", 600),
    "derp_lpp": ("Rezerva so LPP-jevi zasloni; brez podatkov je primestni LPP. Preveri, ali "
                 "je sprememba pri derp.si trajna (gitlab.com/derp-si).", 600),
    "nocno": ("Nočni uvoz ali opravilo ne uspe drugo noč zapored, uvoz teče predolgo (podproces "
              "ubije časovna meja 30 min; na arwenu `pgrep -af 'kajros.cli update'`) ali je "
              "uvoz prevozniku vzel veliko voženj. Vrstica pove, kaj in zakaj; zavrnjen zip: "
              "zajem.md, „Nov vozni red“. " + CLAUDE, 0),
    "zajem_napake": ("Vir odgovarja, pade naša obdelava: vrstica pove korak, izjemo in kje "
                     "v kodi (datoteka:vrstica ← klicatelj). " + CLAUDE, 600),
}

#: Vrstice, ki ponoči (nič ne vozi) nimajo ocene. Takrat pošta ne ve, ali je
#: okvara mimo, zato ne pošlje ne „stoji“ ne „spet dela“: obstala nit ob
#: 23:50 bi sicer ob 0:35 dobila „spet dela“ in ob 4:00 znova „stoji“.
_PO_VOZNEM_REDU = frozenset({"feed", "zeleznica", "avtobus", "zamude_sz", "zamude_lpp", "nap",
                             "marprom", "kranj", "skladnost_sz", "dosled_vlaki"})

#: Vozila brez vsake zamude: oranžno takoj šele, ko izpeljava zamud iz leg
#: odpove za velik del prevoznika. Ponovitev 14.–17. 10. 2026 po minutah: pri
#: (3 vozila, 5 %) 5 pošt v treh dneh, vse zaradi resnice na cesti (odhod
#: 30–120 min pozno, zastoj ob zapori za maraton, izpad interneta); pri 10
#: vozilih in 25 % nobene, prava okvara (prehod ne piše) pa doseže prag v
#: 9–24 min. Vrhovi po vrzeli leg NAP (do 71 %) trajajo do 5 min.
BREZ_ZAMUDE_POSTA, BREZ_ZAMUDE_POSTA_DELEZ = 10, 0.25

#: NAP, ki zavrača prijavo, se ne popravi sam: novo geslo ali odobritev.
NAP_PRIJAVA_S = 3600


def podnevi(zdaj: float) -> bool:
    """Ali sme iti oranžna pošta (ni nujna, ponoči ne zvoni)."""
    return DAN_OD_H <= datetime.fromtimestamp(zdaj, TZ).hour < DAN_DO_H


def posta(z: dict, m: dict, ocena: dict[str, tuple[str, str]],
          zdaj: float | None = None) -> dict[str, Okvara | None]:
    """Vrstica -> okvara, ki gre v pošto, ali None, kadar se je ta hip ne
    da oceniti (ponoči nič ne vozi). Zelenih in rumenih vrstic ni. `ocena` je
    izid `ocena(z, m, zdaj, sled)`.
    """
    out: dict[str, Okvara | None] = {}
    ukrepi = {f"vozni_red_{k}": f"gtfs_{k}" for k in z.get("mestni_vozni_red") or {}}
    ukrepi.update(vozni_red="gtfs_ijpp", vozni_red_lpp="gtfs_lpp", nap="nap")
    for k, (raz, razlog) in ocena.items():
        if raz == SLABA:
            ukrep, po_s = (_POSTA.get(k) or (_NIT if k.startswith("nit:") else None)
                           or (viri.po_kljucu()[ukrepi[k]].ukrep if k in ukrepi else None,
                               600))
            out[k] = Okvara(razlog, ukrep or CLAUDE, po_s)
        elif raz == ORANZNA:
            ukrep, po_s = _ORANZNO.get(k) or (
                viri.po_kljucu()[ukrepi[k]].ukrep if k in ukrepi else CLAUDE, 600)
            out[k] = Okvara(razlog, ukrep, po_s, nujno=False)
        elif k in _PO_VOZNEM_REDU and raz != DOBRA and (
                raz == "" or k == "zamude_sz" and not _vozijo(z, "zeleznica")):
            out[k] = None
    return out


def _vozijo(z: dict, omr: str) -> bool:
    vozi = z.get("vozi_zdaj")
    return vozi is None or vozi.get(omr, 0) >= MIN_VOZENJ


# --- vozila za vrstico -------------------------------------------------------

#: Toliko povezav ob eni vrstici; več je seznam, ki ga nihče ne prebere.
PRIMEROV = 6


def _primer(p: dict, prevoznik: str = "") -> dict:
    """Ena povezava: oznaka in pot na zemljevid z izbranim vozilom."""
    # Oboje: vozilo je lahko že na naslednji vožnji (fantom, 1. 11. 2026: LPP
    # 19B 39 min po tem, ko je stara vožnja izgubila lego), zemljevid ga najde
    # po id-ju.
    q = {k: p[i] for k, i in (("trip", "trip_id"), ("vozilo", "vozilo")) if p.get(i)}
    if p.get("lat") is not None and p.get("lon") is not None:
        q.update(lat=f"{p['lat']:.5f}", lon=f"{p['lon']:.5f}", z="16")
    oznaka = p.get("oznaka") or p.get("trip_id") or p.get("vozilo") or "?"
    if prevoznik and not oznaka.startswith(prevoznik):
        oznaka = f"{prevoznik} {oznaka}"
    out = {"oznaka": oznaka, "pot": "/app/map?" + urlencode(q)}
    if p.get("vozilo"):
        out["dosje"] = "/admin/vozilo/" + quote(str(p["vozilo"]), safe="")
    # Vožnja brez sveže lege na zemljevidu ni vidna; okno jo pokaže vseeno.
    if p.get("train_no") and p.get("trip_id"):
        okno = "/app/bus/" if p.get("network") == "avtobus" else "/app/train/"
        out["okno"] = (okno + quote(str(p["train_no"]), safe="")
                       + "?" + urlencode({"trip": p["trip_id"]}))
    return out


def primeri(z: dict) -> dict[str, list[dict]]:
    """Vrstica -> vozila, ki jo prižgejo, s potjo na zemljevid, kjer je
    vozilo izbrano (`?trip=` ali `?vozilo=`, `dashboard.js`).

    David, 31. 10. 2026: „če te vozila rabijo pozornost, zraven dodaj link do
    zemljevida, kjer je to vozilo označeno, da vidim sam, kaj je to“.
    """
    out: dict[str, list[dict]] = {}
    lbz = [_primer(p, ime_) for ime_, ps in (z.get("lega_brez_zamude_primeri") or {}).items()
           for p in ps]
    if lbz:
        out["lega_brez_zamude"] = lbz[:PRIMEROV]
    fa = [_primer(p, p.get("prevoznik") or "") for p in (z.get("fantomi") or {}).get("voznje") or []]
    if fa:
        out["fantomi"] = fa[:PRIMEROV]
    bv = z.get("vozila_brez_voznje") or {}
    if bv.get("LPP"):
        out["neznane"] = [_primer(p) for p in bv["LPP"][:PRIMEROV]]
    if bv.get("Marprom"):
        out["marprom"] = [_primer(p) for p in bv["Marprom"][:PRIMEROV]]
    return out
