package app.kajros

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

/**
 * Odhodna tabla ene postaje za widget: nastavitev, prenos in shramba.
 *
 * **S ciljem je to relacija** (23. 10. 2026): samo zveze do izbrane postaje, s
 * prihodom (`/api/connections`). Vozaču je tabla s 30 odhodi v vse smeri
 * odgovor na vprašanje, ki ga ni postavil; "kdaj mi pelje v službo" je ena
 * vrstica. Isti widget in iste postavitve -- vrstica ima samo še prihod.
 *
 * **Zakaj tu in ne v `Preverjevalec`.** Ta vprasa po ENI voznji, ker to rabi
 * budilka; widget vprasa po postaji in vzame prve tri. Odgovor je isti
 * endpoint (`/api/departures`) in to ni nakljucje: to je tabla, ki jo potnik
 * vidi na strani, in nobena druga stevilka ne sme biti na widgetu.
 *
 * Racun je ves na strezniku. `zamuda.min`, `zamuda.razred` in
 * `zamuda.prezgodaj` pridejo izracunani (`stats.opis_zamude()`); Android jih
 * samo izpise. **Zaokrozevanja ne sme ponoviti**: `kotlin.math.round` zaokrozi
 * pol na sodo in bi se pri 30 s razsel s stranjo.
 */
object Tabla {

    private const val DATOTEKA = "tabla"
    private const val CAKAJ_MS = 5000
    /**
     * Koliko vrstic widget shrani. Velik widget jih pokaže v seznamu, manjši
     * prve, ki še niso odpeljale -- shramba jih ima več, da se tabla med dvema
     * osvežitvama premakne naprej sama, brez zahteve.
     *
     * Avtobusno postajališče v središču ima v štirih urah 150 odhodov
     * (Bavarski dvor: 119 kB, gzip 10 kB, 22. 10. 2026); 30 je več, kot jih
     * kdo prebere na domačem zaslonu.
     */
    const val SHRANI = 30
    /** Koliko naprej vprasamo. Manj bi pri redki progi vrnilo prazno tablo. */
    private const val OKNO_MIN = 240
    /** Toliko predlogov kot na strani (`attachSuggest`); vec jih tipkovnica prekrije. */
    private const val ZADETKOV = 8

    private val URA = DateTimeFormatter.ofPattern("HH:mm")
    /** Strežnik bere uro `od` v svojem pasu, ne v telefonovem. */
    private val LJUBLJANA = ZoneId.of("Europe/Ljubljana")

    /** Ena vrstica table, ze pripravljena za izpis. */
    data class Odhod(
        val ura: String,
        val kam: String,
        val trainNo: String,
        val tripId: String?,
        /** Zaokrozena minuta s streznika, ali null, kadar zamuda se ni znana. */
        val zamudaMin: Int?,
        /** `tocno`, `1-5`, `5-15`, `nad-15` -- kljuc razreda s streznika. */
        val razred: String?,
        val prezgodaj: Boolean,
        /** Tir s table SŽ (`peroni.py`), kadar ga SŽ objavi in ni star. */
        val tir: String? = null,
        /** Odpovedana vožnja ali obvoz, ki tu ne ustavi: vrstica je prečrtana. */
        val odpadla: Boolean = false,
        /** Voznoredni odhod v epohi (ms); 0 = ni znan (stanje izpred 23. 10. 2026). */
        val voznoredniMs: Long = 0,
        /** Relacija: voznoredni prihod na cilj ("07:29"); na tabli null. */
        val prihod: String? = null,
        /** Relacija s prestopom: kje ("Ljubljana") in ali drži ("tesno", "ne drži"). */
        val prestop: String? = null,
        val prestopStanje: String? = null,
    ) {
        /**
         * Ali vrstica še sodi na tablo ob [zdajMs].
         *
         * Shranjena tabla je stara do pol ure; brez tega bi widget ob 7:10 še
         * kazal vlak ob 6:57 kot naslednjega. Odpeljal je, ko je mimo ura z
         * zamudo in še minuta. **Brez podatka o zamudi ostane deset minut** --
         * toliko nazaj gre tudi strežnik (`api_departures`): vlak, o katerem
         * feed molči, morda šele prihaja.
         */
        fun vidno(zdajMs: Long): Boolean {
            if (voznoredniMs <= 0) return true
            val doMs = if (zamudaMin == null) voznoredniMs + 10 * 60_000L
                else voznoredniMs + zamudaMin * 60_000L + 60_000L
            return zdajMs < doMs
        }

        /** Kdaj [vidno] postane false. */
        fun odideMs(): Long =
            if (zamudaMin == null) voznoredniMs + 10 * 60_000L
            else voznoredniMs + zamudaMin * 60_000L + 60_000L
    }

    /**
     * Kaj widget kaze in od kdaj.
     *
     * [opozorilo] je prva ovira, ki imenuje to postajo; [smeri] so strani
     * ceste, med katerimi gumb na widgetu preklaplja.
     */
    data class Stanje(
        val odhodi: List<Odhod>,
        val obMs: Long,
        val opozorilo: String? = null,
        val smeri: List<Smer> = emptyList(),
    )

    // ---------- nastavitev widgeta ----------

    /**
     * Postaja in omrezje tega widgeta.
     *
     * Na widget se shrani oboje, ker je **ime postaje brez omrezja dvoumno**:
     * "Ljubljana" je zeleznisko vozlisce in hkrati mestno postajalisce, in
     * privzeta zeleznica bi avtobusnemu potniku tiho vrnila drugo tablo.
     */
    data class Nastavitev(
        val postaja: String,
        val omrezje: String,
        /**
         * Stran ceste (`journey.smeri_postaje` na strezniku), ali null = obe.
         *
         * Mestno postajalisce je dvoje in tabla je kazala oboje skupaj; widget
         * pa pokaze samo tri vrstice, in ce sta dve z druge strani ceste, sta
         * dve od treh neuporabni.
         */
        val smer: String? = null,
        /** "→ Tobačna" -- shranjena, ker jo widget izpise tudi brez omrezja. */
        val smerNapis: String? = null,
        /** Tonska podlaga ali brez nje (`Izris.Videz`). */
        val videz: Izris.Videz = Izris.Videz.TONSKA,
        /**
         * Cilj relacije, ali null = vsi odhodi. S ciljem stran ceste ne
         * velja: smer pove cilj sam.
         */
        val cilj: String? = null,
        /**
         * Potnikovo ime table ("Domov", "Služba") namesto imen postaj -- na
         * ikoni 1×1 je to vse, kar je treba vedeti, kam gre.
         */
        val oznaka: String? = null,
        /**
         * Izhodišče, za katero [oznaka] velja. Po ⇄ je ni: "Domov" v drugo
         * smer bi bila laž. Drugi ⇄ jo vrne.
         */
        val oznakaOd: String? = null,
    ) {
        val vlak: Boolean get() = omrezje == "zeleznica"

        /** Ista relacija v drugo smer (gumb ⇄); brez cilja ni česa obrniti. */
        fun obrnjena(): Nastavitev? = cilj?.let { copy(postaja = it, cilj = postaja) }

        /** Ime za smer, ki je zdaj na tabli, ali null. */
        fun oznakaZdaj(): String? = oznaka?.takeIf { oznakaOd == null || oznakaOd == postaja }
    }

    /** Ena stran ceste, kot jo pove streznik. */
    data class Smer(val kljuc: String, val napis: String)

    /**
     * "→ Tobačna" ali "→ Vič Glince · Jadranska" -- isto kot `smerNapis` na
     * strani. Imen se ne sklanja.
     */
    fun smerNapis(naslednje: List<String>): String =
        "→ " + naslednje.joinToString(" · ").ifBlank { "končna" }

    /**
     * Gumb ⇄: druga stran ceste.
     *
     * Iz „obeh“ (`null`) na prvo, nato po vrsti v krogu. Nazaj na obe gumb ne
     * gre: ⇄ pomeni „druga stran“, in pri dveh straneh bi vsak drugi pritisk
     * pokazal obe, kar ni odgovor na vprašanje. Obe se izbere v nastavitvi.
     */
    fun naslednjaSmer(smeri: List<Smer>, zdaj: String?): Smer? {
        if (smeri.isEmpty()) return null
        val i = smeri.indexOfFirst { it.kljuc == zdaj }
        return smeri[(i + 1).mod(smeri.size)]
    }

    fun nastavi(c: Context, widgetId: Int, n: Nastavitev) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .putString("postaja_$widgetId", n.postaja)
            .putString("omrezje_$widgetId", n.omrezje)
            .putString("smer_$widgetId", n.smer)
            .putString("smer_napis_$widgetId", n.smerNapis)
            .putString("videz_$widgetId", n.videz.name)
            .putString("cilj_$widgetId", n.cilj)
            .putString("oznaka_$widgetId", n.oznaka)
            .putString("oznaka_od_$widgetId", n.oznakaOd)
            .apply()
    }

    fun nastavitev(c: Context, widgetId: Int): Nastavitev? {
        val p = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
        val postaja = p.getString("postaja_$widgetId", null) ?: return null
        return Nastavitev(postaja, p.getString("omrezje_$widgetId", "zeleznica")!!,
            p.getString("smer_$widgetId", null), p.getString("smer_napis_$widgetId", null),
            Izris.Videz.iz(p.getString("videz_$widgetId", null)),
            p.getString("cilj_$widgetId", null),
            p.getString("oznaka_$widgetId", null), p.getString("oznaka_od_$widgetId", null))
    }

    /** Widget je odstranjen z zaslona; njegova nastavitev nima vec lastnika. */
    fun pozabi(c: Context, widgetId: Int) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .remove("postaja_$widgetId")
            .remove("omrezje_$widgetId")
            .remove("smer_$widgetId")
            .remove("smer_napis_$widgetId")
            .remove("videz_$widgetId")
            .remove("cilj_$widgetId")
            .remove("oznaka_$widgetId")
            .remove("oznaka_od_$widgetId")
            .remove("stanje_$widgetId")
            .apply()
    }

    // ---------- shramba zadnjega odgovora ----------
    //
    // Widget se prerise tudi takrat, ko omrezja ni (sistem ga zbudi, zaslon se
    // prizge). Brez shrambe bi takrat obvisel prazen -- zato pokaze zadnje, kar
    // ve, IN uro tistega odgovora. Stara stevilka z uro je podatek, stara
    // stevilka brez ure je laz.

    fun shraniStanje(c: Context, widgetId: Int, s: Stanje) {
        val a = JSONArray()
        s.odhodi.forEach { o ->
            a.put(JSONObject().apply {
                put("ura", o.ura); put("kam", o.kam); put("train_no", o.trainNo)
                put("trip", o.tripId ?: JSONObject.NULL)
                put("min", o.zamudaMin ?: JSONObject.NULL)
                put("razred", o.razred ?: JSONObject.NULL)
                put("prezgodaj", o.prezgodaj)
                put("tir", o.tir ?: JSONObject.NULL)
                put("odpadla", o.odpadla)
                put("vr_ms", o.voznoredniMs)
                put("prihod", o.prihod ?: JSONObject.NULL)
                put("prestop", o.prestop ?: JSONObject.NULL)
                put("prestop_stanje", o.prestopStanje ?: JSONObject.NULL)
            })
        }
        val smeri = JSONArray()
        s.smeri.forEach { smeri.put(JSONObject().put("kljuc", it.kljuc).put("napis", it.napis)) }
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .putString("stanje_$widgetId", JSONObject()
                .put("ob", s.obMs).put("odhodi", a)
                .put("opozorilo", s.opozorilo ?: JSONObject.NULL)
                .put("smeri", smeri).toString())
            .apply()
    }

    /** Shranjena tabla ne velja več (druga stran ceste); nova pride s prenosom. */
    fun pozabiStanje(c: Context, widgetId: Int) {
        c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE).edit()
            .remove("stanje_$widgetId").apply()
    }

    fun stanje(c: Context, widgetId: Int): Stanje? {
        val niz = c.getSharedPreferences(DATOTEKA, Context.MODE_PRIVATE)
            .getString("stanje_$widgetId", null) ?: return null
        return try {
            val o = JSONObject(niz)
            val a = o.optJSONArray("odhodi") ?: JSONArray()
            Stanje((0 until a.length()).map { i ->
                val r = a.getJSONObject(i)
                Odhod(
                    ura = r.optString("ura"),
                    kam = r.optString("kam"),
                    trainNo = r.optString("train_no"),
                    tripId = if (r.isNull("trip")) null else r.optString("trip"),
                    zamudaMin = if (r.isNull("min")) null else r.getInt("min"),
                    razred = if (r.isNull("razred")) null else r.optString("razred"),
                    prezgodaj = r.optBoolean("prezgodaj"),
                    tir = if (r.isNull("tir")) null else r.optString("tir").ifBlank { null },
                    odpadla = r.optBoolean("odpadla"),
                    voznoredniMs = r.optLong("vr_ms"),
                    prihod = niz(r, "prihod"),
                    prestop = niz(r, "prestop"),
                    prestopStanje = niz(r, "prestop_stanje"),
                )
            }, o.optLong("ob"),
                opozorilo = if (o.isNull("opozorilo")) null else o.optString("opozorilo").ifBlank { null },
                smeri = (o.optJSONArray("smeri") ?: JSONArray()).let { sm ->
                    (0 until sm.length()).map { i ->
                        val d = sm.getJSONObject(i)
                        Smer(d.optString("kljuc"), d.optString("napis"))
                    }
                })
        } catch (e: org.json.JSONException) {
            null
        }
    }

    // ---------- besede in starost ----------
    //
    // Cist JVM in zato preizkuseno brez naprave. Pravilo o besedi je isto kot
    // na strani (`common.delayText`): minus pred stevilko je uganka, beseda ni.

    /**
     * Zamuda, kot jo widget izpise.
     *
     * Minuta pride s streznika ze zaokrozena; tu se samo odloci beseda. Kadar
     * zamude se ni, je to **pomisljaj in ne nicla** -- "tocno" za voznjo, o
     * kateri feed se ni rekel nicesar, bi bila trditev, ki je nimamo.
     */
    fun zamudaNapis(o: Odhod): String = napis(o.zamudaMin, o.prezgodaj)

    /**
     * Isto za zamudo budilke, ki jo widget izpelje sam: budilka hrani sekunde
     * z zadnjega preverjanja, ne odločitve strežnika, in `Ura` presodi, ali
     * še velja. Prag za „prej“ je isti kot `prezgodaj` na strežniku.
     */
    fun zamudaNapis(m: Int?): String = napis(m, m != null && m <= -1)

    private fun napis(m: Int?, prezgodaj: Boolean): String {
        if (m == null) return "—"
        if (prezgodaj) return "${-m} prej"
        if (m <= 0) return "točno"
        return "+$m"
    }

    /** Zaokrožena minuta, `floor(x + 0.5)` kot `stats._minute()` -- ne bančno. */
    fun minute(s: Int): Int = Math.floorDiv(s + 30, 60)

    /** Ključ razreda iz zaokrožene minute, isti pragovi kot `stats._razred_zamude()`. */
    fun razred(m: Int): String = when {
        m <= 0 -> "tocno"
        m <= 5 -> "1-5"
        m <= 15 -> "5-15"
        else -> "nad-15"
    }

    /** Koliko minut je star podatek. */
    fun starostMin(obMs: Long, zdajMs: Long): Int =
        if (obMs <= 0) Int.MAX_VALUE
        else Math.max(0, Math.round((zdajMs - obMs) / 60_000.0).toInt())

    /**
     * Ali je podatek toliko star, da mora widget to povedati z besedo.
     *
     * Dva koraka osvezevanja (2 x 15 min): en izpusceni cikel je Doze in ne
     * okvara, dva pa sta nekaj, kar mora potnik vedeti, preden se zanese na
     * stevilko.
     */
    fun jeStaro(obMs: Long, zdajMs: Long): Boolean = starostMin(obMs, zdajMs) > 30

    // ---------- prenos ----------

    /**
     * Kaj je streznik povedal. **Trije izidi, ne dva.**
     *
     * "Ni zveze" in "te postaje ni" sta razlicni novici in ju ne sme zdruziti
     * nihce: prvo je zacasno in postaje ne sme zavreci, drugo je tipkarska
     * napaka in jo mora nastavitev povedati takoj. Ista razlika kot v
     * `Preverjevalec.Odgovor`.
     *
     * Prazna tabla je tretji izid in ne napaka: pozno zvecer od tod res ne
     * pelje nic vec.
     */
    sealed class Izid {
        object BrezZveze : Izid()
        object NiPostaje : Izid()
        data class Odhodi(
            val vrstice: List<Odhod>,
            /** Strani ceste te postaje; prazno pri vlakih in postajah z eno. */
            val smeri: List<Smer> = emptyList(),
            /**
             * false, kadar je bila smer zahtevana, streznik pa je ne pozna vec
             * (nov vozni red). Tabla je takrat cela in widget ne sme trditi
             * smeri, ki je ne kaze.
             */
            val smerVelja: Boolean = true,
            /**
             * Ime, kot ga pozna streznik. Widget pred 22. 9. 2026 je shranil
             * kar vnos ("bavarski"); s tem se ob prvi osvezitvi popravi.
             */
            val postaja: String? = null,
            /** Naslov prve ovire, ki zadeva to postajo ([opozorilo]). */
            val opozorilo: String? = null,
            /** Ime cilja, kot ga pozna streznik (samo pri relaciji). */
            val cilj: String? = null,
        ) : Izid() {
            /**
             * Nastavitev, kot jo potrjuje odgovor: imeni postaj streznikovi,
             * smer pa samo, ce jo streznik se pozna -- napis nad tablo, ki
             * kaze obe strani, ne sme trditi ene.
             */
            fun popravi(n: Nastavitev): Nastavitev = n.copy(
                postaja = postaja ?: n.postaja,
                smer = if (smerVelja) n.smer else null,
                smerNapis = if (smerVelja) n.smerNapis else null,
                cilj = cilj ?: n.cilj,
                // Ime gre s postajo, ki jo je strežnik zapisal po svoje.
                oznakaOd = if (n.oznakaOd == n.postaja) postaja ?: n.oznakaOd else n.oznakaOd,
            )
        }
    }

    /**
     * Naslov table za widget. Cist JVM (izvor je niz), da ga je mogoce
     * preizkusiti -- `smer` je `stop_id` in v poizvedbo gre kodiran.
     *
     * Relacija vpraša za zveze od [od] naprej (ura v Ljubljani, kot jo bere
     * strežnik): brez tega pride ves dan, mestna relacija 115 zvez in 85 kB.
     */
    fun naslov(izvor: String, n: Nastavitev, od: String? = null): String = if (n.cilj != null) buildString {
        append(izvor).append("/api/connections?from=")
        append(URLEncoder.encode(n.postaja, "UTF-8"))
        append("&to=").append(URLEncoder.encode(n.cilj, "UTF-8"))
        append("&network=").append(n.omrezje)
        if (od != null) append("&od=").append(od)
        append("&limit=").append(SHRANI)
    } else buildString {
        append(izvor).append("/api/departures?station=")
        append(URLEncoder.encode(n.postaja, "UTF-8"))
        append("&network=").append(n.omrezje)
        append("&window=").append(OKNO_MIN)
        // Strežnik pred 23. 10. 2026 `limit` prezre in vrne vse; widget vseeno
        // shrani samo [SHRANI].
        append("&limit=").append(SHRANI)
        if (!n.smer.isNullOrBlank()) append("&smer=").append(URLEncoder.encode(n.smer, "UTF-8"))
    }

    /** Prvih [SHRANI] vrstic odhodne table te postaje ali zvez do cilja. */
    fun prenesi(c: Context, n: Nastavitev): Izid {
        if (n.cilj != null) return prenesiZveze(c, n)
        val (koda, besedilo) = prenesi(naslov(Nastavitve.naslov(c), n))
        if (koda == 404) return Izid.NiPostaje
        if (besedilo == null) return Izid.BrezZveze
        return try {
            val o = JSONObject(besedilo)
            val a = o.optJSONArray("board") ?: return Izid.BrezZveze
            val sm = o.optJSONArray("smeri") ?: JSONArray()
            val smeri = (0 until sm.length()).map { i ->
                val d = sm.getJSONObject(i)
                val nasl = d.optJSONArray("naslednje") ?: JSONArray()
                Smer(d.optString("kljuc"), smerNapis((0 until nasl.length()).map { nasl.optString(it) }))
            }.filter { it.kljuc.isNotBlank() }
            Izid.Odhodi(
                (0 until minOf(a.length(), SHRANI)).map { vrstica(a.getJSONObject(it)) },
                if (smeri.size > 1) smeri else emptyList(),
                smerVelja = n.smer.isNullOrBlank() || !o.isNull("smer"),
                postaja = o.optString("station").ifBlank { null },
                opozorilo = opozorilo(o.optJSONArray("alerts"), n.vlak),
            )
        } catch (e: org.json.JSONException) {
            Izid.BrezZveze
        }
    }

    /**
     * Zveze do cilja s pričakovanim odhodom od pred desetimi minutami naprej:
     * strežnik reže po voznem redu in zamudi, zato vlak ob 7:00 z zamudo
     * 18 min ob 7:12 še pride. Kdaj vrstica res odide, odloči [Odhod.vidno].
     *
     * Neposredne in s prestopom v eni vrsti po odhodu. Strežnik vrne vsake
     * po [SHRANI]; skupaj jih ostane [SHRANI].
     */
    private fun prenesiZveze(c: Context, n: Nastavitev): Izid {
        val od = java.time.LocalTime.now(LJUBLJANA).minusMinutes(10)
        // Tik po polnoči bi "23:55" vprašal za konec dneva, ki je že mimo.
        val ura = if (od.hour >= 23 && java.time.LocalTime.now(LJUBLJANA).hour < 1) null
            else od.format(URA)
        val (koda, besedilo) = prenesi(naslov(Nastavitve.naslov(c), n, ura))
        if (koda == 404) return Izid.NiPostaje
        if (besedilo == null) return Izid.BrezZveze
        return try {
            val o = JSONObject(besedilo)
            val neposredne = o.optJSONArray("connections") ?: return Izid.BrezZveze
            val s = o.optJSONArray("transfers") ?: JSONArray()
            val vse = (0 until neposredne.length()).map { zveza(neposredne.getJSONObject(it), n) } +
                (0 until s.length()).map { prestop(s.getJSONObject(it), n) }
            // Odpeljane stran, preden se odreže: strežnik pred 23. 10. 2026 `od`
            // prezre in vrne cel dan, mestna relacija pa ima 115 zvez.
            val zdaj = System.currentTimeMillis()
            Izid.Odhodi(
                vse.filter { it.vidno(zdaj) }.sortedBy { it.voznoredniMs }.take(SHRANI),
                postaja = o.optString("from").ifBlank { null },
                cilj = o.optString("to").ifBlank { null },
                opozorilo = opozorilo(o.optJSONArray("alerts"), n.vlak),
            )
        } catch (e: org.json.JSONException) {
            Izid.BrezZveze
        }
    }

    /** Neposredna zveza: kot vrstica table, s prihodom. */
    private fun zveza(r: JSONObject, n: Nastavitev): Odhod {
        val z = r.optJSONObject("zamuda")
        val min = if (z == null || z.isNull("min")) null else z.getInt("min")
        return Odhod(
            ura = ura(r.optString("sched_dep")),
            kam = n.cilj ?: "",
            trainNo = r.optString("train_no"),
            tripId = r.optString("trip_id").ifBlank { null },
            zamudaMin = min,
            razred = z?.optString("razred")?.ifBlank { null },
            prezgodaj = z?.optBoolean("prezgodaj") ?: false,
            tir = niz(r, "tir"),
            odpadla = r.optBoolean("odpovedano") || r.optBoolean("ne_ustavi"),
            voznoredniMs = casMs(r.optString("sched_dep")),
            prihod = prihod(r.optString("sched_arr"), min),
        )
    }

    /**
     * Prihod, kot ga potnik dočaka: vozni red in zamuda ob odhodu, ista
     * ocena kot druga vrstica zveze na strani (`connections.js`). Sam vozni
     * red ob „+18“ pri odhodu bi se bral kot obljuba prihoda -- in z njim bi
     * potnik zamudil prestop.
     */
    private fun prihod(iso: String?, zamudaMin: Int?): String {
        val ms = casMs(iso)
        return if (ms == 0L) "--:--" else uraMs(ms + (zamudaMin ?: 0) * 60_000L)
    }

    /**
     * Zveza s prestopom: obe vožnji v imenu, kraj prestopa in ali drži.
     * Zamude ob odhodu strežnik tu ne pove (`transfer` je zamuda na
     * prestopu), zato je pomišljaj -- ne izračunana ničla.
     */
    private fun prestop(r: JSONObject, n: Nastavitev): Odhod {
        val noge = r.optJSONArray("legs")
        val prva = noge?.optJSONObject(0)
        val stanje = r.optJSONObject("transfer")?.optString("status")
        return Odhod(
            ura = ura(r.optString("sched_dep")),
            kam = n.cilj ?: "",
            trainNo = listOf(r.optString("train1"), r.optString("train2"))
                .filter { it.isNotBlank() }.joinToString(" + "),
            tripId = r.optString("trip1").ifBlank { null },
            zamudaMin = null, razred = null, prezgodaj = false,
            tir = prva?.let { niz(it, "tir") },
            voznoredniMs = casMs(r.optString("sched_dep")),
            prihod = ura(r.optString("sched_arr")),
            prestop = r.optString("via").ifBlank { null },
            prestopStanje = stanje?.takeIf { it == "tesno" || it == "ne drži" },
        )
    }

    /** Niz ali null: `optString` za JSON null vrne "null". */
    private fun niz(o: JSONObject, kljuc: String): String? =
        if (o.isNull(kljuc)) null else o.optString(kljuc).ifBlank { null }

    /**
     * Ovira, ki jo widget pokaže nad seznamom.
     *
     * Pri vlakih **samo tista, ki imenuje to postajo** (`mentions_route` s
     * strežnika): splošno obvestilo visi na 75 vlakih in bi bilo nad vsako
     * tablo, kar je enako, kot če ga ne bi bilo. Pri avtobusih so obvestila že
     * vezana na postajališče (`alerts.for_stops`).
     */
    private fun opozorilo(a: JSONArray?, vlak: Boolean): String? {
        a ?: return null
        for (i in 0 until a.length()) {
            val o = a.optJSONObject(i) ?: continue
            if (vlak && !o.optBoolean("mentions_route")) continue
            val naslov = o.optString("header").trim()
            if (naslov.isNotEmpty() && naslov != "null") return naslov
        }
        return null
    }

    /**
     * Postaje, ki ustrezajo vnosu, v vrstnem redu streznika -- ali null, kadar
     * streznika ni bilo mogoce vprasati.
     *
     * Iskanje je strezniskovo (`journey.search_stations`), isto kot na strani:
     * seznam v telefonu bi bil drugo pravilo za isto stvar in bi se ob
     * naslednjem uvozu voznega reda razsel.
     */
    fun isci(c: Context, vnos: String, omrezje: String): List<String>? {
        val url = buildString {
            append(Nastavitve.naslov(c)).append("/api/stations/search?q=")
            append(URLEncoder.encode(vnos, "UTF-8"))
            append("&limit=").append(ZADETKOV)
            append("&network=").append(omrezje)
        }
        val (_, besedilo) = prenesi(url)
        besedilo ?: return null
        return try {
            val a = JSONArray(besedilo)
            (0 until a.length()).map { a.getJSONObject(it).optString("name") }.filter { it.isNotBlank() }
        } catch (e: org.json.JSONException) {
            null
        }
    }

    private fun vrstica(r: JSONObject): Odhod {
        val z = r.optJSONObject("zamuda")
        return Odhod(
            ura = ura(r.optString("sched")),
            // `towards` je smer s TE postaje in ne konec proge: vlak, ki vozi
            // naprej, ima oboje razlicno, potnik pa bere prvo.
            kam = r.optString("towards").ifBlank { r.optString("destination") },
            trainNo = r.optString("train_no"),
            tripId = r.optString("trip_id").ifBlank { null },
            zamudaMin = if (z == null || z.isNull("min")) null else z.getInt("min"),
            razred = z?.optString("razred")?.ifBlank { null },
            prezgodaj = z?.optBoolean("prezgodaj") ?: false,
            tir = if (r.isNull("tir")) null else r.optString("tir").ifBlank { null },
            // Odpovedana vožnja ima oboje; obvoz, ki tu ne ustavi, samo drugo.
            odpadla = r.optBoolean("odpovedano") || r.optBoolean("ne_ustavi"),
            voznoredniMs = casMs(r.optString("sched")),
        )
    }

    private fun casMs(iso: String?): Long {
        if (iso.isNullOrBlank()) return 0
        return try {
            OffsetDateTime.parse(iso).toInstant().toEpochMilli()
        } catch (e: DateTimeParseException) {
            0
        }
    }

    /**
     * Ura na postaji: vozni red je slovenski, tudi kadar je telefon v drugem
     * časovnem pasu -- tabla ob postaji ne sme kazati ure, ki je na peronu ni.
     */
    private fun ura(iso: String?): String {
        if (iso.isNullOrBlank()) return "--:--"
        return try {
            OffsetDateTime.parse(iso).atZoneSameInstant(LJUBLJANA).format(URA)
        } catch (e: DateTimeParseException) {
            "--:--"
        }
    }

    private fun uraMs(ms: Long): String =
        java.time.Instant.ofEpochMilli(ms).atZone(LJUBLJANA).format(URA)

    /** Koda odgovora in telo. Koda je 0, kadar odgovora sploh ni bilo. */
    private fun prenesi(url: String): Pair<Int, String?> {
        var zveza: HttpURLConnection? = null
        return try {
            zveza = (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = CAKAJ_MS
                readTimeout = CAKAJ_MS
                requestMethod = "GET"
                // Cloudflare pred kajros.app zavrne zahteve brez verodostojnega
                // UA -- isto kot v `Preverjevalec`.
                setRequestProperty("User-Agent",
                    "Kajros/${BuildConfig.VERSION_NAME} (Android)")
                setRequestProperty("Accept", "application/json")
            }
            val koda = zveza.responseCode
            koda to (if (koda != 200) null
                     else zveza.inputStream.bufferedReader().use { it.readText() })
        } catch (e: IOException) {
            0 to null
        } finally {
            zveza?.disconnect()
        }
    }
}
