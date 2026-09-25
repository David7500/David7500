package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class DeljenjeTest {

    private fun t(ms: Long) = Deljenje.Tocka(46.0, 14.5, 10f, ms, 12f)

    @Test
    fun gostejse_od_razmika_odpadejo() {
        val v = Deljenje.Vrsta()
        assertTrue(v.dodaj(t(10_000)))
        assertFalse(v.dodaj(t(11_000)))
        assertTrue(v.dodaj(t(13_000)))
        assertEquals(2, v.velikost)
    }

    @Test
    fun vrsta_ne_zraste_cez_mejo() {
        val v = Deljenje.Vrsta()
        for (i in 1..100) v.dodaj(t(i * 5_000L))
        assertEquals(Deljenje.NAJVEC_V_VRSTI, v.velikost)
        // Odpadejo najstarejse: prva ostala je 41. tocka.
        assertEquals(41 * 5_000L, v.vzemi().first().tMs)
    }

    @Test
    fun neposlane_gredo_nazaj_pred_novejse() {
        val v = Deljenje.Vrsta()
        v.dodaj(t(5_000)); v.dodaj(t(10_000))
        val poslane = v.vzemi()
        v.dodaj(t(15_000))
        v.vrni(poslane)
        assertEquals(listOf(5_000L, 10_000L, 15_000L), v.vzemi().map { it.tMs })
    }

    @Test
    fun telo_je_json_ki_ga_streznik_pricakuje() {
        val telo = Deljenje.telo("462|1", "2026-09-25", null,
            listOf(Deljenje.Tocka(46.1, 14.2, null, 1_000L, Float.NaN)), konec = false)
        assertEquals(
            "{\"trip_id\":\"462|1\",\"service_date\":\"2026-09-25\",\"deljenje\":null," +
                "\"tocke\":[{\"lat\":46.1,\"lon\":14.2,\"acc\":null,\"t\":1000,\"v\":null}]," +
                "\"konec\":false}",
            telo)
    }

    @Test
    fun niz_ubezi_narekovaje_in_krmilne_znake() {
        assertEquals("\"a\\\"b\\\\c\\u000a\"", Deljenje.niz("a\"b\\c\n"))
    }

    @Test
    fun zavrnitev_je_4xx_razen_429() {
        assertTrue(Deljenje.jeZavrnitev(404))
        assertTrue(Deljenje.jeZavrnitev(400))
        assertFalse(Deljenje.jeZavrnitev(429))
        assertFalse(Deljenje.jeZavrnitev(502))
        assertFalse(Deljenje.jeZavrnitev(200))
    }
}
