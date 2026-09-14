---
paths:
  - "kajros/static/dashboard.js"
  - "kajros/static/dashboard.css"
  - "kajros/static/train.js"
  - "kajros/static/train.css"
---

# Zemljevida: veliki in tisti v oknu vožnje

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

  **Iskalnik najde tudi postaje** (14. 9. 2026). Kazalo obeh omrežij je isto
  kot pri najhitrejši poti (`common.naloziKazalo()`, 12 h v `localStorage`),
  največ štiri postaje. Z besedo so nad vozili, s številko („25", „IC 502")
  pod njimi. Izbira postavi obroč in oblaček s povezavo na odhodno tablo;
  železniška postaja je tista, ki je v `/api/stations?network=zeleznica`.

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

**Končna zamuda po dnevih: 15 dni v širini okvirja, ostali levo.** Prej je
graf stisnil vse, kar je šlo noter (7 px na stolpec) — na telefonu 40 stolpcev
brez razločljivega dneva. Zdaj drsi vodoravno, odpre se pri zadnjih dneh, os
stoji posebej (`.runs-ovoj`), da ob drsenju ne odide.

Frontend je **vanilla JS brez ogrodja**. Grafi so ročno risan SVG z lastnim
tooltipom (`train.js`) — ni chart knjižnice in je ne dodajaj brez razloga.
Leaflet se nalaga z unpkg CDN.

## Avtobusi: plast na prevoznika, privzeto ugasnjeni

**Ena skupna avtobusna plast je zemljevid zadušila.** Ob 15:10 je bilo na njem
1 530 vozil in slika je bila zelena kaša, v kateri posameznega avtobusa ni bilo
mogoče najti. Zdaj je **vsak prevoznik svoja plast in svoje potrditveno polje**,
in **vsi so privzeto ugasnjeni**: zemljevid se odpre kot železniški, avtobuse
prižgeš, ko jih res iščeš.

Barve niso izbrane na oko, ampak preverjene s `scripts/preveri_paleto.py`:

| | | |
|---|---|---|
| LPP | `#4db97f` | zelena |
| Arriva | `#6fb8ff` | modra |
| Nomago | `#9d7ae0` | vijolična |
| AP Murska Sobota | `#c9a227` | zlata |

Najslabši par je pri deutan/protan **ΔE 9,6** (prag 3, „na prvi pogled“ 6) in
celo pri tritanopiji 4,8. Proti lestvici zamud zelena in oranžna pri deutanu
trčita (ΔE 1,2), a to ni težava: **vozila loči oblika** — avtobus je puščica,
vlak krog — in oznaka poleg nosi ime prevoznika. Barva nikoli ne nosi pomena
sama; to pravilo projekt že ima.

**LPP ima dva `agency_id` in na zemljevidu eno vrstico.** `1118` so primestne
linije iz IJPP, `lpp` mestne iz lastnega vira. Ključ `lpp` v `BUS_LAYERS` ni
obstajal, zato so mestni avtobusi padli med „druge prevoznike" — **104 od 179
živih vozil na produkciji** (7. 9. 2026), torej večina, za stikalom, ki je
privzeto ugasnjeno in se imenuje, kot da prevoznika ne poznamo. Zdaj oba
ključa peljeta skozi `agencyKey()` v isto plast, isti števec in isto barvo.

Zakaj ena vrstica in ne dve: na postajališču piše oboje „LPP", številke se med
viroma ne prekrivajo (mestne 1–27, primestne 40–84), zemljevid pa odgovarja na
*„kje je moj avtobus"*. Statistika ju loči (`stats.AGENCY_NAMES`: „LPP mestni"
/ „LPP primestni"), ker tam vprašanje ni isto — zamuda mestne linije in
primestne sta dve različni stvari.

**Peta vrstica „Drugi prevozniki" ni okras.** Če v zajem pride nov prevoznik,
bi njegova vozila brez nje tiho izginila — plast brez stikala je plast, ki je
ni. Vrstica se skrije, kadar je števec 0.

**Gumb za nastavitve stoji zgoraj desno, in to je bila draga lekcija.**
Dvakrat je bil spodaj in dvakrat ga uporabnik ni videl:

1. kot vrstica v barvi podlage se je zlil z navedbo vira;
2. kot plavajoča tipka 14 px nad dnom je izginil **pod Chromovo spodnjo
   naslovno vrstico**. Ta prekrije dno postavitvenega okna, ne da bi ga
   skrajšala, zato `bottom: 0` ni viden. Dokaz je bila opomba o skritih
   oznakah: postavljena 66 px nad dnom se je na telefonu risala **tik nad**
   URL vrstico, torej je bilo spodnjih 66 px prekritih.

**Dna zaslona v brskalniku ne uporabljaj za nadzor**, ki ga mora uporabnik
najti. Zgornji desni kot je edini, ki ga noben brskalnik ne prekrije — in tam
že stoji tipka za lastno lego, zato se dve okrogli tipki druga pod drugo bereta
kot orodji zemljevida. Uporabnik je to lego **potrdil na svojem telefonu**
(3. 9. 2026); prejšnji dve sta padli prav zato, ker sta bili potrjeni samo na
posnetku brez zaslona. Posnetek namizja ne dokaže dosegljivosti na telefonu.

Ker je na tipki ikona in ne besedilo, mora imeti `aria-label`.

**`display: flex` povozi `[hidden]`.** Vrstica „Drugi prevozniki" se je kazala
kljub ničli, ker ima `.layer` svoj `display`. Potrebno je izrecno
`.layer[hidden] { display: none; }`.
