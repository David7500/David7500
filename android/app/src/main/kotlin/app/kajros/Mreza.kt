package app.kajros

import kotlin.math.cos
import kotlin.math.sin

/**
 * Toga pretvorba v prostoru: x' = L·x + T. Samo vrtenja, premiki in zrcaljenje,
 * zato se normale pretvorijo z isto matriko L in ostanejo enotske.
 */
class Afina(private val l: FloatArray, private val t: FloatArray) {

    operator fun times(b: Afina): Afina {
        val r = FloatArray(9)
        for (i in 0..2) for (j in 0..2) {
            r[i * 3 + j] = l[i * 3] * b.l[j] + l[i * 3 + 1] * b.l[3 + j] + l[i * 3 + 2] * b.l[6 + j]
        }
        val tt = FloatArray(3) { i ->
            l[i * 3] * b.t[0] + l[i * 3 + 1] * b.t[1] + l[i * 3 + 2] * b.t[2] + t[i]
        }
        return Afina(r, tt)
    }

    fun tocka(x: Float, y: Float, z: Float, izhod: FloatArray, o: Int = 0) {
        izhod[o] = l[0] * x + l[1] * y + l[2] * z + t[0]
        izhod[o + 1] = l[3] * x + l[4] * y + l[5] * z + t[1]
        izhod[o + 2] = l[6] * x + l[7] * y + l[8] * z + t[2]
    }

    fun smer(x: Float, y: Float, z: Float, izhod: FloatArray, o: Int = 0) {
        izhod[o] = l[0] * x + l[1] * y + l[2] * z
        izhod[o + 1] = l[3] * x + l[4] * y + l[5] * z
        izhod[o + 2] = l[6] * x + l[7] * y + l[8] * z
    }

    /** Matrika 4×4 za OpenGL (po stolpcih). */
    fun gl(): FloatArray = floatArrayOf(
        l[0], l[3], l[6], 0f,
        l[1], l[4], l[7], 0f,
        l[2], l[5], l[8], 0f,
        t[0], t[1], t[2], 1f,
    )

    companion object {
        val ENOTA = Afina(floatArrayOf(1f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 1f), floatArrayOf(0f, 0f, 0f))

        fun premik(x: Float, y: Float, z: Float) =
            Afina(floatArrayOf(1f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 1f), floatArrayOf(x, y, z))

        fun okoliX(a: Float): Afina {
            val c = cos(a); val s = sin(a)
            return Afina(floatArrayOf(1f, 0f, 0f, 0f, c, -s, 0f, s, c), floatArrayOf(0f, 0f, 0f))
        }

        fun okoliY(a: Float): Afina {
            val c = cos(a); val s = sin(a)
            return Afina(floatArrayOf(c, 0f, s, 0f, 1f, 0f, -s, 0f, c), floatArrayOf(0f, 0f, 0f))
        }

        fun okoliZ(a: Float): Afina {
            val c = cos(a); val s = sin(a)
            return Afina(floatArrayOf(c, -s, 0f, s, c, 0f, 0f, 0f, 1f), floatArrayOf(0f, 0f, 0f))
        }

        /** Zrcalo čez ravnino x = 0 (zadnja kabina je zrcaljena sprednja). */
        val ZRCALO_X = Afina(floatArrayOf(-1f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 1f), floatArrayOf(0f, 0f, 0f))
    }
}

/** Barva iz zapisa 0xRRGGBB v tri števila 0..1, brez pretvorbe (kot three.js r128). */
fun barva(rgb: Int): FloatArray = floatArrayOf(
    ((rgb shr 16) and 0xff) / 255f, ((rgb shr 8) and 0xff) / 255f, (rgb and 0xff) / 255f)

/**
 * Trikotniki osvetljenih ploskev: lega, normala, barva in sij po oglišču
 * ([NA_OGLISCE] števil). Brez indeksov: največja mreža ima nekaj deset tisoč
 * oglišč in kratke indekse bi presegla.
 *
 * Gradniki imajo mere v metrih in sledijo prototipu (`design/budilka/`), da
 * je mogoče prizor primerjati s three.js ploskev za ploskvijo.
 */
class Mreza {

    companion object {
        const val NA_OGLISCE = 12
    }

    private var a = FloatArray(NA_OGLISCE * 1024)
    var dolzina = 0
        private set
    val oglisc: Int get() = dolzina / NA_OGLISCE

    /** Pretvorba, ki velja za vse, kar se doda; spremeni jo [pod]. */
    var pretvorba: Afina = Afina.ENOTA
        private set

    /** Najmanjši in največji x, y, z vseh dodanih oglišč (po pretvorbi). */
    val meje = floatArrayOf(Float.MAX_VALUE, Float.MAX_VALUE, Float.MAX_VALUE,
        -Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE)

    private val p = FloatArray(3)
    private val n = FloatArray(3)

    fun podatki(): FloatArray = a.copyOf(dolzina)

    fun pod(dodatna: Afina, blok: () -> Unit) {
        val prej = pretvorba
        pretvorba = prej * dodatna
        try { blok() } finally { pretvorba = prej }
    }

    private fun oglisce(x: Float, y: Float, z: Float, nx: Float, ny: Float, nz: Float,
                        b: FloatArray, s: FloatArray) {
        if (dolzina + NA_OGLISCE > a.size) a = a.copyOf(a.size * 2)
        pretvorba.tocka(x, y, z, p)
        pretvorba.smer(nx, ny, nz, n)
        for (i in 0..2) {
            if (p[i] < meje[i]) meje[i] = p[i]
            if (p[i] > meje[3 + i]) meje[3 + i] = p[i]
        }
        a[dolzina++] = p[0]; a[dolzina++] = p[1]; a[dolzina++] = p[2]
        a[dolzina++] = n[0]; a[dolzina++] = n[1]; a[dolzina++] = n[2]
        a[dolzina++] = b[0]; a[dolzina++] = b[1]; a[dolzina++] = b[2]
        a[dolzina++] = s[0]; a[dolzina++] = s[1]; a[dolzina++] = s[2]
    }

    /** Štirikotnik a-b-c-d (v smeri, ki jo vidi normala) kot dva trikotnika. */
    fun stirikotnik(q: FloatArray, nx: Float, ny: Float, nz: Float, b: FloatArray, s: FloatArray) {
        for (i in intArrayOf(0, 1, 2, 0, 2, 3)) {
            oglisce(q[i * 3], q[i * 3 + 1], q[i * 3 + 2], nx, ny, nz, b, s)
        }
    }

    /** Škatla po robovih: x0..x1, y0..y1, z0..z1 (metri). Edini gradnik večine sveta. */
    fun skatla(x0: Float, x1: Float, y0: Float, y1: Float, z0: Float, z1: Float,
               rgb: Int, sij: Int = 0) {
        val b = barva(rgb); val s = barva(sij)
        stirikotnik(floatArrayOf(x1, y0, z1, x1, y0, z0, x1, y1, z0, x1, y1, z1), 1f, 0f, 0f, b, s)
        stirikotnik(floatArrayOf(x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0), -1f, 0f, 0f, b, s)
        stirikotnik(floatArrayOf(x0, y1, z1, x1, y1, z1, x1, y1, z0, x0, y1, z0), 0f, 1f, 0f, b, s)
        stirikotnik(floatArrayOf(x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1), 0f, -1f, 0f, b, s)
        stirikotnik(floatArrayOf(x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1), 0f, 0f, 1f, b, s)
        stirikotnik(floatArrayOf(x1, y0, z0, x0, y0, z0, x0, y1, z0, x1, y1, z0), 0f, 0f, -1f, b, s)
    }

    /**
     * Konveksen mnogokotnik v ravnini (x, y), izvlečen od z0 do z1.
     * [xy] = x0, y0, x1, y1, … v nasprotni smeri urinega kazalca.
     */
    fun izvlek(xy: FloatArray, z0: Float, z1: Float, rgb: Int) {
        val b = barva(rgb); val s = barva(0)
        val k = xy.size / 2
        for (i in 1 until k - 1) {
            oglisce(xy[0], xy[1], z1, 0f, 0f, 1f, b, s)
            oglisce(xy[i * 2], xy[i * 2 + 1], z1, 0f, 0f, 1f, b, s)
            oglisce(xy[i * 2 + 2], xy[i * 2 + 3], z1, 0f, 0f, 1f, b, s)
            oglisce(xy[0], xy[1], z0, 0f, 0f, -1f, b, s)
            oglisce(xy[i * 2 + 2], xy[i * 2 + 3], z0, 0f, 0f, -1f, b, s)
            oglisce(xy[i * 2], xy[i * 2 + 1], z0, 0f, 0f, -1f, b, s)
        }
        for (i in 0 until k) {
            val j = (i + 1) % k
            val x0 = xy[i * 2]; val y0 = xy[i * 2 + 1]; val x1 = xy[j * 2]; val y1 = xy[j * 2 + 1]
            val dx = x1 - x0; val dy = y1 - y0
            val d = kotlin.math.sqrt(dx * dx + dy * dy)
            if (d < 1e-6f) continue
            stirikotnik(floatArrayOf(x0, y0, z0, x1, y1, z0, x1, y1, z1, x0, y0, z1),
                dy / d, -dx / d, 0f, b, s)
        }
    }

    /** Valj z osjo z, središče v izhodišču, gladke stranice (kot three.js). */
    fun valj(r: Float, visina: Float, odsekov: Int, rgb: Int) {
        val b = barva(rgb); val s = barva(0)
        val h = visina / 2
        for (i in 0 until odsekov) {
            val a0 = (i.toFloat() / odsekov) * 2f * Math.PI.toFloat()
            val a1 = ((i + 1).toFloat() / odsekov) * 2f * Math.PI.toFloat()
            val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
            // plašč
            oglisce(r * c0, r * s0, -h, c0, s0, 0f, b, s)
            oglisce(r * c1, r * s1, -h, c1, s1, 0f, b, s)
            oglisce(r * c1, r * s1, h, c1, s1, 0f, b, s)
            oglisce(r * c0, r * s0, -h, c0, s0, 0f, b, s)
            oglisce(r * c1, r * s1, h, c1, s1, 0f, b, s)
            oglisce(r * c0, r * s0, h, c0, s0, 0f, b, s)
            // pokrova
            oglisce(0f, 0f, h, 0f, 0f, 1f, b, s)
            oglisce(r * c0, r * s0, h, 0f, 0f, 1f, b, s)
            oglisce(r * c1, r * s1, h, 0f, 0f, 1f, b, s)
            oglisce(0f, 0f, -h, 0f, 0f, -1f, b, s)
            oglisce(r * c1, r * s1, -h, 0f, 0f, -1f, b, s)
            oglisce(r * c0, r * s0, -h, 0f, 0f, -1f, b, s)
        }
    }
}

/**
 * Neosvetljene ploskve (napis, številčnica, hribi): lega in koordinata
 * teksture, 5 števil na oglišče. Barvo in teksturo da risar.
 */
class Ploskev {
    private var a = FloatArray(5 * 256)
    var dolzina = 0
        private set
    val oglisc: Int get() = dolzina / 5
    private val p = FloatArray(3)

    fun podatki(): FloatArray = a.copyOf(dolzina)

    fun oglisce(t: Afina, x: Float, y: Float, z: Float, u: Float, v: Float) {
        if (dolzina + 5 > a.size) a = a.copyOf(a.size * 2)
        t.tocka(x, y, z, p)
        a[dolzina++] = p[0]; a[dolzina++] = p[1]; a[dolzina++] = p[2]
        a[dolzina++] = u; a[dolzina++] = v
    }

    /** Pravokotnik v ravnini (x, y), obrnjen proti +z; v = 0 zgoraj. */
    fun pravokotnik(t: Afina, x0: Float, x1: Float, y0: Float, y1: Float, z: Float = 0f) {
        oglisce(t, x0, y0, z, 0f, 1f); oglisce(t, x1, y0, z, 1f, 1f); oglisce(t, x1, y1, z, 1f, 0f)
        oglisce(t, x0, y0, z, 0f, 1f); oglisce(t, x1, y1, z, 1f, 0f); oglisce(t, x0, y1, z, 0f, 0f)
    }

    /** Krog ali kolobar (r0 > 0) v ravnini (x, y); tekstura čez krog polmera r1. */
    fun kolobar(t: Afina, r0: Float, r1: Float, odsekov: Int, z: Float = 0f) {
        for (i in 0 until odsekov) {
            val a0 = (i.toFloat() / odsekov) * 2f * Math.PI.toFloat()
            val a1 = ((i + 1).toFloat() / odsekov) * 2f * Math.PI.toFloat()
            fun o(r: Float, a: Float) = oglisce(t, r * cos(a), r * sin(a), z,
                0.5f + 0.5f * r / r1 * cos(a), 0.5f - 0.5f * r / r1 * sin(a))
            if (r0 <= 0f) {
                o(0f, a0); o(r1, a0); o(r1, a1)
            } else {
                o(r0, a0); o(r1, a0); o(r1, a1)
                o(r0, a0); o(r1, a1); o(r0, a1)
            }
        }
    }
}
