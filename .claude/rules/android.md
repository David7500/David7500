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

## Budilka (načrtovano)

Davidovo pravilo, dobesedno: *„uporabnik vnese, koliko časa (x minut) preden
pride vlak naj zazvoni (upošteva se zamude); če pa ni povezave, potem zazvoni
x minut preden je napovedan vozni red tega vlaka (nič upoštevanja zamud)."*

Iz tega sledi, da mora biti **voznoredna ura shranjena lokalno** ob nastavitvi
budilke — sicer nadomestna pot rabi omrežje, ki ga ravno ni.

Preverjanje ob `voznoredna − X − 5 min`, nato `GET /api/train/{no}/run`, ura
zvonjenja `expected − X`, ponovno preverjanje vsakih 5 minut. Ura se sme
premakniti tudi **nazaj**: mestni avtobus je pogosto prezgoden.

Obvestilo vedno pove, kateri primer velja („upoštevana zamuda +7" proti „po
voznem redu — zamude nisem mogel preveriti"). Ura brez razloga ni odgovor.
