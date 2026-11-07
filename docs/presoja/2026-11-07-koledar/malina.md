# Malina iz projekta (koledar pet 6. 11., delano sob 7. 11. 2026)

Stanje na začetku: pospravka še ni (po 3. 11. noben commit ne briše skript za malino); koledar je pri tej vrstici točen.
Worktree je bil na "Initial commit" (samo README); vejo sem postavil na `claude/slovenske-zeleznice-api-ql84hf` (f4e0bc3).

## Ali arwen skripte rabi (ssh david@192.168.1.46, samo branje, 7. 11. ~10.30)

* `crontab -l`: prazen. `systemctl list-timers --all`: 17 časovnikov, kajros ima samo `kajros-backup.timer` (naslednji 8. 11. 02:40; kliče `deploy/varnostna-kopija-baze.sh`, ta ostane).
* Naložene enote `kajros*`: `kajros.service` (teče), `kajros-backup.service/.timer`. `kajros-zajem.service` obstaja kot datoteka v `/etc/systemd/system`, `is-enabled` = disabled, `is-active` = inactive (ostanek; ne dotikam se, David lahko `sudo rm`).
* `~/.ssh/known_hosts` na arwenu: 0 zadetkov za 192.168.1.166, `~/.ssh/config` brez maline: ključ arwen -> malina ni bil nikoli postavljen, `zapolni-vrzel.sh` na arwenu ni mogel teči.
* `deploy/posodobi.sh` ne kliče nobene od brisanih skript (komentar "namenoma NI install-rpi.sh").
* grep po scripts/, deploy/, tests/, kajros/, .claude/, android/: noben test ali `preveri.sh` ne kliče potegni.sh, varnostna-kopija.sh, zapolni-vrzel.sh, install-rpi.sh, preseli/pospravi-malino.sh. `KAJROS_MODE` bere samo install-rpi.sh, koda ga ne.
* `scripts/varnostna-kopija.sh` je delal `git bundle` na malino. Arwen `~/kajros` ima po potiskih 901 commitov (`git rev-list --count --all`, vrh 0c5b135) = kopija zgodovine kode brez skripte.

## Odločitve

* Brišem: `deploy/install-rpi.sh`, `preseli-malino.sh`, `pospravi-malino.sh`, `zapolni-vrzel.sh`, `kajros-zajem.service`, `scripts/potegni.sh`, `scripts/varnostna-kopija.sh`.
* `scripts/build_deploy_zip.sh` ostane (zip za gostitelja, `git archive`), le brez navodil za malino.
* potegni.sh ni bil edina pot do podatkov za razvoj: `VACUUM INTO` z arwena (postopek v objava.md). Nova skripta ni potrebna.
* Zgodovinski zapisi (MERITVE.md, KOLEDAR.md Opravljeno, docs/presoja/, javna-postavitev.md, zbiranje-sredstev.md) ostanejo.

## Izid

* Izbrisano 7 datotek: deploy/install-rpi.sh, preseli-malino.sh, pospravi-malino.sh, zapolni-vrzel.sh, kajros-zajem.service, scripts/potegni.sh, varnostna-kopija.sh. Diff: 15 datotek, 46 vrstic dodanih, 173 odstranjenih.
* Prepisano: DEPLOY.md (ostane arwen, varnostne kopije baze, prenos z `merge`, Paket za gostitelja), `.claude/rules/objava.md` (nov razdelek "Kopija baze za razvoj" s postopkom VACUUM INTO, preizkušenim 7. 11. na majhni bazi na arwenu; "Zgodovina kode" = arwen `~/kajros`), CLAUDE.md (dve vrstici), HANDOVER.md, README.md, zajem.md, strezba.md, SKILL preveri-vire, STATISTIKA.md, android omrezje.xml in README (cleartext za 192.168.1.166 gre ven ob naslednji gradnji).
* Ostane namenoma: komentarji v kodi in testih z "na malini ..." kot zgodovinski razlog; docs/javna-postavitev.md in docs/zbiranje-sredstev.md (zapisi odločitev; vrstica 43 omenja potegni.sh), MERITVE.md, KOLEDAR.md Opravljeno, docs/presoja/.
* pytest: 1398 passed (12 s). preveri.sh s KAJROS_DATA_DIR na skupno razvojno bazo: "vse zeleno", izhod 0. Brez KAJROS_DATA_DIR v okolju skripte preveri_skladnost ustvarijo prazno data/ v worktreeju (prvi poskus: 3 PADE, no such table): ni napaka kode.
