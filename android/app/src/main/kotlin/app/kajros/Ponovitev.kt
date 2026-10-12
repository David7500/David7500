package app.kajros

import java.time.DayOfWeek
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * Budilka, ki se ponavlja: kdaj je naslednja in kako se temu rece.
 *
 * Cista aritmetika, brez Androida -- iz istega razloga kot [Ura]. Tu je vse,
 * kar je mogoce narediti narobe pri prestavljanju na naslednji dan, in to je
 * predvsem eno: **ura mora ostati ura po zidni uri, ne po epoch ms.** Prestop
 * na poletni cas premakne dan za 23 ali 25 ur; kdor bi pristel 86 400 000,
 * bi imel budilko uro narobe dvakrat na leto.
 */
object Ponovitev {

    /** Ponedeljek je bit 0, nedelja bit 6 -- isto kot `DayOfWeek.value - 1`. */
    const val VSI = 0b1111111
    const val DELAVNIKI = 0b0011111
    const val VIKEND = 0b1100000

    /** Kratice za prikaz. Podatek, ne besedilo vmesnika -- zato tu in ne v `strings.xml`. */
    val KRATICE = listOf("pon", "tor", "sre", "čet", "pet", "sob", "ned")

    private val DATUM = DateTimeFormatter.ISO_LOCAL_DATE

    fun jePonavljajoca(dnevi: Int): Boolean = (dnevi and VSI) != 0

    fun velja(dnevi: Int, dan: DayOfWeek): Boolean =
        (dnevi shr (dan.value - 1)) and 1 == 1

    /**
     * Naslednji odhod po [poMs], ob **isti uri po zidni uri** kot [voznoredniMs].
     *
     * Vrne [voznoredniMs] nespremenjen, kadar budilka ni ponavljajoca -- klicatelj
     * tako ne rabi posebnega primera.
     */
    fun naslednji(
        voznoredniMs: Long,
        dnevi: Int,
        poMs: Long,
        cona: ZoneId = ZoneId.systemDefault(),
    ): Long {
        if (!jePonavljajoca(dnevi)) return voznoredniMs
        val ura = Instant.ofEpochMilli(voznoredniMs).atZone(cona).toLocalTime()
        val zacetek = Instant.ofEpochMilli(poMs).atZone(cona).toLocalDate()
        // Sedem dni je dovolj za vsak vzorec; osmi je varovalka, kadar je
        // danasnja ura ze mimo in isti dan cez teden edini v naboru.
        for (i in 0..7L) {
            val d: LocalDate = zacetek.plusDays(i)
            if (!velja(dnevi, d.dayOfWeek)) continue
            // `atZone` sam premakne uro, ki je ob prehodu na poletni cas ni.
            val ms = d.atTime(ura).atZone(cona).toInstant().toEpochMilli()
            if (ms > poMs) return ms
        }
        return voznoredniMs
    }

    /**
     * Prva ponovitev nove budilke: na dan iz nabora **in** z zvonjenjem, ki še
     * ni mimo. [prejMs] je, koliko pred voznim redom budilka zvoni (minute in
     * rezerva).
     *
     * Prvi pogoj: stran pošlje vožnjo, ki jo je človek gledal, in ta ni nujno
     * na dan iz nabora (12. 9. 2026: tor + sre, vožnja v ponedeljek). Meja
     * `max(voznja - 1 s, zdaj)` pusti vožnjo pri miru, kadar je njen dan v
     * naboru, in premakne tisto, ki je danes že mimo.
     *
     * Drugi: ponavljajoča budilka, nastavljena 15 minut pred vlakom z
     * X = 25, je zazvonila takoj (izmerjeno 12. 10. 2026 na RG 18: nastavljena
     * 19:14, zazvonila 19:14:46). Kdor jo nastavi na peronu, jo rabi naslednjič,
     * ne zdaj. Enkratna ostane, kot je: zvoni takoj in stran to pove.
     */
    fun prva(
        voznoredniMs: Long,
        dnevi: Int,
        zdajMs: Long,
        prejMs: Long,
        cona: ZoneId = ZoneId.systemDefault(),
    ): Long {
        if (!jePonavljajoca(dnevi)) return voznoredniMs
        val vr = naslednji(voznoredniMs, dnevi, maxOf(voznoredniMs - 1000L, zdajMs), cona)
        return if (vr - prejMs > zdajMs) vr else naslednji(vr, dnevi, vr, cona)
    }

    /**
     * Ali shranjeni odhod pade na dan iz nabora.
     *
     * Enkratna budilka je vedno "v naboru" -- nabora nima in je ni treba
     * premikati. Za ponavljajoco je to edini nacin, da opazimo budilko, ki je
     * nastala, preden je `Most.nastavi()` prvo ponovitev poravnal.
     */
    fun jeVNaboru(voznoredniMs: Long, dnevi: Int, cona: ZoneId = ZoneId.systemDefault()): Boolean =
        !jePonavljajoca(dnevi) ||
            velja(dnevi, Instant.ofEpochMilli(voznoredniMs).atZone(cona).dayOfWeek)

    /** Prometni dan odhoda, kot ga pricakuje `/api/departures`. */
    fun dan(voznoredniMs: Long, cona: ZoneId = ZoneId.systemDefault()): String =
        Instant.ofEpochMilli(voznoredniMs).atZone(cona).toLocalDate().format(DATUM)

    /**
     * Kako se naboru dni rece po slovensko.
     *
     * Nastete dneve locimo z vejico in ne z zamikom v postavitvi: vrstica v
     * seznamu budilk je ena in mora povedati vzorec na en pogled.
     */
    fun ime(dnevi: Int): String = when (dnevi and VSI) {
        0 -> "enkratna"
        VSI -> "vsak dan"
        DELAVNIKI -> "vsak delavnik"
        VIKEND -> "vikend"
        else -> (0..6).filter { (dnevi shr it) and 1 == 1 }
            .joinToString(", ") { KRATICE[it] }
    }
}
