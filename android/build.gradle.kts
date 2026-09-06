// AGP in Kotlin sta orodji za gradnjo; v APK ju ni. Edina knjiznica, ki v APK
// res pride, je Kotlinova standardna (JetBrains) -- AndroidX, Play Services in
// Firebase ni nikjer, ker aplikacija med tekom ne sme imeti stika z Googlom.
plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}
