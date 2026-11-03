---
paths:
  - "deploy/**"
  - "scripts/**"
---
# Objava in malina

## Trije stroji

**Malina od 3. 11. 2026 ni več del projekta** (David). Spodnje o malini je ostanek do pospravka 6. 11. (`KOLEDAR.md`): ne preverjaj, ne nameščaj, ne predlagaj.

| stroj | naslov | vloga |
|---|---|---|
| malina (`raspberrypi`, Pi Zero W) | `192.168.1.166` | zajem ves čas, **varovalo**, brez vlakov |
| arwen (prenosnik, x86_64) | `192.168.1.46` | **strežnik `kajros.app`** (port 8000, cloudflared) + svoj zajem, edini z vlaki |
| ta računalnik | — | razvoj |

Dva zajema = dva vira, namenoma: arwen se zapira, malina ne. Ne združuj.

## Objava na arwen = `git push`

```bash
git push arwen claude/slovenske-zeleznice-api-ql84hf
```

`~/kajros` na arwenu = repozitorij z `receive.denyCurrentBranch = updateInstead`; `post-receive` (povezava na `deploy/post-receive`) požene `deploy/posodobi.sh` (izpiše commit, prepiše v `/opt/kajros`, `systemctl restart` z `NOPASSWD`, počaka na `/api/health`). Izpis pride nazaj. **Objavi se samo odjavljena veja**, druge se le shranijo. Baza `/var/lib/kajros`. **Nova vrsta povzetka**: do konca izračuna ob zagonu strani, ki jo berejo, visijo (`stats.summary_get` čaka `_SUMMARY_LOCK`), Cloudflare po 125 s vrne 524; ostalo spletišče normalno (statistika 29. 10. 2026: 16 min). Po potisku počakaj na 200, preden trdiš, da dela. Enkratna nastavitev: `ssh david@192.168.1.46 'bash -s' < deploy/arwen-git.sh` (po prvem potisku še enkrat za kavelj).

**Česar potisk ne prinese** (enkrat ali redko na arwenu):
* **OSRM in tiri**: `ssh david@192.168.1.46 'cd ~/kajros && deploy/osrm.sh'` — peš `:5000`, avtobus `:5001`, tir `:5002`, `/var/lib/kajros/tiri.json`; nato `sudo systemctl restart kajros.service` (brez gesla). **Slike ne vleci mimo skripte** (podatki vezani na različico; vleče le `znova`).
* **Chrome in Xvfb** (s sudo, David vpiše geslo — odpri ptyxis): `ssh -t david@192.168.1.46 'sudo bash ~/kajros/deploy/brskalnik.sh'`. Google Chrome (AppArmor `/etc/apparmor.d/chrome`; Chromium bi bil snap), preizkus `kajros brskalnik` v peskovniku storitve, šele nato restart.
* **Kazalo naslovov** (`naslovi.sqlite`, 51 MB): `ssh david@192.168.1.46 'cd ~/kajros && deploy/naslovi.sh'` (docker brez sudota).
* Prijava NAP `deploy/nap.sh`, žeton Ko-fi `deploy/kofi.sh`, žeton admin `deploy/zeton.sh`.

**Ne spreminjaj, kako se stroj vede do lastnika**: `HandleLidSwitch` ostane privzet (David pazi pokrov; vrzel zapolni malina). Kar namestitev spremeni zunaj sebe, mora biti našteto: paketi (`python3-venv`, `python3-pip`, `sqlite3`, `git`), uporabnik `kajros`, enote v `/etc/systemd/system/`.

## Malina

* **Deploy požene David** (`sudo` z geslom; `NOPASSWD` le za `/usr/bin/tee /sys/class/leds/…`). `sudo -n true` lahko uspe zaradi `timestamp_type=global` po njegovem ukazu — ne poskušaj sam. Pripravi ukaz.
* Namestitev: `sudo bash deploy/install-rpi.sh && sudo systemctl restart kajros.service` (idempotentna). **Nikoli brez `KAJROS_SRC`** — privzeto klonira z GitHuba, kjer naših commitov ni → malina nazaduje. Drevo najprej z `rsync` v `~/kajros-koda`.
* **Malina streže samo zajem** — deploy predlagaj le ob spremembi zajema: `git diff --name-only <zadnje> -- kajros/collector.py kajros/gtfs.py kajros/alerts.py kajros/db.py`.
* Enota `kajros-zajem.service` (`kajros.service` = `disabled`, hkrati ne smeta teči). `KAJROS_AGENCIES=1118,1119,1121,1123`, mestni LPP vklopljen.
* **`KAJROS_OCENA=0`**: `ocena.tick()` v zajemni zanki bi na malini vzel ~14 s od 120. Senca se polni samo na arwenu.
* Zmogljivost izmerjena na njej: 427 MB RAM + 426 MB swapa; zajem 38 MB RSS, uvoz ~216 MB v podprocesu.
* **Poizvedb na malini ne poganjaj** (`COUNT(*)` čez `run` > 120 s) — analiza na kopiji. **Pred `.backup` ustavi pisca** (sicer se začne znova).
* Domača mapa: `~/kajros-koda`, `~/kajros-zgodovina`. `deploy/pospravi-malino.sh` za stare enote.

## Vleka baze

* **Razvoj: `./scripts/potegni.sh`** — `backup()` (WAL!), prenos, `PRAGMA quick_check`, `merge`, `repair`. Smer ena: z maline sem. Idempotentno (`obs` ključen po `(trip_id, service_date, stop_seq, feed_ts)`).
* **Arwen: `deploy/zapolni-vrzel.sh`**, ne `potegni.sh` (`/opt/kajros/.venv/bin/python`, `sudo -u kajros`). Rabi ključ arwen → malina: `ssh-keygen -t ed25519` in `ssh-copy-id david@192.168.1.166` naredi David.

## Varnostna kopija zgodovine

`./scripts/varnostna-kopija.sh`: `git bundle` na malino, pet zadnjih; obnovitev `git clone kajros-YYYYMMDD-HHMM.bundle kajros` (preizkušeno). Arwen ima vso zgodovino. Ključ za GitHub obstaja (`push --dry-run` dela), a **ne potiskaj brez vprašanja** — koda zaprta.

## Dostop od zunaj: samo Cloudflare

* Imenovani Cloudflarov tunel z arwena (`cloudflared` → `localhost:8000`), cona na Cloudflaru (CNAME na `cfargotunnel.com` drugje kaže v `fd00::/8`). **Vrat na usmerjevalniku ne odpiraj.**
* SSH od zunaj = druga gostiteljica za **Access** (brskalniški terminal); brez Access odprto vsem.
* Pisalne poti: `CLAUDE.md`.

## Kar Cloudflare stori brez vprašanja

* **Rob povozi `Cache-Control`** (`max-age=14400` ob našem `no-cache`) → statika nosi odtis v naslovu (`api.s()`).
* Browser Integrity Check je 6. 9. 2026 vračal 403 (koda 1010) za `Python-urllib`; 12. 9. spet 200. Odprtost endpointov pomeri znova, ko je pomembna.
* Restart strežnika stane 1,3 s; sonda za Cloudflarom lahko meri njegov 403, ne nas.
