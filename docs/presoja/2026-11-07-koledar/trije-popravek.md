# Naloga B: trije majhni popravki (7. 11. 2026)

Veja `worktree-wf_97941863-054-2`, izhodišče 244d6ed.

## (1) Marprom, korak nazaj

Preizkus `test_potrebuje_korak_nazaj` pred popravkom pade (vrne `nova` pri koraku 1). Popravek `marprom.potrebuje`: prazen `naprej` + naslednje = največji seq vožnje pod `s.seq` -> `s.seq` ostane, nadaljuje do preverbe okna (`PO_KONCU_S`) in `PREVERI`/None. Odstop od naročila: tudi korak nazaj gre skozi preverbo konca vožnje (sicer vozilo za koncem, ki mu next skače nazaj, ne bi dobilo `NOVA`). `test_preverjanje_vzame_voznjo_ko_je_dokaz_ali_je_mimo` je imel korak 1 kot „za vozilom“ -> prestavljen na korak 2 (192). test_marprom 20/20.
