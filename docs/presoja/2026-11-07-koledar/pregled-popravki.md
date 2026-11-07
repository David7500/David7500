# Popravki iz pregleda 5. 11. (štiri napake)

Vir: `docs/presoja/2026-11-05-pregled.md`, točke 1–4. Vrstica koledarja pet 6. 11. 2026.

## Stanje pred delom (7. 11., ~10.00)

* Vse štiri napake v kodi še odprte (veja na f4e0bc3). Commit 90a1007 („odrezan žeton“) je žeton zamude v `common.js` (prikaz), ne žeton za `/admin` ali `/stik`: ni popravil ničesar od tega.
* Prenova zajema vlakov 6. 11.: trenutno zamudo SŽ nosi `stats.last_measured` (`trenutna_s`, `trenutna_seq`, prag `TRENUTNA_VISJA_S` 60 s), bere jo `stats.trenutna_zamuda(lm)`. Tabla, iskalnik in glava okna jo že rabijo; opozorilo o zapori ne (`zapore.dopolni`, `api.api_run`).

## Popravki (vsak: preizkus rdeč, popravek, zelen)

1. **Prekinjena zahteva** (`api._preberi_telo`): `ClientDisconnect` → 400 „Zahteva je bila prekinjena.“ Velja za vseh šest pisalnih poti (ena funkcija). Preizkus `test_prekinjena_zahteva_ni_500` (prej `ClientDisconnect`, zdaj 400).
2. **Ne-ASCII žeton** (`api._preveri_admina`, `stik._preveri_zeton`): `compare_digest` nad bajti, kot `donacije.py`. `/admin?k=ž` 403 namesto 500, `/stik` z `1.ž` zavrnitev. Preizkusa `test_ne_ascii_zeton_je_napacen_ne_500` (prej TypeError), `test_ponarejen_zeton[1.ž]`.
3. **Zapora in zamuda SŽ**: `zapore.dopolni` jemlje `stats.trenutna_zamuda(lm)`, `api.api_run` `max(zamuda na meji, trenutna_s)` (meja se lahko premakne zaradi deljenja lege, trenutna velja samo navzgor). Preizkus `test_zapora_po_trenutni_zamudi_sz`: +0 na A, SŽ +6 h → tabla in okno brez opozorila (prej oba z njim; tabla in okno sta padla vsak posebej); SŽ +5 min → oba z opozorilom. Učinek po pregledu majhen: SŽ nad mejo za ≥ 3 min v 11 od 4 453 trenutkov (16. 10.).
4. **Nočni povzetki** (`statistika._avto`): brez ure z ≥ 10 vzorci `None`. Preizkus `test_avto_brez_ure_z_dovolj_vzorci` (36 vzorcev, 6 ur po 6: prej `ValueError: max() iterable argument is empty`).

## Preverjanje

* pytest: 1 404 zelenih (12,5 s).
* `scripts/preveri.sh` na 8012: izhodna koda 0. Opomba: brez `KAJROS_DATA_DIR` v okolju `preveri.sh` skladnost bere `./data` v worktreeju, ki ga ni → prazna baza, „no such table: run“. Ob zagonu preveri.sh v worktreeju podaj isti `KAJROS_DATA_DIR` kot strežniku.
