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
# Zemljevida: veliki in v oknu vožnje

## Zemljevid

* **Edini skupni pogled.** Vlak = ploščica na zadnji postaji z meritvijo ali na postaji, kjer po voznem redu in zamudi stoji; avtobus = **oblika vozila** na izmerjeni legi (15–34 px), v smeri vožnje.
* **Postaja iz poročila SŽ ni lega vlaka** (je cilj, `zajem.md`): na kartici vrstica „napoved prevoznika → Ljubljana · +15 min · ob 21:20“; zamuda, barva, kraj iz meritve.
* **Vlak = znak na postaji** (`trainSvg`): oranžna pokončna ploščica z vlakom od spredaj. Zavrnjeno: vlak od zgoraj („zgleda kot bus“), obroč okoli ikone. Oznaka = napis z obrobo iz senc.
* **Ime na dotik, odide po 5 s** (`common.NAME_MS`) — avtobusna postajališča in pike na poti izbranega; železniška postaja odpre oblaček z odhodi. Brez gumba za zapiranje. Klik ustavi razširjanje (sicer zapre spodnjo ploščo). Pika 3,4 px. `zadetek()` (`dashboard.js`) in `runImeNaDotik()` zadeneta v **12 px** od prsta, vozilo prednost.
* **Avtobusna postajališča = plast, privzeto ugasnjena** (9 519, 211 kB, ob prvem vklopu), od **z13** (z12 600, z11 1 694 — mreža izgine); pod pragom pove zakaj. Železniške postaje privzeto vklopljene (271).
* **Od blizu nadstrešek ali znak**: pika v barvi prevoznika (več prevoznikov `SKUPNA_INK` `#d5dae2`). Od `NADSTRESKI_OD` (= `AVTO_3D_OD`) nadstrešek ob cesti (povečan 2–3×), stran po `desno`, ≥ `ROB_M` 3,8 m od osi. **Avtobusna postaja** („AP“ ali končna ≥ 20 tras dveh prevoznikov) = znak na drogu že od daleč. Brez smeri (> 15 m od trase) znak od blizu. Podatki v `postajalisce` (`pripni.postajalisca`), `/api/stations?network=avtobus`. Samo v sliki (`posodobiNadstreske` v `posodobi3D`).
* Vsaka plast se izklopi posebej (vlaki, avtobusi, proge, **trase vozil**, postaje, postajališča, podlaga, dodatna imena). Trase privzeto ugasnjene (444 oblik, ~870 kB) — osvežitev na 5 min, ETag po naboru (304).
* **Trase so lahko pretrgane** — ravna črta čez pol Slovenije = laž. Uvoz reže na kose (`gtfs.SHAPE_BREAK_M`; točke 514 m pri 99,9 %, nato skok na 22,8 km). Na poenostavljenih točkah praga ni mogoče postaviti. **Pogoj risanja = vsaj en kos z ≥ 2 točkama** (`trasa.length > 1` je izpustil 93 % oblik).
* **Iskalnik vozila** namesto lestvice zamud; najde tudi postaje (`common.naloziKazalo()`, največ štiri; z besedo nad vozili, s številko pod).
* **Podlaga = vektorska OpenFreeMap** (MIT, brez ključa), riše **MapLibre GL JS 6.10 povsod, brez Leafleta**; gostovan pri nas (`static/maplibre-6.10.0/`, različica v **poti** — `maplibre-gl.mjs` uvaža po relativnem imenu, Cloudflare drži statiko 4 h). Tuje: `tiles.openfreemap.org`.
  * **Slog je naš** (`static/podlaga.json`): `name:sl` pred lokalnimi, „Četrtna skupnost“ odrezana. Barve po Slometovi (kopno `#232d39`, voda `#2b4153`). Tiri s pragovi (glavni z12,5, stranski z15), poti za pesce, imena točk od z16. `metadata.kajros:napisi = dodatni` = stikalo „Dodatna imena krajev“. Meje v MapLibrovih enotah (Leaflet = +1).
  * **Esri = rezerva** (`naEsri()`, `pkEsri()`), le če slog pade **pred prvim izrisom**. Brez WebGL2 zemljevida ni nikjer — stran to pove.
  * Stikala „Zatemni podlago“ ni (napisi so svoje plasti).
  * Navedba vira v slogu (`sources.omt.attribution`), povsod gumb (i). **Privzeto zaprta** (`common.zapriNavedbo`, 22. 10. 2026): MapLibre jo razpre in zapre šele ob vleki; smernice OSMF dovolijo samodejno zapiranje po 5 s in je ne zahtevajo ob vsakem odprtju → razprta samo prvič na napravi, 5 s (`kajros:navedba`).
  * Cena: država na telefonu 1,27 MB, Ljubljana z15 1,0 MB; ploščice `max-age` deset let.

## Železniška postaja in ovire na progi

* **Ena pot do postaje** (`odpriPostajo`): dotik pike, iskalnik, „odhodi s postaje X ›“ v oblačku vlakov. Kartica: 3 odhodi, zapore na postaji, „cela odhodna tabla ›“. `/api/departures?network=zeleznica` šele ob dotiku (2,5 kB), osveži `pollLive`.
* **Ista pravila kot tabla**: `razvrstiTablo`/`nepotrjen` v `common.js`, `delayText`/`delayColor`, `tirHtml`, „lahko do“ iz `do_s`. Nadomestni „po voznem redu“; brez meritve „običajno · N voženj“.
* **Plast „Ovire na progi“** (`/api/zapore?dan=`, privzeto prižgana): `Feature` na zaporo, odseki iz `edge` (`osm`, sicer `geojson`), `okna`, `stanje` (`zdaj` / `pozneje` + `zacne` / `koncano`). `OVIRA_INK` `#f2d36b` črtkana; velja 4,5 px, končana bledi na pol. Nad progo in potjo izbranega, pod pikami in vozili. Dotik: „danes 8.00–16.00 · velja zdaj“ (`common.kdajZapore`), povezava na `/app/ovire`.
* **Stanje računa strežnik ob vsaki strežbi**, geometrija predpomnjena (`alerts_etag`, 5 min). Zemljevid vpraša na minuto.
* Barva preverjena (`preveri_paleto.py`): najslabše ΔE 5,2 proti 1–5 min — loči oblika (črtkana) in beseda.

## Od blizu: trase na cesti

* **Trase pripete na OSM** (`pripni.py`, lastni OSRM `deploy/osrm/avtobus.lua`, `tir.lua`, `deploy/osrm.sh`): od osi 3,1 m → 0,4 m. `shape.osm`, `edge.osm`; surova ostane. Brez OSRM kot prej.
* **Širina v metrih od MapLibrovega z16** (`sirinaM` v `common.js`): izbrani avtobus 7,5 m, vlak 3,2 m, vse trase 2,5 m; ceste in tiri podlage (`metadata.kajros:sirine`). `interpolate` nad `zoom` mora biti na vrhu → ob izbiri se zamenja cel izraz (`trasaSirina`).
* Črte na tleh pod stavbami (`naTleh` = `stavbe-3d`), pike in vozila nad.
* Naša proga od Leafletovega z16 bledi, pri z17,5 izgine (podlaga riše vsak tir).
* **Klik na vozilo pobarva pot** (`izberi` → `drawStops` → `narisiTraso`): naprej **`IZBRANA_INK` `#f0934f`**, prevoženo `ZA_INK`. Trase vseh (`k-vse-trase`) v barvi prevoznika, ob izbiri bledijo na 0,15 (proti AP MS ΔE 3,3 — loči širina in bledenje). Vozilo > 300 m od trase ima vso pot pred sabo. Krožna linija: odsek najbližji prejšnji legi. Pot gre s kartico. Postaja z več vlaki: pot ob dotiku kartice (`data-trip`).
* **Kjer vozila res vozijo drugje, trasa gre za njimi** (`opazovano.trasa_po_obvozih`, `/api/trip/{id}/shape`): pot vozil (sled, pripeta z OSRM) namesto objavljenega odseka, zato ocena lege, razrez poti in razdalja do potnika delajo brez nove veje. `po_voznem_redu` = objavljeno, črtkano v `OVIRA_INK` z napisom (`k-trasa-skica`, `run-po-voznem-redu`), skrito postajališče rumeno. 44 od 46 odsekov; konca dlje od 150 m od trase: ostane objavljena.
* **Trasa od prvega do zadnjega postanka** (`pripni.do_postaj`): odreže ali podaljša po cesti (OSRM `/route`); začetek > 150 m 165 → 27. **Konca da najdaljša vožnja trase**: skrajšana bi traso odrezala na svojem postanku (30. 10. 2026: 59 tras, LPP 18 brez 12 od 30 postankov).
* **Vožnja brez trase = pot po cesti skozi postajališča** (`pripni.brez_trase`; LPP devet linij, 10 455 od 60 526 voženj): 97 % dolžine v 20 m od prevoznikove.
* **Kartica vozila prosojna, vleka glave premakne, – skrči** (`omogociPremik`): poslušalci na zunanjem elementu (MapLibre `setHTML` ustvari vsebino znova), premik v `--px`/`--py`.
* **Končana vožnja** (`koncana` v `/api/vehicles`, `api._voznja_koncana`): izmerjena končna in GPS nad 120° proti trasi ali nad 300 m od nje. Feed LPP vozilo drži na stari vožnji, ko že pelje nazaj (LPP 9: 8 min). Pot vsa prevožena, ocena ne drsi, kartica „vožnja končana“. Model po GPS ima prav.
* **Avtobus na cesti** (`cesta` v `/api/vehicles`, `pripni.na_cesto`): na pripeti trasi, 1,9 m desno, kadar GPS ≤ 15 m in smer v 60° (69,6 % vozečih). **Ni ocena lege** — ista meritev, mediana 4,2 m; `lat`/`lon` ostaneta.
* **Vlak v 3D na tiru**: `_na_postaji` na pripeto traso; s tirom s table in številko v OSM (`tiri.py`, `${DATA_DIR}/tiri.json`, `na_postaji.tir`) na tisti tir. Sicer drug ob drugem (`VLAK_TIR_M`).
* Pike postaj od z15 do z18 rastejo na dvojno, `circle-pitch-alignment: map`.

## Vozilo iz naslova

`?trip=` in/ali `?vozilo=` (`pokaziVoziloIzNaslova`): najprej vožnja, sicer vozilo (lahko je že na naslednji). Vozilo zunaj slike: pogled gre tja, lat/lon povezave je lahko star. Ni ga: napis 5 s, ne tišina (fantom LPP 19B, 1. 11. 2026).

## Pogled se ne premika sam

Od prvega izrisa: **pogled iz naslova** (`lat`/`lon`/`z`), sicer **zadnji na napravi** (`kajros:map-pogled`, `moveend`), sicer **okvir Slovenije** (`bounds`). Nobenega `fitBounds` po prihodu vozil. Izjema: izbrani avtobus na oceni (spodaj).

**Podatki na pot ob začetku modula** (`zgodaj` v `dashboard.js`); `pollVehicles(url, onData, prva)` vzame začeto zahtevo. **Avtobusi ne čakajo postaj**: zanka leg pred `await loadStatic()` (hladne postaje 6,7 s). **V aplikaciji domača stran potegne zemljevid vnaprej** (`data-vnaprej`, `<link rel=prefetch>`); naslovi natanko kot v `dashboard.html`. V brskalniku ne.

## 3D od blizu

Od Leafletovega **z15** nagib, pri **z17,5** 60°; stavbe rastejo do `render_height`. Stikalo „3D od blizu“ privzeto vklopljeno.

* Okno vožnje in pot (`/app/pot/podrobno`) 3D iz `pkUstvari()` (`pot_karta.js`), brez stikala; od blizu je vozilo model (meja `AVTO_3D_OD`, velikost `avtoPovecava`/`vlakPovecava` v `vozila3d.js`). Od daleč ikona kot DOM (`rotationAlignment: map`, `pitchAlignment: viewport`), skrita ob modelu. Ikona od zgoraj `voziloSvg` v `vozila3d.js` (veliki zemljevid in pot; okno ima svojo, ker je vedno na oceni).
* **Nagib = lastnost približka** (`transformCameraUpdate`), `touchPitch` in `pitchWithRotate` ugasnjena.
* **`z` v naslovu v Leafletovih enotah** (MapLibre + 1; `train.js` pelje na `&z=15`, `LZ` v `dashboard.js`).
* **Vlaki DOM, avtobusi plast** (1 530 v konici). Avtobus v nagibu `icon-pitch-alignment: viewport`.
* Stavbe pod napisi.
* Cena nagiba ~ploščica na obzorju (OpenFreeMap do z14); cena = risanje stavb.
* **Ikona avtobusa od zgoraj**: svetlo vetrobransko spredaj, enodelno telo. Od Leafletovega z14 številka linije ob LPP (`OZNAKA_OD`, `text-optional`); medkrajevni brez (šifra ni na vozilu). Od `AVTOBUS_3D_OD` na strehi modela (`OZNAKE_3D`, svoji plasti, vedno vidna): s plastjo ikon je izginila in vozil se ni dalo ločiti. Izbrano: tanek oranžen obroč s sijem (`k-izbrano`, `k-izbrano-sij`, `obrocIzbranega`).
* **Od Leafletovega z16 avtobusi 3D modeli** (`vozila3d.js`): LPP zgibni 18 m, ostali 12 m, barve prevoznika, **streha v barvi legende**.
* **Goli WebGL2 v plasti po meri, ne three.js** (172 kB za nekaj škatel). Instanciranje; lega kot odmik od izhodišča v Sloveniji (float32 bi trepetal).
* Model večji od resničnega (`povecava3D`); v plast le vozila v sliki (`posodobi3D`). Dotik išče sam (`zadetek3D`).
* **Vlak 3D samo tam, kjer JE**: na postaji po voznem redu in zamudi (`api._na_postaji`, `na_postaji` v `/api/live`) ali s potnikom (`naPotnikovi()`, `verodostojno`; dovolj en, `deljenje.md`). Med postajama ploščica.
  * Med postankom stoji na X (`stoji:X`, „po voznem redu in zamudi zdaj stoji tu“) — sklep (70 % časa se prekriva z zapisanim). Postanek brez čakanja nikoli „stoji“.
  * Model po vrsti: regionalni FLIRT (510/610), ICS KISS (313), IC/EC/EN/AVT Taurus (541) z vagoni, nadomestni avtobus. Podoba, ne trditev.
  * `vlakPovecava` (2,4× pri z15, od z18 prava velikost); več vlakov drug ob drugem (`odmik`).

## Ocena lege (okno vožnje in izbrani avtobus)

**Med meritvama pika drsi po trasi**: `hitrost × starost` vzdolž trase, vsako sekundo. Lega ob strežbi ~30 s stara (50 km/h = pol km). Na 79 primerih:

| kaj naredimo s piko | mediana | v 100 m |
|---|---|---|
| pustimo pri miru (prej) | 63 m | 63 % |
| premaknemo po smeri (`bearing`) | 36 m | 72 % |
| **premaknemo po trasi** | **30 m** | **80 %** |

* Ne premikamo stoječega (`speed_ms < 1`), > 120 m od trase, nikoli čez konec. Podnapis „ocena · GPS pred 42 s“ (beseda od `OCENA_VIDNA_M`, 40 m).
* **Na oceni vozilo gleda po trasi**: smer = tetiva od repa do čela **narisanega** vozila (`smerNaOceni`); 324 parov: mediana 5,6° → 2,4°.
* Samo LPP (mestni in 1118) — Arriva, Nomago, AP MS hitrosti ne pošiljajo, stojijo na meritvi s smerjo iz feeda.
* **Meritev od ocene loči oblika, ne barva**: vozilo v barvi prevoznika, na oceni **prosojno s črtkanim obrisom**; zadnja izmerjena lega **rdeča** pika s svetlim obročem (`bringToFront()`), vedno narisana. Pot razreže ocena (`narisiRunTraso`, osveži na 30 m premika): naprej `--accent-lit`, prevoženo `ZA_INK`. Barve v `common.js` (`AGENCY_INK`, `ZA_INK`, `MERITEV_INK`). Legende ni — oceno pove podnapis.
* **Na velikem zemljevidu ne za vsa vozila** — 80 ocen = 80 izmišljenih leg.
* **Izjema: izbrani avtobus s `speed_ms`** (19. 10. 2026): mestni LPP po 60 s stoji 374 m → ocena 106 m (n=165), po 120 s 677 → 198. Ista koda kot okno (`ocenaNaTrasi`, `smerNaOceni`, `polAvtobusa`).
  * Brez novih zahtev (trasa iz `drawStops`, lega iz `/api/vehicles`).
  * Svoja plast z enim vozilom (`k-avtobus-izbran`, `filtrirajAvtobuse`) — `setData` na ~600 vozilih 4,8–19 ms, izbrani 1,9 ms. Korak ne bere `clientWidth`.
  * Oblika kot okno (`obrisOcene`, `k-izbrano-meritev`, `MERITEV_INK`), kartica od `OCENA_VIDNA_M` (40 m). Obroč, kartica, model in razrez na `legaVozila`; plast vseh na `legaIzmerjena`.
  * **Pogled gre za izbranim, dokler ga človek ne povleče** (`drziVSliki`, rob 15 %, `dragstart`).
  * Ob novi meritvi ocena skoči; glajenja namenoma ni.
  * Skrit zavihek ne računa.
* **Izjema: vlak s potnikom**: `/api/vehicles?trip=` na 5 s, drsi z `ocenaNaTrasi` (`POSTANEK_VLAK_S`); na 30 s poročilu mediana 244 m, ocena 31 m. Po 15 s (`POROCILO_STARO_S`) prosojna ploščica „poročilo pred N s“, po `deljenje.SVEZE_S` (120 s) nazaj na feed. Indigo značka, brez utripa. Skupna koda `ocenaZdaj`, `trasaZaOceno`, `premakniPotIzbrane`.
* **Rep za vlakom s potnikom**: indigo črta zadnje 3 min (`deljenje.REP_S`), `line-gradient` (`lineMetrics`); na oceni do vlaka črtkano. Začetek pošlje strežnik (`rep`, `deljenje.rep_od`); prve tri minute repa ni. Od Leafletovega z10. Avtobusi ne.
* **Lastna lega teče sama, kadar je dovoljenje že dano** (David, 22. 10. 2026); **okna za dovoljenje ne odpremo sami** — samo dotik (gumb lege, „Vklopi“ na domači). Ena pot: `LEGA` v `common.js` (en `watchPosition` na stran, samo vidna stran, ob vrnitvi lega > 60 s pade), `stanjeLege()` (`dano`/`vprasaj`/`zavrnjeno`/`neznano`; v aplikaciji iz mostu), gumb `poisciMe()`. **Pogled se za piko ne premakne**; gumb ga premakne k tebi, drugi dotik na velikem zemljevidu piko skrije za ta ogled. `#2f7fff`, **obroč točnosti obvezen**. Na velikem zemljevidu **pika nad vozili** (oznaka DOM `.me-pika`, z-index 2 med vlaki 1 in oblački 3), obroč plast na tleh pod njimi (David, 22. 10.). Lege ne beri mimo `common.js` (`tests/test_lega.py`; izjema `deli.js`).
* **Razdalja do vozila po poti** (`projekcijaNaTraso`), z **ocenjeno** lego. Nad **1 km** od proge (`OB_PROGI_M`) ne računamo; tudi ne, ko je **vozilo** dlje od `NA_TRASI_M` (300 m, `common.js`) od trase — lega ni na poti (pelje na začetek ali je feed prištel drugo vozilo; 22. 10. avtobus na avtocesti „še 420 m“). Mestni LPP v živo: 105 od 109 v 50 m, 2 nad 2 km (na končni, prišteta sosednji vožnji). Zgodovine leg mestnega LPP ni (`lega` ima samo NAP). „Do tebe ima še 1,2 km poti“ / „Tvojo lego je že prevozil — 420 m naprej po poti“. Brez dotika gumba se vrstica pokaže samo, ko je razdaljo mogoče izmeriti (`razdaljaDoMene`); razlog, zakaj je ni, šele po dotiku.

## Okno vožnje (osnutek E, David 23.–24. 10. 2026)

* **Vrh = en postanek in koliko še do njega** (`ciljOkna`): tvoj (`postaja` v naslovu) › pred odhodom izhodišče › cilj. Odštevanje v obliki, ura, pod njo **žeton ob prečrtanem voznem redu** („vozni red ~~11:11~~ +21 min“; ob veliki uri se je bral kot seštevek, 28. 10. 2026), beseda vira (`izmerjeno` / `zadnji podatek` / `običajno` / `v živo`; naša napoved **brez besede** — „ocena“ se je brala kot gumb, 28. 10. 2026), tir, vreme. Isti vrh riše kartica na zemljevidu avtobusa (`kartaOdstHtml`), budilka bere isto številko (`vrhOkna`). 20 min po pričakovani uri brez potrditve „ni potrditve“ (`NEPOTRJEN_MIN` = `stats.NEPOTRJEN_ODHOD_S`).
* **Avtobus ima zemljevid vedno, vlak nikoli** („je itak samo tir“). Avtobus: pot naprej v barvi omrežja, prevoženo sivo, postajališča, tvoje belo z imenom (stran imena po legi na zaslonu). Vozilo z lego: GPS ali **verodostojna lega potnikov** (`deljenje.md`), avtobus z GPS dobi potnikovo, kadar je novejša; `/api/vehicles?trip=` (`api._vozilo_po_potnikih`, `vir: "potniki"`), ritem v `X-Osvezi-Cez` (GPS 10 s, potniki 5 s).
  * Brez lege pilula pove zakaj (`pilulaBrezVozila`): „odpelje ob“, „še na prejšnji vožnji“ z vozilom verige na njegovem GPS (`postaviVoziloVerige`), „lege vozila ni“. Pot reže zadnja meritev. Prazen zemljevid brez besede je videti kot okvara.
  * Prvi pogled počaka prvo lego ≤ 1,5 s (`zacetniPogled`). Nato gre za vozilom samo, ko uide iz vidnega dela — čez rob ali pod kartico odštevanja (ocena lege odpelje pol kilometra od meritve) —, in to le, dokler ga človek ne povleče (`drziVozilo`, `dragstart`). (i) zgoraj desno (spodaj kartica čez vso širino; na 360 px je odrezala ime), +/− samo pri `pointer: fine`, brez vrtenja.
  * Brez WebGL2 vrh in trak kot pri vlaku.
* **Vlak: trak od izhodišča do cilja** (`trakHtml`), merilo vozni red. Vlak med zadnjo prevoženo in naslednjo po uri (15–85 %), s potnikom na njegovi legi v indigu (`legaPotnikaNaTraku`).
* **Osvežitev na 10 s med vožnjo** (30 min pred odhodom do 10 min po cilju, `voziAliKmalu`), sicer 60 s (`ritemOkna`; `pollWhileVisible` vzame ritem kot funkcijo): SŽ preračuna na 15 s, derp.si pošlje na 30. Napoved (`/predict`) ob istem naslovu predpomnjena 30 s (`fetchRunAndForecast`). Veriga vozila (`/vehicle`) samo pred odhodom.
  * Pod vrhom svežina, teče sama: „novica pred N s“ (od `tiho_s`), nad `TIHO_S` „N min brez novic“, s potnikom „potnik pred N s“. Ob „GPS pred N s“ se „novica pred“ skrije — dve starosti druga ob drugi sta uganka.
  * Neuspela osvežitev stran pusti: „brez zveze · podatki od HH:MM“ (`brezZveze`); prazno stran bi sicer pustil vsak predor.
  * Sprememba na vrhu se dvigne (`je-novo` po `podpisVrha`; ob `prefers-reduced-motion` samo obroč).
* **Vreme = žeton ob postanku na vrhu** (ikona + °, črtkan = napoved, od „zahtevnih“ beseda); v vrstici postanka samo zahtevne in hude.
* **Skupina dejanj** (povezani gumbi, ikona nad besedo, robove postavi vidnost — `uredSkupino`): budilka (aplikacija), „Deli lego“, „Javi, kako polno“, pri vlaku „N ovir“. Kar o zasedenosti vemo, je vrstica nad skupino (`#zas-namig`, `zasedenost.md`). Odprt en razdelek (`data-odprto`).
* **Postanki na črti**: prevoženi zloženi, vozilo je vrstica med zadnjim in naslednjim, naprej črtkano. Ničla = „točno“, tudi v kartici deljenja.
* **Okno nima** preklopa preprosto/napredno, krivulje zamude, končnih zamud po dnevih, poročil prevoznika (`/reports`), legende pod zemljevidom in ure v glavi — zgodovina gre v statistiko (`strani.md`).
* **Geste**: `cooperativeGestures` (namig v `pkUstvari`), razširjen pogled ga ugasne.

  | | vgrajen | čez celo stran |
  |---|---|---|
  | kolešček | ne (Ctrl/⌘ + kolešček da) | da |
  | **miška** | **vleče zemljevid** | isto |
  | en prst | pomika **stran** | pomika zemljevid |
  | dva prsta | pomikata in približujeta | isto |
  | gumba +/− | samo miška | samo miška |

* **Razširi čez stran, ne čez zaslon** (`is-max`, `position: fixed; inset: 0`). **Rabi `!important`** na `position`, `inset`, `margin`, `height` — `@media` pravila (0,3,1) so premagala (0,3,0), na namizju 240 px.
* **Starost lege teče sama**: `common.ageHtml()` → `<span class="age-live">` z izhodiščem v `data-`; ena sekundna zanka po razredu. Ura odjemalca ni v računu. **Kdor izpiše `ageHtml()`, ponastavi števec** — podnapis samo ob novih podatkih (`nova`), ne v sekundni zanki.
* Nad 1000 px dva stolpca (flex, ne grid): levo zdaj 420 px, lepljivo (zemljevid 340 px), desno postanki do 560 px.
* **Ena vožnja, ena zanka leg** (`runMap.pollTrip`; prej vsak `loadRun` nova).
* Opomb malo — le, kar spremeni ravnanje („čakaj na postajališču, ne na peronu“).
* Statika z `Cache-Control: no-cache` (+ `ETag`).

## Osvežitev

* **Gumb „osveži“ obstaja, ker se osveževanje ne vidi**: pove uro odgovora („osveženo ob 20:44:25“) in napako. `common.pripniOsvezi()`; zanki imata `zdaj()` (`pollWhileVisible`, `pollVehicles`). **`zdaj()` napake ne pogoltne**, `tick()` jo.
* **Na velikem zemljevidu ni golega `setInterval`**: vse skozi `pollWhileVisible` / `pollVehicles` (skrit zavihek nič). Prvi korak sproži `pollWhileVisible` sam — ne kliči ročno pred njim.
* Gumb levo pod približevanjem (desno ga prekrije `.sheet-toggle`).
* Stranska plošča je na telefonu spodnja, privzeto zaprta; izbira vozila jo zapre.

## Avtobusi: plast na prevoznika, od približka

* **Vsak prevoznik svoja plast in polje** (1 530 vozil = kaša). **Vsi prižgani**; mestni LPP (`agency = 'lpp'`) od z12 (`MESTNI_OD`), ostali od z9 (`AVTOBUSI_OD`), opomba `opombaPriblizka()`. Prag v filtru (`["zoom"]` celoštevilski).
* V shrambo samo, kar človek prestavi (`setLayer(…, zapomni)`, `kajros:map-avtobus-*`).
* „na velik zemljevid“ iz okna nosi `&trip=`: prižge plast za ta ogled, odpre kartico, `trip` odstrani.

| | | |
|---|---|---|
| LPP | `#4db97f` | zelena |
| Arriva | `#6fb8ff` | modra |
| Nomago | `#9d7ae0` | vijolična |
| AP Murska Sobota | `#c9a227` | zlata |
| Marprom | `#d71920` | rdeča (vozila in marprom.si) |
| Kranj | `#eeeacc` | topla bela (vozila brez enotne barve) |

Najslabši deutan/protan ΔE 9,6, tritan 4,8; Marprom in Kranj od ostalih ≥ 16, Marprom proti „nad 15 min“ 5,5. Barva nikoli sama — loči oblika in ime. Marpromova rdeča ima na podlagi 3,6 : 1: drobno besedilo `inkZaBesedilo()`, značka z barvo prevoznika `besediloNaInk()` (`common.js`).
* **Model po prevozniku**: LPP zgibni, Arriva/Nomago/AP MS medkrajevni visokopodni, Marprom in Kranj `avtoMestni` (nizkopodni, troje vrat; Marprom rdeče čelo in streha, Kranj baterije na strehi, zadaj brez motorja).

* **LPP dva `agency_id` (1118, `lpp`), ena vrstica** (`agencyKey()`); statistika loči (`stats.AGENCY_NAMES`).
* „Drugi prevozniki“ obvezna (nov prevoznik bi tiho izginil), skrita pri 0. `.layer[hidden] { display: none; }` (flex povozi `[hidden]`).
* **Dna zaslona v brskalniku ne uporabljaj za nadzor** (Chromova spodnja vrstica ga prekrije). Gumb nastavitev zgoraj desno pod lego, `aria-label`. Posnetek namizja ne dokaže dosegljivosti na telefonu.
