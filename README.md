# sztrack

**Kdaj mi pelje in koliko zamuja.** Zajem, prikaz in analiza zamud
slovenskega javnega potniškega prometa iz odprtih podatkov —
vlaki SŽ in avtobusi (LPP, Arriva, Nomago, AP Murska Sobota).

Zaledje je Python (FastAPI + SQLite), prikaz vanilla JS brez ogrodja.
Vse teče skozi isti JSON API, tako da je prikaz zamenljiv.

```bash
./venv/bin/python -m uvicorn sztrack.api:app --host 127.0.0.1 --port 8001 --reload
# nato http://127.0.0.1:8001/app
```

## Strani

| pot | kaj |
|---|---|
| `/app` | vlaki: iskalnik povezav in odhodna tabla — vstopna stran |
| `/app/bus` | avtobusi: ista stran, drugo omrežje |
| `/app/train/{št}` | okno ene vožnje: profil poti, zgodovina, razmere, hitrosti |
| `/app/ovire` | dela na progi in nadomestni prevozi |
| `/app/statistika` | razrezi zajetega: po vrsti vlaka, uri, dnevu (dnevni povzetek) |
| `/app/map` | živi zemljevid |
| `/docs` | OpenAPI |

Vsaka stran ima preklop **preprosto / napredno**. Napredni pogled ne odpre
druge strani — na isti doda p90, deleže, številke postankov in to, kaj je
o vrednosti rekel feed.

## Od kod podatki

```
SŽ + IJPP → NAP (b2b.nap.si, CC BY-SA 4.0) → DERP gtfs-generators → GTFS + GTFS-RT
```

| Kaj | vir | velikost | pogostost |
|---|---|---|---|
| Vozni red | [`ijpp_gtfs.zip`](https://gitlab.com/derp-si/gtfs-generators) | 43 MB | ~1×/dan |
| Zamude | `rt.gtfs.derp.si/sources/ijpp/trip_updates` | 250 KB | 30 s |
| Ovire in žive zamude | `rt.gtfs.derp.si/sources/ijpp/service_alerts` | 110 KB | 60 s |
| Vreme | `open-meteo.com` (arhiv + napoved) | — | dnevno, za nazaj |

Vsi viri podpirajo pogojni GET — ob nespremenjenih podatkih se ne prenese nič.
V zipu je **ves** slovenski javni promet: 20 736 voženj petih agencij, 9 791
postajališč, 403 208 postankov. Privzeto se uvozi samo SŽ; ostale doda
`SZ_AGENCIES=1118,1123,1119,1121`.

**Dve ločeni omrežji, ne en kup.** `/app` so vlaki in nadomestni prevozi SŽ
(ti na svoji relaciji zamenjujejo vlak), `/app/bus` so avtobusi. Potnik ve,
ali gre z vlakom ali z busom. Skupen je samo zemljevid: vlak je krog na zadnji
postaji z meritvijo, avtobus puščica na izmerjeni legi iz GPS.

## Kaj podatki so in česa ni

To ni akademska opomba — vsaka postavka spodaj določa, kaj sme prikaz trditi.

* **Feed pri vlakih nosi samo `delay`**, brez absolutnega časa. Dejanski čas =
  vozni red + zamuda. Ločljivost 60 s, zato sekund ne kažemo nikoli in hitrosti
  računamo le na odsekih ≥ 5 km.
* **Feed je drseče okno.** En klic da postanke okoli trenutnega položaja; celo
  vožnjo sestavimo iz zaporednih pollov.
* **Zamude naprej po progi so napoved — in izmerjeno slaba.** Prevoznikova
  napoved za še nedosežene postanke ima MAE 7,9 min proti 1,3 min za preprost
  prenos trenutne zamude naprej. Prikaz zato uporablja lastno oceno.
  Merljivo: `sztrack backtest --operator`.
* **Vlak zamudo porabi na rezervi voznega reda.** Napoved zato ni statistika
  sama: `slack = Σ max(0, postanek − 2 min)` med izhodiščem in ciljem se
  odšteje od trenutne zamude, ostanek popravi zgodovina te poti. LP 4219 ima
  na Mostu na Soči devet minut postanka in ni nikoli nadoknadil več kot sedem.
  MAE 1,92 min proti 2,94 min za prenos (`sztrack backtest`).
* **Ničli, ki jo feed vrne za en klic, ne verjamemo.** Pri 14 % postankov se
  pojavi vzorec X, 0, X v razmiku ene minute; zamuda med dvema klicema ne pade
  za več, kot je vmes minilo časa.
* **Zamuda je izmerjena v prometnem mestu, ne na peronu.** Ime tega mesta je v
  `SZ-DELAY` obvestilih in ga prikaz pove.
* **Odhodne zamude s prve postaje ni** — feed nikoli ne poroča `stop_seq = 1`.
  Odhodna tabla zato vzame meritev naslednje postaje in napiše, od kod je.
* **Vlaki nimajo GPS, avtobusi ga imajo.** `vehicle_positions` vsebuje
  izključno avtobuse (do 130 hkrati, s smerjo in hitrostjo). Lega vlaka na
  zemljevidu je zadnje znano prometno mesto, lega avtobusa je izmerjena.
  `current_status` pa ni zanesljiv — med vozili s `STOPPED_AT` so bila taka
  pri 32 km/h — zato ali vozilo stoji, presodi izmerjena hitrost.
* **Kje je avtobus, ki se še ni začel voziti, pove veriga vozila.** GTFS
  `block_id` veže vožnje istega vozila; imajo ga samo avtobusi in tam le
  tretjina voženj. Zamude prejšnje vožnje **ne prenašamo naprej** -- izmerjeno
  je slabše od nevednosti (MAE 4,53 min proti 2,29 min za „predpostavi
  točno"), ker vozilo zamudo med vožnjama nadoknadi. Prikaz zato pove, kje
  vozilo je, ne kdaj bo.
* **Zgodovine ni nikjer.** Če je ne posnamemo sami, je ni.
* **Ni** cen, sestave vlaka, perona, zasedenosti. Odpovedi feed pozna
  strukturirano, a jih SŽ pošiljajo kot besedilo obvestila. `bikes_allowed`
  je pri vseh 20 736 vožnjah `0` -- polje obstaja, podatka ni.

## Ukazna vrstica

```bash
sztrack init                      # ustvari bazo
sztrack update                    # prenesi + uvozi vozni red (304 -> preskoči)
sztrack poll                      # neprekinjen zajem zamud
sztrack alerts --live             # zadnja poročila prevoznika o zamudi
sztrack show "LPV 2206" --date 2026-08-28
sztrack stats --days 90           # lestvica vlakov
sztrack backtest                  # izmeri napako napovedi
sztrack backtest --operator       # prevoznikova napoved proti prenosu zamude
sztrack summarize                 # znova izracunaj dnevne razreze statistike
sztrack repair                    # znova zgradi `run` iz dnevnika `obs`
sztrack prune                     # pobriši star dnevnik (`run` ostane)
sztrack weather --days 7          # dopolni vreme za nazaj
sztrack merge druga.sqlite        # prilij zajem z drugega stroja
sztrack seed                      # zgradi priloženo bazo za namestitev
sztrack export --out export/      # GeoJSON mreže in postaj
```

## Razvoj

```bash
./scripts/dev-restart.sh          # ponovni zagon strežnika na 8001
./venv/bin/python -m pytest tests/ -q
./venv/bin/python scripts/preveri_paleto.py    # kontrast in barvna slepota
```

Odvisnosti v `requirements.txt` je pet in naj tako ostane; razvojne so
v `requirements-dev.txt`.

## Objava

Ciljni gostitelj je Raspberry Pi doma. Podrobnosti v [DEPLOY.md](DEPLOY.md),
navodila za delo na projektu v [CLAUDE.md](CLAUDE.md).

**API nima avtentikacije — vrat na usmerjevalniku ne odpiraj.**

## Licenca podatkov

Podatki SŽ in IJPP prek [NAP](https://www.nap.si), **CC BY-SA 4.0**,
obdelava [DERP](https://derp.si). Vreme [Open-Meteo](https://open-meteo.com)
(CC BY 4.0). Zemljevid © OpenStreetMap contributors.
