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
 *
 * Izjema je budilka: hrani sekunde z zadnjega preverjanja in `Ura` sama
 * presodi, ali zamuda se velja, zato minuto in razred widget odstevanja
 * izpelje sam. Pragovi so zato tu preizkuseni na istih mejah kot na strezniku.
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
    fun `minuta budilke se zaokrozi kot na strezniku`() {
        // `floor(x + 0.5)`: 30 s je minuta, -30 s je nic, -31 s je minuta prej.
        assertEquals(0, Tabla.minute(29))
        assertEquals(1, Tabla.minute(30))
        assertEquals(2, Tabla.minute(90))
        assertEquals(0, Tabla.minute(-30))
        assertEquals(-1, Tabla.minute(-31))
    }

    @Test
    fun `razred budilke ima meje strezniskega`() {
        // `stats._razred_zamude()`: 5 je se "1-5", 6 je "5-15", 16 "nad-15".
        assertEquals("tocno", Tabla.razred(0))
        assertEquals("tocno", Tabla.razred(-3))
        assertEquals("1-5", Tabla.razred(1))
        assertEquals("1-5", Tabla.razred(5))
        assertEquals("5-15", Tabla.razred(6))
        assertEquals("5-15", Tabla.razred(15))
        assertEquals("nad-15", Tabla.razred(16))
    }

    @Test
    fun `beseda budilke je ista kot na tabli`() {
        assertEquals("—", Tabla.zamudaNapis(null as Int?))
        assertEquals("+4", Tabla.zamudaNapis(4))
        assertEquals("3 prej", Tabla.zamudaNapis(-3))
        assertEquals("točno", Tabla.zamudaNapis(0))
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

/** Stran ceste na widgetu: napis in poizvedba. */
class TablaSmerTest {

    @Test
    fun `napis smeri je isti kot na strani`() {
        assertEquals("→ Tobačna", Tabla.smerNapis(listOf("Tobačna")))
        assertEquals("→ Vič Glince · Jadranska", Tabla.smerNapis(listOf("Vič Glince", "Jadranska")))
        assertEquals("→ končna", Tabla.smerNapis(emptyList()))
    }

    @Test
    fun `smer gre v poizvedbo kodirana, brez nje je ni`() {
        val brez = Tabla.naslov("https://kajros.app", Tabla.Nastavitev("Bavarski dvor", "avtobus"))
        assertTrue("smer=" !in brez, brez)
        assertTrue("station=Bavarski+dvor" in brez, brez)
        val z = Tabla.naslov("https://kajros.app",
            Tabla.Nastavitev("Bavarski dvor", "avtobus", "295616c0-387b|x", "→ Kolodvor"))
        assertTrue(z.endsWith("&smer=295616c0-387b%7Cx"), z)
    }
}

class TablaPopravekTest {

    private val n = Tabla.Nastavitev("bavarski", "avtobus", "s1", "→ Kolodvor")

    @Test
    fun `ime postaje prevzame streznikovo`() {
        assertEquals("Bavarski dvor",
            Tabla.Izid.Odhodi(emptyList(), postaja = "Bavarski dvor").popravi(n).postaja)
    }

    @Test
    fun `smer, ki je streznik ne pozna vec, gre z napisom vred`() {
        val p = Tabla.Izid.Odhodi(emptyList(), smerVelja = false).popravi(n)
        assertEquals(null, p.smer)
        assertEquals(null, p.smerNapis)
        assertEquals("bavarski", p.postaja)
    }
}

/** Tabla s ciljem je relacija: druga poizvedba, obrat smeri, imeni s strežnika. */
class TablaRelacijaTest {

    private val n = Tabla.Nastavitev("kranj", "zeleznica", cilj = "ljubljana")

    @Test
    fun `s ciljem vprasa za zveze od ure naprej`() {
        val url = Tabla.naslov("https://kajros.app", n, "16:05")
        assertTrue(url.startsWith("https://kajros.app/api/connections?from=kranj&to=ljubljana"), url)
        assertTrue("&od=16:05" in url && "&limit=${Tabla.SHRANI}" in url, url)
        assertTrue("departures" !in url, url)
    }

    @Test
    fun `obrat zamenja izhodisce in cilj, brez cilja ga ni`() {
        val o = n.obrnjena()!!
        assertEquals("ljubljana", o.postaja)
        assertEquals("kranj", o.cilj)
        assertEquals(null, Tabla.Nastavitev("Kranj", "zeleznica").obrnjena())
    }

    @Test
    fun `imeni prevzame streznikovi`() {
        val p = Tabla.Izid.Odhodi(emptyList(), postaja = "Kranj", cilj = "Ljubljana").popravi(n)
        assertEquals("Kranj", p.postaja)
        assertEquals("Ljubljana", p.cilj)
    }
}
