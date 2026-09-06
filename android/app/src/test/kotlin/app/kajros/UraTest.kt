package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Budilka je edini del te aplikacije, ki lahko koga pusti na postaji. Zato ima
 * aritmetika teste, in ti tecejo brez naprave.
 *
 * Pravilo: `zvoni = voznoredna + zamuda - X`. **Rezerve ni** -- doloci jo
 * potnik s tem, koliko izbere X.
 */
class UraTest {

    private val ODHOD = 1_757_180_400_000L   // poljuben trenutek, epoch ms
    private fun min(m: Int) = m * 60_000L
    /** Dalec od zvonjenja, da preventiva ne posega vmes. */
    private val DALEC = ODHOD - min(90)

    @Test
    fun `zamuda premakne zvonjenje za celo zamudo, brez odbitka`() {
        val i = Ura.izracunaj(ODHOD, 25, 12 * 60, DALEC, DALEC, vlak = true)
        assertEquals(ODHOD + min(12) - min(25), i.zvoniOb)
        assertEquals(Ura.Vir.ZAMUDA, i.vir)
        assertEquals(12 * 60, i.upostevanaS)
    }

    @Test
    fun `brez zamude zvoni X minut pred voznim redom`() {
        val i = Ura.izracunaj(ODHOD, 25, 0, DALEC, DALEC, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
    }

    @Test
    fun `vlak ne zvoni pred voznim redom, tudi ce feed trdi drugace`() {
        // Vlak v 10 775 meritvah ni odpeljal prezgodaj niti enkrat; negativna
        // vrednost iz feeda je smet in ne razlog za zgodnejse zvonjenje.
        val i = Ura.izracunaj(ODHOD, 25, -4 * 60, DALEC, DALEC, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
        assertEquals(0, i.upostevanaS)
    }

    @Test
    fun `prezgoden avtobus zvoni prej`() {
        // Avtobusi prezgodaj GREJO -- v 25,3 % primerov -- zato pri njih
        // omejitve na vozni red ni in je ne sme biti.
        val i = Ura.izracunaj(ODHOD, 15, -4 * 60, DALEC, DALEC, vlak = false)
        assertEquals(ODHOD - min(4) - min(15), i.zvoniOb)
    }

    @Test
    fun `brez povezave velja vozni red`() {
        val i = Ura.izracunaj(ODHOD, 25, null, 0, DALEC, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
        assertEquals(Ura.Vir.VOZNI_RED, i.vir)
        assertEquals(ODHOD, i.odhodMs)
    }

    @Test
    fun `brez povezave nikoli pozneje od voznega reda`() {
        // Dvajset minut stara "+15" bi drzala uro, tudi ko vlak vmes nadoknadi.
        // Preventiva tega ne ujame, ker premakne le za tri minute.
        val star = DALEC - min(30)
        val i = Ura.izracunaj(ODHOD, 25, 15 * 60, star, DALEC, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
        assertEquals(Ura.Vir.VOZNI_RED, i.vir)
    }

    @Test
    fun `brez povezave sme stara zamuda zvonjenje premakniti NAPREJ`() {
        // Premik naprej potnika ne more pustiti na postaji, zato ga obdrzimo:
        // stara vest, da je avtobus osem minut prezgoden, je opozorilo.
        val star = DALEC - min(30)
        val i = Ura.izracunaj(ODHOD, 15, -8 * 60, star, DALEC, vlak = false)
        assertEquals(ODHOD - min(8) - min(15), i.zvoniOb)
    }

    @Test
    fun `v zadnjem oknu brez povezave zvoni takoj in to pove`() {
        val zvoni = ODHOD - min(25)
        val zdaj = zvoni - Ura.PREVENTIVA_MS + 1000
        val i = Ura.izracunaj(ODHOD, 25, null, 0, zdaj, vlak = true)
        assertEquals(zdaj, i.zvoniOb)
        assertEquals(Ura.Vir.PREVENTIVA, i.vir)
        // Potnik izgubi do 3,5 minute spanca, ne pa vlaka.
        assertTrue(zvoni - i.zvoniOb <= Ura.PREVENTIVA_MS)
    }

    @Test
    fun `sveza povezava preventive ne sprozi`() {
        val zvoni = ODHOD + min(12) - min(25)
        val zdaj = zvoni - min(1)
        val i = Ura.izracunaj(ODHOD, 25, 12 * 60, zdaj - 10_000, zdaj, vlak = true)
        assertEquals(Ura.Vir.ZAMUDA, i.vir)
        assertEquals(zvoni, i.zvoniOb)
    }

    @Test
    fun `podatek velja dve preverjanji, ne trdih trideset sekund`() {
        // Ta razlika je stala eno budilko: s trdo mejo 30 s je bil podatek med
        // dvema preverjanjema (5 min narazen) vedno videti kot izpad, ura je
        // padla na vozni red in budilka je zazvonila 25 minut prezgodaj.
        val stara = Ura.izracunaj(ODHOD, 25, 600, DALEC - min(4), DALEC, true)
        assertEquals(Ura.Vir.ZAMUDA, stara.vir)

        val prestara = Ura.izracunaj(ODHOD, 25, 600, DALEC - min(11), DALEC, true)
        assertEquals(Ura.Vir.VOZNI_RED, prestara.vir)
    }

    @Test
    fun `tik pred zvonjenjem je meja stroga`() {
        // Tam se preverja vsakih 30 s, zato dve minuti tisine pomenita izpad.
        val zvoni = ODHOD - min(25)
        val zdaj = zvoni - min(4)
        assertEquals(Ura.Vir.ZAMUDA,
            Ura.izracunaj(ODHOD, 25, 0, zdaj - 60_000L, zdaj, true).vir)
        assertEquals(Ura.Vir.VOZNI_RED,
            Ura.izracunaj(ODHOD, 25, 0, zdaj - min(2), zdaj, true).vir)
    }

    @Test
    fun `obvestilo ne sme trditi ure, ki ji racun ni verjel`() {
        // Ta napaka je bila na zaslonu: naslov "ob 22:34" (iz zamude) in pod
        // njim "po voznem redu -- zamude nisem mogel preveriti".
        val sveza = Ura.izracunaj(ODHOD, 25, 24 * 60, DALEC, DALEC, true)
        assertEquals(ODHOD + min(24), sveza.odhodMs)

        val stara = Ura.izracunaj(ODHOD, 25, 24 * 60, DALEC - min(30), DALEC, true)
        assertEquals(Ura.Vir.VOZNI_RED, stara.vir)
        assertEquals(ODHOD, stara.odhodMs)
    }

    @Test
    fun `zamuda null s postavljenim casom ne podre budilke`() {
        // Pokvarjen zapis v shrambi ne sme pasti na `!!` ravno ob proženju.
        val i = Ura.izracunaj(ODHOD, 25, null, DALEC, DALEC, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
        assertEquals(ODHOD, i.odhodMs)
        assertEquals(Ura.Vir.VOZNI_RED, i.vir)
    }

    @Test
    fun `X vecji od casa do odhoda pomeni zvonjenje v preteklosti`() {
        // Ne popravljamo ga tu: klicatelj mora vedeti, da je zamujeno, in
        // zazvoniti takoj. Tiho prestavljanje naprej bi budilko utisalo.
        val i = Ura.izracunaj(ODHOD, 600, 0, DALEC, DALEC, vlak = true)
        assertEquals(ODHOD - min(600), i.zvoniOb)
    }

    @Test
    fun `korak preverjanja se krajsa, blizje ko je ura`() {
        val zvoni = ODHOD
        assertEquals(zvoni - min(30) + min(5),
            Ura.naslednjePreverjanje(zvoni - min(30), zvoni))
        assertEquals(zvoni - min(10) + min(1),
            Ura.naslednjePreverjanje(zvoni - min(10), zvoni))
        assertEquals(zvoni - min(3) + 30_000L,
            Ura.naslednjePreverjanje(zvoni - min(3), zvoni))
    }

    @Test
    fun `preverjanje se ne nacrtuje cez zvonjenje`() {
        val zvoni = ODHOD
        assertNull(Ura.naslednjePreverjanje(zvoni - 20_000L, zvoni))
        assertNull(Ura.naslednjePreverjanje(zvoni, zvoni))
        assertNull(Ura.naslednjePreverjanje(zvoni + min(1), zvoni))
    }

    @Test
    fun `okno preventive je tri minute in pol, meja izpada pol minute`() {
        // Ce kdo ti stevilki spremeni, naj ve, kaj pomenita: prva je, koliko
        // spanca potnik najvec izgubi, druga pa, kdaj podatek neha veljati.
        assertEquals(210_000L, Ura.PREVENTIVA_MS)
        assertEquals(30_000L, Ura.IZPAD_MS)
        // Veljavnost se veže na korak preverjanja, ne obratno.
        assertEquals(2 * 5 * 60_000L + 15_000L, Ura.veljavnost(20 * 60_000L))
        assertEquals(2 * 30_000L + 15_000L, Ura.veljavnost(60_000L))
    }
}
