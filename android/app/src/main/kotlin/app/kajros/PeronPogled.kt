package app.kajros

import android.annotation.SuppressLint
import android.content.Context
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.VelocityTracker
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Prizor zvonjenja: vozilo potegneš do sebe in budilka se ustavi.
 *
 * Poteg šteje samo, če se začne na vozilu (z rezervo za prst) -- dlan, žep ali
 * dotik mimo ga ne premaknejo. Kdaj je dovolj, odloči [Peron.ustavi].
 *
 * Kdor uporablja bralnik zaslona, vozila ne vidi in ga ne more vleči: zanj
 * je prizor gumb, ki ga ustavi z dvojnim dotikom. Gumb „Ustavi“ je tudi v
 * obvestilu, ki ostane v vrstici stanja ves čas zvonjenja.
 */
class PeronPogled(c: Context, atributi: AttributeSet? = null) : GLSurfaceView(c, atributi) {

    private var risar: PeronRisar? = null
    /**
     * Poteg je uspel. Zvonjenje se ustavi takoj, ne šele, ko vozilo pripelje:
     * spuščeno pelje še sekundo ali dve, in toliko glasnega zvonjenja po
     * opravljeni kretnji bi bilo kazen.
     */
    var obUstavitvi: (() -> Unit)? = null
    private var sled: VelocityTracker? = null
    private var x0 = 0f
    private var p0 = 0f
    private var cetrtina = 0
    private val gostota = resources.displayMetrics.density
    private val tresljaj = c.getSystemService(Vibrator::class.java)

    fun zacni(r: PeronRisar) {
        setEGLContextClientVersion(2)
        setEGLConfigChooser(PeronRisar.Nastavitev())
        preserveEGLContextOnPause = true
        setRenderer(r)
        risar = r
    }

    private fun naVozilu(x: Float, y: Float): Boolean {
        val o = risar?.okvir ?: return false
        val rez = 44f * gostota
        return x >= o[0] - rez && x <= o[2] + rez && y >= o[1] - rez && y <= o[3] + rez
    }

    // Dotik ni klik: budilko ustavi samo poteg. Pot za bralnik zaslona je
    // `performAccessibilityAction`, ne `performClick`.
    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(e: MotionEvent): Boolean {
        val r = risar ?: return false
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                if (r.koncano || !naVozilu(e.x, e.y)) return false
                parent?.requestDisallowInterceptTouchEvent(true)
                x0 = e.x
                p0 = r.p
                cetrtina = Peron.cetrtina(p0)
                r.vlecem = true
                sled?.recycle()
                sled = VelocityTracker.obtain().also { it.addMovement(e) }
            }
            MotionEvent.ACTION_MOVE -> {
                sled?.addMovement(e)
                r.cilj = cilj(e)
                // Ob vsaki četrtini poti kratek tresljaj, kot zobnik.
                val c4 = Peron.cetrtina(r.cilj)
                if (c4 != cetrtina) { cetrtina = c4; brni(8) }
            }
            MotionEvent.ACTION_UP -> {
                val s = sled
                s?.addMovement(e)
                s?.computeCurrentVelocity(1)
                val hitrost = (s?.xVelocity ?: 0f) / gostota
                // Dvig nosi zadnjo lego prsta; zadnji premik je lahko krajši.
                val ustavi = Peron.ustavi(cilj(e), hitrost)
                r.cilj = if (ustavi) 1f else 0f
                r.vlecem = false
                konecSledi()
                if (ustavi) obUstavitvi?.invoke()
            }
            MotionEvent.ACTION_CANCEL -> {
                r.cilj = 0f
                r.vlecem = false
                konecSledi()
            }
        }
        return true
    }

    private fun cilj(e: MotionEvent): Float =
        (p0 + (e.x - x0) / (width * Peron.POT_DELEZ)).coerceIn(0f, 1f)

    private fun konecSledi() {
        sled?.recycle()
        sled = null
    }

    fun brni(ms: Long) {
        tresljaj?.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE))
    }

    override fun onInitializeAccessibilityNodeInfo(info: AccessibilityNodeInfo) {
        super.onInitializeAccessibilityNodeInfo(info)
        info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_CLICK)
    }

    override fun performAccessibilityAction(akcija: Int, argumenti: Bundle?): Boolean {
        val r = risar
        if (akcija == AccessibilityNodeInfo.ACTION_CLICK && r != null && !r.koncano) {
            r.vlecem = false
            r.cilj = 1f
            obUstavitvi?.invoke()
            return true
        }
        return super.performAccessibilityAction(akcija, argumenti)
    }
}
