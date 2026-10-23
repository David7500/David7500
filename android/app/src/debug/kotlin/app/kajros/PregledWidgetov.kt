package app.kajros

import android.app.Activity
import android.app.WallpaperManager
import android.appwidget.AppWidgetHost
import android.appwidget.AppWidgetHostView
import android.appwidget.AppWidgetManager
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.util.SizeF
import android.util.TypedValue
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.RemoteViews
import android.widget.ScrollView
import android.widget.TextView

/**
 * Samo v razvojni gradnji: en widget v vseh velikostih na enem zaslonu, z
 * vzorčnimi podatki, za posnetke z `adb exec-out screencap`.
 *
 *     adb shell am start -n app.kajros/.PregledWidgetov -e kaj tabla -e stanje 0
 *
 * `kaj` je `odstevanje`, `budilke` ali `tabla`; `stanje` izbere vzorec (glej
 * `vzorci`). `ozadje` `svetlo` pobarva zaslon kot svetlo ozadje. `tapeta`
 * `svetla` ali `temna` postavi enobarvno ozadje zaslona naprave, po katerem
 * se ravna videz brez podlage (`Izris.svetloOzadje`) -- samo za emulator.
 *
 * `kaj` `zivo` pa widgete res veže na gostitelja (pred tem
 * `adb shell appwidget grantbind --package app.kajros`): tabla za Ljubljano
 * vpraša strežnik, budilke in odštevanje berejo shrambo -- vse po isti poti
 * kot na domačem zaslonu.
 *
 * Od Androida 12 widgeti niso vezani (`bindAppWidgetId`): `AppWidgetHostView`
 * dobi RemoteViews naravnost iz `pogled()`, zato jih ne prepiše nobena
 * osvežitev in vzorec ostane vzorec. Postavitev iz zemljevida velikosti izbere
 * pogled sam ob razporeditvi -- isto kot na domačem zaslonu.
 *
 * Prej velikost pove launcher v `OPTION_APPWIDGET_*`, ki jih ima samo vezan
 * widget: tam jih vežemo (`grantbind` kot pri `zivo`), povemo velikost in
 * vzorec pošljemo za osvežitvijo, ki jo sproži vezava.
 */
class PregledWidgetov : Activity() {

    /** Velikosti iz Googlove preglednice mrež; ležeče 3×2 je ožje od zaslona. */
    private val vrste = listOf(
        listOf(57 to 102, 130 to 102, 203 to 102),
        listOf(276 to 102),
        listOf(269 to 51),
        listOf(130 to 220, 260 to 220),
        listOf(276 to 220),
        listOf(400 to 117),
        listOf(130 to 337, 260 to 337),
    )

    private var gostitelj: AppWidgetHost? = null

    override fun onCreate(s: Bundle?) {
        super.onCreate(s)
        intent.getStringExtra("tapeta")?.let { tapeta(it == "svetla") }
        val kaj = intent.getStringExtra("kaj") ?: "tabla"
        if (kaj == "zivo") { zivo(); return }
        val stanje = intent.getStringExtra("stanje")?.toIntOrNull() ?: 0
        val svetlo = intent.getStringExtra("ozadje") == "svetlo"
        val zdaj = System.currentTimeMillis()

        val (razred, opis, zgradi) = vzorec(kaj, stanje, zdaj)
        val info = AppWidgetManager.getInstance(this)
            .getInstalledProvidersForPackage(packageName, null)
            .first { it.provider.className == razred }

        val stolpec = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(4), dp(28), dp(4), dp(8))
        }
        stolpec.addView(TextView(this).apply {
            text = "$kaj $stanje: $opis"
            setTextColor(if (svetlo) Color.BLACK else Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
        })
        val am = AppWidgetManager.getInstance(this)
        val vezani = Build.VERSION.SDK_INT < Build.VERSION_CODES.S
        val h = if (!vezani) null else AppWidgetHost(this, 4748).also {
            it.deleteHost(); it.startListening(); gostitelj = it
        }
        var id = 1000
        for (vrsta in vrste) {
            val v = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            for ((s, vis) in vrsta) {
                val hv: AppWidgetHostView
                if (h != null) {
                    id = h.allocateAppWidgetId()
                    if (!am.bindAppWidgetIdIfAllowed(id, info.provider)) {
                        stolpec.addView(TextView(this).apply {
                            text = "Ni dovoljenja: adb shell appwidget grantbind --package app.kajros"
                            setTextColor(Color.WHITE)
                        })
                        h.deleteAppWidgetId(id)
                        continue
                    }
                    am.updateAppWidgetOptions(id, Bundle().apply {
                        putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, s)
                        putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH, s)
                        putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT, vis)
                        putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT, vis)
                    })
                    hv = h.createView(this, id, info)
                    val vid = id
                    // Za `onUpdate` in `onAppWidgetOptionsChanged`, ki ju je
                    // sprožila vezava in tečeta na tej niti za `onCreate`.
                    for (zamik in longArrayOf(1500, 3000)) {
                        stolpec.postDelayed({ am.updateAppWidget(vid, zgradi(vid)) }, zamik)
                    }
                } else {
                    hv = AppWidgetHostView(this)
                    hv.setAppWidget(++id, info)
                    hv.updateAppWidget(zgradi(id))
                }
                hv.setPadding(0, 0, 0, 0)
                hv.layoutParams = LinearLayout.LayoutParams(dp(s), dp(vis)).apply {
                    setMargins(dp(4), dp(4), dp(4), dp(4))
                }
                v.addView(hv)
            }
            stolpec.addView(v)
        }
        setContentView(ScrollView(this).apply {
            setBackgroundColor(if (svetlo) Color.rgb(0xe9, 0xe2, 0xd6) else Color.rgb(0x2c, 0x3a, 0x4a))
            addView(stolpec, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT))
        })
    }

    override fun onDestroy() {
        gostitelj?.deleteHost()
        super.onDestroy()
    }

    private fun tapeta(svetla: Boolean) {
        val bmp = Bitmap.createBitmap(64, 64, Bitmap.Config.ARGB_8888)
        bmp.eraseColor(if (svetla) Color.rgb(0xe9, 0xe2, 0xd6) else Color.rgb(0x2c, 0x3a, 0x4a))
        WallpaperManager.getInstance(this).setBitmap(bmp, null, true, WallpaperManager.FLAG_SYSTEM)
    }

    /** Pravi widgeti, vezani na lastnega gostitelja: osvežitve pridejo od ponudnikov. */
    private fun zivo() {
        val am = AppWidgetManager.getInstance(this)
        val h = AppWidgetHost(this, 4747)
        // Ostanki prejšnjega zagona (ubit proces ne pokliče `onDestroy`).
        h.deleteHost()
        gostitelj = h
        h.startListening()
        val stolpec = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(4), dp(28), dp(4), dp(8))
        }
        val vsi = am.getInstalledProvidersForPackage(packageName, null)
        for ((razred, s, v) in listOf(
            Triple(WidgetTabla::class.java, 276, 220),
            Triple(Widget::class.java, 276, 102),
            Triple(WidgetBudilke::class.java, 276, 220),
        )) {
            val info = vsi.first { it.provider.className == razred.name }
            val id = h.allocateAppWidgetId()
            if (!am.bindAppWidgetIdIfAllowed(id, info.provider)) {
                h.deleteAppWidgetId(id)
                stolpec.addView(TextView(this).apply {
                    text = "Ni dovoljenja: adb shell appwidget grantbind --package app.kajros"
                    setTextColor(Color.WHITE)
                })
                break
            }
            // Nastavitev pred prvim `onUpdate`: ta pride kot oddaja in teče za
            // tem `onCreate`, na isti niti.
            if (razred == WidgetTabla::class.java) {
                Tabla.nastavi(this, id, Tabla.Nastavitev("Ljubljana", "zeleznica"))
            }
            val hv = h.createView(this, id, info)
            hv.layoutParams = LinearLayout.LayoutParams(dp(s), dp(v)).apply {
                setMargins(dp(4), dp(4), dp(4), dp(4))
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                hv.updateAppWidgetSize(Bundle(), listOf(SizeF(s.toFloat(), v.toFloat())))
            }
            stolpec.addView(hv)
        }
        setContentView(ScrollView(this).apply {
            setBackgroundColor(Color.rgb(0x2c, 0x3a, 0x4a))
            addView(stolpec)
        })
    }

    private fun dp(v: Int): Int = (v * resources.displayMetrics.density + 0.5f).toInt()

    private fun minuta(ms: Long): Long = ms - ms % 60_000L

    private fun budilka(
        id: String, trainNo: String, smer: String, postaja: String, vr: Long,
        vlak: Boolean = true, zamudaS: Int? = null, zamudaObMs: Long = 0, stikObMs: Long = zamudaObMs,
        odzvonjeno: Boolean = false, tir: String? = null, dnevi: Int = 0, ugasnjena: Boolean = false,
    ) = Budilka(
        id = id, trainNo = trainNo, tripId = null,
        omrezje = if (vlak) "zeleznica" else "avtobus",
        postaja = postaja, stopSeq = 5, dan = Ponovitev.dan(vr), voznoredniMs = vr,
        minutPrej = 25, zbudi = true, dnevi = dnevi, ugasnjena = ugasnjena, smer = smer,
        zamudaS = zamudaS, zamudaObMs = zamudaObMs, stikObMs = stikObMs,
        odzvonjeno = odzvonjeno, tir = tir,
    )

    private fun odhod(
        vr: Long, kam: String, no: String, min: Int?, tir: String? = null, odpadla: Boolean = false,
    ) = Tabla.Odhod(
        ura = String.format("%tR", vr), kam = kam, trainNo = no, tripId = "t-$no",
        zamudaMin = min, razred = min?.let { Tabla.razred(it) }, prezgodaj = (min ?: 0) <= -1,
        tir = tir, odpadla = odpadla, voznoredniMs = vr,
    )

    /** Razred ponudnika, opis vzorca in izris za id. */
    private fun vzorec(kaj: String, stanje: Int, zdaj: Long): Triple<String, String, (Int) -> RemoteViews> {
        val m = minuta(zdaj)
        val jutri = run {
            val k = java.util.Calendar.getInstance()
            k.timeInMillis = zdaj
            k.add(java.util.Calendar.DAY_OF_YEAR, 1)
            k.set(java.util.Calendar.HOUR_OF_DAY, 6); k.set(java.util.Calendar.MINUTE, 57)
            k.set(java.util.Calendar.SECOND, 0); k.set(java.util.Calendar.MILLISECOND, 0)
            k.timeInMillis
        }
        return when (kaj) {
            "odstevanje" -> {
                val vzorci = listOf(
                    "šteje, +4, tir 3" to budilka("a", "LPV 2010", "Koper", "Ljubljana",
                        m + 18 * 60_000L, zamudaS = 240, zamudaObMs = zdaj - 30_000L,
                        odzvonjeno = true, tir = "3"),
                    "daleč, nepreverjena" to budilka("b", "LPV 2010", "Koper", "Ljubljana", jutri),
                    "avtobus, 2 min prej" to budilka("c", "LPP 6", "Črnuče", "Bavarski dvor",
                        m + 9 * 60_000L, vlak = false, zamudaS = -120,
                        zamudaObMs = zdaj - 30_000L, odzvonjeno = true),
                    "zastarela po zvonjenju" to budilka("d", "LPV 2010", "Koper", "Ljubljana",
                        m + 3 * 60_000L, zamudaS = 240, zamudaObMs = zdaj - 20 * 60_000L,
                        stikObMs = zdaj - 20 * 60_000L, odzvonjeno = true),
                    "odhod zdaj" to budilka("e", "IC 502", "Maribor", "Ljubljana",
                        m - 60_000L + 40_000L, zamudaS = 0, zamudaObMs = zdaj - 20_000L,
                        odzvonjeno = true, tir = "1"),
                    "ni budilke" to null,
                )
                val (opis, b) = vzorci[stanje.coerceIn(vzorci.indices)]
                Triple(Widget::class.java.name, opis) { id -> Widget.pogled(this, id, b, zdaj) }
            }
            "budilke" -> {
                val vse = listOf(
                    budilka("1", "LPV 2010", "Koper", "Ljubljana", jutri, dnevi = Ponovitev.DELAVNIKI),
                    budilka("2", "LPP 6", "Črnuče", "Bavarski dvor", jutri + 50 * 60_000L,
                        vlak = false, ugasnjena = true),
                    budilka("3", "IC 502", "Maribor", "Ljubljana", jutri + 10 * 3600_000L,
                        dnevi = Ponovitev.VSI),
                    budilka("4", "Arriva", "Bohinj", "Kranj", jutri + 11 * 3600_000L,
                        vlak = false, dnevi = Ponovitev.VIKEND),
                    budilka("5", "LP 2433", "Kranj", "Ljubljana", jutri + 12 * 3600_000L,
                        ugasnjena = true),
                )
                val vzorci = listOf(
                    "tri" to vse.take(3),
                    "ena ugasnjena" to listOf(vse[1]),
                    "pet" to vse,
                    "nobene" to emptyList(),
                    "zazvonila" to listOf(budilka("z", "LPV 2010", "Koper", "Ljubljana",
                        m + 12 * 60_000L, zamudaS = 180, zamudaObMs = zdaj - 30_000L,
                        odzvonjeno = true)) + vse.take(2),
                )
                val (opis, b) = vzorci[stanje.coerceIn(vzorci.indices)]
                Triple(WidgetBudilke::class.java.name, opis) { id -> WidgetBudilke.pogled(this, id, b, zdaj) }
            }
            else -> {
                val vlak = Tabla.Nastavitev("Ljubljana", "zeleznica")
                val bus = Tabla.Nastavitev("Bavarski dvor", "avtobus", "s1", "→ Razstavišče · Kolodvor")
                val vrstice = listOf(
                    odhod(m + 4 * 60_000L, "Koper", "LPV 2010", 4, tir = "3"),
                    odhod(m + 11 * 60_000L, "Maribor", "IC 502", 0, tir = "1"),
                    odhod(m + 19 * 60_000L, "Kamnik", "LP 2610", null, odpadla = true),
                    odhod(m + 25 * 60_000L, "Kranj", "LP 2433", null),
                    odhod(m + 33 * 60_000L, "Zagreb", "EC 212", 17, tir = "7"),
                    odhod(m + 41 * 60_000L, "Grosuplje", "LP 2210", 2),
                    odhod(m + 52 * 60_000L, "Jesenice", "LPV 2410", null),
                )
                val busi = listOf(
                    odhod(m + 2 * 60_000L, "Črnuče", "LPP 6", -2),
                    odhod(m + 6 * 60_000L, "Bežigrad", "LPP 1", 3),
                    odhod(m + 9 * 60_000L, "Ježica", "LPP 6B", null),
                    odhod(m + 14 * 60_000L, "Tomačevo", "LPP 27", 8),
                )
                val smeri = listOf(Tabla.Smer("s1", "→ Razstavišče · Kolodvor"),
                    Tabla.Smer("s2", "→ Tivoli"))
                val vzorci = listOf(
                    Triple("vlak, ovira", vlak, Tabla.Stanje(vrstice, zdaj - 3 * 60_000L,
                        "Med Ljubljano in Kamnikom nadomestni avtobus.")),
                    Triple("avtobus, stran ceste", bus, Tabla.Stanje(busi, zdaj - 60_000L, smeri = smeri)),
                    Triple("star podatek", vlak, Tabla.Stanje(vrstice, zdaj - 41 * 60_000L)),
                    Triple("prazna", vlak, Tabla.Stanje(emptyList(), zdaj - 60_000L)),
                    Triple("brez postaje", null, null),
                    Triple("brez podlage", vlak.copy(videz = Izris.Videz.BREZ),
                        Tabla.Stanje(vrstice, zdaj - 60_000L)),
                )
                val (opis, n, st) = vzorci[stanje.coerceIn(vzorci.indices)]
                Triple(WidgetTabla::class.java.name, opis) { id -> WidgetTabla.pogled(this, id, n, st, zdaj) }
            }
        }
    }
}
