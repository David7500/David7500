package app.kajros

import android.Manifest
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInstaller
import android.os.Build
import android.os.Handler
import android.os.Looper
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

/**
 * Posodobitev, ki jo aplikacija namesti sama: samo tako budilka obdrži
 * dovoljenje za cel zaslon.
 *
 * David, 6. 10. 2026: „vsakič ko posodobiš, moraš spet dati dovoljenje.“
 * Izmerjeno na emulatorju (Android 15): sistemski namestitveni program, ki ga
 * odpre brskalnik, ob **vsaki** namestitvi postavi `USE_FULL_SCREEN_INTENT`
 * na `deny`, tudi ko ga je potnik pred tem vklopil (1.4 → 1.5: `allow` →
 * `deny`). Od Androida 14 sme to edino posebno dovoljenje ob namestitvi
 * podeliti vsak namestitveni program (`SessionParams.setPermissionState`),
 * zato ga podeli aplikacija, kadar namešča sama sebe. Kajros je budilka; Play
 * ga budilkam podeli ob namestitvi.
 *
 * Potnik še vedno potrdi dvakrat: vrstica je njegov klik, sistemsko okno
 * „Posodobi“ drugi. Prvič Android vpraša še, ali sme Kajros nameščati
 * aplikacije -- tako kot je ob prvi namestitvi vprašal za brskalnik.
 */
object Namestitev {

    private const val CAKAJ_MS = 15_000
    /** APK ima 115 kB. Kar je stokrat večje, ni naša izdaja. */
    private const val NAJVEC_B = 16L * 1024 * 1024
    private const val AKCIJA = "app.kajros.NAMESTITEV"

    /** Kaj naj vrstica pove, ko namestitev ne uspe. Nastavi jo glavna dejavnost. */
    @Volatile
    var obNeuspehu: ((String?) -> Unit)? = null

    /**
     * Prenese [izdaja] v sejo namestitvenega programa in jo preda sistemu.
     *
     * Prenos teče v svoji niti; [neuspeh] pride v glavni niti z razlogom, ki ga
     * potnik razume (ali `null`, kadar ga je preklical sam). Uspeha ni treba
     * javljati: sistem ob posodobitvi aplikacijo ustavi.
     */
    fun zacni(c: Context, izdaja: Posodobitev.Izdaja, neuspeh: (String?) -> Unit) {
        val app = c.applicationContext
        val glavna = Handler(Looper.getMainLooper())
        obNeuspehu = neuspeh
        Thread {
            try {
                predaj(app, izdaja)
            } catch (e: IOException) {
                Dnevnik.zapisi(app, null, "posodobitev ${izdaja.ime}: ${e.message}")
                glavna.post { neuspeh(e.message) }
            } catch (e: SecurityException) {
                Dnevnik.zapisi(app, null, "posodobitev ${izdaja.ime}: ${e.message}")
                glavna.post { neuspeh(e.message) }
            }
        }.start()
    }

    private fun predaj(c: Context, izdaja: Posodobitev.Izdaja) {
        val vsota = izdaja.sha256.lowercase()
        if (vsota.length != 64) throw IOException("strežnik ni poslal vsote")
        val namescevalec = c.packageManager.packageInstaller
        val parametri = PackageInstaller.SessionParams(
            PackageInstaller.SessionParams.MODE_FULL_INSTALL).apply {
            setAppPackageName(c.packageName)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                setPermissionState(Manifest.permission.USE_FULL_SCREEN_INTENT,
                    PackageInstaller.SessionParams.PERMISSION_STATE_GRANTED)
            }
        }
        val id = namescevalec.createSession(parametri)
        val seja = namescevalec.openSession(id)
        var predana = false
        try {
            prenesi(izdaja.url, seja, vsota)
            val namera = Intent(c, NamestitevSprejemnik::class.java).setAction(AKCIJA)
            // Spremenljiva, ker namestitveni program vanjo vpiše izid; namera
            // je izrecna (naš sprejemnik), zato je to dovoljeno tudi na 14+.
            val zastavice = PendingIntent.FLAG_UPDATE_CURRENT or
                (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) PendingIntent.FLAG_MUTABLE else 0)
            seja.commit(PendingIntent.getBroadcast(c, id, namera, zastavice).intentSender)
            predana = true
            Dnevnik.zapisi(c, null, "posodobitev ${izdaja.ime} prenesena, čaka na potrditev")
        } finally {
            if (!predana) seja.abandon()
            seja.close()
        }
    }

    /** Piše v sejo in sproti računa vsoto; brez ujemanja seja ne gre naprej. */
    private fun prenesi(url: String, seja: PackageInstaller.Session, vsota: String) {
        val zveza = URL(url).openConnection() as HttpURLConnection
        try {
            zveza.connectTimeout = CAKAJ_MS
            zveza.readTimeout = CAKAJ_MS
            zveza.setRequestProperty("User-Agent", "Kajros/${BuildConfig.VERSION_NAME} (Android)")
            if (zveza.responseCode != 200) throw IOException("strežnik je vrnil ${zveza.responseCode}")
            val dolzina = zveza.contentLengthLong
            if (dolzina > NAJVEC_B) throw IOException("datoteka je prevelika")
            val md = MessageDigest.getInstance("SHA-256")
            var skupaj = 0L
            zveza.inputStream.use { vhod ->
                seja.openWrite("kajros.apk", 0, dolzina).use { izhod ->
                    val buf = ByteArray(64 * 1024)
                    while (true) {
                        val n = vhod.read(buf)
                        if (n < 0) break
                        skupaj += n
                        if (skupaj > NAJVEC_B) throw IOException("datoteka je prevelika")
                        md.update(buf, 0, n)
                        izhod.write(buf, 0, n)
                    }
                    seja.fsync(izhod)
                }
            }
            val dobljena = md.digest().joinToString("") { "%02x".format(it) }
            if (dobljena != vsota) throw IOException("prenesena datoteka ni cela")
        } finally {
            zveza.disconnect()
        }
    }
}

/**
 * Izid namestitve. Sistem ga pošlje sem; prvi je skoraj vedno „potnik naj
 * potrdi“, in okno za potrditev odpremo mi.
 */
class NamestitevSprejemnik : BroadcastReceiver() {

    override fun onReceive(c: Context, i: Intent) {
        val stanje = i.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)
        when (stanje) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                val potrdi = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU)
                    i.getParcelableExtra(Intent.EXTRA_INTENT, Intent::class.java)
                else @Suppress("DEPRECATION") i.getParcelableExtra(Intent.EXTRA_INTENT)
                if (potrdi == null) { javi(c, "sistem ni vrnil okna za potrditev"); return }
                c.startActivity(potrdi.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
            // Ob uspehu je proces tako ali tako ustavljen; to se vidi le, ko
            // posodobitev ni zamenjala tega procesa (redko, a ne škodi).
            PackageInstaller.STATUS_SUCCESS -> Dnevnik.zapisi(c, null, "posodobitev nameščena")
            // Potnik je v sistemskem oknu pritisnil „Prekliči“: ni napaka.
            PackageInstaller.STATUS_FAILURE_ABORTED -> {
                Dnevnik.zapisi(c, null, "posodobitev preklicana")
                Namestitev.obNeuspehu?.invoke(null)
            }
            else -> javi(c, i.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE) ?: "napaka $stanje")
        }
    }

    private fun javi(c: Context, zakaj: String) {
        Dnevnik.zapisi(c, null, "posodobitev ni uspela: $zakaj")
        Namestitev.obNeuspehu?.invoke(zakaj)
    }
}
