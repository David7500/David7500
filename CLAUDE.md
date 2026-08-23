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

CLI: `./venv/bin/python -m sztrack.cli <init|update|poll|show|stats|merge|weather|export>`

## Od kod podatki

```
SŽ + IJPP → NAP (b2b.nap.si, CC BY-SA 4.0) → DERP gtfs-generators → GTFS + GTFS-RT
```

| Kaj | URL | Velikost | Pogostost |
|---|---|---|---|
| Vozni red | `gitlab.com/api/v4/projects/derp-si%2Fgtfs-generators/packages/generic/IJPP/latest/ijpp_gtfs.zip` | 41 MB | ~1×/dan |
| Zamude | `rt.gtfs.derp.si/sources/ijpp/trip_updates` | 250 KB | 30 s |
| Ovire | `rt.gtfs.derp.si/sources/ijpp/service_alerts` | 80 KB | — |
| Vreme | `archive-api.open-meteo.com` + `api.open-meteo.com` | — | dnevno, za nazaj |

SŽ nimajo javnega API-ja; `potniski.sz.si` je za Cloudflarom, stari SOAP je mrtev.
Oba GTFS vira podpirata pogojni GET (ETag) — ob nespremenjenem se ne prenese nič.

## Kaj podatki so in česa ni — to omejuje prikaz

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa. Dejanski čas =
`vozni red + zamuda`. Iz tega:

* **Ločljivost 60 s**, `uncertainty: 120`. Ne kaži sekund. Hitrosti samo na
  odsekih ≥ 5 km (`segment_speeds()` to že filtrira).
* **Feed je drseče okno** — en klic da le postanke okoli trenutnega položaja.
  Celo vožnjo sestavljamo iz zaporednih pollov.
* **Zamude naprej po progi so napoved, ne meritev.** Merodajna je zadnja znana
  vrednost (`run`). V prikazu morajo biti označene drugače kot potrjene.
* **Zamuda je izmerjena v prometnem mestu, ne nujno na postaji** (SŽ appa piše
  npr. "Slovenska Bistrica" za vlak, ki tam ne ustavlja). Prikaz naj pove, kje.
* **Položaj vlaka je interpoliran, ne GPS.** `vehicle_positions` vsebuje
  avtobuse, vlakov ne. Dashboard zato riše vlake na zadnji znani postaji.
* **Odhodne zamude s prve postaje ni.** Feed ni nikoli poročal `stop_seq = 1`
  — najnižji zajeti je 2. Prva meritev pride šele na drugi postaji, in 29 %
  voženj (179 od 628) je tam že čez minuto. Vlak, ki *"štarta z zamudo"*, je
  v podatkih viden šele pozneje in nikoli na izhodišču.
* **Zgodovine ni nikjer.** Če je ne posnamemo sami, je ni.
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

`LPV 2010` ni oznaka proge, ampak **ena vožnja** (trip): 721 različnih številk
na 723 tripov. `route_id` je 1 : 1 s tripom in za združevanje neuporaben —
zgodovino poti gradi po `train_no`. Parnost številke nosi smer, v zajetih
podatkih brez izjeme. Predpona (`LP`, `LPV`, `IC`, `MV`, `EN` …) je vrsta vlaka.

## Koda

```
sztrack/
  geo.py         haversine, projekcija postaj na progo, Douglas-Peucker
  db.py          SQLite shema + merge_from()
  gtfs.py        pogojni prenos zipa, uvoz železniškega dela
  collector.py   poll zamud, razreševanje obratovalnega dne
  weather.py     Open-Meteo, mreža 0,1° (~8 km) × 1 h
  stats.py       zgodovina, porazdelitve, hitrosti, napoved, povezave
  server.py      lifespan: bootstrap + zajem v ozadnji niti
  api.py         FastAPI: /api/* + strani /app*
  cli.py         ukazna vrstica
  templates/     connections.html (vstopna), dashboard.html, train.html
  static/        common.js + connections/dashboard/train .js/.css
```

Tabele: `station`, `edge`, `trip`, `sched`, `service_day` (statika) ·
`obs` (dnevnik sprememb), `run` (zadnje stanje na postanek) · `weather` · `alert`.

Zajem piše **samo ob spremembi vrednosti** — sicer bi bilo milijone praznih vrstic.

## Strani

| pot | kaj |
|---|---|
| `/app` | iskalnik povezav — vstopna stran |
| `/app/map` | živi zemljevid (Leaflet + OSM rastrske ploščice) |
| `/app/train/{no}` | okno enega vlaka: profil poti, zgodovina, razmere, hitrosti |

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
validatorjem (skill `dataviz`, `scripts/validate_palette.js`), ne na oko.

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

Lokalna baza `data/sz.sqlite` (2026-08-23): 11913 meritev, 7176 postankov,
3 obratovalni dnevi, 21312 vremenskih vrstic, 267 postaj, 5,4 MB. Merodajen je
zajem na malini; lokalna kopija je posnetek in za njim zaostaja.

Za napoved zamude (`stats.predict`) je zaenkrat izhodiščni model: prenos
trenutne zamude naprej, popravljen za historično mediano spremembe na odseku.
Za kaj boljšega rabi 2–3 mesece zajema.

## Odprto

* Dostop do API-ja od zunaj (Tailscale ali Cloudflare Tunnel).
  **Vrat na usmerjevalniku ne odpiraj — API nima avtentikacije.**
* Oblikovne smeri in mockupi v `design/`, dve platni:
  * smeri in barve — https://claude.ai/code/artifact/189e04ee-26e3-4c2e-916a-26da4e9ae709
  * prenova okna vlaka (`design/okno-vlaka/`) —
    https://claude.ai/code/artifact/c219b447-a3b8-4d5a-b5a8-267953914791
  Platni sta skica, **koda je merodajna**: okno vlaka je od takrat dobilo
  semafor razmer namesto enega modrega odtenka in izgubilo zavihke.

Daljši zapisi: [HANDOVER.md](HANDOVER.md) (stanje projekta),
[docs/APLIKACIJA.md](docs/APLIKACIJA.md) (dogovorjeno o prikazu),
[design/README.md](design/README.md) (smeri in barve).
