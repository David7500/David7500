package app.kajros

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Kaj se zgodi ob uri zvonjenja.
 *
 * Dva nacina, ker se ju izbere pri vsaki budilki posebej: **obvesti** je
 * obvestilo z zvokom, **zbudi** je celozaslonsko zvonjenje, ki traja, dokler
 * ga ne ustavis.
 */
object Zvonjenje {

    const val KANAL_ZBUDI = "zbudi"
    const val KANAL_OBVESTI = "obvesti"
    /** Za sporocila, ki niso alarm: preskocena voznja, ki danes ne vozi. */
    const val KANAL_TIHO = "tiho"

    private val URA = SimpleDateFormat("HH:mm", Locale("sl"))

    fun kanali(c: Context) {
        val nm = c.getSystemService(NotificationManager::class.java) ?: return
        // Kanal za alarme se slisi tudi, kadar je telefon na tiho -- prav to
        // budilko loci od obvestila.
        nm.createNotificationChannel(
            NotificationChannel(KANAL_ZBUDI, c.getString(R.string.kanal_zbudi),
                NotificationManager.IMPORTANCE_HIGH).apply {
                setSound(null, null)   // zvok predvaja dejavnost, ne obvestilo
                enableVibration(false)
                setBypassDnd(true)
            })
        nm.createNotificationChannel(
            NotificationChannel(KANAL_OBVESTI, c.getString(R.string.kanal_obvesti),
                NotificationManager.IMPORTANCE_HIGH))
        nm.createNotificationChannel(
            NotificationChannel(KANAL_TIHO, c.getString(R.string.kanal_tiho),
                NotificationManager.IMPORTANCE_LOW))
    }

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
        val (naslov, zakaj) = besedilo(c, b, zdajMs)
        val nm = c.getSystemService(NotificationManager::class.java) ?: return

        if (!b.zbudi) {
            nm.notify(b.id.hashCode(), Notification.Builder(c, KANAL_OBVESTI)
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
            return
        }

        val zaslon = Intent(c, ZvonjenjeDejavnost::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
            putExtra(ZvonjenjeDejavnost.ID, b.id)
        }
        val polni = PendingIntent.getActivity(
            c, b.id.hashCode(), zaslon,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        // Obvestilo s `fullScreenIntent` je edini nacin, da se zaslon odpre sam,
        // tudi ko je telefon zaklenjen. Ce sistem tega ne dovoli, ostane
        // obvestilo -- zato ima naslov in besedilo, ne le prozilec.
        nm.notify(b.id.hashCode(), Notification.Builder(c, KANAL_ZBUDI)
            .setSmallIcon(R.drawable.ikona_obvestilo)
            .setContentTitle(naslov)
            .setContentText(zakaj)
            .setCategory(Notification.CATEGORY_ALARM)
            .setOngoing(true)
            .setFullScreenIntent(polni, true)
            .setContentIntent(polni)
            .build())
        try {
            c.startActivity(zaslon)
        } catch (e: SecurityException) {
            // Od Androida 10 zagon dejavnosti iz ozadja ni vedno dovoljen.
            // Obvestilo s `fullScreenIntent` je takrat tisto, kar zbudi zaslon.
        }
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

    fun utisaj(c: Context, id: String) {
        c.getSystemService(NotificationManager::class.java)?.cancel(id.hashCode())
    }
}
