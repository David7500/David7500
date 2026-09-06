package app.kajros

import kotlin.math.max
import kotlin.math.min

/**
 * Kdaj naj budilka zazvoni. Cista aritmetika, brez Androida -- da jo je mogoce
 * preizkusiti brez naprave. Tu je vse, kar je v budilki mogoce narediti narobe.
 *
 * Pravilo je Davidovo in je preprosto:
 *
 *     zvoni = voznoredna_ura + zamuda - X
 *
 * **Rezerve ni.** Rezervo doloci uporabnik sam s tem, koliko izbere X --
 * v njem je ze. (Locena moznost "+3 min" pride s prenovo vmesnika.)
 * Meritev pravi, da bi 5 minut rezerve prihranilo tretjino zamujenih vlakov
 * in dve tretjini avtobusov (`docs/MERITVE.md`), a to je odlocitev potnika,
 * ne aplikacije.
 *
 * Zamuda se preverja do konca in vse pogosteje, blizje ko je ura. Ce povezave
 * ni, budilka **zazvoni preventivno** malo prej in to pove.
 */
object Ura {

    /**
     * Zadnje okno pred zvonjenjem. Ce v njem povezave ni, zazvonimo takoj:
     * potnik izgubi do treh minut spanca, ne pa vlaka.
     */
    const val PREVENTIVA_MS = 210_000L          // 3,5 min

    /**
     * Najkrajsa doba, ko podatek se velja. Prava meja je **dva zgresena
     * preverjanja**, ne stalno stevilo sekund.
     *
     * Ta razlika je stala eno budilko: meja je bila trdih 30 s, korak
     * preverjanja dalec od ure pa je 5 minut -- podatek je bil zato med dvema
     * preverjanjema vedno videti kot izpad, ura zvonjenja je padla na vozni
     * red in budilka je zazvonila 25 minut prezgodaj.
     */
    const val IZPAD_MS = 30_000L

    /** Koliko pred prvim moznim zvonjenjem se zacne preverjati. */
    const val ZALET_MS = 10 * 60 * 1000L

    /** Iz cesa je nastala ura zvonjenja. To gre v obvestilo, ne ostane v kodi. */
    enum class Vir {
        /** Zamuda je sveza in upostevana. */
        ZAMUDA,
        /** Zamude ni (ali ji ne verjamemo) -- velja vozni red. */
        VOZNI_RED,
        /** Zvoni prej, ker povezave ni. */
        PREVENTIVA,
    }

    data class Izid(
        /** Trenutek zvonjenja, epoch ms. */
        val zvoniOb: Long,
        val vir: Vir,
        /** Zamuda, ki jo je racun res upsteval, v sekundah. */
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
     * @param voznoredniMs voznoredni odhod s postanka, epoch ms
     * @param minutPrej    koliko prej hoce potnik zvonjenje (njegov X)
     * @param zamudaS      zadnja znana zamuda ali null
     * @param zamudaObMs   kdaj smo jo dobili (0 = nikoli)
     * @param zdajMs       zdaj
     * @param vlak         `network == "zeleznica"`
     */
    fun izracunaj(
        voznoredniMs: Long,
        minutPrej: Int,
        zamudaS: Int?,
        zamudaObMs: Long,
        zdajMs: Long,
        vlak: Boolean,
    ): Izid {
        val poVoznemRedu = voznoredniMs - minutPrej * 60_000L
        // `zamudaS == null` je tu zato, da `odhodMs` spodaj ne more pasti na
        // `!!`. Brez tega bi pokvarjen zapis v shrambi (zamuda null, cas pa
        // nastavljen) podrl budilko ravno ob prozenju.
        val brezZveze = zamudaS == null || zamudaObMs <= 0L ||
            zdajMs - zamudaObMs > veljavnost(voznoredniMs - minutPrej * 60_000L - zdajMs)

        // Vlak pred voznim redom ne odpelje -- izmerjeno na 10 775 primerih,
        // niti enkrat. Negativna vrednost iz feeda je zato smet in ne razlog
        // za zgodnejse zvonjenje. Avtobusi prezgodaj GREJO (25,3 %), zato pri
        // njih te omejitve ni in je ne sme biti.
        val upostevana = when {
            zamudaS == null -> 0
            vlak -> max(0, zamudaS)
            else -> zamudaS
        }
        val izZamude = voznoredniMs + upostevana * 1000L - minutPrej * 60_000L

        // Brez povezave nikoli POZNEJE od voznega reda. Sicer bi dvajset minut
        // stara "+15" drzala uro, tudi ko vlak vmes nadoknadi -- in preventiva
        // spodaj tega ne ujame, ker premakne le za tri minute.
        var zvoni = if (brezZveze) min(izZamude, poVoznemRedu) else izZamude

        var vir = if (brezZveze) Vir.VOZNI_RED else Vir.ZAMUDA
        if (brezZveze && zdajMs >= zvoni - PREVENTIVA_MS) {
            // Zadnje okno in povezave ni: ne cakamo na cudez.
            zvoni = min(zvoni, zdajMs)
            vir = Vir.PREVENTIVA
        }

        return Izid(
            zvoniOb = zvoni,
            vir = vir,
            upostevanaS = if (brezZveze) 0 else upostevana,
            surovaS = zamudaS,
            odhodMs = if (brezZveze) voznoredniMs else voznoredniMs + zamudaS!! * 1000L,
        )
    }

    /** Razmik med preverjanji glede na to, koliko casa je se do zvonjenja. */
    fun korak(doZvonjenjaMs: Long): Long = when {
        doZvonjenjaMs > 15 * 60_000L -> 5 * 60_000L
        doZvonjenjaMs > 5 * 60_000L -> 60_000L
        else -> 30_000L
    }

    /**
     * Koliko casa podatek se velja: dve preverjanji plus zamik.
     *
     * Dalec od ure to pomeni deset minut, tik pred njo pa slabo minuto in pol
     * -- natanko takrat, ko je pomembno.
     */
    fun veljavnost(doZvonjenjaMs: Long): Long =
        maxOf(IZPAD_MS, 2 * korak(doZvonjenjaMs) + 15_000L)

    /**
     * Kdaj naslednjic preveriti zamudo, ali null, ce je cas za zvonjenje.
     *
     * Korak se krajsa, blizje ko je ura: dvajset minut prej se zamuda med
     * dvema minutama tako rekoc ne spremeni, tri minute prej pa je vsaka
     * sprememba pomembna. Prebujanje telefona ni zastonj.
     */
    fun naslednjePreverjanje(zdajMs: Long, zvoniObMs: Long): Long? {
        val doZvonjenja = zvoniObMs - zdajMs
        if (doZvonjenja <= 0) return null
        val cez = zdajMs + korak(doZvonjenja)
        // Zadnje preverjanje naj pade PRED zvonjenjem, ne vanj ali za njim.
        return if (cez >= zvoniObMs) null else cez
    }
}
