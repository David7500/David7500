package app.kajros

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView

/**
 * Katera postaja gre na widget z odhodno tablo.
 *
 * **Postaje ni mogoce shraniti, ne da bi jo prej nasli.** Gumb vprasa
 * streznik in shrani sele, ko tabla res pride -- widget, ki bi ostal prazen,
 * je za potnika okvara aplikacije in ne tipkarska napaka izpred treh dni.
 *
 * Iskalnika postaj tu ni: imena razresi streznik (`resolve_station()`), isto
 * kot na strani. Svoj seznam postaj v telefonu bi bil drugo pravilo za isto
 * stvar in bi se ob naslednjem uvozu voznega reda razsel.
 */
class TablaNastavitev : Activity() {

    private var widgetId = AppWidgetManager.INVALID_APPWIDGET_ID
    private var omrezje = "zeleznica"
    private val glavna = Handler(Looper.getMainLooper())

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        // **Najprej preklic.** Kdor okno zapre z gumbom nazaj, widgeta ni
        // narocil; brez tega bi na zaslonu ostal prazen pravokotnik.
        setResult(RESULT_CANCELED)
        setContentView(R.layout.tabla_nastavitev)

        widgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
            ?: AppWidgetManager.INVALID_APPWIDGET_ID
        if (widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) { finish(); return }

        // Ze nastavljen widget: polje pokaze, kaj je v njem, da ga je mogoce
        // popraviti in ne le prepisati na slepo.
        Tabla.nastavitev(this, widgetId)?.let { n ->
            findViewById<EditText>(R.id.postaja).setText(n.postaja)
            omrezje = n.omrezje
        }
        findViewById<Button>(R.id.vlak).setOnClickListener { izberi("zeleznica") }
        findViewById<Button>(R.id.avtobus).setOnClickListener { izberi("avtobus") }
        findViewById<Button>(R.id.shrani).setOnClickListener { poisciInShrani() }
        izberi(omrezje)
    }

    private fun izberi(kaj: String) {
        omrezje = kaj
        val vlak = kaj == "zeleznica"
        // Izbrano je polno, drugo prazno. Brez te razlike je na zaslonu dvoje
        // enakih gumbov in nobeden ne pove, kaj velja.
        findViewById<Button>(R.id.vlak).setBackgroundResource(
            if (vlak) R.drawable.gumb else R.drawable.gumb_tih)
        findViewById<Button>(R.id.vlak).setTextColor(
            getColor(if (vlak) R.color.na_poudarku else R.color.ink_dim))
        findViewById<Button>(R.id.avtobus).setBackgroundResource(
            if (vlak) R.drawable.gumb_tih else R.drawable.gumb)
        findViewById<Button>(R.id.avtobus).setTextColor(
            getColor(if (vlak) R.color.ink_dim else R.color.na_poudarku))
    }

    private fun povej(niz: Int, barva: Int) {
        findViewById<TextView>(R.id.izid).apply {
            setText(niz)
            setTextColor(getColor(barva))
            visibility = View.VISIBLE
        }
    }

    private fun poisciInShrani() {
        val ime = findViewById<EditText>(R.id.postaja).text.toString().trim()
        if (ime.isBlank()) { povej(R.string.tabla_ni_postaje, R.color.sev_bad); return }
        povej(R.string.tabla_iscem, R.color.ink_dim)
        val n = Tabla.Nastavitev(ime, omrezje)
        // Omrezje na svoji niti; pet sekund cakanja na glavni bi bila zamrznjena
        // aplikacija.
        Thread {
            val izid = Tabla.prenesi(this, n)
            glavna.post { koncaj(n, izid) }
        }.start()
    }

    /**
     * Odgovor je prisel.
     *
     * Prazna tabla se **shrani**: pozno zvecer je prazna upraviceno in postaja
     * je prava. Zavrnemo samo postajo, ki je streznik ne pozna -- in izpad
     * zveze ni to, zato takrat ne zavrnemo nicesar.
     */
    private fun koncaj(n: Tabla.Nastavitev, izid: Tabla.Izid) {
        if (izid is Tabla.Izid.BrezZveze) {
            povej(R.string.tabla_ni_zveze, R.color.sev_bad); return
        }
        if (izid is Tabla.Izid.NiPostaje) {
            povej(R.string.tabla_ni_postaje, R.color.sev_bad); return
        }
        Tabla.nastavi(this, widgetId, n)
        Tabla.shraniStanje(this, widgetId,
            Tabla.Stanje((izid as Tabla.Izid.Odhodi).vrstice, System.currentTimeMillis()))
        val am = AppWidgetManager.getInstance(this)
        am.updateAppWidget(widgetId, WidgetTabla.pogled(this, widgetId, null))
        // Ritem se zacne tu in ne sele ob prvem sistemskem obhodu: widget, ki
        // se pol ure ne osvezi, je videti kot pokvarjen, ne kot varcen.
        WidgetTabla.naRitem(this)
        setResult(RESULT_OK, Intent().putExtra(
            AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId))
        finish()
    }
}
