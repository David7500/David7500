package app.kajros

import android.app.Activity
import android.os.Handler
import android.os.Looper
import android.webkit.JavascriptInterface
import org.json.JSONArray
import org.json.JSONObject

/**
 * Edina vez med stranjo in aplikacijo. `window.Kajros` obstaja samo tu, zato
 * spletni gumb za budilko v brskalniku sploh ne nastane.
 *
 * **Ta razred je viden vsaki strani, ki jo WebView nalozi.** Zato vsaka metoda
 * najprej vprasa, ali je stran nasa. Metode tecejo na WebViewovi niti, ne na
 * glavni, in `webView.url` od tam ni dovoljeno brati -- izvor zato belezi
 * dejavnost ob vsakem nalaganju in ga tu samo preberemo.
 */
class Most(
    private val dejavnost: Activity,
    private val naslov: () -> String,
) {

    /** Zadnji nalozeni naslov. Pise ga glavna nit, bere WebViewova. */
    @Volatile
    var trenutniUrl: String? = null

    private val glavna = Handler(Looper.getMainLooper())

    private fun nas(): Boolean = Nastavitve.jeNas(trenutniUrl, naslov())

    /**
     * Razlicica mostu. Stran in APK se lahko razideta -- uporabnik posodobi
     * stran takoj, aplikacijo pa cez mesec -- zato mora stran vedeti, s cim
     * govori, preden poklice karkoli drugega.
     */
    @JavascriptInterface
    fun razlicica(): Int = if (nas()) 1 else 0

    /** Vrne id nove budilke ali prazen niz. */
    @JavascriptInterface
    fun nastavi(zapis: String): String {
        if (!nas()) return ""
        val o = try { JSONObject(zapis) } catch (e: org.json.JSONException) { return "" }
        val vr = o.optLong("voznoredni_ms")
        val minut = o.optInt("minut_prej", -1)
        // Stran sme poslati smeti; budilka brez ure ali brez postanka ni budilka.
        if (vr <= 0 || minut < 0 || minut > 24 * 60) return ""
        if (o.optInt("stop_seq", -1) < 0) return ""

        val b = Budilka(
            id = "b" + System.currentTimeMillis() + "-" + (0..9999).random(),
            trainNo = o.optString("train_no"),
            tripId = if (o.isNull("trip")) null else o.optString("trip").ifBlank { null },
            omrezje = if (o.optString("omrezje") == "avtobus") "avtobus" else "zeleznica",
            postaja = o.optString("postaja"),
            stopSeq = o.optInt("stop_seq"),
            dan = o.optString("dan"),
            voznoredniMs = vr,
            minutPrej = minut,
            zbudi = o.optBoolean("zbudi", true),
            smer = o.optString("smer"),
        )
        val zdaj = System.currentTimeMillis()
        Shramba.pocisti(dejavnost, zdaj)
        Shramba.shrani(dejavnost, b.copy(zvoniObMs = b.izracun(zdaj).zvoniOb))
        glavna.post { Nacrtovalec.nastavi(dejavnost, b, zdaj) }
        return b.id
    }

    @JavascriptInterface
    fun seznam(): String {
        if (!nas()) return "[]"
        val zdaj = System.currentTimeMillis()
        val a = JSONArray()
        Shramba.vse(dejavnost).sortedBy { it.voznoredniMs }.forEach {
            a.put(it.json().put("zvoni_ob_ms", it.izracun(zdaj).zvoniOb))
        }
        return a.toString()
    }

    @JavascriptInterface
    fun odstrani(id: String): Boolean {
        if (!nas()) return false
        Shramba.odstrani(dejavnost, id)
        glavna.post { Nacrtovalec.preklici(dejavnost, id) }
        return true
    }

    /** Kaj sistem trenutno dovoli. Stran naj gumba ne ponuja, ce ne bo delal. */
    @JavascriptInterface
    fun dovoljenja(): String {
        if (!nas()) return "{}"
        return JSONObject()
            .put("obvestila", GlavnaDejavnost.smeObvescati(dejavnost))
            .put("tocni_alarmi", Nacrtovalec.smeTocenAlarm(dejavnost))
            .toString()
    }

    @JavascriptInterface
    fun zahtevajDovoljenja() {
        if (!nas()) return
        glavna.post { (dejavnost as? GlavnaDejavnost)?.zahtevajZaBudilko() }
    }
}
