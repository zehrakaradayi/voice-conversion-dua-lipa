"""Aşama 2: Dua Lipa kuru vokallerini temizle, train/test böl, Seed-VC referansını seç.

    .venv/bin/python hazirla.py

Girdi:  stems/dua_*_lead.wav (GPU ayırma çıktısı)
Çıktı:  dataset_temiz/train/*.wav, dataset_temiz/test/*.wav, dataset_temiz/ref/seedvc_ref.wav,
        dataset_temiz/ozet.json
"""
import json
import shutil
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SR = 44100
TEST_SONG = "dua_pretty_please"  # bütün şarkı teste gider, eğitime hiç girmez
TRAIN_TARGET_SEC = 15 * 60
TOP_DB = 35  # şarkının tepe noktasına göre bu kadar sessiz yerler kesilir
MIN_SEG, MAX_SEG = 1.5, 12.0  # saniye
MERGE_GAP = 0.35  # bundan kısa sessizlikler segmenti bölmez
MIN_VOICED = 0.35  # pyin'e göre bu orandan az notalı segment ayırma artığıdır, atılır
PEAK_DB = -3.0
REF_SEC = 20.0

STEMS, OUT = Path("stems"), Path("dataset_temiz")


def voiced_ratio(y):
    y16 = librosa.resample(y, orig_sr=SR, target_sr=16000)
    _, vf, _ = librosa.pyin(y16, fmin=80, fmax=1000, sr=16000, frame_length=1024, hop_length=320)
    return float(vf.mean()) if len(vf) else 0.0


def segments(y):
    """Sessizlikten bölünmüş, kısa boşlukları birleştirilmiş, MAX_SEG'e kadar parçalanmış aralıklar."""
    iv = librosa.effects.split(y, top_db=TOP_DB, frame_length=2048, hop_length=512)
    merged = []
    for s, e in iv:
        if merged and s - merged[-1][1] < MERGE_GAP * SR:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    out = []
    for s, e in merged:
        n = int(np.ceil((e - s) / (MAX_SEG * SR)))
        step = (e - s) // n
        out += [(s + i * step, s + (i + 1) * step if i < n - 1 else e) for i in range(n)]
    pad = int(0.05 * SR)
    return [(max(0, s - pad), min(len(y), e + pad)) for s, e in out if (e - s) / SR >= MIN_SEG]


def peak_norm(y):
    return y * (10 ** (PEAK_DB / 20) / max(np.abs(y).max(), 1e-9))


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    for d in ("train", "test", "ref"):
        (OUT / d).mkdir(parents=True)

    pool, test_sec, dropped = {}, 0.0, {}
    for f in sorted(STEMS.glob("dua_*_lead.wav")):
        song = f.name[: -len("_lead.wav")]
        y, sr = sf.read(f)
        assert sr == SR and y.ndim == 1, (f, sr, y.shape)
        kept = []
        for s, e in segments(y):
            seg = y[s:e]
            if voiced_ratio(seg) < MIN_VOICED:
                dropped[song] = dropped.get(song, 0) + (e - s) / SR
                continue
            kept.append((s, peak_norm(seg)))
        if song == TEST_SONG:
            for s, seg in kept:
                sf.write(OUT / "test" / f"{song}_{s / SR:07.2f}.wav", seg, SR, subtype="PCM_16")
                test_sec += len(seg) / SR
        else:
            pool[song] = kept
        print(f"{song:24s} {sum(len(x) for _, x in kept) / SR / 60:4.2f} dk tutuldu, "
              f"{dropped.get(song, 0):5.1f} sn atıldı", flush=True)

    # her seferinde en az süresi olan şarkıdan bir segment alarak 15 dakikayı doldur: şarkılar dengeli kalır
    train, per_song, total = [], {s: 0.0 for s in pool}, 0.0
    queues = {s: list(v) for s, v in pool.items()}
    while total < TRAIN_TARGET_SEC and any(queues.values()):
        song = min((s for s in queues if queues[s]), key=per_song.get)
        s, seg = queues[song].pop(0)
        name = f"{song}_{s / SR:07.2f}.wav"
        sf.write(OUT / "train" / name, seg, SR, subtype="PCM_16")
        train.append(name)
        per_song[song] += len(seg) / SR
        total += len(seg) / SR

    # Seed-VC referansı: train segmentlerinden arka arkaya ~20 sn, en çok notalı (en temiz) pencere
    best = None
    for song, kept in pool.items():
        used = [(s, seg) for s, seg in kept if f"{song}_{s / SR:07.2f}.wav" in train]
        for i in range(len(used)):
            parts, dur = [], 0.0
            for _, seg in used[i:]:
                parts.append(seg)
                dur += len(seg) / SR
                if dur >= REF_SEC:
                    break
            if dur < REF_SEC:
                continue
            ref = np.concatenate(parts)[: int(REF_SEC * SR)]
            score = voiced_ratio(ref)
            if best is None or score > best[0]:
                best = (score, song, used[i][0] / SR, ref)
    score, ref_song, ref_start, ref = best
    sf.write(OUT / "ref" / "seedvc_ref.wav", peak_norm(ref), SR, subtype="PCM_16")

    ozet = {"test_sarkisi": TEST_SONG, "test_dk": round(test_sec / 60, 2),
            "train_dk": round(total / 60, 2), "train_segment": len(train),
            "train_sarki_basina_dk": {k: round(v / 60, 2) for k, v in per_song.items()},
            "atilan_sn": {k: round(v, 1) for k, v in dropped.items()},
            "ref": {"sarki": ref_song, "baslangic_sn": round(ref_start, 1), "notali_oran": round(score, 2)}}
    (OUT / "ozet.json").write_text(json.dumps(ozet, indent=2, ensure_ascii=False))
    print(json.dumps(ozet, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
