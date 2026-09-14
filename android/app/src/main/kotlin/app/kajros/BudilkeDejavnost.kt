package app.kajros

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import java.text.SimpleDateFormat
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

    private val ura = SimpleDateFormat("HH:mm", Locale("sl"))
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
            // Dovoljenje za cel zaslon ima svoj zaslon; v podrobnostih
            // aplikacije ga na vecini telefonov ni mogoce najti.
            val akcija = if (samoCelZaslon() &&
                android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.UPSIDE_DOWN_CAKE)
                android.provider.Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT
            else android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS
            try {
                startActivity(Intent(akcija, Uri.parse("package:$packageName")))
            } catch (e: android.content.ActivityNotFoundException) {
                startActivity(Intent(android.provider.Settings
                    .ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName")))
            }
        }
        findViewById<Button>(R.id.dnevnik).setOnClickListener { pokaziDnevnik() }
    }

    /** Vse drugo je urejeno, manjka samo cel zaslon. */
    private fun samoCelZaslon(): Boolean =
        GlavnaDejavnost.smeObvescati(this) && Nacrtovalec.smeTocenAlarm(this) &&
            !Zvonjenje.smeCelZaslon(this)

    private fun pokaziDnevnik() {
        val p = (16 * resources.displayMetrics.density).toInt()
        val besedilo = TextView(this).apply {
            text = Dnevnik.beri(this@BudilkeDejavnost).ifBlank { getString(R.string.dnevnik_prazen) }
            setTextColor(getColor(R.color.ink_dim))
            textSize = 12f
            typeface = android.graphics.Typeface.MONOSPACE
            setTextIsSelectable(true)
            setPadding(p, p / 2, p, 0)
        }
        android.app.AlertDialog.Builder(this)
            .setTitle(R.string.dnevnik)
            .setView(android.widget.ScrollView(this).apply { addView(besedilo) })
            .setPositiveButton(R.string.zapri, null)
            .show()
    }

    override fun onResume() {
        super.onResume()
        // Ponavljajoce se tu prestavijo na naslednji dan, ce jim je ura mimo:
        // seznam mora kazati, kdaj bo zvonilo, ne kdaj je zvonilo vceraj.
        Nacrtovalec.vseZnova(this)
        narisi()
    }

    private fun narisi() {
        findViewById<TextView>(R.id.opozorilo).apply {
            val vse = GlavnaDejavnost.smeObvescati(this@BudilkeDejavnost) &&
                Nacrtovalec.smeTocenAlarm(this@BudilkeDejavnost)
            visibility = if (vse && Zvonjenje.smeCelZaslon(this@BudilkeDejavnost))
                View.GONE else View.VISIBLE
            setText(if (vse) R.string.budilka_cel_zaslon else R.string.budilka_dovoljenja)
        }
        findViewById<Button>(R.id.naslov).text =
            getString(R.string.budilke_naslov_streznika,
                Nastavitve.naslov(this).removePrefix("https://").removePrefix("http://"))

        val seznam = findViewById<LinearLayout>(R.id.seznam)
        seznam.removeAllViews()
        val zdaj = System.currentTimeMillis()
        val budilke = Shramba.vse(this).sortedBy { it.voznoredniMs }

        if (budilke.isEmpty()) {
            seznam.addView(besedilo(R.string.budilk_ni, R.color.ink, 16))
            seznam.addView(besedilo(R.string.budilk_ni_kako, R.color.ink_dim, 14))
            return
        }
        budilke.forEach { seznam.addView(vrstica(seznam, it, zdaj)) }
    }

    private fun besedilo(niz: Int, barva: Int, velikost: Int): TextView =
        TextView(this).apply {
            setText(niz)
            setTextColor(getColor(barva))
            textSize = velikost.toFloat()
            setPadding(0, (12 * resources.displayMetrics.density).toInt(), 0, 0)
        }

    private fun vrstica(starsi: LinearLayout, b: Budilka, zdajMs: Long): View {
        val v = LayoutInflater.from(this)
            .inflate(R.layout.budilka_vrstica, starsi, false)
        val izid = b.izracun(zdajMs)

        v.findViewById<TextView>(R.id.kaj).text =
            if (b.trainNo.isBlank()) b.postaja else "${b.trainNo} · ${b.postaja}"
        v.findViewById<TextView>(R.id.smer).apply {
            text = "→ ${b.smer}"
            visibility = if (b.smer.isBlank()) View.GONE else View.VISIBLE
        }

        // Ura zvonjenja stoji na zadnji znani zamudi in se bo se premikala;
        // koliko je do nje, je tisto, kar clovek res bere.
        v.findViewById<TextView>(R.id.zvoni).text = when {
            b.ugasnjena -> getString(R.string.budilka_ugasnjena)
            b.odzvonjeno -> getString(R.string.budilka_odzvonjeno)
            else -> getString(R.string.budilka_zvoni_ob, ura.format(Date(izid.zvoniOb))) +
                "  " + getString(R.string.budilka_cez, presledek(izid.zvoniOb - zdajMs))
        }

        // Vozni red je edino, kar je gotovo, zato je vedno zraven -- in kadar
        // se odhod od njega loci, sta obe uri na zaslonu, ne le izracunana.
        v.findViewById<TextView>(R.id.odhod).text = buildString {
            append(dan.format(Date(b.voznoredniMs))).append(' ')
            append(getString(R.string.budilka_vozni_red, ura.format(Date(b.voznoredniMs))))
            // Odhod pisemo LE, kadar se od voznega reda loci. "odhod 17:19 ·
            // vozni red 17:19" je bilo na zaslonu in ni povedalo nicesar --
            // dve imeni za isto uro sta videti kot dva podatka.
            val min = Math.round((izid.odhodMs - b.voznoredniMs) / 60_000.0).toInt()
            if (min != 0) {
                append(" · ").append(getString(R.string.budilka_odhod,
                    ura.format(Date(izid.odhodMs))))
                append(if (min > 0) " +$min min" else " $min min")
            }
        }

        v.findViewById<TextView>(R.id.kako).text = buildString {
            append(Ponovitev.ime(b.dnevi))
            append(" · ").append(getString(
                if (b.zbudi) R.string.budilka_zbudi else R.string.budilka_obvesti))
            append(" · ").append(b.minutPrej).append(" min prej")
            if (b.rezervaS > 0) append(" +").append(b.rezervaS / 60).append(" rezerve")
        }

        // Od kdaj je stevilka. Brez tega bi "+4 min" izpred pol ure izgledalo
        // enako kot "+4 min" izpred pol minute -- in prva ne pomeni nicesar.
        v.findViewById<TextView>(R.id.vir).text = when {
            b.zamudaObMs > 0 && b.zamudaObMs >= b.stikObMs ->
                getString(R.string.budilka_preverjeno, ura.format(Date(b.zamudaObMs)))
            b.stikObMs > 0 -> getString(R.string.budilka_ni_podatka, ura.format(Date(b.stikObMs)))
            else -> getString(R.string.budilka_nepreverjeno)
        }

        v.findViewById<Switch>(R.id.vklop).apply {
            isChecked = !b.ugasnjena
            setOnCheckedChangeListener { _, vklop ->
                Shramba.shrani(this@BudilkeDejavnost, b.copy(ugasnjena = !vklop))
                Nacrtovalec.vseZnova(this@BudilkeDejavnost)
                narisi()
            }
        }
        v.findViewById<Button>(R.id.odpri_voznjo).setOnClickListener { odpriVoznjo(b) }
        v.findViewById<Button>(R.id.odstrani).setOnClickListener {
            Shramba.odstrani(this, b.id)
            Nacrtovalec.preklici(this, b.id)
            Zvonjenje.utisaj(this, b.id)
            Widget.osvezi(this)
            narisi()
        }
        return v
    }

    /** Okno te voznje v aplikaciji -- ista stran, ki jo potnik ze pozna. */
    private fun odpriVoznjo(b: Budilka) {
        val pot = if (b.vlak) "/app/train/" else "/app/bus/"
        val naslov = buildString {
            append(Nastavitve.naslov(this@BudilkeDejavnost)).append(pot)
            // `Nastavitve.zaPot`, ne `URLEncoder`: stevilka vlaka gre v POT in
            // presledek mora biti `%20`, ne `+`. Glej opombo tam.
            append(Nastavitve.zaPot(b.trainNo))
            append("?postaja=").append(Nastavitve.zaPot(b.postaja))
            append("&date=").append(Nastavitve.zaPot(b.dan))
            if (!b.tripId.isNullOrBlank()) {
                append("&trip=").append(Nastavitve.zaPot(b.tripId))
            }
        }
        startActivity(Intent(this, GlavnaDejavnost::class.java)
            .setAction(GlavnaDejavnost.AKCIJA_ODPRI)
            .putExtra(GlavnaDejavnost.KAM, naslov))
        finish()
    }

    /** "3 h 12 min" ali "7 min". Sekund tu ni: seznam se ne osvezuje sam. */
    private fun presledek(ms: Long): String {
        val minut = Math.max(0, Math.round(ms / 60_000.0).toInt())
        return if (minut >= 60) "${minut / 60} h ${minut % 60} min" else "$minut min"
    }
}
