plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

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
        versionCode = 1
        versionName = "0.1"
        // Privzeti naslov je tu in ne v kodi, da ga je mogoce zamenjati z
        // `-PkajrosUrl=...`, ne da bi se dotaknil izvorne datoteke.
        buildConfigField("String", "PRIVZETI_NASLOV",
            "\"${project.findProperty("kajrosUrl") ?: "https://kajros.app"}\"")
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
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
