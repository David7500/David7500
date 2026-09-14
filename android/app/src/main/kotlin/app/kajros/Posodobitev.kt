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
 * Aplikacija zato **vpraša, ne ukrepa**: pokaže vrstico s povezavo, prenos in
 * namestitev pa sta uporabnikova klika. Samodejnega prenosa namenoma ni --
 * `REQUEST_INSTALL_PACKAGES` je dovoljenje, ki ga ta aplikacija ne rabi, in
 * tiho nameščanje iz omrežja je natanko tisto, pred čimer Android svari.
 */
object Posodobitev {

    private const val CAKAJ_MS = 5000
    private const val DATOTEKA = "kajros"
    private const val KLJUC_VPRASANO = "posodobitev_vprasano"
    private const val KLJUC_PRESKOCENA = "posodobitev_preskocena"

    /** Enkrat na dan je dovolj: izdaja je redka, zagon aplikacije ni. */
    private const val RAZMIK_MS = 24L * 60 * 60 * 1000

    data class Izdaja(val koda: Int, val ime: String, val stran: String)

    /**
     * Preveri v ozadnji niti in [kaj] pokliče v glavni, kadar je kaj novega.
     *
     * Ne vrne ničesar, kadar preverjanje odpove: to je navadno stanje (ni
     * omrežja) in vrstica o posodobitvi ob takem trenutku bi bila napačna
     * vest -- takrat potnika zanima vlak, ne različica.
     */
    fun preveri(c: Context, kaj: (Izdaja) -> Unit) {
        if (!jeCas(c)) return
        val glavna = android.os.Handler(c.mainLooper)
        Thread {
            val izdaja = vprasaj(c)
            if (izdaja != null && izdaja.koda > BuildConfig.VERSION_CODE &&
                izdaja.koda != preskocena(c)) {
                glavna.post { kaj(izdaja) }
            }
        }.start()
    }

    /** Te različice ne omenjaj več. Naslednja bo spet imela večjo kodo. */
    fun preskoci(c: Context, koda: Int) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .edit().putInt(KLJUC_PRESKOCENA, koda).apply()
    }

    private fun preskocena(c: Context): Int =
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .getInt(KLJUC_PRESKOCENA, 0)

    private fun jeCas(c: Context): Boolean {
        val p = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
        val zadnjic = p.getLong(KLJUC_VPRASANO, 0)
        val zdaj = System.currentTimeMillis()
        // Tudi ura naprej ali nazaj (ročna sprememba, potovanje) ne sme
        // preverjanja ustaviti za vedno, zato je pogoj razlika v obe smeri.
        if (zdaj - zadnjic in 0 until RAZMIK_MS) return false
        p.edit().putLong(KLJUC_VPRASANO, zdaj).apply()
        return true
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
            // Naslov iz odgovora mora biti v NAŠEM izvoru: odgovor je podatek
            // s strežnika, in tudi naš strežnik ne sme odpreti povezave, ki
            // pelje drugam, samo zato, ker jo je vrnil.
            if (!Nastavitve.jeNas(stran, Nastavitve.naslov(c))) null
            else Izdaja(j.getInt("koda"), j.optString("ime"), stran)
        } catch (e: JSONException) {
            null
        }
    }
}
