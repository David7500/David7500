package app.kajros

import android.content.BroadcastReceiver
import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Base64
import android.webkit.MimeTypeMap
import org.json.JSONObject
import java.io.File

/**
 * „Pošlji z …“ za stran: sistemski izbirnik, ki ga WebView nima.
 *
 * **Most je spletni standard, ne povabilo.** Stran kliče `navigator.share`
 * kot v brskalniku (`common.js` ga v aplikaciji nadomesti z
 * [Most.poslji]), APK pa o besedilu, povezavi in gumbih ne ve ničesar. Novo
 * besedilo, nov gumb ali nova stran za pošiljanje ne rabi nove različice
 * aplikacije -- ta pride do ljudi s tedni zamika (David, 13. 10. 2026).
 *
 * Zato tudi **datoteke** (Web Share Level 2: slike za Instagram, PDF).
 * Ob 1.13 jih ne pošlje še nobena stran; tu so, ker bi jih sicer prvi
 * gumb, ki jih rabi, moral čakati na novo aplikacijo.
 */
object Posiljanje {

    /** Pod tem imenom jih [Datoteke] streže prejemniku. */
    const val AVTORITETA = "app.kajros.datoteke"

    /** Id pošiljanja, ki čaka na izid, in id zadnjega izbranega. Piše jih
     *  glavna nit in sprejemnik, ki tudi teče na glavni. */
    @Volatile var caka: String? = null
    @Volatile var izbran: String? = null

    /** Največ datotek in bajtov v enem pošiljanju. Vse gre skozi most kot
     *  base64 v enem nizu; 10 MB je slika ali kratek posnetek, ne arhiv. */
    const val NAJVEC_DATOTEK = 10
    const val NAJVEC_BAJTOV = 10L * 1024 * 1024

    /** Stare datoteke gredo ob naslednjem pošiljanju; prejemnik jih do takrat
     *  že ima (WhatsApp jih kopira ob pošiljanju). */
    private const val ZIVI_MS = 10 * 60_000L

    /** Kot Chrome na Androidu: besedilo in pod njim povezava, ena vrstica
     *  sporočila. Brez obojega ni česa poslati. */
    fun besedilo(text: String?, url: String?): String? {
        val deli = listOf(text, url).map { it?.trim().orEmpty() }.filter { it.isNotEmpty() }
        return deli.joinToString("\n").ifEmpty { null }
    }

    /**
     * Ime datoteke, kot ga sme videti prejemnik, ali `null`. Ime pride s
     * strani in gre v pot na disku -- `../` ali `/` bi pisal drugam.
     */
    fun varnoIme(ime: String?): String? {
        val cisto = ime.orEmpty()
            .replace(Regex("[^\\p{L}\\p{N}._ -]"), "_")
            .trimStart('.', ' ')
            .take(100)
            .trimEnd()
        return cisto.ifEmpty { null }
    }

    /** Velikost po dekodiranju base64, brez dekodiranja. */
    fun bajtov(base64: String): Long {
        val dolzina = base64.trimEnd('=').length.toLong()
        return dolzina * 3 / 4
    }

    fun prevec(velikosti: List<Long>): Boolean =
        velikosti.size > NAJVEC_DATOTEK || velikosti.sum() > NAJVEC_BAJTOV

    fun mapa(c: Context): File = File(c.cacheDir, "poslji")

    /** `optString` vrne za JSON `null` niz „null“; stran sme polje izpustiti
     *  ali ga poslati kot `null`, oboje pomeni „ni“. */
    private fun JSONObject.niz(k: String): String? = if (isNull(k)) null else optString(k)

    /**
     * Namera za izbirnik iz zapisa v obliki Web Share (`title`, `text`, `url`,
     * `files` z `name`, `type`, `data` v base64), ali `null`, kadar ni česa
     * poslati ali je datotek preveč.
     */
    fun namera(c: Context, o: JSONObject): Intent? {
        val besedilo = besedilo(o.niz("text"), o.niz("url"))
        val seznam = o.optJSONArray("files")
        val datoteke = (0 until (seznam?.length() ?: 0)).mapNotNull { seznam?.optJSONObject(it) }
        if (prevec(datoteke.map { bajtov(it.optString("data")) })) return null
        val uri = shrani(c, datoteke) ?: return null
        if (besedilo == null && uri.isEmpty()) return null

        val n = if (uri.size > 1) {
            Intent(Intent.ACTION_SEND_MULTIPLE).putParcelableArrayListExtra(Intent.EXTRA_STREAM, ArrayList(uri))
        } else {
            Intent(Intent.ACTION_SEND).also { if (uri.isNotEmpty()) it.putExtra(Intent.EXTRA_STREAM, uri[0]) }
        }
        n.type = when {
            uri.isEmpty() -> "text/plain"
            else -> skupnaVrsta(datoteke.map { it.optString("type") })
        }
        besedilo?.let { n.putExtra(Intent.EXTRA_TEXT, it) }
        o.niz("title")?.trim()?.takeIf { it.isNotEmpty() }?.let { n.putExtra(Intent.EXTRA_SUBJECT, it) }
        if (uri.isNotEmpty()) {
            // Dovoljenje za branje gre skozi izbirnik samo prek `ClipData`.
            val clip = ClipData.newRawUri(null, uri[0])
            uri.drop(1).forEach { clip.addItem(ClipData.Item(it)) }
            n.clipData = clip
            n.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        return n
    }

    /** Vrsta namere: ena vrsta ostane, dve sliki različnih vrst sta „katera
     *  koli slika“, slika in PDF skupaj „karkoli“. (Zvezdice v komentarju
     *  Kotlin bere kot začetek gnezdenega komentarja.) */
    fun skupnaVrsta(vrste: List<String>): String {
        val ciste = vrste.map { it.ifEmpty { "application/octet-stream" } }.distinct()
        if (ciste.size == 1) return ciste[0]
        val glavne = ciste.map { it.substringBefore('/') }.distinct()
        return if (glavne.size == 1) "${glavne[0]}/*" else "*/*"
    }

    /** Zapiše datoteke v svojo mapo, vrne njihove naslove; `null` ob napaki. */
    private fun shrani(c: Context, datoteke: List<JSONObject>): List<Uri>? {
        val koren = mapa(c)
        val zdaj = System.currentTimeMillis()
        koren.listFiles()?.filter { zdaj - it.lastModified() > ZIVI_MS }?.forEach { it.deleteRecursively() }
        return datoteke.mapIndexed { i, d ->
            val bajti = try {
                Base64.decode(d.optString("data"), Base64.DEFAULT)
            } catch (e: IllegalArgumentException) {
                return null
            }
            val vrsta = d.optString("type")
            var ime = varnoIme(d.optString("name")) ?: "datoteka"
            // Prejemnik vrsto pogosto ugane iz končnice, `getType` pa jo iz nje
            // prebere: brez končnice bi bila slika „application/octet-stream“.
            MimeTypeMap.getSingleton().getExtensionFromMimeType(vrsta)?.let {
                if (!ime.lowercase().endsWith(".$it")) ime = "$ime.$it"
            }
            val podmapa = "$zdaj-$i"
            val f = File(File(koren, podmapa).also { it.mkdirs() }, ime)
            f.writeBytes(bajti)
            Uri.Builder().scheme("content").authority(AVTORITETA)
                .appendPath(podmapa).appendPath(ime).build()
        }
    }
}

/**
 * Izbirnik ga pokliče, ko potnik izbere, komu pošlje ([GlavnaDejavnost.poslji]).
 * Preklica izbirnik ne javi -- vrnitev brez tega klica je preklic. Namero
 * sestavimo mi (`PendingIntent`), zato ni izvožen.
 */
class PoslanoSprejemnik : BroadcastReceiver() {
    companion object { const val ID = "id" }

    override fun onReceive(c: Context, n: Intent) {
        Posiljanje.izbran = n.getStringExtra(ID)
    }
}
