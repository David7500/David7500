package app.kajros

import android.app.Notification
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.media.AudioAttributes
import android.media.AudioManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.os.VibrationAttributes
import android.os.VibrationEffect
import android.os.Vibrator

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
 * (ponavlja se, dokler obvestila ni vec). Storitev v ospredju je tu, ker je
 * bilo do Androida 13 takega obvestila nemogoce podrsati stran. Od 14 se ga da
 * (izmerjeno 7. 10. 2026), zato zvok varuje se [straza]: odmahnjena ali s
 * tipko za glasnost utisana budilka je tiha budilka.
 *
 * **Najprej nezno, nato glasno** (6. 10. 2026). Zvonjenje se zacne
 * [Ura.NEZNO_MS] pred uro zvonjenja na kanalu `budilka-zacetek` (harfa, ki
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
        /**
         * Drugi številki iste faze, za [objavi]: zvok se začne znova samo ob
         * novem obvestilu, posodobitev obstoječega ga ne sproži. 4713 ima
         * deljenje lege.
         */
        private const val OBVESTILO_DRUGO = 4715
        private const val OBVESTILO_NEZNO_DRUGO = 4716
        private val VSA_OBVESTILA =
            listOf(OBVESTILO, OBVESTILO_DRUGO, OBVESTILO_NEZNO, OBVESTILO_NEZNO_DRUGO)

        /**
         * Kako pogosto [straza] pogleda, ali zvok še teče, in po koliko
         * zaporednih tihih pogledih zazvoni znova. Prvi pogled pride po
         * 2 s, ker sistem zvok obvestila začne s 700 ms zamika (izmerjeno
         * na Volli: „notification will be delayed by 700ms“).
         */
        private const val STRAZA_MS = 2_000L
        private const val STRAZA_TIHIH = 2
        /** Toliko poskusov na fazo, nato samo zapis: zvok, ki se ne začne, ne bo začel ob petem. */
        private const val STRAZA_POSKUSOV = 3
        /**
         * Nežni del traja vsaj toliko, tudi ko je ura glasnega že mimo
         * (budnica je prišla pozno, ali pa je potnik nastavil budilko za
         * vlak, ki odpelje čez nekaj minut). Prej je v takem primeru takoj
         * zazvonilo glasno, in David je 6. 10. 2026 slišal ravno to: „začne
         * že s srednjo jakostjo, namesto da začne čisto potihem“. V dvajsetih
         * sekundah zvok zraste od šepeta do jasno slišnega (od 1.10: harfa od
         * -61 do -33 dBFS, glej `zvok_nezno.py`); od rezerve vzame manj, kot
         * vlak zamudi na eni postaji. Od 1.10 je to tudi [Ura.NEZNO_MS].
         */
        private const val NAJMANJ_NEZNO_MS = 20_000L

        /**
         * Tresenje se nežnemu delu pridruži šele pri 35 %, ko je zvok že
         * slišen. Prej je kanal zavibriral takoj ob začetku, in na votli
         * nočni omarici je bilo to glasneje od zvoka (David, 6. 10. 2026:
         * „najprej zvok od nič, enkrat vmes še vibriranje“).
         *
         * Sunki se začnejo mehko in redko, nato rastejo: do glasnega so
         * dvakrat daljši, močnejši in vsako sekundo. V 1.7 so bili ves čas
         * enaki (150 ms, 70/255, na 2,5 s), od 60 % naprej; David: „začne
         * tresti čisto malo in počasi, kar mi je všeč, a bi lahko povečal,
         * da bi hitreje treslo“.
         */
        private const val TRESENJE_DELEZ = 0.35
        private val TRESENJE_RAZMIK_MS = 2_500L to 1_000L
        private val TRESENJE_SUNEK_MS = 150L to 300L
        private val TRESENJE_JAKOST = 70 to 200

        private fun med(meji: Pair<Long, Long>, d: Double): Long =
            (meji.first + (meji.second - meji.first) * d).toLong()

        /** Ali zaslon zvonjenja ta hip sveti; piše ga [ZvonjenjeDejavnost]. */
        @Volatile
        var zaslonViden = false

        /** Ura glasnega dela budilke, ki ta hip zvoni; bere jo zaslon. */
        @Volatile
        var glasnoOb: Long = 0
            private set

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

        /**
         * Budilka gumba „Preizkusi zvonjenje“. Ni v shrambi: ne prestavi se,
         * ne pride v widget in ne čaka na vkrcanje. Zvoni po isti poti kot
         * prava -- isti kanali, isti zaslon --, ker mora potnik slišati
         * natanko to, kar bo slišal zjutraj. Brez preizkusa je bila tiha
         * budilka (1.7--1.9, Samsung 7. 10. 2026) vidna šele, ko je že
         * zamudila.
         */
        const val PREIZKUS = "preizkus"
        @Volatile
        private var preizkus: Budilka? = null

        /** Budilka, ki zvoni pod tem id-jem: iz shrambe ali preizkus. */
        fun budilka(c: Context, id: String): Budilka? =
            if (id == PREIZKUS) preizkus else Shramba.ena(c, id)

        /**
         * Zvoni takoj: nežni del najkrajši dovoljeni (20 s), nato glasno.
         * `zvoni` in `glasnoOb` sta postavljena že tu, ker zaslon, ki ga
         * odpre klicatelj, lahko pride pred storitvijo in bi se brez njiju
         * takoj zaprl.
         */
        fun preizkusi(c: Context) {
            val zdaj = System.currentTimeMillis()
            preizkus = Budilka(id = PREIZKUS, trainNo = "", tripId = null, omrezje = "zeleznica",
                postaja = c.getString(R.string.preizkus), stopSeq = 0, dan = "",
                voznoredniMs = zdaj + 5 * 60_000L, minutPrej = 0, zbudi = true)
            zvoni = PREIZKUS
            glasnoOb = zdaj + NAJMANJ_NEZNO_MS
            zazeni(c, PREIZKUS, zdaj)
        }
    }

    private val roka = Handler(Looper.getMainLooper())
    private val glasno = Runnable { zvoniGlasno() }
    private var tresenjeOd = 0L
    private val tresi = object : Runnable {
        override fun run() {
            // Delež poti od prvega sunka do glasnega dela.
            val d = ((System.currentTimeMillis() - tresenjeOd).toDouble() /
                (glasnoOb - tresenjeOd).coerceAtLeast(1L)).coerceIn(0.0, 1.0)
            tresljaj(d)
            roka.postDelayed(this, med(TRESENJE_RAZMIK_MS, d))
        }
    }
    private var budnost: PowerManager.WakeLock? = null

    /** Faza zvonjenja in številka obvestila, ki ta hip nosi storitev. */
    private var nezno = false
    private var stevilka = 0
    /** Ali je obvestilo objavljeno za odprt zaslon (kanal brez plavajočega obvestila). */
    private var objavljenoNaZaslonu = false
    private var tihih = 0
    private var poskusov = 0

    /**
     * Zvok obvestila utihne, ne da bi budilka nehala zvoniti. Izmerjeno na
     * Volli (Android 16) 7. 10. 2026 pri preizkusu:
     *
     * * **tipka za glasnost** -- sistem utiša zvok obvestila, preden tipka
     *   pride do aplikacije (`RingtonePlayer: stop` 13:28:14,33, tipka v
     *   zaslonu zvonjenja 14,48);
     * * **podrsano plavajoče obvestilo** -- Android 14+ sme obvestilo
     *   storitve odmahniti (`notification_canceled` z razlogom 2, 13:28:45,51).
     *
     * Ostane tresenje in zaslon, zvok pa ne -- natanko „samo malo vibrira“.
     * Zato straža vsaki 2 s pogleda, ali kakšen predvajalnik zvoni kot
     * budilka, in če ga dvakrat zapored ni, isto fazo objavi znova. Ustavi
     * jo samo „Ustavi“ ali poteg. Na isti poti zamenja kanal, kadar se
     * zaslon zvonjenja odpre ali zapre: čez odprt zaslon ne sme viseti
     * plavajoče obvestilo, ki ga človek podrsa stran.
     */
    private val straza = object : Runnable {
        override fun run() {
            val b = zvoni?.let { budilka(this@ZvonjenjeStoritev, it) } ?: return
            when {
                zaslonViden != objavljenoNaZaslonu -> objavi(b)
                zvokTece() -> { tihih = 0; poskusov = 0 }
                ++tihih < STRAZA_TIHIH -> {}
                poskusov < STRAZA_POSKUSOV -> {
                    poskusov++
                    Dnevnik.zapisi(this@ZvonjenjeStoritev, b, "zvok utihnil, zvonim znova")
                    objavi(b)
                }
                poskusov == STRAZA_POSKUSOV -> {
                    poskusov++
                    Dnevnik.zapisi(this@ZvonjenjeStoritev, b,
                        "zvok se ne začne · " + Zvonjenje.stanjeZvoka(this@ZvonjenjeStoritev))
                }
            }
            roka.postDelayed(this, STRAZA_MS)
        }
    }

    /**
     * Ali kateri predvajalnik ta hip zvoni kot budilka. Zvok predvaja
     * sistem, ne mi, zato ga vidimo samo med vsemi predvajalniki naprave.
     */
    private fun zvokTece(): Boolean =
        getSystemService(AudioManager::class.java)?.activePlaybackConfigurations
            ?.any { it.audioAttributes.usage == AudioAttributes.USAGE_ALARM } ?: true

    /**
     * Obvestilo zdajšnje faze pod drugo številko kot doslej, prejšnje gre
     * stran. Nova številka zato, ker sistem zvok začne samo ob novem
     * obvestilu; prejšnje po `startForeground` ni več obvestilo storitve in
     * ga `cancel` pobere.
     */
    private fun objavi(b: Budilka?) {
        val prej = stevilka
        stevilka = if (nezno) {
            if (prej == OBVESTILO_NEZNO) OBVESTILO_NEZNO_DRUGO else OBVESTILO_NEZNO
        } else {
            if (prej == OBVESTILO) OBVESTILO_DRUGO else OBVESTILO
        }
        objavljenoNaZaslonu = b != null && zaslonViden
        vOspredje(stevilka, Zvonjenje.obvestiloZbudi(this, b, System.currentTimeMillis(),
            nezno, naZaslonu = objavljenoNaZaslonu))
        if (prej != 0 && prej != stevilka) {
            getSystemService(NotificationManager::class.java)?.cancel(prej)
        }
        tihih = 0
    }

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
        val b = id?.let { budilka(this, it) }
        // `startForeground` mora priti v nekaj sekundah tudi, ce budilke vmes
        // ni vec -- sicer sistem aplikacijo podre.
        Zvonjenje.kanali(this)
        val zdaj = System.currentTimeMillis()
        val doGlasnega = maxOf(glasnoOb - zdaj, NAJMANJ_NEZNO_MS)
        nezno = b != null
        if (b != null) {
            zvoni = b.id
            ZvonjenjeStoritev.glasnoOb = zdaj + doGlasnega
        }
        objavi(b)
        if (b == null) { ustavi(); return }
        poskusov = 0
        roka.removeCallbacks(straza)
        roka.postDelayed(straza, STRAZA_MS)
        if (nezno) {
            budnost = getSystemService(PowerManager::class.java)
                ?.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "kajros:nezno")
                ?.apply { acquire(doGlasnega + 10_000L) }
            roka.postDelayed(glasno, doGlasnega)
            tresenjeOd = zdaj + (doGlasnega * TRESENJE_DELEZ).toLong()
            roka.postDelayed(tresi, tresenjeOd - zdaj)
            Dnevnik.zapisi(this, b, "zvoni nežno, glasno čez ${(doGlasnega + 500) / 1000} s")
            Dnevnik.zapisi(this, b, Zvonjenje.stanjeZvoka(this))
        }
    }

    /** Konec neznega dela: glasno obvestilo prevzame storitev, nezno gre stran. */
    private fun zvoniGlasno() {
        val b = zvoni?.let { budilka(this, it) } ?: return
        ZvonjenjeStoritev.glasnoOb = System.currentTimeMillis()
        // Glasni kanal trese sam; nežni sunki bi se mešali z njim.
        nehajTresti()
        nezno = false
        poskusov = 0
        objavi(b)
        budnost?.let { if (it.isHeld) it.release() }
        budnost = null
        Dnevnik.zapisi(this, b, "zvoni glasno")
    }

    /**
     * Sunek, usmerjen kot budilka: pride tudi v tihem načinu. `d` je delež
     * poti do glasnega (0 mehko, 1 najmočneje).
     */
    private fun tresljaj(d: Double) {
        val v = getSystemService(Vibrator::class.java) ?: return
        val jakost = med(TRESENJE_JAKOST.first.toLong() to TRESENJE_JAKOST.second.toLong(), d).toInt()
        // Brez nadzora jakosti ostane samo dolžina: kratek sunek je mehak.
        val ucinek = if (v.hasAmplitudeControl()) {
            VibrationEffect.createOneShot(med(TRESENJE_SUNEK_MS, d), jakost)
        } else {
            VibrationEffect.createOneShot(med(60L to 200L, d), VibrationEffect.DEFAULT_AMPLITUDE)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            v.vibrate(ucinek, VibrationAttributes.createForUsage(VibrationAttributes.USAGE_ALARM))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(ucinek, AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build())
        }
    }

    private fun nehajTresti() {
        roka.removeCallbacks(tresi)
        getSystemService(Vibrator::class.java)?.cancel()
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
        val b = kdo?.let { budilka(this, it) }
        if (b?.id == PREIZKUS) {
            // Odlog preizkusa nima česa prestaviti: oboje ga konča.
            preizkus = null
            Dnevnik.zapisi(this, b, "preizkus ustavljen")
        } else if (b != null) {
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
        roka.removeCallbacks(straza)
        nehajTresti()
        budnost?.let { if (it.isHeld) it.release() }
        budnost = null
        // `stopForeground` pobere samo obvestilo storitve; ostala so iz
        // prejšnjih faz ali objav, ki jih je straža zamenjala.
        getSystemService(NotificationManager::class.java)?.let { nm ->
            VSA_OBVESTILA.filter { it != stevilka }.forEach { nm.cancel(it) }
        }
        stevilka = 0
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
        roka.removeCallbacks(straza)
        nehajTresti()
        budnost?.let { if (it.isHeld) it.release() }
        zvoni = null
        super.onDestroy()
    }
}
