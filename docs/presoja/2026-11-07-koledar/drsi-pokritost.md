# Koledar 7. 11. 2026: varovalo „zamuda raste z uro“ in meje pokritosti

Vrstica: (1) `KAJROS_DRSI` senca → vodi? (2) meje vrstice `pokritost` po prevozniku.
Vir: arwen, samo branje, 1.–7. 11. (7. 11. do ~10.20).

## (1) Ura namesto zamude

**Ponovitev pravila na `obs`** (`collector.ura_namesto_zamude`, prvi napovedani
postanek, brez končne, nagib ≥ 0,8 neprekinjeno 15 min), vsi avtobusi (prej le
`lpp`, `1118`): 89 zadetkov — 1. 11. 27 (praznik), 2. 11. 16, 3. 11. 11,
4. 11. 9, 5. 11. 13, 6. 11. 13, 7. 11. do 10.20 0. Po prevozniku: mestni LPP 73,
LPP primestni 16, medkrajevni (Arriva, Nomago, AP MS), Marprom, Kranj 0.
Skripta: `.claude/skills/preveri-vire/skripte/drsi_teden.py`.

Tabela `lega` (14 dni) za mestni LPP nima točk: 73 od 73 zadetkov brez lege.
Lega iz `dosje.sqlite` (`stanje` + `tocke`) — spodaj.

## (2) Pokritost

`pokritost` na arwenu 31. 10. 19.00 – 7. 11. 10.00: 1 652 vzorcev na 5 min,
11 738 vrstic. Vsak dan luknja 1.00–3.30 (nič ne vozi, vrstic ni). Še 2. 11.
7.16, 99 min brez vzorca (zanka ni pisala).

Delež vzorcev (po voznem redu ≥ 3 vožnje) po razredu razmerja:

| prevoznik | mediana po VR | lega < 0,5 | zamuda 15 min < 0,5 | zamuda danes < 0,5 |
|---|---|---|---|---|
| LPP primestni (1118) | 23 | 41 od 1 391 | 1 od 1 391 | 1 od 1 391 |
| Nomago (1119) | 62 | 1 od 1 498 | 2 od 1 498 | 1 od 1 498 |
| AP MS (1121) | 10 | 5 od 1 251 | 178 od 1 251 | 22 od 1 251 |
| Arriva (1123) | 83 | 1 od 1 469 | 1 od 1 469 | 1 od 1 469 |
| vlaki (1161) | 27 | lege ni (vse < 0,1) | 6 od 1 548 | 0 od 1 548 |
| Kranj | 4 | 191 od 963 | 197 od 963 | 197 od 963 |
| mestni LPP | 51 | 5 od 1 502 | 5 od 1 502 | 5 od 1 502 |
| Marprom | 15 | 66 od 1 277 | 75 od 1 277 | 75 od 1 277 |

Epizode ≥ 20 min pod polovico izhodišča (izhodišče = mediana razmerja
prevoznika v tednu):

* LPP primestni, lega: 2. 11. 9.26–11.42 (136 min) 0 vozil z lego, zamude
  ves čas 20–26 od 20–29 — **pravi izpad leg**, edina taka epizoda.
* Kranj: 1. 11. (praznik) 8.12–19.30, 3–6 voženj po voznem redu, 0 z lego in
  zamudo — **praznik, ne izpad** (zip MOK praznika ne pozna, isto 31. 10.,
  `docs/MERITVE.md`). Od 2. 11. naprej nobene epizode.
* Marprom: 1. 11. 6.18 (31 min, ≤ 10 voženj) in 11.19 (20 min, ≤ 7), 5. 11.
  15.41 (21 min, najmanj 0,32 od ≤ 20).
* AP MS, zamuda v 15 min: 8 epizod (1. 11. in 7. 11. zjutraj), zamuda danes
  le ena (1. 11. 19.40, 27 min, 0,38): zamuda v 15 min za medkrajevne podceni.

## Izid (iz poročila agenta, 7. 11. 2026)

(1) Senca ostane: ponovitev 1.–7. 11. dala 89 zadetkov (mestni LPP 73, LPP primestni 16), od tega 8 fantomov (vozilo 0 m med drsenjem in še 60 min po njem) in najmanj 35 resnic (14 primestnih v konici 15.10–15.50 AP Ljubljana → Tivoli, vozilo se premika 300–2 300 m; 11 mestnih vozi; 10 stalo, nato vozilo s to zamudo); 36 brez lege. Vklop vodi bi pobrisal resnico. (2) Meje izmerjene, vrstica v zdravje.py še ni napisana: ≥ 5 voženj po voznem redu, razmerje pod polovico izhodišča prevoznika, rumeno od 10 min, oranžno od 20 min. Na tednu 4 oranžne, od tega 2 na delavnik in obe pravi (lege LPP primestni 2. 11., 136 min; Marprom 5. 11., 21 min); drugi 2 sta bili na praznik 1. 11. Commita ni.

docs/VIRI-PRESOJA.md, točka 1 (ura namesto zamude), 7. 11.: ponovitev pravila na obs za vse avtobuse 1.–7. 11.: 89 zadetkov (1. 11. 27, 2. 11. 16, 3. 11. 11, 4. 11. 9, 5. 11. 13, 6. 11. 13, 7. 11. do 10.20 0). Mestni LPP 73, LPP primestni 16, ostali 0. Vozilo iz dosje.sqlite (stanje po vožnji, mestni LPP brez dneva), premik iz tock. LPP primestni: 14 vozi med drsenjem (konica 15.10–15.50, AP Ljubljana → Tivoli/Bavarski dvor, 300–2 300 m, nato 13–36 postankov z isto zamudo), 1 stal in nato vozil, 1 fantom (25 Medvode 6. 11. ob 5.43). Mestni LPP: 11 vozi, 9 stal in nato vozil, 7 fantomov (vozilo 0 m), 10 brez lege, nato postanki v obs, 36 brez lege brez česarkoli (25× linija 9 na praznik 1. 11., postanek 22). Fantomi: vsi na postanku ≤ 3, zamuda ob začetku 31–54 min, run konča pri +71–76. Zasloni LPP kažejo isto, 58–59 min. Linija SŽ (Kolodvor) 3× z začetno zamudo −26 do −42 min, tj. čaka uro odhoda. Odločitev: senca ostane, ker bi vodi pobrisal ≥ 35 resnic za 8 fantomov. Ob 15 min drsenja se fantom in pozen odhod ne ločita (oba 0 m); loči ju šele premik v naslednjih 30–60 min. Predlog: popravek za nazaj po premiku vozila (1.–6. 11.: 8 fantomov, 0 resnic).

docs/VIRI-PRESOJA.md, točka 3 (pokritost), 7. 11.: tabela pokritost na arwenu 31. 10. 19.00 – 7. 11. 10.00, 1 652 vzorcev, 11 738 vrstic. Vsak dan med 1.00 in 3.30 ni vrstic (nič ne vozi). 2. 11. od 7.16 99 min ni bilo nobenega vzorca (zanka ni pisala). Lega vlakov je vedno 0, zato vlaki samo zamuda v 15 min. Pri AP MS zamuda v 15 min pod 0,5 v 178 od 1 251 vzorcev, zamuda danes v 22: za medkrajevne velja zamuda danes. Izhodišča (mediana tedna, lega/zamuda): LPP primestni 0,84/0,89, Nomago 0,94/0,94, AP MS 0,88/0,84, Arriva 0,96/0,94, SŽ 0,94, Kranj 0,67, mestni LPP 0,97, Marprom 0,90. Pravilo: ≥ 5 voženj po voznem redu, pod polovico izhodišča, rumeno od 10 min, oranžno od 20 min. Na tednu rumena 10 (8 na praznik 1. 11.), oranžna 4: LPP primestni 2. 11. od 9.26, 136 min 0 z lego pri 20–29 vožnjah z zamudo (pravi izpad leg); Marprom 5. 11. od 15.41, 21 min, 6–7 od 17–20 (pravi); Marprom 1. 11. od 6.18, 41 min, in AP MS 1. 11. od 19.40, 27 min (praznik, nepreverjeno). Pri N = 3 bi bilo oranžnih 6 (Kranj ves praznik 1. 11. 8.12–19.30), pri N = 8 3.

Skripte: `drsi/drsi_teden.py`, `drsi/drsi_lega.py`, `drsi/meje.py`, tabela `drsi/pokritost.csv`.
