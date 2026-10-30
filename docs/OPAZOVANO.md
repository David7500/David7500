# Opazovano: sistem za vse avtobuse

Stanje 30. 10. 2026: načrt, nič od tega ni narejeno. Meritve: `docs/MERITVE.md`, „Marprom: obvoz G2“.

## Zakaj

David, 30. 10. 2026: „Hočem, da je nek sistem, ki potem dela pri vseh avtobusih. Ne da popraviva neko napakico, in potem spet, in potem to vpliva na druge buse.“

Isti vzorec se je ponovil pri več prevoznikih: LPP 18 po obvozu, 27 po Vilharjevi, Brnik letališče, zdaj G2 v Mariboru. Vsakič je bil vzrok isti: objavljeni podatki povedo, kaj naj bi vozilo delalo, ne kaj dela. Odgovor je bil vsakič svoj, po viru. LPP ima `zive.py`, RT `ne_ustavi` in zaslone, Marprom in NAP nimajo ničesar.

## Pravilo

**Vsak vir samo pove, kje so vozila. Kaj to pomeni, izračuna ena koda za vse. Prikaz bere samo njen rezultat.**

Noben popravek ne sme imeti pogoja po prevozniku, razen na vhodu vira. Popravek, ki bi ga rabil pogoj, je znak, da manjka splošno pravilo.

## Štirje deli

### 1. Straža in izhodiščna meritev (najprej)

Dnevna vrstica po prevozniku, ki se ne obrezuje:

* delež vozil z vožnjo, tudi za vozila brez nje (danes hranimo le trenutno stanje, zato preteklih ni mogoče prešteti);
* delež voženj voznega reda z lego;
* delež postankov s prehodom;
* trase s premalo točkami ali do postajališča dlje kot 200 m;
* vozni red po dnevih v tednu: prvi delavnik, sobota in nedelja brez voženj, po vsakem viru. `do` danes kaže zadnji datum katerekoli storitve: pri Marpromu 20. 6. 2027, delavnikov pa ni od 1. 1. 2027.

Odgovor na „to vpliva na druge buse“: vsaka sprememba zajema se ponovi na istih posnetih dneh (`lega`, način `ponovi_dan.py`) in primerja s to vrstico za vse prevoznike. Sprememba, ki enega izboljša in drugega poslabša, je vidna pred objavo. Pri Marpromu je izhodišče že znano: 1 012 in 1 026 od 1 136 voženj z lego (28. in 29. 10.).

### 2. Tabela opazovanega

Nočni izračun iz `lega` in `gps_prehod` po (`shape_id`, `stop_id`): voženj, prehodov, kako blizu je prišlo vozilo, od kdaj. Stanje: `vozi` ali `ne_ustavi`, z dokazi in datumom. Stanje se samo zapre, ko vozila spet pridejo mimo, zato obvoz po koncu zapore ne rabi posega.

Izmerjeno 28.–29. 10. 2026, pari z vsaj 10 vožnjami:

| prevoznik | parov | 0 prehodov | pod 30 % | nad 70 % |
|---|---:|---:|---:|---:|
| 1119 | 3 465 | 33 | 45 | 3 330 |
| 1123 | 4 375 | 34 | 14 | 4 303 |
| 1121 | 652 | 1 | 0 | 650 |
| kranj | 197 | 0 | 0 | 193 |
| marprom | 892 | 3 | 4 | 873 |

Skupaj 71 od 9 581 parov brez prehoda (0,7 %).

**Ni še dokazano, da 0 prehodov pomeni „ne ustavi“.** Pravi primer je Ljubljanska – Focheva (104 + 102, potrjeno v časopisu). Ormož bolnica (40), Naklo (32) in Postojna SŠC (17) so morda odmik postajališča, kjer vozilo vozi mimo in ga prehod ne zazna. Zato najprej senca: razlika med „vozilo je prišlo blizu“ in „ni ga bilo“, ročno preverjeni primeri, šele nato prag. Prehodi na zaporo Meljske (G3, 29. 10.: 5 od 37) so dober preizkus za občasen obvoz, zapora Vrbanske 3.–26. 11. (P7) pa za začetek in konec v živo.

**Mestni LPP v `gps_prehod` ni** (1118: samo 30 parov pod pragom). Zanj ostaja RT in zasloni; v tabelo se zapiše kot drug vir dokaza, da prikaz bere eno mesto.

### 3. En prikaz

* Tabla, zveze, pristajalne strani: `api._oznaci_obvoze` že nastavi `ne_ustavi` za LPP. Tabela iz 2. dela je dodaten vir, brez nove veje v prikazu.
* Zemljevid: črta, kjer vozila res vozijo, iz `lega` na obvozu; objavljena ostane vidna kot „po voznem redu“. Vozilo ne sme biti videti, kot da je zašlo.
* Besedilo: dokler je dokaz samo iz leg, „zadnje dni tu ni ustavljal“, ne trditev, da je zaprto.

### 4. Pripis vozila na vožnjo

Skupna funkcija namesto logike po viru, in samo z dokazom: napačen par je zamuda druge vožnje (`zive.py`). Prvi primer je Marprom: mrtvo vozilo (`Predicted: 1`) zasede prihod linije, živo za njim vožnje ne dobi (34 od 45 v 7-minutnem vzorcu). Kandidat: najbližja prosta vožnja iste variante na naslednjem postajališču. Preverba v senci: pri vozilih, kjer pripis poznamo, mora dati isto vožnjo.

## Vrstni red

1. Del 1, brez spremembe prikaza. Brez tega drugih korakov ni mogoče primerjati.
2. Del 2 v senci, nekaj dni, ročna preverba vseh 71 parov.
3. Priklop na `ne_ustavi`, nato črta na zemljevidu.
4. Del 4.

Vsak korak v svojem commitu, s številkami pred in po, za vse prevoznike.

## Kdo kaj (30. 10. 2026)

| seja | delo | zapis |
|---|---|---|
| sztrack-77 | prikaz na namizju. Ne moti je. | CSS, predloge, `common.js`, `dashboard.js`, `train.js` |
| sztrack-06 [03308a] | trase: odrezane in krožne, ponovno pripenjanje | `pripni.py`, `geo.py` (`3c2a25e`) |
| sztrack-06 [a4652c] | zadnja zamuda na končni, vzorčenje v živo | `collector.py`, `api.py`, `test_koncana_voznja.py` |
| sztrack-b1 | del 1, straža po prevoznikih | svoj worktree, nov modul |
| sztrack-c0 | del 2, samo meritev 71 parov | svoj worktree, brez `kajros/` |
| sztrack-3d | rezerva, del 4 šele po delu 1 | |
| sztrack-7b | usklajevanje, vključitev | ta dokument |

Pravila za vse: objavlja samo David ali seja z njegovim izrecnim „objavi“. Nova dela v worktreeju, ne v skupni kopiji. Pri 90 % 5h okna predaja in stop, ostanek je za prikaz. Brez subagentov.

## Kaj ni del tega

* Trase krožnih in odrezanih: popravljeno v 3c2a25e (druga seja), velja po uvozu in ponovnem pripenjanju.
* Delavniki Marproma 2027: rabi nov zip. Del 1 mora rok pokazati, pisanje Marpromu je Davidova odločitev.
* Pozor pri `api.py`, `collector.py`, `dashboard.js`: 30. 10. jih ureja druga seja. Delo v worktreeju (spomin `socasne-seje`).
