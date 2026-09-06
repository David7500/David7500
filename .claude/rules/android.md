---
paths:
  - "android/**"
---

# Aplikacija za Android

Nativni ovoj z WebView na `kajros.app`. Vmesnik ostane **en sam — spletni**;
nativno je samo tisto, česar splet ne zmore. To je zaenkrat ena stvar: budilka.

## Zakaj tako in ne drugače

| možnost | zakaj ne |
|---|---|
| PWA | alarma ob določeni uri ne zna. `Notification Triggers` je bil v Chromu preizkušen in **nikoli izdan**, `Periodic Background Sync` dela v urah in je vezan na Chrome, Web Push gre skozi FCM (Google) in bi zahteval buden strežnik |
| TWA | zahteva Chrome kot ponudnika. Telefon je razgooglana Volla 22 s Fennecom — TWA bi pomenil namestiti Chromium |
| GeckoView | most do JavaScripta je z njim moreč; `addJavascriptInterface` na WebView je ena vrstica. To je bilo odločilno, ne hitrost |
| service worker | David: „ne zaenkrat pač nič ne pokaže". Posledica je, da nedosegljivega strežnika ne pokrije splet — pokrije ga **nativni zaslon napake** |

Razdeljevanje: samopodpisan APK s `kajros.app`, kasneje F-Droid. Brez Play
Store in brez Googlovega računa.

## Meja zaupanja je ena sama funkcija

`Nastavitve.izvor()` pove, katera stran je naša. Vse drugo jo bere:

* povezava zunaj tega izvora se **ne odpre v WebView**, ampak v brskalniku;
* dovoljenje za lego dobi samo ta izvor;
* most (`window.Kajros`) ga bo preveril ob vsakem klicu.

To ni pedantnost: `addJavascriptInterface` je viden **vsaki** strani, ki jo
WebView naloži. Zato so tudi sheme, ki smejo ven, naštete — `intent:` ni med
njimi, ker je znana pot, s katero tuja stran odpre poljubno dejavnost.

Razčlenjevanje gre skozi `java.net.URI`, **ne** `android.net.Uri`: prvi je
navaden JVM in ga je mogoče preizkusiti brez naprave. Varnostno pravilo brez
testov ni pravilo.

## Nič odvisnosti

Ne AndroidX, ne `appcompat`. Vse potrebno je v ogrodju od API 26: `WebView`,
`AlarmManager`, `NotificationChannel`, `Ringtone`. Zato je izdajni APK 28 kB in
v njem ni **nobenega** Googlovega niza (preverjeno z `aapt2 dump strings`).
Če se v `dependencies` kdaj pojavi vrstica, mora biti zraven razlog.

`-keepclassmembers` za `@JavascriptInterface` v `proguard-rules.pro` **mora
ostati**: R8 bi metode mostu sicer preimenoval in `Kajros.nastavi()` bi tiho
ne obstajal — samo v izdajni različici.

## Orodja puščajo, in to je treba loviti sproti

`orodja.sh` postavi vse v `~/kajros-android` in **dokaže**, da drugod ni nič.
Trije primeri, ki jih je dokaz ujel, so v [docs/MERITVE.md](../../docs/MERITVE.md).
Najhujši: AGP ob vsaki gradnji naredi `~/.android/analytics.settings` z
obstojnim `userId`; premakne ga **samo `-Duser.home`**, ne `ANDROID_USER_HOME`
in ne `HOME`.

Zato ta dokaz ni enkraten — `zgradi.sh` ga ponovi ob vsaki gradnji in pade,
če kaj uide.

Spremenljivk okolja ne dodajaj na slepo: AGP pade, če najde več različnih poti
do svoje mape (`ANDROID_PREFS_ROOT`, `ANDROID_SDK_HOME`, `ANDROID_USER_HOME`).
Emulator pa `ANDROID_USER_HOME` sploh ne bere in rabi `ANDROID_AVD_HOME`.

## Preverjanje

```bash
./zgradi.sh                 # testi JVM + APK + revizija domačega imenika
KAJROS_EMULATOR=1 ./orodja.sh && ./zgradi.sh emulator
./zgradi.sh namesti
adb exec-out screencap -p > ../posnetki/x.png
```

Emulatorjeva slika je `default`, **ne** `google_apis` — AOSP brez Googlovih
storitev, ista izbira kot pri telefonu.

`variations_seed_loader.cc: Seed missing signature` v dnevniku ni naša napaka:
to je WebViewova lastna konfiguracija, ki je na AOSP ni.

## Budilka

Davidovo pravilo, dobesedno: *„uporabnik vnese, koliko časa (x minut) preden
pride vlak naj zazvoni (upošteva se zamude); če pa ni povezave, potem zazvoni
x minut preden je napovedan vozni red"* in *„uporabnik ne sme zamuditi, raje
kej rezerve, če ni zihr"*.

Vse, kar budilka rabi, je **shranjeno lokalno** — predvsem voznoredna ura.
Če bi jo bilo treba pridobiti, bi nadomestna pot rabila ravno tisto, česar
takrat ni.

**Aritmetika je v `Ura.kt` in je čista** (brez Androida), da jo je mogoče
preizkusiti brez naprave. Tam je vse, kar je mogoče narediti narobe.

### Rezerva ni ocena

`REZERVA_S = 5 min`, `REZERVA_BREZ_ZVEZE_AVTOBUS_S = 3 min`. Obe sta izmerjeni
na 63 843 vrsticah sence (`docs/MERITVE.md`, „Rezerva budilke"). Brez rezerve
bi budilka zvonila prepozno v 32 % primerov pri vlakih in 64 % pri avtobusih.

Pri vlakih je rezultat omejen na 0 (`max(0, zamuda − rezerva)`), ker **vlak
pred voznim redom ne odpelje** — 0 primerov od 10 775. Pri avtobusih te
omejitve NI in je ne sme biti: ti prezgodaj gredo v 25 % primerov, in z njo
bi delež zamud zrasel s 6,4 na 28,9 %.

### Kje budilka bere zamudo

**`/api/departures`, ne `/api/train/{no}/run`.** Prva izbira je bila druga in
je bila napačna: `run` vrne `zamuda: null` za vsak postanek, ki ga feed še ni
dosegel — torej ravno za tistega, na katerem potnik čaka. Izmerjeno na EN 414:
Zidani Most je imel napoved prevoznika, Ljubljana pa nič, medtem ko je tabla
kazala +24 min iz naše ocene.

Odhodna tabla vrne natanko številko, ki jo potnik vidi. **Na njej je umerjena
tudi rezerva** (senca meri `ours_s`, kar je isti izračun `stats.predict`), zato
bi vsak drug vir pomenil, da rezerva varuje pred napako, ki je ne merimo.

### Obvestilo ne sme trditi ure, ki ji račun ni verjel

Ta napaka je bila na zaslonu: naslov „ob 22:34" (iz zamude) in pod njim
„po voznem redu — zamude nisem mogel preveriti". Zato `Ura.Izid` nosi
`odhodMs`, ki ga izračuna **ista odločitev** kot uro zvonjenja.

### Pasti, ki so se pokazale šele na napravi

* **`setAlarmClock` brez dovoljenja vrže `SecurityException`.** Od Androida 12
  točen alarm ni pravica. Ujet je in nadomeščen s `setAndAllowWhileIdle` —
  slabša budilka je boljša od podrte aplikacije.
* **`PendingIntent` brez `data` se zlije v enega.** `extras` se pri primerjavi
  ne upoštevajo, zato bi `FLAG_UPDATE_CURRENT` vse budilke združil v eno.
  Ločuje jih `kajros://budilka/<id>`.
* **Zagon dejavnosti iz ozadja je blokiran** (`Background activity launch
  blocked!` v dnevniku). Zaslon odpre obvestilo s `fullScreenIntent`, ne naš
  `startActivity` — in to le, kadar je telefon **zaklenjen**; sicer je to
  navadno obvestilo. Preizkušeno z `locksettings set-pin`.
* **`display` iz razreda premaga `[hidden]`** iz brskalnikovega sloga.
  `.bud-plast` brez `[hidden] { display: none }` leži čez vso stran in požira
  vsak klik — tudi v brskalniku, kjer gumba za budilko sploh ni.
