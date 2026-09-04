# Izmerjeno

Številke, ki niso pravilo, ampak stanje: koliko je zajetega, koliko stane,
kako hitro teče. Se starajo — ob vsaki spremembi popravi datum.

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

## Razdalje med postajami

`stop_times.txt` nima `shape_dist_traveled`. Postaje projiciramo na polilinijo
iz `shapes.txt`, razlika kumulativnih razdalj je dolžina odseka, mediana čez
vse vlake. Rezultat: 267 postaj, 389 odsekov (275 elementarnih), **1253,8 km**
elementarne mreže — ujema se z realno slovensko mrežo.

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
