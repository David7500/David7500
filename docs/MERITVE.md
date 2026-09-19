# Izmerjeno

Številke, ki niso pravilo, ampak stanje: koliko je zajetega, koliko stane,
kako hitro teče. Se starajo — ob vsaki spremembi popravi datum.

## Hitrost odgovorov (4. 9. 2026)

Merjeno na razvojnem računalniku pri 832 000 vrsticah `run` in 6,3 mio `obs`,
z ogretim predpomnilnikom:

| endpoint | prej | zdaj | kaj je bilo narobe |
|---|---|---|---|
| `/api/health` | 1223 ms | **80 ms** | `COUNT(*)` čez `obs` in razrez `run JOIN trip` ob vsakem klicu; stran ga kliče vsakih 30 s |
| `/api/live?network=zeleznica` | 245 ms | **5 ms** | predpomnilnik se razveljavi ob vsakem zajemu, torej z isto periodo, kot ga zemljevid vprašuje |
| `/api/departures?station=…` | 145 ms | **15 ms** | `MIN/MAX(stop_seq) GROUP BY trip_id` čez 403 208 vrstic `sched` ob vsaki zahtevi |
| `/api/connections` | 87 ms | 40 ms | — (najtežja poizvedba je 25 ms, prostora ni veliko) |
| `/api/stations/search` | 53 ms | 56 ms | — |

Vzorec vseh treh popravkov je isti: **agregat, ki se med zahtevami ne
spremeni, se ne sme računati v zahtevi.** Dvakrat je odgovor statika voznega
reda (shrani se ob uvozu), enkrat pa delo, ki ga lahko opravi zajemna nit
vnaprej.

## Pokritost zajema (4. 9. 2026)

Koliko voženj iz voznega reda dejansko vidimo v realnem času:

| kaj | v voznem redu | zajetih | pokritost |
|---|---|---|---|
| pravi vlaki | 601 | 598 | **99,5 %** |
| nadomestni prevoz SŽ (`BUS …`) | 53 | 0 | **0 %** |
| avtobusi | 10 007 | 9 799 | 97,9 % |

Merjeno na 3. 9. 2026 in ponovljivo na 1.–3. 9. (nihanje pod odstotkom).
**Skupna železniška pokritost je videti kot 91 % samo zato, ker nadomestne
prevoze šteje zraven.** Teh je 56 v voznem redu in imajo v petnajstih dneh
zajema **nič** meritev — feed zanje ne poroča.

Avtobusi so 31. 8. pri 63,1 %, ker je bil zajem takrat še v vzponu; od 1. 9.
naprej so nad 95 %.

## Model po omrežjih (4. 9. 2026)

`kajros backtest`, izpuščanje enega dne. Železnica 15 dni in **521 781**
nalog, avtobusi 7 dni in **6 004 849**.

| model | železnica MAE | v 5 min | avtobusi MAE | v 5 min |
|---|---|---|---|---|
| **rezerva+razred (v uporabi)** | **2,06** | 90,0 % | 2,98 | 93,0 % |
| združen | 2,07 | 89,6 % | **2,85** | **93,6 %** |
| odsek+razred | 2,36 | 87,5 % | 2,89 | 93,4 % |
| rezerva+mediana | **2,00** | **90,5 %** | 3,16 | 92,4 % |
| prenos | 3,04 | 82,3 % | 3,38 | 91,0 % |

Zgodovino ima 88 % železniških voženj (82 % vsaj tri dni) in 77 % avtobusnih
(47 %). Razlaga in kaj iz tega sledi: `.claude/rules/model.md`.

## Avtobusni model (19. 9. 2026)

Kopija baze z arwena 19. 9. ob 00:20 (`VACUUM INTO`; `.backup` se med
zajemom vrti v krogu). Avtobusnih vrstic `run` **3,25 mio** v 21 dneh
(29. 8.–18. 9.), dnevnik `obs` 21,7 mio (4.–19. 9.), senca 271 095
razrešenih avtobusnih napovedi (3.–18. 9.). Pravila, ki so iz tega nastala,
in kaj ni pomagalo: `.claude/rules/model.md`, „Avtobusni model“.

**Mestni LPP ni imel zgodovine.** Od 603 140 njegovih vrstic `run` jih je
489 k (81 %) na nagrobnikih — vožnjah prejšnjih uvozov brez `sched` — ker ima
LPP za vsak datum svoj `trip_id`. Srednji del id-ja (`dan|vožnja|vzorec`) se
ponovi 22-krat v 31 dneh in preživi nov zip. S ključem brez dneva ima LPP 12
dni zgodovine namesto 2; v senci je bilo 0 % napovedi LPP z vsaj tremi dnevi.

**Tri merila**, vsa z učenjem **samo na preteklih dneh** (ne izpuščanje enega):

| merilo | kaj | nalog |
|---|---|---|
| senca, ponovljena | kar je prikaz posnel v živo; trenutna in prevoznikova vrednost sta takratni | 217 784 (8.–18. 9.) |
| rekonstrukcija iz `obs` | vse vožnje 15 min pred postankom; kaj je feed vedel ob T, pravilo `_LAST_MEASURED_SQL` | 2,3 mio, od tega 40,5 % pred odhodom |
| simulacija iz `run` | isto iz končnih vrednosti — **pušča** pri „še ni odpeljal“, rabljena samo za vozilo na poti | 3,0 mio |

Ponovitev sence z modelom, prepisanim v pandas, se s tem, kar je strežnik res
zapisal, ujema na dve decimalki (2,97 proti 2,97); nova koda skozi pravi
`stats.predict` in pandas različica se ujemata v 99,4 % vrstic (18. 9.).

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

Pred odhodom (rekonstrukcija iz `obs`) je razlika pri LPP večja: 1 → 8,77 in
2,07 min, 0,5 → 9,81 in 2,17. Pri primestnem 1118 je tam najboljše 0.

**Vožnja brez meritve** (rekonstrukcija, 605 334 pogledov, ko ima prevoznik vrednost):

| | delež | prevoznik | običajno | običajno + presežek |
|---|---|---|---|---|
| prevoznik ≤ običajno | 69 % | 3,98 | **2,67** | 2,67 |
| prevoznik > običajno | 15 % | 4,78 | 4,67 | **4,40** |
| brez 3 dni zgodovine | 16 % | **2,83** | (vozni red 3,25) | |

72,9 % prevoznikovih vrednosti pred odhodom je natanko 0 (LPP 88 %, IJPP
41–67 %).

**Dnevni sunki so v repu, ne v sredini.** Odklon od lastne mediane vožnje,
povprečje po dnevu: 11. 9. (petek, rahel dež) LPP +9,8 min, Arriva +7,3,
Nomago +2,1; mediana istih odklonov pa 0,5 / 0,3 / 0,05. 10. 9. je deževalo
v 97 % ur (4,4 mm/h povprečno) in LPP je bil +2,0. Petek je povprečno najslabši
dan (Arriva +3,0, LPP +4,5 min nad mediano vožnje), popoldne 14–18 h najslabši
del dneva (LPP do +4,3). Napovedi to ne premakne, ker je mediana okoli nič —
glej `.claude/rules/model.md`.

**Cena na arwenu** (po objavi, 19. 9.): odhodna tabla Bavarski dvor, 135
odhodov, **590 ms**, od tega „običajno“ 100 ms na klic (prej 15–18 ms) —
dodatnih 920 vrstic zgodovine za 112 mestnih odhodov, ki je prej niso imeli.
Tabla ga kliče dvakrat (še za včerajšnji prometni dan). Glavna poizvedba table
je ~340 ms in je nova koda ne spremeni. Obhod sence v konici: 0,34 s lokalno.

**Prezgodnji odhod z izhodišča** (senca, 8.–18. 9.). Kadar je zadnji izmerjeni
postanek izhodišče vožnje (11,7 % pogledov; LPP nikoli, AP MS 21 %) in je
vozilo tam prezgodnje, je resnica na cilju v mediani −0,02 min, naša napoved
pa je nosila −4,6 min naprej:

| izrez | n | prej | izhodišče ≥ 0 |
|---|---|---|---|
| izhodišče, prezgodaj | 7 799 | 6,24 · 65,8 % | **2,75 · 90,5 %** |
| izhodišče, vse | 27 462 | 4,11 · 83,2 % | **3,10 · 90,4 %** |
| vse | 217 784 | 2,62 · 91,5 % | **2,49 · 92,4 %** |

Na drugih postankih je pri prezgodnjem vozilu (≤ −3 min) sedanji model
najboljši: 3,06 proti 3,49 za „običajno“ in 4,23 za odrez na nič.

**Končni model na senci po prevoznikih** (14.–18. 9., prej → zdaj):
1118 2,20 → 1,87 · Nomago 2,46 → 2,17 · AP MS 2,56 → 2,24 · Arriva
3,42 → 2,86 · mestni LPP 1,84 → 1,79 min. Backtest (8 dni): 2,13 → 2,12 min,
v 5 min 94,9 → 95,1 %.

**Gradientni strop** (LightGBM, cilj L1, učenje 6.–13., test 14.–18. 9.):
senca 2,43 → 2,20 min, strošek 6,38 → **6,50**; simulacija na poti 2,68 →
2,42. Pred odhodom 2,89 → 2,87 (brez LPP nič). Najpomembnejše: odklon od
običajnega na izhodišču (19,6 % dobička), prevoznikov presežek (14,1 %),
naša ocena, ura. Dež 1,7–2,3 %, dan v tednu 1,1–2,9 %.

## Razdalje med postajami

`stop_times.txt` nima `shape_dist_traveled`. Postaje projiciramo na polilinijo
iz `shapes.txt`, razlika kumulativnih razdalj je dolžina odseka, mediana čez
vse vlake.

**4. 9. 2026:** 271 postaj, 389 odsekov (268 elementarnih), **1140,8 km**
elementarne mreže. Slovensko železniško omrežje meri ~1209 km, del pa je brez
potniškega prometa — izračun je torej v pravem redu velikosti.

**Prej je tu pisalo 267 postaj, 275 elementarnih in 1253,8 km.** Številka se z
regeneracijo voznega reda premakne in nova je resničnosti celo bližja od
stare. Kdor jo navaja, naj jo pomeri znova; kdor jo primerja s prejšnjo, naj
ve, da se je spremenil vozni red, ne mreža.

`elementary = 0` so "preskoki" hitrih vlakov čez vmesne postaje: za risanje
mreže filtriraj `elementary = 1`, za hitrosti uporabi odsek, ki ustreza
dejanskemu paru zaporednih postankov danega vlaka.

**To niso uradne km-lege**, ampak dolžine GTFS shapeov — odstopanje ~2–4 %
(Zidani Most–Ljubljana da 63,63 km proti uradnim ~61 km).

## Poraba

| | |
|---|---|
| Uvoz GTFS | 23 s, vrh 54 MB (pretočno branje `shapes.txt`; prej 269 MB) |
| Strežnik ob zagonu | 57–60 MB RSS |
| Po prvem zajemu | 74 MB RSS |
| Osvežitev v istem procesu | vrh 89 MB, ostane 85 MB → zato `KAJROS_REFRESH=off` privzeto |

## Hitrost pri velikih podatkih

Izmerjeno na **sintetični bazi z letom zajema vseh prevoznikov**: 52 122 000
vrstic `run`, 365 dni, 5,9 GB (generator je v scratchpadu, ne v repozitoriju).
To je stanje, do katerega bo baza prišla sama; pri devetih dneh je vse hitro
in ne pove nič.

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

Trije vzorci, ki so bili vsak po enkrat vzrok počasnosti in se v novi kodi
ne smejo ponoviti:

1. **Filtriraj znotraj poizvedbe, ne za njo.** Okenska funkcija čez oba
   omrežja, filter `t.network` šele za njo: železniško vprašanje (700 000
   vrstic) plača avtobusne (12 M). Bilo je dvakrat — v `_LIVE_SQL` in v
   `stats.breakdowns` (38 s).
2. **Koreliran `EXISTS` teče enkrat na vrstico.** Ista pogoja kot
   nekorelirana podpoizvedba: 392 ms → 65 ms.
3. **Ponavljajoče se opravilo naslednji čas računa od tika, ne od „zdaj".**
   Zanka zajema je tiknila na 10 s, `next_positions` pa se je nastavljal na
   `time.monotonic() + 10` **po** opravljenem delu -- torej vedno za drobec
   pozneje od naslednjega tika, ki ga je zato zgrešil in preskočil cel obhod.
   Izmerjeno: lege so se brale v razmikih **19, 11, 19, 11 s namesto 10**,
   mediana 15 s. Zanka zdaj spi do prvega naslednjega opravila
   (`min(next_*) - now`), ne fiksen tik, in razmiki so 10, 11, 10, 10, 10.
4. **Preveri `EXPLAIN QUERY PLAN`, preden verjameš, da je indeks.**
   `SCAN t USING INDEX trip_train_no` **ni** iskanje po indeksu, ampak
   pregled cele tabele po napačnem — manjkal je `trip(route_id)`.

## Stanje zajema

## Stanje zajema

Lokalna baza `data/kajros.sqlite` (2026-09-01): 251 031 meritev,
1 838 411 vrstic dnevnika, 12 obratovalnih dni,
64 272 vremenskih vrstic, 9 791 postaj, 478 obvestil, 233 MB.
Merodajen je zajem na malini; lokalna kopija je posnetek in za njim zaostaja.

**Malina zajema samo železnico.** V `kajros-zajem.service` je
`KAJROS_AGENCIES=` prazen, zato uvoz vzame le SŽ in `trip` ima 789 voženj.
Storitev se imenuje **`kajros-zajem`**, ne `kajros` — ta obstaja, a je
`inactive`, in kdor preverja napačno ime, sklepa, da zajem stoji.

Posledica, ki jo je bilo videti šele ob prilitju: malina je 29.–31. 8. nekaj
avtobusov vseeno posnela (takrat je imela njihove vožnje uvožene), potem pa
jih je uvoz brez `KAJROS_AGENCIES` iz `trip` odstranil in **43 362 meritev je
ostalo sirot** — vrstic v `run` brez vožnje, ki jih tam ni mogoče prebrati.
Lokalna baza te vožnje ima, zato jih je `kajros merge` rešil (sirot 0).
Prilitje je dodalo 217 545 vrstic dnevnika in 31. 8. dvignilo železnico s
4 645 na 6 912 meritev; `kajros repair` je nato popravil 1 511 vrstic, ki
niso šle skozi novejše varovalke (malina teče starejšo kodo).

## Prvi šolski dan (1. 9. 2026)

Izmerjeno na jutru do 9:00, primerjano z istim oknom prejšnjih dni — sicer bi
primerjal pol dneva s celim.

**Šolski vozni red je avtobusni dogodek, ne železniški.** Razpisanih voženj
31. 8. → 1. 9.: železnica **638 → 655** (+2,7 %), avtobusi **6 812 → 9 880**
(**+45 %**). Od 9 880 avtobusnih jih 8 167 prejšnji dan sploh ni bilo.

**Železnica prvega šolskega dne ni bila slabša — bila je celo malenkost
boljša.** Jutro do 9:00, mediana zamude in delež do 5 minut:

| dan | meritev | mediana | do 5 min | p90 |
|---|---|---|---|---|
| 24. 8. pon | 1 988 | 2,0 min | 66 % | 13 min |
| 25. 8. tor | 1 990 | 2,0 min | 73 % | 11 min |
| 26. 8. sre | 1 989 | 2,0 min | 68 % | 13 min |
| 28. 8. pet | 1 948 | 1,0 min | 78 % | 10 min |
| 31. 8. pon | 1 913 | 1,0 min | 76 % | 12 min |
| **1. 9. tor (šola)** | **2 012** | **2,0 min** | **75 %** | **11 min** |

Tudi **40 vlakov, ki 31. 8. niso vozili** (šolski), se ne loči: mediana 2,0 min
in 69 % do petih minut proti 75 % pri ostalih, na 97 meritvah — premalo za
razliko. Najhujši tega jutra so bili običajni osumljenci na dolgih relacijah
(IC 503 Hodoš–Koper mediana +20 min, LPV 2803 Maribor–Dobova +18, RG 318 +18),
ne šolski vlaki.

**Zadrževanje na postajah se pri železnici ni spremenilo** — mediana razlike
med odhodno in prihodno zamudo je 0 s in nad 60 s je 0 % postankov, enako kot
prejšnje dni. S tem odpade skrb, da bi šolska gneča podrla `MIN_DWELL_S`; pri
avtobusih je mediana 5 s in 5 % postankov nad minuto, a je 31. 8. za primerjavo
le 911 postankov proti 51 344 današnjim, zato to **ni** primerjava.

**Avtobusov ni s čim primerjati in to je odgovor.** Jutranji zajem avtobusov
pred 1. 9. praktično ne obstaja (31. 8. do 9:00 le 1 142 meritev, in te so
polne zmrznjenih vrednosti). Današnje jutro je zato prva izmerjena avtobusna
konica in postane izhodišče: Nomago mediana 2,0 min in 79 % do petih minut,
Arriva 2,1 min in 76 %, LPP 2,0 min in 76 %, AP MS 1,6 min in 87 %.

**Kar je resnično boleče, ni zamuda, ampak izguba zgodovine.** Model se uči po
`trip_id`, šolski vozni red pa je prinesel 8 167 novih voženj — zato ima danes
zgodovino **le 11 % avtobusnih voženj** (1 133 od 9 880) proti **87 %
železniških** (568 od 655). Napoved in „običajna zamuda" sta pri avtobusih
torej od 1. 9. slepi in se bosta polnili znova; pri železnici se ni zgodilo nič.
`trip_id` so sicer ostali stabilni (0 sirot v `run`) — nove vožnje so res nove
storitve, ne preimenovane stare.


## Senčno merjenje: kaj je potnik res videl (2. 9. 2026)

Prvi izid `kajros ocena` — 7 776 razrešenih napovedi v treh dneh (1 008
železniških, 6 768 avtobusnih), posnetih 25 minut pred vlakom in 15 pred
avtobusom.

**Parna primerjava** (samo vrstice, kjer imajo vrednost vsi trije; prevoznik
je sicer meril na lažjem vzorcu in je bil videti boljši, kot je — 6 598 vrstic):

| model | MAE | v 5 min | podcenjenih | odklon |
|---|---|---|---|---|
| **naša ocena** | **3,28 min** | **86,6 %** | **5,2 %** | +1,04 min |
| naša brez pravila „prevoznik ve več“ | 3,59 | 85,8 % | 9,1 % | −0,61 |
| prevoznik | 3,39 | 82,4 % | 13,5 % | −1,26 |
| prenos zamude | 3,44 | 80,8 % | 14,8 % | −1,37 |

Iz tega štiri stvari:

* **Naša ocena premaga oboje — prevoznika in prenos — po vseh merilih.**
  Prva različica poročila je trdila nasprotno (prevoznik MAE 3,39 proti našim
  3,63), ker je vsak model merila na svojem vzorcu. To je natanko past, pred
  katero svari `ocena.py`, in se ji je treba izogniti tudi pri branju.
* **Pravilo „prevoznik ve več“ se izplača.** Sproži se v 41 % primerov (skoraj
  samo pri avtobusih) in tam je MAE 2,65 proti 3,31 brez njega, delež v petih
  minutah 88,6 proti 87,0.
* **Vsi razen nas podcenjujejo.** Odklon prenosa je −1,37 min, prevoznika
  −1,26; naša številka je +1,04, torej rahlo pesimistična.

  **Popravek 3. 9. 2026:** tu je prej pisalo, da je to „varna smer“. Ni.
  Pozitiven odklon pomeni, da vozilo napovemo **poznejše, kot je**, potnik
  pride pozneje in mu odpelje pred nosom. Varna smer je negativna. Glej
  „Smer napake“ spodaj.
* **Pri železnici prevoznik v potnikovem oknu praktično molči** — vrednost za
  ciljni postanek je imel v **4 od 1 008** primerov (0,4 %). Pri avtobusih je
  molčal v 2,6 %. Za vlake smo torej edini vir odgovora in tam smo 3,52 min
  proti 4,50 pri prenosu (78,5 proti 72,4 % v petih minutah).

**Številka, ki jo potnik vidi, je dvakrat slabša od backtesta** (1,92 min in
91 %). To ni napaka merjenja, ampak drugo vprašanje: v potnikovem oknu je cilj
mediano **6 postankov naprej pri železnici in 8 pri avtobusu** (p90 9 oziroma
13), backtest pa je poln kratkih skokov. Zastarelost ni kriva — „trenutna
zamuda“ je ob pogledu stara 2,7 min (železnica) oziroma 1,2 min (avtobus).

**Popravljeno 2. 9.** — glej `.claude/rules/model.md`, „Meja ostanka“: model
ostanku ne verjame več kot `max(10 min, trenutna zamuda)`. Na nalogah sence
3,63 → 3,18 min in pri 9–10 postankih 4,24 → 2,95; na avtobusnem backtestu
4,14 → 3,41 min. Spodnji odstavek opisuje stanje pred popravkom.

**Kje se da izboljšati, konkretno:** pri **9–10 postankih naprej** naš model
izgubi proti golemu prenosu (MAE 4,62 proti 3,59; brez pravila prevoznika celo
5,36). Odklon je tam +2,13 min povprečno, a le +0,72 mediano — torej ne
sistematično precenjevanje, ampak **rep**: manjšina primerov, kjer napovemo
veliko zamudo, ki se ne zgodi. Najhuje je pri avtobusih (+2,22) in takrat, ko
je vozilo ob pogledu skoraj točno (odklon +3,89 min pri zamudi pod 2 min).
Pri drugih razdaljah (4–8 in 11+) model prenos prepričljivo premaga.

## Neverjetne zamude pri avtobusih (3. 9. 2026)

Domača stran je ob 00:20 kazala **„avtobusi +833 min“**. Vzrok je bil dvojen.

**Prvi vzrok — manjkajoča varovalka, popravljeno.** `MIN_RUNS_FOR_DAY = 20`
je bil uporabljen samo v `/api/overview` (železnica), ne pa v
`/api/overview/bus`. Zato je avtobusni pregled ob 00:20 računal mediano iz
**šestih** voženj. `home.js` je `yesterday` že bral — samo poslali ga nismo.

**Drugi vzrok — vrednosti, ki niso zamude.** V bazi je **2 541 avtobusnih
vrstic z zamudo nad 4 h**, največ **16,3 h**. Primer: N0556 (Nomago), vozni
red 05:50, „zamuda“ 58 800 s na vseh postankih.

Porazdelitev pove, da to ni rep prave porazdelitve:

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

**Železnica nima nobene vrstice nad 3 h v 68 tisoč meritvah.** Pri avtobusih
pa padanje med 120 in 240 minutami skoraj zastane (3 464 → 2 541, razmerje
0,73 na dvakratni razdalji), kar je oblika **drugega procesa**, ne repa zamud.

**Kar ni dokaz, in zakaj to tu piše.** Preizkusil sem domnevo, da gre za
prevoznikovo napako ujemanja: vozilo, ki vozi zdaj, pripeto voznemu redu
izpred ur. Podpis bi bil „vozni red + zamuda ≈ čas branja feeda“ in pri
vrsticah nad 4 h se je pojavil v 75,4 %. **Kontrola ga je podrla:** pri
običajnih zamudah 0–5 min je isti podpis v 72,3 %. Seveda — pri prvem
postanku je „vozni red + zamuda = zdaj“ ravno to, kar živi feed je. Domneva
je še vedno verjetna, dokazana pa ni.

**Odprto: kje je meja.** Rez pri 3 h bi vrgel 2 735 avtobusnih vrstic
(0,56 %), pri 2 h pa 3 464 (0,71 %). Ker meja ni izmerjena, ampak sklepana,
zajema **nisem** spreminjal — podatki se ne brišejo na domnevo. Odločitev
čaka.

## Model ločeno po omrežjih (3. 9. 2026)

Senca ima 11 787 razrešenih napovedi, od tega **2 001 železniških** — prvič
dovolj, da se model pomeri na vlakih posebej.

**Železnica** (2 001 vrstic, posneto 25 min pred vlakom):

| model | MAE | v 2 min | v 5 min | podcenjenih | odklon |
|---|---|---|---|---|---|
| **naša ocena** | **3,56 min** | **64,1 %** | **82,0 %** | 13,2 % | **−1,71** |
| prenos zamude | 4,40 | 54,8 % | 75,5 % | 21,9 % | −3,40 |
| prevoznik | 3,73 | 73,3 % | 73,3 % | 26,7 % | −3,60 |

**Prevoznik pri vlakih molči v 99,3 %** (vrednost je imel v 15 od 2 001
primerov), zato je njegova vrstica anekdota, ne meritev. Proti prenosu zamude
smo boljši po vseh merilih: MAE 3,56 proti 4,40 in 82,0 % proti 75,5 % v petih
minutah.

**Kar je novo in ni bilo vidno v skupni številki: predznak odklona se med
omrežjema obrne.**

| | odklon | pomen |
|---|---|---|
| železnica | **−1,71 min** | napovemo **manj** zamude, kot je je |
| avtobusi | **+0,83 min** | napovemo **več** zamude, kot je je |
| skupaj | +0,40 min | povprečje, ki obeh ne opiše |

Verjetna razlaga, **ni preverjena**: meja ostanka (`max(10 min, trenutna
zamuda)`, uvedena 2. 9.) pri vlakih veže, ker zamuda na dolgih relacijah raste
naprej, pri avtobusih pa ne, ker se na kratkih relacijah pobere. Preveri se
tako, da se meri delež primerov, kjer meja res odreže.

**Odprto: katero smer napake hočemo.** Za *ujeti* vlak je varno podcenjevati —
kdor pride prezgodaj, čaka; kdor prepozno, vlak zamudi. Za *načrtovanje
prestopa* je varno ravno obratno. Model tega ne more imeti prav v obe smeri
hkrati, zato je to odločitev o rabi in ne popravek. Do nje se model ne
spreminja. Zapis v tem dokumentu, ki je trdil, da je pozitiven odklon „varna
smer“, je bil zato prehiter.


## Strop zamude za statistiko (3. 9. 2026)

Lestvica najbolj zamujajočih je bila pri avtobusih neuporabna: prva vrstica
N6223 z mediano **654 min na dveh vožnjah**. Vzrok so vrednosti, ki niso
zamude, ampak feedova zamenjava prometnega dne — isti pojav, ki ga pri
prikazu že lovi `api.MAX_LIVE_DELAY_S` (6 h).

Za statistiko je meja nižja in **izmerjena, ne izbrana** —
`stats.MAX_REALNA_ZAMUDA_S = 3 h`:

| | vrstic | odpade | mediana | povprečje | p99 |
|---|---|---|---|---|---|
| železnica | 69 803 | **0 (0,00 %)** | 2,00 → 2,00 | 6,25 → 6,25 | 39,0 → 39,0 |
| avtobusi | 537 253 | 2 614 (0,49 %) | 2,18 → 2,15 | **7,25 → 4,86** | 73,4 → 59,0 |

Dvoje to potrjuje. Prvič: **iz železnice strop ne vzame ničesar**, torej ne
reže v prave zamude — in železnica je omrežje, kjer imamo največ zaupanja.
Drugič: pri avtobusih se mediana komaj premakne, **povprečje pa pade za
tretjino**. Robustna mera stabilna, občutljiva sesuta — to je podpis
izstopajočih vrednosti, ne repa prave porazdelitve.

Podatki se **ne brišejo**; to je filter branja in zajem hrani vse. Lestvica
ima ob tem še spodnjo mejo vzorca (`MIN_RUNS_FOR_RANK = 5`): vožnja z dvema
zajemoma na vrhu ni najslabši vlak, ampak najmanjši vzorec.

Po popravku je najslabša avtobusna vožnja A5117 s **64 min na petih vožnjah**
namesto 654 min na dveh; železniška lestvica se ni spremenila (EC 211,
46 min, 12 voženj, 8 % točnih).


## Smer napake: kaj stane potnika (3. 9. 2026)

Vprašanje je bilo, ali naj model raje podcenjuje ali precenjuje zamudo.
Odgovor je odvisen od ene številke, ki je prej nismo imeli: **koliko stane
zamujeno vozilo.**

**Razmik do naslednjega odhoda z iste postaje v isto smer** (po `headsign`,
06–20, zajeti vozni red):

| | razmikov | mediana | p25 | p75 | p90 | nad uro |
|---|---|---|---|---|---|---|
| železnica | 5 205 | **87 min** | 55 | 153 | 260 | 66 % |
| avtobusi | 194 231 | **40 min** | 15 | 70 | 139 | 28 % |

Zamujen vlak torej stane mediano 87 minut, odvečno čakanje pa toliko minut,
kolikor smo podcenili. Razmerje je 20 : 1 do 90 : 1 — asimetrija ni majhna.

**Kje smo zdaj** (senca, delež primerov, kjer smo napovedali *več* zamude,
kot je bila — to je smer, ki vozilo zamudi):

| | > 0 | > 1 min | > 2 min | > 5 min | odklon | n |
|---|---|---|---|---|---|---|
| železnica | 32,1 % | 17,7 % | 11,1 % | 4,5 % | **−0,94 min** | 5 771 |
| avtobusi | **64,0 %** | 46,8 % | **30,9 %** | 6,9 % | **+0,42 min** | 29 642 |

**Prag odloči, katero zgodbo ta tabela pove**, in prav zato je tu razpisan v
štirih stolpcih namesto v enem. Poročilo `kajros ocena` je do 3. 9. 2026
kazalo precenitve pri pragu 0 in podcenitve pri pragu 5 min, eno poleg
drugega: pisalo je 58,8 % proti 6,3 % in zvenelo kot sistematično
precenjevanje. Pri istem pragu je 6,5 % proti 6,4 %. Odtlej oba stolpca
merita pri potnikovi rezervi (5 min).

**Kar je videti kot očiten sklep, a ni.** Če vsako oceno zamaknemo navzdol za
`k` minut in stroške seštejemo (podcenitev = čakanje, precenitev = razmik do
naslednjega), pade povprečen strošek s 27,9 na 10,1 min pri železnici in z
26,9 na 7,8 pri avtobusih — najbolje pri `k = 5`. MAE pa zraste z 2,93 na
6,65 oziroma s 3,36 na 5,53.

**Zakaj tega vseeno ne naredimo.** Model predpostavlja, da potnik pride
natanko ob napovedani minuti. Ne pride — pride z rezervo. In rezerva ter
zamik sta **zamenljiva**:

| potnikova rezerva | najboljši `k`, železnica | najboljši `k`, avtobusi |
|---|---|---|
| 0 min | 5 (strošek 10,1) | 5 (7,8) |
| 2 min | 3 (10,1) | 3 (7,8) |
| **5 min** | **0 (10,1)** | **0 (7,8)** |
| 10 min | 0 (12,3) | 0 (10,6) |

Strošek je pri vseh treh prvih vrsticah **enak**: šteje samo vsota `k + B`,
in optimum je okoli **5 minut skupaj**. Potnik jih prispeva sam. Če jih
dodamo še mi, je skupna rezerva 10 in strošek **zraste** (12,3 proti 10,1).

**Sklep, ki iz tega sledi:**

1. **Številke ne zamikamo.** Prikazana vrednost ostane najboljša ocena;
   zamik bi podvojil rezervo, ki jo potnik že ima, in pokvaril MAE za nič.
2. **Nikoli pa ne smemo biti sistematično pesimistični.** Pozitiven odklon
   poje potnikovo lastno rezervo, ne da bi ta o tem vedel. Avtobusi so pri
   **+0,47 min in 63,6 % precenitev** — to je edino, kar je treba popraviti,
   in cilj je odklon ≈ 0, ne negativen.
3. **Železnica pri −1,27 je v redu.** Pri 87-minutnem razmiku je rahla
   previdnost poceni zavarovanje.
4. **Če hočemo pomagati, pomagajmo naravnost, ne z lažjo v številki:**
   ob „pričakovano 15:47“ sodi „bodi na peronu do 15:45“. Nasvet ločen od
   meritve — številka naj pomeni to, kar piše.

**Meje tega izračuna.** Predpostavlja, da zamujeno vozilo pomeni čakanje
celega razmika (v resnici obstajajo obvozi in druge relacije) in da potnik
cilja natanko na prikazano minuto. Zato je absolutni strošek precenjen;
**razmerje** med možnostmi in ugotovitev, da sta `k` in rezerva zamenljiva,
pa sta na te predpostavke neobčutljiva.

## Aplikacija za Android: velikost in čistost (12. 9. 2026)

**APK.** Ovoj z WebView, brez AndroidX in brez česarkoli Googlovega; edina
knjižnica v paketu je Kotlinova standardna.

| različica | velikost | zakaj toliko |
|---|---|---|
| izdajna (R8) | **60 942 B** (~60 kB) | naša koda + kar od Kotlina res rabi |
| razvojna | 937 170 B (~915 kB) | brez R8; Kotlinova standardna knjižnica cela |

Rast po rezinah, vse izmerjeno na izdajni različici: **28 kB** gol ovoj
(6. 9.) → **50 kB** z budilko, seznamom in mostom (7. 9.) → **60 kB** s
ponavljajočimi budilkami, widgetom in bogatejšim seznamom (12. 9.). Devet
kilobajtov za ponavljanje in widget je toliko, kolikor stane `java.time` v
`Ponovitev.kt` in `RemoteViews` v widgetu — nobene nove odvisnosti ni.

Preverjeno v paketu 12. 9. 2026: `aapt2 dump strings` najde **0** nizov z
`com/google`, `gms`, `firebase` ali `androidx`. `minSdk` 26, `targetSdk` 35.

**17. 9. 2026: widget po smernicah stane 1 472 B.** Podpisani izdajni APK
79 394 → **80 866 B**; v tem so predogledna postavitev za izbirnik
(`previewLayout`), sistemska zaobljenost v `values-v31`, meji za stiskanje in
opis za bralnik zaslona. Izmerjeno z gradnjo iz `git worktree` na HEAD, ne po
oceni.

**Objavljena 17. 9. 2026 kot 1.2** (`versionCode` 3, 98 014 B, sha256
`71f8f5aa…`); prenos s `kajros.app/prenos/kajros-1.2.apk` preverjen z vsoto.

**Dva nova widgeta stanejo 17 148 B.** Izdajni APK 80 866 → **98 014 B**
(~96 kB): odhodna tabla ene postaje s svojo nastavitveno dejavnostjo in seznam
budilk s stikali. Večino tega nosi tabla — prenos, razčlenjevanje odgovora,
shramba zadnjega stanja in zaslon za izbiro postaje; seznam budilk je samo
izris tega, kar je že v telefonu. Nobene nove odvisnosti ni.

**Ritem table je 15 minut, a sistem ga sme raztegniti.** Izmerjeno na
emulatorju (Android 15, `dumpsys alarm`):

```
tag=*alarm*:app.kajros.TABLA
type=ELAPSED origWhen=+13m46s repeatInterval=900000 window=+11m15s
whenElapsed=+13m46s maxWhenElapsed=+25m1s
```

`setInexactRepeating` torej ne obljublja 15 minut, ampak **od 15 do 25**, in
`ELAPSED` (brez `_WAKEUP`) pomeni, da se spečega telefona ne budi. Prav zato
widget nosi uro podatka in od 30 minut naprej to pove z besedo — številka brez
ure bi trdila svežino, ki je ta ritem ne more zagotoviti.

**Dovoljenj je enajst, ne štiri** — budilka jih je prinesla sedem:
`INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_FINE_LOCATION`,
`ACCESS_COARSE_LOCATION`, `USE_EXACT_ALARM`, `SCHEDULE_EXACT_ALARM`
(do SDK 32), `POST_NOTIFICATIONS`, `USE_FULL_SCREEN_INTENT`, `WAKE_LOCK`,
`VIBRATE`, `RECEIVE_BOOT_COMPLETED`. Za widget ni bilo treba nobenega.

**Orodja.** `~/kajros-android` = 2,4 GB brez emulatorja, 5,5 GB z njim.
Nič sistemskega, nič sudota.

**Tri uhajanja zunaj mape**, ki jih je našla revizija in ne domneva:

| kaj | kdo | kaj to premakne |
|---|---|---|
| `~/.java/.userPrefs/google/prefs.xml` | JVM za sdkmanager | `-Djava.util.prefs.userRoot` |
| `~/.android/adbkey` | `adb` | samo drugačen `HOME` (ne `ANDROID_USER_HOME`) |
| `~/.android/analytics.settings` z obstojnim `userId` | AGP ob **vsaki** gradnji | samo `-Duser.home` |

Zadnjega je bilo najtežje ujeti: preizkušeno je bilo troje in dve nista
delovali — `ANDROID_USER_HOME` sam pušča, `HOME=$KOREN/domov` prav tako
(za razliko od adb), `ANDROID_PREFS_ROOT` pa AGP sesuje, ker zahteva eno samo
spremenljivko. Telemetrija `sdkmanagerja` se izklopi z `--no-metrics`, a samo
na novem `android` CLI — na `sdkmanager` je zastavica tiha in brez učinka
(izmerjeno na številu datotek v `analytics/metrics/spool/`: brez nje 8 → 9,
z njo ostane 9).

`android/zgradi.sh` isto revizijo ponovi ob vsaki gradnji in **pade**, če kaj
uide — enkratna meritev tega razreda napake ne ujame.

## Rezerva budilke: koliko prej naj zazvoni (6. 9. 2026)

David: *„Uporabnik pa ne sme zamuditi, raje kej rezerve, če ni zihr."*
Koliko rezerve, je vprašanje s številko. Vir je senca (`napoved`, 63 843
razrešenih vrstic): `ours_s` je, kar bi prikaz **takrat** povedal, `actual_s`
je resnica. Napaka budilke je `ours_s − actual_s` — pozitivna pomeni, da smo
obljubili večjo zamudo, kot je bila, in bi budilka zvonila **prepozno**.

**Brez rezerve bi budilka zvonila prepozno v 32 % primerov pri vlakih in
64 % pri avtobusih.** Mediana napake je pri avtobusih +0,8 min, p95 +5,6.

Strošek po isti metodi kot „Smer napake" zgoraj: `P(zamudi) × razmik +
odvečno čakanje`, razmik 87 min (železnica) in 40 min (avtobusi).

| R [min] | železnica, zamudi | strošek | avtobusi, zamudi | strošek |
|---|---|---|---|---|
| 0 | 32,2 % | 30,13 | 63,6 % | 27,06 |
| 3 | 8,0 % | 11,48 | 17,4 % | 10,43 |
| 4 | 5,7 % | 10,40 | 10,4 % | 8,48 |
| **5** | **4,5 %** | **10,29** | **6,4 %** | **7,81** |
| 6 | 3,4 % | 10,33 | 4,3 % | 7,93 |
| 8 | 2,1 % | 11,10 | 2,3 % | 9,07 |

Optimum je pri obeh omrežjih **R = 5 min** in krivulja je med 4 in 6 ravna,
torej izbira ni krhka. (Pri ohlapnejši definiciji zamude — „manjka več kot
2 min" — bi bil optimum 3; vzet je strogi, ker je tako zahteval David.)

**Vlak v 10 775 meritvah ni odpeljal prezgodaj niti enkrat** (avtobus v
25,3 %, več kot 2 min prezgodaj v 8,8 %, p01 = −6,2 min). Iz tega sledi
popravek, ki je zastonj:

| pravilo | železnica: zamudi / strošek | avtobusi: zamudi / strošek |
|---|---|---|
| `ours` | 32,2 % / 30,13 | 63,6 % / 27,06 |
| `ours − 5` | 4,5 % / 10,29 | **6,4 % / 7,81** |
| **`max(0, ours − 5)`** | **4,5 % / 8,32** | 28,9 % / 14,81 |

Pri vlakih **isti delež zamud, a 2 minuti manj odvečnega čakanja**: budilka
ne sme zvoniti pred voznim redom, ker vlak pred njim ne odpelje. Pri
avtobusih bi ista omejitev delež zamud početverila — ti prezgodaj **gredo**.

**Brez povezave**, ko zamude ne poznamo, velja isti račun na golem `actual_s`:

| | najcenejši R | zakaj |
|---|---|---|
| železnica | **0** | vlak prezgodaj ne odpelje; vsaka rezerva je čisto čakanje |
| avtobusi | **3** | 25,3 % jih odpelje prej; strošek 14,92 → 9,50 |

**Kaj je s to meritvijo narejeno.** Rezerve aplikacija **ne dodaja sama**
(odločeno 6. 9. 2026): `zvoni = voznoredna + zamuda − X`, rezervo pa določi
potnik s tem, koliko izbere X. Ta meritev je zato zapisana v vmesniku, kjer
X izbira — da ve, kaj kupuje z vsako minuto. Številke veljajo naprej in bodo
podlaga za ločeno možnost „+3 min", ko bo vmesnik prenovljen.

Namesto pavšalne rezerve pokriva izpad povezave svoje pravilo: zadnjih
3,5 minute pred zvonjenjem brez odgovora pomeni **takojšnje zvonjenje** z
razlogom. Cena je do 3,5 minute spanca, in samo takrat, ko povezave res ni.

**Česar ta meritev ne pove:** kako napaka raste s starostjo podatka.
`ocena.py` snema pri stalnem horizontu (25 min vlaki, 15 avtobusi), zato v
`napoved` razpona ni. Zastarel podatek zato ni obravnavan kot slabša napoved,
ampak kot **odsotnost** povezave — konservativno, kot je bilo naročeno.

## Kaj LPP v IJPP sploh je (6. 9. 2026)

Prijava: „odhodi iz postaje Polje najdejo samo LPP 25, čeprav so tam vsaj
trije busi". Preverjeno v bazi — **prikaz je pravilen, feed je nepopoln.**

Postajališči z imenom `Polje` (`1167324`, `1167325`, Ljubljana) strežeta v
celotnem voznem redu **samo liniji 25** (199 postankov). V nedeljo 6. 9. je
tam 31 odhodov, v ponedeljek 7. 9. jih je 80 — vsi linija 25.

**Linij 20 in 22 v podatkih sploh ni**, pri nobeni agenciji. Znotraj 1,2 km od
Polja je edina druga stvar železniška postaja Ljubljana Polje.

| agencija | linij | voženj |
|---|---|---|
| 1123 (AP MS) | 486 | 8 981 |
| 1119 (Nomago) | 922 | 6 941 |
| 1118 (**LPP**) | **37** | 3 174 |
| 1121 (Arriva) | 115 | 965 |

LPP jih ima 37: `12D, 15, 19I, 21D, 25, 30, 3B, 3G, 40, 42, 44, 45, 46, 461,
47, 48, 48P, 49, 50, 51, 52, 53, 54, 56, 60, 68, 69, 6B, 71, 72, 73, 74, 76,
78, 80, 82, 84`. Mestnih linij 1, 2, 5, 6, 7, 9, 11, 13, 14, 18, 20, 22, 27 ni.
Prisotne so večinoma primestne (40+) in nekaj mestnih.

To je vrzel pri viru, ne pri nas, in je ni mogoče zapolniti iz drugega
odprtega vira. Vredno vprašanja DUJPP, ko bo tekla korespondenca.

## Mestni LPP je dosegljiv, a po drugi poti (7. 9. 2026)

Nadaljevanje zgornjega: mestnih linij LPP v IJPP ni. Vprašanje je bilo, ali
obstaja odprt vir. **Obstaja**, in je isti `derp.si`, s katerega že jemljemo
IJPP — le drug vir. Potrjeno iz konfiguracije projekta transitous
(`feeds/si.json`, vnos `name: lpp`), ne uganjeno.

| vir | dostop | vsebina |
|---|---|---|
| `avl.lpp.si/transit/api/gtfs` | odprt, 42 MB | statični GTFS, agencija `lpp`, **31 prog — ravno mestne in nočne** |
| `rt.gtfs.derp.si/sources/lpp/all` | **odprt, brez ključa** | 600 entitet: 280 trip_updates, **139 leg vozil**, 181 obvestil |
| `data.lpp.si/api/bus/buses-on-route` | **401** | lege — zaklenjeno, a jih ima derp.si |
| `data.lpp.si` ostalo | odprt | 117 oznak linij, 1 459 postajališč, `eta_min` |

Feeda sta **komplementarna**: IJPP nosi primestne LPP linije (40–84),
`avl.lpp.si` mestne (01–28, N1, N3, N5).

**Past: `delay` je v tem feedu vedno 0.** Izmerjeno dvakrat — v nedeljo ob
22:00 (2 721 postankov) in v ponedeljkovi konici ob 07:11 (2 604 postankov):
**nobena zamuda ni neničelna**, in `trip_update.delay` ni izpolnjen pri nobeni
vožnji. Kdor bi bral `delay`, bi zapisal, da mestni LPP nikoli ne zamuja.

**Zamuda je vseeno tam, le v drugi obliki.** 1 882 od 4 517 postankov nosi
**absolutni napovedani čas**. To je natanko primer, ki ga `collector._delay_of()`
že pokriva (`m.time − (polnoč + t_s)`). Preverjeno na šestih postankih ob 07:11
proti uradnemu voznemu redu:

| vozni red | napoved | zamuda |
|---|---|---|
| 07:07 | 07:10:13 | **+3,2 min** |
| 07:13 | 07:11:50 | **−1,2 min** |
| 07:12 | 07:13:02 | +1,0 min |
| 07:10 | 07:13:14 | +3,2 min |
| 07:15 | 07:16:25 | +1,4 min |

**`trip_id` se ujemata 1 : 1.** RT uporablja isto trojno obliko UUID
(`service|?|trip`) kot uradni `trips.txt`; vsak preverjeni RT `trip_id` je v
voznem redu natanko enkrat. Združevanje gre torej z `avl.lpp.si`, **ne** z NAP.

Lege vozil: 139, starost mediana 146 s (IJPP ima 10 s). Za zemljevid dovolj,
za oceno hitrosti manj natančno.

**Kar ostaja odprto: licenca.** Za `avl.lpp.si` in `data.lpp.si` ni navedene.
Odprt dostop ni dovoljenje za objavo. Vsi podatki v kajrosu so zdaj CC BY-SA 4.0
z obvezno navedbo vira; preden gre mestni LPP na zaslon, mora biti jasno, pod
čim. Vprašanje za LPP in za DUJPP v istem krogu pisem.

## Uvoz mestnega LPP: kaj to prinese in kaj stane (7. 9. 2026)

Uvoz je zgrajen in preizkušen na kopiji baze. Vklopi se s `KAJROS_LPP=1`,
privzeto je izklopljen.

**Kaj prinese.** Postajališče „Polje", zaradi katerega se je vse začelo:

| | linij | odhodov danes |
|---|---|---|
| prej (samo IJPP) | 1 (linija 25) | 80 |
| zdaj | **5** (27, 11, 25, 24, 11B) | **365** |

V bazo pride 31 mestnih in nočnih linij: 1, 1B, 2, 3, 5, 6, 7, 8, 9, 10, 11,
11B, 13, 14, 16, 18, 18L, 19B, 20, 20Z, 22, 23, 24, 26, 27, 28, N1, N3, N3B,
N5 in SŽ.

**Kaj stane.** Uvoz obeh zipov traja **27 s**:

| | prej | z LPP |
|---|---|---|
| vožnje | 20 850 | 39 899 (+19 163) |
| postanki (`sched`) | 403 208 | 889 731 |
| postajališča | 9 791 | 10 509 |

**Okno je nujno.** LPP nima voznih vzorcev, ampak svojo vožnjo za vsak datum:
62 989 voženj in 1,6 milijona postankov za 31 dni. Uvažamo osem dni
(`KAJROS_LPP_DAYS`), kar da zgornjih 19 163 voženj.

**Zamude so kakovostnejše od avtobusov v IJPP.** En zajem ob 07:40 je dal
4 157 postankov, **2 071 z neničelno zamudo** (49,8 %):

| p01 | p25 | mediana | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| −4 min | 0 | 0 | +1 | +7 | +23 | +69 |

Nad 30 min je 27 vrstic (0,65 %) in **vse pripadajo eni sami vožnji** (linija 1,
27 postankov, povprečno +66 min). **Nad 2 h ni ničesar** — za primerjavo je
IJPP-jev avtobusni feed imel 2 541 vrstic nad 4 h. Ta vir je torej bistveno
čistejši in za zdaj ne potrebuje svoje varovalke.

Leg vozil je 145 (IJPP jih ima ~1 000), starost mediana 146 s.

**Kar je bilo treba obiti:** `delay` v tem feedu je vedno 0. Zamuda pride iz
absolutnih napovedanih časov prek `collector._delay_of()`.

**V produkciji od 7. 9. 2026, 08:16.** Prvi zajem na arwenu: „LPP: 240 voženj,
3 575 sprememb, 140 leg". Vozni red je 38 070 voženj (od tega 19 163 LPP) in
10 493 postajališč; vozil z GPS je 1 235 namesto ~1 000. Bavarski dvor kaže
150 odhodov z živimi zamudami mestnih linij (18L +4 min izmerjeno, 6B +11 min
ocena), Polje pa 150 odhodov na petih linijah namesto 80 na eni.

## Kaj je LPP podrl in kaj je to stalo (7. 9. 2026)

Vklop mestnega LPP je potrojil avtobusno omrežje in s tem odkril tri napake,
ki so bile v kodi že prej, le da jih železnica ni sprožila. Vse tri so bile
najdene s pregledom `preglej vse`, ne s prijavo uporabnika.

**1. `/api/live` se ni odzival — 216 s.** `EXPLAIN QUERY PLAN` je pokazal
`SCAN p` in za njim `SCAN tail`: CTE `tail` je bil materializiran brez
indeksa, zato je bil za vsako vrstico `passed` pregledan cel. Železnica
2 006 × 2 006, avtobusi **59 557 × 59 557 = 3,5 milijarde** primerjav.
`tail` je bil samo „zamuda na zadnjem postanku", kar je okenska funkcija.

| | prej | zdaj |
|---|---|---|
| avtobusi | 216,1 s | **4,3 s** (arwen), 0,14 s (razvojni) |
| železnica | 2,27 s | 0,66 s |

Izid pri železnici je enak vrstico za vrstico.

**2. Iskanje zvez z enim prestopom — 26,5 s.** Poizvedba se razveji čez vse
pare voženj, ki se kje srečata; na prometni mestni postaji je to izmerjeno
26,5 s od trenutne ure in 40,5 s za cel dan, pri vlakih pa 0,0 s.

Rešitev je merjena ločnica, ne pospešitev poizvedbe. Mediana razmika med
zaporednimi neposrednimi odhodi:

| relacija | zvez | mediana razmika |
|---|---|---|
| Bavarski dvor → Polje (mestni) | 161 | **6 min** |
| Ljubljana AP → Maribor AP | 8 | 70 min |
| Ljubljana → Maribor (vlak) | 11 | 120 min |
| Ljubljana → Koper (vlak) | 3 | 520 min |

Med 6 in 70 minutami ni ničesar, zato je meja **15 minut**: pri gostejšem
taktu prestopa sploh ne iščemo, ker ne more nič prihraniti. Izid:
Bavarski dvor → Polje **26,5 s → 0,13 s**, vlaki nespremenjeni.
Mestni par brez neposredne zveze (ZALOG → Štajerska) ostane pri 3,0 s in
osmih zvezah.

**3. `plan()` je tiho vračal nič.** `MAX_STOP_TIMES = 200 000` je bil
postavljen na domnevo „pri avtobusih 80 000"; z LPP jih je **247 346**, zato
je `_timetable_for_day()` vračal prazen vozni red — in tega ni nihče povedal.
Meja je zdaj izmerjena: cel avtobusni dan je 92 MB zadržano, 127 MB vrh,
naloži se v 1,6 s. Nova meja 300 000, predpomnilnik z štirih na dva vnosa
(najhujši primer ~184 MB namesto 370). Prazen izid se odslej predpomni, da se
četrt milijona vrstic ne bere znova ob vsakem klicu.

**Kar ostaja počasno in ni popravljeno:** `/api/stations/search` je na arwenu
~4 s za vsako poizvedbo (lokalno 0,35 s). Brskalnika to ne prizadene, ker
odkar obstaja `/api/stations/index`, išče sam; endpoint je še vedno v rabi kot
zasilna pot in pri prvih pritiskih tipk, preden se kazalo naloži.

## Isto postajališče pod dvema imenoma (7. 9. 2026)

LPP piše **12 % imen s samimi velikimi črkami** („ČRNUČE", 45 od 388), IJPP
pa normalno. Ker v aplikaciji vse teče po **imenu** postaje, sta to dve
različni postaji: iskalnik pokaže obe, odhodna tabla razdeli odhode, budilka
pa si zapomni tisto, ki je nikjer drugje ni.

Imen, ki se razlikujejo samo po velikosti črk ali šumniku, je **24**. Slepo
združevanje bi bilo napačno — razdelitev po razdalji je ostra:

| razdalja | parov | kaj so |
|---|---|---|
| 3–215 m | **14** | isto postajališče, dva zapisa |
| 0,8–111,6 km | **10** | različna kraja z istim imenom |

Med 215 m in 829 m ni ničesar. „Celje" in „Čelje" sta **112 km** narazen,
„Lozice" in „Ložice" 43 km, „Rožna Dolina" in „Rožna dolina" 66 km — to so
različne vasi in jih ni dovoljeno zliti.

Uvoz zato poenoti ime samo, kadar sta zapisa tudi **fizično na istem mestu**
(`ISTO_POSTAJALISCE_M = 500`). Kanonično je ime, ki ni v samih velikih črkah;
ob več takih odloči pogostost in nato abeceda, da je izid ponovljiv.
Izid uvoza: `imen_poenotenih: 14`, preostalih dvojnic 10 — vse različni kraji.

## Vzdrževanje po vklopu LPP (7. 9. 2026)

Preverjeno, ker se je baza čez noč povečala za 40 %.

**Obrez deluje.** Politika je 90 dni za železnico in 14 za avtobuse
(`OBS_KEEP_DAYS`). Avtobusnih vrstic pred 14-dnevno mejo je **0**; ostanejo
le železniške iz avgusta, po nekaj tisoč na dan.

**Koliko doda LPP.** Med 08:16 in 12:15 je zapisal **57 567 meritev** — na
cel obratovalni dan okoli 250 000, ob dosedanjih ~470 000. Baza je z uvozom
zrasla s 605 na **845 MB** (statični vozni red), v ustaljenem stanju bo pri
štirinajstdnevnem oknu okoli 1,3–1,4 GB. Na arwenu je 33 GB prostega.

| dan | meritev | opomba |
|---|---|---|
| 2026-09-02 do 04 | ~1,31 M | delovni dnevi, brez LPP |
| 2026-09-05, 06 | 293 k, 240 k | vikend |
| 2026-09-07 do 12:15 | 529 k | ponedeljek, LPP od 08:16 |

**Dnevni povzetek je hiter.** `refresh_summaries()` je **3,1 s** (železnica
267 + 409 ms, avtobusi 470 + 1 902 ms). Opravilo ob 3:30 torej ni ogroženo.

**Storitev se ne sesuva.** `NRestarts = 0`, v dnevniku dveh ur nobene napake;
vsi ponovni zagoni so bili moji.

**Senca zdaj zajema tudi mestni LPP** (545 vrstic, 472 razrešenih). Rezerva
budilke je bila umerjena brez njih — ko bo vrstic dovolj, jo je vredno
premeriti ločeno, saj je mestni LPP bistveno točnejši: mediana zamude 0 min
in p90 3 min proti 3 in 11 min pri primestnem LPP.

## Obvestila mestnega LPP: 181 vrstic, dve novici (7. 9. 2026)

Feed `sources/lpp/all` nosi poleg zamud in leg tudi **obvestila** — teh doslej
nismo brali in so šla vsakih 30 s v smeti.

Izmerjeno: **181 obvestil, od tega dve različni.** „Postaja Čerinova na
obvozu" (147 voženj) in „Postaja Tbilisijska na obvozu" (34), obe z
besedilom „Vozilo se ne bo ustavilo na postaji". Vsako ima svoj naključen
UUID, zato bi jih običajen zajem zapisal 181 in stran bi pokazala isto poved
stokrat.

Združujejo se po besedilu (`alerts.ingest_lpp()`), prizadeta postajališča pa
se zberejo v `alert_entity`. Odhodna tabla jih pokaže prek `for_stops()` —
za potnika je to natanko en podatek: **tu se avtobus ne bo ustavil**.

Vrsta je `obvoz` in ne `ovira`, zato števci ovir (`/api/health`,
`overview.disruptions`) ostanejo železniški in se skladnost ne podre.

**Past, ki je stala en obhod:** `alert_entity.route_id` in `trip_id` sta
`NOT NULL DEFAULT ''`. Prvi zapis je vstavljal `NULL`, vsaka vrstica je padla
na omejitvi, `INSERT OR IGNORE` pa jo je **tiho požrl** — obvestili sta bili
zapisani, a brez enega samega postajališča, in videti je bilo, kot da zajem dela.
Zdaj gre prazen niz in navaden `INSERT`, da bi se ista napaka slišala takoj.

## Feed ne poroča prvega postanka (7. 9. 2026)

Prijava: okno vožnje pri vlaku, ki še ni odpeljal, povsod kaže „?" in „brez
ocene", iskalnik pa za isto vožnjo pove „običajno 0 min, 16 voženj, 100 %
v 5 min".

Vzroka sta dva in prvi je splošnejši od prijave:

**1. Železniški feed prvega postanka ne poroča nikoli.** Od **716 voženj z
meritvami jih ima 0** kdaj meritev na svojem prvem postanku. Ni naključje
vzorca in ni splošno pravilo GTFS-RT — **pri avtobusih ga ima 14 555 od
16 671 (87 %)**. Gre za lastnost SŽ-jevega vira. Zato „običajna zamuda" na
izhodišču vlaka ne more obstajati, ne glede na to, koliko dni zajemamo; za
LPV 2273 se meritve začnejo pri `stop_seq = 2` (Ljubljana Polje, 16 dni).

**2. Okno vožnje ni imelo zgodovine.** `typical_at_stops()` obstaja od prej
in ga iskalnik uporablja (`typical_dep`, `typical_arr`), `/api/train/{no}/run`
pa ga ni vračal. Isti podatek, dva prikaza, ena številka manj.

Endpoint ga zdaj vrne za vsak postanek. Za izhodišče, kjer ga po točki 1 ni,
prikaz vzame naslednji postanek in to **pove** — ni napoved za ta dan, je
opis preteklih voženj.

## Gumb „shrani" je čakal na omrežje po podatek, ki ga je stran že imela (7. 9. 2026)

Klik na „shrani" je pokazal potrditev šele po 1–2 s. Vzrok ni bilo pisanje —
shramba je `localStorage` — ampak **preverba, ali postaji sploh poznamo**:
`stationExists()` je za vsako od obeh imen poklical `/api/stations/search`.

Izmerjeno prek Cloudflara na `kajros.app` (`/api/stations/search?q=Ljubljana`,
omrežje avtobusi): **0,69 / 0,67 / 0,63 s**. Dve zahteti vzporedno sta torej
~0,7 s samo režije, na mobilnem omrežju pa še TLS in čakanje v vrsti.

Kazalo postaj je bilo v pomnilniku že od nalaganja strani (`KAZALO`, za
iskalnik brez sunkov). Zdaj preverba bere njega: **0 zahtev**. Strežnik ostane
le za primer, ko se kazalo še ni naložilo. Iskanje gre po celem kazalu, ne po
prvih osmih zadetkih — točno ujemanje sme biti kjerkoli.

## Ura, ki teče nazaj: `run` hrani zadnje stanje, tudi kadar je smet (7. 9. 2026)

Okno vožnje je pri **vsaki deseti** vožnji avtobusa in vsaki dvajseti vožnji
vlaka kazalo nemogoč vozni red: naslednja postaja **pred** prejšnjo. Vozilo ne
more priti na postajo, preden je odpeljalo s prejšnje.

Vzroki so trije in vsi izvirajo iz tega, da `run` hrani **zadnje** stanje
postanka:

1. **Feed postanek neha pošiljati** in ostane nepotrjena napoved. RG 310,
   4. 9.: Litostroj +29 min (feed 17:59), nato Stegne in Vižmarje z **ničlo**
   in feedom iz 17:32 in 17:34, nato spet +22. Nezapolnjena ničla razloži 36 %
   železniških in 7 % avtobusnih skokov — je torej podmnožica pojava, ne vzrok.
2. **Feed za nazaj popravi že prevožen postanek.** N0507, 7. 9.: ob 16:14 je
   dobil +30 min za postanek, prevožen ob 15:48, medtem ko je vsa vožnja
   tekla nekaj minut pred voznim redom.
3. **Mestni LPP pošilja samo postanke pred vozilom**, zato je vsaka vrednost
   zadnja napoved pred prehodom in cel snop se lahko popravi hkrati.

Točka 3 je bila izmerjena s projekcijo lege vozila na postaje vožnje: vozilo
pri postaji 8 od 26, `stop_time_update` samo za 9–26. Pri mestnem LPP zato v
`run` **nikoli ni meritve** — vedno le zadnja napoved pred prehodom (mediana
42 s pred prehodom, p90 27 s po njem). IJPP je drugačen: 56 % voženj ima v
seznamu še vedno prvi postanek, torej se prevoženi postanki osvežujejo.

### Kaj pomaga

Katera vrednost je napačna, iz nje same ni ugotovljivo. Ugotovljivo pa je,
katere si nasprotujejo z največ drugimi: obdrži se **nepadajoče zaporedje ur z
največjo skupno težo**, ostalo se označi (`stats.oznaci_neskladne()`).

Dvoje je bilo treba izmeriti, ne uganiti:

* **Utež.** Postanek, nazadnje osvežen prej kot kateri od prejšnjih, je lažji.
  Brez tega bi štetje samih postankov pri RG 310 zavrglo **pravo** vrednost,
  ker sta bili luknji dve in prava ena. Lahek postanek pa se obdrži, kadar
  ničemur ne nasprotuje — sicer bi pri avtobusih padlo 4,73 % postankov
  namesto 2,29 %.
* **Zaokroževanje na minuto.** Prikaz kaže minute; skok za 20 s ni nemogoč
  vozni red, ampak natančnost. Brez tega bi bilo pri mestnem LPP prizadetih
  38,4 % voženj namesto 17,2 %.

Izid na celi bazi (61 362 voženj, 1,1 s za vse skupaj — 18 µs na vožnjo):

| omrežje | vožnje z uro nazaj prej | potem | izpuščenih postankov |
|---|---|---|---|
| železnica | 4,9 % (364/7 466) | **0** | 0,57 % |
| avtobus | 10,1 % (5 347/52 680) | **0** | 2,29 % |
| LPP mestni | 3,6 % (39/1 081) | **0** | 1,33 % |

Meja med meritvijo in napovedjo (`_LAST_MEASURED_SQL`) nosi le **lokalni** del
pravila — postanek, osvežen prej kot kateri od prejšnjih — ker teče nad
seznamom voženj hkrati in celotne verige ne zmore. Pri železnici lokalni del
razloži vse primere (451 od 452), pri avtobusih dve petini.

### Neskladne vrednosti statistike ne pokvarijo (7. 9. 2026)

Vprašanje, ki se ponuja samo od sebe: če je 2,29 % avtobusnih postankov
smeti, ali je treba očistiti tudi agregate? **Ne.** Primerjava vseh vrednosti
proti tistim, ki ostanejo po `oznaci_neskladne()`:

| omrežje | mediana | povprečje | p95 | v 5 min |
|---|---|---|---|---|
| avtobus | 2,2 → 2,2 min | 7,4 → 7,3 | 22,3 → 21,0 | 71,7 → 72,1 % |
| železnica | 2,0 → 2,0 | 6,4 → 6,4 | 24,0 → 24,0 | 59,5 → 59,4 % |
| LPP mestni | 0,7 → 0,7 | 1,6 → 1,6 | 7,5 → 7,3 | 89,5 → 89,7 % |

Napaka je torej **lokalna**: uniči eno vrstico na zaslonu, agregata ne
premakne. Filtriranje v statistiki bi bilo dodatna zapletenost brez učinka —
in `povzetek` se računa v SQL, kjer verige ni mogoče pognati.

## Zamuda, ki lovi uro: potrjeno, brez poštenega filtra (7. 9. 2026)

Na strani „Vožnje, ki najbolj zamujajo" je bil N0786 z **mediano 111 min**.
Dnevnik `obs` pokaže, zakaj: vrednost raste v koraku z uro.

```
07:03:35  seq 1–2: 540 s   seq 3–5: 4260 s
07:07:02  vsi:    4800 s
07:12:18  vsi:    5400 s      … končno stanje 7 080 s (118 min)
```

To je pojav, ki ga `collector._je_nazaj_v_prihodnost()` že opisuje (vozilo
obstane, feed pa zamudo pripisuje naprej). Njegova varovalka tega primera ne
ujame, ker zahteva, da je bil prejšnji zapis **meritev** — feed pa je tu za
prihod in odhod ves čas dajal isto vrednost.

**Poštenega dodatnega filtra ni** in to je izmerjeno, ne domnevano:

* „Zamuda raste 1 : 1 z uro" ni znak smeti: pri železnici to velja za
  **29,9 %** zadnjih sprememb, ker vlak, ki stoji pred signalom, res nabira
  zamudo minuto na minuto. Pri avtobusih 8,3 %, pri LPP 8,8 %.
* „Zapis je meritev, kadar sta prihod in odhod različna" drži pri vlakih
  (3,4 % vrstic ob 67,7 % voznorednih postankov), pri avtobusih pa ne:
  **58,8 %** vrstic ima različna časa, čeprav ima vozni red postanek le pri
  **0,6 %**. Filtrirati po tem bi zavrglo 41 % avtobusnih meritev.

Ostaja torej odprto in zapisano. Kar se da povedati pošteno, je sam prikaz:
seznam najhujših voženj **že** kaže število voženj in delež v petih minutah,
torej „5 voženj · 20 % v 5 min" ob 111 min — bralec vidi, na čem stoji.

## „Celje" je na avtobusni strani pomenilo vas 112 km stran (7. 9. 2026)

Iskanje sklada šumnike, zato je „celje" **točno** ime vasi **Čelje** pri
Ilirski Bistrici — in točno ime je bilo doslej vedno prvo. Posledica ni bila
le vrstni red v spustnem seznamu: `resolve_station()` vzame prvi zadetek, zato
je iskalnik zvez z vpisanim „Celje" tiho iskal iz **Čelja**.

| | postankov v voznem redu | lega |
|---|---|---|
| Čelje | **2** | 45,592 / 14,154 |
| Celje AP | **1 014** | 46,233 / 15,268 |

Razdalja med njima je 112 km.

Takih iskanj je na avtobusnem omrežju **26 od 5 361** (železniško nima
nobenega): „novo" je dalo postajo „Novo" (12) pred „Novo mesto" (631),
„krizan" pa „Križan" (31) pred „Križanke" (4 818).

**Prag je izmerjen, ne izbran.** Točni zadetek izgubi prvo mesto, kadar je
vsaj **20-krat** manj prometen od najboljšega:

| prag | spremenjenih prvih zadetkov |
|---|---|
| 10 | 49 — med njimi pari, ki so ISTI kraj („Boršt" proti „Boršt/Krki K") |
| **20** | **26** |
| 50 | 14 — „celje" ostane, „novo" pade ven |

Točni zadetek se ne skrije: gre na **drugo** mesto. Šumnika ni mogoče vtipkati
tako, da bi ga ločil od nešumnika, zato bi bila „Čelje" sicer nedosegljiva.

## Ob polnoči je tabla skrila vlake, ki so bili na poti (7. 9. 2026)

Vožnja, ki odpelje ob 23:50, ima svoje postanke ob 24:21 in pripada
**včerajšnjemu** prometnemu dnevu. Tabla pa je vprašala samo današnji dan,
zato je ob 00:30 na Laškem kazala šele vlak ob 01:58 — LPV 2007, ki je
pripeljal ob 00:56, ga ni bilo.

Obseg: čez polnoč sega **10 železniških** in **154 avtobusnih** voženj
(50 oziroma 2 241 postankov po polnoči). Najdlje vozeča se konča ob **33:48**
(avtobus) oziroma **26:23** (vlak).

**Prag ni trd.** `stats.se_vozi_vceraj()` ga vzame iz baze (`MAX(trip.end_s)`,
predpomnjeno po žigu GTFS uvoza) — ena nova nočna linija bi trdo številko
tiho podrla. Praktično to pomeni: železnica neha gledati včeraj po 02:23,
avtobusi po 09:48. Isto funkcijo uporablja tudi zemljevid, ki je to rešitev
imel že prej; zdaj je na enem mestu.

Rešeno z rekurzijo, ne z drugo poizvedbo: vse, kar sledi (meja meritve,
združevanje dvojnikov, običajna zamuda), mora teči nad **pravim** prometnim
dnevom, sicer bi bilo treba isti račun napisati dvakrat.

Cena, izmerjena na tabli s 150 vrsticami: ob 00:30 avtobusi 17,5 → 35,0 ms,
železnica 0,1 → 0,4 ms. **Podnevi nič** — ob 17:00 rekurzije ni (50,3 ms
prej in potem). Poizvedba je ozka sama po sebi: pri `from_s` čez 86 400 se
ujamejo samo postanki po polnoči.

Ista vrzel je bila v **iskalniku zvez**: vstopnih postankov med polnočjo in
tretjo uro je **2 145** (avtobusi) in **41** (vlaki), ponoči pa so pogosto
edini. `stats.connections()` zdaj pogleda včerajšnji dan po istem pragu; cena
ob 00:30 je 72,3 → 102,7 ms (avtobusi) in 2,3 → 4,5 ms (vlaki), podnevi nič.

Past, na katero se je treba paziti: rep se mora izračunati **pred** zgodnjim
`return []`. Kadar današnji dan nima nobene zveze, je včerajšnji rep edino,
kar sploh obstaja — in ravno tam je bila napaka najbolj vidna.

## Viri segajo različno daleč, prikaz pa je molčal (7. 9. 2026)

| vir | vozni red znan do | dni naprej |
|---|---|---|
| železnica | 2026-12-12 | 97 |
| avtobusi IJPP | 2027-12-31 | 481 |
| **mestni LPP** | **2026-09-15** | **9** |

Mestni LPP se uvaža v oknu osmih dni (cel mesec je 62 989 voženj in 1,6
milijona postankov). Posledica na zaslonu: iskanje na avtobusni strani za
čez dva tedna je vrnilo samo državni vozni red — brez besede o tem, da
česa manjka. Iskanje vlaka za junij 2027 je vrnilo „na ta dan ni vožnje",
kar zveni kot dejstvo o prometu, v resnici pa vozni red še ni objavljen.

Endpointa `/api/connections` in `/api/departures` zato vračata `vozni_red_do`
(in `lpp_do` pri avtobusih), prikaz pa oboje pove.

Ubeseditev je bila popravljena po prvem posnetku: „mestnih linij LPP ni" si
je nasprotovalo z značkami **LPP 25** tik pod njim. Linija 25 je namreč v
**obeh** virih — državni jo nosi kot primestno. Besedilo zato govori o
**viru**, ne o kategoriji linij.

## Večina živih avtobusov je bila skrita pod „drugi prevozniki" (7. 9. 2026)

`/api/vehicles` na produkciji, 18:40:

| `agency` | vozil | kam je padel na zemljevidu |
|---|---|---|
| `lpp` (mestni LPP) | **104** | „Drugi prevozniki" |
| `1123` Arriva | 33 | svoja plast |
| `1119` Nomago | 30 | svoja plast |
| `1118` LPP primestni | 9 | plast „LPP" |
| `1121` AP MS | 3 | svoja plast |

Torej **58 % vseh živih vozil** je bilo za stikalom, ki je privzeto ugasnjeno
in ne nosi imena prevoznika. Kdor je prižgal „LPP", je v Ljubljani videl devet
avtobusov — vsi primestni, večina zunaj mesta. Podatek je bil ves čas v
odgovoru; manjkal je le ključ `lpp` v `BUS_LAYERS`.

Po popravku isti pogled (Ljubljana, z13): števec LPP **124**, vrstica „Drugi
prevozniki" skrita, ker je števec 0.

## Zakaj je lega stara 1–2 minuti (7. 9. 2026)

Vprašanje je bilo, ali ni lega osvežena vsakih 40 s in torej največ toliko
stara. Ni — in nobena od sekund ni naša. Izmerjeno ob 18:59–19:03 na
`/app/bus/11` (mestni LPP) in naravnost na obeh feedih:

**Kar prikaz kaže na tem vozilu (zaporedna branja na 12 s):**
86 → 98 → 110 → 122 → 135 s, nato skok na 57 s. To je natanko en cikel.

**Od kod te sekunde, po členih:**

| člen | LPP (`sources/lpp/all`) | IJPP (`vehicle_positions`) |
|---|---|---|
| lega je stara že v feedu (glava − `vehicle.timestamp`) | mediana **35 s** (min 26, p90 50, max 54) | mediana **33 s** (p90 74, max 194) |
| kako pogosto se feed osveži | **~90 s** (n=99, mediana 90, min 69, max 111 — vsa vozila hkrati, torej paket) | polovica vozil se v 60 s ne premakne; premaknjenim mediana 40 s |
| glava feeda ob branju | stara 20–59 s | stara **1–2 s** |
| koliko doda naš zajem | **0 s** (izmerjeno: vseh 99 leg ima natanko isti `seen_ts` kot feed ta hip) | 0 s |

Torej: 35 s je lega stara, preden jo derp.si sploh zapakira, do 90 s traja, da
naredi nov posnetek, in do 30 s je naš cikel (`POLL_SECONDS`, LPP hodi po ritmu
zamud). Vsota se ujema z opaženim: najmanj ~57 s, največ ~147 s.

`seen_ts` je `vehicle.timestamp` iz feeda, ne čas našega branja — zato je
„lega stara N" poštena številka in prav zato ni videti lepše.

**Edino, kar je naše, je zadnjih do 30 s.** LPP feed **nima ne `ETag` ne
`Last-Modified`** (preverjeno v glavah), zato pogojna zahteva ni mogoča:
vsakih 30 s se prenese 315 682 B, kar je **909 MB/dan**, in ker se vsebina
spremeni le vsakih ~90 s, sta dve tretjini tega isti bajti. Pogostejši zajem
bi povprečno starost znižal za ~10 s in promet potrojil na 2,7 GB/dan.

## Ima LPP-jev lastni API lege in je hitrejši? (7. 9. 2026)

Vprašanje po meritvi starosti leg: novi vir mestnega LPP — ima GPS in se
osvežuje pogosteje od derp.si?

**Lege: ne.** Edina endpointa s koordinatami vozil sta še vedno zaprta,
preverjeno danes znova:

```
401  /api/bus/buses-on-route      {"message":"No permission for this API"}
401  /api/bus/bus-details
404  /api/bus/buses, /transit/api/vehicles, /transit/api/vehicle-positions
```

Koordinate, ki se v odprtih odgovorih **pojavijo**, so koordinate
**postajališč**, ne vozil (`arrivals-on-route`, `stations-on-route`).

**Napovedani prihodi: da, in precej.** Odprta endpointa, oba brez ključa:

| endpoint | kako pogosto se vsebina spremeni | cena |
|---|---|---|
| `/api/station/arrival?station-code=` | **30 s** (5 sprememb v 150 s, razmiki 30,3 / 30,3 / 30,3 s) | 14 kB |
| `/api/route/arrivals-on-route?trip-id=` | **10–20 s** (razmiki 20,2 / 10,1 / 20,2 / 10,1 / 20,2) | 25 kB, 57 ms, 39 postankov naenkrat |
| derp.si `sources/lpp/all` (kar beremo zdaj) | ~90 s | 315 kB |

Torej **3–9× hitreje od derp.si** — a to je `eta_min` v **celih minutah**, ne
lega. Zaokroževanje na minuto je ±30 s, kar je primerljivo s pridobljeno
svežino; kdor bo to gradil, mora oboje izmeriti skupaj, ne le svežino.

**Identifikatorji se ujemajo brez prevajanja.** `trip_id` pri `data.lpp.si` je
natanko **tretja komponenta** našega trojnega derp.si id-ja
(`a|b|093c945c-…` ↔ `093C945C-…`, velike črke). Na tabli Bavarskega dvora se
je 11 od 15 prihodov ujelo z našo tabelo `trip` na prvi poskus; štirje
neujeti so primestne linije (56, 3G, 25), ki pridejo iz IJPP z drugimi id-ji.

Za zajem cele mreže to ni uporabno (ena zahteva na vožnjo, ~276 živih), za
**odprto stran ene vožnje** pa je: en klic, 25 kB, vse postanke naenkrat.
Licenca `data.lpp.si` ostaja nenavedena — to je pogoj, ne podrobnost.

## Spoj z `data.lpp.si`: kaj se je izkazalo za resnično (7. 9. 2026)

| trditev | izmerjeno |
|---|---|
| njihov `trip_id` je **vzorec proge**, ne vožnja | 19 163 voženj LPP → **85** različnih tretjih komponent, najpogostejša 993× |
| `vehicle_id` je isti v obeh virih | naš `vehicle_now.vehicle_id` najden v njihovem odgovoru pri 4 od 8 (manjkajoči so vozila brez preostalih prihodov) |
| postajališča so ista | 704 od 714 se ujema **pod 5 m**, mediana razdalje **0,0 m**; imena enaka pri 711 |
| vrstni red postankov se ujema | ena vožnja linije 11: **39 od 39**, razdalja 0,0 m |
| koliko voženj sploh dobi svežo napoved | **19 od 25** svežih mestnih vozil ob 22:15 |

Najmočnejši dokaz, da spoj ni naključen: **meje se ujemajo**. Kjer naša
`stats.last_measured()` reče, da je vozilo pri postanku 9, njihova eta pokriva
postanke 10–27; pri meji 16 pokriva 17–21. Dva vira, ki se nista videla, se
strinjata o legi vozila.

Prva različica primerjave je pokazala razlike +20 in +14,6 min pri dveh
vožnjah — to je bila **moja napaka, ne vira**: vzel sem prvi prihod na
postajališču, ta pa pripada naslednjemu avtobusu iste linije. Z izbiro po
`vehicle_id` te razlike ni.

Kar s tem virom **ni** rešeno: starost lege. Koordinat vozil v odprtem delu
API-ja ni, zato ostaja 57–147 s iz prejšnjega razdelka.

## Vleka z maline je prerasla svojo skripto (7. 9. 2026)

`scripts/potegni.sh` je imel `timeout 900 scp`. Baza na malini je medtem
zrasla na **683 MB**, WiFi Pi Zerota pa da **~730 kB/s** — prenos torej rabi
~16 minut. Ob 23:05 je `timeout` ubil `scp` pri **655 MB od 683** in skripta
je zaradi `set -e` tiho odnehala: v dnevniku je ostalo „prenašam …" in nič
več. Videti je bilo, kot da še teče.

Popravek ni večja meja, ampak **`rsync --append-verify --partial`**: prenos se
da nadaljevati. Drugi poskus je prenesel manjkajočih 28 MB v 33 s. Kopija na
malini se ob neuspehu **ne izbriše**, zato je ponoven zagon poceni.

### Kaj je prilitje res prineslo

| korak | `obs` | `run` |
|---|---|---|
| malina → prenosnik | **+3 007 323** | +90 338 |
| prenosnik → arwen | **+6 309 794** | 1 010 766 → **1 249 005** |
| arwen `obs` skupaj | 6 740 872 → **13 050 666** | |

`repair` po prilitju: 3 535 popravljenih vrstic, **0 osirotelih meritev**.

### Merilo ni vsota, ampak pokritost

Vsota vrstic je zavajala: prenosnik jih je imel največ (1,15 M), a je bil
pogosto ugasnjen; malina jih je imela najmanj (962 k), a **neprekinjeno in
dlje nazaj**. Šele po prilitju obojega je pokritost taka:

| dan | ur z meritvijo |
|---|---|
| 2026-08-21 | 9/24 — prvi dan zajema |
| 2026-08-22 … 08-26 | **24/24** |
| 2026-08-27 | **16/24 — edina prava luknja** |
| 2026-08-28 … 09-07 | **24/24** |

Osem ur 27. 8. nima nobena od treh naprav; te ni več od kod dobiti.

Ob tem se je pokazalo še eno napačno branje: dnevi s tretjino običajnih
meritev (5. in 6. 9.) **niso izpad**, ampak **sobota in nedelja** — takrat
vozi mnogo manj avtobusov. Preden kdo lovi luknjo, naj pogleda dan v tednu.

### Kar je prilitje pokvarilo in kako je bilo popravljeno

Prilitje 6,3 milijona meritev ima dve posledici, ki ju je bilo treba ujeti
takoj — obe sta bili vidni šele **po** njem, ne med njim:

**1. WAL je zrasel na 902 MB in se ni imel kdaj zložiti nazaj.** Strežnik je
ves čas držal odprte bralne povezave, zato SQLite ni mogel narediti
checkpointa. Posledica: `/api/health` **15,4 s** in v dnevniku zajema
`database is locked` vsakih nekaj sekund. Popravek: ustaviti storitev,
`PRAGMA wal_checkpoint(TRUNCATE)` (12 s), zagnati nazaj — WAL 902 MB → 543 kB,
baza 973 MB → 1,52 GB. **Po vsakem velikem prilitju v živo bazo je to nujen
zadnji korak**, sicer je videti kot okvara.

**2. `MAX(feed_ts) FROM run` je postal 938 ms.** Ta poizvedba je vprašanje
„ali zajem še dela" in `/api/health` je ne sme predpomniti (prag „zajem stoji"
je 90 s). Pri 1,25 mio vrstic je bil to pregled cele tabele — in ker
`connections.js` kliče health vsakih 30 s na vsak odprt zavihek, je to
sekunda dela z diskom na zavihek na pol minute, na istem disku, kjer piše
zajem. Popravek je indeks `run_feed_ts`:

| | pred | po |
|---|---|---|
| arwen (1,25 mio vrstic) | 938 ms | — |
| razvojni računalnik | 65,9 ms | **0,1 ms** |

Poduk, ki velja naprej: **poizvedba, ki je bila poceni pri 800 000 vrsticah,
ni nujno poceni pri 1,25 milijona.** Po vsakem večjem prilitju izmeri
`/api/health` in tiste poizvedbe, ki se ne dajo predpomniti.

## Spletna kopija SQLite se ob pisanju začne znova (7. 9. 2026)

Selitev maline je obtičala in razlog je vreden zapisa, ker ni viden iz ničesar,
kar bi človek pogledal prvo.

`sqlite3 baza ".backup kam"` je **spletna** kopija: kadar kdo med njo piše v
izvorno bazo, se kopiranje **začne znova od prve strani**. Zajem na malini piše
vsakih 30 s, baza je 683 MB in kopija na SD kartici napreduje ~17 MB/min —
torej rabi ~40 minut. Kopija se v takih pogojih **ne konča nikoli**.

Kako je bilo videti: datoteka je 17 minut stala pri **190 873 600 bajtih**,
njen `mtime` pa se je ves čas osveževal. `sqlite3` je porabil 2:38
procesorskega časa in bil v stanju `D`. Videti je bilo kot počasen stroj, ne
kot zanka.

**Pravilo:** pred kopijo ustavi pisca. `deploy/preseli-malino.sh` zdaj ustavi
`sztrack-zajem` pred `.backup` in ga ob padcu prižge nazaj — stroj brez zajema
je slabši od stroja s starim imenom.

Ob tem odpadel še `gzip -1` na 683 MB: na Pi Zero W je to nekaj dodatnih minut,
prostora pa je 19 G in dnevne stisnjene kopije obstajajo posebej.

## Kar je bilo poceni pri 6,7 milijona, ni poceni pri 13 (8. 9. 2026)

Po prilitju je `/api/health` prek tunela odgovarjal **13,3 s**. Isti endpoint
je bil na arwenu lokalno 7 ms — razlike torej ni delal tunel, ampak **iztek
predpomnilnika**: kdor po 600 s prvi pride mimo, plača cel izračun.

Kaj števci stanejo na arwenu s **toplim** predpomnilnikom, po prilitju:

| poizvedba | čas |
|---|---|
| `COUNT(*) FROM obs` (13,05 mio) | **932 ms** |
| razrez po omrežjih (`run JOIN trip`) | **1 452 ms** |
| `COUNT(*) FROM run` | 29 ms |

To je natanko tisto, kar pravilo projekta prepoveduje — agregat čez vso
zgodovino v zahtevi. Popravek ni večji TTL (ta samo redkeje izpostavi istega
nesrečnika), ampak **postrezi staro, osveži v ozadju**: `_predpomni(...,
v_ozadju=True)` vrne prejšnjo vrednost takoj in novo izračuna v niti, pri čemer
ključavnica poskrbi, da teče ena osvežitev in ne ena na obiskovalca. Sinhrono
ostane samo prvi klic po zagonu, ko stare vrednosti še ni.

Pokrito z dvema testoma: da se stara vrednost res postreže in nova res
izračuna, in da se privzeto vedenje brez zastavice ne spremeni.

## Prometni dan je pri LPP zapisan v `trip_id` (8. 9. 2026)

Po selitvi malina mestnega LPP ni zajemala: `poll_lpp` je vračal `trips: 0`,
brez napake. Videti je bilo, kot da ponoči pač nič ne vozi.

Vzrok je v obliki id-ja. Trojni `trip_id` pri LPP ima **prometni dan v prvi
komponenti** — izmerjeno na arwenu: devet različnih prvih komponent, vsaka
~2 428 voženj, in vsaka pripada natanko enemu datumu:

| prva komponenta | dan |
|---|---|
| `6bec7600-…` | 2026-09-07 |
| `96959eb0-…` | 2026-09-08 |
| `ceec99e5-…` | 2026-09-09 |

Malina je uvozila ob 00:15 in dobila okno **od 8. 9. naprej**. Feed ob 01:10 pa
je govoril o vožnji z dne **7. 9.** — nočni avtobus, ki je speljal pred
polnočjo. Ujemanja ni bilo: `ujetih v trip: 0 od 1`.

Popravek: okno se začne **včeraj**, ne danes. Cena je en dan, ~2 400 voženj in
~62 000 postankov (celo okno je 19 163 voženj in 496 542 postankov na osem dni).

Arwen tega ni pokazal, ker je uvozil prejšnji dan opoldne in ima 7. 9. v oknu.
Napaka bi se torej pokazala šele ob prvem uvozu tik po polnoči — in bi bila
videti kot mirna noč.

### Malina po selitvi, izmerjeno

| kaj | vrednost |
|---|---|
| uvoz voznega reda (IJPP + LPP) | ~50 min, **vrh RSS 213 MB** od 427 + 426 swapa |
| vozni red po uvozu | 32 478 voženj (19 163 LPP mestni, 5 402 Arriva, 4 823 Nomago, 1 569 LPP primestni, 789 SŽ, 732 AP MS) |
| postankov | 496 542 |
| baza | 683 → 696 MB, disk 18 G prost |
| selitev | 962 951 → 962 951 meritev |

## Prikaz je trdil dogodek, o katerem ni imel novic (8. 9. 2026)

Uporabnik je stal na Ljubljani Polje, aplikacija pa je za LPV 2001 kazala
**„+6 min · izmerjeno · vlak je tu že bil"**. Kaj je vlak res počel, iz naših
podatkov **ni ugotovljivo** in tu tega ne domnevamo. Ugotovljivo je dvoje
drugega, in oboje je bilo narobe pri nas.

**1. Meja meritve je prehitevala feed.** Postanek je veljal za prevožen, ko je
bil „vozni red plus zadnja znana zamuda" mimo. To je ura, ne meritev: ko feed
o vožnji utihne, se pogoj sam od sebe razširi do konca proge. Ob 07:04 je
prikaz trdil, da je vlak prevozil **vseh 29 postankov**, vključno s prihodom v
Ljubljano ob 07:01. Meja je zdaj zamejena z zadnjo besedo feeda o tej vožnji.

Varno je izmerjeno: vožnje, ki so **v** feedu, so sveže — mediana **45 s**,
p90 59 s, največ 343 s (733 voženj). V normalnem obratovanju to ne spremeni nič.

**2. Tišine feeda prikaz ni povedal.** Kaj je feed rekel o tej vožnji:

| ura | postanek | vrednost |
|---|---|---|
| 06:43:25 | Ljubljana Zalog | +6 |
| 06:51:52 | Ljubljana (končna) | **0** |
| 06:52:56 | Ljubljana Polje | +6 |
| 06:54:22 | Ljubljana | +6 |
| — | — | **24 minut tišine** |
| 07:18:53 | Ljubljana | **+29** |

Ob 07:00 je bila zadnja novica o vlaku stara **7 minut**, prikaz pa je pisal
„pred 5 min" — to je bila starost *domnevnega prehoda* (vozni red + zamuda),
ne starost novice. Zdaj se pokaže tišina: „o vlaku 15 min ni novic — to je
zadnja znana številka, ne trenutna", prag **180 s** (trikratnik izmerjenega
ritma osveževanja).

**Kar ostaja nerešeno in je vredno zgraditi:** feed **prevožene postanke
izpušča** — vsaka preverjena železniška vožnja ima v sporočilu le okno
postankov pred vozilom (LP 4201: 26–29 od 31; LPV 2402: samo 14 od 17). Izpad
postanka iz okna je torej **opazovan dogodek prehoda**, ne aritmetika z
zamudo. Tega ne beležimo, zato takega vprašanja za nazaj ni mogoče razrešiti.

### Koliko je takih voženj (8. 9. 2026, zadnjih 14 dni)

Vprašanje po LPV 2001: je bil to izjemen primer? Merilo: za vsak postanek
primerjaj vrednost, ki bi jo prikaz **kazal ob domnevnem prehodu** (zadnja
izjava feeda do tedaj), s **končno** vrednostjo istega postanka.

| | železnica | avtobus |
|---|---|---|
| primerjanih postankov | 81 798 | — |
| postankov, popravljenih za ≥ 5 min | 118 (**0,14 %**) | 25 691 |
| postankov, popravljenih za ≥ 10 min | 51 (0,06 %) | — |
| **voženj z vsaj enim takim postankom** | 113 od 6 948 (**1,63 %**) | 11 682 od 63 136 (**18,50 %**) |

**Prevladujoča oblika ni tista, ki jo je pokazal LPV 2001.** Pri železnici je
**90 od 118 popravkov (76 %) izhajalo iz prikazane NIČLE** — prikaz je trdil
„točno", resnica pa je bila do **+66 min**. Pri avtobusih je takih 17 %
(največja +647 min, kar je že znani vzorec „ura namesto zamude").

Najhujši primeri, vsi z istim podpisom:

```
2026-08-26  LP 3191   postanek  9: videno +0 -> na koncu +66 min
2026-09-04  LPV 2271  postanek 12: videno +0 -> na koncu +34 min
2026-08-27  LP 3387   postanek  2: videno +0 -> na koncu +29 min
```

Obstoječi varovalki tega ne ujameta: `is_zero_blip` in pogoj
`NOT (delay_s = 0 AND prev_max >= 300)` se sprožita šele, kadar je kak
**prejšnji** postanek že kazal veliko zamudo. Pri postanku 2 ali 6 pred njim
ni ničesar, kar bi sprožilo sum.

**Edino, kar bi to res rešilo, je zapis okna feeda.** Feed prevožene postanke
izpušča; dokler je postanek v sporočilu, vozilo mimo njega ŠE NI. To velja
enako za ničlo kot za +6 in ne zahteva nobene domneve o velikosti zamude.

## Koliko časa res hodiš do postajališča (8. 9. 2026)

Za iskanje poti od vrat do vrat je hoja polovica odgovora. Vprašanje je bilo,
ali zadošča zračna razdalja s stalnim faktorjem obvoza.

**Prvi poskus umeritve iz naših podatkov ne odgovori na vprašanje.** Razmerje
med potjo po `shape` polilinji in zračno črto med **sosednjima postajališčema
iste linije**, 42 869 parov:

| razdalja | parov | mediana | p90 |
|---|---|---|---|
| < 300 m | 1 095 | 1,21 | 2,44 |
| 300–800 m | 14 760 | 1,06 | 1,49 |
| > 800 m | 27 014 | 1,07 | 1,33 |

Mediana 1,07 — a to meri cesto med dvema postajališčema, ki po definiciji
ležita na isti cesti. Pešec, ki gre od hiše do postaje, ni na tej cesti.
Ta številka je torej **prenizka**, ne previsoka, in za rezervo neuporabna.

**Prava umeritev proti pešpotim.** Naključne točke po Sloveniji do svojih
najbližjih postajališč, primerjava zračne črte s pravo pešpotjo (OSRM, peš
profil). Dva neodvisna vzorca:

| vzorec | parov | mediana | p75 | p90 | največji |
|---|---|---|---|---|---|
| javni OSRM, razvojna baza | 211 | 1,42 | 1,85 | 2,55 | 4,76 |
| naš OSRM, arwenova baza | 1 080 | 1,43 | 1,83 | 2,63 | **7,86** |

Obvoz ni šum, ampak **ovire** — Sava, proga, avtocesta. Postajališče 300 m
stran po zraku je lahko 1 400 m hoje.

| faktor | pokrije primerov |
|---|---|
| 1,2 | 30 % |
| 1,3 | 41 % |
| 1,45 | **52 %** |
| 1,6 | 65 % |

Ena konstanta torej ne more biti hkrati varna in uporabna: 1,45 podceni pot v
48 % primerov (potnik zamudi avtobus), 2,63 pa bi iz 500 m naredila 15 minut
hoje in stran bi zavračala dosegljive povezave.

**Zato hoja teče čez svoj usmerjevalnik** (`kajros/hoja.py`, `deploy/osrm.sh`).
Faktor ostane le kot zasilna pot in je zato **p75 (1,85), ne mediana** — brez
usmerjevalnika velja pravilo budilke, da potnik ne sme zamuditi. Izmerjeno na
831 parih, kaj ta zasilna ocena naredi: mediana **+366 s predolga**, p10 −814 s,
in v 15 % primerov je še vedno prekratka. To je cena tega, da nečesa ne merimo.

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

Troje, kar je meritev pokazala in bi se sicer domnevalo:

* **Naš strežnik vrne isto kot javni** — 412,8 m do decimalke. „Samo za demo"
  je bila omejitev gostitelja, ne programa.
* **Peš profil hodi 5,00 km/h**, kar je natanko hitrost, ki jo je zahteval
  David. `duration` je torej že prava številka in je ni treba računati.
* **Peš nedosegljivih postajališč ni** — 0 od 831. Ravnanje za `null` v matriki
  vseeno obstaja, ker bi bila tiha ničla videti kot „nič hoje".

Meja velikosti matrike je bila preizkušena do 300 koordinat brez napake;
privzetek ni dokumentiran, zato ga `deploy/osrm.sh` nastavlja izrecno na 1 000.

## Doseg hoje: 25 minut je zastonj (8. 9. 2026)

Pričakovanje je bilo, da večji doseg podraži iskanje. Ne podraži ga — cena je v
premetavanju voznega reda, ne v številu izhodiščnih postajališč.

| primer | 10 min | 15 min | 20 min | 25 min |
|---|---|---|---|---|
| Bavarski dvor → Vič | 08:27 | 08:25 | 08:24 | **08:24** |
| Grosuplje → LJ center | 09:07 | 08:57 | 08:57 | **08:57** |
| Bohinj → Kranj | 10:26 | 10:26 | 10:22 | **10:22** |
| čas iskanja | 259–283 ms | 252–441 ms | 263–305 ms | 267–316 ms |

Pri Bavarskem dvoru gre število izhodišč s 16 na 73 in iskanje ostane enako
hitro; pri Grosuplju je prihod **10 minut boljši**, ker je bilo pravo
postajališče 11 minut hoje daleč.

Kandidatov v polmeru 2 083 m (25 min × 5 km/h): Bavarski dvor **201**,
Ljubljana Polje 66, Grosuplje 27, Bohinjska Bistrica 9.

## Iskanje od vrat do vrat, prototip (8. 9. 2026)

Prototip čez **obe omrežji hkrati**, štiri noge, hoja na obeh koncih,
peš prestopi med postajališči do 300 m:

| primer | izhodišč | ciljev | iskanje |
|---|---|---|---|
| Bavarski dvor → Vič | 44 | 12 | 314 ms |
| Grosuplje → LJ center | 13 | 47 | 312 ms |
| Bohinj → Kranj | 5 | 13 | 280 ms |
| Ljubljana Polje → Maribor | 3 | 6 | 225 ms |

Vozni red obeh omrežij za 8. 9. 2026 je **255 245 postankov** v 12 963 vožnjah;
naloži se v 1,74 s in zadrži 94 MB (vrh 131 MB).

Preverjeno na roko, da izid ni naključje: Grosuplje → Ljubljana center ob 8:00
= 416 m hoje (6,5 min) → LP 3232 ob 08:17 → Ljubljana 08:44 → 982 m hoje
(15,3 min) → **08:59**. Prototip vrne isto minuto.

**Peš vso pot je včasih hitreje.** Ljubljana Polje → BTC ob 8:00 z avtobusom
pomeni prihod 09:04; hoja je 47 minut, torej 08:47. Stran, ki tega ne pove,
pošilja ljudi na počasnejšo pot.

### Peš povezave med postajališči

| doseg | povezav | najbolj povezano postajališče |
|---|---|---|
| 150 m | 5 609 | 7 sosedov |
| 300 m | 7 314 | 14 sosedov |
| 500 m | 12 070 | 25 sosedov |

Brez teh se prestopa **samo na istem `stop_id`** — „Bavarski dvor" v eno smer in
v drugo za iskalnik nista isti kraj. Takih imen je **4 507 od 5 500**.

Izmerjeno, ko so bile poti res izračunane (`kajros pespoti`, 8. 9. 2026):

| | |
|---|---|
| postajališč s peš sosedom v 500 m | 9 970 od 10 509 |
| shranjenih poti (usmerjenih, ≤ 6 min) | **20 060** |
| od tega isto ime, torej čez cesto | 10 890 (54 %) |
| imen, ki dobijo soseda z drugim imenom | 1 781 |
| trajanje | mediana 1,6 min, p90 5,4 min |
| gradnja prek tunela do arwena | 97 s |

Primer, ki je bil doslej neviden: „Bavarski dvor" → „Bavarski dvor" (druga
smer) je **133 s hoje**, 169 m po zraku. In primer, zakaj zračna razdalja ne
zadošča niti tu: „Bavarski dvor" → „Gosposvetska" je 99 m po zraku in 115 s
hoje — obvoz 1,61×.

## Iskanje od vrat do vrat: kaj je bilo narobe, preden je delalo (8. 9. 2026)

`kajros pot --od lat,lon --do lat,lon`. Izmerjeno s toplimi predpomnilniki, čez
obe omrežji, hoja iz OSRM prek tunela do arwena:

| primer | izhodišč/ciljev | čas | predlogov |
|---|---|---|---|
| Grosuplje → LJ center | 25 / 120 | 179 ms | 2 |
| Ljubljana Polje → BTC | 19 / 62 | 193 ms | 2 |
| Bavarski dvor → Vič | 120 / 87 | 282 ms | 2 |
| Bohinjska Bistrica → Kranj | 7 / 50 | 99 ms | 2 |
| Maribor → Koper | 21 / 11 | 720 ms | 2 |

Prvi izid, ki ga druga slovenska orodja ne dajo — Maribor → Koper vključi
**4 minute hoje z železniške postaje Ljubljana na avtobusno**, ker je vlak do
Ljubljane in avtobus naprej hitrejši od same železnice.

### Štiri napake, ki jih je bilo treba popraviti

**1. Iskanje po postajah v SQL je bilo 629 ms.** Poizvedba „katera
postajališča so blizu in ta dan kaj strežejo" je šla čez `JOIN sched JOIN trip
JOIN service_day`. Ista stvar v Pythonu, z množico postajališč iz **že
naloženega voznega reda**, je 7 ms. Vozni red se za iskanje tako ali tako
naloži; nova poizvedba je bila delo, ki je bilo že opravljeno.

**2. Brez obrezovanja po meji je iskanje 510 ms, z njim 7 ms.** Zgornja meja
je čas hoje vso pot (kadar obstaja) in se med iskanjem stiska ob vsakem
doseženem cilju. Brez nje zadnja kroga premetavata pol države, ki je ne bo
nihče videl. Izid je do minute isti.

**3. Krogi niso omejevali nog — v obeh iskanjih.** Z eno samo tabelo
najboljših prihodov se ob poznejši izboljšavi prepiše tudi starš postajališča
in veriga nazaj preskoči kroge. Izmerjeno na Maribor → Koper: pri meji **dveh**
nog je iskanje vrnilo pot s **štirimi** vožnjami.

To ni bila samo netočna dokumentacija. `journey.plan()` ima varovalko
`len(legs) > max_legs: return []` — torej je predolgo verigo **tiho zavrgel**
in veljavna pot je izginila brez sledu. Oboje je zdaj RAPTOR z oznakami po
krogih (`tau[k]` = najzgodnejši prihod z največ k vožnjami).

Popravek `journey.plan()` ne poslabša izida: vzorec 80 naključnih parov
železniških postaj da **4 % brez odgovora**, kar je natanko zapisana številka
izpred popravka, in vsi trije dokumentirani primeri še delajo (Ljutomer mesto
→ Ribnica 3 prestopi, Stara Cerkev → Prevalje 3, Narin → Kranj 2).

**4. Za Maribor → Koper je usmerjevalnik računal 200 km dolgo pešpot**, samo
da jo je iskanje takoj zavrglo. Zračna črta je spodnja meja poti: če je že ona
daljša od tega, kar je peš mogoče, se usmerjevalnika ne vpraša.

### Kar se v izidu vidi in ni napaka

* **Dve hoji zapored** nastaneta, kadar pot s postajališča pelje čez peš
  prestop na drugo in šele od tam do vrat. Za potnika je to ena hoja, zato se
  zlijeta; vmesno postajališče je brez pomena, minute ne.
* **Hoja nič minut** je postajališče pred vrati. Ni noga, ampak šum.
* **Ista pot iz dveh vprašanj.** „Najhitreje" in „z manj hoje" data lahko isto
  vožnjo z drugačnim repom; ključ za razdvajanje so zato **samo vožnje**, ne
  ure — te se razlikujejo za pol minute.

## Zamude v poti od vrat do vrat (8. 9. 2026)

Iskanje teče po voznem redu, ker napovedi za vožnjo čez pet ur ni; zamuda se
pripiše šele na koncu in veriga se z njo prebere znova.

Pravilo, katera številka velja, je **izluščeno in ne prepisano**:
`stats.zamuda_na_postanku()` zdaj uporabljata iskalnik zvez in ta stran.
Preverjeno, da izluščenje ničesar ne spremeni — `/api/connections` za isto
poizvedbo vrne **bajt za bajt isti odgovor** (18 346 B).

Prvi izid v živo (RG 432, Litija → Ljubljana, 8. 9. ob 12:35): vozni red
12:35 → 13:07, z zamudo **12:58 → 13:31**, žeton „+23 min · ocena". Potnik ima
torej triindvajset minut več, preden mora od doma — in to je edino, zaradi
česar ta stran obstaja.

Preostanek prestopa se računa iz **zaokroženih minut**, ne iz sekund:
`ostane = načrtovano − zamuda prvega + zamuda drugega`. Vse tri številke
stojijo na zaslonu druga ob drugi in bralec, ki jih sešteje, mora priti do
iste — ista past kot pri razredu zamude.

## Kaj je pokazal zaslon, česar meritev ni (8. 9. 2026)

Stran `/app/pot` je v produkciji ponudila **dva predloga, od katerih je bil
drugi po vseh merilih slabši**: Grosuplje → Zmajski most, 12:53 z 20 minutami
hoje poleg 13:01 z 10 minutami, oba s prihodom 13:31. Odideš prej, hodiš
dvakrat dlje, prideš ob isti minuti.

Vzrok: vprašanje „z manj hoje" omeji hojo na **vsakem koncu posebej** (10 min
tja, 10 min nazaj), ne v vsoti — zato zna dati pot z več hoje skupaj. Zdaj
odpade vsak predlog, ki je po vseh štirih merilih (odhod, prihod, hoja,
prestopi) slabši od že izbranega.

Posledica je bila, da je ostal en sam predlog. Zato so dodani **naslednji
odhodi**: dve nadaljnji iskanji z začetkom minuto za prvim odhodom. To je
poceni, ker sta peš matriki že izračunani in vsako nadaljnje iskanje je le še
krog čez vozni red. Izid za isto vprašanje: 13:00 (avtobus 69), 13:27 (LP 3296
+ 3B) in 13:40 — namesto ene ure.

### Zmogljivost v produkciji (arwen)

| | čas |
|---|---|
| prvi klic po zagonu (hladen vozni red) | **14,7 s** |
| topel klic | **0,85 s** |
| ogrevanje v ozadju (`server._ogrej_pot`) | 9,6 s |

Prva zahteva po zagonu je bila **26,5 s**, ker je tekla vzporedno z ogrevanjem
in isti vozni red naložila še enkrat. Ključavnica na ključ (ne skupna) je to
znižala na 14,7 s — toliko, kolikor traja eno nalaganje.

`_TT_CACHE_MAX` je z dveh na tri: pot bere obe omrežji hkrati, iskalnik zvez
pa vsako posebej, in pri dveh vnosih je vsako iskanje zvez izrinilo skupno
sliko. Cena je majhna, ker je železnica drobna — avtobusi 92 MB, oboje skupaj
94 MB, železnica ~3 MB.

## Vrstni red predlogov je nasprotoval številkam v njih (8. 9. 2026)

Prijava s testiranja: Križanke → Novo Polje ob 12:51 je ponudil štiri avtobusne
poti in **nobene z vlakom**, čeprav je vlak prišel prej. Preverjeno na roko:

| pot | vozni red | z zamudo |
|---|---|---|
| avtobus 19B + 25 | 12:52 → **13:35** | 12:51 → **13:43** |
| vlak LPV 2219 | 13:01 → **13:38** | (brez meritve) 13:38 |

Vzroka sta bila dva in oba sta bila napaka:

**1. Razvrščanje po voznem redu, prikaz z zamudo.** Stran je razvrstila po
voznoredni uri (13:35 < 13:38) in poleg izpisala pričakovano (13:43). Vrstni
red in številke so si nasprotovali — ista past kot barva, ki pripoveduje drugo
zgodbo kot številka poleg nje. Zdaj se zamude pripišejo **pred** razvrščanjem
in ključ je ura, ki je na zaslonu.

**2. Druge poti sploh ni bilo med predlogi.** Nadaljnja iskanja so gledala
poznejše odhode, ne drugih poti. Zdaj je med predlogi tudi iskanje, ki
**izloči vožnje najboljše poti** — tako pride na zaslon vlak, tudi kadar
avtobus po voznem redu zmaga za tri minute.

### Zamude v samem iskanju: izmerjeno, in ni zmaga

Ob tem je bil preizkušen tudi prenos znane zamude v samo iskanje (vozila, ki so
zdaj na poti, odpeljejo z izmerjeno zamudo). Na 39 naključnih parih v Ljubljani:

| | |
|---|---|
| boljši pričakovani prihod | 1 |
| slabši | 1 |
| enak | 37 |
| mediana razlike | 0,0 min |
| cena | +85 ms na iskanje |

Torej **ni** izboljšava prihoda. Obdržano je iz drugega razloga: brez tega
iskanje ponuja prestope, za katere iz meritev **že vemo, da ne držijo** — na
183 ponujenih prestopih 1 (1 %), z zamudami 0 od 175. In ker so zamude na
zaslonu, bi razvrščanje po voznem redu spet delalo vrstni red, ki nasprotuje
številkam.

Vozila, ki še ne vozijo, zamude nimajo in se obravnavajo kot točna — to velja
za obe različici. `zamiki()` je predpomnjen na žig zajema, ker je izračun za
vseh 13 107 voženj dneva 541 ms.

### Odhodi, ki so že odpeljali, se preskočijo

`at_stop` je urejen po odhodu, iskanje pa je za vsako postajališče v čelu
prehodilo **vse dnevne odhode** in šele nato zavrglo tiste pred potnikovim
prihodom. Z dvojiškim iskanjem (`bisect`) se začne pri prvem odhodu, ki je še
lahko naš — največ `MAX_ZAMIK_S` (60 min) pred prihodom, ker vožnja z zamudo
odpelje pozneje, kot piše.

| primer | prej | zdaj |
|---|---|---|
| Križanke → Novo Polje | 633 ms | **299 ms** |
| Bavarski dvor → Vič | 575 ms | **303 ms** |
| Maribor → Koper | 569 ms | **429 ms** |
| Grosuplje → LJ center | 228 ms | **180 ms** |

Ista meja obreže tudi zamike same: 482 minut ni zamuda, ampak feedova
zamenjava prometnega dne (isti razlog kot `api.MAX_LIVE_DELAY_S`).

## Zakaj je iskanje postaje trajalo pet sekund (8. 9. 2026)

Prijava s testiranja: vpis imena postaje je čakal več kot pet sekund.

| poizvedba | čas (razvojni) |
|---|---|
| `/api/stations/search?q=ljublj&network=zeleznica` | 0,05 s |
| `…&network=avtobus` | 0,55 s |
| `…&network=vse` | **1,35 s** |

Stran s potjo išče čez **obe** omrežji, in to na vsak pritisk tipke; arwen je
pri takih poizvedbah ~3–4× počasnejši, torej okoli pet sekund. Iskalnik zvez
tega nikoli ni delal tako — kazalo naloži enkrat in išče v brskalniku.

Zdaj enako tu: `/api/stations/index?network=vse&koordinate=1` je **323 kB**,
hrani se 12 h v `localStorage`, in strežnikov predpomnilnik ga postreže v
**3,6 ms** (hladno 1,6 s, enkrat na uvoz voznega reda). Razvrščanje je isto
kot na strežniku (`iskalnikKazala()`), sicer bi ista črka dala dva različna
seznama.

Kazalo nosi tudi lego — postajališče z **največ prometa** pod tem imenom.
Naključno izbrano bi pri „Bavarski dvor" enkrat dalo eno stran ceste in enkrat
drugo.

## Tabla je ponavljala vrednost, ki jo je okno vožnje zavrglo (8. 9. 2026)

Straža `tabla in okno vožnje ista številka` je večkrat pokazala isto: linija 8
na Bavarskem dvoru, tabla „izmerjeno −1 min", okno vožnje „neskladno".
Preverjeno, da pade **tudi na kodi izpred vseh sprememb tega dne** — torej ni
šlo za regresijo, ampak za zapisano omejitev: `_LAST_MEASURED_SQL` nosi le
**lokalni** del pravila, ker teče nad vsemi vožnjami hkrati.

Tabla je imela svojo, krajšo različico pravila (primerjava z zadnjo meritvijo),
okno pa celo verigo (`stats.oznaci_neskladne`). Zdaj tudi tabla uporablja celo
verigo: `journey._neskladni_postanki()` prebere `run` za vse vožnje s table v
**eni** poizvedbi in požene isto funkcijo po vožnjah. Tabla prometnega mestnega
postajališča ima do devetdeset voženj, zato ena poizvedba in ne ena na vožnjo —
izmerjeno ostane 49 ms (Ljubljana) in 96 ms (Bavarski dvor).

Kaj tabla pokaže namesto zavrnjene vrednosti: **zadnjo skladno meritev in kje
je bila** — „+4 min, izmerjeno na postaji Tivoli". To ni nasprotje z oknom,
ampak razkritje, zato je bila popravljena tudi straža: napaka je le, kadar
tabla **ponovi** vrednost, ki jo je okno zavrglo (`delay_from` ni nastavljen).

Kolikokrat pravilo prime, izmerjeno na celem dnevu (12 371 voženj, 237 675
postankov):

| | neskladnih postankov | voženj z vsaj enim |
|---|---|---|
| avtobusi | 5 012 / 230 665 (2,17 %) | 1 621 / 11 775 (13,8 %) |
| železnica | 17 / 7 010 (0,24 %) | 15 / 596 (2,5 %) |
| skupaj | 5 029 (2,12 %) | 1 636 (13,2 %) |

## Predlog, ki je bil ovinek namesto poti (8. 9. 2026)

Prijava s preizkusa: iz Ljubljane Polje proti vzhodu je stran predlagala vlak
**na zahod** v Ljubljano in nato **8,8 km (1 h 46) peš nazaj** — dve uri za
pot, ki jo prehodiš precej hitreje.

**Vzroka nisem dokazal.** Preverjeno je bilo dvoje in oboje je bilo v redu:
`blizu()` spoštuje mejo hoje na **obeh** straneh (največja vrnjena vrednost je
natanko 1 500 s = 25 min, izmerjeno na 30 točkah), in podrobna stran vrne isto
kot seznam (30 parov, največja razlika v skupni hoji **0 min**).

Vgrajeni sta zato dve varovalki, ki nesmisel te oblike naredita nemogoč ne
glede na vzrok:

* **Pot z vozilom, v kateri je hoje več, kot bi je bilo peš vso pot, ni
  predlog.** Za to je bilo treba trajanje hoje računati tudi takrat, ko je
  hoja predolga, da bi jo ponudili (`MAX_PES_PRIMERJAVA_S` 3 h proti
  `MAX_PES_VSO_POT_S` 1 h) — brez te številke primerjave ni mogoče narediti.
* **Kadar z vozilom ni ničesar, se pove, koliko je peš.** „Ni poti" je slabši
  odgovor od resnice „peš 1 h 25"; potnik sicer čaka avtobus, ki ne pride.

Preizkušeno na vzorcu iz prijave: (46,073, 14,582) → (46,076, 14,615) zdaj da
samo hojo 44 min, prej pa je isti vzorec dal pot z vozilom in dolgo hojo.

## Ali je meja hoje do postaje sploh potrebna (8. 9. 2026)

David je vprašal, ali polje „največ hoje" rabiva. Izmerjeno na 40 parih točk
(1,5–25 km narazen, jutranja konica, obe omrežji):

| meja | poti z vozilom | hoje mediana | hoje p90 | prihod proti 45 min |
|---|---|---|---|---|
| 10 min | 11/40 (28 %) | 16 min | 19 min | **enak** |
| 15 min | 15/40 (38 %) | 18 min | 30 min | **enak** |
| 20 min | 23/40 (58 %) | 23 min | 35 min | **enak** |
| **25 min** | **30/40 (75 %)** | **28 min** | 48 min | **enak** |
| 30 min | 32/40 (80 %) | 33 min | 51 min | **enak** |
| 35 min | 35/40 (88 %) | 37 min | 54 min | **enak** |
| 45 min | 38/40 (95 %) | 40 min | 59 min | — |

**Meja ne vpliva na uro prihoda** — mediana razlike je pri vsaki vrednosti
**0 minut**. Ne gre torej za izbiro med „hitreje" in „manj hoje", ki bi jo
lahko rešil algoritem sam; meja odloča o tem, **ali odgovor obstaja in koliko
hodiš**.

Zato ostane. Brez nje bi bilo treba izbrati eno številko za vse: pri 45 vsi
hodijo 40 minut, pri 25 četrtina ne dobi ničesar. Preverjena je bila tudi
tretja pot — iskati vedno na 45 in med predlogi vedno ponuditi tudi pot z malo
hoje: **ne gre**, ker je taka pot med predlogi le v **2 primerih od 38**.
Takih poti večinoma ni in razvrščanje ne more nadomestiti omejitve.

Cena večje meje je nič: iskanje je pri 25 min 293 ms in pri 45 min 315 ms.

Koraki v izbirniku so po tej meritvi: 10 / 15 / 25 (privzeto) / 35 / 45 in
„po meri". Med 25 in „po meri" prej ni bilo ničesar, čeprav se prav tam
odgovor najbolj spremeni.

## Prehoda vlaka se iz teh podatkov ne da ugotoviti (9. 9. 2026)

Drugič v dveh dneh: prikaz je ob 06:53 trdil, da je LPV 2001 že bil v Ljubljani
Polje; David je bil na peronu in vlak je prišel ob **07:05**. Kaj je feed
govoril:

```
06:37:28  Laze (26)             +4 min
06:42:28  Ljubljana Zalog (27)  +4 min
06:50:13  Ljubljana Polje (28)  +4 min   <- zadnja beseda o Polju
06:52:16  Ljubljana (29)         0 min
06:53:43  Ljubljana (29)        +4 min
07:03:43  Ljubljana (29)       +15 min   <- resnica, 13 minut prepozno
```

Feed je Polje zamrznil na +4 **minuto po voznem redu** in ga ni nikoli popravil;
popravil je samo končno postajo, ob 07:03. Vrednost torej ni bila zastarela,
ampak napačna, in do 07:03 ji ni nasprotovalo nobeno opažanje.

**Pet možnih signalov, vsi izmerjeni, vsi odpovejo:**

| signal | izid |
|---|---|
| tišina feeda (popravek 8. 9.) | feed ni molčal — zadnja beseda 06:53:43 |
| potrditev postanka **po** prehodu | železnica **0,4 %** postankov (avtobusi 68 %) |
| obvestila SŽ s krajem | zadnji kraj 06:28 (Kresnice), naslednji 07:04 |
| rob okna feeda | **0 izpadov** pri 39 vožnjah v 11 min; 69/69 postankov, ki jim je vozni red mimo, ostane v oknu |
| „nerazrešena ničla" za kasnejši postanek | pred napačnimi trditvami **redkejša** (7 %) kot pred pravilnimi (24 %); natančnost 3 % |

Zadnji dve sta bili včeraj zapisani kot obetavni; obe sta zdaj **zaprti** in
naj se ne lovita znova.

**Obseg danes:** 180 od 1 967 železniških postankov z dnevnikom (**9,2 %**) je
bilo pozneje popravljenih za ≥ 5 min navzgor; prizadetih 66 od 174 voženj.

**Kaj iz tega sledi.** Če prehoda ni mogoče zaznati, popravek ne more biti
boljše zaznavanje, ampak poštenejša trditev. Beseda „izmerjeno" za prevožen
postanek pri železnici trdi opažanje, ki ga v **99,6 %** primerov nimamo.

### Kaj je popravek stal (9. 9. 2026)

„Izmerjeno" ostane samo tam, kjer je feed vrednost potrdil po prehodu:

| omrežje | postankov | ostane „izmerjeno" | postane „zadnji podatek" |
|---|---|---|---|
| železnica | 2 007 | **6 (0,3 %)** | 2 001 (99,7 %) |
| avtobusi | 72 076 | 50 166 (69,6 %) | 21 910 (30,4 %) |

Pri vlakih torej beseda skoraj povsod izgine — in prav to je bila ugotovitev:
tam je bila trditev o opažanju, ki ga nimamo.

### Koliko je feed zgrešil in ali bi pomagala zadnja beseda o vožnji

O Ljubljani Polje je feed 9. 9. povedal **eno samo stvar**: ob 06:50:13 prihod
ob 06:52:00 (+4 min). Nikoli je ni popravil. David je bil na peronu: vlak je
prišel ob **07:05:00**. Razlika **780 s = 13 minut**.

Zadnja beseda o **vožnji** (+15 min v Ljubljani, ob 07:03:43) bi na Polju
pomenila prihod 07:03 — torej **120 s** od resnice. Feed je vedel, le da tega
ni zapisal na Polje.

**Zato preizkušeno in NE uvedeno:** za nepotrjen postanek vzeti zadnjo besedo
o vožnji s poznejšega postanka.

| različica | primerov | boljša | slabša |
|---|---|---|---|
| vedno | 1 662 | 195 | **921** |
| le če je poznejša za ≥ 5 min večja | 558 | 56 | **497** |
| ≥ 7 min | 410 | 34 | 372 |
| ≥ 10 min | 293 | 22 | 268 |

Zamuda po potnikovi postaji običajno **zraste upravičeno**, zato prenos nazaj
škodi. Pošteno pa je treba povedati **omejitev merila**: za „resnico" je vzeta
končna vrednost naslednjega postanka, ta pa je pogosto zamrznjena iz istega
trenutka kot merjena — merilo je torej nagnjeno v korist zamrznjene vrednosti.
Edina prava resnica, ki jo imamo, je Davidova ura, in ta govori nasprotno.

**Kar iz tega sledi:** ugibati se ne izplača, povedati pa je treba. Kadar
zadnja beseda o vožnji močno odstopa od številke za potnikovo postajo, naj
prikaz pokaže **obe** — brez trditve, katera drži.

## Kaj stane štetje obiska (12. 9. 2026)

Projekt o sebi ni vedel ničesar: strežnik ni beležil zahtev, pred njim pa je
Cloudflarov tunel, ki svojega dnevnika ne da. `obisk.py` zato šteje v
pomnilniku in enkrat na minuto zapiše v bazo.

**Cena na zahtevo je 0,11 ms** (mediana, p99 0,30 ms), merjeno v strežniku
samem na 300 zahtevah: čas od konca odgovora do konca vpisa v števce. Za
primerjavo je bilo v istem teku notranje delo zahteve 1,47 ms, torej je
štetje **7 % zahteve** pri najcenejšem predpomnjenem odgovoru.

Merjeno posebej, izven strežnika: `iz_zahteve()` 30 µs, od tega iskanje oblike
poti 4,6 µs (46 vzorcev) in zgoščevanje ključa 1,0 µs. Razlika do 0,11 ms je
`request.headers` in `request.url`, ki ju Starlette sestavi šele ob prvi rabi.

**Primerjava „vklopljeno proti izklopljeno" na celi zahtevi ne pove nič in to
je vredno zapisati**, ker je bila prva meritev prav takšna in je kazala
2,8 ms razlike. Ob ponovitvi se je obrnila:

| krog | OBISK=1 | OBISK=0 |
|---|---|---|
| 1 | 1,88 ms | 3,13 ms |
| 2 | 4,13 ms | 1,75 ms |

Mediana 1 000 zahtev z ohranjeno povezavo, brez zajema. Razlika med dvema
procesoma na tem računalniku je torej večja od merjenega učinka — sklep iz
enega para bi bil za faktor 25 napačen. Velja samo meritev v procesu.

**Koliko vrstic to naredi:** `obisk_pot` je ena vrstica na (dan, pot, vrsta),
torej ~46 vzorcev poti krat dve vrsti; `obisk_razrez` 24 ur + naprave +
države; `obiskovalec` eno vrstico na obiskovalca na dan. Pri stotih
obiskovalcih na dan je to nekaj sto vrstic dnevno in ~100 000 na leto — proti
`run`, ki raste v milijone, nič. Obrez je `KAJROS_OBISK_KEEP_DAYS` (550 dni).

**Zakaj ne vrstica na zahtevo:** en obisk strani jih naredi 10–30 (lege na
10 s, zamude na 30 s, dokler je zavihek odprt). Vrstica na zahtevo bi pomenila
stalno pisanje v isto bazo, v katero teče zajem, in na malini je to kartica.

## Prva ugotovitev pregleda: hladen `/api/health` je zrasel na 20,6 s (12. 9. 2026)

Uro po objavi je `/admin` na arwenu pokazal `/api/health` s p95 nad 5 s in
**najdlje 20 575 ms**. Topel je isti endpoint 11–14 ms (tri zaporedne
meritve), torej ne gre za počasnost strežbe, ampak za ceno **prvega** klica po
zagonu.

V tem zapisu je bila ta cena 6. 9. 2026 izmerjena kot **2 683 ms** pri 5,3 mio
`obs`. Baza je odtlej zrasla na **2,4 GB in 19,3 mio meritev** — številka je
torej zrasla **7,7-krat**, medtem ko je zapisana ostala stara.

Plača jo tisti, ki vpraša prvi, in po vsaki objavi je to **`posodobi.sh` sam**:
njegov `curl` na `/api/health` je del čakanja na odgovor. Ogrevanje
(`server._ogrej_health`) se sproži v istem trenutku, zato se v najslabšem
primeru oba ustavita pred isto ključavnico.

Ni popravljeno, ker to ni okvara strežbe: za obiskovalca je odgovor topel,
razen v prvi minuti po restartu. Zapisano je zato, ker je to **prva številka,
ki je prišla iz pregleda in je ne bi videl nihče** — in ker pri nadaljnji rasti
baze ne bo ostala 20 s.

## Priprava na javni obisk (12. 9. 2026)

Kar je bilo pred prvim pravim obiskovalcem izmerjeno in popravljeno.

**Tuji izvori na vsaki strani.** `fonts.googleapis.com` je bil na **vseh
devetih** predlogah, `unpkg.com` (Leaflet) na treh. Naslov IP vsakega
obiskovalca je torej ob vsakem odprtju šel Googlu, zemljevid pa je visel na
tujem CDN-ju. Po samogostitvi je na živi strani na vseh osmih javnih poteh
**nič** tujih gostiteljev v HTML; ostanejo samo ploščice zemljevida.

| kaj | velikost | opomba |
|---|---|---|
| pisave (6 rezov) | 148 kB | `latin` + `latin-ext`, brez štirih drugih naborov |
| Leaflet + 5 slik | 192 kB | 1.9.4, isti kot prej |

**IBM Plex Sans je variabilna pisava, Mono ni.** Google za teže 400, 500 in
600 servira **isto datoteko** — vse tri so bile bajt v bajt enake
(md5 `b2c9031d`). Prva različica jih je prenesla vse tri in nosila 91 kB
podvojenega. Mono je statičen: 400 in 600 se res razlikujeta.

**Chromium tiho zavrne variabilno pisavo iz `data:` URI.** Izmerjeno s
štirimi vrsticami druga ob drugi: statični Mono se naloži, variabilni Sans
pa je pikel v piko enak serifni rezervi. Prek HTTP se naloži oboje. Isto
pisavo s `file://` zavrne obakrat (CORS velja tudi tam). Slika je v vseh
primerih nastala in imela pravo velikost v pikah — torej videti kot uspeh;
`naredi-ikone.sh` zato vpraša `document.fonts.check()`.

**Headless chromium z `--virtual-time-budget` ne požene service workerja.**
`register()` se ne razreši ne v eno ne v drugo smer; virtualni čas ne teče v
njegovih nitih. Preizkus zato teče brez njega, dogodek `load` pa se zakasni
s počasnim odgovorom iz začasnega strežnika.

**Service worker, preverjen z ugasnjenim strežnikom:** lupina 9 datotek,
`/brez-omrezja` shranjena, **`/api/` v nobenem predpomnilniku (0 vnosov)**,
že obiskana stran postrežena iz predpomnilnika, nikoli obiskana dobi
„brez zveze“.

**Cena endpointov na arwenu** (prek `kajros.app`, mediana dveh klicev):

| pot | hladno | toplo |
|---|---|---|
| `/api/pot` (prvi po zagonu) | **5,2 s** | 0,6–1,7 s |
| `/api/live` | 3,2 s | 0,13 s |
| `/api/connections` | 0,58 s | 0,29 s |
| `/api/stations` | 0,51 s | 0,53 s |
| `/api/stats` | 0,17 s | 0,20 s |

Petsekundni prvi klic je **enkratno ogrevanje po zagonu**, ne cena vsake
poti: pet različnih parov koordinat da 0,6–1,7 s. `server._ogrej_pot()` to
že drži toplo na 300 s.

**Disk na arwenu ni kajrosova težava.** 194 GB od 234 je zasedenih (88 %), a
`/var/lib/kajros` je od tega **4,3 GB**; 115 GB je `/home/david`. WAL stoji
pri 273 MB in ne raste — to je visoka voda, ne uhajanje.

**Cloudflare `Python-urllib` ne blokira več** (200 na `/api/health`, prav
tako `curl`, `python-requests`, `Wget`). Prej zapisani *Browser Integrity
Check* je torej odpadel; podrobnosti v `.claude/rules/objava.md`.

**Naš `robots.txt` je na živi strani pripet za Cloudflarovim.** Njihov
blok o signalih za AI je spredaj, naše `Disallow: /api/` in `Sitemap:` pa
zadaj in veljavne. Brez našega bi Cloudflare postregel samo svojega, ta pa
o naših poteh ne ve ničesar.

## Kaj je pokazal pregled Androida pred trgovino (12. 9. 2026)

Stanje pred spremembami, izmerjeno in ne domnevano:

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

Zapisi so trdili 28 kB (README) in 50 kB (`android.md`). Obe številki sta bili
resnični, ko sta bili zapisani — vmes sta prišli budilka in njen vmesnik. Pri
velikosti, ki se meri ob vsaki gradnji, je zastarela številka poceni napaka;
popravljeno je oboje.

**Tiha napaka, ki bi jo videla šele trgovina:** `ACCESS_*_LOCATION` pomeni
privzeto `uses-feature required="true"` za strojno opremo. `aapt2 dump badging`:

```
uses-implied-feature: name='android.hardware.location'
  reason='requested ACCESS_COARSE_LOCATION … ACCESS_FINE_LOCATION permission'
```

Aplikacija bi bila torej skrita vsaki napravi brez GPS, čeprav brez lege dela
vse razen gumba „kje sem“. Popravek so tri izrecne vrstice `required="false"`.

**Dva niza sta bila razvojna, ne javna**: „Če teče na prenosniku, je ta najbrž
zaprt“ in naslov `192.168.1.164:8001` kot pomoč v polju za strežnik. Za potnika
nista pomenila nič.

**Trgovine ni nobene, in to je izbira po pravilih, ne po okusu.** Glavni
F-Droid in IzzyOnDroid zahtevata prosto licenco za vse in gradnjo iz javnega
izvora ([pravila](https://f-droid.org/docs/Inclusion_Policy/)); koda je zaprta
(3. 9. 2026). Google Play zaprto kodo sprejme, a zahteva račun, 25 $,
preverjanje identitete in — za osebni račun, odprt po 13. 11. 2023 — **12
preizkuševalcev, ki aplikacijo držijo nameščeno 14 dni**, poleg tega AAB in od
31. 8. 2026 `targetSdk` 36. Lasten repozitorij F-Droid bi delal, a ga najde le,
kdor pozna naslov.

Izbrano: **prenos s `kajros.app/android`**, ker deluje danes in za vsakogar.
Cena je vprašanje o neznanem viru ob namestitvi in to, da posodobitve ne
ponudi nihče — zato jo poišče aplikacija sama (`/api/android/razlicica`,
enkrat na dan).

**Rok, ki ga je treba imeti v mislih:** Google od 30. 9. 2026 zahteva
registriranega, preverjenega razvijalca za namestitev na certificiranih
napravah (najprej Brazilija, Indonezija, Singapur, Tajska; globalno 2027).
Razgooglane naprave to ne zadeva, navadnega telefona pa bo — takrat bo treba
izbrati znova.

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

**Lastna varovalka je med preizkusom ugriznila in to je prav.** Vrstice ni
bilo, dokler je strežnik vračal `stran: https://kajros.app/android`,
aplikacija pa je kazala na `http://10.0.2.2:8001` — `Nastavitve.jeNas()`
tujega naslova ne sprejme niti od našega strežnika. Preizkus je stekel šele s
`KAJROS_BASE_URL=http://10.0.2.2:8001`. V produkciji se izvora ujemata.

**Dve številki o isti stvari na istem zaslonu.** Stran je pisala „Različica
0.1 · 60 kB“ (izračunano iz bajtov) in dva odstavka nižje „velika okoli
64 kB“ (zapisano na roko). Razlika je `du -h`, ki zaokroži na bloke po 4 KiB:
datoteka ima **61 854 B**. Trdo zapisana številka je odstranjena — velikost
pove tista, ki je izračunana iz datoteke. Ista napaka kot povsod: številka
mora pomeniti to, kar bralec misli, da pomeni.

## Prva objava aplikacije (12. 9. 2026)

`kajros-1.0.apk`, **71 822 B**, podpisan z lastnim ključem (SHA-256 potrdila
`fe89…73f4`, velja do 28. 1. 2054). Preverjeno na objavljeni datoteki, ne na
lokalni: prenesena s `https://kajros.app/prenos/kajros-1.0.apk` ima isto vsoto
kot `/api/android/razlicica` in kot stran, `apksigner` potrdi naš podpis, na
emulatorju se namesti (`Success`) in zažene.

Podpis doda 9 968 B (61 854 → 71 822). Sheme: **v1 false, v2 true, v3 true** —
v1 velja do API 23, mi smo od 26 naprej, zato ni potreben.

**Cloudflare predpomni 404 in to je ugriznilo pri prvi objavi.** Naslov APK-ja
sem zahteval, preden je datoteka prišla na strežnik; ko je prišla, je izvor
vračal 200, rob pa še vedno 404:

```
HTTP/2 404 · age: 171 · cf-cache-status: HIT     (izvor lokalno: 200)
```

`.apk` je med končninami, ki jih Cloudflare predpomni sam od sebe. Izteklo se
je po ~3,5 minute (`cf-cache-status: EXPIRED` → 200). Popravek je na naši
strani: `_napaka_html()` vsaki napaki doda **`Cache-Control: no-store`**, zato
se noben 404 ne more več prijeti ne na robu ne v brskalniku. Preverjeno na obeh
oblikah napake (JSON in stran).

Nauk za naslednjič: **objavi datoteko, preden naslov kamorkoli objaviš** —
en sam radoveden klik pred objavo zamrzne 404 za vse.

## Koliko ljudi je res na strani (15. 9. 2026)

Pregled je kazal **104 ljudi in 94 botov** za en dan, v resnici pa so stran
rabili lastnik (telefon, računalnik, aplikacija) in morda dva ali trije.
Razčlenitev iz `obiskovalec` na arwenu, do 21:06:

| zahtev na obiskovalca | „ljudi" | od tega krajše od minute |
|---|---|---|
| 1 | **79** | 79 |
| 2–3 | 9 | 5 |
| 4–10 | 8 | 6 |
| 11–100 | 5 | 1 |
| več | 3 | 0 |

* **81 od 104 ni poslalo ničesar razen strani** — nobenega `/api/health`, ki ga
  domača stran pokliče vedno. Po državah je pri teh zahtev natanko toliko kot
  ogledov: US 28, TH 13, CN 11, HK 10, SG 4, KR 3.
* **RU: 147 zahtev, 0 ogledov, vse 404**, od 00:01 do 21:06, z UA brskalnika.
* 50 prvih dotikov med 00 in 02.
* **Aplikacija je štela dvakrat**: pari z enakim prvim in zadnjim dotikom na
  sekundo (06:54:50–14:37:11, 07:04:38–10:44:33) — WebView in budilka pošiljata
  različen UA.

Obiskovalcev z vsaj 5 zahtevami je bilo 13; brez skenerja in parov aplikacije
~10 ključev, kar se ujema s tremi napravami lastnika na dveh omrežjih in
nekaj drugimi. Popravek je v `obisk.py` („človek je, kdor je stran pognal“).

**DuckDuckGo je kot opis `kajros.app` kazal JSON** s seznamom endpointov.
Koren je stregel HTML samo ob `Accept: text/html`; izmerjeno na živi strani:

| odjemalec | `Accept` | dobil |
|---|---|---|
| Googlebot | `text/html,…` | stran |
| katerikoli | brez | JSON |
| katerikoli | `*/*` | JSON |
| `facebookexternalhit` | `*/*` | JSON |
| `HEAD /` | brez | JSON |

Google je bil zato v redu, Bing (in z njim DuckDuckGo) ne. Hkrati izmerjeno:
`http://kajros.app/` in `www.kajros.app` vračata **200 z isto vsebino** in ne
preusmerita — dvojnik, ki ga drži skupaj samo `rel=canonical`.

## Pristajalne strani: koliko jih sme biti (17. 9. 2026)

Zemljevid strani je imel **enajst naslovov** in vsak je bil prazna lupina, ki
se napolni v JS — iskalnik torej ni imel česa indeksirati. Vprašanje je bilo,
koliko strani sme nastati in po čem se izberejo.

**Parov postaj je preveč, da bi jih imeli vse.** Vsi pari, ki jih poveže vsaj
ena vožnja v voznem redu:

| omrežje | vseh parov nad pragom voženj | nad pragom razdalje |
|---|---|---|
| železnica (≥ 4 vožnje) | 6 185 | **5 903** (≥ 3 km) |
| avtobus brez LPP (≥ 30 voženj) | 47 533 | **26 049** (≥ 6 km) |
| avtobus z mestnim LPP (≥ 20) | 83 289 | — |

Zato `NAJVEC_RELACIJ = 400` na omrežje; ostalo ostane dosegljivo in `noindex`.

**Meja razdalje ni okras.** Brez nje je vrh avtobusne lestvice po prometu:

```
Ljubljana Kino Šiška → Ljubljana Tivoli     870 voženj   1,2 km
Ljubljana Slovenija avto → Ljubljana Tivoli 870 voženj   1,6 km
```

To sta postajališči iste ulice — nihče ne išče povezave med njima, ker gre peš.
Z mejo 6 km je vrh `Medvode → Ljubljana Šentvid` (510) in `Grosuplje →
Ljubljana Strelišče` (471), torej relaciji, ki ju ljudje res vozijo.

**Mestni LPP relacij nima.** Brez izločitve (`agency = 'lpp'`) je vrh
`Ajdovščina → Konzorcij` s 5 398 vožnjami — imeni dveh postajališč v središču
Ljubljane. Postajališča svoje strani obdržijo, relacije ne.

**Lego imena mora dati najprometnejše postajališče, ne povprečje.**
Prvi poskus je razdaljo meril iz povprečja vseh postajališč z istim imenom in
„Ajdovščina" (postajališče LPP + mesto 25 km stran) je dalo **25 km** za par
sredi Ljubljane. Isto pravilo kot v kazalu postaj (`journey.station_index`).

**Cena izračuna** (razvojni računalnik, 90 dni, 1,93 mio vrstic `run`):

| korak | železnica | avtobus |
|---|---|---|
| izbor parov | 0,1 s | 4,4 s |
| vožnje izbranih relacij + zamude | 0,5 s | 3,5 s |
| zamude po postajah | 0,2 s | 2,9 s |
| **skupaj `pristanek`** | **4,8 s** | **15,1 s** |

Dvajset sekund enkrat na dan, v istem opravilu kot ostali povzetki. V zahtevi
se to ne računa; stran bere shranjeni povzetek in ga ima predpomnjenega.

**Zamude se seštevajo kot histogram po zaokroženi minuti, ne kot seznam
sekund.** Razred zamude se tako ali tako določa iz minute
(`stats._razred_zamude`), torej je histogram natanko tako natančen kot prikaz
— in ne potegne 1,9 mio vrstic v pomnilnik. Kvantil ima isto definicijo kot
`stats._pct()`; test to primerja.

**Bralno transakcijo je treba zapreti pred zapisom.** Prvi zagon je pri
avtobusih odpovedal z „database is locked": v WAL je bralec priklenjen na
posnetek ob prvem branju, zajem medtem piše in zapis v isti transakciji
odpove s SQLITE_BUSY_SNAPSHOT — česar čakanje **ne** reši. Pri petnajstih
sekundah branja je vmesni zapis zajema skoraj gotov.

**Izmerjene strani** (17. 9. 2026, topel predpomnilnik):

| stran | velikost | čas |
|---|---|---|
| `/vlak/zidani-most/ljubljana` | 12,6 kB | 44 ms |
| `/postaja/celje` | 9,3 kB | 28 ms |
| `/postajalisce/bavarski-dvor` | 10,7 kB | 67 ms |
| `/postaje` | 27,0 kB | 13 ms |
| `/sitemap.xml` | 92,7 kB (1 370 naslovov) | — |

Prva različica avtobusne relacije je bila **43 kB**: Medvode → Ljubljana
Šentvid ima 108 voženj na dan in stran je bila samo naštevanje. Zato
`NAJVEC_ODHODOV = 24` in vrstica, ki pove, koliko jih je vseh.

**Prva številka, ki jo te strani povedo in je drugje ni:** na relaciji
`Zidani Most → Ljubljana` je mediana zamude ob prihodu **15 min**, p90 35 min,
in **15,5 %** voženj pride v petih minutah (734 meritev, 21. 8.–17. 9. 2026).
V nasprotni smeri je mediana **2 min** in 67,9 % točnih.
