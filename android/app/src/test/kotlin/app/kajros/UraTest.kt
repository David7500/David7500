package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Budilka je edini del te aplikacije, ki lahko koga pusti na postaji. Zato ima
 * aritmetika teste, in ti tecejo brez naprave.
 */
class UraTest {

    private val ODHOD = 1_757_180_400_000L   // poljuben trenutek, epoch ms
    private fun min(m: Int) = m * 60_000L

    @Test
    fun `brez zamude zvoni X minut pred voznim redom`() {
        val i = Ura.izracunaj(ODHOD, minutPrej = 25, zamudaS = 0, starostS = 0, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
        // Zamuda 0 in rezerva 5 dasta max(0, -5) = 0 pri vlaku: rezerva se ne
        // porabi, ker vlak pred voznim redom ne odpelje.
        assertEquals(0, i.upostevanaS)
    }

    @Test
    fun `zamuda premakne zvonjenje naprej, a le za del nad rezervo`() {
        val i = Ura.izracunaj(ODHOD, 25, zamudaS = 12 * 60, starostS = 0, vlak = true)
        // +12 min zamude, 5 min rezerve => zvoni, kot bi vlak zamujal 7.
        assertEquals(ODHOD + min(7) - min(25), i.zvoniOb)
        assertEquals(Ura.Vir.ZAMUDA, i.vir)
    }

    @Test
    fun `majhna zamuda vlaka zvonjenja ne premakne`() {
        // +3 min je pod rezervo. Vlak prezgodaj ne odpelje, zato ni razloga
        // zvoniti pred voznim redom -- to je popravek, ki je prihranil dve
        // minuti odvecnega cakanja na vsako budilko.
        val i = Ura.izracunaj(ODHOD, 25, zamudaS = 3 * 60, starostS = 0, vlak = true)
        assertEquals(ODHOD - min(25), i.zvoniOb)
    }

    @Test
    fun `prezgoden avtobus zvoni prej, in to takoj`() {
        // Avtobusi prezgodaj GREJO -- v 25,3 % primerov. Zato pri njih omejitve
        // na vozni red ni: -4 min zamude in 5 min rezerve dasta -9.
        val i = Ura.izracunaj(ODHOD, 15, zamudaS = -4 * 60, starostS = 0, vlak = false)
        assertEquals(ODHOD - min(9) - min(15), i.zvoniOb)
        assertEquals(-9 * 60, i.upostevanaS)
    }

    @Test
    fun `avtobus brez zamude vseeno dobi tri minute rezerve`() {
        val i = Ura.izracunaj(ODHOD, 15, zamudaS = 0, starostS = 0, vlak = false)
        assertEquals(ODHOD - min(5) - min(15), i.zvoniOb)
    }

    @Test
    fun `brez povezave zvoni po voznem redu -- vlak natanko, avtobus s tremi minutami`() {
        val vlak = Ura.izracunaj(ODHOD, 25, zamudaS = null, starostS = 0, vlak = true)
        assertEquals(ODHOD - min(25), vlak.zvoniOb)
        assertEquals(Ura.Vir.VOZNI_RED, vlak.vir)

        val bus = Ura.izracunaj(ODHOD, 15, zamudaS = null, starostS = 0, vlak = false)
        assertEquals(ODHOD - min(3) - min(15), bus.zvoniOb)
        assertEquals(Ura.Vir.VOZNI_RED, bus.vir)
    }

    @Test
    fun `zastarela zamuda sme zvonjenje premakniti naprej, nazaj pa ne`() {
        val star = Ura.SVEZE_S + 60
        // Stara zamuda +20 min: ce ji verjamemo in vlak vmes nadoknadi, budilka
        // zvoni 15 minut prepozno. Zato jo zavrzemo in ostane vozni red.
        val pozno = Ura.izracunaj(ODHOD, 25, zamudaS = 20 * 60, starostS = star, vlak = true)
        assertEquals(ODHOD - min(25), pozno.zvoniOb)
        assertEquals(Ura.Vir.VOZNI_RED, pozno.vir)

        // Stara zamuda -8 min pri avtobusu pa je opozorilo in ga upostevamo:
        // premik naprej potnika ne more pustiti na postaji.
        val zgodaj = Ura.izracunaj(ODHOD, 15, zamudaS = -8 * 60, starostS = star, vlak = false)
        assertEquals(ODHOD - min(13) - min(15), zgodaj.zvoniOb)
    }

    @Test
    fun `sveza meja je natanko dvajset minut`() {
        assertEquals(Ura.Vir.ZAMUDA,
            Ura.izracunaj(ODHOD, 25, 20 * 60, Ura.SVEZE_S, true).vir)
        assertEquals(Ura.Vir.VOZNI_RED,
            Ura.izracunaj(ODHOD, 25, 20 * 60, Ura.SVEZE_S + 1, true).vir)
    }

    @Test
    fun `X vecji od casa do odhoda pomeni zvonjenje v preteklosti`() {
        // Ne popravljamo ga tu: klicatelj mora vedeti, da je zamujeno, in
        // zazvoniti takoj. Tiho prestavljanje naprej bi budilko utisalo.
        val i = Ura.izracunaj(ODHOD, 600, zamudaS = 0, starostS = 0, vlak = true)
        assertTrue(i.zvoniOb < ODHOD)
        assertEquals(ODHOD - min(600), i.zvoniOb)
    }

    @Test
    fun `preverjanje se ponavlja do zvonjenja in ne cez`() {
        val zdaj = ODHOD - min(40)
        val zvoni = ODHOD - min(25)
        assertEquals(zdaj + Ura.KORAK_MS, Ura.naslednjePreverjanje(zdaj, zvoni))
        // Natanko en korak pred zvonjenjem naslednjega preverjanja NI: padlo bi
        // v isti trenutek kot zvonjenje in ne bi nicesar spremenilo.
        assertNull(Ura.naslednjePreverjanje(zvoni - Ura.KORAK_MS, zvoni))
        // Tri minute pred zvonjenjem naslednjega koraka ni -- naslednje, kar
        // se zgodi, je zvonjenje samo.
        assertNull(Ura.naslednjePreverjanje(zvoni - min(3), zvoni))
        assertNull(Ura.naslednjePreverjanje(zvoni, zvoni))
        assertNull(Ura.naslednjePreverjanje(zvoni + min(1), zvoni))
    }

    @Test
    fun `obvestilo ne sme trditi ure, ki ji racun ni verjel`() {
        // Ta napaka je bila na zaslonu: naslov "ob 22:34" (iz zamude) in pod
        // njim "po voznem redu -- zamude nisem mogel preveriti".
        val sveza = Ura.izracunaj(ODHOD, 25, 24 * 60, 0, true)
        assertEquals(ODHOD + min(24), sveza.odhodMs)

        val stara = Ura.izracunaj(ODHOD, 25, 24 * 60, Ura.SVEZE_S + 1, true)
        assertEquals(Ura.Vir.VOZNI_RED, stara.vir)
        assertEquals(ODHOD, stara.odhodMs)

        val brez = Ura.izracunaj(ODHOD, 25, null, 0, true)
        assertEquals(ODHOD, brez.odhodMs)
    }

    @Test
    fun `rezerva je tocno pet minut in pri avtobusu brez zveze tri`() {
        // Ce kdo te stevilki spremeni, naj ve, da sta izmerjeni -- glej
        // docs/MERITVE.md, razdelek "Rezerva budilke".
        assertEquals(300, Ura.REZERVA_S)
        assertEquals(180, Ura.REZERVA_BREZ_ZVEZE_AVTOBUS_S)
    }
}
