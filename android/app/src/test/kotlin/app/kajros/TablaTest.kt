package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * Besede in starost na widgetu z odhodno tablo.
 *
 * Racuna tu skoraj ni in prav to je bistvo: minuto in razred izracuna streznik
 * (`stats.opis_zamude()`), ker bi se drugace pravilo pisalo dvakrat.
 * `kotlin.math.round` zaokrozi pol na sodo in bi se pri 30 s s stranjo razsel.
 * Preizkuseno je torej samo, kar je res nase -- beseda.
 */
class TablaTest {

    private fun odhod(min: Int?, prezgodaj: Boolean = false) = Tabla.Odhod(
        ura = "06:53", kam = "Koper", trainNo = "LPV 2010", tripId = "t1",
        zamudaMin = min, razred = null, prezgodaj = prezgodaj,
    )

    @Test
    fun `brez podatka je pomisljaj, ne nicla`() {
        // "Tocno" za voznjo, o kateri feed se ni rekel nicesar, je trditev,
        // ki je nimamo -- in prav ta je potnika ze poslala s perona.
        assertEquals("—", Tabla.zamudaNapis(odhod(null)))
    }

    @Test
    fun `zamuda ima plus, prezgodnja ima besedo`() {
        // Minus pred stevilko je uganka, beseda ni. Isto pravilo kot
        // `common.delayText` na strani.
        assertEquals("+4", Tabla.zamudaNapis(odhod(4)))
        assertEquals("3 prej", Tabla.zamudaNapis(odhod(-3, prezgodaj = true)))
    }

    @Test
    fun `nicla je tocno`() {
        assertEquals("točno", Tabla.zamudaNapis(odhod(0)))
    }

    @Test
    fun `starost se meri v minutah in nikoli ni negativna`() {
        val zdaj = 1_700_000_000_000L
        assertEquals(0, Tabla.starostMin(zdaj, zdaj))
        assertEquals(15, Tabla.starostMin(zdaj - 15 * 60_000L, zdaj))
        // Ura telefona se sme premakniti nazaj; to ni podatek iz prihodnosti.
        assertEquals(0, Tabla.starostMin(zdaj + 60_000L, zdaj))
    }

    @Test
    fun `en izpusceni korak ni star podatek, dva sta`() {
        // Ritem je 15 minut. En izpusceni cikel je Doze in ne okvara.
        val zdaj = 1_700_000_000_000L
        assertFalse(Tabla.jeStaro(zdaj - 16 * 60_000L, zdaj))
        assertTrue(Tabla.jeStaro(zdaj - 31 * 60_000L, zdaj))
    }

    @Test
    fun `brez ure je podatek vedno star`() {
        // `obMs = 0` pomeni, da odgovora se ni bilo. To ni "svez".
        assertTrue(Tabla.jeStaro(0, 1_700_000_000_000L))
    }
}
