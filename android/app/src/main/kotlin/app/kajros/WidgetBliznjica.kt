package app.kajros

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.util.SizeF
import android.view.View
import android.widget.RemoteViews

/**
 * Bližnjica: ena oblika z domače strani, en dotik do poti, iskalnika,
 * zemljevida, ovir ali budilk.
 *
 * Nič ne prenese in nima ritma: hrani samo, kaj odpre ([BliznjicaNastavitev])
 * in ali ima ime. Ime leži na ozadju zaslona kot ime ikone v launcherju, zato
 * je njegova barva odvisna od ozadja (`Izris.svetloOzadje`).
 */
class WidgetBliznjica : AppWidgetProvider() {

    /**
     * Kam vodi. Oblike in barve so z domače strani (budilka rjav cvet,
     * zemljevid modrozelena detelja) in iz table (omrežji, ovire); „Kam
     * greš?“ je poudarjen krog kot gumb iskanja na domači strani.
     */
    enum class Dejanje(
        val ime: Int, val opis: Int, val ikona: Int, val oblika: Int,
        val polnilo: Int, val barvaIkone: Int,
        /** Pot na strani; brez nje gre dotik v nativni seznam budilk. */
        val pot: String?,
    ) {
        POT(R.string.bliznjica_pot, R.string.bliznjica_pot_opis, R.drawable.ikona_pot,
            R.drawable.oblika_krog, R.color.poudarek, R.color.na_poudarku, "/app/pot#kam"),
        VLAKI(R.string.bliznjica_vlaki, R.string.bliznjica_vlaki_opis, R.drawable.ikona_vlak,
            R.drawable.oblika_zvezda, R.color.m_kont, R.color.m_na_kont, "/app/train"),
        AVTOBUSI(R.string.bliznjica_avtobusi, R.string.bliznjica_avtobusi_opis, R.drawable.ikona_bus,
            R.drawable.oblika_zvezda, R.color.bus_kont, R.color.bus_na_kont, "/app/bus"),
        ZEMLJEVID(R.string.bliznjica_zemljevid, R.string.bliznjica_zemljevid_opis,
            R.drawable.ikona_zemljevid, R.drawable.oblika_detelja, R.color.zem_kont,
            R.color.zem_na_kont, "/app/map"),
        /** Obrnjeni barvi ovire: temno rumen krog na temnem ozadju se ne vidi. */
        OVIRE(R.string.bliznjica_ovire, R.string.bliznjica_ovire_opis, R.drawable.ikona_ovira,
            R.drawable.oblika_krog, R.color.ovira_na_kont, R.color.ovira_kont, "/app/ovire"),
        BUDILKE(R.string.bliznjica_budilke, R.string.bliznjica_budilke_opis, R.drawable.ikona_budilka,
            R.drawable.oblika_cvet, R.color.m_kont, R.color.m_na_kont, null);

        companion object {
            fun iz(niz: String?): Dejanje? = values().firstOrNull { it.name == niz }
        }
    }

    override fun onUpdate(c: Context, m: AppWidgetManager, ids: IntArray) {
        for (id in ids) m.updateAppWidget(id, pogled(c, id))
    }

    override fun onDeleted(c: Context, ids: IntArray) {
        val e = prefs(c).edit()
        for (id in ids) e.remove(DEJANJE + id).remove(IME + id)
        e.apply()
    }

    /** Pred Androidom 12 ime pokaže ali skrije aplikacija sama (glej [izris]). */
    override fun onAppWidgetOptionsChanged(c: Context, m: AppWidgetManager, id: Int, o: Bundle) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) m.updateAppWidget(id, pogled(c, id))
    }

    companion object {
        private const val DEJANJE = "dejanje_"
        private const val IME = "ime_"

        /**
         * Od te višine je pod obliko prostor za ime: oblika 64 dp, ime 16 in
         * robovi. Nižja celica (1×1 ležeče, 51 dp) ime skrije, sicer bi ga
         * odrezalo napol.
         */
        private const val Z_IMENOM_DP = 92f

        private fun prefs(c: Context) =
            c.getSharedPreferences("bliznjica", Context.MODE_PRIVATE)

        fun dejanje(c: Context, id: Int): Dejanje? =
            Dejanje.iz(prefs(c).getString(DEJANJE + id, null))

        fun zImenom(c: Context, id: Int): Boolean = prefs(c).getBoolean(IME + id, true)

        fun shrani(c: Context, id: Int, d: Dejanje, ime: Boolean) {
            prefs(c).edit().putString(DEJANJE + id, d.name).putBoolean(IME + id, ime).apply()
        }

        /**
         * Dokler potnik ne izbere (nekateri launcherji widget narišejo, preden
         * se okno nastavitve zapre), kaže „Kam greš?“: prazen krog bi bil
         * videti kot okvara, pot od vrat do vrat pa so vrata, ki ne škodijo.
         */
        fun pogled(c: Context, id: Int): RemoteViews =
            izris(c, id, dejanje(c, id) ?: Dejanje.POT, zImenom(c, id))

        /**
         * Od Androida 12 obe različici naenkrat in launcher izbere po višini;
         * prej izbere aplikacija iz velikosti, ki jo pove launcher (pokončno
         * največja višina, ležeče najmanjša, kot `Izris.odzivno`).
         */
        fun izris(c: Context, id: Int, d: Dejanje, ime: Boolean): RemoteViews {
            if (!ime) return risba(c, id, d, false)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                return RemoteViews(mapOf(
                    SizeF(40f, 40f) to risba(c, id, d, false),
                    SizeF(40f, Z_IMENOM_DP) to risba(c, id, d, true)))
            }
            val o = AppWidgetManager.getInstance(c).getAppWidgetOptions(id)
            val pokoncno = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT)
            val lezece = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT)
            if (pokoncno <= 0) return risba(c, id, d, true)
            val p = pokoncno >= Z_IMENOM_DP
            val l = lezece >= Z_IMENOM_DP
            return if (p == l) risba(c, id, d, p) else RemoteViews(risba(c, id, d, l), risba(c, id, d, p))
        }

        private fun risba(c: Context, id: Int, d: Dejanje, ime: Boolean): RemoteViews {
            val v = RemoteViews(c.packageName,
                if (Izris.svetloOzadje(c)) R.layout.w_bliznjica_svetlo else R.layout.w_bliznjica)
            v.setImageViewResource(R.id.oblika, d.oblika)
            v.setInt(R.id.oblika, "setColorFilter", c.getColor(d.polnilo))
            v.setImageViewResource(R.id.ikona, d.ikona)
            v.setInt(R.id.ikona, "setColorFilter", c.getColor(d.barvaIkone))
            if (ime) v.setTextViewText(R.id.ime, c.getString(d.ime))
            v.setViewVisibility(R.id.ime, if (ime) View.VISIBLE else View.GONE)
            v.setContentDescription(R.id.bliznjica, c.getString(d.ime))
            v.setOnClickPendingIntent(R.id.bliznjica, namera(c, id, d))
            return v
        }

        private fun namera(c: Context, id: Int, d: Dejanje): PendingIntent =
            if (d.pot != null) Izris.odpri(c, id * 20, Nastavitve.naslov(c) + d.pot)
            // Ista namera kot ozadje widgeta z budilkami: seznam je nativen
            // in dela brez omrežja.
            else PendingIntent.getActivity(c, 0, Intent(c, BudilkeDejavnost::class.java),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }
}
