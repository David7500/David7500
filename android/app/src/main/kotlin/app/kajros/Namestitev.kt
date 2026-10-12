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
import java.net.ConnectException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.UnknownHostException
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
 * Potnik še vedno potrdi dvakrat: „Posodobi“ v aplikaciji je njegov klik,
 * sistemsko okno drugi. Prvič Android vpraša še, ali sme Kajros nameščati
 * aplikacije -- tako kot je ob prvi namestitvi vprašal za brskalnik.
 *
 * Vsak korak je [Stanje], ki ga kaže zaslon „O aplikaciji“. Do 1.11 je bila
 * namestitev vrstica, ki je med prenosom napisala „Prenašam …“ in nato čakala
 * na sistemsko okno; če se to ni odprlo, se ni zgodilo nič več in vrstica se
 * ni dala več pritisniti.
 */
object Namestitev {

    private const val CAKAJ_MS = 15_000
    /** APK ima 166 kB. Kar je stokrat večje, ni naša izdaja. */
    private const val NAJVEC_B = 16L * 1024 * 1024
    private const val AKCIJA = "app.kajros.NAMESTITEV"

    sealed class Stanje {
        object Miruje : Stanje()
        /** [skupaj] je -1, kadar strežnik dolžine ni povedal. */
        data class Prenasam(val izdaja: Posodobitev.Izdaja, val prejeto: Long, val skupaj: Long) : Stanje()
        /**
         * Seja je predana, sistem čaka na potnika. [namera] odpre okno znova:
         * sprejemnik ga odpre sam, a ga sistem sme tiho zavrniti (zagon
         * dejavnosti iz ozadja), in takrat je gumb edina pot naprej.
         */
        data class Potrdi(val izdaja: Posodobitev.Izdaja?, val namera: Intent) : Stanje()
        data class Napaka(val izdaja: Posodobitev.Izdaja?, val zakaj: String) : Stanje()
    }

    @Volatile
    var stanje: Stanje = Stanje.Miruje
        private set

    /** Izdaja, ki se ta hip namešča. Sprejemnik je ne pozna, zaslon jo rabi. */
    @Volatile
    private var trenutna: Posodobitev.Izdaja? = null

    /** Zaslon, ki stanje kaže; kliče se v glavni niti. */
    var poslusalec: ((Stanje) -> Unit)? = null

    private val glavna = Handler(Looper.getMainLooper())

    internal fun nastavi(s: Stanje) {
        stanje = s
        glavna.post { poslusalec?.invoke(stanje) }
    }

    internal fun napaka(zakaj: String) = nastavi(Stanje.Napaka(trenutna, zakaj))

    internal fun potrdi(namera: Intent) = nastavi(Stanje.Potrdi(trenutna, namera))

    /** Uspeh ali preklic v sistemskem oknu; preklic ni napaka, potnik je rekel ne. */
    internal fun koncano() = nastavi(Stanje.Miruje)

    /**
     * Prenese [izdaja] v sejo namestitvenega programa in jo preda sistemu.
     * Prenos teče v svoji niti; kar se zgodi, pove [stanje].
     */
    fun zacni(c: Context, izdaja: Posodobitev.Izdaja) {
        if (stanje is Stanje.Prenasam) return
        val app = c.applicationContext
        trenutna = izdaja
        nastavi(Stanje.Prenasam(izdaja, 0, -1))
        Thread {
            try {
                pocisti(app)
                predaj(app, izdaja)
            } catch (e: IOException) {
                Dnevnik.zapisi(app, null, "posodobitev ${izdaja.ime}: $e")
                napaka(razlog(e))
            } catch (e: SecurityException) {
                Dnevnik.zapisi(app, null, "posodobitev ${izdaja.ime}: $e")
                napaka(e.message ?: "telefon ni dovolil namestitve")
            }
        }.start()
    }

    /**
     * Seje prejšnjih poskusov. Sistem jih hrani tudi čez ponovni zagon in jih
     * na aplikacijo omeji; nova namestitev je nova seja.
     */
    private fun pocisti(c: Context) {
        val namescevalec = c.packageManager.packageInstaller
        for (s in namescevalec.mySessions) {
            try { namescevalec.abandonSession(s.sessionId) } catch (e: SecurityException) { }
        }
    }

    /** Sporočilo izjeme je za dnevnik; potnik dobi stavek, ki ga razume. */
    private fun razlog(e: IOException): String = when (e) {
        is UnknownHostException, is ConnectException -> "ni povezave s strežnikom"
        is SocketTimeoutException -> "strežnik se ni odzval pravočasno"
        else -> e.message ?: "prenos ni uspel"
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
            prenesi(izdaja, seja, vsota)
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
    private fun prenesi(izdaja: Posodobitev.Izdaja, seja: PackageInstaller.Session, vsota: String) {
        val zveza = URL(izdaja.url).openConnection() as HttpURLConnection
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
                    val buf = ByteArray(16 * 1024)
                    while (true) {
                        val n = vhod.read(buf)
                        if (n < 0) break
                        skupaj += n
                        if (skupaj > NAJVEC_B) throw IOException("datoteka je prevelika")
                        md.update(buf, 0, n)
                        izhod.write(buf, 0, n)
                        nastavi(Stanje.Prenasam(izdaja, skupaj, dolzina))
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

    /**
     * Izid seje, kot ga potnik razume. Sporočilo sistema je angleško in za
     * razvijalca („INSTALL_FAILED_…“); ostane v dnevniku.
     */
    fun opisIzida(c: Context, stanje: Int): String = c.getString(when (stanje) {
        PackageInstaller.STATUS_FAILURE_BLOCKED -> R.string.namestitev_blokirana
        PackageInstaller.STATUS_FAILURE_CONFLICT -> R.string.namestitev_spor
        PackageInstaller.STATUS_FAILURE_INCOMPATIBLE -> R.string.namestitev_nezdruzljiva
        PackageInstaller.STATUS_FAILURE_STORAGE -> R.string.namestitev_prostor
        PackageInstaller.STATUS_FAILURE_INVALID -> R.string.namestitev_neveljavna
        else -> R.string.namestitev_neznano
    })
}

/**
 * Izid namestitve. Sistem ga pošlje sem; prvi je skoraj vedno „potnik naj
 * potrdi“, in okno za potrditev odpremo mi.
 */
class NamestitevSprejemnik : BroadcastReceiver() {

    override fun onReceive(c: Context, i: Intent) {
        val stanje = i.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)
        val sporocilo = i.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)
        when (stanje) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                val potrdi = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU)
                    i.getParcelableExtra(Intent.EXTRA_INTENT, Intent::class.java)
                else @Suppress("DEPRECATION") i.getParcelableExtra(Intent.EXTRA_INTENT)
                if (potrdi == null) {
                    Dnevnik.zapisi(c, null, "posodobitev: sistem ni vrnil okna za potrditev")
                    Namestitev.napaka(c.getString(R.string.namestitev_neznano))
                    return
                }
                potrdi.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                Namestitev.potrdi(potrdi)
                // Sistem sme zagon tiho zavrniti (dejavnost iz ozadja, Xiaomi,
                // Samsung); takrat ostane gumb na zaslonu, ki ga odpre znova.
                try {
                    c.startActivity(potrdi)
                } catch (e: RuntimeException) {
                    Dnevnik.zapisi(c, null, "posodobitev: okna ni bilo mogoče odpreti: $e")
                }
            }
            // Ob uspehu je proces tako ali tako ustavljen; to se vidi le, ko
            // posodobitev ni zamenjala tega procesa (redko, a ne škodi).
            PackageInstaller.STATUS_SUCCESS -> {
                Dnevnik.zapisi(c, null, "posodobitev nameščena")
                Namestitev.koncano()
            }
            PackageInstaller.STATUS_FAILURE_ABORTED -> {
                Dnevnik.zapisi(c, null, "posodobitev preklicana ($sporocilo)")
                Namestitev.koncano()
            }
            else -> {
                Dnevnik.zapisi(c, null, "posodobitev ni uspela: $stanje $sporocilo")
                Namestitev.napaka(Namestitev.opisIzida(c, stanje))
            }
        }
    }
}
