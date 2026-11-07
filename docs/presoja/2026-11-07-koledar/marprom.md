# Marprom po popravku fc2bde6 (koledar 7. 11. 2026)

Okni: pred = pon 2. in tor 3. 11. (2 delavnika), po = čet 5. in pet 6. 11. (2 delavnika). Popravek objavljen sre 4. 11. 21.50. Vir: dosje `stanje` na arwenu, samo branje. Skripti `.claude/skills/preveri-vire/skripte/marprom_izpadi.py`, `marprom_sredi.py`.

## Izpadi vožnja -> brez -> vožnja (`marprom_izpadi.py`, `marprom_sredi.py`)

| okno | izpadov | na isto | od tega `ni_prihoda` + `ni_v_voznem_redu` | `-` (brez zakaja) | na drugo |
|---|---|---|---|---|---|
| pon 2. 11. | 312 | 155 | 133 | 21 | 157 |
| tor 3. 11. | 302 | 153 | 134 | 18 | 149 |
| čet 5. 11. | 307 | 89 | 62 | 27 | 218 |
| pet 6. 11. | 568 | 412 | 93 | 319 | 156 |
| 2.–3. 11. | 627 | 308 (593 min) | 267 | 39 | 319 |
| 5.–6. 11. | 886 | 501 (408 min) | 155 | 346 | 385 |

Izgubljene minute sredi vožnje, vozilo ostalo na vožnji (`marprom_sredi.py`): `ni_prihoda` 888 -> 341 min (-62 %), `ni_v_voznem_redu` 22 -> 16, `-` 8 -> 1 974 min.

`-` 6. 11. ni Marprom: 375 izpadov brez zakaja (2.–5. 11. 71–94 na dan), ob 7. uri 161 in 14.–16. uri 185 = 12 ponovnih zagonov storitve 6. 11. (journalctl: 7.37–7.52 šest, 14.45–16.29 šest); 2.–3. 11. po en zagon na dan, 5. 11. dva. Zagon pobriše `_vozila`, vsa vozila so do prvega razrešenja (mediana ~31 s) brez vožnje.

## Kaj od izpadov na isto ostane po popravku

Izpadi na isto z `ni_prihoda`/`ni_v_voznem_redu`, brez 5 min po zagonu: 2.–3. 11. 263 sredi vožnje (565 min) + 5 ob koncu; 5.–6. 11. 144 sredi (219 min) + 11 ob zagonu. Pred nobenim od 144 ni bilo `obdrzana`: popravek jih ne doseže, ker `potrebuje` vrne `NOVA`, ne `PREVERI`.

Vzrok 139 od 144: Marprom `NextStopPointId` skoči **natanko eno postajališče nazaj** (139 od 139 korak 1, nobeno postajališče na vožnji dvakrat). `potrebuje` (`kajros/marprom.py:220-224`, `naprej = [q ... if q >= s.seq]`) to vzame za novo vožnjo, razrešitev ne najde prihoda, vozilo izpade, mediana 70 s (p90 140 s), nato spet ista vožnja. Pari: 174->173 38, 84->359 25, 248->159 22, 46->43 19 (104 od 139); linije G2 43, G4 27, P16 26, G6 12; 31 vozil. 2.–3. 11. istih 173.
Ali je korak 1 nazaj kdaj prava menjava: 1. 11. 13.00–7. 11. 10.00 od 401 izpadov s korakom 1 nazaj 398 nazaj na isto vožnjo, 3 na drugo (2 po 48 in 51 min = konec izmene, 1 po 2 min). Korak 3+ nazaj: 81 na drugo, 5 na isto -> to je prava menjava.

## Ali obdržana drži (`marprom_obdrzana.py`, 4. 11. 21.50–7. 11. 10.00)

155 nizov `obdrzana`:

| konec niza | nizov | min | opomba |
|---|---|---|---|
| potrjena (Marprom spet pokaže isto vožnjo) | 104 | 332 | vse brez vrzeli v vzorcih; v 30 min vseh 104 na isti |
| izpuščena po meji 5 min za koncem | 29 | 204 (87 brez vrzeli) | vse po koncu po voznem redu; 12 pred končno, **0 miruje**; v 30 min 24 na drugi vožnji, 4 brez |
| druga vožnja (prevzame naslednjo iste linije) | 16 | 268 (23 brez vrzeli) | 16 od 16 ista linija; 13 po koncu po voznem redu |
| `izpodrinjena` | 6 | 3 | 10–50 s; isti dve vožnji oba dneva (G3 na mp-199 ob 8.13/8.17 in 5.42, P18 na mp-144 ob 19.32 in 20.32); v 30 min 6 od 6 brez vožnje = menjava vozila, prevzem prav |

Naslednje postajališče med nizom na obdržani vožnji: 158 od 159 vzorcev `stanje`. Stoječega vozila na končni z obdržano vožnjo ni (0 od 155 koncev z `miruje` na končni). Dolgi nizi (do 6 209 s, marprom-600 6. 11. 10.58–12.42) so vrzel v vzorcih: vozila ni v odgovoru Marproma, `_vozila` ga zbriše, `stanje` piše le spremembe; 21 od 155 nizov ima vrzel > 120 s.

**Sklep: obdržana drži.** Nobenega primera, da bi vozilo z obdržano vožnjo vozilo drugo.

## Ostalo

* Izpadi na drugo (prava menjava, `naslednje_ni_na_A`): 2. 11. 107 (560 min), 3. 11. 100 (718), 5. 11. **154 (1 510)**, 6. 11. 94 (563). 5. 11. odstopa z `ni_prihoda` 102 (drugi dnevi 43–52), največ 13.–16. ure (vrstic brez vožnje z `ni_prihoda` 61/73/72/45 na uro proti 30/51/63/53 6. 11.). 6. 11. s popravkom normalen, zato ni popravek; vzrok 5. 11. ni izmerjen.
* 12 zagonov storitve 6. 11. = 375 izpadov brez zakaja. Cena objav, ne koda.
