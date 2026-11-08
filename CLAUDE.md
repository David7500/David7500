# Kajros

Zajem in analiza **zamud slovenskega javnega prevoza** iz odprtih podatkov. Ime = grški *kairos* (pravi trenutek) proti *chronosu* (urni čas): vozni red = chronos, resnica = kairos, razlika = projekt. Python (FastAPI + SQLite), prikaz vanilla JS. Zgodovine teh podatkov nikjer drugje ni — če je ne posnamemo sami, je ni.

Veja: `claude/slovenske-zeleznice-api-ql84hf` · remote `David7500/David7500`

**Koledar: [KOLEDAR.md](KOLEDAR.md).** „Poglej koledar“ = skill `koledar`: naredi zapadlo, izid vpiši, dodaj nove roke. **Vsaka seja in vsak agent** (David, 31. 10. 2026): naloga za pozneje — z datumom ali pogojem (meritev čez teden, praznik, rok vira, Davidovo dejanje, odločitev po senci) — gre takoj v „Na vrsti“ v `KOLEDAR.md` (datum z dnevom, kdo, kaj in zakaj, kako, podrobnosti), ne samo v odgovor, predajo ali commit. Agent, ki sam ne sme pisati, rok vrne v izidu, da ga vpiše glavna seja.

## Zagon

```bash
./scripts/dev-restart.sh          # počaka na sproščen port in izpiše naslove
```

Venv = `venv/` (Python 3.14), **ne** `.venv`. Strežnik pogosto že teče na 8001 — `pgrep -af uvicorn` pred zagonom drugega. CLI: `./venv/bin/python -m kajros.cli <ukaz>` (seznam: `--help`).

**Pred „končano“: `./scripts/preveri.sh`** — testi, odzivi strani, konzola brskalnika, **pyflakes**, **skladnost številk**, paleta; z izhodno kodo. Sami testi: `./venv/bin/python -m pytest -q`. `scripts/preveri_skladnost.py` straži napake, ki so si nasprotovale na zaslonu: osirotele meritve, vsota razredov proti deležu točnih, razred po zaokroženi minuti, hitrost `/api/health`, beseda namesto minusa pri prestopu.

Avtobusi: `KAJROS_AGENCIES=1118,1119,1121,1123`, brez tega v bazi samo SŽ. **Mestni LPP in Marprom = svoja vira** (`KAJROS_LPP`, `KAJROS_MARPROM`, privzeto vklopljena): občinska, v IJPP ju ni. Podrobno `.claude/rules/zajem.md`.

**Strežnik posluša na vseh vmesnikih** (`KAJROS_HOST`, privzeto `0.0.0.0`): telefon = glavna preizkusna naprava. To **ni** odpiranje vrat na usmerjevalniku — API brez avtentikacije, samo domače omrežje. Samo ta računalnik: `KAJROS_HOST=127.0.0.1 ./scripts/dev-restart.sh`.

**Lastna lega prek omrežnega naslova ne dela — ni naša napaka.** `navigator.geolocation` rabi varen kontekst (HTTPS ali `localhost`); `http://192.168.1.164:8001` ni (`window.isSecureContext = false`). Prikaz to pove, ne čaka tiho.

## Od kod podatki

```
SŽ + IJPP → NAP (b2b.nap.si, CC BY-SA 4.0) → DERP gtfs-generators → GTFS + GTFS-RT
```

| Kaj | Vir | Ritem |
|---|---|---|
| Vozni red | `gitlab.com/.../IJPP/latest/ijpp_gtfs.zip` (41 MB) | ~1×/dan |
| Zamude | `rt.gtfs.derp.si/sources/ijpp/trip_updates` | 30 s |
| Mestni LPP, vse troje | `rt.gtfs.derp.si/sources/lpp/all` + `avl.lpp.si/transit/api/gtfs` | 30 s |
| Lega vozil | `.../vehicle_positions` | 10 s (`KAJROS_POSITION_SECONDS`) |
| Vreme | `open-meteo.com` (ima arhiv) | dnevno |
| Zamude vlakov — **vodijo** (derp.si isto, prek posrednika) | zemljevid potniski.sz.si, `admin-ajax.php?action=aktivni_vlaki`, Chrome | 5 s (SŽ preračuna na 15) |
| Zamude mestnega LPP, drugi vir | zasloni LPP `data.lpp.si/api/station/arrival`, ~75–100 postajališč | 2 min |
| Mestni Marprom (Maribor), lege in vožnje | `vozniredi.marprom.si/OBA/` (izvirnik, brez ključa); zamuda iz leg | 10 s |
| Vozni red Marproma | `vozniredi.marprom.si/gtfs/gtfs.zip`, ko ne pokrije tedna kopija `gtfs.derp.si` | ~1×/dan |
| Mestni Kranj: vozni red / lege | MOK prek Ridanga (`kranj-avl-prod.ridango.cloud`) / Ridangov GTFS-RT prek derp.si | ~1×/dan / 10 s |
| Mestni Murska Sobota (linije 1, 2) | NeTEx (DUJPP prek NAP), zip DERP `extract_moms_gtfs`; lege NAP | ~1×/dan |
| Lege avtobusov IJPP, izvirnik | NAP SIRI-VM `b2b.nap.si/data/b2b.siri.api` (prijava `deploy/nap.sh`) | 10 s |
| Promet na cestah, za vlak/avto — **še brez prikaza** | NAP FCD NCUP `b2b.fcd.datexii33.status` + potovalni časi AC DARS, `promet.sqlite` | 1 min |
| Tir vlaka | tabla postaje potniski.sz.si, Chrome | ~10 min/postajo |
| Ovire — **vodijo** (angleške in ob molku `.../service_alerts`) | stanje v prometu potniski.sz.si (`var roadworks`), Chrome | 5 min |
| Kje ustavi nadomestni avtobus | seznam potniski.sz.si, posnetek v gitu (`scripts/nadomestna_postajalisca.py`) | ročno ob spremembi |
| Avtobusna postajališča OSM, za `opazovano.py` | Overpass, posnetek v gitu (`scripts/osm_postajalisca.py`, ODbL) | ročno |

SŽ nimajo javnega API-ja; `potniski.sz.si` je za Cloudflarom, ki od 7. 10. 2026 spusti le Chrome z oknom → Chrome pod Xvfb (`brskalnik.py`, namestitev `deploy/brskalnik.sh`); stari SOAP mrtev. Zip = **ves** slovenski javni potniški promet (pet agencij); `config.RAIL_AGENCY_ID` jih edini loči. **Vsak vir opisan enkrat, v `kajros/viri.py`** (naslov, ritem, izvor, licenca, ukrep ob izpadu); vsak klic na tuj strežnik gre skozi `viri.branje()`, sicer ga /admin ne vidi (`test_vsak_klic_na_tuj_streznik_je_v_registru`).

## Pravila, ki veljajo povsod

* **Model se meri na dveh merilih.** `kajros backtest` = zgodovina s kratkimi skoki, `kajros ocena` = številka, ki jo je potnik videl 25 min prej. Zadnja sprememba: na prvem za las slabša, na drugem mnogo boljša — z enim merilom bi jo zavrgli.
* **Meri, ne domnevaj.** Vsaka trditev v zapisih ima številko in vzorec („na 79 primerih“). Neizmerjeno ni dejstvo. Nov model/hevristika najprej proti referenci (prenos zamude); česar ne premaga, ne gre v prikaz.
* **Nikoli ne beri `stu.arrival.delay` naravnost** — protobuf za neizpolnjeno polje vrne 0 = „točno“. Uporabi `collector._delay_of()`.
* **Povsod `COALESCE(delay_dep, delay_arr)`, ne obratno.** `departure.delay` izpolnjen pri vseh 100 %, `arrival.delay` ne. Namenoma obratno samo **prihod** na cilj ali naslednjo postajo (`to_delay_s`, `typical_dwell`, `operator_forecast_tasks`) — ne „popravljaj“.
* **Voznoredne sekunde od poldneva minus 12 h, ne od polnoči** (GTFS). Epoha ↔ `t_s` samo prek `stats.polnoc()` / `stats.abs_time()`; ob premiku ure polnoč zamaknjena za uro (25. 10. 2026 bi bila zamuda LPP +60 min).
* **Meja meritev/napoved = `stats.last_measured()`.** Za zadnjim prevoženim postankom je napoved; vsak prikaz zamude to upošteva (napaka že dvakrat na zaslonu). **Trenutna zamuda = `stats.trenutna_zamuda(lm)`, ne `lm["delay_s"]`**: vlak, ki stoji med postajama, ima po SŽ višjo. Straža: primerjava z zemljevidom SŽ (`skladnost_sz` v zdravju) — 11.–16. 10. 2026 prikaz prenizek pri 42 % voženj z zamudo, zdravje zeleno (`zajem.md`).
* **Omrežje filtriraj v poizvedbi** (`WHERE t.network = ?`), ne za njo in ne z `(? IS NULL OR t.network = ?)` — tega SQLite ne indeksira (1,7 s namesto 6 ms, 18. 10. 2026). Že trikrat vzrok počasnosti. Izjema: kjer poizvedba bolje začne drugje (tabla, zveze, `LAST_STOP_SQL` avtobusov), `+t.network = ?` — izmeri obe omrežji (`docs/presoja/2026-11-08-koledar/omrezje.md`).
* **Pisalnih poti natanko šest**: `POST /stik`, `POST /admin/sporocila/{id}`, `POST /api/deli` (deljenje lege), `POST /admin/obvestila` (za žetonom), `POST /donacije/ko-fi` (za žetonom Ko-fi), `POST /api/zasedenost` (za `KAJROS_ZASEDENOST`; komentar gre skozi `/stik`). Vse ostalo `GET`. Nova = zavestna odločitev: `test_pisalne_poti_so_nastete` pade. Varovalke na enem mestu v modulu, ki piše (`stik.py`, `deljenje.py`, `obvestila.py`, `donacije.py`, `zasedenost.py`).
* **V enem SQL stavku ne mešaj `?` in `:ime`** — sqlite veže po vrstnem redu, tiho napačne vrstice.
* **`run` hrani zadnje stanje postanka**: `MAX(stop_seq)` po koncu vožnje ni dokaz, da vozilo vozi. Živost iz `_LIVE_SQL`.
* **Spremembo prikaza poglej pred „končano“, v obeh širinah** (telefon ~430 px, namizje ~1850 px): `chromium --headless --disable-gpu --window-size=1850,1000 --virtual-time-budget=7000 --screenshot=$PWD/posnetki/x.png <url>`. Chromium v `/tmp` ne more pisati; `posnetki/` v `.gitignore`. **Ne v `$HOME`.**

## Koda

```
kajros/
  geo.py         haversine, projekcija postaj na progo, Douglas-Peucker
  db.py          SQLite shema + merge_from() + migracije
  gtfs.py        pogojni prenos zipa, uvoz voznega reda
  collector.py   poll zamud in leg, obratovalni dan, varovalke pred smetmi
  iz_lege.py     zamuda iz lege na trasi, kjer feed zamud vožnje nima
  odsek.py       zamuda na dolgem odseku iz lege in profila ostanka časa; senca, prikaz je ne bere
  prehod.py      prehod postanka iz GPS brez trase; odkloni.py kje vozila ne vozijo po trasi
  alerts.py      ovire (SZ-OVIRA); poročila o zamudi piše zemljevid SŽ (`zamude_sz`)
  zapore.py      zapora tira iz besedila ovir, vlak pred tabo: opozorilo, ne napoved
  nadomestni.py  kje ustavi nadomestni avtobus na postaji (posnetek strani SŽ)
  weather.py     Open-Meteo, mreža 0,1° (~8 km) × 1 h
  stats.py       zgodovina, porazdelitve, napoved, dnevni povzetek
  journey.py     odhodna tabla, iskanje postaj, zveze s prestopi
  pot.py         od vrat do vrat: naprej (čim prej) in nazaj (biti tam do)
  hoja.py        pešpoti in navodila iz lastnega OSRM; kolo = ista pot, 15 km/h
  naslovi.py     kazalo naslovov iz OSM -- lastno, ne tuji geokodirnik
  pripni.py      trase GTFS pripete na ceste in tire OSM (lastni OSRM)
  tiri.py        tiri s številko iz OSM: vlak na postaji stoji na tiru s table SŽ
  pristanek.py   pristajalne strani: katere relacije in postaje imajo naslov
  lpp.py         živi prihodi mestnega LPP (data.lpp.si), samo za prikaz
  zive.py        vožnje LPP pod id-ji brez voznega reda: par z objavljeno, objava na vzorec, ki ga LPP vozi
  backtest.py    merjenje napovedi z izpuščanjem enega dne
  ocena.py       senčno merjenje: kaj je prikaz trdil 25 min prej in kaj je bilo
  statistika.py  strani statistike: dnevni agregati (`stat_dan`, ne obrezuje se) in nočna okna
  brskalnik.py   Chrome za potniski.sz.si (CDP na localhostu, Xvfb): edina pot mimo Cloudflara
  peroni.py      tir vlaka s table SŽ, svoja nit; star ali manjkajoč se ne pokaže
  zamude_sz.py   zamude vlakov z zemljevida SŽ, svoja nit; vodi, derp.si le ob molku
  ovire_sz.py    ovire s strani SŽ, svoja nit; vodi slovenske, derp.si le ob molku
  zamude_lpp.py  zamude mestnega LPP z zaslonov LPP, svoja nit; vozilo -> vožnja prek derp.si
  nap.py         lege IJPP z NAP (SIRI-VM), svoja nit; vodi lege in zamude medkrajevnih
  marprom.py     mestni Maribor z Marpromovega API-ja, svoja nit: vožnja po njegovih prihodih, zamuda iz leg
  kranj.py       mestni Kranj: lege Ridanga prek derp.si, svoja nit, zamuda iz leg
  promet.py      promet na cestah z NAP (FCD, AC), svoja nit in `promet.sqlite`
  dosje.py       vse o vsakem vozilu: vsak vzorec vsakega vira in kaj smo naredili; svoja nit in `dosje.sqlite`; `kajros vozilo <id>`
  obisk.py       števci obiska brez IP; sol dneva, praznjenje v svoji niti
  stik.py        sporočila obiskovalcev; obvestila.py skrbnik potnikom (z rokom); donacije.py Ko-fi brez imena
  viri.py        register virov + dnevnik branj: zavihek Viri v /admin, preverjanje
  koledar.py     KOLEDAR.md v /admin (zavihek Koledar): lasten izris Markdowna, pot ob kodi
  zdravje.py     kdaj je zajem zdrav (barve v /admin), kaj gre v pošto (`posta`: samo poseg); opozorila.py pošlje
  deljenje.py    potnik na vozilu deli lego: kandidati, točke, prehodi, soglasje
  zasedenost.py  kako polno je vozilo po poročilih potnikov
  opazovano.py   kje vozila zadnje dni ne ustavijo, iz leg in prehodov, za vse enako; prikaz bere `za_prikaz`
  indexnow.py    iskalnikom (Bing ...) pošlje seznam strani; Google ne
  server.py      lifespan: bootstrap + zajem v ozadnji niti; cli.py ukazna vrstica
  api.py         FastAPI: /api/* + strani /app*; markdown.py stran za agente (`Accept: text/markdown`)
  templates/ · static/   predloge; base.css (barvni žetoni) + common.js + po ena .js/.css na stran
tests/           pytest · scripts/ dev-restart.sh, preveri.sh, preveri_paleto.py
android/         ovoj z WebView (Kotlin), orodja v ~/kajros-android · o-nas/ vir 3D /o-nas, gradi.sh → static/o-nas/o3.js
```

**Trd datum v pripravi + računan datum v testu = bomba.** Priprava vstavi `service_day('S1','2026-08-31')`, test dan računa (`_pred`); ko se ujameta: `UNIQUE constraint failed` (31. 8. 2026 pet rdečih). Računani vstavki zato `INSERT OR IGNORE`.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day`, `shape` (statika; `shape.osm`/`edge.osm` = pripeta, `pripeto` = predpomnilnik po vsebini) · `obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `vehicle_now` · `weather` · `alert` + `alert_entity` · `delay_report` · `povzetek` · `napoved` · `deljenje` + `deljenje_tocka` + `deljenje_prehod` · `peron` + `peron_postaja` · `sz_zamuda` + `lpp_zamuda` (drugi vir, za primerjavo z derp.si) · `ziva_voznja` + `popravek_vzorca` (`zive.py`) · `odklon` · `lega` + `gps_prehod` (lege 14 dni) · `obvestilo` · `donacija` · `zasedenost` + `opomba` · `stat_dan` (dnevni agregati statistike, ne obrezuje se) · `odsek_profil` (28 dni) · `opazovano` + `opazovano_dan` (ne obrezuje se) + `opazovano_izid` (21 dni) · `obisk_pot` + `obisk_razrez` + `obiskovalec` + `obisk_odziv` · `sporocilo` (zadnjih pet samo strežni stroj). `promet.sqlite`: `fcd` (dnevnik po odseku, `NULL` = spet prosto) + `fcd_zdaj` + `fcd_odsek` · `obhod` · `ac`. `dosje.sqlite`: `tocke` + `stanje` + `telo` + `zamude` + `vozilo_dan` + `oznaka`.

## Omrežji: `network` ni `mode`

`trip.network` (`zeleznica` / `avtobus`) loči **strani aplikacije**. Nadomestni prevoz SŽ: `mode = 'bus'`, `network = 'zeleznica'` — zamenjuje vlak, sodi med vlake. Vsi potniški endpointi imajo `network`, **privzeto `zeleznica`**: mešanje škodi (iskanje „ljublj“ je mestna postajališča potisnilo pred postajo Ljubljana).

Pri avtobusih, hitro pozabljeno:

* **Številka linije ≠ številka vožnje.** LPP 3G ima 388 voženj. Poizvedba po `train_no` vedno skozi `stats.resolve_trip()`; povezava na eno vožnjo nosi `?trip=<id>`. Isto pri devetih vlakih s sezonskimi različicami.
* **Barva linije ≠ linija.** Vsi LPP `route_color` = ista zelena, zato oznaka = prevoznik + številka („LPP 25“), kot na postajališču. Prevoznik v `trip.agency` kot GTFS ID (1118, 1123 …), ime v `common.AGENCY` in `stats.AGENCY_NAMES`. **Medkrajevni (Arriva, Nomago, AP MS) številke na avtobusu nimajo**: `train_no` = šifra registra (A6346), oznaka „Arriva“ oz. „Arriva → Bohinj Ukanc“, kjer smeri ne pove drugo (`common.imeVoznje`, `pristanek.ime_voznje`).
* **Mestno postajališče ima `stop_id` za vsako smer in vsak vir** („Bavarski dvor“ v `station` štirikrat). Aplikacija teče po **imenu**; stran ceste loči `journey.smeri_postaje()` po smeri do naslednjega postanka, tabla, widget in pristajalna stran jo nosijo kot `smer`.

## Številke vlakov

`LPV 2010` = **ena vožnja** (trip), ne proga. `route_id` 1 : 1 s tripom, za združevanje neuporaben — zgodovina po `train_no` **znotraj `trip_id`**. Parnost = smer. Predpona (`LP`, `LPV`, `IC`, `MV`, `EN` …) = vrsta; `BUS …` = nadomestni prevoz.

**`trip_id` niso stabilni.** Vse poizvedbe skozi `JOIN trip` (omrežje), zato uvoz **obdrži vožnjo z meritvami**, tudi brez nje v novem voznem redu („nagrobnik“ brez `sched`; 1. 9. 2026 bi sicer izginilo 114 voženj s 3 043 meritvami), in jo poveže z naslednico (`zamenjava`), na katero zajem prevede zamudo in lego; zgodovina gre nanjo trajno, po vožnji čez dneve (`prednik`). `kajros repair` prešteje osirotele meritve. Podrobno `zajem.md`.

## Strani

| pot | kaj |
|---|---|
| `/` | domača: vlak ali avtobus |
| `/app/train` · `/app/bus` | iskalnik povezav in odhodna tabla, po omrežju |
| `/app/pot` · `/app/pot/podrobno` | od vrat do vrat čez obe omrežji, vodenje po pešpoti |
| `/app/map` | živi zemljevid — **edini skupni pogled** obeh omrežij |
| `/app/train/{no}` · `/app/bus/{no}` | okno ene vožnje |
| `/app/ovire` | dela na progi, nadomestni prevozi (samo železnica) |
| `/statistika` · `…/napovedi` · `…/prevozniki` · `…/prevoznik/{ime}` · `…/sz` · `…/relacije` | statistika (od 29. 10. 2026, `docs/STATISTIKA.md`): točnost, napovedi proti uradnim, prevozniki; izris na strežniku |
| `/statistika/vlak/{št}` · `/statistika/linija/{prevoznik}/{št}` | ena vožnja ali linija (`stat_voznja`); `/app/statistika[/bus]` → 301 na `/statistika` |
| `/vlak/{od}/{cilj}` · `/avtobus/…` | **pristajalna relacije**: odhodi danes, izmerjena zamuda, izris na strežniku |
| `/postaja/{ime}` · `/postajalisce/{ime}` | pristajalna postaje |
| `/postaje` · `/postajalisca` | kazalo — edina pot do pristajalnih poleg zemljevida strani |
| `/stik` | obrazec; nabiralnik v `/admin` |
| `/zasebnost` | kaj hranimo; skladna z `obisk.py` in `stik.py` |
| `/o-nas` | zgodba v 3D, kaj je tu, od kod podatki; edina besedilna stran z JS (vir `o-nas/`) |
| `/primerjava` | druge strani za zamude po njihovih besedah, z datumom pregleda |
| `/donacije` | za kaj gre denar, trak cilja (`config.CILJ`, ista kartica na `/`), gumb `ko-fi.com/kajros`; `KAJROS_DONACIJE=` skrije vse |
| `/admin` | **skrbnik**: obisk, napake, odzivni čas, zdravje zajema, deljenje lege, obvestila, koledar |

**Pristajalne strani so za iskalnik in brez JS**: „vlak ljubljana koper“ → odgovor v odgovoru strežnika. Katere nastanejo: `kajros/pristanek.py`; v zemljevidu strani vrh po teži (promet izhodišča × promet cilja), ostalo `noindex`. Kaj ljudje iščejo: `docs/MERITVE.md` („Iskalniki“).

Še: `/favicon.ico`, `/robots.txt`, `/sitemap.xml`, `/llms.txt`, `/sw.js`, `/brez-omrezja`; `/android` = stran s prenosom, `/prenos` = podpisan APK. Napaka = **stran** za človeka, JSON pod `/api/`. Absolutni naslov = `KAJROS_BASE_URL`, ne `request.url` (za tunelom `http://127.0.0.1:8000`). **Tujih izvorov v strani ni** razen ploščic zemljevida.

**`/admin` zahteva žeton** (brez 404): `/admin?k=<žeton>`, nato piškotek. Žeton `${KAJROS_DATA_DIR}/.admin-zeton` (`deploy/zeton.sh`, **brez sudota**), `KAJROS_ADMIN_TOKEN` povozi, v razvoju izpiše `dev-restart.sh`. Obisk **brez IP-ja** (sol dneva). Podrobno `strezba.md`.

## Kam gre

Uporabnik = potnik z vprašanjem *„kdaj mi pelje in koliko zamuja“*, ne dispečer. Iskalnik povezav = vstopna stran; zemljevid ostane, ni cilj razvoja. Vreme kot **dejavnik** zamude čaka 2–3 mesece zajema; do takrat se vreme samo *pokaže ob* zamudi.

Ne bo, ker podatka ni: cene, sestava vlaka. **Zasedenost** od 21. 10. 2026 iz poročil potnikov (`zasedenost.py`, za stikalom); validacije ima DUJPP. **Tir** od 25. 9. 2026 s table SŽ, samo kjer ga SŽ objavi (14 od 20); stran ni API, dodatek sme izginiti.

## Konvencije

* **Jezik: slovenščina** povsod — koda, komentarji, commiti, UI, dokumentacija. Šumniki obvezni.
* Komentarji povedo **zakaj**. Commit: kratka prva vrstica, telo = razlog in izmerjene posledice, ne seznam datotek.
* Brez novih odvisnosti brez razloga; `requirements.txt` ima pet vrstic.
* `venv/`, `data/`, `export/`, `posnetki/`, `*.sqlite` v `.gitignore` — **razen** `seed/kajros.sqlite` (namestitev).
* **Agregat čez vso zgodovino se ne računa v zahtevi** (`stats.summary_get()`, dnevno ob 3:30, `KAJROS_MAINT_HOUR`). Taka številka na strani nosi **čas izračuna**.
* **Mrtve kode ne puščaj** — git jo hrani. Izjema v komentarju, z rokom.
* **Odgovori na kratko, brez uvodov in olepšav** (caveman). Tehnična vsebina ostane; koda, commiti, dokumentacija = normalna proza. Izklop: „normal mode“.

## Objava

Arwen (`david@192.168.1.46`) = **edini zajem in strežnik** `kajros.app`. **Maline od 3. 11. 2026 v projektu ni** (David): na njej nič ne preverjaj, ne nameščaj, ne vleci. Ta računalnik = razvoj; podatki za analizo = kopija z arwena (`VACUUM INTO`). Podrobno `.claude/rules/objava.md`, [DEPLOY.md](DEPLOY.md).

**Objava = `git push arwen <veja>`** — kavelj na arwenu požene `deploy/posodobi.sh`, izpis se vrne. **Objavlja Claude sam** po zelenem `preveri.sh` (David 3. 11. 2026; dovoljenje `Bash(git push arwen:*)` v `.claude/settings.local.json`).

## Kje je zapisano ostalo

**Zdravje zajema v `/admin`: rumeno = samo, oranžno = `/preveri-vire` (skill), rdeče = takoj** (`kajros/zdravje.py`). Odprte luknje virov po prednosti: [docs/VIRI-PRESOJA.md](docs/VIRI-PRESOJA.md).

`.claude/rules/` — naloži se ob dotiku datotek (`paths:`); razrez **po datotekah, ki znanje rabijo**, ne po temah: `zajem` (feed, varovalke, viri), `strezba` (API, predpomnilnik, obisk), `model` (napoved, prestopi, senca), `oznake` (beseda in barva zamude, slog), `zemljevid`, `strani`, `objava` (stroji, deploy), `android`, `deljenje`, `zasedenost`. Zapis v pravila: telegrafsko, pravilo + razlog + številka, brez zgodovine.

Stanje (koliko zajetega, poraba, hitrost) = [docs/MERITVE.md](docs/MERITVE.md). Daljše: [HANDOVER.md](HANDOVER.md), [docs/APLIKACIJA.md](docs/APLIKACIJA.md), [design/README.md](design/README.md).

## Odprto

* **Vrat na usmerjevalniku ne odpiraj**: `kajros.app` gre prek imenovanega Cloudflarovega tunela z arwena (`objava.md`).
* Ločen model napovedi za avtobuse, ko bo meritev dovolj.
* **Koda zaprta** (3. 9. 2026): zasebni repozitorij, brez licence = vse pravice pridržane. **Endpointi odprti** — API sme brati vsak. Podatki CC BY-SA 4.0, navedba vira = pogoj rabe; `seed/kajros.sqlite` je izpeljanka. Zato Android ni v F-Droid/IzzyOnDroid (prosta licenca). **V Play gre od novembra 2026** (David 8. 11.), stran (`/android`, `android.md`) ostane drugi kanal; ovire in načrt nativne aplikacije: `docs/presoja/2026-11-08-nativna/NACRT.md`.
* **Iskalniki in AI: koraki z Davidovo prijavo** (Search Console, Bing, Cloudflare, objave) v `docs/ISKALNIKI-NALOGE.md`.
* **Delovni imenik še `sztrack`.** Preimenovanje prekine tekočo sejo in poti; ločeno: `mv ~/Dokumenti/Projekti/{sztrack,kajros}`.
