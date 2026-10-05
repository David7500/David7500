# Stran /o-nas v 3D

Ena stran, en svet, ena kamera: drsenje premika čas filma `T`, vse na zaslonu je funkcija `T`, zato se da drseti naprej in nazaj. Besedilo je v predlogi `kajros/templates/o_nas.html` (berljivo brez JS), svet je tu, zgrajen v en sveženj `kajros/static/o-nas/o3.js`. Pravila in zakaj je ta stran izjema: `.claude/rules/strani.md`.

| poglavje | T | prizor |
|---|---|---|
| uvod | 0 | številčnica ure postaje |
| 1 ime | 0–54 | kronos (ura, tabla 07.42), prazen tir, KISS pripelje ob 7.55, „+13 min“ |
| 2 zgodba | 54–128 | dijak vstopi skozi vrata v preddverje, vožnja skozi dolino (cerkev, kozolca), šola ob 8.00, prihod 8.13 |
| 3 kaj dela | 128–206 | relief Slovenije, omrežje, vse vožnje 1. 10. 2026 med 7. in 8. uro, IC 351 po dnevih, budilka |
| 4 podpri | 206–240 | postaja ponoči, dijak s prenosnikom na klopi |

Ure v zgodbi so ponazoritev, ne trditev o kateri progi; na strani o avtorju piše samo »dijak«.

## Datoteke

* `src/main.js` — časovnica: drsenje → `T`, ključi kamere (Hermitov zlepek z omejenimi tangentami, rezi), ura postaje kot švicarska podrejena ura (`uraKorak`), pot dijaka skozi vrata, testne kljuke `window.__film`.
* `src/vlak.js` — Stadler KISS SŽ 313: karoserija iz obročev, čelo kot višinsko polje z luknjo za spenjačo, poslikava v senčilniku. Mere s fotografij na Commons (313-001, -002, -008, -010, -016, -017, -018). Za okni notranjost brez geometrije (žarek v škatlo etaže: sedeži, potniki, luči, daljna okna); pod nadstreškom se v karoseriji odbija nadstrešek. Za vrati vmesnega voza pravo preddverje s stopnicami, v karoseriji je takrat odprtina.
* `src/postaja.js` — peron, nadstrešek, ura, tabla, poslopje, dijak (postava »močan«, izbrana med tremi).
* `src/proga.js` — tir, pragovi, gramoz, vozna mreža. Žice so trak z najmanj 1,25 piksla in pokritostjo, ne `LINES`, zato ne utripajo; tirnice in pragovi imajo zamik globine po plasteh.
* `src/pokrajina.js`, `src/nebo.js` — teren, drevesa, vasi, megla; nebo in zračna perspektiva v vseh materialih.
* `src/karta.js` — Pogl. 3; podatki se nalagajo vzporedno in ne zadržijo prvega kadra. Barve zamud vzame iz spremenljivk v `base.css`.

## Gradnja

```bash
o-nas/gradi.sh
```

Prenese pripeti različici three.js in esbuilda z npm v `o-nas/node_modules` (preverjeni po sha512, Node ni potreben) in zapiše `kajros/static/o-nas/o3.js`. Sveženj gre v git, strežnik ničesar ne gradi.

## Podatki za Pogl. 3

`kajros/static/o-nas/` (`karta.json`, `karta-podatki.png`, `relief.png`) je posnetek 1. 10. 2026, ne živ podatek. Nova različica:

```bash
cd o-nas/prep
# izvoz s strežnika, baza samo za branje
ssh -o BatchMode=yes david@192.168.1.46 'nice -n 19 python3 - | gzip -6' < izvoz_karte.py > karta-surovo.json.gz
# višine: Terrain Tiles (Mapzen, AWS), terrarium z9, x 274..279, y 180..183
mkdir -p dem && for x in 274 275 276 277 278 279; do for y in 180 181 182 183; do
  curl -fsS "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/9/$x/$y.png" -o "dem/t_${x}_${y}.png"; done; done
../../venv/bin/python pripravi_karto.py
```

Meja (`slovenija.json`) je iz Natural Earth (`ne_10m_admin_0_countries`). Številke v besedilu Pogl. 3 (77 vlakov, 1 106 avtobusov, IC 351 v 42 dneh) so iz istega izvoza; ob novem izvozu jih popravi v predlogi.

## Pregled

```bash
python o-nas/posnetek.py "http://127.0.0.1:8001/o-nas?dpr=1" --size 412x860 --mobile --shots T=0,T=50,T=230
```

`T=` je čas filma, `P=T:px:py:pz:cx:cy:cz:f` lastna kamera. Rabi `websockets` v svojem venv-u; posnetki v `posnetki/`.
