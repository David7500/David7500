---
paths:
  - "kajros/static/**"
  - "kajros/templates/**"
  - "scripts/preveri_paleto.py"
---
# Kako je zamuda napisana in pobarvana

Velja povsod, kjer se zamuda pokaže: kartica zemljevida, iskalnik, časovnica, postanek potnika.

## Prezgodnja vožnja

* **Avtobus lahko PREZGODEN; vlak v zajetih podatkih nikoli.** Preverjeno znova 4. 9. 2026 na **78 082** železniških vrsticah `run` (prej 45 146): ni niti ene negativne vrednosti, najmanjša natanko 0.

  Avtobusi (**750 935** vrstic): **10,7 %** vsaj minuto prezgodnjih, **3,8 %** vsaj tri; **37,9 % voženj ima vsaj en prezgodnji postanek**.

  | prevoznik | vsaj minuto prej | vrstic |
  |---|---|---|
  | LPP | 21,3 % | 104 780 |
  | Nomago | 9,6 % | 296 293 |
  | Arriva | 8,8 % | 314 621 |
  | AP Murska Sobota | 5,9 % | 39 306 |

  **Vse številke so od prve meritve zdrsnile navzdol** (bilo 12,0 / 4,5 / 41,7 %, LPP 22,6, Nomago 10,6). Smer drži, velikost se z vzorcem spreminja — zato zapisane z vzorcem; kdor jih navaja, naj jih pomeri znova.

  Prikaz je to do zdaj **skrival**: vrstica je pričakovano uro izpisala samo ob `delay_s >= 60`, prezgoden avtobus je kazal zgolj voznoredno uro. Napaka v najslabšo smer — potnik pride ob objavljeni uri, avtobusa ni več. Zdaj prag `abs(delay_s) >= 60`, žeton pove „3 min prej", ne „−3 min": minus pred številko je uganka, beseda ni. Barva ostane siva (res ni zamuda) — zato mora povedati beseda. Pravilo v `common.delayText()`, velja **povsod**: kartica zemljevida, iskalnik vozila, stolpec zamude v časovnici, postanek potnika. Ozki stolpci: kratka oblika („5 prej").

  **V glavi okna vožnje smer nosi naslov, ne enota.** „Trenutna zamuda" nad „6 min prej" si nasprotuje, „Vozi prezgodaj" nad „6 min prej" ponovi besedo. Naslov pove smer, številka velikost: **„Vozi prezgodaj" · „6 min"**.

  Resničnost prezgodnje vrednosti preverjena na LPP 25 (Medvode ↔ Zadobrova). Proti Zadobrovi prezgodnja na Gosposvetski v **vseh 17 zajetih vožnjah**, povprečno −4,4 min, najpozneje −5 s; profil čez progo = lok, ki na obeh koncih izgine (Prušnikova −74 s, Kompas −224, Gosposvetska −265, Kolodvor −73, konec +123). GPS potrdi: 30. 8. ob 12:10:44 vozilo LJ LPP-124 že za postankom z voznim redom 12:13. Ni napaka zajema, ampak **prevelika rezerva voznega reda skozi Šiško** — v nasprotni smeri ista postaja povprečno +370 s. Zajem LPP za zdaj samo vikendski (od 29. 8.); ali velja med tednom, se bo videlo.

## „Izmerjeno" je trditev o dogodku, ne o številki

Beseda = **opažanje**; feed potrdil samo, če je vrednost osvežil **po** trenutku, ki ga trdi prehod (`stats.potrjen_prehod()`). Izmerjeno 9. 9. 2026 na celem dnevu: železnica **0,3 %** postankov (6 od 2 007), avtobusi **69,6 %** (50 166 od 72 076).

Pri vlakih je bila beseda skoraj vedno **sklep iz ure**, ne meritev — dvakrat v dveh dneh poslala potnika s perona, s katerega vlak še ni odpeljal. Zdaj razlika povedana:

| kaj vemo | žeton | stavek |
|---|---|---|
| feed potrdil po prehodu | `izmerjeno` | „vlak je tu že bil" |
| ni potrdil | `zadnji podatek` | „po zadnjem podatku bi bil tu ob 06:53" |

Enako za glavo okna vožnje: „izmerjeno na postaji Blanca" proti „zadnji podatek s postaje Blanca".

**Pravilo je na strežniku, na enem mestu.** `stats.potrjen_prehod()` uporabljajo okno vožnje (`/api/train/{no}/run`), odhodna tabla (`journey.board`) in vse prek `stats.zamuda_na_postanku()` — iskalnik zvez in pot. Straža `preveri_skladnost.py` odslej primerja tudi **besedo**, ne le številk: če se tabla in okno razideta, je pravilo spet napisano dvakrat.

**Kadar sta resnici dve, se pokažeta obe.** Številka za potnikovo postajo je lahko zamrznjena napoved, feed pa je medtem o vožnji povedal nekaj drugega. 9. 9. 2026: pri Polju „+4 min, podatek ob 06:50", za Ljubljano „+15 min ob 07:03" — +15 je bilo **120 s** od resnice, +4 pa **780 s**. Katera drži, se ne da ugotoviti (izmerjeno: prenos poznejše vrednosti nazaj slabši v 921 primerih od 1 662), zato prikaz **ne izbira**:

> po zadnjem podatku bi bil tu ob 06:53
> novejša beseda o vožnji: **+15 min** (Ljubljana, 07:03)

Pogoja dva: številka za postanek **ni potrjena** (`zadnji podatek`) in razlika vsaj **5 minut** (`RAZKRIJ_RAZLIKO_S`) — pod tem šum, ne druga resnica. Ime postaje v oklepaju, ker se ga ne da splošno sklanjati.

**Nepotrjen odhod ni odpeljan** (24. 9. 2026). Tabla in iskalnik zvez sta vlak, čim je minila ura po zadnjem podatku, posivila; iskalnik ga je zložil pod „pokaži prejšnje“. Kadar vlak čaka na prejšnji postaji in feed zamude ne osveži, je bil prav ta vlak še na poti. Zdaj strežnik vsaki železniški vrstici doda `nepotrjen_do` (`stats.nepotrjen_do()`, 20 min po pričakovanem odhodu, izmerjeno v `docs/MERITVE.md`); prikaz vrstico med pričakovanim odhodom in to uro pokaže napol prosojno (`is-unconfirmed`, 0,72 — med živo in odpeljano 0,4) z besedo **„po zadnjem podatku bi odpeljal ob 10:10, potrditve ni“**. Ni naslednja, ni med odpeljanimi. Primerjavo z uro naredi odjemalec, ker ura teče tudi med osvežitvama; mejo postavi strežnik. Pristajalni strani je ne kažeta — nimata JS, naslov „Naslednji odhodi“.

**Zakaj ne poskušamo prehoda zaznati bolje.** Pet signalov izmerjenih, vsi odpovejo — podrobnosti v `docs/MERITVE.md`, „Prehoda vlaka se iz teh podatkov ne da ugotoviti". Kar ni mogoče izmeriti, se ne sme trditi.

## Barve zamud

Ordinalni ramp v enem odtenku, validiran na monotonost svetlosti in kontrast:

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

Pravila (obstoječa koda in nova):

* **Vsaka oznaka poleg barve vedno nosi tudi minute.** Barva nikoli sama ne nosi pomena — barvna slepota; +4 proti +14 je za potnika bistvena razlika.
* **Razred iz zaokrožene minute, ne iz sekund.** Meje v `DELAY_RAMP` v minutah, isto zaokroževanje kot `delayLabel`. Prej sekunde (`<= 60` = točno): 60 s pisalo „+1" sivo, 61 s „+1" oranžno — ista številka, dve barvi. Barva ne sme pripovedovati druge zgodbe kot številka poleg nje.

  **Ista past pri „prej".** Prag `s <= -60`, zaokroževanje se prelomi pri −30 s: −45 s izpisalo golo **„−1"** namesto „1 min prej". Pravilo zdaj v `common.isEarly()`, uporabljata ga okno vožnje in iskalnik zvez — en prag, ena zaokrožena minuta.
* **Isto za prestop.** Preostanek pod ničlo pisalo `-1 min za prestop`; zdaj **„zmanjka 1 min“**. Negativna številka = zveza NE drži — potnik mora razumeti brez ugibanja. Ničla ni „0 min za prestop“ (videti kot podatek), ampak **„brez rezerve“**. Pravilo v `connections.prestopText()`.
* **Kar se na zaslonu sešteva, zaokroži enkrat, potem računaj.** Preostali čas za prestop bil `round(dejansko_s)`, poleg `round(načrtovano_s)` in `round(zamuda_s)` — vsaka prav, skupaj „načrtovano 52 min, prvi vlak +5, ostane 48". Bralec sešteje: 47, ima prav. Zdaj preostanek iz **zaokroženih minut** (`preostaliPrestop()`), ne iz sekund. Ista past kot pri razredu zamude.
* **Razred se na strežniku šteje po ISTI zaokroženi minuti kot na zaslonu.** Pravilo popravljeno na odjemalcu, `stats.py` pa razvrščal po sekundah (`v <= 60` = „točno“) — v režo 30–60 s pade **3 280 od 45 015 voženj (7,29 %)**: strežnik jih štel kot sive „točno“, barvna lestvica bi jih pobarvala oranžno „1–5 min“. Zdaj vse skozi `stats._razred_zamude()`.

  **`floor(x + 0.5)`, ne `round()`:** JS `Math.round` zaokroži pol navzgor, Pythonov `round` bančno (`round(0.5) == 0`) → pri natanko 30 s bi se prikaz in izračun razšla.
* **„Točno“ in „delež točnih“ nista isto, ne smeta nositi iste besede.** Žeton `točno` = zaokroženih **nič** minut, `on_time_share` = **pet**. V istem okvirju „točno 81“ in „točnih 69 %“ — 81 od 162 je 50 %, bralec ne more uskladiti. Zato prikaz povsod pove prag: **„72 % v 5 min“**.

  V istem okvirju se morata **sešteti**: prag `ON_TIME_MIN = 5` v **minutah**, ne 300 s. V sekundah, razred „1–5 min“ pa do zaokroženih pet (330 s): 553 voženj (1,23 %) se ni ujelo — v razredu, a ne med točnimi. Zdaj `točno + 1–5 min = izpisani odstotek`, preverjeno v testu.
* Odtenek lestvice **samo tam, kjer pomeni velikost zamude**.
* **Omrežje prestavi samo poudarek, ne lestvice.** `body.net-avtobus` premakne `--accent` na zeleno; `--d-*` ostanejo oranžni tudi tam. Ista barva = ista zamuda povsod — sicer „+5 min“ na avtobusni in železniški strani nista primerljiva. Lestvica validirana na monotonost svetlosti in barvno slepoto; zelena različica bi rabila svojo validacijo in bi trčila s poudarkom.

  **Kar sme biti zeleno, gre skozi `var(--accent)`, nikoli skozi trdo zapisan `#f0934f`.** Koda tega ni držala: `.hist-note strong`, žetona shranjenih poti in zvezdica na iskalniku so bili na avtobusni strani oranžni brez razloga. Trdi izjemi: **legenda omrežij na zemljevidu** (oranžna = vlak, zelena = avtobus, to je njun pomen) in **omrežji v orodni vrstici domače strani** (`.orodna-vlak` proti `.orodna-bus`).
* **Padec zamude na postaji riši vedno, krogec prihoda le, kadar je prostor** (`MIN_SPLIT_PX = 15`). Krogec premer 10 pik, polna pika odhoda 11 — pri manjšem razmiku se prekrijeta, navpičnica med njima izgine pod njima, videti **dva nepovezana krogca**. Prijavljeno pri Divači (+16 → +15, razmik natanko 10 pik).

  Rešitev ni skrivanje: enominutni padec je resničen podatek. Odsek se konča pri **prihodni** vrednosti, navpičnica pade na odhodno — pri majhni razliki stopnica ob piki, bere se; pri veliki (Ljubljana, 170 pik) dobi še krogec. Skrivanje bi izgubilo prav to, zaradi česar je padec narisan.
* Kjer meritve ni (ocena, napoved): rezervirana `#a8d8ff`, lestvica je ne uporablja.
* Vreme ima **svoj semafor**, ne odtenek lestvice zamud.

### Semafor razmer

| stopnja | oznaka | barva |
|---|---|---|
| 0 | mirne | `#6b7480` |
| 1–3 | blage | `#5aa87d` |
| 4–6 | zahtevne | `#d9b33c` |
| 7–10 | hude | `#d1495b` |

Stopnja 0–10 = seštevek točk za padavine, sneg, sunke vetra, meglo, nevihto in mraz (`weather.severity()`). Razčlenitev v tooltip — indeks brez razčlenitve = črna skrinja. Modelska vrednost za celico 8 × 8 km, ne meritev na peronu.

**Žeton nikoli ne pokaže gole stopnje.** „0" potniku ne pove nič — popravljeno prej — a **„1" prav tako ne**: številka brez enote in lestvice je uganka, razlaga v `title`, ki ga na telefonu ni mogoče doseči. Prvi popravek rešil pol težave.

Zato: do vključno **blagih (≤ 3) temperatura** (pove nekaj sama), od **zahtevnih (≥ 4) naprej beseda** („zahtevne", „hude"), ki pove, kaj je narobe. Barva ostane ista lestvica razmer. Besede le tam, kjer je kaj povedati; takih postankov malo, širina ni težava. Žetoni v preprostem pogledu na **postajah naprej po progi** (napoved, črtkan rob); prevožene postaje tam skrite, mirno vreme za nazaj ne pove ničesar.

**Lestvic ne mešaj v istem registru.** Rumena razmer `#d9b33c` proti svetli oranžni zamud `#f2a87e`: pri deutanu ΔE 5,5 — nerazločljivo. Zato zamuda = krivulja s pikami zgoraj, razmere = stolpci v ločenem pasu spodaj, vsak stolpec od stopnje 4 naprej nosi svojo številko. Paleto preverjaj z `scripts/preveri_paleto.py`, ne na oko. Meri kontrast (WCAG), monotonost svetlosti, razločljivost pri barvni slepoti (CIEDE2000 na simulaciji protan/deutan/tritan). Trk obeh lestvic pri tritanu **ΔE 1,6**, hujši od prej zapisanih 5,5 — ločena registra nujna, ne okrasna.


## `[hidden]` je eno pravilo, ne enajst

`display` iz razreda premaga `[hidden]` iz brskalnikovega sloga (avtorski). Past ugriznila vsaj trikrat — vrstica „Drugi prevozniki" ni izginila pri števcu 0, prazen sloj budilke ležal čez vso stran in požiral vsak klik, gumb „pokaži vso pot" viden, preden je bilo kaj pokazati.

Vsakič popravljeno **v svoji datoteki** → isto pravilo zapisano enajstkrat, vsak nov razred z `display` past čakal znova. Odslej v `base.css` eno samo `[hidden] { display: none !important; }`; `!important` ker mora premagati prav razrede, zaradi katerih past nastala. **Novih `X[hidden]` ne dodajaj.**

## Dotik: stran ne sme izdati WebView-a

Prijavljeno 26. 9. 2026: „gumbi so modri, ko klikneš" — Chromov `tap-highlight`. Aplikacija za Android kaže spletno stran, zato se občutek nativnega dela **v CSS**, ne v Kotlinu, in pride na telefon z objavo strežnika, brez novega APK. Vse v razdelku „dotik" v `base.css`:

* **Pritisk = plast v barvi besedila** (`box-shadow: inset … color-mix(currentColor 14%)` na `:active`), kot Materialov „state layer": na temni podlagi posvetli, na oranžni s temnim besedilom potemni. Ne `background`, ker je ta pri gumbih pomen. Element z lastnim `box-shadow` višje specifičnosti (`.net-tab.is-on`) plasti nima — namerno.
* **`:hover` samo v `@media (hover: hover)`**, v vseh datotekah razen `admin.css`. Na dotik obvisi na zadnjem pritisnjenem elementu in vrstica je videti izbrana. Pravilo z vejico (`.x:hover, .x.is-active`) se razcepi, sicer bi na telefonu izgubil tudi `.is-active`. Varuje `tests/test_dotik.py`.
* **`color-scheme: dark`** — brez tega so izbirnik datuma, ure, spustni seznam in drsnik svetli. Posledica: ikona koledarja je zdaj bela, `invert` jo je potemnil; zdaj `opacity`.
* **`accent-color: var(--accent)`** za vsa potrditvena polja (na avtobusni strani zelena), ne več po datotekah.
* Dolg pritisk na povezavo ne označi besedila **samo v aplikaciji** (`.v-aplikaciji`, postavi `common.js` iz `MOST`): v brskalniku je meni „odpri v novem zavihku" koristen. Strani brez `common.js` (besedilne, pristajalne) razreda nimajo.
* **Vleke povezav in slik ni na zaslonu na dotik** (`@media (pointer: coarse)`, `-webkit-user-drag: none`): dolg pritisk je začel vleko z oblačkom „ime · naslov strani" (prijavljeno 26. 9. 2026). Velja za vse strani, tudi brez `common.js`; z miško vleka ostane. Preizkus prek CDP: `Input.setInterceptDrags` + premik z miško; z `setTouchEmulationEnabled` (`pointer: coarse`) dogodka `dragIntercepted` ni, brez njega je.
* Prehod med stranmi `@view-transition` (Chrome/WebView 126+), 0,16 s, izklopljen pri `prefers-reduced-motion`.

Preizkus pritiska: `chromium --headless` z `--virtual-time-budget` ga ne zna; prek CDP `Input.dispatchMouseEvent mousePressed`, nato `getComputedStyle(el).boxShadow`. Dotik (`dispatchTouchEvent`) v brezglavem Chromu `:active` **ne** sproži — izmerjeno, ni napaka CSS.

## Slog: Material 3 (od 26. 9. 2026)

Izbran na domači strani (osnutek G), razširjen na vse strani prek skupnih gradnikov v `base.css`. Pravila:

* **Oznake v stavčni velikosti**, Plex Sans 500, 12,5–14 px — nikjer več razprtih velikih črk (`text-transform: uppercase`, `letter-spacing`), razen v `admin.css`. Te so bile prvi znak „AI videza". Naslovi razdelkov v barvi poudarka (Materialov „list subheader").
* **Zaobljenost** `--r-sm` 8, `--r` 12, `--r-lg` 20, gumbi `--r-pilula`. Prej 5/7/10.
* **Materialove vloge** so spremenljivke (`--m-kont`, `--m-na-kont`, `--m-sek`, `--m-na-sek`, `--m-visoka`, `--m-najvisja`, `--m-obroba`); `body.net-avtobus` jih prestavi na zeleno. Izbrano v segmentnem gumbu = `--m-sek`, ne obroba v poudarku.
* **Polja so zapolnjena** (`--m-visoka`, brez obrobe, 48 px, 16 px pisava), fokus = 2 px poudarka.
* **Brez roba na levi kot poudarka** (`border-left: 3px`) — naslednja vožnja na tabli in v zvezah ima tonsko podlago. Stanje prestopa nosi značka z besedo, ne rob.
* Opozorila (ovire) so tonska rumena (`#2e2811`, besedilo `#f2d36b`), brez obrobe.
* Obvestila kajrosa (`obvestila.py`) so tonska modra (`--m-info`): niso ne zamuda ne ovira prevoznika, povedo, da govorimo mi.
* Zgornja vrstica v barvi strani, brez obrobe.
* **Glavni meni = plavajoča orodna vrstica na dnu** (`_orodna.html`, vključi jo `_nav.html`, domača stran posebej): Domov, Vlaki, Avtobusi, Pot, Zemljevid. Izbrana je pilula z imenom v poudarku, ostale ikona. Vlaki | Avtobusi sta tu **namesto segmentnega gumba v glavi** — izbrana pilula pove omrežje enako na prvi pogled. V glavi ostanejo ovire (samo železnica) in ⋮ za meni Več (`_vec.html`, `strani.md`). Okno vožnje ima izbrano omrežje vožnje (`here`).
  * Kar je pod njo, ima zadnjih `--orodna-prostor` pik praznih: drseče strani spodnji odmik (`.domov`, `.conn-page`, v oknu vožnje `.col` oziroma `.train-body` na telefonu); na zemljevidih jo nosi zemljevid, dvignejo se le gumbi MapLibra in opombe (`.label-note*` nad navedbo vira, sicer se prekrivata).
  * Odprta spodnja plošča zemljevida (z-index 1100) jo pokrije; pri vodenju po pešpoti (`body.vodenje`) je ni. **Vsak modalni sloj mora biti nad 1000**: list budilke je imel 60 in vrstica je pokrila gumb „Nastavi“ (prijava 28. 9. 2026).
  * `view-transition-name: orodna` jo pri prehodu med stranmi pusti na mestu.
  * **Na domači strani je razprta** (1. 10. 2026): Vlaki in Avtobusi kot pilula z imenom v barvi omrežja (`.orodna-omr`), ločilo, Pot, Zemljevid; Domova ni. Namesto dveh velikih gumbov na strani, glej `strani.md`.
  * **Okvir je na vseh straneh enak** (2. 10. 2026): `--orodna-sirina` = `min(380px, 100vw − 24px)`, višina 64, gumbi 48. Pilula z imenom vzame, kolikor rabi, ikone si razdelijo ostanek (`flex: 1 1 0`). Prej se je širina ravnala po imenu izbrane pilule (pri 412 pikah od 292 do 368) in domača je bila višja (76) — vrstica je ob vsakem prehodu skočila, prijavljeno kot neprofesionalno; pri 360 pikah je zemljevidna segla čez rob. Pod 401 piko se skrčijo odmiki pilul, pod 360 ostane v piluli samo ime. **Ne dajaj vrstici višine ali širine po strani.**

## Znak

Ikona aplikacije: **K kot kazalca na številčnici**, siva roka = vozni red, oranžna = resnica (*chronos* proti *kairosu*), po oranžni pelje avtobus. Vir **`static/favicon.svg`** (podlaga in znak v ločenih skupinah); `scripts/naredi-ikone.sh` iz njega naredi PNG, Android ima isto risbo v `ikona_znak.xml` brez prelivov, stisnjeno na 75 %, da oznake ure ostanejo v varni coni adaptivne ikone.

* **V glavi strani je od 2. 10. 2026 ista ikona** (`_znak.html`, makro `znak(px, id)`), ne več monogram K brez podlage (3.–30. 9.): potnik ikono vidi na zaslonu telefona in v zavihku, v aplikaciji je bila druga. Glava 30 px, domača 38, meni Več 52.
* **Pod 48 px brez drobnih oznak ure, črtkane ceste in oken avtobusa** — pri 30 px so manjše od pike in risbo zamažejo. Poti morajo ostati iste kot v `favicon.svg`; varuje `test_znak_je_ista_risba_kot_ikona`.
* **`id` preliva mora biti na strani edinstven** (`<defs>`): glava in meni Več sta na isti strani, meni ima `zv`.
* **Znak na avtobusni strani ne pozeleni več** (monogram je bral `currentColor`). Omrežje pove pilula v orodni vrstici in poudarek strani.
* **V komentarju SVG in XML ni `--`.** Favicon z `--` v komentarju ni veljaven XML, brskalnik ga ne pokaže; aapt gradnjo ustavi.
* Znak mora zdržati **svetlo in temno podlago**. Prvi poskus monograma: belo steblo, na svetli podlagi izginilo; Android si ozadje določi sam.

**Chromium ne more brati iz `/tmp`** (isti razlog, kot da tja ne more pisati). Prva različica ikon zato = posnetek njegove strani z napako, videti kot uspeh — datoteka obstajala, 200, prava velikost v bajtih. Razkril šele enak `md5` dveh različnih ikon. `naredi-ikone.sh` zato po vsaki sliki preveri **dejansko velikost slike**, ne le obstoja datoteke.

## Namestitev na telefon (PWA)

`static/manifest.webmanifest` povezan z vseh strani, skupaj z `apple-touch-icon` (180 px, ker iOS manifesta za ikono ne bere) in `theme-color` `#0f1115`. Bližnjice v manifestu: vlaki, avtobusi, zemljevid.

**Kaj po `http://` res dela: izmerjeno, ne domnevano** (3. 9. 2026, chromium brez zaslona):

| izvor | `isSecureContext` | `navigator.serviceWorker` |
|---|---|---|
| `http://127.0.0.1:8001` | `true` | obstaja |
| `http://192.168.1.164:8001` | `false` | **ne obstaja** |

Manifest se kljub temu **prenese tudi po nevarnem izvoru** — v dnevniku strežnika `GET /static/manifest.webmanifest` ob nalaganju po omrežnem naslovu. Zato „dodaj na začetni zaslon" dobi pravo ime in ikono že zdaj; namestitev kot aplikacija (WebAPK) in delovanje brez omrežja ne, ker oboje visi na varnem kontekstu.

**Service worker tu od 12. 9. 2026**, ker je HTTPS na `kajros.app`. Streže ga `api.sw()` iz predloge `templates/sw.js`, registrira se v `common.js` samo kadar `isSecureContext` — po omrežnem naslovu bi vrgel napako v konzolo, ta pa mora ostati prazna, ker jo `preveri.sh` bere kot merilo.

**Nad njim eno pravilo: `/api/` se ne predpomni nikoli.** Projekt meri zamude, zamuda iz predpomnilnika = laž — najhujša vrsta, ker je videti kot podatek in nosi uro. Potnik, ki bi videl „+2 min“ izpred pol ure, bi zamudil vlak, o katerem misli, da ima čas. Isto za `/admin`: pregled za skrbnika ne sme pustiti sledi na napravi.

Ostalo razdeljeno po tem, kaj se sme postarati:

| kaj | ravnanje | zakaj |
|---|---|---|
| `/static/*` | najprej predpomnilnik | naslov nosi odtis vsebine → nespremenljiv |
| strani orodne vrstice (`/`, `/app/train`, `/app/bus`, `/app/pot`, `/app/map`) | najprej predpomnilnik, v ozadju omrežje | HTML brez številk, vse živo iz `/api/`; čakanje na HTML je bilo pol prehoda (MERITVE, 2. 10. 2026) |
| ostale strani | najprej omrežje, predpomnilnik kot rezerva | vsebujejo tudi številke (pristajalne, okno vožnje z relacijo v naslovu) |
| `/api/*`, `/admin` | delavec se jih ne dotakne | glej zgoraj |
| tuji izvori (ploščice) | delavec se jih ne dotakne | niso naši |

**Na seznam `api._SW_STRANI` sme samo stran, katere HTML ne nosi ničesar iz baze** — sicer bi potnik dobil staro številko iz predpomnilnika. Različica predpomnilnika = **odtis lupine in vseh predlog in statike** (`_odtis_aplikacije()`), ne ročna številka: `sw.js` se ob objavi spremeni sam, brskalnik to zazna kot novega delavca. Ročna številka bi bila prej ali slej pozabljena, obiskovalci bi dobivali staro aplikacijo. Naslovi statike nosijo odtis, zato se stari vnosi ne povozijo, ampak kopičijo — ob novi različici gredo vsi ven naenkrat.

`/brez-omrezja` **namerno ne ponudi zadnjih znanih zamud.** Stran se pokaže v predoru in dvigalu, natanko kjer je stara številka videti sveža.

**Preverjeno z ugasnjenim strežnikom, ne po opisu** (12. 9. 2026): lupina 9 datotek, offline stran shranjena, **`/api/` v nobenem predpomnilniku (0 vnosov)**, že obiskana stran se postreže iz predpomnilnika, nikoli obiskana dobi „brez zveze“.

**Headless chromium z `--virtual-time-budget` delavca ne požene.** `register()` se ne razreši v nobeno smer — virtualni čas ne teče v nitih service workerja. Preizkus zato teče brez njega, dogodek `load` se zakasni s počasnim odgovorom iz začasnega strežnika. Brez tega je videti, kot da registracija tiho odpove.

## Ovire: kaj velja danes in kaj šele pozneje

`alerts.for_train()` filtrira samo `end_ts >= zdaj`, ne `start_ts <= zdaj` — **namerno**: nadomestni prevoz, ki se začne v petek, je za potnika, ki gleda četrtkov vlak, uporabna vest.

Brez datuma zavajajoče. Izmerjeno 4. 9. 2026: od 62 shranjenih ovir **16 veljavnih, 32 še nezačetih** (5.–19. 9.). Na LPV 2250 okno vožnje pisalo „Obvestila o ovirah na tej poti — 7“, od tega štiri začele šele 7.–19. 9.

Zato dvoje:

* vsaka ovira, ki se še ni začela, nosi **„velja od D. M.“** (`alert-later`, barva `--sev-hard`);
* **naslov razčleni števec** — „— 3 zdaj, 4 pozneje“ namesto „— 7“. Škatla zaprta, kadar jih je več kot dve, torej natanko ko je razlika največja in je ni videti.

Isto pravilo kot povsod: številka mora pomeniti tisto, kar bralec misli, da pomeni.

**Možna dodatna zamuda** (`zapore.py`, 5. 10. 2026): zapora tira na poti ali vlak pred njim, ki je tam izgubil čas. V oknu vožnje odprta škatla nad obvestili, na tabli in v iskalniku rumena vrstica (`.opozorilo`, `common.opozorilaVrsticeHtml`), zapore v eni vrstici. Imena postaj v imenovalniku („odsek Zagorje – Sava“). Številka zamude se zaradi opozorila ne spremeni.

## „v živo" je tretja vrsta številke, poleg meritve in ocene

Mestni LPP ima od 7. 9. 2026 na oknu vožnje **prevoznikovo živo napoved** (`zamuda.vrsta === "živo"`, iz `data.lpp.si`, osvežena na 10–30 s). Piše se `LPP v živo · čez N min`, prednost pred našo oceno — ne ker bi bila načelno boljša, ampak ker je pri mestnem LPP **naša zgodovina zgrajena iz napovedi**: feed pošlje samo postanke pred vozilom, zato v `run` meritve nikoli ni. Naša ocena ostane vidna v naprednem pogledu za primerjavo.

Meritve ta številka **ne prepiše nikoli** — pogoj `stop_seq > meja`.

Popravljena navedba vira: pod mestnim LPP je pisalo „IJPP prek NAP", česar tam ni. Zdaj `viriHtml()` pove „LPP (avl.lpp.si), obdelava DERP" in doda „živi prihodi data.lpp.si", kadar so res uporabljeni.

## Tir

Tir s table SŽ (`peroni.py`) = `tirHtml()` v `common.js`: ploščica „tir 6-A“ ob imenu postaje (okno vožnje), prva v vrstici pod odhodom (tabla, neposredna zveza) in v vrstici prestopa kot „tir 3 → tir 1“. **Ne ob imenih postaj v nogah prestopa** — na 375 px potisnil cilj izven vrstice.

Sprememba čez dan z besedo (`tir 7-A · prej 6-A`), barva `--sev-hard` samo poudarek. Kadar tira ni (postaja ga pri SŽ nima, vir obstal): nič — ne „tir ?“, ne ugibanje iz zgodovine.
