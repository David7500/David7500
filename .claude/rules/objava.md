---
paths:
  - "deploy/**"
  - "scripts/**"
---
# Objava

## Dva stroja

**Malina od 3. 11. 2026 ni več del projekta** (David); skripte in navodila zanjo so šli ven 7. 11. Ne preverjaj, ne nameščaj, ne vleci.

| stroj | naslov | vloga |
|---|---|---|
| arwen (prenosnik, x86_64) | `192.168.1.46` | **strežnik `kajros.app`** (port 8000, cloudflared) + **edini zajem** |
| ta računalnik | — | razvoj |

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

**Ne spreminjaj, kako se stroj vede do lastnika**: `HandleLidSwitch` ostane privzet (David pazi pokrov). Kar namestitev spremeni zunaj sebe, mora biti našteto: paketi (`python3-venv`, `python3-pip`, `sqlite3`, `git`), uporabnik `kajros`, enote v `/etc/systemd/system/`.

## Kopija baze za razvoj

Za razvoj in analizo (backtest, senca, modeli) kopija z arwena; v `data/` je ne prilivaj, če ne rabiš (skupna razvojna baza). Postopek (~3 min za `VACUUM INTO`, scp ~8 min za 3 GB):

1. Na arwenu iz bralnega pogleda, nizka prednost, v ozadju (preizkušeno 7. 11. 2026 na majhni bazi): `echo "VACUUM INTO '/var/tmp/kajros-analiza.sqlite';" | ssh david@192.168.1.46 'cat > /var/tmp/vi.sql'`, nato `ssh david@192.168.1.46 'setsid nohup sh -c "nice -n 19 ionice -c3 sqlite3 "file:/var/lib/kajros/kajros.sqlite?mode=ro" < /var/tmp/vi.sql" > /var/tmp/vi.log 2>&1 &'`.
2. Ko je `sqlite3` v `ps` izginil in je `vi.log` prazen: `scp david@192.168.1.46:/var/tmp/kajros-analiza.sqlite <scratchpad>/`.
3. **Na arwenu pobriši** `/var/tmp/kajros-analiza.sqlite`, `vi.sql`, `vi.log` (disk je skupen z zajemom).

* **`.backup` ne dela**: zajem piše vsakih 30 s, kopija se začne znova. `VACUUM INTO` je ena bralna transakcija.
* Samo železnica (268 MB namesto 4,3 GB): v KOPIJI na arwenu `DELETE` vrstic `obs`/`run`/`sched`/`trip`, ki niso `network='zeleznica'`, in `napoved` z drugim omrežjem, `VACUUM`, šele nato scp.
* Scratchpad je v `/tmp` = tmpfs 16 GB: drži eno kopijo. `pkill -f` ujame tudi lastno lupino.
* **Težke poizvedbe na produkcijski bazi ne poganjaj** (`COUNT(*)` čez `run` je drag): najprej izvleci vrstice v `/var/tmp/….sqlite` na arwenu. Nikoli pisanja v `/var/lib/kajros/kajros.sqlite`.
* Prilitje kopije v drugo bazo: `./venv/bin/python -m kajros.cli merge <kopija>` in `repair` (`obs` ključen po `(trip_id, service_date, stop_seq, feed_ts)`, idempotentno).

## Zgodovina kode

Arwen `~/kajros` ima ob vsakem `git push arwen` vso zgodovino (901 commitov, 7. 11. 2026): to je druga kopija poleg razvojnega diska. Ključ za GitHub obstaja (`push --dry-run` dela), a **ne potiskaj brez vprašanja** — koda zaprta.

## Dostop od zunaj: samo Cloudflare

* Imenovani Cloudflarov tunel z arwena (`cloudflared` → `localhost:8000`), cona na Cloudflaru (CNAME na `cfargotunnel.com` drugje kaže v `fd00::/8`). **Vrat na usmerjevalniku ne odpiraj.**
* SSH od zunaj = druga gostiteljica za **Access** (brskalniški terminal); brez Access odprto vsem.
* Pisalne poti: `CLAUDE.md`.

## Kar Cloudflare stori brez vprašanja

* **Rob povozi `Cache-Control`** (`max-age=14400` ob našem `no-cache`) → statika nosi odtis v naslovu (`api.s()`).
* Browser Integrity Check je 6. 9. 2026 vračal 403 (koda 1010) za `Python-urllib`; 12. 9. spet 200. Odprtost endpointov pomeri znova, ko je pomembna.
* Restart strežnika stane 1,3 s; sonda za Cloudflarom lahko meri njegov 403, ne nas.
