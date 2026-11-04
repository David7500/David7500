---
paths:
  - "kajros/stats.py"
  - "kajros/backtest.py"
  - "kajros/journey.py"
  - "kajros/ocena.py"
  - "kajros/zapore.py"
---
# Napoved zamude, zveze in prestopi

Nov model najprej proti **prenosu trenutne zamude** (`kajros backtest`). Česar ne premaga, ne gre v prikaz.

## Prevoznikova napoved

* **Šteje samo navzgor** (`stats._with_operator()`: `max(naša, njegova)`). Povprečno smet (MAE 8,26), a enosmerna (12 026 primerov):

  | | delež | prevoznik | naš model |
  |---|---|---|---|
  | napove **več** kot mi | 10 % | **0,21 min** | 2,66 min |
  | napove manj ali enako | 90 % | 9,17 min | **1,22 min** |

* **Izjema `stats._operator_is_stale`**: vlak **stoji na dolgem postanku** (≥ 5 min), prevoznikova vrednost = natanko zamuda ob prihodu (±1 min) → to je prenos, ne napoved (RG 1604: +19 → vlak +5). Na 926 od 63 967 tam `max` slabši; z izjemo skupno 1,189 → 1,177. Velja v `predict`, tabli, iskalniku. Meri **vsak poll posebej** (`kajros backtest --operator`) — ena naloga na par postankov podpisa ne vsebuje (0 od 12 154).
* **Pri vlaku velja prevoznikova beseda tudi naprej** (`stats.SIDRO_PREVOZNIKA`): izhodišče modela se premakne na postanek, kjer prevoznik zmaga (LPV 2252: Sava +22, Litija prej 08:46). Čas ne teče nazaj. Senca 2,74 → 2,54, strošek 8,79 → 8,72. Merilo `scripts/preizkusi_sidro.py` (okno iz `obs`). `own_delay_s` = naša brez prevoznika (`ours_own_s`); `od_prevoznika` pove postajo. Avtobusi niso izmerjeni. Vzrok: SŽ postanke pred vlakom odšteva po uri s staro zamudo.
* **Zamude naprej po progi = napoved, izmerjeno slaba** (11 310 nalog: prevoznik MAE 7,9, 58 %; prenos 1,3, 94 %; feed 0 pri ≥ 5 min zamude: 18,5 min). Prikaz naprej = lastna ocena; prevoznikova le, kjer napove več (`from_operator`, opomba „napoved prevoznika“ v vrstici).

## Zapora tira in vlak pred njim: opozorilo, ne napoved (`zapore.py`)

Ob zapori enega tira izguba ≥ 5 min pri 16 % prehodov (sicer 4 %), za vlakom z izgubo ≥ 10 min 18–23 %. **Mediana 0** → `opozorila` ob vrstici, številka ostane (višja bi trem od štirih vlak odpeljala pred nosom).
* Dnevi in ure so **v besedilu**; `zapore.razberi` izpusti, česar ne razume.
* Odsek = `edge.elementary` (ujame tudi vlak brez postanka).
* Vlak pred njim le iz **prevoženih** postankov (`last_measured`).
* **Interval, ne premik**: „lahko do“ = ocena + `zapore.dodatek` (p90 izgub zapor ali izguba vlaka pred njim); resnica pod mejo 89,7–94,9 %. Samo v Pythonu: okno `dodatek` po postankih, tabla/iskalnik `do_s`.
* Merilo `scripts/preizkusi_zapore.py`.

## Dolg postanek in izhodišče

* **Zamude ne prenašaj čez dolg postanek** (RG 1604: +15, odpelje po voznem redu; tabla je pisala 23:20). `journey.board()`, `stats.connections()` odštejeta **rezervo voznega reda** (`stats._slack_ahead()` + `_after_slack()`); pri **prihodni** tabli postanek na tej postaji ne šteje.
* **Vse troje skozi `stats.estimate_at()`** (kliče `predict()`; brez modela prenos z rezervo) — prej iskalnik +11, okno +24 za isti vlak. **Prihodna tabla ostane pri prenosu z rezervo** (`predict()` računa odhodno).
* **Postaja izstopa = PRIHOD**: `estimate_at(prihod=True)` / `zamuda_na_postanku(prihod=True)` prišteje rezervo, porabljeno na tej postaji (`slack_here_s`). Na postanku > 2 min z zamudo ≥ 3 min je prihodna zamuda višja od odhodne za 4,0 min (vlak, 1 411) oz. 3,0 (avtobus, 3 383) — toliko kot prestop. Pot (`pripni_zamude`) in iskalnik zvez (`zamuda_prihod`) isto.
* **Vlak s `stop_seq = 1` nikoli ne poroča** — tabla vzame naslednjo postajo in napiše, od kod („izmerjeno na postaji Grosuplje“). Avtobusi poročajo.

## Ena odločitev za potnikov postanek

`stats.zamuda_na_postanku()` odloči **izmerjena / ocena / napoved prevoznika** in od kod; rabita jo `stats.connections()` in `pot.pripni_zamude()`. Isto pravilo na dveh mestih = tiha napaka. `test_ista_zamuda_kot_iskalnik_zvez`.

## Prestopi

* **Do trije.** `journey.transfers()` en prestop v SQL; brez zadetka `journey.plan()` (dnevni vozni red v pomnilniku, do štirih nog). 80 parov: brez odgovora 36 % → 4 %. 28 ms železnica, 60 ms avtobus.
* Pragi po omrežju (`journey.TRANSFER_LIMITS`): železnica 6–120 min, avtobus 3–30.
* **Prestop ne vozi v krogu** (`journey.BLIZU_M` 300 m): odpade, kadar druga vožnja pelje nazaj mimo izhodišča ali prva naprej mimo cilja (`_prestopi`; `plan()` prek `_v_krogu`). Konzorcij → Bavarski dvor jih je imel 8 (LPP 6 do Dolgega mosta in nazaj, 52 min za 600 m). 200 mestnih parov do 2,5 km (24. 10. 2026): prestopov 350 → 283, 9 parov ostane brez — vseh 9 dobi `blizu_z_zvezo()` (postajališče z drugim imenom do 300 m od izhodišča ali cilja z neposredno vožnjo; `blizu` v `/api/connections`).
* **Prestop upošteva OBA vozila**: `wait = načrtovano + zamuda2 − zamuda1`; izpis „drugi +N min“. **Zaokroži enkrat, potem računaj.**
* Za prestop je nevarna **podcenitev** prvega vozila (obratno od vstopa).
* **Tveganje prestopa** (`pot.pripni_tveganje`, `docs/MERITVE.md` „Ali prestop drži“): vnaprej zgodovina ISTEGA prestopa (oba isti dan, prihodna zamuda prvega, odhodna drugega, z izhodišča nikoli negativna), skrčena proti `PRESTOP_IZHODISCE` z 2 dnevoma (Brier 0,098; razred sam 0,152; razred pod najnižjim izmerjenim dobi najnižjega). Vlak na izhodišču ne poroča: dan, ko je vozil (meritev na naslednjem postanku), = 0.
* **Zdaj**: kadar je na poti **katerokoli** od obeh vozil → `verjetnost_zdaj` iz napake sence (`ocena.porazdelitev_napak`, povzetek `napake_sence`; Brier 0,059 proti 0,068 na 398). Senca meri le `ocena.HORIZONT_S` (15/25 min) pred vozilom: dlje **največ izhodišče za živo rezervo** — meja, ne meritev; izmeri z drugim horizontom sence. Isto za zadnjo vožnjo pri roku (`ROK_IZHODISCE`), `vir` = „zdaj“.
* Zanesljivost predloga = zmnožek delov, pri roku × zadnja vožnja v rezervi (0,114 proti 0,118 za delež dni celega predloga).
* Iskanje ponuja prestope, ki ne držijo: vlak → avtobus s 3–6 min rezerve 48 %, avtobus → avtobus 70 %. **Pri roku prvi = najpoznejši z zanesljivostjo ≥ 0,9** (`ZANESLJIVO_P`). Iskanje nazaj vidi le nekaj zvez pred rokom → brez zanesljive išče znova z rokom −20 in −40 min (`ROK_PREJ_S`): prvi zanesljiv 88 → 93 % (6–25 km), 91 → 99 % (2–4 km), odhod mediana 3 min prej (`scripts/preizkusi_rok.py`). Prevlada ne izrine predloga, ki je za > 0,05 zanesljivejši — **razen hoje vso pot**: vožnja brez prestopa, ki odpelje ob isti uri ali pozneje, pripelje prej in hodi manj, jo izrine (prej prva v 8 od 100 mestnih).
* Izhodišča so izmerjena na planerju (`scripts/preizkusi_prestope.py`); ob spremembi praga ali iskanja meri znova.

## Model napovedi (`stats.predict`)

Vlak najprej porabi **rezervo voznega reda**, ostanek popravi historična mediana ostanka pri **tem vlaku** po razredu trenutne zamude. 292 736 nalog, izpuščanje dneva:

| model | MAE | v 5 min |
|---|---|---|
| prenos (referenca) | 2,94 min | 82,7 % |
| vlak (mediana spremembe) | 2,00 min | 90,3 % |
| odsek + razred zamude | 2,27 min | 87,7 % |
| združen (krčenje) | 1,98 min | 89,7 % |
| vlak, premica `d_j = a + b·d_i` | 2,08 min | 89,5 % |
| rezerva sama | 3,01 min | 82,3 % |
| **rezerva + razred zamude (v uporabi)** | **1,92 min** | **91,0 %** |

* `slack = Σ max(0, postanek − MIN_DWELL_S)`; `_after_slack()` porabi največ, kolikor zamuja, nikoli do prehitevanja. Dela prvi dan. `MIN_DWELL_S = 120` (60–180 s ravno, 0 slabše 2,214).
* Običajni postanek se **kaže, ne uporablja** (historična mediana MAE 1,911 → 1,912) — okno: „vozni red tu čaka 18 min; ta vlak, kadar zamuja, stoji običajno 15“.
* Razred šteje pri velikih zamudah (nad 30 min 3,62 → 3,31). `stats.delay_bucket` in `backtest._bucket` = **ista funkcija**. Prag tri dni (1: 2,19, 3: 1,99).
* Združevanje po odseku poslabša; združen model ni vreden zapletenosti; premica prešumna.
* Prikazani dan izpuščen iz učenja (`predict(exclude_date=...)`).
* **Ne pomaga** (vse ≥ 1,914): rezerva iz opaženega okrevanja, trend zamude, stanje odseka danes, nasprotni vlak, popravek za stanje mreže (`--day-offset` 2,00 → 2,06). **Strop**: mediana s testnim dnem 1,198 — vrzel je v **številu dni**. Ovire med dnevi ne ločijo (vse veljajo ves čas); zapore v besedilu da (28 % proti < 1 %), a mediana 0 → opozorilo.
* `backtest._medians()` predračuna mediane (sicer 6,5 min na dan pri avtobusih).

## `run` hrani zadnje stanje — tudi smet

Vozilo ne more priti na postajo, preden odpelje s prejšnje (prej vsaka deseta avtobusna vožnja). `stats.oznaci_neskladne()` obdrži **nepadajoče zaporedje ur z največjo skupno težo**, ostalo `zamuda.vrsta = "neskladno"`. Ne poenostavljaj:
* **Utež**: postanek, osvežen prej od prejšnjih, je lažji; obdrži se, če ničemur ne nasprotuje (sicer 4,73 % namesto 2,29 %).
* **Zaokroževanje na minuto** (sicer LPP 38,4 % namesto 17,2 %).

Izid 0 % voženj z uro nazaj. `_LAST_MEASURED_SQL` nosi le lokalni del; niz gre skozi odstotkovno formatiranje — **brez znaka za odstotek**.

## Meja ostanka

`predict()` ostanku verjame največ **`max(10 min, trenutna zamuda)`** (`OMEJI_OSTANEK_S`, `OMEJI_OSTANEK_DELEZ`): pri 69 % napovedi stoji za mediano en sam dan. Senca 3,63 → 3,18, avtobusi 4,14 → 3,41; železnica backtest 2,07 → 2,10 (zavestno). Ne pomaga: sorazmerno krčenje, asimetrično, manj rezerve. `backtest` in `predict` morata imeti isti prag `MIN_SAMPLES`.

## Senčno merjenje (`ocena.py`)

Na `KAJROS_OCENA_SECONDS` (120 s) v `napoved`: kaj bi prikaz povedal **25 min pred vlakom** / **15 pred avtobusom** (`HORIZONT_S`); resnica se dopiše po prehodu.
* **Parna primerjava** (naša, prevoznik, prenos v isti vrstici).
* **Samo prvi posnetek** (`(trip_id, service_date, stop_seq)`); `horizon_s` za razrez.
* **„Prevozil“ = `stats.last_measured()`**, ne obstoj vrstice v `run`.
* Vožnje brez meritve se merijo (`pred_odhodom`, sicer „običajno“; `ours_own_s` golo), blok „PRED ODHODOM“ posebej.
* Avtobusi vzorčeni (`OCENA_BUS_VZOREC`, vsaka peta, po `trip_id`, vsota bajtov — ne `hash`).
* `ours_s` = kar prikaz res pokaže (z `_with_operator`), `ours_own_s` brez.
* **`podcenjenih` in `precenjenih` pri istem pragu** (5 min, potnikova rezerva).
* **Nevarna smer = PRECENITEV** (vozilo odpelje pred nosom; 2 318 zamujenih po `_strosek`, nobeden iz podcenitve).
* `OCENA_KEEP_DAYS` 30.

## Dolg odsek: zamuda iz lege (`odsek.py`, senca od 4. 11. 2026)

Odsek NAP ≥ 15 min po voznem redu: okno kaže zadnjo meritev, avtobus pa porabi rezervo. Ocena zamude na **naslednjem** postanku, `ocena.snapshot` jo piše v `lega_s`, `ours_lega_s`, `lega_vir`; prikaz je ne bere.
* **Profil** (`odsek_profil`, nočno iz `lega` + `gps_prehod`): zdaj + običajni ostanek do prehoda, odsek = ime, ime, dolžina po trasi na 500 m, koš 5 %, ≥ 3 dni. Na `ponovitev.py` MAE 3,27 → 1,35, v 2 min 38 → 83 % (29 098 vzorcev, izpuščen dan).
* **Razdalja** (vozni red po razdalji) le brez profila in od 30 % odseka: pod tem slabša od prenosa, odklon od +2 do −2 min (mesto, avtocesta).
* **Izhodišče za naprej = naslednji postanek**, ne zadnji prevoženi: ocena že vsebuje rezervo odseka, `predict` iz `k` bi jo štel dvakrat.
* Merili: `kajros ocena` (blok DOLG ODSEK, iste vrstice), zgodovina `docs/presoja/dolg_odsek/ponovitev.py`; `kajros backtest` leg ne vidi. Odločitev v `KOLEDAR.md`.

## Iskanje postaj

`journey.search_stations()` razvršča po `(razred, -promet, ime)`: točno ime (0), vse ostalo (1). Ločevanje začetka imena je dajalo „Polje (Tolmin)“ (2 vožnji) pred „Kranj Zlato Polje“ (586). Ločevanje ostane le pri izboru kandidatov (`CANDIDATE_CAP` 300). **Postanke istega imena seštej PRED razvrščanjem.**

## Strop 3 h pri VSEM branju zgodovine

`stats.MAX_REALNA_ZAMUDA_S` v `predict`, `typical_at_stops`, `history`, `_dnevi_prednikov`, `backtest._delays_by_day`, statistiki, pristajalnih. Nad 3 h = zamenjava prometnega dne. **Filter po vrsticah, ne po dnevih.** Model 3,03 → 2,44. Senca: `resolve` hrani surovo, `ocena.report` izloči in prešteje.

## „Končna zamuda“ = zadnja OPAŽENA

`LAST_STOP_SQL` = `MAX(stop_seq)` iz `run`; z zadnjim iz voznega reda 96,3 %. Agregati brez vpliva; pri posamezni vožnji poglej število zajetih postankov.

## Strošek potnika

Podcenitev = čakanje razlike; precenitev = **razmik do naslednjega** (`RAZMIK_S`: 87 min železnica, 40 avtobusi). `kajros ocena` ima `precenj.` in `strošek`. Neodvisna poizvedba da 80 min — pred popravkom obe poizvedbi primerjaj. **Ne zamikaj navzdol**: zamik `k` in potnikova rezerva sta zamenljiva; `ocena.POTNIKOVA_REZERVA_S` = 5 min, da je optimalni zamik nič.

## Katera vožnja danes pelje

`resolve_trip()`: **meritev → vozi danes → dni veljavnosti** (LP 4208 tri tripi). `/api/train/{no}/run` vrne razrešeno vožnjo; neobstoječa zahtevana = 404. `stats.last_measured()` (Python) in `common.lastMeasured()` (JS) = isto pravilo dvakrat — morata se ujemati.

## Avtobusni model (19. 9. 2026)

Ista koda, različna pravila (tabele v `docs/MERITVE.md`):
1. **Vožnja = vožnja čez dneve** (`db.voznja_sql`, izrazni indeks `trip_voznja` — izraz dobesedno skozi `db.voznja_sql()`). Nagrobniki LPP brez `sched` → `history()` vzame vozni red prikazane.
2. **Meja ostanka le do treh dni** (`OSTANEK_BREZ_MEJE_DNI`).
3. **Prevoznik navzgor do polovice, mestni LPP v celoti** (`PREVOZNIK_NAVZGOR`, `PREVOZNIK_NAVZGOR_AGENCIJA`; 1118 polovico).
4. **Vožnja brez meritve** (`stats.pred_odhodom`): prevoznik ne več od običajnega → „običajno“; več → pravilo 3; brez treh dni → prevoznik. Tabla in iskalnik isto (73 % prevoznikovih pred odhodom = ničla).
5. **Prezgodnji odhod z izhodišča ni odhod** (`stats.odhod_z_izhodisca`) — v trenutni in zgodovini (6,24 → 2,75).

Senca 2,60 → 2,28 min, strošek 6,72 → 6,15; pred odhodom (40 % pogledov) 3,68 → 2,78. Merilo za nazaj iz `obs`, ne iz končnih vrednosti `run` (te lažejo). Ura, dež, dan dvignejo MAE, ne sredine.

**Ne pomaga**: „običajno“ po dnevu v tednu (3,10) / 7 dni / dež; sidro v običajni; stanje danes; odsek; „združen“ (rabi nočno tabelo); spodnja meja iz ure; prevoznik 0,25. LightGBM 2,43 → 2,20, a strošek slabši; dobiček večinoma pravilo 5.

`kajros backtest --network avtobus` ne gre v pomnilnik → `--dni 7`, `--modeli 'a;b'` (podpičje). 7 dni, 4 modeli: 9,3 GB, 7 min.

## Prehod je sklepan, ne izmerjen — odprto

Prevožen = vozni red + zadnja zamuda mimo = **ura**. Meja ne prehiti zadnje besede feeda; tišina > 180 s z besedo. Nerešeno: 1,63 % železniških in 18,50 % avtobusnih voženj ima postanek, kjer je bila videna številka pozneje popravljena za ≥ 5 min (železnica 76 % iz **ničle**). Nepotrjen odhod pri železnici 20 min po pričakovani uri (`stats.NEPOTRJEN_ODHOD_S`) z besedo. Signal (postanek še v sporočilu = vozilo še ni mimo) pred vgradnjo izmeri proti človeku na peronu — [[prehod-ni-izmerjen]], `docs/MERITVE.md`.
