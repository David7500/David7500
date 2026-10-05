---
paths:
  - "kajros/pristanek.py"
  - "kajros/static/pot.js"
  - "kajros/static/pot.css"
  - "kajros/static/pot_karta.js"
  - "kajros/static/pot_podrobno.js"
  - "kajros/static/pristanek.css"
  - "kajros/static/connections.js"
  - "kajros/static/connections.css"
  - "kajros/static/home.js"
  - "kajros/static/home.css"
  - "kajros/templates/**"
  - "kajros/static/o_nas.css"
  - "o-nas/**"
---
# Strani in kaj je na njih

## Strani

**Hitrosti po odsekih ni več nikjer.** Bila = isti podatek v drugi enoti, zložen v zaprt `<details>` na dnu okna vožnje. Tu je pisalo, da `/api/speeds` in `stats.segment_speeds()` ostaneta, „ker ju rabi izvoz in mreža razdalj" — **ni držalo**: `kajros export` zapiše `network.geojson` in `stations.json`, oba iz `network_geojson()`; `segment_speeds()` ni klical nihče. Odstranjena (45 + 4 vrstice); v zgodovini, če bi zatrebala. Odpadel tudi `/api/trains` s `stats.trains()` — prav tako ga ni klical nihče.

**`/app/statistika` odgovarja na „kdaj se splača potovati", ne „kakšna je statistika".** Stran prej odstranjena do prenove; vrnjena s tem vprašanjem, ker je edino, ki ga potnik res ima. **19. 9. 2026 spet umaknjena** („v taki obliki skoraj neuporabna"): ploščica na domači strani odšla, pot iz zemljevida strani, stran ima `noindex`. Stran in endpointa ostanejo do prenove. Na vrhu ena poved (najboljša in najslabša ura), pod njo razrezi po uri, dnevu v tednu in vrsti vlaka, na dnu dan za dnem, ki je `adv-only`.

Tri pravila, ki so se pokazala šele na posnetku prve različice:

* **Merilo stolpcev postavijo samo vrstice z dovolj vzorca** (`MIN_VZOREC`, 30 voženj). Prva različica: nočna ura s 13 vožnjami in mediano 24 min je določila merilo — cel dan se stisnil v pahljačo po dve piki. Vrstica, ki ji ne verjamemo dovolj za naslov, ne sme voditi slike; presežek se odreže na 100 % in dobi znak `›`.
* **Število meritev ostane vidno tudi na telefonu.** Prvi poskus ga je skril („širina je dragocenejša") — a telefon je glavna naprava in prav tam bi „sreda je najhujša" ostala brez vzorca. Skrči se ime, ne vzorec.
* **Ure so po POSTANKU, ne po odhodu vožnje.** „Ura odhoda" odgovarja na drugo vprašanje, kot ga potnik ima: vlak, ki odpelje ob 05:00 in nabira zamudo do 09:00, jo v tistem rezu vso pripiše peti uri, ko na omrežju še ni bilo nič narobe. Izmerjeno na železnici: ob 04:00 rez po odhodu **4 min**, po postanku **0 min**; ob 23:00 **10 min** proti **3 min**. Vzorec desetkrat večji (ob 06:00 4 485 postankov proti 367 vožnjam), zato nobena ura ne pade pod prag. Polje `by_stop_hour`; `by_hour` ostaja v API-ju, še vedno po vožnji.
* **Ista meja velja za sliko, ne le za naslov.** Prva različica je merilo postavljala po vzorcu (≥ 30 postankov), zato so ga postavljale nočne ure: 02:00 s 6 min in 115 postanki najdaljši stolpec, dnevne ure stisnjene v enako dolge palice. Kar ne sme voditi povedi, ne sme voditi slike. Pri **vrstah vlaka to NE velja** — EN s 46 vožnjami = 2 % prometa in hkrati resnična ugotovitev (nočni vlak, ki vedno zamuja), zato je merilo prometa vklopljeno samo pri urah (`poPrometu`).
* **Naslov primerja samo ure z rednim prometom** (`DELEZ_PROMETA`, 25 % postankov najprometnejše ure). Brez tega odgovor „ob 03:00 vlaki zamujajo 0 min" — resničen, a za izbiro poti neuporaben. Prag izmerjen, ne izbran: delež pade s 34 % (04:00) na 4,9 % (03:00) in z 39 % (22:00) na 21,6 % (23:00) → prelom čist.
* **Blok po dnevu v tednu sam pove, kdaj mu ni za verjeti.** Pri manj kot štirih ponovitvah vsakega dne (28 dni zajema) podnaslov to napiše z izračunano številko, ne z občutkom.

* **Lestvica najhujših nosi sidro čez vse vožnje.** Razrez urejen padajoče → prva vrstica najhujša, ne tipična; brez primerjave se „EC 211 · 46 min“ bere kot opis omrežja. Mediana vseh železniških voženj **3 min**, p90 20 min, 60 % jih konča v petih minutah (6 472 voženj); avtobusi 1,6 min in 74 % (38 272). Zato uvodna poved doda „Čez vse vožnje je mediana …“, podnaslov lestvice pove „najhujši, ne tipični“.

  Ni domnevana zmeda: prvi, ki je `kajros stats` prebral kot „vlaki zamujajo 46 minut“, je bil avtor kode, ki je imel poizvedbo pred sabo. Potnik nima niti te prednosti.

  Polja `median_s`, `p90_s`, `on_time_share` v `breakdowns()`; računajo se iz vrstic, ki jih razrezi tako ali tako berejo → brez nove poizvedbe in brez agregata v zahtevi.

  **Ob spremembi polj povečaj `stats.SUMMARY_VERSION`.** Povzetek shranjen v `povzetek`, velja 36 ur; brez tega predpomnilnik streže staro obliko, stran novo polje izpusti, videti je, kot da sprememba ne dela. Točno to se je zgodilo pri `median_s`.

## Domača stran je razcepišče, ne nadzorna plošča

**Živih številk tam ni** (odstranjeni 12. 9. 2026 na prijavo). Bili sta dve:

* „danes običajno: vlaki +2 min · avtobusi +1 min" — vsak dan skoraj ista številka, ne spremeni ničesar, kar bo človek na tej strani storil;
* števec vozil „na poti" na vsaki kartici — podatek o omrežju, ne o njegovi poti.

Odpadli **dve zahtevi od treh** (`/api/overview` in `/api/overview/bus`, najdražji na strani, ki je samo razcepišče). 1. 10. 2026 odpadla še tretja, `/api/health` za število ovir — ovir na domači strani ni več (spodaj). Obseg zajema („zajetih N meritev v M dneh") je bil v nogi do 19. 9. 2026, odšel — potniku ne pove ničesar.

**Noge ni nikjer** (od 2. 10. 2026). Ob orodni vrstici na dnu je bila spletni ostanek, ki ga nativna aplikacija nima (prijava: „mogoče je malo čudno“). Vsebina je v **meniju Več** (`_vec.html`): gumb ⋮ skrajno desno v glavi vsake strani razen `/admin` in `/brez-omrezja`, odpre **spodnji list** (osnutek C od petih, platno „Kajros: meni v zgornji vrstici“): ikona in ime, „Podpri kajros“ (tonski, `--m-kont`) ob Stik in O nas, nato Vse postaje, Vsa postajališča (edina pot do kazal pristajalnih strani poleg zemljevida strani), Aplikacija za Android (v aplikaciji skrita), Zasebnost, na dnu navedba vira, pogoj CC BY-SA.

* **List je `popover`, ne `<dialog>` z JS.** Pristajalne in besedilne strani JS nimajo, meni pa morajo imeti. Odpre ga `popovertarget`, zapre dotik zunaj ali Esc. Brskalnik brez `popover` (pred Chromom 114) ga pokaže na koncu strani kot navaden razdelek — zato je `vec_list()` za skripti na koncu `<body>`, slog lista pa pod `@supports selector(:popover-open)`.
* **Tipka nazaj list zapre**, ne zapusti strani (`common.js`, `pripniMeniVec()`): ob odprtju vnos v zgodovino, zaprt list ga vzame nazaj. Povezava v listu gre najprej nazaj čez ta vnos, šele nato na cilj — brez tega mrtev korak v zgodovini. Poteg navzdol nad 80 px list zapre. Preverjeno prek CDP s pravim dotikom.
* **Gumb je v kotu glave pripet** (pod 560 px `position: absolute`, glava `padding-right: 52px` prek `:has`): v toku se je pri 320 px na ovirah prelomil v drugo vrstico na levo; zemljevid in okno vožnje imata svoj odmik glave, ki bi ga brez `:has` povozila.
* **Podpora je zdaj vidna le, kdor meni odpre.** Obisk `/donacije` primerjaj pred 2. 10. 2026 in po njem, preden sklepaš, da meni deluje.

**Podpora (`/donacije`) pelje na `ko-fi.com/kajros`** (odprto 19. 9. 2026, PayPal Business na ime „kajros“, da donator ne vidi lastnikovega imena). Naslov = privzetek v `config.py`, ne v enoti, ker ga agent tam ne more pisati. Prazen `KAJROS_DONACIJE=` skrije vse: pot je ploščice na domači strani (na mestu nekdanje „Kdaj potovati") in gumba v meniju Več ni: prošnja brez naslova, kamor bi denar šel, je slabša od nobene. Stran pove ime ponudnika ob gumbu, ker gumb pelje s strani.

**Povedi so pisane, kot se piše, ne kot se govori.** „Kdaj ti pelje in koliko zamuja" in „kje je zdaj kaj" prijavljena kot stavka, ki se v slovenščini tako ne uporabljata; zdaj „Odhodi in zamude slovenskih vlakov in avtobusov" in „kje so vlaki in avtobusi ta trenutek". Isto za naslove v zavihku brskalnika: „Vozni red vlakov in zamude v živo — kajros", ne „kdaj mi pelje vlak".

**Naslov strani se začne s tem, kar človek vtipka v iskalnik, znamka je zadnja** (29. 9. 2026). „vozni red“, „zamude“, „v živo“, „vlakov/avtobusov“ — besede iz Googlovega samodejnega dopolnjevanja („vozni red vlakov zamude“, „sž zamude vlakov danes“). „kajros — …“ je porabil prvo mesto za besedo, ki je nihče ne išče. Opis pristajalne strani nosi številke (vožnje danes, najhitrejša, običajna zamuda), ne splošnega stavka, ki je bil enak na 800 straneh.

**Domača stran ima `<h1>`** — eno vrstico pod znamko (`.d-geslo`). Brez nje je iskalnik videl gumbe: 296 znakov besedila, ne „zamude“ ne „vozni red“.

**Domača stran je Material 3 Expressive** (osnutek G, izbran 26. 9. 2026 med devetimi na platnu „Domača stran kajros"). Zavrnjene prej: kartice z ikonami in prelivom („preveč AI generirano"), tipografske vrstice („vse isto oblikovano in dolgočasno"), ploščice 14.–26. 9. („zgleda tako AI": vse enako zaobljene kartice z obrobo, razprte velike črke, pastelna polja). Sestava:

* **Budilka = tonska kartica na vrhu, a samo, kadar budilka obstaja** (`--m-kont` #5a2e12, besedilo #ffdbc8, 8,8 : 1). „Budilke morajo biti takoj dostopne, ne da iščeš, kje so." V aplikaciji `home.js` bere `Kajros.seznam()`: ura zvonjenja 40 px, dan in odštevanje ob njej, stikalo (`preklopi`); pod njo čez vso širino vožnja in odhod z zamudo; gumb „Vse budilke (N)". Po zvonjenju kaže odhod, kot widget. Uro in odhod izračuna Kotlin (`odhod_ms`, `vir`), stran samo izpiše. **Zamuda v kartici je žeton na podlagi strani** (`.bud-zam`): `--d-big` na rjavem vsebniku ne doseže kontrasta.
  * **Skrčena 1. 10. 2026** (osnutek 1 od dveh; prijava obiskovalke: začetna stran „preveč overwhelming“, „rabila minuto, da sem jo pregledala“). Prej je bila kartica vedno, tudi prazna („Ni nastavljenih budilk — odpri vožnjo in pritisni budilka“: navodilo za funkcijo, ki je novinec še ne pozna), z dnevi v krogih in še do tremi budilkami s stikali — največji element strani. Dnevi, „zvoni N min prej“ in druge budilke so zdaj en dotik stran, v seznamu.
  * **Vse ugasnjene → kartica ostane** („Vse budilke so ugasnjene“ + seznam), sicer jih s prve strani ne bi bilo mogoče prižgati. Nobene budilke → kartice ni, namesto nje oblika „Budilke · ni nastavljenih“ ob zemljevidu, ki odpre seznam.
  * **V brskalniku** budilk ni; povabilo na aplikacijo je oblika „Budilka · za Android“ (`#bud-oblika` → `/android`), ne prva kartica.
* **Vlaki in Avtobusi sta v razprti orodni vrstici, ne na strani** (osnutek D od štirih, 1. 10. 2026). Prej dva velika povezana gumba tik nad orodno vrstico, ki je imela isti dve mesti še enkrat — ista izbira dvakrat na enem zaslonu, del prijavljene zmede. Na domači strani: Vlaki in Avtobusi kot pilula z imenom v barvi omrežja, ločilo, Pot in Zemljevid kot ikoni; Domova ni, ker si doma. Okvir vrstice je isti kot drugod (od 2. 10. 2026, prej 76 px visoka — skok ob prehodu, glej `oznake.md`). Barvi sta pomen (trdo zapisani, izjema iz `oznake.md`).

  Teža izmerjena na obisku (7 dni do 1. 10. 2026, osebe po dnevih): `/` 1 196, `/app/bus` 644, `/app/train` 405, `/app/pot` 376, `/app/map` 189, `/app/ovire` 62. Omrežji sta najpogostejša pot naprej, zato v vrstici z imenom in barvo, ne kot gola ikona.
* **Najhitrejša pot = iskalna vrstica** „Kam greš?" z okroglim gumbom, prva pod naslovom. Pelje na `/app/pot#kam` (od 5. 10. 2026): kazalec v polju **Kam**, ne Od kod — človek je ravno odgovoril na „kam“. Od kod dobi „moja lega“ samo, kadar brskalnik strani lego že dovoli (`navigator.permissions`); dovoljenja ne zahtevamo sami (`zemljevid.md`). Lojtra, ne poizvedba: hash ne gre ne na strežnik ne v ključ service workerja.
* **Moje poti = shranjene poti z naslednjima odhodoma in zamudo** (osnutek A, 1. 10. 2026), pod iskanjem. Iz `kajros:fav` (zvezdica v iskalniku, obe omrežji, največ šest), kartica na pot: `/api/connections` brez prestopov ali `/api/departures` za shranjeno tablo (s stranjo ceste iz `kajros:smer`); izmerjeno na arwenu 40–90 ms, ~20 kB na pot; osvežitev na 60 s in ob vrnitvi na stran. Prej značke z imeni, ki so samo odprle iskalnik. Ni živa številka o omrežju (te so odšle 12. 9.), ampak o tvoji poti.
  * Ura je voznoredna, ob njej zamuda iz `zamuda` (strežnik), „točno“ pri zaokroženi ničli; mimo je odhod šele po pričakovani uri, nepotrjen ostane do `nepotrjen_do` („potrditve odhoda ni“). „brez podatka“ samo za odhode v 30 min (kot `pot.BREZ_PODATKA_PRED_S`), nadomestni prevoz „po voznem redu“.
  * **Danes nič več → prva jutrišnja** z oznako „jutri“: ob 23:20 je bila sicer prazna vsaka kartica (prvi preizkus).
  * **Novinec pogostih poti ne vidi** (zavrnjeno ob osnutku): ena poved v tihi kartici, kako pot shrani. Tuje poti so šum.
* **Budilka, Zemljevid, Deli lego = ikone v oblikah** (cvet, detelja, zvezda; poti iz `r = R(1 + a·cos nθ)`, v predlogi), vsaka v svoji barvi — rjava, modrozelena, indigo (izbrano 1. 10. 2026 med šestimi kombinacijami) — in s podnapisom: „za Android“, „vozila v živo“, „pomagaj drugim“. Brez podnapisa „Deli lego“ ni povedal, čemu je. Pritisk posvetli obliko, ne pravokotnika okrog nje.
* **Ovir na domači strani ni** (od 1. 10. 2026). Veljajo samo za vlake, domača stran je obema omrežjema; `/app/ovire` je v 7 dneh odprlo 62 oseb na dan proti 1 196 na `/`; rumena značka je bila 28 dni zapored opoldne med 15 in 25 — nikoli ni povedala, da je danes kaj drugače, kar je bil njen razlog. Ostanejo na strani Vlaki (povezava v glavi, kartica pod iskalnikom) in v oknu vožnje za tisti vlak. Na domačo stran sodijo samo, kadar zadenejo potnikovo shranjeno pot — to še ni narejeno.
* **Deli lego:** oblika je vabilo (`deli-oblika`); `deli.js` shrani njen HTML in ga vrne v fazi `miruje`, v drugih fazah na istem mestu razpre kartico čez vso širino (`je-odprt` → `flex-basis: 100%`).
* Podpora nima več svoje ploščice; je gumb v meniju Več (pogoj: `KAJROS_DONACIJE`).
* **Plavajoča orodna vrstica** (`_orodna.html`) je od 26. 9. 2026 na vseh straneh aplikacije (domača, iskalnik, pot, zemljevid, ovire, okno vožnje), ne na besedilnih in pristajalnih; na domači razprta (zgoraj). Glej „Slog: Material 3“ v `oznake.md`.

`home.css` rabijo tudi napaka, stik, zasebnost, `/android` in `/brez-omrezja` (`.home`, `.home-brand`, `.home-lead`, `.more-link`) — spremembo teh razredov preveri tudi tam.

## `/app/pot` („Najhitrejša pot") — edina stran, ki se ne začne pri postaji

Potnik ve, **kje stoji**, ne s katere postaje mu pelje. Zato dva vhoda = kraja (naslov, ulica, kraj, postaja, shranjena točka, lastna lega, klik na zemljevid), ne dve imeni; iskanje teče **čez obe omrežji** — vlak in avtobus lahko v isti verigi. Za zemljevidom druga stran, ki omrežji namerno meša; zato ima `/api/stations/search` tu `network=vse`, drugod privzeto `zeleznica`.

**Naslovi so iz našega kazala, ne iz geokodirnika** (23. 9. 2026, `kajros/naslovi.py`, `/api/naslovi`). Tuji ponudnik bi ob vsaki tipki izvedel, kam kdo gre; prej zato naslova ni bilo mogoče vpisati. Kazalo iz OSM (hišne številke GURS tam za vso državo), 51 MB, poizvedba 1–15 ms. Polje: en seznam s tremi viri: shranjene točke, postaje (kazalo v brskalniku, takoj), naslovi/ulice/kraji/točke (strežnik, 160 ms zakasnitve, prekinjeno ob naslednji tipki). S številko v poizvedbi naslovi prvi, brez nje postaje. Razvrščanje upošteva **okolico** — drugi konec poti, lastno lego ali sredino zemljevida —, sicer „Trubarjeva 5" v Laškem pred Ljubljano. „Poišči" po tipkanju brez izbire vzame prvi zadetek, ne javi „manjka cilj". Kadar kazala na strežniku ni, polje išče samo po postajah, kot prej.

**Vprašanje časa = prihod, ne odhod.** „Kdaj moraš biti tam?": **čim prej** (privzeto, danes od zdaj; prvi predlog = najzgodnejši prihod) ali **do ure** (dan in ura; prvi predlog = tisti, s katerim od doma odideš **najpozneje**, z oznako „najpozneje" in rezervo do roka na vsaki kartici). Odhod ob uri izginil: odgovor na vprašanje, ki ga nihče ne postavi — človek ve, kdaj mora biti v službi, ne kdaj mora od doma. `/api/pot` `ob` ostane za druge odjemalce. Kadar za danes do roka ne gre več, stran ne reče „ni poti", ampak „Do 8:00 ne prideš več. Najhitreje si tam ob 8:14." (`ne_ujames`). Pot, ki po napovedi zamude pride prepozno, ostane na seznamu, na dnu in rdeče.

**Kolo ali rolka = potrditveno polje, ne drsnik** — 15 km/h na obeh koncih (`kmh`), drobno pod gumbom, ker ga večina ne rabi. V verigi „kolo 4" namesto „peš 12"; prestop med postajališči ostane „peš".

**Na domači strani prva, ne med „ostalim".** Edina stran brez zahteve, da potnik ve postajo — prvo vprašanje, ne zadnje. Ni tretja izbira ob vlaku in avtobusu, ampak **drugo vprašanje**, zato iskalna vrstica, ne tretji enak gumb. Omrežji sta od 1. 10. 2026 v orodni vrstici na dnu. Ikona Pot v njej to vrstico podvaja; ostala je, da ima vrstica na vseh straneh iste cilje.

**Iskanje postaj gre skozi kazalo, ne strežnik.** `/api/stations/search` za `network=vse` izmerjeno **1,35 s** na razvojnem računalniku — okoli pet na arwenu, na vsako tipko. Postaje se ne spreminjajo vsak dan: `/api/stations/index?network=vse&koordinate=1` se naloži enkrat (323 kB, 12 h v `localStorage`), išče se v brskalniku z istim razvrščanjem kot strežnik (`iskalnikKazala()` v `common.js`). Toplo 3,6 ms.

**Kazalo nosi tudi lego** — postajališče z **največ prometa** pod tem imenom. Naključno izbrano bi pri „Bavarski dvor" enkrat dalo eno stran ceste, enkrat drugo → iskanje poti od tam dva različna izida za isto ime.

**Predlog = vrstica, ne izpis.** Prej vsaka noga svoja vrstica z urami in postajami — štirje predlogi = dvajset vrstic, med katerimi ni mogoče izbirati na pogled. Zdaj troje: ure in trajanje, **veriga** (`peš 7 › LPP 9 › 7 min za prestop › LPP 25 +2 › peš 10`), drobno o prestopih. Rezerva prestopa mora ostati v verigi — brez nje „1 prestop" ne pove, ali zveza drži, in prav to je edino, zaradi česar je prestop vreden pozornosti.

**Brez podatka ≠ točno.** Vožnja, o kateri feed danes ni povedal ničesar, nosi v verigi sivo „brez podatka" — isto besedo kot iskalnik zvez. Prej prazno mesto, brano kot „vozi po voznem redu": 22. 9. 2026 je tako stal 25 s Tržnice Moste, ki je zamujal 20 minut, ker njegov feed zaradi novih id-jev ni prišel do nas (`zajem.md`, „Nov vozni red, stari id-ji v feedu"). Kdaj velja, pove strežnik (`brez_podatka`); za drug dan podatka v živo ne more biti, žetona ni. **Samo za odhode v naslednjih 30 minutah** (`pot.BREZ_PODATKA_PRED_S`, 30. 9. 2026): prej je stal pri 86 % voženj na seznamu, mediana 78 min do odhoda — tam podatka še ne more biti in beseda je bila šum.

**Zemljevid čez celo stran**, ne čez cel zaslon — isti razlog kot pri oknu vožnje: fullscreen skrije naslovno vrstico, gumb nazaj in vsak drug orientir, izhod je tipka, ki je na telefonu ni.

**Lega se ne izmeri enkrat, ampak ji sledimo.** Prvi popravek GPS pogosto zgreši za sto metrov, v naslednjih sekundah ga popravi, potnik se medtem premika; `maximumAge` zato **0** — brez tega brskalnik vrne do minuto star popravek in prvi klik pokaže, kje si bil, ne kje si.

Štiri stvari, pokazale se šele na zaslonu:

* **Ravna črta med postajama ni proga.** Prva različica je Grosuplje–Ljubljana narisala kot daljico čez pokrajino, kar trdi pot, ki je ni. Zdaj najprej skica, nato jo zamenja **prava trasa iz `shape`**, izrezana med vstopnim in izstopnim postajališčem. Hoja črtkana modra, vožnja polna oranžna — potnik mora videti, kje ga nese vozilo in kje njegove noge.
* **Imen postaj ne sklanjaj.** „peš 7 min od izhodišča do Grosuplje" je narobe, „do Grosupljega" bi moral nekdo izpeljati — za „Bavarski dvor" ali „Vič Glince" ne bi delalo. Zato puščica: `izhodišče → Grosuplje`.
* **Kateri klik gre kam, mora biti vidno.** Prvi klik postavi izhodišče, naslednji cilj; katero polje je „nabito", pove barva oznake.
* **Vir hoje pride na zaslon.** Kadar usmerjevalnik ne odgovori, stran napiše „hoja je **ocena**" — zasilna številka je izmerjeno mediano 6 minut predolga, brez te besede se bere kot izmerjena.

**Pot deljiva prek naslova** (`?od=lat,lon&do=lat,lon&tam=HH:MM&dan=…&kolo=1`). Brez tega je edini način, da nekomu poveš pot do sebe, opis s stavki — stran naj bi ga nadomestila. Današnji dan v naslov ne gre.

**Polje se glasi „do postaje največ".** Brez „do postaje" si stran nasprotuje: polje pravi 25 minut, pot „vso pot peš" ima 85. Omejitev velja za dostop do postajališča in z njega, ne za hojo sploh — razlika je bila prijavljena kot napaka, ker je bila nevidna. „Po meri" odšel s poenostavitvijo obrazca (23. 9. 2026); vrednost iz naslova, ki je med izbirami ni, dobi svojo izbiro. Meji kot na endpointu (3–45).

**Polje ostane, izmerjeno.** Na 40 parih točk (1,5–25 km, jutranja konica) je ura prihoda pri **vsaki** vrednosti meje enaka — mediana razlike 0 minut. Meja ne izbira med „hitreje" in „manj hoje", ampak med **ali odgovor obstaja** in **koliko hodiš**: 10 min da pot v 28 % primerov s 16 minutami hoje, 45 min v 95 % s 40 minutami. Brez polja bi bilo treba izbrati eno številko za vse, obe skrajnosti slabi. Preizkušeno tudi „iskati vedno na 45 in ponuditi tudi pot z malo hoje" — **ne gre**, taka pot med predlogi le v 2 primerih od 38.

Koraki izbirnika po isti meritvi 10 / 15 / 25 / 35 / 45: pri vsakem se delež najdenih poti merljivo spremeni (28 / 38 / 75 / 88 / 95 %).

**Ko z vozilom ni ničesar, stran pove dvoje**, ne le „ni poti": koliko traja hoja vso pot (resnica, ki jo imamo) in **koliko hoje bi bilo treba**, da bi bilo v dosegu prvo postajališče — s številko in gumbom, ki jo nastavi. Zadnje ni obljuba: postajališče v dosegu še ni zveza, tako tudi piše. Zato prefilter kandidatov meri do **45 minut** ne glede na nastavljeno mejo; sicer postajališča tik čez mejo ne izmeri in številke ni od kod dobiti.

**Zamenjava krajev in dan sta manjkala** (dodano 12. 9. 2026):

* **Zamenjava** = gumb med poljema. Pot nazaj = isto vprašanje z zamenjanima koncema; kraja z lego iz GPS ali klikom na zemljevid ni bilo mogoče prepisati. Kadar je odgovor že na zaslonu, se poišče takoj — gumb, ki vidno stanje pusti pri miru, je videti kot okvara.
* **Dan** = polje z dvema puščicama, isto kot v iskalniku zvez. `/api/pot` je `date` sprejemal ves čas, stran ga ni pošiljala. Ker ima polje zdaj dve strani, slog (`.date-row`, `.day-nav`, `.day-step`) v `base.css`, poslušalec v `common.pripniDnevnePuscice()`; dve različici istega računa bi se razšli ob prvem prehodu na zimski čas. Najmanjša širina **210 px** ni na oko: pri 160 px leva puščica ležala čez besedilo datuma — datum konča pri ~105 px, puščici zasedeta 68 px levo od koledarskega gumbka brskalnika, ki je 28 px od desnega roba.
* **Dan in ura vidna samo pri „do ure"**; „čim prej" je vedno danes. Rok, ki je danes že mimo, ne vrne poti za nazaj, ampak `ne_ujames` in najhitrejšo pot od zdaj.
* **Danes ne pelje nič več → jutrišnje zveze** (`danes_ni`, 30. 9. 2026), ne „ni poti": ob 22:30 je bilo brez vozila 74 od 100 vprašanj, jutrišnjo zvezo jih ima 54. Naslov to pove z dnem („Danes ne pelje nič več. Prve zveze · 1. 10."), kartice nosijo samo uri. Jutrišnje iskanje gre od polnoči brez meje hoje in brez ponovnega iskanja današnjega dne (`nadaljevanje=True`) — sicer bi ga odrezala hoja ob polnoči.
* **Ob isti minuti prihoda je prvi tisti, s katerim odideš najpozneje**; prestop več mora prinesti vsaj 10 min doma (`pot.PRESTOP_VREDEN_S`). Prej: 05:44 z dvema prestopoma nad 11:43 s tremi, isti prihod. Trajanje na kartici = razlika prikazanih ur (`trajanjePrikaz`), rezerva prestopa po urah, ki jih stran kaže (`rezervaPrestopa`: zamuda prve vožnje ob izstopu, vožnja brez podatka po voznem redu).
* Sprememba dneva, ure, meje ali kolesa odgovor **osveži samo, kadar je že na zaslonu**; dokler ga ni, išče samo gumb — isto pravilo kot na vstopni strani.

**Shranjene točke („dom", „služba") ostanejo v brskalniku.** Kje kdo stanuje = najobčutljivejši podatek, ki ga aplikacija lahko drži, zato `localStorage` (`kajros:tocke`, največ šest). Strežnik dobi samo koordinate, ki jih poizvedba nosi tako ali tako (`/api/pot?od_lat=…`); **ime ne gre nikamor**, tudi v naslov strani ne — sicer bi deljena povezava povedala, da je tista točka tvoj dom. Obratno naslov, ki ga odpreš sam, koordinate **poimenuje**: če se ujemajo s shranjeno točko, v polju piše „dom", ne 46.05611, 14.50577.

Ujemanje po razdalji (`TOCKA_PRAG`, 1e-4 ≈ 11 m), ne po enakosti: naslov nosi pet decimalk, lega iz GPS vse, dve zapisovanji istega praga bi se razšli.

Troje odločeno:

* **Žetoni pod obema poljema, ne enkrat na stran.** „Dom" je enkrat izhodišče, enkrat cilj; en sam seznam bi bil isti ugib kot klik na zemljevid, preden je oznaka povedala, kateri klik gre kam.
* **Zvezdica govori isto kot v iskalniku zvez** (`☆ shrani` / `★ shranjeno`): en gumb pove stanje in ga preklopi, križca na žetonu ni. Odstrani se tako, da točko postaviš in odtakneš zvezdico — dve poti do istega dejanja pri dveh poljih = dvanajst gumbov za šest točk.
* **Isto ime = isti kraj.** Shranjevanje pod obstoječim imenom popravi koordinate; brez tega bi seznam tiho dobil dva žetona z napisom „služba".

Ime se vpraša **v strani**, ne s `prompt()`: v aplikaciji za Android `WebChromeClient` (`Krom`) `onJsPrompt` ne obravnava, zato okna tam ni in shranjevanje bi tiho odpovedalo.

### `/app/pot/podrobno` — ista pot, razložena

Seznam = „s čim in kdaj", ta stran = **„kako"**. Klik na predlog pelje sem, doda dvoje:

* **prava pešpot na zemljevidu**, ne ravna črta (`hoja.pot()`, OSRM `route` z geometrijo). Brez usmerjevalnika: se **napiše** in nariše zračna črta; ravna črta brez opombe trdi pot, ki je ni;
* **vmesni postanki vožnje** v `<details>` — potnika najprej zanima, kje izstopi, potem šele kaj je vmes.

**Črta mora biti sklenjena od starta do cilja** (23. 9. 2026, prijavljeno z zaslona). Dve vrzeli: usmerjevalnik začne pešpot na najbližji poti, ne na vratih/postajališču (`hoja.pot()` zdaj doda priključek na oba konca); trasa vožnje odrezana na najbližjem **ogljišču**, ponekod sto metrov od postajališča (`common.trasa()` zdaj reže na projekciji + doda priključek do postajališča; projekcijo bližje od 35 m izpusti, sicer kljukica ob obroču). **Start in cilj = oznaki z besedo** (`pkKonca()`), ne krogca v plasti: obroč velikosti postajališča se je med ulicami izgubil. Oznaka MapLibra ne sme dobiti `position` iz našega sloga — z `relative` je start stal v Tivoliju. Postajališča nosijo ime od Leafletovega z13.

**Lastna lega in izhodišče nista ista pika.** Izhodišče je bilo polna modra pika, enaka lastni legi — pri iskanju od svoje lege dve enaki piki eno na drugi, postajališča sploh ne. Zdaj: polna modra = samo „ti", izhodišče prazen svetel obroč, postajališče obroč v barvi vožnje, cilj polna oranžna. Isto na seznamu predlogov (`pot.js`).

**Peš korak ima vodenje** („vodi me do postajališča / do cilja", 23. 9. 2026). Zamenjalo kompas: puščica proti koncu koraka je povedala smer, ne poti. Zemljevid gre čez stran, od blizu in nagnjen (`pot_karta.js`, isti nagib kot veliki zemljevid), obrnjen v smer hoje, lega v spodnji tretjini. Zgoraj **samo naslednji zavoj** (znak, „čez 120 m", „Zavij levo", ulica v imenovalniku — sklanjati ne znamo), spodaj koliko je še in **ali ujameš vozilo**: „LPP 6 odpelje ob 12:03 · čez 9 min · 3 min rezerve" (zeleno / rumeno pod 3 min / rdeče „pohiti"). Navodila iz OSRM (`steps=true`, `hoja.navodilo()`).

* **Smer kamere**: smer gibanja iz GPS pri hoji (> 0,7 m/s), sicer kompas telefona (`deviceorientationabsolute`, iOS na prošnjo iz dotika), sicer smer poti. Če zemljevid premakneš s prstom, kamera ne vleče nazaj, dokler ne pritisneš „sledi mi".
* **Zašel**: odmik od poti nad 35 m in nad dvojno točnostjo, trikrat zapored → nova pot od tu (`/api/pot/hoja`), največ vsakih 20 s (šum GPS 15 m: 149 lažnih preračunov na 305 km namesto 630). Preračun samo, ko si pot že začel (bil v **35 m** od nje; s 60 m je vozilo, ki pelje mimo pešpoti, sprožilo preračun sredi vožnje v 69 od 70 simuliranih voženj): „vodi me do cilja" se pogosto pritisne na vlaku, pot sedem kilometrov stran ni zašla, ampak je pred tabo. Takrat in brez lege se po navodilih lista na roko (‹ ›).
* **Prihod**: konec bližje od točnosti lege (najmanj 15 m) — „Tu je postajališče" z vozilom in gumbom „ko izstopiš: vodi me do cilja".
* Zaslon med vodenjem ne ugasne (`wakeLock`), zamude se osvežujejo vsakih 30 s, odštevanje vsakih 5 s; tresljaj 20 m pred zavojem in ob prihodu.

**Žeton zamude ob izstopu je drug od vstopnega in mora biti viden.** Vozilo vmes rezervo porabi ali izgubi: „+1 min" nad prihodom šest minut za voznim redom je videti kot napaka, čeprav je napoved. Zato drugi žeton na izstopni vrstici — samo kadar se od prvega res razlikuje.

**Pot je v naslovu** (`?noge=trip:od_seq:do_seq;…`), ne v seji: kdor jo pošlje, pošlje pot, ne svojega brskalnika. `trip_id` LPP nosi navpičnice → `encodeURIComponent`; ločnica se bere **z desne** — sicer se id z dvopičjem razlomi na napačnem mestu.

**`date` = prometni dan predloga, `dan` = dan vprašanja** (23. 9. 2026). Pred 04:00 iskanje bere tudi včerajšnji prometni dan (`pot.NOCNI_S`) — IC 350 ob 00:05 je včerajšnji. Povezava je nosila dan vprašanja, podrobnosti so pokazale **jutrišnjo** vožnjo ob isti uri. Zdaj vsak predlog nosi `datum`, podrobnosti `zivo` (ali odštevati in osveževati zamude) — prej je stran sklepala iz „dan je danes". Glava kaže koledarski dan odhoda, ne prometnega.

**Kartica predloga je povezava, zato klik ne izbira.** Pot na zemljevidu seznama se pokaže ob dotiku ali fokusu; na telefonu ne naredi nič v napoto, na namizju ostane predogled.

**Predlogi poti so ločeni po omrežju in izračunani, ne ugibani.** Avtobusna stran jih doslej ni imela — prazen obrazec brez izhodišča; železniški seznam tja ne sodi, ker se „Ljubljana“ na avtobusnem omrežju razreši drugam. Avtobusnih šest = **šest najpogostejših relacij po številu voženj** v zajetem voznem redu (4. 9. 2026): Grosuplje ↔ Ljubljana Železna 194×, Ljubljana AP → Kamnik 189×, → Škofja Loka 186×, → Kranj AP 129×, → Vrhnika Voljčeva 118×. Preverjeno: vsa imena se razrešijo z `resolve_station()`, predlog da rezultat (Ljubljana AP → Kamnik: 84 neposrednih).

Žetone riše `popularChipsHtml()`, poslušalca pripne `wirePopularChips()` — oboje skupno. Prej poslušalec pripet samo v železniški veji, zato avtobusna žetonov ne bi imela, tudi če bi jih izrisala.

**Pregled pod iskalnikom = žetoni + (pri vlakih) povezava na ovire, nič drugega.** Kartica „Kako vozijo vlaki/avtobusi" (mediana končne zamude dneva, razredi) odstranjena 29. 9. 2026 z `/api/overview*` in `stats.day_summary`. Ob 00:03 je kazala „avtobusi +839 min": tri vožnje, vse s feedovo zamenjavo prometnega dne (14–22 h) — dnevni povzetek edini ni imel stropa `MAX_REALNA_ZAMUDA_S`, avtobusna kartica pa ni brala `yesterday`, ki ga je strežnik pošiljal od 3. 9. Isti razlog kot na domači strani: tudi pravilna številka potniku ne pove, kdaj mu pelje. Število ovir iz `/api/health`; doda se le, če je pregled še na zaslonu, sicer bi prepisal medtem sproženo iskanje.

**Iskalnik si zapomni vse poti, ne zadnje.** Dva seznama, ker dve vprašanji: `kajros:fav` = „to je moja pot", človek pove sam (zvezdica); `kajros:recent` = „tu sem pravkar bil", napiše se sam (šest zadnjih). Oba v žetonih **pod iskalnikom**, ne v pregledu — pregled prva poizvedba pobriše prav takrat, ko bi seznam rabil za naslednjo. Prazno polje za postajo ob dotiku ponudi imena iz teh poizvedb; drugega ugibanja za prazno polje ni.

Oba seznama **ločena po omrežju**. Prejšnji `kajros:last` ni bil: kdor je na `/app` iskal Celje–Ljubljana, nato odprl `/app/bus`, dobil isto vprašanje razrešeno na avtobusnem omrežju („Ljubljana AP") in prazen odgovor. Zadnja poizvedba je zdaj prva med nedavnimi, svojega zapisa nima več.

Okno vožnje isto za vlak in avtobus, a govori o tem, kar je pred potnikom: besedo (vlak / nadomestni prevoz / avtobus), opozorilo in povezavo nazaj izbere iz `network`. Pri avtobusu z več vožnjami na isto številko linije je v naslovu `?trip=<id>`.

**Vstopna stran preklopa preprosto/napredno nima namenoma.** Izbira med dvema odgovoroma pri „kdaj mi pelje vlak" je sama breme: potnik ne vidi, kaj mu drugi pogled skriva, dokler ne vidi, ni razloga vklopiti. Napredno na njej se je razdelilo na dvoje, nič ni skrito: razumljivo vsakomur (**neposredno**, **načrtovano N min za prestop**, **točnih N %**, **najslabša**, koliko je zajetega) zdaj vedno vidno; ostalo s strani odšlo, ker tja ni sodilo — številka postanka, „izhodišče — feed odhodne zamude ne poroča", prevoznikova napoved (prikaz je tako ali tako ne uporablja). Preklop obdržita okno vožnje in ovire: tam gre za eno vožnjo ali eno številko, ne za izbiro poti.

Druge strani imajo preklop **preprosto / napredno**. Ni druga stran: napredni pogled = razred `is-advanced` na `<body>`, ki odkrije elemente z `adv-only` (p90, delež točnih, številka postanka, kaj pravi feed). Potnik in radovednež gledata isto vožnjo.

**Pot mora povedati, s čim greš.** `/app` je bil vlakovni samo po dogovoru, iz naslova nevidno; zdaj `/app/train`, `/app` preusmerja (308). Okno vožnje ima obe poti: `/app/train/{no}` in `/app/bus/{no}`. Streženo z isto predlogo, a naslov ne sme lagati — `/app/train/25` za mestno linijo 25 = napačen naslov, ki ga bo nekdo delil naprej; strežnik pogleda `trip.network` in preusmeri (307).

**Za nadomestni prevoz SŽ feed ne poroča zamud — nikoli.** Izmerjeno 4. 9. 2026: 56 voženj `BUS …` v voznem redu, **0 meritev** v petnajstih dneh; pri pravih vlakih pokritost **99,5 %** (601 voženj v voznem redu, 598 zajetih). Skupna železniška pokritost je videti kot 91 % samo ker nadomestne prevoze šteje zraven.

Zato okno vožnje pove „feed **ne poroča zamud** — velja vozni red“, ne „še ni nobene meritve“. Beseda **„še“** obljublja številko, ki ne pride, potnik čaka zaman. Pravilo v `train.jeNadomestni()`.

**Vrste vlaka ostanejo kratice, ker imena ni.** Statistika piše „AVT“ in „MO“ brez pojasnila — avtovlak na bohinjski progi (10 voženj) in Maribor–Šentilj (20). Polnega imena ne moremo pripisati: `route_long_name` v GTFS **prazen pri vseh 2 571 progah** (izmerjeno 2. 9. 2026); ugibanje pomena kratice = domneva zapisana kot dejstvo.

Konkretna posledica manjka iz pisma DUJPP-u (`docs/pismo-podatki.md`, nit #6). Če polje kdaj dobimo, eno mesto, kjer se takoj pozna.

**Stran ovir kaže tudi napovedane, ne le veljavnih.** Doslej je `active()` filtrirala `start_ts <= zdaj` in stran je molčala prav o tem, čemur je namenjena: izmerjeno 4. 9. 2026 **16 veljavnih in 32 še nezačetih**, najbližja že naslednji dan. Potnik, ki v četrtek gleda sobotno pot, o sobotnem nadomestnem prevozu ni izvedel nič.

Zdaj zraven tiste do **14 dni naprej** (`alerts.NAPOVEDANO_DNI`), z žetonom „napovedano“, razvrščene za veljavne. Števec pove oboje: „16 veljavnih, 24 napovedanih“ — „40 veljavnih“ bi bilo neresnično.

**Števec na vstopni strani ostane pri veljavnih** (`active_count`): piše „veljavnih obvestil“, napovedana bi besedo naredila neresnično. Zato `/api/alerts` privzeto vrne oboje z zastavico `napovedana`, števca ne.

**Nadomestni prevoz pove „po voznem redu“, ne „brez podatka“.** Velja na odhodni tabli in v iskalniku, kot že v oknu vožnje: feed zanje ne poroča nikoli (56 voženj, 0 meritev v petnajstih dneh), „brez podatka“ obljublja številko, ki ne pride. Ob žetonu stoji razlog — brez njega je „po voznem redu“ videti kot izbira prikaza, ne dejstvo o viru.

**Ovire so samo pri vlakih.** `SZ-OVIRA` obvestila = dela na progi, zapore tira, nadomestni prevozi SŽ; za avtobuse takih obvestil ni, povezava tja bi obljubljala podatek, ki zanje ne obstaja.

**Omrežji sta ločeni tudi na pogled.** V glavi segmentni preklop `Vlaki | Avtobusi`, ne dve povezavi med štirimi; avtobusna stran ima svojo barvo (`body.net-avtobus` prestavi `--accent` na zeleno, isto kot vozila na zemljevidu). Doslej trenutna stran samo izpuščena iz seznama povezav, razlika nikjer vidna — kdor je na `/app/bus` iskal „Ljubljana", dobil postajališče LPP in ni razumel zakaj.

**Eno ime v naslovu, en pomen.** Ura na odhodni tabli = `ob`, ne `from`: `from` je na isti strani že izhodiščna postaja iskanja A–B, `restore()` ga tako bere. Ko sta bila isto ime, je deljena povezava na tablo z uro (`?station=Ljubljana&from=08:00`, jo je tvorila aplikacija sama) vpisala **„08:00“ v polje OD**. Ni bilo takoj vidno, ker se je odprla tabla — pokazalo se šele ob preklopu na zavihek Od–do. `/api/departures` ostane pri `from`; dvoumnost je bila v naslovu strani, ne v API-ju.

Ista družina kot pravilo o mešanju `?` in `:ime` v SQL: ena reža, dva pomena.

**Iskanje na vstopni strani sproži samo gumb.** Izbira postaje iz predlogov ne išče: človek pogosto popravi še drugo polje ali dan, vsak vmesni ugib = zahteva za odgovor, ki ga nihče ni prosil. Izjema: poizvedba iz naslova (deljena povezava) — odgovor je tam prav to, po kar je človek prišel.

**Avtobusna tabla ima smer: stran ceste** (22. 9. 2026). Mestno postajališče je dvoje, tabla kazala oboje: Bavarski dvor 53 odhodov v pol ure, polovica z druge strani ceste. Na imenih z vsaj dvema postajališčema je **89 %** avtobusnega prometa, torej ni posebnost LPP. Nad tablo gumbi „obe · → Tobačna · → Vič Glince · Jadranska“; oznaka = **naslednja postaja**, ker jo potnik vidi na postajališču in je kratka (cilji na hubu deset različnih). Imen se ne sklanja — „→ Tobačna“, ne „proti Tobačni“.

* **Strani izračuna strežnik** (`journey.smeri_postaje`): smer vožnje do naslednjega postanka in lega. `stop_id` sam tega ne pove, ker ima vsak vir svojega (Bavarski dvor: dva LPP, dva IJPP, strani dve). Od 4 126 imen z dvema postajališčema je smer pri 3 596 nasprotna (> 120°), pri 65 podobna (< 45° — enosmerne ulice, kjer izbire ni). Meji: 60° in 250 m; IJPP-jev Bavarski dvor 149 m od LPP-jevega z isto naslednjo postajo, kraji z istim imenom kilometre narazen.
* **„Proti centru / iz centra“ (Trola, ljbus.cc) zavrnjeno**: v središču (Bavarski dvor, Konzorcij) nima pomena, medkrajevna postajališča bi rabila drugo pravilo.
* **Filtrira strežnik, ne brskalnik.** Tabla ima mejo 150 vrstic; rezana po obeh straneh bi izbrano smer končala sredi okna, glava bi trdila „6 h naprej“ (Hajdrihova, 14. 9. od 07:00: 150 skupaj, 79 v eni smeri). Preklop vseeno takojšen — iz cele table se izbrana stran pokaže takoj, nato pride prava. Osvežitev na 30 s odtlej **tiha** (`searchBoard(push, tiho)`): prej je tablo za hip zamenjala z „iščem …“ in stran skočila na vrh.
* **Izbira se zapomni po pravem imenu postajališča** (`kajros:smer`), ne po vnosu — „hajdri“ in „Hajdrihova“ = ista tabla. Ključ, ki ga strežnik ne pozna več, se tiho pozabi, tabla spet cela. Ključ = katerikoli `stop_id` smeri, zato ga ne podre, če ob uvozu prevlada drugo postajališče.
* Odhodi/prihodi odtlej **„Tabla“**, ne „Smer“: dve izbiri z istim imenom na enem zaslonu = uganka.

**Današnja tabla je po pričakovani uri, ne po voznem redu** (25. 9. 2026). Po voznem redu je na Bavarskem dvoru na vrhu stal LPP 14 z 12:46 in +49 min, pod njim deset že odpeljanih, nato mešanica svetlih in temnih vrstic: odpeljanost po pričakovani uri, vrstni red ne. Poudarek „čez 20 min“ je dobila prav ta vožnja, LPP 13 pa peljal čez dve. Zdaj: odpeljane pod „pokaži N prejšnjih“ (kot pri zvezah, odprtost preživi osvežitev), nepotrjen odhod nad naslednjo, poudarjena prva po pričakovani uri. Vozni red ostane prečrtan v vrstici. Drug dan po voznem redu — tam „zdaj“ ni. Pristajalna stran postaje razvršča enako (`pristanek._po_pricakovani`) in **izpiše pričakovano uro**, voznoredno prečrtano nad njo (`pristanek.ura_odhoda`) — z voznoredno so ure tekle nazaj (17:55, 17:57, 17:50 z +10, 18:15). API in widget ne, tam vrstni red še voznoredni.

**Prestop gre v iskalniku nad neposredne, kadar prej pripelje** (25. 9. 2026). Ljubljana → Maribor ob 17:31: poudarjen na vrhu LPV 2002 ob 20:50 s prihodom ob 23:26, zveza s prestopom ob 17:50 pa pripeljala ob 20:34, skoraj tri ure prej — pod njim. Strežnik prestope, ki jih kakšna neposredna prekaša, že izloči, zato je vsak preostali prava izbira. Kadar najzgodnejši prihod s prestopom prehiti naslednjo neposredno (ali neposredne danes ni več), je razdelek „Z enim prestopom — prej na cilju“ prvi, pod njim „Neposredno“. Samo danes; drug dan seznam = vozni red.

**Odhodna tabla združi sezonske različice.** Devet vlakov ima dva ali tri tripe z različnimi obdobji veljavnosti; kadar oba veljata isti dan, bila ista vožnja na tabli **dvakrat**. Izmerjeno na Bled Jezeru 3. 9. 2026: LP 4208 ob 09:13 v dveh vrsticah, ena brez meritve, ena s +6 min — potnik vidi dva vlaka, kjer je en.

Ključ združevanja = **fizični odhod** (številka, voznoredna minuta, smer), ne `trip_id`. Obdrži se vrstica, ki ima kaj povedati: najprej izmerjeno, nato kakršnakoli vrednost, sicer prva. `resolve_trip()` isto rešuje za okno vožnje, a po dnevih veljavnosti — na tabli bolje po podatku, ker feed poroča za trip, ki dejansko vozi.

**Nakup vozovnice: povezava na `eshop.sz.si`, brez relacije.** V oknu vožnje in pod rezultati iskalnika, **samo pri železnici** (nadomestni prevoz SŽ vključno — `mode = bus`, a `network = zeleznica`; avtobusne vozovnice SŽ ne prodaja).

Relacije v naslov **ni mogoče podati**, preizkušeno v dveh smereh:

* `eshop.sz.si` = `POST` z internimi ID-ji postaj (`TravelFromId`); GET parametri se tiho ignorirajo — `?TravelFrom=Ljubljana&TravelTo=Koper` pusti polji prazni.
* `potniski.sz.si/vozni-redi-results/` GET **sprejme** (`entry-station` = UIC koda brez predpone `79`, Ljubljana 7942300 → `42300`), a **gumb za nakup pelje v trgovino brez prenesene relacije** — ovinek brez koristi. Ugotovil uporabnik; z naše strani se ne da preveriti, ker je `potniski.sz.si` za Cloudflarom (403 tudi iz brskalnika brez zaslona).

Zato povezava vodi na trgovino in **to tudi piše** („relacijo vpišeš tam“). Obljubiti izpolnjeno pot = laž, ki bi jo potnik odkril šele tam.

**Da mi na `potniski.sz.si` ne moremo, samo po sebi povezave ne bi oviralo** — odpre jo uporabnikov brskalnik, ne naš strežnik. Ta razloček je bil enkrat spregledan in stran prehitro zavržena; zavrnjena zdaj iz drugega razloga.

## Pristajalne strani so za iskalnik in nimajo JS

`/vlak/{od}/{cilj}`, `/postaja/{ime}` in kazali `/postaje` · `/postajalisca`. Zakaj obstajajo in po čem so izbrane: `kajros/pristanek.py`; številke v `docs/MERITVE.md`. Tu: kar velja za izris.

* **Brez JS — to je ves njihov razlog.** Kar bi se dorisalo v brskalniku, `/app/*` že ima. Zato tudi ni žetonov iz `common.js` — zamuda = navaden `<span>`, pravilo o besedi in razredu pride s strežnika (`stats.opis_zamude()`), ne iz predloge.
* **Razred zamude mora premagati okvir, v katerem stoji.** `.odhodi td` in `.stevilo b` sta specifičnejša od enega razreda in sta barvo tiho povozila — „+15 min" je bil bel. Zato `.pristanek .z-…`.
* **Imen postaj se ne sklanja, tudi tu ne.** „ob prihodu v Ljubljana" je bilo na prvem posnetku; zdaj „običajna zamuda ob prihodu" (cilj je v naslovu) in „Prva ob 14:23, **smer** Dobova".
* **Ob številu pravilna oblika** (`pristanek.stevnik()`): 1 vožnja, 2 vožnji, 3 vožnje, 5 voženj. Odločata **zadnji dve števki** — 21 = „enaindvajset voženj", 101 = „sto ena vožnja".
* **Vožnja brez meritve ne dobi pomišljaja, ampak zgodovino.** „običajno +13 min", sivo in z besedo: brez nje je stolpec pri jutranjem vlaku prazen, čeprav o njem vemo osemnajst prejšnjih voženj. Vrednost **ni napoved za ta dan**; stran jo tako tudi imenuje (`stats.typical_at_stops()`).
* **Vsaka številka nosi vzorec in čas izračuna** — „na 734 vožnjah od 21. 8. do 17. 9., preračunano 17. 9. ob 03:31". Velja povsod, kjer je agregat čez vso zgodovino.
* **Kar ni v kazalu, dobi `noindex, follow`.** Prostor naslovov je neskončen (91 000 parov postaj pri avtobusih), iskalnik ga bo prehodil. **Zato je izbor kazala ključen**: do 29. 9. 2026 je bil po številu voženj in `noindex` sta dobili Ljubljana → Maribor in → Koper, najbolj iskani relaciji. Zdaj po `pristanek._teza()`; pravilo ne sme nazaj na število voženj. Naslov se pred izrisom **zloži v našo obliko in preusmeri s 301**, sicer sta `/postaja/Celje` in `/postaja/celje` dve strani z isto vsebino.
* **Drobtine (`BreadcrumbList`) in `WebSite` v JSON-LD** se pišejo s `tojson`, ne ročno — imena postaj so vnos iz GTFS.

## `/primerjava`: druge strani po njihovih besedah

Nastala 29. 9. 2026, ker AI na vprašanje „najboljša stran za zamude“ odgovori iz strani, ki primerjajo. **Pošteno ali nič**: o drugih samo to, kar povedo same (naslov, opis, stran „o projektu“, zemljevid strani), z datumom pregleda na strani; nič „samo pri nas“, česar ni mogoče dokazati; uradna stran SŽ prva, ker ima prednost. Lažne ocene in skrito besedilo za AI so zavrnjeni — v EU prepovedani (direktiva 2019/2161), in skupnost je majhna. Ob spremembi pri drugih se popravi besedilo in datum. Isto velja za `Kaj je tu` na `/o-nas`: vsaka alineja mora biti res.

## `/o-nas` je zgodba v 3D, edina besedilna stran z JS (5. 10. 2026)

Izbral David: stran naj bo „povezana čez celo drsenje“, ne 3D slike, in je edina, ki sme biti razkošna; ostale ostanejo čiste. En svet in ena kamera v three.js, drsenje premika čas filma. Vir v `o-nas/` (README tam), sveženj `static/o-nas/o3.js` 733 kB (gzip 201 kB) in podatki Pogl. 3 0,94 MB.

* **Besedilo je v predlogi, ne v JS.** Iskalnik, agent (`Accept: text/markdown`) in brskalnik brez WebGL dobijo vso zgodbo in `Kaj je tu`; `.brez-3d` in `html:not(.js)` naredita iz taktov navadno stran. Oznake v prostoru so `aria-hidden`, zato jih Markdown izpusti.
* **three.js samo tu.** Za zemljevide ostane zavrnjen (`zemljevid.md`: za nekaj škatel ni vreden 172 kB), tu je ves prizor 3D. V `requirements.txt` ni nič novega: `o-nas/gradi.sh` prenese pripeta three in esbuild (preverjena po sha512), sveženj je v gitu, strežnik ničesar ne gradi.
* **Podatki Pogl. 3 so posnetek 1. 10. 2026**, ne živi. Številke v besedilu (77 vlakov, 1 106 avtobusov, IC 351 v 42 dneh) so iz istega izvoza; ob novem izvozu popravi oboje. Nalagajo se vzporedno z gradnjo sveta, prvi kader jih ne čaka.
* **Zgodba:** o avtorju samo „dijak“ (brez proge, kraja, šole in imena). Ure so ponazoritev (vozni red 7.42, vlak 7.55, +13 min). Vlak je SŽ 313 (Stadler KISS), modeliran po fotografijah; dijak ima postavo „močan“, izbrano med tremi.
* **Kar je bilo prijavljeno, da se ne vrne:** žice kot `LINES` so bile pod nadomestno meglo bele in so utripale → trak s pokritostjo; trak sijaja 1 mm nad tirnico je v daljavi migljal → sijaj v senčilniku, tirnice in pragovi z zamikom globine po plasteh; sekundni kazalec je ob drsenju skočil nazaj → švicarska podrejena ura z minutnim impulzom iz drsenja (`uraKorak`); kamera je med dvema ključema zanihala pod peron → tangente zlepka omejene (Fritsch–Carlson v `zlepek`); naslovi so bili ob svetlem slogu gostitelja temni → barve na `body.o-nas`.
* Pred objavo spremembe poglej posnetke telefona in namizja z `o-nas/posnetek.py` (čas filma `T=`, lastna kamera `P=`); `preveri.sh` vidi le, da stran naloži brez napake.

## Besedilne strani govorijo potniku, ne razvijalcu

Prijavljeno 12. 9. 2026 na `/android` in `/zasebnost`: obe „naklada[li] in posreduj[ali] zelo tehnične podatke“. Sprožilni primer:

> Lastna lega dela povsod. V brskalniku po domačem omrežju (`http://192.168…`)
> je ni, ker to ni varen kontekst.

To opisuje **razvojno okolje**, ne lastnosti aplikacije.

Prvi popravek je take odstavke le zložil v `<details>` — **zavrnjeno**: „noben produkt nima tako podrobno napisanih stvari, to naj bi bilo samo za naju“. Zloženo ni skrito; isto besedilo z enim klikom več.

Pravilo: kar zanima naju, **ne gre na stran v nobeni obliki**. Mesto: `docs/` in `.claude/rules/`. Tako odpadli: licenčna politika trgovin, kontrolna vsota SHA-256, `sha256sum`, formula `blake2s(sol ‖ IP ‖ UA)`, doba hrambe, oblika poti v števcih, razlaga omejevanja neželene pošte.

Ostane **obljuba, ne dokaz**: „naslova IP ne shranimo nikoli“ zadošča, „ker je sol zavržena ob polnoči“ je za naju. Skladnost z `obisk.py` in `stik.py` velja naprej — krajše ne sme pomeniti manj resnično.

Izrisana stran: `/android` 8,5 → **3,0 kB**, `/zasebnost` 9,6 → **4,1 kB**.
