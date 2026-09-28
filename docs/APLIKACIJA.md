# Kakšna bo aplikacija

Zapis dogovorjenega. Odprto je označeno.

## Osnovna postavitev

**Zaledje in prikaz ločena po API-ju, ne po procesu.** Zajem in strežba v enem procesu (`main.py` → FastAPI z zajemom v ozadnji niti); frontend govori z njim samo prek JSON-a. Izbira prikaza zato ne zahteva sprememb v zaledju.

**Zemljevid: MapLibre, podlaga vektorska OpenFreeMap** (22. 9. 2026). Prej Leaflet z rastrskimi ploščicami (OSM, nato Esri „Dark Gray Canvas"). MapLibre je BSD, plačljiv je Mapbox, ne MapLibre. Veliki zemljevid = MapLibre sam, ker se od blizu nagne v 3D; od 23. 9. 2026 tudi obe strani poti (vodenje po pešpoti = kamera za hrbtom pešca). Okno vožnje ostane Leaflet z MapLibrom kot podlago (glej `.claude/rules/zemljevid.md`).

## Kaj aplikacija dela

Iz pogovora štiri stvari:

1. **Kje so vlaki zdaj in kdo zamuja.** Živa slika mreže, vlaki obarvani po zamudi.
2. **Kaj je z enim vlakom.** Cela vožnja postaja–postaja: voznoredni čas, dejanski čas, zamuda po postajah, razdalje odsekov.
3. **Kakšen je ta vlak po navadi.** Zgodovina zamud, porazdelitev, točnost, najslabše vožnje.
4. **Kje na mreži zamude nastajajo.** Hitrosti po odsekih, voznoredne proti izmerjenim; mediana prirasta zamude po odseku.

Peta stvar, napoved zamude, zaenkrat izhodiščna: prenos trenutne zamude naprej, popravljen za historično mediano spremembe na odseku. Za boljše rabimo 2–3 mesece zajema.

## Kaj že stoji

`/app` — živ nadzorni pregled (commit `e90eb2c`): FastAPI streže Jinja2 lupino in statiko, Leaflet z OSM ploščicami riše mrežo in vlake, ob strani lestvica zamud. Vlaki narisani **na zadnji znani postaji, brez interpolacije položaja** — skladno s podatki. Barve iz lestvice spodaj, vedno z izpisanim številom minut.

V bistvu smer **A (nadzorna soba)**. Ostale tri ostajajo kot dodatni pogledi, ne zamenjava.

## Štiri oblikovne smeri — izbira je odprta

Platno: https://claude.ai/code/artifact/189e04ee-26e3-4c2e-916a-26da4e9ae709

| | Smer | Ideja | Za | Proti |
|---|---|---|---|---|
| **A** | Nadzorna soba | zemljevid = aplikacija; temno, gosto | takoj vidiš, kje je težava | na telefonu nepraktično |
| **B** | Vozni red | tipografija = aplikacija; po vzoru tiskanih voznih redov | en vlak od zgoraj navzdol, kot ljudje razmišljajo | slabo za pogled na celo mrežo |
| **C** | Analitika | številke = aplikacija; porazdelitve, lestvice | edina izkoristi zajeto zgodovino | prvih nekaj mesecev prazna |
| **D** | Sledilnik | en vlak = aplikacija; telefon, velika številka | reši potnikovo vprašanje v treh sekundah | ne odgovori na nič širšega |

Smeri se da mešati — npr. A za zemljevid, D za posamezen vlak.

Zemljevidi v mockupih iz **prave geometrije mreže** (267 postaj, 283 elementarnih odsekov), ne izmišljeni. Živi podatki resnični; 30-dnevna zgodovina in porazdelitev ponazoritveni.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast proti podlagi v svetli in temni različici:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

**Vsaka oznaka poleg barve vedno nosi tudi število minut.** Barva nikoli ne nosi pomena sama — zaradi barvne slepote in ker je razlika med +4 in +14 za potnika bistvena, odtenek pa ne pove, katera je.

## Kar mora prikaz priznati o podatkih

Ni pedantnost — brez tega aplikacija laže.

* **Ločljivost 60 s**, zastavica `uncertainty: 120`. Ne kaži sekund in ne računaj hitrosti na kratkih odsekih (`/api/speeds` upošteva samo ≥ 5 km).
* **Zamuda izmerjena v prometnem mestu, ne nujno na postaji.** Uradna aplikacija SŽ piše „3 min V ODHODU – Slovenska Bistrica", čeprav vlak tam ne ustavlja. Prikaz naj pove, **kje** je bila zamuda nazadnje izmerjena, in ne dela videza, da velja za postajo, kjer stojiš.
* **Zamude naprej po progi = napoved, ne meritev.** Označi drugače kot potrjene — v smeri D rešeno z oznako „napoved" ob prihodnjih postajah.
* **Položaj vlaka interpoliran iz voznega reda in zamude, ne GPS.** Preverjeno: `vehicle_positions` vsebuje avtobuse, vlakov ne. Pika na zemljevidu naj ne daje vtisa metrske natančnosti.
* **Ni cen, sestave vlaka, perona ne zasedenosti.** Za ceno: vzdrževati ločeno ali uporabnika poslati v uradno aplikacijo.

## Endpointi, ki jih bo prikaz uporabljal

| endpoint | za kaj |
|---|---|
| `GET /api/network.geojson` | geometrija prog z dolžino odseka v km — osnovna plast zemljevida |
| `GET /api/stations` | 267 postaj s koordinatami |
| `GET /api/live` | vlaki trenutno v feedu z zadnjo znano zamudo |
| `GET /api/train/{no}/run?date=` | ena vožnja: red, zamuda, dejanski časi |
| `GET /api/train/{no}/history?days=` | zgodovina po dnevih in po postajah |
| `GET /api/train/{no}/predict?stop_seq=&delay_s=` | napoved naprej po progi |
| `GET /api/speeds?train_no=` | voznoredna proti izmerjeni hitrosti po odsekih |
| `GET /api/stats?days=` | lestvica vlakov po zamudi |
| `GET /api/health` | stanje zajema |

`network.geojson` ~1 MB; za prikaz postrezi kot statično datoteko (`kajros export`), ne kliči v vroči zanki.

## Dostop

Doma API na `http://<ip>:8000`, za razvoj zadošča. Od zunaj odločeno: **imenovani Cloudflarov tunel** na domeni `kajros.app`. Tailscale Funnel odpade, ker zna samo `*.ts.net`; isti tunel zmore tudi ssh prek brskalnika (za Accessom), drugo orodje ni potrebno.

**Vrat na usmerjevalniku ne odpiraj — API nima avtentikacije.** Samo za branje: v `api.py` ni poti razen `GET` in nobenega pisanja v bazo iz zahteve. CORS odprt za vse izvore, namerno, da prikaz lahko teče drugje.

**Odgovori predpomnjeni tam, kjer se med zahtevami ne spremenijo.** Kdor piše svoj prikaz: `/api/health` (60 s), `/api/live` in razrezi statistike so predpomnjeni; glava `X-Osvezi-Cez` pri legah pove, čez koliko sekund je smiselno vprašati znova.
