package app.kajros

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Kaj odpre bližnjica na domačem zaslonu in ali ima pod obliko ime.
 *
 * Shrani takoj, brez strežnika: bližnjica ne prenaša ničesar, zato tudi
 * preverjati nima česa.
 */
class BliznjicaNastavitev : Activity() {

    private var widgetId = AppWidgetManager.INVALID_APPWIDGET_ID
    private var izbrano = WidgetBliznjica.Dejanje.POT
    private var zImenom = true
    private val vrstice = mutableMapOf<WidgetBliznjica.Dejanje, View>()

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        // Najprej preklic: kdor okno zapre z gumbom nazaj, widgeta ni naročil.
        setResult(RESULT_CANCELED)
        setContentView(R.layout.bliznjica_nastavitev)

        widgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
            ?: AppWidgetManager.INVALID_APPWIDGET_ID
        if (widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) { finish(); return }

        // Že postavljena bližnjica pokaže, kaj je v njej.
        WidgetBliznjica.dejanje(this, widgetId)?.let { izbrano = it }
        zImenom = WidgetBliznjica.zImenom(this, widgetId)

        val seznam = findViewById<LinearLayout>(R.id.dejanja)
        for (d in WidgetBliznjica.Dejanje.values()) {
            val v = layoutInflater.inflate(R.layout.bliznjica_vrstica, seznam, false)
            v.findViewById<ImageView>(R.id.oblika).apply {
                setImageResource(d.oblika)
                setColorFilter(getColor(d.polnilo))
            }
            v.findViewById<ImageView>(R.id.ikona).apply {
                setImageResource(d.ikona)
                setColorFilter(getColor(d.barvaIkone))
            }
            v.findViewById<TextView>(R.id.ime).setText(d.ime)
            v.findViewById<TextView>(R.id.opis).setText(d.opis)
            v.setOnClickListener { izberi(d) }
            seznam.addView(v)
            vrstice[d] = v
        }
        findViewById<Button>(R.id.ime_da).setOnClickListener { izberiIme(true) }
        findViewById<Button>(R.id.ime_ne).setOnClickListener { izberiIme(false) }
        findViewById<Button>(R.id.shrani).setOnClickListener { shrani() }
        izberi(izbrano)
        izberiIme(zImenom)
    }

    private fun izberi(d: WidgetBliznjica.Dejanje) {
        izbrano = d
        for ((k, v) in vrstice) {
            v.setBackgroundResource(if (k == d) R.drawable.gumb_izbran else R.drawable.gumb_tih)
            v.isSelected = k == d
        }
    }

    private fun izberiIme(da: Boolean) {
        zImenom = da
        oznaci(findViewById(R.id.ime_da), da)
        oznaci(findViewById(R.id.ime_ne), !da)
    }

    /** Izbrano polno, drugo prazno, kot pri omrežju v nastavitvi table. */
    private fun oznaci(b: Button, vklop: Boolean) {
        b.setBackgroundResource(if (vklop) R.drawable.gumb else R.drawable.gumb_tih)
        b.setTextColor(getColor(if (vklop) R.color.na_poudarku else R.color.ink_dim))
    }

    private fun shrani() {
        WidgetBliznjica.shrani(this, widgetId, izbrano, zImenom)
        AppWidgetManager.getInstance(this)
            .updateAppWidget(widgetId, WidgetBliznjica.pogled(this, widgetId))
        setResult(RESULT_OK, Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId))
        finish()
    }
}
