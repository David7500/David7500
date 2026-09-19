---
paths:
  - "kajros/pristanek.py"
  - "kajros/static/pristanek.css"
  - "kajros/static/connections.js"
  - "kajros/static/connections.css"
  - "kajros/static/home.js"
  - "kajros/static/home.css"
  - "kajros/templates/**"
---

# Strani in kaj je na njih

## Strani

**Hitrosti po odsekih ni več nikjer.** Bila je isti podatek v drugi enoti,
zložen v zaprt `<details>` na dnu okna vožnje. Tu je nekaj časa pisalo, da
`/api/speeds` in `stats.segment_speeds()` ostaneta, „ker ju rabi izvoz in
mreža razdalj" — **to ni držalo**: `kajros export` zapiše `network.geojson`
in `stations.json`, oba iz `network_geojson()`, in `segment_speeds()` ni
klical nihče. Odstranjena sta (45 + 4 vrstice); v zgodovini sta, če bi kdaj
zares zatrebala. Skupaj z njima je odpadel še `/api/trains` s
`stats.trains()`, ki ga prav tako ni klical nihče.

**`/app/statistika` odgovarja na „kdaj se splača potovati", ne „kakšna je
statistika".** Stran je bila prej odstranjena do prenove; vrnjena je s tem
vprašanjem, ker je edino, ki ga potnik res ima. **19. 9. 2026 spet umaknjena**
(„v taki obliki skoraj neuporabna"): ploščica na domači strani je odšla, pot iz
zemljevida strani, stran ima `noindex`. Stran in endpointa ostanejo do prenove. Na vrhu je ena poved
(najboljša in najslabša ura), pod njo razrezi po uri, dnevu v tednu in vrsti
vlaka, na dnu pa dan za dnem, ki je `adv-only`.

Tri pravila, ki so se pokazala šele na posnetku prve različice:

* **Merilo stolpcev postavijo samo vrstice z dovolj vzorca** (`MIN_VZOREC`,
  30 voženj). Prva različica je pustila nočno uro z 13 vožnjami in mediano
  24 min, da je določila merilo — cel dan se je stisnil v pahljačo po dve
  piki. Vrstica, ki ji ne verjamemo dovolj za naslov, ne sme voditi slike;
  presežek se odreže na 100 % in dobi znak `›`.
* **Število meritev ostane vidno tudi na telefonu.** Prvi poskus ga je tam
  skril („širina je dragocenejša") — a telefon je glavna naprava in prav tam
  bi „sreda je najhujša" ostala brez vzorca. Skrči se ime, ne vzorec.
* **Ure so po POSTANKU, ne po odhodu vožnje.** „Ura odhoda" odgovarja na
  drugo vprašanje, kot ga potnik ima: vlak, ki odpelje ob 05:00 in nabira
  zamudo do 09:00, jo v tistem rezu vso pripiše peti uri, ko na omrežju še ni
  bilo nič narobe. Izmerjeno na železnici: ob 04:00 da rez po odhodu **4 min**,
  rez po postanku **0 min**; ob 23:00 **10 min** proti **3 min**. Vzorec je
  ob tem desetkrat večji (ob 06:00 4 485 postankov proti 367 vožnjam), zato
  nobena ura ne pade pod prag. Polje je `by_stop_hour`; `by_hour` ostaja v
  API-ju in je še vedno po vožnji.
* **Ista meja velja za sliko, ne le za naslov.** Prva različica je merilo
  stolpcev postavljala po vzorcu (≥ 30 postankov), zato so ga postavljale
  nočne ure: 02:00 s 6 min in 115 postanki je bila najdaljši stolpec, dnevne
  ure pa so se stisnile v enako dolge palice. Kar ne sme voditi povedi, ne sme
  voditi niti slike. Pri **vrstah vlaka to NE velja** — EN s 46 vožnjami je 2 %
  prometa in hkrati resnična ugotovitev (nočni vlak, ki vedno zamuja), zato je
  merilo prometa vklopljeno samo pri urah (`poPrometu`).
* **Naslov primerja samo ure z rednim prometom** (`DELEZ_PROMETA`, 25 %
  postankov najprometnejše ure). Brez tega je odgovor „ob 03:00 vlaki zamujajo
  0 min" — resničen, a za izbiro poti neuporaben. Prag je izmerjen, ne izbran:
  delež pade s 34 % (04:00) na 4,9 % (03:00) in z 39 % (22:00) na 21,6 %
  (23:00), torej je prelom čist.
* **Blok po dnevu v tednu sam pove, kdaj mu ni za verjeti.** Pri manj kot
  štirih ponovitvah vsakega dne (28 dni zajema) podnaslov to napiše z
  izračunano številko, ne z občutkom.

* **Lestvica najhujših nosi sidro čez vse vožnje.** Ta razrez je urejen
  padajoče, zato je njegova prva vrstica najhujša in ne tipična — brez
  primerjave se „EC 211 · 46 min“ bere kot opis omrežja. Mediana vseh
  železniških voženj je **3 min**, p90 20 min, 60 % jih konča v petih
  minutah (6 472 voženj); pri avtobusih 1,6 min in 74 % (38 272).
  Zato uvodna poved doda „Čez vse vožnje je mediana …“, podnaslov lestvice
  pa pove „najhujši, ne tipični“.

  To ni domnevana zmeda: prvi, ki je `kajros stats` prebral kot „vlaki
  zamujajo 46 minut“, je bil avtor te kode, ki je imel poizvedbo pred sabo.
  Potnik nima niti te prednosti.

  Polja so `median_s`, `p90_s` in `on_time_share` v `breakdowns()`; računajo
  se iz vrstic, ki jih razrezi tako ali tako berejo, torej brez nove
  poizvedbe in brez agregata v zahtevi.

  **Ob spremembi polj povečaj `stats.SUMMARY_VERSION`.** Povzetek je
  shranjen v `povzetek` in velja 36 ur; brez tega bi predpomnilnik stregel
  staro obliko, stran bi novo polje izpustila in videti bi bilo, kot da
  sprememba ne dela. Točno to se je zgodilo pri `median_s`.

## Domača stran je razcepišče, ne nadzorna plošča

**Živih številk tam ni** (odstranjeni 12. 9. 2026 na prijavo). Bili sta dve:

* „danes običajno: vlaki +2 min · avtobusi +1 min" — vsak dan skoraj ista
  številka, torej ne spremeni ničesar, kar bo človek na tej strani storil;
* števec vozil „na poti" na vsaki kartici — podatek o omrežju, ne o njegovi
  poti.

Z njima sta odpadli **dve zahtevi od treh** (`/api/overview` in
`/api/overview/bus`, najdražji na strani, ki je samo razcepišče). Ostane
`/api/health` za število ovir na ploščici. Obseg zajema („zajetih N meritev v
M dneh") je bil v nogi do 19. 9. 2026 in je odšel — potniku ne pove ničesar.

**Noga je ena za vse strani** (`_noga.html`, slog v `base.css`). Stik, „o
nas" in podpora so gumbi — prej so bili stavki v odstavku drobnega sivega
besedila in jih je bilo treba iskati. Pod njimi postaje, postajališča,
Android, zasebnost (edina pot do kazal pristajalnih strani poleg sitemapa) in
ena vrstica navedbe vira, ki je pogoj CC BY-SA. Izbirniki so `.noga .x`, ker
`.besedilo p` / `.besedilo a` sicer povozita razmik in barvo — to se je
pokazalo na prvem posnetku. Karta, okno vožnje in pot noge nimajo: so
celozaslonske aplikacije.

**Podpora (`/donacije`) pelje na `ko-fi.com/kajros`** (odprto 19. 9. 2026,
PayPal Business na ime „kajros“, da donator ne vidi lastnikovega imena).
Naslov je privzetek v `config.py`, ne v enoti, ker ga agent tam ne more
pisati. Prazen `KAJROS_DONACIJE=` skrije vse: pot je ploščice na domači strani (na mestu nekdanje „Kdaj potovati") in gumba v
nogi ni: prošnja brez naslova, kamor bi denar šel, je slabša od nobene. Stran
pove ime ponudnika ob gumbu, ker gumb pelje s strani.

**Povedi so pisane, kot se piše, ne kot se govori.** „Kdaj ti pelje in koliko
zamuja" in „kje je zdaj kaj" sta bili prijavljeni kot stavka, ki se v
slovenščini tako ne uporabljata; zdaj „Odhodi in zamude slovenskih vlakov in
avtobusov" in „kje so vlaki in avtobusi ta trenutek". Isto velja za naslove v
zavihku brskalnika: „kajros — vlaki: odhodi in zamude", ne „kdaj mi pelje
vlak".

**Domača stran so ploščice** (izbrano 14. 9. 2026 med petimi osnutki,
preverjeno v telefonski širini). Dve zavrnjeni različici pred tem: kartice z
ikonami in prelivom („preveč AI generirano", „od vrat do vrat" butasto), nato
tipografske vrstice („vse isto oblikovano in dolgočasno"). Zdaj ima vsaka
izbira svojo velikost in malo sliko:

* **Budilke so prva ploščica, ne povezava.** „Budilke morajo biti takoj
  dostopne, ne da iščeš, kje so." V aplikaciji `home.js` bere
  `Kajros.seznam()`: naslednja budilka z uro zvonjenja, dnem, odštevanjem,
  odhodom z zamudo, ponavljanjem in „zvoni N min prej"; pod njo do tri druge
  s stikalom (`preklopi`). Po zvonjenju kaže odhod, isto kot widget. Uro in
  odhod izračuna Kotlin (`odhod_ms`, `vir` v `seznam()`), stran jih samo
  izpiše; aplikacija 1.0 teh polj nima in takrat velja vozni red. V brskalniku
  je ploščica povabilo na aplikacijo. V glavi drugih strani budilk ni.
* **Vlaki in avtobusi sta barvni kartici brez statistike** — število vozil in
  „običajno +2 min" sta bila odstranjena že 12. 9. in se nista vrnila.
* Ovire nosijo število veljavnih iz `/api/health` (`alerts_active`, ista
  funkcija kot na strani ovir), ker ga stran bere tako ali tako.
* Pike na zemljevidu so **slika, ne podatek**.

`home.css` rabijo tudi napaka, stik, zasebnost, `/android` in
`/brez-omrezja` (`.home`, `.home-brand`, `.home-lead`, `.more-link`) — spremembo teh razredov preveri tudi tam.

## `/app/pot` („Najhitrejša pot") — edina stran, ki se ne začne pri postaji

Potnik ve, **kje stoji**, ne pa, s katere postaje mu pelje. Zato sta vhoda dva
kraja (klik na zemljevid, lastna lega, ime postaje) in ne dve imeni, iskanje pa
teče **čez obe omrežji** — vlak in avtobus sta lahko v isti verigi. To je za
zemljevidom druga stran, ki omrežji namerno meša; zato ima `/api/stations/search`
tu `network=vse`, drugod pa ostane privzeta `zeleznica`.

**Na domači strani je NAD omrežjema, ne med „ostalim".** Je edina stran, ki
dela brez tega, da potnik ve, s katere postaje gre — torej prvo vprašanje, ne
zadnje. Ni pa tretja izbira ob vlaku in avtobusu, ampak **drugo vprašanje**,
zato drugačna kartica in ne tretja enaka; razlog za natanko dve izbiri pod njo
velja naprej.

**Iskanje postaj gre skozi kazalo, ne skozi strežnik.** `/api/stations/search`
je bil za `network=vse` izmerjeno **1,35 s** na razvojnem računalniku — okoli
pet na arwenu, in to na vsak pritisk tipke. Postaje se ne spreminjajo vsak dan:
`/api/stations/index?network=vse&koordinate=1` se naloži enkrat (323 kB, hrani
se 12 h v `localStorage`) in išče se v brskalniku z istim razvrščanjem kot na
strežniku (`iskalnikKazala()` v `common.js`). Toplo je 3,6 ms.

**Kazalo nosi tudi lego** — postajališče z **največ prometa** pod tem imenom.
Naključno izbrano bi pri „Bavarski dvor" enkrat dalo eno stran ceste in enkrat
drugo, iskanje poti od tam pa dva različna izida za isto ime.

**Predlog je vrstica, ne izpis.** Prej je vsaka noga imela svojo vrstico z
urami in postajami — štirje predlogi so dali dvajset vrstic, med katerimi ni
bilo mogoče izbirati na pogled. Zdaj troje: ure in trajanje, **veriga**
(`peš 7 › LPP 9 › 7 min za prestop › LPP 25 +2 › peš 10`) in drobno o
prestopih. Rezerva prestopa mora ostati v verigi — brez nje „1 prestop" ne
pove, ali zveza drži, in prav to je edino, zaradi česar je prestop vreden
pozornosti.

**Zemljevid gre čez celo stran**, ne čez cel zaslon — isti razlog kot pri oknu
vožnje: fullscreen skrije naslovno vrstico, gumb nazaj in vsak drug orientir,
izhod pa je tipka, ki je na telefonu ni.

**Lega se ne izmeri enkrat, ampak ji sledimo.** Prvi popravek GPS pogosto
zgreši za sto metrov in ga v naslednjih sekundah popravi, potnik pa se medtem
premika; `maximumAge` je zato **0** — brez tega brskalnik vrne do minuto star
popravek in prvi klik pokaže, kje si bil, ne kje si.

Štiri stvari, ki so se pokazale šele na zaslonu:

* **Ravna črta med postajama ni proga.** Prva različica je Grosuplje–Ljubljana
  narisala kot daljico čez pokrajino, kar trdi pot, ki je ni. Zdaj se najprej
  nariše skica, nato jo zamenja **prava trasa iz `shape`**, izrezana med
  vstopnim in izstopnim postajališčem. Hoja je črtkana in modra, vožnja polna
  in oranžna — potnik mora videti, kje ga nese vozilo in kje njegove noge.
* **Imen postaj ne sklanjaj.** „peš 7 min od izhodišča do Grosuplje" je narobe,
  „do Grosupljega" pa bi moral nekdo izpeljati — in za „Bavarski dvor" ali
  „Vič Glince" to ne bi delalo. Zato puščica: `izhodišče → Grosuplje`.
* **Kateri klik gre kam, mora biti vidno.** Prvi klik postavi izhodišče,
  naslednji cilj; katero polje je „nabito", pove barva oznake.
* **Vir hoje pride na zaslon.** Kadar usmerjevalnik ne odgovori, stran napiše
  „hoja je **ocena**" — zasilna številka je izmerjeno mediano 6 minut predolga
  in brez te besede se bere kot izmerjena.

**Pot je deljiva prek naslova** (`?od=lat,lon&do=lat,lon&ob=HH:MM`). Brez tega
je edini način, da nekomu poveš, kako priti do tebe, opis s stavki — in prav
to je stran, ki naj bi ga nadomestila.

**Polje se imenuje „Največ hoje DO POSTAJE".** Brez teh dveh besed si stran
nasprotuje sama s sabo: polje pravi 25 minut, pot „vso pot peš" pa jih ima 85.
Omejitev velja za dostop do postajališča in z njega, ne za hojo sploh — in ta
razlika je bila prijavljena kot napaka, ker je bila nevidna.

Ima tudi „po meri": 25 minut je privzetek in ne pravilo. Meji polja sta isti
kot na endpointu (3–45) — polje, ki dovoli več od strežnika, laže.

**Polje ostane, in to je izmerjeno.** Na 40 parih točk (1,5–25 km, jutranja
konica) je ura prihoda pri **vsaki** vrednosti meje enaka — mediana razlike
0 minut. Meja torej ne izbira med „hitreje" in „manj hoje", ampak med **ali
odgovor obstaja** in **koliko hodiš**: 10 min da pot v 28 % primerov s
16 minutami hoje, 45 min v 95 % s 40 minutami. Brez polja bi bilo treba
izbrati eno številko za vse, in obe skrajnosti sta slabi. Preizkušeno je bilo
tudi „iskati vedno na 45 in ponuditi tudi pot z malo hoje" — **ne gre**, taka
pot je med predlogi le v 2 primerih od 38.

Koraki izbirnika so po isti meritvi 10 / 15 / 25 / 35 / 45: pri vsakem se
delež najdenih poti merljivo spremeni (28 / 38 / 75 / 88 / 95 %).

**Ko z vozilom ni ničesar, stran pove dvoje**, ne le „ni poti": koliko traja
hoja vso pot (to je resnica, ki jo imamo) in **koliko hoje bi bilo treba**, da
bi bilo v dosegu prvo postajališče — s številko in gumbom, ki jo nastavi.
Zadnje ni obljuba: postajališče v dosegu še ni zveza, in tako tudi piše.
Zato prefilter kandidatov meri do **45 minut** ne glede na nastavljeno mejo;
sicer postajališča tik čez mejo sploh ne izmeri in te številke ni od kod dobiti.

**Zamenjava krajev in dan sta manjkala** (dodano 12. 9. 2026):

* **Zamenjava** je gumb med poljema. Pot nazaj je isto vprašanje z zamenjanima
  koncema, kraja z lego iz GPS ali s klikom na zemljevid pa ni bilo mogoče
  prepisati. Kadar je odgovor že na zaslonu, se poišče takoj — gumb, ki vidno
  stanje pusti pri miru, je videti kot okvara.
* **Dan** je polje z dvema puščicama, isto kot v iskalniku zvez. `/api/pot` je
  `date` sprejemal ves čas, stran ga ni pošiljala. Ker ima polje zdaj dve
  strani, sta slog (`.date-row`, `.day-nav`, `.day-step`) v `base.css` in
  poslušalec v `common.pripniDnevnePuscice()`; dve različici istega računa bi
  se razšli ob prvem prehodu na zimski čas. Najmanjša širina **210 px** ni
  izbrana na oko: pri 160 px je leva puščica ležala čez besedilo datuma —
  datum konča pri ~105 px, puščici zasedeta 68 px levo od koledarskega gumbka
  brskalnika, ki stoji 28 px od desnega roba.
* **Ura, ki je danes že mimo, se ne popravi tiho.** „Ob 06:00" ob treh
  popoldne je vrnilo jutranje odhode, kot da so pred tabo, in nič tega ni
  povedalo. Zdaj piše „Ta ura je danes že mimo — predlogi so za nazaj" in
  ponudi **poišči od zdaj**. Iskanje se ne premakne samo: pogled nazaj je
  včasih prav to, po kar je človek prišel.
* Sprememba dneva ali ure odgovor **osveži samo, kadar je ta že na zaslonu**;
  dokler ga ni, išče samo gumb — isto pravilo kot na vstopni strani.

**Shranjene točke („dom", „služba") ostanejo v brskalniku.** Kje kdo stanuje,
je najobčutljivejši podatek, ki ga aplikacija lahko drži, zato je v
`localStorage` (`kajros:tocke`, največ šest). Strežnik dobi samo koordinate, ki
jih poizvedba nosi tako ali tako (`/api/pot?od_lat=…`); **ime ne gre nikamor**,
tudi v naslov strani ne — sicer bi deljena povezava povedala, da je tista točka
tvoj dom. Obratno pa naslov, ki ga odpreš sam, koordinate **poimenuje**: če se
ujemajo s shranjeno točko, piše v polju „dom" in ne 46.05611, 14.50577.

Ujemanje je po razdalji (`TOCKA_PRAG`, 1e-4 ≈ 11 m), ne po enakosti: naslov
nosi pet decimalk, lega iz GPS pa vse, in dve zapisovanji istega praga bi se
razšli.

Troje, kar je pri tem odločeno:

* **Žetoni so pod obema poljema, ne enkrat na stran.** „Dom" je enkrat
  izhodišče in enkrat cilj; en sam seznam bi bil isti ugib, kot je bil klik na
  zemljevid, preden je oznaka povedala, kateri klik gre kam.
* **Zvezdica govori isto kot v iskalniku zvez** (`☆ shrani` / `★ shranjeno`):
  en gumb pove stanje in ga preklopi, križca na žetonu ni. Odstrani se tako,
  da točko postaviš in odtakneš zvezdico — dve poti do istega dejanja bi pri
  dveh poljih pomenili dvanajst gumbov za šest točk.
* **Isto ime je isti kraj.** Shranjevanje pod obstoječim imenom popravi
  koordinate; brez tega bi seznam tiho dobil dva žetona z napisom „služba".

Ime se vpraša **v strani**, ne s `prompt()`: v aplikaciji za Android
`WebChromeClient` (`Krom`) `onJsPrompt` ne obravnava, zato okna tam sploh ni in
shranjevanje bi tiho odpovedalo.

### `/app/pot/podrobno` — ista pot, razložena

Seznam odgovarja na „s čim in kdaj", ta stran na **„kako"**. Klik na predlog
pelje sem in doda dvoje, česar seznam nima:

* **prava pešpot na zemljevidu**, ne ravna črta (`hoja.pot()`, OSRM `route` z
  geometrijo). Kadar usmerjevalnika ni, se to **napiše** in nariše zračna črta;
  ravna črta brez opombe bi trdila pot, ki je ni;
* **vmesni postanki vožnje**, zaprti v `<details>` — potnika najprej zanima,
  kje izstopi, in šele potem, kaj je vmes.

**Lastna lega in izhodišče nista ista pika.** Izhodišče je bilo polna modra
pika, enaka kot lastna lega — kdor je iskal od svoje lege, je imel dve enaki
piki eno na drugi in postajališča sploh ne. Zdaj: polna modra je samo „ti",
izhodišče prazen svetel obroč, postajališče obroč v barvi vožnje, cilj polna
oranžna. Isto na seznamu predlogov (`pot.js`).

**Kompas kaže, v katero smer se obrniti.** Pojavi se z lego (gumb v kotu) in
kaže proti koncu izbranega peš koraka (privzeto do postajališča) z razdaljo.
Smer telefona bere `deviceorientationabsolute` (iOS `webkitCompassHeading`
na izrecno prošnjo iz dotika); kadar je ni, kaže glede na zemljevid in napiše
„sever je zgoraj". Pod natančnostjo GPS puščica pobledi in piše „tu si".

**Žeton zamude ob izstopu je drug od vstopnega in mora biti viden.** Vozilo
vmes rezervo porabi ali izgubi: „+1 min" nad prihodom šest minut za voznim
redom je videti kot napaka, čeprav je napoved. Zato drugi žeton na izstopni
vrstici — a samo takrat, kadar se od prvega res razlikuje.

**Pot je v naslovu** (`?noge=trip:od_seq:do_seq;…`), ne v seji: kdor jo komu
pošlje, mu pošlje pot, ne svojega brskalnika. `trip_id` LPP nosi navpičnice,
zato gre skozi `encodeURIComponent`, ločnica pa se bere **z desne** — sicer se
id z dvopičjem razlomi na napačnem mestu.

**Kartica predloga je povezava, zato klik ne izbira.** Pot se na zemljevidu
seznama pokaže ob dotiku ali fokusu; na telefonu to ne naredi ničesar, kar bi
bilo v napoto, na namizju pa ostane predogled.

**Predlogi poti so ločeni po omrežju in izračunani, ne ugibani.** Avtobusna
stran jih doslej ni imela nobene — bila je prazen obrazec brez izhodišča —
železniški seznam pa tja ne sodi, ker se „Ljubljana“ na avtobusnem omrežju
razreši drugam. Avtobusnih šest je **šest najpogostejših relacij po številu
voženj** v zajetem voznem redu (4. 9. 2026): Grosuplje ↔ Ljubljana Železna
194×, Ljubljana AP → Kamnik 189×, → Škofja Loka 186×, → Kranj AP 129×,
→ Vrhnika Voljčeva 118×. Preverjeno je, da se vsa imena razrešijo z
`resolve_station()` in da predlog res da rezultat (Ljubljana AP → Kamnik:
84 neposrednih).

Žetone riše `popularChipsHtml()`, poslušalca pripne `wirePopularChips()` —
oboje skupno. Prej je bil poslušalec pripet samo v železniški veji, zato
avtobusna žetonov ne bi imela, tudi če bi jih izrisala.

**Iskalnik si zapomni vse poti, ne zadnje.** Dva seznama, ker sta dve
vprašanji: `kajros:fav` je „to je moja pot" in ga človek pove sam (zvezdica),
`kajros:recent` je „tu sem pravkar bil" in se napiše sam (šest zadnjih).
Oba sta v žetonih **pod iskalnikom**, ne v pregledu — pregled prva poizvedba
pobriše prav takrat, ko bi seznam rabil za naslednjo. Prazno polje za postajo
ob dotiku ponudi imena iz teh poizvedb; drugega ugiba za prazno polje nimamo.

Oba seznama sta **ločena po omrežju**. Prejšnji `kajros:last` ni bil, in to
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
tako ne uporablja. Preklop obdržita okno vožnje in ovire: tam gre
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

**Za nadomestni prevoz SŽ feed ne poroča zamud — nikoli.** Izmerjeno
4. 9. 2026: 56 voženj `BUS …` v voznem redu, **0 meritev** v petnajstih dneh,
medtem ko je pri pravih vlakih pokritost **99,5 %** (601 voženj v voznem redu,
598 zajetih). Skupna železniška pokritost je videti kot 91 % samo zato, ker
nadomestne prevoze šteje zraven.

Zato okno vožnje pove „feed **ne poroča zamud** — velja vozni red“, ne
„še ni nobene meritve“. Beseda **„še“** obljublja številko, ki ne pride, in
potnik čaka zaman. Pravilo je v `train.jeNadomestni()`.

**Vrste vlaka ostanejo kratice, ker imena ni.** Na statistiki piše „AVT“ in
„MO“ brez pojasnila — to sta avtovlak na bohinjski progi (10 voženj) in
Maribor–Šentilj (20). Polnega imena ne moremo pripisati: `route_long_name` je
v GTFS **prazen pri vseh 2 571 progah** (izmerjeno 2. 9. 2026) in ugibati
pomen kratice bi pomenilo zapisati domnevo kot dejstvo.

To je konkretna posledica manjka, ki je naveden v pismu DUJPP-u
(`docs/pismo-podatki.md`, nit #6). Če polje kdaj dobimo, je to eno mesto,
kjer se takoj pozna.

**Stran ovir kaže tudi napovedane, ne le veljavnih.** Doslej je `active()`
filtrirala `start_ts <= zdaj` in stran je molčala prav o tem, čemur je
namenjena: izmerjeno 4. 9. 2026 je bilo **16 veljavnih in 32 takih, ki se še
niso začele**, najbližja že naslednji dan. Potnik, ki v četrtek gleda sobotno
pot, o sobotnem nadomestnem prevozu ni izvedel ničesar.

Zdaj gredo zraven tiste do **14 dni naprej** (`alerts.NAPOVEDANO_DNI`),
označene z žetonom „napovedano“ in razvrščene za veljavne. Števec pove oboje:
„16 veljavnih, 24 napovedanih“ — „40 veljavnih“ bi bilo neresnično.

**Števec na vstopni strani ostane pri veljavnih** (`active_count`): tam piše
„veljavnih obvestil“ in napovedana bi to besedo naredila neresnično. Zato
`/api/alerts` privzeto vrne oboje z zastavico `napovedana`, števca pa ne.

**Nadomestni prevoz pove „po voznem redu“, ne „brez podatka“.** Velja na
odhodni tabli in v iskalniku, tako kot že v oknu vožnje: feed zanje ne poroča
nikoli (56 voženj, 0 meritev v petnajstih dneh), zato je „brez podatka“
obljuba številke, ki ne pride. Poleg žetona stoji razlog — brez njega je
„po voznem redu“ videti kot izbira prikaza in ne kot dejstvo o viru.

**Ovire so samo pri vlakih.** `SZ-OVIRA` obvestila so dela na progi, zapore
tira in nadomestni prevozi SŽ; za avtobuse takih obvestil ni in povezava tja
bi obljubljala podatek, ki zanje ne obstaja.

**Omrežji sta ločeni tudi na pogled.** V glavi je segmentni preklop
`Vlaki | Avtobusi`, ne dve povezavi med štirimi, in avtobusna stran ima svojo
barvo (`body.net-avtobus` prestavi `--accent` na zeleno, isto kot vozila na
zemljevidu). Doslej je bila trenutna stran samo izpuščena iz seznama povezav
in razlika ni bila vidna nikjer — kdor je na `/app/bus` iskal „Ljubljana",
je dobil postajališče LPP in ni razumel, zakaj.

**Eno ime v naslovu, en pomen.** Ura na odhodni tabli je `ob`, ne `from`:
`from` je na isti strani že izhodiščna postaja iskanja A–B in `restore()` ga
tako tudi bere. Dokler sta bila isto ime, je deljena povezava na tablo z uro
(`?station=Ljubljana&from=08:00`, ki jo je tvorila sama aplikacija) vpisala
**„08:00“ v polje OD**. Vidno ni bilo takoj, ker se je odprla tabla — pokazalo
se je šele ob preklopu na zavihek Od–do. `/api/departures` ostane pri svojem
`from`; dvoumnost je bila v naslovu strani, ne v API-ju.

Ista družina kot pravilo o mešanju `?` in `:ime` v SQL: ena reža, dva pomena.

**Iskanje na vstopni strani sproži samo gumb.** Izbira postaje iz predlogov
ne išče: človek pogosto popravi še drugo polje ali dan, vsak vmesni ugib pa je
zahteva za odgovor, ki ga nihče ni prosil. Izjema je poizvedba iz naslova
(deljena povezava) — tam je odgovor prav to, po kar je človek prišel.

**Odhodna tabla združi sezonske različice.** Devet vlakov ima dva ali tri
tripe z različnimi obdobji veljavnosti; kadar oba veljata isti dan, je bila
ista vožnja na tabli **dvakrat**. Izmerjeno na Bled Jezeru 3. 9. 2026: LP 4208
ob 09:13 v dveh vrsticah, ena brez meritve in ena s +6 min — potnik vidi dva
vlaka, kjer je en.

Ključ združevanja je **fizični odhod** (številka, voznoredna minuta, smer), ne
`trip_id`. Obdrži se vrstica, ki ima kaj povedati: najprej izmerjeno, nato
kakršnakoli vrednost, sicer prva. `resolve_trip()` isto reč rešuje za okno
vožnje, a po dnevih veljavnosti — na tabli je bolje po podatku, ker feed poroča
za tisti trip, ki dejansko vozi.


**Nakup vozovnice: povezava na `eshop.sz.si`, brez relacije.** Je v oknu
vožnje in pod rezultati iskalnika, **samo pri železnici** (nadomestni prevoz SŽ
vključno — `mode = bus`, a `network = zeleznica`; avtobusne vozovnice SŽ ne
prodaja).

Relacije v naslov **ni mogoče podati** in to je bilo preizkušeno v dveh smereh:

* `eshop.sz.si` je `POST` z internimi ID-ji postaj (`TravelFromId`); GET
  parametri se tiho ignorirajo — `?TravelFrom=Ljubljana&TravelTo=Koper` pusti
  polji prazni.
* `potniski.sz.si/vozni-redi-results/` GET **sprejme** (`entry-station` je UIC
  koda brez predpone `79`, Ljubljana 7942300 → `42300`), a **gumb za nakup
  pelje v trgovino brez prenesene relacije** — torej ovinek brez koristi.
  To je ugotovil uporabnik; z naše strani se ne da preveriti, ker je
  `potniski.sz.si` za Cloudflarom (403 tudi iz brskalnika brez zaslona).

Zato povezava vodi na trgovino in **to tudi piše** („relacijo vpišeš tam“).
Obljubiti izpolnjeno pot bi bila laž, ki bi jo potnik odkril šele tam.

**Da mi na `potniski.sz.si` ne moremo, samo po sebi povezave ne bi oviralo** —
odpre jo uporabnikov brskalnik, ne naš strežnik. Ta razloček je bil enkrat
spregledan in stran prehitro zavržena; zavrnjena je zdaj iz drugega razloga.

## Pristajalne strani so za iskalnik in nimajo JS

`/vlak/{od}/{cilj}`, `/postaja/{ime}` in kazali `/postaje` · `/postajalisca`.
Zakaj obstajajo in po čem so izbrane, je v `kajros/pristanek.py`; številke v
`docs/MERITVE.md`. Tu je, kar velja za izris.

* **Brez JS, ker je to ves njihov razlog.** Kar bi se dorisalo v brskalniku,
  `/app/*` že ima. Zato tudi ni žetonov iz `common.js` — zamuda je navaden
  `<span>`, pravilo o besedi in razredu pa pride s strežnika
  (`stats.opis_zamude()`), ne iz predloge.
* **Razred zamude mora premagati okvir, v katerem stoji.** `.odhodi td` in
  `.stevilo b` sta specifičnejša od enega samega razreda in sta barvo tiho
  povozila — „+15 min" je bil bel. Zato `.pristanek .z-…`.
* **Imen postaj se ne sklanja, tudi tu ne.** „ob prihodu v Ljubljana" je bilo
  na prvem posnetku; zdaj „običajna zamuda ob prihodu" (cilj je v naslovu) in
  „Prva ob 14:23, **smer** Dobova".
* **Ob številu stoji pravilna oblika** (`pristanek.stevnik()`): 1 vožnja,
  2 vožnji, 3 vožnje, 5 voženj. Odločata **zadnji dve števki** — 21 je
  „enaindvajset voženj", 101 pa „sto ena vožnja".
* **Vožnja brez meritve ne dobi pomišljaja, ampak zgodovino.** „običajno
  +13 min", sivo in z besedo: brez nje je stolpec pri jutranjem vlaku prazen,
  čeprav o njem vemo osemnajst prejšnjih voženj. Vrednost **ni napoved za ta
  dan** in stran je tako tudi imenuje (`stats.typical_at_stops()`).
* **Vsaka številka nosi vzorec in čas izračuna** — „na 734 vožnjah od 21. 8.
  do 17. 9., preračunano 17. 9. ob 03:31". Pravilo velja povsod, kjer je
  agregat čez vso zgodovino.
* **Kar ni v kazalu, dobi `noindex, follow`.** Prostor naslovov je sicer
  neskončen (26 000 parov postaj pri avtobusih) in iskalnik ga bo prehodil.
  Naslov se pred izrisom **zloži v našo obliko in preusmeri s 301**, sicer
  sta `/postaja/Celje` in `/postaja/celje` dve strani z isto vsebino.

## Besedilne strani govorijo potniku, ne razvijalcu

Prijavljeno 12. 9. 2026 na `/android` in `/zasebnost`: obe sta „naklada[li] in
posreduj[ali] zelo tehnične podatke“. Primer, ki je to sprožil:

> Lastna lega dela povsod. V brskalniku po domačem omrežju (`http://192.168…`)
> je ni, ker to ni varen kontekst.

To je opis **razvojnega okolja**, ne lastnosti aplikacije.

Prvi popravek je take odstavke le zložil v `<details>` — in to je bilo
**zavrnjeno**: „noben produkt nima tako podrobno napisanih stvari, to naj bi
bilo samo za naju“. Zloženo ni skrito; je isto besedilo z enim klikom več.

Pravilo: kar zanima naju, **ne gre na stran v nobeni obliki**. Mesto za to so
`docs/` in `.claude/rules/`. Tako so odpadli licenčna politika trgovin,
kontrolna vsota SHA-256, `sha256sum`, formula `blake2s(sol ‖ IP ‖ UA)`,
doba hrambe, oblika poti v števcih in razlaga omejevanja neželene pošte.

Kar mora ostati, je **obljuba, ne dokaz**: „naslova IP ne shranimo nikoli“
zadošča, „ker je sol zavržena ob polnoči“ je za naju. Skladnost z `obisk.py`
in `stik.py` velja naprej — krajše ne sme pomeniti manj resnično.

Izrisana stran: `/android` 8,5 → **3,0 kB**, `/zasebnost` 9,6 → **4,1 kB**.
