---
paths:
  - "sztrack/static/**"
  - "sztrack/templates/**"
---

# Prikaz: strani, zemljevidi, barve

Ciljni uporabnik je potnik z vprašanjem „kdaj mi pelje in koliko zamuja“, ne
dispečer. Vsaka odločitev spodaj ima razlog, ki je bil enkrat napaka na
zaslonu.

## Prezgodnja vožnja

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

## Zemljevid

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

## Strani

**Hitrosti po odsekih ni več nikjer.** Bila je isti podatek v drugi enoti,
zložen v zaprt `<details>` na dnu okna vožnje. Tu je nekaj časa pisalo, da
`/api/speeds` in `stats.segment_speeds()` ostaneta, „ker ju rabi izvoz in
mreža razdalj" — **to ni držalo**: `sztrack export` zapiše `network.geojson`
in `stations.json`, oba iz `network_geojson()`, in `segment_speeds()` ni
klical nihče. Odstranjena sta (45 + 4 vrstice); v zgodovini sta, če bi kdaj
zares zatrebala. Skupaj z njima je odpadel še `/api/trains` s
`stats.trains()`, ki ga prav tako ni klical nihče.

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

**Lastna lega je na obeh zemljevidih, a je nikoli ne zahtevamo sami.**
Dovoljenje, ki ga nihče ni prosil, je vsiljivo in ga brskalnik ob zavrnitvi
pogosto zapomni za vedno — zato se `locateMe()` sproži šele ob dotiku gumba.
Na velikem zemljevidu je gumb pod približevanjem (drugi klik lego skrije, kar
je hkrati „možnost prikaza" in zato ne rabi še ene izbire med plastmi), v oknu
vožnje pa v glavi okvira. Barva je `#2f7fff`: ne nastopa v nobeni lestvici in
je dovolj nasičena, da se loči od blede `#a8d8ff`, ki pomeni oceno. **Obroč
točnosti ni okras** — GPS v mestu zna zgrešiti za sto metrov in pika brez
njega trdi natančnost, ki je nima; ista napaka, kot bi bila pika vozila brez
„lega stara N s".

**Razdalja do vozila se meri po poti, ne zračno.** Obe točki — tvojo in
ocenjeno lego vozila — projiciramo na traso in odštejemo razdalji vzdolž nje
(`projekcijaNaTraso`). Zračna črta čez Golovec je pri mestnem avtobusu lahko
trikrat krajša od prave in bi obljubljala prihod, ki ga ne bo. Vozilo se vzame
na **ocenjeni** legi, isti, ki je narisana: dve številki o istem vozilu, ena s
slike in ena iz besedila, se ne smeta razhajati. Kadar je človek od proge več
kot **1 km** (`OB_PROGI_M`), računa ne delamo in to povemo — blok ali dva stran
je še „pri postajališču", čez to pa bi bila številka izmišljena. Besedilo pove
smer: „Do tebe ima še 1,2 km poti" oziroma „Tvojo lego je že prevozil — 420 m
naprej po poti"; „je 1,5 km pred tvojo lego" se bere dvoumno.

**Geste so omejene, dokler je zemljevid element strani.** Vprašanje „naj
kolešček približuje" ima odgovor „ne, dokler je to element" — kazalec zaide
čez zemljevid in stran se neha pomikati. Zato:

| | vgrajen | čez celo stran |
|---|---|---|
| kolešček | ne (Ctrl/⌘ + kolešček da) | da |
| **miška** | **vleče zemljevid** | isto |
| en prst | pomika **stran** | pomika zemljevid |
| dva prsta | pomikata in približujeta | isto |
| gumba +/− | vedno | vedno |

Resnična napaka tu **ni bila** manjkajoča povečava, ampak `dragging`: ta je
privzeto vklopljen in je en prst pomikal zemljevid namesto strani — na
telefonu se s tega okvira ni dalo odpomakniti. Dva prsta zemljevid vseeno
pomikata in približujeta, ker to opravi `touchZoom` (med širjenjem prstov
premika tudi središče); dvoprstna povečava je torej **delala že prej**,
manjkalo je nasprotno.

**Vlečenje se preklaplja po vhodni napravi, ne po napravi nasploh.** Prvi
popravek je `dragging` preprosto ugasnil in s tem vzel tudi vlečenje z miško,
ki strani ne pomika in ni v konfliktu z ničimer. `initDragPolicy()` ga zato
ugasne ob `touchstart` in prižge ob `mousedown` — prenosnik z zaslonom na
dotik mora imeti oboje, in odloči tisti vhod, ki je pravkar v rabi.
Poslušalca sta v **zajemni** fazi na ovoju: Leaflet svojega obesi na zabojnik
zemljevida in ga dobi v mehurčni, torej za nama, zato je ob njegovem branju
`dragging` že v pravem stanju.

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
