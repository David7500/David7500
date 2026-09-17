package app.kajros

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

/**
 * Odhodna tabla ene postaje za widget: nastavitev, prenos in shramba.
 *
 * **Zakaj tu in ne v `Preverjevalec`.** Ta vprasa po ENI voznji, ker to rabi
 * budilka; widget vprasa po postaji in vzame prve tri. Odgovor je isti
 * endpoint (`/api/departures`) in to ni nakljucje: to je tabla, ki jo potnik
 * vidi na strani, in nobena druga stevilka ne sme biti na widgetu.
 *
 * Racun je ves na strezniku. `zamuda.min`, `zamuda.razred` in
 * `zamuda.prezgodaj` pridejo izracunani (`stats.opis_zamude()`); Android jih
 * samo izpise. **Zaokrozevanja ne sme ponoviti**: `kotlin.math.round` zaokrozi
 * pol na sodo in bi se pri 30 s razsel s stranjo.
 */
object Tabla {

    private const val DATOTEKA = "tabla"
    private const val CAKAJ_MS = 5000
    /** Kolikor vrstic gre na widget. */
    const val VRSTIC = 3
    /** Koliko naprej vprasamo. Manj bi pri redki progi vrnilo prazno tablo. */
    private const val OKNO_MIN = 240

    private val URA = DateTimeFormatter.ofPattern("HH:mm")

    /** Ena vrstica table, ze pripravljena za izpis. */
    data class Odhod(
        val ura: String,
        val kam: String,
        val trainNo: String,
        val tripId: String?,
        /** Zaokrozena minuta s streznika, ali null, kadar zamuda se ni znana. */
        val zamudaMin: Int?,
        /** `tocno`, `1-5`, `5-15`, `nad-15` -- kljuc razreda s streznika. */
        val razred: String?,
        val prezgodaj: Boolean,
    )

    /** Kaj widget kaze in od kdaj. */
    data class Stanje(val odhodi: List<Odhod>, val obMs: Long)

    // ---------- nastavitev widgeta ----------

    /**
     * Postaja in omrezje tega widgeta.
     *
     * Na widget se shrani oboje, ker je **ime postaje brez omrezja dvoumno**:
     * "Ljubljana" je zeleznisko vozlisce in hkrati mestno postajalisce, in
     * privzeta zeleznica bi avtobusnemu potniku tiho vrnila drugo tablo.
     */
    data class Nastavitev(val postaja: String, val omrezje: String) {
        val vlak: Boolean get() = omrezje == "zeleznica"
    }

    fun nastavi(c: Context, widgetId: Int, n: Nastavitev) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .putString("postaja_$widgetId", n.postaja)
            .putString("omrezje_$widgetId", n.omrezje)
            .apply()
    }

    fun nastavitev(c: Context, widgetId: Int): Nastavitev? {
        val p = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
        val postaja = p.getString("postaja_$widgetId", null) ?: return null
        return Nastavitev(postaja, p.getString("omrezje_$widgetId", "zeleznica")!!)
    }

    /** Widget je odstranjen z zaslona; njegova nastavitev nima vec lastnika. */
    fun pozabi(c: Context, widgetId: Int) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .remove("postaja_$widgetId")
            .remove("omrezje_$widgetId")
            .remove("stanje_$widgetId")
            .apply()
    }

    // ---------- shramba zadnjega odgovora ----------
    //
    // Widget se prerise tudi takrat, ko omrezja ni (sistem ga zbudi, zaslon se
    // prizge). Brez shrambe bi takrat obvisel prazen -- zato pokaze zadnje, kar
    // ve, IN uro tistega odgovora. Stara stevilka z uro je podatek, stara
    // stevilka brez ure je laz.

    fun shraniStanje(c: Context, widgetId: Int, s: Stanje) {
        val a = JSONArray()
        s.odhodi.forEach { o ->
            a.put(JSONObject().apply {
                put("ura", o.ura); put("kam", o.kam); put("train_no", o.trainNo)
                put("trip", o.tripId ?: JSONObject.NULL)
                put("min", o.zamudaMin ?: JSONObject.NULL)
                put("razred", o.razred ?: JSONObject.NULL)
                put("prezgodaj", o.prezgodaj)
            })
        }
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .putString("stanje_$widgetId",
                JSONObject().put("ob", s.obMs).put("odhodi", a).toString())
            .apply()
    }

    fun stanje(c: Context, widgetId: Int): Stanje? {
        val niz = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .getString("stanje_$widgetId", null) ?: return null
        return try {
            val o = JSONObject(niz)
            val a = o.optJSONArray("odhodi") ?: JSONArray()
            Stanje((0 until a.length()).map { i ->
                val r = a.getJSONObject(i)
                Odhod(
                    ura = r.optString("ura"),
                    kam = r.optString("kam"),
                    trainNo = r.optString("train_no"),
                    tripId = if (r.isNull("trip")) null else r.optString("trip"),
                    zamudaMin = if (r.isNull("min")) null else r.getInt("min"),
                    razred = if (r.isNull("razred")) null else r.optString("razred"),
                    prezgodaj = r.optBoolean("prezgodaj"),
                )
            }, o.optLong("ob"))
        } catch (e: org.json.JSONException) {
            null
        }
    }

    // ---------- besede in starost ----------
    //
    // Cist JVM in zato preizkuseno brez naprave. Pravilo o besedi je isto kot
    // na strani (`common.delayText`): minus pred stevilko je uganka, beseda ni.

    /**
     * Zamuda, kot jo widget izpise.
     *
     * Minuta pride s streznika ze zaokrozena; tu se samo odloci beseda. Kadar
     * zamude se ni, je to **pomisljaj in ne nicla** -- "tocno" za voznjo, o
     * kateri feed se ni rekel nicesar, bi bila trditev, ki je nimamo.
     */
    fun zamudaNapis(o: Odhod): String {
        val m = o.zamudaMin ?: return "—"
        if (o.prezgodaj) return "${-m} prej"
        if (m <= 0) return "točno"
        return "+$m"
    }

    /** Koliko minut je star podatek. */
    fun starostMin(obMs: Long, zdajMs: Long): Int =
        if (obMs <= 0) Int.MAX_VALUE
        else Math.max(0, Math.round((zdajMs - obMs) / 60_000.0).toInt())

    /**
     * Ali je podatek toliko star, da mora widget to povedati z besedo.
     *
     * Dva koraka osvezevanja (2 x 15 min): en izpusceni cikel je Doze in ne
     * okvara, dva pa sta nekaj, kar mora potnik vedeti, preden se zanese na
     * stevilko.
     */
    fun jeStaro(obMs: Long, zdajMs: Long): Boolean = starostMin(obMs, zdajMs) > 30

    // ---------- prenos ----------

    /**
     * Kaj je streznik povedal. **Trije izidi, ne dva.**
     *
     * "Ni zveze" in "te postaje ni" sta razlicni novici in ju ne sme zdruziti
     * nihce: prvo je zacasno in postaje ne sme zavreci, drugo je tipkarska
     * napaka in jo mora nastavitev povedati takoj. Ista razlika kot v
     * `Preverjevalec.Odgovor`.
     *
     * Prazna tabla je tretji izid in ne napaka: pozno zvecer od tod res ne
     * pelje nic vec.
     */
    sealed class Izid {
        object BrezZveze : Izid()
        object NiPostaje : Izid()
        data class Odhodi(val vrstice: List<Odhod>) : Izid()
    }

    /** Prve [VRSTIC] vrstice odhodne table te postaje. */
    fun prenesi(c: Context, n: Nastavitev): Izid {
        val url = buildString {
            append(Nastavitve.naslov(c)).append("/api/departures?station=")
            append(URLEncoder.encode(n.postaja, "UTF-8"))
            append("&network=").append(n.omrezje)
            append("&window=").append(OKNO_MIN)
        }
        val (koda, besedilo) = prenesi(url)
        if (koda == 404) return Izid.NiPostaje
        if (besedilo == null) return Izid.BrezZveze
        return try {
            val a = JSONObject(besedilo).optJSONArray("board") ?: return Izid.BrezZveze
            Izid.Odhodi((0 until minOf(a.length(), VRSTIC))
                .map { vrstica(a.getJSONObject(it)) })
        } catch (e: org.json.JSONException) {
            Izid.BrezZveze
        }
    }

    private fun vrstica(r: JSONObject): Odhod {
        val z = r.optJSONObject("zamuda")
        return Odhod(
            ura = ura(r.optString("sched")),
            // `towards` je smer s TE postaje in ne konec proge: vlak, ki vozi
            // naprej, ima oboje razlicno, potnik pa bere prvo.
            kam = r.optString("towards").ifBlank { r.optString("destination") },
            trainNo = r.optString("train_no"),
            tripId = r.optString("trip_id").ifBlank { null },
            zamudaMin = if (z == null || z.isNull("min")) null else z.getInt("min"),
            razred = z?.optString("razred")?.ifBlank { null },
            prezgodaj = z?.optBoolean("prezgodaj") ?: false,
        )
    }

    private fun ura(iso: String?): String {
        if (iso.isNullOrBlank()) return "--:--"
        return try {
            OffsetDateTime.parse(iso).atZoneSameInstant(ZoneId.systemDefault()).format(URA)
        } catch (e: DateTimeParseException) {
            "--:--"
        }
    }

    /** Koda odgovora in telo. Koda je 0, kadar odgovora sploh ni bilo. */
    private fun prenesi(url: String): Pair<Int, String?> {
        var zveza: HttpURLConnection? = null
        return try {
            zveza = (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = CAKAJ_MS
                readTimeout = CAKAJ_MS
                requestMethod = "GET"
                // Cloudflare pred kajros.app zavrne zahteve brez verodostojnega
                // UA -- isto kot v `Preverjevalec`.
                setRequestProperty("User-Agent",
                    "Kajros/${BuildConfig.VERSION_NAME} (Android)")
                setRequestProperty("Accept", "application/json")
            }
            val koda = zveza.responseCode
            koda to (if (koda != 200) null
                     else zveza.inputStream.bufferedReader().use { it.readText() })
        } catch (e: IOException) {
            0 to null
        } finally {
            zveza?.disconnect()
        }
    }
}
