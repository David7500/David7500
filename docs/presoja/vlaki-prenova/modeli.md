# Modeli napovedi za vlake: čiščenje zgodovine, natančna in varna (6. 11. 2026)

Točka 3 načrta iz [2026-11-06-vlaki-prenova.md](../2026-11-06-vlaki-prenova.md). Koda: `kajros/backtest.py` (`evaluate_varne`, `porocilo_ciscenja`, `MODELI_VARNI`), `kajros/stats.py` (`ocisti_dan`, `predict(ocisti=...)`), `kajros/ocena.py` (`strosek_para`). Ponovitev:

```bash
KAJROS_DATA_DIR=<mapa s kajros.sqlite> ./venv/bin/python -m kajros.cli backtest --varne [--vzorec N] [--dni N]
```

## Podatki in postopek

* Kopija arwenove baze **6. 11. 2026 ob 14.40** (pred popravkom `kajros popravi-vlake --zapisi` ob 15.10), samo `network = 'zeleznica'`: 435 562 vrstic `run`, 78 dni (21. 8.–6. 11.), 35 888 voženj-dni, 791 vožnja. Arwenova baza je zdaj popravljena; številke spodaj so na nepopravljeni kopiji.
* Izpuščanje dneva, `MAX_HORIZON` 12 postankov, 2 828 935 nalog v ocenjevanju (cele baze, brez `--vzorec`). Ocenjevanje je **samo na nalogah, kjer oba postanka preživita čiščenje** (isti nabor za vse modele in obe vrsti učenja). Brez tega bi primerjali razliko vzorcev. Čas: 7,5 min na vse.
* Modeli z učenjem imajo dve vrstici: učeni iz vseh dni, in „, cisto“ (učeni samo iz nalog, kjer oba postanka preživita čiščenje). Testni dan je v obeh primerih izpuščen v `predict`.
* Obdobji: `do 9. 10.` (derp.si piše zamude), `od 17. 10.` (zemljevid SŽ). 10.–16. 10. je samo v `vse`.
* Metrike: `podcenj.`/`precenj.` = delež napovedi > 5 min pod/nad resnico, `strošek` = `ocena.strosek_para` (podcenitev = čakanje, precenitev = razmik 87 min, potnikova rezerva 5 min), `odklon` = povprečje (napoved − resnica), **zveznost** = povprečje |napoved(i+1 → j) − napoved(i → j)| za isti cilj j in zaporedni izmerjeni izhodišči iste vožnje z |Δzamuda| ≤ 60 s, `skok` = delež teh parov z razliko > 5 min.

## Čiščenje učne zgodovine (`stats.ocisti_dan`)

Ena funkcija za `backtest._delays_by_day(ocisti=True)`, `backtest.build_tasks(oznaci=True)` in `stats.predict(ocisti=True)`. **V `predict` je pripravljena, ne vklopljena** (privzeto `ocisti=False`, prikaz se ne spremeni). Zgodovina predhodnikov (`_dnevi_prednikov`) nima `feed_ts` in ostane neočiščena.

* **(a) nepotrjena napoved**: zadnji zapis `run.feed_ts` starejši od voznorednega prihoda + zamuda − 120 s. **Samo od 10. 10. 2026** (`stats.FEED_TS_NAS_OD`): prej je `feed_ts` žig derp.si, ki se ne premakne, dokler se vožnja ne spremeni, in pravilo bi zadelo 75 % postankov (na moji kopiji 198 077 od 266 564; mediana „zadnji zapis − pričakovani prihod“ je −3,5 min, od 17. 10. +4,8 min).
* **(b) fizika**: zamuda med izmerjenima postankoma a < b ne more pasti za več kot `Σ max(0, postanek − MIN_DWELL_S)` na a+1..b in 120 s. Pogoj je `u_a ≤ u_b + 120` z `u_k = d_k + kumulativna rezerva do k`; ostane najdaljša veriga (`_najboljsa_veriga` z drugim pogojem), ostali so osamelci V in Λ. Pogoj velja med zaporednima članoma verige.

Koliko odstranita (postanki; voženj-dni z vsaj enim odstranjenim):

| obdobje | postankov | (a) | (b) | voženj-dni | z (a) | z (b) |
|---|---|---|---|---|---|---|
| do 9. 10. | 266 564 | 0 (izpuščeno) | 2 690 (1,0 %) | 22 322 | 0 | 1 574 (7,1 %) |
| od 17. 10. | 131 857 | 1 131 (0,9 %) | 1 223 (0,9 %) | 10 305 | 396 (3,8 %) | 763 (7,4 %) |
| vse | 435 562 | 1 135 | 4 196 (1,0 %) | 35 888 | 400 | 2 507 (7,0 %) |

(b) odstrani 1 % postankov, a v 7 % voženj-dni. Pri tem so tudi pravi hitri vlaki (nadoknadil več, kot dovoli rezerva postankov), ki jih pravilo po navodilu ne loči od smeti. Čez vse ostane 99 % postankov, torej učna množica ostane skoraj cela.

## Rezultati

### do 9. 10.

| model | n | MAE (min) | v 5 min | podcenj. | precenj. | strošek (min) | odklon (min) | zveznost (min) | skok > 5 min |
|---|---|---|---|---|---|---|---|---|---|
| prenos | 1727837 | 3,09 | 82,3 % | 16,3 % | 1,3 % | 8,67 | -2,47 | 0,14 | 0,0 % |
| fizika | 1727837 | 3,22 | 81,4 % | 18,6 % | 0,0 % | 8,05 | -3,05 | 0,12 | 0,0 % |
| fizika_razred (sedanji) | 1727837 | 2,03 | 90,8 % | 7,9 % | 1,3 % | 7,19 | -0,99 | 0,36 | 0,3 % |
| fizika_razred_skrcen n0=2 | 1727837 | 2,02 | 90,4 % | 8,1 % | 1,4 % | 7,28 | -0,98 | 0,35 | 0,3 % |
| fizika_razred_skrcen n0=4 | 1727837 | 2,02 | 90,5 % | 8,1 % | 1,4 % | 7,24 | -0,99 | 0,35 | 0,2 % |
| varna_min | 1727837 | 2,98 | 83,2 % | 16,7 % | 0,2 % | 7,86 | -2,73 | 0,16 | 0,0 % |
| varna_q 0,10 | 1727837 | 2,70 | 85,3 % | 14,6 % | 0,1 % | 7,63 | -2,58 | 0,30 | 0,2 % |
| varna_q 0,25 | 1727837 | 2,26 | 88,3 % | 11,4 % | 0,2 % | 7,15 | -1,93 | 0,29 | 0,1 % |
| varna_strosek | 1727837 | 4,12 | 91,4 % | 7,2 % | 1,4 % | 4,60 | 1,68 | 0,36 | 0,4 % |
| varna_strosek brez zamika | 1727837 | 3,32 | 81,9 % | 18,0 % | 0,0 % | 8,31 | -3,28 | 0,37 | 0,5 % |
| fizika_razred (sedanji), cisto | 1727837 | 2,02 | 90,8 % | 7,9 % | 1,4 % | 7,20 | -0,98 | 0,36 | 0,3 % |
| fizika_razred_skrcen n0=2, cisto | 1727837 | 2,02 | 90,4 % | 8,1 % | 1,5 % | 7,28 | -0,97 | 0,35 | 0,2 % |
| fizika_razred_skrcen n0=4, cisto | 1727837 | 2,02 | 90,5 % | 8,1 % | 1,4 % | 7,24 | -0,98 | 0,34 | 0,2 % |
| varna_min, cisto | 1727837 | 2,98 | 83,2 % | 16,7 % | 0,2 % | 7,86 | -2,72 | 0,16 | 0,0 % |
| varna_q 0,10, cisto | 1727837 | 2,63 | 85,9 % | 14,1 % | 0,1 % | 7,55 | -2,50 | 0,28 | 0,1 % |
| varna_q 0,25, cisto | 1727837 | 2,24 | 88,5 % | 11,3 % | 0,3 % | 7,13 | -1,90 | 0,29 | 0,1 % |
| varna_strosek, cisto | 1727837 | 4,14 | 91,5 % | 6,9 % | 1,6 % | 4,60 | 1,81 | 0,31 | 0,1 % |
| varna_strosek brez zamika, cisto | 1727837 | 3,20 | 83,0 % | 16,9 % | 0,0 % | 8,18 | -3,15 | 0,32 | 0,2 % |

### od 17. 10.

| model | n | MAE (min) | v 5 min | podcenj. | precenj. | strošek (min) | odklon (min) | zveznost (min) | skok > 5 min |
|---|---|---|---|---|---|---|---|---|---|
| prenos | 881284 | 2,98 | 83,6 % | 15,4 % | 1,1 % | 8,36 | -2,40 | 0,13 | 0,0 % |
| fizika | 881284 | 3,16 | 82,2 % | 17,8 % | 0,0 % | 7,97 | -2,96 | 0,14 | 0,1 % |
| fizika_razred (sedanji) | 881284 | 2,17 | 90,6 % | 7,8 % | 1,6 % | 7,41 | -0,96 | 0,48 | 0,7 % |
| fizika_razred_skrcen n0=2 | 881284 | 2,17 | 90,3 % | 8,0 % | 1,8 % | 7,51 | -0,95 | 0,47 | 0,7 % |
| fizika_razred_skrcen n0=4 | 881284 | 2,17 | 90,3 % | 8,0 % | 1,7 % | 7,49 | -0,95 | 0,47 | 0,6 % |
| varna_min | 881284 | 2,92 | 84,1 % | 15,8 % | 0,2 % | 7,78 | -2,63 | 0,17 | 0,0 % |
| varna_q 0,10 | 881284 | 2,66 | 86,4 % | 13,6 % | 0,1 % | 7,56 | -2,50 | 0,34 | 0,3 % |
| varna_q 0,25 | 881284 | 2,30 | 88,9 % | 10,8 % | 0,3 % | 7,13 | -1,86 | 0,36 | 0,3 % |
| varna_strosek | 881284 | 4,24 | 91,3 % | 6,7 % | 2,0 % | 5,04 | 1,77 | 0,41 | 0,5 % |
| varna_strosek brez zamika | 881284 | 3,25 | 83,3 % | 16,6 % | 0,0 % | 8,22 | -3,18 | 0,41 | 0,7 % |
| fizika_razred (sedanji), cisto | 881284 | 2,16 | 90,6 % | 7,8 % | 1,6 % | 7,42 | -0,95 | 0,47 | 0,7 % |
| fizika_razred_skrcen n0=2, cisto | 881284 | 2,16 | 90,3 % | 7,9 % | 1,8 % | 7,52 | -0,94 | 0,46 | 0,7 % |
| fizika_razred_skrcen n0=4, cisto | 881284 | 2,17 | 90,3 % | 7,9 % | 1,8 % | 7,50 | -0,94 | 0,46 | 0,6 % |
| varna_min, cisto | 881284 | 2,91 | 84,1 % | 15,8 % | 0,2 % | 7,77 | -2,62 | 0,17 | 0,0 % |
| varna_q 0,10, cisto | 881284 | 2,59 | 86,9 % | 13,1 % | 0,1 % | 7,48 | -2,41 | 0,32 | 0,2 % |
| varna_q 0,25, cisto | 881284 | 2,28 | 89,0 % | 10,6 % | 0,3 % | 7,11 | -1,83 | 0,35 | 0,2 % |
| varna_strosek, cisto | 881284 | 4,26 | 91,5 % | 6,3 % | 2,2 % | 5,04 | 1,90 | 0,35 | 0,2 % |
| varna_strosek brez zamika, cisto | 881284 | 3,12 | 84,3 % | 15,6 % | 0,0 % | 8,08 | -3,05 | 0,36 | 0,3 % |

### vse

| model | n | MAE (min) | v 5 min | podcenj. | precenj. | strošek (min) | odklon (min) | zveznost (min) | skok > 5 min |
|---|---|---|---|---|---|---|---|---|---|
| prenos | 2828935 | 3,01 | 83,0 % | 15,8 % | 1,2 % | 8,49 | -2,41 | 0,14 | 0,0 % |
| fizika | 2828935 | 3,15 | 81,9 % | 18,1 % | 0,0 % | 7,98 | -2,97 | 0,13 | 0,1 % |
| fizika_razred (sedanji) | 2828935 | 2,05 | 90,8 % | 7,7 % | 1,5 % | 7,30 | -0,95 | 0,40 | 0,5 % |
| fizika_razred_skrcen n0=2 | 2828935 | 2,05 | 90,4 % | 8,0 % | 1,6 % | 7,39 | -0,94 | 0,40 | 0,4 % |
| fizika_razred_skrcen n0=4 | 2828935 | 2,05 | 90,5 % | 8,0 % | 1,6 % | 7,35 | -0,95 | 0,39 | 0,4 % |
| varna_min | 2828935 | 2,91 | 83,7 % | 16,2 % | 0,2 % | 7,79 | -2,65 | 0,16 | 0,0 % |
| varna_q 0,10 | 2828935 | 2,64 | 85,9 % | 14,1 % | 0,1 % | 7,57 | -2,51 | 0,31 | 0,2 % |
| varna_q 0,25 | 2828935 | 2,25 | 88,7 % | 11,0 % | 0,3 % | 7,14 | -1,87 | 0,32 | 0,2 % |
| varna_strosek | 2828935 | 4,14 | 91,5 % | 6,8 % | 1,7 % | 4,72 | 1,76 | 0,37 | 0,4 % |
| varna_strosek brez zamika | 2828935 | 3,25 | 82,6 % | 17,3 % | 0,0 % | 8,23 | -3,19 | 0,38 | 0,5 % |
| fizika_razred (sedanji), cisto | 2828935 | 2,05 | 90,8 % | 7,7 % | 1,5 % | 7,30 | -0,94 | 0,40 | 0,4 % |
| fizika_razred_skrcen n0=2, cisto | 2828935 | 2,04 | 90,5 % | 7,9 % | 1,6 % | 7,39 | -0,93 | 0,39 | 0,4 % |
| fizika_razred_skrcen n0=4, cisto | 2828935 | 2,04 | 90,5 % | 7,9 % | 1,6 % | 7,36 | -0,94 | 0,39 | 0,4 % |
| varna_min, cisto | 2828935 | 2,91 | 83,7 % | 16,1 % | 0,2 % | 7,79 | -2,64 | 0,16 | 0,0 % |
| varna_q 0,10, cisto | 2828935 | 2,58 | 86,4 % | 13,5 % | 0,1 % | 7,50 | -2,43 | 0,29 | 0,1 % |
| varna_q 0,25, cisto | 2828935 | 2,23 | 88,8 % | 10,9 % | 0,3 % | 7,12 | -1,84 | 0,31 | 0,2 % |
| varna_strosek, cisto | 2828935 | 4,16 | 91,7 % | 6,5 % | 1,8 % | 4,72 | 1,89 | 0,32 | 0,1 % |
| varna_strosek brez zamika, cisto | 2828935 | 3,13 | 83,7 % | 16,3 % | 0,0 % | 8,11 | -3,07 | 0,34 | 0,3 % |


### Odvisnost od posameznega pravila

Test nabor je drugačen pri vsaki nastavitvi, zato absolutne številke niso primerljive; primerljiv je razmik surovo/čisto znotraj nastavitve (celotno obdobje):

| nastavitev | n | sedanji, surovo MAE / strošek | sedanji, čisto MAE / strošek |
|---|---|---|---|
| obe pravili | 2 828 935 | 2,05 / 7,30 | 2,05 / 7,30 |
| samo (b) | 2 832 961 | 2,05 / 7,30 | 2,05 / 7,30 |
| samo (a) | 2 884 249 | 2,15 / 7,63 | 2,15 / 7,63 |


## Sklep

**Čiščenje učne zgodovine na natančnost ne vpliva.** Celotno obdobje, sedanji model: MAE 2,05 → 2,05, strošek 7,30 → 7,30, zveznost 0,40 → 0,40; „od 17. 10.“ 2,17 → 2,16. Ocenjevalni nabor je pri tem enak, torej ni učinek vzorca. Čiščenje (b) zato ni popravilo modela, ampak **higiena merila**: 1 % postankov (7 % voženj-dni) so osamelci in jih backtest šteje kot napake modela. Samo (a) (zadene le 0,9 % postankov od 17. 10.) ne spremeni ničesar. Ni dokazano, da bi bil RG 318 posledica smeti v učenju: skoki > 5 min so pri sedanjem modelu 0,5 % parov, čiščenje jih zmanjša le na 0,4 %.

**Najboljša natančna po MAE in zveznosti: ni razlike, ki bi jo vzorec ločil.** Skrčen razred (n0 = 4, čisto) ima MAE 2,04 in zveznost 0,39 proti 2,05 in 0,40 pri sedanjem, ob strošku 7,36 proti 7,30 in precenj. 1,6 % proti 1,5 %. Pri n0 = 2 enako. Skrčenje torej ne izboljša zveznosti (skok > 5 min 0,4 % proti 0,4–0,5 %); prag treh dni v sedanjem modelu ni slabši. `prenos` in `fizika` sta najzveznejša (0,13–0,14) in najmanj natančna (MAE 3,0–3,15). Priporočilo: ostati pri sedanjem modelu; skrčenje samo, če kdo hoče utež namesto praga, brez pričakovane koristi.

**Najboljša varna: `varna_q 0,25` (razred skrčen n0 = 4, čisto).** Celotno obdobje: precenj. 0,3 % (sedanji 1,5 %), strošek 7,12 (sedanji 7,30), MAE 2,23 (sedanji 2,05), podcenj. 10,9 % (sedanji 7,7 %), v 5 min 88,8 %. Torej pet krat manj zamujenih vlakov in nižji strošek, ob 0,18 min slabšem MAE. Pri „od 17. 10.“ enako (precenj. 0,3 %, 7,11 proti 7,41 sedanji). `varna_q 0,10` ima precenj. 0,1 %, a strošek 7,50 (slabši od sedanjega). `varna_min` (min(sedanji, prenos)) ima precenj. 0,2 %, a strošek 7,79: preveč čakanja. `fizika` (samo rezerva) precenj. 0,0 %, strošek 7,98.

**`varna_strosek` ni varna.** Formalni minimum stroška (4,72) je skoraj ves zamik: odklon +1,9 min (napoved v povprečju za 1,9 min pozno), ker potnik po definiciji pride 5 min pred prikazano uro, in vsaka prikazana ura, ki je 5 min po pričakovani, mu odvzame čakanje. Brez zamika (`varna_strosek brez zamika`) je strošek 8,11, slabši od sedanjega 7,30, precenj. pa 0,0 %. Precenj. pri zamaknjeni različici je 1,8 %, ne manj od sedanjega. To je isto opozorilo kot v `model.md` („ne zamikaj“), samo v drugo smer: `strošek` je občutljiv na zamik, zato ga ne bi uporabljal kot edino merilo; `precenj.` in `odklon` morata stati ob njem.

Zveznost je sicer majhna težava v backtestu (RG 318 ostaja redek primer): povprečna razlika med sosednjima izhodiščema 0,4 min, v 0,4–0,5 % parov skok nad 5 min.

## Odvisnost za odhod z izhodišča (točka 5, neobvezno)

`docs/presoja/vlaki-prenova/pred_odhodom.py`; ista kopija, `run` od 1. 9. Par (A, B, S) velja, če v drugih dneh drži ≥ 70 % ob ≤ 20 % zamud B sicer (isto kot `povezave.py`); 2 642 parov, 567 vlakov B. Resnica = zamuda B na prvem izmerjenem od 2. in 3. postanka (odhoda z izhodišča ne poroča nihče, zato **približek, ki vsebuje tudi zamudo na prvem odseku**). Nabor: dnevi B, kjer obstaja veljaven par (1 814 nalog, A zamuja ≥ 5 min po razmiku samo v 49):

| vse | n | MAE | v 5 min | podcenj. | precenj. | strošek |
|---|---|---|---|---|---|---|
| vozni red | 1 814 | 5,91 | 63,1 % | 36,9 % | 0,0 % | 10,91 |
| običajno (mediana drugih dni) | 1 814 | 4,27 | 72,0 % | 19,6 % | 8,4 % | 14,27 |
| odvisnost od A (znano pred B) | 1 814 | 5,62 | 63,8 % | 35,9 % | 0,2 % | 10,74 |
| odvisnost od A (A prispe, zgornja meja) | 1 814 | 3,37 | 84,8 % | 10,4 % | 4,7 % | 11,04 |

Odvisnost brez popravka z znano zamudo A (zamuda na A-jevem prejšnjem postanku, ki ga je A odpeljal ≥ 5 min pred B) prinese komaj kaj (MAE 5,91 → 5,62, strošek 10,91 → 10,74), ker A bistveno zamuja le pri 3 % nalog. „Običajno“ ima nižji MAE, a precenj. 8,4 % (nevarno). Zgornja meja z A-jevo dejansko zamudo kaže, da bi odvisnost lahko pomagala, če bi vedeli, kdaj A res pride; to ni merjeno. Zaključek: za zdaj vozni red.

## Kaj ni narejeno

* `predict(ocisti=True)` ni vklopljen; ni merjeno na senci (`kajros ocena`).
* Merjeno je samo `kajros backtest` (zgodovina s kratkimi skoki), ne števila, ki jo je potnik videl 25 min prej. `varna_q` in `varna_strosek` bi bilo treba izmeriti še tam, preden gre karkoli v prikaz.
* `n0` za `varna_q` je fiksen (4); razmik med kvantili 0,10 in 0,25 ni optimiziran.
* Kopija je pred `popravi-vlake --zapisi` (arwen, 6. 11. 15.10); ponovitev na popravljeni bazi lahko spremeni (b).
