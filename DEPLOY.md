# Objava na majhnem strežniku (Pella in podobni)

En sam proces streže API in hkrati zajema zamude — ločenega delavca ni.
Zajem teče v ozadnji niti, ki jo zažene FastAPI ob zagonu.

## Vsebina paketa

```
main.py            vstopna točka: uvicorn na $PORT
requirements.txt   fastapi, uvicorn, requests, gtfs-realtime-bindings
Procfile           web: python main.py
sztrack/           koda
seed/sz.sqlite     pripravljen vozni red (1,7 MB) za takojšen zagon
```

## Zagon

Zagonski ukaz je `python main.py`. Vrata prebere iz `PORT`; če ga ni, uporabi 8000.

## Nastavitve prek okolja

| Spremenljivka | Privzeto | Kaj počne |
|---|---|---|
| `PORT` | 8000 | vrata |
| `SZ_DATA_DIR` | `data` | kam gre baza (naj bo na trajnem disku) |
| `SZ_POLL_SECONDS` | 30 | razmik med zajemi |
| `SZ_COLLECTOR` | 1 | `0` izklopi zajem (samo API) |
| `SZ_REFRESH_HOUR` | 4 | ura dnevne osvežitve voznega reda |

## Kaj se zgodi ob prvem zagonu

Če baze še ni, se prekopira `seed/sz.sqlite` — zagon je takojšen. Če je tudi
seed ni, si vozni red prenese sam (41 MB, uvoz ~23 s pri polnem jedru; na 0,1
jedra računaj nekaj minut) in zip nato pobriše.

**Obstoječa baza se nikoli ne povozi.** Ponovna objava paketa torej ne izbriše
zajete zgodovine — dokler je `SZ_DATA_DIR` na disku, ki preživi objavo.

## Poraba

Merjeno na tem paketu:

| | |
|---|---|
| RSS ob zagonu (s priloženo bazo) | **60 MB** |
| RSS po prvem zajemu | **74 MB** |
| Uvoz GTFS (vrh) | **54 MB**, 23 s |
| Baza po uvozu | 1,7 MB |
| Promet | 250 KB / 30 s + 41 MB enkrat na dan |

Pri 100 MB pomnilnika ostane okoli 25 MB rezerve. Če jo bo zmanjkalo, je prvi
korak `SZ_POLL_SECONDS=60` in izogibanje `/api/network.geojson` v vroči zanki
(odgovor je ~1 MB — postavi ga raje kot statično datoteko prek `sztrack export`).

## Trajnost diska je pogoj

Zgodovine zamud ni od nikoder dobiti nazaj — GTFS-RT nosi samo trenutno stanje.
Če gostitelj ob vsaki objavi ali ponovnem zagonu zavrže disk, se zbrano izgubi.
Pred resnim zajemom preveri, ali `SZ_DATA_DIR` preživi ponovni zagon, in si
uredi občasno kopijo `sz.sqlite`.
