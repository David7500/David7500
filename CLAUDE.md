# Kajros

Zajem in analiza **zamud slovenskega javnega prevoza** iz odprtih podatkov.
Ime je grški *kairos* — pravi trenutek, v nasprotju s *chronosom*, urnim
časom. Vozni red je chronos, resnica je kairos; razlika med njima je projekt.
Zaledje v Pythonu (FastAPI + SQLite), prikaz v vanilla JS. Zgodovine teh
podatkov ni nikjer drugje — če je ne posnamemo sami, je ni.

Veja: `claude/slovenske-zeleznice-api-ql84hf` · remote `David7500/David7500`

## Zagon

```bash
./scripts/dev-restart.sh          # počaka na sproščen port in izpiše naslove
```

Venv je `venv/` (Python 3.12), **ne** `.venv`. Strežnik med razvojem pogosto že
teče na 8001 — preveri s `pgrep -af uvicorn`, preden zaganjaš drugega.
CLI: `./venv/bin/python -m kajros.cli <ukaz>` — `init`, `update`, `poll`,
`show`, `stats`, `merge`, `weather`, `export`, `alerts`, `backtest`, `repair`,
`prune`, `ocena`, `seed`.

**Preverjanje pred „končano“: `./scripts/preveri.sh`** — testi, odzivi vseh
strani, konzola brskalnika, **pyflakes**, **skladnost številk** in paleta v
enem, z izhodno kodo. Sami testi: `./venv/bin/python -m pytest -q` (233 preizkusov).
`scripts/preveri_skladnost.py` straži napake, ki so si nasprotovale na
zaslonu: osirotele meritve, vsota razredov proti deležu točnih, razred po
zaokroženi minuti, hitrost `/api/health`, beseda namesto minusa pri prestopu.

Avtobusi se uvozijo z `KAJROS_AGENCIES=1118,1119,1121,1123`. Brez tega so v bazi
samo SŽ. **Mestni LPP je drug vir** (`KAJROS_LPP`, privzeto vklopljen): v IJPP
ga ni, ker je občinski. Podrobnosti v `.claude/rules/zajem.md`.

**Strežnik posluša na vseh vmesnikih** (`KAJROS_HOST`, privzeto `0.0.0.0`), ker je
telefon glavna preizkusna naprava. To **ni** isto kot odpiranje vrat na
usmerjevalniku: API nima avtentikacije in ga sme videti samo domače omrežje.
Za samo ta računalnik: `KAJROS_HOST=127.0.0.1 ./scripts/dev-restart.sh`.

**Prek omrežnega naslova lastna lega ne dela in to ni naša napaka.**
`navigator.geolocation` zahteva varen kontekst — HTTPS ali `localhost` — in
`http://192.168.1.164:8001` ni ne eno ne drugo (izmerjeno:
`window.isSecureContext = false`). Prikaz to pove, namesto da bi tiho čakal.

## Od kod podatki

```
SŽ + IJPP → NAP (b2b.nap.si, CC BY-SA 4.0) → DERP gtfs-generators → GTFS + GTFS-RT
```

| Kaj | Vir | Pogostost |
|---|---|---|
| Vozni red | `gitlab.com/.../IJPP/latest/ijpp_gtfs.zip` (41 MB) | ~1×/dan |
| Zamude | `rt.gtfs.derp.si/sources/ijpp/trip_updates` | 30 s |
| Mestni LPP, vse troje | `rt.gtfs.derp.si/sources/lpp/all` + `avl.lpp.si/transit/api/gtfs` | 30 s |
| Ovire in žive zamude | `.../service_alerts` | 60 s |
| Lega vozil | `.../vehicle_positions` | 10 s (`KAJROS_POSITION_SECONDS`) |
| Vreme | `open-meteo.com` (ima arhiv za nazaj) | dnevno |

SŽ nimajo javnega API-ja; `potniski.sz.si` je za Cloudflarom, stari SOAP je
mrtev. V zipu je **ves** slovenski javni potniški promet (pet agencij), ne le
železnica; `config.RAIL_AGENCY_ID` je edino, kar jih loči.

## Pravila, ki veljajo povsod

* **Model se meri na dveh merilih, ne enem.** `kajros backtest` je zgodovina
  s kratkimi skoki, `kajros ocena` pa številka, ki jo je potnik res videl 25
  minut prej. Zadnja sprememba je bila na prvem merilu za las slabša in na
  drugem mnogo boljša — brez obojega bi jo zavrgli.
* **Meri, ne domnevaj.** Vsaka trditev v teh zapisih ima za sabo številko.
  Kar ni izmerjeno, se ne zapiše kot dejstvo — in kar je, se zapiše z
  vzorcem („na 79 primerih“), da naslednji ve, koliko zaupati.
* **Nikoli ne beri `stu.arrival.delay` naravnost** — protobuf za neizpolnjeno
  polje vrne 0, kar je videti kot „točno“. Uporabljaj `collector._delay_of()`.
* **Povsod `COALESCE(delay_dep, delay_arr)`, ne obratno.** `departure.delay`
  je izpolnjen pri vseh prevoznikih stoodstotno, `arrival.delay` ne.
* **Meja med meritvijo in napovedjo je `stats.last_measured()`.** Kar je za
  zadnjim prevoženim postankom, je napoved — vsak prikaz zamude to upošteva.
  Ta napaka je bila že dvakrat na zaslonu.
* **Omrežje filtriraj znotraj poizvedbe, ne za njo** (`WHERE t.network = ?`).
  Bil je že dvakrat vzrok počasnosti.
* **V enem SQL stavku ne mešaj `?` in `:ime`** — sqlite veže po vrstnem redu
  pojavitve in tiho vrne napačne vrstice.
* **`run` hrani zadnje stanje postanka**, zato `MAX(stop_seq)` po koncu vožnje
  ni dokaz, da vozilo še vozi. Živost sklepaj iz `_LIVE_SQL`.
* **Spremembo prikaza poglej, preden jo razglasiš za končano.**
  `chromium --headless --disable-gpu --window-size=1850,1000
  --virtual-time-budget=7000 --screenshot=$PWD/posnetki/x.png <url>`.
  V `/tmp` chromium ne more pisati; `posnetki/` je v `.gitignore`. **Ne v
  `$HOME`.**

## Koda

```
kajros/
  geo.py         haversine, projekcija postaj na progo, Douglas-Peucker
  db.py          SQLite shema + merge_from() + migracije
  gtfs.py        pogojni prenos zipa, uvoz voznega reda
  collector.py   poll zamud in leg, obratovalni dan, varovalke pred smetmi
  alerts.py      ovire (SZ-OVIRA) in žive zamude s prometnim mestom (SZ-DELAY)
  weather.py     Open-Meteo, mreža 0,1° (~8 km) × 1 h
  stats.py       zgodovina, porazdelitve, napoved, dnevni povzetek
  journey.py     odhodna tabla, iskanje postaj, zveze s prestopi
  lpp.py         živi prihodi mestnega LPP (data.lpp.si), samo za prikaz
  backtest.py    merjenje napovedi z izpuščanjem enega dne
  ocena.py       senčno merjenje: kaj je prikaz trdil 25 min prej in kaj je bilo
  obisk.py       števci obiska brez IP; sol dneva, praznjenje v svoji niti
  server.py      lifespan: bootstrap + zajem v ozadnji niti
  api.py         FastAPI: /api/* + strani /app*
  cli.py         ukazna vrstica
  templates/     home, connections (vstopna), dashboard, train, alerts
  static/        base.css (barvni žetoni) + common.js + po ena .js/.css na stran
tests/           enotni testi čistih funkcij (pytest, requirements-dev.txt)
scripts/         dev-restart.sh, preveri.sh, potegni.sh, preveri_paleto.py
android/         nativni ovoj z WebView (Kotlin); orodja ločeno v ~/kajros-android
```

**Trd datum v pripravi + računan datum v testu = bomba.** Priprava vstavlja
`service_day('S1','2026-08-31')`, testi pa dan računajo (`_pred`). Na dan, ko
se datuma ujameta, je to `UNIQUE constraint failed` — zgodilo se je 31. 8. 2026
in podrlo pet zelenih preizkusov. Računani vstavki gredo zato skozi
`INSERT OR IGNORE`.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day`, `shape` (statika) ·
`obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `vehicle_now` ·
`weather` · `alert` + `alert_entity` · `delay_report` · `povzetek` · `napoved` ·
`obisk_pot` + `obisk_razrez` + `obiskovalec` + `obisk_odziv` (samo strežni stroj).

**Senčno merjenje napovedi teče ob strežniku** (`ocena.py`, vsakih 120 s).
Vsakih nekaj minut posname, kaj bi prikaz **ta hip** povedal za postanek, ki je
25 minut pred vlakom (15 pred avtobusom) — našo oceno, prevoznikovo in prenos
zamude — in ko vozilo tja pride, v isto vrstico dopiše resnico. Izid:
`kajros ocena`. To ni backtest: backtest meri model na zgodovini, to meri
**številko, ki jo je potnik res videl**. Ugasne se s `KAJROS_OCENA=0`.

## Omrežji: `network` ni `mode`

`trip.network` (`zeleznica` / `avtobus`) loči **strani aplikacije**. Nadomestni
prevoz SŽ je `mode = 'bus'`, a `network = 'zeleznica'`, ker zamenjuje vlak in
sodi v isti odgovor kot vlaki. Vsi potniški endpointi imajo `network` in
**privzeto `zeleznica`**, da mešanja ne povzroči pozabljen parameter — mešanje
je bilo merljivo škodljivo: iskanje „ljublj“ je vračalo mestna postajališča in
postajo Ljubljana potisnilo iz prvih petih zadetkov.

Kar je pri avtobusih drugače in se hitro pozabi:

* **Številka linije ni številka vožnje.** LPP linija 3G ima 388 voženj. Vsaka
  poizvedba po `train_no` mora skozi `stats.resolve_trip()`; povezave na eno
  vožnjo nosijo `?trip=<id>`. Isto velja za devet vlakov s sezonskimi
  različicami.
* **Barva linije ni barva linije.** Vsi LPP `route_color` so ista zelena
  prevoznika, zato oznaka nosi ime prevoznika in številko („LPP 25“) — in
  iskati se mora dati po tem, kar človek vidi na postajališču.
  Prevoznik je v `trip.agency` kot GTFS ID (1118, 1123 …); ime je v
  `common.AGENCY` in `stats.AGENCY_NAMES`.
* **Mestno postajališče ima svoj `stop_id` za vsako smer** („Bavarski dvor“ je
  v `station` dvakrat). Vse v aplikaciji teče po **imenu** postaje.

## Številke vlakov

`LPV 2010` ni oznaka proge, ampak **ena vožnja** (trip). `route_id` je 1 : 1 s
tripom in za združevanje neuporaben — zgodovino gradi po `train_no` **znotraj
`trip_id`**. Parnost številke nosi smer. Predpona (`LP`, `LPV`, `IC`, `MV`,
`EN` …) je vrsta vlaka; `BUS …` je nadomestni prevoz.

**`trip_id` so med regeneracijami GTFS stabilni — a ne vsi.** Ob prehodu na
šolski vozni red 1. 9. 2026 je iz `trip` izginilo **114 voženj s 3 043
meritvami** (0,37 %). Meritve so ostale, a jih ni videla nobena poizvedba: vse
gredo skozi `JOIN trip`, ker je omrežje tam. Zato uvoz zdaj **obdrži vožnjo,
ki ima meritve**, tudi če je nov vozni red nima (`gtfs.py`, „nagrobnik“ brez
`sched`), `kajros merge` pa take vožnje prinese s seboj. `kajros repair`
prešteje osirotele meritve.

## Strani

| pot | kaj |
|---|---|
| `/` | domača stran: s čim greš — vlak ali avtobus |
| `/app/train` · `/app/bus` | iskalnik povezav in odhodna tabla, po omrežju |
| `/app/map` | živi zemljevid — **edini skupni pogled** obeh omrežij |
| `/app/train/{no}` · `/app/bus/{no}` | okno ene vožnje |
| `/app/ovire` | dela na progi in nadomestni prevozi (samo železnica) |
| `/app/statistika[/bus]` | kdaj se splača potovati: zamuda po uri, dnevu, vrsti |
| `/zasebnost` | kaj o obiskovalcu hranimo; mora ostati skladna z `obisk.py` |
| `/admin` | **za skrbnika**: obisk, napake, odzivni čas, zdravje zajema |

Poti, ki niso za aplikacijo, ampak za brskalnike in iskalnike: `/favicon.ico`,
`/robots.txt`, `/sitemap.xml`, `/sw.js`, `/brez-omrezja`. Napaka je **stran**,
kadar jo bere človek, in JSON pod `/api/`. Absolutni naslov zanje je
`KAJROS_BASE_URL`, ne `request.url` — za tunelom je ta `http://127.0.0.1:8000`.
**Tujih izvorov v strani ni**: pisave in Leaflet so naši, ostanejo le ploščice
zemljevida. Podrobnosti v `.claude/rules/strezba.md` in `oznake.md`.

**Pregled za skrbnika zahteva žeton**; brez njega poti ni (404). Prvi obisk
`/admin?k=<žeton>`, nato piškotek s potjo `/admin`. Žeton je
`${KAJROS_DATA_DIR}/.admin-zeton` (postavi ga `deploy/zeton.sh`, **brez
sudota** — enote v `/etc` agent ne more pisati), `KAJROS_ADMIN_TOKEN` ga
povozi; v razvoju ga naredi `dev-restart.sh` sam in izpiše naslov. Šteje se **brez IP-ja**: obiskovalec je
zgoščena vrednost s soljo, ki se ob polnoči zavrže — zato mesečnih unikatov ni
in vsota dnevnih ni isto. Podrobnosti v `.claude/rules/strezba.md`.

## Kam gre

Ciljni uporabnik ni dispečer, ampak potnik z vprašanjem *„kdaj mi pelje in
koliko zamuja“*. Iskalnik povezav je vstopna stran; zemljevid ostane, ker je
uporaben, a ni cilj razvoja. Globlja analiza (vreme kot **dejavnik** zamude)
čaka 2–3 mesece zajema — do takrat se vreme samo *pokaže ob* zamudi.

Česar ne bo, ker podatka ni: cene, sestava vlaka, peron, zasedenost.

## Konvencije

* **Jezik: slovenščina** povsod — koda, komentarji, commiti, UI, dokumentacija.
  Šumniki obvezni.
* Komentarji povedo **zakaj**, ne kaj.
* Commit sporočila: kratka prva vrstica, telo pojasni razlog in izmerjene
  posledice, ne naštevanja datotek.
* Ne dodajaj odvisnosti brez razloga; `requirements.txt` ima pet vrstic.
* `venv/`, `data/`, `export/`, `posnetki/`, `*.sqlite` so v `.gitignore` —
  **razen** `seed/kajros.sqlite`, ki ga rabi namestitev.
* **Agregat čez vso zgodovino se ne računa v zahtevi** (`stats.summary_get()`,
  enkrat na dan ob 3:30, `KAJROS_MAINT_HOUR`). Vsaka taka številka mora na strani
  nositi **čas izračuna**.
* **Mrtve kode ne puščaj.** Kar nima klicatelja, gre ven — v git zgodovini
  ostane. Izjema mora biti napisana v komentarju, z rokom.

## Objava

Malina doma (`david@192.168.1.166`) je **merodajen zajem**: teče ves čas in
zajema vse prevoznike. Ta računalnik je razvoj; baza se **vleče z maline**
(`./scripts/potegni.sh`), nikoli obratno. Podrobnosti: `.claude/rules/objava.md`
in [DEPLOY.md](DEPLOY.md).

**Deploy požene uporabnik sam** — `david` na malini za sudo rabi geslo.
Pripravi ukaz in mu ga daj.

## Kje je zapisano ostalo

Poglobljena pravila so v `.claude/rules/` in se naložijo, ko se dotakneš
ustreznih datotek:

| datoteka | velja za | o čem |
|---|---|---|
| `zajem.md` | `collector.py`, `alerts.py`, `gtfs.py`, `db.py` | kaj feed pošlje in kje laže; varovalke pred smetmi |
| `strezba.md` | `api.py`, `obisk.py` | meja meritve, omrežje, živa vožnja, predpomnilnik leg, štetje obiska |
| `model.md` | `stats.py`, `backtest.py`, `journey.py` | napoved zamude, prestopi, kaj je bilo preizkušeno in ne pomaga |
| `oznake.md` | `static/**`, `templates/**` | kako je zamuda napisana in pobarvana |
| `zemljevid.md` | `dashboard.*`, `train.*` | plasti, geste, ocena lege, pasti CSS |
| `strani.md` | `connections.*`, `home.*`, `templates/**` | katera stran odgovarja na katero vprašanje |
| `objava.md` | `deploy/**`, `scripts/**` | malina, namestitev, vleka baze |
| `android.md` | `android/**` | ovoj z WebView, meja izvora, budilka, orodja |

Razrez ni po temah, ampak **po datotekah, ki znanje res rabijo**: to je edino,
kar se pozna pri porabi konteksta. Popravek v `connections.js` naloži 10 kB
(`oznake` + `strani`), ne 25 kB o zemljevidih; popravek v `api.py` 6 kB
namesto 25 kB o zajemu.

Meritve, ki niso pravilo, ampak stanje (koliko je zajetega, poraba, hitrost):
[docs/MERITVE.md](docs/MERITVE.md). Daljši zapisi: [HANDOVER.md](HANDOVER.md),
[docs/APLIKACIJA.md](docs/APLIKACIJA.md), [design/README.md](design/README.md).

## Odprto

* Dostop od zunaj: **`kajros.app`** (registrirana 3. 9. 2026, name.com). Ta
  nakup je razveljavil prejšnjo izbiro Tailscale Funnela — ta zna samo
  `*.ts.net` in domene ne postreže. Pot je **imenovani Cloudflarov tunel**,
  ne hitri; podrobnosti in izmerjeno v `.claude/rules/objava.md`.
  **Vrat na usmerjevalniku ne odpiraj.**
* Ločen model napovedi za avtobuse, ko bo meritev dovolj.
* **Koda je zaprta** (odločeno 3. 9. 2026): zasebni repozitorij, brez licence,
  torej „vse pravice pridržane“. **Endpointi so odprti** — API sme brati vsak.
  Podatki ostajajo CC BY-SA 4.0 in navedba vira je pogoj rabe, ne okras;
  `seed/kajros.sqlite` je njihova izpeljanka.
* **Delovni imenik se še vedno imenuje `sztrack`.** Preimenovanje mape bi
  prekinilo tekočo sejo in poti v lupini; naredi se ločeno, git ostane cel:
  `mv ~/Dokumenti/Projekti/{sztrack,kajros}`.
