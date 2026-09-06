# Most do JavaScripta se klice po imenu iz strani, ne iz Kotlina -- R8 bi
# metode brez tega odstranil ali preimenoval in `Kajros.nastavi()` bi v izdajni
# razlicici tiho ne obstajal. To je klasicna past, ki se pokaze sele v izdaji.
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
