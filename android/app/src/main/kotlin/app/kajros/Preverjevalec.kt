package app.kajros

import android.content.Context
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.time.Instant
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlin.math.abs

/**
 * Vpraša strežnik, koliko vozilo zamuja. Edini klic API, ki ga aplikacija dela
 * sama -- vse drugo je stran v WebView.
 *
 * **Bere `/api/departures`, ne `/api/train/{no}/run`.** Prva izbira je bila
 * druga in je bila napačna: `run` vrne `zamuda: null` za vsak postanek, ki ga
 * feed še ni dosegel, in to je ravno tisti, na katerem potnik čaka. Izmerjeno
 * na EN 414: Zidani Most je imel napoved prevoznika, Ljubljana pa nič, medtem
 * ko je tabla kazala +24 min iz naše ocene.
 *
 * Odhodna tabla vrne natanko številko, ki jo potnik vidi -- izmerjeno, kadar je
 * vozilo tam že bilo, in našo oceno sicer. Na tej številki je umerjena tudi
 * rezerva v `Ura` (senca meri `ours_s`, kar je isti izračun), zato bi vsak drug
 * vir pomenil, da rezerva varuje pred napako, ki je ne merimo.
 */
object Preverjevalec {

    private const val CAKAJ_MS = 5000
    /** Kako blizu voznemu redu mora biti vrstica, da je to ista vožnja. */
    private const val UJEMANJE_MS = 90_000L

    private val URA = DateTimeFormatter.ofPattern("HH:mm")

    /**
     * Kaj smo izvedeli. Trije izidi, ne dva: **"ni odgovora" in "danes ne vozi"
     * nista isto.** Prvo pomeni zvoni po voznem redu, drugo pomeni ne zvoni --
     * in ponavljajoča budilka bi brez te razlike vsako nedeljo zbudila potnika
     * za vlak, ki ne pelje.
     */
    sealed class Odgovor {
        /** Strežnika ni bilo mogoče vprašati. */
        object BrezZveze : Odgovor()
        /** Tabla je odgovorila in te vožnje danes ni na njej. */
        object NeVozi : Odgovor()
        /** Vožnja obstaja; zamuda je lahko tudi neznana. */
        data class Vozi(val zamudaS: Int?, val tripId: String?) : Odgovor()
    }

    fun preveri(c: Context, b: Budilka): Odgovor {
        // Okno okrog voznorednega odhoda, ne "od zdaj": budilka se preverja
        // pol ure prej, widget pa tudi uro prej, in obakrat mora biti odgovor
        // isti. Nazaj samo do polnoči -- čez njo je to drug prometni dan in
        // tabla ga zna dodati sama.
        val odhod = Instant.ofEpochMilli(b.voznoredniMs).atZone(ZoneId.systemDefault())
        val od = odhod.minusMinutes(30).let {
            if (it.toLocalDate() != odhod.toLocalDate()) odhod.toLocalDate().atStartOfDay(odhod.zone)
            else it
        }
        val url = buildString {
            append(Nastavitve.naslov(c)).append("/api/departures?station=")
            append(URLEncoder.encode(b.postaja, "UTF-8"))
            append("&date=").append(URLEncoder.encode(b.dan, "UTF-8"))
            append("&network=").append(if (b.vlak) "zeleznica" else "avtobus")
            append("&from=").append(URLEncoder.encode(od.format(URA), "UTF-8"))
            append("&window=120")
        }
        val besedilo = prenesi(url) ?: return Odgovor.BrezZveze
        return try {
            val vrstice = JSONObject(besedilo).optJSONArray("board") ?: return Odgovor.BrezZveze
            for (i in 0 until vrstice.length()) {
                val r = vrstice.getJSONObject(i)
                if (!jeNasa(r, b)) continue
                val z = r.optJSONObject("zamuda")
                val zamuda = if (z == null || z.isNull("s")) null else z.getInt("s")
                return Odgovor.Vozi(zamuda, r.optString("trip_id").ifBlank { null })
            }
            Odgovor.NeVozi
        } catch (e: org.json.JSONException) {
            Odgovor.BrezZveze
        }
    }

    /**
     * `trip_id` je edini zanesljiv ključ: LPP linija 3G ima 388 voženj in tudi
     * devet vlakov ima sezonske različice.
     *
     * Ponavljajoča budilka ga nima -- naslednji dan je vožnja druga -- zato je
     * takrat ključ **številka in voznoredna ura**. Po `stop_seq` se ne da:
     * sezonska različica iste linije ima lahko drugačen vrstni red postankov,
     * ura odhoda s te postaje pa je tista, ki jo je potnik izbral.
     */
    private fun jeNasa(r: JSONObject, b: Budilka): Boolean {
        if (!b.tripId.isNullOrBlank()) return r.optString("trip_id") == b.tripId
        if (r.optString("train_no") != b.trainNo) return false
        val sched = casMs(r.optString("sched")) ?: return r.optInt("stop_seq", -1) == b.stopSeq
        return abs(sched - b.voznoredniMs) <= UJEMANJE_MS
    }

    private fun casMs(iso: String?): Long? {
        if (iso.isNullOrBlank()) return null
        return try {
            OffsetDateTime.parse(iso).toInstant().toEpochMilli()
        } catch (e: java.time.format.DateTimeParseException) {
            null
        }
    }

    private fun prenesi(url: String): String? {
        var zveza: HttpURLConnection? = null
        return try {
            zveza = (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = CAKAJ_MS
                readTimeout = CAKAJ_MS
                requestMethod = "GET"
                // Cloudflare pred kajros.app zavrne zahteve brez verodostojnega
                // UA (izmerjeno: `Python-urllib` dobi 403). Povemo, kdo smo.
                setRequestProperty("User-Agent",
                    "Kajros/${BuildConfig.VERSION_NAME} (Android)")
                setRequestProperty("Accept", "application/json")
            }
            if (zveza.responseCode != 200) null
            else zveza.inputStream.bufferedReader().use { it.readText() }
        } catch (e: IOException) {
            // Ni omrežja, ni strežnika, potekel čas -- vse to je isti odgovor:
            // zamude ne poznamo. Kaj potem, ve `Ura`.
            null
        } finally {
            zveza?.disconnect()
        }
    }
}
