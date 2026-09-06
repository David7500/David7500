package app.kajros

/**
 * Kdaj naj budilka zazvoni. Cista aritmetika, brez Androida -- da jo je mogoce
 * preizkusiti brez naprave. Tu je vse, kar je v budilki mogoce narediti narobe.
 *
 * Davidovo pravilo: *"uporabnik vnese, koliko casa (x minut) preden pride vlak
 * naj zazvoni (upostevajo se zamude); ce pa ni povezave, zazvoni x minut preden
 * je napovedan vozni red"*, in *"uporabnik ne sme zamuditi, raje kej rezerve,
 * ce ni zihr"*.
 *
 * Koliko je "kej rezerve", je izmerjeno na 63 843 razreseih vrsticah sence
 * (`docs/MERITVE.md`), ne ocenjeno.
 */
object Ura {

    /**
     * Rezerva, kadar zamudo poznamo.
     *
     * Brez nje bi budilka zvonila prepozno v 32 % primerov pri vlakih in 64 %
     * pri avtobusih -- prikaz namrec zamudo pogosto precenju in vozilo pride
     * prej, kot je obljubljeno. Strosek (`P(zamudi) x razmik + odvecno
     * cakanje`) je pri obeh omrezjih najnizji pri **5 minutah** in med 4 in 6
     * raven, torej izbira ni krhka.
     */
    const val REZERVA_S = 5 * 60

    /**
     * Rezerva, kadar zamude NE poznamo -- samo za avtobuse.
     *
     * Vlak v 10 775 meritvah ni odpeljal prezgodaj niti enkrat, zato je pri
     * njem vsaka rezerva cisto cakanje. Avtobus odpelje prezgodaj v 25,3 %
     * primerov; pri treh minutah pade strosek s 14,92 na 9,50.
     */
    const val REZERVA_BREZ_ZVEZE_AVTOBUS_S = 3 * 60

    /**
     * Kdaj je zadnja znana zamuda prestara, da bi ji se verjeli.
     *
     * Ista meja kot `FRESH_S` v `train.js`. Koliko natanko napaka raste s
     * starostjo podatka, **ni izmerjeno** -- senca snema pri stalnem horizontu.
     * Zato zastarel podatek ni obravnavan kot slabsa napoved, ampak kot
     * odsotnost povezave: konservativno, kot je bilo naroceno.
     */
    const val SVEZE_S = 20 * 60

    /** Iz cesa je nastala ura zvonjenja. To gre v obvestilo, ne ostane v kodi. */
    enum class Vir { ZAMUDA, VOZNI_RED }

    data class Izid(
        /** Trenutek zvonjenja, epoch ms. */
        val zvoniOb: Long,
        val vir: Vir,
        /** Zamuda, ki jo je racun res upsteval (z rezervo), v sekundah. */
        val upostevanaS: Int,
        /** Zamuda, kot jo je javil streznik, ali null. */
        val surovaS: Int?,
        /**
         * Kdaj po **tej isti odlocitvi** vozilo odpelje. Za obvestilo.
         *
         * Loceno polje zato, ker se je prikaz ze zlagal: naslov je trdil
         * 22:34 (iz zamude), razlog pod njim pa "po voznem redu, zamude nisem
         * mogel preveriti". Ce racun zamudi ni verjel, je ne sme pokazati.
         */
        val odhodMs: Long,
    )

    /**
     * Zamuda, zmanjsana za rezervo.
     *
     * Pri vlaku je rezultat omejen na 0: **vlak pred voznim redom ne odpelje**,
     * zato zgodnejse zvonjenje ne pridobi nicesar. Izmerjeno je, da ta omejitev
     * pri vlakih delez zamud ne spremeni (4,5 %), odvecno cakanje pa skrajsa za
     * dve minuti. Pri avtobusih iste omejitve NI in je ne sme biti -- ti
     * prezgodaj gredo, in z njo bi delez zamud zrasel s 6,4 na 28,9 %.
     */
    fun zRezervo(zamudaS: Int, vlak: Boolean): Int {
        val z = zamudaS - REZERVA_S
        return if (vlak) maxOf(0, z) else z
    }

    /** Kar upostevamo, kadar zamude nimamo. */
    fun brezZveze(vlak: Boolean): Int =
        if (vlak) 0 else -REZERVA_BREZ_ZVEZE_AVTOBUS_S

    /**
     * @param voznoredniMs voznoredni odhod s postanka, epoch ms
     * @param minutPrej    koliko prej hoce potnik zvonjenje (njegov X)
     * @param zamudaS      zadnja znana zamuda ali null
     * @param starostS     koliko sekund je stara ta zamuda
     * @param vlak         `network == "zeleznica"`
     */
    fun izracunaj(
        voznoredniMs: Long,
        minutPrej: Int,
        zamudaS: Int?,
        starostS: Int,
        vlak: Boolean,
    ): Izid {
        val sveza = zamudaS != null && starostS <= SVEZE_S
        val upostevana = if (sveza) {
            zRezervo(zamudaS!!, vlak)
        } else if (zamudaS != null) {
            // Stara zamuda ni nic vredna, skodi pa lahko: ce je trdila +10 in
            // vozilo vmes nadoknadi, bi budilka zvonila deset minut prepozno.
            // Vzamemo zgodnejso od obeh moznosti -- podatek sme zvonjenje
            // premakniti naprej, nazaj pa ne.
            minOf(brezZveze(vlak), zRezervo(zamudaS, vlak))
        } else {
            brezZveze(vlak)
        }
        return Izid(
            zvoniOb = voznoredniMs + upostevana * 1000L - minutPrej * 60_000L,
            vir = if (sveza) Vir.ZAMUDA else Vir.VOZNI_RED,
            upostevanaS = upostevana,
            surovaS = zamudaS,
            odhodMs = if (sveza) voznoredniMs + zamudaS!! * 1000L else voznoredniMs,
        )
    }

    /**
     * Kdaj naslednjic preveriti zamudo, ali null, ce je cas za zvonjenje.
     *
     * Zamuda se spreminja, zato preverjamo do konca in ne enkrat. Prvo
     * preverjanje je pet minut pred najzgodnejsim moznim zvonjenjem, da je
     * odgovor tu, preden bi bilo treba zvoniti.
     */
    fun naslednjePreverjanje(zdajMs: Long, zvoniObMs: Long): Long? {
        if (zvoniObMs <= zdajMs) return null
        val cez = zdajMs + KORAK_MS
        // Zadnje preverjanje naj pade tik pred zvonjenjem, ne za njim.
        return if (cez >= zvoniObMs) null else cez
    }

    /** Razmik med preverjanji. */
    const val KORAK_MS = 5 * 60 * 1000L
}
