# Izmerjeno

Številke, ki niso pravilo, ampak stanje: koliko je zajetega, koliko stane,
kako hitro teče. Se starajo — ob vsaki spremembi popravi datum.

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
| Osvežitev v istem procesu | vrh 89 MB, ostane 85 MB → zato `SZ_REFRESH=off` privzeto |

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
`SZ_AGENCIES=` prazen, zato uvoz vzame le SŽ in `trip` ima 789 voženj.
Storitev se imenuje **`kajros-zajem`**, ne `kajros` — ta obstaja, a je
`inactive`, in kdor preverja napačno ime, sklepa, da zajem stoji.

Posledica, ki jo je bilo videti šele ob prilitju: malina je 29.–31. 8. nekaj
avtobusov vseeno posnela (takrat je imela njihove vožnje uvožene), potem pa
jih je uvoz brez `SZ_AGENCIES` iz `trip` odstranil in **43 362 meritev je
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
  −1,26; naša številka je +1,04, torej rahlo pesimistična. To je varna smer:
  kdor pride prezgodaj, čaka, kdor prepozno, vlak zamudi.
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
