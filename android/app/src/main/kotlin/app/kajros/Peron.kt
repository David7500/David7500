package app.kajros

import kotlin.math.PI
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.hypot
import kotlin.math.sin

/**
 * Prizor zaslona zvonjenja „Peron“: noč pred zoro, stojiš na peronu pod
 * nadstreškom, ob tabli s svojo postajo in postajno uro, vozilo pripelje iz
 * daljave. Budilko ustaviš tako, da ga potegneš do sebe; na cilju se mu
 * prižgejo okna in odprejo vrata.
 *
 * Prenos prototipa `design/budilka/prototip.html` (three.js), ki ga je David
 * izbral 6. 10. 2026 („V peron je boljša“). Mere v metrih in barve so iste,
 * zato se ju da primerjati ploskev za ploskvijo. Brez knjižnic: prizor je
 * nekaj sto škatel, en izvlečen profil čela in valji koles.
 *
 * Tu je samo geometrija in odločitev o potegu (čista koda, preizkusi v
 * `PeronTest`); risanje je v [PeronRisar].
 */
class Peron(val vlak: Boolean) {

    companion object {
        const val CILJ_X = 60f

        /** Kamera stoji na peronu in gleda proti vozilu, ki prihaja. */
        val KAMERA = floatArrayOf(CILJ_X + 6f, 2.35f, 6.2f)
        val POGLED = floatArrayOf(CILJ_X - 30f, 2.1f, -0.6f)
        const val ZORNI_KOT = 56f
        const val BLIZU = 0.1f
        const val DALEC = 900f

        /** Tabla s krajem in postajna ura visita z nadstreška. */
        val TABLA = floatArrayOf(CILJ_X - 10f, 3.85f, 5.0f)
        val URA = floatArrayOf(CILJ_X - 2f, 3.5f, 3.6f)
        /** Topla luč nadstreška: ena sama, ker je vsaka luč v senčilniku nov račun. */
        val LUC = floatArrayOf(CILJ_X - 8f, 4.1f, 5.5f)

        // Barve vlaka (Stadler KISS SŽ 313, poenostavljen) in okna, ki se ob
        // prihodu prižge.
        const val BELA = 0xeceae4
        const val MODRA = 0x1a9be6
        const val CRNA = 0x0b0d10
        const val STEKLO = 0x101a24
        const val STREHA = 0x3d4247
        const val OKNO_LUC = 0xffd59a
        const val OKNO_SIJ = 0x7a5426

        /**
         * Kdaj poteg ustavi budilko. Začeti je treba NA vozilu (to preveri
         * pogled) in priti čez [PRAG] poti ali ga sunkovito zalučati proti
         * cilju: vsaj [SUNEK_HITROST] dp/ms po vsaj [SUNEK_POT] poti. Vsa pot
         * je [POT_DELEZ] širine prizora.
         *
         * Prva različica prototipa je zahtevala 85 % treh četrtin širine, in
         * David je 6. 10. 2026 rekel: „težko potegniti čisto do roba“. Zdaj
         * zadošča tretjina širine ali kratek sunek; dlan ali žep vozila še
         * vedno ne premakneta, ker poteg, ki se ne začne na vozilu, ne šteje.
         */
        const val PRAG = 0.6f
        const val POT_DELEZ = 0.5f
        const val SUNEK_HITROST = 0.6f
        const val SUNEK_POT = 0.3f

        /** Ali spust pri napredku [cilj] in hitrosti [hitrostDpMs] (proti cilju) ustavi budilko. */
        fun ustavi(cilj: Float, hitrostDpMs: Float): Boolean =
            cilj >= PRAG || (hitrostDpMs >= SUNEK_HITROST && cilj >= SUNEK_POT)

        /** Kateri četrtini poti pripada napredek: ob prehodu kratek tresljaj, kot zobnik. */
        fun cetrtina(p: Float): Int = floor(p * 4f).toInt()

        /** Kot okoli y, da je +z predmeta na [poz] obrnjen proti kameri. */
        fun protiKameri(poz: FloatArray): Float =
            atan2(KAMERA[0] - poz[0], KAMERA[2] - poz[2])
    }

    /** Vozilo pripelje iz daljave z leve in se ustavi ob tebi. */
    val zacetek = CILJ_X - if (vlak) 95f else 70f
    val konec = CILJ_X

    fun xVozila(p: Float) = zacetek + (konec - zacetek) * p

    // ------------------------------------------------------------ svet

    /**
     * Vse, kar se ne premika in je osvetljeno. Hribov iz prototipa ni: so na
     * obzorju za hrbtom kamere (+x) in s perona se ne vidijo.
     */
    val svet = Mreza()
    /** Zvezde: nekaj sto točk na kupoli, brez megle. */
    val zvezde: FloatArray

    // ------------------------------------------------------------ vozilo

    /** Vozilo brez oken, vrat in koles; čelo je na x = 0, voza nazaj v -x. */
    val vozilo = Mreza()
    /** Vsa okna: ena barva, ki se ob prihodu prižge. */
    val okna = Mreza()
    /** Ena vrata v svojem izhodišču; risar jih postavi na [vrata] in jih ob prihodu odpre. */
    val vrataMreza = Mreza()
    val vrata = ArrayList<FloatArray>()   // x, z
    class Kolo(val x: Float, val z: Float, val r: Float)
    val kolesa = ArrayList<Kolo>()
    /** Kolo s svetlo piko, ki pokaže vrtenje: levo (z < 0) in desno. */
    val koloLevo = Mreza()
    val koloDesno = Mreza()
    /** Sij luči (aditivno): x, y, z, barva, velikost, ali utripa z zvonjenjem. */
    class Sij(val x: Float, val y: Float, val z: Float, val barva: Int, val velikost: Float, val zaromet: Boolean)
    val siji = ArrayList<Sij>()
    var dolzina = 0f
        private set

    // ------------------------------------------------------------ tabla in ura

    val tablaKot = protiKameri(TABLA)
    val uraKot = protiKameri(URA)
    /** Napis na tabli: pravokotnik, ki mu risar da teksturo. */
    val tablaNapis = Ploskev()
    val uraStevilcnica = Ploskev()
    val uraObroc = Ploskev()
    /** Kazalci v svojem izhodišču; risar jih zavrti okoli z ure. */
    val kazalecUre = Ploskev()
    val kazalecMinut = Ploskev()
    val kazalecSekund = Ploskev()

    init {
        zgradiSvet()
        zvezde = zgradiZvezde()
        if (vlak) zgradiVlak() else zgradiAvtobus()
        kolo(koloLevo, if (vlak) 0.46f else 0.5f, -1f)
        kolo(koloDesno, if (vlak) 0.46f else 0.5f, 1f)
        zgradiTabloInUro()
    }

    private fun zgradiSvet() {
        // Tla.
        svet.stirikotnik(floatArrayOf(-650f, -0.02f, 300f, 950f, -0.02f, 300f,
            950f, -0.02f, -300f, -650f, -0.02f, -300f), 0f, 1f, 0f, barva(0x090c14), barva(0))

        // Za kamero (x > cilj + 30) ni ničesar videti, onkraj megle pa tudi ne:
        // proga se zato riše samo, kolikor je vidna.
        val od = -200f
        val doX = CILJ_X + 30f
        if (vlak) {
            svet.skatla(od, doX, 0f, 0.22f, -1.8f, 1.8f, 0x22242a)
            for (z in floatArrayOf(-0.72f, 0.72f)) svet.skatla(od, doX, 0.30f, 0.45f, z - 0.04f, z + 0.04f, 0x9aa1ab)
            var x = od
            while (x < doX) {
                svet.skatla(x - 0.12f, x + 0.12f, 0.20f, 0.32f, -1.25f, 1.25f, 0x3a342e)
                x += 0.62f
            }
            // Drogovi vozne mreže ob progi, vsakih 50 m, in vozni vod.
            x = -180f
            while (x < doX) {
                svet.skatla(x - 0.12f, x + 0.12f, 0f, 7.2f, -3.4f, -3.2f, 0x2c3038)
                svet.skatla(x - 0.08f, x + 0.08f, 6.6f, 6.75f, -3.3f, 0.2f, 0x2c3038)
                x += 50f
            }
            svet.skatla(od, doX, 5.95f, 5.98f, -0.02f, 0.02f, 0x5b616b)
        } else {
            svet.skatla(od, doX, 0f, 0.06f, -3.6f, 3.6f, 0x1d2026)
            var x = od
            while (x < doX) {
                svet.skatla(x - 1.5f, x + 1.5f, 0.06f, 0.08f, -0.07f, 0.07f, 0xc9c3b4)
                x += 6f
            }
            x = -180f
            while (x < doX) {
                svet.skatla(x - 0.08f, x + 0.08f, 0f, 5.5f, -4.6f, -4.45f, 0x2c3038)
                x += 35f
            }
        }

        // Peron z nadstreškom ob cilju, na strani kamere (+z).
        val c = CILJ_X
        svet.skatla(c - 90f, c + 18f, 0f, 0.55f, 2.2f, 8.5f, 0x363b44)
        svet.skatla(c - 90f, c + 18f, 0.55f, 0.565f, 2.25f, 2.6f, 0xd8a817)
        svet.skatla(c - 90f, c + 18f, 0.55f, 0.56f, 2.75f, 3.15f, 0x4a505b)      // taktilni pas
        // Streha sveti sama malo: osvetljena so oglišča, pri dolgi škatli so
        // daleč od luči in spodnja ploskev bi bila črna.
        svet.skatla(c - 70f, c + 14f, 4.3f, 4.5f, 2.9f, 8.8f, 0x2a2f38, 0x161a22)  // streha
        svet.skatla(c - 70f, c + 14f, 4.22f, 4.3f, 3.0f, 3.2f, 0xfff0d0, 0xffd9a6) // svetlobni pas
        svet.skatla(c - 70f, c + 14f, 4.22f, 4.3f, 7.0f, 7.2f, 0xfff0d0, 0xffd9a6)
        // Stebri nadstreška; tik ob tebi jih ni, da ne zastirajo pogleda.
        var x = c - 64f
        while (x <= c - 16f) {
            svet.skatla(x - 0.09f, x + 0.09f, 0.55f, 4.3f, 7.4f, 7.58f, 0x3b414b)
            x += 12f
        }
    }

    private fun zgradiZvezde(): FloatArray {
        // Stalno seme: nebo je vsako jutro isto, kot pravo.
        val r = java.util.Random(313)
        val z = FloatArray(380 * 3)
        for (i in 0 until 380) {
            val a = r.nextFloat() * 2f * PI.toFloat()
            val e = 0.08f + r.nextFloat() * 0.9f
            val d = 700f
            z[i * 3] = cos(a) * cos(e) * d + 60f
            z[i * 3 + 1] = sin(e) * d
            z[i * 3 + 2] = sin(a) * cos(e) * d
        }
        return z
    }

    private fun zgradiTabloInUro() {
        val tabla = Afina.premik(TABLA[0], TABLA[1], TABLA[2]) * Afina.okoliY(tablaKot)
        tablaNapis.pravokotnik(tabla, -1.4f, 1.4f, -0.35f, 0.35f)
        svet.pod(tabla) {
            svet.skatla(-1.1f, -1.06f, 0.35f, 0.85f, -0.02f, 0.02f, 0x3b414b)
            svet.skatla(1.06f, 1.1f, 0.35f, 0.85f, -0.02f, 0.02f, 0x3b414b)
        }
        val ura = Afina.premik(URA[0], URA[1], URA[2]) * Afina.okoliY(uraKot)
        uraStevilcnica.kolobar(ura, 0f, 0.42f, 40)
        uraObroc.kolobar(ura, 0.42f, 0.47f, 40)
        svet.pod(ura) { svet.skatla(-0.02f, 0.02f, 0.47f, 1.0f, -0.02f, 0.02f, 0x262a31) }
        fun kazalec(k: Ploskev, dol: Float, sir: Float, z: Float) =
            k.pravokotnik(Afina.ENOTA, -sir / 2, sir / 2, -0.05f, dol - 0.05f, z)
        kazalec(kazalecUre, 0.27f, 0.05f, 0.004f)
        kazalec(kazalecMinut, 0.38f, 0.035f, 0.006f)
        kazalec(kazalecSekund, 0.36f, 0.012f, 0.008f)
    }

    // ------------------------------------------------------------ vlak

    private fun okno(x0: Float, x1: Float, y0: Float, y1: Float, z: Float) =
        okna.skatla(x0, x1, y0, y1, z - 0.012f, z + 0.012f, STEKLO)

    /**
     * Voz od x0 do x1; čelo (3,4 m) za x1, kadar [celo], in pred x0, kadar
     * [zadaj] (KISS ima kabino na obeh koncih). Mere s strani o-nas: širina
     * 2,80 m, streha 4,34 m, kolo r 0,46 m; pasovi po višini kot na vozilu.
     */
    private fun voz(x0: Float, x1: Float, celo: Boolean, zadaj: Boolean) {
        val w = 1.40f
        val wz = 1.30f
        fun pas(y0: Float, y1: Float, sir: Float, b: Int) = vozilo.skatla(x0, x1, y0, y1, -sir, sir, b)
        pas(0.30f, 0.93f, w, BELA)
        pas(0.93f, 1.11f, w + 0.005f, MODRA)
        pas(1.11f, 2.50f, w, CRNA)
        pas(2.50f, 2.68f, w + 0.005f, MODRA)
        pas(2.68f, 2.86f, wz + 0.08f, BELA)
        pas(2.86f, 3.80f, wz - 0.02f, CRNA)
        pas(3.80f, 4.05f, wz, BELA)
        pas(4.05f, 4.34f, 1.05f, STREHA)
        for (s in floatArrayOf(-1f, 1f)) {
            // Okna zgornje etaže med belimi stebrički in spodnje na črnem pasu.
            var x = x0 + 1.4f
            while (x < x1 - 1.6f) {
                okno(x + 0.2f, x + 1.82f, 2.92f, 3.74f, s * (wz - 0.02f))
                vozilo.skatla(x, x + 0.2f, 2.86f, 3.80f, s * wz - 0.012f, s * wz + 0.012f, BELA)
                x += 1.92f
            }
            x = x0 + 2.2f
            while (x < x1 - 2.5f) {
                okno(x, x + 1.9f, 1.2f, 1.76f, s * w)
                x += 2.6f
            }
        }
        // Vrata: dva para na voz; na cilju se odprejo.
        for (xv in floatArrayOf(x0 + 5.6f, x1 - 7.2f)) {
            for (s in floatArrayOf(-1f, 1f)) vrata.add(floatArrayOf(xv, s * (w + 0.01f)))
        }
        for (xb in floatArrayOf(x0 + 2.85f, x1 - 2.85f)) {
            vozilo.skatla(xb - 1.6f, xb + 1.6f, 0.18f, 0.62f, -1.2f, 1.2f, 0x22252a)
            for (xo in floatArrayOf(xb - 1.2f, xb + 1.2f)) {
                for (z in floatArrayOf(-0.78f, 0.78f)) kolesa.add(Kolo(xo, z, 0.46f))
            }
        }
        if (celo) celoVoza(x1, 1f)
        if (zadaj) celoVoza(x0, -1f)
    }

    /**
     * Čelo: stranski profil v (x, y), izvlečen čez širino 2,8 m. [smer] -1 je
     * zadnja kabina: isto čelo, zrcaljeno okoli x0, luči so tam rdeče.
     */
    private fun celoVoza(x0: Float, smer: Float) {
        val l = 3.4f
        val t = if (smer > 0) Afina.premik(x0, 0f, 0f) else Afina.premik(x0, 0f, 0f) * Afina.ZRCALO_X
        vozilo.pod(t) {
            vozilo.izvlek(floatArrayOf(0f, 0.30f, l - 0.25f, 0.30f, l, 0.62f, l, 1.30f,
                l - 0.45f, 2.25f, l - 1.95f, 3.78f, 0f, 4.34f), -1.4f, 1.4f, BELA)
            // Vetrobransko steklo leži na nagnjenem delu profila.
            val nag = atan2(3.78f - 2.25f, 1.95f - 0.45f)
            val v = hypot(1.5f, 1.53f) * 0.92f
            val sredina = Afina.premik(l - 1.2f + 0.03f, (2.25f + 3.78f) / 2f, 0f) *
                Afina.okoliY(PI.toFloat() / 2f) * Afina.okoliX(-(PI.toFloat() / 2f - nag))
            vozilo.pod(sredina) {
                vozilo.stirikotnik(floatArrayOf(-1.21f, -v / 2, 0f, 1.21f, -v / 2, 0f,
                    1.21f, v / 2, 0f, -1.21f, v / 2, 0f), 0f, 0f, 1f, barva(STEKLO), barva(0))
            }
            vozilo.skatla(l - 0.02f, l + 0.02f, 0.62f, 1.30f, -1.25f, 1.25f, CRNA)
            vozilo.skatla(l - 0.2f, l + 0.02f, 0.93f, 1.11f, -1.2f, 1.2f, MODRA)
            for (z in floatArrayOf(-0.95f, 0.95f)) {
                val spredaj = smer > 0
                vozilo.skatla(l + 0.01f, l + 0.05f, 0.86f, 1.06f, z - 0.18f, z + 0.18f,
                    if (spredaj) 0xfff6d8 else 0xff3a2e, if (spredaj) 0xfff1c8 else 0xff2a20)
                val xs = x0 + smer * (l + 0.25f)
                siji.add(if (spredaj) Sij(xs, 0.96f, z, 0xfff1d6, 3.2f, true)
                else Sij(xs, 0.96f, z, 0xff5040, 1.8f, false))
            }
        }
    }

    private fun zgradiVlak() {
        val lc = 23.6f
        val lv = 26f
        val rega = 0.9f
        voz(-lc - 3.4f, -3.4f, celo = true, zadaj = false)
        vozilo.skatla(-lc - 3.4f - rega, -lc - 3.4f, 0.6f, 3.9f, -1.1f, 1.1f, 0x1c1f24)
        voz(-lc - 3.4f - rega - lv + 3.4f, -lc - 3.4f - rega, celo = false, zadaj = true)
        // Odjemnik toka.
        vozilo.skatla(-14.2f, -12.2f, 4.34f, 4.40f, -0.5f, 0.5f, 0x555a61)
        vozilo.pod(Afina.premik(-13.175f, 4.85f, 0f) * Afina.okoliZ(0.5f)) {
            vozilo.skatla(-0.025f, 0.025f, -0.45f, 0.45f, -0.03f, 0.03f, 0x777c83)
        }
        vozilo.skatla(-13.9f, -12.6f, 5.25f, 5.3f, -0.6f, 0.6f, 0x777c83)
        dolzina = lc + 3.4f + rega + lv
        vrataMreza.skatla(0f, 1.3f, 0.45f, 2.48f, -0.015f, 0.015f, BELA)
        vrataMreza.skatla(0.25f, 1.05f, 1.14f, 2.09f, -0.02f, 0.02f, STEKLO)
    }

    // ------------------------------------------------------------ avtobus

    /** Medkrajevni, nevtralne barve, brez znamke: 12 × 2,55 × 3,40 m, tri osi. */
    private fun zgradiAvtobus() {
        val l = 12f
        val w = 1.275f
        val b = 0xe3e6ea
        vozilo.skatla(-l, -0.35f, 0.35f, 1.20f, -w, w, b)
        vozilo.skatla(-l, -0.35f, 0.35f, 0.62f, -w - 0.005f, w + 0.005f, 0x2b3036)
        vozilo.skatla(-l, -0.35f, 1.20f, 2.58f, -w + 0.02f, w - 0.02f, STEKLO)
        vozilo.skatla(-l, -0.35f, 2.58f, 3.40f, -w, w, b)
        vozilo.skatla(-l, -0.35f, 1.08f, 1.18f, -w - 0.006f, w + 0.006f, 0x4db97f)
        for (s in floatArrayOf(-1f, 1f)) {
            var x = -l + 1.1f
            while (x < -1.2f) {
                okno(x + 0.16f, x + 1.55f, 1.28f, 2.5f, s * (w - 0.01f))
                vozilo.skatla(x, x + 0.16f, 1.20f, 2.58f, s * (w - 0.02f) - 0.02f, s * (w - 0.02f) + 0.02f, b)
                x += 1.55f
            }
        }
        vozilo.skatla(-0.35f, 0f, 0.35f, 1.20f, -w + 0.05f, w - 0.05f, b)
        vozilo.skatla(-0.35f, -0.02f, 1.20f, 3.20f, -w + 0.06f, w - 0.06f, STEKLO)
        vozilo.skatla(-0.35f, -0.1f, 3.20f, 3.40f, -w + 0.04f, w - 0.04f, b)
        for (z in floatArrayOf(-0.95f, 0.95f)) {
            vozilo.skatla(-0.02f, 0.03f, 0.62f, 0.80f, z - 0.2f, z + 0.2f, 0xfff6d8, 0xfff1c8)
            siji.add(Sij(0.25f, 0.7f, z, 0xfff1d6, 3f, true))
            vozilo.skatla(-l - 0.03f, -l + 0.01f, 0.62f, 0.95f, z - 0.15f, z + 0.15f, 0xff3a2e, 0xff2a20)
        }
        for (xv in floatArrayOf(-1.6f, -6.9f)) vrata.add(floatArrayOf(xv, w + 0.02f))
        vrataMreza.skatla(0f, 1.1f, 0.40f, 2.95f, -0.012f, 0.012f, STEKLO)
        for (xo in floatArrayOf(-2.6f, -8.4f, -9.8f)) {
            for (z in floatArrayOf(-1.05f, 1.05f)) kolesa.add(Kolo(xo, z, 0.5f))
        }
        dolzina = l
    }

    /** Kolo se vrti okoli osi z skupaj s svetlo piko, da se vrtenje vidi. */
    private fun kolo(m: Mreza, r: Float, stran: Float) {
        m.valj(r, 0.14f, 14, 0x5a5f66)
        val zf = 0.074f * stran
        m.skatla(r * 0.42f, r * 0.78f, -0.06f, 0.06f, zf - 0.005f, zf + 0.005f, 0xc9ced6)
    }
}
