package app.kajros

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build

/**
 * Kdaj naj sistem zbudi aplikacijo.
 *
 * **Ena sama nacrtovana budnica na budilko**, ne dve. Ob prozenju se sele
 * odloci, ali je cas za preverjanje ali za zvonjenje -- tako ni mogoce, da bi
 * se razsli in bi eden zvonil, drugi pa ne.
 *
 * Uporabljen je `setAlarmClock`, ker je edini, ki ga Doze ne zadrzi in ga
 * varcevanje z baterijo ne premakne. `setExactAndAllowWhileIdle` je v Doze
 * omejen na en prozen na ~9 minut, kar je manj, kot rabimo.
 */
object Nacrtovalec {

    private fun namera(c: Context, id: String): PendingIntent {
        val i = Intent(c, Sprozilec::class.java).apply {
            action = Sprozilec.PROZI
            // `data` loci namere med sabo: brez nje bi `FLAG_UPDATE_CURRENT`
            // vse budilke zdruzil v eno, ker se `extras` pri primerjavi ne
            // upostevajo. To je klasicna past `PendingIntent`.
            data = android.net.Uri.parse("kajros://budilka/$id")
            putExtra(Sprozilec.ID, id)
        }
        return PendingIntent.getBroadcast(
            c, 0, i,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    /**
     * Kdaj naj se aplikacija naslednjic zbudi za to budilko.
     *
     * Prvic dovolj zgodaj, da je zamuda znana, preden bi bilo treba zvoniti;
     * potem na vsak korak; nazadnje ob samem zvonjenju.
     */
    fun kdaj(b: Budilka, zdajMs: Long): Long {
        val zvoni = b.izracun(zdajMs).zvoniOb
        // Avtobus zna biti prezgoden, zato racunamo z zaletom -- sicer bi prvo
        // preverjanje padlo sele za trenutkom, ko bi ze moralo zvoniti.
        val zacetek = zvoni - Ura.ZALET_MS
        if (zdajMs < zacetek) return zacetek
        return Ura.naslednjePreverjanje(zdajMs, zvoni) ?: zvoni
    }

    fun nastavi(c: Context, b: Budilka, zdajMs: Long = System.currentTimeMillis()) {
        if (b.odzvonjeno || b.ugasnjena) { preklici(c, b.id); return }
        val am = c.getSystemService(AlarmManager::class.java) ?: return
        val ob = kdaj(b, zdajMs)
        val pokazi = PendingIntent.getActivity(
            c, 0,
            Intent(c, GlavnaDejavnost::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        // `setAlarmClock` brez dovoljenja vrze `SecurityException` in bi
        // aplikacijo podrl -- od Androida 12 tocen alarm ni pravica. Ce ga ni,
        // nastavimo, kar smemo: `setAndAllowWhileIdle` sme sistem premakniti za
        // nekaj minut, kar je slabsa budilka, a je budilka.
        try {
            am.setAlarmClock(AlarmManager.AlarmClockInfo(ob, pokazi), namera(c, b.id))
        } catch (e: SecurityException) {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, ob, namera(c, b.id))
        }
    }

    /**
     * Zvonjenje je koncano in potnik ga je ustavil: ponavljajoco prestavi.
     *
     * Loceno od [vseZnova], ker ima ta varovalko "sveze odzvonjeno" -- ta
     * varuje zaslon zvonjenja, ki se stoji, in tu ravno ne velja: zaslon se
     * zapira in shranjene budilke ne bo vec bral.
     */
    fun poZvonjenju(c: Context, id: String) {
        val b = Shramba.ena(c, id) ?: return
        val zdaj = System.currentTimeMillis()
        if (b.odzvonjeno && b.ponavljajoca) Shramba.shrani(c, b.prestavljena(zdaj))
        vseZnova(c, zdaj)
    }

    fun preklici(c: Context, id: String) {
        c.getSystemService(AlarmManager::class.java)?.cancel(namera(c, id))
    }

    /**
     * Toliko po odzvonjenju ponavljajoce se ne prestavimo. Zaslon zvonjenja
     * takrat se stoji in bere shranjeno budilko; ce bi jo pod njim zamenjali
     * z jutrisnjo, bi gumb "se dve minuti" odlozil napacen dan.
     */
    private const val NEDAVNO_MS = 5 * 60_000L

    /**
     * Vse budilke znova: prestavi ponavljajoce in nastavi budnice.
     *
     * Klice se ob zagonu aplikacije, po ponovnem zagonu telefona in vsakic, ko
     * se seznam spremeni -- `AlarmManager` ponovnega zagona ne prezivi, in
     * ponavljajoca budilka se mora nekje prestaviti na naslednji dan. Oboje je
     * ista poteza in zato eno mesto: dve poti do istega stanja bi se razsli.
     */
    fun vseZnova(c: Context, zdajMs: Long = System.currentTimeMillis()) {
        Shramba.pocisti(c, zdajMs)
        Shramba.vse(c).forEach { b ->
            val mimo = b.odzvonjeno || b.voznoredniMs < zdajMs - 60_000L
            val sveze = b.odzvonjeno && zdajMs - b.zvoniObMs < NEDAVNO_MS
            // Budilka, nastavljena pred popravkom 12. 9. 2026, ima lahko prvo
            // ponovitev zunaj izbranega nabora (izmerjeno: nabor tor + sre,
            // shranjen ponedeljek). Take ne cakamo, da odzvoni na napacen dan
            // -- poravnamo jo ob prvem obhodu.
            val zunajNabora = !Ponovitev.jeVNaboru(b.voznoredniMs, b.dnevi)
            if (b.ponavljajoca && (mimo || zunajNabora) && !sveze) {
                Shramba.shrani(c, b.prestavljena(zdajMs))
            }
        }
        Shramba.vse(c).forEach {
            if (it.odzvonjeno || it.ugasnjena) preklici(c, it.id) else nastavi(c, it, zdajMs)
        }
        Widget.osvezi(c)
    }

    /**
     * Ali sme aplikacija sploh nastaviti tocen alarm.
     *
     * Od Androida 12 je to dovoljenje, ne pravica. `USE_EXACT_ALARM` (33+)
     * imamo brez vprasanja, ker smo budilka; ta preveri je za starejse in za
     * primer, ko ga uporabnik odvzame.
     */
    fun smeTocenAlarm(c: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true
        val am = c.getSystemService(AlarmManager::class.java) ?: return false
        return am.canScheduleExactAlarms()
    }
}
