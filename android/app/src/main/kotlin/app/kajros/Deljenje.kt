package app.kajros

import java.util.Locale

/**
 * Deljenje lege: vrsta tock in telo zahteve za `POST /api/deli`.
 *
 * Cisti JVM brez Androida, da je preizkusljivo brez naprave -- storitev
 * ([DeljenjeStoritev]) samo nabira lego in posilja, kar ji pripravi to.
 * Pravila so ista kot v `deli.js`, ker streznik (`deljenje.py`) enako
 * obravnava oba odjemalca.
 */
object Deljenje {

    /** Najmanjsi razmik tock; streznik gostejsih ne sprejme (`RAZMIK_S`). */
    const val RAZMIK_MS = 3_000L
    /**
     * Kako pogosto se nabrane tocke poslje. Streznik jih sprejme 60 naenkrat.
     * Toliko kot mali zemljevid v oknu voznje vprasa (`deljenje.POSILJANJE_S`);
     * do 1.3 je bilo 10 s.
     */
    const val POSLJI_MS = 5_000L
    /**
     * Najvec tock v vrsti brez povezave. V predoru ali med postajami brez
     * signala se nabirajo; ko zveza pride, gredo vse -- a ne vec kot streznik
     * sprejme v eni zahtevi (`TOCK_NA_ZAHTEVO`).
     */
    const val NAJVEC_V_VRSTI = 60
    /** Deljenje, daljse od tega, se konca samo -- isto kot na strezniku. */
    const val NAJDALJE_MS = 6 * 3600 * 1000L

    data class Tocka(val lat: Double, val lon: Double, val acc: Float?,
                     val tMs: Long, val v: Float?)

    /** Tocke, ki cakajo na posiljanje. Ni varna za vec niti; klice jo ena. */
    class Vrsta {
        private val tocke = ArrayDeque<Tocka>()
        private var zadnjaMs = 0L

        val velikost: Int get() = tocke.size

        /** Doda tocko, ce je dovolj za prejsnjo. Vrne, ali jo je dodala. */
        fun dodaj(t: Tocka): Boolean {
            if (t.tMs - zadnjaMs < RAZMIK_MS) return false
            zadnjaMs = t.tMs
            tocke.addLast(t)
            while (tocke.size > NAJVEC_V_VRSTI) tocke.removeFirst()
            return true
        }

        /** Vzame vse, kar caka. */
        fun vzemi(): List<Tocka> = tocke.toList().also { tocke.clear() }

        /**
         * Posiljanje ni uspelo (ni zveze): tocke gredo nazaj na zacetek.
         * Novejse, ki so prisle vmes, ostanejo; odpadejo najstarejse.
         */
        fun vrni(neposlane: List<Tocka>) {
            for (t in neposlane.asReversed()) tocke.addFirst(t)
            while (tocke.size > NAJVEC_V_VRSTI) tocke.removeFirst()
        }
    }

    /** JSON niz z ubeznimi znaki -- rocno, ker org.json v testih JVM ni. */
    fun niz(s: String?): String {
        if (s == null) return "null"
        val b = StringBuilder("\"")
        for (c in s) {
            when {
                c == '"' -> b.append("\\\"")
                c == '\\' -> b.append("\\\\")
                c < ' ' -> b.append(String.format(Locale.ROOT, "\\u%04x", c.code))
                else -> b.append(c)
            }
        }
        return b.append('"').toString()
    }

    private fun stevilo(x: Number?): String =
        if (x == null || (x is Double && !x.isFinite()) || (x is Float && !x.isFinite())) "null"
        else x.toString()

    /** Telo zahteve. `deljenje` je null ob prvem posiljanju. */
    fun telo(tripId: String, dan: String, deljenje: String?, tocke: List<Tocka>,
             konec: Boolean): String {
        val t = tocke.joinToString(",") {
            "{\"lat\":${stevilo(it.lat)},\"lon\":${stevilo(it.lon)}," +
                "\"acc\":${stevilo(it.acc)},\"t\":${it.tMs},\"v\":${stevilo(it.v)}}"
        }
        return "{\"trip_id\":${niz(tripId)},\"service_date\":${niz(dan)}," +
            "\"deljenje\":${niz(deljenje)},\"tocke\":[$t],\"konec\":$konec}"
    }

    /**
     * Ali odgovor strežnika pomeni, da je deljenja konec, ne glede na to, kaj
     * pravi telo. 4xx razen 429 je zavrnitev (voznja ne vozi vec, deljenja ne
     * pozna) in ponavljanje ne pomaga; 429 in 5xx sta prehodna.
     */
    fun jeZavrnitev(koda: Int): Boolean = koda in 400..499 && koda != 429
}
