package app.kajros

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
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
 * predrago. Kdor hoce vedeti takoj, ima na 4×1 in 4×2 gumb "preveri".
 *
 * Velikost odloci, koliko pove (`Velikost`): 1×1 samo stevec in zamudo, trak
 * se voznjo in uro odhoda, 2×2 zetona zamude in tira, 4×2 stavek o tem, od
 * kod je ura, in kdaj je bila zamuda preverjena.
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
        idji.forEach { am.updateAppWidget(it, pogled(c, it)) }
        naslednjiIzris(c)
    }

    override fun onReceive(c: Context, namera: Intent) {
        if (namera.action == IZRISI) { osvezi(c); return }
        super.onReceive(c, namera)
    }

    override fun onDisabled(c: Context) {
        c.getSystemService(AlarmManager::class.java)?.cancel(izris(c))
    }

    /**
     * Potnik je widget raztegnil. Od Androida 12 postavitev izbere launcher
     * sam; prej jo izberemo mi iz nove velikosti ([Izris.odzivno]).
     */
    override fun onAppWidgetOptionsChanged(c: Context, am: AppWidgetManager, id: Int, o: Bundle?) {
        am.updateAppWidget(id, pogled(c, id))
    }

    /** Ko potnik doda prvi widget, se mora nekje zaceti tudi osvezevanje. */
    override fun onEnabled(c: Context) {
        Nacrtovalec.vseZnova(c)
    }

    companion object {

        private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

        /**
         * Do kod se odsteva v sekundah.
         *
         * Ni meritev, ampak presoja berljivosti: `65:00:31` na domacem zaslonu
         * bere kot stoparica in ne odgovori na vprasanje "kdaj mi pelje".
         * Zadnja ura je okno, v katerem se clovek odpravlja -- takrat je ziva
         * sekunda koristna, prej pa je koristna ura odhoda. Do 23. 10. 2026 sta
         * bili dve uri, a "1:05:31" se ob zetonu zamude ne izide ne na 2×1 ne
         * na 2×2, in ura in pol pred odhodom je bolj uporabna ura kot stevec.
         *
         * Preklop se zgodi ob naslednji osvezitvi widgeta, torej najvec pol
         * ure pozneje (`updatePeriodMillis`) ali prej, ce se budilka tako ali
         * tako zbudi.
         */
        private const val BLIZU_MS = 3600 * 1000L

        /** Seznama odstevanje nima: kaze eno voznjo, tudi cez pol zaslona. */
        private val PONUJENE = listOf(
            Velikost.MINI, Velikost.PAS, Velikost.TRAK, Velikost.TRAK_SIROK,
            Velikost.KVADRAT, Velikost.SREDNJI,
        )

        private const val IZRISI = "app.kajros.ODSTEVANJE_IZRISI"

        /** Prerise vse widgete. Klice se od povsod, kjer se budilke spremenijo. */
        fun osvezi(c: Context) {
            val am = AppWidgetManager.getInstance(c) ?: return
            val idji = am.getAppWidgetIds(ComponentName(c, Widget::class.java))
            idji.forEach { am.updateAppWidget(it, pogled(c, it)) }
            if (idji.isNotEmpty()) naslednjiIzris(c)
        }

        private fun izris(c: Context): PendingIntent = PendingIntent.getBroadcast(
            c, 0, Intent(c, Widget::class.java).setAction(IZRISI),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        /**
         * Stevec se zacne uro pred odhodom in ob odhodu rece "zdaj" -- tudi
         * kadar se takrat ne zbudi nic drugega (budilka zacne preverjati sele
         * malo pred zvonjenjem, sistem widget osvezi na pol ure).
         *
         * `ELAPSED_REALTIME` brez `_WAKEUP`, kot pri tabli: na ugasnjenem
         * zaslonu ni kaj steti, ob prizigu pa se izris zgodi takoj.
         */
        private fun naslednjiIzris(c: Context) {
            val am = c.getSystemService(AlarmManager::class.java) ?: return
            val zdaj = System.currentTimeMillis()
            val odhod = naslednja(c, zdaj)?.izracun(zdaj)?.odhodMs
            val kdaj = listOfNotNull(odhod?.minus(BLIZU_MS), odhod).filter { it > zdaj }.minOrNull()
            if (kdaj == null) { am.cancel(izris(c)); return }
            am.setWindow(AlarmManager.ELAPSED_REALTIME,
                SystemClock.elapsedRealtime() + (kdaj - zdaj), 30_000L, izris(c))
        }

        /**
         * Budilka, ki jo widget kaze: prva, katere odhod se ni mimo.
         *
         * **Tudi odzvonjena.** Po zvonjenju je vprasanje "koliko casa imam se
         * do vlaka" -- prej je widget takrat pisal "ni budilke" ali jutrisnji
         * odhod, ravno ko je potnik stopil skozi vrata.
         *
         * Ena in ne seznam: stevilka, ki jo potnik lovi s praga, je ena sama.
         *
         * **Odzvonjena ostane do konca sledenja**, ne do odhoda po zdajsnjem
         * racunu. Ta pade na vozni red, kakor hitro zamuda ni sveza, in widget
         * je budilko izpustil toliko pred prihodom, kolikor je vlak zamujal
         * (22. 9. 2026). Konec sledenja je isti trenutek, ko jo `Nacrtovalec`
         * neha osvezevati -- dve meji za isto stvar bi se razsli.
         */
        fun naslednja(c: Context, zdajMs: Long): Budilka? =
            Shramba.vse(c)
                .filter {
                    !it.ugasnjena && if (it.odzvonjeno) zdajMs < it.konecSledenjaMs()
                        else maxOf(it.voznoredniMs, it.izracun(zdajMs).odhodMs) > zdajMs - 60_000L
                }
                .minByOrNull { it.izracun(zdajMs).odhodMs }

        fun pogled(c: Context, widgetId: Int): RemoteViews {
            val zdaj = System.currentTimeMillis()
            return pogled(c, widgetId, naslednja(c, zdaj), zdaj)
        }

        /** Izris za [b] v vseh velikostih; pregled widgetov ga klice z vzorcem. */
        fun pogled(c: Context, widgetId: Int, b: Budilka?, zdajMs: Long): RemoteViews =
            Izris.odzivno(c, widgetId, PONUJENE, Velikost.TRAK) { vel ->
                if (b == null) brezBudilke(c, vel) else Risba(c, widgetId, b, zdajMs).zgradi(vel)
            }

        /**
         * Brez budilke ni kam peljati in ostane domaca stran. Siva podlaga:
         * rjava kartica brez budilke bi obljubljala nekaj, cesar ni.
         */
        private fun brezBudilke(c: Context, vel: Velikost): RemoteViews {
            val v = when (vel) {
                Velikost.MINI -> RemoteViews(c.packageName, R.layout.w_mini).apply {
                    setTextViewText(R.id.nad, c.getString(R.string.ime))
                    setTextViewText(R.id.glavno, "—")
                    setTextColor(R.id.glavno, c.getColor(R.color.ink_dim))
                    setTextViewText(R.id.pod, c.getString(R.string.widget_brez))
                    setTextViewTextSize(R.id.pod, TypedValue.COMPLEX_UNIT_SP, 11f)
                }
                Velikost.PAS -> RemoteViews(c.packageName, R.layout.w_pas).apply {
                    setTextViewText(R.id.glavno, c.getString(R.string.widget_brez_naslov))
                    setTextViewText(R.id.nad, c.getString(R.string.widget_brez_kako))
                }
                else -> RemoteViews(c.packageName, R.layout.w_sporocilo).apply {
                    setTextViewText(R.id.naslov, c.getString(R.string.widget_brez_naslov))
                    setTextViewText(R.id.besedilo, c.getString(R.string.widget_brez_kako))
                }
            }
            v.setContentDescription(android.R.id.background, c.getString(R.string.widget_opis))
            v.setOnClickPendingIntent(android.R.id.background, PendingIntent.getActivity(
                c, 0, Intent(c, GlavnaDejavnost::class.java),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
            return v
        }

        /**
         * Ena budilka v vseh velikostih. Vse velikosti rabijo isti izracun --
         * odhod, zamudo, ki ji je racun verjel, in barve omrezja.
         */
        private class Risba(val c: Context, val id: Int, val b: Budilka, val zdaj: Long) {
            val izid = b.izracun(zdaj)
            val t = Izris.ton(c, b.vlak)
            val doOdhoda = izid.odhodMs - zdaj

            /**
             * Zamuda v zaokrozenih minutah, ali null, kadar ji racun ne verjame.
             *
             * Iz odhoda in ne iz `upostevanaS`: ta ima odsteto potnikovo
             * rezervo, in widget je pri treh minutah rezerve in dveh zamude
             * pisal "1 min pred redom" za vlak, ki je zamujal.
             */
            val zamudaMin: Int? = if (izid.vir == Ura.Vir.ZAMUDA)
                Tabla.minute(((izid.odhodMs - b.voznoredniMs) / 1000).toInt()) else null

            /** Vsak widget svoje kode: `extras` namere med sabo ne locijo. */
            val koda = id * 20

            fun zgradi(vel: Velikost): RemoteViews = when (vel) {
                Velikost.MINI -> mini()
                Velikost.PAS -> trak(R.layout.w_pas, pas = true, gumb = false)
                Velikost.TRAK -> trak(R.layout.w_trak, pas = false, gumb = false)
                Velikost.TRAK_SIROK -> trak(R.layout.w_trak, pas = false, gumb = true)
                Velikost.KVADRAT -> kvadrat()
                else -> srednji()
            }

            /** "LPV 2010 → Koper". */
            private fun kaj(): String =
                if (b.smer.isBlank()) b.trainNo else "${b.trainNo} → ${b.smer}"

            /**
             * Dotik pelje **na voznjo**, ne na domaco stran. Widget odgovarja
             * na "koliko casa imam se", naslednje vprasanje pa je "in kje je
             * zdaj" -- domaca stran nanj ne odgovori.
             */
            private fun osnova(v: RemoteViews) {
                v.setInt(android.R.id.background, "setBackgroundResource", t.podlaga)
                v.setOnClickPendingIntent(android.R.id.background,
                    Izris.odpri(c, koda, b.naslovVoznje(Nastavitve.naslov(c))))
                // Bralnik zaslona bi sicer prebral samo stoparico, ki je brez
                // konteksta gola stevilka. Ura odhoda je tu in ne v
                // `Chronometer`, ker se ta ne da prebrati.
                v.setContentDescription(android.R.id.background, buildString {
                    append(b.trainNo)
                    if (b.smer.isNotBlank()) append(", smer ").append(b.smer)
                    append(", ").append(b.postaja).append(". ").append(stavek())
                })
            }

            /**
             * Velika stevilka: odstevanje, "zdaj" ali ura odhoda.
             *
             * [manjsa] je velikost pisave za uro z dnevom, ki je daljsa od
             * stevca in bi pri polni velikosti usla iz okvira; null pusti
             * velikost iz postavitve.
             */
            private fun stevilka(v: RemoteViews, manjsa: Float?, samoUra: Boolean) {
                val odsteva = doOdhoda in 1..BLIZU_MS
                v.setViewVisibility(R.id.stevec, if (odsteva) View.VISIBLE else View.GONE)
                v.setViewVisibility(R.id.glavno, if (odsteva) View.GONE else View.VISIBLE)
                v.setTextColor(R.id.stevec, t.glavna)
                v.setTextColor(R.id.glavno, t.glavna)
                when {
                    // `Chronometer` steje v casovnici `elapsedRealtime`, ne v
                    // epoch -- zato razliko pristejemo, namesto da bi mu dali
                    // cas odhoda.
                    odsteva -> {
                        v.setChronometer(R.id.stevec,
                            SystemClock.elapsedRealtime() + doOdhoda, null, true)
                        v.setChronometerCountDown(R.id.stevec, true)
                    }
                    // Cez niclo `Chronometer` steje naprej z minusom; to ni odgovor.
                    doOdhoda <= 0 -> v.setTextViewText(R.id.glavno, c.getString(R.string.widget_zdaj))
                    samoUra -> v.setTextViewText(R.id.glavno, URA.format(Date(izid.odhodMs)))
                    else -> {
                        val napis = Izris.danUra(c, izid.odhodMs, zdaj)
                        v.setTextViewText(R.id.glavno, napis)
                        // Samo daljsi napis ("jutri 06:57") gre manjsi; ura sama ostane velika.
                        if (napis.length > 5) manjsa?.let {
                            v.setTextViewTextSize(R.id.glavno, TypedValue.COMPLEX_UNIT_SP, it)
                        }
                    }
                }
            }

            /**
             * Ali zeton zamude kaj pove. Dalec od odhoda zamude se nihce ne
             * pozna in pomisljaj je samo sum; v zadnji uri pa pove, da je se ni.
             */
            private val zetonPove: Boolean = zamudaMin != null || doOdhoda <= BLIZU_MS

            /**
             * Zeton zamude. Na tonski podlagi je podlaga strani, kot `.bud-zam`
             * na domaci strani: temna oranzna (`d_big`) na rjavem ne doseze
             * kontrasta. Barva nikoli sama -- v zetonu je vedno stevilka.
             */
            private fun zeton(v: RemoteViews, viewId: Int, dolgo: Boolean) {
                val m = zamudaMin
                v.setViewVisibility(viewId, if (zetonPove) View.VISIBLE else View.GONE)
                v.setInt(viewId, "setBackgroundResource", R.drawable.zeton_temen)
                v.setTextViewText(viewId, when {
                    m == null || !dolgo -> Tabla.zamudaNapis(m)
                    m <= -1 -> c.getString(R.string.widget_zeton_prej, -m)
                    m == 0 -> c.getString(R.string.widget_zeton_tocno)
                    else -> c.getString(R.string.widget_zeton_zamuja, m)
                })
                v.setTextColor(viewId, c.getColor(
                    if (m == null) R.color.ink_faint else Izris.barvaZamude(Tabla.razred(m))))
            }

            /** Tir s table SŽ ob zadnjem preverjanju; brez njega widget ne ugiba. */
            private fun tir(): String? = b.tir?.let { c.getString(R.string.widget_tir, it) }

            /**
             * Kratek stavek traku: ura odhoda in postaja. Kadar je ura odhoda
             * ze zgoraj (odhod je dalec), je ne ponovimo.
             */
            private fun kratko(): String {
                val zDodatki = listOfNotNull(b.postaja.ifBlank { null }, tir()).joinToString(" · ")
                return when {
                    doOdhoda <= 0 || doOdhoda > BLIZU_MS -> zDodatki
                    izid.vir == Ura.Vir.ZAMUDA -> c.getString(R.string.widget_odhod_kje,
                        URA.format(Date(izid.odhodMs)), zDodatki)
                    else -> c.getString(R.string.widget_red_kje,
                        URA.format(Date(b.voznoredniMs)), zDodatki)
                }
            }

            /**
             * Vrstica pod stevilko: od kod je ura, ki jo widget kaze.
             *
             * Ko veliko polje ze kaze uro odhoda (odhod je dalec), je ne
             * ponovimo -- "tor. 06:49" nad "vozni red 06:49" sta dve imeni za
             * isto uro in nista dva podatka. Isto pravilo kot v seznamu budilk.
             */
            private fun stavek(): String {
                val red = URA.format(Date(b.voznoredniMs))
                val odhod = URA.format(Date(izid.odhodMs))
                val uraJeZgoraj = doOdhoda > BLIZU_MS
                // Po zvonjenju je "se ni preverjena" neresnica: bila je, a je
                // zdaj prestara, da bi ji stevec sledil. Zato pove, kaj je bilo
                // znano in kdaj -- stevec pa vseeno tece do voznega reda, ker
                // pred njim vlak ne odpelje.
                val zadnja = b.zamudaS?.let { Tabla.minute(it) } ?: 0
                if (b.odzvonjeno && izid.vir != Ura.Vir.ZAMUDA && zadnja >= 1) {
                    return c.getString(R.string.widget_zastarela, red,
                        URA.format(Date(b.zamudaObMs)), zadnja)
                }
                val m = zamudaMin ?: 0
                return when {
                    izid.vir == Ura.Vir.NI_PODATKA ->
                        if (uraJeZgoraj) c.getString(R.string.widget_ni_podatka_dan)
                        else c.getString(R.string.widget_ni_podatka, odhod)
                    izid.vir != Ura.Vir.ZAMUDA ->
                        if (uraJeZgoraj) c.getString(R.string.widget_nepreverjena)
                        else c.getString(R.string.widget_vozni_red, odhod)
                    m >= 1 ->
                        if (uraJeZgoraj) c.getString(R.string.widget_zamuja_dan, m, red)
                        else c.getString(R.string.widget_zamuda, odhod, m)
                    m <= -1 ->
                        if (uraJeZgoraj) c.getString(R.string.widget_prezgodaj_dan, -m, red)
                        else c.getString(R.string.widget_prezgodaj, odhod, -m)
                    else ->
                        if (uraJeZgoraj) c.getString(R.string.widget_tocno_dan)
                        else c.getString(R.string.widget_tocno, odhod)
                }
            }

            /** Stavek 2×2, kjer zamudo ze nosi zeton: samo, od kod je ura. */
            private fun stavekKratek(): String {
                val zadnja = b.zamudaS?.let { Tabla.minute(it) } ?: 0
                return when {
                    b.odzvonjeno && izid.vir != Ura.Vir.ZAMUDA && zadnja >= 1 ->
                        c.getString(R.string.widget_zastarela_kratko,
                            URA.format(Date(b.zamudaObMs)), zadnja)
                    izid.vir == Ura.Vir.ZAMUDA ->
                        c.getString(R.string.budilka_vozni_red, URA.format(Date(b.voznoredniMs)))
                    izid.vir == Ura.Vir.NI_PODATKA -> c.getString(R.string.widget_ni_podatka_dan)
                    doOdhoda > BLIZU_MS -> c.getString(R.string.widget_nepreverjena)
                    else -> c.getString(R.string.widget_red_nepreverjena,
                        URA.format(Date(b.voznoredniMs)))
                }
            }

            /**
             * Gumb "preveri zdaj": zamudo vpraša takoj, ne sele ob naslednjem
             * koraku budilke. Gre skozi `Sprozilec` kot budnica sama -- drug
             * zapis iste poti bi se z njo razsel. Svoj `data`, da ne povozi
             * budnice (`kajros://budilka/<id>`).
             */
            private fun preveri(v: RemoteViews, viewId: Int) {
                v.setViewVisibility(viewId, View.VISIBLE)
                v.setImageViewResource(viewId, R.drawable.ikona_osvezi)
                v.setInt(viewId, "setBackgroundResource", t.gumb)
                v.setInt(viewId, "setColorFilter", t.glavna)
                v.setContentDescription(viewId, c.getString(R.string.widget_preveri))
                v.setOnClickPendingIntent(viewId, PendingIntent.getBroadcast(
                    c, 0,
                    Intent(c, Sprozilec::class.java)
                        .setAction(Sprozilec.PROZI)
                        .setData(Uri.parse("kajros://preveri/${b.id}"))
                        .putExtra(Sprozilec.ID, b.id),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
            }

            // ---------- velikosti ----------

            /** 1×1: stevec in zamuda; odhod dalec je ura, pod njo dan, kadar ni danes. */
            private fun mini(): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_mini)
                osnova(v)
                v.setTextViewText(R.id.nad, b.trainNo)
                v.setTextColor(R.id.nad, t.drugotna)
                stevilka(v, null, samoUra = true)
                val dan = Izris.dan(c, izid.odhodMs, zdaj)
                if (!zetonPove && dan != c.getString(R.string.widget_danes)) {
                    v.setTextViewText(R.id.pod, dan)
                    v.setTextColor(R.id.pod, t.drugotna)
                } else {
                    zeton(v, R.id.pod, dolgo = false)
                }
                return v
            }

            /** Trak: voznja, stevilka z zetonom, ura odhoda; 4×1 se gumb. Pas je isto v eni vrsti. */
            private fun trak(postavitev: Int, pas: Boolean, gumb: Boolean): RemoteViews {
                val v = RemoteViews(c.packageName, postavitev)
                osnova(v)
                // Na traku se stevilka pomanjsa sama (`autoSizeTextType`).
                stevilka(v, null, samoUra = false)
                zeton(v, R.id.pod, dolgo = gumb)
                v.setTextColor(R.id.nad, t.drugotna)
                if (pas) {
                    v.setTextViewText(R.id.nad, kaj() + " · " + kratko())
                } else {
                    v.setTextViewText(R.id.nad, kaj())
                    v.setTextViewText(R.id.opis, kratko())
                    v.setTextColor(R.id.opis, t.drugotna)
                }
                if (gumb) preveri(v, R.id.gumb)
                return v
            }

            /** 2×2 in 3×2: voznja, smer in postaja, stevilka, zetona zamude in tira. */
            private fun kvadrat(): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_odstevanje_kvadrat)
                osnova(v)
                v.setTextViewText(R.id.kaj, b.trainNo)
                v.setTextColor(R.id.kaj, t.glavna)
                v.setTextViewText(R.id.kje, listOfNotNull(
                    b.smer.ifBlank { null }?.let { "→ $it" }, b.postaja.ifBlank { null },
                ).joinToString(" · "))
                v.setTextColor(R.id.kje, t.drugotna)
                // Velikost stevilke tu izbere postavitev sama (`autoSizeTextType`).
                stevilka(v, null, samoUra = false)
                zeton(v, R.id.zamuda, dolgo = true)
                if (zamudaMin == null) v.setViewVisibility(R.id.zamuda, View.GONE)
                val tir = tir()
                v.setViewVisibility(R.id.tir, if (tir == null) View.GONE else View.VISIBLE)
                if (tir != null) {
                    v.setTextViewText(R.id.tir, tir)
                    v.setInt(R.id.tir, "setBackgroundResource", t.zeton)
                    v.setTextColor(R.id.tir, t.glavna)
                }
                v.setTextViewText(R.id.pod, stavekKratek())
                v.setTextColor(R.id.pod, t.drugotna)
                return v
            }

            /**
             * Stavek ob zetonu, ki minute ze nosi: samo se, od kod je ura.
             * Brez zetona (zamuda ni sveza) je to cel [stavek].
             */
            private fun stavekObZetonu(): String {
                val m = zamudaMin ?: return stavek()
                val red = URA.format(Date(b.voznoredniMs))
                return when {
                    doOdhoda > BLIZU_MS -> c.getString(R.string.budilka_vozni_red, red)
                    m == 0 -> c.getString(R.string.budilka_odhod, red)
                    else -> c.getString(R.string.widget_odhod_red, URA.format(Date(izid.odhodMs)), red)
                }
            }

            /** 4×2: voznja, stevilka z zetonom, od kod je ura, kdaj je bila zamuda preverjena, gumb preveri. */
            private fun srednji(): RemoteViews {
                val v = RemoteViews(c.packageName, R.layout.w_odstevanje_srednji)
                osnova(v)
                v.setTextViewText(R.id.kaj, kaj())
                v.setTextColor(R.id.kaj, t.glavna)
                v.setTextViewText(R.id.kje,
                    listOfNotNull(b.postaja.ifBlank { null }, tir()).joinToString(" · "))
                v.setTextColor(R.id.kje, t.drugotna)
                stevilka(v, 26f, samoUra = false)
                // Kratek zeton kot na tabli ("+4", "2 prej"): ob 38 sp se
                // "2 min prej" na 4×2 ne izide.
                zeton(v, R.id.zamuda, dolgo = false)
                if (zamudaMin == null) v.setViewVisibility(R.id.zamuda, View.GONE)
                v.setTextViewText(R.id.podpis, stavekObZetonu())
                v.setTextColor(R.id.podpis, t.drugotna)
                // Kdaj je strežnik nazadnje odgovoril, tudi brez zamude: gumb
                // poleg pove, da se da vprašati znova.
                v.setTextViewText(R.id.pod, if (b.stikObMs > 0)
                    c.getString(R.string.widget_preverjeno, URA.format(Date(b.stikObMs))) else "")
                v.setTextColor(R.id.pod, t.drugotna)
                preveri(v, R.id.gumb)
                return v
            }
        }
    }
}
