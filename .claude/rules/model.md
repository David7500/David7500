---
paths:
  - "kajros/stats.py"
  - "kajros/backtest.py"
  - "kajros/journey.py"
  - "kajros/ocena.py"
---
# Napoved zamude, zveze in prestopi

Vsak nov model se najprej pomeri s **prenosom trenutne zamude naprej** (`kajros backtest`). Kar ga ne premaga, ne sodi v prikaz.

## Prevoznikova napoved

* **Prevoznikova napoved šteje samo navzgor.** Njegova vrednost za nedosežen postanek v povprečju = smet (MAE 8,26 min), a napaka **enosmerna**. Merjeno na 12 026 primerih z znano prevoznikovo vrednostjo:

  | | delež | prevoznik | naš model |
  |---|---|---|---|
  | napove **več** kot mi | 10 % | **0,21 min** | 2,66 min |
  | napove manj ali enako | 90 % | 9,17 min | **1,22 min** |

  Nizka vrednost = privzeta ničla za postanek, ki ga feed še ni razrešil; visoka = prevoznik **ve** nekaj, česar iz zgodovine ni mogoče vedeti — okvara, zapora, križanje. Zato `stats._with_operator()`: `max(naša ocena, njegova)`, nikoli navzdol.

  **Ena izjema, izmerjena** (`stats._operator_is_stale`): dokler vlak **stoji na postaji z dolgim postankom**, njegova vrednost naprej ni napoved, ampak prenos zamude ob prihodu — koliko postanka bo skrajšal, se še ne ve. Ujeto v živo 29. 8.: RG 1604 stal v Ljubljani (postanek 21 min, prišel +19); ob 23:04 prevoznik za Zalog objavil +19, ob 23:12 ob odhodu popravil na +5. Vlak prišel +5.

  Podpis: prevoznikova vrednost = **natanko** zamuda ob prihodu na postajo, kjer vlak stoji (±1 min); postanek tam ≥ 5 min; vrednost večja od tega, kar že vemo. Pojavi se v 926 od 63 967 primerov, tam `max` **slabši** — MAE 4,19 proti 3,31 min, delež v petih minutah 71,2 proti 81,4 %. Z izjemo skupno 1,189 → 1,177 min in 94,27 → 94,42 %. Na teh nalogah MAE 1,36 → 1,12 min, delež v petih minutah 93,7 → 94,8 %, boljše v **vseh** razredih zamude. Velja v `predict`, na odhodni tabli in v iskalniku zvez. Merljivo: `kajros backtest --operator`.

  **Merilo samo bilo prekratko.** `backtest.operator_forecast_tasks()` vzame eno nalogo na par postankov — kaj je feed trdil o cilju, ko je bilo izhodišče zadnjič potrjeno. Zaradi te konstrukcije zgornjega podpisa **sploh ne vsebuje** (0 primerov od 12 154): prevoznikova prenesena vrednost se pojavi šele **po** zadnji spremembi na izhodišču. Pošteno merilo = vsak poll posebej — 63 967 nalog namesto 12 154 — šele tam vidna tudi slaba stran pravila. Kdor pravilo spreminja, naj meri tako.

* **Zamude naprej po progi = napoved, ne meritev** — in **izmerjeno slaba**. Feed za nedosežene postanke pogosto objavi 0, dokler nima prave vrednosti. Merjeno (`kajros backtest --operator`, 11 310 nalog): prevoznikova napoved MAE 7,9 min, 58 % v petih minutah; prenos trenutne zamude MAE 1,3 min, 94 %. Najhujši rez — feed 0, vlak zamuja ≥ 5 min: napaka 18,5 min, 6 % napovedi v petih minutah. **Zato prikaz naprej po progi uporablja lastno oceno, ne feedove vrednosti**; prevoznikova številka ostane vidna v naprednem pogledu.

## Zamuda čez dolg postanek in izhodišče

* **Zamude ne prenašaj naprej čez dolg postanek — tabla je zato lagala.** RG 1604 stoji v Ljubljani 21 min (22:44 → 23:05): pride +15, odpelje **po voznem redu**. Odhodna tabla zamudo prenesla naravnost in pisala 23:20 — potnik bi prišel na prazen peron. Napaka v najslabšo smer, ker vlaka ne zamudiš, če prideš prezgodaj.

  `journey.board()` in `stats.connections()` zato med zadnjo meritvijo in potnikovo postajo odštejeta **rezervo voznega reda** (`stats._slack_ahead()`
  + `_after_slack()`). Pri **prihodni** tabli se postanek na tej postaji ne šteje — vozilo šele pride, postanek je za tem.

  **Rezerva sama ni cel model, in dolgo je bila.** Okno vožnje isti postanek računalo s `predict()` — rezerva **in** historični ostanek — iskalnik in tabla samo z rezervo. Razhajanje vidno na zaslonu: 1. 9. RG 318 za Ljubljano Polje v iskalniku **+11 min**, v oknu iste vožnje **+24**; LPV 2250 +3 proti +18. Dve številki o istem vlaku na isti postaji, obe „ocena" — slabša na vstopni strani. Backtest: prenos 2,94 min MAE in 82,7 % v petih minutah; rezerva + razred 1,92 min in 91,0 %.

  Zdaj vse troje skozi `stats.estimate_at()`: pokliče `predict()`, vzame vrednost za potnikovo postajo; kadar model nima, ostane prenos z rezervo. Po popravku: **3 od 3 zvez se ujema z oknom vožnje**. Cena nič, ker model teče samo na vrsticah „ocena", teh 2–3: iskalnik 2 → 3 ms, odhodna tabla brez merljive razlike (52 ms prej in potem).

  **Prihodna tabla ostane pri prenosu z rezervo.** `predict()` računa **odhodno** zamudo in v rezervo šteje tudi postanek na ciljni postaji — pri odhodu prav; pri prihodu vozilo tega postanka še ni opravilo.

  Poceni: `_slack_ahead()` bere samo postanke nad `MIN_DWELL_S`, na vsej železnici 406 od 10 019.

* **Odhodne zamude s prve postaje ni — pri vlakih.** Feed za vlak nikoli ni poročal `stop_seq = 1`; najnižji zajeti = 2. Vlak, ki *"štarta z zamudo"*, v podatkih viden šele na drugi postaji. Odhodna tabla zato za izhodišče vzame meritev naslednje postaje in napiše, od kod ("izmerjeno na postaji Grosuplje") — brez tega tabla prazna prav tam, kjer potnik vstopa. **Pri avtobusih to ne velja**: poročajo tudi `stop_seq = 1`, tabla uporabi njihovo meritev. Ista koda pokrije oboje: naslednjo postajo vzame šele, kadar lastne ni.

## Katera zamuda velja na potnikovem postanku — eno pravilo, eno mesto

`stats.zamuda_na_postanku()` odloči, ali je številka **izmerjena**, **ocena** ali **napoved prevoznika**, in od kod. Uporabljata jo `stats.connections()` (iskalnik zvez) in `pot.pripni_zamude()` (pot od vrat do vrat).

Do 8. 9. 2026 pravilo vgrajeno v `connections()`. Ob dodajanju druge strani izluščeno — ne zaradi lepote, ampak ker je „isto pravilo na dveh mestih" v projektu dokumentiran razred napake in bi bila razlika **tiha**: prikaz bi feedovo napoved pokazal kot izmerjeno zamudo.

Izluščenje preverjeno, da ničesar ne spremeni: `/api/connections` za isto poizvedbo vrne **bajt za bajt isti odgovor** (18 346 B). Test `test_ista_zamuda_kot_iskalnik_zvez` primerja obe strani na isti vožnji.

## Prestopi

* **Prestopov do trije.** `journey.transfers()` išče enega v SQL in pove, ali zveza drži (meritev obeh vlakov na prestopni postaji). Kadar ne najde nič, prevzame `journey.plan()`: dnevni vozni red v pomnilnik, krog na nogo, do štirih nog. Vzorec 80 parov železniških postaj: **36 % brez odgovora**; s tem **4 %**. Ljutomer mesto → Ribnica in Stara Cerkev → Prevalje rabita tri prestope — ni izmišljen primer. Cena: 28 ms na železnici, 60 ms na avtobusnem omrežju.
* **Pragovi za prestop odvisni od omrežja** (`journey.TRANSFER_LIMITS`): železnica 6–120 min, avtobus 3–30. Tri minute pri mestni liniji = prestop, pri vlaku = lovljenje; pol ure čakanja na liniji, ki vozi vsakih deset minut, ni prestop, ampak znak, da smo zamudili tri boljše.

## Model napovedi

Napoved zamude (`stats.predict`): vlak najprej porabi **rezervo voznega reda**; ostanek popravi historična mediana ostanka pri **tem vlaku**, ločena po razredu trenutne zamude. Izmerjeno (`kajros backtest`, 292 736 nalog, izpuščanje enega dne):

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

**Običajni postanek se kaže, ne uporablja.** `MIN_DWELL_S = 120` = predpostavka, da vlak postanek skrajša na dve minuti. Zamenjava s **historično mediano dejanskega postanka** natančnosti ne izboljša (MAE 1,911 → 1,912 min; enako na odsekih z dolgim postankom in brez zgodovine odseka) — rezerva in historični popravek se seštejeta, premik predpostavke med njima vsote ne spremeni.

Namen: prikaz. Pri postanku nad pet minut okno vožnje napiše „vozni red tu čaka 18 min; ta vlak, kadar zamuja, stoji običajno 15". Skriti dvominutni prag = predpostavka, ki je nihče ne vidi in zna biti močno mimo; ta stavek potnik lahko preveri.

**Rezerva voznega reda = edini vhod v napoved, ki ni statistika.** `slack = Σ max(0, postanek − MIN_DWELL_S)` čez postaje med izhodiščem in ciljem; `stats._after_slack()` jo porabi, največ kolikor vlak zamuja, nikoli tako, da bi prihitel. Deluje **prvi dan zajema**, ker je vozni red znan vnaprej.

Izvor: LP 4219 ima na Mostu na Soči **devet minut postanka** (križanje na enotirni bohinjski progi); v devetih dneh nikoli nadoknadil več kot sedem minut niti stal manj kot dve — +16 → +9, +11 → +4, +10 → +3, vsakič natanko sedem. Konstantna mediana spremembe tega ne izrazi: iz +11 napovedala +9, vlak pripeljal +3. Z rezervo napove +4.

`MIN_DWELL_S = 120`. Backtest med 60 in 180 s raven (1,932 / 1,924 / 1,928 min), pri 0 vidno slabši (2,214) — rezerva brez najkrajšega postanka šteje ves postanek za prihranek. 120 s se ujema z izmerjenim dnom.

Sama rezerva **slabša od prenosa** (3,01 min): zna le brisati zamudo, ne ustvarjati. Uporabna šele z ostankom — kar rezerva ne pojasni. Razrez po trenutni zamudi, kjer je razlika največja:

| trenutna zamuda | vlak + razred | rezerva + razred |
|---|---|---|
| 0–2 min | 1,73 min · 91,3 % | 1,71 min · 91,4 % |
| 2–10 min | 2,06 min · 90,6 % | 1,96 min · 91,4 % |
| 10–30 min | 2,30 min · 89,1 % | 2,20 min · 90,0 % |
| nad 30 min | 3,32 min · 83,7 % | **2,93 min · 85,9 %** |

Troje spoštovati, preden kdo piše nov model:

* **Združevanje po odseku model poslabša.** Na istem tiru se IC in lokalni vlak ne obnašata enako; skupna mediana zabriše prav to, kar šteje.
* **Združen model prihrani 1 % MAE, izgubi pri deležu v petih minutah.** Ni vredno zapletenosti. Prag `MIN_SAMPLES` 1–3 da isti rezultat, 4+ poslabša.
* **Razred zamude šteje, a le pri velikih zamudah.** Skupno razlika komaj 0,7 %; razrez po trenutni zamudi pokaže, kje:

  | trenutna zamuda | vlak | vlak + razred | nalog |
  |---|---|---|---|
  | 0–2 min | 1,74 min · 91,2 % | 1,73 min · 91,3 % | 137 180 |
  | 2–10 min | 2,05 min · 90,7 % | 2,06 min · 90,6 % | 80 531 |
  | 10–30 min | 2,33 min · 88,7 % | 2,30 min · 89,1 % | 68 876 |
  | **nad 30 min** | 3,62 min · 82,1 % | **3,31 min · 83,8 %** | 5 602 |

  Fizikalno: postanek s pol minute rezerve vlaku z 11 min vzame dve, točnemu nič — nima česa nadoknaditi. Mediana čez oba ne opisuje nobenega. Prag treh dni s podobno zamudo izmerjen: pri 1 MAE 2,19 min, pri 2 2,11 min, pri 3 1,99 min. `stats.delay_bucket` in `backtest._bucket` = **ista funkcija** — sicer bi merili en model in uporabljali drugega.

**Premica `d_j = a + b·d_i` preizkušena, slabša** (MAE 2,08 min, nad 30 min 4,78 min). Zna izraziti postanek, ki zamudo pobriše (`b ≈ 0`), a pri devetih dneh naklon prešumen — in kar naklon lovi iz podatkov, piše vozni red zastonj.

**Prikazani dan izpuščen iz učenja** (`stats.predict(exclude_date=...)`, enako kot `history`). Pri tekoči vožnji naprej po progi meritve ni; pri ogledu končanega dne bi model deloma napovedoval iz odgovora.

**Preizkušeno in ne pomaga** — vse z izpuščanjem enega dne, vse slabše ali enako `rezerva + razred` (1,914 min · 91,0 %):

| zamisel | MAE | v 5 min |
|---|---|---|
| rezerva iz voznega reda **in** največjega opaženega okrevanja | 1,921 | 90,9 % |
| rezerva le iz opaženega okrevanja (brez voznega reda) | 1,935 | 90,9 % |
| dodaten člen za trend zamude (raste/pada) | 1,917 | 91,0 % |
| stanje odseka danes: kaj so tam delali drugi vlaki pred nami (30 % teže) | 1,921 | 90,9 % |
| isto, polna teža | 2,089 | 89,6 % |
| zamuda nasprotnega vlaka na isti postaji (križanje), 10 % teže | 2,020 | 90,4 % |

Zakaj nobena: pri devetih dneh mediana po `(vlak, i, j, razred)` že zajame skoraj vso strukturo. **Strop izmerjen**: mediana, ki pozna tudi testni dan, da MAE 1,198 min in 95,0 % — razlika do naših 1,914 min = vrzel v **številu dni**, ne v domiselnosti modela. Obvestila o ovirah neuporabna iz drugega razloga: 522 od 779 vlakov ima kakšno, vsa veljala ves čas zajema — med dnevi ne ločijo ničesar.

**Preizkušeno in ne pomaga** (`kajros backtest --day-offset`): popravek za stanje mreže na ta dan. Zamisel razumna — če cel dan zamuja bolj kot običajno, bo tudi ta vlak — a povprečna sprememba zamude čez zajete dni le med 115 in 142 s. Premalo za rešitev, dovolj za šum: MAE 2,00 → 2,06 min, delež v petih minutah 90,2 % → 89,1 %. (Mediana neuporabna: pri večini sosednjih postankov se zamuda ne spremeni → vsak dan 0.)

Vsak nov model najprej pomeri s `prenos`. Kar ga ne premaga, ne sodi v prikaz, četudi domiselno.

**Avtobusi imajo od 19. 9. 2026 svoja pravila** — glej „Avtobusni model“ spodaj. Železnica ostane pri opisanem tu.

**Meritev neizvedljiva, dokler mediane niso bile predračunane.** `statistics.median` klican enkrat na napoved. Pri železnici seznam po odseku kratek, razlike ni bilo; pri mestnem avtobusu isti odsek vozi več linij, seznam zraste na desettisoče, `odsek+razred` za en dan porabil 6,5 minute namesto 0,3 sekunde. `backtest._medians()` jih izračuna enkrat ob učenju — rezultat do zadnje decimalke isti.

## `run` hrani zadnje stanje — tudi kadar je smet

Vozilo ne more priti na postajo, preden odpelje s prejšnje. Prikaz je to kazal pri **vsaki deseti** vožnji avtobusa, vsaki dvajseti vlaka. Trije vzroki (feed postanek neha pošiljati; feed za nazaj popravi prevožen postanek; mestni LPP pošilja le postanke pred vozilom); nobenega ni mogoče ugotoviti iz ene same vrednosti.

`stats.oznaci_neskladne()` zato ne ugiba vzroka: obdrži **nepadajoče zaporedje ur z največjo skupno težo**, ostalo označi (`zamuda.vrsta = "neskladno"`). Dvoje izmerjeno — ne „poenostavljaj":

* **Utež.** Postanek, nazadnje osvežen prej kot kateri od prejšnjih, je lažji — sicer bi štetje samih postankov pri RG 310 zavrglo *pravo* vrednost (luknji dve, prava ena). Lahek postanek se vseeno **obdrži**, kadar ničemur ne nasprotuje: brez tega pade 4,73 % avtobusnih postankov namesto 2,29 %.
* **Zaokroževanje na minuto.** Prikaz kaže minute; 20 s nazaj ≠ nemogoč vozni red. Brez tega prizadetih pri LPP 38,4 % voženj namesto 17,2 %.

Izid: vožnje z uro nazaj 4,9 / 10,1 / 3,6 % → **0 %** v vseh treh omrežjih. Podrobnosti, tabela: [docs/MERITVE.md](../../docs/MERITVE.md).

`_LAST_MEASURED_SQL` nosi le **lokalni** del pravila — teče nad seznamom voženj hkrati, cele verige ne zmore. Niz gre skozi odstotkovno formatiranje: znaka za odstotek v njem ne sme biti.

## Meja ostanka: mediana enega dneva ni mediana

`predict()` ostanku verjame največ **`max(10 min, trenutna zamuda)`** (`OMEJI_OSTANEK_S`, `OMEJI_OSTANEK_DELEZ`). Izmerjeno na nalogah sence: pri **69 %** napovedi v potnikovem oknu stoji za mediano ostanka **en sam dan**; pri 9–10 postankih naprej jih ima 92 % največ dva. En dan zna biti poljubno velik; ta rep je gnal napako — tam model **slabši od golega prenosa zamude** (4,30 proti 3,59 min).

Meja absolutna **in** sorazmerna: absolutna, da točnemu vozilu ne pripišemo velike spremembe; sorazmerna, da močno zamujajočemu ne odrežemo prave (vlak s +25 min lahko izgubi še deset, točen ne).

Izmerjeno na treh merilih hkrati — številke iz 2. 9. 2026:

| | naloge sence (8 557) | backtest železnica (445 419) | backtest avtobusi |
|---|---|---|---|
| brez meje (prej) | 3,63 min · 84,8 % | **2,07** · **90,1 %** | 4,14 · 91,5 % |
| **z mejo (zdaj)** | **3,18** · **85,0 %** | 2,10 · 89,7 % | **3,41** · **91,5 %** |

Pri 9–10 postankih naprej 4,24 → 2,95 min. Železnica na zgodovinski nalogi izgubi 0,03 min in 0,4 odstotne točke — cena sprejeta zavestno: zgodovinska naloga = poln kratkih skokov, kjer meja skoraj ne prime; potnikovo okno je 6–8 postankov daleč.

**Preizkušeno in ne pomaga** (vse na istih nalogah sence):

| zamisel | MAE | v 5 min | podcenjenih |
|---|---|---|---|
| sorazmerno krčenje `ostanek × n/(n+1)` | 3,36 | 83,7 % | 10,5 % |
| isto, asimetrično (le navzdol) | 3,57 | 84,7 % | 7,2 % |
| manj rezerve voznega reda (×0,5 ali ×0) | brez razlike | | |
| ostanek šele od 3 dni naprej (kot je meril backtest) | 3,63 | 80,8 % | 13,9 % |

Zadnja vrstica = **napaka v merilu, ne zamisel**: `backtest` je prag `MIN_SAMPLES` uporabljal tudi za nepogojeno mediano, `stats.predict` ne — merili smo en model, stregli drugega. Zdaj poravnana; prejšnja različica ostaja v tabeli kot `rezerva+razred, prag 3 dni`.

## Senčno merjenje: kaj je potnik res videl (`ocena.py`)

Backtest meri model na zgodovini z izpuščanjem enega dne — pošteno do modela, ne do **prikaza**: potnik ne vpraša „kakšna bo zamuda na postanku j, če poznam zamudo na i“, ampak pred odhodom od doma pogleda v aplikacijo in prebere eno številko.

`ocena.py` teče ob strežniku (vsakih `KAJROS_OCENA_SECONDS`, privzeto 120 s) in v tabelo `napoved` posname, kaj bi prikaz **ta hip** povedal za postanek **25 minut pred vlakom** oz. **15 pred avtobusom** (`HORIZONT_S`). Ko vozilo postanek prevozi, se v isto vrstico dopiše resnica.

Kaj spoštovati ob spremembah:

* **Primerjava je parna.** Ena vrstica: naša ocena, prevoznikova vrednost in prenos zamude ob istem trenutku, za isti postanek. Vsak model na svojem vzorcu = merjenje tudi razlike med vzorci.
* **Zapiše se prvi posnetek in nobeden več** (ključ `(trip_id, service_date, stop_seq)`). Potnik pogleda enkrat; drugi obhod čez 2 min bi meril napoved s krajšim horizontom in razred bi se tiho premaknil. Dejanski horizont vseeno v `horizon_s` za razrez.
* **Meja „prevozil“ = `stats.last_measured()`, ne obstoj vrstice v `run`.** Feed za še nedosežen postanek objavi vrednost, ki ni meritev — prav to razliko merimo. Resnica iz `run` brez te meje = prevoznikova napoved kot resnica; prevoznik bi zmagal sam proti sebi.
* **Vožnje brez izmerjenega postanka se od 19. 9. 2026 tudi merijo**, ne le štejejo (`brez_meritve`). Vrstica brez izhodišča (`from_seq`, `current_s`, `carry_s` = NULL); `ours_s` = kar pokaže iskalnik (`pred_odhodom`, sicer „običajno“), `ours_own_s` = golo „običajno“. Poročilo jih izpiše posebej („PRED ODHODOM“) in na istih vrsticah — mešane s pogledi na poti bi merile razmerje med vrstama, ne modela. Posledica za kontinuiteto: postanek, ki ga prvi obhod ujame pred odhodom, dobi to vrstico in pozneje nobene na poti (zapiše se prvi posnetek) — pogledov na poti odtlej nekaj manj.
* **Avtobusi se vzorčijo** (`OCENA_BUS_VZOREC`, vsaka peta vožnja), sicer ~135 000 vrstic/dan. Vzorči se po `trip_id`, ne po postanku: vožnja cela ali nobena, sicer razrez po zamudi meri kose poti. Vzorec mora biti **stabilen med zagoni** — zato vsota bajtov, ne vgrajeni `hash` (soljen s `PYTHONHASHSEED`).
* **`ours_s` = kar prikaz res pokaže** — s pravilom „prevoznik ve več“ (`_with_operator`). Naša vrednost brez pravila v `ours_own_s`, da se pravilo preveri tudi v potnikovem oknu, kjer je horizont krajši od tistega, na katerem je bilo izmerjeno.
* **`podcenjenih` in `precenjenih` merita pri istem pragu** — zgrešeno za več kot potnikova rezerva (5 min), vsak v svojo smer. Prag ni izbran, ampak izpeljan: precenitev pod rezervo potnika po `_strosek` ne stane nič.

  Do 3. 9. 2026 ni držalo: `precenjenih` štel **vsako** precenitev, tudi enosekundno, `podcenjenih` le nad 5 min — stolpca pa eden ob drugem kot primerjava. Na 35 325 vrsticah: **58,8 % proti 6,3 %**; pri enakem pragu **6,6 % proti 6,3 %**. Prva slika: smo precenjevalec; druga: uravnoteženi — resnična druga. Ista past kot „60 s sivo, 61 s oranžno“: dve sosednji številki, ne merjeni enako, se bereta kot primerjava, čeprav nista.
* **Nevarna smer je PRECENITEV, ne podcenitev.** Prezgodaj na peronu = čakanje; prepozno = vozilo zamujeno — in prepozno pripelje prav precenitev. Prešteto na zajetih vrsticah: **2 318 primerov, kjer potnik po `_strosek` vozilo zamudi, in nobeden ne izvira iz podcenitve.**

  Do 3. 9. 2026 tu pisalo nasprotno („napoved, ki kaže manj od resnice, je hujša napaka“) — v protislovju s `_strosek` v istem modulu.

  **Za prestop velja obratno** — ne posplošuj: kdor računa na zvezo, ga podcenjena zamuda prvega vozila pripelje do zamujenega drugega. `ocena` meri **vstop na postaji**, zato tam zgornja smer.
* Tabela se obrezuje (`OCENA_KEEP_DAYS`, 30 dni). `run` = zgodovina, ne briše se nikoli; to je merilo, in merilo, staro pol leta, meri model, ki ga ni več.

**Prestop upošteva OBA vlaka.** `journey.py`: `wait = načrtovano + zamuda2 − zamuda1` — če zamuja tudi vlak, na katerega prestopaš, zveza morda drži. Prikaz je odšteval le prvega, žeton pa bral strežnikov `wait_s` — formuli se razideta natanko, ko zamuja drugi, torej v primeru, ki potnika najbolj zanima. Zdaj oba računata isto; izpis pove „drugi +N min“, kadar ni nič.

Ostane pravilo, zaradi katerega je bila razlika uvedena: **zaokroži enkrat, potem računaj.** Vse tri številke na zaslonu = zaokrožene minute; vsota se mora ujeti s četrto.

## Iskanje postaj: promet odloča prej kot oblika ujemanja

`journey.search_stations()` razvršča po `(razred, -promet, ime)`. Razreda: **točno ime (0)** in **vse ostalo (1)** — začetek imena in začetek besede sta za potnika enako dober zadetek; ne ločimo.

Ločevanje do 2. 9. 2026 merljivo narobe: „polje“ → „Polje (Tolmin)“ z **2** vožnjama pred „Kranj Zlato Polje P+R“ s **586**; „Novo Polje“ s 199 padlo na **deveto** mesto — stran zahteva osem, ni ga bilo videti. Isto „most“ (Most na Soči 34 pred Zidanim Mostom 142), „gora“ (Gora pri Pečah 26 pred Kranjsko Goro 285), „vas“ (Vaše/Medvodah 29 pred Latkovo vasjo 218). Preverjeno na 12 poizvedbah: „ljublj“, „mesto“, „bavarski“, „maribor“ nespremenjeni, ostali popravljeni.

**Ločevanje ostane pri IZBORU kandidatov** (`CANDIDATE_CAP`, 300): ena črka ujame tisoče postajališč; promet se šteje le za verjetne.

**Postanke istega imena seštej PRED razvrščanjem.** Mestno postajališče ima svoj `stop_id` za vsako smer; prej razvrščeno po postankih enega, izpisana vsota vseh — seznam urejen po drugi številki, kot jo je kazal („Bavarski dvor“ pokaže 1 137, razvrščen po 573).


## „Končna zamuda“ je zadnja OPAŽENA, ne nujno zadnja

`LAST_STOP_SQL` vzame `MAX(stop_seq)` iz `run` = zadnji videni postanek, ne zadnji iz voznega reda. Ujemata se v **96,3 %** (6 581 celih proti 253 nepopolnim, izmerjeno 4. 9. 2026); pri nepopolnih manjka mediano **en** postanek, povprečno 2,8, največ 30.

**Na agregate ne vpliva:** mediana čez vse vožnje 3,00 min, samo čez cele prav tako 3,00. Nepopolnih ne izločamo — izločanje bi vrglo podatek, ne popravilo številke.

**Pri posamezni vožnji pomeni.** MV 247 27. 8.: zajetih 5 postankov od 15; „končna zamuda 25 min“ = zamuda na petem. Na tej relaciji zamuda vzdolž poti raste (18 → 47 min v drugih dneh) — resnična končna skoraj gotovo višja. Kdor bere eno vrstico, naj pogleda tudi število zajetih postankov.

## Smer napake in strošek potnika

**MAE ne loči smeri, potnik jo loči zelo.** Podcenimo — potnik pride prezgodaj, čaka razliko. Precenimo — vozilo odpelje pred nosom, čaka **razmik do naslednjega**: izmerjena mediana **87 min železnica**, **40 min avtobusi** (razmik z iste postaje v isto smer po `headsign`, 06–20). Zato `kajros ocena` poleg MAE ima stolpca `precenj.` in `strošek`.

**`RAZMIK_S` vreden ponovne meritve, a ne na slepo.** Neodvisna poizvedba 4. 9. 2026: železnica **mediana 80 min na 4 969 razmikih**, 64 % nad uro; zapisano 87 min na 5 205, 66 %; avtobusi 39 min proti 40. Razlika pri železnici 8 %.

Konstante **nisem spremenil**, ker ne vem, ali je vzrok premaknjen vozni red ali to, da moja poizvedba ni ista kot izvirna (razmik po `headsign` se da šteti na več načinov). Pred popravkom obe poizvedbi postaviti eno ob drugo — sicer se v mero vgradi razlika med dvema izračunoma, ne sprememba sveta. Mera `strošek` linearno odvisna od te konstante.

**Številke ne zamikamo navzdol, čeprav je videti, da bi se izplačalo.** Znižanje vsake ocene za `k` minut: strošek s 27,9 na 10,1 min pri `k = 5`. A model predpostavlja, da potnik pride natanko ob prikazani minuti. Če ima lastno rezervo `B`, sta `k` in `B` **zamenljiva**: `B = 5` → najboljši `k = 0` z **istim** stroškom; `B = 10` → strošek zraste (12,3 proti 10,1). Šteje le vsota; optimum ~5 min, ki jih potnik prispeva sam. Zato `ocena.POTNIKOVA_REZERVA_S` = 5 min — izbrana, da je optimalni zamik natanko nič in mera ne dela videza, da se izplača napovedovati manj, kot merimo.

## Avtobusni pozitivni odklon — razrešeno 19. 9. 2026

Izvor: `max(naša, prevoznikova)` — maksimum dveh šumnih ocen navzgor pristranski (+0,26 min, 4,4 % precenjenih). Avtobusi zdaj: polovica presežka; mestni LPP: ves — glej „Avtobusni model“ spodaj. Povprečje v obe smeri (čakalo na dva tedna sence) pomerjeno, **slabše** (2,72 proti 2,62 min): prevozniku navzdol se še vedno ne verjame.


## Katera vožnja danes pelje, pove meritev

`resolve_trip()` je izbiral po dnevih veljavnosti. **LP 4208 ima tri tripe**; 3. 9. 2026 peljal 465938 (83 dni, **30 meritev**), izbira vzela 456511 (232 dni, **nič meritev**) — klik na vlak na živem seznamu je odprl okno vožnje, ki o njem ne ve nič, čeprav je vlak vozil 8 min pozno.

Vrstni red zdaj: **meritev → vozi danes → dni veljavnosti**. Meritev = najmočnejši dokaz, katera vožnja se res pelje; vozni red pove le, katera bi se lahko.

**`/api/train/{no}/run` vrne razrešeno vožnjo, ne poslane.** Prej `trip_id` pri vlaku brez `?trip=` vedno `null` — prikaz ni vedel, katero od več voženj gleda, `predict()` se je učil iz vseh treh hkrati. Zahtevana neobstoječa vožnja ostaja 404 — razrešitev je ne sme tiho zamenjati.

**Isto pravilo napisano dvakrat:** `stats.last_measured()` (Python) in `common.lastMeasured()` (JS). Primerjano na 27 živih vožnjah: ujemata se v vseh; edina razlika LP 4208, izvor v izbiri vožnje, ne v meji. Razhod = tiha napaka na zaslonu — po zapisu v `CLAUDE.md` tam že dvakrat.

## Avtobusni model (19. 9. 2026)

Železnica in avtobusi od tu: **ista koda, različna pravila**. Vseh pet razlik izmerjenih na treh merilih hkrati; podrobnosti in tabele v [docs/MERITVE.md](../../docs/MERITVE.md), „Avtobusni model“.

1. **Vožnja = vožnja čez dneve, ne `trip_id`** (`db.voznja_sql`). Mestni LPP ima za vsak datum svoj `trip_id` (`dan|vožnja|vzorec`), zato model, „običajno“ in zgodovina okna vožnje zanj **nikoli niso imeli preteklega dne**; senca: 0 % napovedi LPP z zgodovino. Ključ: izrazni indeks `trip_voznja`; poizvedba mora izraz ponoviti dobesedno → vedno skozi `db.voznja_sql()`. Nagrobniki LPP nimajo `sched` → `history()` vzame vozni red prikazane vožnje.
2. **Meja ostanka velja samo, dokler ni treh dni** (`OSTANEK_BREZ_MEJE_DNI`). Nekatere vožnje na določenem postanku vsak dan uro „pozne“ (A6385: +62 min v devetih dneh); meja jih je rezala na +10.
3. **Prevoznik navzgor do polovice, pri mestnem LPP v celoti** (`PREVOZNIK_NAVZGOR`, `PREVOZNIK_NAVZGOR_AGENCIJA`). Mestni LPP: živi del iz lastnega sistema sledenja vozil; primestni LPP (1118) = IJPP, dobi polovico.
4. **Vožnja brez meritve** (`stats.pred_odhodom`): prevoznik ne pove več od običajnega → „običajno“; pove več → zgornje pravilo; brez treh dni zgodovine → prevoznik. Prej: tabla kazala običajno, iskalnik zvez prevoznikovo vrednost — **za isto vožnjo ob istem trenutku**; 73 % prevoznikovih vrednosti pred odhodom = gola ničla.
5. **Prezgodnji odhod z izhodišča ni odhod** (`stats.odhod_z_izhodisca`), v trenutni vrednosti in v zgodovini. Avtobus s prvega postanka ne odpelje pred voznim redom; negativna vrednost tam = čaka. Model jo je nosil naprej in napovedal „5 min prej“ za avtobus, ki je peljal točno (na teh pogledih 6,24 → 2,75 min). Na drugih postankih prezgodnja vrednost ostane — tam model izmerjeno najboljši. Vlaka se ne tiče: izhodišča feed zanj ne poroča.

Izid, prikazana številka (učenje samo na preteklih dneh):

| | prej | zdaj |
|---|---|---|
| senca 14.–18. 9., vozilo na poti (124 909) | 2,60 min · 91,2 % · strošek 6,72 | **2,28 · 93,4 % · 6,15** |
| senca 8.–13. 9. (92 875) | 3,00 · 89,5 % · 7,18 | **2,77 · 91,1 % · 6,80** |
| pred odhodom, iskalnik (463 075, iz `obs`) | 3,68 · 85,4 % · 8,59 | **2,78 · 90,9 % · 7,18** |
| pred odhodom, tabla (isto) | 2,90 · 90,2 % · 7,43 | **2,78 · 90,9 % · 7,18** |
| backtest 8 dni (10,6 mio nalog), oboje že z novim ključem | 2,13 · 94,9 % | 2,12 · 95,1 % |

Senca: MAE boljši **vseh 16 dni** 3.–18. 9.; precenjenih (nevarna smer) manj ali enako vseh 16; strošek nižji v 14 (5. 9. enak, 6. 9. +0,20 — nedelja, vožnje imajo po dva dneva zgodovine). Boljši vsi prevozniki; mestni LPP: precenjenih z 0,9 na 1,7 %, ker mu verjamemo v celoti.

**Pred odhodom = 40 % vseh pogledov** (15 min pred avtobusom). Senca jih do
19. 9. samo štela (`brez_meritve`) — zato napaka nevidna; odtlej jih meri (`kajros ocena`, blok „PRED ODHODOM“). Merilo za nazaj: rekonstrukcija iz `obs` — kaj je feed vedel ob T, isto pravilo kot `_LAST_MEASURED_SQL`, brez meje zadnje besede feeda (iz `obs` ni obnovljiva). Simulacija iz končnih vrednosti v `run` tu **laže**: že razvrstitev „še ni odpeljal“ izda, da vozilo zamuja.

**Ura, dež in dan v tednu povečajo negotovost, ne premaknejo sredine.** Po vseh treh rezih predznačena mediana napake novega modela +0,1 do +0,4 min; raste le MAE (suho 2,49, rahel dež 3,19; 14–16 h 3,2–3,5 proti 2,0–2,5; petek 3,50 proti ~2,3). Ura je že v vožnji sami — vsak odhod ima svojo zgodovino.

**Preizkušeno in ne pomaga** (vse z učenjem samo na preteklih dneh):

| zamisel | izid |
|---|---|
| „običajno“ po tipu dneva / po dnevu v tednu (≥ 2 dni); osnova = mediana vseh preteklih dni | 2,76 → 2,76 / **3,10** |
| „običajno“ iz zadnjih 7 dni | 2,76 → 2,82 |
| „običajno“ ločeno za dež in suho | 2,76 → 2,79 |
| sidro v običajni zamudi, `typ_j + ρ·(d_i − typ_i)`, zmes z modelom | senca 2,43 → 2,41 |
| stanje danes: odklon linije / prevoznika / postajališča v zadnji uri | ±0,01; linija s težo 0,4 slabše |
| odsek (vse vožnje med istima postajališčema) za vožnje brez 3 dni | senca 2,43 → 2,43 |
| „združen“ (vožnja, skrčena proti odseku) | backtest 2,13 → 2,05, senca 2,43 → 2,41, dobiček z dnevi pada; rabi nočno tabelo odsekov |
| spodnja meja iz ure, ko vožnja po voznem redu že vozi, a ni izmerjena | strošek 14,39 → 14,90, precenjenih 6,0 → 10,7 % |
| prevoznik navzgor 0,25 (ali 0,25 do 10 min presežka, nad tem 0,75–1), po pravilu izhodišča | senca 14.–18. MAE 2,28 → 2,24, a strošek 6,15 → 6,26, v 5 min 93,4 → 93,3 %; mere si nasprotujejo, ostane 0,5 |

**Strop znan.** Gradientni model (LightGBM, vse zgornje značilke) na isti senci: 2,43 → 2,20 min, a **slabši** strošek (6,38 → 6,50). 58 % dobička pri vozilih, prezgodnjih na izhodišču — zdaj pravilo 5 (2,44 → 2,28). Za ostanek preprost izraz ni našel ničesar nad 0,02 min.

`kajros backtest --network avtobus` v celoti ne gre v pomnilnik (21 dni ≈ 24 mio nalog) → `--dni 7` in `--modeli 'a;b'` (podpičje, ker imena modelov vsebujejo vejice). Sedem dni, štirje modeli: 9,3 GB, 7 min.

## Prehod ni izmerjen, ampak sklepan — in to je odprta luknja

Postanek velja za prevožen, ko je „vozni red + zadnja znana zamuda" mimo = **ura, ne opažanje.** 8. 9. 2026: LPV 2001 ob 07:00 kazal „+6 min · izmerjeno · vlak je tu že bil", potnik stal na Ljubljani Polje; feed po 24 min tišine povedal +29.

Popravljeno: meja ne sme prehiteti zadnje besede feeda; tišina nad 180 s se pove z besedo. **Nerešeno ostaja jedro**: v 14 dneh 1,63 % železniških in 18,50 % avtobusnih voženj ima vsaj en postanek, kjer je bila videna številka kasneje popravljena za ≥ 5 min — pri železnici 76 % iz prikazane **ničle**, resnica do +66 min.

**Kar se da brez signala, je narejeno** (24. 9. 2026): nepotrjen odhod pri železnici ni odpeljan še 20 min po pričakovani uri (`stats.NEPOTRJEN_ODHOD_S`), pove se z besedo. Rekonstrukcija iz `obs`: 4,13 % nepotrjenih trditev o odhodu napačnih za ≥ 3 min; 87 % od teh vlak odpelje v 20 min. Tišina feeda obeh ne loči. Tabla išče po pričakovani uri, ne po voznem redu — prej je vlak z zamudo nad 10 min izginil, preden je prišel. Številke v `docs/MERITVE.md`.

**Signal obstaja in ga ne beležimo.** Feed prevožene postanke izpušča; dokler je postanek v sporočilu, vozilo mimo njega še ni. Pred vgradnjo mora biti izmerjeno proti resnici, ki jo pove človek na peronu — postopek v spominu [[prehod-ni-izmerjen]] in v `docs/MERITVE.md`.
