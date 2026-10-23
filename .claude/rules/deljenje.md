---
paths:
  - "kajros/deljenje.py"
  - "kajros/static/deli.js"
  - "kajros/static/deli.css"
  - "kajros/static/admin_deljenje.js"
  - "android/app/src/main/kotlin/app/kajros/Deljenje*.kt"
  - "tests/test_deljenje.py"
---
# Deljenje lege potnikov

Potnik na vozilu deli lego, drugi vidijo vozilo. Razlog: feed prehod vlaka potrdi v 0,4 % postankov (`docs/MERITVE.md`, „Prehoda vlaka se iz teh podatkov ne da ugotoviti“).

## Kaj se pokaže

* **Verodostojno (`stanje()["verodostojno"]`) → feed ni več potreben**, kadar je med svežimi eno poročilo potnika, ki **se je peljal** (`peljal_ts`: vzdolž trase ≥ `PELJE_M` 100 m, povprečno ≥ `PELJE_MS` 6 m/s, od najstarejše točke v 30 s), in vlak po njem ne prehiteva za > `PREZGODAJ_VLAK_S` (3 min, ni izmerjeno); ali ko se ujemata dva. (Soglasja dveh v 16 dneh in 36 deljenjih ni bilo nikoli.) Takrat: veliki zemljevid vlak na potnikovi legi, okno odpre mali zemljevid, `deljenje.dopolni()` zamenja zamudo, uro in `nepotrjen_do` (vrsta „po poročilu potnikov“), meja meritve do `mimo_seq`, napoved od potnikove lege (`common.fetchRunAndForecast`).
* „Se je peljal“ loči izstopivšega ob progi od vlaka, ki stoji.
* **Ni verodostojno → feed IN poročilo**, vsak s svojo oznako (tabla „potnik na vozilu: …“).
* Prehod šteje samo od potnika, ki se je peljal (`deljenje_prehod` × `peljal_ts`); en je meritev.
* **Avtobus z GPS: zmaga novejša lega** (`api._s_potniki_na_legah`; GPS NAP 29 s, LPP 85 s, potnik 5–10 s). Vlaki in nadomestni na veliki zemljevid iz `/api/live` (`_s_potniki`), v `/api/vehicles` samo z `?trip=` (5 s, drsi po progi — `zemljevid.md`). Vrstica nosi `zamuda`, `pri`, `med`, `rep` (`rep_od`: zadnje 3 min, **nikoli prve 3 min deljenja**; `/zasebnost` to pove).
* **Vlak prezgodaj ne vozi**: zamuda navzdol omejena z 0; na postaji pred odhodom čaka (`Voznja.zamuda(stoji=True)`).
* Odjemalca pošiljata na `POSILJANJE_S` (5 s).
* **Ujemanje po zamudi, ne po legi** (`SOGLASJE_S` 2 min); izbere se največja skupina.
* **Samo sveže** (`SVEZE_S` 120 s) **in teče** (`konec IS NULL`), **ne med izstopanjem** (`zunaj < SUMLJIV_ZUNAJ`, 2): izstop se potrdi šele po minuti, vozilo bi vmes po poročilu „stalo“. Prehodi veljajo ves dan.
* **En pošiljatelj = en poročevalec**: nov začetek na isti vožnji konča prejšnjega (`konec = 'znova'`). Preslikava v pomnilniku; za CGNAT je `znova` lahko drug potnik.

## Zasloni (potrjeni 11. 10. 2026)

Platno „Deljenje lege: zasloni“ (https://claude.ai/artifact/7HtH4tb627i9HpGnWbaXoo). Kartica **indigo** (`--deli-*` v `base.css`, `preveri_paleto.py`); zamuda na podlagi strani (`.deli-zam`; `--d-big` na indigu 2,8 : 1).

* **Okno vožnje: gumb „Deli, kje je“ v vrstici Pomagaj drugim** ob „Kako polno?“ (`#pomoc`, David 23. 10. 2026: kartica „Si na tem vlaku? Deli, kje je“ je bila prevelika). Prvi dotik začne, kartica je razdelek pod vrstico (`deli-okno`); med deljenjem gumb nosi stanje („Deliš lego · drugi te vidijo“) in razdelek odpre/zapre, ustavi samo „Ustavi“. Gumb skrije `train.js` `posodobiDeli`, razdelek `deli.js`; `vir = okno`. Ena lega ≤ 120 m, strežnik preveri. **Samo, ko vozi ali odpelje v 30 min, do 10 min po prihodu.** Zavrnitve s `koda`: `ni_tu`/`ne_vozi` „Deli, ko vstopiš“, `ni_na_trasi` „Nisi ob progi“. Strežnik sprejme 15 min pred voznim redom (`KANDIDAT_PRED_S`).
* **Izbira** (domača, iskalnik): ikona v barvi vozila, prvi „najbolj verjetno“ (značka nad imenom), opomba, da gre iz okna hitreje.
* **Kartica nov zaslon pripelje na zaslon** (`naZaslon`), nad orodno vrstico, samo ko je vsaj delno vidna; deljenje iz aplikacije ob odprtju strani ne premakne ničesar.
* **Drugi te še ne vidijo**: lega na progi ✓, „ko vlak spelje, te pokažemo“; v brskalniku nasvet o zaslonu in `/android`.
* **Drugi te vidijo**: „ta vlak gleda N ljudi“, kraj s hitrostjo ali „stoji N min“, „je zdaj na tablah“.
* **Hvala**: minute, potrjeni odhodi, gledalci (`jaz`). Brez spola v besedilu.

**Gledalci** (`deljenje.poglej`, `gledalcev`): kdor je v zadnji minuti vprašal po vožnji z živim poročilom; ključ iz `obisk.py` (`kljuc_zahteve`), **samo v pomnilniku**; pošiljatelj (`_delilci`) in roboti ne.

**Stoji** (`stanje()["stoji_s"]`): od prve točke v 40 m (`STOJI_OD_M`), napis od minute.

## Kaj se hrani

Točke **projicirane na traso** (`deljenje_tocka`: razdalja, odmik, čas, natančnost, hitrost) — brez surovih koordinat in identitete (Davidova zahteva, za model). Lega pred potrditvijo vozila ne gre nikamor; kandidati so `POST` (koordinate ne v dnevnike). `/zasebnost` to pove.

## Varovalke

API brez avtentikacije:
* Začetek samo za vožnjo, ki je lahko tu.
* Točka ≤ 200 m od trase, ≤ 250 km/h; avtobus nad 130 km/h (`HITROST_MAX_BUS_MS`) ni hitrost.
* **Izstop = dokaz ≥ 3 točke IN ≥ `IZSTOP_S` (60 s)**, pred vožnjo (`peljal_ts`) `IZSTOP_PRED_VOZNJO_S` (10 min) — `_dokaz_izstopa`. Dokaz: izven trase za več od 200 m + natančnost, **ne s hitrostjo vozila**; ali vstran, medtem ko vozilo stoji (`VSTRAN_M`). Do 23. 10. 2026 tri točke (~15 s): od 34 izstopov 14 lažnih med vožnjo (5–28 m/s, trasa Jesenice–Lesce do 200 m mimo tira, M2129 na avtocesti), 6 pred vožnjo (čakanje na postaji), 14 pravih (hoja 0–2,1 m/s).
* **Izven trase s hitrostjo vozila (`VOZI_MS`) ni izstop** (obvoz, zgrešena trasa): točka ne šteje, deljenje teče, `jaz.na_trasi = false`. Po `MIMO_TRASE_S` (10 min) brez točke na trasi konec `trasa` (drugo vozilo).
* **Lega iz omrežja med GPS se preskoči** (natančnost > `NATANCNA_M` 50 m do `NATANCNA_VELJA_S` 20 s po natančni); brez GPS sme naprej le za premik minus natančnost. V 11 od 16 skokov naprej je skočila taka točka; ponovitev 11 646 točk: skokov 20 → 8, točk −3,3 %, „peljal“ isti.
* Prehod čez rob postaje le, če se je potnik peljal (`VOZI_MS`).
* Natančnost slabša od 250 m se preskoči (predor ni izstop).
* Omejitve na pošiljatelja v pomnilniku, dnevni strop v bazi; urna šteje le začeta deljenja.
* `Content-Type: application/json` obvezen (CORS dovoli le GET).
* **`trip_id` do `stats.TRIP_NAJDALJSI` (200)**, ne 64: mestni LPP ima trojni UUID (110 znakov). Do 22. 10. 2026 rez na 64 → vsak začetek na mestnem LPP 404 „Te vožnje ne poznam“ (`zavrnjen:neznana` 8× 21. 10.; mestnega LPP ni delil nihče, 0 od 128 deljenj). Test `test_dolg_trip_id_mestnega_lpp_se_deli`.

## Kandidati

Postaje v okolici (vlak 12 km, avtobus 6 km), vožnje skozi njih, projekcija na traso (krožna in prva točka le v delu, kjer je vozilo lahko — `Voznja.okno()`), čas v oknu −15 / +45 min po voznem redu in zadnji zamudi (nesimetrično namenoma). Avtobus z GPS po razdalji. Smer iz dveh leg (≥ 40 m) izloči nasprotne. Vlak, ki bi med postajama prehiteval > `PREZGODAJ_VLAK_S`, ni kandidat.

Kandidat nosi `odhod` in `zamuda_s`: „odhod 06:30 iz Kamnik · zdaj +45 min“ (zamuda od 3 min) — sicer sta dve vožnji Arrive enaka gumba (7 epizod napačne izbire v 16 dneh).

## Lijak (`deljenje_lijak`)

Dnevni števci brez identitete (`stej`): `kandidati` / `kandidati:0`, `zacetek:<odjemalec>`, `zavrnjen:<koda>` (`Zavrnjeno.koda`), `peljal`. Deljenje hrani `odjemalec` (`splet` | `aplikacija` | `android`) in `vir` (`VIRI`: `domov`, `iskalnik`, `okno`, `budilka`, `vodenje`). V brskalniku nobeno deljenje ni trajalo dlje od ~2 min. Tabela „Lijak“ v `/admin#deljenje`.

## Pregled za skrbnika (`/admin#deljenje`)

Vsako deljenje posebej: kartice levo (filter po izidu), zemljevid (izbrano modro s prehodi), podrobnosti (kar vidijo potniki — samo živo; dejstva; **graf vožnje** čas proti legi, vozni red črtkano; prehodi). Naslov `#deljenje/2026-10-11/<oznaka>`; pretekli dan brez živega (`javno`, `feed`, `gps` = None).
* **Oznaka ni id** (`deljenje.oznaka`, sha256[:12]) — z id-jem bi kdo dodajal točke.
* Parameter je `izbrano`, **ne `k`** (`?k=` = žeton, 403).
* Točke samo za izbrano (`podrobno`; 6 h = 4 000 točk).
* **„Javno“ iz `stanje()`**, ne iz lastnega računa; feed in GPS zraven samo ob živem.
* Sled = del trase med prvo in zadnjo točko (`_kosi()`); cela trasa le živim.
* Izid: `konec` (`izstop`, `trasa`, `cilj`, `cas`, `potnik`, `znova`), sicer `deli` ali **`utihnil`**.

## Android

`DeljenjeStoritev` = storitev v ospredju `location` (lega z ugasnjenim zaslonom). Začne jo **stran** (`Most.deliZacni()`), storitev le pošilja; stran v aplikaciji lege ne pošilja (sicer dva „potnika“).
* **Zagon**: storitev začne šele v `glavna.post`, stran pa `deliStanje()` vpraša takoj. Do 1.14 je `zaganja` nastal šele v `glavna.post` → „ne deli“ → stran „Deljenje je ustavljeno.“, storitev delila naprej, potnik začel znova: **16 od 70 deljenj v aplikaciji** (`znova` v minuti), A6215 23. 10. štirikrat v 95 s. Popravek dvojen: `deli.js` čaka do `ZAGON_MS` (15 s), da storitev javi `aktivno`, in pred `deliZacni()` prebere star `konec` (velja za 1.14); od naslednje različice `Most` postavi `zaganja` takoj (`DeljenjeStoritev.zaganjam`).
* Ista vožnja, izbrana znova med deljenjem = isto deljenje (brez `znova`, brez novega čakanja na „peljal“). Menjava vožnje na delavčevi niti (sicer odgovor stare vrne njen `deljenje` → 404).

### Deljenje ob vožnji (1.9)

„Vsi ob progi, gruča = vlak“ zavrnjeno (brskalnik v ozadju lege ne da, strežnik bi dobil lego ljudi zunaj vlaka). Namesto: vezano na trenutek, ko aplikacija ve za vožnjo.
* **Privolitev = stikalo „Ko se peljem, pomagaj drugim“**, privzeto ugasnjeno (`Nastavitve.deliObVoznji`); zavrnjeno dovoljenje = stikalo nazaj.
* **Sprožilca**: poteg budilke (`ZvonjenjeDejavnost.ustavi`, samo z zaslona) in vodenje do postajališča ob vožnji v 30 min (`pot_podrobno.js`, `Most.cakajVkrcanje`). Zadošča „med uporabo“.
* **Čakanje** (`DeljenjeStoritev.cakaj`): obvestilo „Deljenje ob vožnji · LP 3224 → Ljubljana“ z „Ne tokrat“, lega na 10 s, **ne zapusti telefona**. Vožnjo poišče `Preverjevalec`, postajo `/api/stations/search`.
* **Vkrcan** (`Vkrcanje.kt`, `VkrcanjeTest`): bil na postaji (vlak 300 m, avtobus 120 m, negotovost do 200 m), nato **dve zaporedni legi** zunaj s ≥ 6 m/s in ≤ 100 m natančnosti, ne prej kot 3 min pred odhodom. Brez postaje ni vkrcanja. Pol ure po odhodu (ali 2 h čakanja) konec.
* Naprej isto deljenje kot z gumbom.
* **Zavrnjen začetek = `zavrnjen:<koda>`** (od 1.14, `Deljenje.konecZavrnitve`), stran pove isto kot v brskalniku („Deli, ko vstopiš“ …) na zaslonu „Deljenje ne gre“. Do 1.13 je bil vsak konec ob zavrnitvi `napaka` → „Hvala! Strežnik deljenja ni več sprejel“ tudi, ko ni bila sprejeta niti ena točka; `deli.js` tak konec brez stanja zdaj kaže kot napako.
* Obvestilo deljenja 4713 (4712 = nežni del budilke, ki ga storitev zvonjenja pobriše).

**Emulator:** `adb emu geo fix` rabi avtentikacijo (`~/.emulator_console_auth_token`; vtičnica 5554, `auth <žeton>`). Varen kontekst: `adb reverse tcp:8001 tcp:8001`, `http://127.0.0.1:8001` (`-PkajrosUrl`, nato `pm clear`).
