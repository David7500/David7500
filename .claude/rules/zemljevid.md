---
paths:
  - "kajros/static/dashboard.js"
  - "kajros/static/dashboard.css"
  - "kajros/static/train.js"
  - "kajros/static/train.css"
---
# Zemljevida: veliki in tisti v oknu vožnje

## Zemljevid

* **Zemljevid = edini skupni pogled.** Vlak = krog na zadnji postaji z meritvijo; avtobus = **oblika vozila** na izmerjeni legi, raste s približkom (15–34 px), kaže v smer vožnje. Puščica premalo: pri velikem približku videti kot pika, od vlaka se ni ločila.

  **Ime postaje se pokaže na dotik, po petih sekundah odide.** Pike so bile `interactive: false` → nema točka, ni se dalo izvedeti, katera postaja. Trajne oznake na mestni liniji zakrijejo progo pod sabo. Zato klik odpre oblaček (`common.NAME_MS`), `setTimeout` ga zapre. Brez gumba za zapiranje — na telefonu manjši od prsta, zahteval bi natančnejši dotik od tistega, ki je ime odprl. Klik ustavi razširjanje dogodka, sicer na telefonu zapre spodnjo ploščo. Velja na velikem zemljevidu, na trasi izbranega vozila, v oknu vožnje. Polmer pike 3,4 namesto 2,4 px: 2,4 < prst. Veliki zemljevid (`zadetek()` v `dashboard.js`) in okno vožnje (`runImeNaDotik()`) zadeneta, kar je v **12 px** od prsta, vozilo oziroma izmerjeno lego pred postajo — MapLibre sicer zadene samo piko samo.

  **Avtobusna postajališča = svoja plast, privzeto ugasnjena.** Vseh 9 519 (211 kB z gzipom, 167 ms), zato naložijo se šele ob prvem vklopu — enako kot trase. Rišejo se **od z13 naprej**; meja izmerjena na ljubljanskem oknu 1200 × 800: z13 253, z12 600, z11 1 694 in mreža prog izgine pod njimi. Pod pragom plast ne riše nič in pove, zakaj. Železniške postaje ostanejo svoja, privzeto vklopljena plast — 271, progo prav opisujejo.

  Vsaka plast se da izklopiti posebej (vlaki, avtobusi, železniške proge, **trase vozil na poti**, železniške postaje, avtobusna postajališča, podlaga, dodatna imena), ne le avtobusi. Trase privzeto ugasnjene, naložijo se ob vklopu: gost snop črt čez vso Ljubljano odgovarja na „kod vozijo linije", ne na „kje je moj avtobus", drugo je razlog za obisk strani. 128 različnih oblik, 108 kB z gzipom.

  **Trase so lahko pretrgane; ravna črta čez pol Slovenije = laž.** V zajetem GTFS 2 185 razmikov od 4,85 milijona (0,045 %) daljših od kilometra, pri 193 oblikah; najdaljši 40 km. Uvoz traso razreže na kose (`gtfs.SHAPE_BREAK_M`), vsakega nariše posebej — 2 897 oblik da 4 732 kosov. Meja izmerjena, ne izbrana: surove točke 17 m narazen (mediana), 105 m pri 99 %, 514 m pri 99,9 %, nato skok na 22,8 km. Med pol kilometra in dvajsetimi ni ničesar. Na **poenostavljenih** točkah praga ni mogoče postaviti — dolg raven odsek videti enako kot preskok. Namesto lestvice „največje zamude" je **iskalnik vozila**: vprašanje pred zemljevidom = „kje je moj avtobus", ne „kdo danes najbolj zamuja".

  **Iskalnik najde tudi postaje** (14. 9. 2026). Kazalo obeh omrežij isto kot pri najhitrejši poti (`common.naloziKazalo()`, 12 h v `localStorage`), največ štiri postaje. Z besedo so nad vozili, s številko („25", „IC 502") pod njimi. Izbira postavi obroč in oblaček s povezavo na odhodno tablo; železniška postaja = tista v `/api/stations?network=zeleznica`.

  **Podlaga = vektorska OpenFreeMap** (22. 9. 2026, prej Esri „Dark Gray Canvas"). Odprta koda (MIT), brez ključa, registracije, omejitve ogledov; podatki OpenStreetMap. Riše jo **MapLibre GL JS 6.10, povsod sam, brez Leafleta**: veliki zemljevid (22. 9.), obe strani poti (23. 9., vodenje po pešpoti rabi kamero za hrbtom), okno vožnje (25. 9. 2026, `pot_karta.js` si delita; glej „3D od blizu“ spodaj). Leaflet in `leaflet-maplibre-gl` odšla iz repozitorija. Knjižnica gostovana pri nas (`static/maplibre-6.10.0/`, različica v **poti**, ker `maplibre-gl.mjs` uvaža sosede po relativnem imenu, Cloudflare pa statiko drži štiri ure). Tuje: ploščice in pisave z `tiles.openfreemap.org`.

  * **Slog je naš** (`static/podlaga.json`, 30 plasti), imena `name:sl` pred
    lokalnimi (Celovec, Trst, Gradec), „Četrtna skupnost“ odrezana.
    **Barve so po Slometovi podlagi** (izbrano 22. 9. 2026 med „vedno
    barvno“ in „barve šele od blizu“; vzorčeno z njegovih posnetkov): kopno
    modro-sivo `#232d39`, voda `#2b4153`, trava in gozd temno zelena, stavbe
    temnejše od kopnega. Prej je bila siva, in uporabnik je Slometovo
    ocenil kot lepšo in podrobnejšo — zato še **tiri** s pragovi (glavni od
    z12,5, stranski od z15), **poti za pesce** črtkano čez zelenice,
    igrišča, pokopališča, letališke steze in **imena pomembnih točk** (šole,
    bolnišnice, cerkve) od z16, drobno in bledo. Naša mreža prog od blizu
    pobledi (`k-proge`), da tirov ne prekrije. Napisi z `metadata.kajros:napisi = dodatni` (vasi, četrti,
    vode) so stikalo „Dodatna imena krajev“ — to so zdaj plasti v slogu, ne
    ploščice, zato se ugasnejo brez podlage. Imena ulic so v osnovi od
    MapLibrovega z14, torej **Leafletovega z15** (MapLibre ima 512-pikselne
    ploščice in je za ena nižje; vse meje v slogu so v njegovih enotah).
  * **Esri ostane rezerva** (`naEsri()`, `pkEsri()`), kadar slog ali opis
    ploščic pade **pred prvim izrisom** (preverjeno z nedosegljivim
    `tiles.openfreemap.org`). Napaka ene ploščice pozneje ni razlog za
    menjavo. Esri riše MapLibre, ki zna samo WebGL2, zato rezerve **brez
    WebGL2 ni** na nobenem zemljevidu: stran to pove (veliki pokaže pot do
    tabel, okno vožnje obdrži hitrost in starost lege v glavi).
  * **Stikala „Zatemni podlago“ ni več** (22. 9. 2026). Nastalo je pri
    Esrijevih ploščicah, kjer so bila imena ulic vpečena v podlago in jih
    drugače ni bilo mogoče potisniti nazaj za vozila. V vektorskem slogu so
    napisi svoje plasti in umirjeni že sami; uporabnik razlike med vklopom in
    izklopom ni videl. Zatemnitev podlage v oknu vožnje (CSS filter na
    Leafletovi plasti) je odšla z Leafletom: filter na platnu MapLibra bi
    zatemnil tudi traso in vozilo.
  * **Navedba vira je v slogu** (`sources.omt.attribution`), ker jo veliki
    zemljevid bere od tam in ob rezervi pokaže Esrijevo. V oknu vožnje je
    od začetka zložena v gumb (i): odprta je v okvirju 260 px pokrila traso.
  * **Cena so podatki**, izmerjeno 22. 9. 2026 (vsota ploščic, ki jih MapLibre
    naloži; stisnjeno): pregled države na telefonu **1,27 MB** (6 ploščic;
    Esri 74 kB), namizje 3,4 MB; Ljubljana pri z13 367 kB, pri z15 1,0 MB
    (Esri 187 kB). Ploščice imajo `max-age` deset let in naslov z različico,
    zato se plačajo enkrat na napravo; MapLibre sam je 299 kB, prav tako enkrat.

## Pogled se ne premika sam (26. 9. 2026)

Prej: zemljevid se je odprl pri z8, po prihodu vlakov in avtobusov pa `fitBounds` na njihov okvir — skok sekundo ali dve po tem, ko je človek že gledal („precej neprofesionalno"). Zdaj velja od prvega izrisa: **pogled iz naslova** (`lat`/`lon`/`z`), sicer **zadnji pogled na tej napravi** (`kajros:map-pogled` v `localStorage`, zapiše ga `moveend`), sicer **okvir Slovenije** (`bounds` v konstruktorju). Na telefonu je to trak čez sredino — isto, kar je dal okvir vozil, ko so bila razkropljena po državi; razlika je le, da ne skoči. Preverjeno prek CDP: naslov se v 8 s po odprtju ne spremeni (ni `moveend`), vlaki so na zemljevidu.

**Podatki gredo na pot ob začetku modula** (`zgodaj` v `dashboard.js`: postaje, proge, vlaki, avtobusi), med nalaganjem MapLibra — prej so čakali na slog in drug na drugega. `pollVehicles(url, onData, prva)` vzame že začeto zahtevo. **V aplikaciji domača stran potegne zemljevid vnaprej** (`data-vnaprej` na `.domov`, `<link rel=prefetch>` ob mirovanju): MapLibre 1,1 MB (okrog 300 kB stisnjeno), `dashboard.js`, slog. Naslovi morajo biti natanko taki kot v `dashboard.html`, sicer predpomnilnik ne zadene. V brskalniku ne — prenos bi plačal vsak obiskovalec domače strani.

## 3D od blizu (vsi zemljevidi)

Od daleč raven zemljevid; od Leafletovega **z15** se kamera nagiba, pri **z17,5** 60°; hkrati se stavbe dvignejo od ploskve do prave višine (`render_height` iz OSM). Prelivanje, ne skok, je bila želja (22. 9. 2026, po Slometovem zemljevidu, od koder formula nagiba in razpon zoomov). Stikalo „3D od blizu“ privzeto vklopljeno.

* **Leaflet nagiba ne zna** → vsi zemljevidi samo MapLibre. Ovoj `leaflet-maplibre-gl` je MapLibrovo kamero držal v Leafletovi ravnini — zato okno vožnje do 25. 9. 2026 ni imelo 3D, veliki zemljevid pa ga je imel.
* **Okno vožnje nagib in stavbe dobi iz `pkUstvari()`** (`pot_karta.js`), stikala nima. **Od blizu je avtobus tudi tam model** (25. 9. 2026, na prijavo: „ko približaš, je vozilo še kar 2D“) — oblika prevoznikova, barva **ocene** (`avtobusi3D({ enotna: ESTIMATE_COLOR })`): pasovi in streha `#a8d8ff`, belo ostane belo. Barve prevoznika so na velikem zemljevidu barva meritve; tu vozilo stoji na oceni lege, legenda to barvo tako imenuje. Meja (`AVTO_3D_OD`) in velikost (`avtoPovecava`) v `avtobusi3d.js`, ker ju rabita oba zemljevida. Od daleč ostane ikona kot DOM (`rotationAlignment: map`, `pitchAlignment: viewport`), ker se premika vsako sekundo in je ena; ko je model viden, je ikona skrita, sicer bi ga kot element nad platnom prekrila.
* **Nagib = lastnost približka**, ne gesta: `transformCameraUpdate` ga postavi ob vsaki spremembi kamere, `touchPitch` in `pitchWithRotate` ugasnjena, da se ne prepirata. Vrtenje ostane, kompas vrne sever.
* **`z` v naslovu ostane v Leafletovih enotah** (MapLibrov zoom + 1), ker ga delijo drugi (`train.js` pelje na `&z=15`) in vse meje na strani (`LZ` v `dashboard.js`).
* **Vlaki DOM, avtobusi plast.** Oznaka vlaka = HTML z več vrsticami in značko, vlakov nekaj deset; avtobusov ob konici 1 530, DOM bi pri vsakem premiku vsakega prestavljal posebej. Avtobus v nagibu stoji **obrnjen proti gledalcu** (`icon-pitch-alignment: viewport`): položen na cesto je bil pri 60° za pol nižji, med stavbami ga je bilo težko najti.
* **Stavbe pod napisi**, sicer stavba pokrije ime ulice za sabo. Naše plasti in zatemnitev nad stavbami.
* **Cena v podatkih majhna**: OpenFreeMap ima ploščice do z14, nad tem se povečujejo, zato nagib doda kvečjemu kakšno ploščico na obzorju. Izmerjeno (Ljubljana, Chromov dnevnik omrežja): telefon pri z17 **2 ploščici z 3D in brez**; namizje 1400 × 900 pri z16 4 in 4, pri z17,5 **4 (786 kB) proti 2 (451 kB)**. Cena = risanje stavb, zato stikalo.
* **Brez WebGL2 zemljevida ni**; stran to pove z dvema povezavama; iskalnik in plasti se skrijejo, ker brez zemljevida ne naredijo ničesar.
* **Od Leafletovega z16 so avtobusi 3D modeli** (`avtobusi3d.js`), pod tem ikone. Meja tam, kjer se kamera že vidno nagne; od zgoraj bi bil model bela škatla. Vsak prevoznik ima **svoj model in barve**: LPP zgibni mestni 18 m (148 od 224 njegovih avtobusov zgibnih), Arriva, Nomago in AP Murska Sobota medkrajevni 12 m; barve z njihovih logotipov in strani. **Streha nosi barvo z legende**, ker se od zgoraj vidi samo streha.
* **Modeli goli WebGL2 v plasti po meri**, ne three.js (Slomet ga ima za en GLTF): three.js 172 kB stisnjen, dobra polovica MapLibra (299 kB), za nekaj škatel ni vreden nove odvisnosti. Vsa vozila istega modela = en klic risanja (instanciranje). Lega gre v senčilnik kot odmik od izhodišča v Sloveniji — absolutni Mercator v float32 bi pri z18 trepetal za metre.
* **Model večji od resničnega**: pri z16 ~36 px kot ikona, pri z19 1,7-krat (`povecava3D`). Plasti damo samo vozila v sliki in pas okrog nje (`posodobi3D` ob premiku). `queryRenderedFeatures` plasti po meri ne vidi, zato dotik išče sam (`zadetek3D`: razdalja do lege, polmer pol modela).

**Med dvema meritvama pika drsi naprej po trasi — samo v oknu vožnje.** Lega ob strežbi ~30 s stara (izmerjeno), pri 50 km/h **več kot pol kilometra**. Ocena = `hitrost × starost` vzdolž trase linije, osvežena vsako sekundo.

Izmerjeno na 79 primerih (šestminutni zajem sledi iz feeda, razmik 15–60 s), napaka proti dejanski naslednji legi:

| kaj naredimo s piko | mediana | v 100 m |
|---|---|---|
| pustimo pri miru (prej) | 63 m | 63 % |
| premaknemo po smeri (`bearing`) | 36 m | 72 % |
| **premaknemo po trasi** | **30 m** | **80 %** |

Trasa boljša od smeri, ker cesta zavija, vozilo pa ne pove, da bo zavilo. Vzorec majhen (41 vozil ob desetih zvečer) — smer jasna, natančnost številk ne; kdor spreminja, naj izmeri znova.

Varovala, brez katerih bi ocena lagala: ne premikamo **stoječega** vozila (`speed_ms < 1`), ne vozila, od trase oddaljenega nad 120 m (ni na njej), nikoli čez konec trase. Podnapis pove „ocenjeno iz lege pred 42 s", ne „lega stara 42 s".

**Na oceni vozilo gleda po trasi, ne po smeri iz feeda** (25. 9. 2026, na prijavo „modeli naj bolj sledijo trasi"). Smer iz feeda stara kot lega; avtobus, ki ga je ocena odpeljala čez ovinek, je z njo stal počez na cesto. Izmerjeno na 324 parih zaporednih leg (31 vozil LPP), proti smeri ob naslednji legi: mediana **5,6° → 2,4°**, v 20° **74 → 87 %**, nad 45° 12,3 → 8,0 %; kar ostane = napaka lege, ne smeri. Smer = tetiva od repa do čela **narisanega** vozila (`smerNaOceni`): model povečan (pri z15 zgibni 89 m), s tetivo njegove dolžine oba konca v ovinku ležita na trasi. Natančnosti dolžina tetive ne spremeni (0–150 m: 84–87 % v 20°).

Ocena teče **samo pri LPP**: Arriva, Nomago in AP Murska Sobota hitrosti ne pošiljajo (0 od 445 vozil), zato stojijo na izmerjeni legi s smerjo iz feeda. Tam in na velikem zemljevidu ostane smer iz feeda, ker trasa ni boljša: proti smeri premika med legama pri Arrivi nad 45° 11,5 % s feedom in 12,1 % s traso (487 parov); pri LPP se feed s traso ujema v 95 % v 15°.

**Barva loči meritev od ocene.** Vozilo na tem zemljevidu ni zeleno kot drugod, ampak `ESTIMATE_COLOR` (`#a8d8ff`) in rahlo prosojno — odtenek rezerviran za „tu meritve ni", lestvica zamud ga ne uporablja. Zadnja **izmerjena** lega = **rdeča** pika s svetlim obročem: trasa in postajališča zeleni, zelena pika bi se izgubila; rdeča ni iz nobene lestvice (ne zamud, ne razmer), tu ne more pomeniti drugega. Pika se **dvigne nad traso** (`bringToFront()`): črta in pika v isti plasti, vrstni red risanja = vrstni red dodajanja, 3 px široka trasa jo je prerezala, videti kot del proge. Riše se vedno — kadar vozilo stoji, jo oblika vozila pokrije, dveh oznak ni videti. Pod zemljevidom enovrstična legenda; brez nje je moder avtobus ob rdeči piki uganka, razlika med njima pa je bistvo okvira.

**Lastna lega je na obeh zemljevidih, a je nikoli ne zahtevamo sami.** Nezaprošeno dovoljenje je vsiljivo, brskalnik ob zavrnitvi pogosto zapomni za vedno — zato se `locateMe()` sproži šele ob dotiku gumba. Na velikem zemljevidu gumb pod približevanjem (drugi klik lego skrije, kar je hkrati „možnost prikaza", zato ne rabi še ene izbire med plastmi), v oknu vožnje v glavi okvira. Barva `#2f7fff`: ne nastopa v nobeni lestvici, dovolj nasičena, da se loči od blede `#a8d8ff` (ocena). **Obroč točnosti ni okras** — GPS v mestu zgreši za sto metrov, pika brez njega trdi natančnost, ki je nima; ista napaka kot pika vozila brez „lega stara N s".

**Razdalja do vozila se meri po poti, ne zračno.** Tvojo in ocenjeno lego vozila projiciramo na traso in odštejemo razdalji vzdolž nje (`projekcijaNaTraso`). Zračna črta čez Golovec je pri mestnem avtobusu lahko trikrat krajša od prave, obljubljala bi prihod, ki ga ne bo. Vozilo vzamemo na **ocenjeni** legi, isti kot narisana: dve številki o istem vozilu, ena s slike, ena iz besedila, se ne smeta razhajati. Kadar je človek od proge več kot **1 km** (`OB_PROGI_M`), računa ne delamo in to povemo — blok ali dva stran je še „pri postajališču", čez to bi bila številka izmišljena. Besedilo pove smer: „Do tebe ima še 1,2 km poti" oz. „Tvojo lego je že prevozil — 420 m naprej po poti"; „je 1,5 km pred tvojo lego" se bere dvoumno.

**Geste omejene, dokler je zemljevid element strani.** „Naj kolešček približuje?" → „ne, dokler je to element": kazalec zaide čez zemljevid, stran se neha pomikati. Od prehoda na MapLibre to opravi njegov `cooperativeGestures` (namig v slovenščini v `pkUstvari`), razširjen pogled ga ugasne. Tabela ostaja ista:

| | vgrajen | čez celo stran |
|---|---|---|
| kolešček | ne (Ctrl/⌘ + kolešček da) | da |
| **miška** | **vleče zemljevid** | isto |
| en prst | pomika **stran** | pomika zemljevid |
| dva prsta | pomikata in približujeta | isto |
| gumba +/− | vedno | vedno |

Resnična napaka **ni bila** manjkajoča povečava, ampak vlečenje z enim prstom: pomikalo zemljevid namesto strani, s tega okvira se na telefonu ni dalo odpomakniti. Vlečenje z miško strani ne pomika, ostane zemljevidu — prenosnik z zaslonom na dotik mora imeti oboje.

**Gumb razširi zemljevid čez celo stran, ne čez cel zaslon.** Fullscreen API vzame ves monitor in skrije brskalnik; za „hočem videti več zemljevida" preveč — izgubi se naslovna vrstica, gumb nazaj in vsak orientir, izhod je tipka, ki je na telefonu ni. Razred `is-max` na okviru (`position: fixed; inset: 0`) naredi isto koristno stvar brez tega; glava in legenda ostaneta, ker brez njiju ni ne hitrosti ne pomena oznak.

**Razširjen zemljevid mora prezreti postavitev, in to zahteva `!important`.** Namizna pravila v `@media` (`body:not(.is-advanced) .col-run .run-map`) imajo specifičnost **(0,3,1)** in so `.run-map-wrap.is-max .run-map` **(0,3,0)** tiho premagala: zemljevid čez celo stran ostal visok **240 px** in zamaknjen za **12 px** margine, ostalo črno. Na telefonu se to **ni videlo**, ker tam teh pravil ni — popravljeno šele ob prijavi z namizja. Rešitev ni daljši selektor, ampak `!important` na `position`, `inset`, `margin`, `height`: element je iztrgan iz postavitve in mora prezreti vsa pravila o njej. Isti vzorec kot `adv-only` v `base.css`.

**Na velikem zemljevidu tega ni** — odločitev, ne opustitev: tam je vprašanje „kje je vse skupaj", ocena za osemdeset vozil = osemdeset izmišljenih leg. V oknu vožnje gledaš eno vozilo, vprašanje je natanko „kje je zdaj".

**Trasa se skoraj nikoli ni risala.** Pogoj `trasa.length > 1` napisan, ko je bil `points` ravna lista točk; odkar jih uvoz reže na kose (`SHAPE_BREAK_M`), je enodelna trasa dolga 1 in pogoj je ni spustil. To je bilo **2 706 od 2 897 oblik, torej 93 %** — v oknu vožnje in na velikem zemljevidu. Pravilen pogoj: „vsaj en kos z vsaj dvema točkama".

**Okno vožnje z GPS ima živ zemljevid, v preprostem pogledu.** „Kje je zdaj" je pri avtobusu prvo vprašanje. MapLibre se naloži šele, ko lega res obstaja — vlaki je nimajo nikoli, zanje okvira ni; prazen bi obljubljal podatek, ki ne obstaja.

**Starost lege mora teči sama.** „lega stara 59 s" je stala do naslednjega polla, nato skočila nazaj na 38 -- videti kot okvara, čeprav vsaka vrednost pravilna. Starost = edina številka na strani, ki se spreminja tudi ko se ne zgodi nič, zato jo šteje brskalnik: `common.ageHtml()` vrne `<span class="age-live">` z izhodiščem v `data-`atributih, ena sekundna zanka jih poišče po razredu. Iščemo po razredu, ne po registru, ker se kartica na zemljevidu gradi iz niza HTML in nanjo ni kam obesiti sklica. **Ura odjemalca ni v računu** — prištevamo razliko dveh lastnih meritev, zamik ure ne škodi.

**Kdor izpiše `ageHtml()`, ponastavi števec.** Funkcija ob vsakem klicu zapiše novo izhodišče, zato izpis ne sme teči v sekundni zanki. Zgodilo se je, ko je pike začel premikati `postaviVozilo()`: vsako sekundo je prepisal tudi podnapis, števec se je vrnil na izvorno vrednost, zanka v `common.js` ga je vmes povečala, naslednji izris povozil — videti kot utripanje. Podnapis se zato prepiše **samo ob novih podatkih** (`nova`), premik pike teče vsako sekundo. Pravilno: 55, 56, …, 60, **50** (prispela nova lega), 51, 52.

**Preprost pogled ni samo za telefon.** Okno vožnje = en stolpec 340 px; ker je zgodovina v preprostem pogledu skrita, je na namizju ostal ozek trak ob praznem zaslonu. Nad 1000 px se vsebina razdeli: levo, kar velja **zdaj** (zamuda, razmere, kje je vozilo), desno pot po postajah. Flex, ne grid — časovnica je visoka, kot element čez več grid vrstic bi te vrstice raztegnila, levi stolpec pa bi visel v praznem.

Izmerjeno pri 1920 × 993: levi stolpec **599 px, od tega zemljevid 320** — 53 % višine za okvir, ki samo pove „kje je zdaj", desni stolpec 360. Na namizju zato zemljevid 240 px (telefon 210, privzeto 260) in blok trenutne zamude tesnejši; stolpec **506 px**. Zrak med vrsticami se stiska **samo tu** — na telefonu loči dotik od dotika.

**Statične datoteke z `Cache-Control: no-cache`.** Brez glave brskalnik ugiba in datoteko, ki se dolgo ni spremenila, drži ure. Prijavljena posledica: popravek spodnje plošče na strežniku, uporabnik pa dobival staro CSS, gumba ni bilo. `no-cache` ≠ „ne shranjuj" — datoteka se shrani in pred vsako rabo preveri; z `ETag` odgovor 304 brez telesa.

**Opomb naj bo malo.** Prikaz je imel na zemljevidu tri odstavke razlage, v oknu vožnje štirivrstično opombo o vremenu in drugo o virih podatkov. Zapisano dvakrat, prebrano nikoli. Velja: opomba pove tisto, kar spremeni potnikovo ravnanje („čakaj na postajališču, ne na peronu"), ostalo v tooltip ali odpade. Razlaga o virih podatkov ne sodi tja, kjer človek gleda svojo vožnjo.

**Stranska plošča zemljevida je na telefonu spodnja plošča.** 320 px stolpca na 390 px zaslonu pojedlo pol slike in ga ni bilo mogoče skriti; zdaj privzeto zaprt, odpre se na dotik. Izbira vozila ga spet zapre — naslednje, kar človek hoče videti, je zemljevid.

Okno vlaka = **ena slika, ne zavihki**. Krivulja zamude čez vse postaje poti, pod njo v istem grafu pas razmer: vprašanje ni *"kakšno je vreme"*, ampak *"je zamuda tam, kjer je bilo vreme hudo"*. Hitrost po odsekih = isti podatek v drugi enoti, zato na dnu v zaprtem `<details>`, naloži se šele ob odprtju. Zavihkov ne vračaj — eno vprašanje so razbili na tri strani.

**Končna zamuda po dnevih: 15 dni v širini okvirja, ostali levo.** Prej je graf stisnil vse (7 px na stolpec) — na telefonu 40 stolpcev brez razločljivega dneva. Zdaj drsi vodoravno, odpre se pri zadnjih dneh, os stoji posebej (`.runs-ovoj`), da ob drsenju ne odide.

Frontend = **vanilla JS brez ogrodja**. Grafi = ročno risan SVG z lastnim tooltipom (`train.js`) — ni chart knjižnice, ne dodajaj je brez razloga. MapLibre gostovan pri nas (`static/maplibre-6.10.0/`).

## Gumb „osveži“ obstaja zato, ker se osveževanje ne vidi

Oba zemljevida se osvežujeta sama, v koraku s strežbo. Ko vozilo stoji ali feed zaostane, je slika mirna — videti **enako kot obtičala stran**. Brez gumba edini izhod = ponovno nalaganje cele strani, ki podlago, plasti in kazalo postaj znova prinese za nič.

Gumb ničesar ne pohitri. Pove dvoje: da se je pravkar vprašalo in **ob kateri uri je bil odgovor** („osveženo ob 20:44:25“). Ob napaki tudi pove („osvežitev ni uspela — ni zveze s strežnikom“) in pordeči — tiha napaka = človek ne ve, ali stran še teče.

Skupen je `common.pripniOsvezi()`; obe zanki imata odslej `zdaj()` (`pollWhileVisible`, `pollVehicles`). **`zdaj()` napake ne pogoltne**, `tick()` jo še vedno: ritem sme eno zahtevo zamuditi, gumb pod prstom ne.

**Na velikem zemljevidu levo pod približevanjem, ne desno pod lego.** Desno na telefonu pri `top: 62px` že stoji tipka za spodnjo ploščo (`.sheet-toggle`, `z-index: 1100`) in je gumb prekrila. Videlo se je šele na posnetku v telefonski širini; na namizju te tipke ni.

### Lega vozila se je nalagala v vzporednih zankah

`loadPosition()` se kliče iz `loadRun()`, ta teče vsakih 30 s — `pollVehicles` je ob vsakem klicu začel **novo** zanko. Izmerjeno na `/app/bus/12D` (chromium, `--virtual-time-budget=90000`, štirje cikli `loadRun`): **19 zahtev po legi z varovalko odstranjeno proti 12 z njo**. Razlika raste z odprtostjo strani, ker vsaka zanka ostane za vedno.

Varovalka: ena vožnja, ena zanka (`runMap.pollTrip`).

## Avtobusi: plast na prevoznika, privzeto ugasnjeni

**Ena skupna avtobusna plast je zemljevid zadušila.** Ob 15:10 na njem 1 530 vozil, slika zelena kaša, posameznega avtobusa ni bilo mogoče najti. Zdaj **vsak prevoznik svoja plast in svoje potrditveno polje**, **vsi privzeto ugasnjeni**: zemljevid se odpre kot železniški, avtobuse prižgeš, ko jih iščeš.

Barve preverjene (ne izbrane na oko) s `scripts/preveri_paleto.py`:

| | | |
|---|---|---|
| LPP | `#4db97f` | zelena |
| Arriva | `#6fb8ff` | modra |
| Nomago | `#9d7ae0` | vijolična |
| AP Murska Sobota | `#c9a227` | zlata |

Najslabši par pri deutan/protan **ΔE 9,6** (prag 3, „na prvi pogled“ 6), pri tritanopiji 4,8. Proti lestvici zamud zelena in oranžna pri deutanu trčita (ΔE 1,2), a to ni težava: **vozila loči oblika** — avtobus puščica, vlak krog — in oznaka poleg nosi ime prevoznika. Barva nikoli ne nosi pomena sama; pravilo projekt že ima.

**LPP ima dva `agency_id`, na zemljevidu eno vrstico.** `1118` = primestne linije iz IJPP, `lpp` = mestne iz lastnega vira. Ključa `lpp` v `BUS_LAYERS` ni bilo, zato so mestni avtobusi padli med „druge prevoznike" — **104 od 179 živih vozil na produkciji** (7. 9. 2026), torej večina, za stikalom, ki je privzeto ugasnjeno in se imenuje, kot da prevoznika ne poznamo. Zdaj oba ključa skozi `agencyKey()` v isto plast, isti števec, isto barvo.

Zakaj ena vrstica, ne dve: na postajališču piše oboje „LPP", številke se med viroma ne prekrivajo (mestne 1–27, primestne 40–84), zemljevid odgovarja na *„kje je moj avtobus"*. Statistika ju loči (`stats.AGENCY_NAMES`: „LPP mestni" / „LPP primestni"), ker tam vprašanje ni isto — zamuda mestne in primestne linije sta dve različni stvari.

**Peta vrstica „Drugi prevozniki" ni okras.** Če v zajem pride nov prevoznik, bi njegova vozila brez nje tiho izginila — plast brez stikala = plast, ki je ni. Vrstica se skrije, kadar je števec 0.

**Gumb za nastavitve zgoraj desno — draga lekcija.** Dvakrat je bil spodaj, dvakrat ga uporabnik ni videl:

1. kot vrstica v barvi podlage se je zlil z navedbo vira;
2. kot plavajoča tipka 14 px nad dnom je izginil **pod Chromovo spodnjo naslovno vrstico**. Ta prekrije dno postavitvenega okna, ne da bi ga skrajšala, zato `bottom: 0` ni viden. Dokaz: opomba o skritih oznakah, postavljena 66 px nad dnom, se je na telefonu risala **tik nad** URL vrstico → spodnjih 66 px prekritih.

**Dna zaslona v brskalniku ne uporabljaj za nadzor**, ki ga mora uporabnik najti. Zgornji desni kot edini, ki ga noben brskalnik ne prekrije — tam že stoji tipka za lastno lego, zato se dve okrogli tipki druga pod drugo bereta kot orodji zemljevida. Uporabnik lego **potrdil na svojem telefonu** (3. 9. 2026); prejšnji dve padli, ker potrjeni samo na posnetku brez zaslona. Posnetek namizja ne dokaže dosegljivosti na telefonu.

Ker je na tipki ikona, ne besedilo, mora imeti `aria-label`.

**`display: flex` povozi `[hidden]`.** Vrstica „Drugi prevozniki" se je kazala kljub ničli, ker ima `.layer` svoj `display`. Potrebno izrecno `.layer[hidden] { display: none; }`.
