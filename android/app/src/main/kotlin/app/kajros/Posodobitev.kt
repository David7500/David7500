package app.kajros

import android.content.Context
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

/**
 * Ali je izšla novejša različica aplikacije.
 *
 * Zunaj trgovine posodobitve ne ponudi nihče. Play in F-Droid to naredita
 * sama; kdor aplikacijo namesti z naše strani, bi brez tega ostal na
 * različici, s katero jo je namestil -- in popravek napake, ki je videti kot
 * napaka strani, nikoli ne bi prišel do njega.
 *
 * Aplikacija zato **vpraša, ne ukrepa**: pokaže vrstico, prenos in namestitev
 * pa sta uporabnikova klika. Samodejnega prenosa ni. Vrstica vodi na zaslon
 * „O aplikaciji“ (`AplikacijaDejavnost`), kjer se da preveriti tudi ročno. Namesti pa aplikacija
 * sama (`Namestitev`), ne brskalnik: sistemski namestitveni program ob vsaki
 * posodobitvi vzame budilki dovoljenje za cel zaslon (izmerjeno 6. 10. 2026),
 * in to je bila cena `REQUEST_INSTALL_PACKAGES`, ki ga prej nismo hoteli.
 */
object Posodobitev {

    private const val CAKAJ_MS = 5000
    private const val DATOTEKA = "kajros"
    private const val KLJUC_VPRASANO = "posodobitev_vprasano"
    private const val KLJUC_PRESKOCENA = "posodobitev_preskocena"

    /** Enkrat na dan je dovolj: izdaja je redka, zagon aplikacije ni. */
    private const val RAZMIK_MS = 24L * 60 * 60 * 1000

    /** [url] je APK, [stran] stran s prenosom: ta ostane, kadar namestitev ne uspe. */
    data class Izdaja(
        val koda: Int, val ime: String, val stran: String,
        val url: String, val sha256: String, val objavljeno: String,
    ) {
        val novejsa: Boolean get() = koda > BuildConfig.VERSION_CODE
    }

    /**
     * Zadnji odgovor strežnika v tem procesu. Vrstica in zaslon „O aplikaciji“
     * govorita o isti izdaji, ne da bi jo zaslon spraševal še enkrat.
     */
    @Volatile
    var zadnja: Izdaja? = null
        private set

    /**
     * Preveri v ozadnji niti in [kaj] pokliče v glavni, kadar je kaj novega.
     *
     * Ne vrne ničesar, kadar preverjanje odpove: to je navadno stanje (ni
     * omrežja) in vrstica o posodobitvi ob takem trenutku bi bila napačna
     * vest -- takrat potnika zanima vlak, ne različica.
     */
    fun preveri(c: Context, kaj: (Izdaja) -> Unit) {
        if (!jeCas(c)) return
        preveriZdaj(c) { izdaja ->
            if (izdaja != null && izdaja.novejsa && izdaja.koda != preskocena(c)) kaj(izdaja)
        }
    }

    /**
     * Vpraša takoj, mimo enkrat na dan: zaslon „O aplikaciji“, kjer je
     * potnik vprašal sam. [kaj] dobi `null`, kadar odgovora ni.
     */
    fun preveriZdaj(c: Context, kaj: (Izdaja?) -> Unit) {
        val app = c.applicationContext
        val glavna = android.os.Handler(c.mainLooper)
        Thread {
            val izdaja = vprasaj(app)
            if (izdaja != null) {
                zadnja = izdaja
                // Šteje šele odgovor: preverjanje brez omrežja bi sicer
                // naslednje odložilo za ves dan.
                app.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
                    .edit().putLong(KLJUC_VPRASANO, System.currentTimeMillis()).apply()
            }
            glavna.post { kaj(izdaja) }
        }.start()
    }

    /** Kdaj je strežnik nazadnje odgovoril; 0, če še nikoli. */
    fun nazadnjeVprasano(c: Context): Long =
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).getLong(KLJUC_VPRASANO, 0)

    /** Te različice ne omenjaj več. Naslednja bo spet imela večjo kodo. */
    fun preskoci(c: Context, koda: Int) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .edit().putInt(KLJUC_PRESKOCENA, koda).apply()
    }

    private fun preskocena(c: Context): Int =
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .getInt(KLJUC_PRESKOCENA, 0)

    private fun jeCas(c: Context): Boolean {
        val zadnjic = nazadnjeVprasano(c)
        // Tudi ura naprej ali nazaj (ročna sprememba, potovanje) ne sme
        // preverjanja ustaviti za vedno, zato je pogoj razlika v obe smeri.
        return System.currentTimeMillis() - zadnjic !in 0 until RAZMIK_MS
    }

    private fun vprasaj(c: Context): Izdaja? {
        // Samo naš izvor. Ista meja zaupanja kot povsod: kdor nastavi naslov,
        // nastavi vir te trditve, zato tu ne sme biti trdo zapisane domene --
        // sicer bi aplikacija, usmerjena na drug strežnik, ponujala tujo
        // datoteko kot svojo posodobitev.
        val url = Nastavitve.naslov(c) + "/api/android/razlicica"
        var zveza: HttpURLConnection? = null
        val besedilo = try {
            zveza = (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = CAKAJ_MS
                readTimeout = CAKAJ_MS
                requestMethod = "GET"
                setRequestProperty("User-Agent",
                    "Kajros/${BuildConfig.VERSION_NAME} (Android)")
                setRequestProperty("Accept", "application/json")
            }
            if (zveza.responseCode != 200) null
            else zveza.inputStream.bufferedReader().use { it.readText() }
        } catch (e: IOException) {
            null
        } finally {
            zveza?.disconnect()
        } ?: return null

        return try {
            val j = JSONObject(besedilo)
            val stran = j.optString("stran")
            val apk = j.optString("url")
            // Naslova iz odgovora morata biti v NAŠEM izvoru: odgovor je podatek
            // s strežnika, in tudi naš strežnik ne sme odpreti povezave, ki
            // pelje drugam, ali namestiti datoteke od drugod, samo zato, ker jo
            // je vrnil.
            val nas = Nastavitve.naslov(c)
            if (!Nastavitve.jeNas(stran, nas) || !Nastavitve.jeNas(apk, nas)) null
            else Izdaja(j.getInt("koda"), j.optString("ime"), stran, apk,
                j.optString("sha256"), j.optString("objavljeno"))
        } catch (e: JSONException) {
            null
        }
    }
}
