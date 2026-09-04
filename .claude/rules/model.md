---
paths:
  - "kajros/stats.py"
  - "kajros/backtest.py"
  - "kajros/journey.py"
  - "kajros/ocena.py"
---

# Napoved zamude, zveze in prestopi

Vsak nov model se najprej pomeri s **prenosom trenutne zamude naprej**
(`kajros backtest`). Kar ga ne premaga, ne sodi v prikaz.

## Prevoznikova napoved

* **Prevoznikova napoved šteje samo navzgor.** Njegova vrednost za še
  nedosežen postanek je v povprečju smet (MAE 8,26 min), a napaka je
  **enosmerna**. Merjeno na 12 026 primerih z znano prevoznikovo vrednostjo:

  | | delež | prevoznik | naš model |
  |---|---|---|---|
  | napove **več** kot mi | 10 % | **0,21 min** | 2,66 min |
  | napove manj ali enako | 90 % | 9,17 min | **1,22 min** |

  Nizka vrednost je namreč privzeta ničla za postanek, ki ga feed še ni
  razrešil; visoka pa pomeni, da prevoznik **ve** za nekaj, česar iz zgodovine
  ni mogoče vedeti — okvaro, zaporo, križanje. Zato `stats._with_operator()`:
  `max(naša ocena, njegova)`, nikoli navzdol.

  **Ena izjema, in ta je izmerjena** (`stats._operator_is_stale`): dokler vlak
  **stoji na postaji z dolgim postankom**, njegova vrednost za naprej ni
  napoved, ampak prenos zamude, s katero je prišel — koliko postanka bo
  skrajšal, se še ne ve. Ujeto v živo 29. 8.: RG 1604 je stal v Ljubljani
  (postanek 21 min, prišel +19), ob 23:04 je prevoznik za Zalog objavil +19 in
  ob 23:12, ko je vlak odpeljal, to popravil na +5. Vlak je prišel +5.

  Podpis: prevoznikova vrednost je **natanko** zamuda ob prihodu na postajo,
  kjer vlak stoji (±1 min), postanek tam je ≥ 5 min, vrednost pa je večja od
  tega, kar že vemo. Pojavi se v 926 od 63 967 primerov in tam je `max`
  **slabši** — MAE 4,19 proti 3,31 min, delež v petih minutah 71,2 proti
  81,4 %. Z izjemo skupno 1,189 → 1,177 min in 94,27 → 94,42 %. Na teh nalogah MAE 1,36 → 1,12
  min, delež v petih minutah 93,7 → 94,8 %, in boljše je v **vseh** razredih
  zamude. Velja v `predict`, na odhodni tabli in v iskalniku zvez.
  Merljivo: `kajros backtest --operator`.

  **Merilo samo je bilo prekratko.** `backtest.operator_forecast_tasks()` vzame
  eno nalogo na par postankov — kaj je feed trdil o cilju v trenutku, ko je bilo
  izhodišče zadnjič potrjeno. Prav zaradi te konstrukcije zgornjega podpisa
  **sploh ne vsebuje** (0 primerov od 12 154): prevoznikova prenesena vrednost
  se pojavi šele **po** zadnji spremembi na izhodišču. Pošteno merilo je vsak
  poll posebej — 63 967 nalog namesto 12 154 — in šele tam se vidi tudi slaba
  stran pravila. Kdor pravilo spreminja, naj meri tako.

* **Zamude naprej po progi so napoved, ne meritev** -- in ta napoved je
  **izmerjeno slaba**. Feed za še nedosežene postanke pogosto objavi 0, dokler
  nima prave vrednosti. Merjeno (`kajros backtest --operator`, 11 310 nalog):
  prevoznikova napoved MAE 7,9 min in 58 % v petih minutah, prenos trenutne
  zamude naprej MAE 1,3 min in 94 %. V najhujšem rezu -- feed pravi 0, vlak pa
  zamuja ≥ 5 min -- je napaka 18,5 min in v petih minutah je 6 % napovedi.
  **Zato prikaz naprej po progi uporablja lastno oceno, ne feedove vrednosti**;
  prevoznikova številka ostane vidna v naprednem pogledu.

## Zamuda čez dolg postanek in izhodišče

* **Zamude ne prenašaj naprej čez dolg postanek — tabla je zato lagala.**
  RG 1604 stoji v Ljubljani 21 minut (22:44 → 23:05): pride +15 in odpelje
  **po voznem redu**. Odhodna tabla je zamudo prenesla naravnost in pisala
  23:20 — potnik bi prišel na že prazen peron. Napaka v najslabšo smer, ker
  vlaka ne zamudiš, če prideš prezgodaj.

  `journey.board()` in `stats.connections()` zato med zadnjo meritvijo in
  potnikovo postajo odštejeta **rezervo voznega reda** (`stats._slack_ahead()`
  + `_after_slack()`). Pri **prihodni** tabli se postanek na tej postaji ne
  šteje — vozilo šele pride, postanek je za tem.

  **Rezerva sama pa ni cel model, in dolgo je bila.** Okno vožnje je isti
  postanek računalo s `predict()` — torej z rezervo **in** historičnim
  ostankom — iskalnik in tabla pa samo z rezervo. Razhajanje je bilo vidno na
  zaslonu: 1. 9. je RG 318 za Ljubljano Polje v iskalniku pisal **+11 min**, v
  oknu iste vožnje pa **+24**; LPV 2250 +3 proti +18. Dve številki o istem
  vlaku na isti postaji, obe označeni „ocena" — in slabša od njiju je bila na
  vstopni strani. Backtest pravi, kaj je boljše: prenos 2,94 min MAE in 82,7 %
  v petih minutah, rezerva + razred 1,92 min in 91,0 %.

  Zdaj gre vse troje skozi `stats.estimate_at()`, ki pokliče `predict()` in
  vzame vrednost za potnikovo postajo; kadar je model nima, ostane prenos z
  rezervo. Izmerjeno po popravku: **3 od 3 zvez se ujema z oknom vožnje**.
  Cena je nič, ker model teče samo na vrsticah, ki so „ocena", teh pa je 2–3:
  iskalnik 2 → 3 ms, odhodna tabla brez merljive razlike (52 ms prej in potem).

  **Prihodna tabla ostane pri prenosu z rezervo.** `predict()` računa
  **odhodno** zamudo in v rezervo šteje tudi postanek na ciljni postaji, kar je
  pri odhodu prav; pri prihodu vozilo tega postanka še ni opravilo.

  Poceni je: `_slack_ahead()` bere samo postanke nad `MIN_DWELL_S`, teh je na
  vsej železnici 406 od 10 019.

* **Odhodne zamude s prve postaje ni — pri vlakih.** Feed za vlak nikoli ni
  poročal `stop_seq = 1`; najnižji zajeti je 2. Vlak, ki *"štarta z zamudo"*,
  je v podatkih viden šele na drugi postaji. Odhodna tabla zato za izhodišče
  vzame meritev naslednje postaje in zraven napiše, od kod je ("izmerjeno na
  postaji Grosuplje") -- brez tega je tabla prazna prav tam, kjer potnik
  vstopa. **Pri avtobusih to ne velja**: ti poročajo tudi `stop_seq = 1`, zato
  tabla uporabi njihovo lastno meritev. Ista koda pokrije oboje, ker vzame
  naslednjo postajo šele, kadar lastne ni.

## Prestopi

* **Prestopov je lahko do trije.** `journey.transfers()` išče enega v SQL in
  zna pri njem povedati, ali zveza drži (meritev obeh vlakov na prestopni
  postaji). Kadar ne najde nič, prevzame `journey.plan()`: dnevni vozni red v
  pomnilnik in krog na nogo, do štirih nog. Vzorec 80 parov železniških postaj
  je imel **36 % brez odgovora**; s tem jih ostane **4 %**. Ljutomer mesto →
  Ribnica in Stara Cerkev → Prevalje rabita tri prestope, kar ni izmišljen
  primer. Cena: 28 ms na železnici, 60 ms na avtobusnem omrežju.
* **Pragovi za prestop so odvisni od omrežja** (`journey.TRANSFER_LIMITS`):
  železnica 6–120 min, avtobus 3–30. Tri minute so pri mestni liniji prestop,
  pri vlaku lovljenje; čakanje pol ure na liniji, ki vozi vsakih deset minut,
  pa ni prestop, ampak znak, da smo zamudili tri boljše.

## Model napovedi

Za napoved zamude (`stats.predict`): vlak najprej porabi **rezervo voznega
reda**, kar ostane, popravi historična mediana ostanka pri **tem vlaku**,
ločena po razredu trenutne zamude. Izmerjeno (`kajros backtest`, 292 736
nalog, izpuščanje enega dne):

| model | MAE | v 5 min |
|---|---|---|
| prenos (referenca) | 2,94 min | 82,7 % |
| vlak (mediana spremembe) | 2,00 min | 90,3 % |
| odsek | 2,25 min | 87,9 % |
| odsek + razred zamude | 2,27 min | 87,7 % |
| združen (krčenje) | 1,98 min | 89,7 % |
| vlak + razred zamude | 1,99 min | 90,5 % |
| vlak, premica `d_j = a + b·d_i` | 2,08 min | 89,5 % |
| rezerva sama (brez učenja) | 3,01 min | 82,3 % |
| **rezerva + razred zamude (v uporabi)** | **1,92 min** | **91,0 %** |

**Običajni postanek se kaže, ne uporablja.** `MIN_DWELL_S = 120` je
predpostavka, da vlak postanek skrajša na dve minuti. Preizkušeno je, da
zamenjava s **historično mediano dejanskega postanka** natančnosti ne izboljša
(MAE 1,911 → 1,912 min; enako na odsekih z dolgim postankom in tam, kjer za
odsek ni zgodovine) — ker se rezerva in historični popravek seštejeta in
premikanje predpostavke med njima vsote ne spremeni.

Prikazu pa je namenjena: pri postanku nad pet minut okno vožnje napiše
„vozni red tu čaka 18 min; ta vlak, kadar zamuja, stoji običajno 15". Skriti
dvominutni prag je predpostavka, ki je nihče ne vidi in ki zna biti močno
mimo; ta stavek potnik lahko preveri.

**Rezerva voznega reda je edini vhod v napoved, ki ni statistika.**
`slack = Σ max(0, postanek − MIN_DWELL_S)` čez postaje med izhodiščem in
ciljem; `stats._after_slack()` jo porabi, a največ toliko, kolikor vlak
zamuja, in nikoli tako, da bi prihitel. Zna delati **prvi dan zajema**, ker
je vozni red znan vnaprej.

Od kod: LP 4219 ima na Mostu na Soči **devet minut postanka** (križanje na
enotirni bohinjski progi) in v devetih dneh ni nikoli nadoknadil več kot sedem
minut niti stal manj kot dve — +16 → +9, +11 → +4, +10 → +3, vsakič natanko
sedem. Konstantna mediana spremembe tega ne more izraziti: iz +11 je
napovedala +9, vlak je pripeljal +3. Z rezervo napove +4.

`MIN_DWELL_S = 120`. Backtest je med 60 in 180 s raven (1,932 / 1,924 /
1,928 min), pri 0 pa vidno slabši (2,214) — rezerva brez najkrajšega postanka
šteje ves postanek za prihranek. 120 s se ujema z izmerjenim dnom.

Sama rezerva je **slabša od prenosa** (3,01 min): zna samo brisati zamudo, ne
pa je ustvarjati. Šele ostanek — kar rezerva ne pojasni — jo naredi uporabno.
Razrez po trenutni zamudi, kjer je razlika največja:

| trenutna zamuda | vlak + razred | rezerva + razred |
|---|---|---|
| 0–2 min | 1,73 min · 91,3 % | 1,71 min · 91,4 % |
| 2–10 min | 2,06 min · 90,6 % | 1,96 min · 91,4 % |
| 10–30 min | 2,30 min · 89,1 % | 2,20 min · 90,0 % |
| nad 30 min | 3,32 min · 83,7 % | **2,93 min · 85,9 %** |

Iz tega troje, kar velja spoštovati, preden kdo piše nov model:

* **Združevanje po odseku model poslabša.** Na istem tiru se IC in lokalni vlak
  ne obnašata enako, zato skupna mediana zabriše prav tisto, kar šteje.
* **Združen model prihrani 1 % MAE in izgubi pri deležu v petih minutah.** To
  ni vredno zapletenosti. Prag `MIN_SAMPLES` 1–3 da isti rezultat, 4 in več
  poslabša.
* **Razred zamude šteje, a le pri velikih zamudah.** Skupno je razlika
  komaj 0,7 %; razrez po trenutni zamudi pa pokaže, kje je:

  | trenutna zamuda | vlak | vlak + razred | nalog |
  |---|---|---|---|
  | 0–2 min | 1,74 min · 91,2 % | 1,73 min · 91,3 % | 137 180 |
  | 2–10 min | 2,05 min · 90,7 % | 2,06 min · 90,6 % | 80 531 |
  | 10–30 min | 2,33 min · 88,7 % | 2,30 min · 89,1 % | 68 876 |
  | **nad 30 min** | 3,62 min · 82,1 % | **3,31 min · 83,8 %** | 5 602 |

  Fizikalno je razumljivo: postanek s pol minute rezerve vlaku z 11 minutami
  vzame dve, točnemu pa nič — ta nima česa nadoknaditi. Mediana čez oba
  opisuje nobenega od njiju. Prag treh dni s podobno zamudo je izmerjen:
  pri 1 je MAE 2,19 min, pri 2 2,11 min, pri 3 1,99 min. `stats.delay_bucket`
  in `backtest._bucket` sta **ista funkcija** — sicer bi merili en model in
  uporabljali drugega.

**Premica `d_j = a + b·d_i` je bila preizkušena in je slabša** (MAE 2,08 min,
nad 30 min celo 4,78 min). Zna izraziti postanek, ki zamudo pobriše (`b ≈ 0`),
a je pri devetih dneh naklon prešumen — in kar naklon lovi iz podatkov, piše
vozni red zastonj.

**Prikazani dan je izpuščen iz učenja** (`stats.predict(exclude_date=...)`,
enako kot `history`). Pri tekoči vožnji naprej po progi meritve ni, pri ogledu
končanega dne pa bi model deloma napovedoval iz odgovora.

**Preizkušeno in ne pomaga** — vse merjeno z izpuščanjem enega dne, vse
slabše ali enako `rezerva + razred` (1,914 min · 91,0 %):

| zamisel | MAE | v 5 min |
|---|---|---|
| rezerva iz voznega reda **in** največjega opaženega okrevanja | 1,921 | 90,9 % |
| rezerva samo iz opaženega okrevanja (brez voznega reda) | 1,935 | 90,9 % |
| dodaten člen za trend zamude (raste/pada) | 1,917 | 91,0 % |
| stanje odseka danes: kaj so tam delali drugi vlaki pred nami (30 % teže) | 1,921 | 90,9 % |
| isto, s polno težo | 2,089 | 89,6 % |
| zamuda nasprotnega vlaka na isti postaji (križanje), 10 % teže | 2,020 | 90,4 % |

Zakaj nobena: pri devetih dneh mediana po `(vlak, i, j, razred)` že zajame
skoraj vso strukturo. **Strop je izmerjen**: mediana, ki bi poznala tudi
testni dan, da MAE 1,198 min in 95,0 % — torej je razlika do naših 1,914 min
vrzel v **številu dni**, ne v domiselnosti modela. Obvestila o ovirah so za
model neuporabna iz drugega razloga: 522 od 779 vlakov ima kakšno, vsa pa so
veljala ves čas zajema, zato med dnevi ne ločijo ničesar.

**Preizkušeno in ne pomaga** (`kajros backtest --day-offset`): popravek za
stanje mreže na ta dan. Zamisel je razumna -- če cel dan zamuja bolj kot
običajno, bo tudi ta vlak -- a povprečna sprememba zamude se čez zajete dni
giblje le med 115 in 142 s. Premalo, da bi kaj rešilo, dovolj, da doda šum:
MAE 2,00 → 2,06 min, delež v petih minutah 90,2 % → 89,1 %. (Mediana je za to
neuporabna: pri večini sosednjih postankov se zamuda ne spremeni, zato je
vsak dan 0.)

Vsak nov model naj se najprej pomeri s `prenos`. Kar ga ne premaga, ne sodi
v prikaz, pa naj bo še tako domiseln.

**Avtobusi bodo dobili svoj model; zdaj ga nimajo in to je izmerjeno.**
`backtest --network avtobus`, 2 dneva in 326 685 nalog: sedanji model da
**natanko isto kot prenos zamude** (2,74 min · 92,5 %), ker z dvema dnevoma
ni niti enega para (vožnja, i, j) z dovolj vzorci. Edini, ki kaj pridobi, je
`odsek` (2,63 min · 92,9 %) -- združevanje po fizičnem odseku čez vse linije.
Model torej avtobusom ne škodi, a jim tudi ne pomaga.

Ko bo meritev dovolj, gresta modela **narazen**: pri avtobusu so smiselni
vhodi, ki jih železnica nima ali jih tam ni vredno gledati -- ura dneva
(gneča), vreme, GPS hitrost in lega, gostota postajališč. Do takrat velja
isto pravilo: kar ne premaga prenosa, ne gre v prikaz.

**Meritev je bila neizvedljiva, dokler mediane niso bile predračunane.**
`statistics.median` se je klical enkrat na napoved. Pri železnici je bil
seznam po odseku kratek in razlike ni bilo; pri mestnem avtobusu isti odsek
vozi več linij, seznam zraste na desettisoče in `odsek+razred` je za en dan
porabil 6,5 minute namesto 0,3 sekunde. `backtest._medians()` jih izračuna
enkrat ob učenju -- rezultat do zadnje decimalke isti.


## Meja ostanka: mediana enega dneva ni mediana

`predict()` ostanku ne verjame več kot **`max(10 min, trenutna zamuda)`**
(`OMEJI_OSTANEK_S`, `OMEJI_OSTANEK_DELEZ`). Razlog je izmerjen na nalogah
sence: pri **69 %** napovedi v potnikovem oknu stoji za mediano ostanka **en
sam dan**, pri devetih do desetih postankih naprej pa jih ima 92 % največ dva.
En dan zna biti poljubno velik in prav ta rep je gnal napako — tam je bil
model **slabši od golega prenosa zamude** (4,30 proti 3,59 min).

Meja je absolutna **in** sorazmerna: absolutna zato, da točnemu vozilu ne
pripišemo velike spremembe, sorazmerna pa zato, da močno zamujajočemu ne
odrežemo prave (vlak s +25 min lahko izgubi še deset, točen ne).

Izmerjeno na treh merilih hkrati — številke so iz 2. 9. 2026:

| | naloge sence (8 557) | backtest železnica (445 419) | backtest avtobusi |
|---|---|---|---|
| brez meje (prej) | 3,63 min · 84,8 % | **2,07** · **90,1 %** | 4,14 · 91,5 % |
| **z mejo (zdaj)** | **3,18** · **85,0 %** | 2,10 · 89,7 % | **3,41** · **91,5 %** |

Pri devetih do desetih postankih naprej 4,24 → 2,95 min. Železnica na
zgodovinski nalogi izgubi 0,03 min in 0,4 odstotne točke — to je cena, ki je
bila sprejeta zavestno: zgodovinska naloga je poln kratkih skokov, kjer meja
skoraj ne prime, potnikovo okno pa je šest do osem postankov daleč.

**Preizkušeno in ne pomaga** (vse na istih nalogah sence):

| zamisel | MAE | v 5 min | podcenjenih |
|---|---|---|---|
| sorazmerno krčenje `ostanek × n/(n+1)` | 3,36 | 83,7 % | 10,5 % |
| isto, asimetrično (le navzdol) | 3,57 | 84,7 % | 7,2 % |
| manj rezerve voznega reda (×0,5 ali ×0) | brez razlike | | |
| ostanek šele od 3 dni naprej (kot je meril backtest) | 3,63 | 80,8 % | 13,9 % |

Zadnja vrstica je bila **napaka v merilu, ne zamisel**: `backtest` je prag
`MIN_SAMPLES` uporabljal tudi za nepogojeno mediano, `stats.predict` pa ne —
torej smo merili en model in stregli drugega. Zdaj sta poravnana, prejšnja
različica pa ostaja v tabeli kot `rezerva+razred, prag 3 dni`.

## Senčno merjenje: kaj je potnik res videl (`ocena.py`)

Backtest meri model na zgodovini z izpuščanjem enega dne. To je pošteno do
modela, ni pa pošteno do **prikaza**: potnik ne vpraša „kakšna bo zamuda na
postanku j, če poznam zamudo na i“, ampak pogleda v aplikacijo, preden gre od
doma, in prebere eno številko.

`ocena.py` zato teče ob strežniku (vsakih `KAJROS_OCENA_SECONDS`, privzeto 120 s)
in v tabelo `napoved` posname, kaj bi prikaz **ta hip** povedal za postanek,
ki je **25 minut pred vlakom** oziroma **15 pred avtobusom** (`HORIZONT_S`).
Ko vozilo tisti postanek prevozi, se v isto vrstico dopiše resnica.

Kar velja spoštovati, če se ga kdo dotakne:

* **Primerjava je parna.** V eni vrstici so naša ocena, prevoznikova vrednost
  in prenos zamude ob istem trenutku, za isti postanek. Kdor bi vsak model
  meril na svojem vzorcu, bi meril tudi razliko med vzorci.
* **Zapiše se prvi posnetek in nobeden več** (ključ je `(trip_id,
  service_date, stop_seq)`). Potnik pogleda enkrat; drugi obhod čez dve minuti
  bi meril napoved s krajšim horizontom in razred bi se tiho premaknil.
  Dejanski horizont je vseeno v `horizon_s`, da se da po njem razrezati.
* **Meja „prevozil“ je `stats.last_measured()`, ne obstoj vrstice v `run`.**
  Feed za še nedosežen postanek objavi vrednost, ki ni meritev — in prav ta
  razlika je tisto, kar tu merimo. Če bi resnico brali iz `run` brez te meje,
  bi za resnico vzeli prevoznikovo napoved in prevoznik bi zmagal sam proti
  sebi.
* **Vožnje brez izmerjenega postanka se ne merijo, ampak štejejo**
  (`brez_meritve`). To ni izpuščen primer, ampak ugotovitev: to je okno, v
  katerem potniku ne znamo povedati ničesar.
* **Avtobusi se vzorčijo** (`OCENA_BUS_VZOREC`, vsaka peta vožnja), sicer bi
  bilo ~135 000 vrstic na dan. Vzorči se po `trip_id` in ne po postanku:
  vožnja mora biti cela ali nobena, sicer se razrez po zamudi meri na kosih
  poti. Vzorec mora biti **stabilen med zagoni**, zato vsota bajtov in ne
  vgrajeni `hash` (ta je soljen s `PYTHONHASHSEED`).
* **`ours_s` je to, kar prikaz res pokaže** — torej z pravilom „prevoznik ve
  več“ (`_with_operator`). Naša vrednost brez tega pravila je v `ours_own_s`,
  da se da pravilo preveriti tudi v potnikovem oknu, kjer je horizont krajši
  od tistega, na katerem je bilo izmerjeno.
* **`podcenjenih` in `precenjenih` merita pri istem pragu** — zgrešeno za več
  kot potnikovo rezervo (5 min), vsak v svojo smer. Prag ni izbran, ampak
  izpeljan: precenitev, manjša od rezerve, potnika po `_strosek` ne stane nič.

  Do 3. 9. 2026 to ni držalo: `precenjenih` je štel **vsako** precenitev, tudi
  enosekundno, `podcenjenih` pa samo tiste nad pet minut — in stolpca sta stala
  eden ob drugem kot primerjava. Na 35 325 vrsticah je tako pisalo **58,8 %
  proti 6,3 %**, pri enakem pragu pa **6,6 % proti 6,3 %**. Prva slika je
  trdila, da smo precenjevalec, druga, da smo uravnoteženi; resnična je druga.
  Ista past kot „60 s sivo, 61 s oranžno“: dve sosednji številki, ki nista
  merjeni enako, se bereta kot primerjava, tudi če to nista.
* **Nevarna smer je PRECENITEV, ne podcenitev.** Kdor pride na peron prezgodaj,
  čaka; kdor pride prepozno, je vozilo zamudil — in prepozno ga pripelje prav
  precenitev. Prešteto na zajetih vrsticah: **2 318 primerov, kjer potnik po
  `_strosek` vozilo zamudi, in nobeden ne izvira iz podcenitve.**

  Tu je do 3. 9. 2026 pisalo nasprotno („napoved, ki kaže manj od resnice, je
  hujša napaka“). Zapis je bil v protislovju s `_strosek` v istem modulu.

  **Za prestop velja obratno** in tega ne posplošuj: kdor računa na zvezo,
  ga podcenjena zamuda prvega vozila pripelje do zamujenega drugega. `ocena`
  meri **vstop na postaji**, zato tam velja zgornja smer.
* Tabela se obrezuje (`OCENA_KEEP_DAYS`, 30 dni). `run` je zgodovina in se ne
  briše nikoli; to je merilo, in merilo, staro pol leta, meri model, ki ga ni
  več.

## Iskanje postaj: promet odloča prej kot oblika ujemanja

`journey.search_stations()` razvršča po `(razred, -promet, ime)`. Razredi so
**točno ime (0)** in **vse ostalo (1)** — začetek imena in začetek besede sta
za potnika enako dober zadetek in ju ne ločimo.

Ločevanje je bilo tam do 2. 9. 2026 in je bilo merljivo narobe: „polje“ je
dalo „Polje (Tolmin)“ z **2** vožnjama pred „Kranj Zlato Polje P+R“ s **586**,
„Novo Polje“ s 199 pa je padlo na **deveto** mesto — stran zahteva osem in ga
ni bilo videti. Isto pri „most“ (Most na Soči 34 pred Zidanim Mostom 142),
„gora“ (Gora pri Pečah 26 pred Kranjsko Goro 285) in „vas“ (Vaše/Medvodah 29
pred Latkovo vasjo 218). Preverjeno na dvanajstih poizvedbah: „ljublj“,
„mesto“, „bavarski“ in „maribor“ se niso spremenili, ostali so se popravili.

**Ločevanje pa ostane pri IZBORU kandidatov** (`CANDIDATE_CAP`, 300): ena
črka se ujame s tisoči postajališč in promet se šteje samo za verjetne.

**Postanke istega imena seštej PRED razvrščanjem.** Mestno postajališče ima
svoj `stop_id` za vsako smer; prej se je razvrščalo po postankih enega, izpisala
pa se je vsota vseh — seznam je bil urejen po drugi številki, kot jo je kazal
(„Bavarski dvor“ pokaže 1 137, razvrstil pa se je po 573).


## Smer napake in strošek potnika

**MAE ne loči smeri, potnik pa jo loči zelo.** Podcenimo — potnik pride
prezgodaj in čaka razliko. Precenimo — vozilo mu odpelje pred nosom in čaka
**razmik do naslednjega**, ki je izmerjeno mediano **87 min pri železnici** in
**40 min pri avtobusih** (razmik z iste postaje v isto smer po `headsign`,
06–20). Zato ima `kajros ocena` poleg MAE še stolpca `precenj.` in `strošek`.

**Številke ne zamikamo navzdol, čeprav je videti, da bi se izplačalo.** Če
vsako oceno znižamo za `k` minut, pade strošek s 27,9 na 10,1 min pri `k = 5`.
A model predpostavlja, da potnik pride natanko ob prikazani minuti. Če ima
lastno rezervo `B`, sta `k` in `B` **zamenljiva**: pri `B = 5` je najboljši
`k = 0` z **istim** stroškom, pri `B = 10` pa strošek zraste (12,3 proti 10,1).
Šteje samo vsota in optimum je okoli pet minut, ki jih potnik prispeva sam.
`ocena.POTNIKOVA_REZERVA_S` je zato 5 min — izbrana tako, da je optimalni
zamik natanko nič in mera ne dela videza, da se izplača napovedovati manj,
kot merimo.

## Avtobusni pozitivni odklon: diagnoza, brez popravka

Naš odklon je pri avtobusih **+0,42 min**, pri železnici −0,94. Izvor je
izmerjen: **pravilo „prevoznik ve več“** (`_with_operator`, `max(naša,
njegova)`). Maksimum dveh šumnih ocen je navzgor pristranski — to je
aritmetika, ne napaka pravila.

**Kaj pravilo res zamenja, se vidi šele pri simetričnem pragu** (avtobusi,
n = 29 642, 30 dni sence):

| | odklon | precenili | podcenili | MAE | strošek |
|---|---|---|---|---|---|
| naša ocena **s** pravilom | +0,42 | **6,9 %** | 5,7 % | 3,16 | **7,73** |
| ista vrstica **brez** pravila | −0,94 | 4,2 % | 9,4 % | 3,18 | 7,93 |

Pravilo **skoraj podvoji nevarno smer** (4,2 → 6,9 %) in za toliko poreže
varno (9,4 → 5,7 %). Dokler je to bral samo `odklon`, je bila to opomba o
pristranskosti; zdaj je vidno kot menjava varne napake za nevarno.

**Vseeno ostane**, ker je strošek — edina mera, ki obe smeri tehta s ceno —
z njim nižji (7,73 proti 7,93 min). Ima tudi svojo izmerjeno utemeljitev:
kadar prevoznik napove več, je njegov MAE 0,21 proti našim 2,66. A rezerva je
tanka in odvisna od `RAZMIK_S`; kdor se ga dotakne, naj to številko pomeri
znova.

**Preizkušeno in NE uvedeno:** povprečje naše in prevoznikove vrednosti da na
parnem izrezu MAE 2,77 (proti 2,85), odklon **−0,03** (proti +0,85) in strošek
7,09 (proti 7,27) — boljše po vseh treh merilih hkrati. Vseeno ni uvedeno,
ker:

* utemeljitev obstoječega pravila pravi, da je nizka prevoznikova vrednost
  **privzeta ničla** za nerazrešen postanek; povprečenje z njo bi moralo
  škoditi, pa ne škoduje, in **mehanizma, zakaj, nimam**;
* podatka sta dva dneva in dobiček pri MAE se ne ponovi (2. 9.: 3,06 → 2,93;
  3. 9.: 2,44 → 2,45), popravek odklona pa se ponovi oba dneva
  (+0,95 → −0,01 in +0,63 → −0,07).

Ko bo sence za dva tedna, se to pomeri znova: če odklon ostane popravljen in
MAE vsaj enak, se uvede. Prej ne — utemeljeno pravilo se ne ruši z razlago,
ki je ni.


## Katera vožnja danes pelje, pove meritev

`resolve_trip()` je izbiral po dnevih veljavnosti. **LP 4208 ima tri tripe**;
3. 9. 2026 je peljal 465938 (83 dni, **30 meritev**), izbira pa je vzela 456511
(232 dni, **nič meritev**) — kdor je vlak kliknil na živem seznamu, je pristal
na oknu vožnje, ki o njem ne ve nič, čeprav je vlak vozil 8 minut pozno.

Vrstni red je zdaj **meritev → vozi danes → dni veljavnosti**. Meritev je
najmočnejši dokaz, katera vožnja se v resnici pelje; vozni red pove samo,
katera bi se lahko.

**`/api/train/{no}/run` vrne razrešeno vožnjo, ne poslane.** Prej je bil
`trip_id` pri vlaku brez `?trip=` vedno `null`, zato prikaz ni vedel, katero
od več voženj gleda, in `predict()` se je učil iz vseh treh hkrati. Zahtevana
vožnja, ki ne obstaja, ostaja 404 — razrešitev je ne sme tiho zamenjati.

**Isto pravilo je napisano dvakrat.** `stats.last_measured()` v Pythonu in
`common.lastMeasured()` v JS. Primerjano na 27 živih vožnjah: ujemata se v
vseh, edina razlika je bila prav LP 4208 in je izvirala iz izbire vožnje, ne
iz meje. Če se kdaj razideta, je to tiha napaka na zaslonu — ta je bila po
zapisu v `CLAUDE.md` tam že dvakrat.


## Avtobusni model: prva meritev, ki odločitev sploh omogoča (4. 9. 2026)

Do zdaj je bila odločitev „ni dovolj podatkov“. Zdaj jih je: **77 %**
avtobusnih voženj ima zgodovino (1. 9. jih je 11 %), **47 %** vsaj tri dni
(prag `MIN_PREDICT_SAMPLES`); pri železnici 88 % oziroma 82 %.

`kajros backtest` na obeh omrežjih — železnica 15 dni in **521 781** nalog,
avtobusi 7 dni in **6 004 849** nalog:

| model | železnica MAE | v 5 min | avtobusi MAE | v 5 min |
|---|---|---|---|---|
| **rezerva+razred (v uporabi)** | **2,06** | 90,0 % | 2,98 | 93,0 % |
| združen | 2,07 | 89,6 % | **2,85** | **93,6 %** |
| odsek+razred | 2,36 | 87,5 % | 2,89 | 93,4 % |
| odsek | 2,37 | 87,4 % | 2,94 | 93,2 % |
| rezerva+mediana | **2,00** | **90,5 %** | 3,16 | 92,4 % |
| prenos | 3,04 | 82,3 % | 3,38 | 91,0 % |

**Sedanji model je pisan za železnico in tam je blizu najboljšega; pri
avtobusih ga „združen“ prekaša** za 0,13 min MAE in 0,6 odstotne točke.
To je prvi merljiv razlog za omrežju lasten model — ne velik, a ponovljiv na
šestih milijonih nalog.

**Zamenjave zaenkrat NI**, in to ni oklevanje, ampak pravilo: model se meri na
dveh merilih, backtest in `kajros ocena`. Senca je 4. 9. stara **tri dni**
(47 892 vrstic) in na njej se razlika 0,13 min ne da ločiti od šuma. Ko bo
sence za dva tedna, se to pomeri znova — skupaj s preizkusom povprečenja,
ki čaka na isto.

Opomba za tistega, ki to nadaljuje: `rezerva+razred, prag 3 dni` je pri
avtobusih **slabši** od sedanjega (3,16 proti 2,98), pri železnici pa
neznatno boljši (2,03 proti 2,06). Prag torej ni skupna nastavitev.
