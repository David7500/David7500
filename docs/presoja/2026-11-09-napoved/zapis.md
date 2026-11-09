# Predelava modela napovedi za vlake: podobni dnevi + veriga (9. 11. 2026)

Odgovor na [2026-11-06-napoved-skok.md](../2026-11-06-napoved-skok.md) (RG 318: napoved skoči za 10 min, ker je razred zamude dobil tretji dan) in na Davidovo navodilo, naj se model premisli kot celota. Točka 3 prenove ([2026-11-06-vlaki-prenova.md](../2026-11-06-vlaki-prenova.md)).

Stanje: model je v kodi (`stats.mesanice_naprej`, `stats.iz_mesanice`) in **teče v senci** (`napoved.podobni_s`, `napoved.podobni_varna_s`). Prikaz se ni spremenil. Odločitev o prikazu je v `KOLEDAR.md`.

## Kaj je bilo narobe z razredom

Sedanji model (`stats.predict`) vzame mediano ostanka iz dni, ko je bil vlak na izhodiščnem postanku v istem razredu zamude (meje 2, 10, 30 min), če so taki dnevi vsaj trije; sicer iz vseh dni. Tri težave, vse izmerjene spodaj:

1. **Prag in meja razreda sta stopnici.** Dan, ki pride v razred ali iz njega, zamenja učno množico. Zamuda, ki se med sosednjima postankoma spremeni za manj kot minuto, a prestopi mejo razreda, tudi.
2. **Zgodovina meša režime.** Do 10. 10. je zamude pisal derp.si, od 17. 10. zemljevid SŽ, 6.–7. 11. se je zajem spet spremenil. Ostanek »Laze → Ljubljana« pri RG 318 je bil v starem režimu okoli −2 min, v novem okoli +8. Vsi dnevi 90-dnevnega okna štejejo enako.
3. **Učni vzorec razreda je majhen.** Za napoved i → j štejejo samo dnevi s podobno zamudo na i. Koraki med postanki pa se dajo učiti iz vseh dni, ko sta oba postanka izmerjena.

Prejšnje merjenje (`vlaki-prenova/modeli.md`) je krčenje razreda in čiščenje zgodovine zavrnilo, ker se povprečje ni premaknilo. Merilo je izpuščalo en dan in učilo iz vseh drugih, **tudi prihodnjih**. To je sedanjemu modelu po menjavi režima dalo dni, ki jih produkcija takrat ni imela: MAE 2,20 z izpuščanjem dneva proti 2,30 z učenjem samo iz preteklih dni (isti vzorec, spodaj). Zato je tu glavni protokol **naprej**: model za dan D vidi samo dni pred D, kot produkcija.

## Model

Vsak pretekli dan dobi utež namesto mesta v razredu:

* **podobnost zamude**: jedro `exp(−½·((d − d_dan)/h)²)`, `h = 90 s + 0,25·|d|` (pri +2 min je podoben dan z ±2 min, pri +30 min z ±9 min);
* **starost**: razpolovna doba 21 dni.

Napoved za postanek j je kvantil utežene mešanice dveh delov:

* **neposredni podobni dnevi**: ostanek i → j vsakega dne (po porabljeni rezervi voznega reda, kot doslej);
* **veriga** s težo štirih dni: porazdelitev zamude, ki jo dobimo, če gremo po korakih med postanki (hrbtenica so postanki, izmerjeni v vsaj polovici dni). Vsak korak je utežen z istim jedrom na zamudi pred korakom in s predhodnikom treh dni iz vseh dni. Zamuda v verigi je na mreži ene minute in ne gre pod nič.

Ostanek je omejen kot doslej (`_omejen_ostanek`, `max(10 min, trenutna zamuda)`), učenje je iz očiščene zgodovine (`ocisti_dan`). **Natančna** je mediana mešanice, **varna** njen kvantil 0,30; ker sta iz iste porazdelitve, varna nikoli ni nad natančno (odprta točka prenove).

## Meritve

Podatki: kopija železniškega dela arwenove baze 9. 11. 2026 ob 21.10 (po popravilu zgodovine 6.–7. 11.): 453 086 vrstic `run`, 37 023 voženj-dni, 21. 8.–9. 11.; 184 792 vrstic sence. Skripte: [modeli2.py](modeli2.py) (zgodovina), [senca2.py](senca2.py) (vrstice sence), [izvoz_vlaki.py](izvoz_vlaki.py) (kopija). Stolpci kot v `modeli.md`; »vožnje s skokom« = delež voženj-dni, kjer se napoved za isti cilj med sosednjima izmerjenima izhodiščema (zamuda se razlikuje ≤ 60 s) spremeni za več kot 5 min. To je, kar potnik vidi; delež parov (0,5–1 %) je težavo skrival.

### Merilo 1: zgodovina, učenje samo iz preteklih dni

Dnevi 17. 10.–9. 11. (zemljevid SŽ), vsaka šesta vožnja-dan: 1 907 voženj-dni, 168 303 nalog, do 12 postankov naprej.

| model | MAE (min) | v 2 min | podcenj. | precenj. | strošek (min) | odklon | zveznost (min) | vožnje s skokom |
|---|---|---|---|---|---|---|---|---|
| prenos | 3,03 | 66,8 % | 15,2 % | 1,29 % | 8,54 | −2,38 | 0,13 | 0,0 % |
| razred (v prikazu) | 2,30 | 74,6 % | 7,7 % | 2,16 % | 7,82 | −0,89 | 0,54 | **16,0 %** |
| varna_q 0,25 (v senci od 6. 11.) | 2,36 | 74,1 % | 10,6 % | 0,47 % | 7,19 | −1,78 | 0,40 | 8,7 % |
| jedro brez starosti | 2,29 | 74,2 % | 7,6 % | 2,14 % | 7,76 | −0,86 | 0,51 | 14,4 % |
| jedro, razpolovna doba 21 | 2,17 | 76,1 % | 7,2 % | 1,79 % | 7,46 | −0,86 | 0,43 | 10,2 % |
| veriga sama, 21 | 2,20 | 72,1 % | 7,2 % | 2,33 % | 7,76 | −0,67 | 0,36 | 3,0 % |
| **podobni (jedro + veriga), mediana** | **2,16** | 76,2 % | 7,2 % | 1,63 % | 7,30 | −0,84 | 0,38 | **6,1 %** |
| podobni, kvantil 0,25 | 2,29 | 76,4 % | 10,4 % | 0,21 % | 7,04 | −1,86 | 0,28 | 2,4 % |
| **podobni, kvantil 0,30 (varna)** | **2,22** | 77,2 % | 9,6 % | **0,34 %** | **6,96** | −1,66 | 0,29 | **3,1 %** |
| podobni, kvantil 0,35 | 2,18 | 77,6 % | 9,0 % | 0,53 % | 6,93 | −1,47 | 0,31 | 4,1 % |

Kaj je kaj prineslo:

* **Starost je največji vzvod**: MAE 2,29 → 2,17, precenjenih 2,14 → 1,79 %. Razpolovna doba 7 / 14 / 21 / 30 / 45 dni: MAE 2,11 / 2,13 / 2,17 / 2,20 / 2,23. Na poznejših dneh (od 31. 10., 131 926 nalog), kjer prehoda režima ni več tik pred testom: 2,04 / 2,02 / 2,04 / 2,07 / 2,11, precenjenih 2,28 / 1,84 / 1,74 / 1,76 / 1,82 %, strošek 7,72 / 7,37 / 7,29 / 7,32 / 7,37. Sedem dni je premalo (vzorec), 21 ima najnižji strošek. Golo krajše okno sedanjega modela (30 dni) da MAE 2,20, a precenjenih 2,25 % in 13,5 % voženj s skokom.
* **Jedro namesto razreda** samo po sebi malo (2,30 → 2,29), parametri so ploski: predhodnik 1,5 / 3 / 6 dni MAE 2,28 / 2,29 / 2,29, ožje ali širše jedro 2,28 / 2,30.
* **Veriga** kot predhodnik: natančnost ista, precenjenih 1,79 → 1,63 %, vožnje s skokom 10,2 → 6,1 % (pri kvantilu 0,30: 6,3 → 3,1 %). Sama je manj natančna (v 2 min 72 % proti 76 %).
* **Meja ostanka** ostane: brez nje precenjenih 2,75 % namesto 2,14 % pri istem MAE.
* **Čiščenje učne zgodovine** povprečja ne spremeni (surova 2,154 / 1,59 % / 7,27, očiščena 2,158 / 1,63 % / 7,30). Vklopljeno je zaradi primera, ne povprečja: osamelec »V« je sicer »podoben dan« vlaku, ki ima danes res majhno zamudo (preizkus `test_rg318_trije_slabi_dnevi_ne_premaknejo_napovedi`).

Stari režim, kjer menjave vira ni (test 20. 9.–9. 10., 57 637 nalog): razred 2,06 / 1,70 % / 7,42 / 6,1 % voženj s skokom; podobni mediana 2,01 / 1,53 % / 7,23 / 3,1 %; varna_q 0,25 2,19 / 0,41 % / 7,12 / 2,8 %; podobni kvantil 0,35 2,05 / 0,57 % / 6,94 / 1,8 %. Utež starosti v mirnem obdobju ne škodi (jedro brez nje 2,03, z 21 dnevi 2,02).

Z izpuščanjem dneva (stari protokol, isti vzorec od 17. 10.): razred 2,20 / 1,69 % / 7,46 / 11,7 %; varna_q 0,25 2,32 / 0,29 % / 7,12 / 5,7 %; podobni mediana 2,05 / 1,20 % / 7,00 / 4,0 %; podobni kvantil 0,30 2,18 / 0,25 % / 6,95 / 2,5 %. Vrstni red je isti.

### Merilo 2: kar je videl potnik (vrstice sence, ponovitev)

Za vsako vrstico `napoved` na poti (izhodišče `from_seq`, zamuda `current_s`, cilj 25 min naprej) je kandidat izračunan z zgodovino pred tem dnem; resnica je sedanja vrednost v `run`. Preverba ponovitve: razred, izračunan tako, da MAE 3,133 proti zapisanemu `ours_own_s` 3,138; varna_q 0,25 na vrsticah z `varna_s` 2,806 proti zapisanemu 2,827.

| 17. 10.–9. 11., 91 822 vrstic | MAE (min) | v 2 min | podcenj. | precenj. | strošek (min) |
|---|---|---|---|---|---|
| prenos | 4,17 | 56,0 % | 21,8 % | 1,35 % | 9,66 |
| prikaz (`ours_s`) | 3,14 | 67,2 % | 12,5 % | 2,20 % | 8,63 |
| varna_q 0,25 | 3,33 | 65,0 % | 16,4 % | 0,52 % | 8,17 |
| **podobni, mediana** | **3,01** | 68,7 % | 12,1 % | 1,67 % | 8,11 |
| **podobni, kvantil 0,30** | 3,21 | 68,1 % | 15,4 % | **0,38 %** | **7,95** |
| podobni, kvantil 0,35 | 3,13 | 69,0 % | 14,5 % | 0,56 % | 7,87 |

| od 6. 11. (po popravku zajema), 10 697 vrstic | MAE | v 2 min | podcenj. | precenj. | strošek |
|---|---|---|---|---|---|
| prikaz | 2,68 | 69,3 % | 10,0 % | 2,06 % | 7,93 |
| `varna_s`, kot zapisana | 2,83 | 68,0 % | 14,0 % | 0,35 % | 7,51 |
| podobni, mediana | 2,54 | 71,0 % | 9,8 % | 1,65 % | 7,54 |
| **podobni, kvantil 0,30** | 2,69 | 71,5 % | 12,8 % | **0,22 %** | **7,25** |
| podobni, kvantil 0,35 | 2,62 | 72,1 % | 12,1 % | 0,36 % | 7,14 |

Opomba k resnici: pri 20 247 od 91 822 vrstic se sedanja vrednost v `run` razlikuje od `actual_s`, zapisanega ob razrešitvi (popravilo zgodovine 6.–7. 11. in poznejši zapisi zemljevida). Vsi modeli so tu merjeni proti isti resnici, zato so primerljivi med seboj, s številkami `kajros ocena` pa ne naravnost (`2026-11-09-koledar/varna.md` ima za varno 0,8 % precenjenih proti zapisani resnici).

## Sklep

* **Kvantil 0,30 je nova varna**: proti varni, ki čaka na prikaz, ima na obeh merilih manj precenjenih (0,34 proti 0,47 %; 0,38 proti 0,52 %), nižji strošek (6,96 proti 7,19; 7,95 proti 8,17), nižji MAE (2,22 proti 2,36; 3,21 proti 3,33) in tretjino voženj s skokom (3,1 proti 8,7 %). Kvantil 0,35 ima še nižji strošek, a na zgodovini več precenjenih od sedanje varne (0,53 proti 0,47 %), zato ne.
* **Mediana je nova natančna**: MAE 2,16 proti 2,30 in 3,01 proti 3,14, ob manj precenjenih.
* V prikaz gre šele po senci v živo, ker ponovitev ne vidi dveh stvari: zgodovine predhodnikov (`_dnevi_prednikov`, v produkciji jo model ima) in hitrosti.

## Omejitve in odprto

* **Hitrost**: `predict` za najdaljše vlake (30 postankov naprej) 2,3 → 22,5 ms, če se model računa do konca vožnje. Senca ga računa samo do postanka v potnikovem oknu (`podobni_do`). Pred prikazom: tabla in iskalnik rabita samo potnikov postanek, okno vožnje vse; izmeri `/api/train/.../predict` in tablo.
* **Resnica je zemljevid SŽ**, ne prehod vlaka. Model napoveduje, kaj bo SŽ pokazal ob uri prehoda. Tega ne popravi noben model; popravi vir (tabela zamud SŽ, zahteva po ZJI: `KOLEDAR.md`).
* **Menjava voznega reda 13. 12.**: z razpolovno dobo 21 dni se model novemu režimu privadi v 2–3 tednih, a samo, če zgodovina preživi menjavo `trip_id` (vrstica »Zgodovina čez mejo veljavnosti« v koledarju, rok 4. 12.).
* Ni merjeno: avtobusi (model je samo za železnico), sidro prevoznika (`SIDRO_PREVOZNIKA`) skupaj z novim modelom, horizont nad 12 postankov na zgodovini.
* Kvantil in teže (`UTEZ_VERIGE`, `N0_KORAK`) niso uglašeni; izbrane so okrogle vrednosti, ker je okolica ploska.

## Ponovitev

```bash
# kopija (arwen, samo branje), nato:
./venv/bin/python docs/presoja/2026-11-09-napoved/modeli2.py <kopija> --vzorec 6
./venv/bin/python docs/presoja/2026-11-09-napoved/senca2.py <kopija> --modeli 'sedanji,varna_q25,hibrid+ pol=21,hibrid+ q30 pol=21'
# ista koda kot v produkciji, stari protokol (izpuščanje dneva):
KAJROS_DATA_DIR=<mapa> ./venv/bin/python -m kajros.cli backtest --varne --vzorec 12 --modeli 'fizika_razred (sedanji);varna_q 0,25;podobni;podobni varna'
```
