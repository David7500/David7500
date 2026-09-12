package app.kajros

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.SystemClock
import android.util.TypedValue
import android.view.View
import android.widget.RemoteViews
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Widget na domacem zaslonu: koliko casa je se do odhoda.
 *
 * **Odsteva `Chronometer`, ne mi.** Widget, ki bi kazal sekunde in bi ga
 * risala aplikacija, bi zahteval prebujanje vsako sekundo -- to je baterija za
 * nic. `Chronometer` s `setChronometerCountDown` tece v sistemskem procesu in
 * nas ne stane nicesar; mi mu povemo samo, do kdaj naj steje.
 *
 * Zamuda se osvezi takrat, ko se ze tako zbudi budilka (`Sprozilec`), torej od
 * priblizno pol ure pred odhodom. Prej widget kaze vozni red in to tudi pise --
 * dodatno spraševanje strežnika vsako minuto cel dan bi bilo za eno stevilko
 * predrago.
 */
class Widget : AppWidgetProvider() {

    override fun onUpdate(c: Context, am: AppWidgetManager, idji: IntArray) {
        // **Tu se ponavljajoca budilka prestavi, tudi ce aplikacije nihce ne
        // odpre.** Brez tega bi budilka, ki je odzvonila in je nihce ni
        // ustavil, ostala `odzvonjeno` za vedno -- widget bi pisal "ni
        // budilke", jutrisnji alarm pa ne bi bil nastavljen. Sistem nas zaradi
        // widgeta tako ali tako zbudi vsake pol ure; to je najcenejsi kraj,
        // kjer se to lahko popravi samo od sebe.
        Nacrtovalec.vseZnova(c)
        idji.forEach { am.updateAppWidget(it, pogled(c)) }
    }

    /** Ko potnik doda prvi widget, se mora nekje zaceti tudi osvezevanje. */
    override fun onEnabled(c: Context) {
        Nacrtovalec.vseZnova(c)
    }

    companion object {

        private val URA = SimpleDateFormat("HH:mm", Locale("sl"))
        /** "tor. 06:49" -- dan in ura, kadar je odhod predalec za odstevanje. */
        private val DAN_URA = SimpleDateFormat("EEE HH:mm", Locale("sl"))
        /** "tor. 15. 9. 06:49" -- ko je vec kot teden dni in bi bil dan dvoumen. */
        private val DATUM_URA = SimpleDateFormat("EEE d. M. HH:mm", Locale("sl"))

        /**
         * Do kod se odsteva v sekundah.
         *
         * Ni meritev, ampak presoja berljivosti: `65:00:31` na domacem zaslonu
         * bere kot stoparica in ne odgovori na vprasanje "kdaj mi pelje".
         * Dve uri sta okno, v katerem se clovek pripravlja na pot -- takrat je
         * ziva sekunda koristna, prej pa je koristna ura odhoda.
         *
         * Preklop se zgodi ob naslednji osvezitvi widgeta, torej najvec pol
         * ure pozneje (`updatePeriodMillis`) ali prej, ce se budilka tako ali
         * tako zbudi.
         */
        private const val BLIZU_MS = 2 * 3600 * 1000L
        private const val TEDEN_MS = 7 * 24 * 3600 * 1000L

        /** Prerise vse widgete. Klice se od povsod, kjer se budilke spremenijo. */
        fun osvezi(c: Context) {
            val am = AppWidgetManager.getInstance(c) ?: return
            val idji = am.getAppWidgetIds(ComponentName(c, Widget::class.java))
            if (idji.isEmpty()) return
            val v = pogled(c)
            idji.forEach { am.updateAppWidget(it, v) }
        }

        /**
         * Budilka, ki jo widget kaze: prva, ki se ni odzvonila in ni ugasnjena.
         *
         * Ena in ne seznam: widget je velik kot dve vrstici ikon in stevilka,
         * ki jo potnik lovi s praga, je ena sama.
         */
        fun naslednja(c: Context, zdajMs: Long): Budilka? =
            Shramba.vse(c)
                .filter { !it.ugasnjena && !it.odzvonjeno && it.voznoredniMs > zdajMs - 60_000L }
                .minByOrNull { it.izracun(zdajMs).odhodMs }

        private fun pogled(c: Context): RemoteViews {
            val v = RemoteViews(c.packageName, R.layout.widget)
            v.setOnClickPendingIntent(R.id.widget_koren, PendingIntent.getActivity(
                c, 0, Intent(c, GlavnaDejavnost::class.java),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))

            val zdaj = System.currentTimeMillis()
            val b = naslednja(c, zdaj)
            if (b == null) {
                v.setTextViewText(R.id.widget_kaj, c.getString(R.string.ime))
                v.setTextViewText(R.id.widget_kje, c.getString(R.string.widget_brez))
                v.setViewVisibility(R.id.widget_stevec, View.GONE)
                v.setViewVisibility(R.id.widget_staticno, View.GONE)
                v.setTextViewText(R.id.widget_pod, c.getString(R.string.widget_brez_kako))
                return v
            }

            val izid = b.izracun(zdaj)
            v.setTextViewText(R.id.widget_kaj, if (b.smer.isBlank()) b.trainNo
                else "${b.trainNo} → ${b.smer}")
            v.setTextViewText(R.id.widget_kje, b.postaja)

            // `Chronometer` steje v casovnici `elapsedRealtime`, ne v epoch --
            // zato razliko pristejemo, namesto da bi mu dali cas odhoda.
            val doOdhoda = izid.odhodMs - zdaj
            val odsteva = doOdhoda in 1..BLIZU_MS
            v.setViewVisibility(R.id.widget_stevec, if (odsteva) View.VISIBLE else View.GONE)
            v.setViewVisibility(R.id.widget_staticno, if (odsteva) View.GONE else View.VISIBLE)

            if (odsteva) {
                // `Chronometer` steje v casovnici `elapsedRealtime`, ne v epoch --
                // zato razliko pristejemo, namesto da bi mu dali cas odhoda.
                v.setChronometer(R.id.widget_stevec,
                    SystemClock.elapsedRealtime() + doOdhoda, null, true)
                v.setChronometerCountDown(R.id.widget_stevec, true)
            } else if (doOdhoda <= 0) {
                // Cez niclo `Chronometer` steje naprej z minusom; to ni odgovor.
                v.setTextViewText(R.id.widget_staticno, c.getString(R.string.widget_zdaj))
                v.setTextViewTextSize(R.id.widget_staticno, TypedValue.COMPLEX_UNIT_SP, 32f)
            } else {
                val oblika = if (doOdhoda > TEDEN_MS) DATUM_URA else DAN_URA
                v.setTextViewText(R.id.widget_staticno, oblika.format(Date(izid.odhodMs)))
                // Ura z dnevom je daljsa od stevca in pri 32sp uide iz okvira.
                v.setTextViewTextSize(R.id.widget_staticno, TypedValue.COMPLEX_UNIT_SP, 23f)
            }

            // Voznoredna ura pride iz budilke, ne iz racuna: `upostevanaS` ima
            // odsteto rezervo, `odhodMs` pa ne, zato bi izpeljava
            // `odhodMs - upostevanaS` uro zamaknila za rezervo.
            v.setTextViewText(R.id.widget_pod, pod(c, izid, URA.format(Date(b.voznoredniMs)),
                uraJeZgoraj = !odsteva && doOdhoda > 0))
            return v
        }

        /**
         * Vrstica pod stevilko: od kod je ura, ki jo widget kaze.
         *
         * `uraJeZgoraj` pove, da veliko polje ze kaze uro odhoda. Takrat je ne
         * ponovimo -- "tor. 06:49" nad "vozni red 06:49" sta dve imeni za isto
         * uro in nista dva podatka. Isto pravilo kot v seznamu budilk.
         */
        private fun pod(c: Context, izid: Ura.Izid, red: String, uraJeZgoraj: Boolean): String {
            val odhod = URA.format(Date(izid.odhodMs))
            val zamuda = Math.round(izid.upostevanaS / 60.0).toInt()
            return when {
                izid.vir != Ura.Vir.ZAMUDA ->
                    if (uraJeZgoraj) c.getString(R.string.widget_nepreverjena)
                    else c.getString(R.string.widget_vozni_red, odhod)
                izid.upostevanaS >= 60 ->
                    if (uraJeZgoraj) c.getString(R.string.widget_zamuja_dan, zamuda, red)
                    else c.getString(R.string.widget_zamuda, odhod, zamuda)
                izid.upostevanaS <= -60 ->
                    if (uraJeZgoraj) c.getString(R.string.widget_prezgodaj_dan, -zamuda, red)
                    else c.getString(R.string.widget_prezgodaj, odhod, -zamuda)
                else ->
                    if (uraJeZgoraj) c.getString(R.string.widget_tocno_dan)
                    else c.getString(R.string.widget_tocno, odhod)
            }
        }
    }
}
