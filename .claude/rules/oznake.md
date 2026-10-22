---
paths:
  - "kajros/static/**"
  - "kajros/templates/**"
  - "scripts/preveri_paleto.py"
---
# Kako je zamuda napisana in pobarvana

Velja povsod, kjer se zamuda pokaže: kartica zemljevida, iskalnik, časovnica, postanek potnika.

## Prezgodnja vožnja

* **Avtobus je lahko PREZGODEN, vlak nikoli** (78 082 železniških vrstic, najmanjša 0). Avtobusi: 10,7 % vrstic ≥ 1 min prej, 37,9 % voženj vsaj en prezgodnji postanek (LPP 21,3 %, Nomago 9,6, Arriva 8,8, AP MS 5,9). Številke zdrsnejo z vzorcem — meri znova.
* Prag `abs(delay_s) >= 60`; žeton **„3 min prej“**, ne „−3 min“ (minus = uganka). Barva siva, zato beseda. `common.delayText()`, povsod; ozki stolpci „5 prej“.
* Glava okna: smer nosi naslov, številka velikost — **„Vozi prezgodaj“ · „6 min“**.
* Vzrok je prevelika rezerva voznega reda (LPP 25 Gosposvetska −4,4 min v 17 od 17, GPS potrdi).

## „Izmerjeno“ je trditev o dogodku

Beseda velja le, kadar je feed vrednost osvežil **po** trenutku prehoda (`stats.potrjen_prehod()`): železnica 0,3 % postankov, avtobusi 69,6 %.

| kaj vemo | žeton | stavek |
|---|---|---|
| feed potrdil po prehodu | `izmerjeno` | „vlak je tu že bil“ |
| ni potrdil | `zadnji podatek` | „po zadnjem podatku bi bil tu ob 06:53“ |

Glava: „izmerjeno na postaji Blanca“ / „zadnji podatek s postaje Blanca“. Pravilo na strežniku (`/api/train/{no}/run`, `journey.board`, `stats.zamuda_na_postanku()`); `preveri_skladnost.py` primerja tudi besedo.

* **Dve resnici → pokažeta se obe** (prikaz ne izbira; prenos nazaj slabši v 921 od 1 662), ko je številka `zadnji podatek` in razlika ≥ 5 min (`RAZKRIJ_RAZLIKO_S`):
  > po zadnjem podatku bi bil tu ob 06:53
  > novejša beseda o vožnji: **+15 min** (Ljubljana, 07:03)
* **Nepotrjen odhod ni odpeljan**: `nepotrjen_do` (`stats.nepotrjen_do()`, 20 min po pričakovanem); vrstica `is-unconfirmed` (0,72) z **„po zadnjem podatku bi odpeljal ob 10:10, potrditve ni“**. Ni naslednja, ni odpeljana. Primerja odjemalec, mejo postavi strežnik. Pristajalne ne.
* Prehoda bolje ne zaznavamo — pet signalov odpove (`docs/MERITVE.md`).

## Barve zamud

| razred | svetla | temna |
|---|---|---|
| točno | `#8a8175` | `#7c8698` |
| 1–5 min | `#f0934f` | `#f2a87e` |
| 5–15 min | `#dd6a26` | `#e07b45` |
| nad 15 min | `#a83f10` | `#b85417` |

* **Oznaka poleg barve vedno nosi minute.**
* **Razred iz zaokrožene minute** (`DELAY_RAMP` v minutah; prej 60 s sivo, 61 s oranžno). Isto za „prej“: `common.isEarly()`.
* Prestop: pod ničlo **„zmanjka 1 min“**, ničla **„brez rezerve“** (`connections.prestopText()`).
* **Ura ob zamudi = vozni red + zaokrožena minuta žetona** (`stats.ura_z_zamudo`, odjemalec `pricakovanaUra`). `actual_arr`/`actual_dep` ostaneta na sekundo (ločita „izmerjeno“). Straža v `preveri_skladnost.py`.
* **Zaokroži enkrat, potem računaj** (`preostaliPrestop()` iz zaokroženih minut).
* Strežnik razvršča po isti minuti (`stats._razred_zamude()`). **`floor(x + 0.5)`, ne `round()`** (Python bančno).
* **„Točno“ ≠ „delež točnih“**: žeton = 0 min, `on_time_share` = 5 → povsod **„72 % v 5 min“**. `ON_TIME_MIN = 5` v minutah, da se `točno + 1–5 min` sešteje (test).
* Odtenek lestvice samo za velikost zamude.
* **Omrežje prestavi samo poudarek**: `body.net-avtobus` → `--accent` zelen, `--d-*` ostanejo. **Kar sme biti zeleno, gre skozi `var(--accent)`**, nikoli `#f0934f`. Trdi izjemi: legenda omrežij na zemljevidu, `.orodna-vlak` / `.orodna-bus`.
* **Padec zamude na postaji riši vedno, krogec prihoda le pri razmiku ≥ `MIN_SPLIT_PX` (15)**.
* Ocena/napoved: rezervirana `#a8d8ff`.
* Vreme ima svoj semafor.

### Semafor razmer

| stopnja | oznaka | barva |
|---|---|---|
| 0 | mirne | `#6b7480` |
| 1–3 | blage | `#5aa87d` |
| 4–6 | zahtevne | `#d9b33c` |
| 7–10 | hude | `#d1495b` |

`weather.severity()` (padavine, sneg, sunki, megla, nevihta, mraz), razčlenitev v tooltip; model za celico 8 × 8 km. **Žeton nikoli gole stopnje**: do blagih temperatura, od zahtevnih beseda. Žetoni le na postajah naprej (črtkan rob).

**Lestvic ne mešaj v istem registru** (rumena razmer proti oranžni zamud pri tritanu ΔE 1,6): zamuda = krivulja zgoraj, razmere = stolpci v ločenem pasu, od stopnje 4 s številko. Paleta s `scripts/preveri_paleto.py` (WCAG, monotonost, CIEDE2000 na protan/deutan/tritan), ne na oko.

## `[hidden]` je eno pravilo

`display` iz razreda premaga `[hidden]`. V `base.css` eno `[hidden] { display: none !important; }`. **Novih `X[hidden]` ne dodajaj.**

## Dotik: stran ne sme izdati WebView-a

Ureja se v CSS (razdelek „dotik“ v `base.css`), pride z objavo strežnika:
* **Pritisk = plast v barvi besedila** (`box-shadow: inset … color-mix(currentColor 14%)` na `:active`), ne `background`.
* **`:hover` samo v `@media (hover: hover)`** (razen `admin.css`); pravilo z vejico se razcepi. `tests/test_dotik.py`.
* **`color-scheme: dark`** (ikona koledarja `opacity`, ne `invert`).
* `accent-color: var(--accent)`.
* Dolg pritisk ne označi besedila **samo v aplikaciji** (`.v-aplikaciji` iz `common.js` po `MOST`).
* Brez vleke povezav in slik pri `@media (pointer: coarse)` (`-webkit-user-drag: none`).
* `@view-transition` 0,16 s, izklop pri `prefers-reduced-motion`.

Preizkus pritiska prek CDP `Input.dispatchMouseEvent mousePressed` + `getComputedStyle(el).boxShadow`; `dispatchTouchEvent` v brezglavem `:active` ne sproži.

## Slog: Material 3 (od 26. 9. 2026)

* **Oznake v stavčni velikosti**, Plex Sans 500, 12,5–14 px — nikjer `text-transform: uppercase`/`letter-spacing` (razen `admin.css`). Naslovi razdelkov v poudarku.
* Zaobljenost `--r-sm` 8, `--r` 12, `--r-lg` 20, gumbi `--r-pilula`.
* Vloge: `--m-kont`, `--m-na-kont`, `--m-sek`, `--m-na-sek`, `--m-visoka`, `--m-najvisja`, `--m-obroba`; `body.net-avtobus` jih prestavi. Izbrano v segmentnem = `--m-sek`.
* Polja zapolnjena (`--m-visoka`, 48 px, 16 px pisava), fokus 2 px poudarka.
* **Modra `#2f7fff` = ti**: pika, obroč, znak kartice „Pokaži, kje si“, ikona žetona „Najbližje“. Ni v nobeni lestvici in ne v poudarku omrežja.
* **Brez `border-left` kot poudarka** — tonska podlaga, stanje prestopa z značko.
* Ovire tonsko rumene (`#2e2811`, `#f2d36b`); obvestila kajrosa tonsko modra (`--m-info`).
* Zgornja vrstica v barvi strani, brez obrobe.
* **Plavajoča orodna vrstica** (`_orodna.html` prek `_nav.html`): Domov, Vlaki, Avtobusi, Pot, Zemljevid; izbrana pilula z imenom. V glavi ovire in ⋮ (`_vec.html`). Okno vožnje: omrežje vožnje (`here`).
  * Pod njo `--orodna-prostor` praznih (`.domov`, `.conn-page`, `.col`/`.train-body`); na zemljevidih se dvignejo le gumbi MapLibra in `.label-note*`.
  * **Vsak modalni sloj nad z-index 1000** (spodnja plošča 1100); pri `body.vodenje` je ni.
  * `view-transition-name: orodna`.
  * **Odprta tipkovnica jo skrije** (`html.tipkovnica`, `common.js`): aplikacija (`adjustResize`) in Firefox okno skrčita, vrstica je skočila nad tipkovnico. Pogoj: polje za vnos ima fokus **in** okno ≥ `TIPKOVNICA_PX` (150) nižje od najvišjega pri isti širini. Chrome okna ne skrči — tam vrstica že ostane pod tipkovnico.
  * Na domači razprta (`.orodna-omr`).
  * **Okvir povsod enak**: `--orodna-sirina` = `min(380px, 100vw − 24px)`, višina 64, gumbi 48; pilula po potrebi, ikone `flex: 1 1 0`. Pod 401 px manjši odmiki, pod 360 samo ime. **Ne dajaj vrstici višine ali širine po strani.**

## Znak

**K kot kazalca na številčnici**: siva = vozni red, oranžna = resnica, po oranžni avtobus. Vir `static/favicon.svg`; `scripts/naredi-ikone.sh` → PNG (preveri **dejansko velikost slike** — chromium ne bere iz `/tmp` in je slikal napako); Android `ikona_znak.xml` brez prelivov, 75 %.
* V glavi ista ikona (`_znak.html`, `znak(px, id)`): glava 30 px, domača 38, meni 52.
* Pod 48 px brez drobnih oznak; poti iste kot v `favicon.svg` (`test_znak_je_ista_risba_kot_ikona`).
* `id` preliva edinstven na strani (meni ima `zv`).
* Znak ne pozeleni.
* **V komentarju SVG in XML ni `--`.**
* Zdrži svetlo in temno podlago.

## PWA in service worker

`static/manifest.webmanifest`, `apple-touch-icon` 180 px, `theme-color` `#0f1115`; bližnjice vlaki, avtobusi, zemljevid. Po `http://192.168.…` `isSecureContext = false`, `navigator.serviceWorker` ni (manifest se prenese).

Service worker (`api.sw()` iz `templates/sw.js`), registracija v `common.js` samo ob `isSecureContext` (konzola mora biti prazna za `preveri.sh`).

**`/api/` se ne predpomni nikoli** (zamuda iz predpomnilnika = laž z uro); tudi `/admin` ne.

| kaj | ravnanje | zakaj |
|---|---|---|
| `/static/*` | najprej predpomnilnik | naslov nosi odtis |
| strani orodne vrstice (`/`, `/app/train`, `/app/bus`, `/app/pot`, `/app/map`) | predpomnilnik, v ozadju omrežje | HTML brez številk |
| ostale strani | najprej omrežje | nosijo številke |
| `/api/*`, `/admin` | ne dotakne se | glej zgoraj |
| tuji izvori | ne dotakne se | niso naši |

* **`api._SW_STRANI` samo strani brez česarkoli iz baze.**
* Različica = odtis lupine, predlog in statike (`_odtis_aplikacije()`), ne ročna številka.
* `/brez-omrezja` namerno brez zadnjih zamud.
* Headless z `--virtual-time-budget` delavca ne požene — preizkus brez njega.

## Ovire na oknu vožnje

`alerts.for_train()` filtrira `end_ts >= zdaj` (namerno tudi prihodnje). Še nezačeta nosi **„velja od D. M.“** (`alert-later`, `--sev-hard`); naslov razčleni „— 3 zdaj, 4 pozneje“.

**Možna dodatna zamuda** (`zapore.py`): v oknu odprta škatla nad obvestili, na tabli in v iskalniku `.opozorilo` (`common.opozorilaVrsticeHtml`); imena v imenovalniku („odsek Zagorje – Sava“). Številka ostane; pod njo „lahko do +41“ (`.stop-do`, `.conn-do`), rumeno — meja, ne zamuda.

## „v živo“ = tretja vrsta številke

Mestni LPP: `zamuda.vrsta === "živo"` iz `data.lpp.si` („LPP v živo · čez N min“), prednost pred našo oceno (naša zgodovina LPP je iz napovedi). Meritve ne prepiše nikoli (`stop_seq > meja`). `viriHtml()`: „LPP (avl.lpp.si), obdelava DERP“ + „živi prihodi data.lpp.si“.

## Tir

`tirHtml()` v `common.js`: „tir 6-A“ ob imenu postaje, prva v vrstici pod odhodom, pri prestopu „tir 3 → tir 1“. **Ne ob imenih v nogah prestopa** (375 px). Sprememba „tir 7-A · prej 6-A“ (`--sev-hard`). Brez tira nič — ne „tir ?“.
