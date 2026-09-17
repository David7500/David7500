package app.kajros

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.SystemClock
import android.view.View
import android.widget.RemoteViews
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Odhodna tabla ene postaje na domacem zaslonu.
 *
 * **Vprasanje je "kdaj mi pelje z moje postaje".** Widget z budilko nanj ne
 * odgovori: ta pove, koliko casa je se do voznje, ki si jo ze izbral. Ta pove,
 * katere so -- in prav to je vsakodnevno vprasanje, za katero je bilo doslej
 * treba odpreti aplikacijo.
 *
 * Postajo izbere potnik ob dodajanju widgeta ([TablaNastavitev]) in vsak widget
 * ima svojo: dva sta dva konca iste poti.
 */
class WidgetTabla : AppWidgetProvider() {

    override fun onUpdate(c: Context, am: AppWidgetManager, idji: IntArray) {
        naRitem(c)
        // `goAsync` tu dela, ker `onUpdate` tece znotraj `onReceive`. Brez
        // njega sme sistem proces ubiti takoj, ko se sprejemnik konca -- in
        // nit s prenosom bi umrla sredi zahteve.
        vOzadju(c, idji, goAsync())
    }

    override fun onReceive(c: Context, namera: Intent) {
        if (namera.action == OSVEZI) {
            val am = AppWidgetManager.getInstance(c) ?: return
            vOzadju(c, am.getAppWidgetIds(ComponentName(c, WidgetTabla::class.java)),
                goAsync())
            return
        }
        super.onReceive(c, namera)
    }

    /**
     * Prerise iz shranjenega stanja takoj, nato v niti prenese sveze.
     *
     * **Omrezje ne sme na glavno nit**: `onReceive` tece na njej in
     * `NetworkOnMainThreadException` bi widget podrl. Prvi izris je zato iz
     * shrambe -- widget se ne sme zatemniti, dokler cakamo na odgovor.
     */
    private fun vOzadju(c: Context, idji: IntArray, rezultat: PendingResult) {
        val am = AppWidgetManager.getInstance(c)
        if (am == null || idji.isEmpty()) { rezultat.finish(); return }
        idji.forEach { am.updateAppWidget(it, pogled(c, it, null)) }
        Thread {
            try {
                for (id in idji) {
                    val n = Tabla.nastavitev(c, id) ?: continue
                    // Samo odgovor prepise shranjeno stanje. "Ni zveze" pusti
                    // pri miru, kar widget ze kaze -- stara tabla z uro je
                    // uporabna, prazna ni.
                    val izid = Tabla.prenesi(c, n)
                    if (izid !is Tabla.Izid.Odhodi) continue
                    Tabla.shraniStanje(c, id,
                        Tabla.Stanje(izid.vrstice, System.currentTimeMillis()))
                    am.updateAppWidget(id, pogled(c, id, null))
                }
            } finally {
                rezultat.finish()
            }
        }.start()
    }

    override fun onEnabled(c: Context) {
        naRitem(c)
    }

    /** Zadnji widget je odstranjen: budnice ni vec komu buditi. */
    override fun onDisabled(c: Context) {
        c.getSystemService(AlarmManager::class.java)?.cancel(budnica(c))
    }

    override fun onDeleted(c: Context, idji: IntArray) {
        idji.forEach { Tabla.pozabi(c, it) }
    }

    companion object {
        const val OSVEZI = "app.kajros.TABLA"

        /**
         * Kako pogosto widget vprasa streznik.
         *
         * **`updatePeriodMillis` tega ne zmore**: sistemski minimum je 30 minut
         * in krajse vrednosti tiho zaokrozi navzgor. Zato lastna budnica.
         *
         * `ELAPSED_REALTIME` in **ne** `_WAKEUP`: telefona ne bujamo zaradi
         * table, ki je nihce ne gleda. Budnica pocaka na prvo, ko je telefon
         * tako ali tako buden -- in to je priblizno takrat, ko clovek pogleda
         * zaslon. Doze jo sme premakniti in to je prav; zato widget nosi uro
         * podatka in ne obljublja svezine, ki je ne more zagotoviti.
         */
        private val KORAK_MS = AlarmManager.INTERVAL_FIFTEEN_MINUTES

        private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

        private val VRSTICA = intArrayOf(
            R.id.tab_vrstica1, R.id.tab_vrstica2, R.id.tab_vrstica3)
        private val URE = intArrayOf(R.id.tab_ura1, R.id.tab_ura2, R.id.tab_ura3)
        private val KAM = intArrayOf(R.id.tab_kam1, R.id.tab_kam2, R.id.tab_kam3)
        private val ZAMUDE = intArrayOf(
            R.id.tab_zamuda1, R.id.tab_zamuda2, R.id.tab_zamuda3)

        private fun budnica(c: Context): PendingIntent = PendingIntent.getBroadcast(
            c, 0, Intent(c, WidgetTabla::class.java).setAction(OSVEZI),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        /** Nastavi ponavljajoco osvezitev. Klice se ob zagonu, dodajanju in vsaki osvezitvi. */
        fun naRitem(c: Context) {
            val am = c.getSystemService(AlarmManager::class.java) ?: return
            // `setInexactRepeating` in ne tocen alarm: to ni budilka. Sistem jih
            // sme zdruziti z drugimi in prav zato skoraj nic ne stane.
            am.setInexactRepeating(
                AlarmManager.ELAPSED_REALTIME,
                SystemClock.elapsedRealtime() + KORAK_MS, KORAK_MS, budnica(c))
        }

        /**
         * Prerise vse table iz shranjenega stanja, brez prenosa.
         *
         * Rabi jo nastavitev, ko widget dobi postajo: takrat je stanje ze
         * shranjeno in nova zahteva bi bila druga za isto sekundo.
         */
        fun osvezi(c: Context) {
            val am = AppWidgetManager.getInstance(c) ?: return
            am.getAppWidgetIds(ComponentName(c, WidgetTabla::class.java))
                .forEach { am.updateAppWidget(it, pogled(c, it, null)) }
        }

        /** Sveze podatke naroci sistem sam; to je samo prosnja zanje. */
        fun zahtevajPrenos(c: Context) {
            c.sendBroadcast(Intent(c, WidgetTabla::class.java).setAction(OSVEZI))
        }

        /**
         * Kaj widget kaze.
         *
         * [vsiljeno] je za predogled in preizkus; sicer se bere shranjeno
         * stanje. Prenosa tu ni -- risanje mora delati tudi brez omrezja.
         */
        fun pogled(c: Context, widgetId: Int, vsiljeno: Tabla.Stanje?): RemoteViews {
            val v = RemoteViews(c.packageName, R.layout.widget_tabla)
            val n = Tabla.nastavitev(c, widgetId)
            val zdaj = System.currentTimeMillis()

            if (n == null) {
                // Widget brez postaje: nastavitev je bila preklicana ali je
                // ostal iz varnostne kopije. Dotik jo odpre znova.
                v.setTextViewText(R.id.tab_postaja, c.getString(R.string.ime))
                v.setTextViewText(R.id.tab_sporocilo,
                    c.getString(R.string.widget_tabla_brez_postaje))
                v.setViewVisibility(R.id.tab_sporocilo, View.VISIBLE)
                VRSTICA.forEach { v.setViewVisibility(it, View.GONE) }
                v.setTextViewText(R.id.tab_ob, "")
                v.setOnClickPendingIntent(R.id.tab_koren, PendingIntent.getActivity(
                    c, widgetId,
                    Intent(c, TablaNastavitev::class.java)
                        .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
                        .setData(Uri.parse("kajros://tabla/$widgetId")),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
                return v
            }

            v.setTextViewText(R.id.tab_postaja, n.postaja)
            // Glava odpre tablo te postaje v aplikaciji -- isti pogled, cel.
            v.setOnClickPendingIntent(R.id.tab_koren, odpri(c, widgetId, naslovTable(c, n)))

            val s = vsiljeno ?: Tabla.stanje(c, widgetId)
            if (s == null) {
                v.setTextViewText(R.id.tab_sporocilo, c.getString(R.string.widget_tabla_caka))
                v.setViewVisibility(R.id.tab_sporocilo, View.VISIBLE)
                VRSTICA.forEach { v.setViewVisibility(it, View.GONE) }
                v.setTextViewText(R.id.tab_ob, "")
                return v
            }

            v.setViewVisibility(R.id.tab_sporocilo,
                if (s.odhodi.isEmpty()) View.VISIBLE else View.GONE)
            if (s.odhodi.isEmpty()) {
                // Prazna tabla ni okvara: pozno zvecer od tod res ne pelje nic.
                v.setTextViewText(R.id.tab_sporocilo, c.getString(R.string.widget_tabla_nic))
            }

            for (i in VRSTICA.indices) {
                val o = s.odhodi.getOrNull(i)
                v.setViewVisibility(VRSTICA[i], if (o == null) View.GONE else View.VISIBLE)
                if (o == null) continue
                narisi(c, v, i, o, widgetId, n)
            }

            // **Ura podatka je del podatka.** Brez nje je "+4 min" izpred pol
            // ure videti enako kot "+4 min" izpred pol minute. Dotik osvezi.
            val star = Tabla.jeStaro(s.obMs, zdaj)
            v.setTextViewText(R.id.tab_ob, when {
                s.obMs <= 0 -> ""
                star -> c.getString(R.string.widget_tabla_staro,
                    URA.format(Date(s.obMs)), Tabla.starostMin(s.obMs, zdaj))
                else -> c.getString(R.string.widget_tabla_ob, URA.format(Date(s.obMs)))
            })
            v.setTextColor(R.id.tab_ob,
                c.getColor(if (star) R.color.sev_hard else R.color.ink_faint))
            v.setContentDescription(R.id.tab_ob, c.getString(R.string.widget_tabla_osvezi))
            v.setOnClickPendingIntent(R.id.tab_ob, PendingIntent.getBroadcast(
                c, 0, Intent(c, WidgetTabla::class.java).setAction(OSVEZI),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
            return v
        }

        private fun narisi(
            c: Context, v: RemoteViews, i: Int, o: Tabla.Odhod,
            widgetId: Int, n: Tabla.Nastavitev,
        ) {
            v.setTextViewText(URE[i], o.ura)
            v.setTextViewText(KAM[i], if (o.kam.isBlank()) o.trainNo
                else "${o.trainNo} → ${o.kam}")
            v.setTextViewText(ZAMUDE[i], Tabla.zamudaNapis(o))
            v.setTextColor(ZAMUDE[i], c.getColor(barva(o)))
            if (o.zamudaMin == null) {
                // Pomisljaj sam ne pove nicesar; bralnik zaslona mora izvedeti,
                // da to ni nicla, ampak manjkajoc podatek.
                v.setContentDescription(ZAMUDE[i],
                    c.getString(R.string.widget_tabla_ni_zamude))
            }
            // Vrstica odpre SVOJO voznjo. Widget pove, da nekaj zamuja;
            // naslednje vprasanje je "kje je" in to je okno vozje.
            v.setOnClickPendingIntent(VRSTICA[i],
                odpri(c, widgetId * 10 + i, naslovVoznje(c, n, o)))
        }

        /** Razred pride s streznika; barva je oblikovanje in sme biti tu. */
        private fun barva(o: Tabla.Odhod): Int = when (o.razred) {
            "tocno" -> R.color.d_ontime
            "1-5" -> R.color.d_small
            "5-15" -> R.color.d_mid
            "nad-15" -> R.color.d_big
            else -> R.color.ink_faint
        }

        private fun naslovTable(c: Context, n: Tabla.Nastavitev): String =
            Nastavitve.naslov(c) + (if (n.vlak) "/app/train" else "/app/bus") +
                "?station=" + Nastavitve.zaPot(n.postaja)

        private fun naslovVoznje(c: Context, n: Tabla.Nastavitev, o: Tabla.Odhod): String =
            buildString {
                append(Nastavitve.naslov(c))
                append(if (n.vlak) "/app/train/" else "/app/bus/")
                // `zaPot` in ne `URLEncoder`: stevilka gre v POT in presledek
                // mora biti `%20`. Glej opombo v `Nastavitve`.
                append(Nastavitve.zaPot(o.trainNo))
                append("?postaja=").append(Nastavitve.zaPot(n.postaja))
                if (!o.tripId.isNullOrBlank()) {
                    append("&trip=").append(Nastavitve.zaPot(o.tripId))
                }
            }

        /**
         * Namera, ki odpre naslov v aplikaciji.
         *
         * [koda] loci namere med sabo: brez nje bi `FLAG_UPDATE_CURRENT` vse
         * vrstice zdruzil v eno, ker se `extras` pri primerjavi ne upostevajo.
         */
        private fun odpri(c: Context, koda: Int, kam: String): PendingIntent =
            PendingIntent.getActivity(
                c, koda,
                Intent(c, GlavnaDejavnost::class.java)
                    .setAction(GlavnaDejavnost.AKCIJA_ODPRI)
                    .putExtra(GlavnaDejavnost.KAM, kam),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }
}
