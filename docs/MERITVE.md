# Izmerjeno

Številke = stanje, ne pravilo: koliko zajetega, koliko stane, kako hitro teče. Se starajo — ob vsaki spremembi popravi datum.

## Hitrost odgovorov (4. 9. 2026)

Razvojni računalnik, 832 000 vrstic `run`, 6,3 mio `obs`, ogret predpomnilnik:

| endpoint | prej | zdaj | kaj narobe |
|---|---|---|---|
| `/api/health` | 1223 ms | **80 ms** | `COUNT(*)` čez `obs` in razrez `run JOIN trip` ob vsakem klicu; stran ga kliče vsakih 30 s |
| `/api/live?network=zeleznica` | 245 ms | **5 ms** | predpomnilnik se razveljavi ob vsakem zajemu = ista perioda, kot ga zemljevid vpraša |
| `/api/departures?station=…` | 145 ms | **15 ms** | `MIN/MAX(stop_seq) GROUP BY trip_id` čez 403 208 vrstic `sched` ob vsaki zahtevi |
| `/api/connections` | 87 ms | 40 ms | — (najtežja poizvedba 25 ms, prostora ni veliko) |
| `/api/stations/search` | 53 ms | 56 ms | — |

Vzorec vseh treh popravkov: **agregat, ki se med zahtevami ne spremeni, se ne sme računati v zahtevi.** Dvakrat = statika voznega reda (shrani se ob uvozu), enkrat = delo, ki ga zajemna nit opravi vnaprej.

## Pokritost zajema (4. 9. 2026)

Koliko voženj iz voznega reda vidimo v realnem času:

| kaj | v voznem redu | zajetih | pokritost |
|---|---|---|---|
| pravi vlaki | 601 | 598 | **99,5 %** |
| nadomestni prevoz SŽ (`BUS …`) | 53 | 0 | **0 %** |
| avtobusi | 10 007 | 9 799 | 97,9 % |

Merjeno 3. 9. 2026, ponovljivo 1.–3. 9. (nihanje pod odstotkom). **Skupna železniška pokritost je videti 91 % samo zato, ker šteje nadomestne prevoze.** Teh 56 v voznem redu ima v 15 dneh zajema **nič** meritev — feed zanje ne poroča.

Avtobusi 31. 8. 63,1 %: zajem takrat še v vzponu; od 1. 9. nad 95 %.

## Model po omrežjih (4. 9. 2026)

`kajros backtest`, izpuščanje enega dne. Železnica 15 dni, **521 781** nalog; avtobusi 7 dni, **6 004 849**.

| model | železnica MAE | v 5 min | avtobusi MAE | v 5 min |
|---|---|---|---|---|
| **rezerva+razred (v uporabi)** | **2,06** | 90,0 % | 2,98 | 93,0 % |
| združen | 2,07 | 89,6 % | **2,85** | **93,6 %** |
| odsek+razred | 2,36 | 87,5 % | 2,89 | 93,4 % |
| rezerva+mediana | **2,00** | **90,5 %** | 3,16 | 92,4 % |
| prenos | 3,04 | 82,3 % | 3,38 | 91,0 % |

Zgodovino ima 88 % železniških voženj (82 % vsaj tri dni) in 77 % avtobusnih (47 %). Razlaga in posledice: `.claude/rules/model.md`.

## Avtobusni model (19. 9. 2026)

Kopija baze z arwena 19. 9. ob 00:20 (`VACUUM INTO`; `.backup` se med zajemom vrti v krogu). Avtobusnih vrstic `run` **3,25 mio** v 21 dneh (29. 8.–18. 9.), dnevnik `obs` 21,7 mio (4.–19. 9.), senca 271 095 razrešenih avtobusnih napovedi (3.–18. 9.). Nastala pravila in kaj ni pomagalo: `.claude/rules/model.md`, „Avtobusni model“.

**Mestni LPP ni imel zgodovine.** Od 603 140 njegovih vrstic `run` jih je 489 k (81 %) na nagrobnikih — vožnjah prejšnjih uvozov brez `sched` — ker ima LPP za vsak datum svoj `trip_id`. Srednji del id-ja (`dan|vožnja|vzorec`) se ponovi 22-krat v 31 dneh in preživi nov zip. S ključem brez dneva ima LPP 12 dni zgodovine namesto 2; v senci 0 % napovedi LPP z vsaj tremi dnevi.

**Tri merila**, vsa z učenjem **samo na preteklih dneh** (ne izpuščanje enega):

| merilo | kaj | nalog |
|---|---|---|
| senca, ponovljena | kar je prikaz posnel v živo; trenutna in prevoznikova vrednost takratni | 217 784 (8.–18. 9.) |
| rekonstrukcija iz `obs` | vse vožnje 15 min pred postankom; kaj je feed vedel ob T, pravilo `_LAST_MEASURED_SQL` | 2,3 mio, od tega 40,5 % pred odhodom |
| simulacija iz `run` | isto iz končnih vrednosti — **pušča** pri „še ni odpeljal“, rabljena samo za vozilo na poti | 3,0 mio |

Ponovitev sence z modelom v pandas se s tem, kar je strežnik zapisal, ujema na dve decimalki (2,97 proti 2,97); nova koda skozi pravi `stats.predict` in pandas različica se ujemata v 99,4 % vrstic (18. 9.).

**Meja ostanka** (simulacija, vozilo na poti, 1,16 mio nalog, 8.–18. 9.):

| meja velja, ko je dni manj kot | MAE | v 5 min | Arriva |
|---|---|---|---|
| vedno (prej) | 3,44 | 89,4 % | 4,61 |
| 2 / **3** / 4 | 3,12 | 89,7 % | 3,73 |
| 7 | 3,21 | | |

**Prevoznik navzgor, delež presežka** (senca, MAE po prevozniku, 6.–13. / 14.–18. 9.):

| | 0 | 0,25 | **0,5** | 0,75 | 1 (prej) |
|---|---|---|---|---|---|
| 1118 | 2,60 / 2,17 | 2,54 / 2,08 | **2,53 / 2,05** | 2,58 / 2,07 | 2,66 / 2,13 |
| Nomago | 2,56 / 2,46 | 2,43 / 2,35 | **2,40 / 2,32** | 2,44 / 2,35 | 2,55 / 2,45 |
| AP MS | 2,54 / 2,45 | 2,42 / 2,36 | **2,37 / 2,34** | 2,38 / 2,37 | 2,44 / 2,44 |
| Arriva | 4,27 / 3,42 | 4,13 / 3,24 | **4,07** / 3,15 | 4,08 / **3,11** | 4,16 / 3,14 |
| mestni LPP | 2,39 / 1,90 | 2,28 / 1,82 | 2,19 / 1,78 | 2,14 / **1,76** | **2,12** / 1,79 |

Pred odhodom (rekonstrukcija iz `obs`) je razlika pri LPP večja: 1 → 8,77 in 2,07 min, 0,5 → 9,81 in 2,17. Pri primestnem 1118 tam najboljše 0.

**Vožnja brez meritve** (rekonstrukcija, 605 334 pogledov, ko ima prevoznik vrednost):

| | delež | prevoznik | običajno | običajno + presežek |
|---|---|---|---|---|
| prevoznik ≤ običajno | 69 % | 3,98 | **2,67** | 2,67 |
| prevoznik > običajno | 15 % | 4,78 | 4,67 | **4,40** |
| brez 3 dni zgodovine | 16 % | **2,83** | (vozni red 3,25) | |

72,9 % prevoznikovih vrednosti pred odhodom je natanko 0 (LPP 88 %, IJPP 41–67 %).

**Dnevni sunki so v repu, ne v sredini.** Odklon od lastne mediane vožnje, povprečje po dnevu: 11. 9. (petek, rahel dež) LPP +9,8 min, Arriva +7,3, Nomago +2,1; mediana istih odklonov 0,5 / 0,3 / 0,05. 10. 9. deževalo v 97 % ur (4,4 mm/h povprečno), LPP +2,0. Petek povprečno najslabši dan (Arriva +3,0, LPP +4,5 min nad mediano vožnje), popoldne 14–18 h najslabši del dneva (LPP do +4,3). Napovedi to ne premakne, ker je mediana okoli nič — glej `.claude/rules/model.md`.

**Cena na arwenu** (po objavi, 19. 9.): odhodna tabla Bavarski dvor, 135 odhodov, **590 ms**, od tega „običajno“ 100 ms na klic (prej 15–18 ms) — dodatnih 920 vrstic zgodovine za 112 mestnih odhodov, ki je prej niso imeli. Tabla ga kliče dvakrat (še za včerajšnji prometni dan). Glavna poizvedba table ~340 ms, nova koda je ne spremeni. Obhod sence v konici: 0,34 s lokalno.

**Prezgodnji odhod z izhodišča** (senca, 8.–18. 9.). Ko je zadnji izmerjeni postanek izhodišče vožnje (11,7 % pogledov; LPP nikoli, AP MS 21 %) in je vozilo tam prezgodnje, je resnica na cilju v mediani −0,02 min, naša napoved pa je nosila −4,6 min naprej:

| izrez | n | prej | izhodišče ≥ 0 |
|---|---|---|---|
| izhodišče, prezgodaj | 7 799 | 6,24 · 65,8 % | **2,75 · 90,5 %** |
| izhodišče, vse | 27 462 | 4,11 · 83,2 % | **3,10 · 90,4 %** |
| vse | 217 784 | 2,62 · 91,5 % | **2,49 · 92,4 %** |

Na drugih postankih je pri prezgodnjem vozilu (≤ −3 min) sedanji model najboljši: 3,06 proti 3,49 za „običajno“ in 4,23 za odrez na nič.

**Končni model na senci po prevoznikih** (14.–18. 9., prej → zdaj): 1118 2,20 → 1,87 · Nomago 2,46 → 2,17 · AP MS 2,56 → 2,24 · Arriva 3,42 → 2,86 · mestni LPP 1,84 → 1,79 min. Backtest (8 dni): 2,13 → 2,12 min, v 5 min 94,9 → 95,1 %.

**Gradientni strop** (LightGBM, cilj L1, učenje 6.–13., test 14.–18. 9.): senca 2,43 → 2,20 min, strošek 6,38 → **6,50**; simulacija na poti 2,68 → 2,42. Pred odhodom 2,89 → 2,87 (brez LPP nič). Najpomembnejše: odklon od običajnega na izhodišču (19,6 % dobička), prevoznikov presežek (14,1 %), naša ocena, ura. Dež 1,7–2,3 %, dan v tednu 1,1–2,9 %.

## Razdalje med postajami

`stop_times.txt` nima `shape_dist_traveled`. Postaje projiciramo na polilinijo iz `shapes.txt`; razlika kumulativnih razdalj = dolžina odseka, mediana čez vse vlake.

**4. 9. 2026:** 271 postaj, 389 odsekov (268 elementarnih), **1140,8 km** elementarne mreže. Slovensko železniško omrežje ~1209 km, del brez potniškega prometa — pravi red velikosti.

**Prej: 267 postaj, 275 elementarnih, 1253,8 km.** Številka se z regeneracijo voznega reda premakne; nova je resničnosti bližja od stare. Kdor jo navaja, naj pomeri znova; kdor primerja s prejšnjo, naj ve: spremenil se je vozni red, ne mreža.

`elementary = 0` = "preskoki" hitrih vlakov čez vmesne postaje: za risanje mreže filtriraj `elementary = 1`, za hitrosti uporabi odsek, ki ustreza dejanskemu paru zaporednih postankov danega vlaka.

**Niso uradne km-lege**, ampak dolžine GTFS shapeov — odstopanje ~2–4 % (Zidani Most–Ljubljana 63,63 km proti uradnim ~61 km).

## Poraba

| | |
|---|---|
| Uvoz GTFS | 23 s, vrh 54 MB (pretočno branje `shapes.txt`; prej 269 MB) |
| Strežnik ob zagonu | 57–60 MB RSS |
| Po prvem zajemu | 74 MB RSS |
| Osvežitev v istem procesu | vrh 89 MB, ostane 85 MB → zato `KAJROS_REFRESH=off` privzeto |

## Hitrost pri velikih podatkih

Izmerjeno na **sintetični bazi z letom zajema vseh prevoznikov**: 52 122 000 vrstic `run`, 365 dni, 5,9 GB (generator v scratchpadu, ne v repozitoriju). Do tega stanja bo baza prišla sama; pri devetih dneh je vse hitro in nič ne pove.

| pot | čas |
|---|---|
| vstopna stran (`/api/overview`) | 29 ms |
| zemljevid, obe omrežji (`/api/live`) | 460 ms |
| živi seznam, samo železnica | 20 ms |
| odhodna tabla | 93 ms |
| prestopi | 46 ms |
| načrt poti do treh prestopov | 2 ms |
| iskanje postaj (avtobusi) | 145 ms |
| statistika, razrez 90 dni | 0,1 ms (dnevni povzetek) |

Trije vzorci, ki so bili vsak po enkrat vzrok počasnosti; v novi kodi se ne smejo ponoviti:

1. **Filtriraj znotraj poizvedbe, ne za njo.** Okenska funkcija čez oba omrežja, filter `t.network` šele za njo: železniško vprašanje (700 000 vrstic) plača avtobusne (12 M). Dvakrat — v `_LIVE_SQL` in `stats.breakdowns` (38 s).
2. **Koreliran `EXISTS` teče enkrat na vrstico.** Isti pogoji kot nekorelirana podpoizvedba: 392 ms → 65 ms.
3. **Ponavljajoče se opravilo naslednji čas računa od tika, ne od „zdaj".** Zanka zajema tikala na 10 s, `next_positions` pa se je nastavljal na `time.monotonic() + 10` **po** opravljenem delu -- vedno drobec pozneje od naslednjega tika, ki ga je zato zgrešil in preskočil cel obhod. Izmerjeno: lege brane v razmikih **19, 11, 19, 11 s namesto 10**, mediana 15 s. Zanka zdaj spi do prvega naslednjega opravila (`min(next_*) - now`), ne fiksen tik; razmiki 10, 11, 10, 10, 10.
4. **Preveri `EXPLAIN QUERY PLAN`, preden verjameš, da je indeks.** `SCAN t USING INDEX trip_train_no` **ni** iskanje po indeksu, ampak pregled cele tabele po napačnem — manjkal je `trip(route_id)`.

## Stanje zajema

## Stanje zajema

Lokalna baza `data/kajros.sqlite` (2026-09-01): 251 031 meritev, 1 838 411 vrstic dnevnika, 12 obratovalnih dni, 64 272 vremenskih vrstic, 9 791 postaj, 478 obvestil, 233 MB. Merodajen je zajem na malini; lokalna kopija = posnetek, za njim zaostaja.

**Malina zajema samo železnico.** V `kajros-zajem.service` je `KAJROS_AGENCIES=` prazen → uvoz vzame le SŽ, `trip` ima 789 voženj. Storitev = **`kajros-zajem`**, ne `kajros` — ta obstaja, a je `inactive`; kdor preverja napačno ime, sklepa, da zajem stoji.

Posledica, vidna šele ob prilitju: malina je 29.–31. 8. nekaj avtobusov posnela (takrat imela njihove vožnje uvožene), nato jih je uvoz brez `KAJROS_AGENCIES` odstranil iz `trip` in **43 362 meritev je ostalo sirot** — vrstic v `run` brez vožnje, tam neberljivih. Lokalna baza te vožnje ima, zato jih je `kajros merge` rešil (sirot 0). Prilitje je dodalo 217 545 vrstic dnevnika in 31. 8. dvignilo železnico s 4 645 na 6 912 meritev; `kajros repair` je nato popravil 1 511 vrstic, ki niso šle skozi novejše varovalke (malina teče starejšo kodo).

## Prvi šolski dan (1. 9. 2026)

Izmerjeno na jutru do 9:00, primerjano z istim oknom prejšnjih dni — sicer bi primerjal pol dneva s celim.

**Šolski vozni red = avtobusni dogodek, ne železniški.** Razpisanih voženj 31. 8. → 1. 9.: železnica **638 → 655** (+2,7 %), avtobusi **6 812 → 9 880** (**+45 %**). Od 9 880 avtobusnih jih 8 167 prejšnji dan sploh ni bilo.

**Železnica prvega šolskega dne ni bila slabša — celo malenkost boljša.** Jutro do 9:00, mediana zamude in delež do 5 minut:

| dan | meritev | mediana | do 5 min | p90 |
|---|---|---|---|---|
| 24. 8. pon | 1 988 | 2,0 min | 66 % | 13 min |
| 25. 8. tor | 1 990 | 2,0 min | 73 % | 11 min |
| 26. 8. sre | 1 989 | 2,0 min | 68 % | 13 min |
| 28. 8. pet | 1 948 | 1,0 min | 78 % | 10 min |
| 31. 8. pon | 1 913 | 1,0 min | 76 % | 12 min |
| **1. 9. tor (šola)** | **2 012** | **2,0 min** | **75 %** | **11 min** |

Tudi **40 vlakov, ki 31. 8. niso vozili** (šolski), se ne loči: mediana 2,0 min, 69 % do petih minut proti 75 % pri ostalih, na 97 meritvah — premalo za razliko. Najhujši tega jutra: običajni osumljenci na dolgih relacijah (IC 503 Hodoš–Koper mediana +20 min, LPV 2803 Maribor–Dobova +18, RG 318 +18), ne šolski vlaki.

**Zadrževanje na postajah se pri železnici ni spremenilo** — mediana razlike med odhodno in prihodno zamudo 0 s, nad 60 s 0 % postankov, enako kot prejšnje dni. Odpade skrb, da bi šolska gneča podrla `MIN_DWELL_S`; pri avtobusih mediana 5 s, 5 % postankov nad minuto, a 31. 8. je za primerjavo le 911 postankov proti 51 344 današnjim, zato to **ni** primerjava.

**Avtobusov ni s čim primerjati in to je odgovor.** Jutranji zajem avtobusov pred 1. 9. praktično ne obstaja (31. 8. do 9:00 le 1 142 meritev, polne zmrznjenih vrednosti). Današnje jutro = prva izmerjena avtobusna konica, postane izhodišče: Nomago mediana 2,0 min, 79 % do petih minut; Arriva 2,1 min, 76 %; LPP 2,0 min, 76 %; AP MS 1,6 min, 87 %.

**Resnično boleča ni zamuda, ampak izguba zgodovine.** Model se uči po `trip_id`, šolski vozni red pa je prinesel 8 167 novih voženj → danes zgodovino ima **le 11 % avtobusnih voženj** (1 133 od 9 880) proti **87 % železniških** (568 od 655). Napoved in „običajna zamuda" sta pri avtobusih od 1. 9. slepi in se bosta polnili znova; pri železnici se ni zgodilo nič. `trip_id` so ostali stabilni (0 sirot v `run`) — nove vožnje so res nove storitve, ne preimenovane stare.

## Senčno merjenje: kaj je potnik res videl (2. 9. 2026)

Prvi izid `kajros ocena` — 7 776 razrešenih napovedi v treh dneh (1 008 železniških, 6 768 avtobusnih), posnetih 25 minut pred vlakom in 15 pred avtobusom.

**Parna primerjava** (samo vrstice, kjer imajo vrednost vsi trije; prevoznik je sicer meril na lažjem vzorcu, videti boljši, kot je — 6 598 vrstic):

| model | MAE | v 5 min | podcenjenih | odklon |
|---|---|---|---|---|
| **naša ocena** | **3,28 min** | **86,6 %** | **5,2 %** | +1,04 min |
| naša brez pravila „prevoznik ve več“ | 3,59 | 85,8 % | 9,1 % | −0,61 |
| prevoznik | 3,39 | 82,4 % | 13,5 % | −1,26 |
| prenos zamude | 3,44 | 80,8 % | 14,8 % | −1,37 |

Štiri ugotovitve:

* **Naša ocena premaga oboje — prevoznika in prenos — po vseh merilih.** Prva različica poročila je trdila nasprotno (prevoznik MAE 3,39 proti našim 3,63), ker vsak model meri na svojem vzorcu. Past, pred katero svari `ocena.py`; izogibati se je treba tudi pri branju.
* **Pravilo „prevoznik ve več“ se izplača.** Sproži se v 41 % primerov (skoraj samo avtobusi); tam MAE 2,65 proti 3,31 brez njega, delež v 5 min 88,6 proti 87,0.
* **Vsi razen nas podcenjujejo.** Odklon prenosa −1,37 min, prevoznika −1,26; naš +1,04 = rahlo pesimistična.

  **Popravek 3. 9. 2026:** prej pisalo, da je to „varna smer“. Ni. Pozitiven odklon = vozilo napovemo **poznejše, kot je**, potnik pride pozneje in mu odpelje pred nosom. Varna smer je negativna. Glej „Smer napake“ spodaj.
* **Pri železnici prevoznik v potnikovem oknu praktično molči** — vrednost za ciljni postanek v **4 od 1 008** primerov (0,4 %). Pri avtobusih molčal v 2,6 %. Za vlake smo edini vir odgovora: 3,52 min proti 4,50 pri prenosu (78,5 proti 72,4 % v 5 min).

**Številka, ki jo potnik vidi, je dvakrat slabša od backtesta** (1,92 min in 91 %). Ni napaka merjenja, ampak drugo vprašanje: v potnikovem oknu je cilj mediano **6 postankov naprej pri železnici in 8 pri avtobusu** (p90 9 oziroma 13), backtest poln kratkih skokov. Zastarelost ni kriva — „trenutna zamuda“ ob pogledu stara 2,7 min (železnica) oziroma 1,2 min (avtobus).

**Popravljeno 2. 9.** — glej `.claude/rules/model.md`, „Meja ostanka“: model ostanku ne verjame več kot `max(10 min, trenutna zamuda)`. Naloge sence 3,63 → 3,18 min, pri 9–10 postankih 4,24 → 2,95; avtobusni backtest 4,14 → 3,41 min. Spodnji odstavek opisuje stanje pred popravkom.

**Kje izboljšati, konkretno:** pri **9–10 postankih naprej** naš model izgubi proti golemu prenosu (MAE 4,62 proti 3,59; brez pravila prevoznika 5,36). Odklon tam +2,13 min povprečno, a le +0,72 mediano — ni sistematično precenjevanje, ampak **rep**: manjšina primerov, kjer napovemo veliko zamudo, ki se ne zgodi. Najhuje pri avtobusih (+2,22) in ko je vozilo ob pogledu skoraj točno (odklon +3,89 min pri zamudi pod 2 min). Pri drugih razdaljah (4–8 in 11+) model prenos prepričljivo premaga.

## Neverjetne zamude pri avtobusih (3. 9. 2026)

Domača stran ob 00:20 kazala **„avtobusi +833 min“**. Vzrok dvojen.

**Prvi vzrok — manjkajoča varovalka, popravljeno.** `MIN_RUNS_FOR_DAY = 20` uporabljen samo v `/api/overview` (železnica), ne v `/api/overview/bus`. Avtobusni pregled ob 00:20 zato računal mediano iz **šestih** voženj. `home.js` je `yesterday` že bral — samo poslali ga nismo.

**Drugi vzrok — vrednosti, ki niso zamude.** V bazi **2 541 avtobusnih vrstic z zamudo nad 4 h**, največ **16,3 h**. Primer: N0556 (Nomago), vozni red 05:50, „zamuda“ 58 800 s na vseh postankih.

Porazdelitev: to ni rep prave porazdelitve:

| nad | železnica (68 156 vrstic) | avtobusi (489 244) |
|---|---|---|
| 30 min | 1 443 (2,1 %) | 18 018 (3,7 %) |
| 60 min | 257 (0,38 %) | 7 255 (1,48 %) |
| 90 min | 74 (0,11 %) | 4 214 (0,86 %) |
| 120 min | 7 (0,01 %) | 3 464 (0,71 %) |
| 180 min | **0** | 2 735 (0,56 %) |
| 240 min | 0 | 2 541 (0,52 %) |
| 480 min | 0 | 1 588 (0,33 %) |
| 720 min | 0 | 137 (0,03 %) |

**Železnica: nobene vrstice nad 3 h v 68 tisoč meritvah.** Pri avtobusih padanje med 120 in 240 minutami skoraj zastane (3 464 → 2 541, razmerje 0,73 na dvakratni razdalji) = oblika **drugega procesa**, ne repa zamud.

**Kar ni dokaz, in zakaj to piše.** Preizkušena domneva: prevoznikova napaka ujemanja — vozilo, ki vozi zdaj, pripeto voznemu redu izpred ur. Podpis „vozni red + zamuda ≈ čas branja feeda“ pri vrsticah nad 4 h v 75,4 %. **Kontrola ga podrla:** pri običajnih zamudah 0–5 min isti podpis v 72,3 %. Pri prvem postanku je „vozni red + zamuda = zdaj“ ravno to, kar živi feed je. Domneva verjetna, ni dokazana.

**Odprto: kje je meja.** Rez pri 3 h bi vrgel 2 735 avtobusnih vrstic (0,56 %), pri 2 h 3 464 (0,71 %). Meja ni izmerjena, ampak sklepana → zajema **nisem** spreminjal — podatki se ne brišejo na domnevo. Odločitev čaka.

## Model ločeno po omrežjih (3. 9. 2026)

Senca: 11 787 razrešenih napovedi, od tega **2 001 železniških** — prvič dovolj za merjenje modela posebej na vlakih.

**Železnica** (2 001 vrstic, posneto 25 min pred vlakom):

| model | MAE | v 2 min | v 5 min | podcenjenih | odklon |
|---|---|---|---|---|---|
| **naša ocena** | **3,56 min** | **64,1 %** | **82,0 %** | 13,2 % | **−1,71** |
| prenos zamude | 4,40 | 54,8 % | 75,5 % | 21,9 % | −3,40 |
| prevoznik | 3,73 | 73,3 % | 73,3 % | 26,7 % | −3,60 |

**Prevoznik pri vlakih molči v 99,3 %** (vrednost v 15 od 2 001 primerov) → njegova vrstica = anekdota, ne meritev. Proti prenosu zamude boljši po vseh merilih: MAE 3,56 proti 4,40, 82,0 % proti 75,5 % v 5 min.

**Novo, v skupni številki nevidno: predznak odklona se med omrežjema obrne.**

| | odklon | pomen |
|---|---|---|
| železnica | **−1,71 min** | napovemo **manj** zamude, kot je je |
| avtobusi | **+0,83 min** | napovemo **več** zamude, kot je je |
| skupaj | +0,40 min | povprečje, ki obeh ne opiše |

Verjetna razlaga, **ni preverjena**: meja ostanka (`max(10 min, trenutna zamuda)`, uvedena 2. 9.) pri vlakih veže, ker zamuda na dolgih relacijah raste naprej; pri avtobusih ne, ker se na kratkih relacijah pobere. Preveri: meriti delež primerov, kjer meja res odreže.

**Odprto: katero smer napake hočemo.** Za *ujeti* vlak varno podcenjevati — kdor pride prezgodaj, čaka; kdor prepozno, vlak zamudi. Za *načrtovanje prestopa* varno ravno obratno. Model ne more imeti prav v obe smeri hkrati → odločitev o rabi, ne popravek. Do nje se model ne spreminja. Zapis, da je pozitiven odklon „varna smer“, je bil zato prehiter.

## Strop zamude za statistiko (3. 9. 2026)

Lestvica najbolj zamujajočih pri avtobusih neuporabna: prva vrstica N6223 z mediano **654 min na dveh vožnjah**. Vzrok: vrednosti, ki niso zamude, ampak feedova zamenjava prometnega dne — isti pojav, ki ga pri prikazu že lovi `api.MAX_LIVE_DELAY_S` (6 h).

Za statistiko nižja meja, **izmerjena, ne izbrana** — `stats.MAX_REALNA_ZAMUDA_S = 3 h`:

| | vrstic | odpade | mediana | povprečje | p99 |
|---|---|---|---|---|---|
| železnica | 69 803 | **0 (0,00 %)** | 2,00 → 2,00 | 6,25 → 6,25 | 39,0 → 39,0 |
| avtobusi | 537 253 | 2 614 (0,49 %) | 2,18 → 2,15 | **7,25 → 4,86** | 73,4 → 59,0 |

Dvoje potrjeno. Prvič: **iz železnice strop ne vzame ničesar** → ne reže pravih zamud; železnica = omrežje z največ zaupanja. Drugič: pri avtobusih se mediana komaj premakne, **povprečje pade za tretjino**. Robustna mera stabilna, občutljiva sesuta = podpis izstopajočih vrednosti, ne repa prave porazdelitve.

Podatki se **ne brišejo**; filter branja, zajem hrani vse. Lestvica ima še spodnjo mejo vzorca (`MIN_RUNS_FOR_RANK = 5`): vožnja z dvema zajemoma na vrhu ni najslabši vlak, ampak najmanjši vzorec.

Po popravku najslabša avtobusna vožnja A5117 s **64 min na petih vožnjah** namesto 654 min na dveh; železniška lestvica nespremenjena (EC 211, 46 min, 12 voženj, 8 % točnih).


## Smer napake: kaj stane potnika (3. 9. 2026)

Vprašanje: naj model raje podcenjuje ali precenjuje zamudo? Odgovor odvisen od nove številke: **koliko stane zamujeno vozilo.**

**Razmik do naslednjega odhoda z iste postaje v isto smer** (po `headsign`, 06–20, zajeti vozni red):

| | razmikov | mediana | p25 | p75 | p90 | nad uro |
|---|---|---|---|---|---|---|
| železnica | 5 205 | **87 min** | 55 | 153 | 260 | 66 % |
| avtobusi | 194 231 | **40 min** | 15 | 70 | 139 | 28 % |

Zamujen vlak stane mediano 87 min; odvečno čakanje = toliko minut, kolikor smo podcenili. Razmerje 20 : 1 do 90 : 1 — asimetrija ni majhna.

**Kje smo zdaj** (senca, delež primerov, kjer smo napovedali *več* zamude, kot je bila — smer, ki vozilo zamudi):

| | > 0 | > 1 min | > 2 min | > 5 min | odklon | n |
|---|---|---|---|---|---|---|
| železnica | 32,1 % | 17,7 % | 11,1 % | 4,5 % | **−0,94 min** | 5 771 |
| avtobusi | **64,0 %** | 46,8 % | **30,9 %** | 6,9 % | **+0,42 min** | 29 642 |

**Prag odloči, katero zgodbo tabela pove**, zato razpisan v štirih stolpcih. Poročilo `kajros ocena` je do 3. 9. 2026 kazalo precenitve pri pragu 0 in podcenitve pri pragu 5 min, eno poleg drugega: 58,8 % proti 6,3 %, zvenelo kot sistematično precenjevanje. Pri istem pragu 6,5 % proti 6,4 %. Odtlej oba stolpca merita pri potnikovi rezervi (5 min).

**Očiten sklep, a ni pravi.** Vsako oceno zamaknemo navzdol za `k` minut, stroške seštejemo (podcenitev = čakanje, precenitev = razmik do naslednjega): povprečen strošek pade s 27,9 na 10,1 min pri železnici, z 26,9 na 7,8 pri avtobusih — najbolje pri `k = 5`. MAE zraste z 2,93 na 6,65 oziroma s 3,36 na 5,53.

**Zakaj tega ne naredimo.** Model predpostavlja, da potnik pride natanko ob napovedani minuti. Ne pride — pride z rezervo. Rezerva in zamik sta **zamenljiva**:

| potnikova rezerva | najboljši `k`, železnica | najboljši `k`, avtobusi |
|---|---|---|
| 0 min | 5 (strošek 10,1) | 5 (7,8) |
| 2 min | 3 (10,1) | 3 (7,8) |
| **5 min** | **0 (10,1)** | **0 (7,8)** |
| 10 min | 0 (12,3) | 0 (10,6) |

Strošek pri prvih treh vrsticah **enak**: šteje samo vsota `k + B`, optimum okoli **5 minut skupaj**. Potnik jih prispeva sam. Če dodamo še mi, skupna rezerva 10 in strošek **zraste** (12,3 proti 10,1).

**Sklep:**

1. **Številke ne zamikamo.** Prikazana vrednost ostane najboljša ocena; zamik bi podvojil rezervo, ki jo potnik že ima, in pokvaril MAE za nič.
2. **Nikoli sistematično pesimistični.** Pozitiven odklon poje potnikovo lastno rezervo brez njegovega védenja. Avtobusi pri **+0,47 min in 63,6 % precenitev** — edino, kar je treba popraviti; cilj odklon ≈ 0, ne negativen.
3. **Železnica pri −1,27 v redu.** Pri 87-minutnem razmiku rahla previdnost = poceni zavarovanje.
4. **Za pomoč pomagaj naravnost, ne z lažjo v številki:** ob „pričakovano 15:47“ sodi „bodi na peronu do 15:45“. Nasvet ločen od meritve — številka naj pomeni, kar piše.

**Meje izračuna.** Predpostavlja, da zamujeno vozilo = čakanje celega razmika (v resnici obstajajo obvozi in druge relacije) in da potnik cilja natanko na prikazano minuto. Absolutni strošek zato precenjen; **razmerje** med možnostmi in ugotovitev, da sta `k` in rezerva zamenljiva, sta na predpostavki neobčutljiva.

## Aplikacija za Android: velikost in čistost (12. 9. 2026)

**APK.** Ovoj z WebView, brez AndroidX, brez Googlovega; edina knjižnica v paketu = Kotlinova standardna.

| različica | velikost | zakaj toliko |
|---|---|---|
| izdajna (R8) | **60 942 B** (~60 kB) | naša koda + kar od Kotlina res rabi |
| razvojna | 937 170 B (~915 kB) | brez R8; Kotlinova standardna knjižnica cela |

Rast po rezinah, izmerjeno na izdajni različici: **28 kB** gol ovoj (6. 9.) → **50 kB** z budilko, seznamom, mostom (7. 9.) → **60 kB** s ponavljajočimi budilkami, widgetom, bogatejšim seznamom (12. 9.). Devet kilobajtov za ponavljanje in widget = cena `java.time` v `Ponovitev.kt` in `RemoteViews` v widgetu — nobene nove odvisnosti.

Preverjeno v paketu 12. 9. 2026: `aapt2 dump strings` najde **0** nizov z `com/google`, `gms`, `firebase` ali `androidx`. `minSdk` 26, `targetSdk` 35.

**17. 9. 2026: widget po smernicah stane 1 472 B.** Podpisani izdajni APK 79 394 → **80 866 B**; vsebuje predogledno postavitev za izbirnik (`previewLayout`), sistemsko zaobljenost v `values-v31`, meji za stiskanje, opis za bralnik zaslona. Izmerjeno z gradnjo iz `git worktree` na HEAD, ne po oceni.

**Objavljena 17. 9. 2026 kot 1.2** (`versionCode` 3, 98 014 B, sha256 `71f8f5aa…`); prenos s `kajros.app/prenos/kajros-1.2.apk` preverjen z vsoto.

**Dva nova widgeta stanejo 17 148 B.** Izdajni APK 80 866 → **98 014 B** (~96 kB): odhodna tabla ene postaje s svojo nastavitveno dejavnostjo + seznam budilk s stikali. Večino nosi tabla — prenos, razčlenjevanje odgovora, shramba zadnjega stanja, zaslon za izbiro postaje; seznam budilk = samo izris tega, kar je že v telefonu. Nobene nove odvisnosti.

**Ritem table = 15 minut, a sistem ga sme raztegniti.** Izmerjeno na emulatorju (Android 15, `dumpsys alarm`):

```
tag=*alarm*:app.kajros.TABLA
type=ELAPSED origWhen=+13m46s repeatInterval=900000 window=+11m15s
whenElapsed=+13m46s maxWhenElapsed=+25m1s
```

`setInexactRepeating` ne obljublja 15 minut, ampak **od 15 do 25**; `ELAPSED` (brez `_WAKEUP`) = spečega telefona ne budi. Zato widget nosi uro podatka in od 30 minut naprej to pove z besedo — številka brez ure bi trdila svežino, ki je ritem ne more zagotoviti.

**Dovoljenj je enajst, ne štiri** — budilka jih je prinesla sedem: `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `USE_EXACT_ALARM`, `SCHEDULE_EXACT_ALARM` (do SDK 32), `POST_NOTIFICATIONS`, `USE_FULL_SCREEN_INTENT`, `WAKE_LOCK`, `VIBRATE`, `RECEIVE_BOOT_COMPLETED`. Za widget ni bilo treba nobenega.

**Orodja.** `~/kajros-android` = 2,4 GB brez emulatorja, 5,5 GB z njim. Nič sistemskega, nič sudota.

**Tri uhajanja zunaj mape**, ki jih je našla revizija, ne domneva:

| kaj | kdo | kaj to premakne |
|---|---|---|
| `~/.java/.userPrefs/google/prefs.xml` | JVM za sdkmanager | `-Djava.util.prefs.userRoot` |
| `~/.android/adbkey` | `adb` | samo drugačen `HOME` (ne `ANDROID_USER_HOME`) |
| `~/.android/analytics.settings` z obstojnim `userId` | AGP ob **vsaki** gradnji | samo `-Duser.home` |

Zadnjega najtežje ujeti: preizkušeno troje, dve nista delovali — `ANDROID_USER_HOME` sam pušča, `HOME=$KOREN/domov` prav tako (za razliko od adb), `ANDROID_PREFS_ROOT` AGP sesuje, ker zahteva eno samo spremenljivko. Telemetrija `sdkmanagerja` se izklopi z `--no-metrics`, a samo na novem `android` CLI — na `sdkmanager` je zastavica tiha, brez učinka (izmerjeno na številu datotek v `analytics/metrics/spool/`: brez nje 8 → 9, z njo ostane 9).

`android/zgradi.sh` isto revizijo ponovi ob vsaki gradnji in **pade**, če kaj uide — enkratna meritev tega razreda napake ne ujame.

## Rezerva budilke: koliko prej naj zazvoni (6. 9. 2026)

David: *„Uporabnik pa ne sme zamuditi, raje kej rezerve, če ni zihr."* Koliko rezerve = vprašanje s številko. Vir: senca (`napoved`, 63 843 razrešenih vrstic): `ours_s` = kar bi prikaz **takrat** povedal, `actual_s` = resnica. Napaka budilke = `ours_s − actual_s` — pozitivna = obljubili večjo zamudo, kot je bila, budilka bi zvonila **prepozno**.

**Brez rezerve budilka zvoni prepozno v 32 % primerov pri vlakih, 64 % pri avtobusih.** Mediana napake pri avtobusih +0,8 min, p95 +5,6.

Strošek po isti metodi kot „Smer napake" zgoraj: `P(zamudi) × razmik + odvečno čakanje`, razmik 87 min (železnica), 40 min (avtobusi).

| R [min] | železnica, zamudi | strošek | avtobusi, zamudi | strošek |
|---|---|---|---|---|
| 0 | 32,2 % | 30,13 | 63,6 % | 27,06 |
| 3 | 8,0 % | 11,48 | 17,4 % | 10,43 |
| 4 | 5,7 % | 10,40 | 10,4 % | 8,48 |
| **5** | **4,5 %** | **10,29** | **6,4 %** | **7,81** |
| 6 | 3,4 % | 10,33 | 4,3 % | 7,93 |
| 8 | 2,1 % | 11,10 | 2,3 % | 9,07 |

Optimum pri obeh omrežjih **R = 5 min**; krivulja med 4 in 6 ravna → izbira ni krhka. (Pri ohlapnejši definiciji zamude — „manjka več kot 2 min" — optimum 3; vzet strogi, ker ga je zahteval David.)

**Vlak v 10 775 meritvah ni odpeljal prezgodaj niti enkrat** (avtobus v 25,3 %, več kot 2 min prezgodaj v 8,8 %, p01 = −6,2 min). Sledi popravek, ki je zastonj:

| pravilo | železnica: zamudi / strošek | avtobusi: zamudi / strošek |
|---|---|---|
| `ours` | 32,2 % / 30,13 | 63,6 % / 27,06 |
| `ours − 5` | 4,5 % / 10,29 | **6,4 % / 7,81** |
| **`max(0, ours − 5)`** | **4,5 % / 8,32** | 28,9 % / 14,81 |

Pri vlakih **isti delež zamud, 2 minuti manj odvečnega čakanja**: budilka ne sme zvoniti pred voznim redom, ker vlak pred njim ne odpelje. Pri avtobusih ista omejitev delež zamud početveri — ti prezgodaj **gredo**.

**Brez povezave**, ko zamude ne poznamo, isti račun na golem `actual_s`:

| | najcenejši R | zakaj |
|---|---|---|
| železnica | **0** | vlak prezgodaj ne odpelje; vsaka rezerva = čisto čakanje |
| avtobusi | **3** | 25,3 % jih odpelje prej; strošek 14,92 → 9,50 |

**Kaj je s to meritvijo narejeno.** Rezerve aplikacija **ne dodaja sama** (odločeno 6. 9. 2026): `zvoni = voznoredna + zamuda − X`, rezervo določi potnik z izbiro X. Meritev zato zapisana v vmesniku, kjer X izbira — da ve, kaj kupuje z vsako minuto. Številke veljajo naprej, podlaga za ločeno možnost „+3 min", ko bo vmesnik prenovljen.

Namesto pavšalne rezerve izpad povezave pokriva svoje pravilo: zadnjih 3,5 minute pred zvonjenjem brez odgovora = **takojšnje zvonjenje** z razlogom. Cena: do 3,5 minute spanca, samo ko povezave res ni.

**Česar meritev ne pove:** kako napaka raste s starostjo podatka. `ocena.py` snema pri stalnem horizontu (25 min vlaki, 15 avtobusi), zato v `napoved` razpona ni. Zastarel podatek zato ni obravnavan kot slabša napoved, ampak kot **odsotnost** povezave — konservativno, kot naročeno.

## Kaj LPP v IJPP sploh je (6. 9. 2026)

Prijava: „odhodi iz postaje Polje najdejo samo LPP 25, čeprav so tam vsaj trije busi". Preverjeno v bazi — **prikaz pravilen, feed nepopoln.**

Postajališči z imenom `Polje` (`1167324`, `1167325`, Ljubljana) strežeta v celotnem voznem redu **samo liniji 25** (199 postankov). Nedelja 6. 9.: 31 odhodov, ponedeljek 7. 9.: 80 — vsi linija 25.

**Linij 20 in 22 v podatkih sploh ni**, pri nobeni agenciji. Znotraj 1,2 km od Polja edina druga stvar = železniška postaja Ljubljana Polje.

| agencija | linij | voženj |
|---|---|---|
| 1123 (AP MS) | 486 | 8 981 |
| 1119 (Nomago) | 922 | 6 941 |
| 1118 (**LPP**) | **37** | 3 174 |
| 1121 (Arriva) | 115 | 965 |

LPP jih ima 37: `12D, 15, 19I, 21D, 25, 30, 3B, 3G, 40, 42, 44, 45, 46, 461, 47, 48, 48P, 49, 50, 51, 52, 53, 54, 56, 60, 68, 69, 6B, 71, 72, 73, 74, 76, 78, 80, 82, 84`. Mestnih linij 1, 2, 5, 6, 7, 9, 11, 13, 14, 18, 20, 22, 27 ni. Prisotne večinoma primestne (40+) in nekaj mestnih.

Vrzel pri viru, ne pri nas; iz drugega odprtega vira je ni mogoče zapolniti. Vredno vprašanja DUJPP, ko bo tekla korespondenca.

## Mestni LPP je dosegljiv, a po drugi poti (7. 9. 2026)

Mestnih linij LPP v IJPP ni. Odprt vir **obstaja**: isti `derp.si` kot za IJPP, drug vir. Potrjeno iz konfiguracije projekta transitous (`feeds/si.json`, vnos `name: lpp`), ne uganjeno.

| vir | dostop | vsebina |
|---|---|---|
| `avl.lpp.si/transit/api/gtfs` | odprt, 42 MB | statični GTFS, agencija `lpp`, **31 prog — ravno mestne in nočne** |
| `rt.gtfs.derp.si/sources/lpp/all` | **odprt, brez ključa** | 600 entitet: 280 trip_updates, **139 leg vozil**, 181 obvestil |
| `data.lpp.si/api/bus/buses-on-route` | **401** | lege — zaklenjeno, a jih ima derp.si |
| `data.lpp.si` ostalo | odprt | 117 oznak linij, 1 459 postajališč, `eta_min` |

Feeda **komplementarna**: IJPP nosi primestne LPP linije (40–84), `avl.lpp.si` mestne (01–28, N1, N3, N5).

**Past: `delay` v tem feedu vedno 0.** Izmerjeno dvakrat — nedelja 22:00 (2 721 postankov), ponedeljkova konica 07:11 (2 604 postankov): **nobena zamuda neničelna**, `trip_update.delay` ni izpolnjen pri nobeni vožnji. Kdor bere `delay`, zapiše, da mestni LPP nikoli ne zamuja.

**Zamuda vseeno je, v drugi obliki.** 1 882 od 4 517 postankov nosi **absolutni napovedani čas**. Točno primer, ki ga `collector._delay_of()` že pokriva (`m.time − (polnoč + t_s)`). Preverjeno na šestih postankih ob 07:11 proti uradnemu voznemu redu:

| vozni red | napoved | zamuda |
|---|---|---|
| 07:07 | 07:10:13 | **+3,2 min** |
| 07:13 | 07:11:50 | **−1,2 min** |
| 07:12 | 07:13:02 | +1,0 min |
| 07:10 | 07:13:14 | +3,2 min |
| 07:15 | 07:16:25 | +1,4 min |

**`trip_id` se ujemata 1 : 1.** RT uporablja isto trojno obliko UUID (`service|?|trip`) kot uradni `trips.txt`; vsak preverjeni RT `trip_id` v voznem redu natanko enkrat. Združevanje z `avl.lpp.si`, **ne** z NAP.

Lege vozil: 139, starost mediana 146 s (IJPP 10 s). Za zemljevid dovolj, za oceno hitrosti manj natančno.

**Odprto: licenca.** Za `avl.lpp.si` in `data.lpp.si` ni navedene. Odprt dostop ≠ dovoljenje za objavo. Vsi podatki v kajrosu zdaj CC BY-SA 4.0 z obvezno navedbo vira; preden mestni LPP gre na zaslon, mora biti jasno, pod čim. Vprašanje za LPP in DUJPP v istem krogu pisem.

## Uvoz mestnega LPP: kaj to prinese in kaj stane (7. 9. 2026)

Uvoz zgrajen in preizkušen na kopiji baze. Vklop `KAJROS_LPP=1`, privzeto izklopljen.

**Kaj prinese.** Postajališče „Polje", zaradi katerega se je vse začelo:

| | linij | odhodov danes |
|---|---|---|
| prej (samo IJPP) | 1 (linija 25) | 80 |
| zdaj | **5** (27, 11, 25, 24, 11B) | **365** |

V bazo pride 31 mestnih in nočnih linij: 1, 1B, 2, 3, 5, 6, 7, 8, 9, 10, 11, 11B, 13, 14, 16, 18, 18L, 19B, 20, 20Z, 22, 23, 24, 26, 27, 28, N1, N3, N3B, N5 in SŽ.

**Kaj stane.** Uvoz obeh zipov traja **27 s**:

| | prej | z LPP |
|---|---|---|
| vožnje | 20 850 | 39 899 (+19 163) |
| postanki (`sched`) | 403 208 | 889 731 |
| postajališča | 9 791 | 10 509 |

**Okno nujno.** LPP nima voznih vzorcev, ima svojo vožnjo za vsak datum: 62 989 voženj in 1,6 milijona postankov za 31 dni. Uvažamo osem dni (`KAJROS_LPP_DAYS`) = zgornjih 19 163 voženj.

**Zamude kakovostnejše od avtobusov v IJPP.** En zajem ob 07:40: 4 157 postankov, **2 071 z neničelno zamudo** (49,8 %):

| p01 | p25 | mediana | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| −4 min | 0 | 0 | +1 | +7 | +23 | +69 |

Nad 30 min 27 vrstic (0,65 %), **vse ene same vožnje** (linija 1, 27 postankov, povprečno +66 min). **Nad 2 h ničesar** — IJPP-jev avtobusni feed je imel 2 541 vrstic nad 4 h. Vir bistveno čistejši, za zdaj brez svoje varovalke.

Leg vozil 145 (IJPP ~1 000), starost mediana 146 s.

**Obiti je bilo treba:** `delay` v feedu vedno 0. Zamuda iz absolutnih napovedanih časov prek `collector._delay_of()`.

**V produkciji od 7. 9. 2026, 08:16.** Prvi zajem na arwenu: „LPP: 240 voženj, 3 575 sprememb, 140 leg". Vozni red 38 070 voženj (od tega 19 163 LPP), 10 493 postajališč; vozil z GPS 1 235 namesto ~1 000. Bavarski dvor: 150 odhodov z živimi zamudami mestnih linij (18L +4 min izmerjeno, 6B +11 min ocena); Polje: 150 odhodov na petih linijah namesto 80 na eni.

## Kaj je LPP podrl in kaj je to stalo (7. 9. 2026)

Vklop mestnega LPP potrojil avtobusno omrežje in odkril tri napake, ki so bile v kodi že prej, le da jih železnica ni sprožila. Vse tri najdene s pregledom `preglej vse`, ne s prijavo uporabnika.

**1. `/api/live` se ni odzival — 216 s.** `EXPLAIN QUERY PLAN`: `SCAN p`, nato `SCAN tail`: CTE `tail` materializiran brez indeksa, zato za vsako vrstico `passed` pregledan cel. Železnica 2 006 × 2 006, avtobusi **59 557 × 59 557 = 3,5 milijarde** primerjav. `tail` = samo „zamuda na zadnjem postanku", kar je okenska funkcija.

| | prej | zdaj |
|---|---|---|
| avtobusi | 216,1 s | **4,3 s** (arwen), 0,14 s (razvojni) |
| železnica | 2,27 s | 0,66 s |

Izid pri železnici enak vrstico za vrstico.

**2. Iskanje zvez z enim prestopom — 26,5 s.** Poizvedba se razveji čez vse pare voženj, ki se kje srečata; na prometni mestni postaji izmerjeno 26,5 s od trenutne ure in 40,5 s za cel dan, pri vlakih 0,0 s.

Rešitev = merjena ločnica, ne pospešitev poizvedbe. Mediana razmika med zaporednimi neposrednimi odhodi:

| relacija | zvez | mediana razmika |
|---|---|---|
| Bavarski dvor → Polje (mestni) | 161 | **6 min** |
| Ljubljana AP → Maribor AP | 8 | 70 min |
| Ljubljana → Maribor (vlak) | 11 | 120 min |
| Ljubljana → Koper (vlak) | 3 | 520 min |

Med 6 in 70 minutami ničesar, zato meja **15 minut**: pri gostejšem taktu prestopa ne iščemo, ker ne more nič prihraniti. Izid: Bavarski dvor → Polje **26,5 s → 0,13 s**, vlaki nespremenjeni. Mestni par brez neposredne zveze (ZALOG → Štajerska) ostane 3,0 s in osem zvez.

**3. `plan()` tiho vračal nič.** `MAX_STOP_TIMES = 200 000` postavljen na domnevo „pri avtobusih 80 000"; z LPP jih **247 346**, zato `_timetable_for_day()` vračal prazen vozni red — nihče ni povedal. Meja zdaj izmerjena: cel avtobusni dan 92 MB zadržano, 127 MB vrh, naloži se v 1,6 s. Nova meja 300 000, predpomnilnik s štirih na dva vnosa (najhujši primer ~184 MB namesto 370). Prazen izid se odslej predpomni, da se četrt milijona vrstic ne bere znova ob vsakem klicu.

**Ostaja počasno, ni popravljeno:** `/api/stations/search` na arwenu ~4 s za vsako poizvedbo (lokalno 0,35 s). Brskalnika ne prizadene, ker odkar obstaja `/api/stations/index`, išče sam; endpoint še v rabi kot zasilna pot in pri prvih pritiskih tipk, preden se kazalo naloži.

## Isto postajališče pod dvema imenoma (7. 9. 2026)

LPP piše **12 % imen s samimi velikimi črkami** („ČRNUČE", 45 od 388), IJPP normalno. Ker v aplikaciji vse teče po **imenu** postaje, sta to dve različni postaji: iskalnik pokaže obe, odhodna tabla razdeli odhode, budilka si zapomni tisto, ki je nikjer drugje ni.

Imen, ki se razlikujejo samo po velikosti črk ali šumniku, **24**. Slepo združevanje bi bilo napačno — razdelitev po razdalji ostra:

| razdalja | parov | kaj so |
|---|---|---|
| 3–215 m | **14** | isto postajališče, dva zapisa |
| 0,8–111,6 km | **10** | različna kraja z istim imenom |

Med 215 m in 829 m ničesar. „Celje" in „Čelje" **112 km** narazen, „Lozice" in „Ložice" 43 km, „Rožna Dolina" in „Rožna dolina" 66 km — različne vasi, ni dovoljeno zliti.

Uvoz zato poenoti ime samo, kadar sta zapisa tudi **fizično na istem mestu** (`ISTO_POSTAJALISCE_M = 500`). Kanonično = ime, ki ni v samih velikih črkah; ob več takih odloči pogostost, nato abeceda, da je izid ponovljiv. Izid uvoza: `imen_poenotenih: 14`, preostalih dvojnic 10 — vse različni kraji.

## Vzdrževanje po vklopu LPP (7. 9. 2026)

Preverjeno, ker baza čez noč +40 %.

**Obrez deluje.** Politika: 90 dni železnica, 14 avtobusi (`OBS_KEEP_DAYS`). Avtobusnih vrstic pred 14-dnevno mejo: **0**; ostanejo le železniške iz avgusta, po nekaj tisoč na dan.

**Koliko doda LPP.** 08:16–12:15 zapisal **57 567 meritev** — cel obratovalni dan okoli 250 000, dosedanjih ~470 000. Baza z uvozom (statični vozni red) 605 → **845 MB**; ustaljeno pri 14-dnevnem oknu okoli 1,3–1,4 GB. Arwen: 33 GB prostega.

| dan | meritev | opomba |
|---|---|---|
| 2026-09-02 do 04 | ~1,31 M | delovni dnevi, brez LPP |
| 2026-09-05, 06 | 293 k, 240 k | vikend |
| 2026-09-07 do 12:15 | 529 k | ponedeljek, LPP od 08:16 |

**Dnevni povzetek hiter.** `refresh_summaries()` **3,1 s** (železnica 267 + 409 ms, avtobusi 470 + 1 902 ms). Opravilo ob 3:30 ni ogroženo.

**Storitev se ne sesuva.** `NRestarts = 0`, v dnevniku dveh ur nobene napake; vsi ponovni zagoni moji.

**Senca zdaj zajema tudi mestni LPP** (545 vrstic, 472 razrešenih). Rezerva budilke umerjena brez njih — ko bo vrstic dovolj, premeriti ločeno, ker je mestni LPP bistveno točnejši: mediana zamude 0 min, p90 3 min proti 3 in 11 min pri primestnem LPP.

## Obvestila mestnega LPP: 181 vrstic, dve novici (7. 9. 2026)

Feed `sources/lpp/all` nosi poleg zamud in leg tudi **obvestila** — doslej nebrana, vsakih 30 s v smeti.

Izmerjeno: **181 obvestil, dve različni.** „Postaja Čerinova na obvozu" (147 voženj) in „Postaja Tbilisijska na obvozu" (34), obe z besedilom „Vozilo se ne bo ustavilo na postaji". Vsako ima naključen UUID → običajen zajem zapiše 181, stran bi pokazala isto poved stokrat.

Združevanje po besedilu (`alerts.ingest_lpp()`), prizadeta postajališča v `alert_entity`. Odhodna tabla jih pokaže prek `for_stops()` — potniku natanko en podatek: **tu se avtobus ne bo ustavil**.

Vrsta `obvoz`, ne `ovira` → števci ovir (`/api/health`, `overview.disruptions`) ostanejo železniški, skladnost se ne podre.

**Past, ki je stala en obhod:** `alert_entity.route_id` in `trip_id` = `NOT NULL DEFAULT ''`. Prvi zapis vstavljal `NULL`, vsaka vrstica padla na omejitvi, `INSERT OR IGNORE` jo je **tiho požrl** — obvestili zapisani, a brez enega postajališča, videti kot da zajem dela. Zdaj prazen niz in navaden `INSERT`, da se ista napaka ssliši takoj.

**Konec obvoza ni v `end_ts`** (25. 9. 2026). Živi feed: 166 obvestil, dve novici: Čerinova (147) in Tbilisijska (19). „Postaja Bavarski dvor na obvozu“ nazadnje viden 22. 9. ob 22:31, `end_ts` december — tabla ga kazala tri dni po koncu. Od 4 obvozov z veljavnim `end_ts` sta 2 imela `last_seen` starejši od dneva. Obvoz zdaj velja le, če viden ob zadnjem branju feeda (±10 min).

## Feed ne poroča prvega postanka (7. 9. 2026)

Prijava: okno vožnje pri vlaku, ki še ni odpeljal, povsod „?" in „brez ocene", iskalnik za isto vožnjo: „običajno 0 min, 16 voženj, 100 % v 5 min".

Vzroka dva, prvi splošnejši od prijave:

**1. Železniški feed prvega postanka ne poroča nikoli.** Od **716 voženj z meritvami jih ima 0** meritev na prvem postanku. Ni naključje vzorca, ni splošno pravilo GTFS-RT — **avtobusi: 14 555 od 16 671 (87 %)**. Lastnost SŽ-jevega vira. „Običajna zamuda" na izhodišču vlaka zato ne more obstajati, ne glede na dni zajema; LPV 2273: meritve se začnejo pri `stop_seq = 2` (Ljubljana Polje, 16 dni).

**2. Okno vožnje ni imelo zgodovine.** `typical_at_stops()` obstaja od prej, iskalnik ga uporablja (`typical_dep`, `typical_arr`), `/api/train/{no}/run` ga ni vračal. Isti podatek, dva prikaza, ena številka manj.

Endpoint ga zdaj vrne za vsak postanek. Za izhodišče, kjer ga po točki 1 ni, prikaz vzame naslednji postanek in to **pove** — ni napoved za ta dan, je opis preteklih voženj.

## Gumb „shrani" je čakal na omrežje po podatek, ki ga je stran že imela (7. 9. 2026)

Klik na „shrani" pokazal potrditev šele po 1–2 s. Vzrok ni pisanje — shramba `localStorage` — ampak **preverba, ali postaji poznamo**: `stationExists()` je za vsako od obeh imen klical `/api/stations/search`.

Izmerjeno prek Cloudflara na `kajros.app` (`/api/stations/search?q=Ljubljana`, omrežje avtobusi): **0,69 / 0,67 / 0,63 s**. Dve zahtevi vzporedno = ~0,7 s samo režije, na mobilnem omrežju še TLS in čakanje v vrsti.

Kazalo postaj v pomnilniku že od nalaganja strani (`KAZALO`, za iskalnik brez sunkov). Preverba zdaj bere njega: **0 zahtev**. Strežnik le kadar se kazalo še ni naložilo. Iskanje po celem kazalu, ne po prvih osmih zadetkih — točno ujemanje sme biti kjerkoli.

## Ura, ki teče nazaj: `run` hrani zadnje stanje, tudi kadar je smet (7. 9. 2026)

Okno vožnje pri **vsaki deseti** vožnji avtobusa in vsaki dvajseti vlaka kazalo nemogoč vozni red: naslednja postaja **pred** prejšnjo. Vozilo ne more priti na postajo, preden odpelje s prejšnje.

Vzroki trije, vsi iz tega, da `run` hrani **zadnje** stanje postanka:

1. **Feed postanek neha pošiljati**, ostane nepotrjena napoved. RG 310,
   4. 9.: Litostroj +29 min (feed 17:59), nato Stegne in Vižmarje z **ničlo** in feedom iz 17:32 in 17:34, nato spet +22. Nezapolnjena ničla razloži 36 % železniških in 7 % avtobusnih skokov — podmnožica pojava, ne vzrok.
2. **Feed za nazaj popravi že prevožen postanek.** N0507, 7. 9.: ob 16:14 dobil +30 min za postanek, prevožen ob 15:48, medtem ko je vsa vožnja tekla nekaj minut pred voznim redom.
3. **Mestni LPP pošilja samo postanke pred vozilom** → vsaka vrednost = zadnja napoved pred prehodom, cel snop se lahko popravi hkrati.

Točka 3 izmerjena s projekcijo lege vozila na postaje vožnje: vozilo pri postaji 8 od 26, `stop_time_update` samo za 9–26. Pri mestnem LPP v `run` zato **nikoli ni meritve** — vedno le zadnja napoved pred prehodom (mediana 42 s pred prehodom, p90 27 s po njem). IJPP drugačen: 56 % voženj ima v seznamu še prvi postanek → prevoženi postanki se osvežujejo.

### Kaj pomaga

Katera vrednost je napačna, iz nje same ni ugotovljivo. Ugotovljivo, katere si nasprotujejo z največ drugimi: obdrži se **nepadajoče zaporedje ur z največjo skupno težo**, ostalo se označi (`stats.oznaci_neskladne()`).

Dvoje izmerjeno, ne uganjeno:

* **Utež.** Postanek, nazadnje osvežen prej kot kateri od prejšnjih, je lažji. Brez tega bi štetje samih postankov pri RG 310 zavrglo **pravo** vrednost (lukenj dve, prava ena). Lahek postanek se obdrži, kadar ničemur ne nasprotuje — sicer pri avtobusih pade 4,73 % postankov namesto 2,29 %.
* **Zaokroževanje na minuto.** Prikaz kaže minute; skok za 20 s ni nemogoč vozni red, ampak natančnost. Brez tega pri mestnem LPP prizadetih 38,4 % voženj namesto 17,2 %.

Izid na celi bazi (61 362 voženj, 1,1 s za vse — 18 µs na vožnjo):

| omrežje | vožnje z uro nazaj prej | potem | izpuščenih postankov |
|---|---|---|---|
| železnica | 4,9 % (364/7 466) | **0** | 0,57 % |
| avtobus | 10,1 % (5 347/52 680) | **0** | 2,29 % |
| LPP mestni | 3,6 % (39/1 081) | **0** | 1,33 % |

Meja med meritvijo in napovedjo (`_LAST_MEASURED_SQL`) nosi le **lokalni** del pravila — postanek, osvežen prej kot kateri od prejšnjih — ker teče nad seznamom voženj hkrati, celotne verige ne zmore. Železnica: lokalni del razloži vse primere (451 od 452); avtobusi: dve petini.

### Neskladne vrednosti statistike ne pokvarijo (7. 9. 2026)

Vprašanje: če je 2,29 % avtobusnih postankov smeti, ali očistiti tudi agregate? **Ne.** Primerjava vseh vrednosti proti tistim, ki ostanejo po `oznaci_neskladne()`:

| omrežje | mediana | povprečje | p95 | v 5 min |
|---|---|---|---|---|
| avtobus | 2,2 → 2,2 min | 7,4 → 7,3 | 22,3 → 21,0 | 71,7 → 72,1 % |
| železnica | 2,0 → 2,0 | 6,4 → 6,4 | 24,0 → 24,0 | 59,5 → 59,4 % |
| LPP mestni | 0,7 → 0,7 | 1,6 → 1,6 | 7,5 → 7,3 | 89,5 → 89,7 % |

Napaka **lokalna**: uniči eno vrstico na zaslonu, agregata ne premakne. Filtriranje v statistiki = dodatna zapletenost brez učinka; `povzetek` se računa v SQL, kjer verige ni mogoče pognati.

## Zamuda, ki lovi uro: potrjeno, brez poštenega filtra (7. 9. 2026)

Na strani „Vožnje, ki najbolj zamujajo" je bil N0786 z **mediano 111 min**. Dnevnik `obs`: vrednost raste v koraku z uro.

```
07:03:35  seq 1–2: 540 s   seq 3–5: 4260 s
07:07:02  vsi:    4800 s
07:12:18  vsi:    5400 s      … končno stanje 7 080 s (118 min)
```

Pojav že opisuje `collector._je_nazaj_v_prihodnost()` (vozilo obstane, feed zamudo pripisuje naprej). Varovalka primera ne ujame: zahteva, da je bil prejšnji zapis **meritev**; feed pa je tu za prihod in odhod ves čas dajal isto vrednost.

**Poštenega dodatnega filtra ni** — izmerjeno, ne domnevano:

* „Zamuda raste 1 : 1 z uro" ni znak smeti: pri železnici velja za **29,9 %** zadnjih sprememb (vlak pred signalom res nabira zamudo minuto na minuto). Avtobusi 8,3 %, LPP 8,8 %.
* „Zapis je meritev, kadar sta prihod in odhod različna" drži pri vlakih (3,4 % vrstic ob 67,7 % voznorednih postankov), pri avtobusih ne: **58,8 %** vrstic ima različna časa, vozni red ima postanek le pri **0,6 %**. Filtriranje po tem bi zavrglo 41 % avtobusnih meritev.

Ostaja odprto in zapisano. Pošteno je le prikaz: seznam najhujših voženj **že** kaže število voženj in delež v 5 min, npr. „5 voženj · 20 % v 5 min" ob 111 min — bralec vidi, na čem stoji.

## „Celje" je na avtobusni strani pomenilo vas 112 km stran (7. 9. 2026)

Iskanje sklada šumnike, zato je „celje" **točno** ime vasi **Čelje** pri Ilirski Bistrici; točno ime je bilo doslej vedno prvo. Posledica: ne le vrstni red v spustnem seznamu — `resolve_station()` vzame prvi zadetek, zato je iskalnik zvez z vpisanim „Celje" tiho iskal iz **Čelja**.

| | postankov v voznem redu | lega |
|---|---|---|
| Čelje | **2** | 45,592 / 14,154 |
| Celje AP | **1 014** | 46,233 / 15,268 |

Razdalja 112 km.

Takih iskanj na avtobusnem omrežju **26 od 5 361** (železniško nobenega): „novo" dalo postajo „Novo" (12) pred „Novo mesto" (631), „krizan" „Križan" (31) pred „Križanke" (4 818).

**Prag izmerjen, ne izbran.** Točni zadetek izgubi prvo mesto, kadar je vsaj **20-krat** manj prometen od najboljšega:

| prag | spremenjenih prvih zadetkov |
|---|---|
| 10 | 49 — med njimi pari, ki so ISTI kraj („Boršt" proti „Boršt/Krki K") |
| **20** | **26** |
| 50 | 14 — „celje" ostane, „novo" pade ven |

Točni zadetek se ne skrije: gre na **drugo** mesto. Šumnika ni mogoče vtipkati tako, da bi ga ločil od nešumnika, zato bi bila „Čelje" sicer nedosegljiva.

## Ob polnoči je tabla skrila vlake, ki so bili na poti (7. 9. 2026)

Vožnja, ki odpelje ob 23:50, ima postanke ob 24:21 in pripada **včerajšnjemu** prometnemu dnevu. Tabla je spraševala samo današnji dan: ob 00:30 na Laškem kazala šele vlak ob 01:58; LPV 2007 (pripeljal ob 00:56) manjkal.

Obseg: čez polnoč sega **10 železniških** in **154 avtobusnih** voženj (50 oz. 2 241 postankov po polnoči). Najdlje vozeča se konča ob **33:48** (avtobus) oz. **26:23** (vlak).

**Prag ni trd.** `stats.se_vozi_vceraj()` ga vzame iz baze (`MAX(trip.end_s)`, predpomnjeno po žigu GTFS uvoza) — ena nova nočna linija bi trdo številko tiho podrla. Praktično: železnica neha gledati včeraj po 02:23, avtobusi po 09:48. Isto funkcijo uporablja zemljevid, ki je rešitev imel že prej; zdaj na enem mestu.

Rešeno z rekurzijo, ne z drugo poizvedbo: vse nadaljnje (meja meritve, združevanje dvojnikov, običajna zamuda) mora teči nad **pravim** prometnim dnevom, sicer bi isti račun pisali dvakrat.

Cena, tabla s 150 vrsticami: ob 00:30 avtobusi 17,5 → 35,0 ms, železnica 0,1 → 0,4 ms. **Podnevi nič** — ob 17:00 rekurzije ni (50,3 ms prej in potem). Poizvedba ozka sama po sebi: pri `from_s` čez 86 400 se ujamejo samo postanki po polnoči.

Ista vrzel v **iskalniku zvez**: vstopnih postankov med polnočjo in 3. uro **2 145** (avtobusi) in **41** (vlaki), ponoči pogosto edini. `stats.connections()` zdaj pogleda včerajšnji dan po istem pragu; cena ob 00:30: 72,3 → 102,7 ms (avtobusi), 2,3 → 4,5 ms (vlaki), podnevi nič.

Past: rep se mora izračunati **pred** zgodnjim `return []`. Kadar današnji dan nima zveze, je včerajšnji rep edino, kar obstaja — tam je bila napaka najbolj vidna.

## Viri segajo različno daleč, prikaz pa je molčal (7. 9. 2026)

| vir | vozni red znan do | dni naprej |
|---|---|---|
| železnica | 2026-12-12 | 97 |
| avtobusi IJPP | 2027-12-31 | 481 |
| **mestni LPP** | **2026-09-15** | **9** |

Mestni LPP se uvaža v oknu osmih dni (cel mesec = 62 989 voženj, 1,6 milijona postankov). Posledica: iskanje na avtobusni strani za čez dva tedna vrnilo samo državni vozni red — brez besede, da česa manjka. Iskanje vlaka za junij 2027 vrnilo „na ta dan ni vožnje" — zveni kot dejstvo o prometu, v resnici vozni red še ni objavljen.

`/api/connections` in `/api/departures` zato vračata `vozni_red_do` (in `lpp_do` pri avtobusih); prikaz pove oboje.

Ubeseditev popravljena po prvem posnetku: „mestnih linij LPP ni" si je nasprotovalo z značkami **LPP 25** tik pod njim. Linija 25 je v **obeh** virih — državni jo nosi kot primestno. Besedilo zato govori o **viru**, ne o kategoriji linij.

## Večina živih avtobusov je bila skrita pod „drugi prevozniki" (7. 9. 2026)

`/api/vehicles` na produkciji, 18:40:

| `agency` | vozil | kam je padel na zemljevidu |
|---|---|---|
| `lpp` (mestni LPP) | **104** | „Drugi prevozniki" |
| `1123` Arriva | 33 | svoja plast |
| `1119` Nomago | 30 | svoja plast |
| `1118` LPP primestni | 9 | plast „LPP" |
| `1121` AP MS | 3 | svoja plast |

**58 % vseh živih vozil** za stikalom, ki je privzeto ugasnjeno in ne nosi imena prevoznika. Kdor je prižgal „LPP", je v Ljubljani videl devet avtobusov — vsi primestni, večina zunaj mesta. Podatek ves čas v odgovoru; manjkal le ključ `lpp` v `BUS_LAYERS`.

Po popravku isti pogled (Ljubljana, z13): števec LPP **124**, vrstica „Drugi prevozniki" skrita, ker je števec 0.

## Zakaj je lega stara 1–2 minuti (7. 9. 2026)

Vprašanje: ali ni lega osvežena vsakih 40 s, torej največ toliko stara. Ni — nobena sekunda ni naša. Izmerjeno 18:59–19:03 na `/app/bus/11` (mestni LPP) in neposredno na obeh feedih:

**Prikaz na tem vozilu (branja na 12 s):** 86 → 98 → 110 → 122 → 135 s, nato skok na 57 s = en cikel.

**Izvor sekund, po členih:**

| člen | LPP (`sources/lpp/all`) | IJPP (`vehicle_positions`) |
|---|---|---|
| lega stara že v feedu (glava − `vehicle.timestamp`) | mediana **35 s** (min 26, p90 50, max 54) | mediana **33 s** (p90 74, max 194) |
| osvežitev feeda | **~90 s** (n=99, mediana 90, min 69, max 111 — vsa vozila hkrati = paket) | polovica vozil se v 60 s ne premakne; premaknjenim mediana 40 s |
| glava feeda ob branju | stara 20–59 s | stara **1–2 s** |
| dodatek našega zajema | **0 s** (vseh 99 leg ima natanko isti `seen_ts` kot feed) | 0 s |

Torej: 35 s lega stara, preden jo derp.si zapakira; do 90 s nov posnetek; do 30 s naš cikel (`POLL_SECONDS`, LPP po ritmu zamud). Vsota ustreza opaženemu: min ~57 s, max ~147 s.

`seen_ts` = `vehicle.timestamp` iz feeda, ne čas našega branja — zato je „lega stara N" poštena številka, a ni videti lepše.

**Naše je samo zadnjih do 30 s.** LPP feed **nima ne `ETag` ne `Last-Modified`** (preverjeno v glavah) → pogojna zahteva ni mogoča: vsakih 30 s 315 682 B = **909 MB/dan**; vsebina se spremeni le vsakih ~90 s, dve tretjini so isti bajti. Pogostejši zajem: povprečna starost −~10 s, promet ×3 na 2,7 GB/dan.

## Ima LPP-jev lastni API lege in je hitrejši? (7. 9. 2026)

Vprašanje po meritvi starosti leg: novi vir mestnega LPP — GPS, pogostejše osveževanje kot derp.si?

**Lege: ne.** Edina endpointa s koordinatami vozil sta še vedno zaprta, danes znova preverjeno:

```
401  /api/bus/buses-on-route      {"message":"No permission for this API"}
401  /api/bus/bus-details
404  /api/bus/buses, /transit/api/vehicles, /transit/api/vehicle-positions
```

Koordinate v odprtih odgovorih so koordinate **postajališč**, ne vozil (`arrivals-on-route`, `stations-on-route`).

**Napovedani prihodi: da, precej.** Odprta endpointa, oba brez ključa:

| endpoint | pogostost spremembe vsebine | cena |
|---|---|---|
| `/api/station/arrival?station-code=` | **30 s** (5 sprememb v 150 s, razmiki 30,3 / 30,3 / 30,3 s) | 14 kB |
| `/api/route/arrivals-on-route?trip-id=` | **10–20 s** (razmiki 20,2 / 10,1 / 20,2 / 10,1 / 20,2) | 25 kB, 57 ms, 39 postankov naenkrat |
| derp.si `sources/lpp/all` (zdaj beremo) | ~90 s | 315 kB |

**3–9× hitreje od derp.si** — a to je `eta_min` v **celih minutah**, ne lega. Zaokroževanje ±30 s je primerljivo s pridobljeno svežino; kdor bo gradil, mora izmeriti oboje skupaj, ne le svežine.

**Identifikatorji se ujemajo brez prevajanja.** `trip_id` pri `data.lpp.si` = natanko **tretja komponenta** našega trojnega derp.si id-ja (`a|b|093c945c-…` ↔ `093C945C-…`, velike črke). Na tabli Bavarskega dvora 11 od 15 prihodov ujetih z našo tabelo `trip` na prvi poskus; štirje neujeti = primestne linije (56, 3G, 25), iz IJPP z drugimi id-ji.

Za zajem cele mreže neuporabno (ena zahteva na vožnjo, ~276 živih); za **odprto stran ene vožnje** uporabno: en klic, 25 kB, vsi postanki. Licenca `data.lpp.si` ostaja nenavedena — to je pogoj, ne podrobnost.

## Spoj z `data.lpp.si`: kaj se je izkazalo za resnično (7. 9. 2026)

| trditev | izmerjeno |
|---|---|
| njihov `trip_id` = **vzorec proge**, ne vožnja | 19 163 voženj LPP → **85** različnih tretjih komponent, najpogostejša 993× |
| `vehicle_id` isti v obeh virih | naš `vehicle_now.vehicle_id` najden v njihovem odgovoru pri 4 od 8 (manjkajoči = vozila brez preostalih prihodov) |
| postajališča ista | 704 od 714 ujemanje **pod 5 m**, mediana razdalje **0,0 m**; imena enaka pri 711 |
| vrstni red postankov se ujema | ena vožnja linije 11: **39 od 39**, razdalja 0,0 m |
| voženj s svežo napovedjo | **19 od 25** svežih mestnih vozil ob 22:15 |

Najmočnejši dokaz, da spoj ni naključen: **meje se ujemajo**. Kjer naša `stats.last_measured()` pove vozilo pri postanku 9, njihova eta pokriva postanke 10–27; pri meji 16 pokriva 17–21. Dva vira, ki se nista videla, se strinjata o legi vozila.

Prva različica primerjave: razlike +20 in +14,6 min pri dveh vožnjah — **moja napaka, ne vira**: vzel sem prvi prihod na postajališču, ta pripada naslednjemu avtobusu iste linije. Z izbiro po `vehicle_id` razlike ni.

S tem virom **ni** rešeno: starost lege. Koordinat vozil v odprtem delu API-ja ni → ostaja 57–147 s iz prejšnjega razdelka.

## Vleka z maline je prerasla svojo skripto (7. 9. 2026)

`scripts/potegni.sh` je imel `timeout 900 scp`. Baza na malini zrasla na **683 MB**, WiFi Pi Zerota da **~730 kB/s** → prenos ~16 min. Ob 23:05 `timeout` ubil `scp` pri **655 MB od 683**; skripta zaradi `set -e` tiho odnehala: v dnevniku ostalo „prenašam …" in nič več. Videti, kot da še teče.

Popravek ni večja meja, ampak **`rsync --append-verify --partial`**: prenos se da nadaljevati. Drugi poskus: manjkajočih 28 MB v 33 s. Kopija na malini se ob neuspehu **ne izbriše** → ponoven zagon poceni.

### Kaj je prilitje res prineslo

| korak | `obs` | `run` |
|---|---|---|
| malina → prenosnik | **+3 007 323** | +90 338 |
| prenosnik → arwen | **+6 309 794** | 1 010 766 → **1 249 005** |
| arwen `obs` skupaj | 6 740 872 → **13 050 666** | |

`repair` po prilitju: 3 535 popravljenih vrstic, **0 osirotelih meritev**.

### Merilo ni vsota, ampak pokritost

Vsota vrstic zavajala: prenosnik jih imel največ (1,15 M), a pogosto ugasnjen; malina najmanj (962 k), a **neprekinjeno in dlje nazaj**. Šele po prilitju obojega pokritost:

| dan | ur z meritvijo |
|---|---|
| 2026-08-21 | 9/24 — prvi dan zajema |
| 2026-08-22 … 08-26 | **24/24** |
| 2026-08-27 | **16/24 — edina prava luknja** |
| 2026-08-28 … 09-07 | **24/24** |

Osem ur 27. 8. nima nobena od treh naprav; ni več od kod dobiti.

Še eno napačno branje: dnevi s tretjino običajnih meritev (5. in 6. 9.) **niso izpad**, ampak **sobota in nedelja** — vozi mnogo manj avtobusov. Preden kdo lovi luknjo, naj pogleda dan v tednu.

### Kar je prilitje pokvarilo in kako je bilo popravljeno

Prilitje 6,3 milijona meritev ima dve posledici, ki ju je bilo treba ujeti takoj — obe vidni šele **po** njem, ne med njim:

**1. WAL zrasel na 902 MB, ni se imel kdaj zložiti nazaj.** Strežnik ves čas držal odprte bralne povezave → SQLite ni mogel narediti checkpointa. Posledica: `/api/health` **15,4 s**, v dnevniku zajema `database is locked` vsakih nekaj sekund. Popravek: ustaviti storitev, `PRAGMA wal_checkpoint(TRUNCATE)` (12 s), zagnati nazaj — WAL 902 MB → 543 kB, baza 973 MB → 1,52 GB. **Po vsakem velikem prilitju v živo bazo je to nujen zadnji korak**, sicer je videti kot okvara.

**2. `MAX(feed_ts) FROM run` postal 938 ms.** Poizvedba = „ali zajem še dela"; `/api/health` je ne sme predpomniti (prag „zajem stoji" 90 s). Pri 1,25 mio vrstic pregled cele tabele — `connections.js` kliče health vsakih 30 s na vsak odprt zavihek → sekunda dela z diskom na zavihek na pol minute, na istem disku, kjer piše zajem. Popravek: indeks `run_feed_ts`:

| | pred | po |
|---|---|---|
| arwen (1,25 mio vrstic) | 938 ms | — |
| razvojni računalnik | 65,9 ms | **0,1 ms** |

Poduk: **poizvedba, poceni pri 800 000 vrsticah, ni nujno poceni pri 1,25 milijona.** Po vsakem večjem prilitju izmeri `/api/health` in poizvedbe, ki se ne dajo predpomniti.

## Spletna kopija SQLite se ob pisanju začne znova (7. 9. 2026)

Selitev maline obtičala; razlog ni viden iz ničesar, kar človek pogleda prvo.

`sqlite3 baza ".backup kam"` = **spletna** kopija: kadar kdo med njo piše v izvorno bazo, se kopiranje **začne znova od prve strani**. Zajem na malini piše vsakih 30 s, baza 683 MB, kopija na SD kartici ~17 MB/min → rabi ~40 min. Kopija se v takih pogojih **ne konča nikoli**.

Videz: datoteka 17 min stala pri **190 873 600 bajtih**, `mtime` se ves čas osveževal. `sqlite3` porabil 2:38 procesorskega časa, stanje `D`. Videti kot počasen stroj, ne zanka.

**Pravilo:** pred kopijo ustavi pisca. `deploy/preseli-malino.sh` zdaj ustavi `sztrack-zajem` pred `.backup` in ga ob padcu prižge nazaj — stroj brez zajema je slabši od stroja s starim imenom.

Odpadel tudi `gzip -1` na 683 MB: na Pi Zero W nekaj dodatnih minut, prostora 19 G, dnevne stisnjene kopije obstajajo posebej.

## Kar je bilo poceni pri 6,7 milijona, ni poceni pri 13 (8. 9. 2026)

Po prilitju je `/api/health` prek tunela odgovarjal **13,3 s**. Isti endpoint na arwenu lokalno 7 ms — razlike ni delal tunel, ampak **iztek predpomnilnika**: kdor po 600 s prvi pride mimo, plača cel izračun.

Cena števcev na arwenu s **toplim** predpomnilnikom, po prilitju:

| poizvedba | čas |
|---|---|
| `COUNT(*) FROM obs` (13,05 mio) | **932 ms** |
| razrez po omrežjih (`run JOIN trip`) | **1 452 ms** |
| `COUNT(*) FROM run` | 29 ms |

Točno to, kar pravilo projekta prepoveduje — agregat čez vso zgodovino v zahtevi. Popravek ni večji TTL (samo redkeje izpostavi istega nesrečnika), ampak **postrezi staro, osveži v ozadju**: `_predpomni(..., v_ozadju=True)` takoj vrne prejšnjo vrednost, novo izračuna v niti; ključavnica poskrbi za eno osvežitev, ne eno na obiskovalca. Sinhrono samo prvi klic po zagonu, ko stare vrednosti ni.

Dva testa: stara vrednost se res postreže in nova res izračuna; privzeto vedenje brez zastavice se ne spremeni.

## Prometni dan je pri LPP zapisan v `trip_id` (8. 9. 2026)

Po selitvi malina mestnega LPP ni zajemala: `poll_lpp` vračal `trips: 0`, brez napake. Videti kot da ponoči nič ne vozi.

Vzrok: trojni `trip_id` pri LPP ima **prometni dan v prvi komponenti** — izmerjeno na arwenu: devet različnih prvih komponent, vsaka ~2 428 voženj, vsaka pripada natanko enemu datumu:

| prva komponenta | dan |
|---|---|
| `6bec7600-…` | 2026-09-07 |
| `96959eb0-…` | 2026-09-08 |
| `ceec99e5-…` | 2026-09-09 |

Malina uvozila ob 00:15, dobila okno **od 8. 9. naprej**. Feed ob 01:10 govoril o vožnji z dne **7. 9.** — nočni avtobus, speljal pred polnočjo. Ujemanja ni: `ujetih v trip: 0 od 1`.

Popravek: okno se začne **včeraj**, ne danes. Cena en dan, ~2 400 voženj, ~62 000 postankov (celo okno 19 163 voženj in 496 542 postankov na osem dni).

Arwen tega ni pokazal: uvozil prejšnji dan opoldne, 7. 9. ima v oknu. Napaka bi se pokazala šele ob prvem uvozu tik po polnoči — videti kot mirna noč.

### Malina po selitvi, izmerjeno

| kaj | vrednost |
|---|---|
| uvoz voznega reda (IJPP + LPP) | ~50 min, **vrh RSS 213 MB** od 427 + 426 swapa |
| vozni red po uvozu | 32 478 voženj (19 163 LPP mestni, 5 402 Arriva, 4 823 Nomago, 1 569 LPP primestni, 789 SŽ, 732 AP MS) |
| postankov | 496 542 |
| baza | 683 → 696 MB, disk 18 G prost |
| selitev | 962 951 → 962 951 meritev |

## Prikaz je trdil dogodek, o katerem ni imel novic (8. 9. 2026)

Uporabnik na Ljubljani Polje, aplikacija za LPV 2001 kazala **„+6 min · izmerjeno · vlak je tu že bil"**. Kaj je vlak res počel, iz naših podatkov **ni ugotovljivo** — tega ne domnevamo. Ugotovljivo je dvoje drugega, oboje narobe pri nas.

**1. Meja meritve je prehitevala feed.** Postanek veljal za prevožen, ko je „vozni red plus zadnja znana zamuda" mimo. To je ura, ne meritev: ko feed o vožnji utihne, se pogoj sam razširi do konca proge. Ob 07:04 prikaz trdil, da je vlak prevozil **vseh 29 postankov**, vključno s prihodom v Ljubljano ob 07:01. Meja zdaj zamejena z zadnjo besedo feeda o tej vožnji.

Varno izmerjeno: vožnje **v** feedu so sveže — mediana **45 s**, p90 59 s, največ 343 s (733 voženj). V normalnem obratovanju nič ne spremeni.

**2. Tišine feeda prikaz ni povedal.** Kaj je feed rekel o tej vožnji:

| ura | postanek | vrednost |
|---|---|---|
| 06:43:25 | Ljubljana Zalog | +6 |
| 06:51:52 | Ljubljana (končna) | **0** |
| 06:52:56 | Ljubljana Polje | +6 |
| 06:54:22 | Ljubljana | +6 |
| — | — | **24 minut tišine** |
| 07:18:53 | Ljubljana | **+29** |

Ob 07:00 zadnja novica o vlaku stara **7 min**, prikaz pisal „pred 5 min" — to je starost *domnevnega prehoda* (vozni red + zamuda), ne novice. Zdaj se pokaže tišina: „o vlaku 15 min ni novic — to je zadnja znana številka, ne trenutna", prag **180 s** (trikratnik izmerjenega ritma osveževanja).

**Nerešeno, vredno zgraditi:** feed **prevožene postanke izpušča** — vsaka preverjena železniška vožnja ima v sporočilu le okno postankov pred vozilom (LP 4201: 26–29 od 31; LPV 2402: samo 14 od 17). Izpad postanka iz okna = **opazovan dogodek prehoda**, ne aritmetika z zamudo. Tega ne beležimo, zato takega vprašanja za nazaj ni mogoče razrešiti.

### Koliko je takih voženj (8. 9. 2026, zadnjih 14 dni)

Vprašanje po LPV 2001: izjemen primer? Merilo: za vsak postanek primerjaj vrednost, ki bi jo prikaz **kazal ob domnevnem prehodu** (zadnja izjava feeda do tedaj), s **končno** vrednostjo istega postanka.

| | železnica | avtobus |
|---|---|---|
| primerjanih postankov | 81 798 | — |
| postankov, popravljenih za ≥ 5 min | 118 (**0,14 %**) | 25 691 |
| postankov, popravljenih za ≥ 10 min | 51 (0,06 %) | — |
| **voženj z vsaj enim takim postankom** | 113 od 6 948 (**1,63 %**) | 11 682 od 63 136 (**18,50 %**) |

**Prevladujoča oblika ni tista iz LPV 2001.** Pri železnici **90 od 118 popravkov (76 %) izhajalo iz prikazane NIČLE** — prikaz trdil „točno", resnica do **+66 min**. Pri avtobusih takih 17 % (največja +647 min, znani vzorec „ura namesto zamude").

Najhujši primeri, vsi z istim podpisom:

```
2026-08-26  LP 3191   postanek  9: videno +0 -> na koncu +66 min
2026-09-04  LPV 2271  postanek 12: videno +0 -> na koncu +34 min
2026-08-27  LP 3387   postanek  2: videno +0 -> na koncu +29 min
```

Obstoječi varovalki tega ne ujameta: `is_zero_blip` in pogoj `NOT (delay_s = 0 AND prev_max >= 300)` se sprožita šele, kadar je kak **prejšnji** postanek že kazal veliko zamudo. Pri postanku 2 ali 6 pred njim ni ničesar, kar bi sprožilo sum.

**Edino, kar bi to res rešilo = zapis okna feeda.** Feed prevožene postanke izpušča; dokler je postanek v sporočilu, vozilo mimo njega ŠE NI. Velja enako za ničlo kot za +6, ne zahteva domneve o velikosti zamude.

## Koliko časa res hodiš do postajališča (8. 9. 2026)

Iskanje poti od vrat do vrat: hoja = polovica odgovora. Vprašanje: ali zadošča zračna razdalja s stalnim faktorjem obvoza.

**Prvi poskus umeritve iz naših podatkov ne odgovori.** Razmerje pot po `shape` polilinji / zračna črta med **sosednjima postajališčema iste linije**, 42 869 parov:

| razdalja | parov | mediana | p90 |
|---|---|---|---|
| < 300 m | 1 095 | 1,21 | 2,44 |
| 300–800 m | 14 760 | 1,06 | 1,49 |
| > 800 m | 27 014 | 1,07 | 1,33 |

Mediana 1,07 — meri cesto med dvema postajališčema, ki po definiciji ležita na isti cesti. Pešec od hiše do postaje ni na tej cesti. Številka = **prenizka**, ne previsoka; za rezervo neuporabna.

**Prava umeritev proti pešpotim.** Naključne točke po Sloveniji do najbližjih postajališč; zračna črta vs prava pešpot (OSRM, peš profil). Dva neodvisna vzorca:

| vzorec | parov | mediana | p75 | p90 | največji |
|---|---|---|---|---|---|
| javni OSRM, razvojna baza | 211 | 1,42 | 1,85 | 2,55 | 4,76 |
| naš OSRM, arwenova baza | 1 080 | 1,43 | 1,83 | 2,63 | **7,86** |

Obvoz ni šum, ampak **ovire** — Sava, proga, avtocesta. Postajališče 300 m stran po zraku = lahko 1 400 m hoje.

| faktor | pokrije primerov |
|---|---|
| 1,2 | 30 % |
| 1,3 | 41 % |
| 1,45 | **52 %** |
| 1,6 | 65 % |

Ena konstanta ne more biti hkrati varna in uporabna: 1,45 podceni pot v 48 % primerov (potnik zamudi avtobus); 2,63 bi iz 500 m naredila 15 minut hoje in stran bi zavračala dosegljive povezave.

**Zato hoja teče čez svoj usmerjevalnik** (`kajros/hoja.py`, `deploy/osrm.sh`). Faktor = le zasilna pot, zato **p75 (1,85), ne mediana** — brez usmerjevalnika velja pravilo budilke: potnik ne sme zamuditi. Izmerjeno na 831 parih, zasilna ocena: mediana **+366 s predolga**, p10 −814 s, v 15 % primerov še vedno prekratka. To = cena nemerjenja.

### Postavitev usmerjevalnika (arwen, i5-6200U, 4 niti)

| korak | čas | vrh pomnilnika |
|---|---|---|
| prenos `slovenia-latest.osm.pbf` (299 MB) | 30 s | — |
| `docker pull` | 21 s | — |
| `osrm-extract -p foot.lua` | **481 s** | **2,25 GB** |
| `osrm-partition` + `osrm-customize` | 106 s | 572 MB |
| podatki na disku (brez `.pbf`) | 807 MB | |
| strežnik med tekom | | 525 MB |

| matrika ena točka → N ciljev | 10 | 30 | 70 | 120 |
|---|---|---|---|---|
| odziv | 8 ms | 14 ms | 32 ms | 81 ms |

Troje, kar je meritev pokazala (sicer bi se domnevalo):

* **Naš strežnik vrne isto kot javni** — 412,8 m do decimalke. „Samo za demo" = omejitev gostitelja, ne programa.
* **Peš profil hodi 5,00 km/h** = natanko hitrost, ki jo je zahteval David. `duration` je že prava številka, računanje ni treba.
* **Peš nedosegljivih postajališč ni** — 0 od 831. Ravnanje za `null` v matriki vseeno obstaja, ker bi tiha ničla izgledala kot „nič hoje".

Meja velikosti matrike preizkušena do 300 koordinat brez napake; privzetek ni dokumentiran, zato ga `deploy/osrm.sh` nastavlja izrecno na 1 000.

## Doseg hoje: 25 minut je zastonj (8. 9. 2026)

Pričakovanje: večji doseg podraži iskanje. Ne podraži — cena je v premetavanju voznega reda, ne v številu izhodiščnih postajališč.

| primer | 10 min | 15 min | 20 min | 25 min |
|---|---|---|---|---|
| Bavarski dvor → Vič | 08:27 | 08:25 | 08:24 | **08:24** |
| Grosuplje → LJ center | 09:07 | 08:57 | 08:57 | **08:57** |
| Bohinj → Kranj | 10:26 | 10:26 | 10:22 | **10:22** |
| čas iskanja | 259–283 ms | 252–441 ms | 263–305 ms | 267–316 ms |

Bavarski dvor: izhodišč s 16 na 73, iskanje enako hitro; Grosuplje: prihod **10 minut boljši**, ker je bilo pravo postajališče 11 minut hoje daleč.

Kandidatov v polmeru 2 083 m (25 min × 5 km/h): Bavarski dvor **201**, Ljubljana Polje 66, Grosuplje 27, Bohinjska Bistrica 9.

## Iskanje od vrat do vrat, prototip (8. 9. 2026)

Prototip čez **obe omrežji hkrati**, štiri noge, hoja na obeh koncih, peš prestopi med postajališči do 300 m:

| primer | izhodišč | ciljev | iskanje |
|---|---|---|---|
| Bavarski dvor → Vič | 44 | 12 | 314 ms |
| Grosuplje → LJ center | 13 | 47 | 312 ms |
| Bohinj → Kranj | 5 | 13 | 280 ms |
| Ljubljana Polje → Maribor | 3 | 6 | 225 ms |

Vozni red obeh omrežij za 8. 9. 2026 = **255 245 postankov** v 12 963 vožnjah; nalaganje 1,74 s, drži 94 MB (vrh 131 MB).

Ročno preverjeno, da izid ni naključje: Grosuplje → Ljubljana center ob 8:00 = 416 m hoje (6,5 min) → LP 3232 ob 08:17 → Ljubljana 08:44 → 982 m hoje (15,3 min) → **08:59**. Prototip vrne isto minuto.

**Peš vso pot je včasih hitreje.** Ljubljana Polje → BTC ob 8:00: avtobus = prihod 09:04; hoja 47 minut = 08:47. Stran, ki tega ne pove, pošilja ljudi na počasnejšo pot.

### Peš povezave med postajališči

| doseg | povezav | najbolj povezano postajališče |
|---|---|---|
| 150 m | 5 609 | 7 sosedov |
| 300 m | 7 314 | 14 sosedov |
| 500 m | 12 070 | 25 sosedov |

Brez teh se prestopa **samo na istem `stop_id`** — „Bavarski dvor" v eno smer in v drugo za iskalnik nista isti kraj. Takih imen **4 507 od 5 500**.

Izmerjeno, ko so bile poti res izračunane (`kajros pespoti`, 8. 9. 2026):

| | |
|---|---|
| postajališč s peš sosedom v 500 m | 9 970 od 10 509 |
| shranjenih poti (usmerjenih, ≤ 6 min) | **20 060** |
| od tega isto ime, torej čez cesto | 10 890 (54 %) |
| imen, ki dobijo soseda z drugim imenom | 1 781 |
| trajanje | mediana 1,6 min, p90 5,4 min |
| gradnja prek tunela do arwena | 97 s |

Doslej neviden primer: „Bavarski dvor" → „Bavarski dvor" (druga smer) = **133 s hoje**, 169 m po zraku. Primer, da zračna razdalja ne zadošča niti tu: „Bavarski dvor" → „Gosposvetska" = 99 m po zraku, 115 s hoje — obvoz 1,61×.

## Iskanje od vrat do vrat: kaj je bilo narobe, preden je delalo (8. 9. 2026)

`kajros pot --od lat,lon --do lat,lon`. Izmerjeno s toplimi predpomnilniki, čez obe omrežji, hoja iz OSRM prek tunela do arwena:

| primer | izhodišč/ciljev | čas | predlogov |
|---|---|---|---|
| Grosuplje → LJ center | 25 / 120 | 179 ms | 2 |
| Ljubljana Polje → BTC | 19 / 62 | 193 ms | 2 |
| Bavarski dvor → Vič | 120 / 87 | 282 ms | 2 |
| Bohinjska Bistrica → Kranj | 7 / 50 | 99 ms | 2 |
| Maribor → Koper | 21 / 11 | 720 ms | 2 |

Prvi izid, ki ga druga slovenska orodja ne dajo — Maribor → Koper vključi **4 minute hoje z železniške postaje Ljubljana na avtobusno**, ker je vlak do Ljubljane + avtobus naprej hitrejši od same železnice.

### Štiri napake, ki jih je bilo treba popraviti

**1. Iskanje po postajah v SQL = 629 ms.** Poizvedba „katera postajališča so blizu in ta dan kaj strežejo" šla čez `JOIN sched JOIN trip JOIN service_day`. Isto v Pythonu, z množico postajališč iz **že naloženega voznega reda** = 7 ms. Vozni red se za iskanje tako naloži; nova poizvedba = že opravljeno delo.

**2. Brez obrezovanja po meji iskanje 510 ms, z njim 7 ms.** Zgornja meja = čas hoje vso pot (kadar obstaja), stiska se ob vsakem doseženem cilju. Brez nje zadnja kroga premetavata pol države, ki je nihče ne vidi. Izid do minute isti.

**3. Krogi niso omejevali nog — v obeh iskanjih.** Z eno tabelo najboljših prihodov poznejša izboljšava prepiše tudi starša postajališča in veriga nazaj preskoči kroge. Izmerjeno Maribor → Koper: pri meji **dveh** nog iskanje vrnilo pot s **štirimi** vožnjami.

Ni bila le netočna dokumentacija. `journey.plan()` ima varovalko `len(legs) > max_legs: return []` — predolgo verigo **tiho zavrgel**, veljavna pot izginila brez sledu. Oboje zdaj RAPTOR z oznakami po krogih (`tau[k]` = najzgodnejši prihod z največ k vožnjami).

Popravek `journey.plan()` ne poslabša izida: vzorec 80 naključnih parov železniških postaj = **4 % brez odgovora**, natanko zapisana številka izpred popravka; vsi trije dokumentirani primeri še delajo (Ljutomer mesto → Ribnica 3 prestopi, Stara Cerkev → Prevalje 3, Narin → Kranj 2).

**4. Za Maribor → Koper usmerjevalnik računal 200 km dolgo pešpot**, iskanje jo takoj zavrglo. Zračna črta = spodnja meja poti: če je že ona daljša od peš mogočega, se usmerjevalnika ne vpraša.

### Kar se v izidu vidi in ni napaka

* **Dve hoji zapored**: pot s postajališča čez peš prestop na drugo, šele od tam do vrat. Za potnika ena hoja → zlijeta se; vmesno postajališče brez pomena, minute ne.
* **Hoja nič minut** = postajališče pred vrati. Ni noga, ampak šum.
* **Ista pot iz dveh vprašanj.** „Najhitreje" in „z manj hoje" lahko dasta isto vožnjo z drugačnim repom; ključ za razdvajanje = **samo vožnje**, ne ure — te se razlikujejo za pol minute.

## Zamude v poti od vrat do vrat (8. 9. 2026)

Iskanje teče po voznem redu, ker napovedi za vožnjo čez pet ur ni; zamuda se pripiše šele na koncu, veriga se z njo prebere znova.

Pravilo, katera številka velja, **izluščeno, ne prepisano**: `stats.zamuda_na_postanku()` zdaj uporabljata iskalnik zvez in ta stran. Preverjeno, da izluščenje ničesar ne spremeni — `/api/connections` za isto poizvedbo vrne **bajt za bajt isti odgovor** (18 346 B).

Prvi izid v živo (RG 432, Litija → Ljubljana, 8. 9. ob 12:35): vozni red 12:35 → 13:07, z zamudo **12:58 → 13:31**, žeton „+23 min · ocena". Potnik ima 23 minut več, preden mora od doma — le zaradi tega ta stran obstaja.

Preostanek prestopa iz **zaokroženih minut**, ne iz sekund: `ostane = načrtovano − zamuda prvega + zamuda drugega`. Vse tri številke na zaslonu druga ob drugi; bralec, ki jih sešteje, mora priti do iste — ista past kot pri razredu zamude.

## Kaj je pokazal zaslon, česar meritev ni (8. 9. 2026)

Stran `/app/pot` v produkciji ponudila **dva predloga, drugi po vseh merilih slabši**: Grosuplje → Zmajski most, 12:53 z 20 min hoje poleg 13:01 z 10 min, oba prihod 13:31. Odideš prej, hodiš dvakrat dlje, prideš ob isti minuti.

Vzrok: vprašanje „z manj hoje" omeji hojo na **vsakem koncu posebej** (10 min tja, 10 min nazaj), ne v vsoti — zato lahko da pot z več hoje skupaj. Zdaj odpade vsak predlog, ki je po vseh štirih merilih (odhod, prihod, hoja, prestopi) slabši od že izbranega.

Posledica: ostal en sam predlog. Zato dodani **naslednji odhodi**: dve nadaljnji iskanji z začetkom minuto za prvim odhodom. Poceni, ker sta peš matriki že izračunani, vsako nadaljnje iskanje = le krog čez vozni red. Izid za isto vprašanje: 13:00 (avtobus 69), 13:27 (LP 3296
+ 3B) in 13:40 — namesto ene ure.

### Zmogljivost v produkciji (arwen)

| | čas |
|---|---|
| prvi klic po zagonu (hladen vozni red) | **14,7 s** |
| topel klic | **0,85 s** |
| ogrevanje v ozadju (`server._ogrej_pot`) | 9,6 s |

Prva zahteva po zagonu **26,5 s**, ker tekla vzporedno z ogrevanjem in isti vozni red naložila še enkrat. Ključavnica na ključ (ne skupna) znižala na 14,7 s — toliko, kolikor traja eno nalaganje.

`_TT_CACHE_MAX` z dveh na tri: pot bere obe omrežji hkrati, iskalnik zvez vsako posebej; pri dveh vnosih je vsako iskanje zvez izrinilo skupno sliko. Cena majhna, ker je železnica drobna — avtobusi 92 MB, oboje skupaj 94 MB, železnica ~3 MB.

## Vrstni red predlogov je nasprotoval številkam v njih (8. 9. 2026)

Prijava s testiranja: Križanke → Novo Polje ob 12:51 ponudil štiri avtobusne poti in **nobene z vlakom**, čeprav vlak prišel prej. Preverjeno na roko:

| pot | vozni red | z zamudo |
|---|---|---|
| avtobus 19B + 25 | 12:52 → **13:35** | 12:51 → **13:43** |
| vlak LPV 2219 | 13:01 → **13:38** | (brez meritve) 13:38 |

Dva vzroka, oba napaki:

**1. Razvrščanje po voznem redu, prikaz z zamudo.** Stran razvrstila po voznoredni uri (13:35 < 13:38), poleg izpisala pričakovano (13:43). Vrstni red in številke si nasprotovali — ista past kot barva, ki pripoveduje drugo zgodbo kot številka poleg nje. Zdaj se zamude pripišejo **pred** razvrščanjem, ključ = ura na zaslonu.

**2. Druge poti sploh ni bilo med predlogi.** Nadaljnja iskanja gledala poznejše odhode, ne drugih poti. Zdaj med predlogi tudi iskanje, ki **izloči vožnje najboljše poti** — tako pride na zaslon vlak, tudi kadar avtobus po voznem redu zmaga za tri minute.

### Zamude v samem iskanju: izmerjeno, in ni zmaga

Preizkušen tudi prenos znane zamude v samo iskanje (vozila, ki so zdaj na poti, odpeljejo z izmerjeno zamudo). Na 39 naključnih parih v Ljubljani:

| | |
|---|---|
| boljši pričakovani prihod | 1 |
| slabši | 1 |
| enak | 37 |
| mediana razlike | 0,0 min |
| cena | +85 ms na iskanje |

**Ni** izboljšava prihoda. Obdržano iz drugega razloga: brez tega iskanje ponuja prestope, za katere iz meritev **že vemo, da ne držijo** — na 183 ponujenih prestopih 1 (1 %), z zamudami 0 od 175. Ker so zamude na zaslonu, bi razvrščanje po voznem redu spet delalo vrstni red, ki nasprotuje številkam.

Vozila, ki še ne vozijo, zamude nimajo, obravnavana kot točna — velja za obe različici. `zamiki()` predpomnjen na žig zajema, ker izračun za vseh 13 107 voženj dneva = 541 ms.

### Odhodi, ki so že odpeljali, se preskočijo

`at_stop` urejen po odhodu, iskanje pa za vsako postajališče v čelu prehodilo **vse dnevne odhode**, šele nato zavrglo tiste pred potnikovim prihodom. Z dvojiškim iskanjem (`bisect`) začne pri prvem odhodu, ki je še lahko naš — največ `MAX_ZAMIK_S` (60 min) pred prihodom, ker vožnja z zamudo odpelje pozneje, kot piše.

| primer | prej | zdaj |
|---|---|---|
| Križanke → Novo Polje | 633 ms | **299 ms** |
| Bavarski dvor → Vič | 575 ms | **303 ms** |
| Maribor → Koper | 569 ms | **429 ms** |
| Grosuplje → LJ center | 228 ms | **180 ms** |

Ista meja obreže tudi zamike same: 482 minut ni zamuda, ampak feedova zamenjava prometnega dne (isti razlog kot `api.MAX_LIVE_DELAY_S`).

## Zakaj je iskanje postaje trajalo pet sekund (8. 9. 2026)

Prijava s testiranja: vpis imena postaje čakal >5 s.

| poizvedba | čas (razvojni) |
|---|---|
| `/api/stations/search?q=ljublj&network=zeleznica` | 0,05 s |
| `…&network=avtobus` | 0,55 s |
| `…&network=vse` | **1,35 s** |

Stran s potjo išče čez **obe** omrežji, na vsak pritisk tipke; arwen ~3–4× počasnejši → okoli 5 s. Iskalnik zvez tega nikoli ni delal — kazalo naloži enkrat, išče v brskalniku.

Zdaj enako tu: `/api/stations/index?network=vse&koordinate=1` = **323 kB**, 12 h v `localStorage`, strežnikov predpomnilnik ga postreže v **3,6 ms** (hladno 1,6 s, enkrat na uvoz voznega reda). Razvrščanje isto kot na strežniku (`iskalnikKazala()`), sicer ista črka da dva različna seznama.

Kazalo nosi tudi lego — postajališče z **največ prometa** pod tem imenom. Naključno izbrano bi pri „Bavarski dvor" enkrat dalo eno stran ceste, enkrat drugo.

## Tabla je ponavljala vrednost, ki jo je okno vožnje zavrglo (8. 9. 2026)

Straža `tabla in okno vožnje ista številka` večkrat pokazala isto: linija 8 na Bavarskem dvoru, tabla „izmerjeno −1 min", okno vožnje „neskladno". Preverjeno: pade **tudi na kodi izpred vseh sprememb tega dne** — ni regresija, ampak zapisana omejitev: `_LAST_MEASURED_SQL` nosi le **lokalni** del pravila, ker teče nad vsemi vožnjami hkrati.

Tabla imela svojo, krajšo različico pravila (primerjava z zadnjo meritvijo), okno celo verigo (`stats.oznaci_neskladne`). Zdaj tudi tabla uporablja celo verigo: `journey._neskladni_postanki()` prebere `run` za vse vožnje s table v **eni** poizvedbi, isto funkcijo požene po vožnjah. Tabla prometnega mestnega postajališča ima do devetdeset voženj, zato ena poizvedba, ne ena na vožnjo — izmerjeno ostane 49 ms (Ljubljana), 96 ms (Bavarski dvor).

Tabla namesto zavrnjene vrednosti pokaže **zadnjo skladno meritev in kje je bila** — „+4 min, izmerjeno na postaji Tivoli". To ni nasprotje z oknom, ampak razkritje, zato popravljena tudi straža: napaka le, kadar tabla **ponovi** vrednost, ki jo je okno zavrglo (`delay_from` ni nastavljen).

Kolikokrat pravilo prime, izmerjeno na celem dnevu (12 371 voženj, 237 675 postankov):

| | neskladnih postankov | voženj z vsaj enim |
|---|---|---|
| avtobusi | 5 012 / 230 665 (2,17 %) | 1 621 / 11 775 (13,8 %) |
| železnica | 17 / 7 010 (0,24 %) | 15 / 596 (2,5 %) |
| skupaj | 5 029 (2,12 %) | 1 636 (13,2 %) |

## Predlog, ki je bil ovinek namesto poti (8. 9. 2026)

Prijava s preizkusa: iz Ljubljane Polje proti vzhodu stran predlagala vlak **na zahod** v Ljubljano, nato **8,8 km (1 h 46) peš nazaj** — dve uri za pot, ki jo prehodiš precej hitreje.

**Vzroka nisem dokazal.** Preverjeno dvoje, oboje v redu: `blizu()` spoštuje mejo hoje na **obeh** straneh (največja vrnjena vrednost natanko 1 500 s = 25 min, izmerjeno na 30 točkah); podrobna stran vrne isto kot seznam (30 parov, največja razlika v skupni hoji **0 min**).

Vgrajeni dve varovalki, ki nesmisel te oblike naredita nemogoč ne glede na vzrok:

* **Pot z vozilom, v kateri je hoje več, kot bi je bilo peš vso pot, ni predlog.** Zato treba trajanje hoje računati tudi, ko je hoja predolga za ponudbo (`MAX_PES_PRIMERJAVA_S` 3 h proti `MAX_PES_VSO_POT_S` 1 h) — brez te številke primerjave ni mogoče narediti.
* **Kadar z vozilom ni ničesar, se pove, koliko je peš.** „Ni poti" slabši odgovor od resnice „peš 1 h 25"; potnik sicer čaka avtobus, ki ne pride.

Preizkušeno na vzorcu iz prijave: (46,073, 14,582) → (46,076, 14,615) zdaj da samo hojo 44 min; prej isti vzorec dal pot z vozilom in dolgo hojo.

## Ali je meja hoje do postaje sploh potrebna (8. 9. 2026)

David vprašal, ali polje „največ hoje" rabiva. Izmerjeno na 40 parih točk (1,5–25 km narazen, jutranja konica, obe omrežji):

| meja | poti z vozilom | hoje mediana | hoje p90 | prihod proti 45 min |
|---|---|---|---|---|
| 10 min | 11/40 (28 %) | 16 min | 19 min | **enak** |
| 15 min | 15/40 (38 %) | 18 min | 30 min | **enak** |
| 20 min | 23/40 (58 %) | 23 min | 35 min | **enak** |
| **25 min** | **30/40 (75 %)** | **28 min** | 48 min | **enak** |
| 30 min | 32/40 (80 %) | 33 min | 51 min | **enak** |
| 35 min | 35/40 (88 %) | 37 min | 54 min | **enak** |
| 45 min | 38/40 (95 %) | 40 min | 59 min | — |

**Meja ne vpliva na uro prihoda** — mediana razlike pri vsaki vrednosti **0 minut**. Ni izbire „hitreje" proti „manj hoje", ki bi jo rešil algoritem sam; meja odloča, **ali odgovor obstaja in koliko hodiš**.

Zato ostane. Brez nje bi bilo treba izbrati eno številko za vse: pri 45 vsi hodijo 40 minut, pri 25 četrtina ne dobi ničesar. Preverjena tudi tretja pot — iskati vedno na 45 in med predlogi vedno ponuditi tudi pot z malo hoje: **ne gre**, ker je taka pot med predlogi le v **2 primerih od 38**. Takih poti večinoma ni, razvrščanje ne more nadomestiti omejitve.

Cena večje meje = nič: iskanje pri 25 min 293 ms, pri 45 min 315 ms.

Koraki v izbirniku po tej meritvi: 10 / 15 / 25 (privzeto) / 35 / 45 in „po meri". Med 25 in „po meri" prej ni bilo ničesar, čeprav se prav tam odgovor najbolj spremeni.

## Prehoda vlaka se iz teh podatkov ne da ugotoviti (9. 9. 2026)

Drugič v dveh dneh: prikaz ob 06:53 trdil, da je LPV 2001 že bil v Ljubljani Polje; David na peronu, vlak prišel ob **07:05**. Feed:

```
06:37:28  Laze (26)             +4 min
06:42:28  Ljubljana Zalog (27)  +4 min
06:50:13  Ljubljana Polje (28)  +4 min   <- zadnja beseda o Polju
06:52:16  Ljubljana (29)         0 min
06:53:43  Ljubljana (29)        +4 min
07:03:43  Ljubljana (29)       +15 min   <- resnica, 13 minut prepozno
```

Feed Polje zamrznil na +4 **minuto po voznem redu**, ga nikoli ni popravil; popravil samo končno postajo, ob 07:03. Vrednost ni bila zastarela, ampak napačna, do 07:03 ji ni nasprotovalo nobeno opažanje.

**Pet možnih signalov, vsi izmerjeni, vsi odpovejo:**

| signal | izid |
|---|---|
| tišina feeda (popravek 8. 9.) | feed ni molčal — zadnja beseda 06:53:43 |
| potrditev postanka **po** prehodu | železnica **0,4 %** postankov (avtobusi 68 %) |
| obvestila SŽ s krajem | zadnji kraj 06:28 (Kresnice), naslednji 07:04 |
| rob okna feeda | **0 izpadov** pri 39 vožnjah v 11 min; 69/69 postankov, ki jim je vozni red mimo, ostane v oknu |
| „nerazrešena ničla" za kasnejši postanek | pred napačnimi trditvami **redkejša** (7 %) kot pred pravilnimi (24 %); natančnost 3 % |

Zadnji dve včeraj zapisani kot obetavni; obe zdaj **zaprti**, naj se ne lovita znova.

**Obseg danes:** 180 od 1 967 železniških postankov z dnevnikom (**9,2 %**) pozneje popravljenih za ≥ 5 min navzgor; prizadetih 66 od 174 voženj.

**Sklep.** Če prehoda ni mogoče zaznati, popravek ne more biti boljše zaznavanje, ampak poštenejša trditev. „Izmerjeno" za prevožen postanek pri železnici trdi opažanje, ki ga v **99,6 %** primerov nimamo.

### Kaj je popravek stal (9. 9. 2026)

„Izmerjeno" ostane samo, kjer je feed vrednost potrdil po prehodu:

| omrežje | postankov | ostane „izmerjeno" | postane „zadnji podatek" |
|---|---|---|---|
| železnica | 2 007 | **6 (0,3 %)** | 2 001 (99,7 %) |
| avtobusi | 72 076 | 50 166 (69,6 %) | 21 910 (30,4 %) |

Pri vlakih beseda skoraj povsod izgine — prav to je bila ugotovitev: tam je bila trditev o opažanju, ki ga nimamo.

### Koliko je feed zgrešil in ali bi pomagala zadnja beseda o vožnji

Ljubljana Polje, 9. 9.: feed povedal **eno samo stvar** — ob 06:50:13 prihod 06:52:00 (+4 min). Nikoli popravljeno. David na peronu: vlak prišel ob **07:05:00**. Razlika **780 s = 13 minut**.

Zadnja beseda o **vožnji** (+15 min v Ljubljani, ob 07:03:43) bi na Polju dala prihod 07:03 — **120 s** od resnice. Feed je vedel, le na Polje ni zapisal.

**Preizkušeno in NE uvedeno:** za nepotrjen postanek vzeti zadnjo besedo o vožnji s poznejšega postanka.

| različica | primerov | boljša | slabša |
|---|---|---|---|
| vedno | 1 662 | 195 | **921** |
| le če je poznejša za ≥ 5 min večja | 558 | 56 | **497** |
| ≥ 7 min | 410 | 34 | 372 |
| ≥ 10 min | 293 | 22 | 268 |

Zamuda po potnikovi postaji običajno **zraste upravičeno** → prenos nazaj škodi. **Omejitev merila**: za „resnico" vzeta končna vrednost naslednjega postanka, ta pogosto zamrznjena iz istega trenutka kot merjena → merilo nagnjeno v korist zamrznjene vrednosti. Edina prava resnica = Davidova ura, ta govori nasprotno.

**Sklep:** ugibati se ne izplača, povedati pa je treba. Kadar zadnja beseda o vožnji močno odstopa od številke za potnikovo postajo, prikaz naj pokaže **obe** — brez trditve, katera drži.

## Kaj stane štetje obiska (12. 9. 2026)

Projekt o sebi ni vedel ničesar: strežnik ni beležil zahtev, pred njim Cloudflarov tunel brez dnevnika. `obisk.py` zato šteje v pomnilniku, enkrat na minuto zapiše v bazo.

**Cena na zahtevo 0,11 ms** (mediana, p99 0,30 ms), merjeno v strežniku na 300 zahtevah: čas od konca odgovora do konca vpisa v števce. V istem teku notranje delo zahteve 1,47 ms → štetje = **7 % zahteve** pri najcenejšem predpomnjenem odgovoru.

Merjeno izven strežnika: `iz_zahteve()` 30 µs, od tega iskanje oblike poti 4,6 µs (46 vzorcev), zgoščevanje ključa 1,0 µs. Razlika do 0,11 ms = `request.headers` in `request.url`, ki ju Starlette sestavi šele ob prvi rabi.

**Primerjava „vklopljeno proti izklopljeno" na celi zahtevi ne pove nič** — prva meritev je bila takšna, kazala 2,8 ms razlike; ob ponovitvi se je obrnila:

| krog | OBISK=1 | OBISK=0 |
|---|---|---|
| 1 | 1,88 ms | 3,13 ms |
| 2 | 4,13 ms | 1,75 ms |

Mediana 1 000 zahtev z ohranjeno povezavo, brez zajema. Razlika med dvema procesoma na tem računalniku večja od merjenega učinka — sklep iz enega para bi bil za faktor 25 napačen. Velja samo meritev v procesu.

**Koliko vrstic:** `obisk_pot` = ena vrstica na (dan, pot, vrsta), ~46 vzorcev poti krat dve vrsti; `obisk_razrez` 24 ur + naprave + države; `obiskovalec` ena vrstica na obiskovalca na dan. Pri stotih obiskovalcih na dan nekaj sto vrstic dnevno, ~100 000 na leto — proti `run` (raste v milijone) nič. Obrez: `KAJROS_OBISK_KEEP_DAYS` (550 dni).

**Zakaj ne vrstica na zahtevo:** en obisk strani naredi 10–30 zahtev (lege na 10 s, zamude na 30 s, dokler zavihek odprt). Vrstica na zahtevo = stalno pisanje v isto bazo, v katero teče zajem; na malini je to kartica.

## Prva ugotovitev pregleda: hladen `/api/health` je zrasel na 20,6 s (12. 9. 2026)

Uro po objavi `/admin` na arwenu: `/api/health` p95 nad 5 s, **najdlje 20 575 ms**. Topel isti endpoint 11–14 ms (tri zaporedne meritve) → ne počasnost strežbe, ampak cena **prvega** klica po zagonu.

6. 9. 2026 v tem zapisu izmerjeno **2 683 ms** pri 5,3 mio `obs`. Baza odtlej **2,4 GB in 19,3 mio meritev** — številka zrasla **7,7-krat**, zapisana ostala stara.

Plača jo prvi vprašalec; po vsaki objavi je to **`posodobi.sh` sam**: njegov `curl` na `/api/health` je del čakanja na odgovor. Ogrevanje (`server._ogrej_health`) se sproži v istem trenutku → v najslabšem primeru oba čakata na isto ključavnico.

Ni popravljeno: ni okvara strežbe, obiskovalcu je odgovor topel razen v prvi minuti po restartu. Zapisano, ker je to **prva številka iz pregleda, ki je nihče ne bi videl** — in ker pri nadaljnji rasti baze ne bo ostala 20 s.

## Priprava na javni obisk (12. 9. 2026)

Izmerjeno in popravljeno pred prvim pravim obiskovalcem.

**Tuji izvori na vsaki strani.** `fonts.googleapis.com` na **vseh devetih** predlogah, `unpkg.com` (Leaflet) na treh. IP vsakega obiskovalca šel Googlu ob vsakem odprtju, zemljevid visel na tujem CDN-ju. Po samogostitvi na živi strani na vseh osmih javnih poteh **nič** tujih gostiteljev v HTML; ostanejo samo ploščice zemljevida.

| kaj | velikost | opomba |
|---|---|---|
| pisave (6 rezov) | 148 kB | `latin` + `latin-ext`, brez štirih drugih naborov |
| Leaflet + 5 slik | 192 kB | 1.9.4, isti kot prej |

**IBM Plex Sans = variabilna pisava, Mono ni.** Google za teže 400, 500 in 600 servira **isto datoteko** — vse tri bajt v bajt enake (md5 `b2c9031d`). Prva različica prenesla vse tri, nosila 91 kB podvojenega. Mono statičen: 400 in 600 se res razlikujeta.

**Chromium tiho zavrne variabilno pisavo iz `data:` URI.** Izmerjeno s štirimi vrsticami druga ob drugi: statični Mono se naloži, variabilni Sans pikel v piko enak serifni rezervi. Prek HTTP se naloži oboje. Isto pisavo s `file://` zavrne obakrat (CORS velja tudi tam). Slika v vseh primerih nastala s pravo velikostjo v pikah — videti kot uspeh; `naredi-ikone.sh` zato vpraša `document.fonts.check()`.

**Headless chromium z `--virtual-time-budget` ne požene service workerja.** `register()` se ne razreši nikamor; virtualni čas ne teče v njegovih nitih. Preizkus zato teče brez njega, dogodek `load` zakasnjen s počasnim odgovorom iz začasnega strežnika.

**Service worker, preverjen z ugasnjenim strežnikom:** lupina 9 datotek, `/brez-omrezja` shranjena, **`/api/` v nobenem predpomnilniku (0 vnosov)**, že obiskana stran postrežena iz predpomnilnika, nikoli obiskana dobi „brez zveze“.

**Cena endpointov na arwenu** (prek `kajros.app`, mediana dveh klicev):

| pot | hladno | toplo |
|---|---|---|
| `/api/pot` (prvi po zagonu) | **5,2 s** | 0,6–1,7 s |
| `/api/live` | 3,2 s | 0,13 s |
| `/api/connections` | 0,58 s | 0,29 s |
| `/api/stations` | 0,51 s | 0,53 s |
| `/api/stats` | 0,17 s | 0,20 s |

Petsekundni prvi klic = **enkratno ogrevanje po zagonu**, ne cena vsake poti: pet različnih parov koordinat da 0,6–1,7 s. `server._ogrej_pot()` to že drži toplo na 300 s.

**Disk na arwenu ni kajrosova težava.** 194 GB od 234 zasedenih (88 %), `/var/lib/kajros` od tega **4,3 GB**; 115 GB `/home/david`. WAL pri 273 MB, ne raste — visoka voda, ne uhajanje.

**Cloudflare `Python-urllib` ne blokira več** (200 na `/api/health`, prav tako `curl`, `python-requests`, `Wget`). Prej zapisani *Browser Integrity Check* odpadel; podrobnosti v `.claude/rules/objava.md`.

**Naš `robots.txt` na živi strani pripet za Cloudflarovim.** Njihov blok o signalih za AI spredaj, naše `Disallow: /api/` in `Sitemap:` zadaj in veljavne. Brez našega bi Cloudflare postregel samo svojega, ta o naših poteh ne ve ničesar.

## Kaj je pokazal pregled Androida pred trgovino (12. 9. 2026)

Stanje pred spremembami, izmerjeno, ne domnevano:

| kaj | izid |
|---|---|
| `./zgradi.sh izdaja` | uspe, 26 s |
| testi JVM | 39, vsi zeleni |
| izdajni APK (nepodpisan) | **61 854 B** (60 kB), 29 datotek, brez nativne kode |
| isti, podpisan | 71 822 B (70 kB) — podpis v2+v3 doda 9 968 B |
| razvojni APK | 894 259 B |
| nizi „google“ / „firebase“ / „gms“ | **0** (`aapt2 dump strings`) |
| `debuggable`, `testOnly` | ju ni |
| revizija domačega imenika | čista |

Zapisi: 28 kB (README), 50 kB (`android.md`). Obe številki sta bili resnični ob zapisu — vmes prišli budilka in njen vmesnik. Pri velikosti, merjeni ob vsaki gradnji, je zastarela številka poceni napaka; popravljeno oboje.

**Tiha napaka, ki bi jo videla šele trgovina:** `ACCESS_*_LOCATION` pomeni privzeto `uses-feature required="true"` za strojno opremo. `aapt2 dump badging`:

```
uses-implied-feature: name='android.hardware.location'
  reason='requested ACCESS_COARSE_LOCATION … ACCESS_FINE_LOCATION permission'
```

Aplikacija skrita vsaki napravi brez GPS, čeprav brez lege dela vse razen gumba „kje sem“. Popravek: tri izrecne vrstice `required="false"`.

**Dva niza razvojna, ne javna**: „Če teče na prenosniku, je ta najbrž zaprt“ in naslov `192.168.1.164:8001` kot pomoč v polju za strežnik. Potniku nista pomenila nič.

**Trgovine ni nobene — izbira po pravilih, ne po okusu.** Glavni F-Droid in IzzyOnDroid zahtevata prosto licenco za vse in gradnjo iz javnega izvora ([pravila](https://f-droid.org/docs/Inclusion_Policy/)); koda zaprta (3. 9. 2026). Google Play zaprto kodo sprejme, a zahteva račun, 25 $, preverjanje identitete in — za osebni račun, odprt po 13. 11. 2023 — **12 preizkuševalcev, ki aplikacijo držijo nameščeno 14 dni**, poleg tega AAB in od
31. 8. 2026 `targetSdk` 36. Lasten repozitorij F-Droid bi delal, a ga najde le, kdor pozna naslov.

Izbrano: **prenos s `kajros.app/android`** — deluje danes in za vsakogar. Cena: vprašanje o neznanem viru ob namestitvi; posodobitve ne ponudi nihče — zato jo poišče aplikacija sama (`/api/android/razlicica`, enkrat na dan).

**Rok:** Google od 30. 9. 2026 zahteva registriranega, preverjenega razvijalca za namestitev na certificiranih napravah (najprej Brazilija, Indonezija, Singapur, Tajska; globalno 2027). Razgooglane naprave ne zadeva, navadnega telefona bo — takrat izbrati znova.

## Stran za prenos aplikacije (12. 9. 2026)

Preverjeno na tekočem strežniku in emulatorju, ne po opisu:

| kaj | izid |
|---|---|
| `/android` z izdajo | 200, 4 915 B |
| `/android` brez izdaje | 200 — pove „prve izdaje še ni“, ne 404 |
| `/api/android/razlicica` | 200 z izdajo, **404** brez nje |
| `/prenos/kajros-0.1.apk` | 200, `application/vnd.android.package-archive`, 61 854 B |
| vrstica o posodobitvi v aplikaciji | vidna pri `koda` 2 proti nameščeni 1 |
| križec na vrstici | skrije jo in zapiše `posodobitev_preskocena=2` |

**Lastna varovalka je med preizkusom ugriznila — prav.** Vrstice ni bilo, dokler je strežnik vračal `stran: https://kajros.app/android`, aplikacija pa kazala na `http://10.0.2.2:8001` — `Nastavitve.jeNas()` tujega naslova ne sprejme niti od našega strežnika. Preizkus stekel šele s `KAJROS_BASE_URL=http://10.0.2.2:8001`. V produkciji se izvora ujemata.

**Dve številki o isti stvari na istem zaslonu.** Stran: „Različica 0.1 · 60 kB“ (izračunano iz bajtov) in dva odstavka nižje „velika okoli 64 kB“ (zapisano na roko). Razlika: `du -h` zaokroži na bloke po 4 KiB; datoteka ima **61 854 B**. Trdo zapisana številka odstranjena — velikost pove izračunana iz datoteke. Ista napaka kot povsod: številka mora pomeniti to, kar bralec misli, da pomeni.

## Prva objava aplikacije (12. 9. 2026)

`kajros-1.0.apk`, **71 822 B**, podpisan z lastnim ključem (SHA-256 potrdila `fe89…73f4`, velja do 28. 1. 2054). Preverjeno na objavljeni datoteki, ne lokalni: prenesena s `https://kajros.app/prenos/kajros-1.0.apk` ima isto vsoto kot `/api/android/razlicica` in stran, `apksigner` potrdi naš podpis, na emulatorju se namesti (`Success`) in zažene.

Podpis doda 9 968 B (61 854 → 71 822). Sheme: **v1 false, v2 true, v3 true** — v1 velja do API 23, mi od 26 naprej, zato ni potreben.

**Cloudflare predpomni 404 — ugriznilo pri prvi objavi.** Naslov APK-ja zahteval, preden je datoteka prišla na strežnik; ko je prišla, izvor vračal 200, rob še vedno 404:

```
HTTP/2 404 · age: 171 · cf-cache-status: HIT     (izvor lokalno: 200)
```

`.apk` je med končnicami, ki jih Cloudflare predpomni sam od sebe. Izteklo po ~3,5 minute (`cf-cache-status: EXPIRED` → 200). Popravek na naši strani: `_napaka_html()` vsaki napaki doda **`Cache-Control: no-store`** — noben 404 se ne more več prijeti ne na robu ne v brskalniku. Preverjeno na obeh oblikah napake (JSON in stran).

Nauk: **objavi datoteko, preden naslov kamorkoli objaviš** — en radoveden klik pred objavo zamrzne 404 za vse.

## Koliko ljudi je res na strani (15. 9. 2026)

Pregled: **104 ljudi in 94 botov** za en dan; v resnici stran rabili lastnik (telefon, računalnik, aplikacija) in morda dva ali trije. Razčlenitev iz `obiskovalec` na arwenu, do 21:06:

| zahtev na obiskovalca | „ljudi" | od tega krajše od minute |
|---|---|---|
| 1 | **79** | 79 |
| 2–3 | 9 | 5 |
| 4–10 | 8 | 6 |
| 11–100 | 5 | 1 |
| več | 3 | 0 |

* **81 od 104 ni poslalo ničesar razen strani** — nobenega `/api/health`, ki ga domača stran pokliče vedno. Po državah pri teh zahtev natanko toliko kot ogledov: US 28, TH 13, CN 11, HK 10, SG 4, KR 3.
* **RU: 147 zahtev, 0 ogledov, vse 404**, od 00:01 do 21:06, z UA brskalnika.
* 50 prvih dotikov med 00 in 02.
* **Aplikacija štela dvakrat**: pari z enakim prvim in zadnjim dotikom na sekundo (06:54:50–14:37:11, 07:04:38–10:44:33) — WebView in budilka pošiljata različen UA.

Obiskovalcev z vsaj 5 zahtevami 13; brez skenerja in parov aplikacije ~10 ključev — ujema se s tremi napravami lastnika na dveh omrežjih in nekaj drugimi. Popravek v `obisk.py` („človek je, kdor je stran pognal“).

**DuckDuckGo je kot opis `kajros.app` kazal JSON** s seznamom endpointov. Koren stregel HTML samo ob `Accept: text/html`; izmerjeno na živi strani:

| odjemalec | `Accept` | dobil |
|---|---|---|
| Googlebot | `text/html,…` | stran |
| katerikoli | brez | JSON |
| katerikoli | `*/*` | JSON |
| `facebookexternalhit` | `*/*` | JSON |
| `HEAD /` | brez | JSON |

Google zato v redu, Bing (in z njim DuckDuckGo) ne. Hkrati izmerjeno: `http://kajros.app/` in `www.kajros.app` vračata **200 z isto vsebino**, ne preusmerita — dvojnik, ki ga drži skupaj samo `rel=canonical`.

## Pristajalne strani: koliko jih sme biti (17. 9. 2026)

Zemljevid strani: **enajst naslovov**, vsak prazna lupina, polnjena v JS — iskalnik ni imel česa indeksirati. Vprašanje: koliko strani sme nastati in po čem se izberejo.

**Parov postaj preveč za vse.** Vsi pari, ki jih poveže vsaj ena vožnja v voznem redu:

| omrežje | vseh parov nad pragom voženj | nad pragom razdalje |
|---|---|---|
| železnica (≥ 4 vožnje) | 6 185 | **5 903** (≥ 3 km) |
| avtobus brez LPP (≥ 30 voženj) | 47 533 | **26 049** (≥ 6 km) |
| avtobus z mestnim LPP (≥ 20) | 83 289 | — |

Zato `NAJVEC_RELACIJ = 400` na omrežje; ostalo ostane dosegljivo in `noindex`.

**Meja razdalje ni okras.** Brez nje vrh avtobusne lestvice po prometu:

```
Ljubljana Kino Šiška → Ljubljana Tivoli     870 voženj   1,2 km
Ljubljana Slovenija avto → Ljubljana Tivoli 870 voženj   1,6 km
```

Postajališči iste ulice — nihče ne išče povezave, ker gre peš. Z mejo 6 km vrh: `Medvode → Ljubljana Šentvid` (510), `Grosuplje → Ljubljana Strelišče` (471) — relaciji, ki ju ljudje res vozijo.

**Mestni LPP relacij nima.** Brez izločitve (`agency = 'lpp'`) vrh `Ajdovščina → Konzorcij` s 5 398 vožnjami — imeni dveh postajališč v središču Ljubljane. Postajališča svoje strani obdržijo, relacije ne.

**Lego imena da najprometnejše postajališče, ne povprečje.** Prvi poskus: razdalja iz povprečja vseh postajališč z istim imenom; „Ajdovščina" (postajališče LPP + mesto 25 km stran) dala **25 km** za par sredi Ljubljane. Isto pravilo kot v kazalu postaj (`journey.station_index`).

**Cena izračuna** (razvojni računalnik, 90 dni, 1,93 mio vrstic `run`):

| korak | železnica | avtobus |
|---|---|---|
| izbor parov | 0,1 s | 4,4 s |
| vožnje izbranih relacij + zamude | 0,5 s | 3,5 s |
| zamude po postajah | 0,2 s | 2,9 s |
| **skupaj `pristanek`** | **4,8 s** | **15,1 s** |

Dvajset sekund enkrat na dan, v istem opravilu kot ostali povzetki. V zahtevi se ne računa; stran bere shranjeni povzetek, predpomnjen.

**Zamude se seštevajo kot histogram po zaokroženi minuti, ne kot seznam sekund.** Razred zamude se itak določa iz minute (`stats._razred_zamude`) → histogram enako natančen kot prikaz, ne vleče 1,9 mio vrstic v pomnilnik. Kvantil ima isto definicijo kot `stats._pct()`; test to primerja.

**Bralno transakcijo zapri pred zapisom.** Prvi zagon pri avtobusih: „database is locked": v WAL je bralec priklenjen na posnetek ob prvem branju, zajem medtem piše, zapis v isti transakciji odpove s SQLITE_BUSY_SNAPSHOT — čakanje to **ne** reši. Pri 15 s branja je vmesni zapis zajema skoraj gotov.

**Izmerjene strani** (17. 9. 2026, topel predpomnilnik):

| stran | velikost | čas |
|---|---|---|
| `/vlak/zidani-most/ljubljana` | 12,6 kB | 44 ms |
| `/postaja/celje` | 9,3 kB | 28 ms |
| `/postajalisce/bavarski-dvor` | 10,7 kB | 67 ms |
| `/postaje` | 27,0 kB | 13 ms |
| `/sitemap.xml` | 92,7 kB (1 370 naslovov) | — |

Prva različica avtobusne relacije **43 kB**: Medvode → Ljubljana Šentvid ima 108 voženj na dan, stran samo naštevanje. Zato `NAJVEC_ODHODOV = 24` in vrstica s skupnim številom.

**Prva številka, ki jo te strani povedo in je drugje ni:** relacija `Zidani Most → Ljubljana`: mediana zamude ob prihodu **15 min**, p90 35 min, **15,5 %** voženj pride v petih minutah (734 meritev, 21. 8.–17. 9. 2026). Nasprotna smer: mediana **2 min**, 67,9 % točnih.

## Pregled je pokazal: iskanje zvez na strežniku traja sekunde (19. 9. 2026)

Prvi dan nove strani `/admin` z odzivnimi časi po poteh, arwen, 19. 9. 2026 do 12:18 (od polnoči):

| pot | zahtev | povprečno | p95 | najdlje |
|---|---|---|---|---|
| `/api/connections` | 74 | 16,4 s | › 5 s | **4,0 min** |
| `/api/pot` | 121 | 7,2 s | › 5 s | 47,2 s |
| `/api/stations` | 31 | 3,4 s | › 5 s | 22,9 s |
| `/api/stations/index` | 149 | 1,7 s | › 5 s | 19,7 s |
| `/api/health` | 634 | 193 ms | ‹ 50 ms | 34,9 s |

18. 9.: `/api/connections` 3,9 s povprečno na 169 zahtevah. Meritev 4. 9. (zgoraj): 40 ms na razvojnem stroju z ~85 k meritvami; arwen jih ima 19 M. Čas = čas v aplikaciji brez omrežja, potnik ga dobi v celoti. Vzrok ni raziskan -- zapisano samo, da je, in s katero številko se bo popravek primerjal.

## Lega vlaka iz voznega reda in zamude: koliko zgreši (19. 9. 2026)

zamudil.si riše vlake, ki drsijo po progi. GPS-a za vlake nimajo ne oni ne mi. Lega = `vozni red + trenutna zamuda`, prištete vsem postankom, enakomerna vožnja med prejšnjim in naslednjim (njihov `/api/map/live`: `prev.ts`, `next.ts`, `shapeSegment`; brskalnik interpolira v `requestAnimationFrame`). Izmerjeno z isto formulo na naših podatkih: 7 454 voženj od 21. 8. do 19. 9., vzorec vsakih 30 s, skupaj 1,25 mio vzorcev. Izločenih 3 296 voženj: manj kot 80 % postankov izmerjenih ali postaja se ne projicira na traso.

Resnica = dejanski prihod in odhod na postanku (`run`), vmes enakomerno. **Isto domnevo ima tudi ocena**, zato meritev zajame samo napako zamude, ne hitrosti med postajama (speljevanje, počasni odseki). To **ni spodnja meja**: napaka hitrosti se z napako zamude lahko sešteje ali odšteje (vlak, ki zamuja in počasi spelje, je bliže oceni, ne dlje). Meritev = samo del napake; celote brez GPS-a vlaka ne izmerimo.

| način | mediana | p90 | p99 | < 500 m | < 1 km |
|---|---|---|---|---|---|
| krog na zadnji postaji (mi danes) | 2,8 km | 11,4 km | 45 km | 13 % | 22 % |
| drsenje, zamuda ob zadnjem postanku | 0 m | 2,1 km | 10,2 km | 72 % | 82 % |
| drsenje, zamuda, kot jo je feed poslal\* | 0 m | 1,7 km | 10,2 km | 74 % | 84 % |

\* delno primerjava same s sabo, glej zadnji odstavek.

Samo vzorci med vožnjo (brez postankov na postaji): mediana ostane 0 m, p90 2,4 oziroma 2,0 km. Mediana 0, ker se zamuda SŽ med dvema postankoma večinoma ne spremeni in je zapisana v celih minutah. Na pravem odseku med postajama je vlak v 90 oziroma 94 % vzorcev. Napaka raste s hitrostjo in razdaljo med postanki. Mediana in p90 za feedovo zamudo: LPV 0 / 1,2 km, LP 0 / 1,3 km, RG 0,1 / 2,2 km, IC 0,4 / 2,3 km, MV 0,6 / 4,2 km, EC 0,5 / 5,1 km, EN 1,2 / 7,0 km.

Feedova zamuda videti boljša, a meritev ni čista. V 69 % vzorcev enaka zadnji izmerjeni; ker `run` na postanku pogosto hrani kar zadnjo feedovo vrednost, se del tega primerja sam s sabo. Skripta enkratna, v repozitorij ni šla.

## Pregled 23. 9. 2026: pot ponoči, naslednji odhodi, tabla s starim načrtom

Vse na razvojni bazi (vozni red 23. 9., `PYTHONHASHSEED=0`, ker set postajališč v iskanju razreši izenačene poti po zgoščevanju).

**Nočna pot.** Pred 04:00 je `api.py` poklical `pot.isci()` za danes in včeraj ter predloga zlepil. Tri napake:

* predlog ni nosil svojega prometnega dne, podrobnosti pa so ga iskale po dnevu vprašanja: IC 350 (vožnja 453052), predlog 23. 9. ob 00:05, podrobnosti **24. 9. ob 00:05**. Ista vožnja vozi tudi danes, zato napaka ni bila videti kot napaka, ampak kot pot;
* hoja vso pot na seznamu dvakrat (center -> Moste ob 00:30: dve enaki „00:30 -> 01:00 peš");
* predpomnilniki v `pot.py` imeli eno mesto, dneva sta se izrivala: **1 673-1 839 ms** na nočno vprašanje toplo. Zdaj iskanje obeh dni teče v `isci()` skozi isto izbiro, predpomnilnik ima dve mesti: **151-154 ms**. Hladno (včerajšnji vozni red v pomnilnik) 3,5 s.

**Naslednji odhodi so preskakovali, kar odpelje v času hoje do postaje.** Iskanje je šlo „od doma minuto po vstopu", ne minuto po odhodu od doma. 60 vprašanj po Ljubljani (20 parov, 07:20 / 12:40 / 17:10, 27 z vozilom):

| | predlogov z vozilom (povprečje) | različnih prihodov | mediana iskanja |
|---|---|---|---|
| prej | 1,55 | 1,52 | 125 ms |
| popravek, 2 naslednja | 1,30 | 1,25 | 129 ms |
| popravek, 3 naslednji | **1,67** | **1,57** | 136 ms |

Prvi prihod enak v 60 od 60. Pri dveh naslednjih se je seznam skrčil: pravi naslednji odhod pri zvezah, ki se stečejo v isti avtobus, pogosto povozi predlog, ki odide pozneje in pride ob isti minuti — zato tri. Posamezni primeri niso dokaz: izenačene poti se med procesi razrešijo različno, isti par je pri drugem `PYTHONHASHSEED` vrnil drug seznam. Preskok sam: `test_naslednji_odhod_v_casu_hoje_ni_preskocen`.

Pri „biti tam do" se je isti avtobus z drugim izstopom vračal kot „prejšnja zveza" in izpadel kot dvojnik: 1,20 -> **1,68** predloga, različnih odhodov 1,15 -> 1,68, najpoznejši odhod enak v 60 od 60, čas enak (133 / 135 ms).

**Odhodna tabla Ljubljana AP: 38-40 s** (razvojna baza, 83 vrstic). Vsa cena = `stats.typical_at_stops()`: pri 166 parih je načrtovalec `run` bral po `stop_seq` in ob vsakem klicu zgradil samodejni indeks čez celo tabelo. Kriva stara statistika (`sqlite_stat1` pri 44 511 vrsticah `run`, brez `trip_voznja`). `CROSS JOIN` vsili pravi vrstni red: **40 324 -> 12 ms**, 1 675 vrstic enakih. Arwen je isti večer imel dober načrt (cela tabla 0,52-0,83 s za okno treh ur podnevi) — zaradi drugačne statistike, ne poizvedbe.

**Kar je bilo v pregledu napačno ali ni vredno popravka:**

* „Stara povezava na kazalo naslovov drži izbrisano datoteko do restarta" — ne do restarta, ampak do naslednjega zbiralnika smeti: povezava ima krožne reference, `clear()` je ne zapre, `gc.collect()` jo (preverjeno z `/proc/self/fd`). Izrecno zapiranje bi podrlo iskanje, ki na njej teče, zato ostane.
* `zamiki()` z vožnjami, ki imajo danes vrstico v `run`, namesto vseh voženj dneva: isti izid (5 829), a počasneje (1 069-1 275 ms proti 813-963 ms). Meja 32 766 vezav pri 10 679 voženj dneva trikrat daleč. Ostane.

## Vlak, ki ga je ura spravila s table (24. 9. 2026)

Prijava: vlak čaka na prejšnji postaji, feed kaže, da bi moral že odpeljati, in vlaka v aplikaciji ni več. Isto v uradni aplikaciji. Dva vzroka: en naš, en v podatkih.

**Tabla je iskala po voznem redu.** Okno = `zdaj − 10 min` po voznem redu, zato je vlak z več kot 10 min zamude izginil, preden je prišel. LPV 2008 22. 9. v Orehovi vasi +20 min: 12 min po voznem redu ga ni bilo na tabli, z oknom, razširjenim za zamudo, je bil. Železniških postankov z zamudo nad 10 min 9.–23. 9.: **24 %** (9 063 od 36 919), p90 zamude 19 min, p99 45 min. Isto napako sta imeli obe pristajalni strani (relacija je rezala po `sched_dep >= zdaj`).

Popravek: `journey.board()` gleda nazaj do `MAX_REALNA_ZAMUDA_S`, a samo po vožnjah, ki jim je zamuda danes segla čez rob okna (sito v poizvedbi), in obdrži, kar po pričakovani uri še ni mimo. Cena, razvojna baza, 23. 9., mediana petih klicev:

| tabla | prej | zdaj |
|---|---|---|
| Ljubljana 16:30 | 8,1 ms | 8,5 ms |
| Zidani Most 16:30 | 14,3 ms | 13,0 ms |
| Bavarski dvor 16:30 | 70 ms | 66–68 ms |
| Ljubljana AP 16:30 | 35–37 ms | 43 ms |

Prva različica sita je imela rezervo 20 min tudi pri avtobusih: Ljubljana AP spustila 52 vrstic skozi, na tabli ostalo 6, čas **35 → 72 ms**. Rezerva zdaj samo pri železnici.

Arwen po objavi (produkcijska baza, 24. 9. ob 11:05, mediana petih klicev `journey.board()`, stara koda iz `git archive 0435e4b` ob isti bazi):

| tabla | prej | zdaj |
|---|---|---|
| Ljubljana | 49 ms | 57 ms |
| Zidani Most | 99 ms | 100 ms |
| Bavarski dvor | 1 233 ms | 1 346–1 359 ms |
| Ljubljana AP | 325 ms | 369–372 ms |

Pri avtobusih je dodatek v poizvedbi, ne v Pythonu: sito čez tri ure nazaj Bavarskemu dvoru doda 90 ms (292 → 389 ms, vrstic 349 → 358), eno uro nazaj 30 ms pri istih vrsticah. Tri ure ostanejo, ker ima 1,45 % avtobusnih postankov (12.–24. 9.) zamudo nad uro. Vezava sita na `s.trip_id` namesto `t.trip_id` prihrani 7–26 ms. Preostala sekunda Bavarskega dvora je v Pythonu (ocena za 150 vrstic), tam že prej.

**„Odpeljal je“ = sklep iz ure.** Rekonstrukcija iz `obs` z istimi varovali kot `_LAST_MEASURED_SQL` (meja ne prehiti zadnje besede feeda, ničla po zamudi ≥ 300 s ni prehod, postanek, osvežen prej kot prejšnji, ni prehod): za vsak postanek prvi trenutek, ko prikaz trdi odhod, in končna vrednost v `run` kot resnica.

| | železnica 20. 8.–23. 9. | avtobusi 19.–21. 9. |
|---|---|---|
| trditev o odhodu | 123 280 | 87 979 |
| nepotrjenih | 118 129 (95,8 %) | 54 671 (62,1 %) |
| od teh je odpeljal ≥ 3 min pozneje | 4 874 (**4,13 %**) | 2 040 (3,73 %) |
| čas do pravega odhoda, p50 / p75 / p90 / p95 | 8,7 / 14,6 / 22,1 / 31,0 min | 6,3 / 18,5 / 43,3 / 94,7 min |

Delež zgrešenih, ki jih pokrije okno po trditvi:

| okno | železnica | avtobusi |
|---|---|---|
| 10 min | 58 % | 62 % |
| 15 min | 77 % | 72 % |
| **20 min** | **87 %** | 77 % |
| 30 min | 95 % | 85 % |

**Tišina feeda po trditvi pravilnih od napačnih ne loči.** Do naslednje besede o vožnji: pravilne p50 3,0 min, p90 7,0; napačne p50 2,5, p90 5,9. Prva sprememba poznejšega postanka: 3,0 proti 4,0 min. Praga, ki bi ju ločil, ni, zato meja ni tišina, ampak čas.

Odločitev: pri železnici vrstica ostane `NEPOTRJEN_ODHOD_S = 20 min` po pričakovanem odhodu, z besedo „po zadnjem podatku bi odpeljal ob HH:MM, potrditve ni“, in ne gre med odpeljane. Konča jo potrditev na tem ali poznejšem postanku. Avtobusi izvzeti: mestni LPP prehoda ne potrdi nikoli, tabla na Bavarskem dvoru (53 odhodov v pol ure) bi bila polna „morda“ vrstic, rep pa predolg, da bi ga kakršnokoli okno smiselno pokrilo.

V živo 24. 9. ob 10:11: MV 311 (Kranj po voznem redu 09:49, zadnji podatek z Lesc-Bleda, +21) je stal na tabli in v iskalniku z besedo. Po starem bi s table izginil ob 09:59, iskalnik pa bi ga ob 10:10 zložil med „prejšnje“. Skripta enkratna, v repozitorij ni šla.

## Aplikacija in prenosi v pregledu (24. 9. 2026)

Vprašanje: koliko prenosov aplikacije, koliko ljudi jo uporablja na dan. Pregled ni znal odgovoriti — razrez naprave šteje zahteve in oglede, ne ljudi; prenosi = ena vrstica `/prenos/{path}` skupaj z `razlicica.json`.

**Števec prenosov na strežniku je bil brez pomena.** `curl -sI` na `kajros.app/prenos/kajros-1.2.apk`: `cf-cache-status: HIT`, `age: 6678`, `cache-control: max-age=14400` — Cloudflare streže APK (98 kB) s svojega roba; do arwena pride le prenos, ki zgreši predpomnilnik. `no-cache` ne reši: `/static/base.css` ga pošilja, na robu izmerjeno `MISS`, nato `REVALIDATED` — Cloudflare hrani, pri nas le preverja `ETag`. Zato `/prenos` zdaj pošilja `no-store`.

Do arwena prišlo doslej (`obisk_pot`, zahtev / od tega ljudi):

| dan | `/android` | `/prenos/{path}` | `/api/android/razlicica` | ogledov v aplikaciji |
|---|---|---|---|---|
| 18. 9. | 50 / 30 | 29 / 9 | 13 | 24 |
| 19. 9. | 116 / 76 | 58 / 15 | 14 | 21 |
| 20. 9. | 88 / 56 | 39 / 10 | 17 | 21 |
| 21. 9. | 90 / 70 | 52 / 11 | 21 | 35 |
| 22. 9. | 76 / 59 | 40 / 11 | 7 | 34 |
| 23. 9. | 41 / 29 | 33 / 9 | 16 | 26 |

Preverjanje posodobitve: enkrat na 24 ur na napravo → stolpec `razlicica` = spodnja meja naprav, ki so aplikacijo ta dan odprle (5–21 na dan). Števila ljudi z aplikacijo za nazaj ni in ne bo: vrstica obiskovalca ni vedela, od kod je prišel.

Šteje se od zdaj (`obisk.py`): v `obiskovalec` stolpca `aplikacija` (različica) in `okno` (zahteve iz WebView — pripomoček in budilka ne štejeta kot odprta aplikacija); v `obisk_razrez` razreza `prenos` (po datoteki) in `prenos_iz` (`stran` | `aplikacija`, loči ga `?iz=aplikacija` na naslovu, ki ga aplikacija dobi iz `/api/android/razlicica`). Prenos se šteje brez dokaza JS, ker `/android` JS nima.

Po objavi (arwen, 24. 9. ob 11:40) dva zaporedna `curl -sI` na APK: `cache-control: no-store`, `cf-cache-status: BYPASS` obakrat — vsak prenos zdaj pride do strežnika. Migracija dodala stolpca na produkcijski bazi, `obisk_aplikacija_od = 2026-09-24`; današnji dan delen (do 11:40 aplikacija ni bila ločena).

## Deljenje lege: ali kandidati najdejo pravo vozilo (25. 9. 2026)

Potnik vozila ne vpisuje; strežnik iz njegove lege predlaga do pet voženj (`deljenje.kandidati`). Merjeno na razvojni bazi, dopoldne ob delavniku.

**Avtobusi, prava lega:** GPS lega avtobusa iz `vehicle_now` (sveža, vožnja že teče) podtaknjena kot potnikova, brez smeri. Na **200** vozilih prava vožnja **prva v 180 (90 %)**, med petimi v 184 (92 %). Na dveh drugih vzorcih po 150: prva v 141 in 130 (94 / 87 %) — razpon je med vzorci, ne napaka enega. Zgrešeni skoraj vsi: vozila z GPS kilometre od lastne trase (feed jih pripisal napačni vožnji) — tudi potnik takega vozila ne bi mogel potrditi.

Polmer iskanja postaj pri avtobusih: samo 2,5 km zgrešil 14 od 150 (medkrajevni avtobus daleč od postajališča), 6 km 7. Zdaj dva koraka — 2,5 km, 6 km samo kadar blizu ni nobenega avtobusa: na istem vzorcu 200 prva 177 proti 174 pri stalnih 6 km, med petimi 184 obakrat.

**Hitrost.** Prva objava na arwenu: Ljubljana **17 s hladno, 1,75 s toplo** — za vsako od ~600 voženj v okolici naloženi postanki in zadnja zamuda, preden je bilo znano, ali vožnja gre mimo. Zdaj prvo sito po trasi (trase si vožnje delijo); postanki, zamuda, GPS samo za preživele. Razvojni računalnik: Ljubljana 0,54 s hladno / 0,09 s toplo, Maribor 0,21 / 0,06, Postojna 0,05 / 0,05. Pomnilnik: vse vožnje v okolici ure (1 512, 941 tras) = 48,5 MB.

Arwen ~9× počasnejši od razvojnega računalnika. Po treh popravkih (sito po trasi, projekcija preskoči oddaljene odseke, postanki enkrat na linijo — 493 voženj v Ljubljani ima 291 različnih zaporedij): Ljubljana **0,65 s toplo**, 4 s hladno takoj po ponovnem zagonu, Maribor 2,4 s hladno, Postojna 0,4 s, Celje 0,6 s (merjeno od zunaj, skozi tunel; `/api/health` 0,15 s). Hladno enkrat na območje po vsakem zagonu ali uvozu voznega reda.

Vozila v `vehicle_now`, katerih vožnja se **še ni začela** (tudi 26 min pred odhodom, do 5 km od trase), v kandidatih niso — potnik v njih ne sedi.

**Vlaki, sintetično:** vlak nima GPS-a → lega izračunana iz voznega reda in feedove zamude, 17 m odmika. Brez smeri, 25 živih vlakov:

| vlak zamuja glede na feed | prvi | med petimi |
|---|---|---|
| natanko kot feed | 21 | 24 |
| 10 min več | 14 | 24 |
| 25 min več | 11 | 22 |

Ko zamuja več, kot feed ve (prav primer, zaradi katerega deljenje obstaja), se v času bolj ujema naslednji vlak iste proge — zato izbira ostane potnikova. Smer iz dveh leg izloči vlake v nasprotni smeri; primer A8425 pri Strunjanu: pred smerjo med petimi en „Koper – Piran“, po njej nobeden.

**Android v ozadju** (emulator, API 35): po potrditvi, telefon v ozadju, zaslon ugasnjen: storitev v 40 s poslala 8 točk (lega na 5 s, pošiljanje na 10 s). Brskalnik tega ne zmore.

## Avtobusi brez zamude: zamenjani id-ji in feed brez novega voznega reda (25. 9. 2026)

Prijava: LPP 25 z Novega Polja proti Bavarskemu dvoru ob 11:11 in 11:36 pisal „brez podatka“ — ne zamude ne običajne zamude. Dva vzroka, nepovezana.

**1. Zgodovina se je ob novem id-ju pretrgala.** 22. 9. 247 voženj dobilo nov id (192 LPP v IJPP, 52 Nomago, 3 Arriva). Zajem jih od takrat prevaja (`zamenjava`), zgodovina pa šla samo po `trip_id`: vožnja 11:11 (478946) pod novim id-jem 2 dneva meritev, pod starim (452527) 15. Običajna zamuda rabi 3 → je ni bilo; model se učil iz dveh dni.

Po popravku (`db.PREDNIKI_SQL`, meritve stare vožnje prevedene na postanke in vozni red nove), na kopiji arwena 25. 9.:

| | prej | potem |
|---|---|---|
| LPP 25 na Novem Polju, odhodov z običajno zamudo | 1 od 21 | 21 od 21 |
| postanki zamenjanih voženj danes z običajno zamudo | 3 303 od 4 987 | 4 772 od 4 987 |
| tabla Novo Polje / Bavarski dvor / Ljubljana AP | 39 / 445 / 140 ms | 71 / 478 / 146 ms |

Prvi osnutek bral `run` stare vožnje po vseh dneh za vsak postanek posebej (ključ: vožnja, dan, postanek): 9,8 ms na klic, `predict` 1,3 → 11,5 ms. Z branjem `run` enkrat (`PREDNIKI_VOZNJE_SQL`): 4,7 ms, `predict` 7,0 ms — toliko kot vožnja z 17 dnevi lastne zgodovine. Dan 22. 9. za te vožnje izgubljen: feed jih javljal pod starimi id-ji, prevoda še ni bilo.

**2. Feed zamud ne nosi voženj z veljavnostjo od 21. 9.** Ni povezano s prvim — druge vožnje (Nomago, Arriva), brez novega id-ja, a nov vozni red z novim obdobjem veljavnosti.

| prevoznik | obdobje od | voženj 25. 9. | odpeljalo do 11:00 | z meritvijo |
|---|---|---|---|---|
| Nomago | 1. 9. | 404 | 173 | 161 |
| Nomago | 7. 9. | 68 | 23 | 23 |
| Nomago | **21. 9.** | **427** | **164** | **0** |
| Arriva | 7. 9. | 313 | 130 | 130 |
| Arriva | 14. 9. | 38 | 14 | 14 |
| Arriva | **21. 9.** | **51** | **24** | **0** |

Enako vsak dan od 21. 9.: Nomago 423–432 voženj/dan brez ene meritve (razen treh zamenjanih), Arriva 51. To = 11 % Nomagovih voženj, 40 linij (N0091, N0112, N0152, N0158, N0324, N0330, N0334 …) in 5 Arrivinih (A2240, A2265, A2280, A6360, A6472). Železnica ni prizadeta (vlaki z obdobjem od 7. 9.: 3 od 4 odpeljanih z meritvijo).

V `vehicle_positions` ta vozila **so**, pod novimi id-ji: ob 11:16 22 vozil (Nomago 18, Arriva 4) na vožnjah z veljavnostjo od 21. 9., nobeno v `trip_updates`. Zamuda na postanek potrebuje vozni red, lega ne → najverjetnejša razlaga: derp.si za `trip_updates` ima vozni red izpred 21. 9. Števec `rt_neznanih` tega ne vidi: šteje id-je v feedu, ki jih mi ne poznamo, ne obratno.

**Števec, ki bi to ujel 21. 9.:** `collector.lega_brez_zamude` ob vsakem branju zamud prešteje vozila s svežo lego na vožnji, ki je po voznem redu na poti vsaj 10 min, in koliko od njih danes nima nobene vrstice v `run`. Pregled za skrbnika kaže po prevozniku. Ob 11:50: na vožnjah, ki jih feed nosi, 0 od 295 (LPP mestni 51, Arriva 106, Nomago 102 …); na vožnjah z veljavnostjo od 21. 9. 10 od 10 (Nomago 8, Arriva 2). Meja 10 min: vozilo na izhodišču ali tik po odhodu še nima prvega sporočila.

## Zamuda iz lege za vožnje, ki jih feed zamud izpušča (25. 9. 2026)

Nadaljevanje zgoraj: ~480 voženj/dan ima lego, zamude ne. `iz_lege.py` jo izmeri sam: lega na traso vožnje (`deljenje.Voznja`), prehod postanka med dvema legama, največ 60 s narazen, zapis v `run`/`obs` z `feed_ts` = časom lege po prehodu.

**Meritev s kodo, ki je šla v zajem**, na vožnjah, ki imajo tudi feed: 24 min surovih leg IJPP (11:40–12:04, 19 594 leg na vožnjah iz voznega reda), predvajanih skozi `iz_lege.opazuj` v prazno bazo s pripeto živo bazo samo za branje.

| prevoznik | prehodov | mediana razlike | mediana \|razlike\| | p90 | v 60 s | v 120 s |
|---|---|---|---|---|---|---|
| Arriva | 688 | −4 s | 5 s | 52 s | 92,3 % | 96,8 % |
| Nomago | 558 | −3 s | 4 s | 56 s | 90,3 % | 95,7 % |
| LPP primestni | 201 | −10 s | 10 s | 39 s | 93,5 % | 96,5 % |
| AP Murska Sobota | 104 | −4 s | 4 s | 60 s | 89,4 % | 98,1 % |
| **vse** | **1 551** | **−4 s** | **5 s** | **54 s** | **91,6 %** | **96,5 %** |

Na vožnjah z veljavnostjo od 21. 9. v istem času 62 prehodov (Nomago 57, Arriva 5), ki jih feed ni imel. Cena: mediana 0,13 ms na lego, p90 0,31 ms; prvi klic za vožnjo zgradi traso (do 50 ms). Številke s `deljenje.py` v stanju 6fefe4e (lega postankov enkrat na linijo). V zajemu gre skozi samo lega vožnje, ki je feed zamud 5 min ni omenil (~25 vozil).

Trije popravki na poti, vsak izmerjen na prvem vzorcu (528 prehodov):

* **Prva lega samo v oknu voznega reda** (od 60 min zamude do 20 min prehitevanja). Brez tega se krožna linija ujela na napačen krak: A-vožnja z 48 postanki dala +5 183 s proti feedovim +361.
* **Meja hitrosti 30 m/s vzdolž trase.** Ena lega skočila čez osem postajališč v 13 s, zamude od −202 do −1 273 s.
* **Izhodišča ne merimo.** Vozilo pred odhodom kroži po postajališču; „prehod“ bil 595–667 s prezgodaj.

Skupaj p90 759 s → 54 s, v 60 s 75 % → 92 %.

Ostanek (4 % nad 2 min) ni razložen. V enem primeru (N0124, vožnja 469707) feed na dveh zaporednih postankih isto vrednost +853 s, lega +257 in +253 s — diši po zamrznjeni napovedi feeda, ne po napaki lege. Izmerjeno ni.

**Števec v pregledu zdaj trojka** [ne v feedu, brez vsake zamude, vozil]: iz lege zapolnjena vožnja ni več „brez zamude“, napaka vira ostane vidna.

## Zajemna nit je jedla pol jedra (25. 9. 2026)

Opazil drugi agent: na arwenu nit zajema porabila ~14 s CPU v 30 s, proces po systemd 85 % jedra v 24 h (22.–23. 9. okoli 50 %). Zahteve si z njo delijo GIL → počasna stran (`/api/overview/bus` 4,8 s, `/api/live` 4,1 s, izmerjeno ob 10:55).

Zanka zajema, kot jo teče `server._worker`, na kopiji baze arwena, 240 s, CPU po opravilih (`time.process_time`):

| opravilo | prej | potem |
|---|---|---|
| ogrevanje živih in pregledov (po vsakem zajemu) | 82,6 s (10,3 s na klic) | 34,3 s (4,3 s) |
| lege + `iz_lege` | 13,3 s | 7,7 s |
| zamude IJPP | 11,0 s | 6,9 s |
| LPP | 11,2 s | 4,3 s |
| senca napovedi | 6,2 s | 6,2 s |
| obvestila | 2,8 s | 0,4 s |
| **skupaj** | **127 s = 53 % jedra** | **60 s = 25 %** |

Trije vzroki:

* **Predpomnilnik statike v `collector._cached` ni predpomnil.** Vsak nov ključ izpraznil vse, ključi trije (okna voženj, koledar, zamenjave) → vse gradilo ob vsakem klicu: 62 gradenj oken, 20 koledarja, 58 zamenjav v 240 s.
* **Pregleda sta `_live()` računala sama**, mimo predpomnilnika `/api/live`. Po vsakem zajemu se `_live("avtobus")` (3,1 s) računal dvakrat.
* **`_LIVE_SQL` bral `run` celega dne** po `run_date`, šele nato ožil na vožnje v oknu. Obrnjeno (vožnje → `run` po ključu): železnica 0,68 → 0,14 s, avtobusi 3,04 → 2,67 s, izid enak vrstico za vrstico v vseh šestih kombinacijah omrežja in noči.

Ostane `_live("avtobus")` z 2,7 s na 30 s: okenske funkcije tečejo čez 92 160 vrstic `run`, ker okno voženj sega 6 h nazaj (`MAX_LIVE_DELAY_S`), žive pa 403 od 407 v zadnji uri po voznorednem koncu. Zožiti okno bi spremenilo pomen (vožnja s feedom, tihim več kot uro) — ni narejeno.

## Viri brezavta.si in tir s table SŽ (25. 9. 2026)

brezavta.si = stran DERP (isti ljudje kot `rt.gtfs.derp.si`); zaledje `api.beta.brezavta.si` (FastAPI, `/openapi.json` javen), pod njim OTP. Kar imajo in kajros nima, večinoma ne pride od njih, ampak iz virov, ki jih uporabljajo. Merjeno 25. 9. 2026 med 12:50 in 13:05 (30 vzorcev po 30 s) in ob 16:45–17:05.

**Lega vlakov SŽ (`api.modra.ninja/sz/lokacije`) = izračunana, ne GPS.** Pokritost popolna (764 od 764 vlakov, ki bi po voznem redu morali voziti), točka leži na progi (odmik od naše trase mediana 4 m, p90 15 m) — a to dokaže le, da jo vir postavi tja sam:

* vlaki na postaji imajo **bitno enake** koordinate: 3295, 2275 in 3123 v Ljubljani na `14.5102706481,46.0585694286`, 601, 312 in 4212 na isti točki na Jesenicah — točka postaje, ne sprejemnik;
* „preslikana“ različica (`/lokacije`) od surove (`/lokacije_raw`) oddaljena mediano 391 m (p90 699 m), obe na progi;
* SŽ sam pravi „približne lokacije“ (potniski.sz.si/info).

Koliko zgreši, ni izmerjeno: rabili bi GPS z vlaka (deljenje lege).

**Tir s table SŽ.** Tabla `…/sz/postaje/{st}/prihodi_raw` na 20 postajah:

| | |
|---|---|
| postaje s tirom pri vseh vlakih | 14 (Ljubljana 119/119, Maribor 91/92, Celje, Zidani Most, Pragersko, Divača, Koper, Sežana, Grosuplje, Postojna, Litija, Ptuj, Murska Sobota, Nova Gorica) |
| postaje brez tira | 6 (Jesenice, Novo mesto, Kranj, Dobova, Trbovlje, Škofja Loka) |
| vlakov voznega reda na tabli | 723 od 755 (96 %); manjkajo mednarodni 1472, 210, 211, 79, 350 |
| odziv | 13–17 s ob zgrešenem predpomnilniku, 0,07 s ob zadetku (60 s) |
| brezavta.si proti tabli (Ljubljana) | 8 od 121 vlakov drug tir — oni kažejo „običajnega“ |

Prvi zagon zajema (16:56): vseh 266 naših postaj se preslika na ime pri SŽ; 17 tabel v 6 minutah = **~21 s na postajo** s premorom. Vseh postaj na deset minut ena nit ne zmore (1 600 tabel na uro proti ~180), zato razmik po prometu: velike vsakih 10 min, majhne najdlje 2 h (`peroni._RAZMIK_SQL`).

**Marprom (mestni avtobusi Maribor).** GTFS `marprom_official`: 1 136 voženj na petek, veljaven do 24. 6. 2027. RT na `rt.gtfs.derp.si/sources/marprom`: 30 od 30 odzivov, glava stara največ 4 s, vsi `trip_id` v GTFS. A zamudo nosi **564 od 772 (73 %)** voženj, ki bi po voznem redu morale voziti, in 37 od 38 vozil v legah nima vožnje. Zamude = napoved po postankih (768 voženj z različnimi, 249 z isto). Kranj 5 voženj, Murska Sobota 3, Celje prazno.

**Cene** (karte.brezavta.si, prodajalna, ne API): določa jih tarifni razred, za vlak in avtobus isti — Ljubljana–Maribor R26 14,0 €, Koper R21 11,5 €, Celje R15 8,5 €, Zidani Most R13 7,5 €, Kranj R05 3,5 € (avtobus do Kranja R06 4,0 €). En par na poizvedbo, 1,5 s.

**Oprema postaj** (`/sz/postaje_oprema`, infrastruktura.sz.si): pokrije vseh 266 naših postaj, a nosi samo dostopnost po tirih. **Sestave vlaka ni** (`/sz/train_details` vrača 500), vozila pri brezavta.si brez modela.

## Krčenje zapisov za Claude (26. 9. 2026)

Vsi `.md`, ki jih bere samo Claude (CLAUDE.md, `.claude/rules/`, `docs/` razen
`pismo-podatki.md`, README-ji, spomin), stisnjeni s caveman-compress: odstavki
v eno vrstico, brez mašil in veznikov, dejstva ista. Vsak kos je preveril drug
klic („kaj manjka ali ima drug pomen“) in manjkajoče vrnil; naslovi, bloki
kode in inline koda so ostali bitno enaki.

| | pred | po | manj |
|---|---|---|---|
| CLAUDE.md (vsaka seja) | 18 322 | 16 602 | 9,4 % |
| `.claude/rules/` (po poti) | 226 762 | 213 671 | 5,8 % |
| `docs/MERITVE.md` | 136 440 | 129 131 | 5,4 % |
| ostali zapisi | 81 942 | 77 580 | 5,3 % |
| spomin | 38 243 | 37 070 | 3,1 % |

Znakov, ne žetonov. Malo, ker so bili zapisi že pisani na kratko in slovenščina
nima členov, ki jih caveman sicer reže; večji del CLAUDE.md je šel s selitvijo
podvojenega v pravila (senčno merjenje, žeton za `/admin`, pristajalne strani).

**`claude --print` s privzetim sistemskim pozivom stane 25,7 k vhodnih žetonov na
klic, z `--system-prompt … --tools ""` 0,8 k** (izmerjeno na enem vprašanju).
Prvi tek krčenja je šel brez tega, dvanajst klicev vzporedno, in izčrpal limit;
drugi (Sonnet, 174 klicev) je stal 1,2 M vhodnih in 0,27 M izhodnih žetonov.

## Vlaki brez derp.si, zamude z zemljevida SŽ (28. 9. 2026)

DUJPP je ob 00:00 UTC objavil vozni red s 783 progami SŽ in 0 vožnjami; uvoz
na arwenu ob 04:22 je pobrisal vozni red vseh 726 vlakov (obnovljen iz kopije
ob 03:33, varovalka `gtfs.izginuli_prevozniki` od istega dne). derp.si ob 08:46:
`trip_updates` 544 vnosov, `vehicle_positions` 539, vlakov 0 -- tudi pod id-ji
iz zipa 27. 9. (vseh 791). Surovi vir SŽ pri derp.si 0 vnosov, `SZ-DELAY` 0.

Zemljevid SŽ (`api.modra.ninja/sz/lokacije`) ob 08:50: 41 vlakov, med njimi
vseh 31, ki so po voznem redu vozili; ostalih 10 zamujenih čez konec voznega
reda. Zamuda mediana 3 min, 19 nad 5 min, največ 50 (LP 4203). Odziv 0,08 s,
`/lokacije_raw` 8,9 s.

Pripenjanje (`zamude_sz.pripni`), 17 branj 08:59--09:08: 574 od 647 vrstic
vlakov; 42 z odhodom v prihodnosti, 31 brez naslednje postaje, drugih 0.
Lokalni strežnik po zagonu: 38 vlakov, 33 samo SŽ, 5 nepripetih; IC 503 na
tabli Ljubljana +26 min, prej „brez podatka“.
