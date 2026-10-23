package app.kajros

import android.app.PendingIntent
import android.app.WallpaperColors
import android.app.WallpaperManager
import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.util.SizeF
import android.widget.RemoteViews
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

/**
 * Kar si widgeti delijo: izbira postavitve po velikosti, barve omrežja,
 * podlaga in namere, ki odprejo stran v aplikaciji.
 *
 * Widgeti so se razlikovali samo po vsebini, postavitve pa so bile vsak svoje
 * -- trije widgeti, tri različne velikosti iste številke. Skupne postavitve
 * (`w_mini`, `w_pas`, `w_trak`, `w_sporocilo`) imajo iste oznake in vsak widget
 * jih napolni po svoje.
 */
object Izris {

    /**
     * Kako widget leži na zaslonu.
     *
     * [BREZ] je samo besedilo na ozadju zaslona, za majhne widgete (1×1, trak);
     * večji brez podlage niso berljivi in ostanejo tonski.
     */
    enum class Videz {
        TONSKA, BREZ;

        companion object {
            fun iz(niz: String?): Videz = values().firstOrNull { it.name == niz } ?: TONSKA
        }
    }

    /**
     * Postavitev za vsako velikost.
     *
     * Od Androida 12 widget pošlje vse postavitve naenkrat in launcher sam
     * izbere tisto, ki se prilega -- tudi ko ga potnik raztegne, brez prebujanja
     * aplikacije. Prej izberemo sami iz velikosti, ki jo pove launcher:
     * pokončno je širina najmanjša in višina največja, ležeče obratno.
     * Velikost se spremeni z `onAppWidgetOptionsChanged`, ki widget preriše.
     *
     * [privzeta] velja, dokler launcher velikosti ne pove (0 × 0 ob dodajanju).
     */
    fun odzivno(
        c: Context, widgetId: Int, ponujene: List<Velikost>, privzeta: Velikost,
        zgradi: (Velikost) -> RemoteViews,
    ): RemoteViews {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return RemoteViews(ponujene.associate { SizeF(it.sirinaDp, it.visinaDp) to zgradi(it) })
        }
        val o = AppWidgetManager.getInstance(c).getAppWidgetOptions(widgetId)
        val minS = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH).toFloat()
        val maxS = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH).toFloat()
        val minV = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT).toFloat()
        val maxV = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT).toFloat()
        if (maxS <= 0f || maxV <= 0f) return zgradi(privzeta)
        val pokoncno = Velikost.za(minS, maxV, ponujene)
        val lezece = Velikost.za(maxS, minV, ponujene)
        return if (pokoncno == lezece) zgradi(pokoncno)
            else RemoteViews(zgradi(lezece), zgradi(pokoncno))
    }

    /**
     * Barve omrežja: vlak rjav, avtobus zelen, kot kartice na straneh.
     * Lestvica zamud ostane ista na obeh (`oznake.md`).
     */
    data class Ton(
        val podlaga: Int,
        val glavna: Int,
        val drugotna: Int,
        val gumb: Int,
        val zeton: Int,
        val krog: Int,
        val ikona: Int,
        val vrstica: Int,
    )

    fun ton(c: Context, vlak: Boolean): Ton =
        if (vlak) Ton(
            podlaga = R.drawable.widget_ozadje_kont,
            glavna = c.getColor(R.color.m_na_kont),
            drugotna = c.getColor(R.color.m_na_kont_2),
            gumb = R.drawable.gumb_krog_vlak,
            zeton = R.drawable.zeton_vlak,
            krog = R.drawable.krog_vlak,
            ikona = R.drawable.ikona_vlak,
            vrstica = R.drawable.widget_vrstica_vklop,
        ) else Ton(
            podlaga = R.drawable.widget_ozadje_bus,
            glavna = c.getColor(R.color.bus_na_kont),
            drugotna = c.getColor(R.color.bus_na_kont_2),
            gumb = R.drawable.gumb_krog_bus,
            zeton = R.drawable.zeton_bus,
            krog = R.drawable.krog_bus,
            ikona = R.drawable.ikona_bus,
            vrstica = R.drawable.widget_vrstica_vklop_bus,
        )

    /** Razred pride s strežnika (`stats.opis_zamude()`); barva je oblikovanje. */
    fun barvaZamude(razred: String?): Int = when (razred) {
        "tocno" -> R.color.d_ontime
        "1-5" -> R.color.d_small
        "5-15" -> R.color.d_mid
        "nad-15" -> R.color.d_big
        else -> R.color.ink_faint
    }

    /**
     * Ali je ozadje zaslona svetlo -- takrat widget brez podlage piše temno.
     *
     * Od Androida 12 to pove sistem (`HINT_SUPPORTS_DARK_TEXT`), od 8.1 se da
     * oceniti iz glavne barve ozadja. Prej in pri živem ozadju brez barv
     * velja temno: svetlo besedilo s senco je berljivo na več ozadjih kot temno.
     */
    fun svetloOzadje(c: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O_MR1) return false
        val barve = try {
            WallpaperManager.getInstance(c).getWallpaperColors(WallpaperManager.FLAG_SYSTEM)
        } catch (e: RuntimeException) {
            null
        } ?: return false
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return barve.colorHints and WallpaperColors.HINT_SUPPORTS_DARK_TEXT != 0
        }
        return barve.primaryColor.luminance() > 0.5f
    }

    /**
     * Postavitvi 1×1 in traku ter barvi besedila za [videz].
     *
     * Barve nastavi koda, zato morajo priti od tu: tonska postavitev je
     * svetla na temni podlagi, brez podlage pa je besedilo take barve, da se
     * bere na ozadju zaslona -- in koda, ki bi pisala `ink`, bi to povozila.
     */
    class Slog(val mini: Int, val trak: Int, val glavna: Int, val drugotna: Int, val brez: Boolean)

    fun slog(c: Context, videz: Videz): Slog = when {
        videz == Videz.TONSKA -> Slog(R.layout.w_mini, R.layout.w_trak,
            c.getColor(R.color.ink), c.getColor(R.color.ink_dim), false)
        svetloOzadje(c) -> Slog(R.layout.w_mini_brez_svetlo, R.layout.w_trak_brez_svetlo,
            c.getColor(R.color.brez_temno), c.getColor(R.color.brez_temno_2), true)
        else -> Slog(R.layout.w_mini_brez, R.layout.w_trak_brez,
            c.getColor(R.color.brez_svetlo), c.getColor(R.color.brez_svetlo_2), true)
    }

    /**
     * "● +4": zamuda brez podlage. Številka je v barvi besedila, razred nosi
     * pika -- oranžna na svetlem ozadju zaslona ne doseže kontrasta, beseda pa
     * minute pove tako ali tako (`oznake.md`: barva nikoli sama).
     */
    fun spikoZamude(napis: String, barva: Int): CharSequence =
        android.text.SpannableString("● $napis").apply {
            setSpan(android.text.style.ForegroundColorSpan(barva), 0, 1,
                android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        }

    /**
     * Namera, ki odpre [kam] v aplikaciji.
     *
     * [koda] loči namere med sabo: brez nje bi `FLAG_UPDATE_CURRENT` vse
     * združil v eno, ker se `extras` pri primerjavi ne upoštevajo.
     */
    fun odpri(c: Context, koda: Int, kam: String): PendingIntent =
        PendingIntent.getActivity(
            c, koda,
            Intent(c, GlavnaDejavnost::class.java)
                .setAction(GlavnaDejavnost.AKCIJA_ODPRI)
                .setData(Uri.parse("kajros://odpri/$koda"))
                .putExtra(GlavnaDejavnost.KAM, kam),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

    /**
     * Predloga za vrstice seznama: vrstica doda samo naslov (`KAM`).
     *
     * **Mora biti spremenljiva** (`FLAG_MUTABLE`): od Androida 12 sistem
     * vrstično namero vstavi v predlogo, nespremenljive pa ne sme spremeniti.
     */
    fun predlogaOdpri(c: Context, koda: Int): PendingIntent =
        PendingIntent.getActivity(
            c, koda,
            Intent(c, GlavnaDejavnost::class.java)
                .setAction(GlavnaDejavnost.AKCIJA_ODPRI),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE)

    /** Vrstica seznama, ki odpre [kam] (gre v [predlogaOdpri]). */
    fun vstavekOdpri(kam: String): Intent =
        Intent().putExtra(GlavnaDejavnost.KAM, kam)

    private val URA = DateTimeFormatter.ofPattern("HH:mm")
    private val DAN = DateTimeFormatter.ofPattern("EEE", Locale("sl"))
    private val DATUM = DateTimeFormatter.ofPattern("EEE d. M.", Locale("sl"))
    private const val TEDEN_MS = 7 * 24 * 3600 * 1000L

    /**
     * "danes", "jutri", "sob." ali, čez teden, "sob. 31. 10.".
     *
     * Po koledarju in ne `+ 24 h`: na dan premika ure je dan dolg 23 ali 25 ur.
     */
    fun dan(c: Context, ms: Long, zdajMs: Long): String {
        val cona = ZoneId.systemDefault()
        val kdaj = Instant.ofEpochMilli(ms).atZone(cona)
        val danes = Instant.ofEpochMilli(zdajMs).atZone(cona).toLocalDate()
        return when (kdaj.toLocalDate()) {
            danes -> c.getString(R.string.widget_danes)
            danes.plusDays(1) -> c.getString(R.string.widget_jutri)
            else -> (if (ms - zdajMs > TEDEN_MS) DATUM else DAN).format(kdaj)
        }
    }

    /**
     * Ura z dnevom, kadar ni danes: "16:57", "jutri 06:57", "sob. 06:57".
     * "Sob." za jutrišnji odhod bi potnika pustil računati, kateri dan je.
     */
    fun danUra(c: Context, ms: Long, zdajMs: Long): String {
        val cona = ZoneId.systemDefault()
        val ura = URA.format(Instant.ofEpochMilli(ms).atZone(cona))
        val danes = Instant.ofEpochMilli(zdajMs).atZone(cona).toLocalDate()
        return if (Instant.ofEpochMilli(ms).atZone(cona).toLocalDate() == danes) ura
            else dan(c, ms, zdajMs) + " " + ura
    }
}
