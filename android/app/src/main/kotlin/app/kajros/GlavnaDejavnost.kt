package app.kajros

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.view.ViewGroup
import android.webkit.GeolocationPermissions
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

/**
 * Ves prikaz kajrosa je spletna stran; ta dejavnost je ovoj okrog nje.
 *
 * Zakaj ovoj in ne cisto nativna aplikacija: vmesnik bi bilo treba pisati
 * dvakrat in ob vsaki spremembi popravljati na dveh mestih. Nativno naj bo
 * samo tisto, cesar splet ne zmore -- to je budilka, ne odhodna tabla.
 */
class GlavnaDejavnost : Activity() {

    companion object {
        const val AKCIJA_NASTAVITVE = "app.kajros.NASTAVITVE"
        /** Odpri dolocen naslov v WebView (iz seznama budilk). */
        const val AKCIJA_ODPRI = "app.kajros.ODPRI"
        const val KAM = "kam"
        private const val ZAHTEVA_LEGA = 1
        private const val ZAHTEVA_OBVESTILA = 2

        /** Od Androida 13 je obvestilo dovoljenje, prej je bilo samoumevno. */
        fun smeObvescati(c: android.content.Context): Boolean =
            Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
                c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
                PackageManager.PERMISSION_GRANTED

        /**
         * Sheme, ki jih smemo predati drugemu programu. `intent:` je izpuscen
         * namerno: tuja stran ga zna sestaviti tako, da odpre poljubno
         * dejavnost v telefonu, in to je znana pot za pobeg iz WebView.
         */
        private val ZUNANJE_SHEME = setOf("http", "https", "mailto", "tel", "sms", "geo")
    }

    private lateinit var web: WebView
    private lateinit var zaslonNapake: ScrollView
    private lateinit var opisNapake: TextView

    /** Trenutni naslov. Bran ob zagonu in ob shranjeni spremembi, ne ob vsakem kliku. */
    private var naslov: String = ""

    /**
     * Ali je bila med tem nalaganjem napaka. `onPageFinished` se sprozi tudi
     * po napaki -- brez te zastavice bi zaslon napake takoj sam sebe skril.
     */
    private var bilaNapaka = false

    /**
     * Naslov, pri katerem je bila napaka. Rabi se, ker WebView javi napako
     * HTTP **pred** `onPageStarted` za isto navigacijo -- izmerjeno na
     * emulatorju 12. 9. 2026:
     *
     *     httpError 525 main=true url=https://…/
     *     pageFinished bilaNapaka=false url=https://…/
     *
     * `onPageStarted` je zastavico pobrisal za nazaj in `onPageFinished` je
     * nas zaslon skril. Posledica je bila natanko tisto, cemur se zaslon
     * izogiba: potnik je videl Cloudflarovo anglesko stran „SSL handshake
     * failed", ne nasega stavka. Zato zacetek nalaganja pobrise stanje samo,
     * kadar gre za DRUG naslov.
     */
    private var naslovNapake: String? = null

    /** Dovoljenje za lego zahteva sistem asinhrono; stran medtem caka na odgovor. */
    private var cakajocaLega: Pair<String, GeolocationPermissions.Callback>? = null

    private lateinit var most: Most

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        setContentView(R.layout.dejavnost)

        web = findViewById(R.id.web)
        zaslonNapake = findViewById(R.id.napaka)
        opisNapake = findViewById(R.id.napaka_naslov)
        findViewById<Button>(R.id.poskusi).setOnClickListener { naloziZnova() }
        findViewById<Button>(R.id.nastavi).setOnClickListener { odpriNastavitve() }
        // Ko strežnika ni, so shranjene budilke edino, kar aplikacija še ve --
        // in ravno takrat te zanima, ob kateri uri gre tvoj vlak po voznem redu.
        findViewById<Button>(R.id.na_budilke).setOnClickListener {
            startActivity(Intent(this, BudilkeDejavnost::class.java))
        }

        naslov = Nastavitve.naslov(this)
        pripraviWeb()
        // Budilke prezivijo ponovni zagon telefona in posodobitev aplikacije,
        // a `AlarmManager` jih ne -- ob vsakem zagonu jih nastavimo znova.
        Nacrtovalec.vseZnova(this)
        Zvonjenje.kanali(this)

        if (stanje != null) web.restoreState(stanje) else web.loadUrl(naslov)
        obravnavajNamero(intent)
        // Zunaj trgovine posodobitve ne ponudi nihce. Vprasa se enkrat na dan
        // in samo pokaze vrstico -- prenos in namestitev sta uporabnikova klika.
        Posodobitev.preveri(this) { pokaziPosodobitev(it) }
    }

    private fun pokaziPosodobitev(izdaja: Posodobitev.Izdaja) {
        val vrstica = findViewById<View>(R.id.posodobitev)
        findViewById<TextView>(R.id.posodobitev_besedilo).text =
            getString(R.string.posodobitev, izdaja.ime)
        vrstica.setOnClickListener {
            // V brskalnik, ne v WebView: stran s prenosom je nasa, a prenos
            // datoteke v WebView ne dela -- `DownloadListener`-ja nimamo in
            // ga zaradi enega gumba ne bomo dodajali.
            odpriZunaj(Uri.parse(izdaja.stran))
        }
        findViewById<Button>(R.id.posodobitev_zapri).setOnClickListener {
            Posodobitev.preskoci(this, izdaja.koda)
            vrstica.visibility = View.GONE
        }
        vrstica.visibility = View.VISIBLE
    }

    override fun onNewIntent(nova: Intent?) {
        super.onNewIntent(nova)
        if (nova != null) { intent = nova; obravnavajNamero(nova) }
    }

    private fun obravnavajNamero(n: Intent) {
        if (n.action == AKCIJA_NASTAVITVE) { odpriNastavitve(); return }
        if (n.action != AKCIJA_ODPRI) return
        val kam = n.getStringExtra(KAM) ?: return
        // Namera je izvozena skupaj z LAUNCHER, torej jo zna poslati tudi tuja
        // aplikacija. Naslov gre zato skozi isto mejo zaupanja kot vse drugo:
        // most do budilk sme videti samo nasa stran.
        if (!Nastavitve.jeNas(kam, naslov)) return
        bilaNapaka = false
        naslovNapake = null
        skrijNapako()
        web.loadUrl(kam)
    }

    override fun onSaveInstanceState(v: Bundle) {
        super.onSaveInstanceState(v)
        web.saveState(v)
    }

    // ---------- WebView ----------

    private fun pripraviWeb() {
        val n = web.settings
        n.javaScriptEnabled = true
        // Brez tega izgubis shranjene relacije in nedavna iskanja: oboje je v
        // `localStorage` (`connections.js`). WebView si ga deli po izvoru,
        // zato aplikacija in brskalnik na telefonu vidita iste shranjene poti.
        n.domStorageEnabled = true
        n.setGeolocationEnabled(true)
        // **WebView si dovoljenje za lego zapomni sam, in to je past.**
        // Izmerjeno na telefonu 9. 9. 2026: v `WebViewProfilePrefsDefault.xml`
        // je stalo `AwGeolocationPermissions%https://kajros.app/ = true`,
        // `dumpsys package` pa je za ACCESS_FINE_LOCATION javljal
        // `granted=false, ONE_TIME`. Sistemsko dovoljenje je bilo "samo
        // tokrat" in je poteklo, WebViewov zapis pa je ostal -- zato
        // `onGeolocationPermissionsShowPrompt` ni bil vec poklican in edini
        // kraj, kjer aplikacija zaprosi Android, se ni izvedel nikoli vec.
        // Lega je tiho odpovedala za vedno in sama iz tega ni mogla ven.
        //
        // Zato te shrambe ne uporabljamo: vir resnice je Androidovo
        // dovoljenje, ne WebViewov spomin. Tu se ze zapisano pobrise, spodaj
        // pa se nic novega ne zapise (`retain = false`).
        GeolocationPermissions.getInstance().clearAll()
        // Nic lokalnega: stran je oddaljena in do datotek v telefonu nima opravka.
        n.allowFileAccess = false
        n.allowContentAccess = false
        // Pri `https` naslovu ne sme na stran priti niti ena nesifrirana zahteva.
        n.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        n.javaScriptCanOpenWindowsAutomatically = false
        n.setSupportMultipleWindows(false)
        n.mediaPlaybackRequiresUserGesture = true
        // Streznik tako vidi, da zahteva prihaja iz aplikacije. Znak
        // `window.Kajros` je zanesljivejsi, a je viden sele strani, ne dnevniku.
        n.userAgentString = n.userAgentString + " Kajros/" + BuildConfig.VERSION_NAME

        web.setBackgroundColor(getColor(R.color.bg))
        most = Most(this) { naslov }
        // Most je viden vsaki strani v tem WebView. Da tuja ne pride do njega,
        // sta dve varovalki: `shouldOverrideUrlLoading` tuje strani sploh ne
        // nalozi, `Most` pa vsak klic preveri proti zadnjemu nalozenemu naslovu.
        web.addJavascriptInterface(most, "Kajros")
        web.webViewClient = Odjemalec()
        web.webChromeClient = Krom()

        // Razhroscevanje prek `chrome://inspect` samo v razvojni razlicici.
        if (BuildConfig.DEBUG) WebView.setWebContentsDebuggingEnabled(true)
    }

    private inner class Odjemalec : WebViewClient() {

        override fun shouldOverrideUrlLoading(v: WebView, z: WebResourceRequest): Boolean {
            val url = z.url.toString()
            if (Nastavitve.jeNas(url, naslov)) return false
            // Tuja stran v tem WebView bi videla most do budilk. Gre ven, v
            // brskalnik -- to ni udobje, ampak varovalka.
            odpriZunaj(z.url)
            return true
        }

        override fun onPageStarted(v: WebView, url: String?, ikona: Bitmap?) {
            // Samo DRUG naslov pomeni novo nalaganje. Za isti naslov je ta
            // klic lahko nadaljevanje navigacije, katere napako smo ze javili
            // (glej [naslovNapake]) -- brisanje bi zaslon napake skrilo.
            if (url != naslovNapake) {
                bilaNapaka = false
                naslovNapake = null
            }
            most.trenutniUrl = url
        }

        override fun onReceivedError(v: WebView, z: WebResourceRequest, e: WebResourceError) {
            // Napaka pri sliki ali pisavi ni razlog, da bi skrili vso stran.
            if (!z.isForMainFrame) return
            naslovNapake = z.url?.toString()
            pokaziNapako(e.description?.toString())
        }

        override fun onReceivedHttpError(
            v: WebView, z: WebResourceRequest, o: WebResourceResponse,
        ) {
            if (!z.isForMainFrame) return
            // Samo napake streznika. Pri 4xx stran obstaja in pove vec od nas:
            // Cloudflarov 403 je svoja stran, nas 404 pa nasa. Nativni zaslon
            // je za primer, ko ni NICESAR -- ne za vsako stevilko nad 400.
            if (o.statusCode >= 500) {
                naslovNapake = z.url?.toString()
                pokaziNapako("HTTP ${o.statusCode}")
            }
        }

        override fun onPageFinished(v: WebView, url: String?) {
            most.trenutniUrl = url
            if (!bilaNapaka) skrijNapako()
        }
    }

    private inner class Krom : WebChromeClient() {

        /**
         * Konzola strani v `logcat`. Brez tega je napaka v JavaScriptu v
         * aplikaciji nevidna -- v brskalniku jo vidis, tu ne. Projekt ima
         * pravilo, da mora biti konzola cista; to je nacin, da se to preveri.
         */
        override fun onConsoleMessage(m: android.webkit.ConsoleMessage): Boolean {
            if (BuildConfig.DEBUG) {
                android.util.Log.d("kajros-stran",
                    "${m.messageLevel()} ${m.message()} (${m.sourceId()}:${m.lineNumber()})")
            }
            return true
        }
        /**
         * Lastna lega. Prek `https://kajros.app` v WebView je kontekst varen in
         * `navigator.geolocation` dela -- prek `http://192.168…` v brskalniku ne
         * (izmerjeno: `window.isSecureContext = false`). To je edina omejitev iz
         * CLAUDE.md, ki jo aplikacija odpravi.
         */
        override fun onGeolocationPermissionsShowPrompt(
            izvor: String, odgovor: GeolocationPermissions.Callback,
        ) {
            if (!Nastavitve.jeNas(izvor, naslov)) { odgovor.invoke(izvor, false, false); return }
            if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED
            ) {
                // Tretji argument je "zapomni si" in je vedno `false`: ce bi
                // WebView shranil "dovoljeno", nas naslednjic ne bi vprasal
                // in Androidovega dovoljenja ne bi preveril nihce.
                odgovor.invoke(izvor, true, false)
                return
            }
            cakajocaLega = izvor to odgovor
            requestPermissions(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION,
                ),
                ZAHTEVA_LEGA,
            )
        }
    }

    /**
     * Kar budilka rabi od sistema: obvestila (13+), tocne alarme (12+) in
     * cel zaslon (14+). Zadnja dva nista dovoljenji, ampak nastavitvi, zato
     * zanju odpremo zaslon sistema.
     */
    fun zahtevajZaBudilko() {
        if (!smeObvescati(this)) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                ZAHTEVA_OBVESTILA)
            return
        }
        if (!Nacrtovalec.smeTocenAlarm(this)) {
            Toast.makeText(this, R.string.ni_tocnih_alarmov, Toast.LENGTH_LONG).show()
            odpriNastavitev(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM)
            return
        }
        if (!Zvonjenje.smeCelZaslon(this) &&
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE
        ) {
            Toast.makeText(this, R.string.ni_celega_zaslona, Toast.LENGTH_LONG).show()
            odpriNastavitev(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT)
        }
    }

    private fun odpriNastavitev(akcija: String) {
        try {
            startActivity(Intent(akcija, Uri.parse("package:$packageName")))
        } catch (e: ActivityNotFoundException) {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:$packageName")))
        }
    }

    override fun onRequestPermissionsResult(
        koda: Int, dovoljenja: Array<out String>, izidi: IntArray,
    ) {
        super.onRequestPermissionsResult(koda, dovoljenja, izidi)
        if (koda == ZAHTEVA_OBVESTILA) {
            // Ce so obvestila urejena, gremo takoj se na tocne alarme -- potnik
            // je pritisnil en gumb in ne bi smel dvakrat iskati istega.
            zahtevajZaBudilko()
            return
        }
        if (koda != ZAHTEVA_LEGA) return
        val (izvor, odgovor) = cakajocaLega ?: return
        cakajocaLega = null
        val da = izidi.any { it == PackageManager.PERMISSION_GRANTED }
        odgovor.invoke(izvor, da, false)
        // Ce je clovek rekel "ne vprasaj vec", sistem naslednjic okna sploh ne
        // pokaze in stran bi cakala v prazno. Povejmo, kje se to odklene.
        if (!da && !shouldShowRequestPermissionRationale(
                Manifest.permission.ACCESS_FINE_LOCATION)) {
            Toast.makeText(this, R.string.lega_zavrnjena, Toast.LENGTH_LONG).show()
        }
    }

    // ---------- napaka ----------

    private fun pokaziNapako(zakaj: String?) {
        bilaNapaka = true
        // Tvoj primer je zaprt prenosnik: telefon JE na omrezju, streznika ni.
        // Ce bi oba primera imela isti stavek, bi te ta pol casa poslal
        // popravljat napacno stvar.
        findViewById<TextView>(R.id.napaka_zakaj)
            .setText(if (jeOmrezje()) R.string.ni_zveze_zakaj else R.string.ni_omrezja)
        opisNapake.text = if (zakaj.isNullOrBlank()) naslov else "$naslov\n$zakaj"
        zaslonNapake.visibility = View.VISIBLE
    }

    private fun jeOmrezje(): Boolean {
        val cm = getSystemService(ConnectivityManager::class.java) ?: return true
        val zmoznosti = cm.getNetworkCapabilities(cm.activeNetwork) ?: return false
        return zmoznosti.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun skrijNapako() {
        zaslonNapake.visibility = View.GONE
    }

    private fun naloziZnova() {
        bilaNapaka = false
        naslovNapake = null
        skrijNapako()
        // `reload()` ponovi zadnji naslov, tudi ce je bila to stran z napako
        // znotraj naseg izvora. Ce se nismo nikamor prisli, zacnemo od doma.
        if (web.url.isNullOrBlank()) web.loadUrl(naslov) else web.reload()
    }

    // ---------- nastavitve ----------

    private fun odpriNastavitve() {
        val polje = EditText(this).apply {
            setText(naslov)
            setSingleLine()
            hint = getString(R.string.nastavitve_pomoc)
            setSelection(text.length)
        }
        val okvir = zZrakom(polje)

        AlertDialog.Builder(this)
            .setTitle(R.string.nastavitve_naslov)
            .setView(okvir)
            .setPositiveButton(R.string.shrani) { _, _ -> shraniNaslov(polje.text.toString()) }
            .setNegativeButton(R.string.preklici, null)
            .show()
    }

    /** Polje brez roba se v pogovornem oknu dotika stene; to mu da zrak. */
    private fun zZrakom(pogled: View): ViewGroup {
        val p = (20 * resources.displayMetrics.density).toInt()
        return android.widget.FrameLayout(this).apply {
            setPadding(p, p / 2, p, 0)
            addView(pogled)
        }
    }

    private fun shraniNaslov(vnos: String) {
        val nov = Nastavitve.ocisti(vnos)
        if (nov == null) {
            Toast.makeText(this, R.string.naslov_ni_veljaven, Toast.LENGTH_LONG).show()
            return
        }
        Nastavitve.shrani(this, nov)
        naslov = nov
        // Piskotki in `localStorage` so vezani na izvor, zato ob menjavi
        // naslova ni kaj brisati -- nov izvor preprosto ne vidi starega.
        bilaNapaka = false
        naslovNapake = null
        skrijNapako()
        web.clearHistory()
        web.loadUrl(naslov)
    }

    // ---------- zunanje povezave ----------

    private fun odpriZunaj(u: Uri) {
        if ((u.scheme?.lowercase() ?: "") !in ZUNANJE_SHEME) return
        try {
            startActivity(
                Intent(Intent.ACTION_VIEW, u).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        } catch (e: ActivityNotFoundException) {
            Toast.makeText(this, u.toString(), Toast.LENGTH_LONG).show()
        }
    }

    // ---------- gumb nazaj ----------

    @Deprecated("Ogrodje brez AndroidX nima nadomestila; predvidevajoci nazaj ni vklopljen.")
    override fun onBackPressed() {
        if (zaslonNapake.visibility == View.VISIBLE) { finish(); return }
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
