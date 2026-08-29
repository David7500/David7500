# sztrack

Zajem in analiza **zamud slovenskih vlakov** iz odprtih podatkov. Zaledje v
Pythonu (FastAPI + SQLite), prikaz v vanilla JS.

Veja: `claude/slovenske-zeleznice-api-ql84hf` · remote `David7500/David7500`

## Zagon

```bash
./venv/bin/python -m uvicorn sztrack.api:app --host 127.0.0.1 --port 8001 --reload
```

Venv je `venv/` (Python 3.12), ne `.venv`. Med razvojem strežnik pogosto že
teče na 8001 — preveri s `pgrep -af uvicorn`, preden zaganjaš drugega.

CLI: `./venv/bin/python -m sztrack.cli <ukaz>` — `init`, `update`, `poll`,
`show`, `stats`, `merge`, `weather`, `export`, `alerts`, `backtest`, `repair`,
`seed`.

Avtobusi se uvozijo z `SZ_AGENCIES=1118` (LPP). Brez tega so v bazi samo SŽ.

Med razvojem: `./scripts/dev-restart.sh` (počaka na sproščen port; `pkill -f`
z golim vzorcem ubije tudi lupino, v kateri je ukaz zapisan).

## Od kod podatki

```
SŽ + IJPP → NAP (b2b.nap.si, CC BY-SA 4.0) → DERP gtfs-generators → GTFS + GTFS-RT
```

| Kaj | URL | Velikost | Pogostost |
|---|---|---|---|
| Vozni red | `gitlab.com/api/v4/projects/derp-si%2Fgtfs-generators/packages/generic/IJPP/latest/ijpp_gtfs.zip` | 41 MB | ~1×/dan |
| Zamude | `rt.gtfs.derp.si/sources/ijpp/trip_updates` | 250 KB | 30 s |
| Ovire in žive zamude | `rt.gtfs.derp.si/sources/ijpp/service_alerts` | 110 KB | 60 s |
| Lega vozil | `rt.gtfs.derp.si/sources/ijpp/vehicle_positions` | 2 KB | 30 s |
| Vreme | `archive-api.open-meteo.com` + `api.open-meteo.com` | — | dnevno, za nazaj |

SŽ nimajo javnega API-ja; `potniski.sz.si` je za Cloudflarom, stari SOAP je mrtev.
Vsi GTFS viri podpirajo pogojni GET (ETag) — ob nespremenjenem se ne prenese nič.

V zipu je **ves** slovenski javni potniški promet, ne le železnica: 20 592
voženj petih agencij (Arriva 8914, Nomago 6864, LPP 3060, AP Murska Sobota 965,
SŽ 789). Uvoz jemlje samo SŽ — vlake in **njihove nadomestne prevoze**
(`route_type = 3`, 56 voženj). Ostale agencije so izpuščene, ne pa nedosegljive;
`config.RAIL_AGENCY_ID` je edino, kar jih loči.

## Kaj podatki so in česa ni — to omejuje prikaz

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa. Dejanski čas =
`vozni red + zamuda`. Iz tega:

* **Ločljivost 60 s**, `uncertainty: 120`. Ne kaži sekund. Hitrosti samo na
  odsekih ≥ 5 km (`segment_speeds()` to že filtrira).
* **Feed je drseče okno** — en klic da le postanke okoli trenutnega položaja.
  Celo vožnjo sestavljamo iz zaporednih pollov.
* **Zamude naprej po progi so napoved, ne meritev** -- in ta napoved je
  **izmerjeno slaba**. Feed za še nedosežene postanke pogosto objavi 0, dokler
  nima prave vrednosti. Merjeno (`sztrack backtest --operator`, 11 310 nalog):
  prevoznikova napoved MAE 7,9 min in 58 % v petih minutah, prenos trenutne
  zamude naprej MAE 1,3 min in 94 %. V najhujšem rezu -- feed pravi 0, vlak pa
  zamuja ≥ 5 min -- je napaka 18,5 min in v petih minutah je 6 % napovedi.
  **Zato prikaz naprej po progi uporablja lastno oceno, ne feedove vrednosti**;
  prevoznikova številka ostane vidna v naprednem pogledu.

* **Ne verjemi ničli, ki jo feed vrne za en klic.** Pri 14 % postankov z več
  kot dvema zapisoma se pojavi vzorec X, 0, X v razmiku ene minute. Zamuda med
  dvema klicema ne more pasti za več, kot je vmes minilo časa. `run` zato ničlo
  po zamudi ≥ 5 min sprejme šele, ko jo potrdi drugi zaporedni poll
  (`collector.is_zero_blip`); dnevnik `obs` obdrži vse. Isto varovalo velja pri
  določanju lege vlaka -- sicer (vozni red + 0) pomeni, da je postanek že minil,
  in vlak na zemljevidu skoči naprej.
* **Zamuda je izmerjena v prometnem mestu, ne nujno na postaji.** Ime tega
  mesta **imamo** -- v `SZ-DELAY-*` obvestilih ("Vlak EC 79 ima izjemno zamudo
  161 min ob prihodu na postajo Sevnica"). `run` pozna samo voznoredne postanke,
  zato je to edini vir. Hrani se v `delay_report`, prikaz ga postavi ob našo
  vrednost.
* **Položaj vlaka je interpoliran, ne GPS.** `vehicle_positions` vsebuje
  avtobuse, vlakov ne. Dashboard zato riše vlake na zadnji znani postaji.
  **Avtobusi pa GPS imajo** -- z legendo, smerjo in hitrostjo (do 130 vozil
  hkrati). Na zemljevidu so zato puščica v smeri vožnje, vlak pa krog na
  postaji: enak simbol za oboje bi zabrisal razliko med izmerjeno lego in
  zadnjo znano postajo. Hrani se samo trenutna lega (`vehicle_now`, upsert):
  sled bi bila ~300 000 točk na dan, prikaz "kje je zdaj" pa rabi eno vrstico.
* **Odhodne zamude s prve postaje ni — pri vlakih.** Feed za vlak nikoli ni
  poročal `stop_seq = 1`; najnižji zajeti je 2. Vlak, ki *"štarta z zamudo"*,
  je v podatkih viden šele na drugi postaji. Odhodna tabla zato za izhodišče
  vzame meritev naslednje postaje in zraven napiše, od kod je ("izmerjeno na
  postaji Grosuplje") -- brez tega je tabla prazna prav tam, kjer potnik
  vstopa. **Pri avtobusih to ne velja**: ti poročajo tudi `stop_seq = 1`, zato
  tabla uporabi njihovo lastno meritev. Ista koda pokrije oboje, ker vzame
  naslednjo postajo šele, kadar lastne ni.
* **Zgodovine ni nikjer.** Če je ne posnamemo sami, je ni.
* **Zakaj vlak zamuja, pove `service_alerts`.** `SZ-OVIRA-*` so dela na progi,
  nadomestni prevozi in združene garniture, vezani na `route_id` (ta je 1 : 1
  s tripom, zato jih znamo pripeti na številko vlaka). Avgusta 2026 jih je bilo
  ~45 hkrati -- nadomestni prevoz Ljubljana–Logatec in Divača–Koper do
  12. decembra, zapore enega tira Celje–Šentjur, Poljčane–Pragersko,
  Maribor–Hoče. **To pojasni, zakaj so zamude v zajetih dneh tako velike.**

* **Odpovedi niso strukturirane.** GTFS-RT ima za to `schedule_relationship`
  (CANCELED, SKIPPED), a SŽ ga ne uporablja -- v vseh zajetih zapisih je
  vrednost `SCHEDULED`. Odpoved sporočijo z besedilom obvestila ("Vlak vozi
  samo do postaje Ljubljana Šiška", `effect = 6`). Zajem polje vseeno šteje in
  ob prvi neničelni vrednosti zavpije v dnevnik; prikaza zanj namenoma še ni,
  ker bi bil to prikaz za podatek, ki ne obstaja.

* **Ni** cen, sestave vlaka, perona, zasedenosti. Mednarodni vlaki (EN/MV)
  pogosto brez realtime pokritja.

Izjema je **vreme**: Open-Meteo ima arhiv za nazaj, zato ga ni treba zbirati
vnaprej — `sztrack weather` ga dopolni za že zajete zamude kadarkoli.

## Kam gre

Ciljni uporabnik ni dispečer, ampak potnik z vprašanjem *"kdaj mi pelje vlak
in koliko zamuja"*. Iz tega izhaja vrstni red:

1. **Iskalnik povezav postaja → postaja je vstopna stran** (`/app`), kot v
   aplikaciji Grem z vlakom. Zemljevid je pogled dispečerja — ostane, ker je
   uporaben, a ni vhod in ni cilj razvoja.
2. Klik na vlak odpre **okno tega vlaka** z analizo poti.
3. Globlja analiza (porazdelitve, vzroki, vreme kot **dejavnik** zamude) čaka
   2–3 mesece zajema. Do takrat ne graditi napovednih modelov in ne trditi
   vzročnosti — vreme se zdaj samo *pokaže ob* zamudi, ne pojasnjuje je.

Česar ne bo, ker podatka ni: cene, sestava vlaka, peron, zasedenost.

## Številke vlakov

`LPV 2010` ni oznaka proge, ampak **ena vožnja** (trip): ~730 različnih številk
na prav toliko tripov. `route_id` je 1 : 1 s tripom in za združevanje neuporaben —
zgodovino poti gradi po `train_no`. Parnost številke nosi smer, v zajetih
podatkih brez izjeme. Predpona (`LP`, `LPV`, `IC`, `MV`, `EN` …) je vrsta vlaka; `BUS …` je
nadomestni prevoz (`trip.mode = 'bus'`).

**`trip_id` so med regeneracijami GTFS stabilni.** Preverjeno ob uvozu novega
voznega reda: vseh 60 409 zajetih meritev se je še vedno ujemalo s tripom.
Zajema torej ni treba varovati pred `sztrack update` — statične tabele se
zamenjajo, `obs` in `run` pa ostaneta veljavna.

## Koda

```
sztrack/
  geo.py         haversine, projekcija postaj na progo, Douglas-Peucker
  db.py          SQLite shema + merge_from() + migracije
  gtfs.py        pogojni prenos zipa, uvoz železniškega dela
  collector.py   poll zamud, razreševanje obratovalnega dne, prehodne ničle
  alerts.py      ovire (SZ-OVIRA) in žive zamude s prometnim mestom (SZ-DELAY)
  weather.py     Open-Meteo, mreža 0,1° (~8 km) × 1 h
  stats.py       zgodovina, porazdelitve, hitrosti, napoved, povezave
  journey.py     odhodna tabla, iskanje postaj, zveze z enim prestopom
  backtest.py    merjenje napovedi z izpuščanjem enega dne
  server.py      lifespan: bootstrap + zajem v ozadnji niti
  api.py         FastAPI: /api/* + strani /app*
  cli.py         ukazna vrstica
  templates/     connections.html (vstopna), dashboard, train, alerts, stats
  static/        base.css (barvni žetoni) + common.js + po ena .js/.css na stran
                 (iskalnik in avtobusna stran si delita connections.js)
tests/           enotni testi čistih funkcij (pytest, requirements-dev.txt)
scripts/         dev-restart.sh, preveri_paleto.py, vzorci_feeda.py, build_deploy_zip.sh
```

**`trip.network` loči strani aplikacije: `zeleznica` in `avtobus`.**
To NI isto kot `mode`. Nadomestni prevoz SŽ je `mode = 'bus'`, a
`network = 'zeleznica'`, ker na svoji relaciji **zamenjuje vlak** in sodi v
isti odgovor kot vlaki. LPP in ostali prevozniki so `avtobus` in imajo svojo
stran `/app/bus`: potnik ve, ali gre z vlakom ali z busom, in ju ne išče
skupaj. Mešanje ni bilo le nepregledno, ampak merljivo škodljivo -- iskanje
"ljublj" je vračalo mestna postajališča (LPP ima tam desetkrat več postankov)
in postajo Ljubljana potisnilo iz prvih petih zadetkov.

Vsi potniški endpointi imajo `network` in **privzeto `zeleznica`** -- tako
mešanja ne more povzročiti pozabljen parameter. Skupen ostane samo zemljevid,
kjer sta vlak in avtobus različna simbola.

`trip.mode` loči `vlak` od `bus`, `trip.agency` pa prevoznika. Avtobusi so v
istih tabelah, ker jih GTFS modelira enako in ker sodijo v isti odgovor --
**ne pa v `edge`**: vozijo po cesti in bi mreži prog dodali odseke, ki niso proge.

Kar je pri avtobusih drugače in se hitro pozabi:

* **Številka linije ni številka vožnje.** LPP linija 3G ima 388 voženj. Vsaka
  poizvedba po `train_no` mora skozi `stats.resolve_trip()`; povezave na eno
  vožnjo nosijo `?trip=<id>`. Isto velja za devet vlakov s sezonskimi
  različicami -- prav ta napaka je vozni red vlaka 4292 podvojila.
* **Barva linije ni barva linije.** Vsi LPP `route_color` so ista zelena
  prevoznika. Barva torej linij ne loči in ne sme; oznaka nosi ime prevoznika
  in številko ("LPP 25"), ker je "25" lahko čigar koli.
* **Mestno postajališče ima svoj `stop_id` za vsako smer.** "Bavarski dvor"
  je v `station` dvakrat. Vse v aplikaciji teče po imenu postaje, zato iskanje
  po imenu združuje.
* **Zemljevid je edini skupni pogled.** Vlak je krog na zadnji postaji z
  meritvijo, avtobus puščica na izmerjeni legi; plast avtobusov se da odložiti.
* **Pragovi za prestop so odvisni od omrežja** (`journey.TRANSFER_LIMITS`):
  železnica 6–120 min, avtobus 3–30. Tri minute so pri mestni liniji prestop,
  pri vlaku lovljenje; čakanje pol ure na liniji, ki vozi vsakih deset minut,
  pa ni prestop, ampak znak, da smo zamudili tri boljše.

Tabele: `station`, `edge`, `trip`, `sched`, `service_day` (statika) ·
`obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `weather` ·
`alert` + `alert_entity` (ovire) · `delay_report` (kje in koliko, po prevozniku).

Zajem piše **samo ob spremembi vrednosti**, in sprememba mora biti vsaj
`collector.OBS_MIN_DELTA_S` (60 s) od zadnje **zapisane**. Prikaz ima
ločljivost ene minute in sekund ne kaže nikoli, feed sam prilaga
`uncertainty: 120` -- sprememba za petnajst sekund torej ni sprememba, ampak
šum.

Pri vlakih to nič ne spremeni: ti poročajo v celih minutah in imajo **1,6
zapisa na postanek**. Pri mestnih avtobusih pa **23,3**, z mediano spremembe
15 sekund — 14 000 vrstic na uro za nihanje, ki ga ne pokažemo. Brez praga bi
vlaki + LPP dali ~20 GB na leto, kar na malini ni izvedljivo.

Primerjamo z zadnjo **zapisano** vrednostjo, ne s prejšnjo prebrano, da se
počasno lezenje sešteva in ne izgine. `run` ostane točen -- prag velja samo
za dnevnik.

## Strani

| pot | kaj |
|---|---|
| `/app` | vlaki: iskalnik povezav in odhodna tabla — vstopna stran |
| `/app/bus` | avtobusi (LPP …): ista stran, drugo omrežje |
| `/app/map` | živi zemljevid — **edini skupni pogled** obeh omrežij |
| `/app/train/{no}` | okno ene vožnje: profil poti, zgodovina, razmere, hitrosti |
| `/app/ovire` | dela na progi in nadomestni prevozi, s filtrom po besedilu |
| `/app/statistika` | razrezi zajetega: po vrsti vlaka, uri, dnevu v tednu |

Okno vožnje je isto za vlak in avtobus, a govori o tem, kar je pred potnikom:
besedo (vlak / nadomestni prevoz / avtobus), opozorilo in povezavo nazaj
izbere iz `network`. Pri avtobusu z več vožnjami na isto številko linije je
v naslovu `?trip=<id>`.

Vsaka stran ima preklop **preprosto / napredno**. To ni druga stran: napredni
pogled je razred `is-advanced` na `<body>`, ki odkrije elemente z razredom
`adv-only` (p90, delež točnih, številka postanka, kaj pravi feed). Potnik in
radovednež gledata isto vožnjo.

Okno vlaka je **ena slika, ne zavihki**. Krivulja zamude čez vse postaje poti
in pod njo, v istem grafu, pas razmer: vprašanje ni *"kakšno je vreme"*, ampak
*"je zamuda tam, kjer je bilo vreme hudo"*. Hitrost po odsekih je isti podatek
v drugi enoti, zato leži na dnu v zaprtem `<details>` in se naloži šele ob
odprtju. Zavihkov ne vračaj — eno vprašanje so razbili na tri strani.

Frontend je **vanilla JS brez ogrodja**. Grafi so ročno risan SVG z lastnim
tooltipom (`train.js`) — ni chart knjižnice in je ne dodajaj brez razloga.
Leaflet se nalaga z unpkg CDN.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

Pravila, ki se jih drži obstoječa koda in naj se jih tudi nova:

* **Vsaka oznaka poleg barve vedno nosi tudi minute.** Barva nikoli ne nosi
  pomena sama — barvna slepota, in +4 proti +14 je za potnika bistvena razlika.
* Odtenek lestvice se uporablja **samo tam, kjer pomeni velikost zamude**.
* Kjer meritve ni (ocena, napoved), nastopi rezervirana `#a8d8ff`, ki je
  lestvica ne uporablja.
* Vreme ima **svoj semafor**, ne odtenek lestvice zamud.

### Semafor razmer

| stopnja | oznaka | barva |
|---|---|---|
| 0 | mirne | `#6b7480` |
| 1–3 | blage | `#5aa87d` |
| 4–6 | zahtevne | `#d9b33c` |
| 7–10 | hude | `#d1495b` |

Stopnja 0–10 je seštevek točk za padavine, sneg, sunke vetra, meglo, nevihto in
mraz (`weather.severity()`). Razčlenitev gre v tooltip — indeks brez razčlenitve
je črna skrinja. Modelska vrednost za celico 8 × 8 km, ne meritev na peronu.

**Lestvic ne mešaj v istem registru.** Rumena razmer `#d9b33c` proti svetli
oranžni zamud `#f2a87e` je pri deutanu ΔE 5,5 — nerazločljivo. Zato je zamuda
krivulja s pikami zgoraj, razmere pa stolpci v ločenem pasu spodaj, in vsak
stolpec od stopnje 4 naprej nosi svojo številko. Paleto preverjaj z
`scripts/preveri_paleto.py`, ne na oko. Ta izmeri kontrast (WCAG), monotonost
svetlosti in razločljivost pri barvni slepoti (CIEDE2000 na simulaciji
protan/deutan/tritan). Trk obeh lestvic je pri tritanu **ΔE 1,6**, torej hujši
od tu prej zapisanih 5,5 — ločena registra sta nujna, ne okrasna.

## Razdalje med postajami

`stop_times.txt` nima `shape_dist_traveled`. Postaje projiciramo na polilinijo
iz `shapes.txt`, razlika kumulativnih razdalj je dolžina odseka, mediana čez
vse vlake. Rezultat: 267 postaj, 389 odsekov (275 elementarnih), **1253,8 km**
elementarne mreže — ujema se z realno slovensko mrežo.

`elementary = 0` so "preskoki" hitrih vlakov čez vmesne postaje: za risanje
mreže filtriraj `elementary = 1`, za hitrosti uporabi odsek, ki ustreza
dejanskemu paru zaporednih postankov danega vlaka.

**To niso uradne km-lege**, ampak dolžine GTFS shapeov — odstopanje ~2–4 %
(Zidani Most–Ljubljana da 63,63 km proti uradnim ~61 km).

## Poraba

| | |
|---|---|
| Uvoz GTFS | 23 s, vrh 54 MB (pretočno branje `shapes.txt`; prej 269 MB) |
| Strežnik ob zagonu | 57–60 MB RSS |
| Po prvem zajemu | 74 MB RSS |
| Osvežitev v istem procesu | vrh 89 MB, ostane 85 MB → zato `SZ_REFRESH=off` privzeto |

## Objava

Ciljni gostitelj je Raspberry Pi doma: **`david@192.168.1.166`**. Tam ob
koncu teče produkcijski zajem — malina je gor ves čas, ta računalnik ne, zato
je merodajna baza na malini in se z nje vleče (`sztrack merge`), ne obratno.

Namestitev/posodobitev: `sudo bash deploy/install-rpi.sh && sudo systemctl
restart sztrack.service` (idempotentna; restart je nujen posebej, `enable --now`
aktivne storitve ne restarta). Podrobnosti v [DEPLOY.md](DEPLOY.md).

**Deploy mora pognati uporabnik sam** — `david` na malini za sudo rabi geslo,
agent nima terminala zanj. `sudo -n true` lahko uspe, a le zaradi predpomnjene
sudo-znamke po uporabnikovem lastnem ukazu; NOPASSWD velja samo za
`/usr/bin/tee /sys/class/leds/…`. Pripravi ukaz in ga daj uporabniku, ne
poskušaj sam.

Pella je bila slepa ulica — zajem je delal, javni API pa je vračal Cloudflare
526 na vseh poteh, ker njihov edge ne vzpostavi TLS do izvora.

Zajem s prejšnjega gostitelja se prilije z `sztrack merge <druga.sqlite>` —
varno tudi pri vzporednem teku, ker so meritve ključene po
`(trip_id, service_date, stop_seq, feed_ts)`. Idempotentno.

## Konvencije

* **Jezik: slovenščina** povsod — koda, komentarji, commiti, UI, dokumentacija.
  Šumniki obvezni.
* Komentarji povedo **zakaj**, ne kaj. Obstoječi so taki; drži se tega.
* Commit sporočila: kratka prva vrstica, telo pojasni razlog in izmerjene
  posledice, ne naštevanja datotek.
* `venv/`, `data/`, `export/`, `*.sqlite` so v `.gitignore` — **razen**
  `seed/sz.sqlite`, ki ga rabi namestitev (izjema `!seed/sz.sqlite`).
* Ne dodajaj odvisnosti brez razloga; `requirements.txt` ima pet vrstic in
  naj tako ostane.
* **V enem SQL stavku ne mešaj `?` in `:ime`.** sqlite veže po vrstnem redu
  pojavitve in tiho vrne napačne vrstice, brez izjeme. Cel stavek naj bo enega
  sloga.
* `run` hrani **zadnje stanje** postanka, zato je `MAX(stop_seq)` po koncu
  vožnje terminus — ne dokaz, da vlak še vozi. Živost sklepaj iz voznoredne
  ure in prevoženih postankov (`_LIVE_SQL`).
* **Spremembo prikaza poglej, preden jo razglasiš za končano.** Posnetek:
  `chromium --headless --disable-gpu --window-size=1850,1000
  --virtual-time-budget=7000 --screenshot=$HOME/x.png <url>` — v `/tmp`
  chromium ne more pisati, zato v `$HOME`.

## Stanje zajema

Lokalna baza `data/sz.sqlite` (2026-08-29): 60402 meritev,
38749 postankov, 9 obratovalnih dni,
34632 vremenskih vrstic, 267 postaj,
44 zapisanih obvestil o ovirah (~20 hkrati veljavnih), 13.7 MB.
Merodajen je zajem na malini; lokalna kopija je posnetek in za njim zaostaja.

Za napoved zamude (`stats.predict`): prenos trenutne zamude naprej, popravljen
za historično mediano spremembe pri **tem vlaku**. To ni ugibanje -- izmerjeno
je (`sztrack backtest`, 258 137 nalog, izpuščanje enega dne):

| model | MAE | v 5 min |
|---|---|---|
| prenos (referenca) | 2,91 min | 82,8 % |
| **vlak (v uporabi)** | **2,00 min** | **90,3 %** |
| odsek | 2,22 min | 88,1 % |
| odsek + razred zamude | 2,26 min | 87,8 % |
| združen (krčenje) | 1,98 min | 89,6 % |

Iz tega dvoje, kar velja spoštovati, preden kdo piše nov model:

* **Združevanje po odseku model poslabša.** Na istem tiru se IC in lokalni vlak
  ne obnašata enako, zato skupna mediana zabriše prav tisto, kar šteje.
* **Združen model prihrani 1 % MAE in izgubi pri deležu v petih minutah.** To
  ni vredno zapletenosti. Prag `MIN_SAMPLES` 1–3 da isti rezultat, 4 in več
  poslabša.

**Preizkušeno in ne pomaga** (`sztrack backtest --day-offset`): popravek za
stanje mreže na ta dan. Zamisel je razumna -- če cel dan zamuja bolj kot
običajno, bo tudi ta vlak -- a povprečna sprememba zamude se čez zajete dni
giblje le med 115 in 142 s. Premalo, da bi kaj rešilo, dovolj, da doda šum:
MAE 2,00 → 2,06 min, delež v petih minutah 90,2 % → 89,1 %. (Mediana je za to
neuporabna: pri večini sosednjih postankov se zamuda ne spremeni, zato je
vsak dan 0.)

Vsak nov model naj se najprej pomeri s `prenos`. Kar ga ne premaga, ne sodi
v prikaz, pa naj bo še tako domiseln.

## Odprto

* Dostop do API-ja od zunaj (Tailscale ali Cloudflare Tunnel).
  **Vrat na usmerjevalniku ne odpiraj — API nima avtentikacije.**
* Oblikovne smeri in mockupi v `design/`, dve platni:
  * smeri in barve — https://claude.ai/code/artifact/189e04ee-26e3-4c2e-916a-26da4e9ae709
  * prenova okna vlaka (`design/okno-vlaka/`) —
    https://claude.ai/code/artifact/c219b447-a3b8-4d5a-b5a8-267953914791
  Platni sta skica, **koda je merodajna**: okno vlaka je od takrat dobilo
  semafor razmer namesto enega modrega odtenka, izgubilo zavihke ter dobilo
  preklop preprosto/napredno, obvestila o ovirah in poročilo prevoznika.
* Zemljevid še vedno stoji na svetlih OSM ploščicah pod temno temo. Ni napaka
  podatkov, je pa edina stran, kjer se aplikacija bori sama s sabo.
* Avtobusi: `vehicle_positions` nosi ~20 vozil z GPS (LPP in medkrajevni),
  vlakov pa ne. Isti GTFS zip že vsebuje avtobusni del, ki ga uvoz namenoma
  izpusti (`RAIL_ROUTE_TYPE`).

Daljši zapisi: [HANDOVER.md](HANDOVER.md) (stanje projekta),
[docs/APLIKACIJA.md](docs/APLIKACIJA.md) (dogovorjeno o prikazu),
[design/README.md](design/README.md) (smeri in barve).
