package app.kajros

import android.app.Activity
import android.app.KeyguardManager
import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.Ringtone
import android.media.RingtoneManager
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.WindowManager
import android.widget.Button
import android.widget.TextView

/**
 * Zvonjenje cez ves zaslon: zbudi telefon in zvoni, dokler ga ne ustavis.
 *
 * To ni obvestilo z zvokom. Ce je namen ujeti vlak, mora budilka zbuditi tudi
 * cloveka, ki ima telefon na tiho v zepu -- zato gre zvok skozi `USAGE_ALARM`.
 */
class ZvonjenjeDejavnost : Activity() {

    companion object {
        const val ID = "id"
        /** "Se dve minuti" -- toliko, kolikor traja pot do vrat, ne pol ure. */
        private const val ODLOG_MS = 2 * 60 * 1000L
    }

    private var zvonec: Ringtone? = null
    private var tresenje: Vibrator? = null
    private var budilka: Budilka? = null

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        prebudiZaslon()
        setContentView(R.layout.zvonjenje)

        val id = intent.getStringExtra(ID)
        val b = id?.let { Shramba.ena(this, it) }
        budilka = b
        if (b == null) { finish(); return }

        val (naslov, zakaj) = Zvonjenje.besedilo(this, b, System.currentTimeMillis())
        findViewById<TextView>(R.id.zvoni_naslov).text = naslov
        findViewById<TextView>(R.id.zvoni_zakaj).text = zakaj

        findViewById<Button>(R.id.ustavi).setOnClickListener { koncaj() }
        findViewById<Button>(R.id.se_malo).setOnClickListener { odlozi() }

        zazvoni()
    }

    private fun prebudiZaslon() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            getSystemService(KeyguardManager::class.java)?.requestDismissKeyguard(this, null)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON,
            )
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
    }

    private fun zazvoni() {
        val ton = RingtoneManager.getActualDefaultRingtoneUri(this, RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
        zvonec = RingtoneManager.getRingtone(this, ton)?.apply {
            // `USAGE_ALARM` je razlog, da se to slisi tudi na tiho. Z
            // `USAGE_NOTIFICATION` bi budilka v zepu ostala nema.
            audioAttributes = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) isLooping = true
            play()
        }
        tresenje = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            getSystemService(VibratorManager::class.java)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION") getSystemService(Vibrator::class.java)
        }
        tresenje?.vibrate(
            VibrationEffect.createWaveform(longArrayOf(0, 600, 700), 0),
            AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build(),
        )
    }

    private fun utisaj() {
        zvonec?.stop(); zvonec = null
        tresenje?.cancel(); tresenje = null
        budilka?.let { Zvonjenje.utisaj(this, it.id) }
    }

    private fun koncaj() {
        utisaj()
        // Ponavljajoca budilka se tu prestavi na naslednji dan. Ce bi cakali
        // na naslednji zagon aplikacije, bi widget do takrat kazal prazno.
        budilka?.let { Nacrtovalec.poZvonjenju(this, it.id) }
        finish()
    }

    private fun odlozi() {
        val b = budilka
        if (b != null) {
            val nova = b.copy(
                odzvonjeno = false,
                odlozenoDoMs = System.currentTimeMillis() + ODLOG_MS,
            )
            Shramba.shrani(this, nova)
            Nacrtovalec.nastavi(this, nova)
        }
        koncaj()
    }

    override fun onDestroy() {
        utisaj()
        super.onDestroy()
    }

    /**
     * Gumb nazaj budilke ne utisa. Kdor jo hoce ustaviti, naj to pove -- sicer
     * je prevec lahko odmahniti in zaspati naprej.
     */
    @Deprecated("Ogrodje brez AndroidX nima nadomestila.")
    override fun onBackPressed() {
        // namenoma nic
    }
}
