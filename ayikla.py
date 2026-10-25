"""Aşama 2: Seed-VC sentetik şarkılarını kulakla ayıkla (Tut / At).

    .venv/bin/python ayikla.py parcala          # synth/*.wav -> outputs/ayikla/*.wav (10–15 sn parçalar)
    ROOT_PATH=/lab/proxy/7861 .venv/bin/python ayikla.py   # dinleme sayfası, 7861
    .venv/bin/python ayikla.py topla            # tutulanlar -> synth_keep/, oran kuralını kontrol eder

Kararlar outputs/ayikla_kararlar.csv dosyasına yazılır; sayfa kapanıp açılınca kaldığı yerden devam eder.
"""
import csv
import os
import shutil
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SYNTH, PARTS, KEEP = Path("synth"), Path("outputs/ayikla"), Path("synth_keep")
DECISIONS = Path("outputs/ayikla_kararlar.csv")
TRAIN = Path("dataset_temiz/train")
SR, MIN_LEN, MAX_LEN = 44100, 10.0, 15.0


def parcala():
    """Sessizliklerden 10–15 sn'lik parçalara böl; vokalsiz kısımlar atılır."""
    shutil.rmtree(PARTS, ignore_errors=True)
    PARTS.mkdir(parents=True)
    for f in sorted(SYNTH.glob("*.wav")):
        y, sr = librosa.load(f, sr=SR, mono=True)
        iv = librosa.effects.split(y, top_db=35)
        parts, start, end = [], None, None
        for s, e in iv:
            if start is None:
                start = s
            elif (e - start) / SR > MAX_LEN:
                parts.append((start, end))
                start = s
            end = e
            if (end - start) / SR >= MIN_LEN:
                parts.append((start, end))
                start = None
        if start is not None and (end - start) / SR >= 3:
            parts.append((start, end))
        for i, (s, e) in enumerate(parts):
            sf.write(PARTS / f"{f.stem}_{i:02d}.wav", y[s:e], SR, subtype="PCM_16")
        print(f"{f.stem}: {len(parts)} parça, {sum(e - s for s, e in parts) / SR / 60:.2f} dk")


def kararlar():
    if not DECISIONS.exists():
        return {}
    return {r["parca"]: r["karar"] for r in csv.DictReader(DECISIONS.open())}


def kaydet(d):
    with DECISIONS.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["parca", "karar"])
        w.writerows(sorted(d.items()))


def dakika(files):
    return sum(sf.info(f).duration for f in files) / 60


def topla():
    d = kararlar()
    keep = [PARTS / p for p, k in d.items() if k == "tut"]
    real_min, keep_min = dakika(TRAIN.glob("*.wav")), dakika(keep)
    all_min = dakika(PARTS.glob("*.wav"))
    print(f"karar verilen {len(d)}/{len(list(PARTS.glob('*.wav')))} parça")
    print(f"üretilen {all_min:.2f} dk, tutulan {keep_min:.2f} dk, gerçek train {real_min:.2f} dk")
    # oran kuralı: tutulan sentetik süre gerçek train süresini geçemez
    assert keep_min <= real_min, "sentetik > gerçek: bazı parçaları At"
    shutil.rmtree(KEEP, ignore_errors=True)
    KEEP.mkdir()
    for f in keep:
        shutil.copy2(f, KEEP / f.name)
    print(f"{len(keep)} parça {KEEP}/ içine kopyalandı")


def app():
    import gradio as gr

    parts = sorted(p.name for p in PARTS.glob("*.wav"))
    ref = "dataset_temiz/ref/seedvc_ref.wav"

    def durum(d):
        tut = [PARTS / p for p, k in d.items() if k == "tut"]
        return (f"{len(d)}/{len(parts)} parça karar verildi · Tut {len(tut)} ({dakika(tut):.2f} dk) · "
                f"At {sum(k == 'at' for k in d.values())}")

    def sonraki(d):
        kalan = [p for p in parts if p not in d]
        if not kalan:
            return None, "Hepsi bitti. Terminalde: .venv/bin/python ayikla.py topla", durum(d)
        return str(PARTS / kalan[0]), kalan[0], durum(d)

    def karar(k, ad):
        d = kararlar()
        if ad in parts:
            d[ad] = k
            kaydet(d)
        return sonraki(d)

    def geri():
        d = kararlar()
        son = [p for p in parts if p in d]
        if son:
            d.pop(son[-1])
            kaydet(d)
        return sonraki(d)

    with gr.Blocks(title="Sentetik ayıklama") as demo:
        gr.Markdown("## Sentetik şarkıları ayıkla\nRobotik, metalik, Dua Lipa'ya hiç benzemeyen ya da iki sesin "
                    "üst üste bindiği parçaları **At**. Genelde yarısı kalır.")
        gr.Audio(ref, label="Referans: Dua Lipa (bu ses böyle)", interactive=False)
        audio = gr.Audio(label="Parça", interactive=False, autoplay=True)
        ad = gr.Textbox(label="Parça adı", interactive=False)
        with gr.Row():
            tut, at, gb = gr.Button("✅ Tut", variant="primary"), gr.Button("❌ At", variant="stop"), gr.Button("↩ Geri al")
        info = gr.Markdown()
        tut.click(lambda a: karar("tut", a), ad, [audio, ad, info])
        at.click(lambda a: karar("at", a), ad, [audio, ad, info])
        gb.click(geri, None, [audio, ad, info])
        demo.load(lambda: sonraki(kararlar()), None, [audio, ad, info])
    demo.launch(server_name="0.0.0.0", server_port=7861, root_path=os.environ.get("ROOT_PATH", ""),
                allowed_paths=[str(PARTS.resolve()), str(Path(ref).parent.resolve())])


if __name__ == "__main__":
    {"parcala": parcala, "topla": topla}.get(sys.argv[1] if len(sys.argv) > 1 else "", app)()
