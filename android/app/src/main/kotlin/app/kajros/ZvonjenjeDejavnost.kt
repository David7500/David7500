package app.kajros

import android.app.Activity
import android.app.KeyguardManager
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import android.widget.Button
import android.widget.TextView

/**
 * Zaslon zvonjenja: kaj pelje in kdaj, ter dva velika gumba.
 *
 * Zvoka tu ni vec -- predvaja ga [ZvonjenjeStoritev], ker se ta zaslon odpre
 * samo, kadar sistem dovoli celozaslonsko obvestilo. Budilka, ki zvoni samo,
 * ce se odpre zaslon, ne zbudi nikogar, ki ima to dovoljenje zavrnjeno.
 */
class ZvonjenjeDejavnost : Activity() {

    companion object {
        const val ID = "id"
    }

    private var id: String? = null
    private val zapri: () -> Unit = { runOnUiThread { finish() } }

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        prebudiZaslon()
        setContentView(R.layout.zvonjenje)

        id = intent.getStringExtra(ID)
        val b = id?.let { Shramba.ena(this, it) }
        // Zvonjenje je lahko ze ustavil gumb v obvestilu; zaslon brez zvonjenja
        // bi cakal na gumb, ki nima vec cesa ustaviti.
        if (b == null || ZvonjenjeStoritev.zvoni != b.id) { finish(); return }

        val (naslov, zakaj) = Zvonjenje.besedilo(this, b, System.currentTimeMillis())
        findViewById<TextView>(R.id.zvoni_naslov).text = naslov
        findViewById<TextView>(R.id.zvoni_zakaj).text = zakaj

        findViewById<Button>(R.id.ustavi).setOnClickListener { ukaz(ZvonjenjeStoritev.USTAVI) }
        findViewById<Button>(R.id.se_malo).setOnClickListener { ukaz(ZvonjenjeStoritev.ODLOZI) }
        ZvonjenjeStoritev.obKoncu = zapri
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

    private fun ukaz(akcija: String) {
        id?.let { startService(ZvonjenjeStoritev.namera(this, akcija, it)) }
        finish()
    }

    override fun onDestroy() {
        if (ZvonjenjeStoritev.obKoncu === zapri) ZvonjenjeStoritev.obKoncu = null
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
