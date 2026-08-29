# sztrack — stanje projekta

Povzetek za nadaljevanje dela. Vse spodaj je preverjeno na živih podatkih,
ne po spominu. Navodila za delo so v [CLAUDE.md](CLAUDE.md), pregled projekta
v [README.md](README.md).

Stanje na dan **2026-08-29**. Veja `claude/slovenske-zeleznice-api-ql84hf`.

## Kaj je narejeno

Delujoča aplikacija, ne več samo zaledje. Iskalnik povezav in odhodna tabla,
okno ene vožnje, stran z ovirami, statistika zajetega, živi zemljevid — vse
s preklopom preprosto / napredno.

Zajem teče v ozadnji niti istega procesa: zamude vsakih 30 s, obvestila
vsakih 60 s, vreme dnevno za nazaj.

## Kaj je odkrilo merjenje

Trije rezultati, ki so spremenili, kaj aplikacija sploh kaže. Vsi so
ponovljivi z ukazom, ne trditev iz spomina.

### 1. Prevoznikova napoved za postanke naprej je slabša od prenosa zamude

`sztrack backtest --operator`, 11 310 nalog iz devetih dni:

| model | MAE | v 5 min | odklon |
|---|---|---|---|
| prenos trenutne zamude | 1,29 min | 94,1 % | −0,48 min |
| prevoznikova napoved | 7,87 min | 58,2 % | −7,85 min |

Vzrok je viden v dnevniku: feed za še nedosežene postanke objavi 0, dokler
nima prave napovedi. V najhujšem rezu — feed pravi 0, vlak pa zamuja ≥ 5 min —
je napaka **18,5 minute** in v petih minutah je le 6 % napovedi.

Prikaz je prej to vrednost postavljal pred lastno oceno. Zdaj je obratno.

### 2. Naš model je že blizu najboljšemu, kar ti podatki dajo

`sztrack backtest`, 258 137 nalog, izpuščanje enega dne:

| model | MAE | v 5 min |
|---|---|---|
| prenos (referenca) | 2,91 min | 82,8 % |
| **vlak (v uporabi)** | **2,00 min** | **90,3 %** |
| odsek | 2,22 min | 88,1 % |
| odsek + razred zamude | 2,26 min | 87,8 % |
| združen (krčenje) | 1,98 min | 89,6 % |

Združevanje po odseku model **poslabša** — na istem tiru se IC in lokalni
vlak ne obnašata enako. Združen model prihrani 1 % MAE in izgubi pri deležu
v petih minutah; ni vredno zapletenosti. Kdor bo pisal nov model, naj se
najprej pomeri s `prenos`.

### 3. Feed vrine ničlo, ki ni res

Pri 14 % postankov z več kot dvema zapisoma se pojavi vzorec X, 0, X v
razmiku ene minute (npr. `1320 · 0 · 1320 · 420 · 0 · 420`). Zamuda med dvema
klicema ne more pasti za več, kot je vmes minilo časa. 45 vrstic v `run` je
zaradi tega trdilo, da je bil vlak točen, čeprav je zamujal pet minut ali več
— prav te vrstice hranijo "delež točnih".

Pravilo je ozko: ničlo po zamudi ≥ 5 min sprejmemo šele ob drugem zaporednem
pollu. `sztrack repair` po istem pravilu znova zgradi `run` iz dnevnika.

## Kaj je bilo spregledano v virih

* **`service_alerts` se ni pobiral.** V njem je ~45 hkrati veljavnih obvestil
  o delih in nadomestnih prevozih, vezanih na `route_id` in s tem na številko
  vlaka. To je edini vir odgovora, **zakaj** vlak zamuja — in pojasni, zakaj
  so zamude v zajetih dneh tako velike (nadomestni prevoz Ljubljana–Logatec in
  Divača–Koper do 12. decembra, zapore enega tira na petih odsekih).
* **`SZ-DELAY` obvestila nosijo ime prometnega mesta**, kjer je zamuda
  izmerjena. `run` pozna samo voznoredne postanke; to je edini vir kraja.
  Vseh 23 poročanih imen se je ujelo s postajo, ki ji poznamo koordinato.
* **Nadomestni prevozi SŽ so v istem zipu** (`route_type = 3`, 56 voženj) in
  jih je uvoz izpuščal. Iskalnik je za Ljubljana–Logatec ponujal dvanajst
  vlakov, ki po obvestilu istega prevoznika ne vozijo.

## Avtobusi

`scripts/vzorci_feeda.py` je čez cel dan vzorčil sestavo obeh RT feedov, ker
ponoči vozi pet vlakov in nič drugega in en sam pogled ne pove ničesar.

**Vse agencije imajo polno realtime pokritost.** Ob 06:42 v soboto je bilo v
`trip_updates` 100 % ali več voženj, ki bi po voznem redu takrat vozile
(Arriva 62, Nomago 54, SŽ 28, LPP 19, AP MS 3). Avtobusi imajo poleg tega
**GPS lego** s smerjo in hitrostjo (do 138 vozil hkrati); vlaki je nimajo.

Uvoženi so **vsi** (`SZ_AGENCIES=1118,1123,1119,1121`): 20 736 voženj,
9 791 postajališč, 403 208 postankov, baza 45 MB, uvoz 14 s z vrhom 217 MB. Odhodna tabla za Bavarski dvor kaže
"LPP 60 → Ljubljana Železna, 09:36 → 09:40, čez 2 min, +4 min" z živo zamudo.
Na zemljevidu je avtobus **puščica v smeri vožnje**, vlak pa krog na postaji —
razlika med izmerjeno lego in zadnjo znano postajo mora ostati vidna.

Kar je bilo treba popraviti, da to ni laž, in kar velja za vsak nadaljnji
prevoznik:

* številka linije ni številka vožnje (LPP 3G ima 388 voženj) — vse gre skozi
  `stats.resolve_trip()`, povezave nosijo `?trip=<id>`;
* barva linije ni barva linije — vsi LPP `route_color` so ista zelena
  prevoznika, zato oznaka nosi tudi ime prevoznika ("LPP 25");
* mestno postajališče ima svoj `stop_id` za vsako smer — iskanje po imenu
  združuje;
* zemljevid je železniški (`?network=zeleznica`), sicer glava šteje 37 vozil,
  riše pa 24;
* **pragova za prestop sta drugačna** (3–30 min proti 6–120): tri minute so
  pri mestni liniji prestop, pri vlaku lovljenje;
* **dnevnik je bilo treba prižgati na prag.** Mestni avtobusi imajo 23,3
  zapisa na postanek proti 1,6 pri vlakih, z mediano spremembe 15 sekund —
  14 000 vrstic na uro za nihanje pod ločljivostjo prikaza. Z minutnim pragom
  504/h, torej 28-krat manj; pri vlakih se ne izgubi nič, ker so vse njihove
  spremembe večkratniki minute. Brez tega bi vlaki + LPP dali ~20 GB na leto.

## Izmerjeno

| | |
|---|---|
| Postaje | 271 (267 železniških + 4 postajališča nadomestnih prevozov) |
| Odseki | 389, od tega 275 elementarnih |
| Elementarna mreža | 1253,8 km (realna slovenska mreža ~1200–1300) |
| Vožnje v voznem redu | 733 vlakov + 56 nadomestnih prevozov |
| Zajeto (lokalno, 2026-08-29) | 69205 meritev, 9 obratovalnih dni, 661 poročil prevoznika |
| Uvoz GTFS | 17 s, vrh 54 MB (pretočno branje `shapes.txt`) |
| Strežnik ob zagonu | 57–60 MB RSS |
| Odziv `/api/*` | vse pod 120 ms; `/api/overview` je najpočasnejši |
| Priložena baza | 1,9 MB |

`trip_id` so med regeneracijami GTFS **stabilni** — po ponovnem uvozu se
vseh 60 409 zajetih meritev še vedno ujema s tripom. Zajema torej ni treba
varovati pred `sztrack update`.

## Objava

**Raspberry Pi** (`david@192.168.1.166`) je **Pi Zero W**: armv6, 427 MB
pomnilnika, eno počasno jedro. Tam teče produkcijski zajem in ga je treba
pustiti teči — malina je gor ves čas, ta računalnik ne. Zamenjava z močnejšim
strojem je odločena; do takrat malina ostane na **stari kodi**, torej brez
obvestil, brez varovala za lažne ničle in brez avtobusov.

Posledica, ki jo je treba imeti v mislih: `alert`, `delay_report` in
`vehicle_now` nastajajo **samo lokalno**. Če ta računalnik ugasne, se ta
zgodovina ne nabira nikjer.

Zajem zamud z maline se prilije brez sudo, ker je baza berljiva za vse:

```bash
ssh david@192.168.1.166 'sqlite3 /var/lib/sztrack/sz.sqlite ".backup /tmp/sz.sqlite"'
scp david@192.168.1.166:/tmp/sz.sqlite /tmp/sz-malina.sqlite
./venv/bin/python -m sztrack.cli merge /tmp/sz-malina.sqlite
./venv/bin/python -m sztrack.cli repair    # malina nima varovala za ničle
```

Namestitev/posodobitev pa mora pognati uporabnik sam (sudo rabi geslo):

```bash
sudo bash deploy/install-rpi.sh && sudo systemctl restart sztrack.service
```

**Pella je bila slepa ulica** — zajem je delal, javni API pa je vračal
Cloudflare 526 na vseh poteh, ker njihov edge ne vzpostavi TLS do izvora.

## Odprto

* **Dostop od zunaj** — Tailscale ali Cloudflare Tunnel.
  **Vrat na usmerjevalniku ne odpiraj: API nima avtentikacije.**
* **Malina.** Na njej je smiselno `SZ_AGENCIES=1118` (SŽ + LPP, vrh 86 MB);
  vseh agencij Pi Zero W s 427 MB ne prenese (vrh 217 MB). Na tem prenosniku
  tečejo vse.
* **Napoved bo boljša šele z več zajema.** Kar se je dalo iztisniti iz devetih
  dni, je iztisnjeno in izmerjeno. Naslednji korak rabi mesece, ne trikov.
* **Vzročnost vremena.** Vreme se zaenkrat samo *pokaže ob* zamudi. Trditve o
  vzroku počakajo na 2–3 mesece zajema, kot je bilo dogovorjeno.
