package app.kajros

import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Kdaj je potnik na vozilu, ki ga čaka -- presodi telefon sam.
 *
 * Deljenje ob vožnji (David, 6. 10. 2026) se ne začne z gumbom, ampak s
 * trenutkom, ko aplikacija ve, s katero vožnjo se boš peljal: ko potegneš
 * budilko ali začneš vodenje do postajališča. Od takrat do vkrcanja lega
 * **ne gre nikamor**; strežnik dobi prve točke šele, ko to pravilo reče
 * "vkrcan", in jih tam preveri še enkrat (na trasi, ob pravem času --
 * `deljenje._zacni`).
 *
 * Pravilo ima dva dela, ker en sam ni dovolj:
 *
 * 1. **Bil si na postaji.** Brez tega bi vožnja z avtom ob progi ob uri
 *    odhoda (zamudil si vlak, pelje te kdo drug) postala "potnik na vlaku".
 * 2. **Nato se pelješ**: dve zaporedni legi zunaj postaje s hitrostjo vozila,
 *    ne prej kot malo pred pričakovanim odhodom. Tako hitro nihče ne teče;
 *    ena sama lega je lahko skok GPS.
 *
 * Čist JVM, brez Androida: preizkusi v `VkrcanjeTest`.
 */
object Vkrcanje {

    /** Hitrost vozila, m/s (22 km/h). Tek je pod 4, kolo v mestu okoli 5. */
    const val VOZI_MS = 6.0

    /** Kako blizu postaje šteje za "na postaji", po omrežju (peron je dolg). */
    fun naPostajiM(vlak: Boolean): Double = if (vlak) 300.0 else 120.0

    /** Natančnost, pri kateri lega še šteje. Slabša je lahko kjerkoli. */
    const val NATANCNOST_M = 100.0

    /** Toliko pred pričakovanim odhodom se vožnja že lahko začne. */
    const val PRED_ODHODOM_MS = 3 * 60_000L

    /**
     * Toliko po pričakovanem odhodu nehamo čakati. Pričakovani odhod ima že
     * zadnjo zamudo; ta zraste, a redko za več kot pol ure med dvema
     * osvežitvama.
     */
    const val PO_ODHODU_MS = 30 * 60_000L

    data class Lega(val lat: Double, val lon: Double, val acc: Double?,
                    val tMs: Long, val v: Double?)

    enum class Izid { CAKA, VKRCAN, PREPOZNO }

    class Stanje(
        private val postajaLat: Double,
        private val postajaLon: Double,
        private val vlak: Boolean,
    ) {
        var bilNaPostaji = false
            private set
        private var hitrih = 0
        private var prejsnja: Lega? = null

        /** Zadnje legi, s katerima je pravilo reklo "vkrcan" -- prve točke deljenja. */
        val zadnje = ArrayDeque<Lega>()

        fun dodaj(l: Lega, odhodMs: Long): Izid {
            if (l.tMs > odhodMs + PO_ODHODU_MS) return Izid.PREPOZNO
            val prej = prejsnja
            prejsnja = l
            zadnje.addLast(l)
            while (zadnje.size > 3) zadnje.removeFirst()

            val d = razdaljaM(l.lat, l.lon, postajaLat, postajaLon)
            val negotovost = minOf(l.acc ?: 0.0, 200.0)
            if (d - negotovost <= naPostajiM(vlak)) {
                bilNaPostaji = true
                hitrih = 0
                return Izid.CAKA
            }
            val hitrost = l.v ?: prej?.let {
                val dt = (l.tMs - it.tMs) / 1000.0
                if (dt >= 2) razdaljaM(l.lat, l.lon, it.lat, it.lon) / dt else null
            }
            val natancna = l.acc == null || l.acc <= NATANCNOST_M
            hitrih = if (bilNaPostaji && natancna && hitrost != null && hitrost >= VOZI_MS &&
                l.tMs >= odhodMs - PRED_ODHODOM_MS) hitrih + 1 else 0
            return if (hitrih >= 2) Izid.VKRCAN else Izid.CAKA
        }
    }

    /** Razdalja po krogli, m. Na nekaj kilometrih je napaka pod metrom. */
    fun razdaljaM(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val r = 6_371_000.0
        val f1 = Math.toRadians(lat1)
        val f2 = Math.toRadians(lat2)
        val df = f2 - f1
        val dl = Math.toRadians(lon2 - lon1)
        val a = sin(df / 2) * sin(df / 2) + cos(f1) * cos(f2) * sin(dl / 2) * sin(dl / 2)
        return 2 * r * asin(sqrt(a))
    }
}
