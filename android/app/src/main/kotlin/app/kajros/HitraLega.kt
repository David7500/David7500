package app.kajros

import android.content.Context
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Looper
import android.os.SystemClock
import org.json.JSONObject

/**
 * Prva lega za stran (most 8), preden se oglasi GPS.
 *
 * `navigator.geolocation` v WebView posluša en sam ponudnik in z
 * `enableHighAccuracy` je to GPS: iz hladnega stanja desetine sekund, pod
 * streho pogosto nikoli. Zato tu, kar WebView ne zna:
 * * zadnja znana lega **vseh** ponudnikov, tudi tista, ki jo je pustila druga
 *   aplikacija (navigacija pred dvema minutama) -- takoj, brez čakanja;
 * * sprotna omrežna lega (`network`, `fused`), kjer jo telefon ima: stolpi in
 *   WiFi odgovorijo v sekundi ali dveh. Razgooglan telefon teh ponudnikov nima.
 *
 * GPS ostane WebView-u: dva poslušalca GPS bi bila samo dvojna baterija. Stran
 * sama presodi, ali je lega dovolj sveža in natančna (`common.js`, `virLege`):
 * tu gre ven vse, s starostjo, tudi stara. Starost je iz monotone ure, ne iz
 * `Location.time`, ki je po telefonih različno zanesljiv.
 *
 * Teče samo, kadar je stran vidna in lego rabi: [ustavi] pokliče stran ob
 * skritju, dejavnost pa v vsakem primeru ob `onPause`.
 */
class HitraLega(private val c: Context, private val oddaj: (String) -> Unit) {

    private companion object {
        /** Stran rabi prvo lego in izboljšavo, ne sledenja: tega ima od GPS. */
        const val KORAK_MS = 2000L
        const val FUSED = "fused"     // `LocationManager.FUSED_PROVIDER` je šele API 31
    }

    private val lm = c.getSystemService(LocationManager::class.java)
    private var tece = false

    // Pred Androidom 11 so te metode abstraktne, ne privzete.
    private val poslusalec = object : LocationListener {
        override fun onLocationChanged(l: Location) = poslji(l)
        @Deprecated("Android 10 in manj")
        override fun onStatusChanged(ponudnik: String?, stanje: Int, dodatki: Bundle?) = Unit
        override fun onProviderEnabled(ponudnik: String) = Unit
        override fun onProviderDisabled(ponudnik: String) = Unit
    }

    /** Vse na glavni niti. Dovoljenja morda ni (več): potem molči, kot lega brez signala. */
    fun zacni() {
        val m = lm ?: return
        if (tece || !DeljenjeStoritev.smeLego(c)) return
        tece = true
        try {
            val vsi = m.getProviders(true)
            vsi.forEach { p -> m.getLastKnownLocation(p)?.let(::poslji) }
            for (p in listOf(LocationManager.NETWORK_PROVIDER, FUSED)) {
                if (p in vsi) m.requestLocationUpdates(p, KORAK_MS, 0f, poslusalec, Looper.getMainLooper())
            }
        } catch (e: SecurityException) {
            ustavi()
        } catch (e: IllegalArgumentException) {
            // Ponudnik je med branjem seznama izginil; GPS strani teče naprej.
            ustavi()
        }
    }

    fun ustavi() {
        if (!tece) return
        tece = false
        lm?.removeUpdates(poslusalec)
    }

    private fun poslji(l: Location) {
        if (!l.hasAccuracy()) return
        val starostMs = (SystemClock.elapsedRealtimeNanos() - l.elapsedRealtimeNanos) / 1_000_000
        oddaj(JSONObject()
            .put("lat", l.latitude).put("lon", l.longitude)
            .put("acc", l.accuracy.toDouble())
            .put("starost_ms", maxOf(0L, starostMs))
            .toString())
    }
}
