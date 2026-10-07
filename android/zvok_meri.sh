#!/usr/bin/env bash
# Kako glasen je MIDI, kot ga zaigra telefon: RMS in vrh v dBFS po oknih.
#
#     ./zvok_meri.sh app/src/main/res/raw/nezno.mid [okno_s]
#
# Zvok budilke predvaja Sonivox v telefonu, zato se meri tam, ne na namizju:
# namizni Sonivox je ~2,5 dB glasnejši, formula iz jakosti udarca pa je pri
# tihih notah zgrešila za 6 dB (7. 10. 2026). PCM naredi Androidov
# `MidiExtractor` -- isti, ki ga uporabi predvajalnik obvestila. Program teče
# prek `app_process` kot uporabnik shell; korena ne rabi.
set -euo pipefail
cd "$(dirname "$0")"
KOREN="${KAJROS_ANDROID:-$HOME/kajros-android}"
MIDI="${1:?pot do .mid}"
OKNO="${2:-2.5}"
ADB="$KOREN/sdk/platform-tools/adb"
BT="$(ls -d "$KOREN/sdk/build-tools"/* | sort -V | tail -1)"
JAR="$(ls -d "$KOREN/sdk/platforms"/android-* | sort -V | tail -1)/android.jar"
MAPA="$(mktemp -d)"; trap 'rm -rf "$MAPA"' EXIT

cat > "$MAPA/Meri.java" <<'JAVA'
import android.media.MediaExtractor;
import android.media.MediaFormat;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class Meri {
    public static void main(String[] a) throws Exception {
        double okno = Double.parseDouble(a[1]);
        MediaExtractor ex = new MediaExtractor();
        ex.setDataSource(a[0]);
        MediaFormat f = ex.getTrackFormat(0);
        int rate = f.getInteger(MediaFormat.KEY_SAMPLE_RATE);
        int ch = f.getInteger(MediaFormat.KEY_CHANNEL_COUNT);
        System.out.println("# " + rate + " Hz, " + ch + " kan. · s · RMS dBFS · vrh dBFS");
        ex.selectTrack(0);
        ByteBuffer b = ByteBuffer.allocateDirect(1 << 20).order(ByteOrder.LITTLE_ENDIAN);
        long vOknu = (long) (okno * rate) * ch;
        double vsota = 0, vrh = 0;
        long n = 0;
        int i = 0;
        while (true) {
            b.clear();
            int len = ex.readSampleData(b, 0);
            if (len < 0) break;
            b.position(0);
            b.limit(len);
            while (b.remaining() >= 2) {
                double s = b.getShort() / 32768.0;
                vsota += s * s;
                vrh = Math.max(vrh, Math.abs(s));
                if (++n == vOknu) {
                    System.out.printf(java.util.Locale.ROOT, "%5.1f %7.1f %7.1f%n", i * okno,
                        10 * Math.log10(vsota / n + 1e-20), 20 * Math.log10(vrh + 1e-10));
                    vsota = 0; vrh = 0; n = 0; i++;
                }
            }
            ex.advance();
        }
    }
}
JAVA
"$KOREN/jdk/bin/javac" --release 11 -cp "$JAR" -d "$MAPA" "$MAPA/Meri.java"
PATH="$KOREN/jdk/bin:$PATH" "$BT/d8" --min-api 26 --output "$MAPA" "$MAPA/Meri.class"
"$ADB" push "$MAPA/classes.dex" /data/local/tmp/kajros-meri.dex >/dev/null
"$ADB" push "$MIDI" /data/local/tmp/kajros-meri.mid >/dev/null
"$ADB" shell CLASSPATH=/data/local/tmp/kajros-meri.dex app_process / Meri \
    /data/local/tmp/kajros-meri.mid "$OKNO"
"$ADB" shell rm -f /data/local/tmp/kajros-meri.dex /data/local/tmp/kajros-meri.mid
