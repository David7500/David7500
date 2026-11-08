# Popis spletnega prikaza za načrt nativne aplikacije (8. 11. 2026)

Namen: za vsak potnikov zaslon ugotoviti, kaj bi morala nativna aplikacija narediti sama, katere podatke bere in kako pogosto se zaslon spreminja. Vsaka sprememba zaslona v nativni aplikaciji gre skozi izdajo v trgovini, v spletu pa se objavi v minutah. Vrstice so seštete čez JS, CSS in predlogo zaslona (`wc -l`). Spremembe so števila commitov (`git log --since=2026-10-09` in `--since=2026-08-10`, torej 30 in 90 dni). Podatki so brani iz kode, strežnik ni bil zagnan.

Predpogoj, ki ga je treba imeti pred očmi: nativni ovoj že obstaja (`android/`, 10 267 vrstic Kotlina, 1.16, most različice 8, 14 commitov v 30 dneh). Budilke, widgeti odhodne table, deljenje lege v ozadju in lega so že nativni, ostalo je WebView.

## `/` domača stran (home.js 554, home.css 371, home.html 192 = 1117 vrstic; 10 / 39 sprememb)

Namen: en dotik do shranjenih poti in budilk. Deli: kartica budilk (samo kadar obstaja), kartice »moje poti« z naslednjima dvema odhodoma, povabilo k deljenju, kartica za lego, podpora/cilj donacij, zemljevid vnaprej naložen po 2 s.

API: `/api/departures` (prek `odhodiPoti()` v common.js) za vsako shranjeno pot, ob praznem danes še za jutri; `/api/podpora`. Ritem: `setInterval` 60 s (`OSVEZI_POTI_MS`) samo kadar je stran vidna, budilke 30 s iz mosta, osvežitev ob `visibilitychange`.

Logika na odjemalcu: `zamudaHtml`, `odhodiHtml`, `naslednjiOdhodi` (common), `mojePoti` in `kljucPoti` (shranjene poti v localStorage), `zamudaPoti`, `ponudiPovabilo`, `ponudiLego`, `izrisiPodporo`. Dvojnik v Pythonu: zamudo in razred že prinese strežnik (`stats.opis_zamude`), razvrščanje `naslednjiOdhodi` dvojnika nima (grep). Widget Tabla.kt isto logiko že ima v Kotlinu.

Most: `seznam`, `preklopi`, `odpriBudilke` (home.js 50, 127, 130). Spremenljivost: srednja, kartice se menjajo v slogu (M3 Expressive osnutek G). Zahtevnost **M**: malo podatkov, ker je večina logike že na strežniku ali v Kotlinu (budilke, widget).

## `/app/train` in `/app/bus` iskalnik in odhodna tabla (connections.js 2151, .css 895, .html 200 = 3246; 20 / 84)

Namen: potnik vpiše postajo ali relacijo in vidi odhode z zamudo. Deli: iskalnik z napovedovanjem postaj, tabla postaje (smeri, razvrstitev), seznam zvez A-B s prestopi, »moje« (priljubljene, nedavne), najbližje postaje po legi, ovire, izbira dneva.

API: `/api/stations/search?q&limit&network` (tipkanje), `/api/stations/index?network` (celo kazalo, v localStorage 12 h, `naloziKazalo`), `/api/svezina`, `/api/connections` (zveze, tudi tabla s ciljem), `/api/departures?station&network&smer&date&kind&limit`, `/api/stations/near`. Ritem: `POLL_MS` 30 s za tabo in zveze (`schedulePoll`), `MOJE_OSVEZI_MS` 60 s za priljubljene in najbližje, ura vsako sekundo (`tickClock`), `pollWhileVisible(refreshFeedDot, 30000)` za pasovo svežine.

Logika na odjemalcu: `zetonHtml`/`zamudaZetona` (beseda in barva zamude), `preostaliPrestop`, `transferBadgeHtml`, `prestopHtml`, `mejaHtml` (meja meritev/napoved), `razvrstitevHtml`, `smeriHtml` in `smerNapis` (smer po imenu postaje), `iskalnikKazala` (iskanje brez šumnikov, `fold`), `imeVoznje`. Dvojniki: `imeVoznje` ↔ `pristanek.ime_voznje` (obstaja, vendar **ni enak**: Python ima posebni veji za marprom/kranj in cifro AP MS, JS gre prek tabele `AGENCY`; vedenje je moralo biti dogovorjeno ročno), `opozoriloBesedilo`/`kdajZapore` ↔ `zapore.kdaj` (strežnik pošilja `kdaj`), `nepotrjen` ↔ `stats.nepotrjen_do` (strežnik pošilja `nepotrjen_do`), prestopna rezerva ↔ `journey` (strežnik računa `stopnja`).

Most: neposredno nobenega (le prek common: lega, share). Spremenljivost: najpogosteje spreminjan zaslon takoj za oknom vožnje. Zahtevnost **L**: veliko stanja (priljubljene, nedavne, dnevi), a podatki so že izračunani na strežniku, Tabla.kt že kliče iste endpointe.

## `/app/train/{no}` in `/app/bus/{no}` okno vožnje (train.js 2505, .css 639, .html 171 = 3315; 36 / 100)

Namen: kje je vlak ali avtobus in koliko zamuja. Deli: glava (hero) z odštevanjem in trenutno zamudo, trak z lego vozila med postajami, časovnica postankov (voznoredni čas, dejanski čas, tir, vreme, zadrževanje), mali zemljevid z vozilom, veriga vožnj, opozorila in zapore, zasedenost, deljenje lege, budilka, pošlji povezavo.

API: `/api/train/{no}/run?date&trip` (glavni), `/api/trip/{id}/shape`, `/api/vehicles?trip=`, `/api/train/{no}/alerts`, `/api/train/{no}/weather`, ob verigi še `run` sosednje vožnje, `/api/zasedenost`. Ritem: `pollWhileVisible(loadRun, ritemOkna)`: pogosteje med vožnjo (`RITEM_VOZI_MS`), redkeje pred njo (`RITEM_MIRUJE_MS`); lega `pollVehicles` po glavi `X-Osvezi-Cez` (privzeto 10 s); preris glave vsakih 15 s; premik vozila po oceni vsako sekundo.

Logika na odjemalcu: `lastMeasured` (meja meritev/napoved; dvojnik `stats.last_measured`, ki ga strežnik vrača kot `last_measured_seq`), `zivaNapoved`/`jeNeskladen`, `vrednostNaPostanku`, `odstevanje`, `notStartedText`, `heroHtml`, `trakHtml`, `vrsticaHtml`, `dwellSplit`, `razdaljaDoPostaje`, `ocenaNaTrasi`/`projekcijaNaTraso`/`tockaNaTrasi` (pomik vozila po trasi med dvema legama; dvojnik v Pythonu ni, `geo.py` rešuje projekcijo postaj, ne ocene pozicije v času), budilke (`budNapovedHtml`, `shraniBudilko`; uro zvonjenja računa Kotlin). `pricakovanaUra` ↔ `stats.ura_z_zamudo`.

Most: `seznam`, `napoved`, `nastavi`, `odstrani`, `dovoljenja`, `zahtevajDovoljenja` (train.js 600-958). Zahtevnost **XL**: največ vrstic, največ sprememb (36 v 30 dneh, 100 v 90), združuje zemljevid, oceno lege v času, časovnico in budilko.

## `/app/map` zemljevid (dashboard.js 2925, vozila3d.js 805, dashboard.css 692, dashboard.html 158 = 4580; 21 / 67)

Namen: živ pogled na vozila obeh omrežij. Deli: vlaki in avtobusi (ploščice in 3D), proge, postaje in postajališča z nadstreški, trasa izbrane vožnje z repom, zapore tira, iskanje vozila, kartica vozila, kartica postaje z odhodi, lastna lega, preklop slojev.

API: `/api/stations?network=…`, `/api/network.geojson`, `/api/live?network=zeleznica`, `/api/vehicles`, `/api/trip/{id}/shape`, `/api/train/{no}?trip=`, `/api/zapore`, `/api/departures?station=`, `/api/shapes/live` (ETag, ~870 kB stisnjeno). Ritem: `POLL_MS` 30 s za vlake, `pollVehicles` 10 s za avtobuse (`X-Osvezi-Cez`), zapore 60 s, proge 5 min, ura 1 s, premik vozil po oceni 1 s.

Logika na odjemalcu: `ocenaZdaj`/`naOceni` (ocena lege med dvema meritvama), `trainPlace`/`groupByStation` (združevanje vlakov na postajo), `worstDelay`, `legaVozila`, `renderTrains`/`renderBuses`, `declutterLabels`, `vehText`/`findMatches` (iskanje vozila po oznaki), 3D modeli v `vozila3d.js` (`vlakModeli`, `avtoModeli`). Dvojnik v Pythonu: nobenega za oceno lege; razred zamude v `/api/live` je delno strežniški (`zamuda` objekt) in delno surov `delay_s`.

Most: lega prek common (`legaZacni`). Zahtevnost **XL**: lasten WebGL2 sloj (glej razdelek Zemljevid), popupi in markerji kot HTML.

## `/app/pot` in `/app/pot/podrobno` od vrat do vrat (pot.js 1671, pot_podrobno.js 1913, pot_karta.js 318, pot.css 799, pot.html 241, pot_podrobno.html 145 = 5087; 21 / 58)

Namen: iz točke A v točko B čez obe omrežji, nato vodenje po poti. Deli: izbira točk (naslovi, shranjene točke, lega), parametri (hoja, kolo, prevozniki, »biti tam do«), seznam predlogov s stopnjo zanesljivosti prestopov, predogled na zemljevidu, vodenje korak za korakom (kompas, ura, 3D vozilo, zaklep zaslona), nasvet, pošlji povezavo.

API: `/api/pot` (od_lat, od_lon, do_lat, do_lon, ob, prihod, hoje, kmh, prevozniki), `/api/pot/podrobno?…&geometrija=0`, `/api/pot/hoja`, `/api/naslovi`, `/api/vehicles?trip=`. Ritem: v vodenju 5 s (`V.osvezi`), osvežitev zamud 30 s (`osveziZamude`, `zivoZanka`, `pollWhileVisible(osveziNaPoti, 30000)`), ura 1 s.

Logika na odjemalcu: `korakiPoti`, `naslednjeNaPoti`, `NA_POTI` (stanje poti v localStorage: 45 min po prihodu, 10 min na cilju, 2 h na vozilu), `prestopDrzi`, `rezervaPrestopa`/`preostanekPrestopa`/`prestopText`, `stavekPoti`, `korakIzLege`/`korakNaPoti`, `preveriZamujeno`, `ogrozenPrestop`, `azimut`/`smerKamere`, `zakleniZaslon` (Wake Lock). Dvojnik: verjetnost prestopa računa strežnik (`pot.verjetnost_zdaj`), stroj stanj vodenja nima dvojnika.

Most: `deliObVoznji`, `cakajVkrcanje`, `deliUstavi`, `nastaviDeliObVoznji` (pot_podrobno.js 527-570). Zahtevnost **XL**: stroj stanj vodenja, kompas, GPS in zaslon, ki mora delovati z ugasnjenim zaslonom (v nativnem prava naloga za foreground storitev).

## `/app/ovire` (alerts.js 174, alerts.html 66 = 240; 3 / 18)

Namen: dela na progi in nadomestni prevozi. Deli: kartice po vrsti ovire in obdobju, »več« za dolgo besedilo. API: `/api/alerts` enkrat ob odprtju, ritma ni. Logika: `kindOf`, `kdajRang` (razvrščanje: veljavno pred napovedanim, nato vrsta), `periodLabel`. Dvojnik: `alerts.razvrsti_linije` (le linije), razvrščanje ovir dvojnika nima. Most: ni. Zahtevnost **S**: en klic, sezname in besedilo prinese strežnik.

## Deljenje lege (deli.js 756, deli.css 171 = 927; 10 / 16)

Namen: potnik na vozilu sporoča lego, da jo vidijo drugi. Deli: iskanje lege, izbira kandidata (vozilo), pošiljanje točk, stanje in ustavitev. API: `POST /api/deli` (točke na 5 s, `POSLJI_MS`), `/api/vehicles?trip=` za mali zemljevid. Ritem: v brskalniku pošiljanje 5 s z Wake Lock; v aplikaciji `MOST.deliStanje` na 5 s. Logika: `beriNativno`, `poslji`, `obLegi`, smer iz druge lege (`SMER_MS`/`SMER_M`); strežnik ima dvojnika (`deljenje.kandidati`, `deljenje.projiciraj`). Most: `deliZacni`, `deliStanje`, `deliUstavi` (deli.js 574-735). **Zahtevnost M**: nativna storitev (`DeljenjeStoritev.kt`, 604 vrstic) že obstaja, v spletu ostane samo UI.

## Zasedenost (zasedenost.js 409, zasedenost.css 80 = 489; 8 / 8)

Namen: potnik javi, kako polno je vozilo, in vidi poročila drugih. Del okna vožnje. API: `GET/POST /api/zasedenost`, komentar prek `POST /stik`. Ritem: 60 s (`OSVEZI_MS`). Logika: žeton za `/stik` (4 s do 2 h), preklic 10 min. Dvojnik: `zasedenost.py`. Most: ni. **Zahtevnost S**.

## Statistika, pristajalne strani, /o-nas, /stik, /donacije, /zasebnost (po eno vrstico)

Statistika (`/statistika…`, izris na strežniku): v nativnem WebView ali odpri v brskalniku. Pristajalne strani (`/vlak/{od}/{cilj}`, `/postaja/{ime}`): izris na strežniku za iskalnike, v aplikaciji nepotrebne. `/o-nas`: 3D zgodba v JS, ostane WebView. `/stik`: obrazec, `POST`, ostane spletni. `/donacije`: kartica cilja in gumb Ko-fi, spletna. `/zasebnost`: besedilo, spletna (Play bo zahteval povezavo nanjo).

## Skupno

### 7. API

**Čas.** Vsi potniški odgovori, ki sem jih pregledal, nosijo absolutni ISO čas z odmikom časovnega pasu (`stats._abs_time()`, api.py: `sched`, `expected`, `nepotrjen_do`, `sched_arr`, `sched_dep`, `actual_dep`, `measured_at`). `/api/pot` nosi epoho v sekundah (`odhod`, `odhod_ocena`, `prihod`). Voznoredne sekunde `t_s` (od poldneva minus 12 h) so v poizvedbah in v surovih vrsticah, odjemalcu se pretvorijo v ISO pred izhodom; polj `t_s` v glavnih odgovorih nisem našel, a ni dokazano za vsako polje. Pravilo polnoči je torej že na strežniku.

**Zamuda.** Strežnik pošilja pripravljen objekt `zamuda = {s, min, razred, vrsta, prezgodaj, pravocasna}` (`stats.opis_zamude`) v `/api/departures`, `/api/connections`, `/api/train/{no}/run` (postanki), `/api/pot`, delno v `/api/live`. Barvo in besedilo (»5 min prej«, »zmanjka 2 min«) sestavlja JS (`delayColor`, `delayText`, `prestopText`). `/api/vehicles` in del `/api/live` nosita samo surov `delay_s`; JS ima za to rezervno pot (`delayMin` iz sekund). Komentar v common.js izrecno pravi, da naj nov odjemalec bere samo objekt, in `Tabla.kt` to že dela. Nativna aplikacija mora razred `zamuda.razred` prevesti v barvo sama, besedilo in prestopno besedo pa lahko prevzame iz skupnega mesta (strežnik jih ne pošilja, kar je vrzel).

**Glave.** `/api/*` nima splošne `Cache-Control`. `X-Osvezi-Cez` (sekunde do naslednjega branja) samo na `/api/vehicles`. ETag samo na statiki in `/api/shapes/live`. Strežniški predpomnilnik (`_predpomni`) je interni. CORS je `*` za GET.

**Različica API ni.** `app.version = "0.1.0"` (FastAPI), nobenega `response_model`, nobenega shema-testa za odgovore. Aplikacija bi se zlomila ob preimenovanju ali odstranitvi: `zamuda.min/razred/prezgodaj`, `train_no`/`agency`/`network`/`headsign` (vhodi `imeVoznje`), `trip_id`, `sched`/`expected`/`nepotrjen_do`, `stops[].sched_arr/sched_dep/actual_dep`, `last_measured_seq`, `noge[]` v `/api/pot`, `delay_s` v `live`/`vehicles`, glava `X-Osvezi-Cez`. Že obstoječa `GET /api/android/razlicica` (koda, ime, url) nosi samo različico APK, ne najnižje podprte različice API.

### 8. Zemljevid

MapLibre GL JS 6.10.0, vgrajen v `static/maplibre-6.10.0/` (maplibre-gl.mjs, worker, css). Slog je `static/podlaga.json`: lastna temna podlaga po shemi OpenMapTiles. Vektorske ploščice `https://tiles.openfreemap.org/planet`, črke `https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf`. Rezerva ob izpadu: Esri Canvas raster (`https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base`, common.js `ESRI_CANVAS`). Zahteva WebGL2 (`imaWebGL2()`).

Naši sloji imajo predpono `k-`: GeoJSON vir z linijami (`k-proge`, `k-vse-trase`, `k-trasa`, `k-rep` z `lineMetrics`, `k-zapore`), krogi (`k-postaje`, `k-postajalisca`, `k-izbrano`), `fill-extrusion` za nadstreške postajališč, `symbol` za imena. Vozila: HTML `maplibregl.Marker` za 2D ploščice, 3D vlaki in avtobusi pa **lasten MapLibre `custom` sloj** (`type: "custom", renderingMode: "3d"`, `vozila3d.js` 805 vrstic) z golim WebGL2, brez three.js (komentar: 172 kB). Modeli so sestavljeni iz kvadrov in osmerokotnih koles, instancirani. Popupi in markerji so HTML (`maplibregl.Popup`).

Kaj gre v MapLibre Native in kaj ne. Gre: slog `podlaga.json` (MapLibre Native bere isto specifikacijo sloga, izrazi in vektorske ploščice OpenFreeMap so enaki), GeoJSON vira in plasti `line`/`circle`/`symbol`/`fill-extrusion`, kamera in nagib. Ne gre kar tako: `custom` sloj z WebGL2 v JS (Native ima custom sloj le prek C++/JNI in OpenGL ES, torej je treba 3D modele prepisati, ne prenesti), HTML markerji in popupi (nadomestijo jih Native anotacije ali Compose prekrivi), `declutterLabels` in ocena lege v 1 s zanki (v Kotlinu na zaslonu). Presoja: v Kotlinu že obstajajo ročni GL meshi (`Mreza.kt` 238 vrstic, `PeronRisar.kt`) za peron, kar je precedens, a ne za zemljevid. Vsaj bi se dal 3D izpustiti in vozila narisati kot 2D simbole, kar je velika razlika v obsegu. Uvoz kode `nativeRender` bi bil nova odvisnost (MapLibre Native Android SDK, ~10+ MB) v aplikaciji, ki je zdaj 71 kB (README, 12. 9. 2026).

### 9. sw.js in /brez-omrezja

Service worker (`templates/sw.js`, 110 vrstic) **nikoli ne predpomni `/api/`** (zamuda iz predpomnilnika je laž z uro zraven) in `/admin`. Lupina se vnaprej naloži: `/brez-omrezja`, `base.css`, `pisave.css`, `common.js`, `home.css`, štiri pisave woff2 (IBM Plex Sans latin/latin-ext, Plex Mono 400/600). `/static/*` je cache-first po odtisu vsebine (nespremenljivo). Pet strani (`/`, `/app/train`, `/app/bus`, `/app/pot`, `/app/map`) postreže iz predpomnilnika in sveže potegne v ozadju (stale-while-revalidate, ker v HTML ni nobene številke). Ostale navigacije omrežje najprej, predpomnilnik kot rezerva. Različica = odtis vseh predlog in statike (`_odtis_aplikacije`), ob spremembi se stari predpomnilniki izbrišejo. MapLibre in ploščice se ne vnaprej nalagajo. `/brez-omrezja` je statična stran z napisom »brez zveze« in izrecno **brez zadnjih znanih zamud**. Posledica za nativno: pravilo »raje nič kot stara številka« je produktna odločitev in jo je treba prenesti (ne predpomniti zamud, ali jih pokazati z jasno starostjo).

### 10. Kazalo common.js (2851 vrstic) po skupinah: kaj mora biti enako v spletu in aplikaciji

| skupina | vrstice | opomba za nativno |
|---|---|---|
| Beseda in barva zamude: `DELAY_RAMP`, `RAZRED_BARVA`, `delayMin/Color/Label/Text`, `isEarly`, `prestopText`, `preostanekPrestopa`, `rezervaPrestopa`, `trajanjePrikaz`, `stavekPoti`, `pricakovanaUra` | 29-153 | obvezno enako; barve so oblikovanje (Kotlin `Tabla.razred` jih že ima), pravila so na strežniku |
| Čas in datum: `TIME_FMT`, `todayIso`, `hhmm`, `dayLabel`, `OSVEZI_URA` | 159-190, 1879 | Europe/Ljubljana vedno, ne telefonski pas |
| Besedilo in sklanjanje: `SKLONI`, `sklon`, `potnikov`, `pluralRuns`, `fold`, `escapeHtml`, `lepoIme`, `alertTitle` | 253-310, 936-958 | dvojnika ni, treba prepisati (slovenska sklanjatev) |
| Most in aplikacija: `MOST`, share, `pripniOAplikaciji` | 362-470 | odpade, če ni WebView |
| Povezava in osvežitev: `jsonOk`, `ZVEZA*`, `refreshFeedDot`, `pollWhileVisible`, `pollVehicles`, `pripniOsvezi` | 606-860, 1809-1925 | politika ritma: pogosteje med vožnjo, skrita stran miruje |
| Vožnja in prevoznik: `AGENCY`, `jeMedkrajevni`, `ciljVoznje`, `imeVoznje`, `lineBadgeHtml`, `AGENCY_INK`, `inkZaBesedilo` | 883-1140 | `imeVoznje` ima Python dvojnika, ni identičen; ena resnica je nuja |
| Vreme: `weatherIconHtml`, `severity*`, `weatherSummary` | 1119-1270 | dvojnik `weather.severity` |
| Meja meritev/napoved: `lastMeasured`, `stopDelay`, `jeNeskladen`, `zivaNapoved`, `fetchRunAndForecast`, `NAPOVED_VELJA_MS` | 1197-1215, 1496-1584 | dvojnik `stats.last_measured`; napaka že dvakrat na zaslonu |
| Tabla in zapore: `razvrstiTablo`, `nepotrjen`, `odhodiPoti`, `naslednjiOdhodi`, `opozoriloBesedilo`, `kdajZapore`, `nadomestniPostanekHtml` | 1325-1495 | `razvrstiTablo` dvojnika nima |
| Lega vozila: `ocenaNaTrasi`, `projekcijaNaTraso`, `tockaNaTrasi`, `postankiNaTrasi`, `razdaljaM`, `OCENA_MAX_ODMIK_M` | 1626-1808 | ocena pozicije vozila med meritvama, enaka na obeh straneh, brez dvojnika |
| Lastna lega: `LEGA`, `locateMe`, `poisciMe`, `vklopiLego` | 2098-2490 | v aplikaciji prek `MOST.legaZacni` |
| Na poti: `NA_POTI`, `korakiPoti`, `naslednjeNaPoti` | 2521-2730 | stroj stanj poti |
| Lokalni spomin: zadnje iskanje, `dneviRabe`, skrita obvestila, kazalo postaj | 573-605, 2031-2070, 2730-2851 | localStorage; v nativnem DataStore/Room, migracije ni |
| Obvestila skrbnika: `obvestiloHtml` | 2761-2851 | `/api/obvestila` vsakih 5 min |

base.css (963 vrstic) nosi barvne žetone in temo; Material 3 Expressive slog bi v nativnem pomenil prepis v Compose temo.

## Tabela zaslonov

| zaslon | vrstice | sprememb 30 d | sprememb 90 d | zahtevnost | razlog |
|---|---|---|---|---|---|
| `/` domača | 1117 | 10 | 39 | M | malo podatkov, budilke in widget že nativni |
| `/app/train`, `/app/bus` | 3246 | 20 | 84 | L | veliko lokalnega stanja, podatki že izračunani na strežniku |
| okno vožnje | 3315 | 36 | 100 | XL | najbolj spreminjan, zemljevid + ocena lege + budilka |
| `/app/map` | 4580 | 21 | 67 | XL | lasten WebGL2 3D sloj, HTML popupi |
| `/app/pot` + podrobno | 5087 | 21 | 58 | XL | vodenje po poti, stroj stanj, kompas, ozadje |
| `/app/ovire` | 240 | 3 | 18 | S | en klic, strežnik pripravi |
| deljenje lege | 927 | 10 | 16 | M | nativna storitev že obstaja |
| zasedenost | 489 | 8 | 8 | S | en klic + obrazec |
| common.js + base.css | 3814 | 31 | 94 | L | skupna logika, ki mora ostati enaka |
| sw.js + brez-omrezja | 145 | 0 | 3 | S | v nativnem odpade |
| api.py (za primerjavo) | 4322 | 74 | 179 | | strežnik se spreminja hitreje kot katerikoli zaslon |

## Tri najpomembnejše ugotovitve

1. Spremenljivost je visoka tam, kjer je vrednost: okno vožnje (36 sprememb/30 d), common.js (31), api.py (74), zemljevid (21), pot (21). Če gredo ti zasloni v nativno, vsaka sprememba čaka na izdajo v trgovini. Zasloni, ki se ne spreminjajo (ovire 3, zasedenost 8), so poceni kandidati za prvi nativni korak; draga in nestanovitna jedra so dober razlog za hibrid ali za stabilen API.
2. Strežnik je že pripravljen kot pogodba, a ne do konca: `zamuda` objekt, ISO časi, `nepotrjen_do`, `kdaj` zapor, verjetnost prestopa prihajajo izračunani, `Tabla.kt` to že izkorišča. Vrzeli: `/api/vehicles` in del `/api/live` samo `delay_s`, beseda zamude se sestavlja v JS, `imeVoznje` je podvojen JS/Python in ni identičen (marprom/kranj/AP MS). Različice API in shema-testov ni: preimenovano polje tiho zlomi starejšo aplikacijo v telefonih, ki se posodabljajo počasneje od strani.
3. Zemljevid in vodenje po poti sta pravi strošek. 3D vozila so lasten WebGL2 sloj (805 vrstic), ki v MapLibre Native ne obstaja, enako HTML markerji in popupi. MapLibre Native bi aplikaciji dodal najmanj nekaj MB (zdaj 71 kB). Pot od vrat do vrat z vodenjem rabi nativno storitev v ozadju (kot `DeljenjeStoritev.kt`). Za Play lansiranje prihodnji teden je realna poteza: ostati hibrid, nativne zaslone dodajati po stabilnosti (ovire, tabla, budilke), in najprej utrditi API.
