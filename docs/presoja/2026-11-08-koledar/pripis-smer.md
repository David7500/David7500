# Pripis NAP: vrata smeri (koledar 8. 11. 2026)

Vrstica koledarja: 1.–7. 11. 807 parov, 45 napačnih (5,6 %), 35 od 40 izpisanih vozi proti
naši vožnji (`2026-11-07-koledar/kratke.md`, točka B). Naloga: vrata smeri v `pripis.py` in
oceno, ponovitev na 1.–8. 11., preostale napake še z drugim merilom; cilj 0 napačnih pri
≥ 30 parih z ≥ 10 vozil.

## Koda

* `pripis.naprej(zgodovina, zdaj, kraj)`: par samo po vožnji, po kateri se je vozilo premaknilo
  naprej. Kraj (voznoredni čas na tetivi, `na_voznji`) se mora od najstarejšega opazovanja
  2–5 min nazaj (`SMER_NAJMANJ_S`, `SMER_S`) premakniti za vsaj 0,3 pretečenega časa
  (`SMER_DELEZ`). Brez opazovanja v tem oknu dokaza ni.
* `pripis.predlagaj(..., naprej=...)`: edina prosta v oknu, ki ne gre naprej, da `smer`.
  Tekmice ostanejo vse, vrata par le odvzamejo.
* `nap.Senca` hrani kraj po kandidatki za zadnjih 5 min (prej samo prejšnji račun za
  `NAZAJ_S`); števec `smer` v `meta.nap.senca` in v `/admin` („ne naprej“).

Zakaj `NAZAJ_S` (30 s na račun) ni zadoščal: nova kandidatka nima prejšnjega računa, napredek pa
je že potrjen z druge vožnje iste variante; pri počasnem padanju kraja (vozilo se obrne) je
padec na minuto pod 30 s.

## Ponovitev 1.–8. 11. (do 13.44)

`pripis_odlocitev.py 2026-11-01..2026-11-08 --baza <kopija arwena> [--smer --koda <nova koda>]`,
kopija `VACUUM INTO` z 8. 11. ob 13.44, 1 008 584 vrstic, 1 185 vozil. Vrata smeri v oceni
ponovijo senco: kraj iz leg istega vozila v zadnjih 5 min, samo kjer bi bila vožnja v oknu sence.

| | parov skozi vrata | vozil | napačnih | meja (< 3 vrstice) | nepotrjenih |
|---|---|---|---|---|---|
| vrata premika (doslej) | 837 | 379 | 47 (5,6 %) | 66 | 11 |
| + vrata smeri | 418 | 223 | **10 (2,4 %)** | 25 | 7 |
| + brez zadnjih 3 min vožnje (poskus) | 105 | 62 | 4 | 13 | 7 |
| + brez zadnjih 5 min | 84 | 54 | 3 | 8 | 5 |
| + brez zadnjih 10 min | 67 | 44 | 3 | 2 | 7 |

Cilj 0 ne drži. Vrata smeri vzamejo 37 od 47 napačnih in polovico parov.

**Drugo merilo** (`pot`, neodvisno od leg pred parom): 15 min po prvi vrstici skozi vrata mora
vozilo ostati na naši vožnji z zamudo v 5 min od prve, kraj ne sme pasti za več kot 2 min.
Z vrati smeri: 22 parov „napačnih po poti“ (10 od njih napačnih tudi po oznaki), 58 „po poti“,
338 premalo leg (vozilo zapusti senco, ker ga NAP pripne).

## Kaj ostane

* **Konec vožnje.** 313 od 418 parov skozi vrata ima vse vrstice skozi vrata v zadnjih 3 min
  vožnje: vozilo pripelje na končno, NAP pa že javlja naslednjo vožnjo (`prezgodaj`,
  `brez_dneva`). Šest preostalih „vozi nazaj“ (1300272 na Maribor AP dvakrat, 1300859 dvakrat,
  1302100, 1301638) je vseh na koncu vožnje: brez zadnjih 3 min jih ostane eden, brez zadnjih
  5 min nobeden. Vozilo pripelje, nato se obrne. Drugo merilo na Maribor AP (46,560 N 15,656 E) zaznamuje tudi pare, ki jih je
  NAP sam imel na tej vožnji (1300233, 1301591, 1301638, 1300234 na 462929–462937): kraj ob
  vožnji po postaji pade, tetiva tam ne loči obrata od manevra.
* **Drugo vozilo na vožnji** (4 pari: 1302076 na 487352 dvakrat, 1301450 na 390471, 1300594
  na 445359): drugo vozilo ima v `lega` isto vožnjo, senca pa ga ni imela med zasedenimi. Brez
  zadnjih 5 min ostanejo prvi trije (to so tedaj vsi napačni po oznaki). derp.si je imel 1302076
  enkrat na 487382.
* „Zapusti vožnjo“ pri dolgih parih (1300841, 1301219: 30+ vrstic, 32–67 km) je tudi lahko
  vožnja čez rob tetive; ni pregledano.

## Odločitev

Ne priklopi. Vrata smeri gredo v senco (merjenje v živo od objave), pravila za konec vožnje ne
dodajam: zadnjih 5 min odstrani tri četrtine parov, preostale napake pa niso samo tam. Naslednji
korak: surova sled teh 13 parov (Maribor AP, drugo vozilo), nato odločitev o koncu vožnje in o
zasedenih iz vseh virov (koledar).
