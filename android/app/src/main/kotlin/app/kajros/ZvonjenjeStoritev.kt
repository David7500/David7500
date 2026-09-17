package app.kajros

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder

/**
 * Zvonjenje: obvestilo, ki ga ni mogoce odmahniti, dokler ga kdo ne ustavi.
 *
 * **Zvoni obvestilo, ne aplikacija.** Dve napaki sta to odlocili, obe izmerjeni
 * na telefonu:
 *
 * 1. 14. 9. 2026 zjutraj je zvok predvajal zaslon zvonjenja, zaslon pa se odpre
 *    samo z dovoljenjem za cel zaslon. Tega ni bilo (`USE_FULL_SCREEN_INTENT:
 *    deny` -- aplikacija ni iz trgovine, zato ga Android 14+ ne da sam), in
 *    budilka se je pokazala kot tiho obvestilo.
 * 2. Isti vecer je zvok predvajala ta storitev -- in Android 16 ga je utisal:
 *    `AudioHardening background playback would be muted for app.kajros (10024),
 *    level: full`, predvajalnik `state:started … muted`. Storitev, zagnana iz
 *    ozadja, ni "v ospredju" za zvok.
 *
 * Zvok obvestila predvaja sistem, ne mi, in te zascite zato ne sprozi. Kanal
 * ima `USAGE_ALARM` (slisi se tudi na tiho) in obvestilo `FLAG_INSISTENT`
 * (ponavlja se, dokler obvestila ni vec). Storitev v ospredju je tu samo zato,
 * ker takega obvestila ni mogoce podrsati stran -- odmahnjena budilka je tiha
 * budilka.
 */
class ZvonjenjeStoritev : Service() {

    companion object {
        const val ID = "id"
        private const val ZVONI = "app.kajros.ZVONI"
        const val USTAVI = "app.kajros.USTAVI"
        const val ODLOZI = "app.kajros.ODLOZI"
        /** "Se dve minuti" -- toliko, kolikor traja pot do vrat, ne pol ure. */
        private const val ODLOG_MS = 2 * 60 * 1000L
        /** Obvestilo storitve v ospredju. Ena naenkrat, zato ena stevilka. */
        const val OBVESTILO = 4711

        /** Katera budilka ta hip zvoni, ali null. */
        @Volatile
        var zvoni: String? = null
            private set

        /** Zaslon zvonjenja se zapre, ko zvonjenje ustavi gumb v obvestilu. */
        @Volatile
        var obKoncu: (() -> Unit)? = null

        fun namera(c: Context, akcija: String, id: String): Intent =
            Intent(c, ZvonjenjeStoritev::class.java).setAction(akcija).putExtra(ID, id)

        fun zazeni(c: Context, id: String) {
            val i = namera(c, ZVONI, id)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) c.startForegroundService(i)
            else c.startService(i)
        }
    }

    override fun onBind(i: Intent?): IBinder? = null

    override fun onStartCommand(i: Intent?, zastavice: Int, zagon: Int): Int {
        val id = i?.getStringExtra(ID)
        when (i?.action) {
            ZVONI -> zacni(id)
            USTAVI -> koncaj(id, odlozi = false)
            ODLOZI -> koncaj(id, odlozi = true)
            else -> stopSelf()
        }
        return START_NOT_STICKY
    }

    private fun zacni(id: String?) {
        val b = id?.let { Shramba.ena(this, it) }
        // `startForeground` mora priti v nekaj sekundah tudi, ce budilke vmes
        // ni vec -- sicer sistem aplikacijo podre.
        Zvonjenje.kanali(this)
        val n = Zvonjenje.obvestiloZbudi(this, b, System.currentTimeMillis())
        if (b != null) zvoni = b.id
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(OBVESTILO, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SYSTEM_EXEMPTED)
        } else {
            startForeground(OBVESTILO, n)
        }
        if (b == null) ustavi()
    }

    private fun koncaj(id: String?, odlozi: Boolean) {
        val kdo = id ?: zvoni
        zvoni = null
        val b = kdo?.let { Shramba.ena(this, it) }
        if (b != null) {
            if (odlozi) {
                val nova = b.copy(
                    odzvonjeno = false,
                    odlozenoDoMs = System.currentTimeMillis() + ODLOG_MS,
                )
                Shramba.shrani(this, nova)
                Nacrtovalec.nastavi(this, nova)
                Widgeti.osvezi(this)
            } else {
                // Ponavljajoca se tu ne prestavi takoj: widget do odhoda odsteva
                // do nje. Prestavi jo `Nacrtovalec`, ko je odhod mimo.
                Nacrtovalec.poZvonjenju(this, b.id)
            }
            Dnevnik.zapisi(this, b, if (odlozi) "odloženo za 2 min" else "ustavljeno")
        }
        ustavi()
    }

    /** Obvestilo gre stran skupaj s storitvijo -- in z njim zvok. */
    private fun ustavi() {
        obKoncu?.invoke()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION") stopForeground(true)
        }
        stopSelf()
    }

    override fun onDestroy() {
        zvoni = null
        super.onDestroy()
    }
}
