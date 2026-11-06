package app.kajros

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.RemoteViews
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Budilke s stikali, od ene do vseh.
 *
 * **Zakaj poleg odstevanja se ta.** Prvi widget odgovarja na "koliko casa imam
 * se" in kaze eno samo budilko. Vprasanje, ki ga ne pokrije, je vecerno:
 * "katere budilke so nastavljene in ali jutri sploh grem". Danes je zanj treba
 * odpreti aplikacijo in najti seznam.
 *
 * **Nic omreznega.** Vse, kar widget pokaze, je v telefonu -- ura zvonjenja je
 * izracunana iz shranjene budilke. Zato dela tudi takrat, ko streznika ni, in
 * ne stane niti ene zahteve.
 *
 * Velikost odloci, koliko jih pokaze (`Velikost`): 1×1 in trak prvo, 2×2 dve,
 * 4×2 tri z dnevi, od 2×3 naprej (Android 12+) vse v seznamu, ki se drsi.
 */
class WidgetBudilke : AppWidgetProvider() {

    override fun onUpdate(c: Context, am: AppWidgetManager, idji: IntArray) {
        // Isti samopopravek kot pri odstevanju: ponavljajoca budilka, ki je
        // odzvonila in je nihce ni ustavil, bi sicer ostala `odzvonjeno` za
        // vedno. Sistem nas zaradi widgeta tako ali tako zbudi.
        Nacrtovalec.vseZnova(c)
        idji.forEach { am.updateAppWidget(it, pogled(c, it)) }
    }

    override fun onAppWidgetOptionsChanged(c: Context, am: AppWidgetManager, id: Int, o: Bundle?) {
        am.updateAppWidget(id, pogled(c, id))
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

        private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

        /** Seznam (2×3 in vec) zna RemoteViews brez storitve sele od Androida 12. */
        private val PONUJENE: List<Velikost> =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) Velikost.values().toList()
            else Velikost.values().toList() - Velikost.STOLPEC - Velikost.VELIK

        private val VRSTICA = intArrayOf(R.id.bud_vrstica1, R.id.bud_vrstica2, R.id.bud_vrstica3)
        private val URE = intArrayOf(R.id.bud_ura1, R.id.bud_ura2, R.id.bud_ura3)
        private val KAJ = intArrayOf(R.id.bud_kaj1, R.id.bud_kaj2, R.id.bud_kaj3)
        private val DNI = intArrayOf(R.id.bud_dni1, R.id.bud_dni2, R.id.bud_dni3)
        private val STIKALA = intArrayOf(R.id.bud_stikalo1, R.id.bud_stikalo2, R.id.bud_stikalo3)

        fun osvezi(c: Context) {
            val am = AppWidgetManager.getInstance(c) ?: return
            am.getAppWidgetIds(ComponentName(c, WidgetBudilke::class.java))
                .forEach { am.updateAppWidget(it, pogled(c, it)) }
        }

        /**
         * Katere budilke widget kaze.
         *
         * **Tudi ugasnjene**, in to je ves smisel: widget je tu zato, da jih je
         * mogoce prizgati nazaj. Vrstni red je po uri odhoda, ugasnjena pa ne
         * gre na konec -- jutri ob sedmih je jutri ob sedmih, ne glede na
         * stikalo, in premikanje vrstic pod prstom je najlazji nacin, da clovek
         * preklopi napacno. Zato tudi 1×1 kaze prvo po uri, ne prvo prizgano:
         * ugasnjena bi pod prstom izginila in na njenem mestu bi bila druga.
         */
        fun zaPrikaz(c: Context, zdajMs: Long): List<Budilka> =
            Shramba.vse(c)
                .filterNot { it.opravljena(zdajMs) }
                .sortedBy { it.voznoredniMs }

        fun pogled(c: Context, widgetId: Int): RemoteViews {
            val zdaj = System.currentTimeMillis()
            return pogled(c, widgetId, zaPrikaz(c, zdaj), zdaj)
        }

        /** Izris za [vse] v vseh velikostih; pregled widgetov ga klice z vzorcem. */
        fun pogled(c: Context, widgetId: Int, vse: List<Budilka>, zdajMs: Long): RemoteViews =
            Izris.odzivno(c, widgetId, PONUJENE, Velikost.KVADRAT) { vel ->
                Risba(c, vse, zdajMs).zgradi(vel)
            }

        private class Risba(val c: Context, val vse: List<Budilka>, val zdaj: Long) {

            /**
             * Od Androida 12 je 4×2 ze seznam: tri vrstice pokoncno se izidejo,
             * lezece (117 dp) pa ne -- seznam pokaze, kolikor gre, in se drsi,
             * nepremicne vrstice pa bi se odrezale na pol.
             */
            fun zgradi(vel: Velikost): RemoteViews = when {
                vse.isEmpty() -> prazno(vel)
                vel == Velikost.MINI -> ena(R.layout.w_mini, vel)
                vel == Velikost.PAS -> ena(R.layout.w_pas, vel)
                vel == Velikost.TRAK || vel == Velikost.TRAK_SIROK -> ena(R.layout.w_trak, vel)
                vel == Velikost.KVADRAT -> vrstice(R.layout.w_budilke_kvadrat, 2, ozka = true)
                Build.VERSION.SDK_INT < Build.VERSION_CODES.S ->
                    vrstice(R.layout.w_budilke_srednji, 3, ozka = false)
                else -> seznam(ozka = vel == Velikost.STOLPEC)
            }

            /** Dotik ozadja odpre seznam. Ta je nativen in dela brez omrezja -- isto kot widget sam. */
            private fun naSeznam(v: RemoteViews) =
                v.setOnClickPendingIntent(android.R.id.background, PendingIntent.getActivity(
                    c, 0, Intent(c, BudilkeDejavnost::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))

            private fun dan(ms: Long): String = Izris.dan(c, ms, zdaj)

            /** "LPV 2010 · Ljubljana". */
            private fun kaj(b: Budilka): String =
                listOf(b.trainNo, b.postaja).filter { it.isNotBlank() }.joinToString(" · ")

            /** Ozka vrstica: "LPV 2010 · vsak delavnik" -- postajo potnik pozna, dneve pa ne vidi drugje. */
            private fun kratko(b: Budilka): String =
                listOf(b.trainNo.ifBlank { b.postaja }, dni(b)).joinToString(" · ")

            /** "vsak delavnik", "enkratna · jutri" ali, po zvonjenju, "zazvonila · odhod 07:01". */
            private fun dni(b: Budilka): String = when {
                b.odzvonjeno -> c.getString(R.string.widget_budilka_zazvonila,
                    URA.format(Date(b.izracun(zdaj).odhodMs)))
                b.ponavljajoca -> Ponovitev.ime(b.dnevi)
                else -> c.getString(R.string.widget_budilka_enkratna, dan(b.izracun(zdaj).zvoniOb))
            }

            /**
             * Stikalo. **`data` loci namere med sabo**: `extras` se pri
             * primerjavi ne upostevajo, zato bi `FLAG_UPDATE_CURRENT` vsa
             * stikala zdruzil v eno in vsako bi preklopilo isto budilko. Ista
             * past kot pri budnicah v `Nacrtovalec`.
             */
            private fun stikalo(v: RemoteViews, viewId: Int, b: Budilka, vSeznamu: Boolean) {
                v.setViewVisibility(viewId, View.VISIBLE)
                v.setImageViewResource(viewId, when {
                    b.ugasnjena -> R.drawable.stikalo_slika_izklop
                    b.vlak -> R.drawable.stikalo_slika_vklop
                    else -> R.drawable.stikalo_slika_vklop_bus
                })
                // Bralnik zaslona bi sicer prebral samo stanje in ne bi povedal,
                // da je to gumb in kaj naredi.
                v.setContentDescription(viewId, c.getString(
                    if (b.ugasnjena) R.string.widget_budilka_izklop_opis
                    else R.string.widget_budilka_vklop_opis, b.trainNo))
                val podatek = Uri.parse("kajros://preklop/${b.id}")
                if (vSeznamu) {
                    v.setOnClickFillInIntent(viewId, Intent().setData(podatek).putExtra(ID, b.id))
                    return
                }
                v.setOnClickPendingIntent(viewId, PendingIntent.getBroadcast(
                    c, 0,
                    Intent(c, WidgetBudilke::class.java)
                        .setAction(PREKLOPI).setData(podatek).putExtra(ID, b.id),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
            }

            /**
             * Ena vrstica. Ura zvonjenja, ne odhoda: widget odgovarja na "kdaj
             * me zbudi"; odstevanje do odhoda ima svoj widget.
             *
             * Ugasnjena mora biti ugasnjena na pogled, ne sele v napisu: ob
             * treh zjutraj je pomembno, katera vrstica NE bo zvonila. Kot v
             * seznamu: vklopljena tonska (rjava ali zelena po omrezju),
             * ugasnjena siva.
             */
            private fun vrstica(
                v: RemoteViews, vrstica: Int, ura: Int, kaj: Int, dni: Int, stikalo: Int,
                b: Budilka, vSeznamu: Boolean, ozka: Boolean,
            ) {
                val t = Izris.ton(c, b.vlak)
                v.setInt(vrstica, "setBackgroundResource",
                    if (b.ugasnjena) R.drawable.widget_vrstica_izklop else t.vrstica)
                v.setTextViewText(ura, URA.format(Date(b.izracun(zdaj).zvoniOb)))
                v.setTextColor(ura, if (b.ugasnjena) c.getColor(R.color.ink_faint) else t.glavna)
                val drugotna = if (b.ugasnjena) c.getColor(R.color.ink_mute) else t.drugotna
                v.setTextViewText(kaj, if (ozka) kratko(b) else kaj(b))
                v.setTextColor(kaj, drugotna)
                v.setTextViewText(dni, dni(b))
                v.setTextColor(dni, drugotna)
                stikalo(v, stikalo, b, vSeznamu)
            }

            // ---------- velikosti ----------

            /**
             * Brez budilk widget ne sme biti prazen pravokotnik: pove, da ni
             * okvara, in kje se nastavi. `_prazen`: stikalo zadnje budilke sicer
             * ostane (`res/values/postavitve.xml`).
             */
            private fun prazno(vel: Velikost): RemoteViews {
                val v = when (vel) {
                    Velikost.MINI -> RemoteViews(c.packageName, R.layout.w_mini_prazen).apply {
                        setTextViewText(R.id.nad, c.getString(R.string.widget_budilke_glava))
                        setTextViewText(R.id.glavno, "—")
                        setTextColor(R.id.glavno, c.getColor(R.color.ink_dim))
                    }
                    Velikost.PAS -> RemoteViews(c.packageName, R.layout.w_pas_prazen).apply {
                        setTextViewText(R.id.glavno, c.getString(R.string.widget_budilke_prazno))
                        setTextViewText(R.id.nad, c.getString(R.string.widget_budilke_kako))
                    }
                    Velikost.TRAK, Velikost.TRAK_SIROK -> RemoteViews(c.packageName, R.layout.w_sporocilo).apply {
                        setTextViewText(R.id.naslov, c.getString(R.string.widget_budilke_prazno))
                        setTextViewText(R.id.besedilo, c.getString(R.string.widget_budilke_kako))
                    }
                    else -> RemoteViews(c.packageName, when {
                        vel == Velikost.KVADRAT -> R.layout.w_budilke_kvadrat
                        Build.VERSION.SDK_INT < Build.VERSION_CODES.S -> R.layout.w_budilke_srednji
                        else -> R.layout.w_budilke_seznam
                    }).apply {
                        setViewVisibility(R.id.bud_prazno, View.VISIBLE)
                        VRSTICA.forEach { setViewVisibility(it, View.GONE) }
                        setViewVisibility(R.id.bud_vec, View.GONE)
                        setViewVisibility(R.id.seznam, View.GONE)
                        setTextViewText(R.id.bud_naslednja, "")
                    }
                }
                naSeznam(v)
                return v
            }

            /** 1×1, pas in trak: prva budilka po uri, s stikalom. */
            private fun ena(postavitev: Int, vel: Velikost): RemoteViews {
                val b = vse.first()
                val t = Izris.ton(c, b.vlak)
                val v = RemoteViews(c.packageName, postavitev)
                naSeznam(v)
                v.setInt(android.R.id.background, "setBackgroundResource",
                    if (b.ugasnjena) R.drawable.widget_ozadje else t.podlaga)
                val glavna = if (b.ugasnjena) c.getColor(R.color.ink_faint) else t.glavna
                val drugotna = if (b.ugasnjena) c.getColor(R.color.ink_mute) else t.drugotna
                v.setTextViewText(R.id.glavno, URA.format(Date(b.izracun(zdaj).zvoniOb)))
                v.setTextColor(R.id.glavno, glavna)
                v.setViewVisibility(R.id.pod, View.GONE)
                when (vel) {
                    Velikost.MINI -> v.setTextViewText(R.id.nad, b.trainNo.ifBlank { b.postaja })
                    Velikost.PAS -> v.setTextViewText(R.id.nad, kaj(b) + " · " + dni(b))
                    else -> {
                        v.setTextViewText(R.id.nad, kaj(b))
                        v.setTextViewText(R.id.opis, dni(b))
                    }
                }
                v.setTextColor(R.id.nad, drugotna)
                v.setTextColor(R.id.opis, drugotna)
                stikalo(v, R.id.stikalo, b, vSeznamu = false)
                return v
            }

            /** 2×2 in 4×2: do [n] vrstic; kadar jih je vec, "in se 2". */
            private fun vrstice(postavitev: Int, n: Int, ozka: Boolean): RemoteViews {
                val v = RemoteViews(c.packageName, postavitev)
                naSeznam(v)
                v.setViewVisibility(R.id.bud_prazno, View.GONE)
                for (i in VRSTICA.indices) {
                    val b = if (i < n) vse.getOrNull(i) else null
                    v.setViewVisibility(VRSTICA[i], if (b == null) View.GONE else View.VISIBLE)
                    if (b != null) {
                        vrstica(v, VRSTICA[i], URE[i], KAJ[i], DNI[i], STIKALA[i], b, false, ozka)
                    }
                }
                val vec = vse.size - n
                v.setViewVisibility(R.id.bud_vec, if (vec > 0) View.VISIBLE else View.GONE)
                if (vec > 0) v.setTextViewText(R.id.bud_vec, c.getString(R.string.widget_budilke_vec, vec))
                return v
            }

            /**
             * Od 4×2 in 2×3 naprej (Android 12+): vse budilke v seznamu, ki se
             * drsi, in spodaj, kdaj zazvoni naslednja. Ozek seznam ima ozke vrstice.
             *
             * Vrstica seznama nima svoje namere -- seznam ima eno predlogo, in
             * ta je stikalo. Dotik glave in noge odpre seznam v aplikaciji.
             */
            private fun seznam(ozka: Boolean): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_budilke_seznam)
                naSeznam(v)
                v.setViewVisibility(R.id.bud_prazno, View.GONE)
                v.setViewVisibility(R.id.seznam, View.VISIBLE)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    val s = RemoteViews.RemoteCollectionItems.Builder()
                        .setHasStableIds(true).setViewTypeCount(1)
                    vse.forEach { b ->
                        val r = RemoteViews(c.packageName,
                            if (ozka) R.layout.w_budilka_vrstica_ozka else R.layout.w_budilka_vrstica)
                        vrstica(r, R.id.bud_vrstica, R.id.bud_ura, R.id.bud_kaj, R.id.bud_dni,
                            R.id.bud_stikalo, b, vSeznamu = true, ozka = ozka)
                        s.addItem(b.id.hashCode().toLong(), r)
                    }
                    v.setRemoteAdapter(R.id.seznam, s.build())
                    // **Mora biti spremenljiva** (`FLAG_MUTABLE`): sistem vanjo
                    // vstavi `data` in id stikala, ki ga je potnik pritisnil.
                    v.setPendingIntentTemplate(R.id.seznam, PendingIntent.getBroadcast(
                        c, 1, Intent(c, WidgetBudilke::class.java).setAction(PREKLOPI),
                        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE))
                }
                v.setTextViewText(R.id.bud_naslednja, naslednja())
                return v
            }

            /** "naslednja zvoni jutri ob 06:41", ali da so vse ugasnjene. */
            private fun naslednja(): String {
                val prizgane = vse.filterNot { it.ugasnjena }
                if (prizgane.isEmpty()) return c.getString(R.string.widget_budilke_vse_ugasnjene)
                val ob = prizgane.filterNot { it.odzvonjeno }
                    .map { it.izracun(zdaj).zvoniOb }.filter { it > zdaj }.minOrNull() ?: return ""
                return c.getString(R.string.widget_budilke_naslednja, dan(ob), URA.format(Date(ob)))
            }
        }
    }
}
