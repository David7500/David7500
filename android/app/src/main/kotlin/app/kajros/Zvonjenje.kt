package app.kajros

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.graphics.drawable.Icon
import android.media.AudioAttributes
import android.os.Build
import android.provider.Settings
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Kaj se zgodi ob uri zvonjenja.
 *
 * Dva nacina, ker se ju izbere pri vsaki budilki posebej: **obvesti** je
 * obvestilo z zvokom, **zbudi** je zvonjenje, ki traja, dokler ga ne ustavis.
 */
object Zvonjenje {

    /**
     * Kanal budilke. Ime je novo, ker zvoka kanala ni mogoce spremeniti, ko
     * kanal obstaja -- stari `zbudi` je bil namenoma brez zvoka (zvok je
     * predvajala aplikacija) in bi tak ostal za vedno.
     */
    const val KANAL_ZBUDI = "budilka"
    private const val KANAL_ZBUDI_STARI = "zbudi"
    const val KANAL_OBVESTI = "obvesti"
    /** Za sporocila, ki niso alarm: preskocena voznja, ki danes ne vozi. */
    const val KANAL_TIHO = "tiho"

    private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

    fun kanali(c: Context) {
        val nm = c.getSystemService(NotificationManager::class.java) ?: return
        nm.deleteNotificationChannel(KANAL_ZBUDI_STARI)
        // `USAGE_ALARM` gre skozi glasnost budilke, ne zvonjenja: slisi se tudi,
        // kadar je telefon na tiho -- prav to budilko loci od obvestila.
        // `DEFAULT_ALARM_ALERT_URI` in ne trenutni ton: ce potnik ton budilke
        // kasneje zamenja, mora slediti, kanal pa bi si zapomnil starega.
        nm.createNotificationChannel(
            NotificationChannel(KANAL_ZBUDI, c.getString(R.string.kanal_zbudi),
                NotificationManager.IMPORTANCE_HIGH).apply {
                setSound(Settings.System.DEFAULT_ALARM_ALERT_URI,
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build())
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 600, 700, 600, 700)
                setBypassDnd(true)
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            })
        nm.createNotificationChannel(
            NotificationChannel(KANAL_OBVESTI, c.getString(R.string.kanal_obvesti),
                NotificationManager.IMPORTANCE_HIGH))
        nm.createNotificationChannel(
            NotificationChannel(KANAL_TIHO, c.getString(R.string.kanal_tiho),
                NotificationManager.IMPORTANCE_LOW))
    }

    /**
     * Ali sme obvestilo odpreti zaslon zvonjenja cez zaklenjen telefon.
     *
     * Od Androida 14 je to dovoljenje, ki ga sistem da sam samo budilkam in
     * klicem **iz trgovine**. Aplikacija s strani ga nima: na telefonu
     * 14. 9. 2026 `USE_FULL_SCREEN_INTENT: deny`. Zvoni vseeno (storitev), a
     * zaslon ostane temen -- zato ga je treba izrecno zaprositi.
     */
    fun smeCelZaslon(c: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE ||
            c.getSystemService(NotificationManager::class.java)?.canUseFullScreenIntent() == true

    /**
     * Naslov obvestila: kaj pelje, od kod in kdaj.
     * Podnaslov: **zakaj ta ura** -- ali je zamuda upostevana ali ne.
     *
     * Ura brez razloga ni odgovor: potnik mora vedeti, ali stoji za njo
     * meritev ali gol vozni red, ker se v drugem primeru splaca pohiteti.
     */
    fun besedilo(c: Context, b: Budilka, zdajMs: Long): Pair<String, String> {
        val izid = b.izracun(zdajMs)
        // Ura v naslovu in razlog pod njo morata biti ista odlocitev.
        val odhod = izid.odhodMs
        val kaj = if (b.trainNo.isBlank()) b.postaja else "${b.trainNo} · ${b.postaja}"
        val naslov = c.getString(R.string.zvoni_naslov, kaj, URA.format(Date(odhod)))
        val zakaj = when {
            izid.vir == Ura.Vir.PREVENTIVA ->
                c.getString(R.string.zvoni_preventivno, URA.format(Date(b.voznoredniMs)))
            izid.vir == Ura.Vir.VOZNI_RED ->
                c.getString(R.string.zvoni_vozni_red, URA.format(Date(b.voznoredniMs)))
            izid.vir == Ura.Vir.NI_PODATKA ->
                c.getString(R.string.zvoni_ni_podatka, URA.format(Date(b.voznoredniMs)))
            izid.surovaS != null && izid.surovaS >= 60 ->
                c.getString(R.string.zvoni_zamuda, Math.round(izid.surovaS / 60.0).toInt())
            izid.surovaS != null && izid.surovaS <= -60 ->
                c.getString(R.string.zvoni_prezgodaj, Math.round(-izid.surovaS / 60.0).toInt())
            else -> c.getString(R.string.zvoni_tocno)
        }
        return naslov to zakaj
    }

    fun sprozi(c: Context, b: Budilka, zdajMs: Long) {
        kanali(c)
        if (b.zbudi) {
            ZvonjenjeStoritev.zazeni(c, b.id)
            return
        }
        val (naslov, zakaj) = besedilo(c, b, zdajMs)
        c.getSystemService(NotificationManager::class.java)?.notify(
            b.id.hashCode(),
            Notification.Builder(c, KANAL_OBVESTI)
                .setSmallIcon(R.drawable.ikona_obvestilo)
                .setContentTitle(naslov)
                .setContentText(zakaj)
                .setStyle(Notification.BigTextStyle().bigText(zakaj))
                .setCategory(Notification.CATEGORY_ALARM)
                .setAutoCancel(true)
                .setContentIntent(PendingIntent.getActivity(
                    c, 0, Intent(c, GlavnaDejavnost::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
                .build())
    }

    /**
     * Obvestilo storitve, ki zvoni. Ima oba gumba, ker zaslona morda ni:
     * brez dovoljenja za cel zaslon in pri odklenjenem telefonu je to edino,
     * kar potnik vidi.
     */
    fun obvestiloZbudi(c: Context, b: Budilka?, zdajMs: Long): Notification {
        val gradnik = Notification.Builder(c, KANAL_ZBUDI)
            .setSmallIcon(R.drawable.ikona_obvestilo)
            .setCategory(Notification.CATEGORY_ALARM)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setOngoing(true)
        if (b == null) return gradnik.setContentTitle(c.getString(R.string.ime)).build()

        val (naslov, zakaj) = besedilo(c, b, zdajMs)
        val zaslon = Intent(c, ZvonjenjeDejavnost::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
            putExtra(ZvonjenjeDejavnost.ID, b.id)
        }
        val polni = PendingIntent.getActivity(
            c, b.id.hashCode(), zaslon,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        fun gumb(akcija: String, napis: Int, koda: Int) = Notification.Action.Builder(
            Icon.createWithResource(c, R.drawable.ikona_obvestilo),
            c.getString(napis),
            PendingIntent.getService(c, koda,
                ZvonjenjeStoritev.namera(c, akcija, b.id),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE),
        ).build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            // Obvestilo storitve sme sistem pokazati sele cez 10 s. Budilka,
            // ki zazvoni deset sekund pozneje, je se vedno budilka, a nicesar
            // ne pridobimo s cakanjem.
            gradnik.setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE)
        }
        val n = gradnik
            .setContentTitle(naslov)
            .setContentText(zakaj)
            .setStyle(Notification.BigTextStyle().bigText(zakaj))
            // Obvestilo s `fullScreenIntent` je edini nacin, da se zaslon odpre
            // sam, kadar je telefon zaklenjen. Ce dovoljenja ni, ostane
            // obvestilo -- zato ima naslov, besedilo in gumba.
            .setFullScreenIntent(polni, true)
            .setContentIntent(polni)
            .addAction(gumb(ZvonjenjeStoritev.USTAVI, R.string.ustavi, 1))
            .addAction(gumb(ZvonjenjeStoritev.ODLOZI, R.string.se_malo, 2))
            .build()
        // Zvok se ponavlja, dokler obvestila ni -- brez tega bi zazvonil enkrat.
        n.flags = n.flags or Notification.FLAG_INSISTENT
        return n
    }

    /**
     * Ponavljajoca budilka je bila preskocena, ker vozilo danes ne vozi.
     *
     * Tiho obvestilo in ne alarm: potnik mora to izvedeti, a ob peti uri
     * zjutraj ne sme biti zbujen zato, da mu povemo, da mu ni treba vstati.
     */
    fun neVozi(c: Context, b: Budilka) {
        kanali(c)
        val kaj = if (b.trainNo.isBlank()) b.postaja else "${b.trainNo} · ${b.postaja}"
        c.getSystemService(NotificationManager::class.java)?.notify(
            b.id.hashCode(),
            Notification.Builder(c, KANAL_TIHO)
                .setSmallIcon(R.drawable.ikona_obvestilo)
                .setContentTitle(c.getString(R.string.ne_vozi_naslov, kaj))
                .setContentText(c.getString(R.string.ne_vozi_zakaj,
                    URA.format(Date(b.voznoredniMs))))
                .setAutoCancel(true)
                .setContentIntent(PendingIntent.getActivity(
                    c, 0, Intent(c, BudilkeDejavnost::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
                .build())
    }

    /** Odstranjena budilka ne sme zvoniti naprej. */
    fun utisaj(c: Context, id: String) {
        c.getSystemService(NotificationManager::class.java)?.cancel(id.hashCode())
        if (ZvonjenjeStoritev.zvoni == id) {
            c.startService(ZvonjenjeStoritev.namera(c, ZvonjenjeStoritev.USTAVI, id))
        }
    }
}
