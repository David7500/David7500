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
* **Prevoznikova napoved šteje samo navzgor.** Njegova vrednost za še
  nedosežen postanek je v povprečju smet (MAE 8,26 min), a napaka je
  **enosmerna**. Merjeno na 12 026 primerih z znano prevoznikovo vrednostjo:

  | | delež | prevoznik | naš model |
  |---|---|---|---|
  | napove **več** kot mi | 10 % | **0,21 min** | 2,66 min |
  | napove manj ali enako | 90 % | 9,17 min | **1,22 min** |

  Nizka vrednost je namreč privzeta ničla za postanek, ki ga feed še ni
  razrešil; visoka pa pomeni, da prevoznik **ve** za nekaj, česar iz zgodovine
  ni mogoče vedeti — okvaro, zaporo, križanje. Zato `stats._with_operator()`:
  `max(naša ocena, njegova)`, nikoli navzdol.

  **Ena izjema, in ta je izmerjena** (`stats._operator_is_stale`): dokler vlak
  **stoji na postaji z dolgim postankom**, njegova vrednost za naprej ni
  napoved, ampak prenos zamude, s katero je prišel — koliko postanka bo
  skrajšal, se še ne ve. Ujeto v živo 29. 8.: RG 1604 je stal v Ljubljani
  (postanek 21 min, prišel +19), ob 23:04 je prevoznik za Zalog objavil +19 in
  ob 23:12, ko je vlak odpeljal, to popravil na +5. Vlak je prišel +5.

  Podpis: prevoznikova vrednost je **natanko** zamuda ob prihodu na postajo,
  kjer vlak stoji (±1 min), postanek tam je ≥ 5 min, vrednost pa je večja od
  tega, kar že vemo. Pojavi se v 926 od 63 967 primerov in tam je `max`
  **slabši** — MAE 4,19 proti 3,31 min, delež v petih minutah 71,2 proti
  81,4 %. Z izjemo skupno 1,189 → 1,177 min in 94,27 → 94,42 %. Na teh nalogah MAE 1,36 → 1,12
  min, delež v petih minutah 93,7 → 94,8 %, in boljše je v **vseh** razredih
  zamude. Velja v `predict`, na odhodni tabli in v iskalniku zvez.
  Merljivo: `sztrack backtest --operator`.

  **Merilo samo je bilo prekratko.** `backtest.operator_forecast_tasks()` vzame
  eno nalogo na par postankov — kaj je feed trdil o cilju v trenutku, ko je bilo
  izhodišče zadnjič potrjeno. Prav zaradi te konstrukcije zgornjega podpisa
  **sploh ne vsebuje** (0 primerov od 12 154): prevoznikova prenesena vrednost
  se pojavi šele **po** zadnji spremembi na izhodišču. Pošteno merilo je vsak
  poll posebej — 63 967 nalog namesto 12 154 — in šele tam se vidi tudi slaba
  stran pravila. Kdor pravilo spreminja, naj meri tako.

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

* **Iz `obs` se ne da ugotoviti, kdaj je bila vrednost nazadnje POTRJENA.**
  Dnevnik piše samo ob spremembi (`OBS_MIN_DELTA_S`), zato je zadnji zapis
  zadnja *sprememba*, ne zadnja potrditev — feed isto vrednost pošilja naprej
  vsakih 30 s, mi je ne zapišemo. Posledica: za nazaj **ni mogoče ločiti
  meritve od napovedi, ki se ni nikoli popravila.** Živi prikaz to reši z
  `stats.last_measured()` (vozni red + zamuda ≤ zdaj), zgodovina pa ne more.

  Kako se to pokaže: RG 1604 ima v `run` na Ljubljani Zalogu 15, 2, 7, 14, 13,
  11, 16 min — na **štirih od osmih dni natanko toliko, kolikor je bila zamuda
  ob prihodu v Ljubljano**, torej feedova napoved izpred postaje. Na Litiji,
  devetnajst minut pozneje, so vrednosti 0, 2, 6, 0, 1, 1, 2 in se ujemajo z
  Zagorjem za njo. Biti +13 na Zalogu in +1 v Litiji je fizično nemogoče, a iz
  zapisa samega se ne vidi, katera od obeh je napoved.

  **Preizkušeno in ne pomaga:** vsiliti modelovo fiziko zaporedju napovedi
  (v točki j ne moreš biti bolj pozen, kot boš v j+1, plus rezerva vmes).
  MAE 1,92 → 1,96 min, delež v petih minutah 91,0 → 90,8 %. Rezerva je tudi v
  voznem času, ne le v postankih, zato pravilo prereže preveč pravih okrevanj.

* **Ne verjemi ničli, ki jo feed vrne za en klic.** Pri 14 % postankov z več
  kot dvema zapisoma se pojavi vzorec X, 0, X v razmiku ene minute. Zamuda med
  dvema klicema ne more pasti za več, kot je vmes minilo časa. `run` zato ničlo
  po zamudi ≥ 5 min sprejme šele, ko jo potrdi drugi zaporedni poll
  (`collector.is_zero_blip`); dnevnik `obs` obdrži vse. Isto varovalo velja pri
  določanju lege vlaka -- sicer (vozni red + 0) pomeni, da je postanek že minil,
  in vlak na zemljevidu skoči naprej.
* **Odhodni zamudi na dolgem postanku ne verjemi.** Feed jo objavi kot ničlo,
  še preden vlak pride, in je pogosto ne popravi. Ujeto v živo 29. 8.: RG 1604
  je imel v Ljubljani zapisan prihod +19 in **odhod 0** — torej dve minuti
  stanja — na Ljubljani Zalogu osem minut pozneje pa **+5**, torej sedem minut
  stanja. Oboje hkrati ne drži, in tokrat prvič vemo, katera stran je napačna:
  Zalog in Litija (+3) sta skladna med sabo, odhodna ničla ni skladna z nikomer.

  Isti vzorec je na tej postaji **pet dni od devetih**. `stats.typical_dwell()`
  zato dan sploh šteje le, kadar sta naslednja dva postanka skladna med sabo
  (razlika pod 2 min), postanek pa izračuna iz **naslednjega** postanka, ne iz
  odhodne vrednosti. RG 1604 v Ljubljani: štirje uporabni dnevi od devetih,
  postanki 7, 9, 11 in 17 min proti 21 po voznem redu.

* **Zamuda ni ena številka na postanek: prihodna in odhodna sta lahko različni.**
  Vlak ne odide takrat, ko pride. LP 4219 ima na Mostu na Soči v voznem redu
  **devet minut postanka** (20:38 → 20:47, križanje na enotirni bohinjski
  progi): 29. 8. je pripeljal +10 in odpeljal +3 — stal je dve minuti namesto
  devetih. Feed je oboje tudi povedal (`prihod 600 / odhod 180`).

  Redko, a ne zanemarljivo: 406 postankov v voznem redu ima nad dve minuti
  zadrževanja, in v devetih dneh se prihodna in odhodna zamuda razlikujeta pri
  1 307 postankih, od tega 362 za pet minut ali več.

  Prikaz kaže `COALESCE(delay_dep, delay_arr)`, torej **odhodno**. To je prav —
  potnika zanima, kdaj gre vlak naprej — a ena številka na vrstico naredi v
  grafu prepad, ki je videti nemogoč („kako je zamuda padla za osem minut med
  dvema postajama"). Zato: kadar se številki razlikujeta za minuto ali več,
  vrstica pokaže **obe** (`+10 → +3`) z razlago postanka, krivulja pa gre v
  naslednjo postajo na **prihodno** vrednost in pade **navpično** na postaji.
  Padec se je zgodil tam, ne na odseku.

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

  **Ritem je izmerjen, ne domnevan** (86 vozil, 492 prehodov med legami):
  vozilo objavi novo lego vsakih **20 s** (404 od 492 razmikov je natanko 20 s),
  in ko se ta v feedu prvič pojavi, je že **20 s stara** (p90 30 s, najstarejša
  104 s). Glava feeda je sveža -- naš prenos je od nje oddaljen 0,5--3 s --
  torej zaostanek ni na naši strani, ampak med vozilom in virom.

  **Spodnja meja je feed in je ni mogoče obiti.** Merjeno na glavi feeda samega
  je mediana starosti lege 21 s ob 19:44 in **33 s ob 21:03** (59 vozil namesto
  86) -- z uro se slabša, ker vozila proti koncu obratovanja poročajo redkeje.
  Hitreje od tega ne more nihče, tudi brskalnik ne, če bi bral naravnost.

  **Naravnost tudi ne more.** Feed nima nobene `Access-Control-Allow-Origin`
  glave, zato CORS branje iz JS blokira; edina pot je posrednik, in ta smo mi.
  Tudi če bi šlo, bi to pomenilo protobuf knjižnico v brskalniku (odvisnost) in
  vsak obiskovalec bi tolkel po tuji javni storitvi namesto po naši.

  Kar je torej naše, je **vzorčenje**, in to je bilo prej večje od potrebnega:
  zajem na 30 s je prispeval mediano 15 s, brskalnik na 20 s še 10 s. Zdaj
  `config.POSITION_SECONDS = 10` (pol vozilovega ritma; pod tem ni česa dobiti)
  in brskalnik vpraša **v koraku s strežbo** -- odgovor nosi glavo
  `X-Osvezi-Cez` s sekundami do naslednjega branja, `common.pollVehicles()` pa
  se po njej ravna, z zamikom 0--2 s (sto brskalnikov ne sme udariti hkrati) in
  brez spraševanja, dokler je stran skrita. Izmerjeno: naš prispevek k starosti
  **15 s → 5 s**.

  **Zdaj ne dodamo praktično ničesar, in to je izmerjeno po vozilih.** V istem
  trenutku prebrana feed in naš `/api/vehicles`, 409 primerjanih vozil: lega je
  ob našem branju **že 28,8 s stara** (p90 42,1), mi pokažemo 32,0 s (p90 47,0),
  razlika pa je **mediana −0,1 s** in p90 19,3 s. Polovico časa je torej naša
  vrednost natanko tako sveža kot feedova — ker vozilo objavlja na 20 s in ima
  ista žiga; p90 je večji od 10-sekundnega cikla zato, ker vozilo med našim
  branjem in primerjavo objavi nov, do 20 s novejši žig.

  **Naš zaostanek za feedom ni „nekaj sekund", ampak dvovrednosten.** Merjeno
  na 490 primerjavah: v **66 %** imamo natanko isti žig kot feed (razlika −1 s),
  v **25 %** pa smo eno vozilovo objavo zadaj (19--20 s). Vmesnih vrednosti
  skoraj ni. Razlog je aritmetičen in se ujema do odstotka: vozilo objavlja na
  20 s, mi beremo na 10 s, torej je verjetnost, da je nova lega prispela po
  našem zadnjem branju, ≈ 5/20 = 25 % (opaženo 122 od 490). Mediana 0 s,
  povprečje 5,5 s, p90 19 s, največ 41 s.

  **Pogojni GET pri legah ne pomaga.** Feed se spreminja **vsaki 2 s** (39 od
  40 zahtev je vrnilo 200, en sam 304) — različna vozila poročajo v različnih
  fazah, zato datoteka skoraj nikoli ni ista. Pri voznem redu in obvestilih
  ETag prihrani prenos, tu ne.

  Iz tega sledi, kaj bi gostejše branje res dalo: pri 5 s bi bila verjetnost
  zaostanka ≈ 12,5 % in povprečje ~2,5 s namesto 5,5. Torej **3 sekunde od 32**,
  za dvakratno breme tuje javne storitve (63 → 127 MB/dan). Zato ostane 10 s;
  kdor hoče preizkusiti, ima `SZ_POSITION_SECONDS` in ne rabi spreminjati kode.
  Številka, ki jo potnik vidi, ni naš zaostanek — je starost meritve GPS v
  vozilu. Zato ima žeton naslov, ki to pove.
* **Okno vožnje je lego naložilo enkrat in nikoli več.** Kdor je stran pustil
  odprto, je gledal, kje je bil avtobus ob odprtju -- in prav tam je vprašanje
  „kje je zdaj" najbolj neposredno. Zdaj se osvežuje z istim
  `pollVehicles()` kot zemljevid. Pogled se **premakne le, kadar vozilo uide
  iz okvira**: brezpogojni `setView` bi zemljevid vsakih deset sekund trgal
  izpod prsta človeku, ki si ogleduje kaj drugega.

* **`/api/vehicles` je predpomnjen na cikel zajema.** Odgovor se med dvema
  branjema leg ne spremeni, zato se izračuna enkrat in vsem strežejo iste
  vrstice; ključ je `positions_fetched`, ne ura, da se razveljavi natanko ob
  novem podatku. Izjema je `age_s`, ki se računa ob vsaki strežbi -- starost
  lege je edino, kar se med cikloma res spreminja, in predpomnjena bi lagala.
  To je edini del prikaza, kjer je število uporabnikov sploh vidno: brez tega
  bi sto obiskovalcev pomenilo sto enakih poizvedb desetkrat na minuto.

* **`vehicle_now` pozna samo lego, zamude v njej ni.** `/api/vehicles` je
  vračal `v.*` in prikaz je bral `v.delay_s`, ki ni obstajal -- kartica na
  zemljevidu je zato pri vsakem avtobusu pisala „? min", njegova stran pa
  +15. Dve številki o istem vozilu, ena izmišljena. Zamudo doda
  `stats.last_measured()` -- **isto pravilo kot živi seznam in okno vožnje**,
  ne nova poizvedba: sicer se razideta spet. Preverjeno na 67 vozilih z
  meritvijo, vsa se ujemajo z vrstico v `run`. Poceni je, ker gre za ~80
  voženj z GPS in ne za vse omrežje (20 ms).

* **Zamude ne prenašaj naprej čez dolg postanek — tabla je zato lagala.**
  RG 1604 stoji v Ljubljani 21 minut (22:44 → 23:05): pride +15 in odpelje
  **po voznem redu**. Odhodna tabla je zamudo prenesla naravnost in pisala
  23:20 — potnik bi prišel na že prazen peron. Napaka v najslabšo smer, ker
  vlaka ne zamudiš, če prideš prezgodaj.

  `journey.board()` in `stats.connections()` zato med zadnjo meritvijo in
  potnikovo postajo odštejeta **rezervo voznega reda** (`stats._slack_ahead()`
  + `_after_slack()`), enako kot `stats.predict()`. Pri **prihodni** tabli se
  postanek na tej postaji ne šteje — vozilo šele pride, postanek je za tem.

  Poceni je: `_slack_ahead()` bere samo postanke nad `MIN_DWELL_S`, teh je na
  vsej železnici 406 od 10 019.

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

* **Ko feed izgubi vozilo, začne objavljati uro namesto zamude.** Za postanke,
  ki jih je vozilo *že prevozilo*, zna objaviti vrednost, ki raste natanko za
  minuto na minuto. Ujeto v živo 30. 8., LPP 25 (vožnja 452632, Poliklinika):
  ob 12:19:36 prihod +58 s in odhod +126 s — prava meritev z **različnima**
  vrednostma — nato ob 12:23:48 skok na +482 in sedem klicev zapored rast
  natanko +60 s na +60 s do **+842 (+14 min)**, ob 12:30:29 pa vrnitev na
  +58/+126. Vozilo je bilo ves ta čas že davno mimo.

  V zajetem je takih zaporedij **11 827 pri 947 vožnjah**. To pojasni tudi
  doslej odprto vprašanje o **enotni zamudi čez vso vožnjo**: Nomagov N6571 s
  27 060 s na vseh postankih je natanko ta vzorec, ujet po tem, ko se je
  ustavil (4 od 12 takih voženj imajo zaporedje v `obs`; pri ostalih smo se
  priključili šele po tem, ko je vrednost že zmrznila).

  Varovalka je `collector.undoes_passing`: zavrne vrednost, ki bi postanek,
  za katerega smo **že zapisali meritev** o prevozu pred več kot 120 s,
  prestavila nazaj v prihodnost. Dnevnik `obs` obdrži vse; čaka samo `run`.

  **Prva različica pravila je bila preširoka in to je bilo merljivo.**
  Brez dodatnega pogoja je vzela pravo dvourno zamudo nočnega vlaka: EN 1276
  je 28. 8. ob 00:03 imel za Celje zapisano `0/0` — feedovo napoved pred
  prihodom, ne meritev — in ob 01:57 pravih +114 min. Zato **za dokaz o
  prevozu šteje samo zapis z različnima vrednostma za prihod in odhod**: te
  feed za nerazrešen postanek ne objavi. Ista past je v projektu zapisana že
  dvakrat („ne verjemi ničli, ki jo feed vrne za en klic").

  Učinek `sztrack repair` na 10 dneh zajema: **852 vrstic** v `run`, od tega
  277 avtobusnih (mediana 51 min, največ 11 h) in **300 železniških**
  (mediana 14 min, največ 80 min). Povprečna zamuda pade pri avtobusih z 9,8
  na 8,8 min, pri železnici s 6,7 na 6,5. Železniški primeri so isti vzorec:
  LPV 2252 je bil 22. 8. ob 08:23 v Zagorju izmerjen s prihodom +2 in
  odhodom +1, uro in četrt pozneje pa je feed zanj objavil +79 min.

  **`repair` popravlja samo postanke, na katerih je varovalka sprožila.**
  Prej je čez `run` prepisal ves ponovljeni dnevnik — in ker `obs` beleži le
  spremembe nad `OBS_MIN_DELTA_S`, je s tem 16 696 vrstic zamenjal za do
  minuto grobejše, da bi popravil 4 217 pokvarjenih. Popravilo mora
  popravljati, ne glajenja.

* **Feed objavlja zamudo za vožnjo, ki se še ni začela — in to je zamuda
  PREJŠNJE vožnje istega vozila.** LPP 25 (452632) 30. 8.: postanek Medvode
  novo naselje ima vozni red 11:41, feed pa je zanj že od 11:11 objavljal
  +8, +10, +11, +12, +13 in ob 11:33:55 **+14 min** — vsakič čas, ki je bil
  takrat še v prihodnosti, torej napoved. Ob 11:35:44 je vrednost popravil
  na 0 in avtobus je odpeljal skoraj točno.

  `run` je vseeno obtičal na +14, ker je popravek zavrnil `is_zero_blip`:
  ta čaka na potrditev druge ničle, feed pa je ničlo povedal **enkrat
  samkrat** in drseče okno je šlo naprej. V grafu je bilo to videti kot
  devet postaj pri +14 in nato **padec za petnajst minut v enem koraku** —
  tam se je končala napoved in začela meritev.

  Zato `collector.is_forecast`: vrednost, ki ob svojem nastanku postanek
  postavlja v prihodnost, **ni meritev**, in ničla, ki jo popravlja, ni blip.
  Merilo je brez prostih parametrov.

* **Zgodovina poti mora biti zamejena na `trip_id`.** `stats.history()` je
  filtrirala po `train_no` in gradila profil po `stop_seq` — po **zaporedni
  številki** postanka. Pri LPP liniji 25 (217 voženj) se je pod „postanek 2"
  sešlo *Medvode novo naselje* (drugi postanek proti Zadobrovi, povprečje
  +7 min) in *Novo Polje* (drugi postanek v **nasprotni smeri**, +1 min) —
  dva različna kraja pod eno oznako, in stolpec je pisal „1 vožnja" nad 850
  meritvami iz 25 voženj. Isto velja za devet vlakov s sezonskimi različicami.

  Pri železnici je to brez posledic: **0 od 663 številk z meritvami ima več
  kot eno vožnjo**. Pri avtobusih jih ima 205 od 242, največ 42.

  Ista funkcija je edina v projektu brala `delay_arr` pred `delay_dep` —
  natanko obratno od pravila, ki velja povsod drugod. Popravljeno.

* **Na izhodišču prihoda ni.** Feed ga za `stop_seq = 1` vseeno pošlje in je
  smet: LPP 25 je 30. 8. na Medvodah naselju poročal prihod −267 s ob odhodu
  −2 s, na drugi vožnji istega dne −1771 s. Prikaz je iz tega sestavil
  „vlak je stal 4 min namesto 0 — izgubil 4 min", torej zgodbo o dogodku, ki
  se ni zgodil. `common.dwellSplit()` zdaj prvi postanek preskoči.

* **Avtobus je lahko PREZGODEN; vlak v zajetih podatkih nikoli.** V 45 146
  železniških vrsticah `run` ni niti ene negativne vrednosti — najmanjša je
  natanko 0. Pri avtobusih je 12,0 % vrstic vsaj minuto prezgodnjih in 4,5 %
  vsaj tri; **41,7 % avtobusnih voženj ima vsaj en prezgodnji postanek**
  (LPP 22,6 % vrstic, Nomago 10,6 %, Arriva 8,9 %).

  Prikaz je to do zdaj **skrival**: vrstica je pričakovano uro izpisala samo
  ob `delay_s >= 60`, torej je prezgoden avtobus kazal zgolj voznoredno uro.
  Napaka v najslabšo smer — potnik pride ob objavljeni uri in avtobusa ni več.
  Zdaj je prag `abs(delay_s) >= 60`, žeton pa pove „3 min prej", ne „−3 min":
  minus pred številko je uganka, beseda ni. Barva ostane siva, ker to res ni
  zamuda — in prav zato mora povedati beseda. Pravilo je v `common.delayText()`
  in velja **povsod**: kartica zemljevida, iskalnik vozila, stolpec zamude v
  časovnici in postanek potnika. Za ozke stolpce ima kratko obliko („5 prej").

  **V glavi okna vožnje smer nosi naslov, ne enota.** „Trenutna zamuda" nad
  „6 min prej" si nasprotuje, „Vozi prezgodaj" nad „6 min prej" pa besedo
  ponovi. Zato naslov pove smer in številka velikost: **„Vozi prezgodaj" ·
  „6 min"**.

  Ali je prezgodnja vrednost resnična, je bilo preverjeno na LPP 25
  (Medvode ↔ Zadobrova). V smeri proti Zadobrovi je bila na Gosposvetski
  prezgodnja v **vseh 17 zajetih vožnjah**, povprečno −4,4 min, najpozneje
  −5 s; profil čez progo je lok, ki na obeh koncih izgine (Prušnikova −74 s,
  Kompas −224, Gosposvetska −265, Kolodvor −73, konec +123). GPS to potrdi:
  30. 8. ob 12:10:44 je bilo vozilo LJ LPP-124 že za postankom, ki ima vozni
  red 12:13. To torej ni napaka zajema, ampak **prevelika rezerva voznega reda
  skozi Šiško** — v nasprotni smeri je ista postaja povprečno +370 s. Zajem
  LPP je za zdaj samo vikendski (od 29. 8.); ali velja med tednom, se bo videlo.

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

  **To velja tudi za iskanje, ne le za izpis.** Iskalnik vozila na zemljevidu
  je poznal samo `train_no` in smer, zato „lpp 25" ni našlo ničesar -- človek
  pa piše prav to, ker je tako videl na postajališču. Išče se po celem imenu,
  kot ga vidi na zaslonu (`AGENCY[agency] + train_no + headsign`), več besed
  pomeni presek in ne unijo, zadetek na začetku številke pa gre naprej -- sicer
  „25" postavi A2505 pred linijo 25. Prevoznik je v `trip.agency` **kot
  GTFS ID** (1118, 1123 …); ime je samo v `common.AGENCY` in `stats.AGENCY_NAMES`.
* **Mestno postajališče ima svoj `stop_id` za vsako smer.** "Bavarski dvor"
  je v `station` dvakrat. Vse v aplikaciji teče po imenu postaje, zato iskanje
  po imenu združuje.
* **Zemljevid je edini skupni pogled.** Vlak je krog na zadnji postaji z
  meritvijo, avtobus **oblika vozila** na izmerjeni legi, ki raste s
  približkom (15–34 px) in kaže v smer vožnje. Puščica je bila premalo: pri
  velikem približku je bila videti kot pika in se od vlaka ni ločila.

  **Ime postaje se pokaže na dotik in po petih sekundah odide.** Pike so bile
  `interactive: false`, torej nema točka na zemljevidu -- iz nje se ni dalo
  izvedeti, katera postaja to je. Trajne oznake pa na mestni liniji zakrijejo
  progo pod sabo. Zato `common.bindFlashName()`: klik odpre oblaček,
  `setTimeout` ga zapre. Brez gumba za zapiranje -- ta bi bil na telefonu
  manjši od prsta in bi zahteval natančnejši dotik od tistega, ki je ime
  odprl. Klik ustavi razširjanje dogodka, sicer na telefonu zapre spodnjo
  ploščo. Velja na velikem zemljevidu, na trasi izbranega vozila in v oknu
  vožnje. Polmer pike je zato 3,4 namesto 2,4 px: 2,4 je manj od prsta.

  **Avtobusna postajališča so svoja plast in privzeto ugasnjena.** Vseh je
  9 519 (211 kB z gzipom, 167 ms), zato se naložijo šele ob prvem vklopu --
  enako kot trase. Rišejo se **od z13 naprej**, in ta meja je izmerjena na
  ljubljanskem oknu 1200 × 800: pri z13 jih je v njem 253, pri z12 600, pri
  z11 pa 1 694 in mreža prog izgine pod njimi. Pod pragom plast ne riše nič
  in pove, zakaj. Železniške postaje ostanejo svoja, privzeto vklopljena
  plast -- teh je 271 in progo prav opisujejo.

  Vsaka plast se da izklopiti posebej (vlaki, avtobusi, železniške proge,
  **trase vozil na poti**, železniške postaje, avtobusna postajališča,
  podlaga, dodatna imena), ne le avtobusi.
  Trase so privzeto ugasnjene in se naložijo šele ob vklopu: gost snop črt čez
  vso Ljubljano odgovarja na „kod vozijo linije", ne na „kje je moj avtobus",
  in drugo je razlog za obisk te strani. 128 različnih oblik, 108 kB z gzipom.

  **Trase so lahko pretrgane in ravna črta čez pol Slovenije je laž.** V
  zajetem GTFS je 2 185 razmikov od 4,85 milijona (0,045 %) daljših od
  kilometra, pri 193 oblikah; najdaljši je 40 km. Uvoz zato traso razreže na
  kose (`gtfs.SHAPE_BREAK_M`) in vsakega nariše posebej — 2 897 oblik da
  4 732 kosov. Meja je izmerjena, ne izbrana: surove točke so 17 m narazen
  (mediana), 105 m pri 99 % in 514 m pri 99,9 %, nato pa skočijo na 22,8 km.
  Med pol kilometra in dvajsetimi ni ničesar. Na **poenostavljenih** točkah
  tega praga ni mogoče postaviti — tam je dolg raven odsek videti enako kot
  preskok. Namesto lestvice „največje zamude"
  je **iskalnik vozila**: vprašanje pred zemljevidom je „kje je moj avtobus",
  ne „kdo danes najbolj zamuja".

  Podlaga je Esri „Dark Gray Canvas". **Imena ulic so vanjo vpečena in jih ni
  mogoče ugasniti posebej** — preverjeno je, da brezplačne podlage brez
  napisov ni: CARTO `*_nolabels` pride z vodnim žigom „API KEY REQUIRED",
  `tiles.wmflabs.org` je ugasnjen, Wikimedia zunanjo rabo zavrača s 403. Zato
  dvoje, kar res dela: „pomirjena podlaga" jih zatemni
  (`brightness(0.42) contrast(0.7)`), izklop podlage jih odstrani s cestami
  vred. Proga je narisana dvakrat — temna obroba, svetla črta — sicer se na
  temni podlagi izgubi ali je videti kot cesta.

  **Esri ima prave ploščice samo do z16.** Nad tem vrne 200 in sličico, ki je
  za vsak kraj **bajt za bajt ista** (2521 B proti 15 647 B pri z16) — prazno
  polje. Zato ne `maxZoom: 16` (približevanje se ustavi prezgodaj in ulice se
  ne razločijo) in ne `maxZoom: 19` (nad 16 sivina), ampak
  **`maxNativeZoom: 16, maxZoom: 19`**: Leaflet zadnjo pravo ploščico raztegne.
  Podlaga je pri z17--19 mehka, naši sloji pa ostanejo ostri, ker so SVG —
  in prav ti so razlog za približevanje. Vozili pri z17+ zrasteta (bus 44 px,
  vlak 38 px), da ostaneta v razmerju z ulico pod sabo.
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
| `/` | domača stran: s čim greš — vlak ali avtobus |
| `/app/train` | vlaki: iskalnik povezav in odhodna tabla |
| `/app/bus` | avtobusi (LPP …): ista stran, drugo omrežje |
| `/app/map` | živi zemljevid — **edini skupni pogled** obeh omrežij |
| `/app/train/{no}` | okno ene **vlakovne** vožnje |
| `/app/bus/{no}` | okno ene **avtobusne** vožnje |
| `/app/ovire` | dela na progi in nadomestni prevozi, s filtrom po besedilu |
| `/app/statistika` | razrezi zajetega: po vrsti vlaka, uri, dnevu v tednu |

**Hitrosti po odsekih ni več nikjer.** Bila je isti podatek v drugi enoti,
zložen v zaprt `<details>` na dnu okna vožnje. `/api/speeds` in
`stats.segment_speeds()` ostaneta — rabi ju izvoz in mreža razdalj.

**Iskalnik si zapomni vse poti, ne zadnje.** Dva seznama, ker sta dve
vprašanji: `sztrack:fav` je „to je moja pot" in ga človek pove sam (zvezdica),
`sztrack:recent` je „tu sem pravkar bil" in se napiše sam (šest zadnjih).
Oba sta v žetonih **pod iskalnikom**, ne v pregledu — pregled prva poizvedba
pobriše prav takrat, ko bi seznam rabil za naslednjo. Prazno polje za postajo
ob dotiku ponudi imena iz teh poizvedb; drugega ugiba za prazno polje nimamo.

Oba seznama sta **ločena po omrežju**. Prejšnji `sztrack:last` ni bil, in to
je bilo videti: kdor je na `/app` iskal Celje–Ljubljana in nato odprl
`/app/bus`, je tam dobil isto vprašanje, razrešeno na avtobusnem omrežju
(„Ljubljana AP"), in prazen odgovor. Zadnja poizvedba je zdaj preprosto prva
med nedavnimi in svojega zapisa nima več.

Okno vožnje je isto za vlak in avtobus, a govori o tem, kar je pred potnikom:
besedo (vlak / nadomestni prevoz / avtobus), opozorilo in povezavo nazaj
izbere iz `network`. Pri avtobusu z več vožnjami na isto številko linije je
v naslovu `?trip=<id>`.

**Vstopna stran preklopa preprosto/napredno nima namenoma.** Izbira med dvema
odgovoroma je pri vprašanju „kdaj mi pelje vlak" sama po sebi breme: potnik ne
vidi, kaj mu drugi pogled skriva, in dokler ne vidi, ga ni razloga vklopiti.
Kar je bilo na njej naprednega, se je razdelilo na dvoje in nič ni ostalo
skrito: razumljivo vsakomur (**neposredno**, **načrtovano N min za prestop**,
**točnih N %**, **najslabša**, koliko je zajetega) je zdaj vedno vidno, ostalo
pa je s te strani odšlo, ker tja ni sodilo — številka postanka, „izhodišče —
feed odhodne zamude ne poroča" in prevoznikova napoved, ki je prikaz tako ali
tako ne uporablja. Preklop obdržijo okno vožnje, statistika in ovire: tam gre
za eno vožnjo ali eno številko, ne več za izbiro poti.

Druge strani imajo preklop **preprosto / napredno**. To ni druga stran: napredni
pogled je razred `is-advanced` na `<body>`, ki odkrije elemente z razredom
`adv-only` (p90, delež točnih, številka postanka, kaj pravi feed). Potnik in
radovednež gledata isto vožnjo.

**Pot mora povedati, s čim greš.** `/app` je bil vlakovni samo po dogovoru in
iz naslova to ni bilo vidno; zdaj je `/app/train` in `/app` nanj preusmerja
(308). Okno vožnje ima obe poti: `/app/train/{no}` in `/app/bus/{no}`.
Streženo je z isto predlogo, a naslov ne sme lagati — `/app/train/25` za
mestno linijo 25 je napačen naslov, ki ga bo nekdo delil naprej, zato ga
strežnik pogleda v `trip.network` in preusmeri (307).

**Ovire so samo pri vlakih.** `SZ-OVIRA` obvestila so dela na progi, zapore
tira in nadomestni prevozi SŽ; za avtobuse takih obvestil ni in povezava tja
bi obljubljala podatek, ki zanje ne obstaja.

**Omrežji sta ločeni tudi na pogled.** V glavi je segmentni preklop
`Vlaki | Avtobusi`, ne dve povezavi med štirimi, in avtobusna stran ima svojo
barvo (`body.net-avtobus` prestavi `--accent` na zeleno, isto kot vozila na
zemljevidu). Doslej je bila trenutna stran samo izpuščena iz seznama povezav
in razlika ni bila vidna nikjer — kdor je na `/app/bus` iskal „Ljubljana",
je dobil postajališče LPP in ni razumel, zakaj.

**Iskanje na vstopni strani sproži samo gumb.** Izbira postaje iz predlogov
ne išče: človek pogosto popravi še drugo polje ali dan, vsak vmesni ugib pa je
zahteva za odgovor, ki ga nihče ni prosil. Izjema je poizvedba iz naslova
(deljena povezava) — tam je odgovor prav to, po kar je človek prišel.

**Med dvema meritvama pika drsi naprej po trasi — samo v oknu vožnje.**
Lega je ob strežbi ~30 s stara (izmerjeno), kar je pri 50 km/h **več kot pol
kilometra**. Ocena je zato `hitrost × starost` vzdolž trase linije, osvežena
vsako sekundo.

Izmerjeno na 79 primerih (šestminutni zajem sledi iz feeda, razmik 15–60 s),
napaka proti dejanski naslednji legi:

| kaj naredimo s piko | mediana | v 100 m |
|---|---|---|
| pustimo pri miru (prej) | 63 m | 63 % |
| premaknemo po smeri (`bearing`) | 36 m | 72 % |
| **premaknemo po trasi** | **30 m** | **80 %** |

Trasa je boljša od smeri, ker cesta zavija, vozilo pa ne pove, da bo zavilo.
Vzorec je majhen (41 vozil ob desetih zvečer) — smer je jasna, natančnost
številk pa ne; kdor to spreminja, naj izmeri znova.

Varovala, brez katerih bi ocena lagala: ne premikamo **stoječega** vozila
(`speed_ms < 1`), ne vozila, ki je od trase oddaljeno nad 120 m (ni na njej),
in nikoli čez konec trase. Podnapis pove „ocenjeno iz lege pred 42 s", ne
„lega stara 42 s".

**Barva loči meritev od ocene.** Vozilo na tem zemljevidu ni zeleno kot
drugod, ampak v `ESTIMATE_COLOR` (`#a8d8ff`) in rahlo prosojno — ta odtenek je
v projektu rezerviran prav za „tu meritve ni" in ga lestvica zamud ne uporablja.
Zadnja **izmerjena** lega je **rdeča** pika s svetlim obročem: trasa in
postajališča so zeleni, zato se zelena pika med njimi izgubi, rdeča pa ni iz
nobene lestvice — ne iz zamud in ne iz razmer — in tu ne more pomeniti nič
drugega. Pika se **dvigne nad traso** (`bringToFront()`): črta in pika sta v
isti plasti, vrstni red risanja je vrstni red dodajanja, in 3 px široka trasa
jo je prerezala tako, da je bila videti kot del proge. Riše se vedno — kadar
vozilo stoji, jo oblika vozila pokrije in dveh oznak ni videti. Pod
zemljevidom je enovrstična legenda; brez nje je moder avtobus ob rdeči piki
uganka, in prav razlika med njima je bistvo tega okvira.

**Geste so omejene, dokler je zemljevid element strani.** Vprašanje „naj
kolešček približuje" ima odgovor „ne, dokler je to element" — kazalec zaide
čez zemljevid in stran se neha pomikati. Zato:

| | vgrajen | čez celo stran |
|---|---|---|
| kolešček | ne (Ctrl/⌘ + kolešček da) | da |
| en prst | pomika **stran** | pomika zemljevid |
| dva prsta | pomikata in približujeta | isto |
| gumba +/− | vedno | vedno |

Resnična napaka tu **ni bila** manjkajoča povečava, ampak `dragging`: ta je
privzeto vklopljen in je en prst pomikal zemljevid namesto strani — na
telefonu se s tega okvira ni dalo odpomakniti. Zdaj je izklopljen, dva prsta
pa zemljevid vseeno pomikata in približujeta, ker to opravi `touchZoom` (med
širjenjem prstov premika tudi središče). Dvoprstna povečava je torej **delala
že prej**; manjkalo je nasprotno.

Na sledilni ploščici brskalnik širjenje prstov pošlje prav kot `wheel` s
`ctrlKey`, zato ista koda pokrije Ctrl + kolešček in ščipanje. Namig se pokaže
**samo ob poskusu brez tipke** in po 2,2 s izgine — takrat človek res ne ve,
zakaj se nič ne zgodi; opomba, ki visi ves čas, bi bila četrta razlaga na tem
okviru.

**Gumb razširi zemljevid čez celo stran, ne čez cel zaslon.** Fullscreen API
vzame ves monitor in skrije brskalnik; za „hočem videti več zemljevida" je to
preveč — človek izgubi naslovno vrstico, gumb nazaj in vsak drug orientir,
izhod pa je tipka, ki je na telefonu ni. Razred `is-max` na okviru
(`position: fixed; inset: 0`) naredi isto koristno stvar in nič od tega; glava
in legenda ostaneta, ker brez njiju ni ne hitrosti ne pomena oznak.

**Razširjen zemljevid mora prezreti postavitev, in to zahteva `!important`.**
Namizna pravila v `@media` (`body:not(.is-advanced) .col-run .run-map`) imajo
specifičnost **(0,3,1)** in so `.run-map-wrap.is-max .run-map` **(0,3,0)** tiho
premagala: zemljevid je čez celo stran ostal visok **240 px** in zamaknjen za
**12 px** margine, vse ostalo pa črno. Na telefonu se to **ni videlo**, ker
tistih pravil tam ni — zato je bilo popravljeno šele, ko je bilo prijavljeno z
namizja. Rešitev ni daljši selektor, ampak `!important` na `position`, `inset`,
`margin` in `height`: element je iztrgan iz postavitve in mora prezreti vsa
pravila o njej. Isti vzorec kot `adv-only` v `base.css`.

**Ozadje zemljevida rabi sestavljen selektor.** `.leaflet-container` ima svoj
`background: #ddd`, Leafletov CSS pa se naloži **šele ob prvi legi**, torej za
našim — enaka specifičnost, poznejši zmaga. Pri 260 px se to ni videlo, ker
ploščice pokrijejo cel okvir; čez celo stran je bila polovica bela. Zato
`.run-map.leaflet-container { background }`. Višina ostane pri enem razredu,
sicer bi sestavljeni selektor povozil telefonsko pravilo v `@media`.

**Na velikem zemljevidu tega ni**, in to je odločitev, ne opustitev: tam je
vprašanje „kje je vse skupaj" in ocena za osemdeset vozil je osemdeset
izmišljenih leg. V oknu vožnje gledaš eno vozilo in vprašanje je natanko
„kje je zdaj".

**Trasa se skoraj nikoli ni risala.** Pogoj `trasa.length > 1` je bil napisan,
ko je bil `points` ravna lista točk; odkar jih uvoz reže na kose
(`SHAPE_BREAK_M`), je enodelna trasa dolga 1 in je pogoj ni spustil skozi.
To je bilo **2 706 od 2 897 oblik, torej 93 %** — v oknu vožnje in na velikem
zemljevidu. Pravilen pogoj je „vsaj en kos z vsaj dvema točkama".

**Okno vožnje z GPS ima živ zemljevid, in to v preprostem pogledu.** „Kje je
zdaj" je pri avtobusu prvo vprašanje. Leaflet se naloži šele, ko lega res
obstaja — vlaki je nimajo nikoli in zanje tega okvira ni; prazen bi obljubljal
podatek, ki ne obstaja.

**Starost lege mora teči sama.** „lega stara 59 s" je stala pri miru do
naslednjega polla in nato skočila nazaj na 38 -- videti kot okvara, čeprav je
bila vsaka vrednost pravilna. Starost je edina številka na strani, ki se
spreminja tudi takrat, ko se ne zgodi nič, zato jo šteje brskalnik:
`common.ageHtml()` vrne `<span class="age-live">` z izhodiščem v
`data-`atributih, ena sekundna zanka pa jih poišče po razredu. Iščemo po
razredu in ne po registru, ker se kartica na zemljevidu gradi iz niza HTML in
nanjo ni kam obesiti sklica. **Ura odjemalca ni v računu** — prištevamo
razliko dveh lastnih meritev, zato zamik ure ne škodi.

**Kdor izpiše `ageHtml()`, ponastavi števec.** Funkcija ob vsakem klicu zapiše
novo izhodišče, zato izpis ne sme teči v sekundni zanki. Prav to se je zgodilo,
ko je pike začel premikati `postaviVozilo()`: ta je vsako sekundo prepisal tudi
podnapis, števec se je vrnil na izvorno vrednost, zanka v `common.js` ga je
vmes povečala in naslednji izris povozil — videti je bilo kot utripanje.
Podnapis se zato prepiše **samo ob novih podatkih** (`nova`), premik pike pa
teče vsako sekundo. Pravilno je videti tako: 55, 56, …, 60, **50** (prispela
nova lega), 51, 52.

**Preprost pogled ni samo za telefon.** Okno vožnje je bilo en stolpec 340 px;
ker je zgodovina v preprostem pogledu skrita, je na namizju ostal ozek trak ob
praznem zaslonu. Nad 1000 px se vsebina razdeli: levo, kar velja **zdaj**
(zamuda, razmere, kje je vozilo), desno pot po postajah. Flex in ne grid —
časovnica je visoka in bi kot element čez več grid vrstic te vrstice
raztegnila, levi stolpec pa bi visel v praznem.

Izmerjeno pri 1920 × 993: levi stolpec je bil **599 px, od tega zemljevid
320** — torej 53 % višine za okvir, ki samo pove „kje je zdaj", medtem ko je
bil desni stolpec 360. Na namizju je zato zemljevid 240 px (na telefonu 210,
privzeto 260) in blok trenutne zamude tesnejši; stolpec meri **506 px**.
Zrak med vrsticami se stiska **samo tu** — na telefonu je prav on tisto, kar
loči dotik od dotika.

**Statične datoteke gredo z `Cache-Control: no-cache`.** Brez glave brskalnik
ugiba in datoteko, ki se dolgo ni spremenila, drži ure. Posledica je bila
prijavljena: popravek spodnje plošče je bil na strežniku, uporabnik pa je
dobival staro CSS in gumba ni bilo. `no-cache` ni „ne shranjuj" — datoteka se
shrani in se pred vsako rabo preveri; z `ETag` je odgovor 304 brez telesa.

**Opomb naj bo malo.** Prikaz je imel na zemljevidu tri odstavke razlage, v
oknu vožnje pa štirivrstično opombo o vremenu in drugo o virih podatkov.
Zapisano dvakrat je bilo prebrano nikoli. Velja: opomba pove tisto, kar
spremeni potnikovo ravnanje („čakaj na postajališču, ne na peronu"), ostalo
gre v tooltip ali odpade. Razlaga o virih podatkov ne sodi tja, kjer človek
gleda svojo vožnjo.

**Stranska plošča zemljevida je na telefonu spodnja plošča.** 320 px stolpca
je na 390 px zaslonu pojedlo pol slike in ga ni bilo mogoče skriti; zdaj je
privzeto zaprt in se odpre na dotik. Izbira vozila ga spet zapre — naslednje,
kar človek hoče videti, je zemljevid.

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
* **Razred se določi iz zaokrožene minute, ne iz sekund.** Meje v `DELAY_RAMP`
  so v minutah in gredo skozi isto zaokroževanje kot `delayLabel`. Prej so bile
  v sekundah (`<= 60` = točno): 60 s je pisalo „+1" sivo, 61 s „+1" oranžno —
  ista številka, dve barvi. Barva ne sme pripovedovati druge zgodbe kot
  številka poleg nje.

  **Ista past se je ponovila pri „prej".** Prag je bil `s <= -60`, zaokroževanje
  pa se prelomi pri −30 s: −45 s je zato izpisalo golo **„−1"** namesto
  „1 min prej". Pravilo je zdaj v `common.isEarly()` in ga uporabljata okno
  vožnje in iskalnik zvez — en prag, ena zaokrožena minuta.
* Odtenek lestvice se uporablja **samo tam, kjer pomeni velikost zamude**.
* **Padec zamude na postaji riši vedno, krogec prihoda pa le, kadar je zanj
  prostor** (`MIN_SPLIT_PX = 15`). Krogec meri v premeru 10 pik, polna pika
  odhoda 11 — pri manjšem razmiku se prekrijeta, navpičnica med njima izgine
  pod njima in videti je kot **dva nepovezana krogca**. Prav to je bilo
  prijavljeno pri Divači (+16 → +15, razmik natanko 10 pik).

  Rešitev ni skrivanje: enominutni padec je resničen podatek. Odsek se konča
  pri **prihodni** vrednosti, navpičnica pa pade na odhodno — pri majhni
  razliki je to stopnica ob piki in se bere, pri veliki (Ljubljana, 170 pik)
  dobi še krogec. Skrivanje bi izgubilo prav tisto, zaradi česar je padec
  narisan.
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

**Pri stopnji 0 žeton kaže temperaturo, ne stopnje.** „0" potniku ne pove nič,
„22°" pa nekaj — stopnja se vrne takoj, ko je kaj za povedati (≥ 1). Žetoni so
v preprostem pogledu na **postajah naprej po progi** (napoved, črtkan rob);
prevožene postaje so tam itak skrite in mirno vreme za nazaj ne pove ničesar.

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
3. **Ponavljajoče se opravilo naslednji čas računa od tika, ne od „zdaj".**
   Zanka zajema je tiknila na 10 s, `next_positions` pa se je nastavljal na
   `time.monotonic() + 10` **po** opravljenem delu -- torej vedno za drobec
   pozneje od naslednjega tika, ki ga je zato zgrešil in preskočil cel obhod.
   Izmerjeno: lege so se brale v razmikih **19, 11, 19, 11 s namesto 10**,
   mediana 15 s. Zanka zdaj spi do prvega naslednjega opravila
   (`min(next_*) - now`), ne fiksen tik, in razmiki so 10, 11, 10, 10, 10.
4. **Preveri `EXPLAIN QUERY PLAN`, preden verjameš, da je indeks.**
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

Za napoved zamude (`stats.predict`): vlak najprej porabi **rezervo voznega
reda**, kar ostane, popravi historična mediana ostanka pri **tem vlaku**,
ločena po razredu trenutne zamude. Izmerjeno (`sztrack backtest`, 292 736
nalog, izpuščanje enega dne):

| model | MAE | v 5 min |
|---|---|---|
| prenos (referenca) | 2,94 min | 82,7 % |
| vlak (mediana spremembe) | 2,00 min | 90,3 % |
| odsek | 2,25 min | 87,9 % |
| odsek + razred zamude | 2,27 min | 87,7 % |
| združen (krčenje) | 1,98 min | 89,7 % |
| vlak + razred zamude | 1,99 min | 90,5 % |
| vlak, premica `d_j = a + b·d_i` | 2,08 min | 89,5 % |
| rezerva sama (brez učenja) | 3,01 min | 82,3 % |
| **rezerva + razred zamude (v uporabi)** | **1,92 min** | **91,0 %** |

**Običajni postanek se kaže, ne uporablja.** `MIN_DWELL_S = 120` je
predpostavka, da vlak postanek skrajša na dve minuti. Preizkušeno je, da
zamenjava s **historično mediano dejanskega postanka** natančnosti ne izboljša
(MAE 1,911 → 1,912 min; enako na odsekih z dolgim postankom in tam, kjer za
odsek ni zgodovine) — ker se rezerva in historični popravek seštejeta in
premikanje predpostavke med njima vsote ne spremeni.

Prikazu pa je namenjena: pri postanku nad pet minut okno vožnje napiše
„vozni red tu čaka 18 min; ta vlak, kadar zamuja, stoji običajno 15". Skriti
dvominutni prag je predpostavka, ki je nihče ne vidi in ki zna biti močno
mimo; ta stavek potnik lahko preveri.

**Rezerva voznega reda je edini vhod v napoved, ki ni statistika.**
`slack = Σ max(0, postanek − MIN_DWELL_S)` čez postaje med izhodiščem in
ciljem; `stats._after_slack()` jo porabi, a največ toliko, kolikor vlak
zamuja, in nikoli tako, da bi prihitel. Zna delati **prvi dan zajema**, ker
je vozni red znan vnaprej.

Od kod: LP 4219 ima na Mostu na Soči **devet minut postanka** (križanje na
enotirni bohinjski progi) in v devetih dneh ni nikoli nadoknadil več kot sedem
minut niti stal manj kot dve — +16 → +9, +11 → +4, +10 → +3, vsakič natanko
sedem. Konstantna mediana spremembe tega ne more izraziti: iz +11 je
napovedala +9, vlak je pripeljal +3. Z rezervo napove +4.

`MIN_DWELL_S = 120`. Backtest je med 60 in 180 s raven (1,932 / 1,924 /
1,928 min), pri 0 pa vidno slabši (2,214) — rezerva brez najkrajšega postanka
šteje ves postanek za prihranek. 120 s se ujema z izmerjenim dnom.

Sama rezerva je **slabša od prenosa** (3,01 min): zna samo brisati zamudo, ne
pa je ustvarjati. Šele ostanek — kar rezerva ne pojasni — jo naredi uporabno.
Razrez po trenutni zamudi, kjer je razlika največja:

| trenutna zamuda | vlak + razred | rezerva + razred |
|---|---|---|
| 0–2 min | 1,73 min · 91,3 % | 1,71 min · 91,4 % |
| 2–10 min | 2,06 min · 90,6 % | 1,96 min · 91,4 % |
| 10–30 min | 2,30 min · 89,1 % | 2,20 min · 90,0 % |
| nad 30 min | 3,32 min · 83,7 % | **2,93 min · 85,9 %** |

Iz tega troje, kar velja spoštovati, preden kdo piše nov model:

* **Združevanje po odseku model poslabša.** Na istem tiru se IC in lokalni vlak
  ne obnašata enako, zato skupna mediana zabriše prav tisto, kar šteje.
* **Združen model prihrani 1 % MAE in izgubi pri deležu v petih minutah.** To
  ni vredno zapletenosti. Prag `MIN_SAMPLES` 1–3 da isti rezultat, 4 in več
  poslabša.
* **Razred zamude šteje, a le pri velikih zamudah.** Skupno je razlika
  komaj 0,7 %; razrez po trenutni zamudi pa pokaže, kje je:

  | trenutna zamuda | vlak | vlak + razred | nalog |
  |---|---|---|---|
  | 0–2 min | 1,74 min · 91,2 % | 1,73 min · 91,3 % | 137 180 |
  | 2–10 min | 2,05 min · 90,7 % | 2,06 min · 90,6 % | 80 531 |
  | 10–30 min | 2,33 min · 88,7 % | 2,30 min · 89,1 % | 68 876 |
  | **nad 30 min** | 3,62 min · 82,1 % | **3,31 min · 83,8 %** | 5 602 |

  Fizikalno je razumljivo: postanek s pol minute rezerve vlaku z 11 minutami
  vzame dve, točnemu pa nič — ta nima česa nadoknaditi. Mediana čez oba
  opisuje nobenega od njiju. Prag treh dni s podobno zamudo je izmerjen:
  pri 1 je MAE 2,19 min, pri 2 2,11 min, pri 3 1,99 min. `stats.delay_bucket`
  in `backtest._bucket` sta **ista funkcija** — sicer bi merili en model in
  uporabljali drugega.

**Premica `d_j = a + b·d_i` je bila preizkušena in je slabša** (MAE 2,08 min,
nad 30 min celo 4,78 min). Zna izraziti postanek, ki zamudo pobriše (`b ≈ 0`),
a je pri devetih dneh naklon prešumen — in kar naklon lovi iz podatkov, piše
vozni red zastonj.

**Prikazani dan je izpuščen iz učenja** (`stats.predict(exclude_date=...)`,
enako kot `history`). Pri tekoči vožnji naprej po progi meritve ni, pri ogledu
končanega dne pa bi model deloma napovedoval iz odgovora.

**Preizkušeno in ne pomaga** — vse merjeno z izpuščanjem enega dne, vse
slabše ali enako `rezerva + razred` (1,914 min · 91,0 %):

| zamisel | MAE | v 5 min |
|---|---|---|
| rezerva iz voznega reda **in** največjega opaženega okrevanja | 1,921 | 90,9 % |
| rezerva samo iz opaženega okrevanja (brez voznega reda) | 1,935 | 90,9 % |
| dodaten člen za trend zamude (raste/pada) | 1,917 | 91,0 % |
| stanje odseka danes: kaj so tam delali drugi vlaki pred nami (30 % teže) | 1,921 | 90,9 % |
| isto, s polno težo | 2,089 | 89,6 % |
| zamuda nasprotnega vlaka na isti postaji (križanje), 10 % teže | 2,020 | 90,4 % |

Zakaj nobena: pri devetih dneh mediana po `(vlak, i, j, razred)` že zajame
skoraj vso strukturo. **Strop je izmerjen**: mediana, ki bi poznala tudi
testni dan, da MAE 1,198 min in 95,0 % — torej je razlika do naših 1,914 min
vrzel v **številu dni**, ne v domiselnosti modela. Obvestila o ovirah so za
model neuporabna iz drugega razloga: 522 od 779 vlakov ima kakšno, vsa pa so
veljala ves čas zajema, zato med dnevi ne ločijo ničesar.

**Preizkušeno in ne pomaga** (`sztrack backtest --day-offset`): popravek za
stanje mreže na ta dan. Zamisel je razumna -- če cel dan zamuja bolj kot
običajno, bo tudi ta vlak -- a povprečna sprememba zamude se čez zajete dni
giblje le med 115 in 142 s. Premalo, da bi kaj rešilo, dovolj, da doda šum:
MAE 2,00 → 2,06 min, delež v petih minutah 90,2 % → 89,1 %. (Mediana je za to
neuporabna: pri večini sosednjih postankov se zamuda ne spremeni, zato je
vsak dan 0.)

Vsak nov model naj se najprej pomeri s `prenos`. Kar ga ne premaga, ne sodi
v prikaz, pa naj bo še tako domiseln.

**Avtobusi bodo dobili svoj model; zdaj ga nimajo in to je izmerjeno.**
`backtest --network avtobus`, 2 dneva in 326 685 nalog: sedanji model da
**natanko isto kot prenos zamude** (2,74 min · 92,5 %), ker z dvema dnevoma
ni niti enega para (vožnja, i, j) z dovolj vzorci. Edini, ki kaj pridobi, je
`odsek` (2,63 min · 92,9 %) -- združevanje po fizičnem odseku čez vse linije.
Model torej avtobusom ne škodi, a jim tudi ne pomaga.

Ko bo meritev dovolj, gresta modela **narazen**: pri avtobusu so smiselni
vhodi, ki jih železnica nima ali jih tam ni vredno gledati -- ura dneva
(gneča), vreme, GPS hitrost in lega, gostota postajališč. Do takrat velja
isto pravilo: kar ne premaga prenosa, ne gre v prikaz.

**Meritev je bila neizvedljiva, dokler mediane niso bile predračunane.**
`statistics.median` se je klical enkrat na napoved. Pri železnici je bil
seznam po odseku kratek in razlike ni bilo; pri mestnem avtobusu isti odsek
vozi več linij, seznam zraste na desettisoče in `odsek+razred` je za en dan
porabil 6,5 minute namesto 0,3 sekunde. `backtest._medians()` jih izračuna
enkrat ob učenju -- rezultat do zadnje decimalke isti.

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
