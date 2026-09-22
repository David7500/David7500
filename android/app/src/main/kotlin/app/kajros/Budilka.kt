package app.kajros

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * Ena budilka. Vse, kar rabi za zvonjenje **brez omrezja**, je tu -- predvsem
 * `voznoredniMs`. Ce bi ga bilo treba pridobiti, bi nadomestna pot rabila
 * ravno tisto, cesar takrat ni.
 */
data class Budilka(
    val id: String,
    val trainNo: String,
    val tripId: String?,
    val omrezje: String,
    val postaja: String,
    val stopSeq: Int,
    val dan: String,
    val voznoredniMs: Long,
    val minutPrej: Int,
    /** true = celozaslonsko zvonjenje, false = navadno obvestilo z zvokom. */
    val zbudi: Boolean,
    /** Kar je potnik sam obkljukal ("še 3 minute"), v sekundah. */
    val rezervaS: Int = 0,
    /**
     * Kateri dnevi v tednu, kot bitna maska (`Ponovitev`). 0 = enkratna.
     *
     * Kdor se vozi vsak dan z istim vlakom, je doslej moral budilko nastavljati
     * vsak vecer znova -- in ravno takrat, ko na to pozabis, je pomembna.
     */
    val dnevi: Int = 0,
    /** Zacasno ugasnjena: ostane v seznamu, a ne zvoni (dopust, bolniska). */
    val ugasnjena: Boolean = false,
    val smer: String = "",
    /** Zadnja znana zamuda in kdaj smo jo dobili. */
    val zamudaS: Int? = null,
    val zamudaObMs: Long = 0,
    /** Zadnji odgovor streznika, tudi kadar o zamudi ni imel podatka. */
    val stikObMs: Long = 0,
    /** Zadnji izracun -- da ga vidi tudi zaslon brez omrezja. */
    val zvoniObMs: Long = 0,
    val odzvonjeno: Boolean = false,
    /** Ce je potnik pritisnil "se dve minuti": takrat, ne po racunu. */
    val odlozenoDoMs: Long = 0,
) {
    val vlak: Boolean get() = omrezje == "zeleznica"
    val ponavljajoca: Boolean get() = Ponovitev.jePonavljajoca(dnevi)

    /**
     * Naslednja ponovitev te budilke po [zdajMs].
     *
     * Vozni red naslednjega dne ni nujno isti in `trip_id` **zagotovo** ni:
     * LPP linija 3G ima 388 voženj, vsak dan svoje. Zato gre id proc in ga
     * `Preverjevalec` na dan odhoda poisce znova po stevilki in uri.
     */
    fun prestavljena(zdajMs: Long): Budilka {
        // **Nikoli na isto voznjo.** Budilka zvoni PRED odhodom, zato je bil
        // "naslednji odhod po zdaj" 14. 9. 2026 isti vlak ob 7:35: ustavljena
        // budilka se je prestavila nase, zvonjenje je bilo ze v preteklosti in
        // je zazvonila znova -- v krogu, dokler je ni kdo ugasnil.
        val vr = Ponovitev.naslednji(voznoredniMs, dnevi, maxOf(zdajMs, voznoredniMs))
        return copy(
            voznoredniMs = vr,
            dan = Ponovitev.dan(vr),
            tripId = null,
            zamudaS = null,
            zamudaObMs = 0,
            stikObMs = 0,
            zvoniObMs = 0,
            odzvonjeno = false,
            odlozenoDoMs = 0,
        )
    }

    fun izracun(zdajMs: Long): Ura.Izid {
        val i = Ura.izracunaj(
            voznoredniMs = voznoredniMs,
            minutPrej = minutPrej,
            zamudaS = zamudaS,
            zamudaObMs = zamudaObMs,
            zdajMs = zdajMs,
            vlak = vlak,
            rezervaS = rezervaS,
            stikObMs = stikObMs,
            sledenje = odzvonjeno,
        )
        // Odlog povozi racun: potnik je rekel "cez dve minuti" in to ni ocena.
        return if (odlozenoDoMs > 0) i.copy(zvoniOb = odlozenoDoMs) else i
    }

    /**
     * Do kdaj po zvonjenju sledimo vozilu -- in do kdaj ga kaze widget.
     *
     * **Po zadnji znani zamudi, tudi zastareli.** Odhod iz [izracun] pade na
     * vozni red, kakor hitro zamuda ni vec sveza, in sledenje se je zato
     * koncalo ob voznem redu, ceprav je vlak po zadnjem podatku imel se pet
     * minut (22. 9. 2026). Kdaj odstevati, pove sveza zamuda; kdaj nehati,
     * pa najpoznejsi odhod, ki ga je kdo trdil -- daljse sledenje stane nekaj
     * prebujanj, prekratko pa potnika pusti brez stevca pred peronom.
     *
     * Pri vlaku negativna zamuda ne steje (pred voznim redom ne odpelje), pri
     * avtobusu pa konca tudi ne premakne naprej -- `maxOf` z voznim redom.
     */
    fun konecSledenjaMs(): Long =
        maxOf(voznoredniMs, voznoredniMs + (zamudaS ?: 0) * 1000L) + Ura.SLEDENJE_ZA_MS

    /**
     * Po zvonjenju: naslednja osvezitev zamude, ali null, ce je odhod mimo.
     *
     * Zvonjenje ni konec: potnik gre proti postaji in widget odsteva do
     * odhoda, zamuda pa se medtem se spreminja.
     *
     * **Ena budnica pade na sam odhod.** `Chronometer` cez niclo steje naprej
     * z minusom; widget mora takrat pisati "zdaj", in to zna samo ob
     * ponovnem izrisu.
     */
    fun sledenjeOb(zdajMs: Long): Long? {
        val konec = konecSledenjaMs()
        if (zdajMs >= konec) return null
        val naslednja = minOf(zdajMs + Ura.SLEDENJE_KORAK_MS, konec)
        val odhod = izracun(zdajMs).odhodMs
        return if (odhod > zdajMs) minOf(naslednja, odhod) else naslednja
    }

    /**
     * Naslov okna te voznje -- ista stran, ki jo potnik ze pozna.
     *
     * Tu in ne v dejavnosti, ker ga rabita dva klica: gumb "Odpri voznjo" v
     * seznamu budilk in dotik widgeta na domacem zaslonu. Dva zapisa istega
     * naslova bi se razsla, prvi pa je bil ze enkrat narobe (`+` namesto
     * `%20` v poti).
     *
     * Vzame [izvor] in ne `Context`, da je cist JVM in ga je mogoce preizkusiti
     * brez naprave -- isti razlog kot pri `Nastavitve.izvor()`.
     */
    fun naslovVoznje(izvor: String): String = buildString {
        append(izvor).append(if (vlak) "/app/train/" else "/app/bus/")
        // `Nastavitve.zaPot`, ne `URLEncoder`: stevilka gre v POT in presledek
        // mora biti `%20`, ne `+`. Glej opombo tam.
        append(Nastavitve.zaPot(trainNo))
        append("?postaja=").append(Nastavitve.zaPot(postaja))
        append("&date=").append(Nastavitve.zaPot(dan))
        if (!tripId.isNullOrBlank()) append("&trip=").append(Nastavitve.zaPot(tripId))
    }

    fun json(): JSONObject = JSONObject().apply {
        put("id", id); put("train_no", trainNo); put("trip", tripId ?: JSONObject.NULL)
        put("omrezje", omrezje); put("postaja", postaja); put("stop_seq", stopSeq)
        put("dan", dan); put("voznoredni_ms", voznoredniMs); put("minut_prej", minutPrej)
        put("zbudi", zbudi); put("rezerva_s", rezervaS); put("smer", smer)
        put("dnevi", dnevi); put("ugasnjena", ugasnjena)
        put("zamuda_s", zamudaS ?: JSONObject.NULL); put("zamuda_ob_ms", zamudaObMs)
        put("stik_ob_ms", stikObMs)
        put("zvoni_ob_ms", zvoniObMs); put("odzvonjeno", odzvonjeno)
        put("odlozeno_do_ms", odlozenoDoMs)
    }

    companion object {
        fun iz(o: JSONObject): Budilka? {
            val id = o.optString("id").ifBlank { return null }
            val vr = o.optLong("voznoredni_ms")
            if (vr <= 0) return null
            return Budilka(
                id = id,
                trainNo = o.optString("train_no"),
                tripId = if (o.isNull("trip")) null else o.optString("trip"),
                omrezje = o.optString("omrezje", "zeleznica"),
                postaja = o.optString("postaja"),
                stopSeq = o.optInt("stop_seq", -1),
                dan = o.optString("dan"),
                voznoredniMs = vr,
                minutPrej = o.optInt("minut_prej", 25),
                zbudi = o.optBoolean("zbudi", true),
                rezervaS = o.optInt("rezerva_s", 0),
                dnevi = o.optInt("dnevi", 0) and Ponovitev.VSI,
                ugasnjena = o.optBoolean("ugasnjena"),
                smer = o.optString("smer"),
                zamudaS = if (o.isNull("zamuda_s")) null else o.optInt("zamuda_s"),
                zamudaObMs = o.optLong("zamuda_ob_ms"),
                stikObMs = o.optLong("stik_ob_ms"),
                zvoniObMs = o.optLong("zvoni_ob_ms"),
                odzvonjeno = o.optBoolean("odzvonjeno"),
                odlozenoDoMs = o.optLong("odlozeno_do_ms"),
            )
        }
    }
}

/**
 * Budilke v `SharedPreferences` kot JSON.
 *
 * Zakaj ne baza: teh je nekaj, ne tisoc, in vsak dostop je celoten seznam.
 * Vsaka baza bi bila vec kode za isti ucinek.
 */
object Shramba {

    private const val DATOTEKA = "budilke"
    private const val KLJUC = "seznam"
    /** Odzvonjene drzimo se en dan, da jih zaslon brez omrezja lahko pokaze. */
    private const val ZADRZI_MS = 24 * 3600 * 1000L

    @Synchronized
    fun vse(c: Context): List<Budilka> {
        val niz = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .getString(KLJUC, null) ?: return emptyList()
        return try {
            val a = JSONArray(niz)
            (0 until a.length()).mapNotNull { Budilka.iz(a.getJSONObject(it)) }
        } catch (e: org.json.JSONException) {
            // Pokvarjen zapis ni razlog za sesutje ob zagonu. Izgubimo budilke,
            // ne aplikacije -- in naslednji zapis stanje popravi.
            emptyList()
        }
    }

    fun ena(c: Context, id: String): Budilka? = vse(c).firstOrNull { it.id == id }

    @Synchronized
    fun zapisi(c: Context, seznam: List<Budilka>) {
        val a = JSONArray()
        seznam.forEach { a.put(it.json()) }
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .edit().putString(KLJUC, a.toString()).apply()
    }

    fun shrani(c: Context, b: Budilka) {
        zapisi(c, vse(c).filter { it.id != b.id } + b)
    }

    fun odstrani(c: Context, id: String) {
        zapisi(c, vse(c).filter { it.id != id })
    }

    /**
     * Pobrise, kar je davno mimo. Klicano ob vsakem pisanju z zunanje strani.
     *
     * Ponavljajoce se ne brisejo nikoli -- njihov odhod je vedno v prihodnosti,
     * dokler jih `Ponovitev.prestavi()` prestavlja, in ce je kdaj v preteklosti,
     * je to okvara, ki jo popravi prestavljanje, ne brisanje.
     */
    fun pocisti(c: Context, zdajMs: Long) {
        val vse = vse(c)
        val ostane = vse.filter { it.ponavljajoca || zdajMs - it.voznoredniMs < ZADRZI_MS }
        if (ostane.size != vse.size) zapisi(c, ostane)
    }
}
