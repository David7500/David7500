package app.kajros

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.view.View
import android.widget.RemoteViews
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Majhen widget: do tri budilke, vsaka s stikalom.
 *
 * **Zakaj poleg odstevanja se ta.** Prvi widget odgovarja na "koliko casa imam
 * se" in kaze eno samo budilko. Vprasanje, ki ga ne pokrije, je vecerno:
 * "katere budilke so nastavljene in ali jutri sploh grem". Danes je zanj treba
 * odpreti aplikacijo in najti seznam.
 *
 * **Nic omreznega.** Vse, kar widget pokaze, je v telefonu -- ura zvonjenja je
 * izracunana iz shranjene budilke. Zato dela tudi takrat, ko streznika ni, in
 * ne stane niti ene zahteve.
 */
class WidgetBudilke : AppWidgetProvider() {

    override fun onUpdate(c: Context, am: AppWidgetManager, idji: IntArray) {
        // Isti samopopravek kot pri odstevanju: ponavljajoca budilka, ki je
        // odzvonila in je nihce ni ustavil, bi sicer ostala `odzvonjeno` za
        // vedno. Sistem nas zaradi widgeta tako ali tako zbudi.
        Nacrtovalec.vseZnova(c)
        idji.forEach { am.updateAppWidget(it, pogled(c)) }
    }

    override fun onReceive(c: Context, namera: Intent) {
        if (namera.action == PREKLOPI) {
            preklopi(c, namera.getStringExtra(ID) ?: return)
            return
        }
        super.onReceive(c, namera)
    }

    /**
     * Stikalo na widgetu.
     *
     * `vseZnova` in ne samo zapis: ugasnjena budilka mora izgubiti svojo
     * budnico, prizgana pa jo dobiti nazaj -- sicer bi stikalo spremenilo
     * samo napis. Ta poteza tudi prerise oba widgeta, ker gre skozi
     * [Widgeti.osvezi].
     */
    private fun preklopi(c: Context, id: String) {
        val b = Shramba.ena(c, id) ?: return
        Shramba.shrani(c, b.copy(ugasnjena = !b.ugasnjena))
        Dnevnik.zapisi(c, b, if (b.ugasnjena) "widget: vklop" else "widget: izklop")
        Nacrtovalec.vseZnova(c)
    }

    companion object {
        const val PREKLOPI = "app.kajros.PREKLOPI"
        const val ID = "id"

        /** Kolikor jih gre na widget, ki je velik dve vrstici ikon. */
        private const val VRSTIC = 3

        private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

        private val VRSTICA = intArrayOf(
            R.id.bud_vrstica1, R.id.bud_vrstica2, R.id.bud_vrstica3)
        private val URE = intArrayOf(R.id.bud_ura1, R.id.bud_ura2, R.id.bud_ura3)
        private val KAJ = intArrayOf(R.id.bud_kaj1, R.id.bud_kaj2, R.id.bud_kaj3)
        private val STIKALA = intArrayOf(
            R.id.bud_stikalo1, R.id.bud_stikalo2, R.id.bud_stikalo3)

        fun osvezi(c: Context) {
            val am = AppWidgetManager.getInstance(c) ?: return
            val idji = am.getAppWidgetIds(ComponentName(c, WidgetBudilke::class.java))
            if (idji.isEmpty()) return
            val v = pogled(c)
            idji.forEach { am.updateAppWidget(it, v) }
        }

        /**
         * Katere budilke widget kaze.
         *
         * **Tudi ugasnjene**, in to je ves smisel: widget je tu zato, da jih je
         * mogoce prizgati nazaj. Vrstni red je po uri odhoda, ugasnjena pa ne
         * gre na konec -- jutri ob sedmih je jutri ob sedmih, ne glede na
         * stikalo, in premikanje vrstic pod prstom je najlazji nacin, da clovek
         * preklopi napacno.
         */
        fun zaPrikaz(c: Context, zdajMs: Long): List<Budilka> =
            Shramba.vse(c)
                .filter { it.ponavljajoca || it.voznoredniMs > zdajMs - 60_000L }
                .sortedBy { it.voznoredniMs }

        private fun pogled(c: Context): RemoteViews {
            val v = RemoteViews(c.packageName, R.layout.widget_budilke)
            val zdaj = System.currentTimeMillis()
            val vse = zaPrikaz(c, zdaj)

            // Dotik ozadja odpre seznam. Ta je nativen in dela brez omrezja --
            // isto kot widget sam.
            v.setOnClickPendingIntent(R.id.bud_koren, PendingIntent.getActivity(
                c, 0, Intent(c, BudilkeDejavnost::class.java),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))

            v.setTextViewText(R.id.bud_glava, c.getString(R.string.widget_budilke_glava))
            v.setViewVisibility(R.id.bud_prazno, if (vse.isEmpty()) View.VISIBLE else View.GONE)
            if (vse.isEmpty()) {
                v.setTextViewText(R.id.bud_prazno, c.getString(R.string.widget_brez_kako))
            }

            for (i in 0 until VRSTIC) {
                val b = vse.getOrNull(i)
                v.setViewVisibility(VRSTICA[i], if (b == null) View.GONE else View.VISIBLE)
                if (b == null) continue
                narisi(c, v, i, b, zdaj)
            }

            val vec = vse.size - VRSTIC
            v.setViewVisibility(R.id.bud_vec, if (vec > 0) View.VISIBLE else View.GONE)
            if (vec > 0) {
                v.setTextViewText(R.id.bud_vec, c.getString(R.string.widget_budilke_vec, vec))
            }
            return v
        }

        private fun narisi(c: Context, v: RemoteViews, i: Int, b: Budilka, zdajMs: Long) {
            // Ura zvonjenja, ne odhoda: widget odgovarja na "kdaj me zbudi".
            // Odstevanje do odhoda ima svoj widget in ga tu ne ponavljamo.
            v.setTextViewText(URE[i], URA.format(Date(b.izracun(zdajMs).zvoniOb)))
            // Ugasnjena mora biti ugasnjena na pogled, ne sele v napisu: ob
            // treh zjutraj je pomembno, katera vrstica NE bo zvonila.
            v.setTextColor(URE[i], c.getColor(
                if (b.ugasnjena) R.color.ink_faint else R.color.accent))
            v.setTextViewText(KAJ[i], buildString {
                append(if (b.trainNo.isBlank()) b.postaja else b.trainNo)
                if (b.postaja.isNotBlank() && b.trainNo.isNotBlank()) {
                    append(" · ").append(b.postaja)
                }
            })

            val stikalo = STIKALA[i]
            v.setTextViewText(stikalo, c.getString(
                if (b.ugasnjena) R.string.widget_budilka_izklop
                else R.string.widget_budilka_vklop))
            v.setTextColor(stikalo, c.getColor(
                if (b.ugasnjena) R.color.ink_mute else R.color.na_poudarku))
            v.setInt(stikalo, "setBackgroundResource",
                if (b.ugasnjena) R.drawable.pilula_izklop else R.drawable.pilula_vklop)
            // Bralnik zaslona bi sicer prebral samo stanje in ne bi povedal,
            // da je to gumb in kaj naredi.
            v.setContentDescription(stikalo, c.getString(
                if (b.ugasnjena) R.string.widget_budilka_izklop_opis
                else R.string.widget_budilka_vklop_opis, b.trainNo))

            // **`data` loci namere med sabo.** `extras` se pri primerjavi ne
            // upostevajo, zato bi `FLAG_UPDATE_CURRENT` vsa tri stikala zdruzil
            // v eno in vsako bi preklopilo isto budilko. Ista past kot pri
            // budnicah v `Nacrtovalec`.
            val i2 = Intent(c, WidgetBudilke::class.java).apply {
                action = PREKLOPI
                data = Uri.parse("kajros://preklop/${b.id}")
                putExtra(ID, b.id)
            }
            v.setOnClickPendingIntent(stikalo, PendingIntent.getBroadcast(
                c, 0, i2,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
        }
    }
}
