package app.kajros

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Kar se zgodi, ko sistem zbudi aplikacijo.
 *
 * Ena nacrtovana budnica na budilko; tu se odloci, ali je cas za preverjanje
 * ali za zvonjenje. Odlocitev je tu in ne v `AlarmManager`, ker se ura
 * zvonjenja med cakanjem premika -- zamuda se spreminja.
 */
class Sprozilec : BroadcastReceiver() {

    companion object {
        const val PROZI = "app.kajros.PROZI"
        const val ID = "id"
        /** Toleranca: budnica sme priti sekundo prezgodaj in vseeno zvoniti. */
        private const val BLIZU_MS = 30_000L
    }

    override fun onReceive(c: Context, i: Intent) {
        if (i.action == Intent.ACTION_BOOT_COMPLETED ||
            i.action == Intent.ACTION_MY_PACKAGE_REPLACED
        ) {
            Nacrtovalec.vseZnova(c)
            return
        }
        if (i.action != PROZI) return
        val id = i.getStringExtra(ID) ?: return
        val b = Shramba.ena(c, id) ?: return
        if (b.odzvonjeno || b.ugasnjena) return

        // Omrezje ne sme teci na glavni niti, prozenje pa ima le nekaj sekund.
        val konec = goAsync()
        Thread {
            try {
                obravnavaj(c, b)
            } finally {
                konec.finish()
            }
        }.start()
    }

    private fun obravnavaj(c: Context, stara: Budilka) {
        val zdaj = System.currentTimeMillis()

        // Ce je cas ze tu, ne izgubljajmo sekund z omrezjem -- zvoni.
        if (zdaj + BLIZU_MS >= stara.izracun(zdaj).zvoniOb) {
            zvoni(c, stara, zdaj)
            return
        }

        // Blizu zvonjenja poskusimo veckrat: takrat je odgovor vreden vec kot
        // sekunda cakanja, in prav takrat izpad povezave pomeni preventivno
        // zvonjenje. Dalec od ure en poskus zadosca.
        val nujno = stara.izracun(zdaj).zvoniOb - zdaj <= Ura.PREVENTIVA_MS
        val poskusov = if (nujno) 3 else 1
        var odgovor: Preverjevalec.Odgovor = Preverjevalec.Odgovor.BrezZveze
        for (i in 0 until poskusov) {
            odgovor = Preverjevalec.preveri(c, stara)
            if (odgovor !is Preverjevalec.Odgovor.BrezZveze) break
            if (i + 1 < poskusov) Thread.sleep(2000)
        }

        // **Ponavljajoca budilka za vozilo, ki danes ne vozi, ne sme zvoniti.**
        // Nabor dni izbere potnik na pamet ("vsak dan"), vozni red pa pozna
        // resnico -- in nedeljski alarm za delavniski vlak je natanko tisto,
        // zaradi cesar ljudje budilke ugasnejo za vedno.
        //
        // Pri enkratni budilki tega ne delamo: tam je vozjno izbral clovek za
        // dolocen dan, in ce je izginila z voznega reda, je to novica, zaradi
        // katere je treba vstati, ne razlog za tisino.
        if (odgovor is Preverjevalec.Odgovor.NeVozi && stara.ponavljajoca) {
            preskoci(c, stara, zdaj)
            return
        }
        val vozi = odgovor as? Preverjevalec.Odgovor.Vozi
        val nova = when {
            vozi == null -> stara
            // "Vozi, zamude pa ne vem" ni razlog, da bi zavrgli zadnjo znano:
            // stara vrednost s svojim casom je se vedno boljsa od nicesar in
            // `Ura` sama presodi, kdaj je prestara.
            vozi.zamudaS == null -> stara.copy(tripId = vozi.tripId ?: stara.tripId)
            else -> stara.copy(
                zamudaS = vozi.zamudaS,
                zamudaObMs = System.currentTimeMillis(),
                tripId = vozi.tripId ?: stara.tripId,
            )
        }

        val izid = nova.izracun(zdaj)
        val posodobljena = nova.copy(zvoniObMs = izid.zvoniOb)
        if (zdaj + BLIZU_MS >= izid.zvoniOb) {
            zvoni(c, posodobljena, zdaj)
        } else {
            Shramba.shrani(c, posodobljena)
            Nacrtovalec.nastavi(c, posodobljena, zdaj)
            Widget.osvezi(c)
        }
    }

    /** Danes te voznje ni: povej in prestavi na naslednji dan iz nabora. */
    private fun preskoci(c: Context, b: Budilka, zdajMs: Long) {
        Zvonjenje.neVozi(c, b)
        Shramba.shrani(c, b.prestavljena(zdajMs))
        Nacrtovalec.vseZnova(c, zdajMs)
    }

    private fun zvoni(c: Context, b: Budilka, zdajMs: Long) {
        // Shranimo trenutek, ko je RES zazvonilo, ne nacrtovanega.
        Shramba.shrani(c, b.copy(odzvonjeno = true, zvoniObMs = zdajMs))
        Nacrtovalec.preklici(c, b.id)
        Zvonjenje.sprozi(c, b, zdajMs)
        Widget.osvezi(c)
    }
}
