package app.kajros

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Kar se zgodi, ko sistem zbudi aplikacijo.
 *
 * Ena nacrtovana budnica na budilko; tu se odloci, ali je cas za preverjanje
 * ali za zvonjenje. Odlocitev je tu in ne v `AlarmManager`, ker se ura
 * zvonjenja med cakanjem premika -- zamuda se spreminja.
 *
 * Po zvonjenju ista budnica sledi vozilu do odhoda: widget takrat odsteva do
 * odhoda in zamuda se se vedno spreminja.
 */
class Sprozilec : BroadcastReceiver() {

    companion object {
        const val PROZI = "app.kajros.PROZI"
        const val ID = "id"
        /** Toleranca: budnica sme priti sekundo prezgodaj in vseeno zvoniti. */
        private const val BLIZU_MS = 30_000L
    }

    private val ura = SimpleDateFormat("HH:mm:ss", Locale("sl"))

    override fun onReceive(c: Context, i: Intent) {
        if (i.action == Intent.ACTION_BOOT_COMPLETED ||
            i.action == Intent.ACTION_MY_PACKAGE_REPLACED
        ) {
            Dnevnik.zapisi(c, null, "zagon: ${i.action?.substringAfterLast('.')}")
            Nacrtovalec.vseZnova(c)
            // `AlarmManager` ponovnega zagona ne prezivi -- tudi ritem odhodne
            // table ne. Brez tega bi tabla po ponovnem zagonu telefona obstala
            // na zadnji uri in tega ne bi povedal nihce.
            WidgetTabla.naRitem(c)
            WidgetTabla.zahtevajPrenos(c)
            return
        }
        if (i.action != PROZI) return
        val id = i.getStringExtra(ID) ?: return
        val b = Shramba.ena(c, id) ?: return
        if (b.ugasnjena) return

        // Omrezje ne sme teci na glavni niti, prozenje pa ima le nekaj sekund.
        val konec = goAsync()
        Thread {
            try {
                if (b.odzvonjeno) sledi(c, b) else obravnavaj(c, b)
            } catch (e: RuntimeException) {
                // Napaka v racunu ne sme pomeniti tisine. Zapisemo jo in budilko
                // nastavimo znova po istem nacrtu -- naslednje prozenje je cez
                // najvec pet minut, zadnje pa ob sami uri zvonjenja.
                Dnevnik.zapisi(c, b, "napaka: $e")
                Nacrtovalec.nastavi(c, b)
            } finally {
                konec.finish()
            }
        }.start()
    }

    private fun obravnavaj(c: Context, stara: Budilka) {
        val zdaj = System.currentTimeMillis()
        val prej = stara.izracun(zdaj)

        // Ce je cas ze tu in ura stoji na SVEZI zamudi (ali na odlogu), ne
        // izgubljajmo sekund z omrezjem -- zvoni. Kadar pa stoji na voznem redu
        // ali preventivi, je vprasanje ravno, ali zamudo lahko izvemo zdaj.
        // 14. 9. 2026 je prav ta bliznjica zazvonila "zamude ni bilo mogoce
        // preveriti", ne da bi strežnik sploh vprasala.
        if (zdaj + BLIZU_MS >= prej.zvoniOb &&
            (prej.vir == Ura.Vir.ZAMUDA || stara.odlozenoDoMs > 0)
        ) {
            zvoni(c, stara, zdaj)
            return
        }

        // Blizu zvonjenja poskusimo veckrat: takrat je odgovor vreden vec kot
        // sekunda cakanja, in prav takrat izpad povezave pomeni preventivno
        // zvonjenje. Dalec od ure en poskus zadosca.
        val nujno = prej.zvoniOb - zdaj <= Ura.PREVENTIVA_MS
        val poskusov = if (nujno) 3 else 1
        var odgovor: Preverjevalec.Odgovor = Preverjevalec.Odgovor.BrezZveze
        for (i in 0 until poskusov) {
            odgovor = Preverjevalec.preveri(c, stara)
            if (odgovor !is Preverjevalec.Odgovor.BrezZveze) break
            if (i + 1 < poskusov) Thread.sleep(2000)
        }

        // Potnik je budilko medtem lahko odstranil ali ugasnil. Shranjevanje
        // stare kopije bi jo obudilo.
        val sveza = Shramba.ena(c, stara.id) ?: return
        if (sveza.ugasnjena || sveza.odzvonjeno) return

        // **Ponavljajoca budilka za vozilo, ki danes ne vozi, ne sme zvoniti.**
        // Nabor dni izbere potnik na pamet ("vsak dan"), vozni red pa pozna
        // resnico -- in nedeljski alarm za delavniski vlak je natanko tisto,
        // zaradi cesar ljudje budilke ugasnejo za vedno.
        //
        // Pri enkratni budilki tega ne delamo: tam je vozjno izbral clovek za
        // dolocen dan, in ce je izginila z voznega reda, je to novica, zaradi
        // katere je treba vstati, ne razlog za tisino.
        if (odgovor is Preverjevalec.Odgovor.NeVozi && sveza.ponavljajoca) {
            preskoci(c, sveza, zdaj)
            return
        }
        val nova = sZamudo(sveza, odgovor)
        val izid = nova.izracun(zdaj)
        val posodobljena = nova.copy(zvoniObMs = izid.zvoniOb)
        Dnevnik.zapisi(c, stara, "preverjeno: ${opis(odgovor)} → zvoni ${
            ura.format(Date(izid.zvoniOb))} (${izid.vir.name.lowercase()})")
        if (zdaj + BLIZU_MS >= izid.zvoniOb) {
            zvoni(c, posodobljena, zdaj)
        } else {
            Shramba.shrani(c, posodobljena)
            Nacrtovalec.nastavi(c, posodobljena, zdaj)
            Widgeti.osvezi(c)
        }
    }

    /**
     * Po zvonjenju: osvezi zamudo do odhoda, da widget odsteva do prave ure.
     * Ko je odhod mimo, `vseZnova` ponavljajoco prestavi na naslednji dan.
     */
    private fun sledi(c: Context, stara: Budilka) {
        val zdaj = System.currentTimeMillis()
        if (stara.sledenjeOb(zdaj) != null) {
            val odgovor = Preverjevalec.preveri(c, stara)
            val sveza = Shramba.ena(c, stara.id) ?: return
            if (sveza.odzvonjeno) Shramba.shrani(c, sZamudo(sveza, odgovor))
        }
        Nacrtovalec.vseZnova(c, zdaj)
    }

    private fun sZamudo(b: Budilka, odgovor: Preverjevalec.Odgovor): Budilka {
        if (odgovor is Preverjevalec.Odgovor.BrezZveze) return b
        // Vsak odgovor je stik -- tudi "ne vozi" in "vozi, zamude pa ne vem".
        // Brez tega je bil odgovor brez zamude isto kot izpad (glej `Ura.Vir`).
        val zdaj = System.currentTimeMillis()
        val vozi = odgovor as? Preverjevalec.Odgovor.Vozi ?: return b.copy(stikObMs = zdaj)
        // "Vozi, zamude pa ne vem" ni razlog, da bi zavrgli zadnjo znano:
        // stara vrednost s svojim casom je se vedno boljsa od nicesar in
        // `Ura` sama presodi, kdaj je prestara.
        if (vozi.zamudaS == null) {
            return b.copy(tripId = vozi.tripId ?: b.tripId, stikObMs = zdaj)
        }
        return b.copy(
            zamudaS = vozi.zamudaS,
            zamudaObMs = zdaj,
            stikObMs = zdaj,
            tripId = vozi.tripId ?: b.tripId,
        )
    }

    private fun opis(o: Preverjevalec.Odgovor): String = when (o) {
        is Preverjevalec.Odgovor.BrezZveze -> "brez zveze"
        is Preverjevalec.Odgovor.NeVozi -> "ne vozi"
        is Preverjevalec.Odgovor.Vozi ->
            if (o.zamudaS == null) "vozi, zamuda neznana" else "zamuda ${o.zamudaS} s"
    }

    /** Danes te voznje ni: povej in prestavi na naslednji dan iz nabora. */
    private fun preskoci(c: Context, b: Budilka, zdajMs: Long) {
        Dnevnik.zapisi(c, b, "danes ne vozi — preskočeno")
        Zvonjenje.neVozi(c, b)
        Shramba.shrani(c, b.prestavljena(zdajMs))
        Nacrtovalec.vseZnova(c, zdajMs)
    }

    private fun zvoni(c: Context, b: Budilka, zdajMs: Long) {
        // Shranimo trenutek, ko je RES zazvonilo, ne nacrtovanega.
        val odzvonjena = b.copy(odzvonjeno = true, zvoniObMs = zdajMs)
        Shramba.shrani(c, odzvonjena)
        Dnevnik.zapisi(c, b, "zvoni (${b.izracun(zdajMs).vir.name.lowercase()}" +
            if (Zvonjenje.smeCelZaslon(c)) ")" else ", celozaslonsko NI dovoljeno)")
        Zvonjenje.sprozi(c, b, zdajMs)
        // Ista budnica odslej sledi vozilu do odhoda -- za widget.
        Nacrtovalec.nastavi(c, odzvonjena, zdajMs)
        Widgeti.osvezi(c)
    }
}
