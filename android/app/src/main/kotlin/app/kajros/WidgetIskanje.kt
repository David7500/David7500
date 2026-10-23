package app.kajros

import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.RemoteViews

/**
 * Iskalna vrstica: „Kam greš?“ odpre pot od vrat do vrat s kazalcem v polju
 * Kam (`/app/pot#kam`, kot na domači strani), gumba ob njej iskalnika vlakov
 * in avtobusov.
 *
 * Nič ne prenese, nič ne hrani, nastavitve nima: je samo vrata v aplikacijo,
 * en dotik prej kot ikona aplikacije in domača stran.
 */
class WidgetIskanje : AppWidgetProvider() {

    override fun onUpdate(c: Context, m: AppWidgetManager, ids: IntArray) {
        for (id in ids) m.updateAppWidget(id, pogled(c, id))
    }

    /** Pred Androidom 12 postavitev po velikosti izbere aplikacija (`Izris.odzivno`). */
    override fun onAppWidgetOptionsChanged(c: Context, m: AppWidgetManager, id: Int, o: Bundle) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) m.updateAppWidget(id, pogled(c, id))
    }

    companion object {
        /**
         * V eni celici povečevalo, do štirih vrstica brez gumbov omrežij,
         * od štirih (`TRAK_SIROK`) z njima. Ležeče je 4×1 nižji od traku in
         * ostane brez gumbov: vrstica sama še vedno pelje do obeh omrežij.
         */
        private val PONUJENE = listOf(Velikost.MINI, Velikost.PAS, Velikost.TRAK_SIROK)

        fun pogled(c: Context, id: Int): RemoteViews =
            Izris.odzivno(c, id, PONUJENE, Velikost.TRAK_SIROK) { izris(c, id, it) }

        private fun izris(c: Context, id: Int, vel: Velikost): RemoteViews {
            val naslov = Nastavitve.naslov(c)
            val koda = id * 20
            if (vel == Velikost.MINI) {
                return RemoteViews(c.packageName, R.layout.w_iskanje_mini).also {
                    it.setOnClickPendingIntent(R.id.kam, Izris.odpri(c, koda, "$naslov/app/pot#kam"))
                }
            }
            val v = RemoteViews(c.packageName, R.layout.w_iskanje)
            v.setOnClickPendingIntent(R.id.kam, Izris.odpri(c, koda, "$naslov/app/pot#kam"))
            if (vel == Velikost.TRAK_SIROK) {
                v.setOnClickPendingIntent(R.id.vlaki, Izris.odpri(c, koda + 1, "$naslov/app/train"))
                v.setOnClickPendingIntent(R.id.avtobusi, Izris.odpri(c, koda + 2, "$naslov/app/bus"))
            } else {
                v.setViewVisibility(R.id.vlaki, View.GONE)
                v.setViewVisibility(R.id.avtobusi, View.GONE)
            }
            return v
        }
    }
}
