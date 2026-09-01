# sztrack

Zajem in analiza **zamud slovenskega javnega prevoza** iz odprtih podatkov.
Zaledje v Pythonu (FastAPI + SQLite), prikaz v vanilla JS. Zgodovine teh
podatkov ni nikjer drugje — če je ne posnamemo sami, je ni.

Veja: `claude/slovenske-zeleznice-api-ql84hf` · remote `David7500/David7500`

## Zagon

```bash
./scripts/dev-restart.sh          # počaka na sproščen port in izpiše naslove
```

Venv je `venv/` (Python 3.12), **ne** `.venv`. Strežnik med razvojem pogosto že
teče na 8001 — preveri s `pgrep -af uvicorn`, preden zaganjaš drugega.
CLI: `./venv/bin/python -m sztrack.cli <ukaz>` — `init`, `update`, `poll`,
`show`, `stats`, `merge`, `weather`, `export`, `alerts`, `backtest`, `repair`,
`prune`, `seed`.

**Preverjanje pred „končano“: `./scripts/preveri.sh`** — testi, odzivi vseh
strani, konzola brskalnika in paleta v enem, z izhodno kodo. Sami testi:
`./venv/bin/python -m pytest -q` (92 preizkusov).

Avtobusi se uvozijo z `SZ_AGENCIES=1118,1119,1121,1123`. Brez tega so v bazi
samo SŽ.

**Strežnik posluša na vseh vmesnikih** (`SZ_HOST`, privzeto `0.0.0.0`), ker je
telefon glavna preizkusna naprava. To **ni** isto kot odpiranje vrat na
usmerjevalniku: API nima avtentikacije in ga sme videti samo domače omrežje.
Za samo ta računalnik: `SZ_HOST=127.0.0.1 ./scripts/dev-restart.sh`.

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
| Ovire in žive zamude | `.../service_alerts` | 60 s |
| Lega vozil | `.../vehicle_positions` | 10 s (`SZ_POSITION_SECONDS`) |
| Vreme | `open-meteo.com` (ima arhiv za nazaj) | dnevno |

SŽ nimajo javnega API-ja; `potniski.sz.si` je za Cloudflarom, stari SOAP je
mrtev. V zipu je **ves** slovenski javni potniški promet (pet agencij), ne le
železnica; `config.RAIL_AGENCY_ID` je edino, kar jih loči.

## Pravila, ki veljajo povsod

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
sztrack/
  geo.py         haversine, projekcija postaj na progo, Douglas-Peucker
  db.py          SQLite shema + merge_from() + migracije
  gtfs.py        pogojni prenos zipa, uvoz voznega reda
  collector.py   poll zamud in leg, obratovalni dan, varovalke pred smetmi
  alerts.py      ovire (SZ-OVIRA) in žive zamude s prometnim mestom (SZ-DELAY)
  weather.py     Open-Meteo, mreža 0,1° (~8 km) × 1 h
  stats.py       zgodovina, porazdelitve, napoved, dnevni povzetek
  journey.py     odhodna tabla, iskanje postaj, zveze s prestopi
  backtest.py    merjenje napovedi z izpuščanjem enega dne
  server.py      lifespan: bootstrap + zajem v ozadnji niti
  api.py         FastAPI: /api/* + strani /app*
  cli.py         ukazna vrstica
  templates/     home, connections (vstopna), dashboard, train, alerts
  static/        base.css (barvni žetoni) + common.js + po ena .js/.css na stran
tests/           enotni testi čistih funkcij (pytest, requirements-dev.txt)
scripts/         dev-restart.sh, preveri.sh, potegni.sh, preveri_paleto.py
```

**Trd datum v pripravi + računan datum v testu = bomba.** Priprava vstavlja
`service_day('S1','2026-08-31')`, testi pa dan računajo (`_pred`). Na dan, ko
se datuma ujameta, je to `UNIQUE constraint failed` — zgodilo se je 31. 8. 2026
in podrlo pet zelenih preizkusov. Računani vstavki gredo zato skozi
`INSERT OR IGNORE`.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day`, `shape` (statika) ·
`obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `vehicle_now` ·
`weather` · `alert` + `alert_entity` · `delay_report` · `summary`.

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

**`trip_id` so med regeneracijami GTFS stabilni** — preverjeno ob uvozu novega
voznega reda (vseh 60 409 meritev se je še ujemalo). Zajema pred `sztrack
update` ni treba varovati.

## Strani

| pot | kaj |
|---|---|
| `/` | domača stran: s čim greš — vlak ali avtobus |
| `/app/train` · `/app/bus` | iskalnik povezav in odhodna tabla, po omrežju |
| `/app/map` | živi zemljevid — **edini skupni pogled** obeh omrežij |
| `/app/train/{no}` · `/app/bus/{no}` | okno ene vožnje |
| `/app/ovire` | dela na progi in nadomestni prevozi (samo železnica) |

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
  **razen** `seed/sz.sqlite`, ki ga rabi namestitev.
* **Agregat čez vso zgodovino se ne računa v zahtevi** (`stats.summary_get()`,
  enkrat na dan ob 3:30, `SZ_MAINT_HOUR`). Vsaka taka številka mora na strani
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
| `podatki.md` | `collector.py`, `alerts.py`, `gtfs.py`, `db.py`, `api.py` | kaj feed je in česa ne pove; varovalke pred smetmi |
| `model.md` | `stats.py`, `backtest.py`, `journey.py` | napoved zamude, prestopi, kaj je bilo preizkušeno in ne pomaga |
| `prikaz.md` | `static/**`, `templates/**` | strani, zemljevidi, barve, geste |
| `objava.md` | `deploy/**`, `scripts/**` | malina, namestitev, vleka baze |

Meritve, ki niso pravilo, ampak stanje (koliko je zajetega, poraba, hitrost):
[docs/MERITVE.md](docs/MERITVE.md). Daljši zapisi: [HANDOVER.md](HANDOVER.md),
[docs/APLIKACIJA.md](docs/APLIKACIJA.md), [design/README.md](design/README.md).

## Odprto

* **Ime projekta.** `sztrack` je bil mišljen samo za vlake; iščemo ironično
  ime, tuja beseda, ki se dobro sliši v slovenščini. Ni še izbrano.
* Statistična stran je odstranjena do prenove; endpointa `/api/stats*` sta
  ostala (glej komentar v `api.py`).
* Dostop od zunaj (Tailscale ali Cloudflare Tunnel). **Vrat na usmerjevalniku
  ne odpiraj — API nima avtentikacije.**
* Ločen model napovedi za avtobuse, ko bo meritev dovolj.
