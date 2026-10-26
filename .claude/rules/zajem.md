---
paths:
  - "kajros/collector.py"
  - "kajros/alerts.py"
  - "kajros/gtfs.py"
  - "kajros/db.py"
  - "kajros/peroni.py"
  - "kajros/brskalnik.py"
  - "kajros/zamude_sz.py"
  - "kajros/ovire_sz.py"
  - "kajros/iz_lege.py"
  - "kajros/viri.py"
  - "kajros/nap.py"
  - "kajros/zamude_lpp.py"
  - "kajros/zdravje.py"
  - "kajros/zive.py"
---

# Kaj feed pošlje in kje laže

Vse **izmerjeno na živem feedu**. Kdor pravilo spremeni, izmeri znova in številko zapiše sem. Strežba (starost leg, predpomnilnik, meja žive vožnje): `strezba.md`.

**Vlaki in avtobusi ne pošiljajo istega** (delež postankov v enem klicu):

| | `arrival.delay` | `departure.delay` | absolutni čas | `uncertainty` | `vehicle.id` |
|---|---|---|---|---|---|
| SŽ | 100 % | 100 % | **0 %** | 100 % | ne |
| Arriva | 61 % | 100 % | 92 % | 0 % | da |
| Nomago | 42 % | 100 % | 97 % | 0 % | da |
| LPP | 39 % | 99 % | 100 % | 0 % | da |
| AP MS | 31 % | 100 % | 94 % | 0 % | da |

* **Nikoli `stu.arrival.delay` naravnost.** Neizpolnjeno = 0 = „točno“: zapisalo 11 906 od 20 523 avtobusnih vrstic (58 %), delež točnih 84,3 % namesto 71,2 %. `collector._delay_of()` polje preveri, ob absolutnem času zamudo izračuna (proti poročani odhodni: mediana −9 s, 87 % v minuti).
* **`COALESCE(delay_dep, delay_arr)`, ne obratno.**

Vlak nosi **samo `delay`**; dejanski čas = vozni red + zamuda:

* **Ločljivost 60 s**, `uncertainty: 120`. Sekund ne kaži. Hitrosti samo na odsekih ≥ 5 km (`segment_speeds()`).
* **Feed = drseče okno** — klic da postanke okoli vozila; vožnja se sestavi iz zaporednih pollov.
* **Meja meritev/napoved = `stats.last_measured()`.** Napaka že dvakrat (`/api/live`, tabla: IC 502 +17 v Borovnici, tabla v Litiji **0 min**).
* **Enotna zamuda čez vso vožnjo pri avtobusih sumljiva, ni dokaz.** 3 636 voženj z ≥ 5 postanki: železnica enotna 19,7 %, **nikoli nad 60 min**; avtobusi 2,2 %, a 11 od 20 nad 60 min (A6345: 7 800 s na 46 postankih). Prikaza namenoma ni: fizično mogoče, 20 primerov premalo. Velja samo `api.MAX_LIVE_DELAY_S`.
* **Iz `obs` se ne vidi, kdaj je bila vrednost POTRJENA** — piše le ob spremembi (`OBS_MIN_DELTA_S`). Za nazaj meritve od nepopravljene napovedi ni mogoče ločiti (RG 1604 na Zalogu 4 od 8 dni natanko zamuda ob prihodu v Ljubljano = napoved). Živo reši `last_measured()`, zgodovina ne. **Ne pomaga**: vsiliti fiziko zaporedju napovedi (MAE 1,92 → 1,96, v 5 min 91,0 → 90,8 %) — rezerva je tudi v voznem času.
* **Ne verjemi ničli za en klic.** 14 % postankov z > 2 zapisoma: X, 0, X v minuti. `run` ničlo po zamudi ≥ 5 min sprejme šele po drugem pollu (`collector.is_zero_blip`); `obs` vse. Isto pri legi vlaka.
* **Odhodni zamudi na dolgem postanku ne verjemi** — feed objavi ničlo pred prihodom in je ne popravi (RG 1604 Ljubljana prihod +19, odhod 0, Zalog +5; pet dni od devetih). `stats.typical_dwell()` dan šteje le, ko sta naslednja postanka skladna (< 2 min), postanek računa iz **naslednjega** postanka.
* **Prihodna ≠ odhodna.** LP 4219 Most na Soči (9 min križanja): +10 → +3. 406 postankov ima > 2 min zadrževanja; v 9 dneh razlika pri 1 307, od tega 362 ≥ 5 min. Prikaz = odhodna; pri razliki ≥ 1 min vrstica postanka pove **obe** z besedo (`dwellSplit`, `dwellNoteHtml`: „vlak je stal 9 min namesto 2 — izgubil 7 min“).
* **`delay_report` je iz zemljevida SŽ, ne od SŽ.** `SZ-DELAY-*` je sestavljal derp.si iz `naslednja_postaja` + `zamuda_min` (od 5 min, izjemna od 30). Od 11. 10. 2026 piše `zamude_sz.porocilo` z našim imenom postaje; `alerts.ingest` derp-ovih ne piše, dokler vodi zemljevid. Poročilo je **svežejše od meritve** (64 voženj: 97 %, mediana +40 s); kraj in zamuda **iz istega vira**. Zaporedja poročil (`/reports`) okno vožnje ne kaže več (24. 10. 2026).
  * **Postaja v poročilu = KAMOR vlak pelje.** 26 711 poročil: 92 % zajetih > 1 min **pred** pričakovanim prihodom na X (mediana 3,9 min), 96 % po odhodu s prejšnjega. Zato je na kartici „napoved prevoznika → X“ (`api._dodaj_porocila`), vlak stoji na zadnji meritvi; **lege iz poročila ni**.
  * **Velja samo za svoj prometni dan in dokler je novejše od meritve.** Združevanje po številki čez dneve je dalo 4 od 22 vlakov včerajšnjo zamudo (LPV 2427, poročilo staro 23,6 h).
* **Zakaj zamuja, povedo ovire** (`ovire_sz.py`). `SZ-OVIRA-*` vezane na `route_id` (1 : 1 s tripom). Avgusta 2026 ~45 hkrati.
* **Odpovedi niso strukturirane.** SŽ `schedule_relationship` vedno `SCHEDULED`; odpoved je besedilo (`effect = 6`). Zajem polje šteje in zavpije ob prvi neničelni; prikaza namenoma ni.
* **Ko feed izgubi vozilo, objavlja uro namesto zamude**: za prevožene postanke vrednost raste natanko minuto na minuto (LPP 25: +58/+126 → +482 … +842 → nazaj). 11 827 zaporedij pri 947 vožnjah; pojasni tudi enotno zamudo (N6571 27 060 s). `collector.undoes_passing` zavrne vrednost, ki bi postanek z meritvijo prevoza izpred > 120 s prestavila v prihodnost; **dokaz prevoza = različna prihod in odhod** (EN 1276 `0/0` = napoved, nato pravih +114). `kajros repair` na 10 dneh: 852 vrstic (277 avtobus, mediana 51 min; 300 železnica, mediana 14 min). **`repair` popravi samo postanke, kjer je varovalka sprožila** — prepis vsega je 16 696 vrstic pogrobil za 4 217 popravkov.
* **Zamuda za vožnjo, ki se še ni začela = zamuda PREJŠNJE vožnje vozila** (LPP 25 Medvode: +8 … +14 pred odhodom, odpeljal točno; `run` obtičal, ker `is_zero_blip` čaka drugo ničlo). `collector.is_forecast`: vrednost, ki postanek postavlja v prihodnost, ni meritev; ničla, ki jo popravlja, ni blip.
* **Zgodovina poti zamejena na `trip_id`**, ne `train_no` + `stop_seq` (LPP 25: dva kraja pod „postanek 2“). Železnica 0 od 663 številk z več vožnjami, avtobusi 205 od 242.
* **Na izhodišču prihoda ni** — feed ga za `stop_seq = 1` pošlje kot smet (−267 s, −1771 s). `common.dwellSplit()` prvi postanek preskoči.
* **Ni** cen, sestave, zasedenosti, tira (tir s table SŽ, spodaj). EN/MV pogosto brez realtime.
* Vreme ima arhiv: `kajros weather` dopolni kadarkoli.

## Avtobusi

* **Veriga vozila (`block_id`) = edini odgovor, kje je avtobus pred začetkom.** Samo avtobusi, 7 547 od 20 736 voženj (36 %), 1 385 blokov; 0,9 % prekrivanj, mediana postanka 14 min. Isti blok pri več `service_id` → sosed **po obratovalnem dnevu**. Ob 20:22 17 od 25 bližnjih voženj s prejšnjo v bloku, 11 s svežo lego.
* **Zamude prejšnje vožnje ne prenašaj.** 195 parov: prenos MAE 4,53, „točno“ 2,29 — slabši od nevednosti; prenese se 11 %. Prejšnja vožnja = **dejstvo o vozilu**, ne napoved.
* **`bikes_allowed` povsod 0** (ni podatka), `wheelchair_accessible` ga ni — uvoz ne bere.

## Mestni LPP: drug feed, laže drugače

Mestnih linij **v IJPP ni** (le primestne 40–84). Vozni red `avl.lpp.si/transit/api/gtfs` (31 prog), živo `rt.gtfs.derp.si/sources/lpp/all`. Brez ključa.

* **`delay` vedno 0** (2 721 in 2 604 postankov, nobena neničelna). `arrival.delay = 0` brez časa = mesto za vožnjo, ki je ne napoveduje (18. 10. 4 550 takih; navaden dan 9,4 % vrstic LPP, 93 % vseh ničel). Od 18. 10. 2026 `ingest(vir="lpp")` `delay` preskoči (`beri_delay`), šteje samo čas. Zgodovina pred tem ostane.
* Zamuda v absolutnih časih — `_delay_of()` bere `.time`.
* Kakovost: mediana 0, p95 +7, p99 +23, nad 2 h nič (IJPP 2 541 vrstic nad 4 h).
* `trip_id` = trojni UUID (`service|?|trip`), 1 : 1 z `avl.lpp.si`, ne z NAP. Okno uvoza osem dni (mesec = 62 989 voženj).
* **Koda postajališča** (`stop_code`, 600011) → `station.koda` ob uvozu (od 22. 10. 2026; IJPP brez). Migracija pozabi `lpp_etag`, da jo naslednja osvežitev napolni. Rabi jo smer table („v center“, `strani.md`). Poti z `trip_id` iz zahteve: meja `stats.TRIP_NAJDALJSI` (200).
* **1 : 1 ni zagotovljeno.** 1. 10. 2026 17 % voženj z UUID-jem, ki ga ni v nobenem voznem redu; 26. 10. vsa 27 po drugi trasi. Kar se da, pripne `zive.py` (spodaj). LPP vozi **drug vozni red**, kot ga objavi (linija 14: 78 odhodov proti 66 v GTFS). Neznane brez para `ingest` šteje **po progi**, samo z napovedjo, `meta.lpp_linije_brez_voznje` (s postajališči) in `meta.lpp_vozila_brez_voznje`; v `run`/`vehicle_now` nič; tablo napolni `lpp.na_tablo` (`strezba.md`).
* **Imena postajališč**: 12 % VELIKE ČRKE. `gtfs._poenoti_imena()` zlije le zapise **na istem mestu** (500 m, tudi prek tretjega), ne vse skupine istega imena („Celje“/„Čelje“ 112 km; daljni „Trnovo“ je do 19. 10. ustavil zlivanje).
* **Pošilja samo postanke PRED vozilom** → v `run` pri LPP **nikoli meritve**, le zadnja napoved pred prehodom (mediana 42 s pred). Kakovost napovedi pri LPP = napoved proti napovedi.
* **Obvoz je po vožnji** (`stop_id` + `trip`, nikoli `route_id`; maraton 17. 10.: 2 808 parov). V `alert_entity`, `alerts.ne_ustavi` za tablo, zveze, pot. **Isti naslov za nov dogodek** — obdobje se ob vsakem branju prepiše (`alerts.zapisi`). Primestni (1118): `lpp.obvozi_zaslonov` (`type` 3). Odpoved (CANCELED) pri LPP obstaja: `collector.odpovedane`, v pomnilniku 5 min.
* **Obvoz se konča tako, da izgine iz feeda** — `end_ts` ostane v prihodnosti (2 od 4 „veljavnih“). `meta.lpp_obvestila_prebrana`; `for_stops()` kaže obvoz le, če viden ≤ 10 min pred zadnjim branjem (`OBVOZ_REZERVA_S`).

## Žive vožnje LPP brez voznega reda (`zive.py`)

Id = `dan|vožnja|vzorec`: dan in vzorec poznamo, vožnje ne. 26. 10. 2026 linija 27 (14 od 15 v feedu) po Vilharjevi (Navje), objava mimo kolodvora (Kolodvor, Friškovec).

* **Par živa → objavljena** (`ziva_voznja`): zamuda, lega, obvoz gredo pod objavljeno, postanki **po postajališču** (`preslikaj`), ne po številki. **Brez para ni zamude, napačen par je zamuda druge vožnje.** Dokaz:
  * **načrt**: zaslon LPP (vrsta 1) za vozilo žive kaže uro objavljene na istem postajališču ± 90 s (13 od 13 načrtov 38–40 s za objavo). Ko vozi, mora napoved dati zamudo −10 … +90 min (linija 1: načrt za vozilovo vožnjo 64 min pozneje). Pred odhodom najzgodnejša in prosta prejšnja ne sme obstajati (linija SŽ: načrt za 17:55, vozilo čakalo na 17:15).
  * **ura**: napoved na skupnih postajališčih −4 … +10 min od ene, nobena druga v −4 … +20 min; po vrsti začetka. Gosta linija ostane brez para (1: 12 od 23, 6: 10 od 20).
  * Ponovitev 26. 10. (215 branj feeda, 796 zaslonov, znane vožnje preimenovane): 252 parov, 0 napačnih; ura proti načrtu 143 : 0 (`soglasje`, `/admin`).
* **Zasedena ni na voljo**: objavljena z napovedjo ali vozilom pod svojim id-jem ali z drugo živo. Vnos brez obojega ne šteje (linija SŽ: objavljeno je feed nosil uro brez ure in vozila, vozilo pa je vozilo pod drugim id-jem ob njenih urah). Par pade, ko objavljena dobi napoved ali vozilo pod svojim id-jem ali je uvoz nima več.
* **Dvojnik** (`_dvojnik`): živa, ki se najbolje ujame z zasedeno in od njene napovedi ne odstopa > 5 min, se preskoči, ne šteje in ni na zemljevidu (linija 2: brez vozila, zadnjih šest postankov, 0–5 min pred objavljeno).
* **Šteje se le z napovedjo**: nezačeta neznana čaka na par (27: 5 od 13 brez ure bi linijo vrgla „mimo voznega reda“).
* **Popravek vzorca** (`popravi`, `popravek_vzorca`): sparjena z drugim vzorcem → objavljena dobi postanke vzorca svoje žive; ob ≥ 2 sparjenih brez nasprotnega dokaza še vse objavljene tega dne, proge in vzorca brez para in meritev (27: 117 voženj). **Ure in številke skupnih postankov ostanejo** (meritve, zgodovina drugih dni, `zamenjava`), novi na prosto številko vmes, ura po voznih časih vzorca, na minuto. Predloga: najdaljša vožnja vzorca drug dan, sicer živa z vsemi postanki.
  * **Meritve** = `run` ali `obs` (dnevnik hrani tudi ničle, ki jih `run` ni sprejel; `repair` bi jih vrnil po objavljenih številkah). Vožnja z meritvami se ne prestavi -- razen sparjene (meritve po postajališču, na skupnih postankih) in ob uvozu.
  * **Nasprotni dokaz** = LPP ta dan vozi tudi objavo -- par z istim vzorcem, objavljena pod svojim id-jem z napovedjo ali **z meritvami** (v feedu je le, dokler vozi) -- ali še drug živ vzorec. Tedaj samo sparjene; prestavljene po skupini se **vrnejo** (`_vrni`, konec obvoza). Vrne se tudi prestavljena pod svojim id-jem z napovedjo na postajališču samo iz objave in sparjena, prestavljena na drug vzorec, kot ga vozi njena živa (naslednje branje jo prestavi prav).
  * Vrnitev pobriše meritve na postankih, kjer ima objava drugo postajališče: pod objavljeno številko bi kazale drug kraj. Samodejna jih nima (po skupini brez meritev; sparjena na tujem vzorcu jih ima le na skupnih).
  * Feed pod id-jem prestavljene ali pod starim id-jem (`zamenjava`) prestavljene naslednice: postanki po postajališču, ne po številki.
  * **Ostane**: zgodovina na novem postanku (Navje pod številko Kolodvora) je zgodovina izpuščenega -- druga dneva iste vožnje in `prednik` vežeta po številki. 26. 10.: 0 vrstic `prednik` in `zamenjava` za 117 prestavljenih; drugi dnevi 27 tega tedna so prestavljeni enako.
  * Uvoz: `uporabi_popravke` na isti vožnji ali naslednici (`zamenjava`), s shranjeno predlogo (`prestavljen`), tudi z meritvami. Napaka v njem uvoza ne ustavi.
  * Značka `meta.vozni_red_popravljen` je v `db.znacka_reda` → predpomnilniki voznega reda; strežnik po popravku ogreje pot.
* Izklop `KAJROS_ZIVE=0` (vse), `KAJROS_ZIVE_POPRAVKI=0` (popravki). `kajros zive --razveljavi DAN|vse` vrne objavo in ta dan ustavi prestavljanje (`meta.zive_razveljavljeno`, vidi ga tudi strežnik).
* `razresi` 25–45 ms na branje pri ~90 neznanih (preimenovanje); prej 120–150 ms (kazalo postajališč, neuspeli popravek se ne ponavlja, `CROSS JOIN`: brez statistike nove tabele 19 ms namesto 0,3).

## Nov vozni red, stari id-ji v feedu

* **Feed ima svojo kopijo voznega reda.** 22. 9. 2026 LPP 25, 12D, 15 nova storitev; feed še popoldne pod **starimi** id-ji → zavrženo, 0 od 62 voženj v `run`. Id pride **iz naprave na vozilu** (NAP SIRI `VehicleJourneyRef`), ne od derp.si.
* **Nov vozni red ni le preštevilčen** (25: 65 → 52 min). `gtfs.povezi_zamenjave()`: ista linija in prevoznik, skupen dan, ≥ 60 % postankov v istem vrstnem redu (po `stop_id`), najmanjši premik na **prvem skupnem postanku** ≤ 10 min, nova vožnja največ enkrat. 22. 9.: 195 od 210. Širiti 10 min ne pomaga — manjka vozilo v feedu, ne pravilo (linija 15 ni v feedu pod nobenim id-jem; edini vir data.lpp.si).
* **Zamuda se preračuna, ne prepiše** (`collector.zamuda_po_zamenjavi`): ohrani se ura, odšteje nov vozni red (15:29 +20 → 15:28 +21). Preverjeno: feed +345 s, po prevodu +45 s = resnica.
* **Par nastane samo ob uvozu**; pozneje: `kajros zamenjave <varnostna kopija izpred uvoza>`.
* **Zip brez prevoznika se zavrne** (`gtfs.izginuli_prevozniki`; 28. 9. 2026 DUJPP 0 voženj SŽ). Meja nič, ne delež. **Pomešane trase** (`gtfs.tuje_trase`): prevoznik z ≥ 20 vožnjami s traso in > polovico tujih (prvi postanek > 2 km od začetka) → zavrnjen.
* **Neznane se štejejo**: `meta.rt_neznanih`, `lpp_rt_neznanih` (`n/vseh`), rdeče nad 2 %. Stare vožnje prevoznikov, ki jih vodi NAP, se ne štejejo (od 14. 10.), ko NAP molči, spet.
* **Vožnje, ki jih feed zamud sploh ne nosi** (od 21. 9. 2026 IJPP brez voženj z veljavnostjo od 21. 9.; lege so): `lega_brez_zamude` [ne v feedu, brez zamude, z lego] po prevozniku. Šteje 15 min po voznem redu **tretjega** postanka (pri drugem + 10 min: 10 lažnih epizod 13. 10.; izhodišča lega ne meri). Vožnja s ≤ 3 postanki se ne šteje.
* **Zgodovina gre čez zamenjavo** (`db.PREDNIKI_SQL`, `prednik`). **Vez po vožnji čez dneve, trajna** (od 21. 10. 2026): `zamenjava` je za zajem in pri LPP po dnevih; `db.zapisi_prednike` ob uvozu prepiše pare v `prednik` (ključi `voznja_sql`), veriga se sestavi. LPP 13.–20. 10. zamenjal id 228 vožnjam; brez tega okno prazno do treh dni.

  21. 10. 2026, mediana stare (≥ 3 dni) proti vsakemu dnevu nove:

  | | parov | zgodovina | brez (ničla) |
  |---|---|---|---|
  | mestni LPP, isti vozni red | 223 | 3,73 min · 81 % v 5 min | 4,84 · 73 % |
  | IJPP, isti vozni red | 112 | 2,22 · 90 % | 4,84 · 70 % |
  | IJPP, drug vozni red, prevod po uri | 95 | 3,12 | 8,00 (brez prevoda 6,32) |

  **Mestni LPP ne vozi ob urah stare** (LPP 16: 07:35 namesto 07:45, prevod +10, MAE 12,2) → vez le, če razlika na nobenem skupnem postanku ne preseže 3 min (`db.PREDNIK_LPP_RAZLIKA_S`); do 3 min MAE 4,97.

## Zamuda iz lege in prehod brez trase

* **Kar feed zamud izpušča, izmerimo iz lege.** Rezerva (`KAJROS_PREHOD_GPS=0`): `iz_lege.py` — lega na traso, prehod med legama ≤ 60 s narazen, zapis v `run`/`obs` kot iz feeda s časom lege po prehodu; s feedom 92 % na minuto. Izhodišča ne meri. Samo s strežnikom (malina `KAJROS_POSITIONS=0`), izklop `KAJROS_ZAMUDA_IZ_LEGE=0`. Vožnja, ki jo feed v 5 min omeni, gre mimo; 304 = vožnje ostanejo „v feedu“ (`iz_lege.feed_nespremenjen`).
* **Kjer vozilo ne vozi po trasi, prehoda ni** (3 % vmesnih postankov). **Varoval ne rahljaj** (mediana 83 s proti 29 s) — popravi se trasa. Stari način beleži `odklon` in `vrsta = 'preskok'` (projekcija skoči čez zanko > 30 m/s); `kajros odkloni` po odsekih.
* **Prehod brez trase** (`prehod.py`, vodi od 13. 10. 2026): obisk = vozilo v 100 m; čas = odhod (zadnji trenutek v 50 m), na cilju prihod. Postanki po vrsti, med naslednjimi osmimi; obisk s preskokom velja šele, ko se konča skladen kasnejši. Prvi obisk in skok > 20 min čakata; prvi brez preskoka velja sam po 15 min (`POTRDI_PRVI_S`; pri 10 štiri napake, pri 15 nič), razen pod −120 s. Prvi dan: 96,9 % vmesnih proti 89,7 %, mediana 7 s, p90 44 s, cilj 84 % proti 39 %. `KAJROS_PREHOD_GPS`: `vodi` (privzeto) / `senca` / `0` (rezerva **do 27. 10. 2026, nato ven**, če vodi drži). Z `vodi` se odklonov ne beleži. Lege v `lega` 14 dni, sled se ob zagonu obnovi.
* **Sled je po vozilu** (`lega.vozilo`): NAP pod isto vožnjo javi dve vozili (~0,5 % voženj). Velja vozilo z največ prehodi (`prehod._izberi`). Prevzame tudi vozilo, ki nadaljuje za zadnjim postankom vodje, ko vodja `CILJ_S` molči (Nomago menja avtobus na poti). **Ne prevzame**, če je na ≥ 2 skupnih postankih `DRUGA_S` (10 min) dlje od voznega reda (NAP prijavi naslednjo vožnjo). Vodja ostane `OKNO_POZNEJE_S` po zadnji legi. Zemljevid kaže vodjo (`prehod.vodja`, `nap.zapisi`). `kajros prehodi` smiseln le do 13. 10.

## Vožnja, obratovalni dan, dnevnik

* `trip.start_s` / `end_s` = prvi odhod in zadnji prihod, iz `sched` (`db.fill_trip_window()`). Vstavljanje mimo uvoza ju mora zapolniti, sicer vožnja **ni živa**.
* **Feed včasih objavi jutrišnji obratovalni dan** (0,026 % vrstic, 2 vožnji, zamuda > 6 h). Pravila namenoma ni — `api.MAX_LIVE_DELAY_S` (6 h) jih drži ven. Meri: `SELECT COUNT(*) FROM run WHERE service_date > date('now','localtime')`. Železnica nikoli čez 3 h (EC 79 2,9 h).
* Indeks `trip_block` je delen (`WHERE block_id IS NOT NULL`).
* **Zajem piše samo ob spremembi ≥ `OBS_MIN_DELTA_S` (60 s) od zadnje ZAPISANE** (lezenje se sešteva). Vlaki 1,6 zapisa na postanek, mestni avtobusi 23,3 (mediana spremembe 15 s). `run` ostane točen.
* **Dnevnik se obrezuje, `run` nikoli.** Z NAP in prehodom 1,6–1,9 mio avtobusnih vrstic `obs` na dan; obrez v eni transakciji držal zapis 116 s → po kosih (`collector.PRUNE_KOS`). 79 B na vrstico. `collector.prune_obs` / `kajros prune`: železnica 90 dni, avtobusi 14. `run` = zgodovina (statistika, običajna zamuda, backtest), brisati ga = brisati projekt; če že, najprej avtobusni. `vehicle_now` = upsert, starejše od ure se briše.

## Obvestila SŽ (4. 9. 2026)

`parse_delay_text()` razčleni 474 od 474. Poln zapis je v `description`, ne `header` — `parse_delay_text(desc) or parse_delay_text(header)`, obratno nič. Vsa poročila `prihod` (veja za odhod nikoli stekla). Vrste samo `SZ-DELAY` / `SZ-OVIRA`. Vsako obvestilo eno obdobje (varovalo `vec_obdobij`).

## Lege so stare, ni naša zamuda

`seen_ts` = `vehicle.timestamp` **iz feeda** (prikaz trdi „lega stara N“). Mestni LPP normalno **57–147 s** (feed se osveži na ~90 s v paketu). Preden iščeš napako: `seen_ts` proti `vehicle.timestamp` (99 od 99). LPP feed brez `ETag`/`Last-Modified` — vsakič 315 kB.

## potniski.sz.si: Chrome mimo Cloudflara (`brskalnik.py`)

Od 7. 10. 2026 Cloudflare zavrača brezglave; beremo s Chromom (10. 10.):

* **Samo Chrome z oknom** (Xvfb `-displayfd`). Izziv reši v 3–7 s, zahteva nato 0,5–0,8 s (`fetch` v strani, `cf_clearance`).
* **CDP po cevi ali `--remote-debugging-port=0` NE gre** — Chrome postavi `navigator.webdriver = true`. Lastna vrata → `false`: `_prosta_vrata()`, lasten WebSocket (`_Ws`, brez odvisnosti).
* Piškotek občasno zavrnjen (403): ponovno nalaganje (7 s), zahteva enkrat znova; drugi izziv zapored ugasne Chrome.
* Cena: Chrome ~400–560 MB PSS, Xvfb 75 MB. Zagon ob prvi zahtevi, vsakih 6 h znova (`NAJDLJE_ZIVI_S`). Po neuspelem zagonu 5 min pavze; po `net::ERR_…` le 30 s (`PO_NAPAKI_OMREZJA_S`).
* Teče na arwenu (`deploy/brskalnik.sh`: Google Chrome — AppArmor dovoli peskovnik — in Xvfb). **Malina ne more** (armv6). Razvoj brez Xvfb odpre okno. Preizkus: `kajros brskalnik`. Stanje v `/admin` → Stroj.
* Izpis napak: `${KAJROS_DATA_DIR}/sz-brskalnik-{chrome,xvfb}.log`, ob izhodu s kodo kopija `…-napaka.log`. `_preberi_zaslon` bere do konca vrstice (Xvfb številko in `\n` zapiše posebej; prej „Missing X server“ 6 od 43 zagonov).

## Tir s table SŽ (`peroni.py`)

Tir ima samo tabla (`/odhodi-in-prihodi-na-postaji/?postaja=<št. SŽ>&datum=<d.m.llll>`, 150–175 kB HTML; 282 postaj).

* **Tir je dodatek**: samo, če ga je potrdilo ZADNJE branje, ne zamujeno za > 2 razmika (`peroni.tiri`). `KAJROS_PERONI=0` ugasne, nič drugega ne pade.
* Tabelo loči naslov („Odhodi vlakov“ / „Prihodi vlakov“), vrstica = slovar po glavi brez zvezdice.
* „BUS“ v stolpcu tira ni tir. Vlak brez številke se ne šteje.
* **Svoja nit, ena postaja naenkrat.** Ritem: Ljubljana, Maribor, Celje vsakih `KAJROS_PERONI_SECONDS` (600 s), majhne redkeje, najdlje 2 h.
* **Tir je lastnost postaje**: 14 od 20 vedno, 6 nikoli (Jesenice, Novo mesto, Kranj, Dobova, Trbovlje, Škofja Loka); brez tira enkrat na dan.
* Tabla kaže le vlake, ki še pridejo; mednarodnih 1472, 210, 211, 79, 350 ni.
* **Ključ = koledarski dan table + številka brez vrste** (vlak ob 00:30 je na naslednjem dnevu).
* Tir se čez dan spreminja: `prvi` ostane, `tir` se posodablja, prikaz napiše „prej 6-A“.

## Zamude vlakov z zemljevida SŽ (`zamude_sz.py`, vodi od 10. 10. 2026)

`/wp-admin/admin-ajax.php?action=aktivni_vlaki` (JSON 3–5 kB; brez vlakov `null`) = **izvor vseh zamud vlakov** (derp.si isto prek `api.modra.ninja`). Vlak po **številki** — pokvarjen zip DUJPP ga ne prizadene.

**Vodi** (David: „raje 15 s prej in brez posrednikov“): dokler prebran v `iz_lege.SZ_VODI_S` (120 s), derp.si vlakov (`zeleznica`, `mode != bus`) ne piše (`collector._sz_vlaki`, `sz_prevzel`); nadomestni avtobusi ostanejo derp.si.

Polje `Vrsta`:
* **1 vozi**: `Postaja` = naslednja, `Odhod` = vozni red PREJŠNJE + `Zamuda_cas` (preizkus prave vožnje in dneva; brez ujemanja se ne pripne).
* **0 stoji na izhodišču**: ni meritev.
* **2 na cilju**: `Odhod` = dejanski prihod. Čez 1–2 min SŽ ponastavi na 0 — velja prvi prihod; ničla po > 3 min = ponastavitev (`PONASTAVITEV_S`).

Pravila:
* **Vlak ne gre nazaj z isto ali manjšo zamudo** (`nazaj`); **z večjo velja** (od 16. 10.) — zemljevid je **izračun** (vozni red + trenutna zamuda), vlak, ki nabira zamudo, skoči nazaj. Staro zavračanje: 76 prikazov ≥ 3 min prenizkih na 13 min, novo 1.
* **Ničla po zamudi velja šele potrjena** (`_nicle`, `nicel`): SŽ na 3–4 min za en odgovor del vlakov nariše po voznem redu (16. 10.: 7 od 59). Z „ne gre nazaj“ je bila **zaskočka** — 11.–16. 10. **611 od 1 444 voženj z zamudo** prenizkih. **Primerja se z zadnjo besedo SŽ** (`sz_zamuda` po `zadnjic_ts`), ne s postankom najdlje naprej. SŽ včasih sam riše vlak po voznem redu več minut (EC 115 +0, nato +21) — tega ne loči nič.
* **Trenutna zamuda ≠ zamuda zadnjega postanka** (`zamude_sz.trenutne`, `stats.trenutna_zamuda`): vlak stoji, SŽ `Zamuda_cas` raste, `Odhod` je v prihodnosti. Ta vrstica **ne gre v `run`**, pripne se z odhodom do 3 h naprej (`NAJDLJE_NAPREJ_S`, `prihodnjih`). `last_measured` doda `trenutna_s`, kadar SŽ ≥ 1 min višja in sveža (≤ 60 s); rabijo jo glava okna, napoved, tabla, iskalnik, kartica (`api._s_trenutno`), senca. Samo navzgor. 11 od 4 453 trenutkov — a ravno ko vlak obtiči.
* **Ničla po zamudi velja, kadar jo pojasni rezerva** (od 17. 10., `stats._LAST_MEASURED_SQL`, `api._LIVE_SQL`): padec od zadnjega postanka z > 2 min ni večji od vsote postankov > 120 s vmes + 2 min (pri vlaku tudi ničla do 2 min). Fantomov neizvedljivih 97,8 %; na dolgem postanku verjame SŽ (ničla za zamujen vlak je cenejša od zamude za točen).
* **Prezgodnji prihod na cilj ne zaklene `run`** (32 od 360 prihodov, 8,9 %): prihod je „zapisan“ le, ko je bil zadnja beseda SŽ.
* **Straža `zamude_sz.skladnost`** (vrstica `skladnost_sz`): ustaljena zamuda SŽ (≥ 2 min ista, `USTALJENA_S`) proti meji `last_measured` **brez** trenutne. Ne šteje vlaka, ki ga SŽ riše po voznem redu. Okno 30 min; rdeče (pošta po 30 min) ≥ 1 % in ≥ 3 vlaki, rumeno od 0,3 %, pod 300 primerjav brez ocene. Staro 2,3–4,1 % mimo, novo 0 od 3 381.
* **Kam gre**: `sz_zamuda` (zadnje stanje), od 5 min `delay_report`, `run` + `obs` (`iz_lege.zapisi_meritev(..., ohrani=True)`). `feed_ts` = čas branja (po prehodu).
* **Pregled**: `meta.zamude_sz` (zapisanih, pred odhodom, na cilju, nepripetih, prihodnjih, nazaj, nicel, ponastavljenih, `skladnost`, `spremenjeno_ts`). Odgovor se spremeni ob vsakem branju; 10 min brez spremembe rumeno (`zdravje.SZ_ZAMRZNJEN_S`), prazen ob ≥ 3 vlakih po voznem redu rumeno, nit 5 min tiho rdeče.
* **Beremo na 5 s, SŽ preračuna na 15** (55 od 55 sprememb). Nespremenjen odgovor ne premakne časa podatka (`korak(..., nespremenjeno=True)`).
* **Tabla zamud SŽ se ne bere** (11. 10. 2026): le ~5 s pred zemljevidom, pripne se tretjina vrstic, piše prometno mesto, ne postanek. Koda sence v gitu (3c965ab); nazaj samo z novo meritvijo.

## Ovire s strani SŽ (`ovire_sz.py`)

`/pomoc-uporabnikom-in-stanje-v-prometu/`, `var roadworks = [...]` (vzporedni seznami `ID_ovire`, `Naslov`, `Opis`, `Cas`, `Relacija`, `ID_vrste`), 440 kB, isti Chrome, na 5 min (`KAJROS_OVIRE_SZ_SECONDS`), svoja nit.

* Enako derp-ovemu (49 od 49). Besedilo: prelomi v presledke, robovi, šele nato oznake HTML. Veljavnost polnoč–23:59:59.
* **Vezi na vlake so izračun ob vsakem branju** (derp.si enkrat, ob prvem pogledu → 11155 0 vlakov namesto 31). Relacija z „ - “ = proga vlaka z ≥ 2 naštetima postajama, brez = naštete postaje. Imena brez presledkov in vezajev; ločilo = vezaj s presledkom vsaj na eni strani („Zidani Most -Hrastnik“).
* **Vodi slovenske**: dokler prebrana v zadnjih treh obhodih (`alerts.ovire_vodi_sz`), derp-ovih slovenskih `SZ-OVIRA` ne pišemo (`ovir_vodi_sz`); angleške ostanejo derp.si.
* Ovira, umaknjena pred rokom, ostane do `end_ts`.

## Zamude mestnega LPP z zaslonov (`zamude_lpp.py`)

* **`station/arrival` poceni (40–100 ms), `route/arrivals-on-route` ne (mediana 7,4 s)** — beremo postajališča.
* `izberi()` požrešno izbere postajališča, da ima vsako zaporedje ≤ `LPP_POSTAJ_KORAK − 1` (11) neizbranih zapored: ~76. Obhod z dvema delavcema 36 s, na 2 min.
* **Vrsta**: 0 napoved, 1 vozni red (ni meritev), 2 prihaja, 3 obvoz. Piše se le 0 in 2.
* **Vožnje vir ne pove.** Vozilo → vožnja prek `vehicle_now` (derp.si, dokler ga hrani), isti vzorec, **LPP-jeva zamuda v 10 min od derp-ove** (`SKLADNO_S`; brez tega mediana 22 namesto 4,5 min).
* **Po voznem redu ne pripenjamo** (edina kandidatka zadela 67 od 98). `meta.zamude_lpp.po_voznem_redu`. Po uri izpada derp.si vir v `run` ne piše; tabla LPP-jeve prihode kaže naprej.
* **Kam**: `lpp_zamuda`; v `run`/`obs` le, ko derp.si vožnje ne nosi (`iz_lege.brez_feeda`). `kajros primerjava`, `/admin` „LPP · ujemanje · 24 h“. Samo na strežniku.
* **Feed, ki od zagona ni odgovoril, je po 5 min prazen** (`iz_lege.feed_prebran`).
* Zadnji `run` ne pove, ali derp.si dela: `/api/health` `derp_prebran`, pregled „derp.si · odgovoril“ (rdeča po 5 min ob ≥ 3 avtobusih).

## Lege IJPP z NAP (`nap.py`)

* **Dostop**: račun nap.si (`kekec3201@proton.me`), SIRI odobren do 8. 10. 2029. Brez prijave **401**, nit čaka 10 min, rumeno. TLS se preverja.
* **Prijava** `${KAJROS_DATA_DIR}/.nap-prijava` (`e-naslov:geslo`, 640, `kajros`), postavi `deploy/nap.sh` — geslo vpiše David. Bere se ob vsakem obhodu.
* **Id vožnje** = zadnji štirje bajti GUID-a v `VehicleJourneyRef` (kot derp-ov `realisToIjpp`). Dan: `collector.resolve_service_date`. Stari id-ji prek `zamenjava`.
* Čas naprej za uro (±3 min) se popravi. Vožnja čez > 30 min gre ven.
* **NAP nima**: vlakov, mestnega in primestnega LPP (`LJLPP…`) — primestni ob izpadu derp.si brez lege.
* **Piše** `vehicle_now` za vsa pripeta vozila, zmaga novejši `seen_ts`; premakne `positions_fetched`.
* **Zamude medkrajevnih vodi NAP** (`config.NAP_PREVOZNIKI`: 1123, 1119, 1121): feed derp.si te vožnje izpusti (`iz_lege.nap_vodi`, `nap_prevzel`, `iz_lege.izpusti`), zamudo meri `iz_lege.opazuj` iz leg NAP; `iz_lege.iz_feeda` jih preskoči. Dokler prebran v 60 s (`NAP_VODI_S`). Izgubi se derp-ova napoved naprej in odhod z izhodišča.
* Ujemanje z derp.si (`nap.primerjaj`): ista vožnja 99,5–100 %, odmik 0,1 m, NAP novejši 7–20 s.
* Cena: 2,7 MB XML, 162 kB gzip; ~1,4 GB/dan. ETag se spremeni vsakič.

## Promet na cestah z NAP (`promet.py`)

Za „kdaj je vlak hitrejši od avta“. Ista prijava, nit `kajros-promet`, vsako minuto, **svoja baza** `promet.sqlite` (40–60 MB/dan, brez varnostne kopije).

* **FCD nosi samo gnečo** (vsak odsek ≥ 20 % počasnejši od proste). Odsotnost = prosto → `fcd` piše `NULL`. Vrzel med `obhod` = neznano, ne prosto.
* Dnevnik ob spremembi ≥ 0,5 s (`PRAG_DS`) od zadnje ZAPISANE (`fcd_zdaj`).
* Ima tudi mestne ulice. Geometrija v `b2b.fcd.datexii33.locations` (OpenLR, 3 GB) — nit je ne bere.
* AC: deset relacij DARS, `ac` po času objave.
* FCD je **datoteka gzip** brez `Content-Encoding` — `razberi_fcd` razpakira sam.
* **Razbor v svojem procesu** (`promet._Razbor`, `spawn`): v niti je držal GIL (tabla 520–610 ms namesto 22).

## Napaka pisanja: najprej `conn.rollback()`

Vsaka nit svojo povezavo, vsak `except` okoli pisanja najprej razveljavi. Sicer zamrznjen posnetek → vsako pisanje „database is locked“ (SQLITE_BUSY_SNAPSHOT) za vedno (1. 10. 2026: nit stala 4,3 h, WAL 5,4 GB). `journal_size_limit` 64 MB v `db.connect()`. Preizkus `test_nit_po_zaklenjeni_bazi_ne_obstane`.

## Nov vir: `viri.vsi()` in `viri.branje()`

Vir opisan enkrat v `viri.vsi()` (naslov, izvor, licenca, ritem, nit, ključi zdravja, ukrep ob izpadu, naslov za preverjanje). Klic na tuj strežnik: `with viri.branje("<ključ>") as b:`. `test_vsak_klic_na_tuj_streznik_je_v_registru`.

* „Ne odgovarja“ šele ob `prag_napak` zaporednih (3; dnevni 1).
* Vir brez svojega pravila v `zdravje.ocena()`: rumeno (`vir:<ključ>`), nikoli rdeče. Vir s pravilom splošnega nima.
* Mrtva nit rdeča (`nit:<ime>`), kadar je zajem zagnan (`viri.zajem_zagnan`).
* Vozni red, ki se konča: IJPP rumeno teden prej, rdeče dva dni prej; LPP rumeno, ko okno < `LPP_DAYS − 2`.
* Podproces (`KAJROS_REFRESH=subprocess`): `viri.shrani()` v `meta.vir:<ključ>`.
* `derp` razdeljen na `derp_ijpp` in `derp_lpp`.
