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

## `/statistika*` — strani statistike (od 29. 10. 2026)

Načrt, odločitve in stanje: `docs/STATISTIKA.md`. Slog **A „Odgovori“** (David): kartica = vprašanje potnika, ena velika številka, trak ali stolpci, povezava naprej. Izris na strežniku, brez JS (`templates/statistika_*.html`, `_stat.html`, `statistika.css`); številke samo iz nočnih povzetkov (`stat_napovedi`, `stat_prevozniki`).
* **Kartica brez vzorca izpade** (`statistika.MIN_VZOREC` 30), ne kaže šuma. Dan z manj vožnjami v stolpcih sivo nizek: izpad zajema ni slab dan.
* **Primerjava prevoznikov** le z ≥ 1 000 vožnjami in ≥ 14 dnevi zajema v oknu (`primerljiv`); ostali „še premalo“ (Marprom, Kranj od 27. 10.).
* **Lestvica**: mestni in LPP primestni po liniji (`LINIJSKI`), ostali po šifri **in uri odhoda** (A6343 = več odhodov na dan). Enak delež loči |mediana| (−5 min na cilju je rezerva, ne točnost).
* **Prevoznikova napoved** samo, kjer jo je objavil pri ≥ 20 % pogledov (`MIN_DELEZ_PREVOZNIKA`); SŽ 0,5 % → „skoraj ne objavlja“.
* Zamuda v vrstici **z besedo**: „5,5 min prej“, „točno“ (`statistika.zamuda_min`); „v 5 min“ vedno s pragom.
* Konkurenca **po metodi, brez imen** („trenutna zamuda, prenesena naprej“); imena le na `/primerjava`.
* Barvi omrežij trdo v `.st` (`--st-vlak`, `--st-bus`): pregled kaže oboje, `body.net-avtobus` bi prebarval vse.
* V zemljevidu strani iz **shranjenih** povzetkov (`poti_za_iskalnik`), v meniju Več.
* **Vlak/linija** (`/statistika/vlak/{slug}`, `/statistika/linija/{prevoznik}/{slug}`) iz `stat_voznja`; pri malo vožnjah na dan stolpec = mediana zamude v barvi razreda (`r-…`), ne delež. Dnevi v tednu le ob razliki (≥ 10 točk ali ≥ 2 min). Medkrajevne šifre `noindex`. Okno vožnje kaže nanje v nogi (`statistika` v `/run`).
* **SŽ** (`/statistika/sz`): samo od `SZ_VODI_OD` (11. 10. 2026, naš bralec zemljevida); prehodi potnikov čez vso zgodovino (redki), kartica od `MIN_PREHODOV` 20. Vzroka odseka („dela, en tir“) ne trdimo.
* **Relacije**: avto = odsek avtoceste od priključka do priključka (stran to pove); brez `promet.sqlite` izpade, ne ničla. Poljuben par `?od=&do=` ob zahtevi (`iskanje_relacije`, ~10 ms, predpomnilnik do konca okna, `noindex`), samo brez prestopa; pod 10 vožnjami brez številke.
* **Namizje ≥ 900 px** (David: „luknje vmes“): vrste flex, ki se raztegnejo, kartice v vrsti enako visoke — ne mreža s fiksnimi stolpci (praznina pod nizkimi). Širino da razred: `st-dvojna` (graf), `st-siroka` (dolg seznam v stolpcih, besedilo). Razlaga in predlogi v dveh stolpcih (`columns`, kartica `display: block`). Namizni del na koncu `statistika.css`.
* Zavihki strani (`glava(izbrano)`) namesto povezave nazaj; nova podstran dobi zavihek ali `izbrano` starša.
* Prag nadomestila SŽ v besedilu (60–119 min četrtina, od 120 polovica; vir gov.si, SŽ): zamuda na končni postaji, ne potnikova.
* **`stat_dan` ima različico** (`STAT_DAN_VERZIJA`): nova vrsta ali pomen → povečaj; vsi dnevi znova, vrste z obrezanim virom (senca 30 dni) ostanejo.

## `/app/statistika` → 301 na `/statistika` (29. 10. 2026)

Stara „Kdaj potovati“ (umaknjena 19. 9.) je zamenjana; predloga in JS izbrisana (git). Pravila z nje, ki veljajo naprej:
* Merilo stolpcev postavijo samo vrstice z dovolj vzorca; število meritev ostane vidno tudi na telefonu — skrči se ime, ne vzorec.
* **Ure po POSTANKU, ne po odhodu vožnje** (`by_stop_hour`; ob 04:00 po odhodu 4 min, po postanku 0).
* **Lestvica najhujših nosi sidro** (mediana čez vse vožnje).
* **Ob spremembi polj povečaj `stats.SUMMARY_VERSION`** — `povzetek` velja 36 h, sicer streže staro obliko.
* Grafi brez knjižnice; na `/statistika*` iz strežnika (širina/višina v `style`).

## Domača stran je razcepišče

* **Živih številk o omrežju ni** (povprečna zamuda, vozila na poti, ovire, obseg zajema) — nič od tega ne spremeni, kar človek tu stori. Ovire (samo vlaki; 62 oseb/dan proti 1 196 na `/`) so na strani Vlaki in v oknu vožnje; na domačo samo, če zadenejo shranjeno pot (ni narejeno).
* **Noge ni nikjer**; vsebina v **meniju Več** (`_vec.html`, ⋮ desno v glavi, razen `/admin` in `/brez-omrezja`): „Podpri kajros“ (`--m-kont`), Stik, O nas, Vse postaje, Vsa postajališča, Android (v aplikaciji skrito), Zasebnost, navedba vira CC BY-SA.
  * List = `popover`, ne `<dialog>` z JS (pristajalne strani JS nimajo). Brez `popover` (pred Chromom 114) razdelek na koncu → `vec_list()` za skripti na koncu `<body>`, slog pod `@supports selector(:popover-open)`.
  * Tipka nazaj list zapre (`common.pripniMeniVec()`, vnos v zgodovino); povezava v listu gre najprej nazaj čez vnos. Poteg navzdol > 80 px zapre.
  * Gumb pripet v kot glave (pod 560 px `position: absolute`, glava `padding-right: 52px` prek `:has`).
* **`/donacije` → `ko-fi.com/kajros`** (PayPal Business na „kajros“). Naslov privzetek v `config.py`. Prazen `KAJROS_DONACIJE=` skrije vse. Stran pove ponudnika ob gumbu.
* **Povedi kot se piše, ne kot se govori** („Odhodi in zamude slovenskih vlakov in avtobusov“).
* **Naslov strani: najprej iskane besede, znamka zadnja** („Vozni red vlakov in zamude v živo — kajros“). Opis pristajalne nosi številke. Domača ima `<h1>` (`.d-geslo`).
* **Material 3 Expressive** (osnutek G, 26. 9. 2026). Zavrnjeno: kartice z ikonami in prelivom, tipografske vrstice, enako zaobljene kartice z obrobo („zgleda tako AI“).
* **Budilka = tonska kartica na vrhu, samo kadar budilka obstaja** (`--m-kont` #5a2e12, besedilo #ffdbc8, 8,8 : 1). `home.js` bere `Kajros.seznam()`: ura 40 px, dan, odštevanje, stikalo (`preklopi`), vožnja z zamudo, „Vse budilke (N)“. Uro in odhod računa Kotlin (`odhod_ms`, `vir`). Zamuda = žeton na podlagi strani (`.bud-zam`; `--d-big` na rjavem ne doseže kontrasta). Skrčena 1. 10. („preveč overwhelming“): dnevi in druge budilke so v seznamu. Vse ugasnjene → kartica ostane. Nobene → oblika „Budilke · ni nastavljenih“. V brskalniku oblika „Budilka · za Android“ (`#bud-oblika` → `/android`).
* **Vlaki in Avtobusi v razprti orodni vrstici**, ne na strani (pilula z imenom v barvi omrežja, Pot in Zemljevid ikoni, brez Domov). Okvir vrstice isti kot drugod. Teža (7 dni): `/` 1 196, `/app/bus` 644, `/app/train` 405, `/app/pot` 376, `/app/map` 189, `/app/ovire` 62.
* **„Kam greš?“** = prva pod naslovom, `/app/pot#kam` (kazalec v polju Kam). Od kod = lega sama (glej `/app/pot`).
* **Moje poti** = shranjene (`kajros:fav`, obe omrežji, največ šest) z naslednjima odhodoma in zamudo: `/api/connections` brez prestopov ali `/api/departures` (stran ceste iz `kajros:smer`), 40–90 ms, osvežitev na 60 s. „točno“ pri zaokroženi ničli; mimo šele po pričakovani uri; nepotrjen do `nepotrjen_do`; „brez podatka“ le v 30 min (`pot.BREZ_PODATKA_PRED_S`); nadomestni „po voznem redu“. Danes nič → prva jutrišnja „jutri“. Novinec dobi eno poved, kako shrani.
* **Povabilo = tiha kartica pod Mojimi potmi** („Se s tabo vozi še kdo? Pošlji mu zamude za Ljubljana → Kranj.“, `utm_source=povabilo`, `obisk._VIRI` „Povabilo“). Komu: shranjena pot z odhodom danes/jutri in kajros odprt ≥ 4 dni (`kajros:dnevi`). Kaj: pristajalna stran poti (`slug` v JS = `pristanek.slug`, 0 razlik na 5 496). **„Pošlji“, ne „Deli“** (Deli = lega); ne sistemsko obvestilo. „Ne zdaj“ 60 dni, poslano 120 (`kajros:povabilo`). `common.posljiPovezavo()`: Web Share, sicer odložišče; aplikacija od 1.13 (most 6).
* **Lega = tiha kartica pod Povabilom** („Pokaži, kje si, na zemljevidih“ · Vklopi · Ne zdaj), samo ob `stanjeLege() === "vprasaj"`: ne ob zavrnitvi v brskalniku (gumb je ne popravi), ne brez varnega konteksta, ne v aplikaciji pred mostom 7. „Vklopi“: v aplikaciji sistemsko okno (`Most.zahtevajLego`), ob trajni zavrnitvi nastavitve aplikacije; v brskalniku `getCurrentPosition`. Zavrnitev in „Ne zdaj“ 60 dni (`kajros:lega-kartica`).
* **Budilka, Zemljevid, Deli lego = ikone v oblikah** (cvet, detelja, zvezda; `r = R(1 + a·cos nθ)`), rjava, modrozelena, indigo, s podnapisom. Pritisk posvetli obliko.
* **Deli lego**: `deli.js` vrne HTML oblike v fazi `miruje`, sicer razpre kartico na **začetek** vrstice (`je-odprt` → `flex-basis: 100%; order: -1`). Nov zaslon kartico pripelje na zaslon (`naZaslon`), `scroll-padding-bottom` nad orodno vrstico.
* **Podpora = kartica cilja pod oblikami** („7 € od 30 €“, gumb na `/donacije`). `config.CILJ`, vsota iz `/api/podpora` (`donacije.cilj()`), ne iz HTML (domačo streže service worker). ✕ do novega cilja (`kajros:podpora`). Pred Playem: `android.md` („Podpora v Playu“).
* **Plavajoča orodna vrstica** (`_orodna.html`) na straneh aplikacije, ne na besedilnih in pristajalnih.

`home.css` rabijo tudi napaka, stik, zasebnost, `/android`, `/brez-omrezja` (`.home`, `.home-brand`, `.home-lead`, `.more-link`) — preveri tudi tam.

## `/app/pot` — edina stran, ki se ne začne pri postaji

Vhoda = kraja (naslov, postaja, shranjena točka, lega, klik), iskanje **čez obe omrežji** (`/api/stations/search` `network=vse`).

* **Naslovi iz našega kazala** (`naslovi.py`, `/api/naslovi`, OSM, 51 MB, 1–15 ms) — tuji geokodirnik bi izvedel, kam kdo gre. En seznam: shranjene točke, postaje (kazalo v brskalniku), naslovi (strežnik, 160 ms zakasnitve, prekinjeno ob tipki). S številko naslovi prvi. Razvrščanje po **okolici** (drugi konec, lega, sredina zemljevida). „Poišči“ brez izbire vzame prvi zadetek. Brez kazala samo postaje.
* **Vprašanje časa = prihod.** **Čim prej** (prvi = najzgodnejši prihod) ali **do ure** (prvi = najpoznejši odhod od doma, „najpozneje“, rezerva). Danes do roka ne gre → „Do 8:00 ne prideš več. Najhitreje si tam ob 8:14.“ (`ne_ujames`). Prepozna po napovedi ostane, na dnu, rdeča.
* **Prevozniki = izbira pod gumbom** (`pot.PREVOZNIKI`, `?prevozniki=lpp,vlak`; 17 od 48 poti prej ni bilo samo LPP). „LPP“ = mestni + primestni (1118); nadomestni pod „vlak“. Vsak prevoznik iz `stats.AGENCY_NAMES` ima gumb (`test_vsak_prevoznik_ima_gumb`): brez njega ostane v iskanju tudi tistemu, ki ga ni izbral. Izbira v `localStorage` (`kajros:prevozniki`), ne v naslovu. Omejitev vidna ob odgovoru („Samo LPP — poišči z vsemi“). Zadnjega ni mogoče izklopiti. Izločena vožnja prek `brez`.
* **Kolo/rolka = potrditveno polje**, 15 km/h (`kmh`); prestop ostane „peš“.
* **Postaje iz kazala v brskalniku** (`/api/stations/index?network=vse&koordinate=1`, 323 kB, 12 h `localStorage`, `iskalnikKazala()`, 3,6 ms; strežnik 1,35 s). Lega = postajališče z **največ prometa** pod imenom.
* **Predlog = vrstica**: ure in trajanje, **veriga** (`peš 7 › LPP 9 › 7 min za prestop › LPP 25 +2 › peš 10`), prestopi. Rezerva prestopa v verigi.
* **Brez podatka ≠ točno** — sivo „brez podatka“ (strežnik `brez_podatka`), samo v 30 min (prej pri 86 % voženj = šum).
* Zemljevid čez stran, ne fullscreen. Lega se sledi, `maximumAge` **0**.
* **Od kod = tvoja lega**, kadar ga ni dal naslov in ga človek ni vpisal; enkrat na ogled, samo lega ≤ 100 m (`LEGA_DOVOLJ_M`), pogled se ne premakne (`S.od.sam`).
* Ravna črta ni proga — skica, nato trasa iz `shape` med postajališčema. Hoja črtkana modra, vožnja polna oranžna. **Imen postaj ne sklanjaj** (`izhodišče → Grosuplje`). Barva oznake pove, kateri klik gre kam. Brez usmerjevalnika „hoja je **ocena**“ (zasilna mediano 6 min predolga).
* **Iskanje vidno, ker traja** (53 % nad 2,5 s, najdaljše 29 s): gumb „Iščem …“ z vrtavko, kartica z gibljivo črto, po 3 s „Še iščem …“; Enter zapre tipkovnico.
* **Pot deljiva prek naslova** (`?od=lat,lon&do=lat,lon&tam=HH:MM&dan=…&kolo=1`), današnji dan ne gre v naslov. **„Pošlji“** ob predlogih in podrobnostih (`common.posljiPovezavo`, `utm_source=poslano`): seznam pošlje vprašanje, podrobnosti pot z `date`. Besedilo `common.stavekPoti` **brez imen krajev** (kraj je lahko „dom“).
* **„do postaje največ“** (meja dostopa, 3–45). Polje ostane: ura prihoda pri vsaki meji enaka (40 parov, mediana 0), meja odloča **ali odgovor obstaja** (10 min 28 %, 45 min 95 %). Koraki 10/15/25/35/45 (28/38/75/88/95 %). „Vedno 45 + pot z malo hoje“ ne gre (2 od 38).
* **Brez vozila pove dvoje**: hoja vso pot in koliko hoje do prvega postajališča (z gumbom). Prefilter do 45 min ne glede na mejo.
* **Zamenjava krajev** = gumb, ob odgovoru išče takoj. **Dan** = polje z dvema puščicama (`.date-row`, `.day-nav`, `.day-step` v `base.css`, `common.pripniDnevnePuscice()`), min. širina 210 px. Dan in ura le pri „do ure“.
* **Danes nič več → jutrišnje** (`danes_ni`; ob 22:30 74 od 100), od polnoči brez meje hoje (`nadaljevanje=True`).
* **Ob istem prihodu prvi tisti z najpoznejšim odhodom**; prestop več mora prinesti ≥ 10 min doma (`pot.PRESTOP_VREDEN_S`). Trajanje = razlika prikazanih ur (`trajanjePrikaz`), rezerva po prikazanih urah (`rezervaPrestopa`).
* **Do 3 min poznejši prihod sme na vrh, če prihrani ≥ 5 min od vrat do vrat** (`pot.izberi_predloge`, `SKORAJ_ENAKO_S`, `PRIHRANEK_S`, prestop = 10 min), ne z > 5 min več hoje. 37 od 1 138 zamenjav. Takrat naslov ne trdi „Najhitreje“ („Skoraj najhitreje na cilju“). `ne_ujames` vzame najzgodnejši prihod.
* **Prevlada po urah na kartici** (`pot.PREVLADA_HOJA_S`): pade predlog, ko je izbran tak, ki po minuti ne pride pozneje, ne odide prej, ≤ 3 min več hoje, ne več prestopov. Naslednji odhod minuto pozneje ostane. Najzgodnejši ostane vedno.
* **Pot z manj hoje sme trajati dlje za 10 min ali prihranjeno hojo** (`pot.MANJ_HOJE_DLJE_S`).
* Zemljevid seznama zajame traso prvega, če ga človek ni premaknil (`premaknjen`). Sprememba dneva/ure/meje/kolesa osveži le odgovor na zaslonu.
* **Po iskanju se obrazec na telefonu skrči v vrstico** (`pot.zlozi()`, `.povzetek` v `base.css`): gumb, Enter, naslov; **ponovno iskanje ob spremembi ne** (zaprlo bi obrazec), vrstica se prepiše. Neznan kraj in manjkajoča ura odpreta. Namizje nima (CSS).
* **Dotik predloga = predogled, ne odpre** (David, 22. 10. 2026): kartica je gumb; predogled (`#pot-predogled`) ima na telefonu zemljevid zgoraj (`body.je-predogled`), pod njim korake na kratko (`korakiPredogledaHtml`) in tveganje. „Začni pot“ (odhod v 2 h) ali „Izberi to pot“ je pripet nad orodno vrstico. Sistemski nazaj zapre predogled (`pushState`, `vUrl` ohrani `history.state`). Druga izbrana pot vpraša „Jo zamenjam?“, razen s `?nova=1` (prišel s poti).
* **Tveganje na kartici** (`pot.pripni_tveganje`): značka `zanesljivo` / `tvegano` / `zelo tvegano` (≥ 0,9 / ≥ 0,7) z vzorcem — „prestop držal 27 od 29 dni“ (≥ 3 dni), sicer „takšen drži v 85 %“, prvo vozilo na poti „po zamudah zdaj drži v 85 %“; pri roku „pravočasno v 92 %“. Besedilo `prestopDrzi`, `STOPNJA_RAZRED` v common.js (ena govorica za seznam, predogled in pot).
* **Pri roku je prvi najpoznejši zanesljiv odhod**; naslov „Odidi najpozneje ob 06:04. Ob 06:32 je tvegano (pravočasno v 72 %).“ Brez zanesljivega: „Zanesljive poti ni — najbolj zanesljiva odide ob …“, „najpozneje“ na kartici samo ob zanesljivem.
* **Lega ob polju, ne pod obrazcem** (`povejOb`, `.tocka-stanje`; prijava 22. 10.: „nekje spodaj, težko vidno“): napredek, napaka, „Dotakni se zemljevida“. Prazno Od kod ob dovoljeni legi: „Poišči“ lego počaka (`legaV`), napis „Iščem tvojo lego …“ je v polju.
* **Shranjene točke („dom“) samo v brskalniku** (`kajros:tocke`, šest). Strežnik dobi koordinate, **ime nikamor**, tudi ne v naslov. Naslov s koordinatami shranjene točke se poimenuje. Ujemanje po razdalji (`TOCKA_PRAG` 1e-4 ≈ 11 m). Žetoni pod obema poljema. Zvezdica `☆`/`★` (beseda v `aria-label`). Isto ime = isti kraj. Ime se vpraša **v strani**, ne s `prompt()` (WebView `onJsPrompt` ne dela).

### `/app/pot/podrobno` — ista pot, razložena

* Prava pešpot (`hoja.pot()`, OSRM z geometrijo); brez usmerjevalnika se napiše in nariše zračna. Vmesni postanki v `<details>`.
* **Črta sklenjena od starta do cilja**: `hoja.pot()` doda priključek na oba konca; `common.trasa()` reže na projekciji + priključek (projekcijo < 35 m izpusti). Start in cilj = oznaki z besedo (`pkKonca()`); oznaka MapLibra ne sme dobiti `position` iz našega sloga.
* Polna modra = samo „ti“; izhodišče prazen svetel obroč, postajališče obroč v barvi vožnje, cilj polna oranžna.
* **Vodenje peš** (`pot_karta.js`): zemljevid od blizu, nagnjen, v smer hoje, lega v spodnji tretjini. Zgoraj le naslednji zavoj (ulica v imenovalniku), spodaj ostanek in **ali ujameš vozilo** (zeleno / rumeno pod 3 min / rdeče „pohiti“). OSRM `steps=true`, `hoja.navodilo()`.
  * Smer: GPS pri > 0,7 m/s, sicer kompas (`deviceorientationabsolute`), sicer smer poti; premik s prstom ustavi sledenje do „sledi mi“.
  * **Zašel**: > 35 m in > dvojna točnost, trikrat zapored → `/api/pot/hoja`, največ na 20 s. Le, ko si bil že v **35 m** od poti (s 60 m preračun med vožnjo v 69 od 70). Sicer listanje na roko (‹ ›).
  * Prihod: bližje od točnosti (≥ 15 m). `wakeLock`, zamude na 30 s, odštevanje na 5 s, tresljaj 20 m pred zavojem.
* Žeton zamude ob izstopu drug od vstopnega — pokaže se, ko se res razlikuje.
* **Povezava na okno vožnje nosi `postaja` in `date`** (brez `postaja` ni bloka „Pri tebi“; vožnja pod `MIN_RUNS_FOR_TYPICAL` = 3 dni zgodovine: ločilna vrstica „vozni red, ocene še ni“).
* **Pot v naslovu** (`?noge=trip:od_seq:do_seq;…`); `trip_id` LPP → `encodeURIComponent`, ločnica se bere **z desne**.
* **`date` = prometni dan predloga, `dan` = dan vprašanja.** Pred 04:00 iskanje bere včerajšnji prometni dan (`pot.NOCNI_S`). Predlog nosi `datum`, podrobnosti `zivo`. Glava kaže koledarski dan.
* Na podrobno vodi „podrobno“ v predogledu; pot na zemljevidu seznama ob lebdenju ali fokusu.
* **Odprta s povezavo ima „Začni pot“** (`#zacni`); izbrana pot „Nadaljuj pot“.

### Pot, na kateri si (`/app/pot/podrobno?na-poti`)

Izbrana pot ostane, dokler je ne končaš ali ne poteče — čez zaprto aplikacijo in druge strani (prijava 22. 10. 2026: na prvem avtobusu ni več vedel, kje prestopi). `NA_POTI` v common.js, `kajros:na-poti` (samo naprava): `spec` (noge, kraja, dan), `vprasanje` (rok), `predlog` (zadnji odgovor `/api/pot/podrobno`), `stanje.korak`.
* **Koraki** `korakiPoti()`: hoja, čakanje (vedno pred vožnjo, tudi brez minute), vožnja, cilj; ure z zamudami. **Korak pove lega, sicer ura, sam nikoli nazaj** (`korakNaPoti`). Na vozilu: na trasi vožnje (odmik ≤ max(35 m, točnost do 80)), po odhodu −3 min, ≥ 3 m/s ali ≥ 120 m za vstopom. Izstop: ob izstopnem počasi ali na koncu trase. Brez lege gumb „sem na vozilu“, „izstopil sem“.
  * **Vožnja za prestopom šele z dokazom** (`seVozi(…, strogo)`): ≥ 120 m po njeni trasi, ne pred njenim odhodom −1 min — lega ob prestopnem postajališču je lahko še v prvem vozilu (pregled 22. 10.: preskok na drugi avtobus pred izstopom).
  * **Cilj**: iz lege le za zadnjo vožnjo, ali z dotikom; **ura sama nikoli** (`korakPoCasu` se ustavi pred njim) — stara zamuda ob vrnitvi na stran bi rekla „na cilju si“ sredi vožnje. Lega šteje šele 30 min pred začetkom (`NP_LEGA_PRED_S`): doma zjutraj ni korak večerne poti.
  * **Brez trase lega vožnje ne dokaže** (ni zemljevida, trasa se ni naložila, strežnik je nima: `ravna`): takrat gre korak tudi po uri, „zamujeno“ se ne trdi. Trasa se nalaga tudi brez zemljevida; neuspela (brez omrežja) ne ostane v predpomnilniku in se naloži ob `online`. Med nalaganjem (`nalaga`) ura ne preskoči čakanja.
  * Ob vrnitvi na stran ura 4 s čaka osvežitev (`poUri`).
* Zgoraj kaj zdaj (`risiKorak`): „Odidi ob“, čakanje z odštevanjem, „še 3 postaje · Izstopi na X“ (postaje iz `postanki[].ll` na trasi, sicer po uri), „Na naslednji izstopi“ v poudarku in tresljaj (`NP_IZSTOP_M` 500 m), „Na cilju si“. Hoja = vodenje po pešpoti kot doslej.
* **Zamujeno** (`preveriZamujeno`): 150 s po pričakovanem odhodu, ko je vozilo z lego že za postajališčem; brez lege vozila po 300 s. Vozilo, ki po GPS še prihaja, ni zamujeno. Ponudi „sem na vozilu“ in „nova pot od tu“.
* **Prestop, ki ne drži** (`ogrozenPrestop`: rezerva pod nič ali „zdaj“ pod 0,5; le prestopi pred tabo): rdeče opozorilo, „Poišči drugo pot“ od kraja prestopa z istim rokom (`/app/pot?…&nova=1`). Tresljaj enkrat na prestop (`stanje.opozorjen`), ne ob vsaki osvežitvi.
* Vozilo trenutne ali naslednje vožnje na zemljevidu (`/api/vehicles?trip=`, `pollVehicles`); med čakanjem „vozilo je 1,2 km od postajališča“, ne „je že odpeljal“ po uri. **Kot na drugih zemljevidih** (David, 23. 10.): od daleč `voziloSvg` (`vozila3d.js`) v smeri `bearing`, od `AVTO_3D_OD` model (`plastVozila`, plast pod `k-jaz`); pilula z imenom zavrnjena.
* **Plošča se zloži** (ročaj, poteg; privzeto zložena, `kajros:na-poti-plosca`). Ročaj = vrstica „Nato … ob … v …“ s stopnjo in **puščico** v krogu (gor/dol), v obeh stanjih; črtice ni (prijava 23. 10.: ni se videlo, da se razpre). Zloženo ostanejo še vozilo z rezervo, opozorilo, stare zamude (`je-staro`), gumb koraka, „sledi mi“, ob zamujenem/ogroženem „nova pot od tu“ (`je-nujno`) in **„končaj pot“**. Razprta ima vso pot (`#koraki` se prestavi vanjo), trenutni korak poudarjen; **drsi samo seznam**, gumbi ostanejo pod njim (prej „končaj“ na dnu seznama).
* **Opomba plošče je ena**, po pomembnosti: prestop, ki ne drži › pot ni več v voznem redu (404) › napaka lege › „Brez povezave — zamude so izpred N min“ (starejše od 2 min, računano ob vsakem izrisu) › brez lege. Med hojo jo deli z vodenjem po pešpoti; svojo prepozna po `data-np`.
* Kamera: hoja kot vodenje; čakanje postajališče, ti in vozilo; vožnja za tabo (sicer za vozilom, sicer po uri), obrnjena po trasi, premik največ na 3 s. Puščica „ti“ tudi med vožnjo.
* Iz shrambe takoj, **tudi kartica s seznama** (brez postankov; prva podrobna osvežitev jo zamenja), tudi brez omrežja; nato sveže, na 30 s (`zivoZanka`; jutrišnja pot, odprta zvečer, postane živa sama). 404 (vozni red zamenjan) → „Poišči jo znova“, tudi med potjo.
* **Ista pot znova ne začne od začetka**: „Nadaljuj pot“ in „Začni pot“ v predogledu iste poti le odpreta pot; druga tekočo zamenja po vprašanju (na podrobni strani drugi dotik).
* **Konec**: „končaj pot“ v dveh dotikih (drugi „res končam?“ rdeče, `je-potrdi`); sama 10 min po cilju ali 45 min po pričakovanem prihodu, na zadnjem vozilu po napredku 2 h (`naPotiPoteklo`: ura je morda stara). Potekla pred očmi ostane na zaslonu kot končana („Nova pot ›“), skrita gre na seznam.
* **Trak na poti** nad orodno vrstico na vseh straneh z njo, razen na poti sami (`trakNaPoti` v common.js, `html.ima-pot` dvigne `--orodna-prostor`): „Izstopi: Kolodvor · LPP 6 · 7:38 · čez 6 min“, ob čakanju vozilo in postajališče, pred odhodom „Odidi ob“. Brez omrežja, iz shrambe; v predogledu skrit.

## Iskalnik zvez in tabla (`connections.*`)

Osnutek E (David, 24. 10. 2026): iskanje iz A, zadetki iz B — vse vrstice enake, naslednja le obarvana (prva „ne sme biti tako drugačna“).

* **En obrazec**: Od + neobvezni Kam. Brez Kam tabla odhodov s postaje Od, s Kam zveze. Zavihkov ni; prihodi in „od ure“ samo prek naslova (`?kind=prihodi&ob=08:00`). Dan = Danes · Jutri · koledar (eno polje `#date`, JS ga prestavi k gumbu, ki odpre `showPicker`).
* **Ura in zamuda skupaj** (David: „ni jasno, kaj je vozni red in kaj zamuda“): „čez N min“ (do 3 h), krepka ura = kdaj res pelje, „vozni red“ s prečrtano uro ob razliki, žeton z enoto. Žeton ima obliko postankov okna vožnje (`.zt`: meritev nevtralno, ocena tonsko, živo s piko, običajno črtkano). Zveza: **„vozni red 17:16 → 17:25“ vedno z urama** — prečrtano le ob živi zamudi; sama beseda je velike ure pustila nejasne. Ure iz „običajno“ ne računamo (zgodovina ni napoved).
* **Predlogi poti po omrežju**, samo dokler ni shranjenih: avtobusnih šest = najpogostejše relacije po številu voženj (preverjene z `resolve_station()`), `popularChipsHtml()`.
* **Najbližja postaja** (lega dovoljena, Od prazen): brez shranjenih kartica z obema stranema ceste in prvim odhodom z vsake (dotik odpre tablo s to stranjo), s shranjenimi tih žeton „Najbližje: Drama · 76 m“. Brez dovoljenja gumb „Najbližje postajališče“ — okno dovoljenja samo na dotik. `/api/stations/near?limit=1` po omrežju. Meja 2 km (`NAJBLIZJE_DO_M`; 95,8 % od 435 044 naslovov OSM do postajališča, 37,7 % do železniške postaje), lega ≤ 100 m (pri 100 m drugo ime v 6,1 %, pri 200 m 12,3 %). Ena natančna lega, nato GPS ugasne.
* Pri vlakih še povezava na ovire. Dnevne kartice ni (avtobusi „+839 min“ ob 00:03). Število ovir iz `/api/svezina` le, če je pregled še na zaslonu.
* **Shranjeno** (`kajros:fav`, zvezdica) = vrstice z naslednjim odhodom (`odhodiPoti` v common.js, isto kot Moje poti na domači), osvežitev 60 s; zvezdica v vrstici odstrani v dveh dotikih („odstrani?“). `kajros:recent` (šest zadnjih) samo v predlogih praznega polja. Oba **ločena po omrežju**.
* Okno vožnje isto za vlak in avtobus; besedo izbere iz `network`. Več voženj na liniji → `?trip=<id>`.
* **Preklopa preprosto/napredno ni nikjer** (David, 23. 10. 2026; zadnji `/app/ovire` 24. 10.). Ovira pokaže vrsto in vzrok (brez „neznano“) in povezavo na obvestilo SŽ; interni ključ in opravičilo z repa opisa ne.
* **Pot pove, s čim greš**: `/app` → `/app/train` (308); `/app/train/{no}` za avtobus preusmeri po `trip.network` (307).
* **Nadomestni prevoz SŽ: feed zamud ne poroča nikoli** (56 voženj, 0 meritev; pravi vlaki 99,5 %). Okno: „feed **ne poroča zamud** — velja vozni red“ (ne „še ni“); tabla in iskalnik „po voznem redu“ z razlogom. `train.jeNadomestni()`.
* Vrste vlaka ostanejo kratice („AVT“, „MO“): `route_long_name` prazen pri vseh 2 571 progah.
* **Ovire**: tudi napovedane do 14 dni (`alerts.NAPOVEDANO_DNI`) z žetonom, za veljavnimi; števec „16 veljavnih, 24 napovedanih“. Vstopni števec samo veljavne (`active_count`); `/api/alerts` vrne oboje z `napovedana`.
* **Kartica ovire** (`alerts.js`, slog E, 24. 10. 2026): vrsta = tonski žeton (dela rumeno kot ovire, nadomestni vijolično, napovedano obrobljeno), obdobje brez leta, razen ko katera meja ni letos (potem obe). Opis nad 320 znaki štiri vrstice + „Preberi vse“, vlakov 12 + „+N še“.
* **Kartica zapore pove, kaj velja danes** („danes 8.00–16.00 · velja zdaj“, sicer „danes ne velja · naslednjič …“; `zapore.kdaj`, `common.kdajZapore`). **Samo obvestila, ki jih razumemo cela** (`zapore.dopolni_ovire`). Današnje naprej, nato brez ure, nato „danes ne velja“.
* **Nadomestni pove, kje ustavi** (`nadomestni.py`, posnetek `kajros/nadomestna_postajalisca.json`, osveži `scripts/nadomestna_postajalisca.py`). GTFS ga postavi na lego železniške postaje; Ljubljana od 24. 8. peron 37–39 avtobusne. Vijolična vrstica z žebljičkom (`common.nadomestniPostanekHtml`) v iskalniku, na tabli, v oknu, v kartici postaje. Lega le po preverjanju razdalje (265 od 274).
  * `pot._nadomestna_mesta`: vstop/izstop na točko SŽ, kadar > 60 m od zapisane; peš prestop vlak ↔ nadomestni.
  * Zemljevid: vijolična bucika (`dashboard.pokaziNadomestniPostanek`).
  * Lege nadomestnega v NAP ni (en večer — ponovi, preden kaj gradiš).
  * Hitri in počasni se ločita po trajanju (`nadomestni.potek`, „vožnja 42 min · 1 postanek“).
* **Zapora tira in vlak pred njim nadomestnega ne zadeneta** (`mode = bus` preskočen v `zapore.dopolni` in oknu).
* **Ovire samo pri vlakih.**
* **Omrežji ločeni na pogled**: segmentni preklop `Vlaki | Avtobusi`, `body.net-avtobus` prestavi `--accent` na zeleno.
* **Eno ime v naslovu, en pomen**: ura table = `ob`, ne `from` (`from` = izhodišče iskanja; deljena tabla je pisala „08:00“ v polje OD). `/api/departures` ostane `from`.
* **‹ in pilula vodita na zadnje iskanje** (`common.zapomniIskanje`, sessionStorage; `history.back()`, kadar s naše strani). Pilula na iskalniku = gola pot. Pot: `kajros:pot-imena`.
* **Iskanje sproži gumb ali sprememba dneva** (David, 24. 10. 2026: Danes/Jutri/koledar išče takoj, `poDnevu`; brez Od samo izbere) in poizvedba iz naslova. Izbira postaje ne.
* **Po iskanju obrazec skrčen v vrstico** (`zlozi()`, `.pz`): le lastno iskanje ali naslov, **nikoli osvežitev**. 404 odpre. Imena se prelomijo, ne odrežejo. Na tabli „Kam?“ (fokus v Kam), pri zvezah zamenjava; pod vrstico zvez dan. **Namizje (≥ 900 px) ne skrči**: z odgovorom dva stolpca, obrazec levo, vrstica nad odgovorom.
* **Tabla po vrsti ali po linijah** (samo avtobus, privzeto po vrsti, `kajros:tabla-razvrstitev`): po linijah ena vrstica na linijo, cilj in stran ceste, „nato čez 24 in 46 min“.
* **Osvežitev zvez je tiha** (30 s): ponovi vprašanje na zaslonu, pozen odgovor ne prepiše novejšega (`zvezeSt`), odprt seznam in škatla ovir ostaneta.
* **Avtobusna tabla ima stran ceste** (89 % prometa na imenih z ≥ 2 postajališčema). Povezani segmenti „Obe · → Tobačna · → Vič Glince“ = **naslednja postaja**, brez sklanjanja.
  * Računa strežnik (`journey.smeri_postaje`; meji 60° in 250 m). „Proti centru“ kot oznaka zavrnjeno (22. 9.).
  * **Mestni LPP: dodatek „v center“ / „iz centra“** ob naslednji postaji (David, 22. 10. 2026: „kot so navajeni“). Ne računamo ga: LPP-jeva koda postajališča (`station.koda`, uvoz iz `stop_code`), liha = proti centru. **Ne v središču** (`SREDISCE_M` 800 m od Kongresnega trga): tam koda smeri ne pove (do 0,5 km 47 %, 0,5–0,8 km 63 % ujemanja po prometu; Bavarski dvor 600012 pelje na Ajdovščino), 0,8–1,5 km 100 %, dlje 95 %. Kode v nasprotju = brez dodatka. Tabla (`.smer-center`) in pristajalna.
  * **Filtrira strežnik** (meja 150 vrstic); preklop takojšen iz cele table, nato prava. Osvežitev tiha (`searchBoard(push, tiho)`).
  * Izbira po pravem imenu (`kajros:smer`, `smerIzSpomina` v common.js), ključ = katerikoli `stop_id` smeri; neznan se tiho pozabi.
* **Današnja tabla po pričakovani uri**: odpeljane pod gumbom „N prejšnjih“ (v vrstici z razvrstitvijo), nepotrjen nad naslednjo, poudarjena prva po pričakovani uri, vozni red prečrtan. Drug dan po voznem redu. Pristajalna enako (`pristanek._po_pricakovani`, `pristanek.ura_odhoda`). API in widget voznoredno.
* **Prestop nad neposredne, kadar prej pripelje** (le danes): „Z enim prestopom — prej na cilju“ prvi.
* **Postajališče čez cesto** (`blizu` v `/api/connections`, `blizuHtml`): brez neposredne vožnje modra kartica nad odgovorom („Postajališče **Pošta** je 60 m stran in od tam pelje“ / „… je 60 m od cilja in tja pelje“) z gumbom, ki zamenja Od ali Kam in išče. Mestno postajališče ima pogosto drugo ime za vsako smer (Konzorcij samo proti jugu); iskalnik veže po imenu in hoje ne pozna.
* **Tabla združi sezonske različice** po fizičnem odhodu (številka, minuta, smer); obdrži izmerjeno, nato katerokoli vrednost.
* **Okno vožnje se da poslati** („Pošlji“): stavek „RG 318 …: zamuja 23 min (zadnji podatek s postaje Trbovlje ob 07:10)“, povezava brez `postaja`; brez Web Share kopira („kopirano“ 2,5 s). Predogled nosi stanje ob pošiljanju (`api._stanje_za_predogled`, vedno „zadnji podatek“, z uro). Mestna linija brez `trip` stanja nima.
* **Vozovnica: `eshop.sz.si` brez relacije**, samo železnica (z nadomestnim). Relacije ni mogoče podati (POST z internimi ID-ji; `potniski.sz.si/vozni-redi-results/` relacije v trgovino ne prenese) — povezava pove „relacijo vpišeš tam“.
* **Ponudba „Shrani na prvo stran“**: isto iskanje znova ≥ 30 min po prejšnjem (`connections.predlagajShranjevanje`, `kajros:ponovitve`, 40 poti); „Ne, hvala“ za vedno.
* **Tiha osvežitev ob napaki poskusi znova**, stari odgovor ostane. Števec zahtev (`zvezeSt`, `tablaSt`) velja tudi v `catch` in `finally`, da napaka starega vprašanja ne vzame osveževanja novemu.

## Pristajalne strani: za iskalnik, brez JS

Zakaj in katere: `kajros/pristanek.py`, številke `docs/MERITVE.md`. Izris:

* **Brez JS** — zamuda = navaden `<span>`, beseda in razred s strežnika (`stats.opis_zamude()`).
* Razred zamude mora premagati okvir: `.pristanek .z-…` (sicer bel „+15 min“).
* Imen ne sklanjaj („Prva ob 14:23, **smer** Dobova“). Število: `pristanek.stevnik()` po zadnjih dveh števkah (101 = „sto ena vožnja“).
* Vožnja brez meritve dobi zgodovino „običajno +13 min“, sivo — ni napoved za ta dan (`stats.typical_at_stops()`).
* **Številka nosi vzorec in čas izračuna** („na 734 vožnjah od 21. 8. do 17. 9., preračunano 17. 9. ob 03:31“).
* **Kar ni v kazalu: `noindex, follow`.** Izbor po `pristanek._teza()`, **nikoli nazaj na število voženj** (takrat sta Ljubljana → Maribor in → Koper dobili `noindex`). Naslov se zloži v našo obliko, 301.
* JSON-LD (`BreadcrumbList`, `WebSite`) s `tojson`.

## `/primerjava`

**Pošteno ali nič**: o drugih le, kar povedo same, z datumom pregleda; uradna SŽ prva; nič „samo pri nas“ brez dokaza. Lažne ocene in skrito besedilo za AI zavrnjeni (direktiva 2019/2161). Isto za „Kaj je tu“ na `/o-nas`.

## `/o-nas`: zgodba v 3D, edina besedilna stran z JS

En svet in kamera v three.js, drsenje premika čas filma. Vir `o-nas/` (README), sveženj `static/o-nas/o3.js` 737 kB (gzip 204), podatki Pogl. 3 0,94 MB.

* **Besedilo v predlogi, ne v JS** (iskalnik, `Accept: text/markdown`, brez WebGL). `.brez-3d`, `html:not(.js)`; oznake v prostoru `aria-hidden`.
* three.js samo tu (za zemljevide zavrnjen). `o-nas/gradi.sh` prenese pripeta three in esbuild (sha512), sveženj v gitu.
* Podatki Pogl. 3 = posnetek 1. 10. 2026; številke v besedilu (77 vlakov, 1 106 avtobusov, IC 351 v 42 dneh) iz istega izvoza.
* Avtor samo „dijak“; ure ponazoritev (7.42, 7.55, +13). Vlak SŽ 313 (Stadler KISS).
* Ne vrni: žice kot `LINES` (utripale) → trak; sijaj 1 mm nad tirnico → v senčilniku, zamik globine; sekundni kazalec nazaj → podrejena ura (`uraKorak`); kamera pod peron → Fritsch–Carlson (`zlepek`); temni naslovi → barve na `body.o-nas`.
* **Telefon je merilo**:
  * Podrobno samo blizu kamere (`pragoviBlizu` 40 m, `kosi()` v `orodja.js`); 0,43–0,56 mio trikotnikov na kader. Preveri s `__film.info()` (`tri`, `klici`).
  * Ugasnjena luč ni skrita: nočne `visible = false`, senčilniki po prvem kadru (`priprave`).
  * Brez računanja po pikah v JS (gramoz 2 s).
  * `ogrej()` naloži vse na GPE med nalaganjem.
  * Ločljivost po času med kadroma (rAF); sence ob premiku, nad 22 ms vsak drugi.
* Ne vrni (11. 10.): velikost sveta = velikost platna (`velikostPlatna`), ne `innerHeight`; film največ 10 s/s, vožnja 7 (`HITROST`); ura na podlagi 30 px s „pouk ob 8.00 · +N min“.
* Kartice lepljive le z `overflow-x: clip` (ne `hidden` iz `base.css`); zamik `--ty`, ne `transform`.
* Pred objavo posnetki telefona in namizja z `o-nas/posnetek.py` (`T=`, `P=`).

## Besedilne strani govorijo potniku

Kar zanima naju (razvojno okolje, licence trgovin, SHA-256, formula soli, doba hrambe), **ne gre na stran v nobeni obliki** — tudi ne v `<details>`. Mesto: `docs/`, `.claude/rules/`. Ostane obljuba („naslova IP ne shranimo nikoli“), skladna z `obisk.py` in `stik.py`.

## Imena, kot jih piše LPP

„BEŽIGRAD (ŽELEZNA) - ZOO - C. STOŽICE P+R_obvoz“ → „Bežigrad (Železna) – Zoo – C. Stožice P+R (obvoz)“: `common.lepoIme` in `pristanek.lepo_ime` (filter `lepo_ime`), ista pravila. Le besede v celoti velike; kratice ostanejo. **Samo prikaz** — shranjena imena so ključi (`lpp.na_tablo` po `(linija, headsign)`).
