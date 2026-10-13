package app.kajros

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.provider.OpenableColumns
import android.webkit.MimeTypeMap
import java.io.File
import java.io.FileNotFoundException

/**
 * Datoteke, ki jih stran pošlje z `navigator.share` ([Posiljanje]), za
 * prejemnika, ki ga je potnik izbral. FileProvider je v AndroidX, ki ga
 * aplikacija nima; ta zna samo eno: brati iz mape `poslji` v predpomnilniku.
 *
 * Ni izvožen. Prejemnik pride do datoteke samo z dovoljenjem, ki ga nosi
 * namera (`FLAG_GRANT_READ_URI_PERMISSION`), in samo do tiste.
 */
class Datoteke : ContentProvider() {

    override fun onCreate(): Boolean = true

    /** Naslov `<podmapa>/<ime>` → datoteka, ali `null`. Ime gre skozi isto
     *  čiščenje kot ob zapisu: `..` ali `/` iz naslova ne sme ven iz mape. */
    private fun datoteka(uri: Uri): File? {
        val deli = uri.pathSegments
        if (deli.size != 2 || !deli[0].matches(Regex("\\d+-\\d+"))) return null
        if (Posiljanje.varnoIme(deli[1]) != deli[1]) return null
        val f = File(File(Posiljanje.mapa(context ?: return null), deli[0]), deli[1])
        return f.takeIf { it.isFile }
    }

    override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor {
        if (mode != "r") throw SecurityException("samo branje")
        val f = datoteka(uri) ?: throw FileNotFoundException(uri.toString())
        return ParcelFileDescriptor.open(f, ParcelFileDescriptor.MODE_READ_ONLY)
    }

    override fun getType(uri: Uri): String? {
        val ime = uri.lastPathSegment ?: return null
        return MimeTypeMap.getSingleton()
            .getMimeTypeFromExtension(ime.substringAfterLast('.', "").lowercase())
    }

    /** Ime in velikost: po tem prejemniki (WhatsApp, Gmail) poimenujejo prilogo. */
    override fun query(uri: Uri, stolpci: Array<String>?, izbor: String?,
                       argumenti: Array<String>?, red: String?): Cursor? {
        val f = datoteka(uri) ?: return null
        val vsi = arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE)
        val izbrani = stolpci?.filter { it in vsi }?.toTypedArray() ?: vsi
        return MatrixCursor(izbrani).apply {
            addRow(izbrani.map { if (it == OpenableColumns.SIZE) f.length() else f.name })
        }
    }

    override fun insert(uri: Uri, vrednosti: ContentValues?): Uri? = null
    override fun update(uri: Uri, vrednosti: ContentValues?, izbor: String?,
                        argumenti: Array<String>?): Int = 0
    override fun delete(uri: Uri, izbor: String?, argumenti: Array<String>?): Int = 0
}
