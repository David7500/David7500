# Najhitrejša pot

Načrt strani za vprašanje *„sem tu, moram biti tam — kako in kdaj grem?"*. Dosedanje strani odgovorijo šele, ko potnik sam ve postajo; tu je izhodišče **točka na zemljevidu**, ne postaja.

Odgovor = veriga: hoja → vožnja → (prestop) → vožnja → hoja, plus ena ura na vrhu — kdaj moraš iz hiše.

## Kaj je odločeno in zakaj

| odločitev | razlog |
|---|---|
| **naslov iz lastnega kazala** | tuji geokodirnik bi ob vsakem tipkanju izvedel, kam greš; kazalo iz OSM 51 MB, teče pri nas (23. 9. 2026, prej naslova sploh ni bilo) |
| **doseg hoje 25 minut** | izmerjeno: večji doseg ne stane nič, najde boljše poti (Grosuplje 10 minut boljši prihod) |
| **hoja iz OSRM, ne iz faktorja** | izmerjeno na 1 080 poteh: faktor 1,45 podceni pot v 48 % primerov, največji obvoz 7,86× |
| **usmerjevalnik doma, ne javni** | javni bi ob vsakem iskanju izvedel, kje si; je „samo za demo", nova točka odpovedi |
| **faktor ostane kot zasilna pot** | če vsebnik ne odgovori, stran vseeno dela — in to prizna |

## Hoja

`hoja.sekunde()` = **ena funkcija**, nihče drug ne ve, od kod številka. Prvi vir OSRM (`KAJROS_OSRM`, privzeto `http://127.0.0.1:5000`), zasilni zračna razdalja × 1,45 pri 5 km/h.

Izmerjeno pri postavitvi na arwenu (Ubuntu 24.04, i5-6200U, 4 niti):

| korak | čas | vrh pomnilnika |
|---|---|---|
| prenos `slovenia-latest.osm.pbf` (299 MB) | 30 s | — |
| `docker pull` | 21 s | — |
| `osrm-extract -p foot.lua` | **481 s** | **2,25 GB** |
| `osrm-partition` + `osrm-customize` | 106 s | 572 MB |
| podatki na disku (brez `.pbf`) | 807 MB | |
| strežnik med tekom | | 525 MB |

| matrika ena točka → N postajališč | 10 | 30 | 70 | 120 |
|---|---|---|---|---|
| odziv | 8 ms | 14 ms | 32 ms | 81 ms |

Troje, kar se hitro pozabi:

* **Naš strežnik vrne isto kot javni** — 412,8 m do decimalke. „Demo" = omejitev gostitelja, ne programa.
* **OSRM-ov peš profil hodi 5,00 km/h**, izmerjeno na 1 080 poteh. Trajanja ni treba računati posebej; `duration` je že prava številka.
* **Predfilter bližnjih postajališč ne sme uporabiti faktorja.** Zračna črta je vedno krajša od prave poti, zato filter pri 2 083 m (25 min × 5 km/h) ne izpusti nič dosegljivega. Faktor v predfiltru bi tiho odrezal postaje, ki so v dosegu.

Kandidatov v tem polmeru: Bavarski dvor 201, Ljubljana Polje 66, Grosuplje 27, Bohinjska Bistrica 9 (8. 9. 2026).

## Iskanje

Jedro = razširjen `journey.plan()` — raztezanje po krogih, že obstaja. Manjkajo štiri stvari:

1. **več izhodišč z različnimi časi** — vsako postajališče dosegljivo ob svoji uri, ker je hoja do vsakega druga;
2. **več ciljev z različnimi časi** — cilj = prihod na točko, ne na postajo;
3. **peš prestop med postajališči** — zdaj se prestopa samo na istem `stop_id`, zato „Bavarski dvor" v eno in drugo smer za iskalnik ni isti kraj. 4 507 od 5 500 imen ima več kot en `stop_id`;
4. **obe omrežji hkrati** — vlak in avtobus v isti verigi.

Izmerjeno s prototipom čez obe omrežji, štiri noge, hoja na obeh koncih: **225–441 ms** na razvojnem računalniku; **čas ni odvisen od dosega hoje** (16 ali 73 izhodiščnih postajališč enako hitro) — cena je v premetavanju voznega reda, ne v številu izhodišč.

Preverjeno na roko: Grosuplje → Ljubljana center ob 8:00 = 416 m hoje (6,5 min) → LP 3232 ob 08:17 → Ljubljana 08:44 → 982 m hoje (15,3 min) → **08:59**. Prototip vrne isto minuto.

## Zamude

Zaradi tega stran obstaja; vozni red zna vsak. Katera številka velja na potnikovem postanku in od kod, odloči `stats.zamuda_na_postanku()` — **isto pravilo kot v iskalniku zvez**. Načrtovano branje iz `journey.board()`; ob pisanju se je pokazalo, da je prav izluščiti pravilo, ne klicati ga skozi tablo, ki odgovarja na drugo vprašanje.

Iskanje teče **po voznem redu**, ker napovedi za vožnjo čez pet ur ni. Zamuda se pripiše, kjer jo imamo, veriga se **znova preveri**: če prva noga zamuja 8 minut, prestop pa je imel 6, predlog pade ali dobi opozorilo.

Pri avtobusih velja tudi obratno: 25 % jih odpelje **pred** voznim redom. Pri hoji na postajo nevarnejše od zamude, mora biti napisano.

## Kaj mora stran priznati

* **Peš vso pot je včasih najhitreje.** Prototip Polje → BTC: prihod 09:04 pri odhodu ob 08:00; hoja 47 minut = 08:47. Če transport izgubi, se to pove.
* **Minute hoje = eno od meril**, sicer bi prvi predlog vedno pošiljal 25 minut peš, da prihraniš dve. Predlogi: „najhitreje", „najmanj hoje", „najmanj prestopov", kadar se razlikujejo.

## Pasti tega projekta

* **Polnoč.** 2 394 postankov ima `dep_s ≥ 86 400`, največji 121 680 (33:48). Iskanje ob 23:40 mora videti v naslednji prometni dan.
* **`network` = stran, ne prevozno sredstvo.** Ta stran je za zemljevidom šele druga, ki meša obe omrežji; `network` mora zavestno pustiti prazen.
* **Prag za prestop je odvisen od omrežja** (vlak 6 min, avtobus 3). Pri mešani verigi velja prag tistega, na kar se vkrcavaš, plus hoja, če postajališče ni isto.
* **`MAX_STOP_TIMES` je tiho vračal prazen vozni red.** Ta razred napake nas je že ugriznil, ko je mestni LPP potrojil omrežje. Ne sme se ponoviti.
* **Zapisovanje lege.** Zahteva nosi, kje si in kam greš. To se ne sme znajti v dnevniku strežnika.

## Vrstni red

1. ✅ Glasna varovalka `MAX_STOP_TIMES` + `hoja.py` + OSRM na arwenu
2. ✅ Peš noge med postajališči (`pespot`, `kajros pespoti`)
3. ✅ Jedro: iskanje z več izhodišči in cilji čez obe omrežji (`pot.py`, `kajros pot`)
4. ✅ Endpoint `/api/pot` + stran `/app/pot`, „čim prej"
5. ✅ Zamude v predlogih in preverjanje, ali veriga drži
6. ✅ Podrobni prikaz ene poti (`/app/pot/podrobno`): pešpot z geometrijo in vmesni postanki vožnje
7. ✅ Shranjene točke („dom", „služba") — `localStorage`, žetoni pod obema poljema
8. ✅ „Biti tam do X" (obratno iskanje, `_isci_nazaj()`), 23. 9. 2026
9. ✅ Kolo ali rolka: 15 km/h na obeh koncih (`kmh`)
10. ✅ Iskanje po naslovu, ulici in kraju iz lastnega kazala (`naslovi.py`)
11. ✅ Vodenje po pešpoti na zemljevidu v 3D (`/app/pot/podrobno`)

**Peš noge v `journey.plan()` namenoma niso vezane.** Njegova oblika odgovora (`train1`, `trip1`, `via`) nima mesta za peš nogo, prikaz bi jo narisal napol; prvorazredne so v `pot.py`, kjer je bil odgovor zasnovan zanje.

## „Biti tam do X" — obratno iskanje

Vprašanje človeka, ki mora biti v službi ob osmih: ne „kdaj sem najprej tam", ampak **„kdaj moram najpozneje od doma"**. Iskanje naprej ne odgovori: odhod 7:04 + prihod 7:52 ne pove, da isti prihod da tudi odhod 7:20.

`_isci_nazaj()` = isti postopek po krogih, obrnjen v času: od cilja z rokom, katera vožnja pripelje dovolj zgodaj, do kdaj moraš biti na njenem vstopu. **Oznaki sta dve na postajališče**: `pes` (do kdaj moraš biti tu, če prideš peš od doma — brez praga) in `voz` (do kdaj moraš sem pripeljati — že manj praga vožnje, na katero se tu vkrcaš). Naprej je ena oznaka, ker je prag znan šele ob vkrcanju; nazaj je znan prej.

Preverjeno 23. 9. 2026 na **60 parih točk** (16 krajev, prometni dan 24. 9., ure 7–18): naprej ob uri T da prihod A; nazaj z rokom A + 1 min. Pri 34 parih z vožnjo **nazaj ni bil nikoli slabši in nikoli prepozen**, v **17 od 34** poznejši odhod za isti prihod (0–37 min pozneje, mediana 0,5). Minuta rezerve v preizkusu: prikaz reže hojo pod minuto; brez nje "slabše" dvakrat, oboje zaradi 19 s oziroma 1 s hoje, ki je v roku ni.

Čas na razvojnem stroju: **mediana 140 ms, največ 307 ms** za celo iskanje z izbirami (naprej 105 / 910 ms).

Izbire poleg prvega = zrcalo iskanja naprej: dve **prejšnji** zvezi (rok = prihod prejšnje − 1 min) namesto naslednjih, manj prestopov, druga pot, manj hoje. Druge izbire smejo oditi največ 30 minut prej od prve.

**Za danes je spodnja meja zdaj.** Če do roka ne gre več, strežnik ne vrne „ni poti", ampak iskanje naprej od zdaj z `ne_ujames` — stran pove, kdaj si tam najprej.

## Kolo ali rolka

Ena druga hitrost, 15 km/h, ne drsnik: potnik ve, ali ima kolo, ne koliko vozi. Pot ostane **peš pot** iz OSRM — kolesarskega profila ni, za „koliko do postaje" je razlika majhna. Peš prestop na postaji ostane hoja.

Doseg 3× daljši, ploščina 9× večja: pri Bavarskem dvoru v 25 minutah vožnje **760 postajališč** (peš 210); meja 120 kandidatov bi jih odrezala pri 1,3 km — tam, kjer kolo začne pomagati. Zato se pri kolesu meri **eno postajališče na ime** (istoimenska v 200 m dobijo njegov čas in razliko po zraku): 340 imen, meja 300. Matrika na razvojnem stroju: 1 × 120 27 ms, 1 × 300 71 ms, 1 × 600 202 ms, 1 × 1 000 453 ms.

Izmerjeno na 50 parih ob 8:00 (37 z odgovorom v obeh): s kolesom na cilju **mediano 23 minut prej** (5–141). Iskanje s kolesom: mediana 217 ms, največ 476 ms na razvojnem stroju — arwen okoli 3× počasnejši.

## Iskanje po naslovu

Do 23. 9. 2026 kraj izbran na zemljevidu, iz shranjenih točk ali po imenu postaje — naslova ni bilo, ker bi ga tuji geokodirnik izvedel ob vsakem pritisku tipke. Zdaj kazalo naše (`kajros/naslovi.py`, `/api/naslovi`, gradnja `deploy/naslovi.sh`).

| kaj | izmerjeno 23. 9. 2026 (razvojni stroj) |
|---|---|
| izvoz OSM (`slovenia-latest.osm.pbf`) | 313 MB |
| osmium `tags-filter` + `export` v vsebniku | 28 s, 1 208 362 predmetov, 566 MB geojsonseq |
| gradnja kazala | 10–12 s |
| kazalo (`naslovi.sqlite`, dve FTS5) | 51 MB |
| hišnih številk v izvozu | 815 060 → **435 044** različnih (točka in stavba v OSM pogosto ista hiša) |
| ulic (iz naslovov) / krajev / imenovanih točk | 17 085 / 11 237 / 82 934 |
| poizvedba | 0–15 ms |

Ugotovljeno pri preizkušanju, zdaj v kodi:

* **Hišna številka ni predpona.** „50*" ujame poštno številko 5000 in vso Novo Gorico; pravi naslov izpadel iz prvih 400 zadetkov.
* **Bližina šteje več od črk.** „Trubarjeva 5" je v Laškem ime do črke, v Ljubljani „Trubarjeva cesta 5"; z večjo težo ujemanja bilo Laško prvo. Brez okolice (človek še ni povedal, kje je) prednost Ljubljana in Maribor, ker tam živi največ ljudi.
* **Dve kazali, ne eno.** Brez številke človek išče ulico, kraj ali ime; s številko naslov. Eno kazalo bi za „ljub" premetalo sto tisoč ljubljanskih naslovov, da bi našlo mesto.
* **Točka brez kraja dobi mesto okrog sebe**, ne najbližje vasi: BTC ima najbližjo vas Hrastje, človek reče „BTC v Ljubljani". Polmer mesta 6 km, trga 2,5 km.
* **„Četrtna skupnost X" = X** — isto kot v slogu zemljevida.

Na arwenu (23. 9. 2026, `deploy/naslovi.sh` z `nice`): skupaj 2 min 47 s, od tega branje izvoza 44 s, gradnja 60 s; kazalo 49 MB na disku. Odziv `/api/pot` prek kajros.app po objavi: prvi klic za jutri 8,7 s (hladen vozni red), nato 0,6–1,5 s za „do ure", „čim prej" in kolo.

OSM v Ljubljani nima vseh hišnih številk (Slovenska cesta 50 manjka, 51 je); pokritost proti registru GURS ni izmerjena.

## Vodenje po pešpoti

Stran `/app/pot/podrobno` ima pri vsakem peš koraku „vodi me". Zemljevid = MapLibre (kot veliki), nagnjen in obrnjen v smer hoje; navodila OSRM-ova (`steps=true`) v slovenščini (`hoja.navodilo()`), ulica v imenovalniku. Pravila in pragovi v `.claude/rules/strani.md`. Preizkušeno v chromiumu z lego prek CDP (`Emulation.setGeolocationOverride`) na poti Polje → Bavarski dvor: prvi zavoj, odštevanje do vlaka z rezervo, preračun po odmiku 78 m (nova pot 44 točk namesto 83), prihod na postajališče, nadaljevanje po izstopu, pogled od daleč (6,4 km od začetka poti).

Ni izmerjeno: kako se vodenje obnese na pravem telefonu med hojo (GPS v mestu, kompas, baterija). Pove šele prva hoja z njim.

### Kaj ostaja odprto

* **Kolesarski profil OSRM**, če bi peš pot kolesarja pošiljala čez stopnice. Zdaj ni izmerjeno.
