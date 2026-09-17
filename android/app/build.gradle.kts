// Uvoz je nujen: v Kotlinovem DSL je `java` že ime razširitve za javanski
// vtičnik, zato `java.util.Properties` ni najdeno.
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Podpisni ključ je trajna identiteta aplikacije: kdor ga zamenja, prisili vse
// nameščene telefone v odstranitev in ponovno namestitev. Zato NE živi v
// repozitoriju, ampak pri orodjih (`~/kajros-android/podpis/`), skupaj z geslom
// v datoteki s pravicami 600. Naredi ga `./podpis.sh`.
//
// `System.getProperty("user.home")` tu NE gre: `orodja.sh` postavi
// `-Duser.home=~/kajros-android/domov`, da AGP ne smeti pravega domačega
// imenika (`~/.android/analytics.settings`). Gradnja bi torej ključ iskala v
// lažnem domu, ga ne našla in **tiho** naredila nepodpisan APK -- kar se je
// tudi zgodilo, ko je bil ključ pravkar narejen.
val podpisMapa = file(System.getenv("KAJROS_PODPIS")
    ?: "${System.getenv("KAJROS_ANDROID") ?: "${System.getenv("HOME")}/kajros-android"}/podpis")
val podpisLastnosti = Properties()
val podpisDatoteka = File(podpisMapa, "podpis.properties")
if (podpisDatoteka.exists()) {
    podpisDatoteka.inputStream().use { podpisLastnosti.load(it) }
}
val podpisJe = podpisLastnosti.getProperty("geslo") != null

android {
    namespace = "app.kajros"
    compileSdk = 35

    defaultConfig {
        applicationId = "app.kajros"
        // API 26 je meja, pod katero ni ne adaptivnih ikon ne
        // `NotificationChannel`. Nad njo je vse, kar rabimo, v ogrodju in
        // AndroidX ni potreben. Volla 22 je krepko nad tem.
        minSdk = 26
        targetSdk = 35
        // `versionCode` je edino, kar telefon primerja -- ob vsaki objavi mora
        // narasti. `versionName` je za ljudi in sme biti karkoli.
        versionCode = 3
        versionName = "1.2"
        // Privzeti naslov je tu in ne v kodi, da ga je mogoce zamenjati z
        // `-PkajrosUrl=...`, ne da bi se dotaknil izvorne datoteke.
        buildConfigField("String", "PRIVZETI_NASLOV",
            "\"${project.findProperty("kajrosUrl") ?: "https://kajros.app"}\"")
    }

    buildFeatures {
        buildConfig = true
    }

    signingConfigs {
        if (podpisJe) {
            create("izdaja") {
                storeFile = File(podpisMapa, podpisLastnosti.getProperty("shramba", "kajros.jks"))
                storePassword = podpisLastnosti.getProperty("geslo")
                keyAlias = podpisLastnosti.getProperty("vzdevek", "kajros")
                keyPassword = podpisLastnosti.getProperty("geslo_kljuca")
                    ?: podpisLastnosti.getProperty("geslo")
                // v1 (podpis v JAR) ni potreben: velja do API 23, mi smo od 26
                // naprej. Izmerjeno -- `apksigner verify -v` pove
                // „v1: false, v2: true, v3: true", in to je pravilno stanje.
                // v3 rabi menjava ključa, če bi bila kdaj potrebna.
                enableV1Signing = false
                enableV2Signing = true
                enableV3Signing = true
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            // Brez ključa gradnja še vedno teče — nepodpisan APK je dovolj za
            // merjenje velikosti. Podpisan nastane šele, ko ključ obstaja.
            if (podpisJe) signingConfig = signingConfigs.getByName("izdaja")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    // Namenoma prazno. Ce se tu kdaj pojavi vrstica, naj bo zraven razlog --
    // brez odvisnosti je APK majhen in v njem ni nicesar Googlovega.
    testImplementation(kotlin("test"))
}
