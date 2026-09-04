---
paths:
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
vprašanjem, ker je edino, ki ga potnik res ima. Na vrhu je ena poved
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
