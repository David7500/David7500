---
paths:
  - "deploy/**"
  - "scripts/**"
---

# Objava in malina

## Objava

Ciljni gostitelj je Raspberry Pi doma: **`david@192.168.1.166`**. Tam ob
koncu teče produkcijski zajem — malina je gor ves čas, ta računalnik ne, zato
je merodajna baza na malini in se z nje vleče (`kajros merge`), ne obratno.

Namestitev/posodobitev: `sudo bash deploy/install-rpi.sh && sudo systemctl
restart kajros.service` (idempotentna; restart je nujen posebej, `enable --now`
aktivne storitve ne restarta). Podrobnosti v [DEPLOY.md](DEPLOY.md).

**Deploy mora pognati uporabnik sam** — `david` na malini za sudo rabi geslo,
agent nima terminala zanj. `sudo -n true` lahko uspe, a le zaradi predpomnjene
sudo-znamke po uporabnikovem lastnem ukazu; NOPASSWD velja samo za
`/usr/bin/tee /sys/class/leds/…`. Pripravi ukaz in ga daj uporabniku, ne
poskušaj sam.

Pella je bila slepa ulica — zajem je delal, javni API pa je vračal Cloudflare
526 na vseh poteh, ker njihov edge ne vzpostavi TLS do izvora.

**Na malini teče izključno zajem, in zajema vse.** Tako je zamišljeno in tako
je tudi v resnici — le da je enota **še vedno `sztrack-zajem.service`**
(`sztrack.cli collect`), ker preimenovalna namestitev tam še ni bila pognana;
po njej bo to `kajros-zajem.service`. `kajros.service` s
strežnikom je `disabled` in tak ostane — hkrati ne smeta teči, ker bi pisali
v isto bazo in se prepirali za feed (`install-rpi.sh` drugo sam ugasne).
`KAJROS_AGENCIES=1118,1119,1121,1123`: meritev, ki je ta trenutek nihče ne
posname, ne obstaja nikoli več, malina pa je edina naprava, ki teče ves čas.

**Senčno merjenje na malini ne teče** (`KAJROS_OCENA=0` v enoti). `ocena.tick()`
je v isti zanki kot zajem, ne v svoji niti: en obhod je na razvojnem računalniku
141 ms, malina pa je pri istem poslu ~100× počasnejša (SQLite v pomnilniku
88,7 s proti 0,90 s), torej **~14 s vsakih 120**. Naslednji zajem bi se za
toliko zamaknil — natanko drift, ki je v `docs/MERITVE.md` že zapisan kot
napaka. Posledica, ki jo je treba imeti v mislih: **senca se polni samo, ko
teče strežnik na tem računalniku**, zato dva tedna sence nista dva koledarska
tedna. Ob prehodu na Pi 4B/5 (obhod ~1,4 s) to premisli znova.

Da zajem ni preveč za Pi Zero W, je izmerjeno **na njem**: 427 MB RAM in
**426 MB swapa**, v rabi 122 + 11. Zajem sam je pri sami železnici **38 MB
RSS**; vrh ob uvozu voznega reda je pri vseh štirih agencijah ~216 MB in teče
v podprocesu, zato se po njem vrne sistemu. Na kartici je 20 GB prostega,
dnevnik `obs` pa se obrezuje in se ustali pri ~356 MB. Prejšnji komentar v
enoti je trdil, da malina vseh agencij *ne* prenese — zapisan je bil brez
swapa v računu.

**Prilitje: `./scripts/potegni.sh`.** Naredi dosledno kopijo (`backup()`, ne
golo kopiranje — baza je v WAL in `kajros.sqlite` sam po sebi nima zadnjih
zapisov), jo prenese, preveri s `PRAGMA quick_check`, prilije z `merge` in
požene `repair`, ker malina teče starejšo kodo in prilite meritve niso šle
skozi novejše varovalke. Izpiše, koliko je pribilo.

Smer je ena sama in to ni okus: 31. 8. je imel ta računalnik 4 645 železniških
meritev, malina pa 6 912. Prilitje je idempotentno — `obs` je ključen po
`(trip_id, service_date, stop_seq, feed_ts)`, zato se podvojene meritve tiho
zavržejo in skripto je varno pognati večkrat na dan. Tudi `repair` je
idempotenten; preverjeno s tremi zaporednimi zagoni (0, 0, 0 popravkov).

**Koda na malini ni iz gita.** `install-rpi.sh` privzeto klonira z GitHuba, kjer
naših commitov ni — zagon brez `KAJROS_SRC` bi malino torej **nazadoval**. Zato se
drevo najprej prenese (`rsync` v `~/kajros-src`), installer pa se požene od
tam.


## Varnostna kopija zgodovine

`./scripts/varnostna-kopija.sh` nese **celotno zgodovino** na malino kot
`git bundle`. Potisk na GitHub rabi ključ, ki ga nimamo, malina pa je imela
samo delovno drevo brez `.git` — 3. 9. 2026 je **196 commitov obstajalo le na
razvojnem disku**.

Sveženj ni razlika, ampak popolna kopija, zato jih hranimo pet zadnjih.
Obnovitev: `git clone kajros-YYYYMMDD-HHMM.bundle kajros`.

**Preizkušeno, ne domnevano:** sveženj (23 MB) je bil prenesen nazaj in
kloniran — 197 commitov, tri veje, koda na mestu. Kopija, ki je nisi poskusil
obnoviti, ni kopija.


## Dostop od zunaj: `kajros.app`

Domena je registrirana 3. 9. 2026 pri name.comu. Zaenkrat je parkirana
(`91.195.240.94`) in **HTTPS ne dela** (`curl https://kajros.app` da `000`).
Ker je `.app` na HSTS preload seznamu, brskalnik http sploh ne poskusi —
chromium vrne prazen DOM. Za to domeno torej ni delne rešitve: ali HTTPS ali
nič.

**Tailscale Funnel odpade in to je izmerjeno, ne domnevano.** Dokumentacija
pravi: „Funnel can only use DNS names in your tailnet's domain
(`tailnet-name.ts.net`)." Funnel je bil izbran prav zato, ker da HTTPS **brez
domene**; ko domena obstaja, ta razlog izgine.

**Pot je imenovani Cloudflarov tunel, ne hitri.** Prejšnji zapis je zavrnil
*hitri* tunel (naključen naslov, umre s procesom) — imenovani tega nima.

**Cona mora biti na Cloudflaru.** Njihova dokumentacija trdi, da CNAME lahko
stoji pri kateremkoli ponudniku; to je **narobe** in preverjeno je:
`example.cfargotunnel.com` razreši v `fd10:aec2:5dae::`, naslov iz zasebnega
razpona `fd00::/8`, ki po internetu ne gre. Zapis mora biti v Cloudflarovi
coni in proksiran, sicer kaže v nič. Torej: imenske strežnike na name.comu
prestavi na Cloudflarove.

**Javna izpostavitev ne odpre pisanja.** V `api.py` ni nobene poti razen
`GET` in nobenega pisanja v bazo iz zahteve; `delay_report` polni `alerts.py`
iz feeda. To se ujema z odločitvijo „endpointi so odprti". Tunel tudi ne
odpre vrat na usmerjevalniku in skrije domači naslov — nasprotno od
preusmeritve vrat.

**Odprto vprašanje: kateri stroj streže.** Merodajen zajem je malina (Pi
Zero W), a je počasna (obhod `ocena.tick()` 88,7 s proti 0,90 s na razvojnem
računalniku). Javni promet nanjo brez predpomnjenja na Cloudflarovem robu ni
premišljen.

## Trije stroji: malina, prenosnik, razvoj

Od 3. 9. 2026 stroji niso več dva:

| stroj | naslov | vloga |
|---|---|---|
| malina (`raspberrypi`, Pi Zero W) | `192.168.1.166` | zajem, teče ves čas, **varovalo** |
| prenosnik (`arwen`, x86_64) | `192.168.1.138` | **strežnik za `kajros.app`** + svoj zajem |
| ta računalnik | — | razvoj |

**Prenosnik zajema sam, ne vleče sproti z maline.** Prikaz mora biti živ, poteg
pa je star toliko, kolikor je star zadnji poteg. Ko prenosnik nekaj časa ne
teče, se vrzel zapolni — prilitje je idempotentno (`obs` je ključen po
`(trip_id, service_date, stop_seq, feed_ts)`), zato ne podvaja.

**Za to NE služi `scripts/potegni.sh`, ampak `deploy/zapolni-vrzel.sh`.**
Prvi je za razvojni računalnik in na prenosniku ne more teči; to je bilo tu
najprej zapisano kot rešitev, ne da bi bilo preizkušeno, in preizkus je
pokazal **tri** ovire hkrati:

* `potegni.sh` kliče `./venv/bin/python`, ki ga v `~/kajros` ni (rsync ga
  izpušča); nameščeni je `/opt/kajros/.venv/bin/python`;
* `david` ne sme pisati v `/var/lib/kajros/kajros.sqlite` — lastnik je
  sistemski uporabnik `kajros`, zato gre prilitje skozi `sudo -u kajros`;
* s prenosnika **ni ključa do maline**.

Zadnje je **enkratna nastavitev, ki jo naredi David** (skript jo izpiše, če
manjka): `ssh-keygen -t ed25519` in `ssh-copy-id david@192.168.1.166`.
Agent tega ne naredi sam — vpis tujega ključa med pooblaščene je poseg v
stroj, ne konfiguracija aplikacije.

**Malina zato ostane prižgana.** Dva zajema pomenita dva vira, a to je namen:
prenosnik se zapira in seli, malina ne. Kdor ju kdaj združi v enega, naj ve,
da s tem izgubi varovalo.

Prenosnik je za to primeren tako, kot malina ni: 7,8 GB pomnilnika proti 427 MB
in x86_64 proti armv6l. Senčno merjenje (`KAJROS_OCENA`) sme tam teči — na
malini je ugasnjeno, ker bi en obhod vzel 88,7 s od vsakih 120.

**Koda je na prenosniku v `/home/david/kajros`** (izvorno drevo za
`KAJROS_SRC=`), nameščena pa v `/opt/kajros` z bazo v `/var/lib/kajros`, tako
kot na malini. Osveži se z `rsync` z razvojnega računalnika, ker commiti
pogosto še niso na GitHubu.

**Nastavitev pokrova pusti pri miru.** Prenosnik ob zaprtju zaspi in strežnik
z njim; skušnjava je nastaviti `HandleLidSwitch=ignore` v
`/etc/systemd/logind.conf`. **Ne.** Bilo je narejeno 3. 9. 2026 in takoj
vrnjeno na privzeto: David pazi sam, da ostane odprt, vrzel po morebitnem
spanju pa zapolni `scripts/potegni.sh` z maline — prav zato malina teče.

Splošneje: **stroj ni naš.** Namestitev sme postaviti svojo aplikacijo in
svoje enote, ne sme pa spreminjati, kako se stroj vede do lastnika. Kar
namestitev vseeno spremeni zunaj sebe, mora biti našteto in povedano:
paketi (`python3-venv`, `python3-pip`, `sqlite3`, `git`), sistemski
uporabnik `kajros`, štiri enote v `/etc/systemd/system/` in `enable --now`
za `kajros.service` ter `kajros-backup.timer`.

**Stanje maline, preverjeno 7. 9. 2026** (ne po spominu — vse iz `systemctl`
in `ls` na njej):

| kaj | vrednost |
|---|---|
| koda | `/opt/sztrack`, stara, pod starim imenom |
| enota | `sztrack-zajem.service`, aktivna, uporabnik `sztrack` |
| baza | `/var/lib/sztrack/sz.sqlite` — **683 MB** + 23 MB WAL |
| kopije | `sztrack-backup.timer` dnevno ~03:20, hrani 3, `.sqlite.gz` |
| prevozniki | `SZ_AGENCIES=1118,1119,1121,1123` |
| disk | 28 G, 19 G prosto |

`kajros.service` in `kajros-zajem.service` na malini ne obstajata. Selitev v
`install-rpi.sh` je napisana in preverjena z branjem: ustavi in onemogoči
`sztrack-zajem`, prestavi `sz.sqlite` → `/var/lib/kajros/kajros.sqlite`,
namesti nove enote. Rabi sudo, torej jo požene David.

**Dvoje, kar je treba vedeti pred to selitvijo:**

* **Malina ne zajema mestnega LPP** — stara koda zastavice `KAJROS_LPP` nima.
  Nova jo ima in je **privzeto vklopljena**, kar pomeni še 42 MB GTFS na Pi
  Zero W. Ali to prenese, **ni izmerjeno**; do takrat naj gre v enoto
  `KAJROS_LPP=0`.
* **Poizvedb na malini ne poganjaj.** `SELECT COUNT(*) FROM run` čez 683 MB
  tam preseže 120 s. Analiza gre na kopijo, ne na izvirnik.


## Dostop od zunaj: samo Cloudflare

**Eno orodje za oboje.** Prvi predlog je bil Cloudflarov tunel za serviranje
in Tailscale za upravljanje; to je bilo odveč in je bilo opuščeno 4. 9. 2026.
Isti imenovani tunel zmore oboje:

| naloga | kako |
|---|---|
| javno streči `kajros.app` | `cloudflared` → `localhost:8000` |
| ssh s telefona od zunaj | druga gostiteljica (npr. `ssh.kajros.app`) → `ssh://localhost:22`, za **Access** |

**Na telefonu ni treba ničesar.** Cloudflare ima *brskalniški SSH terminal*:
po njihovi dokumentaciji rabi `cloudflared` na strežniku in Access, na
odjemalcu pa „no SSH client or Cloudflare One Client required“. Ocenjen čas
postavitve je 20–30 min — več kot `tailscale up`, a en račun namesto dveh.

**Access ni nadloga, ampak pogoj.** SSH na javni gostiteljici brez njega bi
bil odprt vsem; Access pred njim zahteva prijavo (npr. koda na e-pošto).
Cena: tunel je brezplačen brez omejitev, Zero Trust do 50 uporabnikov
brezplačno (iz sekundarnih virov, Cloudflarove cenike ni bilo mogoče
prebrati — preveri ob postavitvi).

Skript na prenosniku (`/home/david/posodobi.sh`), narejen za rabo s telefona —
en ukaz, eno geslo: namesti kodo iz `~/kajros` in preveri `/api/health`.
Kodo tja osveži razvojni računalnik z `rsync`; skript izpiše, kateri commit
nameša, da se stara koda ne namesti tiho.

**Kaj se da od zunaj in kaj ne.** Prestavitev imenskih strežnikov je spletni
obrazec in ne rabi domačega omrežja. Vse, kar rabi `sudo` na strojih, rabi
pot do njih — dokler tunela ni, to pomeni biti doma.

## Kar Cloudflare stori brez vprašanja

**Ponovni zagon strežnika stane 1,3 s, ne več.** Izmerjeno 6. 9. 2026 iz
journala: `Stopping` → `Started` je **163 ms**, proces streže 1,25 s pozneje.
Prva meritev je govorila o 11,5 s in je bila napačna — sonda je dobivala 403
od Cloudflara, ne od nas, in to tudi dve sekundi *pred* restartom.

**Cloudflare vrne 403 odjemalcu z UA `Python-urllib`.** Koda 1010,
„banned your access based on your browser's signature" — to je *Browser
Integrity Check*, na brezplačnem paketu privzeto vklopljen. Zavaja, ker ne
blokira botov na splošno: `curl`, `Wget`, `python-requests`, lastni UA in
celo zahteva **brez** UA dobijo 200. Blokiran je natanko podpis Pythonove
standardne knjižnice — torej odjemalec, s katerim bi naše odprte podatke
prebral nekdo brez odvisnosti.

To je v nasprotju z odločitvijo „endpointi so odprti". Popravi se v nadzorni
plošči (Security → Settings → Browser Integrity Check, ali pravilo WAF s
`skip` za `/api/*`); iz kode se ne da.

**Rob povozi tudi `Cache-Control`.** Strežnik pošilja `no-cache`, Cloudflare
pa privzeto `max-age=14400`. Zato imajo naslovi statike odtis vsebine
(`api.s()`); nastavitev „Respect Existing Headers" bi delovala enako, a bi
bila nevidna in bi jo naslednja objava spet zasenčila.
