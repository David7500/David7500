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

Da to ni preveč za Pi Zero W, je izmerjeno **na njem**: 427 MB RAM in
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
