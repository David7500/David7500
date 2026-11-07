# Popravek zajema vlakov po prvem dnevu prenove (koledar 7. 11. 2026)

Izvedba odločitve glavne seje po [vlaki.md](vlaki.md) (skok nazaj) in [nepripeti-sz.md](nepripeti-sz.md) (Slivnica). Produkcija samo branje; izvleček 6.–7. 11. v `/var/tmp/koledar-vlaki2.sqlite` na arwenu (665 voženj, 9 153 `run`, 17 762 `obs`, 8 962 `sz_zamuda`, do 7. 11. 11.17), na koncu pobrisan.

## Sprotne najdbe

1. **LPV 2401 7. 11. v dnevniku** (`obs`, arwen): postanki 1–7 z odhodom 0 od 04.24.31 do 04.46.31, ob 04.47.16 postanek 4 z +9 (540 s), nato 5 (04.48), 6 (04.52), 7 (04.55), 8 (04.58) s +9 — natanko vozni red + 9 min, zemljevid je izračun. `sz_zamuda.prvic_ts` postankov 1–7 je 15 s pred prvo vrstico v `obs` (04.36.16 proti 04.36.31): **prvi zapis zemljevida v dnevnik ni šel**, ker je derp.si ob 02.54 zapisal 0/0 na vseh 17 postankih (`worth_logging`: enako zadnji zapisani); v `obs` je šele osvežitev 15 s pozneje (prihod `NULL`). Dnevnik prvega zapisa (prihoda) torej ne vidi, za nazaj ga je treba sestaviti iz `prvic_ts`.
2. Kdo bere `sz_zamuda`: samo `zamude_sz` (`potrdi` zadnji zapisani po `zadnjic_ts`, `zapisi` zadnji po `stop_seq` in po `zadnjic_ts`). `run` za postanke za skokom bere `stats.last_measured` (meja prevoženo) — novejša vrstica na postanku zadaj jo že zdaj ustavi (`test_nazaj_z_vecjo_zamudo_je_zvisana_zamuda`), statistika, `dosled`, okno. Dosje dobi surove vzorce pred `potrdi`, popravek ga ne zadene.
3. **Preizkus pred popravkom pade** (`test_skok_nazaj_z_vecjo_zamudo_preklice_neprevozene_postanke`, zaporedje LPV 2401): po skoku `run` [(4, 0, 540), (5, 0, 0), (6, 0, 0), (7, 0, 0)] namesto [(4, 540, 540)].
4. **Popravek** (`zamude_sz.zapisi`): nazaj z večjo zamudo pobriše `sz_zamuda` za `stop_seq >= seq` in `run` za `stop_seq > seq`, kjer je zapis zemljevida (kot emulacija `ponovi.py`: vrstice samo derp.si ostanejo); števec `preklicanih` v `meta.zamude_sz`. Prvi zapis postanka gre v `obs` vedno (`iz_lege.zapisi_meritev(..., v_dnevnik=True)`): dnevnik vidi prihod in skok nazaj tudi, ko je vrednost enaka zadnji vrstici, zato je zgodovino mogoče ponoviti iz `obs`. `obs` se ne briše.
5. **Ponovitev s pravo kodo** (`ponovi_zapisi.py`: zaporedje iz `obs` + `prvic_ts` skozi `zapisi` stare in nove kode na prazni bazi; izvleček do 7. 11. 11.17, voženj-dni z vsemi zapisi `run` po objavi):

   | | voženj | ura nazaj: arwen / stara koda / nova | stal ≥ 10 min | prihod po odhodu | preklicanih | izgubljenih |
   |---|---|---|---|---|---|---|
   | 6. 11. po objavi | 256 | 54 (21,1 %) / 53 / **5 (2,0 %)** | 46 (18,0 %) / 46 / **4 (1,6 %)** | 2 / 2 / 2 | 195 | 3 / 4 |
   | 7. 11. do 11.17 | 108 | 8 (7,4 %) / 8 / **1 (0,9 %)** | 7 (6,5 %) / 7 / **1 (0,9 %)** | 1 / 1 / 1 | 36 | 0 / 0 |

   Stara koda ponovi `run` z arwena (53 / 46 proti 54 / 46), ponovitev je zvesta. „Izgubljenih“ = postanek v `run` z arwena, ki ga ponovitev nima: stara 3 (ponovitev), nova 4, pravilo samo 1 od 3 057. Ne vidi stanj, ki jih je stara koda zavrnila kot „nazaj“ (po preklicu bi bila lahko naprej) — v `obs` jih ni, dosje jih ima. Cilj < 0,5 % ne drži: ostanek je semantika med postajama (vlaki.md, točka 5).
6. **Slivnica** (`zamude_sz.IMENA_ZEMLJEVIDA`, `pripni`): ključ imena z zemljevida dobi še ime iz voznega reda (`naslednje` = {ključ, preslikava}), ujemanje po starem ostane. Arwen: edina postaja vlakov z „livnic“ v imenu je 1120963 Spodnja Slivnica (32 vlakov LP 4491–4537), 266 imen postaj vlakov — preslikava ne more zadeti druge postaje; ostala imena z zemljevida (254 v tednu, nepripeti-sz.md) se ujamejo že zdaj in jih preslikava ne spremeni. Preizkus `test_slivnica_z_zemljevida_je_spodnja_slivnica` (LP 4501 6. 11., „Slivnica, Odhod 04:38, +0“ -> postanek Grosuplje) pred popravkom pade (`pripete == []`).
7. **Popravilo zgodovine** (`kajros popravi-vlake`, `zamude_sz._skoki_nazaj` + `preklici_skoke`, od `PREKLIC_OD` = 6. 11.): zapisi zemljevida po objavi iz `obs` (`observed_at − feed_ts` < 5 s; prvi zapis, ki v `obs` ni šel, iz `sz_zamuda.prvic_ts` z vrednostjo zadnje vrstice dnevnika pred njim) znova po pravilu `zapisi`. Popravi samo preklicane postanke: znova dosežen dobi prihod prvega zapisa po skoku (odhod ostane), nikoli znova dosežen gre iz `run` in `sz_zamuda`; `obs` ostane. Ponovni zagon 0 (idempotentno). Preizkus `test_popravi_vlake_preklice_skoke_nazaj_po_objavi` (LPV 2401, kot na arwenu) pred izvedbo pade (`KeyError`).

   Suho in z zapisom na kopiji izvlečka (`popravi_skoke_suho.py`, do 7. 11. 11.17): **6. 11.: 358 prihodov, 2 postanka, 102 vožnji; 7. 11.: 63 prihodov, 0, 23** (skupaj 421 / 2 / 125). Stari deli ukaza 0 (že pognano 6. 11.). Po zapisu, samo vlaki:

   | | voženj-dni | ura nazaj | stal ≥ 10 min |
   |---|---|---|---|
   | 6. 11., `run` samo po objavi | 242 | 54 (22,3 %) → 6 (2,5 %) | 46 (19,0 %) → 5 (2,1 %) |
   | 6. 11., vse | 599 | 81 (13,5 %) → 29 (4,8 %) | 56 (9,3 %) → 12 (2,0 %) |
   | 7. 11. do 11.17 | 103 | 8 (7,8 %) → 1 (1,0 %) | 7 (6,8 %) → 1 (1,0 %) |

   Na produkciji ni pognano (ne suho ne z zapisom): pove David. Ukaz po objavi popravka: `./venv/bin/python -m kajros.cli popravi-vlake --od 2026-11-06` (štetje), nato `--zapisi`. Pričakovano za 6. 11. ~360 prihodov in 2 postanka, za 7. 11. več kot 63 (izvleček do 11.17, do objave popravka še pride).
8. **Preverjeno**: 1 408 preizkusov zelenih, `preveri.sh` (8021) zelen. Poizvedbe ukaza po indeksih (`obs` in `run` po (trip_id, service_date) za vožnje s `sz_zamuda`), ne po celem dnevu. Izvleček na arwenu pobrisan, strežnik 8021 ustavljen.

## Za glavno sejo

* Ostanek po pravilu (6. 11. 2,0–2,5 %, 7. 11. 0,9–1,0 %) je pripis med postajama (SŽ dvigne zamudo, ko je `Postaja` že naslednja); cilj < 0,5 % brez tega ne drži.
* Pravilo pobriše tudi prihod postanka skoka (`>= seq`, kot predlog in `ponovi.py`): če je bil njegov prvi zapis pravi in nižji (vlak prišel točno, obstal za postajo), prihod dobi višjo zamudo. Ni izmerjeno, koliko takih; dosje bi pokazal.
* Ponovitev ne vidi stanj, ki jih je stara koda zavrnila kot „nazaj“, po preklicu pa bi bila naprej (v `obs` jih ni).
