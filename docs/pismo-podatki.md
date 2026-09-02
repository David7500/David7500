# Prošnja za dopolnitev podatkov (osnutek)

Namenjeno pošiljanju na NAP / IJPP (Ministrstvo za infrastrukturo) oziroma SŽ.
DERP samo pretvarja, kar dobi — manjkajoča polja izvirajo pri viru.

Vse številke spodaj so **izmerjene na zajetem feedu 2. 9. 2026** (`data/ijpp_gtfs.zip`,
`rt.gtfs.derp.si`), ne ocenjene. Če pismo pošlješ čez čas, jih preveri znova.

---

## Osnutek besedila

**Zadeva: Predlog dopolnitve odprtih podatkov IJPP (GTFS in GTFS-RT)**

Spoštovani,

uporabljam odprte podatke IJPP prek NAP (CC BY-SA 4.0, obdelava DERP) za
prikaz voznih redov in zamud slovenskega javnega potniškega prometa. Podatki
so kakovostni in redno osveženi — hvala za to.

Ob rabi sem naletel na nekaj polj, ki jih standard GTFS predvideva, v tem
viru pa jih ni. Spodaj so našteta po tem, koliko bi pomenila potniku, in z
izmerjenim stanjem, da je jasno, o čem govorim.

**1. Peron oziroma tir — najbolj pogrešano.**
`stops.txt` ima štiri stolpce (`stop_id`, `stop_name`, `stop_lat`,
`stop_lon`). Ni polja `platform_code` in ni hierarhije postaja–peron
(`parent_station`, `location_type`), ki jo GTFS predvideva. Zato ni mogoče
povedati, s katerega perona vlak odpelje — to je po uri odhoda najpogostejše
potnikovo vprašanje, na postajah z več peroni pa pogosto edino, ki še ostane.
Če je podatek pri SŽ na voljo, bi bil tudi v realnem času koristen
(`stop_time_update.stop_id`, ki kaže na peronski `stop_id`).

**2. Odpovedi v strukturirani obliki.**
GTFS-RT ima za to `schedule_relationship` (`CANCELED`, `SKIPPED`). V vzorcu
5 135 postankov v 319 vožnjah je bila vrednost **v 100 % `SCHEDULED`**.
Odpovedi so sporočene le kot prosto besedilo v obvestilu („Vlak vozi samo do
postaje …“), česar ni mogoče zanesljivo strojno brati. Za potnika je razlika
med zamudo in odpovedjo največja, ki obstaja.

**3. Lega vlakov.**
`vehicle_positions` nosi 265 vozil, vsa avtobusna. Vlakov v njem ni, zato je
njihov položaj mogoče le sklepati iz zadnje postaje z meritvijo.

**4. `direction_id`.**
Ni ga ne v `trips.txt` ne v realnem času (0 od 319 voženj). Smer vožnje je
zato treba sklepati iz številke vlaka oziroma iz zaporedja postaj.

**5. `shape_dist_traveled` v `stop_times.txt`.**
Ni ga, zato je razdalje med postajami treba računati s projekcijo postaj na
`shapes.txt`. Rezultat odstopa od uradnih kilometrskih leg za približno
2–4 % (Zidani Most–Ljubljana: 63,6 km proti uradnim ~61 km).

**6. `route_long_name`.**
Prazen pri vseh 2 571 progah.

**7. Manjkajoče neobvezne datoteke.**
`transfers.txt` (najkrajši čas za prestop na postaji) je ni; časi prestopov
so zato ocenjeni.

**8. Polja, ki obstajajo, a so povsod enaka.**
`bikes_allowed` je `0` („ni podatka“) pri vseh 20 736 vožnjah;
`wheelchair_accessible` v `trips.txt` in `wheelchair_boarding` v `stops.txt`
ju ni; `occupancy_status` in `congestion_level` v `vehicle_positions` nista
izpolnjena pri nobenem od 265 vozil.

Zanima me predvsem prvo — **peron** — in drugo, **odpovedi**. Če teh podatkov
v izvornih sistemih ni, mi je koristno vedeti tudi to; potem vem, da jih ni
smiselno čakati. Če pa obstajajo in gre le za to, da se v GTFS ne prenesejo,
bi bila njihova vključitev velika pridobitev za vse, ki te podatke
uporabljajo.

Hvala za odgovor in za odprte podatke.

Lep pozdrav

---

## Zapiski k pošiljanju (ne pošiljaj tega dela)

* **Anonimno je šibkejše.** Prošnja od nekoga, ki pove, da podatke dejansko
  uporablja in jih zna izmeriti, je precej težja od anonimne. Če ne želiš
  imena, vsaj povej, da gre za delujočo aplikacijo z zajemom — to je razlika
  med „nekdo sprašuje“ in „nekdo to uporablja“.
* **Ne obljubljaj ničesar.** Ne rabijo vedeti, kaj načrtujeva; rabijo vedeti,
  kaj manjka.
* **Naslovnik:** NAP (podatkovna točka) je pravi prvi naslov; peronski podatek
  pa izvira pri SŽ, zato je smiselno vprašati oba in to v pismu povedati.
* Če odgovorijo z „podatka ni“, je to **odgovor**, ki gre v `CLAUDE.md` med
  stvari, ki jih ne bo — enako kot cene in zasedenost.
