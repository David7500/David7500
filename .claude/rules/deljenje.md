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

Potnik na vozilu deli lego; drugi vidijo, kje je vozilo. Razlog: `docs/MERITVE.md`, „Prehoda vlaka se iz teh podatkov ne da ugotoviti“: feed prehod pri vlaku potrdi v 0,4 % postankov, resnico ima samo človek na vlaku. Uvedeno 25. 9. 2026, obljubljeno dvema potnikoma do 2. 10. 2026.

## Kaj se pokaže (odločil David, 25. 9. 2026; en potnik dovolj od 11. 10. 2026)

* **Verodostojno poročilo (`stanje()["verodostojno"]`): feed ni več potreben.** Velja, kadar je med svežimi vsaj eno poročilo potnika, ki **se je peljal** (`peljal_ts`: vzdolž trase ≥ `PELJE_M` 100 m in obe natančnosti, s povprečno hitrostjo ≥ `PELJE_MS` 6 m/s, od najstarejše točke v zadnjih 30 s, sicer od prejšnje), in vlak po njem ne prehiteva za več od `PREZGODAJ_VLAK_S` (3 min, ni izmerjeno); ali kadar se ujemata dva. Do 11. 10. 2026 je bil pogoj samo soglasje dveh -- v 16 dneh in 36 deljenjih ga ni bilo nikoli (David: „preveč sva bila optimistična“). Takrat: veliki zemljevid vlak postavi na potnikovo lego, okno vožnje odpre mali zemljevid „Kje je zdaj“, `deljenje.dopolni()` zamenja zamudo, pričakovano uro in `nepotrjen_do` (vrsta „po poročilu potnikov“), okno vožnje premakne mejo meritve do zadnje prevožene postaje (`mimo_seq`), napoved za naprej teče od potnikove lege (`common.fetchRunAndForecast`).
* **Zakaj „se je peljal“:** kdor je izstopil in čaka ob progi, je bil razlog za pravilo dveh (1. 10. 2026); iz ene lege ga ne ločimo od vlaka, ki stoji. Do 100 m s hitrostjo vozila pa peš ne pride. Izstop po tem lovita izstopna pravila (spodaj).
* **Poročilo, ki ni verodostojno: feed IN poročilo**, vsak s svojo oznako. Tabla in iskalnik: vrstica „potnik na vozilu: …“; okno vožnje: okvir s poročilom; kartica: obe vrstici. Feedova zamuda, ura in `nepotrjen_do` ostanejo.
* **Prehod šteje samo od potnika, ki se je peljal** (`stanje` poveže `deljenje_prehod` z `deljenje.peljal_ts`); en tak prehod je meritev (prej sta morala biti dva).
* **Avtobus z GPS: zmaga novejša lega** (`api._s_potniki_na_legah`, isto pravilo kot med viri leg). Starost GPS ob branju, izmerjeno 11. 10. 2026: Arriva in Nomago (NAP) mediana 29 s, LPP mestni (derp.si) 85 s; potnik 5–10 s. Star potnik svežega GPS ne premakne. Vlaki in nadomestni gredo na veliki zemljevid iz `/api/live` (`_s_potniki`), v `/api/vehicles` samo z `?trip=` -- veliki zemljevid ga za vsak vlak s potnikom bere na 5 s in vlak med poročili drsi po progi (`zemljevid.md`, izjema od pravila brez ocene). Vrstica s potnikom nosi tudi `zamuda`, `pri`, `med`, da kartica ne zaostaja za lego, in `rep` (začetek repa za vlakom, `rep_od`: zadnje 3 min potnikov, ki so se peljali, **nikoli prve 3 min deljenja**; `/zasebnost` to pove).
* **Vlak prezgodaj ne vozi**: zamuda vlaka po poročilu je navzdol omejena z 0 (`stanje`); kdor na postaji pred odhodom stoji, čaka (`Voznja.zamuda(stoji=True)`, pri vlaku vedno): A5161 je 5. 10. 2026 čakal v Kamniku in kartica je pisala „6 min prej“, tabla naprej prihod pred voznim redom.
* Mali zemljevid lego bere prek `/api/vehicles?trip=` na 5 s; toliko tudi pošiljata odjemalca (`POSILJANJE_S`; do 1. 10. 2026 10 s, Android od 1.4).
* **Ujemanje po zamudi, ne po legi** (`SOGLASJE_S`, 2 min): dve točki iz različnih trenutkov sta na različnih krajih, izpeljana zamuda pa ista. Med verodostojnimi se izbere največja skupina, ki se ujema.
* **Samo dokler so poročila sveža** (`SVEZE_S`, 120 s) **in deljenje teče** (`konec IS NULL`). Prehodi so opažanja in veljajo ves dan, tudi ko je poročevalec izstopil.
* **En pošiljatelj = en poročevalec.** Kdor na isti vožnji začne znova (osvežena stran, izgubljen odgovor na prvo pošiljanje), konča prejšnje deljenje (`konec = 'znova'`, od 1. 10. 2026; prej `potnik` kot gumb Ustavi in se ni dalo ločiti); sicer bi en telefon dal soglasje dveh. Preslikava pošiljatelj → deljenje samo v pomnilniku. Pošiljatelj = naslov, za CGNAT si ga deli več ljudi: `znova`, medtem ko staro deljenje še pošilja, je lahko drug potnik na istem vlaku.

## Zasloni (prototip potrjen 11. 10. 2026)

Platno „Deljenje lege: zasloni“ (https://claude.ai/artifact/7HtH4tb627i9HpGnWbaXoo). Kartica je **indigo** (`--deli-*` v base.css, kontrast v `preveri_paleto.py`) na vseh straneh in obeh omrežjih: vir potnika ima svojo barvo, oranžna ostane zamuda. Zamuda na kartici stoji na podlagi strani (`.deli-zam`): `--d-big` na indigu 2,8 : 1.

* **Okno vožnje: vrstica „Si na tem vlaku? Deli, kje je“** (`deli-okno`, `train.js` `posodobiDeli`). Vožnjo pozna okno, zato ni izbire: ena lega z natančnostjo do 120 m in strežnik preveri, ali je potnik ob progi in vozilo tu (`vir = okno`). **Samo, ko vožnja vozi ali odpelje v 30 min, do 10 min po prihodu na cilj** (David). Zavrnitev pove, kaj storiti: `ni_tu`/`ne_vozi` „Deli, ko vstopiš“, `ni_na_trasi` „Nisi ob progi“ (`koda` v odgovoru `/api/deli`). Strežnik začetek sprejme 15 min pred voznim redom (`KANDIDAT_PRED_S`), vrstica se pokaže 30 min prej -- kdor čaka na peronu, dobi „deli, ko vstopiš“.
* **Izbira** (domača stran, iskalnik): ikona v barvi vozila, prvi kandidat „najbolj verjetno“, opomba, da gre iz okna vožnje hitreje.
* **Deliš, drugi te še ne vidijo**: dva koraka (lega na progi ✓, „ko vlak spelje, te pokažemo“), v brskalniku nasvet o zaslonu in povezava na `/android`.
* **Drugi te vidijo** (verodostojno): „ta vlak gleda N ljudi“, kraj s hitrostjo ali „stoji N min“, zamuda „je zdaj na tablah“; zunaj okna povezava na zemljevid.
* **Hvala**: koliko minut je delil, potrjeni odhodi, koliko ljudi je gledalo (`jaz` v `stanje` odgovora). Brez spola v besedilu („Deljenje se je ob izstopu ustavilo samo“).

**Gledalci** (`deljenje.poglej`, `gledalcev`): kdor je v zadnji minuti vprašal po vožnji z živim poročilom -- okno vožnje (`/api/train/{no}/run`), vlak na velikem zemljevidu ali okno (`/api/vehicles?trip=`), vrstica s potnikom na tabli ali v iskalniku. Ključ je obiskovalec iz `obisk.py` (`kljuc_zahteve`: sol dneva, brez naslova), **samo v pomnilniku**; pošiljatelj sam ni gledalec (`_delilci`), roboti niso. Po ponovnem zagonu strežnika začne od nič.

**Koliko časa stoji** (`stanje()["stoji_s"]`): od prve točke v 40 m od sedanje lege (`STOJI_OD_M`; lega vzdolž trase ne gre nazaj). Napis od minute naprej: „stoji 3 min“ na velikem zemljevidu, kartici in v oknu vožnje.

## Kaj se hrani

Točke **projicirane na traso** (`deljenje_tocka`: razdalja vzdolž, odmik, čas, natančnost, hitrost) — brez surovih koordinat in brez identitete. Hranijo se za kasnejše izboljšanje modela (Davidova zahteva). Lega pred potrditvijo vozila ne gre nikamor; kandidati so `POST`, da koordinate ne pristanejo v dnevnikih strežnika in tunela. `/zasebnost` to pove.

## Varovalke

API nima avtentikacije. Zato:
deljenje se začne samo za vožnjo, ki ta hip lahko je tu (isto pravilo kot kandidati); vsaka točka ≤ 200 m od trase, hitrost ≤ 250 km/h; tri zaporedne natančne točke izven trase **ali odmaknjene vstran, medtem ko vozilo stoji** (`VSTRAN_M`: izstopivši potnik je sicer 10 minut „stal“ 150–185 m od proge kot vlak z rastočo zamudo) = izstop; prehod čez rob postaje samo, če se je potnik čez rob peljal (`VOZI_MS`), ne prehodil; točke z natančnostjo slabšo od 250 m se preskočijo (predor ni izstop); hitrost iz telefona na avtobusu nad 130 km/h (`HITROST_MAX_BUS_MS`) ni hitrost (brskalnik je javil 186 km/h). Omejitve na pošiljatelja so v pomnilniku kot v `stik.py`, dnevni strop čez vse v bazi; urna omejitev šteje samo deljenja, ki so se začela (zavrnjen začetek je pri slabem GPS pogost, ključ si za CGNAT deli veliko ljudi). `Content-Type: application/json` obvezen, da brskalnik pred tujo zahtevo vpraša CORS (dovoli samo GET).

## Kandidati

Postaje v okolici (vlak 12 km, avtobus 6 km), vožnje skozi njih, projekcija na traso (krožna trasa in prva točka deljenja samo v delu, kjer je vozilo po voznem redu lahko -- `Voznja.okno()`; izhodišče je tam tudi konec), nato čas: po voznem redu in zadnji zamudi mora biti vozilo tu v oknu −15 / +45 min (nesimetrično, ker zamuda, ki je feed ne pozna, je prav primer, zaradi katerega vse to obstaja). Avtobus z GPS se oceni po razdalji do vozila. Smer iz dveh leg (≥ 40 m narazen) izloči vozila v nasprotni smeri. Vlak, ki bi med postajama prehiteval več od `PREZGODAJ_VLAK_S`, ni kandidat; na postaji je (potnik čaka nanj). Izmerjeno v `docs/MERITVE.md`, „Deljenje lege“.

Kandidat nosi **uro odhoda z izhodišča in zamudo, ki bi jo vozilo imelo** (`odhod`, `zamuda_s`); gumb pove „odhod 06:30 iz Kamnik · zdaj +45 min“ (zamudo od 3 min). Brez tega sta bili dve liniji Arrive dva enaka gumba „Arriva → Ljubljana AP“, prejšnja vožnja iste linije pa nerazločljiva od prave: v 16 dneh 7 epizod z 19 začetki, med njimi izbire napačne vožnje (`docs/MERITVE.md`, „Deljenje po 16 dneh“).

## Lijak (`deljenje_lijak`, od 11. 10. 2026)

Dnevni števci brez identitete (`stej`): `kandidati` / `kandidati:0` (iskanje z vozilom / brez, ena zahteva, ne en človek), `zacetek:<odjemalec>`, `zavrnjen:<koda>` (`Zavrnjeno.koda`), `peljal`. Deljenje hrani `odjemalec` (`splet` | `aplikacija` | `android`, iz UA) in `vir` (`VIRI`, kar pove odjemalec: `domov`, `iskalnik`; `okno`, `budilka`, `vodenje` pridejo z novim zaslonom in APK). Prej se je odjemalec dal le uganiti iz razmika točk -- in prav to je pokazalo, da v brskalniku nobeno deljenje ni trajalo dlje od ~2 min. Pregled: tabela „Lijak“ v `/admin#deljenje`, stolpca „peljal“ in „od kod“.

## Pregled za skrbnika (`/admin#deljenje`)

Zemljevid in seznam današnjih deljenj po vozilih (`deljenje.pregled()`). **Kar je „javno“, pride iz `stanje()`**, ne iz lastnega računa: pregled mora pokazati isto kot tabla in zemljevid, sicer ne pove ničesar o tem, kar potnik vidi. Zraven feedova zamuda in GPS avtobusa, da se razhajanje vidi -- **samo ob živem deljenju**; feed proti potniku izpred dveh ur ni primerjava.

Sled = del trase med prvo in zadnjo sprejeto točko (`_kosi()`, razrezan na vrzelih), ker surovih koordinat ni. Cela trasa samo živim vozilom: odgovor se vleče na 10 s, trasa do 40 kB. Izmerjeno 25. 9. 2026 na razvojnem stroju, 9 vozil in 23 deljenj, nobeno živo: 10 kB (1,4 kB z gzipom), 4--19 ms; ko je traso nosilo vseh devet: 60 kB (16 kB), 15--44 ms.

Izid deljenja: `konec` iz baze, sicer `deli` (sveže točke) ali **`utihnil`** — brez konca in brez svežih točk, aplikacija zaprta ali brez signala.

## Android

`DeljenjeStoritev` = storitev v ospredju vrste `location`: lego dobiva tudi z ugasnjenim zaslonom (preizkušeno na emulatorju: 8 točk v 40 s v ozadju). Začne jo **stran** prek `Most.deliZacni()` — voznjo izbere stran, storitev samo pošilja. Dvojno pošiljanje (stran in storitev) bi bilo dva „potnika“ in lažno soglasje, zato stran v aplikaciji lege ne pošilja. `zaganja` pokrije trenutek med klicem in zagonom storitve; brez njega je prvo branje stanja deljenje razglasilo za končano.

### Deljenje ob vožnji (1.9, 6. 10. 2026)

Gumb „Pelješ se?“ je dal 12 deljenj v prvem tednu, potrjenih prehodov vlakov je bilo do 6. 10. šest. Davidova zamisel „vsi ob progi, gruča = vlak“ je zavrnjena (brskalnik lege v ozadju ne da, „ves čas“ samo v sistemskih nastavitvah, strežnik bi dobil lego ljudi, ki niso na vlaku). Namesto nje **deljenje, vezano na trenutek, ko aplikacija ve, s katero vožnjo se boš peljal**:

* **Privolitev = stikalo „Ko se peljem, pomagaj drugim“**, privzeto ugasnjeno (`Nastavitve.deliObVoznji`). V seznamu budilk in kot ponudba v vodenju do postajališča. Vklop brez dovoljenja za lego ga zaprosi; zavrnjeno = stikalo nazaj.
* **Sprožilca**: poteg budilke (`ZvonjenjeDejavnost.ustavi`, samo z zaslona, ne z gumba v obvestilu) in vodenje do postajališča, kadar je naslednja vožnja v 30 min (`pot_podrobno.js`, `Most.cakajVkrcanje`). Oba z vidnega zaslona → zadošča dovoljenje „med uporabo“. Okno vožnje kot sprožilec še ne.
* **Čakanje** (`DeljenjeStoritev.cakaj`): storitev vrste `location`, obvestilo „Deljenje ob vožnji · LP 3224 → Ljubljana“ z „Ne tokrat“, lega na 10 s. **Lega med čakanjem ne zapusti telefona.** Pri budilki vožnjo (`trip_id`) poišče tabla (`Preverjevalec`), lego postaje `/api/stations/search` — obe zahtevi brez potnikove lege.
* **Vkrcan** (`Vkrcanje.kt`, testi `VkrcanjeTest`): bil na postaji (vlak 300 m, avtobus 120 m, z negotovostjo do 200 m), nato **dve zaporedni legi** zunaj nje s hitrostjo ≥ 6 m/s in natančnostjo ≤ 100 m, ne prej kot 3 min pred pričakovanim odhodom. Brez postaje ni vkrcanja: avto ob progi ob uri odhoda ni potnik. Pol ure po odhodu (ali 2 h čakanja) konec brez deljenja.
* Od tam naprej **isto deljenje kot z gumbom**: prve točke so legi, s katerima je pravilo reklo „vkrcan“, strežnik jih preveri kot vsako prvo točko (na trasi, ob pravem času). Konec: izstop, cilj, „Ustavi“.
* Obvestilo deljenja ima svojo številko (4713): 4712 je nežni del budilke, ki ga storitev zvonjenja ob koncu pobriše -- in prav takrat se čakanje začne.

**Emulator:** `adb emu geo fix` vrne „unknown command“, ker konzola zahteva avtentikacijo (žeton v `~/.emulator_console_auth_token`). Lega gre prek vtičnice na 5554 z `auth <žeton>`. Za varen kontekst v WebView: `adb reverse tcp:8001 tcp:8001` in naslov `http://127.0.0.1:8001` (`-PkajrosUrl`, nato `pm clear`, ker je shranjen naslov močnejši).
