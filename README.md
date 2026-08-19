# sztrack

Zajem in analiza voznih redov ter zamud **Slovenskih železnic** iz odprtih podatkov.

Prikaz ni vključen namerno — vse teče skozi JSON API, tako da lahko frontend
(zemljevid, dashboard, mobilna aplikacija) izbereš kasneje brez predelave zaledja.

## Od kod podatki

| | vir | velikost | pogostost |
|---|---|---|---|
| Vozni redi | [`ijpp_gtfs.zip`](https://gitlab.com/derp-si/gtfs-generators) (GTFS) | 41 MB | ~1× dnevno |
| Zamude | `rt.gtfs.derp.si/sources/ijpp/trip_updates` (GTFS-RT) | 250 KB | 30 s |

Izvorno gre za podatke SŽ/IJPP z [NAP](https://www.nap.si) (licenca **CC BY-SA 4.0**),
ki jih [DERP](https://derp.si) pretvarja v GTFS in GTFS-RT.

Oba vira podpirata pogojni GET, zato se ob nespremenjenih podatkih ne prenese nič.
41 MB zipa ni treba prenašati zaradi zamud — to sta ločena vira.

## Kaj se da in česa ne

Feed pri vlakih nosi **samo `delay`**, brez absolutnega časa prihoda
(avtobusi ga imajo, vlaki ne). Dejanski čas se zato računa kot
`vozni red + zamuda`. Iz tega sledita dve omejitvi:

* **Ločljivost je 60 s**, z zastavico `uncertainty: 120`. Hitrosti na kratkih
  odsekih so zato nesmiselne — `segment_speeds()` upošteva samo odseke ≥ 5 km.
* **Feed je drseče okno** — v enem klicu dobiš le postanke okoli trenutnega
  položaja vlaka, ne cele vožnje. Zgodovine ni: če je ne posnameš sam,
  je ni nikjer. Zato `poll` teče neprekinjeno in piše ob vsaki spremembi.

Zamude naprej po progi so **napoved, ne meritev** — sistem predvideva, da vlak
nadoknadi. Vrednost se popravi, ko postaja dejansko mine, zato je merodajna
zadnja znana vrednost (tabela `run`).

V podatkih **ni** cen, sestave vlaka, perona, zasedenosti ne GPS pozicije vlakov.

## Namestitev

```bash
pip install -e ".[api]"
```

## Uporaba

```bash
sztrack init                       # ustvari bazo
sztrack update                     # prenesi + uvozi vozni red (304 -> preskoči)
sztrack poll --once                # en zajem zamud
sztrack poll                       # neprekinjeno, vsakih 30 s

sztrack show "LPV 2206"                        # vozni red
sztrack show "LPV 2206" --date 2026-08-18      # konkretna vožnja z zamudami
sztrack stats --days 90                        # lestvica vlakov
sztrack export --out export/                   # GeoJSON mreže in postaj

uvicorn sztrack.api:app --reload   # JSON API na :8000
python main.py                     # API + zajem v enem procesu
```

Za objavo na gostitelju glej [DEPLOY.md](DEPLOY.md); paket sestavi
`scripts/build_deploy_zip.sh`.

Za trajni zajem so v `deploy/` systemd enote (poll kot servis, `update` kot dnevni timer).

## API

| endpoint | kaj vrne |
|---|---|
| `GET /api/stations` | 267 železniških postaj s koordinatami |
| `GET /api/network.geojson` | geometrija prog, vsak odsek z dolžino v km |
| `GET /api/trains` | vsi vlaki v voznem redu |
| `GET /api/train/{no}` | vozni red vlaka |
| `GET /api/train/{no}/run?date=` | ena vožnja: red, zamuda, dejanski časi |
| `GET /api/train/{no}/history?days=` | zgodovina po dnevih in po postajah |
| `GET /api/train/{no}/predict?stop_seq=&delay_s=` | napoved zamude naprej |
| `GET /api/speeds?train_no=` | voznoredna vs. izmerjena hitrost po odsekih |
| `GET /api/stats?days=` | lestvica vlakov po zamudi |
| `GET /api/live` | vlaki trenutno v feedu |

## Razdalje med postajami

`stop_times.txt` nima `shape_dist_traveled`, zato se dolžine odsekov računajo:
postaje se pravokotno projicirajo na polilinijo proge iz `shapes.txt`, razlika
kumulativnih razdalj je dolžina odseka, čez vse vlake se vzame mediana.

Rezultat: **267 postaj**, **389 odsekov**, elementarna mreža ~**1250 km**
(ujema se z dejansko slovensko mrežo). Razpršenost med vlaki po istem odseku
je 0 m — geometrija je konsistentna.

Odseki z `elementary = 0` so »preskoki« hitrih vlakov čez vmesne postaje;
za risanje zemljevida filtriraj `elementary = 1`, za hitrosti pa uporabi tisti
odsek, ki ustreza dejanskemu paru zaporednih postankov danega vlaka.

⚠️ To niso uradne kilometrske lege, ampak dolžine GTFS shapeov — odstopanje
~2–4 % (Zidani Most–Ljubljana da 63,6 km proti uradnim ~61 km). Za primerjave
med vlaki povsem uporabno, za absolutne trditve o hitrosti pa upoštevaj napako.

## Napoved zamude

`stats.predict()` je namenoma preprost: zamuda se prenese naprej, popravljena za
historično mediano spremembe na tem odseku pri tem vlaku. Pri vlakih je to trdna
izhodiščna točka — dokler nimaš nekaj mesecev zajema, kompleksnejši model nima
česa izkoristiti. Ko podatki narastejo, so naslednji koraki ura v dnevu, dan v
tednu in zamuda povezanih voženj iste kompozicije.

## Licenca podatkov

Podatki so **CC BY-SA 4.0** (NAP / DUJPP) — pri objavi navedi vir.
