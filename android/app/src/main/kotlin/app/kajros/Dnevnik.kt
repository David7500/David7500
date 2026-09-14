package app.kajros

import android.content.Context
import android.util.Log
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Kaj je budilka naredila in zakaj -- zadnjih nekaj deset vrstic, v telefonu.
 *
 * `logcat` tega ne nadomesti. Budilka, ki 14. 9. 2026 ob 7:08 ni zbudila, je
 * bila pregledana ob 19:38, sistemski dnevnik pa je takrat segal le do 16:04 --
 * vzrok je bilo treba sklepati iz kode. Ta zapis preživi dan in ga je mogoče
 * prebrati v seznamu budilk, brez kabla in brez razvojne različice.
 *
 * Vsebuje samo, kar je v budilki že tako ali tako: vlak, postajo, uro. Iz
 * telefona ne gre nikamor.
 */
object Dnevnik {

    private const val DATOTEKA = "dnevnik"
    private const val KLJUC = "vrstice"
    private const val NAJVEC = 120

    private val CAS = SimpleDateFormat("d. M. HH:mm:ss", Locale("sl"))

    @Synchronized
    fun zapisi(c: Context, b: Budilka?, kaj: String) {
        val kdo = if (b == null) "" else "${b.trainNo.ifBlank { b.postaja }} · "
        Log.i("kajros-budilka", kdo + kaj)
        val p = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
        val vrstice = (p.getString(KLJUC, "") ?: "").lines().filter { it.isNotBlank() } +
            "${CAS.format(Date())}  $kdo$kaj"
        p.edit().putString(KLJUC, vrstice.takeLast(NAJVEC).joinToString("\n")).apply()
    }

    /** Najnovejše zgoraj: kdor odpre dnevnik, išče, kaj se je pravkar zgodilo. */
    fun beri(c: Context): String =
        (c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).getString(KLJUC, "") ?: "")
            .lines().filter { it.isNotBlank() }.reversed().joinToString("\n")
}
