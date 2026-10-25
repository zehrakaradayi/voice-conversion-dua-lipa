"""training.ipynb'nin yardımcıları: RVC çevirisi (Applio, CPU), Ses benzerliği (ECAPA) ve oktav kontrolü."""
import contextlib
import glob
import os
import re
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
APPLIO = ROOT / "tools" / "Applio"
SR = 44100

# Aşama 6'daki çeviri ayarları; checkpoint dinlemede ve metrikte de aynıları kullanılır
RVC_AYAR = dict(f0_method="rmvpe", index_rate=0.5, protect=0.33, volume_envelope=0.25,
                split_audio=True, f0_autotune=False, embedder_model="contentvec", export_format="WAV")


@contextlib.contextmanager
def _applio_cwd():
    """Applio modelleri göreli yollarla yükler (rvc/models/...), o yüzden çalışma klasörü Applio olmalı."""
    old = os.getcwd()
    os.chdir(APPLIO)
    if str(APPLIO) not in sys.path:
        sys.path.insert(0, str(APPLIO))
    try:
        yield
    finally:
        os.chdir(old)


_vc = None


def cevir(girdi, cikti, pth, index, pitch=0, **ayar):
    """Bir vokali RVC modeliyle çevirir. Model bir kez yüklenir, sonraki çağrılar hızlıdır."""
    global _vc
    girdi, cikti, pth, index = (str(Path(p).resolve()) for p in (girdi, cikti, pth, index))
    Path(cikti).parent.mkdir(parents=True, exist_ok=True)
    with _applio_cwd():
        if _vc is None:
            from rvc.infer.infer import VoiceConverter
            _vc = VoiceConverter()
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            _vc.convert_audio(audio_input_path=girdi, audio_output_path=cikti, model_path=pth,
                              index_path=index, pitch=pitch, **{**RVC_AYAR, **ayar})
    if not Path(cikti).is_file():
        raise RuntimeError(f"Applio çıktı yazmadı: {cikti}")
    return cikti


def checkpointler(model_dir):
    """models/A içindeki A_<epoch>e_<adim>s.pth dosyaları, epoch sırasıyla: [(epoch, adim, yol)]."""
    out = []
    for p in glob.glob(f"{model_dir}/*_*e_*s.pth"):
        m = re.search(r"_(\d+)e_(\d+)s\.pth$", p)
        if m:
            out.append((int(m.group(1)), int(m.group(2)), p))
    return sorted(out)


def index_dosyasi(model_dir):
    files = glob.glob(f"{model_dir}/*.index")
    if len(files) != 1:
        raise FileNotFoundError(f"{model_dir} içinde tek bir .index bekleniyordu: {files}")
    return files[0]


def kes(girdi, cikti, bas, sure):
    y, sr = sf.read(girdi)
    Path(cikti).parent.mkdir(parents=True, exist_ok=True)
    sf.write(cikti, y[int(bas * sr): int((bas + sure) * sr)], sr, subtype="PCM_16")
    return cikti


# ---------- Ses benzerliği (ECAPA) ----------
_ecapa = None
PENCERE = 3.0


def _model():
    global _ecapa
    if _ecapa is None:
        from speechbrain.inference.speaker import EncoderClassifier
        _ecapa = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                                savedir=str(ROOT / "pretrained_models" / "ecapa"),
                                                run_opts={"device": "cpu"})
    return _ecapa


def _sessiz_degil(y, sr=16000):
    iv = librosa.effects.split(y, top_db=35)
    return np.concatenate([y[s:e] for s, e in iv]) if len(iv) else y


def pencereler(dosyalar):
    """Dosyaları 16 kHz'e çevirip sessizliği atar, 3 sn'lik pencerelerin 192 boyutlu ECAPA parmak izlerini döndürür."""
    import torch
    if isinstance(dosyalar, (str, Path)):
        dosyalar = [dosyalar]
    y = np.concatenate([_sessiz_degil(librosa.load(f, sr=16000, mono=True)[0]) for f in dosyalar])
    n = int(PENCERE * 16000)
    parcalar = [y[i:i + n] for i in range(0, len(y) - n + 1, n)]
    if not parcalar:
        raise ValueError(f"3 sn'lik pencere çıkmadı: {dosyalar}")
    with torch.no_grad():
        emb = _model().encode_batch(torch.tensor(np.stack(parcalar), dtype=torch.float32)).squeeze(1).numpy()
    return emb / np.linalg.norm(emb, axis=1, keepdims=True)


class SesBenzerligi:
    """Brief'teki ölçek: orijinal şarkıcı %0, Dua Lipa'nın diğer test kaydı %100.

    Test şarkısı (Pretty Please) ikiye bölünür: ilk yarı 'sen' (parmak izi = pencerelerin ortalaması),
    ikinci yarı 'sen_2'. Çevrilmiş vokalin her penceresi ölçeklenir; medyan ve %25–%75 aralığı raporlanır."""

    def __init__(self, test_dosyalari, sarkici_dosyasi):
        test = sorted(test_dosyalari)
        yari = len(test) // 2
        sen = pencereler(test[:yari]).mean(axis=0)
        self.sen = sen / np.linalg.norm(sen)
        self.alt = float(np.mean(pencereler(sarkici_dosyasi) @ self.sen))  # cos(şarkıcı, sen)
        self.ust = float(np.mean(pencereler(test[yari:]) @ self.sen))  # cos(sen_2, sen)

    def olc(self, dosya):
        cos = pencereler(dosya) @ self.sen
        skor = (cos - self.alt) / (self.ust - self.alt) * 100
        return {"medyan": float(np.median(skor)), "p25": float(np.percentile(skor, 25)),
                "p75": float(np.percentile(skor, 75)), "pencere": len(skor)}


# ---------- Oktav kontrolü ----------
def notalar(dosya):
    y, _ = librosa.load(dosya, sr=16000, mono=True)
    f0, vf, _ = librosa.pyin(y, fmin=80, fmax=1000, sr=16000, frame_length=1024, hop_length=320)
    return np.where(vf, librosa.hz_to_midi(f0), np.nan)


def oktav_kontrolu(orijinal, cevrilmis, kaydirma=0):
    """İkisinde de nota olan karelerde, kaydırma çıkarıldıktan sonra yarım tondan yakın olanların oranı (%)."""
    a, b = notalar(orijinal), notalar(cevrilmis)
    n = min(len(a), len(b))
    a, b = a[:n] + kaydirma, b[:n]
    ok = ~np.isnan(a) & ~np.isnan(b)
    fark = np.abs(a[ok] - b[ok])
    return {"yakin_yuzde": float(np.mean(fark < 0.5) * 100), "oktav_atlama_yuzde": float(np.mean(np.abs(fark - 12) < 1) * 100),
            "kare": int(ok.sum())}
