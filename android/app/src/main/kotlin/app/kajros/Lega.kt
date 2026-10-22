package app.kajros

/**
 * Lastna lega za stran (most 7): kaj pomeni odgovor sistema na vprašanje za
 * dovoljenje.
 *
 * Zakaj stran sploh sprašuje aplikacijo: WebView si dovoljenja ne zapomni
 * (`retain = false`, glej `GlavnaDejavnost.pripraviWeb`), `navigator.permissions`
 * pa v WebView ni (izmerjeno na emulatorju, WebView 124, 22. 10. 2026). Stran
 * zato ne ve, ali bo `navigator.geolocation` odprl sistemsko okno, in do 1.14
 * lege ni smela prižgati sama nikjer -- tudi kadar je bila dovoljena.
 */
object Lega {

    /**
     * Odgovor, hitrejši od tega, je dal sistem sam, brez okna: dovoljenje je
     * zavrnjeno za vedno in sistem ne vpraša več. Izmerjeno na emulatorju
     * (Android 15, dvakrat): od zahteve do odgovora brez okna 72 in 51 ms, do
     * odprtih nastavitev 106 in 67 ms. Človek okno v sekundi komaj prebere.
     */
    const val BREZ_OKNA_MS = 1000L

    /** [trajno]: zavrnjeno za vedno; [nastavitve]: odpri nastavitve aplikacije. */
    data class Odlocitev(val trajno: Boolean, val nastavitve: Boolean)

    /**
     * Kaj pomeni odgovor sistema. [razlog] je `shouldShowRequestPermissionRationale`:
     * po prvi zavrnitvi `true` (sistem bo še vprašal), po drugi `false`
     * (Android 11+ ne vpraša več). [zaGumb]: vprašal je „Vklopi“ na domači
     * strani -- samo ta ob odgovoru brez okna odpre nastavitve; brez tega dotik
     * ne bi naredil ničesar vidnega. Človeku, ki je okno videl in rekel ne,
     * nastavitve niso odgovor.
     */
    fun poOdgovoru(da: Boolean, razlog: Boolean, trajaloMs: Long, zaGumb: Boolean): Odlocitev =
        when {
            da || razlog -> Odlocitev(trajno = false, nastavitve = false)
            else -> Odlocitev(trajno = true, nastavitve = zaGumb && trajaloMs < BREZ_OKNA_MS)
        }
}
