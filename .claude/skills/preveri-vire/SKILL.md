---
name: preveri-vire
description: Preveri zajem virov Kajrosa, ko /admin ali pošta kaže oranžno ali rdeče, ali ko David reče „preveri vire“ ali pokaže posnetek opozoril. Prebere zdravje s produkcije, za vsako vrstico najde vzrok (vir laže, naša koda ali resnica na cesti), presodi stopnjo, popravi, izmeri in zapiše.
---

# Preveri vire

Zajem virov je steber aplikacije. David, 31. 10. 2026: „to more delati v nulo“. Ta postopek je za trenutek, ko `/admin` ali pošta („kajros: za pregled …“ ali „kajros: stoji …“) pokaže oranžno ali rdeče, in za redni pregled.

## Kaj pomeni stopnja

Pravila so v `kajros/zdravje.py` (`ocena`, `posta`, `Sled`), preizkusi v `tests/test_opozorila.py`.

* **Rumeno**: popravi se samo ali je samo za vedenje. Ne ukrepaj, razen če je vrstica nova in je ne znaš pojasniti.
* **Oranžno**: ne popravi se samo. To je tvoje delo (koda ali podatki), ni pa nujno v minuti. Pošta gre podnevi (7–22 h).
* **Rdeče**: takoj. Nekaj stoji ali potniki ta hip ne dobijo podatkov. Najprej povrni delovanje (ponovni zagon `sudo systemctl restart kajros.service` na arwenu dela brez gesla), šele nato išči vzrok. Potniki po 20 min molka dobijo samodejno obvestilo (`obvestila.samodejna`).

Rumena, ki ne mine, postane oranžna (meje v `zdravje.py`, trajanje šteje `Sled`). Novo vrstico zdravja vedno uvrsti po tem merilu: ali se popravi sama, ali jo popravi koda, ali mora kdo ukrepati takoj. Dodaj preizkus.

## Postopek

1. **Stanje produkcije.** `./scripts/admin.sh podatki > <scratchpad>/admin.json`, nato v kontekst samo povzetek: `razredi` (ne zelene), `razlogi`, `ukrepi`, `primeri`, `v_posti`. Celega JSON-a ne beri.
2. **Vzrok vsake oranžne in rdeče vrstice** (in nove rumene). Recepti so spodaj. Baza samo za branje:
   `ssh david@192.168.1.46 'sqlite3 -readonly "file:/var/lib/kajros/kajros.sqlite?mode=ro" "…"'`.
   Daljša analiza: skripto iz `skripte/` prepiši v `/tmp` na arwenu (`scp`) in jo poženi z `/opt/kajros/.venv/bin/python` (baza `mode=ro`). V bazo na arwenu ne piši nikoli.
3. **Presodi, kdo laže.** Vir (napačen ali zamrznjen podatek), naša koda ali resnica na cesti (zastoj, obvoz, odpoved). Povezave v pasu vrstice odprejo vozilo na zemljevidu (`/app/map?trip=…` ali `?vozilo=…`): poglej, kje vozilo res je.
4. **Meri, preden spremeniš pravilo.** Na več dneh in za vse prevoznike, ne samo za tistega, ki je prižgal vrstico (`sistem-ne-krpanje`). Hevristika, ki bi brisala ali skrivala podatke, gre najprej v senco (primer `KAJROS_DRSI`).
5. **Popravi** v kodi, dodaj preizkus, poženi `./scripts/preveri.sh`.
6. **Zapiši sproti.** Številke v `docs/MERITVE.md`, pravilo v `.claude/rules/zajem.md`, razlog v commit, odprto in narejeno v `docs/VIRI-PRESOJA.md`.
7. **Objava.** `git push arwen <veja>` in počakaj na 200 (`.claude/rules/objava.md`). Za malino pripravi ukaz Davidu.

## Recepti po vrstici

| vrstica | kaj pogledati |
|---|---|
| `neznane` IJPP | nov vozni red s starimi id-ji: `kajros update`, nato `kajros zamenjave` (zajem.md, „Nov vozni red, stari id-ji“) |
| `neznane` LPP | `skripte/lpp_neznane.py` (žive vožnje proti objavi: zamik, zasedena kandidatka, par), `skripte/lpp_dvojniki.py DAN…` (enaki dvojniki v objavi) |
| `lega_brez_zamude` | `skripte/brez_zamude.py` (katera vozila, sled v `obs`, `gps_prehod`, `lega`); nato `straza_opazeno` za vozilo: kaj je rekel NAP (`vir='nap'`, prazen `trip_id` = ni pripel) in kaj derp.si. Kartica NAP v /admin: `brez_dneva`, `brez_voznje`, `pripetih` |
| `fantomi` (zamuda raste z uro) | `skripte/fantom.py DAN [x]` in `skripte/fantom_ponovitev.py DAN…`; vozila na zemljevidu prek povezav. Odločitev `KAJROS_DRSI=senca` → `vodi` |
| vir ne odgovarja (`derp_*`, `nap`, `zamude_sz`, `zamude_lpp`, `marprom`, `kranj`, `vir:*`) | gumb „Preveri vire zdaj“ v /admin (`viri.preveri`), kartica vira (zadnja napaka, HTTP), `journalctl -u kajros.service` na arwenu |
| nit ne piše, `nit:*` | rdeče: ponovni zagon, nato vzrok v dnevniku (izjema mimo `except`, zaklenjena baza: `zajem.md`, „Napaka pisanja“) |
| `vozni_red*` | ukrep vira `gtfs_*` v `kajros/viri.py`; mestni zipi: `gtfs.mestni_viri` |
| `skladnost_sz` | primeri vlakov so v vrstici; `zajem.md`, „Straža“ |

## Že znano

* `docs/VIRI-PRESOJA.md`: luknje iz presoje 31. 10. 2026, kaj je narejeno in kaj odprto, po prednosti.
* `docs/presoja/2026-10-31-najdbe.md`: surove najdbe dveh bralcev kode z vrsticami.

## Subagenti

Varčno. Eno vrstico preveri sam. Bralca kode (en, največ dva) samo za širok pregled, ko je kode več kot ~30k žetonov in vrne malo: z mejo klicev orodij in sprotnim zapisom najdb v datoteko. Nad 80 % 5-urnega okna nič novih.
