package app.kajros

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.hypot

class PeronTest {

    @Test
    fun `poteg cez prag ustavi, krajsi se vrne`() {
        assertTrue(Peron.ustavi(0.6f, 0f))
        assertTrue(Peron.ustavi(1f, -2f))
        assertFalse(Peron.ustavi(0.59f, 0f))
        assertFalse(Peron.ustavi(0.2f, 0.1f))
    }

    @Test
    fun `sunek ustavi po tretjini poti, ne prej`() {
        // 18 % širine v 0,1 s: na 412 dp je to 0,74 dp/ms in 0,36 poti.
        assertTrue(Peron.ustavi(0.36f, 0.74f))
        assertFalse(Peron.ustavi(0.25f, 2f))
        assertFalse(Peron.ustavi(0.36f, 0.5f))
        // Sunek nazaj ni sunek proti cilju.
        assertFalse(Peron.ustavi(0.4f, -1.5f))
    }

    @Test
    fun `tretjina sirine zadosca`() {
        // Prej 85 % od 0,68 širine = 58 %, zdaj 60 % od 0,5 = 30 %.
        assertEquals(0.30f, Peron.PRAG * Peron.POT_DELEZ, 1e-6f)
    }

    @Test
    fun `cetrtine poti`() {
        assertEquals(0, Peron.cetrtina(0.24f))
        assertEquals(1, Peron.cetrtina(0.25f))
        assertEquals(4, Peron.cetrtina(1f))
    }

    @Test
    fun `vlak je dolg kot prototip, celo na x = 0`() {
        val p = Peron(vlak = true)
        assertEquals(53.9f, p.dolzina, 1e-4f)
        val m = p.vozilo.meje
        // Sprednje luči segajo 5 cm pred konico, zadnje (zrcaljene) prav toliko za konec.
        assertEquals(0.05f, m[3], 1e-4f)
        assertEquals(-53.95f, m[0], 1e-4f)
        assertEquals(5.3f, m[4], 1e-4f)          // odjemnik toka
        assertEquals(16, p.kolesa.size)
        assertEquals(8, p.vrata.size)
        assertEquals(2, p.siji.count { it.zaromet })
        assertEquals(4, p.siji.size)
        // Zadnje luči so na zadnjem koncu in rdeče.
        assertTrue(p.siji.filter { !it.zaromet }.all { it.x < -53f && it.barva == 0xff5040 })
    }

    @Test
    fun `avtobus ima tri osi in dvoje vrat`() {
        val p = Peron(vlak = false)
        assertEquals(12f, p.dolzina, 0f)
        assertEquals(6, p.kolesa.size)
        assertEquals(2, p.vrata.size)
        assertEquals(-12.03f, p.vozilo.meje[0], 1e-4f)
        assertEquals(Peron.CILJ_X - 70f, p.zacetek, 0f)
    }

    @Test
    fun `vozilo pripelje do cilja`() {
        val p = Peron(vlak = true)
        assertEquals(Peron.CILJ_X - 95f, p.xVozila(0f), 0f)
        assertEquals(Peron.CILJ_X, p.xVozila(1f), 0f)
    }

    @Test
    fun `tabla in ura gledata proti kameri`() {
        for (poz in listOf(Peron.TABLA, Peron.URA)) {
            val smer = FloatArray(3)
            Afina.okoliY(Peron.protiKameri(poz)).smer(0f, 0f, 1f, smer)
            val dx = Peron.KAMERA[0] - poz[0]
            val dz = Peron.KAMERA[2] - poz[2]
            val d = hypot(dx, dz)
            assertEquals(dx / d, smer[0], 1e-5f)
            assertEquals(dz / d, smer[2], 1e-5f)
        }
    }

    @Test
    fun `zrcaljena kabina ima normale obrnjene nazaj`() {
        // Čelna ploskev profila (konica, normala +x) je pri zadnji kabini -x.
        val p = Peron(vlak = true)
        val d = p.vozilo.podatki()
        var spredaj = 0
        var zadaj = 0
        for (i in 0 until p.vozilo.oglisc) {
            val o = i * Mreza.NA_OGLISCE
            if (d[o + 3] > 0.99f && d[o] > -0.1f) spredaj++
            if (d[o + 3] < -0.99f && d[o] < -53.8f) zadaj++
        }
        assertTrue(spredaj > 0)
        assertEquals(spredaj, zadaj)
    }
}
