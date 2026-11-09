# Prenova zamud vlakov: delovni zapis (od 6. 11. 2026)

To je naloga, ki jo je dal David: „Zdaj bova pa dobro pregledala zamude vlakov. Cel sistem na novo.“ Zapis je predaja med sejami: najprej najdbe z dokazi, nato načrt in na koncu stanje.

Naloge, kot jih je naštel David:

1. Časi po postajah morajo biti dosledni. Vlak ne sme na prejšnjo postajo priti pozneje kot na naslednjo. Razumeti je treba, kaj je narobe v podatkih in zakaj.
2. Napaka, ki skoči, opisana v [2026-11-06-napoved-skok.md](2026-11-06-napoved-skok.md) (RG 318), in podobne.
3. Spremljati vlake in povezave med njimi.
4. Poskusiti dobiti več podatkov za vlake.
5. Poleg varne napovedi dodati še natančno. Prikaz zaenkrat kaže samo varno, da potnik ne zamudi.
6. Raziskati vse: vire, zgodovino, napake, nepravilnosti, okvare, manjkajoče podatke.

## Najdbe

### LPV 2206, 6. 11. 2026: tri napake naenkrat

Posnetek: Zagorje 08:08 (+15), Sava 08:02 („ura si nasprotuje“), Litija 08:10 (+1, „nadoknadil 14 min“). Vožnja 453152. Zajem v `obs`, `run`, `sz_zamuda` in vzorci zemljevida v dosjeju so to pokazali:

| ura | kdo piše | kaj |
|---|---|---|
| 07:37:37 | derp.si | +15 na **vseh 12 postankih**, prihod in odhod. Zajem se je ravno zagnal, zemljevid SŽ še ni bil prebran, zato derp.si piše vse vlake. Vir +15 je zemljevid SŽ: vlak „stoji na izhodišču“ (`Vrsta 0`) z `Zamuda_cas` 15. |
| 07:45:49 | zemljevid SŽ | prava vožnja: Hrastnik +2, nato Trbovlje +2, Zagorje +2/+3, Sava +3, Litija +1, naprej 0 do +1 |
| 07:46:49, 07:57:18, 08:07:48 | zemljevid SŽ, **zastarel odgovor** | en sam odgovor: vlak +15 pri Trbovljah oziroma Savi. Sprejet po pravilu „nazaj z večjo zamudo velja“. Hrastnik in Zagorje dobita +15 za vedno. |
| 07:52:04 | zemljevid SŽ, zastarel odgovor | vlak po voznem redu (+0). Ta je zavrnjen, ker ničla rabi potrditev. |

Zemljevid piše samo odhod. Prihod ostane napoved derp.si od 07:37 (+15). Iz para prihod +15 / odhod +1 je okno izračunalo „vlak je stal 0, nadoknadil 14 min“, pri Zagorju pa iz +2 / +15 „stal 14 min namesto 1“. `oznaci_neskladne` je izbral verigo z več postanki (+15 na Zidanem Mostu, v Hrastniku in Zagorju) in kot neskladna označil prava Trbovlje in Savo. Končna zamuda v Ljubljani je v `run` prihod +1, odhod +15.

### Zemljevid SŽ vrača zastarele odgovore

Dosje hrani vsak vzorec zemljevida od 1. 11. 13.42. Na 3 190 voženj-dneh (1.–6. 11.) se vrednost za en sam odgovor (15 s) spremeni in takoj vrne:

* 10 689-krat na ničlo (vlak „po voznem redu“),
* 202-krat na višjo zamudo (kot +15 zgoraj),
* 6-krat na nižjo neničelno.

To je 3,4 na voženj-dan. V istem odgovoru se tako obnaša več vlakov hkrati (pogosto 5–12), zato gre verjetno za odgovor drugega strežnika SŽ s starim stanjem. Ničle zajem že zavrne (`zamude_sz._nicle`), višjih ne. Isti zemljevid bere derp.si, ki nima nobenega sita.

### Ob vsakem zagonu zajema derp.si napiše napoved za vse vlake

`collector.ingest` vlake preda zemljevidu le, ko `iz_lege.sz_vodi()` drži. Ta je ob zagonu napačen, dokler zemljevid prvič ne odgovori, zato prvi poll derp.si zapiše vse vlake, tudi tiste, ki še niso odpeljali, in to z napovedjo za vse postanke. Izbruhi so 1. 11. ob 13.43, 2. 11. ob 12.05, 3. 11. ob 18.12, 4. 11. ob 8.12 in 21.47, 5. 11. ob 16.20 in 21.25, 6. 11. ob 7.38. To so zagoni ob objavah. Zemljevid nato piše samo odhode, prihod ostane napoved:

| obdobje | voženj-dni | ura nazaj ≥ 2 min | „stal ≥ 10 min“ na postanku ≤ 2 min | prihod po odhodu ≥ 2 min | V-osamelec |
|---|---|---|---|---|---|
| 1. 9.–9. 10. (derp.si) | 17 728 | 2,0 % | — | — | 1,6 % |
| 10.–31. 10. (zemljevid vodi) | 10 357 | 1,3 % | 2,0 % | 0,4 % | 0,3 % |
| 1.–6. 11. | 2 994 | **6,9 %** | **25,4 %** | 1,4 % | 0,2 % |

Od 1. 11. je takih postankov 671, od tega ima 664 prihod natanko 0. To je napoved derp.si za vlak, ki še ni odpeljal (MV 247 6. 11.: 0/0 na vseh 16 postankih ob 7.49, odhod 9.15). Skripte so v [vlaki-prenova/](vlaki-prenova/).

### Kaj zemljevid SŽ sploh pove

* **Lega je izračunana, ni GPS.** Ko SŽ zamudo poveča za minuto, vlak na zemljevidu skoči nazaj za minuto vožnje (LPV 2206 ob 07:56:18).
* **`Postaja` se menja po uri**, in sicer ob prihodu na prejšnjo postajo po voznem redu in trenutni zamudi, ne ob prehodu.
* Prave spremembe zamude (brez enojnih odklonov) so 3,1 na voženj-dan. Le 36 % jih pride ob uri `Odhod` (±75 s), torej ob registraciji odhoda s prejšnje postaje. 72 % jih pride brez menjave postaje: SŽ zamudo dviguje po minuto, ko vlak ne pride, kot bi moral.
* **Zamuda pred odhodom (`Vrsta 0`) ni zanesljiva.** Od 191 primerov z zamudo nad 0 je bila v 95 višja od prve zamude v vožnji.

Meritev na vmesni postaji torej pogosto ni meritev: je zadnja zamuda, ki jo je SŽ imel, ko je ura prešla postajo. Isto ugotavlja presoja RG 318: Kresnice, Jevnica in Laze imajo isto vrednost v 49 od 71 dni.

### RG 318 (napoved skoči)

Opis in vprašanja so v [2026-11-06-napoved-skok.md](2026-11-06-napoved-skok.md). Model se je učil iz treh dni, ki so bili smeti (osamelci V). Odprto je, iz katerega vira je vsak osamelec. Mehanizma zgoraj (napoved derp.si v `run`, zastareli odgovori) sta prva kandidata.

## Načrt

### 1. Zajem: v `run` gre samo, kar je izmerjeno in potrjeno

1. **Zemljevid vodi od zagona.** derp.si vlakov ne piše, dokler zemljevid v `SZ_VODI_S` ni dobil priložnosti.
2. **Brez napovedi v `run` za vlake.** Vrstica feeda, ki postanek postavlja v prihodnost, gre v `obs`, ne v `run`.
3. **Prihod in odhod iz istega vira.** Prvi zapis zemljevida za postanek nastavi oba, naslednji samo odhod; na cilju prihod in odhod enako.
4. **Vsaka sprememba z zemljevida rabi potrditev naslednjega odgovora**, ne le ničla. To izloči 202 višja in 10 689 ničelnih enojnih odklonov.
5. **Popravilo zgodovine**: prihodi iz napovedi derp.si od 31. 10. (in prej), kjer je zemljevid postanek izmeril. Ukaz s štetjem pred popravkom.

### 2. Usklajena pot vlaka

En pisec za vlak, ki iz vseh opazovanj sestavi dosledno pot: prihod ≤ odhod ≤ prihod na naslednjo postajo + najkrajša vožnja. Postanek dobi oznako, ali je registriran, prenesen ali ocenjen. Okno nikoli ne kaže ure, ki gre nazaj. Namesto „ura si nasprotuje“ pokaže oceno z besedo.

### 3. Napoved: porazdelitev, varna in natančna

Model vrne razpon za vsak postanek naprej. **Varna** je spodnja meja za vstop (vlak ne odpelje pred njo), za prestop in prihod pa zgornja. **Natančna** je sredina, ki zmanjša absolutno napako. Prikaz kaže samo varno, natančna gre v senco (`ocena`) in backtest. Učenje samo iz očiščene zgodovine, z zveznostjo kot merilom: napoved se ne sme spremeniti za 10 min, ker je razred dobil en dan.

Kaj prikaz zdaj zares dela (senca `kajros ocena --days 14 --network zeleznica`, 23. 10.–6. 11.):

| | MAE | v 5 min | podcenj. | **precenj.** (zamujen vlak) | strošek | n |
|---|---|---|---|---|---|---|
| na poti: prikaz | 2,35 min | 89,0 % | 7,8 % | **3,2 %** | 8,25 min | 57 626 |
| na poti: prenos zamude | 3,01 min | 82,7 % | 15,8 % | 1,5 % | 8,54 min | 57 626 |
| pred odhodom: prikaz („običajno“) | 1,44 min | 90,8 % | 4,9 % | **4,3 %** | 9,04 min | 35 120 |
| pred odhodom: vozni red | 1,48 min | 90,4 % | 9,6 % | 0,0 % | **6,48 min** | 35 120 |

Sedanji prikaz torej ni varen v Davidovem pomenu. Je kompromis, uglašen na MAE. Pred odhodom bi sam vozni red potniku prihranil 2,6 min povprečnega stroška, ker vlak z izhodišča ne odpelje pred uro. Predlog:

* **Natančna** = mediana porazdelitve, merilo MAE. Sedanji model je izhodišče.
* **Varna** = najmanjši pričakovani strošek potnika (`ocena._strosek`: čakanje razlike ali 87 min do naslednjega vlaka, potnikova rezerva 5 min). To je spodnji kvantil, ne mediana. Pred odhodom je to vozni red, razen kadar obstaja dokaz, na primer pozen vlak, od katerega je odvisen (točka 4).
* Backtest dobi stolpce `podcenj.`, `precenj.` in `strošek`, da se varna meri tudi za nazaj, ne le v senci.
* Razred z malo dnevi se skrči proti širšemu ostanku, da napoved ni nezvezna (RG 318).

### 4. Povezave med vlaki

Iz zgodovine se naučimo odvisnosti: vlak B odpelje s postaje S ne prej kot vlak A tam + h. Kandidati so obrat garniture na končni, čakanje na zvezo in križanje na enotirni progi. Odvisnost velja, kadar drži v večini dni, ko je A zamujal. To da napoved pred odhodom z izhodišča, kjer vlak nikoli ne poroča.

Prvo merjenje ([vlaki-prenova/povezave.py](vlaki-prenova/povezave.py), `run` od 1. 9.): par (A, B, S) šteje, kadar je B z izhodišča S odpeljal najmanj 2 min pred prihodom A, če je A v S prišel ≥ 5 min po B-jevem odhodu po voznem redu („drži“). Od 510 parov s ≥ 3 takimi dnevi jih 43 drži ≥ 70 % ob ≤ 20 % zamud B sicer (42 vlakov B, 25 obratov garniture), 293 pa ≤ 30 % (neodvisni). Primeri:

| A | B | postaja | razmik | drži | dni z zamudo A |
|---|---|---|---|---|---|
| LP 3211 | LP 3218 | Črnomelj | 2 min | 97 % | 38 |
| LPV 2266 | LPV 2225 | Ljubljana (obrat) | 10 min | 94 % | 32 |
| ICS 20 | RG 620 | Pragersko | 6 min | 90 % | 40 |
| LP 3229 | LP 3228 | Ivančna Gorica (obrat) | 6 min | 91 % | 35 |
| LPV 2441 | LPV 2206 | Zidani Most (obrat) | 14 min | 100 % | 6 |

LPV 2206 s posnetka je obrat LPV 2441. Zamuda „pred odhodom“ +15 na zemljevidu SŽ je bila verjetno prenesena z njega.

### 5. Straža doslednosti

Regresija 31. 10./1. 11. (25 % voženj-dni s „stal ≥ 10 min“) je bila na zaslonu šest dni, zdravje pa zeleno. Nova vrstica v `zdravje`: delež živih in današnjih voženj vlakov z uro nazaj ali s prihodom/odhodom, ki si nasprotujeta. Rumeno od 1 %, rdeče od 5 %.

### 6. Več virov (raziskava 6. 11., splet)

Javne dejanske ure prehodov nima nihče. Zemljevid SŽ (`aktivni_vlaki`) je edina javna „lega“ in ta je izračunana. Kar je novega:

| vir | kaj da | vrednost |
|---|---|---|
| tabela zamud na „stanje v prometu“ potniski.sz.si (`#zamude table.delays`; derp `sz-platform-scraper` `/delays`) | po vlaku: **prometno mesto**, minute, `actual` ali `predicted` („PREDVIDENA ZAMUDA“), prihod ali odhod | **visoka**: edina javna ločitev izmerjenega od napovedanega in kraj registracije. Brali smo jo do 11. 10. (koda 3c965ab) in opustili, ker je bila le ~5 s pred zemljevidom in piše prometno mesto, ne postanka. Za usklajeno pot (točka 2) je ravno prometno mesto tisto, kar rabimo. |
| ÖBB HAFAS (mgate; derp `gtfs-rt-hafas-lite`, od 1. 11. 2026) | zamuda po postankih, odpovedi, brez ključa | srednja: neodvisen vir vsaj za čezmejne vlake; ali ima domače LP/RG, ni preverjeno. Teden v senci. |
| SŽ-Infrastruktura, Program omrežja 2026 + priloga 2B (PDF odprt) | enotirne 882,8 km, dvotirne 324,4 km; po postaji km, glavni tiri, koristne dolžine | visoka za model križanj (točka 4) |
| SŽ-Infrastruktura, evidenca gibanj vlakov (PO 2026, 6.3) | dejanski časi na merilnih mestih, vzroki zamud UIC 450-2 | najvišja, a ni javna: pot je zahteva po ZJI. Odloči David. |
| RNE TIS | gibanje mednarodnih vlakov | ni za javnost |
| NAP | SIRI, NeTEx, GTFS; RT vlakov ni potrjen | nizka |
| HŽPP, MÁV, Trenitalia, DB | javnega RT za slovenske postaje ni ali ni potrjen | nizka |
| zamudil.si | isti viri kot mi + sestava vlaka s potniski.sz.si | sestavo poiskati v orodjih za razvijalce v Chromu |
| SŽ-PP poročilo o kakovosti 2024 | zamudne minute na 100 km: 2023 5,8; 2024 6,7 | za primerjavo s statistiko |

## Stanje (6. 11. 2026 zvečer)

Objavljeno na arwen:

* **88ec114 zajem**: zemljevid SŽ vodi od zagona (`iz_lege.sz_pricakuj`), napoved vlaka ne gre v `run` (`collector.napoved_vlaka`), prvi zapis postanka nastavi prihod in odhod, vsako stanje zemljevida potrdi naslednji spremenjen odgovor (`zamude_sz.potrdi`, `nepotrjenih` v `meta.zamude_sz`). Preverjeno ob objavi ob 14.45: derp.si ob zagonu ni zapisal nič, LP 4224 je dobil prihod = odhod ob prihodu po uri.
* **4426ec2, 6a84a68 popravilo** `kajros popravi-vlake` (meja `POPRAVI_DO_TS`, zastareli višji zapisi, nepotrjene napovedi) in straža `dosled_vlaki` v zdravju (rumeno od 1 %, rdeče od 5 %). Pognano na arwenu z Davidovim dovoljenjem: 3 975 vmesnih prihodov, 11 185 ciljev, 175 zastarelih višjih odhodov, 297 nepotrjenih napovedi.
* **603b659 okno**: `stats.uskladi_ure` pri vlaku: prejšnji postanek popusti naslednjemu, največ za zamudo naslednjega + desetino voznega časa (najmanj minuto). Samo prikaz, `run` ostane. LPV 2206 6. 11. je zdaj dosleden od Hrastnika (+2) do Ljubljane (+1).

Po popravilu, od 1. 11.: ura nazaj ≥ 2 min 3,4 % voženj-dni (prej 6,9 %), „stal ≥ 10 min“ na postanku ≤ 2 min 5,1 % (prej 25,4 %), prihod po odhodu 1,8 %. Ostanek je semantika zemljevida (spodaj), okno ga uskladi.

Merjenje modelov ([vlaki-prenova/modeli.md](vlaki-prenova/modeli.md), ce84159, še ni objavljeno): čiščenje zgodovine sedanjega modela ne spremeni (MAE 2,05, strošek 7,30). Sedanji model je torej NATANČNA, skrčenje razreda ne pomaga. VARNA je `varna_q` (rezerva + kvantil 0,25): precenj. 0,3 % proti 1,5 %, strošek 7,12 proti 7,30, MAE 2,23 (prenos 3,01). `varna_strosek` ni varna: nižji strošek je le zamik +1,9 min. Pred odhodom odvisnost od vlaka A komaj pomaga (MAE 5,91 → 5,62, resnica je približek), zato je varna pred odhodom vozni red.

**a04d16d varna v senci** (objava 6. 11. ob 15.27): `predict` vrne `varna_delay_s` (ena funkcija z backtestom, `stats.varni_ostanek`), senca piše `napoved.varna_s`, `kajros ocena` ima vrstico „varna (senca)“. Prvi posnetek ob 15.29: 31 vrstic vlakov, vse z `varna_s`, nobena nad našo oceno; 13 pred odhodom (varna = vozni red). Prikaz nespremenjen. Odločitev o prikazu 9. 11. (`KOLEDAR.md`).

**Senca 9. 11.: varna gre v prikaz za vlake na poti** ([varna](2026-11-09-koledar/varna.md)): 6 645 vrstic od popravka zajema 7. 11. 11.36, precenjenih 0,8 proti 3,1 %, strošek 6,79 proti 7,73, MAE 2,00 proti prenosu 2,54. Izvedba sre 11. 11. (`KOLEDAR.md`).

Straža `dosled_vlaki` 6. 11. ob 15.29: 8 od 388 voženj (2,1 %, rumeno), večinoma jutranje pred objavo.

Odprto:

* **„Stal X min“ je lahko napačno pripisan.** SŽ zamudo dviguje, ko je `Postaja` že naslednja, zato povečanje pade v odhod prejšnjega postanka, čeprav je vlak morda obstal na progi. Pravo mesto da tabela zamud SŽ (prometno mesto). Do takrat bi okno lahko reklo „med X in Y izgubil N min“.
* Usklajena pot iz registracij (točka 2), tabela zamud SŽ v senci, HAFAS teden, odvisnosti v modelu, zahteva po ZJI: roki v `KOLEDAR.md`.
* Varna ni nujno ≤ natančna (skrčen kvantil razreda lahko preseže mediano majhnega razreda); pred prikazom `min(varna, natančna)`.
* `ocisti_dan` je pripravljen, v `predict` ni vklopljen (ne spremeni MAE); zgodovina predhodnikov (`_dnevi_prednikov`) ni čiščena.
