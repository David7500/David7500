---
paths:
  - "kajros/static/dashboard.js"
  - "kajros/static/dashboard.css"
  - "kajros/static/train.js"
  - "kajros/static/train.css"
  - "kajros/static/podlaga.json"
  - "kajros/pripni.py"
  - "kajros/tiri.py"
  - "deploy/osrm/**"
---
# Zemljevida: veliki in tisti v oknu vožnje

## Zemljevid

* **Zemljevid = edini skupni pogled.** Vlak = ploščica na zadnji postaji z meritvijo ali na postaji, kjer po voznem redu in zamudi zdaj stoji; avtobus = **oblika vozila** na izmerjeni legi, raste s približkom (15–34 px), kaže v smer vožnje. Puščica premalo: pri velikem približku videti kot pika, od vlaka se ni ločila.

  **Postaja iz poročila SŽ ni lega vlaka**, ampak postaja, kamor pelje (92 % od 26 711 poročil zajetih pred prihodom tja, `zajem.md`). Do 5. 10. 2026 je vlak stal tam: EN 414 v Ljubljani, izmerjen v Zidanem Mostu. Zdaj je poročilo na kartici svoja vrstica („napoved prevoznika → Ljubljana · +15 min · ob 21:20“), zamuda, barva in kraj so iz naše meritve.

  **Vlak = znak na postaji, ne vozilo** (izbral David 4. 10. 2026 med štirimi, `trainSvg`): oranžna zaobljena ploščica z vlakom od spredaj, pokončna. **Zavrnjeno:** vlak od zgoraj v smeri proge („zgleda kot bus“) in obroč okoli ikone (spominjal je na obroč izbranega avtobusa). Tudi žebljiček, polni krog in vlak od strani so bili na izbiro. Oznaka = napis z obrobo iz senc, kot številka ob avtobusu; prej neprosojna temna škatla, ki je v vozlišču prekrila avtobuse in ime postaje.

  **Ime postaje se pokaže na dotik, po petih sekundah odide** — od 5. 10. 2026 samo še avtobusna postajališča in pike na poti izbranega vozila; železniška postaja odpre oblaček z odhodi (razdelek spodaj). Pike so bile `interactive: false` → nema točka, ni se dalo izvedeti, katera postaja. Trajne oznake na mestni liniji zakrijejo progo pod sabo. Zato klik odpre oblaček (`common.NAME_MS`), `setTimeout` ga zapre. Brez gumba za zapiranje — na telefonu manjši od prsta, zahteval bi natančnejši dotik od tistega, ki je ime odprl. Klik ustavi razširjanje dogodka, sicer na telefonu zapre spodnjo ploščo. Velja na velikem zemljevidu, na trasi izbranega vozila, v oknu vožnje. Polmer pike 3,4 namesto 2,4 px: 2,4 < prst. Veliki zemljevid (`zadetek()` v `dashboard.js`) in okno vožnje (`runImeNaDotik()`) zadeneta, kar je v **12 px** od prsta, vozilo oziroma izmerjeno lego pred postajo — MapLibre sicer zadene samo piko samo.

  **Avtobusna postajališča = svoja plast, privzeto ugasnjena.** Vseh 9 519 (211 kB z gzipom, 167 ms), zato naložijo se šele ob prvem vklopu — enako kot trase. Rišejo se **od z13 naprej**; meja izmerjena na ljubljanskem oknu 1200 × 800: z13 253, z12 600, z11 1 694 in mreža prog izgine pod njimi. Pod pragom plast ne riše nič in pove, zakaj. Železniške postaje ostanejo svoja, privzeto vklopljena plast — 271, progo prav opisujejo.

  **Od blizu nadstrešek ali znak** (4. 10. 2026). Pika je v barvi prevoznika, kjer jih ustavlja več, `SKUPNA_INK` `#d5dae2`. Od `NADSTRESKI_OD` (= `AVTO_3D_OD`, kot modeli) jo ob cesti zamenja **nadstrešek** (tla, stebra, steklena stena, streha v barvi prevoznika; povečan 2–3× kot modeli, sicer je ob njih škatlica), stran ceste po `desno`, vsaj `ROB_M` 3,8 m od osi. **Avtobusna postaja** (ime z „AP“ ali končna ≥ 20 tras dveh prevoznikov; 20 postaj) je **znak na drogu** že od daleč, z imenom -- nadstrešek ob robu ceste bi tam lagal, postaja ima perone na dvorišču. Postajališče brez smeri (dlje od 15 m od trase) dobi znak od blizu. Smer, stran, prevozniki in „postaja“ so v tabeli `postajalisce` (`pripni.postajalisca`, po vsakem pripenjanju); `/api/stations?network=avtobus` jih nosi. Pika ostane nevidna pod nadstreškom, ker jo zadene prst. Nadstreški samo za postajališča v sliki (`posodobiNadstreske` v `posodobi3D`).

  Vsaka plast se da izklopiti posebej (vlaki, avtobusi, železniške proge, **trase vozil na poti**, železniške postaje, avtobusna postajališča, podlaga, dodatna imena), ne le avtobusi. Trase privzeto ugasnjene, naložijo se ob vklopu: gost snop črt čez vso Ljubljano odgovarja na „kod vozijo linije", ne na „kje je moj avtobus", drugo je razlog za obisk strani. 128 različnih oblik, 108 kB z gzipom.

  **Trase so lahko pretrgane; ravna črta čez pol Slovenije = laž.** V zajetem GTFS 2 185 razmikov od 4,85 milijona (0,045 %) daljših od kilometra, pri 193 oblikah; najdaljši 40 km. Uvoz traso razreže na kose (`gtfs.SHAPE_BREAK_M`), vsakega nariše posebej — 2 897 oblik da 4 732 kosov. Meja izmerjena, ne izbrana: surove točke 17 m narazen (mediana), 105 m pri 99 %, 514 m pri 99,9 %, nato skok na 22,8 km. Med pol kilometra in dvajsetimi ni ničesar. Na **poenostavljenih** točkah praga ni mogoče postaviti — dolg raven odsek videti enako kot preskok. Namesto lestvice „največje zamude" je **iskalnik vozila**: vprašanje pred zemljevidom = „kje je moj avtobus", ne „kdo danes najbolj zamuja".

  **Iskalnik najde tudi postaje** (14. 9. 2026). Kazalo obeh omrežij isto kot pri najhitrejši poti (`common.naloziKazalo()`, 12 h v `localStorage`), največ štiri postaje. Z besedo so nad vozili, s številko („25", „IC 502") pod njimi. Izbira postavi obroč; železniška postaja (tista v `/api/stations?network=zeleznica`) odpre isti oblaček kot dotik pike, postajališče oblaček s povezavo na odhodno tablo.

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
    izgine (`k-proge`, glej „Od blizu“ spodaj), da tirov ne prekrije. Napisi z `metadata.kajros:napisi = dodatni` (vasi, četrti,
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

## Železniška postaja in ovire na progi (5. 10. 2026)

Prijava: „na zemljevidu nimava možnosti za železniške postaje in za ovire“. Dotik pike postaje je dal ime za 5 s, ista postaja iz iskalnika pa oblaček s povezavo na tablo; zapor tira na zemljevidu ni bilo nikjer, čeprav jih `zapore.py` že bere za tablo.

* **Ena pot do postaje** (`odpriPostajo`): dotik pike, izbira v iskalniku, obroč najdene postaje in gumb „odhodi s postaje X ›“ v oblačku vlakov (ploščica vlaka v vozlišču prekrije piko skoraj ves dan, Ljubljana). Kartica v slogu kartice vozila (premik, skrčitev): naslednji 3 odhodi, zapore tira na postaji, „cela odhodna tabla ›“. Odhodi se vprašajo šele ob dotiku (`/api/departures?network=zeleznica`, prvič 89 ms, nato ~11 ms, 2,5 kB z gzipom) in osvežijo z `pollLive`, dokler je oblaček odprt.
* **Ista pravila kot tabla, ne svoja**: razvrstitev po pričakovani uri in nepotrjeni odhodi so zdaj `razvrstiTablo`/`nepotrjen` v `common.js` (prej samo v `connections.js`), zamuda `delayText`/`delayColor`, tir `tirHtml`, „lahko do“ iz `do_s`. Nadomestni prevoz „po voznem redu“; brez meritve „običajno · N voženj“ s tanjšo številko, kot žeton na tabli.
* **Plast „Ovire na progi“** (`/api/zapore?dan=`, privzeto prižgana): en `Feature` na zaporo, elementarni odseki iz `edge` (`osm`, sicer `geojson`), `okna` dneva in `stanje` (`zdaj` / `pozneje` z `zacne` / `koncano`). Rumena ovir `OVIRA_INK` `#f2d36b`, črtkana; ko velja, 4,5 px namesto 2,5, končana bledi na pol (ta dan je še vedno lahko vzrok zamude). Na tleh, nad progo in potjo izbranega vlaka (zapora na njegovi poti je bistvo), pod pikami postaj in vozili — vlak ob zapori ostane dosegljiv, dotik ima pika prednost pred črto. Dotik črte: odsek, „danes 8.00–16.00 · velja zdaj / začne ob / končano“ (`common.kdajZapore`, ista beseda kot na kartici strani ovir), povezava na `/app/ovire`.
* **Stanje računa strežnik ob vsaki strežbi**, geometrija je predpomnjena (`alerts_etag`, vozni red, pripenjanje; 5 min): predpomnjeno stanje bi do izteka trdilo „začne ob 8.00“. Odgovor je zato sestavljen iz že zapisane geometrije in svežih lastnosti. Zemljevid ga vpraša na minuto.
* **Barva preverjena** (`preveri_paleto.py`, nova skupina): proti lestvici zamud najslabše 1–5 min ΔE 5,2 (tritan), proti izbrani poti 8,1, AP MS 11,3; kontrast 12,9 : 1. Pod 6, zato loči oblika (črtkana črta, ne žeton ne vozilo) in beseda v oblačku.
* **Cena**, izmerjeno 5. 10. 2026 ob 23 h (4 zapore danes, 32 obvestil o zapori tira): 1 972 B z gzipom (6 640 brez), 7. 10. 2 528 B. Prvi klic po zagonu 12 ms (`zapore.karta` brez predpomnilnika 3,9 ms), toplo 4–8 ms (mediana 15 zahtev).

## Od blizu: trase na cesti, ne ob njej (2. 10. 2026)

Prijava: od blizu so trase, proge in postaje tanke črte in pike, ki se od podlage razlikujejo za več metrov in ceste ne zapolnijo. Meritve v `docs/MERITVE.md` („Zemljevid od blizu“).

* **Trase so pripete na OSM** (`kajros/pripni.py`, lastni OSRM s profiloma `deploy/osrm/avtobus.lua` in `tir.lua`, `deploy/osrm.sh`). Surove GTFS so od osi ceste v mediani 3,1 m (IJPP), razpršene na obe strani; pripete 0,4 m. Pripeta je v `shape.osm` in `edge.osm`, surova ostane v `points`/`geojson`. `/api/trip/{id}/shape`, `/api/shapes/live`, mreža prog in `deljenje.trasa()` berejo pripeto, kadar je. Brez OSRM je vse kot prej.
* **Širina v metrih od MapLibrovega z16** (`sirinaM` v `common.js`), od daleč v pikslih. Velja za traso izbranega vozila (avtobus 7,5 m, vlak 3,2 m), vse trase (2,5 m), mali zemljevid in pot od vrat do vrat -- in za **ceste in tire podlage** (`podlaga.json`, `metadata.kajros:sirine`): glavna 10 m, srednja 8, manjša 6, servisna 4,5, pot 1,5, tir 3, pragovi od blizu pravi (0,26 m na 0,6 m). Prej je bila glavna cesta pri z18 16 px = 3,3 m, trasa 3 px = 0,6 m. Izraz s priblizkom mora biti na vrhu (`interpolate` nad `zoom`), zato se širina ob izbiri vlaka ali avtobusa zamenja cela (`trasaSirina`), ne vgnezdi v `case`.
* **Črte na tleh so pod stavbami** (`naTleh` = `stavbe-3d`), pike in vozila nad njimi. Nad stavbami je bila v nagibu trasa narisana čez hišo, za katero leži ulica.
* **Naša proga od Leafletovega z16 pobledi, pri z17,5 izgine** (prej: pobledela na pol in ostala). Podlaga od blizu nariše vsak tir posebej; ena črta po enem od desetih tirov postaje je trdila, da vlak vozi po tistem. Kod vozi izbrani vlak, pokaže njegova pot.
* **Klik na vozilo pobarva njegovo pot** (`izberi` → `drawStops` → `narisiTraso`): naprej **oranžno kajrosa** (`IZBRANA_INK` `#f0934f`, od 4. 10. 2026; prej v barvi vozila, ki se je med enako zelenimi trasami LPP izgubila; vmes en dan rdeče), prevoženo sivo (`ZA_INK`). Trase vseh vozil (`k-vse-trase`) so v barvi prevoznika (`agency` v `/api/shapes/live`) in ob izbiri pobledijo na 0,15. Proti AP Murska Sobota je oranžna pri barvni slepoti le ΔE 3,3 (`preveri_paleto.py`) -- loči ju širina in to, da druge trase ob izbiri pobledijo, ne barva. Razrez je pri vozilu, kot je narisano; vozilo dlje od 300 m od trase (pelje na začetek vožnje) ima vso pot pred sabo. Krožna linija: med enako bližnjimi odseki tisti, ki je najbliže prejšnji legi vzdolž trase. Pot gre s kartico -- zaprta kartica, pobarvana cesta brez razlage ostane uganka. Postaja z več vlaki: oblaček pot pobarva šele ob dotiku kartice vlaka (`data-trip`), z enim takoj.
* **Trasa se začne na prvem postanku in konča na zadnjem** (`pripni.do_postaj`, 4. 10. 2026). Trase IJPP so se pri Ljubljana AP začele na stari legi postaje, 457 m zahodno; vozila čakajo na začasni (GPS pred odhodom, 561 voženj: 40 m od postanka v GTFS). Kos, ki gre mimo postanka, se tam odreže; ki ne gre, se podaljša po cesti (OSRM `/route`). Začetek dlje od 150 m: 165 → 27 tras (Ljubljana AP 111 → 1), p90 457 → 37 m.
* **Vožnja brez trase dobi pot po cesti skozi postajališča** (`pripni.brez_trase`, 4. 10. 2026). LPP v svojem GTFS za devet linij (med njimi 1B, 2, 14, 20Z) trase nima: 10 455 od 60 526 voženj, na produkciji 16 od 44 živih vozil LPP. Prej črtkana skica. Na 40 oblikah LPP, ki traso imajo, je taka pot v mediani 97 % dolžine v 20 m od prevoznikove (p10 88 %); 16 živih vozil na njih je od poti v mediani 3–5 m, največ 32 m (na uradnih trasah največ 48 m). LPP ima še 8 064 voženj z enim samim postankom v `stop_times` -- tem ne pomaga nič.
* **Kartica vozila je prosojna, premakne se z vlekom glave, skrči z gumbom –** (`omogociPremik`, 4. 10. 2026; prekrivala je traso, zaradi katere je bilo vozilo kliknjeno). Poslušalci na zunanjem elementu oblačka, ker MapLibre ob `setHTML` (vsakih 10 s) `.maplibregl-popup-content` ustvari znova; premik v `--px`/`--py`, ker `transform` oblačka nastavlja MapLibre.
* **Avtobus je narisan na cesti** (`cesta` v `/api/vehicles`, `pripni.na_cesto`): na pripeti trasi svoje vožnje, 1,9 m desno (izmerjen desni pas), v smeri ceste, kadar je GPS do 15 m od trase in smer v 60°. Med vozečimi tako 69,6 %; ostali so vožnje, ki se še niso začele, in ostanejo na GPS. **To ni ocena lege** (te na velikem zemljevidu ni, glej spodaj): ista izmerjena lega, premaknjena v mediani 4,2 m na cesto. Meritev ostane v `lat`/`lon`.
* **Vlak v 3D stoji na tiru**: `_na_postaji` ga postavi na pripeto traso (tir OSM, ne postajno poslopje); kjer tabla SŽ objavi tir in ga OSM pozna po številki (`kajros/tiri.py`, `${DATA_DIR}/tiri.json`), na tisti tir (`na_postaji.tir`, 32 % objavljenih tirov). Vlaki brez številke na isti postaji še vedno drug ob drugem (`VLAK_TIR_M`).
* Pike postaj od z15 do z18 rastejo na dvojno in ležijo na tleh (`circle-pitch-alignment: map`).

## Pogled se ne premika sam (26. 9. 2026)

Prej: zemljevid se je odprl pri z8, po prihodu vlakov in avtobusov pa `fitBounds` na njihov okvir — skok sekundo ali dve po tem, ko je človek že gledal („precej neprofesionalno"). Zdaj velja od prvega izrisa: **pogled iz naslova** (`lat`/`lon`/`z`), sicer **zadnji pogled na tej napravi** (`kajros:map-pogled` v `localStorage`, zapiše ga `moveend`), sicer **okvir Slovenije** (`bounds` v konstruktorju). Na telefonu je to trak čez sredino — isto, kar je dal okvir vozil, ko so bila razkropljena po državi; razlika je le, da ne skoči. Preverjeno prek CDP: naslov se v 8 s po odprtju ne spremeni (ni `moveend`), vlaki so na zemljevidu.

**Podatki gredo na pot ob začetku modula** (`zgodaj` v `dashboard.js`: postaje, proge, vlaki, avtobusi), med nalaganjem MapLibra — prej so čakali na slog in drug na drugega. `pollVehicles(url, onData, prva)` vzame že začeto zahtevo. **V aplikaciji domača stran potegne zemljevid vnaprej** (`data-vnaprej` na `.domov`, `<link rel=prefetch>` ob mirovanju): MapLibre 1,1 MB (okrog 300 kB stisnjeno), `dashboard.js`, slog. Naslovi morajo biti natanko taki kot v `dashboard.html`, sicer predpomnilnik ne zadene. V brskalniku ne — prenos bi plačal vsak obiskovalec domače strani.

## 3D od blizu (vsi zemljevidi)

Od daleč raven zemljevid; od Leafletovega **z15** se kamera nagiba, pri **z17,5** 60°; hkrati se stavbe dvignejo od ploskve do prave višine (`render_height` iz OSM). Prelivanje, ne skok, je bila želja (22. 9. 2026, po Slometovem zemljevidu, od koder formula nagiba in razpon zoomov). Stikalo „3D od blizu“ privzeto vklopljeno.

* **Leaflet nagiba ne zna** → vsi zemljevidi samo MapLibre. Ovoj `leaflet-maplibre-gl` je MapLibrovo kamero držal v Leafletovi ravnini — zato okno vožnje do 25. 9. 2026 ni imelo 3D, veliki zemljevid pa ga je imel.
* **Okno vožnje nagib in stavbe dobi iz `pkUstvari()`** (`pot_karta.js`), stikala nima. **Od blizu je avtobus tudi tam model** (25. 9. 2026, na prijavo: „ko približaš, je vozilo še kar 2D“) — oblika in barve prevoznikove, kot na velikem zemljevidu (od 4. 10. 2026; prej barva ocene `#a8d8ff`, glej spodaj). Prosojnega modela plast 3D ne zna; da stoji na oceni, pove podnapis. Meja (`AVTO_3D_OD`) in velikost (`avtoPovecava`) v `vozila3d.js`, ker ju rabita oba zemljevida. Od daleč ostane ikona kot DOM (`rotationAlignment: map`, `pitchAlignment: viewport`), ker se premika vsako sekundo in je ena; ko je model viden, je ikona skrita, sicer bi ga kot element nad platnom prekrila.
* **Nagib = lastnost približka**, ne gesta: `transformCameraUpdate` ga postavi ob vsaki spremembi kamere, `touchPitch` in `pitchWithRotate` ugasnjena, da se ne prepirata. Vrtenje ostane, kompas vrne sever.
* **`z` v naslovu ostane v Leafletovih enotah** (MapLibrov zoom + 1), ker ga delijo drugi (`train.js` pelje na `&z=15`) in vse meje na strani (`LZ` v `dashboard.js`).
* **Vlaki DOM, avtobusi plast.** Oznaka vlaka = HTML z več vrsticami in značko, vlakov nekaj deset; avtobusov ob konici 1 530, DOM bi pri vsakem premiku vsakega prestavljal posebej. Avtobus v nagibu stoji **obrnjen proti gledalcu** (`icon-pitch-alignment: viewport`): položen na cesto je bil pri 60° za pol nižji, med stavbami ga je bilo težko najti.
* **Stavbe pod napisi**, sicer stavba pokrije ime ulice za sabo. Naše plasti in zatemnitev nad stavbami.
* **Cena v podatkih majhna**: OpenFreeMap ima ploščice do z14, nad tem se povečujejo, zato nagib doda kvečjemu kakšno ploščico na obzorju. Izmerjeno (Ljubljana, Chromov dnevnik omrežja): telefon pri z17 **2 ploščici z 3D in brez**; namizje 1400 × 900 pri z16 4 in 4, pri z17,5 **4 (786 kB) proti 2 (451 kB)**. Cena = risanje stavb, zato stikalo.
* **Brez WebGL2 zemljevida ni**; stran to pove z dvema povezavama; iskalnik in plasti se skrijejo, ker brez zemljevida ne naredijo ničesar.
* **Ikona avtobusa od zgoraj** (4. 10. 2026): svetlo vetrobransko steklo spredaj (temno se pri 15–26 px ni videlo, smeri ni bilo mogoče razbrati), temno zadnje, telo enodelno za vse -- LPP v dveh delih (zgibni) je bil en dan in zmeden. Od Leafletovega z14 **številka linije** ob avtobusu LPP (`OZNAKA_OD`, `text-optional`: številka se skrije, vozilo ne) -- pri medkrajevnih je v feedu številka vožnje (A6325), ki je na vozilu ni, zato brez. Izbrano vozilo ima **tanek oranžen obroč s sijem** (`k-izbrano`, `k-izbrano-sij`; debel kolobar je bil štorast), od blizu dovolj velik za model v 3D (`obrocIzbranega`).
* **Od Leafletovega z16 so avtobusi 3D modeli** (`vozila3d.js`), pod tem ikone. Meja tam, kjer se kamera že vidno nagne; od zgoraj bi bil model bela škatla. Vsak prevoznik ima **svoj model in barve**: LPP zgibni mestni 18 m (148 od 224 njegovih avtobusov zgibnih), Arriva, Nomago in AP Murska Sobota medkrajevni 12 m; barve z njihovih logotipov in strani. **Streha nosi barvo z legende**, ker se od zgoraj vidi samo streha.
* **Modeli goli WebGL2 v plasti po meri**, ne three.js (Slomet ga ima za en GLTF): three.js 172 kB stisnjen, dobra polovica MapLibra (299 kB), za nekaj škatel ni vreden nove odvisnosti. Vsa vozila istega modela = en klic risanja (instanciranje). Lega gre v senčilnik kot odmik od izhodišča v Sloveniji — absolutni Mercator v float32 bi pri z18 trepetal za metre.
* **Model večji od resničnega**: pri z16 ~36 px kot ikona, pri z19 1,7-krat (`povecava3D`). Plasti damo samo vozila v sliki in pas okrog nje (`posodobi3D` ob premiku). `queryRenderedFeatures` plasti po meri ne vidi, zato dotik išče sam (`zadetek3D`: razdalja do lege, polmer pol modela).
* **Vlak je 3D samo tam, kjer JE** (28. 9. 2026): stoji na postaji po voznem redu in zamudi (`api._na_postaji`, polje `na_postaji` v `/api/live`) ali na njem delita lego vsaj dva potnika, ki se ujemata (`naPotnikovi()`; en sam je lahko že izstopil in čaka na peronu — od 1. 10. 2026). Med postajama ostane ploščica tudi od blizu — model na zadnji postaji z meritvijo bi trdil, da vlak stoji tam, kjer ga že davno ni. Isto pravilo kot avtobus (3D = GPS).
  * **`_LIVE_SQL` šteje postajo za prevoženo šele ob odhodu**, zato je vlak med postankom na X prej ves postanek kazal na prejšnji postaji. Zdaj med postankom stoji na X (skupina `stoji:X`, kartica „po voznem redu in zamudi zdaj stoji tu“) — sklep, ne meritev: SŽ za postanek objavi eno zamudo (prihod ≠ odhod pri 3,1 % postankov), sklepano okno se z oknom iz zapisanih zamud prekriva **70 % časa** (26 705 postankov nad minuto, 10.–27. 9. 2026). Postanek brez čakanja v voznem redu ni nikoli „stoji“.
  * **Model po vrsti vlaka, ne po garnituri**: sestave SŽ ne objavijo nikjer berljivo. Regionalni = FLIRT (510/610), ICS = KISS (313), IC/EC/EN/AVT = Taurus (541) z vagoni, nadomestni = avtobus. Podoba, ne trditev; barve in razmerja s fotografij na Wikimedia Commons. Siva streha z oranžnim pasom z legende (cela oranžna streha je od blizu prevladala nad vozom).
  * **Svoja povečava** (`vlakPovecava`, 2,4-krat pri MapLibrovem z15, od z18 prava velikost): z avtobusno bi 60–100 m garnitura prekrila pol postaje. Več vlakov na isti postaji stoji drug ob drugem, en tir narazen (`odmik` v senčilniku, raste z modelom); vlak v nasprotni smeri dobi nasprotni predznak.

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

**Meritev od ocene loči oblika, ne barva** (od 4. 10. 2026). Vozilo je v barvi prevoznika (vlak oranžen), **prosojno s črtkanim svetlim obrisom** -- stoji na oceni lege. Do tedaj je bilo v barvi ocene `ESTIMATE_COLOR` (`#a8d8ff`); odkar je Arriva na velikem zemljevidu modra (`#6fb8ff`, ΔE 9,6), se je LPP v oknu vožnje bral kot Arriva (prijava). Ključ v legendi je v barvi vozila (`inkVozila`). **Pot in postajališča so kot pri izbranem vozilu na velikem zemljevidu** (4. 10. 2026, prej zelena): pred vozilom oranžno `IZBRANA_INK`, prevoženo sivo, razrez pri oceni lege (`narisiRunTraso`, osveži se ob novih podatkih in na 30 m premika, ne vsako sekundo); od blizu nadstreški in znaki (`slojiPostajalisc`, iz `vozila3d.js`, kot na velikem). Potnikova postaja je bela, ker bi se oranžna na oranžni poti izgubila. Barve zemljevidov so v `common.js` (`AGENCY_INK`, `IZBRANA_INK`, `ZA_INK`). Zadnja **izmerjena** lega = **rdeča** pika s svetlim obročem: rdeča ni iz nobene lestvice (ne zamud, ne razmer), tu ne more pomeniti drugega. Pika se **dvigne nad traso** (`bringToFront()`): črta in pika v isti plasti, vrstni red risanja = vrstni red dodajanja, 3 px široka trasa jo je prerezala, videti kot del proge. Riše se vedno — kadar vozilo stoji, jo oblika vozila pokrije, dveh oznak ni videti. Pod zemljevidom enovrstična legenda; brez nje je prosojen avtobus ob rdeči piki uganka, razlika med njima pa je bistvo okvira.

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

**Na velikem zemljevidu tega ni** — odločitev, ne opustitev: tam je vprašanje „kje je vse skupaj", ocena za osemdeset vozil = osemdeset izmišljenih leg. V oknu vožnje gledaš eno vozilo, vprašanje je natanko „kje je zdaj". (Avtobus na cesti, `cesta`, ni ocena: ista izmerjena lega, pripeta na traso, ne premaknjena naprej v času.)

**Trasa se skoraj nikoli ni risala.** Pogoj `trasa.length > 1` napisan, ko je bil `points` ravna lista točk; odkar jih uvoz reže na kose (`SHAPE_BREAK_M`), je enodelna trasa dolga 1 in pogoj je ni spustil. To je bilo **2 706 od 2 897 oblik, torej 93 %** — v oknu vožnje in na velikem zemljevidu. Pravilen pogoj: „vsaj en kos z vsaj dvema točkama".

**Okno vožnje z lego ima živ zemljevid, v preprostem pogledu.** „Kje je zdaj" je pri avtobusu prvo vprašanje. MapLibre se naloži šele, ko lega res obstaja; prazen okvir bi obljubljal podatek, ki ne obstaja. Lega je GPS ali, pri vozilu brez njega (vlaki, nadomestni prevoz, ~10 % avtobusov), **lega vsaj dveh potnikov, ki se ujemata** (od 1. 10. 2026) — isto pravilo kot veliki zemljevid. Oboje pride po isti poti, `/api/vehicles?trip=` (`api._vozilo_po_potnikih`, vrstica z `vir: "potniki"`), ritem pa pove strežnik v `X-Osvezi-Cez`: GPS ob naslednjem branju (10 s), potniki na 5 s (kolikor pošiljata odjemalca), vlak brez potnikov na 30 s. Ko poročila zastarajo, okvir izgine. Med poročili vlak drsi po trasi s potnikovo hitrostjo, na postaji 45 s (`POSTANEK_VLAK_S`, meritev v `docs/MERITVE.md`).

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

## Avtobusi: plast na prevoznika, prižgani od približka

**Ena skupna avtobusna plast je zemljevid zadušila.** Ob 15:10 na njem 1 530 vozil, slika zelena kaša, posameznega avtobusa ni bilo mogoče najti. Zato **vsak prevoznik svoja plast in svoje potrditveno polje**.

**Privzeto ugasnjeni (do 1. 10. 2026) so bili napaka.** Zemljevid se je odprl kot železniški in potnik je sklepal, da medkrajevnih avtobusov ni mogoče spremljati (komentar na Facebooku), čeprav ima GPS 90 % voženj. Zdaj **vsi prižgani, kaša se rešuje s približkom**: mestni LPP (`agency = 'lpp'`) od z12 (`MESTNI_OD`), vsi ostali od z9 (`AVTOBUSI_OD`) — pri obeh pragovih je gneča enaka (61 % vozil ima drugo vozilo bližje od pol ikone), meritev v `docs/MERITVE.md`. Pod pragom pove opomba (`opombaPriblizka()`, deli si jo s postajališči), da se pokažejo, ko približaš. Prag je v filtru plasti (`["zoom"]`), ki vidi celoštevilski zoom ploščice — zato cela števila.

* **V shrambo gre samo, kar človek prestavi** (`setLayer(…, zapomni)`). Stara koda je ob vsakem odprtju zapisala vsa stikala, zato je imel vsak obiskovalec shranjeno „ugasnjeno“, ki ga ni izbral; ključi so zato novi (`kajros:map-avtobus-*`, prej `bus-*`).
* **„na velik zemljevid“ iz okna vožnje nosi `&trip=`**: zemljevid prižge plast prevoznika samo za ta ogled (ne v shrambo), odpre kartico in traso, nato `trip` iz naslova odstrani.

Barve preverjene (ne izbrane na oko) s `scripts/preveri_paleto.py`:

| | | |
|---|---|---|
| LPP | `#4db97f` | zelena |
| Arriva | `#6fb8ff` | modra |
| Nomago | `#9d7ae0` | vijolična |
| AP Murska Sobota | `#c9a227` | zlata |

Najslabši par pri deutan/protan **ΔE 9,6** (prag 3, „na prvi pogled“ 6), pri tritanopiji 4,8. Proti lestvici zamud zelena in oranžna pri deutanu trčita (ΔE 1,2), a to ni težava: **vozila loči oblika** — avtobus oblika vozila od zgoraj, vlak ploščica — in oznaka poleg nosi ime prevoznika. Barva nikoli ne nosi pomena sama; pravilo projekt že ima.

**LPP ima dva `agency_id`, na zemljevidu eno vrstico.** `1118` = primestne linije iz IJPP, `lpp` = mestne iz lastnega vira. Ključa `lpp` v `BUS_LAYERS` ni bilo, zato so mestni avtobusi padli med „druge prevoznike" — **104 od 179 živih vozil na produkciji** (7. 9. 2026), torej večina, za stikalom, ki je privzeto ugasnjeno in se imenuje, kot da prevoznika ne poznamo. Zdaj oba ključa skozi `agencyKey()` v isto plast, isti števec, isto barvo.

Zakaj ena vrstica, ne dve: na postajališču piše oboje „LPP", številke se med viroma ne prekrivajo (mestne 1–27, primestne 40–84), zemljevid odgovarja na *„kje je moj avtobus"*. Statistika ju loči (`stats.AGENCY_NAMES`: „LPP mestni" / „LPP primestni"), ker tam vprašanje ni isto — zamuda mestne in primestne linije sta dve različni stvari.

**Peta vrstica „Drugi prevozniki" ni okras.** Če v zajem pride nov prevoznik, bi njegova vozila brez nje tiho izginila — plast brez stikala = plast, ki je ni. Vrstica se skrije, kadar je števec 0.

**Gumb za nastavitve zgoraj desno — draga lekcija.** Dvakrat je bil spodaj, dvakrat ga uporabnik ni videl:

1. kot vrstica v barvi podlage se je zlil z navedbo vira;
2. kot plavajoča tipka 14 px nad dnom je izginil **pod Chromovo spodnjo naslovno vrstico**. Ta prekrije dno postavitvenega okna, ne da bi ga skrajšala, zato `bottom: 0` ni viden. Dokaz: opomba o skritih oznakah, postavljena 66 px nad dnom, se je na telefonu risala **tik nad** URL vrstico → spodnjih 66 px prekritih.

**Dna zaslona v brskalniku ne uporabljaj za nadzor**, ki ga mora uporabnik najti. Zgornji desni kot edini, ki ga noben brskalnik ne prekrije — tam že stoji tipka za lastno lego, zato se dve okrogli tipki druga pod drugo bereta kot orodji zemljevida. Uporabnik lego **potrdil na svojem telefonu** (3. 9. 2026); prejšnji dve padli, ker potrjeni samo na posnetku brez zaslona. Posnetek namizja ne dokaže dosegljivosti na telefonu.

Ker je na tipki ikona, ne besedilo, mora imeti `aria-label`.

**`display: flex` povozi `[hidden]`.** Vrstica „Drugi prevozniki" se je kazala kljub ničli, ker ima `.layer` svoj `display`. Potrebno izrecno `.layer[hidden] { display: none; }`.
