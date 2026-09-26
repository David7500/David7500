# Kajros

Zajem in analiza **zamud slovenskega javnega prevoza** iz odprtih podatkov. Ime = grški *kairos* — pravi trenutek, nasprotje *chronosa* (urni čas). Vozni red = chronos, resnica = kairos; razlika med njima = projekt. Zaledje Python (FastAPI + SQLite), prikaz vanilla JS. Zgodovine teh podatkov nikjer drugje ni — če je ne posnamemo sami, je ni.

Veja: `claude/slovenske-zeleznice-api-ql84hf` · remote `David7500/David7500`

## Zagon

```bash
./scripts/dev-restart.sh          # počaka na sproščen port in izpiše naslove
```

Venv = `venv/` (Python 3.14), **ne** `.venv`. Strežnik med razvojem pogosto že teče na 8001 — preveri `pgrep -af uvicorn`, preden zaženeš drugega. CLI: `./venv/bin/python -m kajros.cli <ukaz>` — `init`, `update`, `poll`, `show`, `stats`, `merge`, `weather`, `export`, `alerts`, `backtest`, `repair`, `prune`, `ocena`, `seed`, `zamenjave`, `pespoti`, `pot`, `naslovi`.

**Preverjanje pred „končano“: `./scripts/preveri.sh`** — testi, odzivi vseh strani, konzola brskalnika, **pyflakes**, **skladnost številk** in paleta v enem, z izhodno kodo. Sami testi: `./venv/bin/python -m pytest -q` (504 preizkusi). `scripts/preveri_skladnost.py` straži napake, ki so si nasprotovale na zaslonu: osirotele meritve, vsota razredov proti deležu točnih, razred po zaokroženi minuti, hitrost `/api/health`, beseda namesto minusa pri prestopu.

Avtobusi se uvozijo z `KAJROS_AGENCIES=1118,1119,1121,1123`. Brez tega so v bazi samo SŽ. **Mestni LPP = drug vir** (`KAJROS_LPP`, privzeto vklopljen): v IJPP ga ni, ker je občinski. Podrobnosti v `.claude/rules/zajem.md`.

**Strežnik posluša na vseh vmesnikih** (`KAJROS_HOST`, privzeto `0.0.0.0`), ker je telefon glavna preizkusna naprava. To **ni** odpiranje vrat na usmerjevalniku: API nima avtentikacije, sme ga videti samo domače omrežje. Samo ta računalnik: `KAJROS_HOST=127.0.0.1 ./scripts/dev-restart.sh`.

**Prek omrežnega naslova lastna lega ne dela — ni naša napaka.** `navigator.geolocation` zahteva varen kontekst (HTTPS ali `localhost`); `http://192.168.1.164:8001` ni ne eno ne drugo (izmerjeno: `window.isSecureContext = false`). Prikaz to pove, ne čaka tiho.

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
| Tir vlaka | tabla potniski.sz.si prek `api.modra.ninja/sz` (tretja oseba) | ~10 min na postajo |

SŽ nimajo javnega API-ja; `potniski.sz.si` za Cloudflarom, stari SOAP mrtev. Zip vsebuje **ves** slovenski javni potniški promet (pet agencij), ne le železnice; `config.RAIL_AGENCY_ID` = edino, kar jih loči.

## Pravila, ki veljajo povsod

* **Model se meri na dveh merilih, ne enem.** `kajros backtest` = zgodovina s kratkimi skoki, `kajros ocena` = številka, ki jo je potnik res videl 25 minut prej. Zadnja sprememba: na prvem merilu za las slabša, na drugem mnogo boljša — brez obojega bi jo zavrgli.
* **Meri, ne domnevaj.** Vsaka trditev v zapisih ima številko. Kar ni izmerjeno, se ne zapiše kot dejstvo; kar je, se zapiše z vzorcem („na 79 primerih“), da naslednji ve, koliko zaupati.
* **Nikoli ne beri `stu.arrival.delay` naravnost** — protobuf za neizpolnjeno polje vrne 0, videti kot „točno“. Uporabi `collector._delay_of()`.
* **Povsod `COALESCE(delay_dep, delay_arr)`, ne obratno.** `departure.delay` izpolnjen pri vseh prevoznikih 100 %, `arrival.delay` ne. Namenoma obratno samo **prihod** na cilj ali naslednjo postajo (`to_delay_s`, `typical_dwell`, `operator_forecast_tasks`) -- ne „popravljaj“.
* **Voznoredne sekunde štejejo od poldneva minus 12 h, ne od polnoči** (GTFS). Epoha ↔ `t_s` samo prek `stats.polnoc()` ali `stats.abs_time()`; na dan premika ure je polnoč za uro zamaknjena (25. 10. 2026 bi bila zamuda LPP +60 min).
* **Meja med meritvijo in napovedjo = `stats.last_measured()`.** Kar je za zadnjim prevoženim postankom, je napoved — vsak prikaz zamude to upošteva. Napaka je bila že dvakrat na zaslonu.
* **Omrežje filtriraj znotraj poizvedbe, ne za njo** (`WHERE t.network = ?`). Bil že dvakrat vzrok počasnosti.
* **Pisalne poti natanko tri** — `POST /stik`, `POST /admin/sporocila/{id}` in `POST /api/deli` (deljenje lege, od 25. 9. 2026). Vse ostalo `GET`. Nova pisalna pot = zavestna odločitev: `test_pisalne_poti_so_nastete` pade, če se seznam podaljša. Varovalke na enem mestu v modulu, ki piše (`stik.py`, `deljenje.py`).
* **V enem SQL stavku ne mešaj `?` in `:ime`** — sqlite veže po vrstnem redu pojavitve, tiho vrne napačne vrstice.
* **`run` hrani zadnje stanje postanka**, zato `MAX(stop_seq)` po koncu vožnje ni dokaz, da vozilo še vozi. Živost sklepaj iz `_LIVE_SQL`.
* **Spremembo prikaza poglej, preden jo razglasiš za končano.** `chromium --headless --disable-gpu --window-size=1850,1000 --virtual-time-budget=7000 --screenshot=$PWD/posnetki/x.png <url>`. V `/tmp` chromium ne more pisati; `posnetki/` v `.gitignore`. **Ne v `$HOME`.**

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
  pot.py         od vrat do vrat: naprej (čim prej) in nazaj (biti tam do)
  hoja.py        pešpoti in navodila iz lastnega OSRM; kolo = ista pot, 15 km/h
  naslovi.py     kazalo naslovov iz OSM -- lastno, ne tuji geokodirnik
  pristanek.py   pristajalne strani: katere relacije in postaje imajo naslov
  lpp.py         živi prihodi mestnega LPP (data.lpp.si), samo za prikaz
  backtest.py    merjenje napovedi z izpuščanjem enega dne
  ocena.py       senčno merjenje: kaj je prikaz trdil 25 min prej in kaj je bilo
  peroni.py      tir vlaka s table SŽ, svoja nit; star ali manjkajoč se ne pokaže
  obisk.py       števci obiska brez IP; sol dneva, praznjenje v svoji niti
  stik.py        sporočila obiskovalcev; piše iz zahteve
  deljenje.py    potnik na vozilu deli lego: kandidati, točke, prehodi, soglasje
  server.py      lifespan: bootstrap + zajem v ozadnji niti
  api.py         FastAPI: /api/* + strani /app*
  cli.py         ukazna vrstica
  templates/     home, connections (vstopna), dashboard, train, alerts
  static/        base.css (barvni žetoni) + common.js + po ena .js/.css na stran
tests/           enotni testi čistih funkcij (pytest, requirements-dev.txt)
scripts/         dev-restart.sh, preveri.sh, potegni.sh, preveri_paleto.py
android/         nativni ovoj z WebView (Kotlin); orodja ločeno v ~/kajros-android
```

**Trd datum v pripravi + računan datum v testu = bomba.** Priprava vstavlja `service_day('S1','2026-08-31')`, testi dan računajo (`_pred`). Ko se datuma ujameta: `UNIQUE constraint failed` — 31. 8. 2026 podrlo pet zelenih preizkusov. Računani vstavki zato skozi `INSERT OR IGNORE`.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day`, `shape` (statika) · `obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `vehicle_now` · `weather` · `alert` + `alert_entity` · `delay_report` · `povzetek` · `napoved` · `deljenje` + `deljenje_tocka` + `deljenje_prehod` (poročila potnikov) · `peron` + `peron_postaja` (tir s table SŽ) · `obisk_pot` + `obisk_razrez` + `obiskovalec` + `obisk_odziv` · `sporocilo` (zadnjih pet samo strežni stroj).

## Omrežji: `network` ni `mode`

`trip.network` (`zeleznica` / `avtobus`) loči **strani aplikacije**. Nadomestni prevoz SŽ: `mode = 'bus'`, a `network = 'zeleznica'`, ker zamenjuje vlak in sodi v isti odgovor kot vlaki. Vsi potniški endpointi imajo `network`, **privzeto `zeleznica`**, da mešanja ne povzroči pozabljen parameter — mešanje merljivo škodljivo: iskanje „ljublj“ vračalo mestna postajališča in postajo Ljubljana potisnilo iz prvih petih zadetkov.

Pri avtobusih drugače, hitro pozabljeno:

* **Številka linije ≠ številka vožnje.** LPP linija 3G ima 388 voženj. Vsaka poizvedba po `train_no` skozi `stats.resolve_trip()`; povezave na eno vožnjo nosijo `?trip=<id>`. Isto velja za devet vlakov s sezonskimi različicami.
* **Barva linije ≠ barva linije.** Vsi LPP `route_color` = ista zelena prevoznika, zato oznaka nosi ime prevoznika in številko („LPP 25“) — iskati se mora dati po tem, kar človek vidi na postajališču. Prevoznik v `trip.agency` kot GTFS ID (1118, 1123 …); ime v `common.AGENCY` in `stats.AGENCY_NAMES`.
* **Mestno postajališče ima svoj `stop_id` za vsako smer** in vsak vir svojega („Bavarski dvor“ v `station` štirikrat). Vse v aplikaciji teče po **imenu** postaje; stran ceste loči `journey.smeri_postaje()` po smeri vožnje do naslednjega postanka, tabla, widget in pristajalna stran jo nosijo kot `smer`.

## Številke vlakov

`LPV 2010` ni oznaka proge, ampak **ena vožnja** (trip). `route_id` 1 : 1 s tripom, za združevanje neuporaben — zgodovino gradi po `train_no` **znotraj `trip_id`**. Parnost številke nosi smer. Predpona (`LP`, `LPV`, `IC`, `MV`, `EN` …) = vrsta vlaka; `BUS …` = nadomestni prevoz.

**`trip_id` niso vedno stabilni.** Vse poizvedbe gredo skozi `JOIN trip` (omrežje je tam), zato uvoz **obdrži vožnjo z meritvami**, tudi če je nov vozni red nima („nagrobnik“ brez `sched`; 1. 9. 2026 bi sicer izginilo 114 voženj s 3 043 meritvami), in izginulo vožnjo poveže z naslednico (tabela `zamenjava`), na katero zajem prevede zamudo in lego (22. 9. 2026: LPP 25, 12D, 15). `kajros repair` prešteje osirotele meritve. Podrobnosti: `.claude/rules/zajem.md`.

## Strani

| pot | kaj |
|---|---|
| `/` | domača stran: s čim greš — vlak ali avtobus |
| `/app/train` · `/app/bus` | iskalnik povezav in odhodna tabla, po omrežju |
| `/app/pot` · `/app/pot/podrobno` | od vrat do vrat čez obe omrežji, z vodenjem po pešpoti |
| `/app/map` | živi zemljevid — **edini skupni pogled** obeh omrežij |
| `/app/train/{no}` · `/app/bus/{no}` | okno ene vožnje |
| `/app/ovire` | dela na progi in nadomestni prevozi (samo železnica) |
| `/app/statistika[/bus]` | kdaj se splača potovati — **umaknjena** (19. 9. 2026): dela, a ni povezana, ni v sitemapu, `noindex` |
| `/vlak/{od}/{cilj}` · `/avtobus/…` | **pristajalna stran ene relacije**: odhodi danes in izmerjena zamuda, izrisana na strežniku |
| `/postaja/{ime}` · `/postajalisce/{ime}` | pristajalna stran ene postaje |
| `/postaje` · `/postajalisca` | kazalo obojega — edina pot do pristajalnih strani, ki ni zemljevid strani |
| `/stik` | obrazec za sporočilo; nabiralnik v `/admin` |
| `/zasebnost` | kaj o obiskovalcu hranimo; skladna z `obisk.py` in `stik.py` |
| `/o-nas` | kaj je kajros, od kod podatki, da ni prevoznikova stran |
| `/donacije` | za kaj gre denar + gumb do `ko-fi.com/kajros` (privzetek v `config.py`); `KAJROS_DONACIJE=` skrije vse |
| `/admin` | **za skrbnika**: obisk, napake, odzivni čas, zdravje zajema, deljenje lege na zemljevidu |

**Pristajalne strani obstajajo zaradi iskalnika in so brez JS**: človek išče „vlak ljubljana koper“, odgovor mora biti v odgovoru strežnika. Meja, katere nastanejo: `kajros/pristanek.py`; v zemljevidu strani vrh po prometu, ostalo `noindex`.

Poti za brskalnike in iskalnike: `/favicon.ico`, `/robots.txt`, `/sitemap.xml`, `/sw.js`, `/brez-omrezja`; `/android` = stran s prenosom, `/prenos` = podpisan APK. Napaka = **stran** za človeka in JSON pod `/api/`. Absolutni naslov = `KAJROS_BASE_URL`, ne `request.url` (za tunelom je ta `http://127.0.0.1:8000`). **Tujih izvorov v strani ni** razen ploščic zemljevida.

**`/admin` zahteva žeton** (brez njega 404): `/admin?k=<žeton>`, nato piškotek. Žeton: `${KAJROS_DATA_DIR}/.admin-zeton` (`deploy/zeton.sh`, **brez sudota**), `KAJROS_ADMIN_TOKEN` ga povozi, v razvoju ga izpiše `dev-restart.sh`. Obisk se šteje **brez IP-ja** (sol dneva). Podrobnosti: `.claude/rules/strezba.md`.

## Kam gre

Ciljni uporabnik ni dispečer, ampak potnik z vprašanjem *„kdaj mi pelje in koliko zamuja“*. Iskalnik povezav = vstopna stran; zemljevid ostane, ker je uporaben, a ni cilj razvoja. Globlja analiza (vreme kot **dejavnik** zamude) čaka 2–3 mesece zajema — do takrat se vreme samo *pokaže ob* zamudi.

Ne bo, ker podatka ni: cene, sestava vlaka, zasedenost. **Tir** od 25. 9. 2026, s table SŽ in samo na postajah, kjer ga SŽ objavi (14 od 20 izmerjenih); vir je tretja oseba, zato je dodatek, ki sme izginiti.

## Konvencije

* **Jezik: slovenščina** povsod — koda, komentarji, commiti, UI, dokumentacija. Šumniki obvezni.
* Komentarji povedo **zakaj**, ne kaj.
* Commit sporočila: kratka prva vrstica, telo pojasni razlog in izmerjene posledice, ne naštevanja datotek.
* Ne dodajaj odvisnosti brez razloga; `requirements.txt` ima pet vrstic.
* `venv/`, `data/`, `export/`, `posnetki/`, `*.sqlite` so v `.gitignore` — **razen** `seed/kajros.sqlite`, ki ga rabi namestitev.
* **Agregat čez vso zgodovino se ne računa v zahtevi** (`stats.summary_get()`, enkrat na dan ob 3:30, `KAJROS_MAINT_HOUR`). Vsaka taka številka mora na strani nositi **čas izračuna**.
* **Mrtve kode ne puščaj.** Kar nima klicatelja, gre ven — v git zgodovini ostane. Izjema mora biti napisana v komentarju, z rokom.
* **Odgovori na kratko, brez uvodov in olepšav** (caveman). Vsa tehnična vsebina ostane; koda, commiti in dokumentacija normalna proza. Izklop: „normal mode“.

## Objava

Malina doma (`david@192.168.1.166`) = **merodajen zajem**: teče ves čas, zajema vse prevoznike. Ta računalnik = razvoj; baza se **vleče z maline** (`./scripts/potegni.sh`), nikoli obratno. Podrobnosti: `.claude/rules/objava.md` in [DEPLOY.md](DEPLOY.md).

**Objava strežnika = `git push arwen <veja>`** — kavelj na arwenu sam požene `deploy/posodobi.sh`, izpis se vrne potiskajočemu. **Na malino deploy požene uporabnik sam**, ker `david` tam za sudo rabi geslo: pripravi ukaz in mu ga daj.

## Kje je zapisano ostalo

Poglobljena pravila so v `.claude/rules/`, naložijo se ob dotiku ustreznih datotek:

| datoteka | velja za | o čem |
|---|---|---|
| `zajem.md` | `collector.py`, `alerts.py`, `gtfs.py`, `db.py`, `peroni.py` | kaj feed pošlje in kje laže; varovalke pred smetmi |
| `strezba.md` | `api.py`, `lpp.py`, `obisk.py` | meja meritve, omrežje, živa vožnja, predpomnilnik leg, štetje obiska |
| `model.md` | `stats.py`, `backtest.py`, `journey.py`, `ocena.py` | napoved zamude, prestopi, senčno merjenje, kaj ne pomaga |
| `oznake.md` | `static/**`, `templates/**` | kako je zamuda napisana in pobarvana |
| `zemljevid.md` | `dashboard.*`, `train.*` | plasti, geste, ocena lege, pasti CSS |
| `strani.md` | `connections.*`, `pot*`, `home.*`, `pristanek.*`, `templates/**` | katera stran odgovarja na katero vprašanje |
| `objava.md` | `deploy/**`, `scripts/**` | malina, namestitev, vleka baze |
| `android.md` | `android/**` | ovoj z WebView, meja izvora, budilka, orodja |
| `deljenje.md` | `deljenje.py`, `deli.*`, `DeljenjeStoritev.kt` | lega potnikov: kaj se pokaže, kaj hrani, varovalke |

Razrez **po datotekah, ki znanje rabijo**, ne po temah: le to se pozna pri porabi konteksta.

Meritve, ki niso pravilo, ampak stanje (koliko zajetega, poraba, hitrost): [docs/MERITVE.md](docs/MERITVE.md). Daljši zapisi: [HANDOVER.md](HANDOVER.md), [docs/APLIKACIJA.md](docs/APLIKACIJA.md), [design/README.md](design/README.md).

## Odprto

* **Vrat na usmerjevalniku ne odpiraj**: `kajros.app` gre prek imenovanega Cloudflarovega tunela z arwena (`.claude/rules/objava.md`).
* Ločen model napovedi za avtobuse, ko bo meritev dovolj.
* **Koda je zaprta** (odločeno 3. 9. 2026): zasebni repozitorij, brez licence = „vse pravice pridržane“. **Endpointi so odprti** — API sme brati vsak. Podatki ostajajo CC BY-SA 4.0, navedba vira je pogoj rabe, ne okras; `seed/kajros.sqlite` je njihova izpeljanka. Posledica za Android: glavni F-Droid in IzzyOnDroid zahtevata prosto licenco, Play pa račun, 25 $ in 12 preizkuševalcev, zato se aplikacija razdeljuje **s strani** (`/android`, glej `.claude/rules/android.md`).
* **Delovni imenik se še vedno imenuje `sztrack`.** Preimenovanje mape bi prekinilo tekočo sejo in poti v lupini; naredi se ločeno, git ostane cel: `mv ~/Dokumenti/Projekti/{sztrack,kajros}`.
