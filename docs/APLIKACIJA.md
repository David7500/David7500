# Kakšna bo aplikacija

Zapis dogovorjenega. Kar je še odprto, je tako tudi označeno.

## Osnovna postavitev

**Zaledje in prikaz sta ločena po API-ju, ne po procesu.** Zajem in strežba
tečeta v enem samem procesu (`main.py` → FastAPI z zajemom v ozadnji niti),
frontend pa govori z njim samo prek JSON-a. Zaradi tega izbira prikaza ne
zahteva nobene spremembe v zaledju.

**Zemljevid: Leaflet + OSM rastrske ploščice.** Odločeno. MapLibre z vektorskimi
ploščicami (OpenFreeMap, Protomaps) je bil alternativa in je prav tako
brezplačen — MapLibre je BSD, plačljiv je Mapbox, ne MapLibre. Leaflet je
preprostejši; ceni se odpovemo gladkemu zoomu in barvanju prog po podatkih na
ravni ploščic.

Pri OSM ploščicah velja njihova politika uporabe: za resno rabo si postavi
lasten predpomnilnik ploščic ali preidi na vektorske.

## Kaj aplikacija dela

Iz pogovora so se izluščile štiri stvari, ki jih zna povedati:

1. **Kje so vlaki zdaj in kdo zamuja.** Živa slika mreže, vlaki obarvani po
   velikosti zamude.
2. **Kaj je z enim vlakom.** Cela vožnja od postaje do postaje: voznoredni čas,
   dejanski čas, zamuda po postajah, razdalje odsekov.
3. **Kakšen je ta vlak po navadi.** Zgodovina zamud, porazdelitev, točnost,
   najslabše vožnje.
4. **Kje na mreži zamude nastajajo.** Hitrosti po odsekih, voznoredne proti
   izmerjenim; mediana prirasta zamude po odseku.

Peta stvar, napoved zamude, je zaenkrat izhodiščna: prenos trenutne zamude
naprej, popravljen za historično mediano spremembe na odseku. Za kaj boljšega
rabimo 2–3 mesece zajema.

## Kaj že stoji

`/app` — živ nadzorni pregled (commit `e90eb2c`): FastAPI streže Jinja2 lupino
in statiko, Leaflet z OSM ploščicami riše mrežo in vlake, ob strani je lestvica
zamud. Vlaki so narisani **na zadnji znani postaji, brez interpolacije položaja**
— kar je skladno s tem, kar podatki dopuščajo. Barve so iz lestvice spodaj,
vedno z izpisanim številom minut.

To je v bistvu smer **A (nadzorna soba)**. Ostale tri ostajajo na mizi kot
dodatni pogledi, ne kot zamenjava.

## Štiri oblikovne smeri — izbira je odprta

Platno: https://claude.ai/code/artifact/189e04ee-26e3-4c2e-916a-26da4e9ae709

| | Smer | Ideja | Za | Proti |
|---|---|---|---|---|
| **A** | Nadzorna soba | zemljevid je aplikacija; temno, gosto | takoj vidiš, kje je težava | na telefonu nepraktično |
| **B** | Vozni red | tipografija je aplikacija; po vzoru tiskanih voznih redov | en vlak od zgoraj navzdol, kot ljudje razmišljajo | slabo za pogled na celo mrežo |
| **C** | Analitika | številke so aplikacija; porazdelitve, lestvice | edina izkoristi zajeto zgodovino | prvih nekaj mesecev prazna |
| **D** | Sledilnik | en vlak je aplikacija; telefon, velika številka | reši potnikovo vprašanje v treh sekundah | ne odgovori na nič širšega |

Smeri se da mešati — na primer A za zemljevid in D za posamezen vlak.

Zemljevidi v mockupih so narisani iz **prave geometrije mreže** (267 postaj,
283 elementarnih odsekov), ne izmišljeni. Živi podatki v njih so resnični;
30-dnevna zgodovina in porazdelitev sta ponazoritveni.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast
proti podlagi v svetli in temni različici:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

**Vsaka oznaka poleg barve vedno nosi tudi število minut.** Barva nikoli ne
nosi pomena sama — zaradi barvne slepote in zato, ker je razlika med +4 in +14
za potnika bistvena, odtenek pa ne pove, katera je.

## Kar mora prikaz priznati o podatkih

To ni pedantnost — če se tega ne držimo, aplikacija laže.

* **Ločljivost je 60 s**, z zastavico `uncertainty: 120`. Ne kaži sekund in ne
  računaj hitrosti na kratkih odsekih (`/api/speeds` upošteva samo ≥ 5 km).
* **Zamuda je izmerjena v prometnem mestu, ne nujno na postaji.** Uradna
  aplikacija SŽ piše „3 min V ODHODU – Slovenska Bistrica", čeprav vlak tam ne
  ustavlja. Naš prikaz naj prav tako pove, **kje** je bila zamuda nazadnje
  izmerjena, in ne dela videza, da meritev velja za postajo, kjer stojiš.
* **Zamude naprej po progi so napoved, ne meritev.** Označi jih drugače kot
  potrjene — v smeri D je to rešeno z oznako „napoved" ob prihodnjih postajah.
* **Položaj vlaka je interpoliran iz voznega reda in zamude, ne GPS.**
  Preverjeno: `vehicle_positions` vsebuje avtobuse, vlakov ne. Pika na
  zemljevidu naj ne daje vtisa metrske natančnosti.
* **Ni cen, sestave vlaka, perona ne zasedenosti.** Če bo aplikacija hotela
  ceno, jo bo treba vzdrževati ločeno ali uporabnika poslati v uradno aplikacijo.

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

`network.geojson` je ~1 MB; za prikaz ga postrezi kot statično datoteko
(`sztrack export`) in ne kliči v vroči zanki.

## Dostop

Doma je API na `http://<ip-pija>:8000` in za razvoj to zadošča. Ko bo prikaz
rabil dostop od zunaj: Tailscale (zasebno) ali Cloudflare Tunnel (javno, s
HTTPS). **Vrat na usmerjevalniku ne odpiraj — API nima avtentikacije.**
CORS je odprt za vse izvore, kar je namerno, da frontend lahko teče drugje.
