package app.kajros

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Katera postaja gre na widget z odhodno tablo -- pri avtobusih katera stran
 * ceste, in po zelji cilj, ki tablo spremeni v relacijo.
 *
 * **Postaja se izbere, ne vtipka** (22. 9. 2026). Doslej je bilo treba ime
 * napisati na pamet in widget je shranil kar vnos ("bavarski"). Zdaj vnos samo
 * isce (`/api/stations/search`, isto kot predlogi na strani), shrani pa se
 * lahko samo ime, ki ga je vrnil streznik. Isto velja za cilj.
 *
 * **Postaje ni mogoce shraniti, ne da bi jo prej nasli.** Gumb vprasa
 * streznik za tablo (ali zveze do cilja) in shrani sele, ko ta res pride --
 * widget, ki bi ostal prazen, je za potnika okvara aplikacije in ne napaka
 * izpred treh dni.
 *
 * Svojega seznama postaj v telefonu ni: imena in vrstni red pozna streznik.
 * Seznam v telefonu bi bil drugo pravilo za isto stvar in bi se ob naslednjem
 * uvozu voznega reda razsel.
 */
class TablaNastavitev : Activity() {

    companion object {
        /** Toliko po zadnji tipki se vprasa streznik -- ne ob vsaki crki. */
        private const val PREMOR_MS = 250L
        /** Kot na strani: ena crka ujame tisoce postajalisc in ne pove nic. */
        private const val NAJMANJ_CRK = 2
    }

    private var widgetId = AppWidgetManager.INVALID_APPWIDGET_ID
    private var omrezje = "zeleznica"
    private var videz = Izris.Videz.TONSKA
    private val glavna = Handler(Looper.getMainLooper())

    private var smeri: List<Tabla.Smer> = emptyList()
    private var izbranaSmer: String? = null

    private val smeriOkvir by lazy { findViewById<LinearLayout>(R.id.smeri) }
    private val shrani by lazy { findViewById<Button>(R.id.shrani) }
    private val oznaka by lazy { findViewById<EditText>(R.id.oznaka) }

    private lateinit var postaja: Iskalnik
    private lateinit var cilj: Iskalnik

    /**
     * Polje, ki isce postajo na strezniku in pod sabo kaze predloge. Na
     * zaslonu sta dve: izhodisce in neobvezen cilj.
     *
     * [ime] je ime, kot ga je vrnil streznik, ali null, dokler ni izbrano.
     */
    private inner class Iskalnik(
        val vnos: EditText,
        val zadetki: LinearLayout,
        val izbrano: (String) -> Unit,
        val spremenjeno: () -> Unit,
    ) {
        var ime: String? = null
        /** Zaporedna stevilka iskanja: odgovor na staro tipkanje se zavrze. */
        private var iskanje = 0
        /** Besedilo v polje pise tudi program; takrat to ni novo iskanje. */
        private var tiho = false
        private val isci = Runnable { isciZdaj() }

        init {
            vnos.addTextChangedListener(object : TextWatcher {
                override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, d: Int) {}
                override fun onTextChanged(s: CharSequence?, a: Int, b: Int, d: Int) {}
                override fun afterTextChanged(s: Editable?) {
                    if (tiho) return
                    // Popravljeno ime ni vec izbrana postaja -- in stran ceste
                    // tiste postaje ne velja za drugo.
                    ime = null
                    spremenjeno()
                    glavna.removeCallbacks(isci)
                    glavna.postDelayed(isci, PREMOR_MS)
                }
            })
            // "Koncano" na tipkovnici vzame prvi predlog: to je tisti, ki bi ga
            // clovek tako ali tako izbral, in brez tega tipka ne naredi nicesar.
            vnos.setOnEditorActionListener { _, akcija, _ ->
                if (akcija != EditorInfo.IME_ACTION_DONE) return@setOnEditorActionListener false
                (zadetki.getChildAt(0) as? TextView)?.let { izberi(it.text.toString()) }
                true
            }
        }

        val prazen: Boolean get() = vnos.text.isNullOrBlank()

        fun isciZdaj() {
            val q = vnos.text.toString().trim()
            val moje = ++iskanje
            if (ime != null || q.length < NAJMANJ_CRK) {
                zadetki.removeAllViews()
                return
            }
            val kje = omrezje
            // Omrezje na svoji niti; cakanje na glavni bi bila zamrznjena tipkovnica.
            Thread {
                val imena = Tabla.isci(this@TablaNastavitev, q, kje)
                glavna.post {
                    if (moje != iskanje || isFinishing) return@post
                    pokaziZadetke(imena)
                }
            }.start()
        }

        private fun pokaziZadetke(imena: List<String>?) {
            zadetki.removeAllViews()
            when {
                imena == null -> povej(R.string.tabla_ni_zveze, R.color.sev_bad)
                imena.isEmpty() -> povej(R.string.tabla_ni_postaje, R.color.sev_bad)
                else -> skrijIzid()
            }
            imena?.forEach { ime ->
                val v = layoutInflater.inflate(R.layout.tabla_zadetek, zadetki, false) as TextView
                v.text = ime
                v.setOnClickListener { izberi(ime) }
                zadetki.addView(v)
            }
        }

        fun izberi(novo: String) {
            ime = novo
            tiho = true
            vnos.setText(novo)
            vnos.setSelection(novo.length)
            tiho = false
            iskanje++
            zadetki.removeAllViews()
            getSystemService(InputMethodManager::class.java)
                ?.hideSoftInputFromWindow(vnos.windowToken, 0)
            izbrano(novo)
        }

        /** Drugo omrezje: isto ime je tam druga postaja (ali je sploh ni). */
        fun znova() {
            ime = null
            isciZdaj()
        }
    }

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        // **Najprej preklic.** Kdor okno zapre z gumbom nazaj, widgeta ni
        // narocil; brez tega bi na zaslonu ostal prazen pravokotnik.
        setResult(RESULT_CANCELED)
        setContentView(R.layout.tabla_nastavitev)

        widgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
            ?: AppWidgetManager.INVALID_APPWIDGET_ID
        if (widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) { finish(); return }

        postaja = Iskalnik(findViewById(R.id.postaja), findViewById(R.id.zadetki),
            izbrano = { naIzbiroPostaje(it) }, spremenjeno = { pozabiIzbiro() })
        cilj = Iskalnik(findViewById(R.id.cilj), findViewById(R.id.zadetki_cilj),
            izbrano = { narisiSmeri(); osveziGumb() }, spremenjeno = { narisiSmeri(); osveziGumb() })

        findViewById<Button>(R.id.vlak).setOnClickListener { izberiOmrezje("zeleznica") }
        findViewById<Button>(R.id.avtobus).setOnClickListener { izberiOmrezje("avtobus") }
        findViewById<Button>(R.id.videz_tonska).setOnClickListener { izberiVidez(Izris.Videz.TONSKA) }
        findViewById<Button>(R.id.videz_brez).setOnClickListener { izberiVidez(Izris.Videz.BREZ) }
        shrani.setOnClickListener { poisciInShrani() }

        // Ze nastavljen widget: pokaze, kaj je v njem, da ga je mogoce
        // popraviti in ne le prepisati na slepo.
        val prej = Tabla.nastavitev(this, widgetId)
        if (prej != null) {
            omrezje = prej.omrezje
            videz = prej.videz
        }
        izberiVidez(videz)
        izberiOmrezje(omrezje, ohraniVnos = true)
        if (prej != null) {
            prej.oznaka?.let { oznaka.setText(it) }
            prej.cilj?.let { cilj.izberi(it) }
            postaja.izberi(prej.postaja)
            // Izbira postaje stran ceste pozabi; shranjena se vrne, preden
            // pride seznam strani -- ta jo obdrži, če jo še pozna.
            izbranaSmer = prej.smer
        } else {
            osveziGumb()
        }
    }

    private fun izberiOmrezje(kaj: String, ohraniVnos: Boolean = false) {
        val zamenjava = kaj != omrezje
        omrezje = kaj
        val vlak = kaj == "zeleznica"
        // Izbrano je polno, drugo prazno. Brez te razlike je na zaslonu dvoje
        // enakih gumbov in nobeden ne pove, kaj velja.
        oznaci(findViewById(R.id.vlak), vlak)
        oznaci(findViewById(R.id.avtobus), !vlak)
        postaja.vnos.setHint(if (vlak) R.string.tabla_postaja else R.string.tabla_postajalisce)
        cilj.vnos.setHint(if (vlak) R.string.tabla_cilj_vnos else R.string.tabla_cilj_vnos_bus)
        if (zamenjava && !ohraniVnos) {
            // Isto ime je na drugem omrezju druga postaja (ali je sploh ni):
            // izbira ne velja, iskanje pa gre znova po novem omrezju.
            pozabiIzbiro()
            postaja.znova()
            cilj.znova()
        }
    }

    private fun izberiVidez(kaj: Izris.Videz) {
        videz = kaj
        oznaci(findViewById(R.id.videz_tonska), kaj == Izris.Videz.TONSKA)
        oznaci(findViewById(R.id.videz_brez), kaj == Izris.Videz.BREZ)
    }

    private fun oznaci(b: Button, vklop: Boolean) {
        b.setBackgroundResource(if (vklop) R.drawable.gumb else R.drawable.gumb_tih)
        b.setTextColor(getColor(if (vklop) R.color.na_poudarku else R.color.ink_dim))
    }

    // ---------- izbira ----------

    /**
     * Postaja je izbrana. Tabla se prenese takoj: pove, ali ima postajalisce
     * vec strani ceste -- in ce odgovora ni, je bolje to vedeti zdaj kot ob
     * shranjevanju.
     */
    private fun naIzbiroPostaje(ime: String) {
        izbranaSmer = null
        smeri = emptyList()
        narisiSmeri()
        osveziGumb()

        if (omrezje != "avtobus") { skrijIzid(); return }
        povej(R.string.tabla_iscem, R.color.ink_dim)
        val n = Tabla.Nastavitev(ime, omrezje)
        Thread {
            val izid = Tabla.prenesi(this, n)
            glavna.post {
                if (postaja.ime != ime || isFinishing) return@post
                when (izid) {
                    is Tabla.Izid.Odhodi -> {
                        skrijIzid()
                        smeri = izid.smeri
                        if (smeri.none { it.kljuc == izbranaSmer }) izbranaSmer = null
                        narisiSmeri()
                    }
                    is Tabla.Izid.NiPostaje -> povej(R.string.tabla_ni_postaje, R.color.sev_bad)
                    is Tabla.Izid.BrezZveze -> povej(R.string.tabla_ni_zveze, R.color.sev_bad)
                }
            }
        }.start()
    }

    private fun pozabiIzbiro() {
        izbranaSmer = null
        smeri = emptyList()
        narisiSmeri()
        osveziGumb()
    }

    /**
     * Gumb za vsako stran ceste in "obe". Brez vec strani ni izbire -- in s
     * ciljem tudi ne: smer pove cilj sam.
     */
    private fun narisiSmeri() {
        smeriOkvir.removeAllViews()
        val pokazi = smeri.size > 1 && cilj.prazen
        val vidno = if (pokazi) View.VISIBLE else View.GONE
        findViewById<View>(R.id.smeri_glava).visibility = vidno
        findViewById<View>(R.id.smeri_pomoc).visibility = vidno
        if (!pokazi) return
        (listOf<Tabla.Smer?>(null) + smeri).forEach { s ->
            val b = layoutInflater.inflate(R.layout.tabla_smer, smeriOkvir, false) as Button
            b.text = s?.napis ?: getString(R.string.tabla_obe_smeri)
            val izbran = s?.kljuc == izbranaSmer
            b.setBackgroundResource(if (izbran) R.drawable.gumb_izbran else R.drawable.gumb_tih)
            b.setTextColor(getColor(if (izbran) R.color.ink else R.color.ink_dim))
            b.setOnClickListener {
                izbranaSmer = s?.kljuc
                narisiSmeri()
            }
            smeriOkvir.addView(b)
        }
    }

    /** Shraniti se da, ko je postaja izbrana, cilj pa izbran ali prazen. */
    private fun osveziGumb() {
        val gre = postaja.ime != null && (cilj.prazen || cilj.ime != null)
        shrani.isEnabled = gre
        shrani.alpha = if (gre) 1f else 0.45f
    }

    private fun povej(niz: Int, barva: Int) {
        findViewById<TextView>(R.id.izid).apply {
            setText(niz)
            setTextColor(getColor(barva))
            visibility = View.VISIBLE
        }
    }

    private fun skrijIzid() {
        findViewById<TextView>(R.id.izid).visibility = View.GONE
    }

    // ---------- shranjevanje ----------

    private fun poisciInShrani() {
        val ime = postaja.ime ?: run { povej(R.string.tabla_izberi, R.color.sev_bad); return }
        if (!cilj.prazen && cilj.ime == null) { povej(R.string.tabla_izberi_cilj, R.color.sev_bad); return }
        val kam = cilj.ime
        // Strežnik isto postajo zavrne (400); brez tega bi okno trdilo, da ga ni.
        if (kam == ime) { povej(R.string.tabla_isti_cilj, R.color.sev_bad); return }
        povej(R.string.tabla_iscem, R.color.ink_dim)
        val smer = if (kam != null) null else smeri.firstOrNull { it.kljuc == izbranaSmer }
        val ozn = oznaka.text.toString().trim().ifBlank { null }
        val n = Tabla.Nastavitev(ime, omrezje, smer?.kljuc, smer?.napis, videz, kam,
            oznaka = ozn, oznakaOd = ozn?.let { ime })
        // Omrezje na svoji niti; pet sekund cakanja na glavni bi bila zamrznjena
        // aplikacija.
        Thread {
            val izid = Tabla.prenesi(this, n)
            // Okno je med čakanjem zaprl (nazaj): launcher je widget že
            // odstranil, shranjena nastavitev in ritem bi ostala brez lastnika.
            glavna.post { if (!isFinishing && !isDestroyed) koncaj(n, izid) }
        }.start()
    }

    /**
     * Odgovor je prisel.
     *
     * Prazna tabla se **shrani**: pozno zvecer je prazna upraviceno in postaja
     * je prava. Zavrnemo samo postajo, ki je streznik ne pozna -- in izpad
     * zveze ni to, zato takrat ne zavrnemo nicesar.
     */
    private fun koncaj(n: Tabla.Nastavitev, izid: Tabla.Izid) {
        if (izid is Tabla.Izid.BrezZveze) {
            povej(R.string.tabla_ni_zveze, R.color.sev_bad); return
        }
        if (izid is Tabla.Izid.NiPostaje) {
            povej(R.string.tabla_ni_postaje, R.color.sev_bad); return
        }
        val odhodi = izid as Tabla.Izid.Odhodi
        Tabla.nastavi(this, widgetId, odhodi.popravi(n))
        Tabla.shraniStanje(this, widgetId, Tabla.Stanje(odhodi.vrstice,
            System.currentTimeMillis(), odhodi.opozorilo, odhodi.smeri))
        val am = AppWidgetManager.getInstance(this)
        am.updateAppWidget(widgetId, WidgetTabla.pogled(this, widgetId))
        // Ritem se zacne tu in ne sele ob prvem sistemskem obhodu: widget, ki
        // se pol ure ne osvezi, je videti kot pokvarjen, ne kot varcen.
        WidgetTabla.naRitem(this)
        setResult(RESULT_OK, Intent().putExtra(
            AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId))
        finish()
    }
}
