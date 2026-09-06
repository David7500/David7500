package app.kajros

import android.content.Context
import java.net.URI
import java.net.URISyntaxException

/**
 * Naslov streznika -- edina nastavitev, ki jo aplikacija ima.
 *
 * Ni udobje, ampak **meja zaupanja**. Most do JavaScripta bo viden vsaki
 * strani, ki jo WebView nalozi, zato mora obstajati en sam kraj, ki pove,
 * katera stran je nasa. Ta kraj je [izvor]; vse drugo ga samo bere.
 *
 * Razclenjevanje gre skozi `java.net.URI` in ne `android.net.Uri`: prvi je
 * navaden JVM in ga je mogoce preizkusiti brez naprave in brez Robolectrica,
 * drugi ne. Ker je to varnostno pravilo, mora imeti teste.
 */
object Nastavitve {

    private const val DATOTEKA = "kajros"
    private const val KLJUC = "naslov"

    /** Sheme, ki jih sploh obravnavamo. `intent:`, `javascript:` in `file:` ne. */
    private val SHEME = setOf("http", "https")

    private val PRIVZETA_VRATA = mapOf("http" to 80, "https" to 443)

    fun naslov(c: Context): String =
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .getString(KLJUC, null) ?: BuildConfig.PRIVZETI_NASLOV

    fun shrani(c: Context, naslov: String) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .edit().putString(KLJUC, naslov).apply()
    }

    /**
     * Kar je clovek natipkal, pretvori v naslov izvora, ali vrne null.
     *
     * Brez sheme predpostavi `https`, ne `http`: kdor natipka samo
     * `kajros.app`, hoce sifrirano povezavo, in tiho zdrsniti na nesifrirano
     * je najslabsi mozni privzetek.
     */
    fun ocisti(vnos: String): String? {
        var v = vnos.trim()
        if (v.isEmpty()) return null
        if (!v.contains("://")) v = "https://$v"
        // Pot zavrzemo: nastavlja se izvor, ne stran. Kam v njem gre aplikacija,
        // je stvar strani.
        return izvor(v)
    }

    /**
     * `shema://gostitelj[:vrata]` ali null.
     *
     * Privzeta vrata izpustimo, ker jih tako zapise tudi WebView, kadar poroca
     * izvor (`onGeolocationPermissionsShowPrompt`). Sicer bi bila
     * `https://kajros.app` in `https://kajros.app:443` dva razlicna niza za
     * isti izvor -- in primerjava bi tiho odpovedala.
     */
    fun izvor(url: String?): String? {
        if (url.isNullOrBlank()) return null
        val u = try {
            URI(url.trim())
        } catch (e: URISyntaxException) {
            return null
        }
        val shema = u.scheme?.lowercase() ?: return null
        if (shema !in SHEME) return null
        val gostitelj = u.host?.lowercase() ?: return null
        if (gostitelj.isBlank()) return null
        return if (u.port == -1 || u.port == PRIVZETA_VRATA[shema]) "$shema://$gostitelj"
        else "$shema://$gostitelj:${u.port}"
    }

    /** Ali je [url] na istem izvoru kot [naslov]. */
    fun jeNas(url: String?, naslov: String): Boolean {
        val a = izvor(url) ?: return false
        val b = izvor(naslov) ?: return false
        return a == b
    }
}
