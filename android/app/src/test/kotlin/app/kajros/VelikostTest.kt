package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * Kateri razred dobi widget dane velikosti.
 *
 * Velikosti so iz Googlove preglednice mrež za telefon (pokončno stolpci 57,
 * 130, 203, 276, 349 dp, vrstice 102, 220, 337 dp; ležeče vrstica 51, dve 117).
 * Na Androidu 12+ izbira launcher, na starejših [Velikost.za] -- obe poti
 * morata dati isto, sicer je widget na starem telefonu drugačen kot na novem.
 */
class VelikostTest {

    private val vse = Velikost.values().toList()

    @Test
    fun `pokoncne mreze dobijo svoj razred`() {
        assertEquals(Velikost.MINI, Velikost.za(57f, 102f, vse))
        assertEquals(Velikost.TRAK, Velikost.za(130f, 102f, vse))
        assertEquals(Velikost.TRAK, Velikost.za(203f, 102f, vse))
        assertEquals(Velikost.TRAK_SIROK, Velikost.za(276f, 102f, vse))
        assertEquals(Velikost.KVADRAT, Velikost.za(130f, 220f, vse))
        assertEquals(Velikost.KVADRAT, Velikost.za(203f, 220f, vse))
        assertEquals(Velikost.SREDNJI, Velikost.za(276f, 220f, vse))
        assertEquals(Velikost.STOLPEC, Velikost.za(203f, 337f, vse))
        assertEquals(Velikost.VELIK, Velikost.za(276f, 337f, vse))
        assertEquals(Velikost.VELIK, Velikost.za(349f, 455f, vse))
    }

    @Test
    fun `lezece vrstice so nizke in dobijo pas ali dve vrstici`() {
        // 1×1 ležeče je 127 × 51: tri vrstice besedila se ne izidejo.
        assertEquals(Velikost.PAS, Velikost.za(127f, 51f, vse))
        assertEquals(Velikost.PAS, Velikost.za(554f, 51f, vse))
        // Dve vrstici ležeče (117 dp) sta že dve vrstici, ne trak.
        assertEquals(Velikost.SREDNJI, Velikost.za(554f, 117f, vse))
    }

    @Test
    fun `widget dobi samo razred, ki ga zna narisati`() {
        val brezSeznama = vse - Velikost.VELIK - Velikost.STOLPEC
        assertEquals(Velikost.SREDNJI, Velikost.za(276f, 455f, brezSeznama))
        assertEquals(Velikost.KVADRAT, Velikost.za(130f, 455f, brezSeznama))
    }

    @Test
    fun `premajhen widget dobi najmanjsi razred, ne nicesar`() {
        // Launcher sme poročati 0 × 0, preden widget sploh postavi.
        assertEquals(Velikost.MINI, Velikost.za(0f, 0f, vse))
        assertEquals(Velikost.TRAK, Velikost.za(0f, 0f, listOf(Velikost.TRAK, Velikost.SREDNJI)))
    }
}
