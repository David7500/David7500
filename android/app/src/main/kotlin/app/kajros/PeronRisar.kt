package app.kajros

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader
import android.graphics.Typeface
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.GLUtils
import android.opengl.Matrix
import android.os.SystemClock
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.util.Calendar
import javax.microedition.khronos.egl.EGL10
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.egl.EGLDisplay
import javax.microedition.khronos.opengles.GL10
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.exp
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Riše [Peron] z OpenGL ES 2.0, brez knjižnic.
 *
 * Osvetlitev je ista kot v prototipu (three.js r128, `MeshLambertMaterial`):
 * Lambert po ogliščih z nebesno, mesečno, zorno in eno točkasto lučjo, sij
 * ploskve prištet, megla po globini. Barve so zapisane kot v prototipu in se
 * ne pretvarjajo, ker jih tudi three.js r128 ni.
 *
 * Napredek [p] (0..1) teče v tej niti: vozilo sledi [cilj] z vzmetjo, kot v
 * prototipu. Pogled piše [cilj] in [vlecem], risar ob prihodu pokliče
 * [obPrihodu] (v svoji niti) in sproti objavlja zaslonski [okvir] vozila, da
 * pogled ve, ali se je poteg začel na njem.
 */
class PeronRisar(
    private val prizor: Peron,
    private val postaja: String,
    /** Gostota zaslona: zvezde so velike v točkah, ne v metrih. */
    private val gostota: Float,
    /** Sistemske animacije ugasnjene: brez vabila in utripanja. */
    private val zmanjsano: Boolean,
    private val obPrihodu: () -> Unit,
) : GLSurfaceView.Renderer {

    @Volatile var cilj = 0f
    @Volatile var vlecem = false
    @Volatile var glasno = false

    @Volatile var p = 0f
        private set
    @Volatile var koncano = false
        private set
    /** Vozilo na zaslonu v slikovnih točkah prizora: levo, zgoraj, desno, spodaj. */
    @Volatile var okvir = floatArrayOf(0f, 0f, 0f, 0f)
        private set

    private var koncanoOb = 0L
    private var prej = 0L
    private var dih = 0f
    private var sirina = 1
    private var visina = 1

    private val proj = FloatArray(16)
    private val pogled = FloatArray(16)
    private val vp = FloatArray(16)
    private val m = FloatArray(16)
    private val mvp = FloatArray(16)
    private val pomoc = FloatArray(16)

    private var osvetljeno = 0
    private var osnovno = 0
    private var nebo = 0

    private class Vbo(val id: Int, val oglisc: Int)
    private lateinit var svet: Vbo
    private lateinit var vozilo: Vbo
    private lateinit var okna: Vbo
    private lateinit var vrata: Vbo
    private lateinit var koloL: Vbo
    private lateinit var koloD: Vbo
    private lateinit var napis: Vbo
    private lateinit var stevilcnica: Vbo
    private lateinit var obroc: Vbo
    private lateinit var kazalecH: Vbo
    private lateinit var kazalecM: Vbo
    private lateinit var kazalecS: Vbo
    private lateinit var zvezde: Vbo
    private lateinit var nebesniPravokotnik: Vbo
    private val sijPodatki = FloatArray(6 * 5 * 8)
    private val sijMedpomnilnik: FloatBuffer = medpomnilnik(sijPodatki.size)
    private var sijVbo = 0

    private var teksNapis = 0
    private var teksStevilcnica = 0
    private var teksSij = 0

    // ------------------------------------------------------------ življenje

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        osvetljeno = program(OSVETLJENO_V, OSVETLJENO_F)
        osnovno = program(OSNOVNO_V, OSNOVNO_F)
        nebo = program(NEBO_V, NEBO_F)
        svet = vbo(prizor.svet.podatki(), Mreza.NA_OGLISCE)
        vozilo = vbo(prizor.vozilo.podatki(), Mreza.NA_OGLISCE)
        okna = vbo(prizor.okna.podatki(), Mreza.NA_OGLISCE)
        vrata = vbo(prizor.vrataMreza.podatki(), Mreza.NA_OGLISCE)
        koloL = vbo(prizor.koloLevo.podatki(), Mreza.NA_OGLISCE)
        koloD = vbo(prizor.koloDesno.podatki(), Mreza.NA_OGLISCE)
        napis = vbo(prizor.tablaNapis.podatki(), 5)
        stevilcnica = vbo(prizor.uraStevilcnica.podatki(), 5)
        obroc = vbo(prizor.uraObroc.podatki(), 5)
        kazalecH = vbo(prizor.kazalecUre.podatki(), 5)
        kazalecM = vbo(prizor.kazalecMinut.podatki(), 5)
        kazalecS = vbo(prizor.kazalecSekund.podatki(), 5)
        zvezde = vbo(prizor.zvezde, 3)
        nebesniPravokotnik = vbo(floatArrayOf(-1f, -1f, 1f, -1f, 1f, 1f, -1f, -1f, 1f, 1f, -1f, 1f), 2)
        sijVbo = IntArray(1).also { GLES20.glGenBuffers(1, it, 0) }[0]

        teksNapis = tekstura(napisBitmap())
        teksStevilcnica = tekstura(stevilcnicaBitmap())
        teksSij = tekstura(sijBitmap())

        GLES20.glDisable(GLES20.GL_CULL_FACE)
        GLES20.glClearColor(0f, 0f, 0f, 1f)
        prej = SystemClock.uptimeMillis()
    }

    override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
        sirina = maxOf(1, w)
        visina = maxOf(1, h)
        GLES20.glViewport(0, 0, sirina, visina)
        Matrix.perspectiveM(proj, 0, Peron.ZORNI_KOT, sirina.toFloat() / visina, Peron.BLIZU, Peron.DALEC)
        val k = Peron.KAMERA
        val c = Peron.POGLED
        Matrix.setLookAtM(pogled, 0, k[0], k[1], k[2], c[0], c[1], c[2], 0f, 1f, 0f)
        Matrix.multiplyMM(vp, 0, proj, 0, pogled, 0)
    }

    override fun onDrawFrame(gl: GL10?) {
        val zdaj = SystemClock.uptimeMillis()
        val dt = min(0.05f, (zdaj - prej) / 1000f)
        prej = zdaj
        premakni(zdaj, dt)

        val x = prizor.xVozila(p)
        izracunajOkvir(x)
        // Zora pri Peronu samo nakaže: tretjina neba ob prihodu.
        val zora = p * 0.3f
        val t = if (koncano) min(1f, (zdaj - koncanoOb) / 700f) else 0f
        val luc = maxOf(t, if (p > 0.6f) (p - 0.6f) / 0.4f * 0.35f else 0f)

        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        narisiNebo(zora)

        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        GLES20.glDepthMask(true)
        GLES20.glDisable(GLES20.GL_BLEND)
        pripraviOsvetljeno(zora)
        osvetljena(svet, null)
        Matrix.setIdentityM(m, 0)
        Matrix.translateM(m, 0, x, 0f, 0f)
        osvetljena(vozilo, m)
        // Okna: ena barva za vse, od temnega stekla do toplo prižganih.
        val o0 = barva(Peron.STEKLO); val o1 = barva(Peron.OKNO_LUC); val s1 = barva(Peron.OKNO_SIJ)
        GLES20.glUniform1f(u(osvetljeno, "uEnotna"), 1f)
        GLES20.glUniform3f(u(osvetljeno, "uBarva"), mesaj(o0[0], o1[0], luc), mesaj(o0[1], o1[1], luc), mesaj(o0[2], o1[2], luc))
        GLES20.glUniform3f(u(osvetljeno, "uSij"), s1[0] * luc, s1[1] * luc, s1[2] * luc)
        osvetljena(okna, m)
        GLES20.glUniform1f(u(osvetljeno, "uEnotna"), 0f)
        // Na cilju se vrata odprejo -- vstopi.
        for (v in prizor.vrata) {
            Matrix.setIdentityM(pomoc, 0)
            Matrix.translateM(pomoc, 0, x + v[0] - t * 0.65f, 0f, v[1])
            osvetljena(vrata, pomoc)
        }
        val pot = x - prizor.zacetek
        for (k in prizor.kolesa) {
            Matrix.setIdentityM(pomoc, 0)
            Matrix.translateM(pomoc, 0, x + k.x, k.r, k.z)
            Matrix.rotateM(pomoc, 0, Math.toDegrees((-pot / k.r).toDouble()).toFloat(), 0f, 0f, 1f)
            osvetljena(if (k.z < 0) koloL else koloD, pomoc)
        }

        narisiTabloInUro()
        narisiZvezde(zora)
        narisiSij(x, zdaj)
    }

    /** Vozilo sledi prstu z vzmetjo; spuščeno se vrne ali pripelje do konca. */
    private fun premakni(zdaj: Long, dt: Float) {
        if (koncano) return
        val vleka = vlecem
        val c = cilj
        val k = if (vleka) 18f else 5f
        var q = p + (c - p) * (1f - exp(-k * dt))
        if (abs(c - q) < 0.0005f) q = c
        // Vabilo: vozilo se vsake 3 s rahlo premakne naprej.
        if (!vleka && c == 0f && q < 0.03f && !zmanjsano) {
            dih += dt
            val f = (dih % 3f) / 3f
            q = if (f < 0.2f) sin(f / 0.2f * PI.toFloat()) * 0.02f else 0f
        }
        p = q
        if (!vleka && q >= 0.999f && c == 1f) {
            p = 1f
            koncano = true
            koncanoOb = zdaj
            obPrihodu()
        }
    }

    private val oglisce = FloatArray(4)
    private val izhod = FloatArray(4)

    private fun izracunajOkvir(x: Float) {
        val mj = prizor.vozilo.meje
        var x0 = Float.MAX_VALUE; var y0 = Float.MAX_VALUE
        var x1 = -Float.MAX_VALUE; var y1 = -Float.MAX_VALUE
        for (i in 0 until 8) {
            oglisce[0] = x + mj[if (i and 1 == 0) 0 else 3]
            oglisce[1] = mj[if (i and 2 == 0) 1 else 4]
            oglisce[2] = mj[if (i and 4 == 0) 2 else 5]
            oglisce[3] = 1f
            Matrix.multiplyMV(izhod, 0, vp, 0, oglisce, 0)
            if (izhod[3] <= 0f) continue
            val zz = izhod[2] / izhod[3]
            if (zz > 1f) continue
            val sx = (izhod[0] / izhod[3] + 1f) / 2f * sirina
            val sy = (1f - izhod[1] / izhod[3]) / 2f * visina
            x0 = min(x0, sx); x1 = maxOf(x1, sx); y0 = min(y0, sy); y1 = maxOf(y1, sy)
        }
        okvir = floatArrayOf(x0, y0, x1, y1)
    }

    // ------------------------------------------------------------ deli prizora

    private fun narisiNebo(zora: Float) {
        GLES20.glDisable(GLES20.GL_DEPTH_TEST)
        GLES20.glDepthMask(false)
        GLES20.glUseProgram(nebo)
        GLES20.glUniform1f(u(nebo, "uZarja"), zora)
        val a = a(nebo, "aXy")
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, nebesniPravokotnik.id)
        GLES20.glEnableVertexAttribArray(a)
        GLES20.glVertexAttribPointer(a, 2, GLES20.GL_FLOAT, false, 8, 0)
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 6)
        GLES20.glDisableVertexAttribArray(a)
    }

    private fun pripraviOsvetljeno(zora: Float) {
        val pr = osvetljeno
        GLES20.glUseProgram(pr)
        GLES20.glUniformMatrix4fv(u(pr, "uVP"), 1, false, vp, 0)
        GLES20.glUniformMatrix4fv(u(pr, "uV"), 1, false, pogled, 0)
        uBarva(pr, "uNebo", 0x8d96b8, 0.62f)
        uBarva(pr, "uTla", 0x080a10, 0.62f)
        uSmer(pr, "uLunaSmer", -40f, 50f, 30f)
        uBarva(pr, "uLuna", 0xc7d2f5, 0.5f)
        uSmer(pr, "uZarjaSmer", 300f, 18f, -20f)
        uBarva(pr, "uZarja", 0xffb27a, zora * 0.9f)
        GLES20.glUniform3f(u(pr, "uLucPoz"), Peron.LUC[0], Peron.LUC[1], Peron.LUC[2])
        uBarva(pr, "uLuc", 0xffd9a6, 1.3f)
        GLES20.glUniform1f(u(pr, "uLucDoseg"), 70f)
        GLES20.glUniform1f(u(pr, "uLucUpad"), 1.6f)
        GLES20.glUniform2f(u(pr, "uMegla"), 30f, 330f)
        val n = barva(0x18233f); val z = barva(0xc4877c); val f = zora * 0.85f
        GLES20.glUniform3f(u(pr, "uMeglaBarva"), mesaj(n[0], z[0], f), mesaj(n[1], z[1], f), mesaj(n[2], z[2], f))
        GLES20.glUniform1f(u(pr, "uEnotna"), 0f)
    }

    private fun osvetljena(v: Vbo, model: FloatArray?) {
        val pr = osvetljeno
        if (model == null) Matrix.setIdentityM(m, 0)
        GLES20.glUniformMatrix4fv(u(pr, "uM"), 1, false, model ?: m, 0)
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, v.id)
        val k = Mreza.NA_OGLISCE * 4
        val imena = arrayOf("aPoz", "aNormala", "aBarva", "aSij")
        for ((i, ime) in imena.withIndex()) {
            val a = a(pr, ime)
            GLES20.glEnableVertexAttribArray(a)
            GLES20.glVertexAttribPointer(a, 3, GLES20.GL_FLOAT, false, k, i * 12)
        }
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, v.oglisc)
        for (ime in imena) GLES20.glDisableVertexAttribArray(a(pr, ime))
    }

    private fun narisiTabloInUro() {
        GLES20.glUseProgram(osnovno)
        GLES20.glUniform1f(u(osnovno, "uTocka"), 1f)
        osnovna(napis, vp, teksNapis, 0xffffff, 1f)
        osnovna(stevilcnica, vp, teksStevilcnica, 0xffffff, 1f)
        osnovna(obroc, vp, 0, 0x20242b, 1f)
        // Švicarska postajna ura: sekundni kazalec obkroži v 58,5 s in počaka na minuto.
        val c = Calendar.getInstance()
        val s = c.get(Calendar.SECOND) + c.get(Calendar.MILLISECOND) / 1000f
        val ss = min(1f, s / 58.5f) * 60f
        val mn = c.get(Calendar.MINUTE)
        val h = c.get(Calendar.HOUR) + mn / 60f
        kazalec(kazalecH, h / 12f * 360f, 0x16181c)
        kazalec(kazalecM, mn / 60f * 360f, 0x16181c)
        kazalec(kazalecS, ss / 60f * 360f, 0xc8102e)
    }

    private fun kazalec(v: Vbo, stopinj: Float, rgb: Int) {
        Matrix.setIdentityM(pomoc, 0)
        Matrix.translateM(pomoc, 0, Peron.URA[0], Peron.URA[1], Peron.URA[2])
        Matrix.rotateM(pomoc, 0, Math.toDegrees(prizor.uraKot.toDouble()).toFloat(), 0f, 1f, 0f)
        Matrix.rotateM(pomoc, 0, -stopinj, 0f, 0f, 1f)
        Matrix.multiplyMM(mvp, 0, vp, 0, pomoc, 0)
        osnovna(v, mvp, 0, rgb, 1f)
    }

    private fun osnovna(v: Vbo, mat: FloatArray, teks: Int, rgb: Int, alfa: Float,
                        nacin: Int = GLES20.GL_TRIANGLES) {
        val pr = osnovno
        GLES20.glUniformMatrix4fv(u(pr, "uMVP"), 1, false, mat, 0)
        val b = barva(rgb)
        GLES20.glUniform4f(u(pr, "uBarva"), b[0], b[1], b[2], alfa)
        GLES20.glUniform1f(u(pr, "uImaTeks"), if (teks != 0) 1f else 0f)
        if (teks != 0) {
            GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, teks)
            GLES20.glUniform1i(u(pr, "uTeks"), 0)
        }
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, v.id)
        val aPoz = a(pr, "aPoz")
        val aUv = a(pr, "aUv")
        GLES20.glEnableVertexAttribArray(aPoz)
        if (nacin == GLES20.GL_POINTS) {
            GLES20.glVertexAttribPointer(aPoz, 3, GLES20.GL_FLOAT, false, 12, 0)
            GLES20.glVertexAttrib2f(aUv, 0f, 0f)
        } else {
            GLES20.glVertexAttribPointer(aPoz, 3, GLES20.GL_FLOAT, false, 20, 0)
            GLES20.glEnableVertexAttribArray(aUv)
            GLES20.glVertexAttribPointer(aUv, 2, GLES20.GL_FLOAT, false, 20, 12)
        }
        GLES20.glDrawArrays(nacin, 0, v.oglisc)
        GLES20.glDisableVertexAttribArray(aPoz)
        GLES20.glDisableVertexAttribArray(aUv)
    }

    private fun narisiZvezde(zora: Float) {
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)
        GLES20.glDepthMask(false)
        GLES20.glUniform1f(u(osnovno, "uTocka"), 1.6f * min(2f, gostota))
        osnovna(zvezde, vp, 0, 0xcfd8ff, 0.8f * (1f - zora), GLES20.GL_POINTS)
    }

    /** Sij luči: kvadrat, vedno obrnjen proti kameri, prištet k sliki. */
    private fun narisiSij(x: Float, zdaj: Long) {
        // Žarometi utripajo hitreje, ko je glasno.
        val u = when {
            koncano || zmanjsano -> 1f
            glasno -> 0.55f + 0.45f * abs(sin(zdaj / 160f))
            else -> 0.85f + 0.15f * sin(zdaj / 900f)
        }
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_ONE, GLES20.GL_ONE)
        GLES20.glDepthMask(false)
        for (s in prizor.siji) {
            oglisce[0] = x + s.x; oglisce[1] = s.y; oglisce[2] = s.z; oglisce[3] = 1f
            Matrix.multiplyMV(izhod, 0, pogled, 0, oglisce, 0)
            val h = s.velikost / 2
            var i = 0
            for ((dx, dy, uu, vv) in KVADRAT) {
                sijPodatki[i++] = izhod[0] + dx * h; sijPodatki[i++] = izhod[1] + dy * h; sijPodatki[i++] = izhod[2]
                sijPodatki[i++] = uu; sijPodatki[i++] = vv
            }
            sijMedpomnilnik.position(0)
            sijMedpomnilnik.put(sijPodatki, 0, i).position(0)
            GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, sijVbo)
            GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER, i * 4, sijMedpomnilnik, GLES20.GL_STREAM_DRAW)
            val b = barva(s.barva)
            val o = if (s.zaromet) u else 1f
            GLES20.glUniformMatrix4fv(u(osnovno, "uMVP"), 1, false, proj, 0)
            GLES20.glUniform4f(u(osnovno, "uBarva"), b[0] * o, b[1] * o, b[2] * o, 1f)
            GLES20.glUniform1f(u(osnovno, "uImaTeks"), 1f)
            GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, teksSij)
            GLES20.glUniform1i(u(osnovno, "uTeks"), 0)
            val aPoz = a(osnovno, "aPoz")
            val aUv = a(osnovno, "aUv")
            GLES20.glEnableVertexAttribArray(aPoz)
            GLES20.glEnableVertexAttribArray(aUv)
            GLES20.glVertexAttribPointer(aPoz, 3, GLES20.GL_FLOAT, false, 20, 0)
            GLES20.glVertexAttribPointer(aUv, 2, GLES20.GL_FLOAT, false, 20, 12)
            GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 6)
            GLES20.glDisableVertexAttribArray(aPoz)
            GLES20.glDisableVertexAttribArray(aUv)
        }
        GLES20.glDepthMask(true)
        GLES20.glDisable(GLES20.GL_BLEND)
    }

    // ------------------------------------------------------------ teksture

    private fun napisBitmap(): Bitmap {
        val bm = Bitmap.createBitmap(1024, 256, Bitmap.Config.ARGB_8888)
        val c = Canvas(bm)
        c.drawColor(if (prizor.vlak) 0xff1d4f8a.toInt() else 0xff1f6b47.toInt())
        val okvir = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE; strokeWidth = 6f; color = 0x55ffffff
        }
        c.drawRect(10f, 10f, 1014f, 246f, okvir)
        val pero = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 120f
            typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
            textAlign = Paint.Align.CENTER
        }
        val sir = pero.measureText(postaja)
        if (sir > 940f) pero.textSize *= 940f / sir
        val fm = pero.fontMetrics
        c.drawText(postaja, 512f, 134f - (fm.ascent + fm.descent) / 2f, pero)
        return bm
    }

    private fun stevilcnicaBitmap(): Bitmap {
        val bm = Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888)
        val c = Canvas(bm)
        c.drawCircle(128f, 128f, 124f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xfff4f2ec.toInt() })
        val pero = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xff16181c.toInt() }
        for (i in 0 until 60) {
            val a = i / 60.0 * 2 * PI
            val d = if (i % 5 == 0) 26f else 9f
            pero.strokeWidth = if (i % 5 == 0) 9f else 3f
            val sa = sin(a).toFloat(); val ca = kotlin.math.cos(a).toFloat()
            c.drawLine(128f + sa * (116f - d), 128f - ca * (116f - d), 128f + sa * 116f, 128f - ca * 116f, pero)
        }
        return bm
    }

    /** Mehak krog za sij, sivinsko: svetlost je jakost, risar ga prišteje. */
    private fun sijBitmap(): Bitmap {
        val bm = Bitmap.createBitmap(64, 64, Bitmap.Config.ARGB_8888)
        val c = Canvas(bm)
        c.drawColor(Color.BLACK)
        c.drawRect(0f, 0f, 64f, 64f, Paint().apply {
            shader = RadialGradient(32f, 32f, 32f,
                intArrayOf(0xffffffff.toInt(), 0xff888888.toInt(), 0xff000000.toInt()),
                floatArrayOf(0f, 0.25f, 1f), Shader.TileMode.CLAMP)
        })
        return bm
    }

    // ------------------------------------------------------------ OpenGL

    private val lokacije = HashMap<String, Int>()
    private fun u(pr: Int, ime: String): Int =
        lokacije.getOrPut("$pr/$ime") { GLES20.glGetUniformLocation(pr, ime) }
    private fun a(pr: Int, ime: String): Int =
        lokacije.getOrPut("$pr@$ime") { GLES20.glGetAttribLocation(pr, ime) }

    private fun uBarva(pr: Int, ime: String, rgb: Int, k: Float) {
        val b = barva(rgb)
        GLES20.glUniform3f(u(pr, ime), b[0] * k, b[1] * k, b[2] * k)
    }

    private fun uSmer(pr: Int, ime: String, x: Float, y: Float, z: Float) {
        val d = sqrt(x * x + y * y + z * z)
        GLES20.glUniform3f(u(pr, ime), x / d, y / d, z / d)
    }

    private fun vbo(podatki: FloatArray, naOglisce: Int): Vbo {
        val id = IntArray(1).also { GLES20.glGenBuffers(1, it, 0) }[0]
        val fb = medpomnilnik(podatki.size).put(podatki).position(0) as FloatBuffer
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, id)
        GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER, podatki.size * 4, fb, GLES20.GL_STATIC_DRAW)
        return Vbo(id, podatki.size / naOglisce)
    }

    private fun tekstura(bm: Bitmap): Int {
        val id = IntArray(1).also { GLES20.glGenTextures(1, it, 0) }[0]
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, id)
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bm, 0)
        GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        bm.recycle()
        return id
    }

    private fun program(v: String, f: String): Int {
        fun senc(vrsta: Int, izvor: String): Int {
            val s = GLES20.glCreateShader(vrsta)
            GLES20.glShaderSource(s, izvor)
            GLES20.glCompileShader(s)
            val ok = IntArray(1)
            GLES20.glGetShaderiv(s, GLES20.GL_COMPILE_STATUS, ok, 0)
            check(ok[0] != 0) { "senčilnik: " + GLES20.glGetShaderInfoLog(s) }
            return s
        }
        val pr = GLES20.glCreateProgram()
        GLES20.glAttachShader(pr, senc(GLES20.GL_VERTEX_SHADER, v))
        GLES20.glAttachShader(pr, senc(GLES20.GL_FRAGMENT_SHADER, f))
        GLES20.glLinkProgram(pr)
        val ok = IntArray(1)
        GLES20.glGetProgramiv(pr, GLES20.GL_LINK_STATUS, ok, 0)
        check(ok[0] != 0) { "program: " + GLES20.glGetProgramInfoLog(pr) }
        return pr
    }

    /**
     * Glajenje robov, kadar ga naprava ima: brez njega so dolgi robovi perona
     * in tračnic stopničasti. Če 4× vzorčenja ni, gre brez.
     */
    class Nastavitev : GLSurfaceView.EGLConfigChooser {
        override fun chooseConfig(egl: EGL10, d: EGLDisplay): EGLConfig {
            fun poskusi(vzorcev: Int): EGLConfig? {
                val zahteva = intArrayOf(
                    EGL10.EGL_RED_SIZE, 8, EGL10.EGL_GREEN_SIZE, 8, EGL10.EGL_BLUE_SIZE, 8,
                    EGL10.EGL_DEPTH_SIZE, 16, EGL10.EGL_RENDERABLE_TYPE, 4, // EGL_OPENGL_ES2_BIT
                    EGL10.EGL_SAMPLE_BUFFERS, if (vzorcev > 0) 1 else 0,
                    EGL10.EGL_SAMPLES, vzorcev, EGL10.EGL_NONE)
                val st = IntArray(1)
                val izbor = arrayOfNulls<EGLConfig>(1)
                return if (egl.eglChooseConfig(d, zahteva, izbor, 1, st) && st[0] > 0) izbor[0] else null
            }
            return poskusi(4) ?: poskusi(0) ?: error("naprava nima nastavitve za OpenGL ES 2")
        }
    }

    companion object {
        private val KVADRAT = arrayOf(
            floatArrayOf(-1f, -1f, 0f, 1f), floatArrayOf(1f, -1f, 1f, 1f), floatArrayOf(1f, 1f, 1f, 0f),
            floatArrayOf(-1f, -1f, 0f, 1f), floatArrayOf(1f, 1f, 1f, 0f), floatArrayOf(-1f, 1f, 0f, 0f),
        )

        private fun mesaj(a: Float, b: Float, t: Float) = a + (b - a) * t

        private fun medpomnilnik(n: Int): FloatBuffer =
            ByteBuffer.allocateDirect(n * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()

        private const val OSVETLJENO_V = """
uniform mat4 uVP;
uniform mat4 uM;
uniform mat4 uV;
uniform vec3 uNebo;
uniform vec3 uTla;
uniform vec3 uLunaSmer;
uniform vec3 uLuna;
uniform vec3 uZarjaSmer;
uniform vec3 uZarja;
uniform vec3 uLucPoz;
uniform vec3 uLuc;
uniform float uLucDoseg;
uniform float uLucUpad;
uniform float uEnotna;
uniform vec3 uBarva;
uniform vec3 uSij;
attribute vec3 aPoz;
attribute vec3 aNormala;
attribute vec3 aBarva;
attribute vec3 aSij;
varying vec3 vBarva;
varying float vGlobina;
void main() {
    vec4 svet = uM * vec4(aPoz, 1.0);
    vec3 n = normalize((uM * vec4(aNormala, 0.0)).xyz);
    vec3 b = mix(aBarva, uBarva, uEnotna);
    vec3 s = mix(aSij, uSij, uEnotna);
    vec3 sv = mix(uTla, uNebo, 0.5 * n.y + 0.5);
    sv += max(dot(n, uLunaSmer), 0.0) * uLuna;
    sv += max(dot(n, uZarjaSmer), 0.0) * uZarja;
    vec3 l = uLucPoz - svet.xyz;
    float d = max(length(l), 0.0001);
    float upad = pow(clamp(1.0 - d / uLucDoseg, 0.0, 1.0), uLucUpad);
    sv += max(dot(n, l / d), 0.0) * upad * uLuc;
    vBarva = b * sv + s;
    vGlobina = -(uV * svet).z;
    gl_Position = uVP * svet;
}
"""
        private const val OSVETLJENO_F = """
precision mediump float;
uniform vec3 uMeglaBarva;
uniform vec2 uMegla;
varying vec3 vBarva;
varying float vGlobina;
// Megla po sliki, ne po ogliščih: tla so ena ploskev, dolga kilometer, in
// faktor, izračunan v njenih ogliščih, bi bil čez vso ploskev napačen.
void main() {
    gl_FragColor = vec4(mix(vBarva, uMeglaBarva, smoothstep(uMegla.x, uMegla.y, vGlobina)), 1.0);
}
"""
        private const val OSNOVNO_V = """
uniform mat4 uMVP;
uniform float uTocka;
attribute vec3 aPoz;
attribute vec2 aUv;
varying vec2 vUv;
void main() {
    vUv = aUv;
    gl_Position = uMVP * vec4(aPoz, 1.0);
    gl_PointSize = uTocka;
}
"""
        private const val OSNOVNO_F = """
precision mediump float;
uniform sampler2D uTeks;
uniform float uImaTeks;
uniform vec4 uBarva;
varying vec2 vUv;
void main() {
    vec4 t = mix(vec4(1.0), texture2D(uTeks, vUv), uImaTeks);
    gl_FragColor = t * uBarva;
}
"""
        // Nebo za prizorom: noč (#060912 → #0f1932 → #24335c) in zora čez njo,
        // kot preliva v prototipu (linearni in eliptični pri 50 % / 58 %).
        private const val NEBO_V = """
attribute vec2 aXy;
varying vec2 vUv;
void main() {
    vUv = vec2(aXy.x * 0.5 + 0.5, 0.5 - aXy.y * 0.5);
    gl_Position = vec4(aXy, 0.0, 1.0);
}
"""
        private const val NEBO_F = """
precision mediump float;
uniform float uZarja;
varying vec2 vUv;
vec3 h(float r, float g, float b) { return vec3(r, g, b) / 255.0; }
void main() {
    float y = vUv.y;
    vec3 osnova = y < 0.45 ? mix(h(6.0, 9.0, 18.0), h(15.0, 25.0, 50.0), y / 0.45)
                           : mix(h(15.0, 25.0, 50.0), h(36.0, 51.0, 92.0), (y - 0.45) / 0.55);
    vec3 lin = y < 0.45 ? mix(h(13.0, 20.0, 40.0), h(52.0, 48.0, 93.0), y / 0.45)
             : y < 0.75 ? mix(h(52.0, 48.0, 93.0), h(184.0, 101.0, 95.0), (y - 0.45) / 0.3)
                        : mix(h(184.0, 101.0, 95.0), h(246.0, 177.0, 127.0), (y - 0.75) / 0.25);
    float d = length(vec2((vUv.x - 0.5) / 0.9, (y - 0.58) / 0.46));
    vec4 rad = d < 0.34 ? mix(vec4(h(255.0, 176.0, 122.0), 1.0), vec4(h(208.0, 112.0, 126.0), 0.4), d / 0.34)
                        : mix(vec4(h(208.0, 112.0, 126.0), 0.4), vec4(h(42.0, 47.0, 90.0), 0.0), clamp((d - 0.34) / 0.38, 0.0, 1.0));
    vec3 zarja = mix(lin, rad.rgb, rad.a);
    gl_FragColor = vec4(mix(osnova, zarja, uZarja), 1.0);
}
"""
    }
}
