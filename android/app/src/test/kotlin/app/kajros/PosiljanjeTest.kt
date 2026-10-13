package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Ime datoteke pride s strani in gre v pot na disku, zato je čiščenje
 * varnostno pravilo -- in [Datoteke] ga ponovi ob branju.
 */
class PosiljanjeTest {

    @Test
    fun `besedilo in povezava sta dve vrstici, prazno odpade`() {
        assertEquals("Zamude vlakov\nhttps://kajros.app/vlak/a/b",
            Posiljanje.besedilo("Zamude vlakov", "https://kajros.app/vlak/a/b"))
        assertEquals("https://kajros.app", Posiljanje.besedilo(null, "https://kajros.app"))
        assertEquals("samo besedilo", Posiljanje.besedilo("  samo besedilo ", ""))
        assertNull(Posiljanje.besedilo(null, "  "))
    }

    @Test
    fun `ime ne more iz mape`() {
        assertEquals("_.._etc_passwd", Posiljanje.varnoIme("/../etc/passwd"))
        assertEquals("_etc_passwd", Posiljanje.varnoIme("../etc/passwd"))
        assertNull(Posiljanje.varnoIme(".."))
        assertNull(Posiljanje.varnoIme(""))
        assertNull(Posiljanje.varnoIme(null))
        assertFalse(Posiljanje.varnoIme("a/b")!!.contains('/'))
    }

    @Test
    fun `slovensko ime ostane berljivo`() {
        assertEquals("Zamude Ljubljana _ Kranj.png", Posiljanje.varnoIme("Zamude Ljubljana – Kranj.png"))
        assertEquals("šumniki čšž.jpg", Posiljanje.varnoIme("šumniki čšž.jpg"))
    }

    @Test
    fun `cisto ime je ze cisto`() {
        // `Datoteke` ob branju zahteva, da se ime s čiščenjem ne spremeni.
        for (ime in listOf("/../x", "a\u0000b.png", "...skrita", "  presledki  ", "x".repeat(300))) {
            val c = Posiljanje.varnoIme(ime) ?: continue
            assertEquals(c, Posiljanje.varnoIme(c))
        }
    }

    @Test
    fun `velikost iz base64 brez dekodiranja`() {
        assertEquals(3, Posiljanje.bajtov("YWJj"))       // "abc"
        assertEquals(2, Posiljanje.bajtov("YWI="))       // "ab"
        assertEquals(1, Posiljanje.bajtov("YQ=="))       // "a"
    }

    @Test
    fun `meja datotek in bajtov`() {
        assertFalse(Posiljanje.prevec(List(10) { 1000L }))
        assertTrue(Posiljanje.prevec(List(11) { 1L }))
        assertTrue(Posiljanje.prevec(listOf(Posiljanje.NAJVEC_BAJTOV + 1)))
    }

    @Test
    fun `vrsta namere za vec datotek`() {
        assertEquals("image/png", Posiljanje.skupnaVrsta(listOf("image/png", "image/png")))
        assertEquals("image/*", Posiljanje.skupnaVrsta(listOf("image/png", "image/jpeg")))
        assertEquals("*/*", Posiljanje.skupnaVrsta(listOf("image/png", "application/pdf")))
        assertEquals("application/octet-stream", Posiljanje.skupnaVrsta(listOf("")))
    }
}
