# Pregled 5. 11., točki 5 in 6: meritvi (7. 11. 2026)

Vir: `docs/presoja/2026-11-05-pregled.md`, točki 5 (vzorec omrežja) in 6 (tabla, ko SŽ dviguje zamudo).

## Stanje pred delom

* Od 3. 11. se noben commit ne dotakne `(? IS NULL OR t.network = ?)` ne veje `lm["stop_seq"] >= d["stop_seq"]` na tabli. Prenova vlakov 6. 11. (88ec114) je dodala `trenutna_s` v `last_measured`, ki jo tabla rabi **samo za postanke naprej**; postanek na meji je ostal pri `run`. Točka 6 torej ni bila rešena.

## Točka 6: tabla, ko SŽ dviguje zamudo

Merilo `koledar-dviguje.py` (scratchpad, na arwenu nad `dosje.sqlite`, samo branje): vsi vzorci zemljevida SŽ (`tocke`, 5 s) 2.–6. 11. 2026. Stanje (Vrsta, Postaja, Zamuda_cas) velja, ko traja ≥ 25 s. Epizoda = Vrsta 1, ista `Postaja`, zamuda višja od zadnje z `Odhod` v preteklosti (to je v `run`), `Odhod` > ura + 60 s.

* **10 epizod na 3 247 voženj-dneh** (9 voženj-dni, 0,28 %). Razlika SŽ − `run`: mediana 5 min, največ 31 (vlak 246 Murska Sobota). Trajanje: mediana ~1 min, največ 5,5 min (631 Radeče).
* **Kaj pove naslednji postanek** (zamuda, ki jo dobi `Postaja`): ≥ SŽ − 1 min v 8 od 10, ≤ `run` + 1 min v 1, vmes 1; bližje SŽ kot `run` v **9 od 10**. Vlak je torej skoraj vedno še stal na postanku na meji, kot pravi SŽ.
* **Cena napake ni simetrična**: ob uri, ko SŽ kaže odhod v prihodnosti, je odhod po `run` že mimo. Če je vlak res odpeljal, ga potnik, ki še ni na vlaku, tako ali tako ne ujame; če stoji, ga tabla s `run` skrije (primer pregleda: vrstica Plave izgine ob 8.56, SŽ odhod 8.58).

**Odločitev: popravek.** Na odhodni tabli postanek na meji vzame `trenutna_s`, kadar je `trenutna_seq` ta postanek in je višja; vrsta „po podatkih SŽ“ (`PO_SZ`, ista beseda kot zemljevid in okno), brez „izmerjeno na“. Prihodna tabla ostane (prihod je po uri že bil). Brez nove poizvedbe: `lm` že nosi `trenutna_s`, zato ni počasneje. Preizkus `test_tabla_na_meji_vzame_dvig_sz_z_odhodom_s_te_postaje`.

Ostane: `stats.zamuda_na_postanku` (iskalnik, pot) ima isto vejo brez `trenutna_s`. Ni popravljeno (meja klicev); pri 0,28 % voženj-dni in ~1 min na epizodo obseg majhen.

## Točka 5: vzorec omrežja

* `_BOARD_SQL`, `_CONNECTIONS_SQL`, `znano_do`, `last_sched_s`: pregled je izmeril, da goli `t.network = ?` škodi ali ne koristi (tabla avtobusov 4–62×). Ne spreminjam: v produkciji `None` ne poda nihče, `(:network IS NULL OR …)` in `+t.network` dasta isti načrt in čas, sprememba bi bila samo kozmetična in bi podrla 22 preizkusov s privzetkom `None`.
* `LAST_STOP_SQL` in `_LIVE_SQL` (odprti v pregledu „izmeri“): meritev na izvlečku arwena (`trip` 165 938, `run` 12 540 357, `sched` 886 688, brez `sqlite_stat1`; produkcija ga nima) **ni končana**: izvleček 4 min, nato stara `LAST_STOP_SQL` za železnico teče > 8 min CPU brez izida (pregled na razvojni bazi: 722 ms). Ustavljeno zaradi meje klicev, izvleček pobrisan. Samo to že kaže, da načrt brez statistike na arwenovi velikosti ni razvojni načrt — prav zato slep popravek ne.
* `_LIVE_SQL` je vroča pot (zemljevid, ogrevanje na 30 s, samo `zeleznica`); `LAST_STOP_SQL` teče ponoči v povzetkih. Rok za meritev z manjšim okvirom (en klic na varianto, `timeout`) v izidu.
