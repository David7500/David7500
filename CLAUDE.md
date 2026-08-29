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

**Vlaki in avtobusi ne pošiljajo istega.** Izmerjeno na živem feedu, po
prevozniku (delež postankov v enem klicu):

| | `arrival.delay` | `departure.delay` | absolutni čas | `uncertainty` | `vehicle.id` |
|---|---|---|---|---|---|
| SŽ | 100 % | 100 % | **0 %** | 100 % | ne |
| Arriva | 61 % | 100 % | 92 % | 0 % | da |
| Nomago | 42 % | 100 % | 97 % | 0 % | da |
| LPP | 39 % | 99 % | 100 % | 0 % | da |
| AP MS | 31 % | 100 % | 94 % | 0 % | da |

Iz tega dvoje, kar velja spoštovati:

* **Nikoli ne beri `stu.arrival.delay` naravnost.** Protobuf za neizpolnjeno
  polje vrne 0, kar je videti kot „točno". Prav ta napaka je v bazo zapisala
  11 906 od 20 523 avtobusnih vrstic (58 %) kot točne; delež točnih je bral
  **84,3 % namesto 71,2 %**. Pri železnici ni prizadeta nobena vrstica.
  Uporabljaj `collector._delay_of()`, ki polje preveri in ob absolutnem času
  zamudo **izračuna** — preverjeno proti poročani odhodni zamudi: mediana
  razlike −9 s, 87 % v eni minuti.
* **Zato povsod `COALESCE(delay_dep, delay_arr)`, ne obratno.**
  `departure.delay` je izpolnjen pri vseh prevoznikih stoodstotno.

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa. Dejanski čas =
`vozni red + zamuda`. Iz tega:

* **Ločljivost 60 s**, `uncertainty: 120`. Ne kaži sekund. Hitrosti samo na
  odsekih ≥ 5 km (`segment_speeds()` to že filtrira).
* **Feed je drseče okno** — en klic da le postanke okoli trenutnega položaja.
  Celo vožnjo sestavljamo iz zaporednih pollov.
* **Meja med meritvijo in napovedjo je `stats.last_measured()`.** Vsak prikaz,
  ki kaže zamudo, jo mora upoštevati: kar je za zadnjim prevoženim postankom,
  je feedova napoved. Ta napaka je bila že dvakrat -- v `/api/live` in v
  odhodni tabli, kjer je IC 502 pri +17 min v Borovnici na tabli v Litiji
  pisal **0 min**. Potnik bi bral, da je vlak točen.
* **Zamude naprej po progi so napoved, ne meritev** -- in ta napoved je
  **izmerjeno slaba**. Feed za še nedosežene postanke pogosto objavi 0, dokler
  nima prave vrednosti. Merjeno (`sztrack backtest --operator`, 11 310 nalog):
  prevoznikova napoved MAE 7,9 min in 58 % v petih minutah, prenos trenutne
  zamude naprej MAE 1,3 min in 94 %. V najhujšem rezu -- feed pravi 0, vlak pa
  zamuja ≥ 5 min -- je napaka 18,5 min in v petih minutah je 6 % napovedi.
  **Zato prikaz naprej po progi uporablja lastno oceno, ne feedove vrednosti**;
  prevoznikova številka ostane vidna v naprednem pogledu.

* **Enotna zamuda čez vso vožnjo je pri avtobusih sumljiva, a ni dokaz.**
  Merjeno na 3 636 vožnjah z vsaj petimi zajetimi postanki: pri **železnici**
  je enotna zamuda pogosta (19,7 % voženj), a **nikoli nad 60 min** — to je
  vlak, ki je ves čas dve minuti pozen. Pri **avtobusih** je enotnih le 2,2 %
  voženj, a **11 od teh 20 je nad 60 min**, in od 19 avtobusnih voženj z
  zamudo nad uro jih je 11 takih. A6345 je imel 7 800 s enako na vseh 46
  postankih.

  **Prikaza za to (še) ni namenoma.** Feed te zapise pošilja z današnjim
  `start_date`, torej naša razrešitev obratovalnega dne ni kriva, in enotna
  zamuda je fizično mogoča: vozilo odpelje pozno in nato vozi po voznem redu.
  Devet dni in dvajset primerov je premalo za pravilo, ki bi skrival podatke.
  Kar bi to razrešilo, je sled skozi `obs`: ali se postanki v zaporednih
  pollih premikajo. Do takrat velja samo `api.MAX_LIVE_DELAY_S`.

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
  zato je to edini vir. Hrani se v `delay_report`.

  Prevoznikovo poročilo je tudi **svežejše od naše meritve**: izmerjeno na 64
  primerjanih vožnjah je novejše v 97 % primerov, mediana razlike +40 s. Zato
  ga zemljevid in glava okna vožnje postavita pred našo vrednost -- a kraj in
  zamuda morata biti **iz istega vira**, sicer piše "Dobova" ob zamudi,
  izmerjeni v Sevnici.

  Zaporedje teh poročil je **dnevnik vožnje**, kakršnega ni nikjer drugje:
  IC 503 je šel s +6 v Ormožu na +29 v Litiji, v Borovnici nadoknadil osem
  minut in do Postojne spet zdrsnil na +25. V oknu vožnje, napredni pogled.
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
  stats.py       zgodovina, porazdelitve, hitrosti, napoved, dnevni povzetek
  journey.py     odhodna tabla, iskanje postaj, zveze s prestopi
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
* **Veriga vozila je edini vir odgovora, kje je avtobus, ki se še ni začel.**
  `trips.txt` nosi `block_id` -- zaporedje voženj istega fizičnega vozila.
  Imajo ga **samo avtobusi** (vseh 789 voženj SŽ je brez) in tudi tam le
  7 547 od 20 736 voženj (36 %), v 1 385 blokih. Veriga je resnična: med
  zaporednima vožnjama je le 0,9 % prekrivanj, mediana postanka 14 min, v
  69 % se konec ene ujema z začetkom naslednje. Isti `block_id` nastopa pri
  več `service_id` (788 od 1385), zato se sosed **išče po obratovalnem dnevu**,
  ne po `service_id`.

  Merjeno ob 20:22: od 25 voženj, ki so se začenjale v naslednji uri in pol,
  jih je 17 imelo prejšnjo vožnjo v bloku in 11 od teh svežo GPS lego. To je
  edini način, da o avtobusu pred odhodom sploh kaj povemo -- zanj takrat ni
  ne zamude ne lege, vozilo pa obstaja.

  **Zamude prejšnje vožnje ne prenašaj naprej.** Izmerjeno na 195 parih
  zajetih voženj: prenos zamude MAE 4,53 min, „predpostavi točno" 2,29 min --
  prenos je torej **slabši od nevednosti**. Vozilo zamudo med vožnjama
  nadoknadi: kadar prejšnja zamuja ≥ 5 min (mediana 12 min) in ima vmes
  15--60 min postanka, se na naslednjo prenese 11 %. Zato je prejšnja vožnja
  v prikazu **dejstvo o vozilu** („zdaj pri postajališču X, na prejšnji vožnji
  +1 min"), ne napoved odhoda, in prikaz to tudi pove.

* **`bikes_allowed` je v celotnem GTFS ničla.** Vseh 20 736 voženj petih
  agencij ima `0` = „ni podatka". Polje obstaja, podatka ni -- zato ga uvoz
  ne bere in ga v shemi ni. Isto velja za `wheelchair_accessible`, ki ga
  `trips.txt` sploh nima. Če se to kdaj spremeni, je oboje en stolpec dela.

* **Prestopov je lahko do trije.** `journey.transfers()` išče enega v SQL in
  zna pri njem povedati, ali zveza drži (meritev obeh vlakov na prestopni
  postaji). Kadar ne najde nič, prevzame `journey.plan()`: dnevni vozni red v
  pomnilnik in krog na nogo, do štirih nog. Vzorec 80 parov železniških postaj
  je imel **36 % brez odgovora**; s tem jih ostane **4 %**. Ljutomer mesto →
  Ribnica in Stara Cerkev → Prevalje rabita tri prestope, kar ni izmišljen
  primer. Cena: 28 ms na železnici, 60 ms na avtobusnem omrežju.
* **Pragovi za prestop so odvisni od omrežja** (`journey.TRANSFER_LIMITS`):
  železnica 6–120 min, avtobus 3–30. Tri minute so pri mestni liniji prestop,
  pri vlaku lovljenje; čakanje pol ure na liniji, ki vozi vsakih deset minut,
  pa ni prestop, ampak znak, da smo zamudili tri boljše.

`trip.start_s` / `trip.end_s` sta **prvi odhod in zadnji prihod vožnje**,
izpeljana iz `sched`, a shranjena v `trip`, ker ju rabi najbolj vroča
poizvedba — "kaj se zdaj vozi". Polni ju `db.fill_trip_window()` ob uvozu
GTFS in ob migraciji. Kdor vstavlja vožnje mimo uvoza (test, ročni popravek),
ju mora zapolniti, sicer vožnja **ni na seznamu živih**.

**Vožnja, ki zamuja več kot `api.MAX_LIVE_DELAY_S` (6 h), ni živa.** To je
pravilo prikaza, ne pospešek. Pri železnici ni nobene zamude čez tri ure
(najhujša EC 79 z 2,9 h); pri avtobusih je nad šest ur 0,67 % vrstic in te
niso zamude — Nomagov N6571 je imel 27 060 s enako na vseh 44 postankih
vožnje, ki je vozila ob 04:15, kar je feedova zamenjava prometnega dne.

`trip.block_id` je veriga voženj istega vozila (glej zgoraj). Indeks
`trip_block` je **delen** (`WHERE block_id IS NOT NULL`): dve tretjini voženj
in vsi vlaki ga nimajo in v indeksu nimajo kaj iskati.

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
vlaki + LPP dali ~1,5 GB na leto, z vsemi prevozniki pa 8,7 GB.

Primerjamo z zadnjo **zapisano** vrednostjo, ne s prejšnjo prebrano, da se
počasno lezenje sešteva in ne izgine. `run` ostane točen -- prag velja samo
za dnevnik.

**Dnevnik se obrezuje, `run` nikoli.** Tudi s pragom nastane z vsemi
prevozniki ~300 000 vrstic `obs` na dan; železnica jih naredi 4 000, torej 1 %.
Ena vrstica stane 79 B (41 B tabela + 38 B ključ, merjeno z `dbstat`) — torej
24 MB na dan in 8,7 GB na leto brez obrezovanja. Zato dve meji (`collector.prune_obs`, dnevno ob osvežitvi
vremena, ali `sztrack prune`): železnica 90 dni, avtobusi 14. Železnica je
jedro in njen dnevnik je poceni; pri avtobusih za prikaz zadošča `run`.
`run` je zgodovina, iz katere živijo statistika, "običajna zamuda" in
backtest -- te se ne briše.

Kar to pomeni za disk, izmerjeno (`dbstat`, 69 B na vrstico): `run` dobi
največ toliko vrstic, kolikor je na dan prevoženih postankov -- železnica
7 832, avtobusi 134 859. Na leto je to 0,2 GB proti 3,4 GB.

**Dolgoročno raste `run`, ne `obs`.** Dnevnik se z obrezovanjem ustali pri
~356 MB (železnica 90 dni = 28 MB, avtobusi 14 dni = 327 MB) in naprej ne
raste. `run` pa raste za vedno in ga po enem letu prekaša za desetkrat.
**Lega vozil ne stane nič**: `vehicle_now` je upsert na vožnjo in starejše od
ure se brišejo -- sled se ne hrani. Zavestna izbira, ne
spregled: `run` je edino, iz česar se da kasneje karkoli izračunati, in
brisati ga pomeni brisati projekt. Če bo kdaj treba, je najprej na vrsti
avtobusni `run`, ne železniški.

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

## Hitrost pri velikih podatkih

Izmerjeno na **sintetični bazi z letom zajema vseh prevoznikov**: 52 122 000
vrstic `run`, 365 dni, 5,9 GB (generator je v scratchpadu, ne v repozitoriju).
To je stanje, do katerega bo baza prišla sama; pri devetih dneh je vse hitro
in ne pove nič.

| pot | čas |
|---|---|
| vstopna stran (`/api/overview`) | 29 ms |
| zemljevid, obe omrežji (`/api/live`) | 460 ms |
| živi seznam, samo železnica | 20 ms |
| odhodna tabla | 93 ms |
| prestopi | 46 ms |
| načrt poti do treh prestopov | 2 ms |
| iskanje postaj (avtobusi) | 145 ms |
| statistika, razrez 90 dni | 0,1 ms (dnevni povzetek) |

Trije vzorci, ki so bili vsak po enkrat vzrok počasnosti in se v novi kodi
ne smejo ponoviti:

1. **Filtriraj znotraj poizvedbe, ne za njo.** Okenska funkcija čez oba
   omrežja, filter `t.network` šele za njo: železniško vprašanje (700 000
   vrstic) plača avtobusne (12 M). Bilo je dvakrat — v `_LIVE_SQL` in v
   `stats.breakdowns` (38 s).
2. **Koreliran `EXISTS` teče enkrat na vrstico.** Ista pogoja kot
   nekorelirana podpoizvedba: 392 ms → 65 ms.
3. **Preveri `EXPLAIN QUERY PLAN`, preden verjameš, da je indeks.**
   `SCAN t USING INDEX trip_train_no` **ni** iskanje po indeksu, ampak
   pregled cele tabele po napačnem — manjkal je `trip(route_id)`.

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
* **Agregat čez vso zgodovino se ne računa v zahtevi.** Razrezi statistike
  gredo skozi `stats.summary_get()` in se izračunajo enkrat na dan (ob 3:30,
  `SZ_MAINT_HOUR`). Pri letu zajema je razlika 17 s proti 0,3 ms. Vsaka taka
  številka mora na strani nositi **čas izračuna** — predpomnjena vrednost
  brez datuma je laž, ki čaka na priložnost.
* **Omrežje filtriraj znotraj poizvedbe, ne za njo.** `WHERE t.network = ?`
  za okenskim izračunom pomeni, da železniško vprašanje (700 000 vrstic)
  plača avtobusne (12 M). Isti vzorec je bil že dvakrat vzrok počasnosti.
* **V enem SQL stavku ne mešaj `?` in `:ime`.** sqlite veže po vrstnem redu
  pojavitve in tiho vrne napačne vrstice, brez izjeme. Cel stavek naj bo enega
  sloga.
* `run` hrani **zadnje stanje** postanka, zato je `MAX(stop_seq)` po koncu
  vožnje terminus — ne dokaz, da vlak še vozi. Živost sklepaj iz voznoredne
  ure in prevoženih postankov (`_LIVE_SQL`).
* **Spremembo prikaza poglej, preden jo razglasiš za končano.** Posnetek:
  `chromium --headless --disable-gpu --window-size=1850,1000
  --virtual-time-budget=7000 --screenshot=$PWD/posnetki/x.png <url>`.
  V `/tmp` chromium ne more pisati (tudi ne v scratchpad, ki je pod njim),
  zato v `posnetki/` v projektu — ta je v `.gitignore`. **Ne v `$HOME`**:
  tam je uporabnikova mapa in tja se ne odlaga smeti.

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
* Avtobusi: `vehicle_positions` nosi ~20 vozil z GPS (LPP in medkrajevni),
  vlakov pa ne. Isti GTFS zip že vsebuje avtobusni del, ki ga uvoz namenoma
  izpusti (`RAIL_ROUTE_TYPE`).

Daljši zapisi: [HANDOVER.md](HANDOVER.md) (stanje projekta),
[docs/APLIKACIJA.md](docs/APLIKACIJA.md) (dogovorjeno o prikazu),
[design/README.md](design/README.md) (smeri in barve).
