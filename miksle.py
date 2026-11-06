"""Aşama 6: kazanan modelin vokalini enstrümanla miksle ve 30 sn'lik nakaratı web/public/ içine kes.

    .venv/bin/python miksle.py

Tam cover özel kalır (outputs/cover/); dışarı çıkan tek şey 30 sn'lik nakarattır.
"""
import glob
import unicodedata
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm as pyln
from pedalboard import Compressor, HighShelfFilter, HighpassFilter, PeakFilter, Pedalboard, Reverb
from pedalboard.io import AudioFile

SR = 44100
SARKI = "cover_simge_uzulmedin_mi"
MODEL = "A"
AI_VOKAL = f"outputs/odev/{SARKI}_A_index100.wav"  # ödevde seçilen düzeltme: index_rate 1.0 (ilk versiyon: outputs/asama4/{SARKI}_A_115e.wav)
NAKARAT = (81.5, 30.0)  # başlangıç sn, süre: ilk nakarat bloğu (67.6–111.4 sn vokal bölümünün sonu)
LUFS, LIMIT_DB = -14.0, -1.5

# brief'teki vokal zinciri
VOKAL_ZINCIRI = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=90),
    PeakFilter(cutoff_frequency_hz=3000, gain_db=-2, q=1.0),
    PeakFilter(cutoff_frequency_hz=6500, gain_db=-3, q=1.0),
    Compressor(threshold_db=-18, ratio=3, attack_ms=5, release_ms=80),
    HighShelfFilter(cutoff_frequency_hz=10000, gain_db=2),  # hafif "air"
    Reverb(room_size=0.35, damping=0.5, wet_level=0.2, dry_level=0.8, width=0.8),
])


def yukle(path, kanal=2):
    y, _ = librosa.load(path, sr=SR, mono=False)
    y = np.atleast_2d(y)
    return np.repeat(y, kanal, axis=0) if y.shape[0] == 1 else y[:kanal]


def orijinal_sarki():
    """sarkilar/ içindeki orijinal mp3 (adlar Unicode NFD olabilir)."""
    for p in glob.glob("sarkilar/*.mp3"):
        if "zülmedin" in unicodedata.normalize("NFC", p):
            return p
    raise FileNotFoundError("Üzülmedin mi orijinali bulunamadı")


def loudness(y):
    return pyln.Meter(SR).integrated_loudness(y.T)


def limiter(y, ceiling_db=LIMIT_DB, window_ms=5):
    """Tepe limiter: tepeler ceiling_db'yi geçmez, sessiz kısımlara kazanç eklemez.
    (pedalboard'un Limiter'ı JUCE'un makeup kazancını da ekliyor, o yüzden kullanılmadı.)"""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    ceil = 10 ** (ceiling_db / 20)
    gain = np.minimum(1.0, ceil / np.maximum(np.abs(y).max(axis=0), 1e-9))
    n = int(window_ms / 1000 * SR) | 1
    gain = uniform_filter1d(minimum_filter1d(gain, 2 * n), n)  # önce genişlet, sonra yumuşat: tepeler kaçmaz
    return np.clip(y * gain, -ceil, ceil)


def master(y):
    return limiter(pyln.normalize.loudness(y.T, loudness(y), LUFS).T)


def kes(y, bas, sure, fade=1.0):
    seg = y[:, int(bas * SR): int((bas + sure) * SR)].copy()
    n = int(fade * SR)
    seg[:, :n] *= np.linspace(0, 1, n)
    seg[:, -n:] *= np.linspace(1, 0, n)
    return seg


def yaz(path, y, fmt):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with AudioFile(str(path), "w", SR, y.shape[0], **({"quality": "V2"} if fmt == "mp3" else {})) as f:
        f.write(y.astype(np.float32))


def main():
    orijinal_vokal = yukle(f"stems/{SARKI}_lead.wav")
    enstruman = yukle(f"stems/{SARKI}_inst.wav")  # enstrüman + orijinal arka vokaller
    vokal = VOKAL_ZINCIRI(yukle(AI_VOKAL).astype(np.float32), SR)

    n = min(vokal.shape[1], enstruman.shape[1], orijinal_vokal.shape[1])
    vokal, enstruman, orijinal_vokal = vokal[:, :n], enstruman[:, :n], orijinal_vokal[:, :n]
    # yeni vokalin seviyesi orijinal vokalinkine eşitlenir, sonra enstrümanla toplanır
    vokal = pyln.normalize.loudness(vokal.T, loudness(vokal), loudness(orijinal_vokal)).T
    cover = master(vokal + enstruman)
    orijinal = master(yukle(orijinal_sarki())[:, :n])

    yaz(f"outputs/cover/{SARKI}_{MODEL}_tam.wav", cover, "wav")  # özel: Drive'a
    yaz("web/public/ai.mp3", kes(cover, *NAKARAT), "mp3")
    yaz("web/public/orijinal.mp3", kes(orijinal, *NAKARAT), "mp3")
    for p in ("web/public/ai.mp3", "web/public/orijinal.mp3"):
        y = yukle(p)
        print(f"{p}: {y.shape[1] / SR:.1f} sn, {loudness(y):.1f} LUFS, tepe {20 * np.log10(np.abs(y).max()):.1f} dB")


if __name__ == "__main__":
    main()
