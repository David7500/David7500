# kajros — stanje projekta

Povzetek za nadaljevanje dela. Vse spodaj je preverjeno na živih podatkih,
ne po spominu. Navodila za delo so v [CLAUDE.md](CLAUDE.md), pregled projekta
v [README.md](README.md).

Posnetek stanja na dan **2026-09-01**. Tekoča pravila so v `CLAUDE.md` in
`.claude/rules/`, izmerjeno stanje v [docs/MERITVE.md](docs/MERITVE.md);
ta zapis je pripoved o poti in se ne posodablja ob vsaki spremembi. Veja `claude/slovenske-zeleznice-api-ql84hf`.

## Kaj je narejeno

Delujoča aplikacija, ne več samo zaledje. Iskalnik povezav in odhodna tabla,
okno ene vožnje, stran z ovirami in živi zemljevid.

Zajem teče v ozadnji niti istega procesa: zamude vsakih 30 s, obvestila
vsakih 60 s, vreme dnevno za nazaj.

## Kaj je odkrilo merjenje

Trije rezultati, ki so spremenili, kaj aplikacija sploh kaže. Vsi so
ponovljivi z ukazom, ne trditev iz spomina.

### 1. Prevoznikova napoved za postanke naprej je slabša od prenosa zamude

`kajros backtest --operator`, 11 310 nalog iz devetih dni:

| model | MAE | v 5 min | odklon |
|---|---|---|---|
| prenos trenutne zamude | 1,29 min | 94,1 % | −0,48 min |
| prevoznikova napoved | 7,87 min | 58,2 % | −7,85 min |

Vzrok je viden v dnevniku: feed za še nedosežene postanke objavi 0, dokler
nima prave napovedi. V najhujšem rezu — feed pravi 0, vlak pa zamuja ≥ 5 min —
je napaka **18,5 minute** in v petih minutah je le 6 % napovedi.

Prikaz je prej to vrednost postavljal pred lastno oceno. Zdaj je obratno.

### 2. Naš model je že blizu najboljšemu, kar ti podatki dajo

`kajros backtest`, izpuščanje enega dne. **Železnica, 4. 9. 2026: 521 781
nalog** (prej 258 137):

| model | MAE | v 5 min |
|---|---|---|
| prenos (referenca) | 3,04 min | 82,3 % |
| **rezerva + razred (v uporabi)** | **2,06 min** | **90,0 %** |
| rezerva + mediana | 2,00 min | 90,5 % |
| vlak | 2,07 min | 90,0 % |
| združen (krčenje) | 2,07 min | 89,6 % |
| odsek + razred zamude | 2,36 min | 87,5 % |
| odsek | 2,37 min | 87,4 % |

**Tu je prej pisalo, da je v uporabi model „vlak“ — to ni držalo.**
`stats.predict()` kliče `_after_slack()` in `delay_bucket()`, torej
**rezerva + razred**. Razlaga, kako je do tega prišlo in kaj je bilo
preizkušeno brez uspeha, je v `.claude/rules/model.md`.

**Pri avtobusih je slika druga**: tam je `združen` boljši od sedanjega
(2,85 proti 2,98 MAE na 6 004 849 nalogah). Zamenjava čaka na dva tedna
sence — glej `docs/MERITVE.md`.

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
pollu. `kajros repair` po istem pravilu znova zgradi `run` iz dnevnika.

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

Uvoženi so **vsi** (`KAJROS_AGENCIES=1118,1123,1119,1121`): 20 736 voženj,
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
  spremembe večkratniki minute.

## Izmerjeno

| | |
|---|---|
Stanje **4. 9. 2026** (prejšnje vrednosti so bile z 29. 8. in so se
premaknile — številke se starajo, zato ob vsaki spremembi popravi datum):

| Postaje (železniška mreža) | 271 |
| Odseki | 389, od tega **268** elementarnih |
| Elementarna mreža | **1140,8 km** (slovensko omrežje ~1209 km, del brez potniškega prometa) |
| Vožnje v voznem redu | 733 vlakov + 56 nadomestnih + **20 061 avtobusnih** |
| Zajeto (lokalno) | **916 452** meritev, 16 obratovalnih dni, 31 863 poročil prevoznika |
| Uvoz GTFS | 17 s, vrh 54 MB (pretočno branje `shapes.txt`) |
| Strežnik | ~215 MB RSS z avtobusi (57–60 MB pri sami železnici) |
| Odziv `/api/*` | `health` 80 ms, `departures` 15 ms, `live` 5 ms, `connections` 40 ms |
| Priložena baza | **4,2 MB** (železniška; z avtobusi bi bila 53 MB, torej več od GTFS zipa) |

**Prej je tu pisalo „vse pod 120 ms“ in to ni držalo:** `/api/health` je delal
1223 ms na klic, `/api/departures` 145 in `/api/live` 245. Vse troje je
popravljeno 4. 9. 2026 — glej `docs/MERITVE.md`, razdelek o hitrosti.

`trip_id` so med regeneracijami GTFS **stabilni, a ne vsi.** Ob prehodu na
šolski vozni red 1. 9. 2026 je iz `trip` izginilo **114 voženj s 3 043
meritvami** (0,37 %); meritve so ostale, a jih ni videla nobena poizvedba, ker
vse gredo skozi `JOIN trip`. Uvoz zato zdaj **obdrži vožnjo, ki ima meritve**,
`kajros merge` jo prinese s seboj in `kajros repair` prešteje osirotele.
Podrobneje v `CLAUDE.md`.

## Objava

**Raspberry Pi** (`david@192.168.1.166`) je **Pi Zero W**: armv6, 427 MB
pomnilnika, 426 MB swapa, eno počasno jedro, 20 GB prostega na kartici.

Od 29. 8. 2026 tam teče **`kajros-zajem.service`** — zajem brez strežnika,
z **vsemi prevozniki** (`KAJROS_AGENCIES=1118,1123,1119,1121`). Namen je, da ima
malina celo bazo za aplikacijo in da lahko razvojni računalnik ugasneš;
obdeluje tisti, ki bazo potegne dol.

Izmerjeno na njej po prehodu: **34 MB RSS**, obremenitev 0,40, 20 003
avtobusnih voženj v voznem redu poleg 733 vlakov, avtobusnih meritev ~34 na
minuto. Obremenitev je enaka kot prej pri samih vlakih, ker je feed drseče
okno: naenkrat vozi ~150 voženj ne glede na velikost voznega reda.

Pravilo, ki to vodi: **zajema se samo tisto, česar kasneje ni mogoče dobiti.**
Zamude in obvestila da; vreme ne (Open-Meteo ima arhiv za nazaj), statistika
ne (izpeljanka `run`), lega vozil ne (je samo „zdaj" in se ne hrani).

Namestitev:

```bash
sudo KAJROS_MODE=zajem KAJROS_AGENCIES=1118,1123,1119,1121 bash ~/kajros-src/deploy/install-rpi.sh
```

Skripta sama ugotovi, da leži v izvornem drevesu, in vzame kodo od tam — na
GitHubu teh commitov ni. Ob spremembi `KAJROS_AGENCIES` sproži ponovni uvoz
voznega reda z `--force`; ta zamenja samo statične tabele, `obs` in `run`
ostaneta (preverjeno: 9 dni in 46 085 meritev je prehod preživelo).

Paket zgradi `./scripts/build_deploy_zip.sh` (`git archive HEAD`) in prekopiraj
z `scp` v `~/`, nato `unzip -o ~/kajros-deploy.zip -d ~/kajros-src`.

Zajem zamud z maline se prilije brez sudo, ker je baza berljiva za vse:

```bash
ssh david@192.168.1.166 'sqlite3 /var/lib/kajros/kajros.sqlite ".backup /tmp/kajros.sqlite"'
scp david@192.168.1.166:/tmp/kajros.sqlite /tmp/sz-malina.sqlite
./venv/bin/python -m kajros.cli merge /tmp/sz-malina.sqlite
./venv/bin/python -m kajros.cli repair    # malina nima varovala za ničle
```

Namestitev/posodobitev pa mora pognati uporabnik sam (sudo rabi geslo):

```bash
sudo bash deploy/install-rpi.sh && sudo systemctl restart kajros.service
```

**Pella je bila slepa ulica** — zajem je delal, javni API pa je vračal
Cloudflare 526 na vseh poteh, ker njihov edge ne vzpostavi TLS do izvora.

## Hitrost pri velikih podatkih

Vprašanje ni bilo prostor (3,4 GB na leto ni nič), ampak ali bo aplikacija
ob letu zajema še uporabna. Izmerjeno na sintetični bazi s **52 122 000
vrsticami `run`** (365 dni vseh prevoznikov, 5,9 GB):

| pot | prej | zdaj |
|---|---|---|
| statistika, razrez 90 dni (avtobusi) | 45,8 s | 0,1 ms |
| zemljevid, obe omrežji | 2,2 s | 460 ms |
| živi seznam, železnica | 504 ms | 20 ms |
| vstopna stran | 340 ms | 29 ms |
| odhodna tabla, prestopi, iskanje | že v redu | 46–145 ms |
| odhodna tabla (znova, 4. 9. 2026) | 145 ms | **15 ms** |
| `/api/health` (znova, 4. 9. 2026) | 1223 ms | **80 ms** |

Trije popravki, vsak z lastnim vzrokom:

1. **Statistika se računa enkrat na dan**, ne ob obisku (tabela `povzetek`,
   3:30, `KAJROS_MAINT_HOUR`). Izmerjeno na pravem zajemu: od tretjega dne naprej
   en nov dan premakne mediano 90-dnevnega okna za 0–1 minuto in delež točnih
   za manj kot odstotno točko. Stran zato pove **čas izračuna** — predpomnjena
   številka brez datuma je laž, ki čaka na priložnost.
2. **Voznoredni okvir vožnje je stolpec** (`trip.start_s` / `trip.end_s`),
   ne grupiranje 403 000 vrstic `sched` ob vsakem klicu. Vožnje, ki se zdaj
   ne morejo voziti, s tem sploh ne pridejo do okenskih funkcij.

   **Isti vzorec je 4. 9. 2026 dobil še dve rabi**, ker je bil isti agregat
   še dvakrat v zahtevi: `trip.first_seq` / `last_seq` za odhodno tablo
   (120 → 7 ms) in predpomnjenje `/api/health` (1223 → 80 ms). Pravilo je
   splošno: **agregat, ki se med zahtevami ne spremeni, ne sodi v zahtevo.**
3. **Manjkal je indeks `trip(route_id)`.** Vsako obvestilo o oviri je bilo
   poln pregled 20 736 voženj.

Pri (2) se je pokazala ena razlika v izpisu in ni bila napaka: **vožnja z
več kot šesturno zamudo ni več na seznamu živih** (`api.MAX_LIVE_DELAY_S`).
Prej je meja veljala samo za včerajšnji prometni dan. Nomagov N6571 je imel
27 060 s (7 h 31 min) enako na vseh 44 postankih vožnje, ki je po voznem redu
vozila ob 04:15 — to je feedova zamenjava prometnega dne, ne avtobus, ki bi
se opoldne še vozil, in na zemljevidu ni imel kaj iskati.

## Odprto

* **Dostop od zunaj — odločeno: samo Cloudflare.** Domena `kajros.app` je
  registrirana 3. 9. 2026. Tailscale Funnel odpade, ker zna samo `*.ts.net`;
  isti imenovani tunel zmore tudi ssh prek brskalnika (za Accessom), zato
  drugo orodje ni potrebno. Čaka na prestavitev imenskih strežnikov na
  Cloudflarove. **Vrat na usmerjevalniku ne odpiraj: API nima avtentikacije**
  — je pa samo za branje (v `api.py` ni poti razen `GET`).
* **Malina.** Na njej je smiselno `KAJROS_AGENCIES=1118` (SŽ + LPP, vrh 86 MB);
  vseh agencij Pi Zero W s 427 MB ne prenese (vrh 217 MB). Na tem prenosniku
  tečejo vse.
* **Napoved bo boljša šele z več zajema.** Kar se je dalo iztisniti iz devetih
  dni, je iztisnjeno in izmerjeno. Naslednji korak rabi mesece, ne trikov.
  Prvi merljiv premik je že tu: pri **avtobusih** je model `združen` boljši od
  sedanjega (2,85 proti 2,98 MAE), ker ima zdaj zgodovino 77 % voženj namesto
  11 %. Zamenjava čaka na dva tedna sence, ne na trik.
* **Vzročnost vremena.** Vreme se zaenkrat samo *pokaže ob* zamudi. Trditve o
  vzroku počakajo na 2–3 mesece zajema, kot je bilo dogovorjeno.
