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

    // ---------- naslov voznje ----------
    //
    // Isti naslov odpira gumb v seznamu budilk in dotik widgeta. Prvic je bil
    // ze narobe (`+` namesto `%20` v poti) in tega na napravi ni bilo videti:
    // stran je pisala "vlak s to stevilko ne obstaja".

    @Test
    fun `presledek v stevilki gre v pot odstotkovno, ne kot plus`() {
        val n = budilka(ob(14, 7, 35)).naslovVoznje("https://kajros.app")
        assertTrue(n.startsWith("https://kajros.app/app/train/LPV%202010?"), n)
        assertTrue("+" !in n, n)
    }

    @Test
    fun `avtobus gre na svojo pot`() {
        val b = budilka(ob(14, 7, 35)).copy(omrezje = "avtobus", trainNo = "25")
        assertTrue(b.naslovVoznje("https://kajros.app").startsWith(
            "https://kajros.app/app/bus/25?"))
    }

    @Test
    fun `brez trip id parametra ni`() {
        val b = budilka(ob(14, 7, 35)).copy(tripId = null)
        assertTrue("trip=" !in b.naslovVoznje("https://kajros.app"))
    }

    @Test
    fun `postaja in dan sta v poizvedbi`() {
        val b = budilka(ob(14, 7, 35)).copy(postaja = "Bavarski dvor")
        val n = b.naslovVoznje("https://kajros.app")
        assertTrue("postaja=Bavarski%20dvor" in n, n)
        assertTrue("date=2026-09-14" in n, n)
        assertTrue("trip=t1" in n, n)
    }
}

/**
 * Po zvonjenju widget odsteva do odhoda. 22. 9. 2026 prijavljeno: odstevanje
 * je izginilo "recimo pet minut pred prihodom".
 */
class SledenjeTest {

    private val CONA = ZoneId.of("Europe/Ljubljana")

    private fun ob(ura: Int, minuta: Int, sekunda: Int = 0): Long =
        ZonedDateTime.of(2026, 9, 22, ura, minuta, sekunda, 0, CONA).toInstant().toEpochMilli()

    /** RG 318 ob 7:31, X = 20, vlak +5 min; zazvonilo je ob 7:16. */
    private fun odzvonjena(zamudaS: Int?, preverjenoOb: Long) = Budilka(
        id = "b1", trainNo = "RG 318", tripId = "t1", omrezje = "zeleznica",
        postaja = "Ljubljana Polje", stopSeq = 3, dan = "2026-09-22",
        voznoredniMs = ob(7, 31), minutPrej = 20, zbudi = true,
        zamudaS = zamudaS, zamudaObMs = if (zamudaS == null) 0 else preverjenoOb,
        stikObMs = preverjenoOb, zvoniObMs = ob(7, 16), odzvonjeno = true,
    )

    @Test
    fun `zamuda velja med dvema osvezitvama sledenja`() {
        // Sledenje osvezi zamudo na dve minuti. Pred popravkom je veljala 75 s,
        // ker je bil korak racunan od ure zvonjenja, ki je ze mimo.
        val b = odzvonjena(300, ob(7, 29))
        assertEquals(ob(7, 36), b.izracun(ob(7, 30, 50)).odhodMs)
    }

    @Test
    fun `sledenje ne neha ob voznem redu, ce vlak zamuja`() {
        // Zadnja osvezitev ob 7:31 je zgresena (Doze, ni signala): ob 7:33 je
        // vlak po zadnjem podatku se tri minute dalec.
        val b = odzvonjena(300, ob(7, 29))
        assertTrue(b.sledenjeOb(ob(7, 33)) != null)
        assertEquals(ob(7, 36) + Ura.SLEDENJE_ZA_MS, b.konecSledenjaMs())
    }

    @Test
    fun `brez osvezitve odsteva do voznega reda, konca pa ne prehiti`() {
        // Pet minut brez odgovora: stevec se vrne na vozni red (pred njim vlak
        // ne odpelje), widget pa ostane do zadnjega znanega odhoda.
        val b = odzvonjena(300, ob(7, 25))
        assertEquals(ob(7, 31), b.izracun(ob(7, 30)).odhodMs)
        assertTrue(b.sledenjeOb(ob(7, 34)) != null)
        assertEquals(null, b.sledenjeOb(ob(7, 37, 31)))
    }

    @Test
    fun `ena osvezitev pade na sam odhod`() {
        // Cez niclo Chronometer steje z minusom; ob odhodu mora widget
        // preklopiti na "zdaj", in to zna samo ob izrisu.
        val b = odzvonjena(300, ob(7, 35))
        assertEquals(ob(7, 36), b.sledenjeOb(ob(7, 35, 10)))
        // Po odhodu je naslednja budnica konec sledenja, ne nov korak cez njega.
        assertEquals(ob(7, 37, 30), b.sledenjeOb(ob(7, 36, 10)))
    }

    @Test
    fun `prezgoden avtobus ne podaljsa sledenja cez vozni red`() {
        val b = odzvonjena(-120, ob(7, 25)).copy(omrezje = "avtobus")
        assertEquals(ob(7, 31) + Ura.SLEDENJE_ZA_MS, b.konecSledenjaMs())
    }

    @Test
    fun `pred zvonjenjem ostane staro merilo veljavnosti`() {
        // Pet minut daleč od zvonjenja je korak 60 s; podatek, star tri
        // minute, tam ne velja -- sprememba je samo za cas po zvonjenju.
        val b = odzvonjena(300, ob(7, 10)).copy(odzvonjeno = false, zvoniObMs = 0)
        assertEquals(ob(7, 31), b.izracun(ob(7, 13)).odhodMs)
    }
}
