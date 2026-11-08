# Nativna aplikacija za Android — načrt

8. 11. 2026. Podlaga: [raziskava.md](raziskava.md) (pravila Playa in nativni sklad, uradni viri), [splet.md](splet.md) (popis spletnih zaslonov), meritve na arwenu (`obiskovalec.aplikacija`), pregled kode `android/`. Posvet z Davidom končan isti dan; odločitve spodaj veljajo pred vsem ostalim v tem zapisu.

## Odločeno 8. 11. 2026 (David)

* **Računa za Play še ni.** David ga odpre v novi seji (predaja na koncu). Osebni račun, odprt po 13. 11. 2023, mora pred produkcijo imeti zaprti preizkus z vsaj 12 preizkuševalci 14 dni zapored, nato je pregled do 7 dni. Produkcija bo torej najprej v začetku decembra.
* **Vse priporočeno je sprejeto:** lasten podpisni ključ, nastavljen ob ustvarjanju aplikacije; donacije v kanalu `play` skrite; končno stanje = nativno vse, kar potnik dela vsak dan, vsebinske strani spletne; sklad in načela kot spodaj.
* **Potek, spremenjen po posvetu.** 14 dni teče od vpisa preizkuševalcev, ne od gradnje. Zato najprej Play 2.0 (faza 0, 1.–2. dan) in nalaganje v zaprti preizkus, da čas začne teči. Od 3. dne nativno: temelji, domača, tabla. Nativne gradnje gredo sproti na isti zaprti preizkus. V produkcijo gre različica, ki je dobra ob koncu preizkusa; lahko je že nativna 3.0.

## Na kratko

1. **Play prihodnji teden in nativna aplikacija sta dve stvari.** V Play gre zdajšnja aplikacija, prilagojena pravilom (2.0). Nativna pride pozneje kot posodobitev iste aplikacije (3.0): isti paket `app.kajros`, isti ključ, budilke in widgeti ostanejo.
2. **Nativna = Kotlin + Jetpack Compose + Material 3 Expressive.** Nativno je vse, kar potnik dela vsak dan. Vsebinske strani (statistika, o nas, zasebnost, stik) ostanejo spletne v okvirju aplikacije, kot pri večini velikih aplikacij.
3. **Najpomembnejša odločitev je pogodba s strežnikom, ne orodje za zaslone.** Strežnik pove, kaj se pokaže (beseda in razred zamude, ime vožnje, meja meritev/napoved), aplikacija samo razporedi. Razlog je izmerjen: 1.–8. 11. je bilo 26 % dni uporabe aplikacije na različici 1.10 ali starejši, čeprav aplikacija sama ponuja posodobitev. Logika, ki živi v aplikaciji, v teh telefonih ostane stara mesece.
4. **Vrstni red:** temelji (pogodba API, lupina, tema, selitev shranjenega) → domača, iskalnik povezav in odhodna tabla → okno vožnje → ovire, zasedenost, spremljanje vožnje v obvestilu → zemljevid → pot od vrat do vrat.
5. **Ocena, ne meritev:** jedro (3.0) 6–8 tednov po začetku; zemljevid in pot še 5–7 tednov. 2.0 odpre zaprti preizkus, nativna raste na istem kanalu (glej Odločeno).

## Kje smo

Izmerjeno 8. 11. 2026:

* **Uporaba aplikacije:** 20–39 ljudi na delavnik (2.–6. 11.: 23, 22, 34, 36, 39) ob 450–550 obiskovalcih spleta; ob koncu tedna 5–19. Skoraj vsi odprejo okno aplikacije (`okno > 0`), ne le widgeta.
* **Različice 1.–8. 11.** (obiskovalec-dni, 186): 1.15 106, 1.10 21, 1.13 19, 1.5 15, 1.16 13, 1.7 5, 1.2 5, 1.4 2. Na 1.10 ali starejši 48 (26 %).
* **Android:** 11 980 vrstic Kotlina s testi, brez knjižnic, APK 242 kB, `minSdk 26`, `targetSdk 35`, samo APK (`assembleRelease`). Nativno že: budilka z zaslonom zvonjenja (OpenGL), pet widgetov (RemoteViews), deljenje lege (storitev v ospredju), pošiljanje, samoposodobitev, hitra lega.
* **Splet za potnika:** ~17 000 vrstic JS. Najbolj spreminjani v 30 dneh: okno vožnje 36 sprememb, `common.js` 31, zemljevid 21, pot 21, iskalnik in tabla 20; `api.py` 74.
* **Strežnik je že pol pogodbe:** objekt `zamuda` (`stats.opis_zamude`) in absolutni ISO časi v tabli, povezavah, postankih in poti; `Tabla.kt` jih že bere. Vrzeli: `/api/vehicles` in del `/api/live` nosita samo `delay_s`; besedo zamude sestavlja JS (`delayText`, `prestopText`); ime vožnje imata JS (`imeVoznje`) in Python (`pristanek.ime_voznje`) v dveh različno zgrajenih izvedbah, enakosti ne preverja noben test; različice API in testov oblike odgovorov ni.

## Zakaj nativna in kaj stane

Kaj dobimo, česar WebView ne zmore ali ne zmore dobro:

* **Spremljanje vožnje v obvestilu in na zaklenjenem zaslonu** (Android 16 `Notification.ProgressStyle`, drugje trajno obvestilo): „LPV 2010 · +4 min · Ljubljana 14.36“, osveženo sproti. Tega splet ne zna in je najmočnejši razlog za aplikacijo.
* **Takojšen zagon** s priljubljenimi in voznim redom iz naprave; zamuda šele, ko pride sveža, ali z uro meritve.
* **Brez omrežja** vozni red priljubljenih (predori na progi).
* **Material 3 Expressive zares:** oblike, gibanje, predvidljivi „nazaj“, haptika, namesto posnemanja v CSS (`slog-material3`).
* **Sistem:** bližnjice na ikoni („Domov → služba“), ploščica v hitrih nastavitvah, povezave `kajros.app/...` se odprejo v aplikaciji (App Links), TalkBack in velikost pisave po sistemsko.
* **Manj tveganja v Playu:** pravilo „webview spam“ cilja aplikacije, ki so samo ovoj strani (raziskava A9).

Kaj stane:

* **Dva odjemalca za vedno.** Splet ostane (iskalniki, namizje, iPhone). Vsak zaslon dvakrat, razen kar riše strežnik.
* **Sprememba prikaza ne pride več takoj k vsem:** izdaja, pregled v Playu (ure do dni), posodabljanje telefonov.
* **Velikost:** od 242 kB na nekaj MB (Compose) in še nekaj MB z zemljevidom (MapLibre Native). Izmeriti v temeljih.
* **Pravilo „nič odvisnosti“ pade**, ostane „nič Googlovih storitev“.
* **Moj čas:** okoli dva meseca gre večina dela v aplikacijo; splet in zajem rasteta počasneje.

## Načela

1. **Strežnik pove kaj, aplikacija kako.** Beseda in razred zamude, ime vožnje, meja meritev/napoved, opozorila in razvrstitev table pridejo iz API-ja kot polja. Aplikacija ne računa ničesar, kar je v `.claude/rules/oznake.md` ali `model.md`. Barva je oblikovanje: aplikacija preslika `razred` v svojo barvo, kot `Tabla.kt` že dela. Ista polja postopno bere tudi splet, zato se `common.js` krči in številke na zaslonih se ne razhajajo (`preveri_skladnost.py`).
2. **Pogodba API s testom.** Isti endpointi kot za splet, brez ločenega `/api/app/`. Spremembe samo dodajajo. Vsak endpoint, ki ga bere aplikacija, ima v pytest posnetek oblike odgovora; test pade ob odstranjenem, preimenovanem ali drugače tipiziranem polju. Prelomna sprememba dobi novo pot (`/api/v2/...`), stara živi, dokler jo kliče katera različica v `obiskovalec.aplikacija`. `/api/android/razlicica` dobi najnižjo podprto različico.
3. **Raje nič kot stara številka**, kot `sw.js`: v napravi se hranijo vozni red, postaje in priljubljene; zamuda iz predpomnilnika nikoli kot trenutna, samo z uro meritve in drugačnim videzom.
4. **Brez Googlovih storitev:** ne GMS, ne Firebase, ne Play Core, ne analitike. Knjižnice AndroidX (Compose) so knjižnice, ne storitve, in so dovoljene z razlogom. Lega ostane iz `LocationManager` (telefoni brez Googla). Obvestila brez potiska: aplikacija sama preverja v oknu, ki ga potnik zažene, kot budilka že dela.
5. **Ena aplikacija, dva kanala:** `play` (brez samoposodobitve, `REQUEST_INSTALL_PACKAGES` in `USE_EXACT_ALARM`) in `stran` (kot zdaj). Isti paket, isti ključ, ista koda; razlika v manifestu in nekaj razredih.
6. **Postopno, ne naenkrat.** Nativni zasloni nadomeščajo spletne po vrsti. Česar še ni, se odpre kot spletni zaslon v nativnem okvirju (obstoječi WebView in most). Vsi potniki dobijo 3.0 šele, ko je nativna vsa dnevna pot; do takrat nativno raste na preizkusnem kanalu Playa.

## Sklad

Izbira je moja; viri v [raziskava.md](raziskava.md).

| kaj | izbira | zakaj |
|---|---|---|
| zasloni | Kotlin, Jetpack Compose (BOM 2026.09.00), Material 3 1.4, ob stabilni 1.5 prehod | ButtonGroup, FloatingToolbar in MotionScheme v 1.5 stabilni; LoadingIndicator in MaterialShapes z `@OptIn` (B1) |
| navigacija | Navigation 3 (1.2.1) | narejena za Compose, ena aktivnost (B2) |
| omrežje, JSON | `HttpURLConnection` kot zdaj v `Tabla.kt`; `org.json` ali kotlinx.serialization, odločim v temeljih po velikosti | OkHttp in Retrofit nista potrebna |
| zemljevid | MapLibre Native Android (13.7.x) z istim `podlaga.json` in ploščicami OpenFreeMap | isti slog kot splet; lastnega 3D sloja ne prenese (lastni sloji samo prek C vtičnika), zato najprej 2D simboli (B3) |
| widgeti | RemoteViews ostanejo | delujejo; Glance šele, če bi delili kodo z zasloni (B4) |
| spremljanje vožnje | `Notification.ProgressStyle` na Androidu 16+, drugje trajno obvestilo | B5 |
| `minSdk` | ostane 26 | Compose ga podpira |
| preizkusi | JVM kot zdaj, Compose UI na emulatorju, posnetki zaslonov v dveh širinah (samo testna knjižnica) | nadomesti pravilo „poglej v obeh širinah“ |
| iOS | ne zdaj | podatkovna plast v čistem Kotlinu brez Androida, da Kotlin Multiplatform ostane mogoč (B9) |

## Faze

### 0. Play 2.0: zdajšnja aplikacija po pravilih (ta teden)

Moje delo okoli 2–3 dni, Davidovo v konzoli. Ustavljalci in posledice v naši kodi:

1. **`targetSdk` in `compileSdk` 36**, obvezno od 31. 8. 2026 (A2). `onBackPressed` v `GlavnaDejavnost.kt:584` (nazaj po zgodovini WebView) in `ZvonjenjeDejavnost.kt:314` se na Androidu 16 ne kličeta več (B6), zato `OnBackInvokedCallback` od API 33, stari klic ostane pod 33. Edge-to-edge je obvezen; postavitve imajo `fitsSystemWindows`, preveriti na emulatorju 16. `ZvonjenjeDejavnost` je zaklenjena pokonci, na zaslonih ≥ 600 dp se to ne upošteva več: zaslon zvonjenja preveriti na tablici.
2. **Kanal `play`** (A4, A5, A7): brez `REQUEST_INSTALL_PACKAGES`, `Posodobitev`, `Namestitev` in posodobitve na zaslonu „O aplikaciji“; brez `USE_EXACT_ALARM`, ostane `SCHEDULE_EXACT_ALARM`, ki ga potnik odobri; `systemExempted` za zvonjenje je dovoljen samo z odobrenim točnim alarmom, zato pred storitvijo `canScheduleExactAlarms()`. Uporabniški agent nosi kanal (`Kajros/2.0 (Android; play)`), da stran Playevim potnikom ne ponuja APK-ja.
3. **AAB** (`bundlePlayRelease`) poleg APK-ja za stran; nov ključ za nalaganje, podpisni ključ obstoječi.
4. **Podpisni ključ, nepovratno** (A3, preverjeno v uradnem besedilu). Play novo aplikacijo sam vpiše z Googlovim ključem; zamenjati ga je mogoče samo pred izdajo v odprti preizkus ali produkcijo. Z Googlovim ključem se namestitve s strani nikoli ne morejo posodobiti iz Playa, samo z odstranitvijo, in budilke ter priljubljene izginejo. Ključ zato izbrati **ob ustvarjanju aplikacije, pred prvim nalaganjem**, tudi v zaprti preizkus: preizkuševalec z APK-jem s strani bi sicer moral aplikacijo najprej odstraniti. Šifrirano datoteko (PEPK) pripravim jaz, naloži David.
5. **Deklaracije v konzoli** (besedila pripravim): full-screen intent = budilka (A6); storitvi v ospredju `location` („user-initiated location sharing“, video vklopa deljenja) in `systemExempted` (zvonjenje budilke) (A7); Data safety: natančna lega, zbrana, izbirna, za delovanje, ni deljena tretjim; sporočila prek `/stik`; poročila o zasedenosti; obisk brez IP (A8); ocena vsebine; ciljna publika 13+; brez oglasov.
6. **Vidno razkritje pred sistemskim oknom za lego pri deljenju** (A8): preveriti, ali soglasje v `deli.js` ustreza obliki (v aplikaciji, tik pred oknom, gumb „Sprejmem“). Za „pokaži, kje si“ ni potrebno, ker potnik to pričakuje.
7. **Donacije.** Izjema za napitnino ustvarjalcu obstaja (FAQ `answer/10281818`: 100 % ustvarjalcu in nič digitalnega v zameno = plačilo med osebama, Play Billing ni potreben), vendar je Google septembra 2026 od AnkiDroida zahteval odstranitev povezave za donacije (A13). Priporočam, da v kanalu `play` kartico in `/donacije` skrijem (rezerva z 20. 10. 2026 je ena vrstica CSS); na spletu in v APK-ju s strani ostanejo. Gre za denar, zato odloči David.
8. **Vpis v trgovino:** ime brez „SŽ“ (npr. „Kajros: vlaki in avtobusi“); v opisu „Kajros ni uradna aplikacija SŽ, LPP ali države; podatki NAP, CC BY-SA 4.0“ (Misrepresentation, A10, in pogoj licence); posnetki z nativnimi deli v ospredju (budilka, widgeti, A9); ikona 512 px, grafika 1024 × 500, vsaj dva posnetka (A12).
9. **`/zasebnost`** dopolniti za aplikacijo iz Playa: lega pri deljenju, točni alarmi samo v napravi, kaj gre na strežnik.
10. **Številka 2.0:** po našem pravilu sprememba namestitve.

**Rok je odvisen od računa** (A1). Osebni račun, odprt po 13. 11. 2023, mora pred produkcijo imeti zaprti preizkus z vsaj 12 preizkuševalci 14 dni zapored, nato pregled do 7 dni. Če preizkus še ne teče, je prihodnji teden začetek zaprtega preizkusa, produkcija pa najprej v začetku decembra. Preizkuševalci rabijo račun Google; poiskati jih je mogoče med 20–39 dnevnimi uporabniki aplikacije (obvestilo v `/admin`) in v skupinah na FB.

### 1. Temelji (1–1,5 tedna)

* **Strežnik:** pogodbeni testi za endpointe, ki jih bo brala aplikacija (`departures`, `stations/search`, `stations/near`, `connections`, `train/{no}`, `train/{no}/run`, `alerts`, `obvestila`, `pot`, `vehicles`, `live`). Manjkajoča polja: `zamuda` v `vehicles` in `live`; beseda zamude na enem mestu v Pythonu (`zamuda.besedilo`); ime vožnje iz ene funkcije povsod; razvrstitev table na strežniku. Splet začne brati ista polja.
* **Aplikacija:** lupina Compose z eno aktivnostjo, Navigation 3, tema iz žetonov `base.css` v tonskih vsebnikih M3 Expressive, spodnja vrstica, spletni zaslon v okvirju za vse, kar še ni nativno.
* **Selitev shranjenega iz WebView.** Priljubljene (`kajros:fav`), nedavna iskanja (`kajros:recent`), shranjene točke in imena (`kajros:tocke`, `kajros:pot-imena`), nastavitve (`kajros:prevozniki`, `kajros:smer`, `kajros:tabla-razvrstitev` ...) in `kajros:naprava` so v `localStorage` izvora `kajros.app`. Ob prvem zagonu 3.0 jih skrit WebView z `loadDataWithBaseURL("https://kajros.app/", ...)` prebere in prek mostu preda nativni hrambi, brez omrežja. Brez tega potnik v 3.0 izgubi priljubljene. Preveriti na emulatorju.
* **Merjenje:** velikost AAB in APK, hladen zagon na šibkem emulatorju, preden se zavežem MapLibre Native.

### 2. Jedro potnika (4–5 tednov)

Vsak zaslon gre na preizkusni kanal takoj, ko je narejen.

1. **Domača, iskanje postaj, iskalnik povezav in odhodna tabla** obeh omrežij (`/app/train`, `/app/bus`; 3 246 vrstic, L). Prvi zaslon odloči, ali se aplikacija zdi nativna, in iskalnik povezav je vstopna stran.
2. **Okno vožnje** (3 315 vrstic, XL): postanki, meja meritev/napoved s strežnika, peron, budilka, majhen zemljevid v 2D. Najbolj spreminjan zaslon (36 sprememb v 30 dneh), zato začnem, ko se umiri prenova zamud vlakov ([2026-11-06-vlaki-prenova.md](../2026-11-06-vlaki-prenova.md)).
3. **Ovire in zasedenost** (S): malo kode, malo sprememb.
4. **Spremljanje vožnje:** `ProgressStyle` na Androidu 16+, drugje trajno obvestilo; isti preverjevalnik kot budilka, brez potiska.

Merilo konca: dnevna pot (odpri → tabla ali povezava → vožnja → budilka ali spremljanje) brez spletnega zaslona; posnetki v dveh širinah; teden na preizkusnem kanalu brez napake. Nato 3.0 v produkcijo.

### 3. Zemljevid (2–3 tedne)

MapLibre Native z istim slogom; vozila kot 2D simboli s smerjo in barvo prevoznika; ocena lege med meritvama (`ocenaNaTrasi`) prepisana v Kotlin z istimi preizkusnimi primeri kot v JS. **3D vozil najprej ne.** Najprej izmeriti, koliko ljudi v aplikaciji odpre zemljevid; prepis lastnega sloja (C vtičnik) šele, če se izplača. Do takrat ostane spletni zemljevid s 3D v okvirju.

### 4. Pot od vrat do vrat in ostalo (3–4 tedne)

Pot z vodenjem (stroj stanj `NA_POTI`, storitev v ospredju kot `DeljenjeStoritev`) in deljenje lege na nativnem zaslonu. Statistika, `/o-nas`, `/stik` in `/zasebnost` ostanejo spletne.

### Ne bo, vsaj zdaj

Prepis naenkrat; iOS; potisk prek FCM; Googlova analitika ali knjižnica za posodobitve v aplikaciji; Wear OS in Android Auto.

## Kaj se spremeni v projektu

* `.claude/rules/android.md`: „vmesnik en sam, spletni“ postane nativno jedro in spletna vsebina; „nič odvisnosti“ postane „nič Googlovih storitev, vsaka knjižnica z razlogom“; preverjanje `aapt2 dump strings` za `gms` in `firebase` ostane.
* `preveri.sh`: pogodbeni testi API. Gradnja aplikacije in posnetki ostanejo v `android/zgradi.sh`.
* **Pravilo dela:** nova funkcija najprej na spletu, kjer je hitra in izmerljiva; v aplikacijo, ko se ustali. Logika vedno na strežnik.
* Pisalnih poti ostane šest; aplikacija rabi iste (`/api/deli`, `/api/zasedenost`, `/stik`).

## Tveganja

* **Prenova zamud vlakov in aplikacija hkrati** rabita isti čas; aplikacija zamakne druge naloge v koledarju.
* **Pregled Playa zavrne full-screen intent ali točni alarm:** budilka zazvoni kot obvestilo z visoko prednostjo; padec že obstaja (`canUseFullScreenIntent`, `canScheduleExactAlarms`).
* **Stari telefoni na stari različici:** pogodbeni testi in najnižja podprta različica.
* **MapLibre Native** je lahko prevelik ali prepočasen za šibke telefone: izmeriti v temeljih, preden se zavežem.

## Vprašanja posveta in Davidovi odgovori (8. 11. 2026)

1. **Stanje Playa?** Računa še ni.
2. **Podpisni ključ:** lasten, ob ustvarjanju aplikacije („Provide a copy of your app signing key“), pred prvim nalaganjem. Sprejeto; datoteko PEPK pripravi Claude.
3. **Donacije v Playu:** skrite. Sprejeto.
4. **Prednost:** Play 2.0 najprej, nato takoj nativno, nativne gradnje na isti zaprti preizkus. Sprejeto (glej Odločeno).
5. **Končno stanje:** nativno vse, kar potnik dela vsak dan, vsebinske strani spletne. Sprejeto.

## Predaja: seja za račun Google Play

**Davidovo (njegova prijava, ne agent):**

1. Razvijalski račun v Play Console, osebni, 25 $: preverjanje identitete z osebnim dokumentom, telefon in e-pošta. Preverjanje lahko traja nekaj dni, zato prvo.
2. Ob prijavi preveriti (iz splošnega znanja, ne iz raziskave):
   * ali Google zahteva dostop do telefona Android z aplikacijo Play Console; Volla je brez Googlovih storitev, morda bo treba drug telefon;
   * javni kontaktni e-naslov v vpisu trgovine je obvezen. To je v nasprotju z odločitvijo „naslova za stik ne objavljamo“ (stik samo prek `/stik`). Odloči David, najverjetneje poseben naslov samo za Play;
   * ime razvijalca naj bo „Kajros“, ne osebno ime (obiskovalcem odgovarjamo brez imena); preveriti, kaj osebni račun pokaže javno;
   * EU (DSA): izjava, ali je razvijalec trgovec. Kajros ne prodaja ničesar; kaj pomenijo donacije, preveriti ob izjavi.
3. Ustvari aplikacijo (`app.kajros`, ime npr. „Kajros: vlaki in avtobusi“) in **takoj nastavi podpisni ključ**, preden kar koli naloži.
4. Zbere vsaj 12 preizkuševalcev z računom Google: obvestilo potnikom v aplikaciji (`/admin`, obvestila), skupine na FB. Šteje 14 dni zapored; kdor se izpiše, začne znova.

**Claudovo (ne rabi računa, lahko vzporedno):** faza 0 (gradnja 2.0, besedila deklaracij, vpisa in Data safety, `/zasebnost`, datoteka PEPK). Roki v `KOLEDAR.md`.
