package app.kajros

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * O aplikaciji: katera različica je nameščena in posodobitev od pritiska do
 * sistemskega okna.
 *
 * 12. 10. 2026 je prijatelj pritisnil vrstico o posodobitvi in „se ni zgodilo
 * nič“; nato je aplikacijo prenesel z interneta, kjer jo je brskalnik označil
 * za nevarno. Različice, ki jo ima, ni mogel nikjer pogledati. Zato tu vsak
 * korak pove, kaj se dogaja, in ima gumb naprej -- tudi kadar sistem okna za
 * potrditev ne odpre sam.
 *
 * Odpre jo vrstica o posodobitvi (z [POSODOBI], takrat namestitev začne
 * sama: pritisk na vrstico je bil potnikov klik) in meni Več na strani
 * (`Most.oAplikaciji()`).
 */
class AplikacijaDejavnost : Activity() {

    companion object {
        /** Potnik je pritisnil vrstico „Na voljo je …“: začni brez drugega klika. */
        const val POSODOBI = "posodobi"
    }

    private val datum = SimpleDateFormat("d. M. yyyy", Locale("sl"))

    private lateinit var kartica: View
    private lateinit var naslovKartice: TextView
    private lateinit var besedilo: TextView
    private lateinit var napredek: ProgressBar
    private lateinit var glavni: Button
    private lateinit var preveri: Button
    private lateinit var sStrani: Button
    private lateinit var preverjeno: TextView

    private var izdaja: Posodobitev.Izdaja? = Posodobitev.zadnja
    private var preverjam = false
    private var niZveze = false
    /** Odprli smo nastavitev za nameščanje; ob vrnitvi namestimo, če je vklopljena. */
    private var cakaDovoljenje = false
    private var brezDovoljenja = false
    /** Vrstica je rekla „posodobi“, a proces izdaje ne pozna več: najprej vprašaj. */
    private var posodobiPoOdgovoru = false

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        setContentView(R.layout.aplikacija)
        kartica = findViewById(R.id.kartica_posodobitev)
        naslovKartice = findViewById(R.id.posodobitve)
        besedilo = findViewById(R.id.stanje)
        napredek = findViewById(R.id.napredek)
        glavni = findViewById(R.id.glavni)
        preveri = findViewById(R.id.preveri)
        sStrani = findViewById(R.id.s_strani)
        preverjeno = findViewById(R.id.preverjeno)

        findViewById<TextView>(R.id.razlicica).text =
            getString(R.string.aplikacija_razlicica, BuildConfig.VERSION_NAME)
        val namescena = packageManager.getPackageInfo(packageName, 0).lastUpdateTime
        findViewById<TextView>(R.id.podrobno).text = getString(R.string.aplikacija_podrobno,
            datum.format(Date(namescena)), Build.VERSION.RELEASE)
        findViewById<View>(R.id.glava).setOnLongClickListener { Dnevnik.pokazi(this); true }

        preveri.setOnClickListener { preveriZdaj() }
        sStrani.setOnClickListener { odpriStran() }

        val takoj = stanje == null && intent.getBooleanExtra(POSODOBI, false)
        val znana = izdaja
        if (takoj && znana != null && znana.novejsa) posodobi(znana)
        // Vrstica je lahko stara ves dan; zaslon, ki ga je potnik odprl sam,
        // vpraša znova. Med namestitvijo ne: odgovor je že tu.
        else if (Namestitev.stanje is Namestitev.Stanje.Miruje) {
            posodobiPoOdgovoru = takoj
            preveriZdaj()
        }
    }

    override fun onResume() {
        super.onResume()
        Namestitev.poslusalec = { narisi() }
        if (cakaDovoljenje) {
            cakaDovoljenje = false
            val i = izdaja
            if (packageManager.canRequestPackageInstalls() && i != null) posodobi(i)
            else brezDovoljenja = true
        }
        narisi()
    }

    override fun onPause() {
        Namestitev.poslusalec = null
        super.onPause()
    }

    private fun preveriZdaj() {
        if (preverjam) return
        preverjam = true
        niZveze = false
        narisi()
        Posodobitev.preveriZdaj(this) { odgovor ->
            preverjam = false
            if (odgovor != null) izdaja = odgovor else niZveze = true
            if (isDestroyed) return@preveriZdaj
            if (posodobiPoOdgovoru && odgovor != null && odgovor.novejsa) posodobi(odgovor)
            posodobiPoOdgovoru = false
            narisi()
        }
    }

    private fun posodobi(i: Posodobitev.Izdaja) {
        // Prvič mora potnik Kajrosu dovoliti nameščanje. Sistemsko okno to
        // sicer ponudi samo, a sejo ob vklopu stikala zavrže (izmerjeno na
        // emulatorju, Android 15: „User rejected permissions“) in potnik
        // bi moral pritisniti še enkrat. Zato najprej nastavitev, ob vrnitvi
        // (`onResume`) pa namestitev brez drugega klika.
        if (!packageManager.canRequestPackageInstalls()) {
            cakaDovoljenje = true
            Toast.makeText(this, R.string.posodobitev_dovoli, Toast.LENGTH_LONG).show()
            try {
                startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:$packageName")))
            } catch (e: ActivityNotFoundException) {
                startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:$packageName")))
            }
            return
        }
        brezDovoljenja = false
        Namestitev.zacni(this, i)
    }

    private fun odpriStran() {
        val stran = izdaja?.stran ?: (Nastavitve.naslov(this) + "/android")
        // Naslov s strežnika je preverjen v `Posodobitev` (naš izvor).
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(stran)))
        } catch (e: ActivityNotFoundException) {
            Toast.makeText(this, stran, Toast.LENGTH_LONG).show()
        }
    }

    /** Vse iz stanja: zaslon se nariše enako, od kodar koli se vanj vrnemo. */
    private fun narisi() {
        val i = izdaja
        val nova = i != null && i.novejsa
        var tekst: CharSequence
        var gumb: Int? = null
        var akcija: (() -> Unit)? = null
        var kazPreveri = false
        var kazStran = false
        napredek.visibility = View.GONE

        // Napaka stare izdaje ne velja več, kadar strežnik zdaj pravi, da
        // novejše ni (izdajo so medtem umaknili ali je že nameščena).
        val stanje = Namestitev.stanje.let { if (it is Namestitev.Stanje.Napaka && !nova) Namestitev.Stanje.Miruje else it }
        when (val s = stanje) {
            is Namestitev.Stanje.Prenasam -> {
                napredek.visibility = View.VISIBLE
                if (s.skupaj > 0) {
                    val del = (100 * s.prejeto / s.skupaj).toInt().coerceIn(0, 100)
                    napredek.isIndeterminate = false
                    napredek.progress = del
                    tekst = getString(R.string.posodobitev_prenasam_del, s.izdaja.ime, del)
                } else {
                    napredek.isIndeterminate = true
                    tekst = getString(R.string.posodobitev_prenasam, s.izdaja.ime)
                }
            }
            is Namestitev.Stanje.Potrdi -> {
                tekst = getText(R.string.posodobitev_potrdi)
                gumb = R.string.gumb_potrdi
                akcija = {
                    try { startActivity(s.namera) } catch (e: RuntimeException) {
                        Namestitev.napaka(getString(R.string.namestitev_neznano))
                    }
                }
            }
            is Namestitev.Stanje.Napaka -> {
                tekst = getString(R.string.posodobitev_napaka, s.zakaj)
                if (nova) { gumb = R.string.gumb_poskusi; akcija = { posodobi(i!!) } }
                kazStran = true
            }
            Namestitev.Stanje.Miruje -> when {
                preverjam -> {
                    tekst = getString(R.string.posodobitev_preverjam)
                    napredek.visibility = View.VISIBLE
                    napredek.isIndeterminate = true
                }
                nova && brezDovoljenja -> {
                    tekst = getString(R.string.posodobitev_brez_dovoljenja)
                    gumb = R.string.gumb_nastavitve
                    akcija = { posodobi(i!!) }
                    kazStran = true
                }
                nova -> {
                    tekst = if (i!!.objavljeno.isBlank()) getString(R.string.posodobitev_nova, i.ime)
                        else getString(R.string.posodobitev_nova_dan, i.ime, objavljena(i.objavljeno))
                    gumb = R.string.gumb_posodobi
                    akcija = { posodobi(i) }
                }
                niZveze -> { tekst = getString(R.string.posodobitev_ni_zveze); kazPreveri = true }
                else -> { tekst = getString(R.string.posodobitev_zadnja); kazPreveri = true }
            }
        }

        besedilo.text = tekst
        glavni.visibility = if (gumb != null) View.VISIBLE else View.GONE
        if (gumb != null) {
            glavni.setText(gumb)
            glavni.setOnClickListener { akcija?.invoke() }
        }
        preveri.visibility = if (kazPreveri) View.VISIBLE else View.GONE
        sStrani.visibility = if (kazStran) View.VISIBLE else View.GONE

        // Nova različica je tonska kartica kot budilka na domači strani: to je
        // edino, kar na tem zaslonu kaj zahteva od potnika.
        val tonska = nova && stanje !is Namestitev.Stanje.Napaka
        kartica.setBackgroundResource(if (tonska) R.drawable.kartica_vklop else R.drawable.kartica)
        naslovKartice.setTextColor(getColor(if (tonska) R.color.m_na_kont else R.color.ink))
        besedilo.setTextColor(getColor(if (tonska) R.color.m_na_kont else R.color.ink))
        // Siva besedila strani na rjavi ne dosežejo kontrasta; tonske vloge da.
        sStrani.setTextColor(getColor(if (tonska) R.color.m_na_kont else R.color.ink_dim))
        preverjeno.setTextColor(getColor(if (tonska) R.color.m_na_kont_2 else R.color.ink_mute))

        val kdaj = Posodobitev.nazadnjeVprasano(this)
        preverjeno.visibility = if (kdaj > 0) View.VISIBLE else View.GONE
        if (kdaj > 0) preverjeno.text = getString(R.string.posodobitev_preverjeno, kdaj(kdaj))
    }

    /** „danes ob 21:40“ ali „11. 10. ob 8:05“, kot povsod na strani. */
    private fun kdaj(ms: Long): String {
        val dan = SimpleDateFormat("d. M.", Locale("sl"))
        val danes = dan.format(Date())
        val tisti = dan.format(Date(ms))
        val ura = SimpleDateFormat("H:mm", Locale("sl")).format(Date(ms))
        return if (tisti == danes) getString(R.string.danes_ob, ura)
            else getString(R.string.dan_ob, tisti, ura)
    }

    /** `2026-10-12` s strežnika v obliko, kot jo pišemo povsod: 12. 10. 2026. */
    private fun objavljena(iso: String): String = try {
        datum.format(SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).parse(iso)!!)
    } catch (e: java.text.ParseException) {
        iso
    }
}
