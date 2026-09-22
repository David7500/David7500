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

    /** Po zvonjenju: kako pogosto osvezimo zamudo, da widget odsteva prav. */
    const val SLEDENJE_KORAK_MS = 2 * 60_000L

    /** Toliko po odhodu se sledenje konca in ponavljajoca gre na naslednji dan. */
    const val SLEDENJE_ZA_MS = 90_000L

    /**
     * Po zvonjenju zamuda velja **dve zgreseni osvezitvi** sledenja, isto
     * pravilo kot pred njim.
     *
     * Pred 22. 9. 2026 se je tudi po zvonjenju merilo po koraku do ure
     * zvonjenja. Ta je bila ze mimo, korak je bil zato 30 s in zamuda je
     * veljala 75 s -- sledenje pa jo osvezi na dve minuti. Vecino casa je bila
     * torej "zastarela", odhod je padel na vozni red in widget je nehal
     * odstevati toliko pred prihodom, kolikor je vlak zamujal.
     */
    const val SLEDENJE_VELJA_MS = 2 * SLEDENJE_KORAK_MS + 15_000L

    /** Iz cesa je nastala ura zvonjenja. To gre v obvestilo, ne ostane v kodi. */
    enum class Vir {
        /** Zamuda je sveza in upostevana. */
        ZAMUDA,
        /**
         * Streznik je odgovoril, a o zamudi te voznje nima podatka -- velja
         * vozni red, preventive pa NI. Tipicno vlak na zacetni postaji, ki se
         * se ni premaknil. 14. 9. 2026 je bil ta primer zamenjan z izpadom
         * povezave in budilka je zazvonila takoj ob prvem preverjanju.
         */
        NI_PODATKA,
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
     * @param rezervaS     kar je potnik sam obkljukal ("se 3 minute"), v sekundah
     * @param stikObMs     zadnji odgovor streznika, tudi brez zamude (0 = nikoli)
     * @param sledenje     budilka je ze zazvonila in zdaj samo sledi odhodu
     */
    fun izracunaj(
        voznoredniMs: Long,
        minutPrej: Int,
        zamudaS: Int?,
        zamudaObMs: Long,
        zdajMs: Long,
        vlak: Boolean,
        rezervaS: Int = 0,
        stikObMs: Long = 0L,
        sledenje: Boolean = false,
    ): Izid {
        val poVoznemRedu = voznoredniMs - minutPrej * 60_000L - rezervaS * 1000L

        // Vlak pred voznim redom ne odpelje -- izmerjeno na 10 775 primerih,
        // niti enkrat. Negativna vrednost iz feeda je zato smet in ne razlog
        // za zgodnejse zvonjenje. Avtobusi prezgodaj GREJO (25,3 %), zato pri
        // njih te omejitve ni in je ne sme biti.
        val upostevana = when {
            zamudaS == null -> 0
            vlak -> max(0, zamudaS)
            else -> zamudaS
        } - rezervaS
        val izZamude = voznoredniMs + upostevana * 1000L - minutPrej * 60_000L

        // Veljavnost se meri od ure, PO KATERI SE NACRTUJE, torej od zvonjenja
        // z zamudo -- ne od voznega reda. Razlika je stala budilko 14. 9. 2026:
        // vlak ob 7:35 z dvajset minutami zamude, preverjanje vsakih 5 minut
        // (do zvonjenja jih je bilo se 20), meja pa izracunana od voznega reda,
        // kjer je bilo "zvonjenje" ze cez minuto in je veljalo 75 s. Pet minut
        // star podatek je bil zato izpad, ura je padla na vozni red in budilka
        // je sporocila "zamude ni bilo mogoce preveriti" 22 minut prezgodaj.
        //
        // Po zvonjenju ura zvonjenja ni vec merilo -- takrat je ritem sledenja.
        fun sveze(obMs: Long) =
            obMs > 0L && zdajMs - obMs <= (if (sledenje) SLEDENJE_VELJA_MS
                                           else veljavnost(izZamude - zdajMs, zdajMs - obMs))
        // `zamudaS != null` je tu tudi zato, da `odhodMs` spodaj ne more pasti
        // na `!!`. Brez tega bi pokvarjen zapis v shrambi (zamuda null, cas pa
        // nastavljen) podrl budilko ravno ob prozenju.
        val zamudaVelja = zamudaS != null && sveze(zamudaObMs)
        // Povezava in zamuda nista isto: streznik, ki odgovori "o tej voznji ne
        // vem nic", je dosegljiv, in preventiva je samo za primer, ko ni.
        val zvezaVelja = zamudaVelja || sveze(stikObMs)

        // Brez sveze zamude nikoli POZNEJE od voznega reda. Sicer bi dvajset
        // minut stara "+15" drzala uro, tudi ko vlak vmes nadoknadi -- in
        // preventiva spodaj tega ne ujame, ker premakne le za tri minute.
        var zvoni = if (zamudaVelja) izZamude else min(izZamude, poVoznemRedu)

        var vir = when {
            zamudaVelja -> Vir.ZAMUDA
            zvezaVelja -> Vir.NI_PODATKA
            else -> Vir.VOZNI_RED
        }
        if (!zvezaVelja && zdajMs >= zvoni - PREVENTIVA_MS) {
            // Zadnje okno in povezave ni: ne cakamo na cudez.
            zvoni = min(zvoni, zdajMs)
            vir = Vir.PREVENTIVA
        }

        return Izid(
            zvoniOb = zvoni,
            vir = vir,
            upostevanaS = if (zamudaVelja) upostevana else 0,
            surovaS = zamudaS,
            odhodMs = if (zamudaVelja) voznoredniMs + zamudaS!! * 1000L else voznoredniMs,
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
     * Prvo preverjanje je tisto, ki je bilo NACRTOVANO, ko je podatek prisel
     * -- takrat je bilo do zvonjenja `doZvonjenjaMs + starostMs` in korak je bil
     * dolg temu primerno. Drugo je zgreseno preverjanje po zdajsnjem koraku.
     * Brez tega bi prehod s 5-minutnega na minutni korak (15 minut pred
     * zvonjenjem) vsakic razglasil izpad, ceprav ni bilo zgreseno nic.
     *
     * Dalec od ure to pomeni deset minut, tik pred njo pa slabo minuto in pol
     * -- natanko takrat, ko je pomembno.
     */
    fun veljavnost(doZvonjenjaMs: Long, starostMs: Long = 0L): Long =
        maxOf(IZPAD_MS, korak(doZvonjenjaMs + starostMs) + korak(doZvonjenjaMs) + 15_000L)

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
