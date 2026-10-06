package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class VkrcanjeTest {

    // Ljubljana Polje in točke vzhodno od nje: 0,001° dolžine je tu ~77 m.
    private val lat = 46.0595
    private val lon = 14.5847
    private val odhod = 1_000_000_000L
    private fun lega(metrovVzhodno: Double, tMs: Long, v: Double? = null, acc: Double? = 10.0) =
        Vkrcanje.Lega(lat, lon + metrovVzhodno / 77_300.0, acc, tMs, v)

    @Test
    fun cakanje_na_postaji_nato_voznja_je_vkrcanje() {
        val s = Vkrcanje.Stanje(lat, lon, vlak = true)
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(50.0, odhod - 60_000, v = 0.3), odhod))
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(400.0, odhod + 60_000, v = 9.0), odhod))
        assertEquals(Vkrcanje.Izid.VKRCAN, s.dodaj(lega(520.0, odhod + 70_000, v = 12.0), odhod))
    }

    @Test
    fun brez_postaje_ni_vkrcanja() {
        // Z avtom ob progi ob uri odhoda: hitro in ob pravem času, a na
        // postaji ga ni bilo.
        val s = Vkrcanje.Stanje(lat, lon, vlak = true)
        for (i in 0..5) {
            assertEquals(Vkrcanje.Izid.CAKA,
                s.dodaj(lega(1000.0 + i * 150, odhod + i * 10_000L, v = 15.0), odhod))
        }
    }

    @Test
    fun hitro_pred_odhodom_ne_steje() {
        // Na postajo s kolesom ali avtom, potem čakanje: hitrost pred
        // odhodom ni vožnja z vlakom.
        val s = Vkrcanje.Stanje(lat, lon, vlak = true)
        s.dodaj(lega(100.0, odhod - 20 * 60_000L), odhod)
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(600.0, odhod - 10 * 60_000L, v = 10.0), odhod))
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(800.0, odhod - 10 * 60_000L + 10_000, v = 10.0), odhod))
    }

    @Test
    fun ena_hitra_lega_je_lahko_skok() {
        val s = Vkrcanje.Stanje(lat, lon, vlak = true)
        s.dodaj(lega(0.0, odhod), odhod)
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(500.0, odhod + 10_000, v = 20.0), odhod))
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(510.0, odhod + 20_000, v = 0.5), odhod))
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(700.0, odhod + 30_000, v = 9.0), odhod))
        assertEquals(Vkrcanje.Izid.VKRCAN, s.dodaj(lega(800.0, odhod + 40_000, v = 9.0), odhod))
    }

    @Test
    fun hitrost_iz_dveh_leg_kadar_je_naprava_ne_pove() {
        val s = Vkrcanje.Stanje(lat, lon, vlak = true)
        s.dodaj(lega(0.0, odhod), odhod)
        s.dodaj(lega(400.0, odhod + 30_000), odhod)            // 400 m / 30 s
        assertEquals(Vkrcanje.Izid.VKRCAN, s.dodaj(lega(600.0, odhod + 40_000), odhod))
        assertEquals(3, s.zadnje.size)
    }

    @Test
    fun nenatancna_lega_ne_steje_za_voznjo_steje_pa_za_postajo() {
        val s = Vkrcanje.Stanje(lat, lon, vlak = true)
        // Omrežna lega 450 m daleč z negotovostjo 200 m: lahko je na postaji.
        s.dodaj(lega(450.0, odhod - 60_000, acc = 200.0), odhod)
        assertTrue(s.bilNaPostaji)
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(900.0, odhod + 60_000, v = 12.0, acc = 400.0), odhod))
        assertEquals(Vkrcanje.Izid.CAKA, s.dodaj(lega(1100.0, odhod + 70_000, v = 12.0, acc = 400.0), odhod))
    }

    @Test
    fun pol_ure_po_odhodu_cakanja_ni_vec() {
        val s = Vkrcanje.Stanje(lat, lon, vlak = false)
        assertEquals(Vkrcanje.Izid.PREPOZNO,
            s.dodaj(lega(0.0, odhod + Vkrcanje.PO_ODHODU_MS + 1), odhod))
    }

    @Test
    fun postajalisce_je_manjse_od_postaje() {
        val bus = Vkrcanje.Stanje(lat, lon, vlak = false)
        bus.dodaj(lega(250.0, odhod - 60_000), odhod)
        assertEquals(false, bus.bilNaPostaji)
        val vlak = Vkrcanje.Stanje(lat, lon, vlak = true)
        vlak.dodaj(lega(250.0, odhod - 60_000), odhod)
        assertEquals(true, vlak.bilNaPostaji)
    }
}
