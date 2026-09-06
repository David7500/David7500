package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Izvor je varnostno pravilo, ne pomozna funkcija: po njem se odloca, katera
 * stran sme videti most do budilk. Zato ima teste, in ti tecejo brez naprave.
 */
class NastavitveTest {

    @Test
    fun `privzeto je https, ne http`() {
        // Kdor natipka samo ime, hoce sifrirano povezavo. Tih zdrs na `http`
        // bi bil najslabsi mozni privzetek.
        assertEquals("https://kajros.app", Nastavitve.ocisti("kajros.app"))
        assertEquals("https://kajros.app", Nastavitve.ocisti("  kajros.app  "))
    }

    @Test
    fun `pot se zavrze, ker se nastavlja izvor`() {
        assertEquals("https://kajros.app", Nastavitve.ocisti("https://kajros.app/app/train?x=1"))
    }

    @Test
    fun `privzeta vrata se izpustijo`() {
        // WebView izvor poroca brez njih. Ce jih ne bi izpustili, bi bila
        // `https://kajros.app` in `https://kajros.app:443` dva razlicna niza
        // za isti izvor in primerjava bi tiho odpovedala.
        assertEquals("https://kajros.app", Nastavitve.izvor("https://kajros.app:443"))
        assertEquals("http://kajros.app", Nastavitve.izvor("http://kajros.app:80"))
    }

    @Test
    fun `nestandardna vrata ostanejo`() {
        assertEquals("http://192.168.1.164:8001",
            Nastavitve.ocisti("http://192.168.1.164:8001"))
        assertEquals("https://kajros.app:8443", Nastavitve.izvor("https://kajros.app:8443/x"))
    }

    @Test
    fun `brez sheme je https tudi pri naslovu IP`() {
        // Mikaven bi bil izjemek "zasebni naslov pomeni http", a to je ugibanje
        // po obsegu naslova. Pravilo ostane eno samo, pomoc v oknu pa pokaze
        // celo obliko `http://192.168.1.164:8001`.
        assertEquals("https://192.168.1.164:8001", Nastavitve.ocisti("192.168.1.164:8001"))
    }

    @Test
    fun `tuje sheme ne obstajajo`() {
        // `intent:` je znana pot za pobeg iz WebView, `javascript:` bi tekel
        // v nasem izvoru, `file:` bi bral telefon.
        assertNull(Nastavitve.izvor("intent://scan/#Intent;scheme=zxing;end"))
        assertNull(Nastavitve.izvor("javascript:alert(1)"))
        assertNull(Nastavitve.izvor("file:///etc/passwd"))
        assertNull(Nastavitve.ocisti("javascript:alert(1)"))
    }

    @Test
    fun `smeti niso naslov`() {
        assertNull(Nastavitve.ocisti(""))
        assertNull(Nastavitve.ocisti("   "))
        assertNull(Nastavitve.izvor(null))
        assertNull(Nastavitve.izvor("https://"))
        assertNull(Nastavitve.izvor("ni naslov"))
    }

    @Test
    fun `podomena ni isti izvor`() {
        // To je razlika, na kateri stoji vsa varnost mostu: `zlo.kajros.app`
        // ni `kajros.app`, ceprav se konca enako.
        assertTrue(Nastavitve.jeNas("https://kajros.app/app/train", "https://kajros.app"))
        assertFalse(Nastavitve.jeNas("https://zlo.kajros.app/", "https://kajros.app"))
        assertFalse(Nastavitve.jeNas("http://kajros.app/", "https://kajros.app"))
        assertFalse(Nastavitve.jeNas("https://kajros.app.zlo.si/", "https://kajros.app"))
        assertFalse(Nastavitve.jeNas(null, "https://kajros.app"))
    }

    @Test
    fun `velike crke v gostitelju so isti izvor`() {
        assertTrue(Nastavitve.jeNas("HTTPS://Kajros.App/app", "https://kajros.app"))
    }
}
