# Naloga B: trije majhni popravki (7. 11. 2026)

Veja `worktree-wf_97941863-054-2`, izhodišče 244d6ed.

## (1) Marprom, korak nazaj

Preizkus `test_potrebuje_korak_nazaj` pred popravkom pade (vrne `nova` pri koraku 1). Popravek `marprom.potrebuje`: prazen `naprej` + naslednje = največji seq vožnje pod `s.seq` -> `s.seq` ostane, nadaljuje do preverbe okna (`PO_KONCU_S`) in `PREVERI`/None. Odstop od naročila: tudi korak nazaj gre skozi preverbo konca vožnje (sicer vozilo za koncem, ki mu next skače nazaj, ne bi dobilo `NOVA`). `test_preverjanje_vzame_voznjo_ko_je_dokaz_ali_je_mimo` je imel korak 1 kot „za vozilom“ -> prestavljen na korak 2 (192). test_marprom 20/20.

## (2) Iskalnik in pot na postanku na meji

Preizkus: drugi del `test_ista_zamuda_kot_iskalnik_zvez` (`tests/test_pot.py`), `zamude_sz.trenutne` zamenjan (SŽ +840 s na postanku 1, `run` +240, ura 8.15 po odhodu iz `run`). Pred popravkom: tabla (840, PO_SZ), iskalnik (240, izmerjeno) -> pade. Popravek `stats.zamuda_na_postanku`, veja `lm.stop_seq >= stop_seq`: `prihod=False`, `trenutna_seq == stop_seq`, `trenutna_s > vrednost` -> (`trenutna_s`, None, PO_SZ). test_pot + test_zamude_sz 112/112.

## (3) Vrstica pokritost v zdravju

Preizkusi (`tests/test_opozorila.py`, 5 × `test_pokritost_*`) pred popravkom padejo (KeyError `pokritost`). Ključi v produkciji preverjeni (meta `pokritost` na arwenu: 1118, 1119, 1121, 1123, 1161, kranj, lpp, marprom -> `stats.AGENCY_NAMES`). Mere: avtobusi lega (`z_lego`) in zamuda danes (`z_kdaj`), vsaka svoj ključ sledi; Kranj, LPP mestni, Marprom imajo eno izhodišče, velja za obe. SŽ samo `z_zamudo`. Stara meta: vrstice ni, sledi se ponastavijo (trajanje začne znova). `posta` preskoči `_SAMO_ADMIN`. `admin.js` vrstici „pokritost · zamuda v 15 min“ doda barvo. Vsi testi 1411.
