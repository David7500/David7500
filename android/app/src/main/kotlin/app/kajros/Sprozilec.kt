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
        if (b.odzvonjeno) return

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

        val nova = Preverjevalec.zamuda(c, stara)?.let {
            stara.copy(zamudaS = it, zamudaObMs = zdaj)
        } ?: stara

        val izid = nova.izracun(zdaj)
        val posodobljena = nova.copy(zvoniObMs = izid.zvoniOb)
        if (zdaj + BLIZU_MS >= izid.zvoniOb) {
            zvoni(c, posodobljena, zdaj)
        } else {
            Shramba.shrani(c, posodobljena)
            Nacrtovalec.nastavi(c, posodobljena, zdaj)
        }
    }

    private fun zvoni(c: Context, b: Budilka, zdajMs: Long) {
        Shramba.shrani(c, b.copy(odzvonjeno = true, zvoniObMs = b.izracun(zdajMs).zvoniOb))
        Nacrtovalec.preklici(c, b.id)
        Zvonjenje.sprozi(c, b, zdajMs)
    }
}
