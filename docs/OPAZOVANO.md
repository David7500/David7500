# Opazovano: sistem za vse avtobuse

Stanje 31. 10. 2026: del 1 (straža) teče na arwenu. Del 2 predelan na izide po vožnjah, del 3 (prikaz in črta na zemljevidu) narejen, oboje za stikalom `KAJROS_OPAZOVANO_PRIKAZ`. Del 4 izmerjen v senci, ni priklopljen. Meritve: `docs/MERITVE.md`, „Marprom: obvoz G2“ in naprej, zadnje „Opazovano, del 3“.


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

**Narejeno** (`kajros/straza.py`, `tests/test_straza.py`, ukaz `kajros straza`): tabele `straza_dan` (po prevozniku, ne obrezuje se), `straza_opazeno` (vozilo + vožnja, 14 dni), `straza_stevec`; vir pove samo `straza.vzorec(vir, vozilo, trip_id)` na vhodu (derp, lpp, nap, kranj, marprom); nočni `straza.dopolni` v `server._povzetki`. `kajros straza --baza A --proti-baza B --dan D` primerja dve bazi in izpiše, koga je sprememba poslabšala. Pri `trip.agency` je prevoznik po viru (`lpp`, `marprom`, `kranj`, IJPP id-ji); `1161` = vlaki SŽ.

**Izhodišče**, arwen, 29. 10. 2026 (celoten dan, branje `mode=ro`, 5 s za dan, 23 s za vozni red in trase):

| prevoznik | vožnje (načrt) | z lego | z meritvijo | postankov s prehodom | rep na končni nad 2 min, 20.–30. 10. | slabe trase / tras | delavnik do | sobota do | nedelja do |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| 1118 | 1 608 | 612 (38,1 %) | 1 038 | 0 % | 32 / 9 185 | 15 / 252 | 31. 12. 2027 | 25. 12. 2027 | 26. 12. 2027 |
| 1119 | 3 990 | 3 838 (96,2 %) | 3 791 | 88,7 % | 0 / 28 606 | 28 / 1 345 | 31. 12. 2027 | 25. 12. 2027 | 26. 12. 2027 |
| 1121 | 720 | 709 (98,5 %) | 656 | 87,3 % | 0 / 4 497 | 6 / 195 | 31. 12. 2027 | 25. 12. 2027 | 26. 12. 2027 |
| 1123 | 4 091 | 3 993 (97,6 %) | 3 953 | 91,2 % | 4 / 32 536 | 40 / 1 120 | 31. 12. 2027 | 25. 12. 2027 | 26. 12. 2027 |
| 1161 (SŽ) | 616 | – | 568 | 0 % | 272 / 4 903 | 3 / 279 | 11. 12. 2026 | 12. 12. 2026 | 6. 12. 2026 |
| kranj | 159 | 154 | 153 | 91,9 % | 0 / 316 | 1 / 54 | 30. 11. 2026 | 28. 11. 2026 | ni |
| lpp (mestni) | 2 227 | – | 2 152 | 0 % | 105 / 3 347 (le 29.–30.) | 0 / 111, 56 voženj brez trase | 6. 11. 2026 | 7. 11. 2026 | 1. 11. 2026 |
| marprom | 1 136 | 1 026 (90,3 %) | 1 006 | 84,1 % | 0 / 1 715 | 6 / 145 | **31. 12. 2026** | 19. 6. 2027 | 20. 6. 2027 |

„–“ = ne vemo (vira za nazaj leg ni hranil; `straza_opazeno` šteje od prvega zagona), ne 0 %. `prehod` je 0 % tam, kjer `gps_prehod` ne nastaja (mestni LPP, 1118, SŽ). Marprom po vrsti dne pokaže, česar `do` ne: delavnikov od 1. 1. 2027 ni, sobote in nedelje so do junija. Marprom z lego 28. 10. 1 012, 29. 10. 1 026 od 1 136 (kot prej). Merilo `rep na končni` je iz `obs` (surov feed, ne popravljen `run`): 1118 32 od 9 185 in Arriva (1123) 4 od 32 536 sta enaka prejšnji meritvi (31/8 936 in 4/31 633; drugi interval); mestni LPP 105 od 3 347, od tega linija 9 90 od 202 (`ed39350`: 76 od 85 samo smer Barje, ostalo 13 od 2 689). **Novo: SŽ 272 od 4 903 (5,5 %)**: pri vlakih rep doslej ni bil merjen; ni preverjeno, ali je ura ali vlak res stoji pred postajo.

Trase: oblika `shape.points`/`osm` je seznam kosov `[[[lat,lon],...]]` pri vseh 3 505 trasah; slabe = manj kot 2 različni točki ali postajališče dlje od 200 m od črte.

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

**Narejeno v senci** (`kajros/opazovano.py`, `tests/test_opazovano.py`, ukaz `kajros opazovano [--vsa] [--racunaj] [--baza POT]`): tabeli `opazovano` (ključ prevoznik, `train_no`, `headsign`, `stop_id`; niz dokazov ene vrstice) in `opazovano_dan` (meja, dan se obdela enkrat, v istem commitu); nočni `opazovano.dopolni` v `server._povzetki` pred stražo, svoj poskus; `kajros straza` po prevozniku pokaže odprte, nove in zaprte. Pravilo in meritve: `docs/MERITVE.md`, „Opazovano, del 2: tabela v senci“.

**Predelano 31. 10. 2026** (`docs/MERITVE.md`, „Opazovano, del 3“). Niz, ki ga en prehod pretrga, je 22 od 131 ključev odpiral znova: vožnje iste linije se obnašajo različno. Zdaj: izid vsake vožnje v `opazovano_izid` (21 dni), stanje iz okna v `opazovano.presodi`: `ne_ustavi` (po potrebi samo za nekatere vožnje), `redko` ali nič. Na istih 13 dneh 0 ključev z več epizodami.

**Za prikaz** (`opazovano.dovolj_za_prikaz`): odprta vrstica, ki je `pravi` (OSM isto ime v 60 m ali druge linije na istem `stop_id`, ob poti vozila ni istega imena) ali `neznan` z `osm_blizu` (OSM postajališče brez imena v 60 m). 74 od 112 odprtih. Napačen in dvoumen ne, dokler potnik ne dobi napotka, kje vozilo ustavi.

### 3. En prikaz

* Tabla, zveze, pristajalne strani: `api._oznaci_obvoze` že nastavi `ne_ustavi` za LPP. Tabela iz 2. dela je dodaten vir, brez nove veje v prikazu.
* Zemljevid: črta, kjer vozila res vozijo, iz `lega` na obvozu; objavljena ostane vidna kot „po voznem redu“. Vozilo ne sme biti videti, kot da je zašlo.
* Besedilo: dokler je dokaz samo iz leg, „zadnje dni tu ni ustavljal“, ne trditev, da je zaprto.

**Narejeno 31. 10. 2026.** Prikaz bere samo `opazovano.za_prikaz` (ali `ne_ustavi`, `za_voznjo`):

| kje | `ne_ustavi` | `redko` |
|---|---|---|
| tabla (`api._oznaci_obvoze`) | prečrtano, „zadnje dni tu ni ustavljal“, ni naslednja | odhod ostane, opomba „zadnje dni tu redko ustavlja“ |
| zveze (`alerts.oznaci_zveze`) | isto, „na cilju“ pri izstopu | opomba |
| prestopi (`alerts.brez_zaprtih_prestopov`), pot (`alerts.ne_ustavi_vsi`) | tu ne vstopi in ne izstopi | ostane |
| pristajalni strani | ni v tabeli, stavek nad njo | stavek nad njo |
| okno vožnje | opomba pri postanku in na kartici, razdalja | opomba, „2 od 77 voženj“ |
| `/api/trip/{id}/shape`, oba zemljevida | pot vozil v `points`, objavljeno v `po_voznem_redu` (črtkano, napis), postajališče rumeno | nič |
| drug dan (jutri) | samo beseda | samo beseda |

Prvi današnji prehod `ne_ustavi` takoj omili v `redko` (preverja se na minuto). Če nočni račun stoji, trditve po 7 dneh odpadejo same; v zdravju rumeno po 2 dneh (`opazovano`).

### 4. Pripis vozila na vožnjo

Skupna funkcija namesto logike po viru, in samo z dokazom: napačen par je zamuda druge vožnje (`zive.py`). Prvi primer je Marprom: mrtvo vozilo (`Predicted: 1`) zasede prihod linije, živo za njim vožnje ne dobi (34 od 45 v 7-minutnem vzorcu). Kandidat: najbližja prosta vožnja iste variante na naslednjem postajališču. Preverba v senci: pri vozilih, kjer pripis poznamo, mora dati isto vožnjo.

**Narejeno, samo v senci** (`kajros/pripis.py`, `tests/test_pripis.py`, `scripts/pripis_senca.py`): vir da varianto ali linijo, naslednje postajališče in čas. Par je samo, če vozilo na varianti napreduje (`Napredek`) in je v oknu −4 … +10 min ena prosta vožnja, v −4 … +30 min pa nobena druga. V `run` ne piše, noben vir je ne kliče. Meritve: `docs/MERITVE.md`, „Pripis vozila na vožnjo: senca“.

| prevoznik | vzorcev | pravih | napačnih | napačnih od predlogov | skritih 25 % drugih vozil |
|---|---:|---:|---:|---:|---:|
| marprom, prihodi, 30. 10. 15:41–19:41, skrito | 7 621 + 36 spornih | 7 621 | 0 (36, če sporne štejemo za napačne) | 0 % (0,47 %) | – |
| marprom, vozila brez vožnje, potrjeno | 162 | 162 | 0 | 0 % (95-odstotna meja ~1,8 %) | – |
| marprom, `lega` 29. 10. | 13 566 | 10 372 | 3 | 0,03 % | 0,01 % |
| kranj, `lega` 29. 10. | 2 193 | 1 749 | 3 | 0,17 % | 0,62 % |
| 1119 (Nomago), `lega` 29. 10. | 106 026 | 58 504 | 24 | 0,04 % | 0,21 % |
| 1121 (AP MS), `lega` 29. 10. | 17 646 | 9 128 | 1 | 0,01 % | 0,02 % |
| 1123 (Arriva), `lega` 29. 10. | 115 092 | 61 670 | 0 | 0 % | 0,15 % |
| 1118 (primestni LPP) | 892 | ni meritve | – | `gps_prehod` ne nastaja, brez vrat napreduje 3–7 % | – |

Par bi danes rabil samo Marprom: NAP vožnjo pove vedno (`brez_voznje` 0), Kranj ima 1 vozilo od 5 brez vožnje in ne pove variante. Noben pogoj po prevozniku: kdor varianto ima in vožnje nima, kliče isto funkcijo.

## Vrstni red

1. Del 1, brez spremembe prikaza. Brez tega drugih korakov ni mogoče primerjati.
2. Del 2 v senci, nekaj dni, ročna preverba vseh 71 parov.
3. Priklop na `ne_ustavi`, nato črta na zemljevidu.
4. Del 4.

Vsak korak v svojem commitu, s številkami pred in po, za vse prevoznike.

## Odprto

* Pripis: priklop samo za Marprom, najprej brez zamude, po ponovitvi meritve na jutranji konici in ob koncu tedna (vzorec je en petek popoldne).
* `marprom.razresi` je 3 vozilom v 4 h dal vožnjo 31–90 min naprej, obvisi do `PREVERI_S`. Vzrok ni dokazan.
* Vrbanska od 3. 11. (P7): prvi preizkus v živo, po zasnovi vidno 5. 11. ob 3.30. Preveri, ali se odpre, in kako hitro se zapre 26. 11.
* Krak „po potrebi“ (Artiče, Medribnik, Zavrh): iz leg ni mogoče vedeti, ali vozilo pride, če kdo čaka. Besedilo tega ne trdi; če potnik sporoči drugače, je to dokaz, da pravilo tu ne velja.
* Začetek zapore se pozna z dnevom zamude, ker je račun nočni. Računati sproti bi skrajšalo zamudo za največ dan.
* Posnetek OSM (`scripts/osm_postajalisca.py`) se ne osvežuje sam.

## Kaj ni del tega

* Trase krožnih in odrezanih: popravljeno v 3c2a25e (druga seja), velja po uvozu in ponovnem pripenjanju.
* Delavniki Marproma 2027: rabi nov zip. Del 1 mora rok pokazati, pisanje Marpromu je Davidova odločitev.
