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

Delujeta oba načina — kar koli od tega gostitelj že uporablja:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT   # gostitelj vodi strežnik (Pella)
python main.py                                 # strežnik zaženemo sami
```

`app` je zato izpostavljen na ravni modula `main`. Če gostitelj javi
`Error loading ASGI app. Attribute "app" not found in module "main"`, pomeni,
da poganja prvo obliko — in prav zato je `app` tam.

Pri drugi obliki se vrata preberejo iz `PORT`; če ga ni, uporabi 8000.

## Nastavitve prek okolja

| Spremenljivka | Privzeto | Kaj počne |
|---|---|---|
| `PORT` | 8000 | vrata |
| `SZ_DATA_DIR` | `data` | kam gre baza (naj bo na trajnem disku) |
| `SZ_POLL_SECONDS` | 30 | razmik med zajemi |
| `SZ_COLLECTOR` | 1 | `0` izklopi zajem (samo API) |
| `SZ_REFRESH` | `off` | osveževanje voznega reda: `off`, `inprocess`, `subprocess` |
| `SZ_REFRESH_HOUR` | 4 | ura osvežitve, kadar ni `off` |

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

## Zakaj je osveževanje voznega reda privzeto izklopljeno

Uvoz GTFS je najdražji trenutek v življenju procesa. Izmerjeno na tem paketu:

| način | vrh pomnilnika | opomba |
|---|---|---|
| `inprocess` | **89 MB** | in ostane pri 85 MB — Python aren skoraj ne vrne sistemu |
| `subprocess` | 54 MB v otroku **poleg 57 MB starša** = ~111 MB skupaj | oboje je hkrati rezidentno |
| `off` | — | privzeto |

Pri 100 MB pomnilnika nobena od obeh ni varna: proces bi ob osvežitvi lahko
dobil OOM, in to vsak dan ob isti uri. Zato je privzeto `off`.

Vozni red osvežiš tako, da drugje pognaš `sztrack update`, novo `sz.sqlite`
daš v `seed/` in objaviš paket — obstoječa baza se ne povozi, ker se seed
uporabi le, kadar baze še ni. (Za to je treba staro bazo enkrat odstraniti
oziroma preimenovati.) Vsebinsko se vozni red spremeni nekajkrat na leto.

Na stroju z več pomnilnika nastavi `SZ_REFRESH=subprocess`.

## Preverjanje, da zajem res teče

```
GET /api/health
```

```json
{"trips": 723, "stations": 267, "observations": 271,
 "runs_recorded": 271, "days_covered": 1,
 "db_bytes": 1708032, "last_feed_at": "2026-08-19T13:51:04+02:00"}
```

Po ponovnem zagonu gostitelja poglej prav to: če `runs_recorded` pade nazaj
na 0, disk ne preživi zagona in zbrano se izgublja.

## Trajnost diska je pogoj

Zgodovine zamud ni od nikoder dobiti nazaj — GTFS-RT nosi samo trenutno stanje.
Če gostitelj ob vsaki objavi ali ponovnem zagonu zavrže disk, se zbrano izgubi.
Pred resnim zajemom preveri, ali `SZ_DATA_DIR` preživi ponovni zagon, in si
uredi občasno kopijo `sz.sqlite`.
