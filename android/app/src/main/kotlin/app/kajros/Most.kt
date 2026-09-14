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
     *
     * 2: ponavljajoce budilke (`dnevi`), `preklopi()` in `odpriBudilke()`.
     */
    @JavascriptInterface
    fun razlicica(): Int = if (nas()) 2 else 0

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
        // **Odhod, ki je ze mimo, ne dobi budilke.** Zazvonila bi v isti
        // sekundi in v prazno -- preizkuseno na LPP 19I stiri minute po
        // odhodu. Stran gumba za tak postanek ne pokaze; to je druga
        // varovalka, ker stran in APK nista nujno iste starosti.
        val dnevi = o.optInt("dnevi", 0) and Ponovitev.VSI
        val zdaj = System.currentTimeMillis()

        // **Prva ponovitev mora biti v izbranem naboru dni.**
        // Stran poslje uro voznje, ki jo je clovek gledal, in ta ni nujno na
        // dan iz nabora: izmerjeno 12. 9. 2026 -- izbrana tor + sre, stran je
        // kazala ponedeljek 14. 9., in budilka bi prvic zazvonila v ponedeljek,
        // torej zunaj vzorca. `prestavljena()` to popravi sele PO zvonjenju,
        // kar je prepozno.
        //
        // `poMs` je vecji od "sekundo pred voznjo" in "zdaj": prvo pusti
        // voznjo pri miru, kadar njen dan v naboru je, drugo poskrbi, da
        // voznja, ki je danes ze mimo, skoci na naslednji dan iz nabora.
        val vrP = if (Ponovitev.jePonavljajoca(dnevi)) {
            Ponovitev.naslednji(vr, dnevi, maxOf(vr - 1000L, zdaj))
        } else {
            vr
        }

        val odhod = vrP + o.optInt("zamuda_s", 0) * 1000L
        if (odhod <= zdaj) return ""

        val b = Budilka(
            id = "b" + System.currentTimeMillis() + "-" + (0..9999).random(),
            trainNo = o.optString("train_no"),
            tripId = if (o.isNull("trip")) null else o.optString("trip").ifBlank { null },
            omrezje = if (o.optString("omrezje") == "avtobus") "avtobus" else "zeleznica",
            postaja = o.optString("postaja"),
            stopSeq = o.optInt("stop_seq"),
            // Ko se ura premakne, se mora premakniti tudi prometni dan --
            // sicer bi `Preverjevalec` vprasal tablo za napacen datum.
            dan = if (vrP != vr) Ponovitev.dan(vrP) else o.optString("dan"),
            voznoredniMs = vrP,
            minutPrej = minut,
            zbudi = o.optBoolean("zbudi", true),
            // Rezerva je potnikova izbira, a ne sme biti orozje: pol ure
            // "rezerve" bi budilko spremenilo v nekaj drugega.
            rezervaS = o.optInt("rezerva_s", 0).coerceIn(0, 600),
            dnevi = dnevi,
            smer = o.optString("smer"),
        )
        Shramba.pocisti(dejavnost, zdaj)
        Shramba.shrani(dejavnost, b.copy(zvoniObMs = b.izracun(zdaj).zvoniOb))
        glavna.post { Nacrtovalec.nastavi(dejavnost, b, zdaj); Widget.osvezi(dejavnost) }
        return b.id
    }

    /**
     * Kdaj bi budilka s temi nastavitvami zazvonila -- **brez** shranjevanja.
     *
     * Racun je v Kotlinu in ne v strani namenoma: `Ura` je edini kraj, ki ve,
     * kaj se zgodi z negativno zamudo pri vlaku in kaj ob izpadu povezave.
     * Dvojnik tega pravila v JavaScriptu bi se prej ali slej razsel s tistim,
     * kar budilka res naredi -- in prikaz bi obljubljal uro, ki je ne bo.
     */
    @JavascriptInterface
    fun napoved(zapis: String): String {
        if (!nas()) return "{}"
        val o = try { JSONObject(zapis) } catch (e: org.json.JSONException) { return "{}" }
        val vr = o.optLong("voznoredni_ms")
        if (vr <= 0) return "{}"
        val zdaj = System.currentTimeMillis()
        val izid = Ura.izracunaj(
            voznoredniMs = vr,
            minutPrej = o.optInt("minut_prej", 25),
            zamudaS = if (o.isNull("zamuda_s")) null else o.optInt("zamuda_s"),
            zamudaObMs = zdaj,
            zdajMs = zdaj,
            vlak = o.optString("omrezje") != "avtobus",
            rezervaS = o.optInt("rezerva_s", 0).coerceIn(0, 600),
            // Stran je podatke pravkar dobila s streznika: to je stik, tudi
            // kadar zamude v njih ni.
            stikObMs = zdaj,
        )
        return JSONObject()
            .put("zvoni_ob_ms", izid.zvoniOb)
            .put("odhod_ms", izid.odhodMs)
            .put("upostevana_s", izid.upostevanaS)
            .toString()
    }

    @JavascriptInterface
    fun seznam(): String {
        if (!nas()) return "[]"
        val zdaj = System.currentTimeMillis()
        val a = JSONArray()
        // Domača stran kaže naslednjo budilko z odhodom in zamudo. Račun je
        // tu, ne v strani: ista odločitev kot pri zvonjenju (glej `napoved`).
        Shramba.vse(dejavnost).sortedBy { it.voznoredniMs }.forEach {
            val izid = it.izracun(zdaj)
            a.put(it.json()
                .put("zvoni_ob_ms", izid.zvoniOb)
                .put("odhod_ms", izid.odhodMs)
                .put("upostevana_s", izid.upostevanaS)
                .put("vir", izid.vir.name.lowercase()))
        }
        return a.toString()
    }

    /** Vklopi ali ugasne budilko, ne da bi jo izbrisal. */
    @JavascriptInterface
    fun preklopi(id: String, vklop: Boolean): Boolean {
        if (!nas()) return false
        val b = Shramba.ena(dejavnost, id) ?: return false
        Shramba.shrani(dejavnost, b.copy(ugasnjena = !vklop))
        glavna.post { Nacrtovalec.vseZnova(dejavnost) }
        return true
    }

    /**
     * Nativni seznam budilk.
     *
     * Doslej je bil dosegljiv samo z dolgim pritiskom na ikono -- gesta, ki jo
     * pozna Android, ne pa nujno clovek, ki aplikacijo uporablja. Zdaj je do
     * njega povezava v glavi strani.
     */
    @JavascriptInterface
    fun odpriBudilke() {
        if (!nas()) return
        glavna.post {
            dejavnost.startActivity(
                android.content.Intent(dejavnost, BudilkeDejavnost::class.java))
        }
    }

    @JavascriptInterface
    fun odstrani(id: String): Boolean {
        if (!nas()) return false
        Shramba.odstrani(dejavnost, id)
        glavna.post { Nacrtovalec.preklici(dejavnost, id); Widget.osvezi(dejavnost) }
        return true
    }

    /** Kaj sistem trenutno dovoli. Stran naj gumba ne ponuja, ce ne bo delal. */
    @JavascriptInterface
    fun dovoljenja(): String {
        if (!nas()) return "{}"
        return JSONObject()
            .put("obvestila", GlavnaDejavnost.smeObvescati(dejavnost))
            .put("tocni_alarmi", Nacrtovalec.smeTocenAlarm(dejavnost))
            .put("cel_zaslon", Zvonjenje.smeCelZaslon(dejavnost))
            .toString()
    }

    @JavascriptInterface
    fun zahtevajDovoljenja() {
        if (!nas()) return
        glavna.post { (dejavnost as? GlavnaDejavnost)?.zahtevajZaBudilko() }
    }
}
