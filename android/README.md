# Aplikacija za Android

Nativni ovoj okrog `kajros.app` z WebView, ki bo dobil **budilko** — edino, česar splet ne zmore. Zakaj ne PWA/TWA: v telefonu ni Chroma (Volla 22 razgooglana, brskalnik Fennec), TWA brez Chroma ne obstaja; alarma ob določeni uri nobena spletna tehnologija ne zna brez Googlovega push strežnika.

## Gradnja

```bash
./orodja.sh                # enkrat: JDK, Android SDK, Gradle v ~/kajros-android
./podpis.sh                # enkrat: podpisni ključ v ~/kajros-android/podpis
./zgradi.sh                # testi JVM + razvojni APK
./zgradi.sh namesti        # in ga naloži na priklopljen telefon
./zgradi.sh izdaja         # izdajni APK (podpisan, če ključ obstaja)
./objavi.sh posreduj       # objavi za prenos na kajros.app/android
```

Orodja **vsa v `~/kajros-android`**, nič sistemsko — glej `orodja.sh`. Odstranitev vsega: `./pocisti.sh` ali `rm -rf ~/kajros-android`.

| kaj | velikost |
|---|---|
| JDK 21 + SDK + Gradle | 2,4 GB |
| + emulator in sistemska slika (neobvezno) | 5,5 GB |

Skripta ne obljublja, da ne smeti računalnika, ampak **dokaže**, da ne smeti: posname vrh domačega imenika pred in po. Ni bilo odveč — ujela tri uhajanja, med njimi `~/.android/analytics.settings` z obstojnim `userId`, ki ga AGP naredi kljub `ANDROID_USER_HOME` (premakne ga šele `-Duser.home`). `./zgradi.sh` dokaz ponovi ob vsaki gradnji in pade, če kaj uide.

**Gradle wrapperja ni namenoma.** Wrapper = binarni `.jar` v gitu; Gradle je orodje in živi z drugimi orodji. Kdor klonira repozitorij, požene `orodja.sh`.

## Kaj je v APK

Nič Googlovega, nič AndroidX. Edina knjižnica v APK: Kotlinova standardna; vse drugo (`WebView`, `AlarmManager`, `NotificationChannel`) v ogrodju od API 26. Izmerjeno 12. 9. 2026: izdajni APK **71 822 B** (70 kB, podpisan; nepodpisan 61 854 B, 29 datotek, brez nativne kode), razvojni **894 259 B** — razlika = Kotlinova standardna knjižnica, ki jo R8 v izdaji odreže, v razvojni ostane cela. Nizov „google“, „firebase“, „gms“ v izdajnem APK **0** (`aapt2 dump strings`).

Android SDK za gradnjo je Googlov. Aplikacija med **tekom** z Googlom nima opravka.

## Meja zaupanja

`Nastavitve.izvor()` = edino mesto, ki pove, katera stran je naša. Vse drugo ga bere:

* povezava zunaj izvora se odpre v brskalniku, ne v WebView;
* dovoljenje za lego dobi samo ta izvor;
* most do budilk (`window.Kajros`) ga bo preveril ob vsakem klicu.

Zato ima `izvor()` teste brez naprave: `./zgradi.sh testi`.

Sheme, ki gredo ven, naštete (`http`, `https`, `mailto`, `tel`, `sms`, `geo`). `intent:` ni med njimi — znana pot, po kateri tuja stran odpre poljubno dejavnost v telefonu.

## Naslov strežnika

Privzeto `https://kajros.app`. Menja se **z dolgim pritiskom na ikono aplikacije → Nastavi naslov**, ker stran zavzame ves zaslon, za nativni gumb ni mesta. Isti gumb na zaslonu, ki se pokaže, ko strežnika ni.

Nešifrirani naslovi dovoljeni samo za naprave v `app/src/main/res/xml/omrezje.xml` (prenosnik, malina, localhost). Nov naslov v domačem omrežju zahteva vrstico tam in novo gradnjo — namerno dražje od `cleartextTrafficPermitted="true"` čez vse.

**Lastna lega v aplikaciji dela**, prek `http://192.168…` v brskalniku ne: `https://kajros.app` v WebView **je** varen kontekst.

## Emulator

Pravilo projekta: spremembo prikaza se **pogleda**, preden je končana. Brez emulatorja je preverjanje odvisno od priklopljenega telefona.

```bash
KAJROS_EMULATOR=1 ./orodja.sh     # enkrat: emulator + AOSP slika Androida 15
./zgradi.sh emulator              # zažene brez okna
./zgradi.sh namesti
adb exec-out screencap -p > ../posnetki/x.png
./zgradi.sh ustavi
```

Slika `default`, **ne** `google_apis`: AOSP brez Googlovih storitev, ista izbira kot pri telefonu. KVM mora biti dosegljiv; na tem računalniku prek ACL (`getfacl /dev/kvm`), brez sudota.

## Preizkušanje na telefonu

Telefon priklopi, v razvijalskih možnostih vklopi razhroščevanje po USB.

```bash
source ~/kajros-android/okolje.sh
adb devices                 # mora videti napravo
./zgradi.sh namesti
adb logcat --pid=$(adb shell pidof app.kajros)
```

Stran samo v razvojni različici razhrošuješ prek `chrome://inspect` (`WebView.setWebContentsDebuggingEnabled` v izdaji izklopljen).

## Budilka

Edino, česar splet ne zmore; edini razlog za obstoj aplikacije. Nastavi se **na strani** — odpri vožnjo, pri svoji postaji „budilka“ — zvoni **nativno** prek `AlarmManager.setAlarmClock`, ker to preživi Doze.

* **Ponavljanje.** Nabor dni (`pon … ned`, `delavniki`, `vsak dan`) v listu budilke; brez izbire = enkratna. Naslednji dan se poišče po **zidni uri**, ne s prištevanjem 86 400 s — ob prehodu na zimski čas ima dan 25 ur, budilka bi bila uro narobe (`Ponovitev.kt`, testi brez naprave).
* **Vožnja, ki danes ne vozi, ne zvoni.** `trip_id` je vsak dan drug, zato ga ponavljajoča budilka na dan odhoda poišče znova po številki in voznoredni uri. Če je tabla odgovorila in vožnje ni, se budilka **preskoči** s tihim obvestilom. „Ni odgovora“ ≠ „danes ne vozi“.
* **Seznam budilk** nativen (dela brez strežnika), dosegljiv iz aplikacije: povezava „budilke“ v glavi strani. Dolg pritisk na ikono ostaja kot bližnjica.

## Widget

Odštevanje do naslednjega odhoda, za katerega imaš budilko. Sekunde riše `Chronometer` v sistemskem procesu (`setChronometerCountDown`), zato odštevanje ne stane nobenega prebujanja. Zamuda se osveži, ko se budilka tako ali tako zbuja — približno pol ure pred odhodom; prej widget piše „zamuda še ni preverjena“.

## Naslov strežnika

Bil na dolgem pritisku na ikono; zdaj na **zaslonu budilk** in zaslonu napake, torej kjer se rabi.

## Razdeljevanje: prenos s kajros.app

Trgovine ni — odločitev, ne opuščeno opravilo (12. 9. 2026):

| trgovina | zakaj ne |
|---|---|
| F-Droid (glavni) | sprejme **samo prosto programje**, gradi iz javnega izvora; koda zaprta |
| IzzyOnDroid | isti pogoj |
| Google Play | Googlov račun, 25 $, preverjanje identitete, **12 preizkuševalcev × 14 dni** za osebni račun, AAB namesto APK, od 31. 8. 2026 `targetSdk` 36 |
| Accrescent | zaprto kodo sprejme; ostaja odprta možnost, a zahteva pregled in `bundletool` |

Zato **stran `/android`** s podpisanim APK-jem, vsoto SHA-256 in navodilom v treh korakih. Deluje danes in za vsakogar; cena: vprašanje o neznanem viru, stran to pove vnaprej.

```bash
./podpis.sh                       # enkrat: ključ za APK
./objavi.sh posreduj              # zgradi, podpiše, pošlje na arwen
```

**Podpisni ključ ni v gitu, brez varnostne kopije posodobitev ni mogoča** — telefon sprejme le nadgradnjo, podpisano z istim ključem kot nameščena različica (`~/kajros-android/podpis/`).

**Dvig `versionCode` = pogoj za posodobitev.** Telefon jo vidi le, če je številka večja od nameščene; `versionName` je za ljudi. Oboje v `app/build.gradle.kts`.

**Posodobitve zunaj trgovine ne ponudi nihče**, zato jih aplikacija poišče sama: `Posodobitev.kt` enkrat na dan vpraša `/api/android/razlicica`, ob novejši kodi pokaže vrstico s povezavo. Prenos in namestitev ostaneta klika uporabnika — `REQUEST_INSTALL_PACKAGES` aplikacija nima in ga ne bo imela.
