package app.kajros

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.graphics.drawable.Icon
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

/**
 * Deljenje lege med voznjo, tudi s telefonom v zepu.
 *
 * Zakaj nativno: brskalnik lege z ugasnjenim zaslonom ne posilja in service
 * worker je nima. Storitev v ospredju vrste `location` pa jo dobiva ves cas,
 * dokler je obvestilo prikazano -- in to je hkrati posteno do potnika: dokler
 * deli, to vidi v vrstici stanja in lahko ustavi z enim dotikom.
 *
 * Voznjo izbere stran (kandidati, potrditev), storitev jo samo dobi. Lego
 * bere iz `LocationManager` (GPS, sicer omrezje) -- brez Googlovih storitev,
 * kot vse v tej aplikaciji. Posilja na `POST /api/deli`, isto kot stran.
 *
 * Zacne se lahko samo, ko je aplikacija spredaj (Android 12+ storitve v
 * ospredju iz ozadja ne dovoli) -- zacne jo `Most.deliZacni()` iz strani.
 */
class DeljenjeStoritev : Service() {

    companion object {
        private const val ZACNI = "app.kajros.DELI_ZACNI"
        private const val USTAVI = "app.kajros.DELI_USTAVI"
        const val KANAL = "deljenje"
        private const val OBVESTILO = 4712
        /** Kako pogosto vprasamo za lego. Streznik gostejsih tock ne rabi. */
        private const val LEGA_MS = 5_000L
        private const val CAKAJ_MS = 15_000

        /** Voznja, ki jo deljenje nosi, kot jo je poslala stran (JSON). */
        @Volatile
        var voznja: String? = null
            private set
        /** Zadnje stanje voznje s streznika (JSON), za stran in obvestilo. */
        @Volatile
        var stanje: String? = null
            private set
        /** Zakaj se je zadnje deljenje koncalo; stran ga prebere enkrat. */
        @Volatile
        var konec: String? = null
        @Volatile
        var aktivno = false
            private set
        /**
         * Stran je deljenje pravkar zacela, storitev pa se ni tekla. Brez tega
         * bi prvo branje stanja (`Most.deliStanje`) videlo "ni aktivno" in
         * stran bi deljenje razglasila za koncano, se preden se je zacelo.
         */
        @Volatile
        var zaganja = false

        fun smeLego(c: Context): Boolean =
            c.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED ||
                c.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED

        fun zacni(c: Context, voznjaJson: String) {
            zaganja = true
            konec = null
            val i = Intent(c, DeljenjeStoritev::class.java)
                .setAction(ZACNI).putExtra("voznja", voznjaJson)
            c.startForegroundService(i)
        }

        fun ustavi(c: Context) {
            if (!aktivno) return
            c.startService(Intent(c, DeljenjeStoritev::class.java).setAction(USTAVI))
        }
    }

    private lateinit var nit: HandlerThread
    private lateinit var delavec: Handler
    private val vrsta = Deljenje.Vrsta()
    private var tripId = ""
    private var dan = ""
    private var oznaka = ""
    private var bus = false
    private var deljenje: String? = null
    private var zacetekMs = 0L
    private var poslanoMs = 0L
    private var lm: LocationManager? = null

    private val poslusalec = object : LocationListener {
        override fun onLocationChanged(l: Location) {
            vrsta.dodaj(Deljenje.Tocka(
                l.latitude, l.longitude,
                if (l.hasAccuracy()) l.accuracy else null,
                l.time,
                if (l.hasSpeed()) l.speed else null))
            // Posiljamo ob legi in ne le ob uri: v dremezu telefona se
            // `postDelayed` zamakne, klic lege pa telefon zbudi sam.
            if (System.currentTimeMillis() - poslanoMs >= Deljenje.POSLJI_MS) poslji(false)
        }

        // Pred API 30 so to abstraktne metode; brez njih se storitev podre.
        @Deprecated("Deprecated in Java")
        override fun onStatusChanged(p: String?, s: Int, e: Bundle?) {}
        override fun onProviderEnabled(p: String) {}
        override fun onProviderDisabled(p: String) {}
    }

    private val ura = object : Runnable {
        override fun run() {
            if (!aktivno) return
            if (System.currentTimeMillis() - zacetekMs > Deljenje.NAJDALJE_MS) {
                koncaj("cas"); return
            }
            if (System.currentTimeMillis() - poslanoMs >= Deljenje.POSLJI_MS) poslji(false)
            delavec.postDelayed(this, Deljenje.POSLJI_MS)
        }
    }

    override fun onBind(i: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        nit = HandlerThread("kajros-deljenje").apply { start() }
        delavec = Handler(nit.looper)
    }

    override fun onStartCommand(i: Intent?, zastavice: Int, zagon: Int): Int {
        when (i?.action) {
            ZACNI -> zacni(i.getStringExtra("voznja"))
            USTAVI -> delavec.post { poslji(true); koncaj("potnik") }
            else -> stopSelf()
        }
        // Brez ponovnega zagona: storitev, ki bi jo sistem obudil brez strani,
        // ne bi vedela, ali potnik se sedi na tem vozilu.
        return START_NOT_STICKY
    }

    private fun zacni(json: String?) {
        val o = try { JSONObject(json ?: "") } catch (e: JSONException) { null }
        tripId = o?.optString("trip_id").orEmpty()
        dan = o?.optString("service_date").orEmpty()
        oznaka = listOf(o?.optString("oznaka"), o?.optString("cilj"))
            .filter { !it.isNullOrBlank() }.joinToString(" → ")
        bus = o?.optString("network") == "avtobus"
        kanal()
        // `startForeground` mora priti v nekaj sekundah tudi, ce je zahteva
        // pokvarjena -- sicer sistem aplikacijo podre.
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(OBVESTILO, obvestilo(null),
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            } else {
                startForeground(OBVESTILO, obvestilo(null))
            }
        } catch (e: SecurityException) {
            // Android 14+: brez dovoljenja za lego storitve vrste `location` ni.
            zaganja = false; konec = "lega"; stopSelf(); return
        }
        if (tripId.isBlank() || dan.isBlank() || !smeLego(this)) {
            konec = "lega"; koncaj(null); return
        }
        voznja = json
        stanje = null
        konec = null
        deljenje = null
        aktivno = true
        zaganja = false
        zacetekMs = System.currentTimeMillis()
        poslanoMs = 0L
        lm = getSystemService(LocationManager::class.java)
        try {
            val ponudniki = lm?.getProviders(true).orEmpty()
            for (p in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
                if (p in ponudniki) lm?.requestLocationUpdates(p, LEGA_MS, 0f, poslusalec, nit.looper)
            }
        } catch (e: SecurityException) {
            konec = "lega"; koncaj(null); return
        }
        delavec.postDelayed(ura, Deljenje.POSLJI_MS)
    }

    /** Poslje nabrane tocke. Tece na delavcevi niti, nikoli na glavni. */
    private fun poslji(zadnjic: Boolean) {
        if (!aktivno) return
        val tocke = vrsta.vzemi()
        if (tocke.isEmpty() && !zadnjic) return
        poslanoMs = System.currentTimeMillis()
        val telo = Deljenje.telo(tripId, dan, deljenje, tocke, zadnjic)
        val (koda, odgovor) = post(telo)
        if (koda == 0 || koda == 429 || koda >= 500) {
            // Ni zveze (predor) ali streznik ta hip ne more: tocke pocakajo.
            if (!zadnjic) vrsta.vrni(tocke)
            return
        }
        val o = try { JSONObject(odgovor ?: "") } catch (e: JSONException) { null }
        if (Deljenje.jeZavrnitev(koda) || o == null) {
            koncaj("napaka"); return
        }
        deljenje = o.optString("deljenje").ifBlank { deljenje }
        o.optJSONObject("stanje")?.let { stanje = it.toString() }
        val k = if (o.isNull("konec")) null else o.optString("konec")
        if (!k.isNullOrBlank() && !zadnjic) { koncaj(k); return }
        osveziObvestilo()
    }

    private fun post(telo: String): Pair<Int, String?> {
        var zveza: HttpURLConnection? = null
        return try {
            zveza = (URL("${Nastavitve.naslov(this)}/api/deli").openConnection()
                as HttpURLConnection).apply {
                connectTimeout = CAKAJ_MS
                readTimeout = CAKAJ_MS
                requestMethod = "POST"
                doOutput = true
                // Cloudflare pred kajros.app zavrne zahteve brez verodostojnega
                // UA -- isto kot v `Tabla`.
                setRequestProperty("User-Agent", "Kajros/${BuildConfig.VERSION_NAME} (Android)")
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
            }
            zveza.outputStream.use { it.write(telo.toByteArray(Charsets.UTF_8)) }
            val koda = zveza.responseCode
            val tok = if (koda < 400) zveza.inputStream else zveza.errorStream
            koda to tok?.bufferedReader()?.use { it.readText() }
        } catch (e: IOException) {
            0 to null
        } finally {
            zveza?.disconnect()
        }
    }

    private fun koncaj(razlog: String?) {
        if (razlog != null) konec = razlog
        aktivno = false
        zaganja = false
        try { lm?.removeUpdates(poslusalec) } catch (e: SecurityException) { /* ze ugasnjeno */ }
        delavec.removeCallbacks(ura)
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        aktivno = false
        try { lm?.removeUpdates(poslusalec) } catch (e: SecurityException) { /* ze ugasnjeno */ }
        nit.quitSafely()
        super.onDestroy()
    }

    // ---------- obvestilo ----------

    private fun kanal() {
        getSystemService(NotificationManager::class.java)?.createNotificationChannel(
            NotificationChannel(KANAL, getString(R.string.kanal_deljenje),
                NotificationManager.IMPORTANCE_LOW))
    }

    /** "Drugi vidijo: med postajama Rakek in Postojna · +32 min" */
    private fun kajVidijo(): String? {
        val s = try { JSONObject(stanje ?: return null) } catch (e: JSONException) { return null }
        val pri = s.optString("pri").takeIf { it.isNotBlank() && !s.isNull("pri") }
        val med = s.optJSONArray("med")
        val kje = when {
            pri != null -> getString(
                if (bus) R.string.deljenje_pri_bus else R.string.deljenje_pri, pri)
            med != null && med.length() == 2 -> getString(
                if (bus) R.string.deljenje_med_bus else R.string.deljenje_med,
                med.optString(0), med.optString(1))
            else -> return null
        }
        val z = s.optJSONObject("zamuda")?.optInt("min") ?: return kje
        return getString(R.string.deljenje_vidijo, kje, if (z > 0) "+$z" else "$z")
    }

    private fun obvestilo(besedilo: String?): Notification {
        val odpri = PendingIntent.getActivity(this, 0,
            Intent(this, GlavnaDejavnost::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val ustavi = Notification.Action.Builder(
            Icon.createWithResource(this, R.drawable.ikona_obvestilo),
            getString(R.string.ustavi),
            PendingIntent.getService(this, 1,
                Intent(this, DeljenjeStoritev::class.java).setAction(USTAVI),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE),
        ).build()
        return Notification.Builder(this, KANAL)
            .setSmallIcon(R.drawable.ikona_obvestilo)
            .setContentTitle(getString(R.string.deljenje_naslov, oznaka))
            .setContentText(besedilo ?: getString(R.string.deljenje_zacetek))
            .setOngoing(true)
            .setContentIntent(odpri)
            .addAction(ustavi)
            .build()
    }

    private fun osveziObvestilo() {
        getSystemService(NotificationManager::class.java)
            ?.notify(OBVESTILO, obvestilo(kajVidijo()))
    }
}
