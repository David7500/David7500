package app.kajros

import android.app.Notification
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager

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
 *
 * **Najprej nezno, nato glasno** (6. 10. 2026). Zvonjenje se zacne
 * [Ura.NEZNO_MS] pred uro zvonjenja na kanalu `budilka-nezno` (zvoncek, ki
 * raste), ob sami uri pride obvestilo na glasnem kanalu. Dve obvestili, ker
 * zvok pripada kanalu in ga obstojecemu obvestilu ni mogoce zamenjati. Med
 * neznim delom drzimo delni `WakeLock`: brez njega bi procesor v Doze lahko
 * zaspal in preklop na glasno zamudil. Ce se preklop vseeno ne bi zgodil,
 * nezni zvok na koncu ze zbudi -- nikoli ni tisine.
 */
class ZvonjenjeStoritev : Service() {

    companion object {
        const val ID = "id"
        private const val ZVONI = "app.kajros.ZVONI"
        const val USTAVI = "app.kajros.USTAVI"
        const val ODLOZI = "app.kajros.ODLOZI"
        /** "Se dve minuti" -- toliko, kolikor traja pot do vrat, ne pol ure. */
        private const val ODLOG_MS = 2 * 60 * 1000L
        /** Ura glasnega dela (epoch ms); do nje zvoni nezno. */
        const val GLASNO_OB = "glasno_ob"
        /** Obvestilo storitve v ospredju: glasno, kot doslej. */
        const val OBVESTILO = 4711
        /** Obvestilo neznega dela. Svoja stevilka, ker ga glasno zamenja. */
        const val OBVESTILO_NEZNO = 4712
        /** Krajsi nezni del ne pomaga -- takrat takoj glasno. */
        private const val NAJMANJ_NEZNO_MS = 5_000L

        /** Katera budilka ta hip zvoni, ali null. */
        @Volatile
        var zvoni: String? = null
            private set

        /** Zaslon zvonjenja se zapre, ko zvonjenje ustavi gumb v obvestilu. */
        @Volatile
        var obKoncu: (() -> Unit)? = null

        fun namera(c: Context, akcija: String, id: String): Intent =
            Intent(c, ZvonjenjeStoritev::class.java).setAction(akcija).putExtra(ID, id)

        fun zazeni(c: Context, id: String, glasnoOb: Long) {
            val i = namera(c, ZVONI, id).putExtra(GLASNO_OB, glasnoOb)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) c.startForegroundService(i)
            else c.startService(i)
        }
    }

    private val roka = Handler(Looper.getMainLooper())
    private val glasno = Runnable { zvoniGlasno() }
    private var budnost: PowerManager.WakeLock? = null

    override fun onBind(i: Intent?): IBinder? = null

    override fun onStartCommand(i: Intent?, zastavice: Int, zagon: Int): Int {
        val id = i?.getStringExtra(ID)
        when (i?.action) {
            ZVONI -> zacni(id, i.getLongExtra(GLASNO_OB, 0L))
            USTAVI -> koncaj(id, odlozi = false)
            ODLOZI -> koncaj(id, odlozi = true)
            else -> stopSelf()
        }
        return START_NOT_STICKY
    }

    private fun zacni(id: String?, glasnoOb: Long) {
        val b = id?.let { Shramba.ena(this, it) }
        // `startForeground` mora priti v nekaj sekundah tudi, ce budilke vmes
        // ni vec -- sicer sistem aplikacijo podre.
        Zvonjenje.kanali(this)
        val zdaj = System.currentTimeMillis()
        val doGlasnega = glasnoOb - zdaj
        val nezno = b != null && doGlasnega >= NAJMANJ_NEZNO_MS
        if (b != null) zvoni = b.id
        vOspredje(if (nezno) OBVESTILO_NEZNO else OBVESTILO,
            Zvonjenje.obvestiloZbudi(this, b, zdaj, nezno))
        if (b == null) { ustavi(); return }
        if (nezno) {
            budnost = getSystemService(PowerManager::class.java)
                ?.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "kajros:nezno")
                ?.apply { acquire(doGlasnega + 10_000L) }
            roka.postDelayed(glasno, doGlasnega)
            Dnevnik.zapisi(this, b, "zvoni nežno, glasno čez ${(doGlasnega + 500) / 1000} s")
        }
    }

    /** Konec neznega dela: glasno obvestilo prevzame storitev, nezno gre stran. */
    private fun zvoniGlasno() {
        val b = zvoni?.let { Shramba.ena(this, it) } ?: return
        vOspredje(OBVESTILO, Zvonjenje.obvestiloZbudi(this, b, System.currentTimeMillis()))
        getSystemService(NotificationManager::class.java)?.cancel(OBVESTILO_NEZNO)
        budnost?.let { if (it.isHeld) it.release() }
        budnost = null
        Dnevnik.zapisi(this, b, "zvoni glasno")
    }

    private fun vOspredje(stevilka: Int, n: Notification) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(stevilka, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SYSTEM_EXEMPTED)
        } else {
            startForeground(stevilka, n)
        }
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
        roka.removeCallbacks(glasno)
        budnost?.let { if (it.isHeld) it.release() }
        budnost = null
        // Nezno obvestilo ni vec obvestilo storitve, kadar je glasno ze prislo;
        // takrat ga `stopForeground` ne pobere.
        getSystemService(NotificationManager::class.java)?.cancel(OBVESTILO_NEZNO)
        obKoncu?.invoke()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION") stopForeground(true)
        }
        stopSelf()
    }

    override fun onDestroy() {
        roka.removeCallbacks(glasno)
        budnost?.let { if (it.isHeld) it.release() }
        zvoni = null
        super.onDestroy()
    }
}
