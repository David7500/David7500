---
paths:
  - "deploy/**"
  - "scripts/**"
---
# Objava in malina

## Objava na arwen je potisk, ne rsync (17. 9. 2026)

`kajros.app` streže **arwen** (`david@192.168.1.46`, port 8000, cloudflared). Objava:

```bash
git push arwen claude/slovenske-zeleznice-api-ql84hf
```

`~/kajros` na arwenu = navaden repozitorij z `receive.denyCurrentBranch = updateInstead` → potisk posodobi tudi delovno drevo; `post-receive` (simbolna povezava na `deploy/post-receive` v drevesu) požene `deploy/posodobi.sh`. Izpis, vključno s čakanjem na `/api/health`, pride nazaj potiskajočemu.

**Objavi se samo veja, ki je na strežniku odjavljena.** Vsaka druga se shrani, ne objavi — veja za poskus ne sme po nesreči pristati na `kajros.app`.

Zakaj zamenjuje `rsync`: ta je pisal **mimo gita** → delovno drevo na strežniku novejše od svojega HEAD (ob prehodu 17. 9. 2026 `git status` tam: sedem spremenjenih in tri neizsledene datoteke, HEAD tri commite zadaj). Katera koda teče, se je dalo ugotoviti samo po datotekah. Tisto stanje ni zavrženo, ampak v `git stash` (`git -C ~/kajros stash list`).

Enkratna nastavitev: `deploy/arwen-git.sh`, gre po cevi, ker je treba skripto dobiti na strežnik, preden je tam koda:

```bash
ssh david@192.168.1.46 'bash -s' < deploy/arwen-git.sh
```

Pri **prvem** zagonu kavlja ni mogoče postaviti (datoteke v drevesu še ni); skripto poženi znova po prvem potisku. Drugi zagon = prazen tek.

**Malina je druga zgodba**, ostane pri sudotu z geslom — glej spodaj.

**Kazalo naslovov ni v gitu, potisk ga ne prinese** (`naslovi.sqlite`, 51 MB, 23. 9. 2026). Na arwenu se zgradi enkrat, nato nekajkrat na leto: `ssh david@192.168.1.46 'cd ~/kajros && deploy/naslovi.sh'` (docker brez sudota, kot `osrm.sh`; piše v `/var/lib/kajros`, skupinsko pisljiv). Brez njega stran dela, le naslova ni mogoče vpisati — samo postajo.

## Objava

Ciljni gostitelj: Raspberry Pi doma, **`david@192.168.1.166`**. Tam teče produkcijski zajem — malina gor ves čas, ta računalnik ne → merodajna baza na malini, z nje se vleče (`kajros merge`), ne obratno.

Namestitev/posodobitev: `sudo bash deploy/install-rpi.sh && sudo systemctl restart kajros.service` (idempotentna; restart nujen posebej, `enable --now` aktivne storitve ne restarta). Podrobnosti v [DEPLOY.md](DEPLOY.md).

**Deploy mora pognati uporabnik sam** — `david` na malini za sudo rabi geslo, agent nima terminala zanj. `sudo -n true` lahko uspe, a le zaradi predpomnjene sudo-znamke po uporabnikovem lastnem ukazu; NOPASSWD velja samo za `/usr/bin/tee /sys/class/leds/…`. Pripravi ukaz, daj uporabniku, ne poskušaj sam.

Pella = slepa ulica — zajem je delal, javni API pa je vračal Cloudflare 526 na vseh poteh, ker njihov edge ne vzpostavi TLS do izvora.

**Malina ostane, kakor je** (odločeno 17. 9. 2026). Tam teče starejša koda, ni zaostanek za nadoknaditi: malina streže **samo zajem** → sprememba v `kajros/static`, `templates` ali `android` nima učinka. Deploy tja predlagaj **samo**, kadar se je res spremenil zajem — `collector.py`, `gtfs.py`, `alerts.py` ali `db.py`. Preveri z `git diff --name-only <zadnje> -- kajros/collector.py kajros/gtfs.py kajros/alerts.py kajros/db.py`, ne na občutek.

**Na malini teče izključno zajem, in zajema vse.** Enota je **še vedno `sztrack-zajem.service`** (`sztrack.cli collect`), ker preimenovalna namestitev tam še ni bila pognana; po njej `kajros-zajem.service`. `kajros.service` s strežnikom = `disabled`, tak ostane — hkrati ne smeta teči: pisala bi v isto bazo in se prepirala za feed (`install-rpi.sh` drugo sam ugasne). `KAJROS_AGENCIES=1118,1119,1121,1123`: meritev, ki je ta trenutek nihče ne posname, ne obstaja nikoli več, malina pa je edina naprava, ki teče ves čas.

**Senčno merjenje na malini ne teče** (`KAJROS_OCENA=0` v enoti). `ocena.tick()` je v isti zanki kot zajem, ne v svoji niti: obhod na razvojnem računalniku 141 ms, malina ~100× počasnejša (SQLite v pomnilniku 88,7 s proti 0,90 s) → **~14 s vsakih 120**. Naslednji zajem bi se zamaknil za toliko — drift, ki je v `docs/MERITVE.md` že zapisan kot napaka. Posledica: **senca se polni samo, ko teče strežnik na tem računalniku** → dva tedna sence ≠ dva koledarska tedna. Ob prehodu na Pi 4B/5 (obhod ~1,4 s) premisli znova.

Da zajem ni preveč za Pi Zero W, izmerjeno **na njem**: 427 MB RAM in **426 MB swapa**, v rabi 122 + 11. Zajem sam pri sami železnici **38 MB RSS**; vrh ob uvozu voznega reda pri vseh štirih agencijah ~216 MB, teče v podprocesu → po njem se vrne sistemu. Na kartici 20 GB prostega, dnevnik `obs` se obrezuje, ustali pri ~356 MB. Prejšnji komentar v enoti je trdil, da malina vseh agencij *ne* prenese — zapisan brez swapa v računu.

**Prilitje: `./scripts/potegni.sh`.** Naredi dosledno kopijo (`backup()`, ne golo kopiranje — baza v WAL, `kajros.sqlite` sam nima zadnjih zapisov), jo prenese, preveri s `PRAGMA quick_check`, prilije z `merge`, požene `repair` (malina teče starejšo kodo, prilite meritve niso šle skozi novejše varovalke). Izpiše, koliko je pribilo.

Smer je ena sama, ni okus: 31. 8. je imel ta računalnik 4 645 železniških meritev, malina 6 912. Prilitje idempotentno — `obs` ključen po `(trip_id, service_date, stop_seq, feed_ts)` → podvojene meritve tiho zavržene, skripto varno pognati večkrat na dan. Tudi `repair` idempotenten; preverjeno s tremi zaporednimi zagoni (0, 0, 0 popravkov).

**Koda na malini ni iz gita.** `install-rpi.sh` privzeto klonira z GitHuba, kjer naših commitov ni → zagon brez `KAJROS_SRC` bi malino **nazadoval**. Zato se drevo najprej prenese (`rsync` v `~/kajros-src`), installer se požene od tam.


## Varnostna kopija zgodovine

`./scripts/varnostna-kopija.sh` nese **celotno zgodovino** na malino kot `git bundle`. Malina je imela samo delovno drevo brez `.git` —
3. 9. 2026: **196 commitov le na razvojnem disku**.

Od 17. 9. 2026 več kopij: **arwen ima vso zgodovino** (`~/kajros` = cilj potiska, ne rsynca).

**Trditev „potisk na GitHub rabi ključ, ki ga nimamo" ne drži več.** Izmerjeno
17. 9. 2026: `git push --dry-run origin <veja>` se poveže in javi `781eb9c..2600f82` → potisk bi delal. Ni dokaz, da je potisk pravi ukrep — koda zaprta, na GitHub gre samo, če David tako reče — je pa dokaz, da ključ obstaja. **Ne potiskaj brez vprašanja.**

Sveženj = popolna kopija, ne razlika → hranimo pet zadnjih. Obnovitev: `git clone kajros-YYYYMMDD-HHMM.bundle kajros`.

**Preizkušeno, ne domnevano:** sveženj (23 MB) prenesen nazaj in kloniran — 197 commitov, tri veje, koda na mestu. Kopija, ki je nisi poskusil obnoviti, ni kopija.

## Dostop od zunaj: `kajros.app`

Domena registrirana 3. 9. 2026 pri name.comu. Zaenkrat parkirana (`91.195.240.94`), **HTTPS ne dela** (`curl https://kajros.app` da `000`). `.app` na HSTS preload seznamu → brskalnik http sploh ne poskusi; chromium vrne prazen DOM. Delne rešitve ni: HTTPS ali nič.

**Tailscale Funnel odpade — izmerjeno, ne domnevano.** Dokumentacija: „Funnel can only use DNS names in your tailnet's domain (`tailnet-name.ts.net`)." Funnel izbran, ker da HTTPS **brez domene**; z domeno razlog izgine.

**Pot = imenovani Cloudflarov tunel, ne hitri.** Prejšnji zapis zavrnil *hitri* tunel (naključen naslov, umre s procesom) — imenovani tega nima.

**Cona mora biti na Cloudflaru.** Njihova dokumentacija trdi, da CNAME lahko stoji pri kateremkoli ponudniku; **narobe**, preverjeno: `example.cfargotunnel.com` razreši v `fd10:aec2:5dae::`, naslov iz zasebnega razpona `fd00::/8`, po internetu ne gre. Zapis mora biti v Cloudflarovi coni in proksiran, sicer kaže v nič. Torej: imenske strežnike na name.comu prestavi na Cloudflarove.

**Javna izpostavitev je dolgo odpirala samo branje.** V `api.py` nobene poti razen `GET`, nobenega pisanja v bazo iz zahteve; `delay_report` polni `alerts.py` iz feeda. Tunel ne odpre vrat na usmerjevalniku in skrije domači naslov — nasprotno od preusmeritve vrat.

**Od 12. 9. 2026 ne drži več; izjem je zdaj štiri:** `POST /stik` (obrazec za sporočilo), `POST /api/deli` (deljenje lege, 25. 9.) ter za žetonom `POST /admin/sporocila/{id}` (prebrano, brisanje) in `POST /admin/obvestila` (obvestila potnikom, 28. 9.). Vse ostalo ostaja `GET`. Varovalke v modulu, ki piše (`stik.py`, `deljenje.py`, `obvestila.py`), preizkušene v istoimenskih testih; `test_pisalne_poti_so_nastete` pade, če se seznam tiho podaljša — nova pisalna pot mora biti dodana zavestno, ne mimogrede.

**Odprto: kateri stroj streže.** Merodajen zajem = malina (Pi Zero W), a počasna (obhod `ocena.tick()` 88,7 s proti 0,90 s na razvojnem računalniku). Javni promet nanjo brez predpomnjenja na Cloudflarovem robu ni premišljen.

## Trije stroji: malina, prenosnik, razvoj

Od 3. 9. 2026 stroji niso več dva:

| stroj | naslov | vloga |
|---|---|---|
| malina (`raspberrypi`, Pi Zero W) | `192.168.1.166` | zajem, teče ves čas, **varovalo** |
| prenosnik (`arwen`, x86_64) | `192.168.1.46` | **strežnik za `kajros.app`** + svoj zajem |
| ta računalnik | — | razvoj |

**Prenosnik zajema sam, ne vleče sproti z maline.** Prikaz mora biti živ, poteg pa star toliko, kolikor zadnji poteg. Ko prenosnik nekaj časa ne teče, se vrzel zapolni — prilitje idempotentno (`obs` ključen po `(trip_id, service_date, stop_seq, feed_ts)`), ne podvaja.

**Za to NE služi `scripts/potegni.sh`, ampak `deploy/zapolni-vrzel.sh`.** Prvi je za razvojni računalnik, na prenosniku ne more teči; bilo zapisano kot rešitev brez preizkusa, preizkus pokazal **tri** ovire hkrati:

* `potegni.sh` kliče `./venv/bin/python`, ki ga v `~/kajros` ni (rsync ga izpušča); nameščeni: `/opt/kajros/.venv/bin/python`;
* `david` ne sme pisati v `/var/lib/kajros/kajros.sqlite` — lastnik sistemski uporabnik `kajros`, prilitje gre skozi `sudo -u kajros`;
* s prenosnika **ni ključa do maline**.

Zadnje = **enkratna nastavitev, ki jo naredi David** (skript izpiše, če manjka): `ssh-keygen -t ed25519` in `ssh-copy-id david@192.168.1.166`. Agent tega ne naredi sam — vpis tujega ključa med pooblaščene je poseg v stroj, ne konfiguracija aplikacije.

**Malina ostane prižgana.** Dva zajema = dva vira, kar je namen: prenosnik se zapira in seli, malina ne. Kdor ju združi v enega, izgubi varovalo.

Prenosnik primeren, malina ne: 7,8 GB pomnilnika proti 427 MB, x86_64 proti armv6l. Senčno merjenje (`KAJROS_OCENA`) sme tam teči — na malini ugasnjeno, ker bi en obhod vzel 88,7 s od vsakih 120.

**Koda na prenosniku v `/home/david/kajros`** (izvorno drevo za `KAJROS_SRC=`), nameščena v `/opt/kajros` z bazo v `/var/lib/kajros`, kot na malini. Osveži z `rsync` z razvojnega računalnika, ker commiti pogosto še niso na GitHubu.

**Nastavitev pokrova pusti pri miru.** Prenosnik ob zaprtju zaspi in strežnik z njim; skušnjava: `HandleLidSwitch=ignore` v `/etc/systemd/logind.conf`. **Ne.** Narejeno 3. 9. 2026, takoj vrnjeno na privzeto: David pazi sam, da ostane odprt, vrzel po morebitnem spanju zapolni `scripts/potegni.sh` z maline — zato malina teče.

Splošneje: **stroj ni naš.** Namestitev sme postaviti svojo aplikacijo in enote, ne sme spreminjati, kako se stroj vede do lastnika. Kar namestitev vseeno spremeni zunaj sebe, mora biti našteto in povedano: paketi (`python3-venv`, `python3-pip`, `sqlite3`, `git`), sistemski uporabnik `kajros`, štiri enote v `/etc/systemd/system/`, `enable --now` za `kajros.service` in `kajros-backup.timer`.

**Stanje maline PRED selitvijo, 7. 9. 2026** (ne po spominu — vse iz `systemctl` in `ls` na njej):

| kaj | vrednost |
|---|---|
| koda | `/opt/sztrack`, stara, pod starim imenom |
| enota | `sztrack-zajem.service`, aktivna, uporabnik `sztrack` |
| baza | `/var/lib/sztrack/sz.sqlite` — **683 MB** + 23 MB WAL |
| kopije | `sztrack-backup.timer` dnevno ~03:20, hrani 3, `.sqlite.gz` |
| prevozniki | `SZ_AGENCIES=1118,1119,1121,1123` |
| disk | 28 G, 19 G prosto |

`kajros.service` in `kajros-zajem.service` na malini ne obstajata. Selitev v `install-rpi.sh` napisana, preverjena z branjem: ustavi in onemogoči `sztrack-zajem`, prestavi `sz.sqlite` → `/var/lib/kajros/kajros.sqlite`, namesti nove enote. Rabi sudo → požene David.

**Dvoje pred selitvijo:**

* **Malina ne zajema mestnega LPP** — stara koda zastavice `KAJROS_LPP` nima. Nova jo ima, **privzeto vklopljena** → še 42 MB GTFS na Pi Zero W. Ali prenese, **ni izmerjeno**; do takrat v enoto `KAJROS_LPP=0`.
* **Poizvedb na malini ne poganjaj.** `SELECT COUNT(*) FROM run` čez 683 MB tam preseže 120 s. Analiza gre na kopijo, ne na izvirnik.

**Selitev opravljena v noči na 8. 9. 2026**, uspela: `962 951 → 962 951` meritev, `sztrack-zajem` onemogočen, `kajros-zajem` teče, baza na `/var/lib/kajros/kajros.sqlite`. Mestni LPP **vklopljen** — Davidova odločitev: naprava, ki teče ves čas, naj zajema vse.

Naučeno, velja naprej:

* **Pred `.backup` ustavi pisca.** Spletna kopija se ob vsakem pisanju v izvorno bazo začne znova; z živim zajemom se 683 MB ne konča nikoli. Prvi poskus 17 minut stal pri 190 MB, videti kot počasen stroj.
* **`sudo` ima na malini `timestamp_type=global`** — ko David enkrat vpiše geslo, velja tudi za agentovo sejo, dokler ne poteče.
* **Domača mapa zdaj čista**: `~/kajros-koda` (koda za namestitev) in `~/kajros-zgodovina` (git bundle + stari posnetki baze). Vse podvojene kopije odstranjene.
* `deploy/pospravi-malino.sh` odstrani stare enote in `/opt/sztrack`, nastavi časovni pas; noče se pognati, dokler selitev ni dokazano uspela.

## Dostop od zunaj: samo Cloudflare

**Eno orodje za oboje.** Prvi predlog: Cloudflarov tunel za serviranje + Tailscale za upravljanje; odveč, opuščeno 4. 9. 2026. Isti imenovani tunel zmore oboje:

| naloga | kako |
|---|---|
| javno streči `kajros.app` | `cloudflared` → `localhost:8000` |
| ssh s telefona od zunaj | druga gostiteljica (npr. `ssh.kajros.app`) → `ssh://localhost:22`, za **Access** |

**Na telefonu ni treba ničesar.** Cloudflare ima *brskalniški SSH terminal*: po dokumentaciji rabi `cloudflared` na strežniku in Access, na odjemalcu „no SSH client or Cloudflare One Client required“. Ocenjen čas postavitve 20–30 min — več kot `tailscale up`, a en račun namesto dveh.

**Access = pogoj, ne nadloga.** SSH na javni gostiteljici brez njega odprt vsem; Access pred njim zahteva prijavo (npr. koda na e-pošto). Cena: tunel brezplačen brez omejitev, Zero Trust do 50 uporabnikov brezplačno (iz sekundarnih virov, Cloudflarovih cenikov ni bilo mogoče prebrati — preveri ob postavitvi).

Posodobitev prenosnika = **`~/kajros/deploy/posodobi.sh`**: izpiše nameščeni commit, prepiše kodo v `/opt/kajros`, `systemctl restart` (eden od štirih ukazov z `NOPASSWD`), počaka na `/api/health`. Kodo v `~/kajros` osveži razvojni računalnik z `rsync`; izpis commita je zato, da se stara koda ne namesti tiho.

**Starega `/home/david/posodobi.sh` ni več** (odstranjen 12. 9. 2026). Nastal pred `brez-sudo.sh`, posodabljal prek `install-rpi.sh`, torej z geslom — po prehodu na lahko pot je objava obtičala na pozivu za geslo, ki ga v seji brez terminala ni mogoče vpisati. Izpis commita, edino vredno v njem, je zdaj v `deploy/posodobi.sh`.

**Kaj se da od zunaj in kaj ne.** Prestavitev imenskih strežnikov = spletni obrazec, ne rabi domačega omrežja. Vse, kar rabi `sudo` na strojih, rabi pot do njih — dokler tunela ni, to pomeni biti doma.

## Kar Cloudflare stori brez vprašanja

**Ponovni zagon strežnika stane 1,3 s, ne več.** Izmerjeno 6. 9. 2026 iz journala: `Stopping` → `Started` **163 ms**, proces streže 1,25 s pozneje. Prva meritev 11,5 s napačna — sonda je dobivala 403 od Cloudflara, ne od nas, tudi dve sekundi *pred* restartom.

**Cloudflare vrne 403 odjemalcu z UA `Python-urllib`.** Koda 1010, „banned your access based on your browser's signature" — *Browser Integrity Check*, na brezplačnem paketu privzeto vklopljen. Zavaja, ker ne blokira botov na splošno: `curl`, `Wget`, `python-requests`, lastni UA in celo zahteva **brez** UA dobijo 200. Blokiran natanko podpis Pythonove standardne knjižnice — odjemalec, s katerim bi naše odprte podatke prebral nekdo brez odvisnosti.

V nasprotju z odločitvijo „endpointi so odprti". Popravek v nadzorni plošči (Security → Settings → Browser Integrity Check, ali pravilo WAF s `skip` za `/api/*`); iz kode se ne da.

**Premerjeno 12. 9. 2026: tega ni več.** `Python-urllib/3.12` dobi na `/api/health` **200**, tako tudi `curl`, `python-requests`, `Wget`. Ni znano, ali je bila nastavitev spremenjena ali jo je Cloudflare umaknil sam — zato ni zaprta zadeva, ampak meritev z datumom. Kdor se zanaša na odprtost endpointov, naj jo pomeri znova; brezplačni paket se spreminja brez najave.

**Rob povozi tudi `Cache-Control`.** Strežnik pošilja `no-cache`, Cloudflare privzeto `max-age=14400`. Zato imajo naslovi statike odtis vsebine (`api.s()`); nastavitev „Respect Existing Headers" bi delovala enako, a bi bila nevidna in bi jo naslednja objava spet zasenčila.
