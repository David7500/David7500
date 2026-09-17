package app.kajros

import android.content.Context

/**
 * Widgeti aplikacije na enem mestu.
 *
 * Budilka se spremeni na sedmih mestih (stran, seznam, zvonjenje, sprozilec,
 * nacrtovalec), widgeta, ki jo kazeta, pa sta dva. Brez te tocke bi moral vsak
 * klicatelj vedeti, koliko jih je -- in tretji widget bi tiho zamrznil povsod,
 * kjer bi ga kdo pozabil dodati. To se je pri drugem skoraj zgodilo.
 *
 * Odhodna tabla (`WidgetTabla`) tu NI: ta ne kaze budilk, ampak vozni red, in
 * ima svoj ritem. Prerisati jo ob vsaki spremembi budilke bi bila zahteva v
 * omrezje za sliko, ki se ni spremenila.
 */
object Widgeti {

    fun osvezi(c: Context) {
        Widget.osvezi(c)
        WidgetBudilke.osvezi(c)
    }
}
