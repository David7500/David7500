package app.kajros

import android.content.Context
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

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

    /** Zamuda v sekundah, ali null, če ni bilo mogoče izvedeti. */
    fun zamuda(c: Context, b: Budilka): Int? {
        val url = buildString {
            append(Nastavitve.naslov(c)).append("/api/departures?station=")
            append(URLEncoder.encode(b.postaja, "UTF-8"))
            append("&date=").append(URLEncoder.encode(b.dan, "UTF-8"))
            append("&network=").append(if (b.vlak) "zeleznica" else "avtobus")
        }
        val besedilo = prenesi(url) ?: return null
        return try {
            val vrstice = JSONObject(besedilo).optJSONArray("board") ?: return null
            for (i in 0 until vrstice.length()) {
                val r = vrstice.getJSONObject(i)
                if (!jeNasa(r, b)) continue
                val z = r.optJSONObject("zamuda") ?: return null
                return if (z.isNull("s")) null else z.getInt("s")
            }
            null
        } catch (e: org.json.JSONException) {
            null
        }
    }

    /**
     * `trip_id` je edini zanesljiv ključ: LPP linija 3G ima 388 voženj in tudi
     * devet vlakov ima sezonske različice. Številka vožnje je nadomestek le
     * takrat, kadar id-ja nimamo.
     */
    private fun jeNasa(r: JSONObject, b: Budilka): Boolean {
        if (!b.tripId.isNullOrBlank()) return r.optString("trip_id") == b.tripId
        return r.optString("train_no") == b.trainNo && r.optInt("stop_seq", -1) == b.stopSeq
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
