# Veriga vozila: ponovitev 7. 11. 2026 (vrstica koledarja „Veriga“)

Skripta `veriga_lpp.py` (razdelek 2 iz 2026-10-31-veriga.md, `straza_opazeno`,
arwen samo branje, 30. 10.–6. 11., pari po `_block_neighbour`).

## 1. Drugo vozilo v paru (vozilo = največ vzorcev, vir derp / lpp)

| skupina | pari | oba z vozilom | drugo vozilo |
|---|---|---|---|
| LPP 25 (derp) | 360 | 307 | 12 (4 %) |
| LPP 25 zvečer (od 18.00) | 102 | 95 | 4 (4 %) |
| LPP primestni (derp) | 3 838 | 3 231 | 151 (5 %); zvečer 861 → 10 (1 %); dan 2 370 → 141 (6 %) |
| LPP mestni (lpp) | 152 | 148 | 0 (0 %); zvečer 11 → 0 |

* Prej (30.–31. 10.): LPP 25 22 parov 0, primestni 243 → 1 %, mestni 64 → 0.
* Pokritost LPP 25 z vozilom: prvi dan 15 od 50 parov (30. 10.), od 31. 10. 30 od 30,
  2.–6. 11. 40–50 od 50 (prej tretjina).
* Mestni LPP: v `trip` so samo 6.–8. 11. (uvoz zamenja vožnje, pretekli dnevi
  izginejo), torej n = 148 je en dan (6. 11.), ne teden.

## 2. Medkrajevni: `veriga/v8.py` na 1.–6. 11. 2026 (po objavi popravka 31. 10.)

Isti postopek kot v `docs/MERITVE.md` (pari blokov z legami NAP, ob 10/5/1 min
pred odhodom), arwen samo branje, 25 s. To je ponovitev pravila na zgodovini
leg, ne dnevnik trditev, ki jih je prikaz res pokazal (takega dnevnika ni).

Pet minut pred odhodom, „novo R=200“: prikazano / prav
* Nomago: 12 037 parov, kaže 35,3 %, prav **99,1 %** (ujame 95,2 %); napak 37
  (drugo vozilo 27, prejšnja že na cilju 10).
* Arriva: 15 165 parov, kaže 34,9 %, prav **99,1 %** (ujame 96,3 %); napak 46 (26 + 20).
* AP MS: 1 477 parov, kaže 38,1 %, prav **98,0 %** (ujame 95,5 %); napak 11 (5 + 6),
  od ~563 prikazov, SE ~0,6 %.
* Skupaj: 94 napak od ~10 100 prikazov = 99,07 %.
* Glava prej pri T-5: 36,8 / 35,9 / 39,1 %. Pilula prej: 90,7 / 89,9 / 90,0 %.
* T-1 min pri 200 m: Nomago 98,6 %, Arriva 98,8 %, AP MS 96,2 % (n ~ 17 napak).
* Vozilo, ki je prejšnjo končalo in stoji do 200 m od izhodišča te: isto vozilo
  95,0 % (Nomago T-10, 141), 97,7 % (T-5, 263), 100 % (Arriva T-5, 449).
* Cilj >= 98,8 % pri T-5: Nomago in Arriva da, **AP MS 98,0 % (en dan manj
  vzorca, 11 napak)** -- v šumu (17.–30. 10.: 98,8 %), ni znak okvare.

## 3. LPP: ponovitev pravila na legah iz `dosje.sqlite` (nova možnost, 7. 11.)

Koledar je trdil, da za LPP zgodovine leg ni. Od 1. 11. 13.42 je v `dosje.sqlite`
(`tocke`: vsak vzorec vsakega vozila, vir derp/lpp). Skripta
`veriga_lpp_dosje.py` (2.–6. 11., delavniki, arwen samo branje):
pravilo ob T-10/5/1 min — lega vozila prejšnje sveža ≤ 180 s, ta vožnja brez
lastne lege (`stanje`), vozilo > 200 m od končne prejšnje, v feedu prihod na
končno še ni zapisan (`run`). Resnica: prejšnja še vozi (vozilo pride ≤ 100 m
od končne po polovici vožnje šele po t) in to vožnjo vozi isto vozilo (straza).
**Omejitev**: „še vozi“ se meri iz iste lege, zato je neodvisen samo preizkus
vozila; napake „že na cilju“ so podcenjene.

Pet minut pred odhodom, kaže / prav:

| skupina | parov | kaže | prav | napak (drugo vozilo + že na cilju) |
|---|---|---|---|---|
| LPP primestni (1118) | 2 903 | 731 (25 %) | **90,4 %** | 66 + 4 |
| LPP 25 | 232 | 45 (19 %) | **95,6 %** | 1 + 1 (n majhen) |
| LPP mestni (6. 11. samo) | 148 | 146 (99 %) | 100 % | 0 |

* Brez pogoja o zapisanem prihodu v feedu: primestni 83,1 % (992 prikazov, 92 že
  na cilju), 1 min pred odhodom 68,2 % (588 prikazov, 118 že na cilju). Pogoj
  „prihod v feedu še ni zapisan“ je za LPP bistven, bližina končne sama ne zadošča
  (vozilo po prihodu odpelje proti začetku te vožnje, > 200 m).
* Primestni, T-5, ob zapisanem pogoju: **dan 89,2 % (603 prikazov), zvečer 96,1 %
  (128)**. Cilj iz medkrajevnih (≥ 98,8 %) **ni dosežen**.
* Vzrok: drugo vozilo. Po liniji (`veriga_lpp_linije.py`, 1118, 2.–6. 11.):
  **47: 27 od 104 parov z obema voziloma (26 %)**, 51: 12 od 90 (13 %), 49: 5 od 43
  (12 %), 3B: 23 od 206 (11 %), 60: 7/93 (8 %), 3G: 13/193 (7 %), **25: 11/232 (5 %)**,
  19I 7/183 (4 %), 12D 5/141 (4 %). Razmik konec prejšnje → začetek te pri teh napakah:
  mediana 6 min, p90 20 min.
* Davidov primer: LPP 25 zvečer 4 od 95 parov z drugim vozilom (4 %, n z 31. 10.:
  0 od 15), torej ni nič pogostejši kot na drugih linijah; zvečer so primestni
  1 % (10 od 861).

## 4. Zaključek, odločitev

* Medkrajevni: popravek drži, 99,1 % (Nomago, Arriva) in 98,0 % (AP MS, v šumu).
* LPP mestni: drži (0 drugih vozil, n = 148, en dan).
* LPP primestni: trditev prava pri 90 % (dan 89 %, zvečer 96 %); veriga je
  derp-ova sintetična (`SYN_`), na posameznih linijah (47, 51, 49, 3B) se vozilo
  menja pogosteje. Koda **nespremenjena**; predlog: varovalo po liniji, ki ga
  odločimo čez teden (rok v izidu), ker je pri 5 delavnikih n po liniji 40–100.
