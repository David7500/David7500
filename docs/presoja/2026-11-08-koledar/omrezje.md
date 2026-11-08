# Vzorec omrežja na arwenovi velikosti (koledar 8. 11. 2026)

Pregled 5. 11., točka 5: `LAST_STOP_SQL` in `_LIVE_SQL` sta bila odprta („izmeri“). Meritev 7. 11.
na izvlečku ni končala (stara `LAST_STOP_SQL` > 8 min): izvleček je bil narejen s `CREATE TABLE
AS`, brez indeksov. Zdaj kopija z `VACUUM INTO` (isti indeksi; `sqlite_stat1` nima ne kopija ne
produkcija), 5,1 GB, 13.44–13.48, `run` 12 619 692 vrstic, `trip` 167 639 avtobusnih in 791
železniških. Skripta `omrezje_cas.py` (koda pred spremembo, ab16f36), meja 300 s, `nice -n 10`.
Arwen ima 7 GB pomnilnika, kopija in produkcija ga delita: časi so z delno toplim predpomnilnikom,
najboljši od dveh (`LAST_STOP_SQL`) oziroma treh (`_LIVE_SQL`) tekov.

Zapisi: „zdaj“ = `(:network IS NULL OR t.network = :network)`, „golo“ = `t.network = :network`,
„plus“ = `+t.network = :network`. Vrstice so pri vseh treh enake.

| poizvedba | omrežje | zdaj | golo | plus |
|---|---|---|---|---|
| `LAST_STOP_SQL` + `network_stats`, 90 dni | železnica | 24,4 s | **1,4 s** | 24,2 s |
| | avtobus | **40,3 s** | 51,0 s | 39,3 s |
| `_LIVE_SQL` pet. 6. 11. ob 8 h | železnica | 211 ms | **66 ms** | 208 ms |
| ob 17 h | železnica | 267 ms | **115 ms** | 261 ms |
| sob. 7. 11. ponoči (`overnight_only`) | železnica | 339 ms | **195 ms** | 333 ms |
| ob 8 h | avtobus | 1 836 ms | **1 573 ms** | 1 817 ms |
| ob 17 h | avtobus | 3 142 ms | **2 784 ms** | 3 142 ms |
| ponoči | avtobus | 866 ms | **721 ms** | 860 ms |

Produkcija potrdi „zdaj“: nočni `network_stats` 8. 11. 24,8 s za železnico in 50,4 s za avtobuse
(`povzetek.took_ms`), `breakdowns` 31,3 s in 161,4 s.

Načrta: pri „zdaj“ in „plus“ obe poizvedbi preletita `run` po ključu
(`SCAN r USING COVERING INDEX sqlite_autoindex_run_1`) in za vsako vrstico pogledata `trip`.
Golo začne pri `trip`: `LAST_STOP_SQL` po `trip_network`, `_LIVE_SQL` po `trip_running`
(omrežje, začetek), nato skok v `run` po vožnji. Za 791 vlakov je to mnogo manj dela, za
167 639 avtobusnih voženj pri `LAST_STOP_SQL` več (vsaka vožnja svoj skok), pri `_LIVE_SQL` pa
manj, ker okvir začetka in konca zoži vožnje že v indeksu.

## Odločitev

* `_LIVE_SQL`: golo, hitrejše v obeh omrežjih. Vroča pot: ogrevanje zemljevida po vsakem branju
  (30 s) in `/api/live`. Privzetek `network` v `_live_rows` in `_live` je zdaj `zeleznica`
  (produkcija `None` ne poda nikoli, `NETWORK_Q` dovoli le omrežji).
* `LAST_STOP_SQL`: po omrežju. Železnica golo, avtobusi `+t.network` (isti načrt in čas kot
  doslej). `LAST_STOP_SQL` je slovar po omrežju; `None` ni več dovoljen (ni ga podal nihče).
  Nočni `network_stats` železnice prihrani okoli 23 s; `breakdowns` ima isti `mx`, posebej ni
  merjen (preverba: `povzetek.took_ms` po prvi noči).
* Pravilo v `CLAUDE.md` dopolnjeno: golo, razen kjer poizvedba začne bolje drugje.
