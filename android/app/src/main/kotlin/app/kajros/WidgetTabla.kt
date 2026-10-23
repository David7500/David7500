package app.kajros

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.text.SpannableString
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.RelativeSizeSpan
import android.text.style.StrikethroughSpan
import android.view.View
import android.widget.RemoteViews
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Odhodna tabla ene postaje na domacem zaslonu, od ene ikone do pol zaslona.
 *
 * **Vprasanje je "kdaj mi pelje z moje postaje".** Widget z budilko nanj ne
 * odgovori: ta pove, koliko casa je se do voznje, ki si jo ze izbral. Ta pove,
 * katere so -- in prav to je vsakodnevno vprasanje, za katero je bilo doslej
 * treba odpreti aplikacijo.
 *
 * Velikost odloci, koliko pove (`Velikost`): 1×1 naslednji odhod, trak enega
 * s podrobnostmi ali tri v vrsti, 4×2 glavo z gumboma in tri vrstice, od 4×3
 * naprej seznam vseh odhodov v stirih urah, ki se drsi.
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

    /**
     * Potnik je widget raztegnil. Od Androida 12 postavitev izbere launcher
     * sam; prej jo izberemo mi iz nove velikosti ([Izris.odzivno]).
     */
    override fun onAppWidgetOptionsChanged(c: Context, am: AppWidgetManager, id: Int, o: Bundle?) {
        am.updateAppWidget(id, pogled(c, id))
    }

    override fun onReceive(c: Context, namera: Intent) {
        when (namera.action) {
            OSVEZI -> {
                val am = AppWidgetManager.getInstance(c) ?: return
                vOzadju(c, am.getAppWidgetIds(ComponentName(c, WidgetTabla::class.java)),
                    goAsync())
            }
            OBRNI -> {
                val id = namera.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,
                    AppWidgetManager.INVALID_APPWIDGET_ID)
                if (id == AppWidgetManager.INVALID_APPWIDGET_ID) return
                obrni(c, id)
                vOzadju(c, intArrayOf(id), goAsync())
            }
            IZRISI -> osvezi(c)
            else -> super.onReceive(c, namera)
        }
    }

    /**
     * Gumb ⇄: pri relaciji druga smer (iz službe domov), na avtobusni tabli
     * druga stran ceste.
     *
     * Stara tabla gre stran, preden pride nova: vrstice z druge strani ceste
     * pod novim napisom bi bile napačne, in brez omrežja bi tam tudi ostale.
     */
    private fun obrni(c: Context, id: Int) {
        val n = Tabla.nastavitev(c, id) ?: return
        val obrnjena = n.obrnjena()
        if (obrnjena != null) {
            Tabla.nastavi(c, id, obrnjena)
            Tabla.pozabiStanje(c, id)
            AppWidgetManager.getInstance(c)?.updateAppWidget(id, pogled(c, id))
            return
        }
        val s = Tabla.stanje(c, id) ?: return
        val nova = Tabla.naslednjaSmer(s.smeri, n.smer) ?: return
        Tabla.nastavi(c, id, n.copy(smer = nova.kljuc, smerNapis = nova.napis))
        Tabla.pozabiStanje(c, id)
        AppWidgetManager.getInstance(c)?.updateAppWidget(id, pogled(c, id))
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
        idji.forEach { am.updateAppWidget(it, pogled(c, it)) }
        Thread {
            try {
                for (id in idji) {
                    val n = Tabla.nastavitev(c, id) ?: continue
                    // Samo odgovor prepise shranjeno stanje. "Ni zveze" pusti
                    // pri miru, kar widget ze kaze -- stara tabla z uro je
                    // uporabna, prazna ni.
                    val izid = Tabla.prenesi(c, n)
                    if (izid !is Tabla.Izid.Odhodi) continue
                    // Stran ceste je ob uvozu izginila: tabla je cela, zato
                    // napis nad njo ne sme vec trditi ene strani.
                    val popravljena = izid.popravi(n)
                    if (popravljena != n) Tabla.nastavi(c, id, popravljena)
                    Tabla.shraniStanje(c, id, Tabla.Stanje(izid.vrstice,
                        System.currentTimeMillis(), izid.opozorilo, izid.smeri))
                    am.updateAppWidget(id, pogled(c, id))
                }
                naslednjiIzris(c)
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
        val am = c.getSystemService(AlarmManager::class.java) ?: return
        am.cancel(budnica(c))
        am.cancel(izris(c))
    }

    override fun onDeleted(c: Context, idji: IntArray) {
        idji.forEach { Tabla.pozabi(c, it) }
    }

    companion object {
        const val OSVEZI = "app.kajros.TABLA"
        private const val OBRNI = "app.kajros.TABLA_OBRNI"
        private const val IZRISI = "app.kajros.TABLA_IZRISI"

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

        /** Seznam (4×3 in več) zna RemoteViews brez storitve šele od Androida 12. */
        private val PONUJENE: List<Velikost> =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) Velikost.values().toList()
            else Velikost.values().toList() - Velikost.STOLPEC - Velikost.VELIK

        private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

        private val URE = intArrayOf(R.id.ura1, R.id.ura2, R.id.ura3)
        private val PARI = intArrayOf(R.id.par1, R.id.par2, R.id.par3)
        private val KAM = intArrayOf(R.id.kam1, R.id.kam2, R.id.kam3)
        private val TIRI = intArrayOf(R.id.tir1, R.id.tir2, R.id.tir3)
        private val ZAMUDE = intArrayOf(R.id.zam1, R.id.zam2, R.id.zam3)
        private val VRSTICE = intArrayOf(R.id.v1, R.id.v2, R.id.v3)

        private fun budnica(c: Context): PendingIntent = PendingIntent.getBroadcast(
            c, 0, Intent(c, WidgetTabla::class.java).setAction(OSVEZI),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        private fun izris(c: Context): PendingIntent = PendingIntent.getBroadcast(
            c, 0, Intent(c, WidgetTabla::class.java).setAction(IZRISI),
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
         * Tabla se premakne naprej sama, ko prvi vlak odpelje.
         *
         * Shranjeno stanje ima [Tabla.SHRANI] vrstic; ko prva odide
         * ([Tabla.Odhod.odideMs]), jo prerisemo iz shrambe -- brez zahteve.
         * Spet `ELAPSED_REALTIME` brez prebujanja: na ugasnjenem zaslonu ni
         * kaj premikati, ob prvem prizigu pa se to zgodi takoj.
         */
        private fun naslednjiIzris(c: Context) {
            val am = c.getSystemService(AlarmManager::class.java) ?: return
            val wm = AppWidgetManager.getInstance(c) ?: return
            val zdaj = System.currentTimeMillis()
            val kdaj = wm.getAppWidgetIds(ComponentName(c, WidgetTabla::class.java)).asList()
                .mapNotNull { Tabla.stanje(c, it) }
                .flatMap { s -> s.odhodi.filter { it.vidno(zdaj) && it.voznoredniMs > 0 } }
                .minOfOrNull { it.odideMs() }
            if (kdaj == null) { am.cancel(izris(c)); return }
            am.setWindow(AlarmManager.ELAPSED_REALTIME,
                SystemClock.elapsedRealtime() + maxOf(kdaj - zdaj, 30_000L),
                60_000L, izris(c))
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
                .forEach { am.updateAppWidget(it, pogled(c, it)) }
            naslednjiIzris(c)
        }

        /** Sveze podatke naroci sistem sam; to je samo prosnja zanje. */
        fun zahtevajPrenos(c: Context) {
            c.sendBroadcast(Intent(c, WidgetTabla::class.java).setAction(OSVEZI))
        }

        /**
         * Kaj widget kaze, za vse velikosti hkrati ([Izris.odzivno]), iz
         * shranjenega stanja. Prenosa tu ni -- risanje mora delati tudi brez
         * omrezja.
         */
        fun pogled(c: Context, widgetId: Int): RemoteViews =
            pogled(c, widgetId, Tabla.nastavitev(c, widgetId), Tabla.stanje(c, widgetId),
                System.currentTimeMillis())

        /** Izris iz [n] in [s] brez shrambe; pregled widgetov ga kliče z vzorcem. */
        fun pogled(
            c: Context, widgetId: Int, n: Tabla.Nastavitev?, s: Tabla.Stanje?, zdajMs: Long,
        ): RemoteViews {
            val slog = Izris.slog(c, n?.videz ?: Izris.Videz.TONSKA)
            return Izris.odzivno(c, widgetId, PONUJENE, Velikost.SREDNJI) { v ->
                if (n == null) brezPostaje(c, widgetId, v, slog)
                else Risba(c, widgetId, n, s, zdajMs, slog).zgradi(v)
            }
        }

        /**
         * Widget brez postaje: nastavitev je bila preklicana ali je ostal iz
         * varnostne kopije. Dotik jo odpre znova.
         */
        private fun brezPostaje(c: Context, id: Int, vel: Velikost, slog: Izris.Slog): RemoteViews {
            val klik = PendingIntent.getActivity(
                c, id,
                Intent(c, TablaNastavitev::class.java)
                    .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id)
                    .setData(Uri.parse("kajros://tabla/$id")),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            val v = if (vel == Velikost.MINI) RemoteViews(c.packageName, slog.mini).apply {
                setTextViewText(R.id.nad, c.getString(R.string.ime))
                setTextViewText(R.id.glavno, "—")
                setTextViewText(R.id.pod, c.getString(R.string.widget_tabla_izberi_kratko))
                setTextColor(R.id.pod, slog.drugotna)
            } else RemoteViews(c.packageName, R.layout.w_sporocilo).apply {
                setTextViewText(R.id.naslov, c.getString(R.string.ime))
                setTextViewText(R.id.besedilo, c.getString(R.string.widget_tabla_brez_postaje))
            }
            v.setOnClickPendingIntent(android.R.id.background, klik)
            return v
        }

        // Z isto stranjo ceste kot widget: stran bi sicer odprla obe in
        // potnik bi iskal vrstice, ki jih je pravkar videl. Relacija odpre
        // iskalnik z isto relacijo.
        private fun naslovTable(c: Context, n: Tabla.Nastavitev): String =
            if (n.cilj != null) Nastavitve.naslov(c) + (if (n.vlak) "/app/train" else "/app/bus") +
                "?from=" + Nastavitve.zaPot(n.postaja) + "&to=" + Nastavitve.zaPot(n.cilj)
            else Nastavitve.naslov(c) + (if (n.vlak) "/app/train" else "/app/bus") +
                "?station=" + Nastavitve.zaPot(n.postaja) +
                (if (n.smer.isNullOrBlank()) "" else "&smer=" + Nastavitve.zaPot(n.smer))

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
         * Ena tabla v vseh velikostih. Razred in ne funkcija s sedmimi
         * parametri: vsaka velikost rabi isto -- postajo, vrstice, ki se niso
         * odpeljale, staro uro in slog.
         */
        private class Risba(
            val c: Context,
            val id: Int,
            val n: Tabla.Nastavitev,
            val s: Tabla.Stanje?,
            val zdaj: Long,
            val slog: Izris.Slog,
        ) {
            /** Vrstice, ki se niso odpeljale ([Tabla.Odhod.vidno]). */
            val vidni: List<Tabla.Odhod> = s?.odhodi?.filter { it.vidno(zdaj) } ?: emptyList()
            val staro: Boolean = s != null && Tabla.jeStaro(s.obMs, zdaj)
            val koda = id * 20

            fun zgradi(vel: Velikost): RemoteViews = when (vel) {
                Velikost.MINI -> mini()
                Velikost.PAS -> trak(R.layout.w_pas, pas = true)
                Velikost.TRAK -> trak(slog.trak, pas = false)
                Velikost.TRAK_SIROK -> trakSirok()
                Velikost.KVADRAT -> kvadrat()
                Velikost.SREDNJI -> srednji()
                Velikost.STOLPEC -> velik(ozek = true)
                Velikost.VELIK -> velik(ozek = false)
            }

            /**
             * Barvi besedila tonske podlage. Brez podlage sta samo 1×1 in trak
             * ([slog]); vse drugo ima podlago tudi pri videzu "brez", in temno
             * besedilo za svetlo ozadje zaslona bi se na njej izgubilo.
             */
            private val tonski = Izris.slog(c, Izris.Videz.TONSKA)

            /** Prazna tabla ni okvara: pozno zvecer od tod res ne pelje nic. */
            private fun prazno(): String = c.getString(when {
                s == null -> R.string.widget_tabla_caka
                n.cilj != null -> R.string.widget_tabla_nic_zvez
                else -> R.string.widget_tabla_nic
            })

            /** Podnaslov pod imenom postaje: "→ Ljubljana" pri relaciji, sicer stran ceste. */
            private val podnaslov: String? = n.cilj?.let { "→ $it" } ?: n.smerNapis

            /** "Ljubljana", "Kranj → Ljubljana" ali "Bavarski dvor → Razstavišče". */
            private fun glava(): CharSequence {
                val smer = podnaslov ?: return n.postaja
                val b = SpannableStringBuilder(n.postaja).append("  ")
                val od = b.length
                b.append(smer)
                b.setSpan(ForegroundColorSpan(c.getColor(R.color.ink_mute)),
                    od, b.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                b.setSpan(RelativeSizeSpan(0.9f), od, b.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                return b
            }

            /**
             * "LPV 2010 → Koper" (pri avtobusu "LPP 6 → Črnuče"); pri relaciji
             * "prihod 07:29 · prestop Medvode · LP 2435" -- prihod prvi, ker ga
             * tropičje na ozkem widgetu ne sme odrezati, številka vlaka pa sme.
             */
            private fun voznja(o: Tabla.Odhod): String = when {
                o.prihod != null -> listOfNotNull(c.getString(R.string.widget_tabla_prihod, o.prihod),
                    prestop(o), o.trainNo.ifBlank { null }).joinToString(" · ")
                o.kam.isBlank() -> o.trainNo
                else -> "${o.trainNo} → ${o.kam}"
            }

            /** "prestop Ljubljana", "prestop Ljubljana (tesno)" ali "… ne drži". */
            private fun prestop(o: Tabla.Odhod): String? = o.prestop?.let {
                c.getString(R.string.widget_tabla_prestop, it) +
                    (o.prestopStanje?.let { st -> " ($st)" } ?: "")
            }

            /** Odpadla vožnja je prečrtana, ne izbrisana: potnik mora vedeti, da je ne bo. */
            private fun precrtaj(besedilo: String, da: Boolean): CharSequence {
                if (!da) return besedilo
                return SpannableString(besedilo).apply {
                    setSpan(StrikethroughSpan(), 0, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
            }

            /** Barva zamude te vrstice; odpadla je v barvi napake. */
            private fun barvaZamude(o: Tabla.Odhod): Int = c.getColor(
                if (o.odpadla) R.color.napaka else Izris.barvaZamude(o.razred))

            /** "odpade", "+4", "točno" ali pomisljaj. */
            private fun napisZamude(o: Tabla.Odhod): String =
                if (o.odpadla) c.getString(R.string.widget_tabla_odpade) else Tabla.zamudaNapis(o)

            /**
             * Zamuda z barvo razreda. Brez podlage ([brez]) je stevilka v barvi
             * besedila s piko razreda pred njo: oranzna na svetlem ozadju
             * zaslona ne doseze kontrasta, beseda pa nosi minute tako ali tako.
             */
            private fun zamuda(v: RemoteViews, viewId: Int, o: Tabla.Odhod, brez: Boolean = false) {
                if (o.odpadla) {
                    v.setTextViewText(viewId, napisZamude(o))
                    v.setTextColor(viewId, barvaZamude(o))
                    return
                }
                val napis = napisZamude(o)
                val barva = barvaZamude(o)
                if (brez) {
                    v.setTextViewText(viewId, Izris.spikoZamude(napis, barva))
                    v.setTextColor(viewId, slog.glavna)
                } else {
                    v.setTextViewText(viewId, napis)
                    v.setTextColor(viewId, barva)
                }
                if (o.zamudaMin == null) {
                    // Pomisljaj sam ne pove nicesar; bralnik zaslona mora izvedeti,
                    // da to ni nicla, ampak manjkajoc podatek.
                    v.setContentDescription(viewId, c.getString(R.string.widget_tabla_ni_zamude))
                }
            }

            /** "osveženo ob 06:52" ali, ko je star, "podatek ob 06:12 — star 40 min". */
            private fun ob(v: RemoteViews, viewId: Int) {
                val st = s ?: run { v.setTextViewText(viewId, ""); return }
                v.setTextViewText(viewId, when {
                    st.obMs <= 0 -> ""
                    staro -> c.getString(R.string.widget_tabla_staro,
                        URA.format(Date(st.obMs)), Tabla.starostMin(st.obMs, zdaj))
                    else -> c.getString(R.string.widget_tabla_ob, URA.format(Date(st.obMs)))
                })
                v.setTextColor(viewId, c.getColor(if (staro) R.color.sev_hard else R.color.ink_faint))
                v.setContentDescription(viewId, c.getString(R.string.widget_tabla_osvezi))
                v.setOnClickPendingIntent(viewId, osveziNamera())
            }

            private fun osveziNamera(): PendingIntent = PendingIntent.getBroadcast(
                c, 0, Intent(c, WidgetTabla::class.java).setAction(OSVEZI),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

            private fun obrniNamera(): PendingIntent = PendingIntent.getBroadcast(
                c, id,
                Intent(c, WidgetTabla::class.java).setAction(OBRNI)
                    .setData(Uri.parse("kajros://tabla-obrni/$id"))
                    .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

            private fun klikTabla(v: RemoteViews) =
                v.setOnClickPendingIntent(android.R.id.background,
                    Izris.odpri(c, koda, naslovTable(c, n)))

            /** Bralnik zaslona prebere vrstico kot stavek, ne kot štiri besede. */
            private fun opis(o: Tabla.Odhod): String = buildString {
                append(o.ura).append(", ").append(voznja(o))
                if (!o.tir.isNullOrBlank()) append(", tir ").append(o.tir)
                append(", ")
                append(if (o.odpadla) c.getString(R.string.widget_tabla_odpade)
                    else if (o.zamudaMin == null) c.getString(R.string.widget_tabla_ni_zamude)
                    else Tabla.zamudaNapis(o))
            }

            // ---------- velikosti ----------

            /** 1×1: naslednji odhod in njegova zamuda; star podatek pove uro. */
            private fun mini(): RemoteViews {
                val v = RemoteViews(c.packageName, slog.mini)
                klikTabla(v)
                // Pri relaciji cilj: od kod potnik ve, kam pa je na ikoni treba povedati.
                v.setTextViewText(R.id.nad, n.cilj?.let { "→ $it" } ?: n.postaja)
                v.setTextColor(R.id.nad, slog.drugotna)
                val o = vidni.firstOrNull()
                if (o == null) {
                    v.setTextViewText(R.id.glavno, "—")
                    v.setTextColor(R.id.glavno, slog.drugotna)
                    v.setTextViewText(R.id.pod, c.getString(
                        if (s == null) R.string.widget_tabla_caka_kratko
                        else R.string.widget_tabla_nic_kratko))
                    v.setTextColor(R.id.pod, slog.drugotna)
                    v.setContentDescription(android.R.id.background, n.postaja + ": " + prazno())
                    return v
                }
                v.setTextViewText(R.id.glavno, precrtaj(o.ura, o.odpadla))
                v.setTextColor(R.id.glavno, if (staro) slog.drugotna else slog.glavna)
                if (staro) {
                    v.setTextViewText(R.id.pod, c.getString(R.string.widget_tabla_ob_kratko,
                        URA.format(Date(s!!.obMs))))
                    v.setTextColor(R.id.pod, c.getColor(R.color.sev_hard))
                } else {
                    zamuda(v, R.id.pod, o, slog.brez)
                }
                v.setContentDescription(android.R.id.background, n.postaja + ": " + opis(o))
                return v
            }

            /** Trak: prvi odhod s podrobnostmi; pas je isto v eni vrsti. */
            private fun trak(postavitev: Int, pas: Boolean): RemoteViews {
                val v = RemoteViews(c.packageName, postavitev)
                klikTabla(v)
                val o = vidni.firstOrNull()
                // Pas ima podlago vedno (`w_pas`), tudi pri videzu "brez".
                val sl = if (pas) tonski else slog
                v.setTextColor(R.id.nad, sl.drugotna)
                v.setTextColor(R.id.opis, sl.drugotna)
                if (o == null) {
                    v.setTextViewText(R.id.nad, n.postaja)
                    v.setTextViewText(R.id.glavno, "—")
                    v.setTextColor(R.id.glavno, sl.drugotna)
                    v.setTextViewText(R.id.pod, "")
                    v.setTextViewText(R.id.opis, prazno())
                    if (pas) v.setTextViewText(R.id.nad, n.postaja + " · " + prazno())
                    return v
                }
                v.setTextViewText(R.id.glavno, precrtaj(o.ura, o.odpadla))
                v.setTextColor(R.id.glavno, if (staro) sl.drugotna else sl.glavna)
                zamuda(v, R.id.pod, o, sl.brez)
                val podrobno = voznja(o) + (if (o.tir.isNullOrBlank()) "" else " · " + c.getString(R.string.widget_tir, o.tir))
                if (pas) {
                    // Pas nima vrstice za uro podatka: star podatek pove spredaj, rumeno.
                    val kje = glava().toString()
                    v.setTextViewText(R.id.nad, if (!staro) "$kje · $podrobno"
                        else SpannableStringBuilder().apply {
                            append(c.getString(R.string.widget_tabla_ob_kratko, URA.format(Date(s!!.obMs))))
                            setSpan(ForegroundColorSpan(c.getColor(R.color.sev_hard)), 0, length,
                                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                            append(" · ").append(kje).append(" · ").append(podrobno)
                        })
                } else {
                    v.setTextViewText(R.id.nad, glava())
                    if (staro) {
                        v.setTextViewText(R.id.opis, c.getString(R.string.widget_tabla_staro,
                            URA.format(Date(s!!.obMs)), Tabla.starostMin(s.obMs, zdaj)))
                        v.setTextColor(R.id.opis, c.getColor(R.color.sev_hard))
                    } else {
                        v.setTextViewText(R.id.opis, precrtaj(podrobno, o.odpadla))
                    }
                }
                v.setContentDescription(android.R.id.background, n.postaja + ": " + opis(o))
                return v
            }

            /** 4×1: trije odhodi v vrsti in gumb za osvezitev. */
            private fun trakSirok(): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_tabla_trak_sirok)
                klikTabla(v)
                v.setTextViewText(R.id.postaja, glava())
                v.setOnClickPendingIntent(R.id.osvezi, osveziNamera())
                ob(v, R.id.ob)
                val pokazi = vidni.isNotEmpty()
                v.setViewVisibility(R.id.odhodi, if (pokazi) View.VISIBLE else View.GONE)
                v.setViewVisibility(R.id.sporocilo, if (pokazi) View.GONE else View.VISIBLE)
                if (!pokazi) { v.setTextViewText(R.id.sporocilo, prazno()); return v }
                for (i in PARI.indices) {
                    // Prazna tretjina ostane, da odhodi ne skacejo po sirini.
                    val o = vidni.getOrNull(i)
                    v.setTextViewText(PARI[i], if (o == null) "" else par(o))
                }
                v.setContentDescription(android.R.id.background,
                    n.postaja + ": " + vidni.take(3).joinToString("; ") { opis(it) })
                return v
            }

            /** "14:45 +4" v enem napisu: ura krepko, zamuda manjsa v barvi razreda. */
            private fun par(o: Tabla.Odhod): CharSequence = SpannableStringBuilder().apply {
                append(precrtaj(o.ura, o.odpadla))
                append(" ")
                val od = length
                append(napisZamude(o))
                setSpan(ForegroundColorSpan(barvaZamude(o)), od, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                setSpan(RelativeSizeSpan(0.8f), od, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            }

            /** Krog z vlakom ali avtobusom pred imenom postaje. */
            private fun ikona(v: RemoteViews) {
                val t = Izris.ton(c, n.vlak)
                v.setInt(R.id.ikona, "setBackgroundResource", t.krog)
                v.setImageViewResource(R.id.ikona, t.ikona)
                v.setInt(R.id.ikona, "setColorFilter", t.glavna)
            }

            /** Tri fiksne vrstice (2×2 in 4×2); vsaka odpre svojo vožnjo. */
            private fun vrstice(v: RemoteViews, polne: Boolean) {
                val pokazi = vidni.isNotEmpty()
                v.setViewVisibility(R.id.sporocilo, if (pokazi) View.GONE else View.VISIBLE)
                if (!pokazi) v.setTextViewText(R.id.sporocilo, prazno())
                for (i in VRSTICE.indices) {
                    val o = vidni.getOrNull(i)
                    v.setViewVisibility(VRSTICE[i], if (o == null) View.GONE else View.VISIBLE)
                    if (o == null) continue
                    v.setTextViewText(URE[i], precrtaj(o.ura, o.odpadla))
                    v.setTextViewText(KAM[i], precrtaj(
                        if (polne) voznja(o) else kratko(o), o.odpadla))
                    if (polne) v.setTextViewText(TIRI[i], tir(o))
                    zamuda(v, ZAMUDE[i], o)
                    v.setContentDescription(VRSTICE[i], opis(o))
                    // Vrstica odpre SVOJO voznjo. Widget pove, da nekaj zamuja;
                    // naslednje vprasanje je "kje je" in to je okno voznje.
                    v.setOnClickPendingIntent(VRSTICE[i],
                        Izris.odpri(c, koda + 1 + i, naslovVoznje(c, n, o)))
                }
            }

            /** "tir 3" ali nic. */
            private fun tir(o: Tabla.Odhod): String =
                if (o.tir.isNullOrBlank()) "" else c.getString(R.string.widget_tir, o.tir)

            /**
             * Ozka vrstica pod uro: "Koper · tir 3" (avtobus: "LPP 6 → Črnuče"),
             * pri relaciji "prihod 07:29 · tir 3".
             */
            private fun kratko(o: Tabla.Odhod): String = listOfNotNull(
                when {
                    o.prihod != null -> c.getString(R.string.widget_tabla_prihod, o.prihod)
                    n.vlak -> o.kam.ifBlank { o.trainNo }
                    else -> voznja(o)
                },
                prestop(o), tir(o).ifBlank { null },
            ).joinToString(" · ")

            /** 2×2 in 3×2: ime postaje, tri kratke vrstice, ura podatka. */
            private fun kvadrat(): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_tabla_kvadrat)
                klikTabla(v)
                ikona(v)
                v.setTextViewText(R.id.postaja, if (n.cilj != null) glava().toString() else n.postaja)
                vrstice(v, polne = false)
                ob(v, R.id.ob)
                return v
            }

            /** Glava 4×2 in velikega: ikona, postaja, stran ceste in gumbi. */
            private fun glavaZGumbi(v: RemoteViews) {
                ikona(v)
                v.setTextViewText(R.id.postaja, n.postaja)
                v.setViewVisibility(R.id.smer, if (podnaslov == null) View.GONE else View.VISIBLE)
                podnaslov?.let { v.setTextViewText(R.id.smer, it) }
                v.setOnClickPendingIntent(R.id.osvezi, osveziNamera())
                // Obrni samo, kjer je kaj obrniti: relacija (druga smer) ali
                // postajalisce z vec stranmi ceste.
                val obrniti = n.cilj != null || (!n.vlak && (s?.smeri?.size ?: 0) > 1)
                v.setViewVisibility(R.id.obrni, if (obrniti) View.VISIBLE else View.GONE)
                if (obrniti) {
                    v.setOnClickPendingIntent(R.id.obrni, obrniNamera())
                    v.setContentDescription(R.id.obrni, c.getString(
                        if (n.cilj != null) R.string.widget_tabla_zamenjaj else R.string.widget_tabla_obrni))
                }
                val ovira = s?.opozorilo
                v.setViewVisibility(R.id.ovira, if (ovira == null) View.GONE else View.VISIBLE)
                if (ovira != null) {
                    // Ovire železnice imajo svojo stran; avtobusne so na tabli
                    // postajališča (`alerts.for_stops`).
                    val kam = if (n.vlak) Nastavitve.naslov(c) + "/app/ovire" else naslovTable(c, n)
                    v.setContentDescription(R.id.ovira, ovira)
                    v.setOnClickPendingIntent(R.id.ovira, Izris.odpri(c, koda + 9, kam))
                }
            }

            /** 4×2: glava z gumbi, tri polne vrstice, ura podatka. */
            private fun srednji(): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_tabla_srednji)
                klikTabla(v)
                glavaZGumbi(v)
                vrstice(v, polne = true)
                ob(v, R.id.ob)
                return v
            }

            /**
             * 4×3 in vec (Android 12+): seznam vseh odhodov, ki se drsi. Ozek
             * (2×3) ima vrstice v dveh vrsticah in glavo brez znaka in gumba za
             * osvezitev -- ime postaje je v tej sirini pomembnejse, osvezi pa
             * tudi dotik ure podatka.
             */
            private fun velik(ozek: Boolean): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_tabla_velik)
                klikTabla(v)
                glavaZGumbi(v)
                if (ozek) {
                    v.setViewVisibility(R.id.ikona, View.GONE)
                    v.setViewVisibility(R.id.osvezi, View.GONE)
                }
                // Na velikem je ovira vrstica nad seznamom; gumb bi jo podvojil.
                v.setViewVisibility(R.id.ovira, View.GONE)
                val ovira = s?.opozorilo
                v.setViewVisibility(R.id.opozorilo, if (ovira == null) View.GONE else View.VISIBLE)
                if (ovira != null) v.setTextViewText(R.id.opozorilo_besedilo, ovira)
                ob(v, R.id.ob)
                val pokazi = vidni.isNotEmpty()
                v.setViewVisibility(R.id.sporocilo, if (pokazi) View.GONE else View.VISIBLE)
                v.setViewVisibility(R.id.seznam, if (pokazi) View.VISIBLE else View.GONE)
                if (!pokazi) { v.setTextViewText(R.id.sporocilo, prazno()); return v }
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    val b = RemoteViews.RemoteCollectionItems.Builder()
                        .setHasStableIds(true).setViewTypeCount(1)
                    vidni.forEachIndexed { i, o -> b.addItem(i.toLong(), vrsticaSeznama(o, ozek)) }
                    v.setRemoteAdapter(R.id.seznam, b.build())
                    v.setPendingIntentTemplate(R.id.seznam, Izris.predlogaOdpri(c, koda + 10))
                }
                return v
            }

            private fun vrsticaSeznama(o: Tabla.Odhod, ozek: Boolean): RemoteViews {
                val r = RemoteViews(c.packageName,
                    if (ozek) R.layout.w_tabla_vrstica_ozka else R.layout.w_tabla_vrstica)
                r.setTextViewText(R.id.ura, precrtaj(o.ura, o.odpadla))
                r.setTextViewText(R.id.kam, precrtaj(if (ozek) kratko(o) else voznja(o), o.odpadla))
                r.setTextViewText(R.id.tir, tir(o))
                zamuda(r, R.id.zam, o)
                r.setContentDescription(R.id.vrstica, opis(o))
                r.setOnClickFillInIntent(R.id.vrstica, Izris.vstavekOdpri(naslovVoznje(c, n, o)))
                return r
            }
        }
    }
}
