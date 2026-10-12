package app.kajros

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.os.Bundle
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.ReplacementSpan
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

/**
 * Pregled nastavljenih budilk.
 *
 * Nativen in ne spletni iz istega razloga kot budilka sama: rabis ga takrat,
 * ko streznika ni. Vse potrebno je ze v telefonu, zato tu ni nobene zahteve
 * v omrezje.
 */
class BudilkeDejavnost : Activity() {

    private companion object {
        const val ZAHTEVA_LEGA = 1
        const val OSVEZI_MS = 30_000L
    }

    private val ura = SimpleDateFormat("HH:mm", Locale("sl"))
    /** Kam vodi opozorilo; postavi ga `narisi()`, ker ve, kaj opozorilo pravi. */
    private var opozoriloNamera: Intent? = null
    private val dan = SimpleDateFormat("EEE d. M.", Locale("sl"))

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        setContentView(R.layout.budilke)
        findViewById<Button>(R.id.odpri).setOnClickListener {
            startActivity(Intent(this, GlavnaDejavnost::class.java))
            finish()
        }
        findViewById<Button>(R.id.naslov).setOnClickListener {
            // Pogovorno okno je v glavni dejavnosti; podvojiti ga bi pomenilo
            // dve poti do iste nastavitve in prilozost, da se razideta.
            startActivity(Intent(this, GlavnaDejavnost::class.java)
                .setAction(GlavnaDejavnost.AKCIJA_NASTAVITVE))
        }
        findViewById<TextView>(R.id.opozorilo).setOnClickListener {
            try {
                opozoriloNamera?.let { startActivity(it) }
            } catch (e: android.content.ActivityNotFoundException) {
                startActivity(Intent(android.provider.Settings
                    .ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName")))
            }
        }
        findViewById<Button>(R.id.preizkusi).setOnClickListener {
            ZvonjenjeStoritev.preizkusi(this)
            // Odpremo ga mi: dejavnost je vidna, zato sme. Prava budilka ga
            // odpre prek obvestila, ker takrat aplikacija ni spredaj.
            startActivity(Intent(this, ZvonjenjeDejavnost::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
                .putExtra(ZvonjenjeDejavnost.ID, ZvonjenjeStoritev.PREIZKUS))
        }
        findViewById<Button>(R.id.dnevnik).setOnClickListener { Dnevnik.pokazi(this) }
        // Dnevnik in naslov strežnika sta bila orodji za razvoj budilke; v
        // izdaji gumbov ni (12. 10. 2026). Naslov ostane na zaslonu napake.
        // Dnevnik pa ostane dosegljiv z dolgim pritiskom na naslov: vzrok
        // budilke, ki na tujem telefonu ne zvoni (Samsung, 7. 10. 2026), je
        // samo v njem -- izdaje z `adb` ni mogoče brati.
        findViewById<View>(R.id.glava).setOnLongClickListener { Dnevnik.pokazi(this); true }
        if (BuildConfig.DEBUG) {
            findViewById<View>(R.id.dnevnik).visibility = View.VISIBLE
            findViewById<View>(R.id.naslov).visibility = View.VISIBLE
        }
        findViewById<Switch>(R.id.deli_ob_voznji).setOnCheckedChangeListener { _, da ->
            // `narisi()` stikalo postavi na shranjeno vrednost; to ni odločitev.
            if (da == Nastavitve.deliObVoznji(this)) return@setOnCheckedChangeListener
            Nastavitve.nastaviDeliObVoznji(this, da)
            if (!da) DeljenjeStoritev.ustaviCakanje(this)
            else if (!DeljenjeStoritev.smeLego(this)) {
                requestPermissions(arrayOf(android.Manifest.permission.ACCESS_FINE_LOCATION,
                    android.Manifest.permission.ACCESS_COARSE_LOCATION), ZAHTEVA_LEGA)
            }
        }
    }

    override fun onRequestPermissionsResult(koda: Int, dovoljenja: Array<out String>,
                                            izidi: IntArray) {
        super.onRequestPermissionsResult(koda, dovoljenja, izidi)
        if (koda != ZAHTEVA_LEGA || izidi.any { it == PackageManager.PERMISSION_GRANTED }) return
        // Brez lege deljenja ni: stikalo, ki bi ostalo vklopljeno, bi lagalo.
        Nastavitve.nastaviDeliObVoznji(this, false)
        findViewById<Switch>(R.id.deli_ob_voznji).isChecked = false
        android.widget.Toast.makeText(this, R.string.deli_ob_voznji_lega,
            android.widget.Toast.LENGTH_LONG).show()
    }

    override fun onResume() {
        super.onResume()
        // Ponavljajoce se tu prestavijo na naslednji dan, ce jim je ura mimo:
        // seznam mora kazati, kdaj bo zvonilo, ne kdaj je zvonilo vceraj.
        Nacrtovalec.vseZnova(this)
        narisi()
        roka.postDelayed(tik, OSVEZI_MS)
    }

    override fun onPause() {
        super.onPause()
        roka.removeCallbacks(tik)
    }

    // Odprt seznam se osvežuje kot kartica na domači strani: "čez 7 min" bi
    // sicer obstal, odzvonjena budilka pa ostala, ko je vozilo že odpeljalo.
    private val roka = android.os.Handler(android.os.Looper.getMainLooper())
    private val tik = object : Runnable {
        override fun run() {
            narisi()
            roka.postDelayed(this, OSVEZI_MS)
        }
    }

    private fun narisi() {
        findViewById<Switch>(R.id.deli_ob_voznji).isChecked = Nastavitve.deliObVoznji(this)
        narisiOpozorilo()
        findViewById<Button>(R.id.naslov).text =
            getString(R.string.budilke_naslov_streznika,
                Nastavitve.naslov(this).removePrefix("https://").removePrefix("http://"))

        val seznam = findViewById<LinearLayout>(R.id.seznam)
        seznam.removeAllViews()
        val zdaj = System.currentTimeMillis()
        val budilke = Shramba.vse(this).filterNot { it.opravljena(zdaj) }
            .sortedBy { it.voznoredniMs }

        if (budilke.isEmpty()) {
            seznam.addView(prazno())
            return
        }
        budilke.forEach { seznam.addView(vrstica(seznam, it, zdaj)) }
    }

    /**
     * Eno opozorilo, najhujše najprej: brez dovoljenj budilka morda sploh ne
     * pride, tiha pride brez zvoka, brez celega zaslona pa zvoni s temnim
     * zaslonom.
     */
    private fun narisiOpozorilo() {
        val paket = Uri.parse("package:$packageName")
        val podrobnosti = Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS, paket)
        val tiho = Zvonjenje.zakajTiho(this)
        val (besedilo, namera) = when {
            !GlavnaDejavnost.smeObvescati(this) || !Nacrtovalec.smeTocenAlarm(this) ->
                getString(R.string.budilka_dovoljenja) to podrobnosti
            tiho.isNotEmpty() -> {
                val akcija = tiho.first().nastavitev
                getString(R.string.budilka_tiha, tiho.joinToString(", ") { it.besedilo }) to
                    if (akcija == android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS) {
                        Intent(akcija).putExtra(android.provider.Settings.EXTRA_APP_PACKAGE, packageName)
                    } else Intent(akcija)
            }
            // Dovoljenje za cel zaslon ima svoj zaslon; v podrobnostih
            // aplikacije ga na vecini telefonov ni mogoce najti.
            !Zvonjenje.smeCelZaslon(this) -> getString(R.string.budilka_cel_zaslon) to
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.UPSIDE_DOWN_CAKE)
                    Intent(android.provider.Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT, paket)
                else podrobnosti
            else -> null to null
        }
        opozoriloNamera = namera
        findViewById<TextView>(R.id.opozorilo).apply {
            visibility = if (besedilo == null) View.GONE else View.VISIBLE
            text = besedilo
        }
    }

    /** Siva kartica namesto seznama: kaj se je zgodilo in kje se budilka nastavi. */
    private fun prazno(): View {
        val dp = resources.displayMetrics.density
        return TextView(this).apply {
            text = getString(R.string.budilk_ni) + "\n" + getString(R.string.budilk_ni_kako)
            setTextColor(getColor(R.color.ink_dim))
            textSize = 15f
            setLineSpacing(3 * dp, 1f)
            setBackgroundResource(R.drawable.kartica)
            setPadding((20 * dp).toInt(), (18 * dp).toInt(), (20 * dp).toInt(), (18 * dp).toInt())
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT).apply { topMargin = (12 * dp).toInt() }
        }
    }

    /**
     * Kartica ene budilke, ista kot na domači strani (`home.js`): ura velika,
     * ob njej dan in odštevanje, pod njo vožnja in odhod z zamudo.
     *
     * Vklopljena je tonska (rjava), ugasnjena siva. Do 12. 10. 2026 sta bili
     * enaki, "ugasnjena" pa napisana v isti oranžni kot ura zvonjenja --
     * brala se je kot opozorilo, ne kot stanje.
     */
    private fun vrstica(starsi: LinearLayout, b: Budilka, zdajMs: Long): View {
        val v = LayoutInflater.from(this)
            .inflate(R.layout.budilka_vrstica, starsi, false)
        val izid = b.izracun(zdajMs)
        val vklop = !b.ugasnjena
        val glavna = getColor(if (vklop) R.color.m_na_kont else R.color.ink_dim)
        val drugotna = getColor(if (vklop) R.color.m_na_kont_2 else R.color.ink_mute)
        if (!vklop) v.setBackgroundResource(R.drawable.kartica)

        // Po zvonjenju je vprašanje odhod, ne zvonjenje (isto kot domača stran
        // in widget). Ugasnjena pokaže, kdaj bi zvonila, a sivo.
        val velika = if (b.odzvonjeno) izid.odhodMs else izid.zvoniOb
        v.findViewById<TextView>(R.id.ura).apply {
            text = ura.format(Date(velika))
            setTextColor(if (vklop) glavna else getColor(R.color.ink_mute))
        }
        v.findViewById<TextView>(R.id.kdaj).apply {
            text = when {
                !vklop -> getString(R.string.budilka_ugasnjena_kdaj, dan(velika, zdajMs))
                b.odzvonjeno -> getString(R.string.budilka_zazvonila)
                else -> getString(R.string.budilka_kdaj, dan(velika, zdajMs))
            }
            setTextColor(drugotna)
        }
        v.findViewById<TextView>(R.id.cez).apply {
            text = cez(velika - zdajMs)
            visibility = if (vklop) View.VISIBLE else View.GONE
            setTextColor(drugotna)
        }

        v.findViewById<TextView>(R.id.kaj).apply {
            val kraj = if (b.smer.isBlank()) b.postaja else "${b.postaja} → ${b.smer}"
            text = if (b.trainNo.isBlank()) kraj else "${b.trainNo} · $kraj"
            setTextColor(glavna)
        }

        // Vozni red je edino, kar je gotovo, zato je zraven, kadar se odhod
        // od njega loči. "odhod 17:19 · vozni red 17:19" je bilo na zaslonu
        // in ni povedalo ničesar -- dve imeni za isto uro sta videti kot dva
        // podatka.
        v.findViewById<TextView>(R.id.odhod).apply {
            val t = SpannableStringBuilder(getString(R.string.budilka_odhod, ura.format(Date(izid.odhodMs))))
            val s = ((izid.odhodMs - b.voznoredniMs) / 1000).toInt()
            val min = Math.round(s / 60.0).toInt()
            when (izid.vir) {
                Ura.Vir.ZAMUDA -> if (min == 0) {
                    t.append(" · ").append(getString(R.string.budilka_tocno))
                } else {
                    t.append(' ')
                    val zac = t.length
                    t.append(if (min <= -1) "${-min} min prej" else "+$min min")
                    t.setSpan(Zeton(getColor(R.color.bg), barvaZamude(min), 8 * resources.displayMetrics.density),
                        zac, t.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                    t.append(" · ").append(getString(R.string.budilka_vozni_red,
                        ura.format(Date(b.voznoredniMs))))
                }
                Ura.Vir.NI_PODATKA -> t.append(" · ").append(getString(R.string.budilka_ni_podatka))
                else -> t.append(" ").append(getString(R.string.budilka_po_voznem_redu))
            }
            text = t
            setTextColor(drugotna)
        }

        v.findViewById<TextView>(R.id.kako).apply {
            text = buildString {
                append(Ponovitev.ime(b.dnevi))
                append(" · ").append(getString(
                    if (b.zbudi) R.string.budilka_zbudi else R.string.budilka_obvesti))
                append(" · ").append(b.minutPrej).append(" min prej")
                if (b.rezervaS > 0) append(" + ").append(b.rezervaS / 60).append(" min rezerve")
            }
            setTextColor(drugotna)
        }

        // Od kdaj je številka. Brez tega bi "+4 min" izpred pol ure izgledalo
        // enako kot "+4 min" izpred pol minute -- in prva ne pomeni ničesar.
        // Beseda gre po `izid.vir`, kot vrstica odhoda nad njo: zastarela
        // zamuda ni "preverjena", ko račun že velja po voznem redu.
        v.findViewById<TextView>(R.id.vir).apply {
            val zadnjic = maxOf(b.zamudaObMs, b.stikObMs)
            text = when {
                izid.vir == Ura.Vir.ZAMUDA ->
                    getString(R.string.budilka_preverjeno, ura.format(Date(b.zamudaObMs)))
                izid.vir == Ura.Vir.NI_PODATKA ->
                    getString(R.string.budilka_vprasano, ura.format(Date(b.stikObMs)))
                zadnjic > 0 -> getString(R.string.budilka_nazadnje, ura.format(Date(zadnjic)))
                else -> getString(R.string.budilka_nepreverjeno)
            }
            setTextColor(drugotna)
        }

        v.findViewById<Switch>(R.id.vklop).apply {
            isChecked = vklop
            setOnCheckedChangeListener { _, da ->
                Shramba.shrani(this@BudilkeDejavnost, b.copy(ugasnjena = !da))
                Nacrtovalec.vseZnova(this@BudilkeDejavnost)
                Widgeti.osvezi(this@BudilkeDejavnost)
                narisi()
            }
        }
        v.findViewById<Button>(R.id.odpri_voznjo).apply {
            setTextColor(glavna)
            if (!vklop) setBackgroundResource(R.drawable.pilula_svetla)
            setOnClickListener { odpriVoznjo(b) }
        }
        v.findViewById<Button>(R.id.odstrani).setOnClickListener { odstrani(b) }
        return v
    }

    /**
     * Odstranitev vpraša. Gumb je en dotik pod stikalom, ponavljajoča budilka
     * pa nosi dneve, minute in rezervo -- znova jo nastaviš le prek vožnje.
     */
    private fun odstrani(b: Budilka) {
        android.app.AlertDialog.Builder(this)
            .setTitle(R.string.budilka_odstrani_vprasanje)
            .setMessage(listOf(b.trainNo, b.postaja, Ponovitev.ime(b.dnevi))
                .filter { it.isNotBlank() }.joinToString(" · "))
            .setPositiveButton(R.string.budilka_odstrani) { _, _ ->
                Shramba.odstrani(this, b.id)
                Nacrtovalec.preklici(this, b.id)
                Zvonjenje.utisaj(this, b.id)
                Widgeti.osvezi(this)
                narisi()
            }
            .setNegativeButton(R.string.preklici, null)
            .show()
    }

    /** "danes", "jutri" ali "sob. 17. 10." -- ura brez dneva je pri budilki dvoumna. */
    private fun dan(ms: Long, zdajMs: Long): String {
        val c = Calendar.getInstance().apply { timeInMillis = zdajMs }
        val danes = c.get(Calendar.YEAR) * 1000 + c.get(Calendar.DAY_OF_YEAR)
        c.add(Calendar.DAY_OF_YEAR, 1)
        val jutri = c.get(Calendar.YEAR) * 1000 + c.get(Calendar.DAY_OF_YEAR)
        c.timeInMillis = ms
        return when (c.get(Calendar.YEAR) * 1000 + c.get(Calendar.DAY_OF_YEAR)) {
            danes -> "danes"
            jutri -> "jutri"
            else -> this.dan.format(Date(ms))
        }
    }

    /** Barva lestvice po zaokroženi minuti, kot `delayColor` v common.js. */
    private fun barvaZamude(min: Int): Int = getColor(when {
        min <= 0 -> R.color.d_ontime
        min <= 5 -> R.color.d_small
        min <= 15 -> R.color.d_mid
        else -> R.color.d_big
    })

    /**
     * Žeton zamude na podlagi strani, kot `.bud-zam` na domači strani:
     * temna oranžna lestvice na rjavi kartici ne doseže kontrasta.
     */
    private class Zeton(val podlaga: Int, val barva: Int, val r: Float) : ReplacementSpan() {
        override fun getSize(p: Paint, t: CharSequence, od: Int, doo: Int,
                             fm: Paint.FontMetricsInt?): Int {
            p.isFakeBoldText = true
            return (p.measureText(t, od, doo) + 2 * r).toInt().also { p.isFakeBoldText = false }
        }

        override fun draw(c: Canvas, t: CharSequence, od: Int, doo: Int, x: Float,
                          vrh: Int, y: Int, dno: Int, p: Paint) {
            val barvaPrej = p.color
            p.isFakeBoldText = true
            val sirina = p.measureText(t, od, doo) + 2 * r
            p.color = podlaga
            c.drawRoundRect(RectF(x, y + p.ascent() - r / 4, x + sirina, y + p.descent() + r / 4), r, r, p)
            p.color = barva
            c.drawText(t, od, doo, x + r, y.toFloat(), p)
            p.color = barvaPrej
            p.isFakeBoldText = false
        }
    }

    /** Okno te voznje v aplikaciji -- ista stran, ki jo potnik ze pozna. */
    private fun odpriVoznjo(b: Budilka) {
        startActivity(Intent(this, GlavnaDejavnost::class.java)
            .setAction(GlavnaDejavnost.AKCIJA_ODPRI)
            .putExtra(GlavnaDejavnost.KAM, b.naslovVoznje(Nastavitve.naslov(this))))
        finish()
    }

    /** "čez 3 h 12 min", "čez 7 min" ali "zdaj", kot `cez()` v home.js. */
    private fun cez(ms: Long): String {
        val minut = Math.round(ms / 60_000.0).toInt()
        if (minut < 1) return "zdaj"
        val h = minut / 60
        return getString(R.string.budilka_cez, when {
            minut < 60 -> "$minut min"
            h < 24 -> "$h h ${minut % 60} min"
            else -> "${Math.round(h / 24.0)} d"
        })
    }
}
