#!/usr/bin/env bash
# Kdo nas bere, ki ni človek -- občasni pregled enega dne, ne blokada.
#
#   scripts/boti.sh [YYYY-MM-DD]     privzeto danes
#
# Bere produkcijsko bazo na arwenu samo za branje (`sqlite3 -readonly`);
# števci obiska so majhni, kopija baze ni potrebna. Kaj iskati:
#
#  * enkratni z vira po urah -- val obiskovalcev z enim ogledom in Googlom v
#    `Referer`, vsak z drugega naslova (12. 10. 2026: 122 od 18:00, Singapur).
#  * prihod -- država in `Sec-Fetch-Mode` vsakega ogleda z znanega vira;
#    „brez“ ni dokaz (`obisk.nacin_odpiranja()`). Veliko „SI brez“ = pravilo
#    izgublja ljudi; „XX navigate“ iz tuje države = ponarejevalec se je učil.
#  * težki -- ključ (IP + UA, sol dneva) z največ zahtevami. Scraper z enega
#    naslova je ves dan en ključ: tisoč zahtev, ogledov 0, razpon čez noč.
#    Ob polnoči ga nova sol razdeli na dva, ritem (s med zahtevama) ostane.
#  * čas strežnika -- delež, ki ga porabijo nečloveški; meja za blokado je
#    hitrost, ne obstoj robota (ljudje 1--3 %, dnevi s crawlerji 10--19 %).
set -euo pipefail

dan=${1:-$(date +%F)}
[[ $dan =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || { echo "datum je YYYY-MM-DD" >&2; exit 2; }

ssh david@192.168.1.46 'sqlite3 -readonly -header -column /var/lib/kajros/kajros.sqlite' <<SQL
.print '== ljudje in boti'
SELECT SUM(bot=0 AND js>0) ljudi, SUM(bot=1) botov, SUM(bot=0 AND js=0) brez_js,
       SUM(CASE WHEN bot=0 AND js>0 THEN ogledov END) ogledov,
       ROUND(1.0*SUM(CASE WHEN bot=0 AND js>0 THEN ogledov END)/SUM(bot=0 AND js>0), 2) na_osebo,
       SUM(bot=0 AND js>0 AND ogledov=1 AND zahtev<=2) enkratni
FROM obiskovalec WHERE dan='$dan';

.print ''
.print '== enkratni (en ogled, največ dve zahtevi) po uri prvega dotika'
SELECT strftime('%H', prvi_s, 'unixepoch', 'localtime') ura, COUNT(*) n
FROM obiskovalec WHERE dan='$dan' AND bot=0 AND js>0 AND ogledov=1 AND zahtev<=2
GROUP BY ura;

.print ''
.print '== prihod z znanega vira: država, Sec-Fetch-Mode'
SELECT kljuc, ogledov FROM obisk_razrez WHERE dan='$dan' AND razsez='prihod' ORDER BY ogledov DESC;

.print ''
.print '== države razen SI (samo ljudje)'
SELECT kljuc, zahtev, ogledov FROM obisk_razrez
WHERE dan='$dan' AND razsez='drzava' AND kljuc<>'SI' AND ogledov>=5 ORDER BY ogledov DESC;

.print ''
.print '== težki ključi'
SELECT substr(kljuc, 1, 6) k, bot, zahtev, js, ogledov og, aplikacija app,
       time(prvi_s, 'unixepoch', 'localtime') prvi, time(zadnji_s, 'unixepoch', 'localtime') zadnji,
       ROUND((zadnji_s - prvi_s) * 1.0 / MAX(1, zahtev - 1), 1) s_med
FROM obiskovalec WHERE dan='$dan' ORDER BY zahtev DESC LIMIT 12;

.print ''
.print '== API brez ogleda, ni aplikacija (ponarejen UA šteje kot človek)'
SELECT substr(kljuc, 1, 6) k, zahtev, time(prvi_s, 'unixepoch', 'localtime') prvi,
       time(zadnji_s, 'unixepoch', 'localtime') zadnji
FROM obiskovalec WHERE dan='$dan' AND bot=0 AND js>0 AND ogledov=0 AND aplikacija IS NULL
ORDER BY zahtev DESC LIMIT 5;

.print ''
.print '== roboti po imenu'
SELECT kljuc, zahtev, ogledov FROM obisk_razrez WHERE dan='$dan' AND razsez='robot' ORDER BY zahtev DESC;

.print ''
.print '== čas strežnika'
SELECT ROUND(SUM(ms_vsota) / 1000) s_vse,
       ROUND(100.0 * SUM(ms_vsota * (zahtev - ljudi) * 1.0 / zahtev) / SUM(ms_vsota), 1) pct_ne_ljudje
FROM obisk_pot WHERE dan='$dan' AND zahtev > 0;
SQL
