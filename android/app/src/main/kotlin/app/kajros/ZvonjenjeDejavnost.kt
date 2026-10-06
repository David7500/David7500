package app.kajros

import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.app.Activity
import android.app.KeyguardManager
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.provider.Settings
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.TextView
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

/**
 * Zaslon zvonjenja „Peron“: vozilo pripelje iz daljave, potegneš ga do sebe
 * in budilka se ustavi (David je 6. 10. 2026 izbral ta prototip izmed dveh).
 *
 * Zvoka tu ni -- predvaja ga [ZvonjenjeStoritev], ker se ta zaslon odpre
 * samo, kadar sistem dovoli celozaslonsko obvestilo. Budilka, ki zvoni samo,
 * ce se odpre zaslon, ne zbudi nikogar, ki ima to dovoljenje zavrnjeno.
 */
class ZvonjenjeDejavnost : Activity() {

    companion object {
        const val ID = "id"
        /** Vrata se odprejo, nato pove, kaj je ustavil (kot v prototipu). */
        private const val KONEC_PO_MS = 1100L
        private const val KONEC_OSTANE_MS = 3500L
        private const val ODLOG_OSTANE_MS = 1800L
    }

    private var id: String? = null
    private val zapri: () -> Unit = { runOnUiThread { finish() } }
    private val roka = Handler(Looper.getMainLooper())
    private val ura = SimpleDateFormat("HH:mm", Locale("sl"))
    private var pogled: PeronPogled? = null
    private var risar: PeronRisar? = null
    private var pika: ObjectAnimator? = null
    private var glasnoPrej: Boolean? = null
    private var zakljuceno = false
    private var zmanjsano = false

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        prebudiZaslon()
        setContentView(R.layout.zvonjenje)

        id = intent.getStringExtra(ID)
        val b = id?.let { Shramba.ena(this, it) }
        // Zvonjenje je lahko ze ustavil gumb v obvestilu; zaslon brez zvonjenja
        // bi cakal na poteg, ki nima vec cesa ustaviti.
        if (b == null || ZvonjenjeStoritev.zvoni != b.id) { finish(); return }

        zmanjsano = Settings.Global.getFloat(contentResolver,
            Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
        // Nadomestni avtobus SŽ je v omrežju železnice, a je avtobus.
        val vlak = b.vlak && !b.trainNo.startsWith("BUS")
        napolniGlavo(b, vlak)

        val r = PeronRisar(Peron(vlak), b.postaja, resources.displayMetrics.density, zmanjsano) {
            roka.post { prispel(b) }
        }
        risar = r
        pogled = findViewById<PeronPogled>(R.id.prizor).also {
            it.zacni(r)
            it.obUstavitvi = { ustavi() }
        }

        findViewById<Button>(R.id.se_malo).setOnClickListener { odlozi() }
        // Konec se zapre na dotik: potnik je buden in hoče naprej.
        findViewById<View>(R.id.konec).setOnClickListener { finish() }
        ZvonjenjeStoritev.obKoncu = zapri
    }

    private fun napolniGlavo(b: Budilka, vlak: Boolean) {
        val zdaj = System.currentTimeMillis()
        val izid = b.izracun(zdaj)
        val (_, zakaj) = Zvonjenje.besedilo(this, b, zdaj)

        val kaj = if (b.trainNo.isBlank()) b.postaja else "${b.trainNo} · ${b.postaja}"
        val naslov = SpannableStringBuilder(kaj)
        if (b.smer.isNotBlank()) {
            val od = naslov.length
            // Nedeljivi presledek: puščica ostane s ciljem, ne na koncu vrstice.
            naslov.append(" →\u00a0${b.smer}")
            naslov.setSpan(ForegroundColorSpan(getColor(R.color.ink_dim)), od, naslov.length,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            naslov.setSpan(StyleSpan(android.graphics.Typeface.NORMAL), od, naslov.length,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }
        findViewById<TextView>(R.id.zvoni_naslov).text = naslov
        findViewById<TextView>(R.id.zvoni_odhod).text = ura.format(Date(izid.odhodMs))
        findViewById<TextView>(R.id.zvoni_zakaj).text = zakaj

        // Zamuda v okvirčku samo, kadar jo je račun res upošteval: naslov in
        // razlog pod njim morata biti ista odločitev (glej `Ura.Izid.odhodMs`).
        val min = izid.surovaS?.let { (it / 60.0).roundToInt() }
        findViewById<TextView>(R.id.zvoni_zamuda).apply {
            if (izid.vir != Ura.Vir.ZAMUDA || min == null || min < 0) {
                visibility = View.GONE
            } else {
                val barva = getColor(when {
                    min <= 0 -> R.color.d_ontime
                    min <= 5 -> R.color.d_small
                    min <= 15 -> R.color.d_mid
                    else -> R.color.d_big
                })
                text = if (min == 0) getString(R.string.zvoni_tocno_znak)
                else getString(R.string.zvoni_zamuda_znak, min)
                setTextColor(barva)
                background = GradientDrawable().apply {
                    cornerRadius = 8 * resources.displayMetrics.density
                    setStroke(resources.displayMetrics.density.roundToInt().coerceAtLeast(1), barva,
                        4 * resources.displayMetrics.density, 3 * resources.displayMetrics.density)
                }
                visibility = View.VISIBLE
            }
        }
        findViewById<TextView>(R.id.namig).setText(if (vlak) R.string.namig_vlak else R.string.namig_avtobus)
        if (!zmanjsano) {
            ObjectAnimator.ofFloat(findViewById(R.id.namig_puscica), View.TRANSLATION_X,
                0f, 7 * resources.displayMetrics.density).apply {
                duration = 800
                repeatMode = ValueAnimator.REVERSE
                repeatCount = ValueAnimator.INFINITE
                start()
            }
        }
    }

    /** Vsako sličico: napredek, ura, faza zvonjenja. */
    private val tik = object : Runnable {
        override fun run() {
            val r = risar ?: return
            findViewById<View>(R.id.napredek).scaleX = r.p
            val zdaj = System.currentTimeMillis()
            findViewById<TextView>(R.id.ura_zdaj).text = ura.format(Date(zdaj))
            // Po ustavitvi faza obstane: zvonjenja ni več, odštevanje do
            // glasnega bi lagalo.
            if (!zakljuceno) {
                val glasnoOb = ZvonjenjeStoritev.glasnoOb
                val glasno = glasnoOb in 1..zdaj
                r.glasno = glasno
                findViewById<TextView>(R.id.faza_besedilo).text =
                    if (glasno) getString(R.string.faza_glasno)
                    else getString(R.string.faza_nezno, ((glasnoOb - zdaj + 999) / 1000).toInt().coerceAtLeast(0))
                if (glasno != glasnoPrej) {
                    glasnoPrej = glasno
                    pokaziFazo(glasno)
                }
            }
            findViewById<View>(R.id.prizor).postOnAnimation(this)
        }
    }

    private fun pokaziFazo(glasno: Boolean) {
        val barva = getColor(if (glasno) R.color.poudarek else R.color.nezno)
        val d = resources.displayMetrics.density
        findViewById<TextView>(R.id.faza_besedilo).setTextColor(barva)
        findViewById<View>(R.id.faza).background = GradientDrawable().apply {
            cornerRadius = 999f
            setColor((barva and 0x00ffffff) or 0x14000000)
            setStroke(d.roundToInt().coerceAtLeast(1), (barva and 0x00ffffff) or (if (glasno) 0x44000000 else 0x33000000))
        }
        val p = findViewById<View>(R.id.faza_pika)
        p.background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(barva) }
        pika?.cancel()
        if (zmanjsano) { p.alpha = 1f; return }
        // Utrip pike: počasen, ko je nežno, hiter, ko je glasno.
        pika = ObjectAnimator.ofFloat(p, View.ALPHA, 0.35f, 1f).apply {
            duration = if (glasno) 300 else 1200
            repeatMode = ValueAnimator.REVERSE
            repeatCount = ValueAnimator.INFINITE
            start()
        }
    }

    /** Poteg je uspel: zvonjenje utihne takoj, vozilo pa še pripelje. */
    private fun ustavi() {
        if (zakljuceno) return
        zakljuceno = true
        // Lastna ustavitev ne sme zapreti zaslona, preden se vrata odprejo.
        if (ZvonjenjeStoritev.obKoncu === zapri) ZvonjenjeStoritev.obKoncu = null
        id?.let { startService(ZvonjenjeStoritev.namera(this, ZvonjenjeStoritev.USTAVI, it)) }
        getSystemService(Vibrator::class.java)?.vibrate(
            VibrationEffect.createWaveform(longArrayOf(0, 30, 60, 30), -1))
    }

    /** Vozilo je pripeljalo: vrata se odprejo, nato pove, kaj sledi. */
    private fun prispel(b: Budilka) {
        ustavi()
        val izid = b.izracun(System.currentTimeMillis())
        val min = izid.surovaS?.let { (it / 60.0).roundToInt() }
        val zamuda = if (izid.vir == Ura.Vir.ZAMUDA && min != null && min > 0)
            " (" + getString(R.string.zvoni_zamuda_znak, min) + ")" else ""
        val kdo = b.trainNo.ifBlank { b.postaja }
        roka.postDelayed({
            pokaziKonec(getString(R.string.konec_naslov),
                getString(R.string.konec_besedilo, kdo, ura.format(Date(izid.odhodMs)), zamuda))
        }, if (zmanjsano) 0 else KONEC_PO_MS)
        roka.postDelayed({ finish() }, (if (zmanjsano) 0 else KONEC_PO_MS) + KONEC_OSTANE_MS)
    }

    private fun odlozi() {
        if (zakljuceno) return
        zakljuceno = true
        if (ZvonjenjeStoritev.obKoncu === zapri) ZvonjenjeStoritev.obKoncu = null
        id?.let { startService(ZvonjenjeStoritev.namera(this, ZvonjenjeStoritev.ODLOZI, it)) }
        pokaziKonec(getString(R.string.odlog_naslov), getString(R.string.odlog_besedilo))
        roka.postDelayed({ finish() }, ODLOG_OSTANE_MS)
    }

    private fun pokaziKonec(naslov: String, besedilo: String) {
        findViewById<TextView>(R.id.konec_naslov).text = naslov
        findViewById<TextView>(R.id.konec_besedilo).text = besedilo
        findViewById<View>(R.id.konec).visibility = View.VISIBLE
    }

    private fun prebudiZaslon() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            getSystemService(KeyguardManager::class.java)?.requestDismissKeyguard(this, null)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON,
            )
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
    }

    override fun onResume() {
        super.onResume()
        ZvonjenjeStoritev.zaslonViden = risar != null
        pogled?.onResume()
        findViewById<View>(R.id.prizor).postOnAnimation(tik)
    }

    override fun onPause() {
        ZvonjenjeStoritev.zaslonViden = false
        findViewById<View>(R.id.prizor).removeCallbacks(tik)
        pogled?.onPause()
        super.onPause()
    }

    override fun onDestroy() {
        roka.removeCallbacksAndMessages(null)
        pika?.cancel()
        if (ZvonjenjeStoritev.obKoncu === zapri) ZvonjenjeStoritev.obKoncu = null
        super.onDestroy()
    }

    /**
     * Gumb nazaj budilke ne utisa. Kdor jo hoce ustaviti, naj to pove -- sicer
     * je prevec lahko odmahniti in zaspati naprej.
     */
    @Deprecated("Ogrodje brez AndroidX nima nadomestila.")
    override fun onBackPressed() {
        // namenoma nic
    }
}
