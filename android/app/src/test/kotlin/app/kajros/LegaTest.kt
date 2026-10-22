package app.kajros

import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * Kaj pomeni odgovor sistema na vprašanje za lego. Napačna odločitev je
 * vidna samo na napravi: gumb „Vklopi“, ki ne naredi ničesar, ali
 * nastavitve, ki se odprejo človeku, ki je ravnokar rekel „ne“.
 */
class LegaTest {

    @Test
    fun `dovoljeno ni zavrnjeno`() {
        assertEquals(Lega.Odlocitev(trajno = false, nastavitve = false),
            Lega.poOdgovoru(da = true, razlog = false, trajaloMs = 50, zaGumb = true))
    }

    @Test
    fun `prva zavrnitev ni za vedno`() {
        // Sistem bo vprašal še enkrat: nastavitve bi bile pretiravanje.
        assertEquals(Lega.Odlocitev(trajno = false, nastavitve = false),
            Lega.poOdgovoru(da = false, razlog = true, trajaloMs = 4000, zaGumb = true))
    }

    @Test
    fun `druga zavrnitev v oknu je za vedno, nastavitev ne odpre`() {
        // Človek je okno videl in rekel ne -- nastavitve mu niso odgovor.
        assertEquals(Lega.Odlocitev(trajno = true, nastavitve = false),
            Lega.poOdgovoru(da = false, razlog = false, trajaloMs = 3500, zaGumb = true))
    }

    @Test
    fun `odgovor brez okna odpre nastavitve`() {
        // Sistem okna ni pokazal: brez nastavitev bi dotik ne naredil ničesar.
        assertEquals(Lega.Odlocitev(trajno = true, nastavitve = true),
            Lega.poOdgovoru(da = false, razlog = false,
                trajaloMs = Lega.BREZ_OKNA_MS - 1, zaGumb = true))
    }

    @Test
    fun `nastavitve odpre samo gumb`() {
        // Okno, ki ga je odprla stran prek WebView (gumb lege na zemljevidu)
        // ali deljenje, ima svoje sporočilo; nastavitev ne odpira samo.
        assertEquals(Lega.Odlocitev(trajno = true, nastavitve = false),
            Lega.poOdgovoru(da = false, razlog = false, trajaloMs = 10, zaGumb = false))
    }
}
