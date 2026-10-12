package app.kajros

import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId
import java.time.ZonedDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * Ponavljajoca budilka ima dva nacina, kako pustiti cloveka na postaji:
 * napacen dan in napacno uro. Oboje se preizkusi brez naprave.
 */
class PonovitevTest {

    private val CONA = ZoneId.of("Europe/Ljubljana")

    private fun ob(leto: Int, mesec: Int, dan: Int, ura: Int, minuta: Int): Long =
        ZonedDateTime.of(leto, mesec, dan, ura, minuta, 0, 0, CONA).toInstant().toEpochMilli()

    private fun beri(ms: Long) = Instant.ofEpochMilli(ms).atZone(CONA)

    @Test
    fun `prestop na zimski cas ohrani uro, ne stevila ur`() {
        // 25. 10. 2026 je nedelja s prehodom na zimski cas: dan ima 25 ur.
        // Kdor bi pristel 86 400 000 ms, bi imel budilko uro prezgodaj -- in
        // dvakrat na leto je to razlika med vlakom in naslednjim vlakom.
        val sobota = ob(2026, 10, 24, 6, 49)
        val naslednji = Ponovitev.naslednji(sobota, Ponovitev.VSI, sobota + 1000, CONA)

        assertEquals(LocalDate.of(2026, 10, 25), beri(naslednji).toLocalDate())
        assertEquals(LocalTime.of(6, 49), beri(naslednji).toLocalTime())
        assertEquals(25 * 3_600_000L, naslednji - sobota)
    }

    @Test
    fun `prestop na poletni cas prav tako`() {
        // 29. 3. 2026 dan traja 23 ur.
        val sobota = ob(2026, 3, 28, 6, 49)
        val naslednji = Ponovitev.naslednji(sobota, Ponovitev.VSI, sobota + 1000, CONA)
        assertEquals(LocalTime.of(6, 49), beri(naslednji).toLocalTime())
        assertEquals(23 * 3_600_000L, naslednji - sobota)
    }

    @Test
    fun `delavniki preskocijo vikend`() {
        val petek = ob(2026, 9, 11, 6, 49)      // petek
        val naslednji = Ponovitev.naslednji(petek, Ponovitev.DELAVNIKI, petek + 1000, CONA)
        assertEquals(LocalDate.of(2026, 9, 14), beri(naslednji).toLocalDate())  // ponedeljek
    }

    @Test
    fun `en sam dan v tednu pomeni cez teden`() {
        val torek = ob(2026, 9, 8, 15, 10)
        val samoTorki = 1 shl 1
        val naslednji = Ponovitev.naslednji(torek, samoTorki, torek + 1000, CONA)
        assertEquals(LocalDate.of(2026, 9, 15), beri(naslednji).toLocalDate())
    }

    @Test
    fun `danes se steje, dokler ura ni mimo`() {
        // Prestavljanje klicemo tudi ob zagonu aplikacije; ce je ura se pred
        // nami, se budilka NE sme prestaviti na jutri.
        val danes = ob(2026, 9, 9, 18, 30)
        val zdaj = ob(2026, 9, 9, 8, 0)
        assertEquals(danes, Ponovitev.naslednji(danes, Ponovitev.VSI, zdaj, CONA))
    }

    @Test
    fun `enkratna budilka se ne prestavi`() {
        val kdaj = ob(2026, 9, 9, 6, 49)
        assertEquals(kdaj, Ponovitev.naslednji(kdaj, 0, kdaj + 1_000_000, CONA))
        assertFalse(Ponovitev.jePonavljajoca(0))
        assertTrue(Ponovitev.jePonavljajoca(Ponovitev.DELAVNIKI))
    }

    @Test
    fun `imena naborov`() {
        assertEquals("vsak dan", Ponovitev.ime(Ponovitev.VSI))
        assertEquals("vsak delavnik", Ponovitev.ime(Ponovitev.DELAVNIKI))
        assertEquals("vikend", Ponovitev.ime(Ponovitev.VIKEND))
        assertEquals("enkratna", Ponovitev.ime(0))
        assertEquals("pon, sre, pet", Ponovitev.ime(0b0010101))
    }

    @Test
    fun `prva ponovitev se poravna na izbrani dan`() {
        // Tako je nastalo na telefonu: izbrana tor + sre, stran je kazala
        // ponedeljek 14. 9. 2026. Budilka ne sme prvic zazvoniti v ponedeljek.
        val ponedeljek = ob(2026, 9, 14, 6, 49)
        val torSre = (1 shl 1) or (1 shl 2)
        val prva = Ponovitev.naslednji(ponedeljek, torSre, ponedeljek - 1000, CONA)

        assertEquals(LocalDate.of(2026, 9, 15), beri(prva).toLocalDate())
        assertEquals(LocalTime.of(6, 49), beri(prva).toLocalTime())
        assertTrue(Ponovitev.velja(torSre, beri(prva).dayOfWeek))
    }

    @Test
    fun `voznja, ki je danes ze mimo, skoci na naslednji dan iz nabora`() {
        val danesZjutraj = ob(2026, 9, 14, 6, 49)     // ponedeljek
        val popoldne = ob(2026, 9, 14, 13, 45)
        val samoPonedeljki = 1
        val prva = Ponovitev.naslednji(
            danesZjutraj, samoPonedeljki, maxOf(danesZjutraj - 1000, popoldne), CONA)

        assertEquals(LocalDate.of(2026, 9, 21), beri(prva).toLocalDate())
        assertEquals(LocalTime.of(6, 49), beri(prva).toLocalTime())
    }

    @Test
    fun `opazi budilko, ki je shranjena na dnevu zunaj nabora`() {
        val ponedeljek = ob(2026, 9, 14, 6, 49)
        val torSre = (1 shl 1) or (1 shl 2)
        assertFalse(Ponovitev.jeVNaboru(ponedeljek, torSre, CONA))
        assertTrue(Ponovitev.jeVNaboru(ob(2026, 9, 15, 6, 49), torSre, CONA))
        // Enkratna nabora nima in je ni treba premikati.
        assertTrue(Ponovitev.jeVNaboru(ponedeljek, 0, CONA))
    }

    @Test
    fun `ponavljajoca, ki bi zazvonila v preteklost, zacne naslednjic`() {
        // RG 18 ob 19:29 v ponedeljek, nastavljena ob 19:14 z X = 25 + 3:
        // zvonjenje 19:01 je mimo, zato prvic v torek, ne takoj.
        val vr = ob(2026, 10, 12, 19, 29)
        val prvic = Ponovitev.prva(vr, Ponovitev.DELAVNIKI, ob(2026, 10, 12, 19, 14),
            28 * 60_000L, CONA)
        assertEquals(ob(2026, 10, 13, 19, 29), prvic)
    }

    @Test
    fun `ponavljajoca z zvonjenjem pred sabo ostane danes`() {
        val vr = ob(2026, 10, 12, 19, 29)
        val prvic = Ponovitev.prva(vr, Ponovitev.DELAVNIKI, ob(2026, 10, 12, 19, 0),
            10 * 60_000L, CONA)
        assertEquals(vr, prvic)
    }

    @Test
    fun `petkova zamujena gre na ponedeljek, enkratna se ne premakne`() {
        val petek = ob(2026, 10, 16, 7, 31)
        val zdaj = ob(2026, 10, 16, 7, 20)
        assertEquals(ob(2026, 10, 19, 7, 31),
            Ponovitev.prva(petek, Ponovitev.DELAVNIKI, zdaj, 25 * 60_000L, CONA))
        assertEquals(petek, Ponovitev.prva(petek, 0, zdaj, 25 * 60_000L, CONA))
    }
}
