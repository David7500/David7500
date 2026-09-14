package app.kajros

import java.time.ZoneId
import java.time.ZonedDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Prestavljanje ponavljajoce budilke. Zanka 14. 9. 2026: ustavljena budilka se
 * je prestavila na ISTI vlak, ker je bil ta se pred njo, in zazvonila znova.
 */
class BudilkaTest {

    private val CONA = ZoneId.of("Europe/Ljubljana")

    private fun ob(dan: Int, ura: Int, minuta: Int): Long =
        ZonedDateTime.of(2026, 9, dan, ura, minuta, 0, 0, CONA).toInstant().toEpochMilli()

    private fun budilka(vr: Long) = Budilka(
        id = "b1", trainNo = "LPV 2010", tripId = "t1", omrezje = "zeleznica",
        postaja = "Grosuplje", stopSeq = 3, dan = "2026-09-14", voznoredniMs = vr,
        minutPrej = 25, zbudi = true, dnevi = Ponovitev.VSI, odzvonjeno = true,
    )

    @Test
    fun `po zvonjenju pred odhodom gre na naslednji dan, ne na isti vlak`() {
        val vr = ob(14, 7, 35)
        val nova = budilka(vr).prestavljena(ob(14, 7, 30))
        assertEquals(ob(15, 7, 35), nova.voznoredniMs)
        assertEquals(false, nova.odzvonjeno)
    }

    @Test
    fun `po odhodu tudi na naslednji dan`() {
        val nova = budilka(ob(14, 7, 35)).prestavljena(ob(14, 9, 0))
        assertEquals(ob(15, 7, 35), nova.voznoredniMs)
    }

    @Test
    fun `stara budilka skoci na prvi dan po zdaj`() {
        // Telefon je bil tri dni ugasnjen: ne na 15., ampak na prvi prihodnji.
        val nova = budilka(ob(14, 7, 35)).prestavljena(ob(17, 12, 0))
        assertEquals(ob(18, 7, 35), nova.voznoredniMs)
        assertTrue(nova.tripId == null)
    }
}
