package app.kajros

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Pregled nastavljenih budilk.
 *
 * Nativen in ne spletni iz istega razloga kot budilka sama: rabis ga takrat,
 * ko streznika ni. Vse potrebno je ze v telefonu, zato tu ni nobene zahteve
 * v omrezje.
 */
class BudilkeDejavnost : Activity() {

    private val ura = SimpleDateFormat("HH:mm", Locale("sl"))
    private val dan = SimpleDateFormat("d. M.", Locale("sl"))

    override fun onCreate(stanje: Bundle?) {
        super.onCreate(stanje)
        setContentView(R.layout.budilke)
        findViewById<Button>(R.id.odpri).setOnClickListener {
            startActivity(Intent(this, GlavnaDejavnost::class.java))
            finish()
        }
    }

    override fun onResume() {
        super.onResume()
        narisi()
    }

    private fun narisi() {
        val seznam = findViewById<LinearLayout>(R.id.seznam)
        seznam.removeAllViews()
        val zdaj = System.currentTimeMillis()
        Shramba.pocisti(this, zdaj)
        val budilke = Shramba.vse(this).sortedBy { it.voznoredniMs }

        if (budilke.isEmpty()) {
            seznam.addView(besedilo(R.string.budilk_ni, R.color.ink, 16))
            seznam.addView(besedilo(R.string.budilk_ni_kako, R.color.ink_dim, 14))
            return
        }
        budilke.forEach { seznam.addView(vrstica(seznam, it, zdaj)) }
    }

    private fun besedilo(niz: Int, barva: Int, velikost: Int): TextView =
        TextView(this).apply {
            setText(niz)
            setTextColor(getColor(barva))
            textSize = velikost.toFloat()
            setPadding(0, (12 * resources.displayMetrics.density).toInt(), 0, 0)
        }

    private fun vrstica(starsi: LinearLayout, b: Budilka, zdajMs: Long): View {
        val v = LayoutInflater.from(this)
            .inflate(R.layout.budilka_vrstica, starsi, false)
        val izid = b.izracun(zdajMs)

        v.findViewById<TextView>(R.id.kaj).text =
            if (b.trainNo.isBlank()) b.postaja else "${b.trainNo} · ${b.postaja}"
        // Ura zvonjenja stoji na zadnji znani zamudi in se bo se premikala.
        // Voznoredna ura je edino, kar je gotovo, zato je vedno zraven.
        v.findViewById<TextView>(R.id.kdaj).text = buildString {
            append(dan.format(Date(b.voznoredniMs))).append(' ')
            append(getString(R.string.budilka_vozni_red, ura.format(Date(b.voznoredniMs))))
            append(" · ")
            if (b.odzvonjeno) append(getString(R.string.budilka_odzvonjeno))
            else append(getString(R.string.budilka_zvoni_ob, ura.format(Date(izid.zvoniOb))))
        }
        v.findViewById<TextView>(R.id.kako).text = buildString {
            append(getString(if (b.zbudi) R.string.budilka_zbudi else R.string.budilka_obvesti))
            append(" · ").append(b.minutPrej).append(" min prej")
            if (b.smer.isNotBlank()) append(" · ").append(b.smer)
        }
        v.findViewById<Button>(R.id.odstrani).setOnClickListener {
            Shramba.odstrani(this, b.id)
            Nacrtovalec.preklici(this, b.id)
            Zvonjenje.utisaj(this, b.id)
            narisi()
        }
        return v
    }
}
