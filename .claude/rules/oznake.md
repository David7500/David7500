---
paths:
  - "kajros/static/**"
  - "kajros/templates/**"
  - "scripts/preveri_paleto.py"
---

# Kako je zamuda napisana in pobarvana

Velja povsod, kjer se zamuda pokaže: kartica zemljevida, iskalnik, časovnica,
postanek potnika.

## Prezgodnja vožnja

* **Avtobus je lahko PREZGODEN; vlak v zajetih podatkih nikoli.** V 45 146
  železniških vrsticah `run` ni niti ene negativne vrednosti — najmanjša je
  natanko 0. Pri avtobusih je 12,0 % vrstic vsaj minuto prezgodnjih in 4,5 %
  vsaj tri; **41,7 % avtobusnih voženj ima vsaj en prezgodnji postanek**
  (LPP 22,6 % vrstic, Nomago 10,6 %, Arriva 8,9 %).

  Prikaz je to do zdaj **skrival**: vrstica je pričakovano uro izpisala samo
  ob `delay_s >= 60`, torej je prezgoden avtobus kazal zgolj voznoredno uro.
  Napaka v najslabšo smer — potnik pride ob objavljeni uri in avtobusa ni več.
  Zdaj je prag `abs(delay_s) >= 60`, žeton pa pove „3 min prej", ne „−3 min":
  minus pred številko je uganka, beseda ni. Barva ostane siva, ker to res ni
  zamuda — in prav zato mora povedati beseda. Pravilo je v `common.delayText()`
  in velja **povsod**: kartica zemljevida, iskalnik vozila, stolpec zamude v
  časovnici in postanek potnika. Za ozke stolpce ima kratko obliko („5 prej").

  **V glavi okna vožnje smer nosi naslov, ne enota.** „Trenutna zamuda" nad
  „6 min prej" si nasprotuje, „Vozi prezgodaj" nad „6 min prej" pa besedo
  ponovi. Zato naslov pove smer in številka velikost: **„Vozi prezgodaj" ·
  „6 min"**.

  Ali je prezgodnja vrednost resnična, je bilo preverjeno na LPP 25
  (Medvode ↔ Zadobrova). V smeri proti Zadobrovi je bila na Gosposvetski
  prezgodnja v **vseh 17 zajetih vožnjah**, povprečno −4,4 min, najpozneje
  −5 s; profil čez progo je lok, ki na obeh koncih izgine (Prušnikova −74 s,
  Kompas −224, Gosposvetska −265, Kolodvor −73, konec +123). GPS to potrdi:
  30. 8. ob 12:10:44 je bilo vozilo LJ LPP-124 že za postankom, ki ima vozni
  red 12:13. To torej ni napaka zajema, ampak **prevelika rezerva voznega reda
  skozi Šiško** — v nasprotni smeri je ista postaja povprečno +370 s. Zajem
  LPP je za zdaj samo vikendski (od 29. 8.); ali velja med tednom, se bo videlo.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

Pravila, ki se jih drži obstoječa koda in naj se jih tudi nova:

* **Vsaka oznaka poleg barve vedno nosi tudi minute.** Barva nikoli ne nosi
  pomena sama — barvna slepota, in +4 proti +14 je za potnika bistvena razlika.
* **Razred se določi iz zaokrožene minute, ne iz sekund.** Meje v `DELAY_RAMP`
  so v minutah in gredo skozi isto zaokroževanje kot `delayLabel`. Prej so bile
  v sekundah (`<= 60` = točno): 60 s je pisalo „+1" sivo, 61 s „+1" oranžno —
  ista številka, dve barvi. Barva ne sme pripovedovati druge zgodbe kot
  številka poleg nje.

  **Ista past se je ponovila pri „prej".** Prag je bil `s <= -60`, zaokroževanje
  pa se prelomi pri −30 s: −45 s je zato izpisalo golo **„−1"** namesto
  „1 min prej". Pravilo je zdaj v `common.isEarly()` in ga uporabljata okno
  vožnje in iskalnik zvez — en prag, ena zaokrožena minuta.
* **Kar se na zaslonu sešteva, zaokroži enkrat in potem računaj.** Preostali
  čas za prestop je bil `round(dejansko_s)`, poleg njega pa `round(načrtovano_s)`
  in `round(zamuda_s)` — vsaka številka zaokrožena prav, skupaj pa
  „načrtovano 52 min, prvi vlak +5, ostane 48". Bralec, ki sešteje, dobi 47 in
  ima prav. Zdaj se preostanek računa iz **zaokroženih minut**
  (`preostaliPrestop()`), ne iz sekund. Ista past kot pri razredu zamude.
* **Razred se šteje na strežniku po ISTI zaokroženi minuti kot na zaslonu.**
  Pravilo zgoraj je bilo popravljeno na odjemalcu, `stats.py` pa je razvrščal
  po sekundah (`v <= 60` = „točno“) — v režo 30–60 s pade **3 280 od 45 015
  voženj (7,29 %)**, ki jih je strežnik štel kot sive „točno“, barvna lestvica
  pa bi jih pobarvala oranžno „1–5 min“. Zdaj gre vse skozi
  `stats._razred_zamude()`.

  **`floor(x + 0.5)`, ne `round()`:** JS `Math.round` zaokroži pol navzgor,
  Pythonov `round` bančno (`round(0.5) == 0`), zato bi se pri natanko 30 s
  prikaz in izračun razšla.
* **„Točno“ in „delež točnih“ nista isto in ne smeta nositi iste besede.**
  Žeton `točno` je zaokroženih **nič** minut, `on_time_share` pa **pet**. V
  istem okvirju je pisalo „točno 81“ in „točnih 69 %“ — 81 od 162 je 50 % in
  bralec tega ne more spraviti skupaj. Zato prikaz zdaj povsod pove prag:
  **„72 % v 5 min“**.

  In ker sta v istem okvirju, se morata **sešteti**: prag je zato
  `ON_TIME_MIN = 5` v **minutah**, ne 300 s. Dokler je bil v sekundah, razred
  „1–5 min“ pa je segal do zaokroženih pet (330 s), se 553 voženj (1,23 %) ni
  ujelo — bile so v razredu, a ne med točnimi. Zdaj velja
  `točno + 1–5 min = izpisani odstotek` in to je preverjeno v testu.
* Odtenek lestvice se uporablja **samo tam, kjer pomeni velikost zamude**.
* **Omrežje prestavi samo poudarek, ne lestvice.** `body.net-avtobus` premakne
  `--accent` na zeleno; `--d-*` ostanejo oranžni tudi tam. Ista barva mora
  pomeniti isto zamudo povsod — sicer „+5 min“ na avtobusni in železniški
  strani nista primerljiva. Lestvica je poleg tega validirana na monotonost
  svetlosti in barvno slepoto; zelena različica bi rabila svojo validacijo in
  bi trčila s poudarkom.

  **Kar sme biti zeleno, gre skozi `var(--accent)`, nikoli skozi trdo zapisan
  `#f0934f`.** Tega se koda ni držala: `.hist-note strong`, žetona shranjenih
  poti in zvezdica na iskalniku so bili na avtobusni strani oranžni brez
  razloga. Izjemi, ki ostaneta trdi, sta **legenda omrežij na zemljevidu**
  (oranžna = vlak, zelena = avtobus, to je njun pomen) in **izbira na domači
  strani** (`.pick-train` proti `.pick-bus`).
* **Padec zamude na postaji riši vedno, krogec prihoda pa le, kadar je zanj
  prostor** (`MIN_SPLIT_PX = 15`). Krogec meri v premeru 10 pik, polna pika
  odhoda 11 — pri manjšem razmiku se prekrijeta, navpičnica med njima izgine
  pod njima in videti je kot **dva nepovezana krogca**. Prav to je bilo
  prijavljeno pri Divači (+16 → +15, razmik natanko 10 pik).

  Rešitev ni skrivanje: enominutni padec je resničen podatek. Odsek se konča
  pri **prihodni** vrednosti, navpičnica pa pade na odhodno — pri majhni
  razliki je to stopnica ob piki in se bere, pri veliki (Ljubljana, 170 pik)
  dobi še krogec. Skrivanje bi izgubilo prav tisto, zaradi česar je padec
  narisan.
* Kjer meritve ni (ocena, napoved), nastopi rezervirana `#a8d8ff`, ki je
  lestvica ne uporablja.
* Vreme ima **svoj semafor**, ne odtenek lestvice zamud.

### Semafor razmer

| stopnja | oznaka | barva |
|---|---|---|
| 0 | mirne | `#6b7480` |
| 1–3 | blage | `#5aa87d` |
| 4–6 | zahtevne | `#d9b33c` |
| 7–10 | hude | `#d1495b` |

Stopnja 0–10 je seštevek točk za padavine, sneg, sunke vetra, meglo, nevihto in
mraz (`weather.severity()`). Razčlenitev gre v tooltip — indeks brez razčlenitve
je črna skrinja. Modelska vrednost za celico 8 × 8 km, ne meritev na peronu.

**Žeton nikoli ne pokaže gole stopnje.** „0" potniku ne pove nič — to je bilo
popravljeno prej — a **„1" prav tako ne**: številka brez enote in brez lestvice
je uganka, razlaga pa je v `title`, ki ga na telefonu ni mogoče doseči. Prvi
popravek je torej rešil pol težave.

Zato: do vključno **blagih (≤ 3) piše temperatura**, ki nekaj pove sama po sebi,
od **zahtevnih (≥ 4) naprej pa beseda** („zahtevne", „hude"), ki pove, kaj je
narobe. Barva ostane ista lestvica razmer. Besede so samo tam, kjer je kaj za
povedati, in takih postankov je malo, zato širina ni težava. Žetoni so
v preprostem pogledu na **postajah naprej po progi** (napoved, črtkan rob);
prevožene postaje so tam itak skrite in mirno vreme za nazaj ne pove ničesar.

**Lestvic ne mešaj v istem registru.** Rumena razmer `#d9b33c` proti svetli
oranžni zamud `#f2a87e` je pri deutanu ΔE 5,5 — nerazločljivo. Zato je zamuda
krivulja s pikami zgoraj, razmere pa stolpci v ločenem pasu spodaj, in vsak
stolpec od stopnje 4 naprej nosi svojo številko. Paleto preverjaj z
`scripts/preveri_paleto.py`, ne na oko. Ta izmeri kontrast (WCAG), monotonost
svetlosti in razločljivost pri barvni slepoti (CIEDE2000 na simulaciji
protan/deutan/tritan). Trk obeh lestvic je pri tritanu **ΔE 1,6**, torej hujši
od tu prej zapisanih 5,5 — ločena registra sta nujna, ne okrasna.


## Znak

Monogram **K**: navpično steblo in dve roki iz iste točke. Siva roka je vozni
red, poudarjena resnica — ista misel kot ime (*chronos* proti *kairosu*).

* **V glavi strani** (`brand-mark`) je znak brez podlage in bere `currentColor`,
  zato na avtobusni strani pozeleni skupaj s poudarkom. Steblo in zgornja roka
  imata `stroke-opacity="0.5"`.
* **Kot ikona** (`static/ikone/`) ima podlago, ker stoji sam. Nastane s
  `scripts/naredi-ikone.sh`, ne ročno.
* **Vlakov znak ni več znamka.** Ostane samo tam, kjer pomeni **omrežje**:
  preklop v glavi in izbira na domači strani. Znamka mora pokrivati oboje.
* Znak mora zdržati **svetlo in temno podlago**. Prvi poskus monograma je imel
  belo steblo in je na svetli podlagi izginil; Android si ozadje določi sam.

**Chromium ne more brati iz `/tmp`** (isti razlog, kot da tja ne more pisati).
Prva različica ikon je bila zato posnetek njegove strani z napako in je bila
videti kot uspeh — datoteka je obstajala, imela 200 in pravo velikost v bajtih.
Razkril jo je šele enak `md5` dveh različnih ikon. `naredi-ikone.sh` zato po
vsaki sliki preveri **dejansko velikost slike**, ne le obstoja datoteke.

## Namestitev na telefon (PWA)

`static/manifest.webmanifest` je povezan z vseh strani, skupaj z
`apple-touch-icon` (180 px, ker iOS manifesta za ikono ne bere) in
`theme-color` `#0f1115`. Bližnjice v manifestu so vlaki, avtobusi, zemljevid.

**Kaj od tega po `http://` res dela, je izmerjeno, ne domnevano** (3. 9. 2026,
chromium brez zaslona):

| izvor | `isSecureContext` | `navigator.serviceWorker` |
|---|---|---|
| `http://127.0.0.1:8001` | `true` | obstaja |
| `http://192.168.1.164:8001` | `false` | **ne obstaja** |

Manifest se kljub temu **prenese tudi po nevarnem izvoru** — v dnevniku
strežnika je `GET /static/manifest.webmanifest` ob nalaganju po omrežnem
naslovu. Zato „dodaj na začetni zaslon" dobi pravo ime in ikono že zdaj;
namestitev kot aplikacija (WebAPK) in delovanje brez omrežja pa ne, ker oboje
visi na varnem kontekstu.

**Service workerja zato (še) ni.** Registrirati se po omrežnem naslovu ne more,
torej bi bil do Tailscale Funnela mrtva koda. Napiše se skupaj s HTTPS, ne prej.
