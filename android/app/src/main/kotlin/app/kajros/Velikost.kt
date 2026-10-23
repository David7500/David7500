package app.kajros

/**
 * Velikostni razredi widgetov: kaj pokaže widget, velik kot ena ikona, in kaj
 * tisti čez pol zaslona.
 *
 * **Pravilo izbire je sistemsko.** Od Androida 12 launcher sam izbere
 * postavitev iz `RemoteViews(Map<SizeF, RemoteViews>)`: največjo, ki se v
 * celoti prilega, in kadar se ne prilega nobena, najmanjšo. Aplikacija se ob
 * spremembi velikosti ne zbudi. Na starejših ga ponovi [za] iz velikosti, ki
 * jih launcher pove v `OPTION_APPWIDGET_*`. Zato je pravilo tu, brez Androida:
 * oba načina morata izbrati isto in to je mogoče preizkusiti brez naprave.
 *
 * Meje so v dp in izhajajo iz Googlove preglednice mrež za telefon: pokončno
 * je ena vrstica visoka 102 dp in dve 220, stolpci so široki 57, 130, 203, 276
 * in 349; ležeče je vrstica nizka 51 dp in dve 117. Razred mora ustrezati
 * obema legama, zato meja za dve vrstici ni 220, ampak 110.
 */
enum class Velikost(val sirinaDp: Float, val visinaDp: Float) {
    /** 1×1: ena številka in dve drobni vrstici. */
    MINI(40f, 40f),
    /** Široko in nizko (vrstica na ležečem zaslonu): vse v eni vrsti. */
    PAS(110f, 40f),
    /** 2×1 in 3×1: tri vrstice besedila. */
    TRAK(110f, 64f),
    /** 4×1: več podatkov v vrsti in gumb. */
    TRAK_SIROK(240f, 64f),
    /** 2×2 in 3×2: glava in tri kratke vrstice. */
    KVADRAT(110f, 110f),
    /** 4×2: glava z gumbi in tri polne vrstice. */
    SREDNJI(240f, 110f),
    /** 2×3, 3×3: ozek seznam. */
    STOLPEC(110f, 250f),
    /** 4×3 in več: seznam, ki se drsi. */
    VELIK(240f, 250f);

    val ploscina: Float get() = sirinaDp * visinaDp

    companion object {
        /**
         * Razred za widget velikosti [sirinaDp] × [visinaDp] med [ponujenimi].
         *
         * Widget ponudi samo razrede, ki jih zna narisati: tabla ima seznam,
         * odštevanje ne. Isto kot sistem: največja ploščina med tistimi, ki se
         * prilegajo, sicer najmanjša.
         */
        fun za(sirinaDp: Float, visinaDp: Float, ponujene: Collection<Velikost>): Velikost {
            require(ponujene.isNotEmpty())
            return ponujene.filter { it.sirinaDp <= sirinaDp && it.visinaDp <= visinaDp }
                .maxByOrNull { it.ploscina }
                ?: ponujene.minByOrNull { it.ploscina }!!
        }
    }
}
