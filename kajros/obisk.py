"""Kdo je bil na strani — števci obiska brez osebnih podatkov.

Doslej tega ni vedel nihče. Strežnik ni beležil ničesar, pred njim pa stoji
Cloudflarov tunel, ki svojega dnevnika ne da; vprašanje „koliko različnih
ljudi to sploh odpre“ je bilo torej neodgovorljivo. Projekt, ki ima za prvo
pravilo „meri, ne domnevaj“, o sebi ni meril ničesar.

**IP se ne shrani nikoli.** Obiskovalec je šestnajst znakov
`blake2s(sol dneva ‖ IP ‖ User-Agent)`, sol pa je šestnajst naključnih bajtov,
ki se ob prehodu dneva zavržejo in nadomestijo. Iz zapisa ni poti nazaj do
naslova, in dveh dni ne more povezati **nihče, tudi mi ne**. Cena te odločitve
je zapisana pri `pregled()`: mesečnih unikatov ni, ker jih iz dnevnih ključev
ni mogoče izračunati — samo vsota dnevnih, ki isto osebo šteje večkrat.

**Pisanje ne gre v zahtevo.** Števci se nabirajo v pomnilniku in jih ena nit
izprazni vsakih `IZPRAZNI_S`. En obisk strani ni ena zahteva, ampak 10–30:
zemljevid anketira lege vsakih 10 s in zamude vsakih 30 s, dokler je zavihek
odprt. Vrstica na zahtevo bi torej pomenila stalno pisanje v isto bazo, v
katero teče zajem — in zajem je edino, česar ni mogoče ponoviti za nazaj.

**Človek je, kdor je stran pognal, ne kdor se predstavi kot brskalnik.**
15. 9. 2026 je pregled kazal 104 ljudi, od tega 79 z eno samo zahtevo na `/`
in nič drugega -- iz ZDA, Tajske, Kitajske, Hongkonga, ponoči. Skenerji
pošiljajo UA Chroma, zato jih `_BOT` ne ujame. Pravi brskalnik pa po strani
požene JS in vpraša `/api/…` ali `/sw.js`; kdor tega ne naredi, stran ni
videl, ampak jo je prenesel. Ogled se zato do tega dokaza drži na čakanju
(`_cakajoci`) in se pripiše za nazaj, ko dokaz pride.

Kar ta modul namenoma **ni**: ni sledilnik poti posameznika po strani. Vrstica
o obiskovalcu nosi pet števil (zahteve, ogledi, klici iz JS, prvi in zadnji
dotik) in različico naše aplikacije, če je prišel iz nje -- ne zaporedja
strani. Kdo je kam kliknil, se iz tega ne da sestaviti. Tudi čakajoči ogledi
so v pomnilniku razrezi, ne seznam poti.

**Aplikacija za Android se šteje posebej** (od 24. 9. 2026). Do tedaj je bila
v pregledu le razrez naprave, ki šteje zahteve in oglede, ne ljudi -- na
vprašanje „koliko ljudi jo uporablja na dan“ ni odgovarjal nihče. Prenosi APK
pa se sploh niso videli: Cloudflare je datoteko stregel s svojega roba
(`cf-cache-status: HIT`, izmerjeno 24. 9.) in do strežnika je prišel le vsak
kdove kateri prenos. Zato mapa `/prenos` pošilja `no-store` (`api.py`).
"""

from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from . import config, db

_NAS = (urlsplit(config.BASE_URL).hostname or "").lower()

TZ = ZoneInfo(config.TIMEZONE)

#: Kako pogosto gredo števci iz pomnilnika v bazo. Minuta je izbrana tako, da
#: je zapis redek proti zajemu (30 s) in da ob padcu procesa izgubimo največ
#: minuto števcev -- to niso meritve zamud, ampak statistika obiska.
IZPRAZNI_S = 60

#: Zgornje meje razredov odzivnega časa v milisekundah; kar je počasnejše od
#: zadnje, pade v vedro `len(VEDRA)`. Natančnih časov ne hranimo -- za
#: vprašanje „ali je stran komu počasna“ je razred dovolj, vsota vseh časov
#: pa je zapisana posebej in da povprečje.
VEDRA = (10, 25, 50, 100, 250, 500, 1000, 2500, 5000)

#: Varovalka pred neomejeno rastjo pomnilnika med dvema praznjenjema. Ključev
#: je v normalnem teku nekaj sto (35 poti × 24 ur); če jih je toliko, nas
#: nekdo namerno preiskuje z izmišljenimi naslovi in nadaljnje štetje ne
#: pove ničesar novega.
NAJVEC_KLJUCEV = 20_000

#: Koliko obiskovalcev brez dokaza (glej opis modula) sme hkrati čakati. Živijo
#: do konca dneva, ne do praznjenja, zato imajo svojo mejo. Kdor pride čez
#: njo, se še vedno šteje v promet in med obiskovalce; izgubi se le pripis
#: njegovega prvega ogleda v razreze, če se kasneje izkaže za človeka. Pri
#: 94 skenerjih na dan je meja petdesetkrat nad izmerjenim.
NAJVEC_CAKAJOCIH = 5_000

#: Kar ni nobena naša pot. Vse take zahteve gredo v eno samo vrstico: brez
#: tega bi en sam bot, ki ugiba `/wp-admin/…`, naredil tisoče vrstic na dan.
NEZNANO = "(neznano)"

# Samopredstavitev programja. Nihče od teh ni človek in vsi bi popačili
# številko, zaradi katere ta modul obstaja. Ujame tudi naš lastni chromium
# (`--headless`) iz `scripts/preveri.sh` in `curl` iz istega skripta.
#
# `python-` brez naštevanja knjižnic: prva različica je imela
# `python-requests|python-httpx` in **spregledala `Python-urllib`**, s katerim
# je tekel naš lastni preizkus hitrosti -- 2 012 zahtev se je v pregledu
# pokazalo kot „računalnik". Ujeto na zaslonu, ne v testu.
_BOT = re.compile(
    r"bot\b|bot/|crawl|spider|slurp|facebookexternalhit|bingpreview|"
    r"headless|phantom|python-|python/|aiohttp|okhttp|"
    r"curl/|wget|scrapy|go-http-client|java/|libwww|"
    r"uptime|pingdom|monitor|probe|scanner|nuclei|zgrab|masscan",
    re.I)
#: Roboti, ki jih hočemo videti po imenu: iskalniki in AI. Vprašanje, na
#: katerega odgovarjajo, je „ali nas kdo sploh bere“ -- 29. 9. 2026
#: `site:kajros.app` ni vrnil ničesar in ni bilo mogoče reči, ali je Google
#: stran sploh obiskal. Ime je tisto, s katerim se robot predstavi sam; kdor
#: hoče, se predstavi za Googlebot, zato v pregledu piše „po predstavitvi“.
#:
#: Iskano je kot podniz v malih črkah, prvi zadetek velja. Kar ni na seznamu,
#: a je bot, šteje `_BOT` kot doslej.
ROBOTI = (
    # iskalniki
    "Googlebot", "Google-InspectionTool", "GoogleOther", "Storebot-Google",
    "bingbot", "BingPreview", "DuckDuckBot", "YandexBot", "Applebot",
    "SeznamBot", "PetalBot", "Baiduspider",
    # iskanje z AI in odpiranje strani na zahtevo uporabnika
    "OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User",
    "PerplexityBot", "Perplexity-User", "DuckAssistBot", "MistralAI-User",
    # učenje modelov (Cloudflare jih 29. 9. 2026 zavrača s 403)
    "GPTBot", "ClaudeBot", "CCBot", "Amazonbot",
    "Bytespider", "meta-externalagent",
    # predogled povezave
    "facebookexternalhit", "Twitterbot", "Slackbot", "TelegramBot",
    "WhatsApp", "Discordbot",
)
_ROBOTI_MALE = tuple((ime.lower(), ime) for ime in ROBOTI)


#: Od kod je človek prišel: ime vira po gostitelju v `Referer`. Shrani se samo
#: ime (Google, ChatGPT …), nikoli naslov, s katerega je prišel -- iskalni niz
#: bi lahko povedal več o človeku kot o strani. Vrstni red šteje: Gemini je
#: pod `google.com`, zato pred Googlom. Ime s piko je domena (tudi njene
#: poddomene), brez pike oznaka kjerkoli v imenu gostitelja (`google.si`,
#: `com.google.android.googlequicksearchbox` iz aplikacije Google).
_VIRI = (
    ("gemini.google.com", "Gemini"), ("google", "Google"),
    ("bing.com", "Bing"),
    ("duckduckgo.com", "DuckDuckGo"), ("search.brave.com", "Brave"),
    ("ecosia.org", "Ecosia"), ("yandex", "Yandex"),
    ("chatgpt.com", "ChatGPT"), ("openai.com", "ChatGPT"),
    ("perplexity.ai", "Perplexity"), ("claude.ai", "Claude"),
    ("copilot.microsoft.com", "Copilot"), ("grok.com", "Grok"),
    ("t.co", "X"), ("x.com", "X"), ("twitter.com", "X"),
    ("reddit.com", "Reddit"), ("facebook.com", "Facebook"),
    ("instagram.com", "Instagram"), ("slo-tech.com", "Slo-Tech"),
    ("zamudil.si", "zamudil.si"), ("brezavta.si", "brezavta.si"),
)
#: Največ znakov imena neznanega vira; ključ ne sme rasti s smetmi v glavi.
_VIR_DOLZINA = 40


def vir_obiska(referer: str, utm: str | None = None) -> str | None:
    """Ime vira, s katerega je prišel obiskovalec, ali `None` (naravnost,
    z naše strani ali brez glave).

    ChatGPT glave pogosto ne pošlje, doda pa `?utm_source=chatgpt.com`.
    """
    if utm:
        ime = _znan_vir(utm.strip().lower())
        if ime:
            return ime
    if not referer:
        return None
    gost = (urlsplit(referer).hostname or "").lower()
    if not gost or _ujema(gost, _NAS):
        return None
    return _znan_vir(gost) or gost.removeprefix("www.")[:_VIR_DOLZINA]


def _ujema(gost: str, iskano: str) -> bool:
    # Podniz ne zadošča: „reddit.com“ vsebuje „t.co“, „dropbox.com“ „x.com“.
    if "." in iskano:
        return gost == iskano or gost.endswith("." + iskano)
    return iskano in gost.split(".")


def _znan_vir(gost: str) -> str | None:
    for iskano, ime in _VIRI:
        if _ujema(gost, iskano):
            return ime
    return None


def robot(ua: str) -> str | None:
    """Ime znanega robota iz UA ali `None`."""
    male = (ua or "").lower()
    for iskano, ime in _ROBOTI_MALE:
        if iskano in male:
            return ime
    return None


# Vrstni red šteje: tablični Android nima „Mobi“, iPad pa se v novem
# iPadOS predstavlja kot Macintosh -- tega ne ujamemo in pade med računalnike.
_TABLICA = re.compile(r"iPad|Tablet|PlayBook|Silk", re.I)
_TELEFON = re.compile(r"Mobi|Android|iPhone|iPod|Windows Phone|Opera Mini", re.I)


SHEMA = """
-- Števci po poti in dnevu. `vrsta` loči stran od klica API -- brez tega je
-- „ogledov strani“ nerazločljivo od anketiranja, ki teče v ozadju zavihka.
CREATE TABLE IF NOT EXISTS obisk_pot (
    dan      TEXT    NOT NULL,
    pot      TEXT    NOT NULL,     -- oblika poti, ne naslov: /app/train/{train_no}
    vrsta    TEXT    NOT NULL,     -- stran | api | drugo
    zahtev   INTEGER NOT NULL DEFAULT 0,
    ljudi    INTEGER NOT NULL DEFAULT 0,   -- od tega tistih, ki niso boti
    napak4   INTEGER NOT NULL DEFAULT 0,
    napak5   INTEGER NOT NULL DEFAULT 0,
    ms_vsota REAL    NOT NULL DEFAULT 0,
    ms_naj   REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (dan, pot, vrsta)
);

-- Razrezi, ki so vsi iste oblike (ura dneva, naprava, država, prenos).
-- Ena tabela in ne štiri: nov razrez je s tem nov `razsez`, ne nova tabela
-- in nova migracija. Pri `prenos` (ključ je ime APK) in `prenos_iz`
-- (`stran` | `aplikacija`) je `zahtev` število prenosov.
CREATE TABLE IF NOT EXISTS obisk_razrez (
    dan     TEXT    NOT NULL,
    razsez  TEXT    NOT NULL,      -- ura | naprava | drzava | prenos | prenos_iz | robot | vir
    kljuc   TEXT    NOT NULL,
    zahtev  INTEGER NOT NULL DEFAULT 0,
    ogledov INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dan, razsez, kljuc)
);

-- Ena vrstica na obiskovalca na dan. `kljuc` je zgoščena vrednost s soljo,
-- ki se ob polnoči zavrže -- ista naprava ima jutri drug ključ in povezave
-- med dnevoma ni. To je namerno; glej opis modula.
CREATE TABLE IF NOT EXISTS obiskovalec (
    dan      TEXT    NOT NULL,
    kljuc    TEXT    NOT NULL,
    bot      INTEGER NOT NULL DEFAULT 0,
    zahtev   INTEGER NOT NULL DEFAULT 0,
    ogledov  INTEGER NOT NULL DEFAULT 0,
    js       INTEGER,              -- zahtev, ki jih pošlje le pognan JS; NULL = pred 15. 9. 2026
    aplikacija TEXT,               -- različica naše aplikacije (`Kajros/1.2`); NULL = ni prišel iz nje
    okno     INTEGER,              -- od tega zahtev iz okna aplikacije, ne iz pripomočka ali budilke
    prvi_s   INTEGER NOT NULL,
    zadnji_s INTEGER NOT NULL,
    PRIMARY KEY (dan, kljuc)
);
CREATE INDEX IF NOT EXISTS obiskovalec_dan ON obiskovalec(dan, bot);

-- Porazdelitev odzivnega časa po razredih (`VEDRA`). Mediana in p95 se iz
-- nje izračunata na razred natančno; povprečje da `obisk_pot.ms_vsota`.
CREATE TABLE IF NOT EXISTS obisk_odziv (
    dan   TEXT    NOT NULL,
    pot   TEXT    NOT NULL,
    vedro INTEGER NOT NULL,
    n     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dan, pot, vedro)
);
"""

# --------------------------------------------------------------- zbiranje

_zaklep = threading.Lock()
# (dan, pot, vrsta) -> [zahtev, ljudi, napak4, napak5, ms_vsota, ms_naj]
_poti: dict[tuple[str, str, str], list] = {}
# (dan, razsez, kljuc) -> [zahtev, ogledov]
_razrezi: dict[tuple[str, str, str], list] = {}
# (dan, kljuc) -> [bot, zahtev, ogledov, js, prvi_s, zadnji_s, aplikacija, okno]
_ljudje: dict[tuple[str, str], list] = {}
# (dan, pot, vedro) -> n
_odzivi: dict[tuple[str, str, int], int] = {}
# dan -> sol. Samo v pomnilniku; v bazo gre ob praznjenju, da restart sredi
# dneva istega obiskovalca ne razdeli na dva.
_soli: dict[str, bytes] = {}
_prelito = False                  # ali smo zadeli NAJVEC_KLJUCEV
# (dan, kljuc) -> {("pot", pot, vrsta) | ("razrez", razsez, k): [zahtev, ogledov]}
# Kar bi obiskovalec prispeval kot človek, dokler tega ne dokaže. Ne prazni
# se ob praznjenju, ampak ob prehodu dneva -- dokaz pride lahko minuto kasneje.
_cakajoci: dict[tuple[str, str], dict[tuple[str, str, str], list]] = {}
# (dan, kljuc) obiskovalcev, ki so dokazali, da so pognali stran. Restart ga
# pobriše; posledica je le, da naslednji ogled spet počaka na prvi klic API,
# ki na vsaki strani pride v sekundi.
_dokazani: set[tuple[str, str]] = set()


def init(conn: sqlite3.Connection) -> None:
    """Ustvari tabele in prevzame današnjo sol, če je proces že tekel."""
    conn.executescript(SHEMA)
    stolpci = {r[1] for r in conn.execute("PRAGMA table_info(obiskovalec)")}
    if "js" not in stolpci:
        # Brez privzete vrednosti: za stare vrstice ne vemo, ali so pognale
        # JS, in ničla bi trdila, da niso -- vsa zgodovina bi čez noč postala
        # boti. NULL `pregled()` šteje po starem pravilu.
        conn.execute("ALTER TABLE obiskovalec ADD COLUMN js INTEGER")
    if "aplikacija" not in stolpci:
        conn.execute("ALTER TABLE obiskovalec ADD COLUMN aplikacija TEXT")
        conn.execute("ALTER TABLE obiskovalec ADD COLUMN okno INTEGER")
    # Od kdaj se aplikacija šteje. Pred tem dnem je NULL v `aplikacija`
    # „ne vemo“, ne „ni je bilo“, in pregled ga mora tako tudi pokazati.
    if not db.get_meta(conn, "obisk_aplikacija_od"):
        db.set_meta(conn, "obisk_aplikacija_od", _danes())
    conn.commit()
    shranjeno = db.get_meta(conn, "obisk_sol")
    if shranjeno and ":" in shranjeno:
        dan, _, hex_ = shranjeno.partition(":")
        if dan == _danes():
            with _zaklep:
                _soli[dan] = bytes.fromhex(hex_)


def _danes() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def sol(dan: str) -> bytes:
    """Sol dneva. Nastane ob prvi rabi in se ob prehodu dneva zavrže."""
    with _zaklep:
        if dan not in _soli:
            _soli.clear()         # včerajšnje soli ne hranimo niti v pomnilniku
            _soli[dan] = secrets.token_bytes(16)
        return _soli[dan]


def kljuc_obiskovalca(ip: str, ua: str, dan: str) -> str:
    """Šestnajst znakov, iz katerih ni poti nazaj do naslova.

    `blake2s` in ne `sha256`: razlika je nezaznavna, a funkcija sprejme sol
    kot `key` in ne kot zlepljen niz, kar je manj priložnosti za napako.
    """
    h = hashlib.blake2s(key=sol(dan), digest_size=8)
    h.update(ip.encode("utf-8", "replace"))
    h.update(b"\x00")
    h.update(ua.encode("utf-8", "replace"))
    return h.hexdigest()


def je_bot(ua: str) -> bool:
    if not ua:
        return True               # brskalnik se vedno predstavi; program ne
    return bool(_BOT.search(ua))


def je_dokaz(pot: str, vrsta: str, koda: int) -> bool:
    """Ali zahtevo pošlje samo brskalnik, ki je stran res pognal.

    `/sw.js` registrira `common.js`, `/api/…` kliče vsaka stran. Napaka ni
    dokaz: skener, ki ugiba `/api/v1/…`, dobi 404 in ni zato nič bolj človek.
    """
    if koda >= 400:
        return False
    return vrsta == "api" or pot == "/sw.js"


def ua_za_kljuc(ua: str) -> str:
    """User-Agent, kakor gre v ključ obiskovalca.

    Aplikacija za Android govori z dvema glasovoma: WebView pošlje UA Chroma s
    pripono ` Kajros/1.0`, budilka in preverjanje posodobitve pa
    `Kajros/1.0 (Android)`. Ista naprava je bila zato dva obiskovalca --
    15. 9. 2026 v bazi kot par z enakim prvim in zadnjim dotikom na sekundo.
    Dve osebi z aplikacijo za istim naslovom se s tem zlijeta v eno; to je
    redkeje kot vsaka raba aplikacije.
    """
    return "Kajros" if "Kajros/" in ua else ua


def naprava(ua: str) -> str:
    # Naš lastni ovoj za Android: budilka se predstavi kot `Kajros/<različica>`,
    # WebView pa doda ` Kajros/<različica>` na konec UA Chroma. Budilka vpraša
    # strežnik tudi takrat, ko nihče ne gleda, zato ne sme pasti med telefone;
    # ogledi v WebView pa so ogledi v aplikaciji, ne v brskalniku. Oboje loči
    # stolpec ogledov -- budilka jih nima.
    if "Kajros/" in ua:
        return "aplikacija"
    if not ua:
        return "neznano"
    if _TABLICA.search(ua):
        return "tablica"
    if _TELEFON.search(ua):
        return "telefon"
    return "računalnik"


_RAZLICICA = re.compile(r"Kajros/(\d{1,3}(?:\.\d{1,3}){0,3})\b")


def aplikacija(ua: str) -> tuple[str | None, bool]:
    """(različica, iz okna) za zahtevo naše aplikacije; (None, False) sicer.

    Okno je WebView, ki doda ` Kajros/1.2` na konec UA Chroma -- tam človek
    aplikacijo gleda. Pripomoček, budilka in preverjanje posodobitve pa se
    predstavijo kot `Kajros/1.2 (Android)` in tečejo tudi takrat, ko je
    nihče ne odpre. Brez tega ločevanja bi bil pripomoček na domačem zaslonu
    vsak dan „uporabnik aplikacije“.

    Različica gre v bazo samo kot števke in pike: UA lahko pošlje kdorkoli in
    s čimerkoli, in `Kajros/<script>` naj bo v bazi `?`, ne niz napadalca.
    """
    if "Kajros/" not in ua:
        return None, False
    m = _RAZLICICA.search(ua)
    return (m.group(1) if m else "?"), not ua.startswith("Kajros/")


def prenos(pot: str, metoda: str, koda: int, obmocje: str) -> str | None:
    """Ime APK, kadar je zahteva začetek prenosa; sicer None.

    Prenos je en `GET` s 200 -- ali 206 od prvega bajta, ker ga upravitelj
    prenosov lahko začne z `Range: bytes=0-`. Nadaljevanje prekinjenega
    prenosa (`bytes=40000-`) ni nov prenos, `HEAD` in 304 pa sploh ne.
    """
    if metoda != "GET" or not pot.startswith("/prenos/") or not pot.endswith(".apk"):
        return None
    if koda == 200 or (koda == 206 and obmocje.replace(" ", "").startswith("bytes=0-")):
        return pot.rsplit("/", 1)[1][:64]
    return None


#: Strani za človeka zunaj `/app`. Do 29. 9. 2026 so bile pristajalne in
#: besedilne strani „drugo“: ogledi se niso šteli, v pregledu „Katere strani“
#: jih ni bilo -- prav tistih, na katere pride človek z iskalnika.
#:
#: `/brez-omrezja` ni med njimi: s strežnika jo vleče samo service worker ob
#: namestitvi (`cache.addAll`), človek jo vidi iz predpomnilnika, brez
#: zahteve. Kot stran je bila 2. 10. 2026 271 „ogledov“ od 1528.
_STRANI = ("/vlak/", "/avtobus/", "/postaja/", "/postajalisce/", "/postaje",
           "/postajalisca", "/o-nas", "/primerjava", "/stik", "/zasebnost",
           "/android", "/donacije")


#: Klik na „Podari“ gre prek naše poti, ki preusmeri na Ko-fi: drugače ne bi
#: nikoli izvedeli, koliko od ljudi na `/donacije` je šlo res naprej. Ni stran
#: (ogled bi napihnil `ogledov`), v `obisk_pot` je pa vseeno vrstica s `ljudi`.
DONACIJE_NAPREJ = "/donacije/naprej"


def vrsta_poti(pot: str) -> str:
    if pot == DONACIJE_NAPREJ:
        return "drugo"
    if pot == "/" or pot.startswith("/app") or pot.startswith(_STRANI):
        return "stran"
    if pot.startswith("/api"):
        return "api"
    return "drugo"


def vedro(ms: float) -> int:
    for i, meja in enumerate(VEDRA):
        if ms <= meja:
            return i
    return len(VEDRA)


def zabelezi(pot: str, vrsta: str, kljuc: str, bot: bool, naprava_: str,
             drzava: str, koda: int, ms: float, zdaj: float | None = None,
             ura: int | None = None, dan: str | None = None,
             razlicica: str | None = None, okno: bool = False,
             prenesel: tuple[str, str] | None = None,
             robot_ime: str | None = None, vir: str | None = None) -> None:
    """Doda eno zahtevo v števce. Samo pomnilnik -- v bazo gre `izprazni()`.

    `prenesel` je (datoteka, od kod) za začetek prenosa APK; glej `prenos()`.
    `robot_ime` je ime iz `ROBOTI`; gre v razrez `robot`, ki šteje zahteve in
    oglede strani, a ne ljudi. `vir` je `vir_obiska()`.

    **Prihod z znanega vira je dokaz, da je človek.** Pristajalne strani nimajo
    JS -- kdor pride z Googla nanje in odide, dokaza po starem ne pošlje in
    ga ne bi šteli nikoli. Googlebot glave `Referer` z Googla ne pošilja.
    """
    global _prelito
    zdaj = time.time() if zdaj is None else zdaj
    trenutek = datetime.fromtimestamp(zdaj, TZ)
    dan = dan or trenutek.strftime("%Y-%m-%d")
    ura = trenutek.hour if ura is None else ura
    ogled = 1 if vrsta == "stran" else 0
    znan_vir = vir is not None and any(vir == ime for _, ime in _VIRI)
    dokaz = je_dokaz(pot, vrsta, koda) or (bool(ogled) and znan_vir and koda < 400)
    with _zaklep:
        if len(_poti) + len(_razrezi) + len(_ljudje) > NAJVEC_KLJUCEV:
            _prelito = True
            return
        p = _poti.setdefault((dan, pot, vrsta), [0, 0, 0, 0, 0.0, 0.0])
        p[0] += 1
        p[2] += 1 if 400 <= koda < 500 else 0
        p[3] += 1 if koda >= 500 else 0
        p[4] += ms
        p[5] = max(p[5], ms)

        kljuc_odziv = (dan, pot, vedro(ms))
        _odzivi[kljuc_odziv] = _odzivi.get(kljuc_odziv, 0) + 1

        # Razrezi in `ljudi` so vprašanje o ljudeh, ne o strojih. Bot, ki vsako
        # uro pobere sitemap, bi sicer narisal enakomeren dan in ubil edino
        # zanimivo črto -- kdaj se ljudje res peljejo. Brskalnik brez dokaza
        # čaka; glej opis modula.
        if not bot:
            prispevek = {("pot", pot, vrsta): [1, 0]}
            for razsez, k in (("ura", f"{ura:02d}"), ("naprava", naprava_),
                              ("drzava", drzava)):
                prispevek[("razrez", razsez, k)] = [1, ogled]
            if vir and ogled:
                prispevek[("razrez", "vir", vir)] = [1, 1]
            obiskovalec = (dan, kljuc)
            if dokaz and obiskovalec not in _dokazani:
                _dokazani.add(obiskovalec)
                _pripisi(dan, _cakajoci.pop(obiskovalec, {}))
            if obiskovalec in _dokazani:
                _pripisi(dan, prispevek)
            elif obiskovalec in _cakajoci or len(_cakajoci) < NAJVEC_CAKAJOCIH:
                caka = _cakajoci.setdefault(obiskovalec, {})
                for k, (n, og) in prispevek.items():
                    c = caka.setdefault(k, [0, 0])
                    c[0] += n
                    c[1] += og
            # Prenos ne čaka na dokaz: `/android` nima JS in kdor pride
            # naravnost nanjo -- iz iskalnika ali iz vrstice o posodobitvi --
            # dokaza ne pošlje nikoli. Bot se izloči po UA kot povsod.
            if prenesel:
                _pripisi(dan, {("razrez", "prenos", prenesel[0]): [1, 0],
                               ("razrez", "prenos_iz", prenesel[1]): [1, 0]})

        if robot_ime:
            _pripisi(dan, {("razrez", "robot", robot_ime): [1, ogled]})

        o = _ljudje.setdefault((dan, kljuc),
                               [0, 0, 0, 0, int(zdaj), int(zdaj), None, 0])
        o[0] = max(o[0], int(bot))
        o[1] += 1
        o[2] += ogled
        o[3] += int(dokaz)
        o[4] = min(o[4], int(zdaj))
        o[5] = max(o[5], int(zdaj))
        o[6] = razlicica or o[6]
        o[7] += int(okno)


def _pripisi(dan: str, prispevek: dict) -> None:
    """Prispevek človeka v števce poti in razrezov. Kliče se pod `_zaklep`."""
    for (kam, a, b), (n, og) in prispevek.items():
        if kam == "pot":
            _poti.setdefault((dan, a, b), [0, 0, 0, 0, 0.0, 0.0])[1] += n
        else:
            r = _razrezi.setdefault((dan, a, b), [0, 0])
            r[0] += n
            r[1] += og


def ip_zahteve(glave, odjemalec: str | None) -> str:
    """Naslov obiskovalca izza posrednika.

    `CF-Connecting-IP` postavi Cloudflare in je edini, ki mu tu smemo verjeti:
    do procesa ne pride nič drugega kot tunel ali domače omrežje, ker
    strežnik ni izpostavljen naravnost (`docs/javna-postavitev.md`). Naslov
    se ne shrani -- gre samo skozi `kljuc_obiskovalca()`.
    """
    za = glave.get("cf-connecting-ip") or glave.get("x-forwarded-for") or ""
    if za:
        return za.split(",")[0].strip()
    return odjemalec or "?"


def iz_zahteve(request, koda: int, ms: float) -> None:
    """Zabeleži eno postreženo zahtevo. Kliče jo posrednik v `api.py`."""
    pot = oblika_poti(request)
    if pot is None:
        return
    glave = request.headers
    ua = glave.get("user-agent", "")
    ime_robota = robot(ua)
    vir = vir_obiska(glave.get("referer", ""),
                     request.query_params.get("utm_source"))
    # `Claude-User` in `Perplexity-User` besede „bot“ nimata, a človek nista.
    bot = je_bot(ua) or ime_robota is not None
    razlicica, okno = aplikacija(ua)
    apk = prenos(request.url.path, request.method, koda, glave.get("range", ""))
    # `?iz=aplikacija` nosi povezava iz vrstice o posodobitvi v aplikaciji
    # (`/api/android/razlicica`); brez nje je prenos nekoga, ki je prišel na
    # stran sam -- večinoma nova namestitev.
    iz = "aplikacija" if request.query_params.get("iz") == "aplikacija" else "stran"
    zabelezi(pot=pot, vrsta=vrsta_poti(request.url.path),
             kljuc=kljuc_obiskovalca(ip_zahteve(glave, _odjemalec(request)),
                                     ua_za_kljuc(ua), _danes()),
             bot=bot, naprava_=naprava(ua),
             drzava=(glave.get("cf-ipcountry") or "??").upper()[:2],
             koda=koda, ms=ms, razlicica=razlicica, okno=okno,
             prenesel=(apk, iz) if apk else None, robot_ime=ime_robota,
             vir=vir)


def _odjemalec(request) -> str | None:
    odj = getattr(request, "client", None)
    return getattr(odj, "host", None) if odj else None


# Oblike poti gradimo iz usmerjevalnika samega, ne iz seznama v kodi: sicer
# se ob novi strani seznam tiho razide in nova stran pade med `(neznano)`.
_vzorci: list[tuple] | None = None


def _zgradi_vzorce(app) -> list[tuple]:
    out = []
    for route in getattr(app, "routes", []):
        rx = getattr(route, "path_regex", None)
        oblika = getattr(route, "path_format", None)
        if rx is not None and oblika:
            out.append((rx, oblika))
    return out


def oblika_poti(request) -> str | None:
    """`/app/train/2010` -> `/app/train/{train_no}`; statika in admin -> nič.

    Brez tega ima vsaka vožnja svojo vrstico in tabela zraste s prometom, ne
    s številom strani. `None` pomeni „ne štej“.
    """
    global _vzorci
    pot = request.url.path
    if pot.startswith("/static") or pot.startswith("/admin"):
        return None
    if _vzorci is None:
        _vzorci = _zgradi_vzorce(request.scope.get("app"))
    for rx, oblika in _vzorci:
        if rx.match(pot):
            return oblika
    return NEZNANO


# -------------------------------------------------------------- praznjenje

def izprazni(conn: sqlite3.Connection) -> int:
    """Števce iz pomnilnika v bazo. Vrne število zapisanih vrstic.

    Ob napaki so števci že vzeti iz pomnilnika in torej izgubljeni. To je
    namerno: vrnitev nazaj bi ob trajni napaki pomnilnik polnila brez konca,
    izguba minute statistike obiska pa ne pokvari ničesar, kar bi bilo
    kasneje treba popraviti -- za razliko od meritve zamude.
    """
    global _prelito
    with _zaklep:
        if not (_poti or _razrezi or _ljudje or _odzivi):
            return 0
        poti = [(d, p, v, *st) for (d, p, v), st in _poti.items()]
        razrezi = [(d, r, k, *st) for (d, r, k), st in _razrezi.items()]
        ljudje = [(d, k, *st) for (d, k), st in _ljudje.items()]
        odzivi = [(d, p, ve, n) for (d, p, ve), n in _odzivi.items()]
        dan_soli = max(_soli) if _soli else None
        sol_ = _soli.get(dan_soli) if dan_soli else None
        preliv = _prelito
        _poti.clear(); _razrezi.clear(); _ljudje.clear(); _odzivi.clear()
        _prelito = False
        # Včerajšnji čakajoči niso dokazali ničesar in ne bodo: jutri imajo
        # drug ključ.
        danes = _danes()
        for k in [k for k in _cakajoci if k[0] < danes]:
            del _cakajoci[k]
        _dokazani.difference_update([k for k in _dokazani if k[0] < danes])

    with conn:
        conn.executemany(
            "INSERT INTO obisk_pot(dan, pot, vrsta, zahtev, ljudi, napak4, napak5,"
            "                      ms_vsota, ms_naj) VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(dan, pot, vrsta) DO UPDATE SET "
            "  zahtev = zahtev + excluded.zahtev, ljudi = ljudi + excluded.ljudi,"
            "  napak4 = napak4 + excluded.napak4, napak5 = napak5 + excluded.napak5,"
            "  ms_vsota = ms_vsota + excluded.ms_vsota,"
            "  ms_naj = MAX(ms_naj, excluded.ms_naj)", poti)
        conn.executemany(
            "INSERT INTO obisk_razrez(dan, razsez, kljuc, zahtev, ogledov)"
            " VALUES(?,?,?,?,?) "
            "ON CONFLICT(dan, razsez, kljuc) DO UPDATE SET "
            "  zahtev = zahtev + excluded.zahtev,"
            "  ogledov = ogledov + excluded.ogledov", razrezi)
        conn.executemany(
            "INSERT INTO obiskovalec(dan, kljuc, bot, zahtev, ogledov, js, prvi_s, zadnji_s,"
            "                        aplikacija, okno)"
            " VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(dan, kljuc) DO UPDATE SET "
            "  bot = MAX(bot, excluded.bot), zahtev = zahtev + excluded.zahtev,"
            "  ogledov = ogledov + excluded.ogledov,"
            "  js = COALESCE(js, 0) + excluded.js,"
            "  prvi_s = MIN(prvi_s, excluded.prvi_s),"
            "  zadnji_s = MAX(zadnji_s, excluded.zadnji_s),"
            "  aplikacija = COALESCE(excluded.aplikacija, aplikacija),"
            "  okno = COALESCE(okno, 0) + excluded.okno", ljudje)
        conn.executemany(
            "INSERT INTO obisk_odziv(dan, pot, vedro, n) VALUES(?,?,?,?) "
            "ON CONFLICT(dan, pot, vedro) DO UPDATE SET n = n + excluded.n", odzivi)
        if sol_ is not None:
            # Sol preživi restart, dneva pa ne: ključ je `obisk_sol` in ne
            # `obisk_sol_<dan>`, zato jo naslednji dan povozi in včerajšnje
            # ni več nikjer.
            db.set_meta(conn, "obisk_sol", f"{dan_soli}:{sol_.hex()}")
        if preliv:
            db.set_meta(conn, "obisk_preliv", datetime.now(TZ).isoformat())
    return len(poti) + len(razrezi) + len(ljudje) + len(odzivi)


def prune(conn: sqlite3.Connection, dni: int | None = None) -> int:
    """Pobriše števce, starejše od `dni`. Vrne število pobrisanih vrstic."""
    dni = config.OBISK_KEEP_DAYS if dni is None else dni
    if dni <= 0:
        return 0
    meja = (datetime.now(TZ).date().toordinal() - dni)
    meja_iso = datetime.fromordinal(meja).strftime("%Y-%m-%d")
    n = 0
    with conn:
        for tabela in ("obisk_pot", "obisk_razrez", "obiskovalec", "obisk_odziv"):
            n += conn.execute(f"DELETE FROM {tabela} WHERE dan < ?", (meja_iso,)).rowcount
    return n


# ----------------------------------------------------------------- pregled

def _percentil(vedra: dict[int, int], p: float) -> dict:
    """Razred, v katerem leži p-ti percentil. Ne vrednost -- razred.

    Točnega časa ne hranimo, zato je pošteno povedati mejo razreda in ne
    izmišljene številke: `{"do": 250}` pomeni „hitreje od 250 ms“,
    `{"do": None}` pa „počasneje od zadnje meje“.
    """
    skupaj = sum(vedra.values())
    if not skupaj:
        return {"do": None, "n": 0}
    cilj = skupaj * p
    tekoce = 0
    for i in range(len(VEDRA) + 1):
        tekoce += vedra.get(i, 0)
        if tekoce >= cilj:
            return {"do": VEDRA[i] if i < len(VEDRA) else None, "n": skupaj}
    return {"do": None, "n": skupaj}


def prejsnje_obdobje(od: str, do: str) -> tuple[str, str]:
    """Obdobje, s katerim se `od`–`do` primerja.

    Cel koledarski mesec se primerja s prejšnjim mesecem in celo leto s
    prejšnjim letom, vse ostalo pa z enako dolgim odsekom tik pred njim.
    Premik za enako število dni bi september (30) primerjal z 2. 8.–31. 8.,
    kar ni noben mesec, ki bi ga kdo imel v glavi.
    """
    a, b = date.fromisoformat(od), date.fromisoformat(do)
    if a.day == 1 and (b + timedelta(days=1)).day == 1 and a.month == b.month:
        konec = a - timedelta(days=1)
        return konec.replace(day=1).isoformat(), konec.isoformat()
    if (a.month, a.day, b.month, b.day) == (1, 1, 12, 31) and a.year == b.year:
        return date(a.year - 1, 1, 1).isoformat(), date(a.year - 1, 12, 31).isoformat()
    n = (b - a).days + 1
    return (a - timedelta(days=n)).isoformat(), (a - timedelta(days=1)).isoformat()


#: Človek je, kdor se ne predstavi kot bot IN je pognal JS. Vrstice pred
#: stolpcem `js` (NULL) štejejo po starem pravilu -- zanje tega ne vemo, in
#: ničla bi jih vse naredila za bote. `js_od` pove, od kdaj velja novo.
_CLOVEK = "o.bot = 0 AND COALESCE(o.js, 1) > 0"
#: Aplikacija: človek, ki je prišel iz nje. `app` jo je odprl, `app_ozadje`
#: pa je samo pripomoček ali budilka -- nameščena je, pogledal je ni.
_APP = f"{_CLOVEK} AND o.aplikacija IS NOT NULL"
_PO_DNEVIH_SQL = (
    "SELECT o.dan,"
    f"      SUM(CASE WHEN {_CLOVEK} THEN 1 ELSE 0 END) AS ljudi,"
    "       SUM(CASE WHEN o.bot = 1 THEN 1 ELSE 0 END) AS botov,"
    "       SUM(CASE WHEN o.bot = 0 AND o.js = 0 THEN 1 ELSE 0 END) AS brez_js,"
    f"      SUM(CASE WHEN {_CLOVEK} THEN o.ogledov ELSE 0 END) AS ogledov,"
    "       SUM(o.zahtev) AS zahtev,"
    f"      SUM(CASE WHEN {_APP} AND o.okno > 0 THEN 1 ELSE 0 END) AS app,"
    f"      SUM(CASE WHEN {_APP} AND COALESCE(o.okno, 0) = 0 THEN 1 ELSE 0 END) AS app_ozadje "
    "FROM obiskovalec o WHERE o.dan BETWEEN ? AND ? GROUP BY o.dan ORDER BY o.dan")
_PRENOSI_SQL = (
    "SELECT dan, kljuc, SUM(zahtev) AS n FROM obisk_razrez "
    "WHERE razsez = 'prenos_iz' AND dan BETWEEN ? AND ? GROUP BY dan, kljuc")


def _po_dnevih(conn: sqlite3.Connection, od: str, do: str) -> list[dict]:
    """Dnevne vrstice obiskovalcev s prenosi APK tistega dne."""
    vrstice = [dict(r) for r in conn.execute(_PO_DNEVIH_SQL, (od, do))]
    prenosi: dict[str, dict[str, int]] = {}
    for r in conn.execute(_PRENOSI_SQL, (od, do)):
        prenosi.setdefault(r["dan"], {})[r["kljuc"]] = r["n"]
    for d in vrstice:
        p = prenosi.get(d["dan"], {})
        d["prenosov"] = sum(p.values())
        d["prenosov_iz_aplikacije"] = p.get("aplikacija", 0)
    return vrstice


def _vsota_dni(vrstice: list[dict]) -> dict:
    return {
        "ljudi_vsota": sum(d["ljudi"] for d in vrstice),
        "ogledov": sum(d["ogledov"] for d in vrstice),
        "zahtev": sum(d["zahtev"] for d in vrstice),
        "botov_vsota": sum(d["botov"] for d in vrstice),
        "brez_js_vsota": sum(d["brez_js"] for d in vrstice),
        "app_vsota": sum(d["app"] for d in vrstice),
        "app_ozadje_vsota": sum(d["app_ozadje"] for d in vrstice),
        "prenosov": sum(d["prenosov"] for d in vrstice),
        "prenosov_iz_aplikacije": sum(d["prenosov_iz_aplikacije"] for d in vrstice),
        "dni": len(vrstice),
    }


def pregled(conn: sqlite3.Connection, od: str | None = None,
            do: str | None = None) -> dict:
    """Vse, kar pokaže stran `/admin`, za obdobje `od`–`do` (privzeto danes).

    **Mesečnega števila različnih ljudi tu ni in ga ne more biti.** Sol se
    vsak dan zavrže, zato je ista naprava jutri drug ključ; `ljudi_vsota` je
    vsota dnevnih in isto osebo šteje tolikokrat, kolikor dni je prišla. To
    je cena zasebnosti in je zapisana tudi na strani, da je številka ne bo
    kdo bral kot mesečne unikate.

    Ne glede na obdobje nosi odgovor še `danes` in `zadnjih30`: zavihek
    „Stanje“ ju rabi vedno, in dva klica namesto enega bi bila dve številki,
    ki se lahko razideta.
    """
    danes = _danes()
    od = od or danes
    do = do or danes
    prej_od, prej_do = prejsnje_obdobje(od, do)
    pred30 = (date.fromisoformat(danes) - timedelta(days=29)).isoformat()

    po_dnevih = _po_dnevih(conn, od, do)
    prej = _po_dnevih(conn, prej_od, prej_do)
    zadnjih30 = _po_dnevih(conn, pred30, danes)
    js_od, prvi_dan = conn.execute(
        "SELECT MIN(CASE WHEN js IS NOT NULL THEN dan END), MIN(dan) "
        "FROM obiskovalec").fetchone()

    strani = [dict(r) for r in conn.execute(
        "SELECT pot, SUM(zahtev) AS zahtev, SUM(ljudi) AS ljudi "
        "FROM obisk_pot WHERE dan BETWEEN ? AND ? AND vrsta = 'stran' "
        "GROUP BY pot ORDER BY ljudi DESC, zahtev DESC", (od, do))]

    # Odzivni čas in napake: obojega ne meri nihče drug. Cloudflare vidi svoj
    # rob, ne našega izračuna, in 2,7 s za `/api/health` je pri njem videti
    # enako kot 3 ms.
    vedra: dict[str, dict[int, int]] = {}
    for r in conn.execute(
            "SELECT pot, vedro, SUM(n) AS n FROM obisk_odziv "
            "WHERE dan BETWEEN ? AND ? GROUP BY pot, vedro", (od, do)):
        vedra.setdefault(r["pot"], {})[r["vedro"]] = r["n"]

    endpointi = []
    for r in conn.execute(
            "SELECT pot, SUM(zahtev) AS zahtev, SUM(napak4) AS napak4,"
            "       SUM(napak5) AS napak5, SUM(ms_vsota) AS ms_vsota,"
            "       MAX(ms_naj) AS ms_naj "
            "FROM obisk_pot WHERE dan BETWEEN ? AND ? GROUP BY pot "
            "ORDER BY zahtev DESC", (od, do)):
        v = vedra.get(r["pot"], {})
        endpointi.append({
            "pot": r["pot"], "zahtev": r["zahtev"],
            "napak4": r["napak4"], "napak5": r["napak5"],
            "ms_povprecje": round(r["ms_vsota"] / r["zahtev"], 1) if r["zahtev"] else None,
            "ms_naj": round(r["ms_naj"], 1),
            "p50": _percentil(v, 0.50), "p95": _percentil(v, 0.95),
        })

    # Podpora: kdo je odprl `/donacije` in kdo je kliknil naprej. Klik ni
    # donacija -- plačilo teče pri ponudniku in ga ne vidimo --, je pa zgornja
    # meja, in prvi korak, ki ga sicer ne bi bilo mogoče izmeriti.
    donacije = {"ogledi": 0, "ljudi": 0, "klikov": 0, "klikov_ljudi": 0}
    for r in conn.execute(
            "SELECT pot, SUM(zahtev) AS zahtev, SUM(ljudi) AS ljudi FROM obisk_pot "
            "WHERE dan BETWEEN ? AND ? AND pot IN ('/donacije', ?) GROUP BY pot",
            (od, do, DONACIJE_NAPREJ)):
        if r["pot"] == DONACIJE_NAPREJ:
            donacije["klikov"], donacije["klikov_ljudi"] = r["zahtev"], r["ljudi"]
        else:
            donacije["ogledi"], donacije["ljudi"] = r["zahtev"], r["ljudi"]

    # Od kod po dnevih: vir je v razrezu že po dnevu, samo seštevali smo ga
    # čez obdobje. Brez tega se vrh (2. 10.) ne da pripisati objavi.
    vir_po_dnevih = [dict(r) for r in conn.execute(
        "SELECT dan, kljuc, SUM(ogledov) AS ogledov FROM obisk_razrez "
        "WHERE razsez = 'vir' AND dan BETWEEN ? AND ? GROUP BY dan, kljuc "
        "ORDER BY dan, ogledov DESC", (od, do))]

    razrezi: dict[str, list] = {}
    for r in conn.execute(
            "SELECT razsez, kljuc, SUM(zahtev) AS zahtev, SUM(ogledov) AS ogledov "
            "FROM obisk_razrez WHERE dan BETWEEN ? AND ? GROUP BY razsez, kljuc "
            "ORDER BY razsez, ogledov DESC, zahtev DESC", (od, do)):
        razrezi.setdefault(r["razsez"], []).append(dict(r))
    if "ura" in razrezi:
        razrezi["ura"].sort(key=lambda x: x["kljuc"])

    # Ljudje po različici aplikacije. Nad enim dnem je to vsota dnevnih, kot
    # povsod na tej strani -- ista naprava šteje enkrat na dan.
    razlicice = [dict(r) for r in conn.execute(
        "SELECT o.aplikacija AS kljuc, COUNT(*) AS ljudi FROM obiskovalec o "
        f"WHERE o.dan BETWEEN ? AND ? AND {_APP} "
        "GROUP BY o.aplikacija ORDER BY ljudi DESC, o.aplikacija DESC", (od, do))]

    skupaj = _vsota_dni(po_dnevih)
    skupaj["napak4"] = sum(e["napak4"] for e in endpointi)
    skupaj["napak5"] = sum(e["napak5"] for e in endpointi)
    danasnji = next((d for d in zadnjih30 if d["dan"] == danes), None)
    return {
        "od": od, "do": do, "danes_dan": danes,
        "danes": danasnji or {"dan": danes, "ljudi": 0, "botov": 0,
                              "brez_js": 0, "ogledov": 0, "zahtev": 0,
                              "app": 0, "app_ozadje": 0, "prenosov": 0,
                              "prenosov_iz_aplikacije": 0},
        "js_od": js_od, "prvi_dan": prvi_dan,
        "aplikacija_od": db.get_meta(conn, "obisk_aplikacija_od"),
        "razlicice": razlicice,
        "skupaj": skupaj,
        "prej": {"od": prej_od, "do": prej_do, **_vsota_dni(prej)},
        "po_dnevih": po_dnevih,
        "zadnjih30": zadnjih30,
        "strani": strani,
        "endpointi": endpointi,
        "razrezi": razrezi,
        "vir_po_dnevih": vir_po_dnevih,
        "donacije": donacije,
        "preliv": db.get_meta(conn, "obisk_preliv"),
    }
