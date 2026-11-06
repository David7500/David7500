# Napoved skoči za 10 minut: RG 318, 6. 11. 2026

Zapis za tistega, ki bo predelal model napovedi (`stats.predict`). Nič ni popravljeno; to je opis primera, izmerjene številke in vprašanja. David želi, da se model premisli kot celota, ne pokrpa na enem mestu.

Dokazi ob tem zapisu: [napoved-skok/rg318-dnevi.txt](napoved-skok/rg318-dnevi.txt) (zamuda na vseh 18 postankih za 71 dni), [napoved-skok/osamelci.py](napoved-skok/osamelci.py) (štetje osamelcev po vseh vlakih).

## Kaj je videl potnik

Vlak RG 318 (Dobova–Jesenice, `trip_id` 455123), 6. 11. 2026 ob 7.34, okno `/app/train/RG%20318?trip=455123&postaja=Ljubljana+Polje`.

* Laze (seq 11): izmerjeno +7 min (420 s). Uradna aplikacija SŽ kaže isto.
* Ljubljana Zalog (seq 12) in Ljubljana Polje (seq 13): naša napoved **+17 min** (1020 s).
* Ob 7.35 izmerjeno v Zalogu: +7 min. Napoved je zgrešila za 10 min, dve postaji pred potnikom.
* Ko je bil Zalog izmerjen, je napoved za Polje padla na +7 min (420 s). Potnik je videl, da zamuda „skoči“ na 17 in nato pade nazaj na 7, čeprav se z vlakom ni zgodilo nič.

## Kako je nastalo 1020 s

`GET /api/train/RG%20318/predict?stop_seq=11&delay_s=420&exclude_date=2026-11-06&trip=455123`:

| postanek | `predicted_delay_s` | `n_samples` | `same_class` | `p90_delay_s` | `basis` |
|---|---|---|---|---|---|
| Ljubljana Zalog | 1020 | 3 | true | 1884 | rezerva + historicni ostanek |
| Ljubljana Polje | 1020 | 3 | true | 1728 | rezerva + historicni ostanek |
| Ljubljana | 840 | 3 | true | 1704 | rezerva + historicni ostanek |

Pot skozi kodo (`kajros/stats.py`, funkcija `predict` in notranja `model`):

1. `delay_bucket(420)` = razred 1 (`DELAY_BUCKETS = (120, 600, 1800)`: 2–10 min).
2. Ostanki se vzamejo samo iz dni, ko je bil vlak pri Lazah v istem razredu, če jih je vsaj `MIN_PREDICT_SAMPLES = 3`. V 71 dneh zgodovine so takšni dnevi natanko trije.
3. Mediana ostankov teh treh dni za Zalog je 1320 s (+22 min). `_omejen_ostanek` jo omeji na `max(OMEJI_OSTANEK_S, 1,0 × 420) = 600 s`. Pri železnici meja velja vedno, ker `OSTANEK_BREZ_MEJE_DNI` nima ključa `zeleznica` in vrne `math.inf`.
4. Rezultat: 420 + 600 = 1020 s. Meja je preprečila +29 min, ni pa preprečila +17 min.
5. Iz Zaloga (izmerjeno 420 s) so dnevi v razredu 1 manj kot trije, zato model vzame vse dni (`n_samples` 64, `same_class` false). Mediana vseh je okoli 0, zato je napoved +7 min.

Napoved torej ni zvezna v vhodnih podatkih: isti vlak z isto zamudo dobi napoved, ki se razlikuje za 10 min, odvisno od tega, ali je razred na zadnjem izmerjenem postanku dosegel tri dneve.

## Trije dnevi, iz katerih se je model učil, so smeti

Edini dnevi z razredom 1 pri Lazah:

| dan | Jevnica | **Laze** | Zalog | Polje | Ljubljana |
|---|---|---|---|---|---|
| 26. 8. | 1200 | **240** | 1500 | 1500 | 1320 |
| 28. 8. | 1680 | **360** | 1680 | 1680 | 1500 |
| 1. 9. | 1500 | **360** | 1860 | 120 | 1680 |

Vlak med Jevnico in Lazami (4 min vožnje) ne pridobi 16–22 min in jih v naslednjih 8 min ne izgubi. Vrednost pri Lazah je napačna meritev, ne zamuda. Na isti dan so v isti vožnji še drugi taki padci (1. 9.: Polje 120 med 1860 in 1680, Kranj 0 med 1620 in 1380).

Model se je iz teh treh dni „naučil“, da vlak z majhno zamudo pri Lazah do Zaloga izgubi 20 min. V resnici je vsak dan, ko je bil vlak pri Lazah res v razredu 1, natanko danes, in danes ni izgubil nič.

### Koliko je takih osamelcev povsod

`osamelci.py` šteje padec „V“: zamuda na postanku je vsaj 10 min nižja od **obeh** sosedov v isti vožnji. Lokalna kopija `data/kajros.sqlite` (razvojni zajem, ne arwen), vse vožnje z `network = 'zeleznica'`, 21. 8.–6. 11. 2026:

| mesec | osamelcev | voženj-dni | delež |
|---|---|---|---|
| avgust | 274 | 4 530 | 6,0 % |
| september | 266 | 9 524 | 2,8 % |
| oktober | 142 | 6 280 | 2,3 % |
| november (do 6.) | 39 | 1 343 | 2,9 % |

Skupaj 721 na 21 677 voženj-dni. Od tega 325 (45 %) z vrednostjo točno 0, ostali so majhne pozitivne vrednosti (60–540 s). Od 15. 10. jih je še vedno 114 (59 z 0), torej to ni le težava zgodnjega zajema. RG 318 jih ima 15, med njimi 5. 10. Lesce-Bled 0 med 1980 in 1740.

`collector.py` že sumi skoka na nič (`SUSPECT_DROP_S = 300`), a le na 0, in le ob zajemu. Padca na 240 ali 360 ne vidi nihče, zgodovina v `run` pa ga hrani za vedno in model ga bere.

**Odprto:** številke ponovi na kopiji z arwena (`VACUUM INTO`, spomin `analiza-baze-arwen`). Ugotovi, iz katerega vira je vsak osamelec (`obs`, `sz_zamuda`, `delay_report`). Preveri, ali 0 pomeni neizpolnjeno polje v protobufu (pravilo „nikoli ne beri `stu.arrival.delay` naravnost“) ali vlak brez zamude na zemljevidu SŽ.

## Zgodovina ima dva režima, model ju meša

Ko pogledaš vseh 71 dni RG 318 (`rg318-dnevi.txt`), se okoli 10.–17. 10. 2026 spremeni sama oblika podatkov. To je čas, ko je vodstvo prevzel zemljevid SŽ (`zamude_sz.py`, od 10. 10.; `zajem.md`).

**Do ~10. 10.** (derp.si):

* Zamuda v Ljubljani je skoraj vsak dan **3 min nižja** kot v Polju (rezerva voznega reda v Ljubljani je 180 s; vlak jo porabi). Primer 22. 9.: Polje 1140, Ljubljana 960.
* Za Ljubljano zamuda pada naprej proti Kranju in Jesenicam (22. 9.: Kranj 540, Jesenice 420).
* Jesenice so izmerjene skoraj vsak dan.

**Od ~17. 10.** (zemljevid SŽ):

* Zamuda **nikoli ne pade**. Ljubljana je vedno enaka ali višja kot Polje (24. 10.: Zalog 960, Polje 1380, Ljubljana 1740).
* Litostroj in Kranj imata pogosto **točno isto vrednost** kot Ljubljana (23. 10.–2. 11. vsak dan). Vlak, ki vozi 24 min med Litostrojem in Kranjem, ne bi imel vsak dan iste zamude do sekunde.
* Jesenic skoraj ni (`None`), dvakrat 0 (3. in 4. 11.).
* Vrednost se zatakne na manjših postajah: Kresnice = Jevnica = Laze v 49 od 71 dni, Litija = … = Laze v 32 od 71. Skok pride v Zalogu ali Ljubljani (10.–5. 11.: Laze → Ljubljana +2 do +14 min, običajno +7 do +10).

Verjetna razlaga (ni dokazana): zemljevid SŽ ima za vlak eno samo trenutno zamudo (`Zamuda_cas`) in jo osveži na večjih postajah. Pri manjših postajah ostane stara vrednost; ko vlak mine več postankov med dvema branjema, dobijo vsi isto. Rezerva voznega reda se na zemljevidu ne pokaže, ker SŽ zamude navzdol ne popravi, dokler vlak ne pride na naslednjo postajo, ki jo osvežijo.

Posledice za model:

* Ostanek „Laze → Ljubljana“ iz starega režima je okoli −2 min, iz novega okoli +8 min. Mediana čez oba ne opisuje nobenega.
* `_after_slack` predpostavlja, da vlak rezervo porabi. V novem režimu je meritev ne pokaže nikoli. Model pravilno napove porabo, meritev pa reče, da je ni bilo, in zato napaka zgleda kot napaka modela. Ni jasno, katera stran ima prav: lahko vlak res ne porabi rezerve, lahko pa SŽ zamude navzdol ne objavlja.
* Ocena `kajros ocena` (kaj je prikaz trdil 25 min prej in kaj je bilo) v novem režimu primerja napoved z vrednostjo, ki ima isto napako kot vir. To je treba vedeti, preden se številkam verjame.

**Odprto:** razdeli backtest na dva obdobja (do 9. 10. in od 17. 10.) in primerjaj MAE modela in prenosa v vsakem posebej. Preštej, pri koliko vlakih je „zamuda v Ljubljani ≥ Polje“ pred in po menjavi vira. Ena vožnja ni vzorec.

## Kaj naj premisli predelava (vprašanja, ne odločitve)

1. **Čiščenje zgodovine pred učenjem.** Osamelec „V“ v isti vožnji je skoraj zagotovo napaka. Vprašanji sta dve: ali naj ga zavrne zajem (preden gre v `run`), ali naj ga preskoči samo učenje (`by_day` v `predict`, `backtest._medians`). Brisanje iz `run` bi vplivalo tudi na statistiko in prikaz preteklih dni.
2. **Razred z malo dnevi.** Prag tri dni je bil izmerjen (`model.md`: prag 1 MAE 2,19, prag 3 MAE 1,99), a samo kot povprečje čez vse naloge. Pri treh dneh en sam napačen dan premakne mediano. Kandidata: krčenje proti mediani vseh dni z utežjo po številu dni (kot `PRESTOP_IZHODISCE` pri prestopih), ali mediana razreda samo, če se ne razlikuje preveč od mediane vseh. Merilo mora biti tudi **zveznost**: napoved se ne sme spremeniti za 10 min samo zato, ker je razred na sosednjem postanku dobil ali izgubil en dan.
3. **Režim vira kot del učne množice.** Model se uči le iz dni, ki imajo isti vir kot danes; ali drugače ločen režim; ali pa krajše okno (`days` je privzeto 90).
4. **Vlak, ki je danes boljši kot kdajkoli.** RG 318 pri Lazah običajno zamuja okoli 19 min (mediana 1110 s, 66 dni), danes 7. Kadar je trenutna zamuda zunaj vsega, kar je ta vlak kdaj imel, je prenos zamude verjetno varnejši od ostanka.
5. **Meja ostanka 600 s pri železnici.** Danes je odrezala 1320 → 600. Brez nje bi bila napoved +29 min. Ali je meja prava številka, ali je bolje ostanek z malo dnevi zavreči.
6. **Zatikanje na manjših postajah.** Če je vrednost na Kresnicah, v Jevnici in pri Lazah ista, ni nujno, da je vlak tam res imel to zamudo. Prikaz jo kaže kot „izmerjeno“. Preveri, ali to drži za vse vlake, preden se model uči iz teh postankov kot iz meritev.

Vsako spremembo izmeri na obeh merilih (`kajros backtest` in `kajros ocena`) in proti prenosu zamude. Kar ne premaga prenosa, ne gre v prikaz.

## Ponovitev

```bash
# napoved iz Laz in iz Zaloga
curl -s 'https://kajros.app/api/train/RG%20318/predict?stop_seq=11&delay_s=420&exclude_date=2026-11-06&trip=455123'
curl -s 'https://kajros.app/api/train/RG%20318/predict?stop_seq=12&delay_s=420&exclude_date=2026-11-06&trip=455123'
# osamelci po vseh vlakih (lokalna baza; na kopiji z arwena zamenjaj pot)
./venv/bin/python docs/presoja/napoved-skok/osamelci.py
```
