# Aplikacija za Android

Nativni ovoj okrog `kajros.app` z WebView, ki bo dobil **budilko** — edino, česar
splet ne zmore. Zakaj tako in ne PWA ali TWA: v telefonu ni Chroma (Volla 22 je
razgooglana, brskalnik je Fennec), TWA pa brez Chroma ne obstaja; alarma ob
določeni uri pa ne zna nobena spletna tehnologija brez Googlovega push strežnika.

## Gradnja

```bash
./orodja.sh                # enkrat: JDK, Android SDK, Gradle v ~/kajros-android
./zgradi.sh                # testi JVM + razvojni APK
./zgradi.sh namesti        # in ga naloži na priklopljen telefon
./zgradi.sh izdaja         # izdajni APK (nepodpisan), za merjenje velikosti
```

Orodja so **vsa v `~/kajros-android`** in nič ni sistemsko — glej `orodja.sh`.
Odstranitev vsega je `./pocisti.sh` ali `rm -rf ~/kajros-android`.

| kaj | velikost |
|---|---|
| JDK 21 + SDK + Gradle | 2,4 GB |
| + emulator in sistemska slika (neobvezno) | 5,5 GB |

Skripta ne obljublja, da ne smeti računalnika, ampak to **dokaže**: posname vrh
domačega imenika pred in po. To ni bilo odveč — ujela je tri uhajanja, med njimi
`~/.android/analytics.settings` z obstojnim `userId`, ki ga AGP naredi kljub
`ANDROID_USER_HOME` (premakne ga šele `-Duser.home`). `./zgradi.sh` isti dokaz
ponovi ob vsaki gradnji in pade, če kaj uide.

**Gradle wrapperja ni namenoma.** Wrapper pomeni binarni `.jar` v gitu; Gradle je
orodje in živi z drugimi orodji. Kdor klonira repozitorij, požene `orodja.sh`.

## Kaj je v APK

Nič Googlovega in nič AndroidX. Edina knjižnica v APK je Kotlinova standardna;
vse drugo (`WebView`, `AlarmManager`, `NotificationChannel`) je v ogrodju od
API 26 naprej. Zato je izdajni APK **28 kB**, razvojni pa 812 kB — razlika je
Kotlinova standardna knjižnica, ki jo R8 v izdaji odreže, v razvojni pa ostane
cela.

Android SDK, s katerim se gradi, je seveda Googlov. Aplikacija med **tekom**
nima z Googlom nobenega opravka.

## Meja zaupanja

`Nastavitve.izvor()` je edino mesto, ki pove, katera stran je naša. Vse drugo
ga bere:

* povezava zunaj tega izvora se ne odpre v WebView, ampak v brskalniku;
* dovoljenje za lego dobi samo ta izvor;
* most do budilk (`window.Kajros`) ga bo preveril ob vsakem klicu.

Zato ima `izvor()` teste, ki tečejo brez naprave: `./zgradi.sh testi`.

Sheme, ki gredo ven, so naštete (`http`, `https`, `mailto`, `tel`, `sms`, `geo`).
`intent:` ni med njimi — je znana pot, s katero tuja stran odpre poljubno
dejavnost v telefonu.

## Naslov strežnika

Privzeto `https://kajros.app`. Zamenja se **z dolgim pritiskom na ikono
aplikacije → Nastavi naslov**, ker stran zavzame ves zaslon in v njej ni mesta za
nativni gumb. Isti gumb je na zaslonu, ki se pokaže, ko strežnika ni.

Nešifrirani naslovi so dovoljeni samo za naprave, naštete v
`app/src/main/res/xml/omrezje.xml` (prenosnik, malina, localhost). Nov naslov v
domačem omrežju zahteva vrstico tam in novo gradnjo — to je namerno dražje od
`cleartextTrafficPermitted="true"` čez vse.

**Lastna lega v aplikaciji dela**, česar prek `http://192.168…` v brskalniku ne:
`https://kajros.app` v WebView **je** varen kontekst.

## Emulator

Ta projekt ima pravilo, da se spremembo prikaza **pogleda**, preden se razglasi
za končano. Brez emulatorja je vsako tako preverjanje odvisno od tega, ali je
telefon priklopljen.

```bash
KAJROS_EMULATOR=1 ./orodja.sh     # enkrat: emulator + AOSP slika Androida 15
./zgradi.sh emulator              # zažene brez okna
./zgradi.sh namesti
adb exec-out screencap -p > ../posnetki/x.png
./zgradi.sh ustavi
```

Slika je `default`, **ne** `google_apis`: AOSP brez Googlovih storitev, torej
ista izbira kot pri telefonu. KVM mora biti dosegljiv; na tem računalniku je
prek ACL (`getfacl /dev/kvm`), torej brez sudota.

## Preizkušanje na telefonu

Telefon priklopi in v razvijalskih možnostih vklopi razhroščevanje po USB.

```bash
source ~/kajros-android/okolje.sh
adb devices                 # mora videti napravo
./zgradi.sh namesti
adb logcat --pid=$(adb shell pidof app.kajros)
```

Stran samo v razvojni različici razhrošuješ prek `chrome://inspect`
(`WebView.setWebContentsDebuggingEnabled` je v izdaji izklopljen).

## Kaj še ni

Budilka. Ovoj je prva rezina; načrt je v pogovoru in v zgodovini commitov.
