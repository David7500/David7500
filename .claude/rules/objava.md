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

**Na malini teče izključno zajem, in zajema vse.** `kajros-zajem.service`
(`kajros.cli collect`) je edina omogočena enota; `kajros.service` s
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
