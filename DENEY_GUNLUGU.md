# Deney Günlüğü — Proje 3: Voice Conversion

## Aşama 1 — Ses ve şarkılar
- **Sanatçı:** Dua Lipa
- **Dönem:** Future Nostalgia (2019–2020)
- **Sanatçının şarkıları (gerçek data, 8):** Boys Will Be Boys, Break My Heart, Cool, Don't Start Now, Hallucinate, Love Again, Physical, Pretty Please
- **Test şarkısı (eğitime girmez):** Pretty Please (bütün şarkı)
- **Cover şarkıları (Simge Sağın, eğitime asla girmez):** Önümüz Yaz, Üzülmedin mi
- **Sentetik şarkılar (`diger/`, 3):** Demet Akalın – Afedersin, Hadise – Düm Tek Tek, Hadise – Sıfır Tolerans
  - Not: Brief 6–8 sentetik şarkı öneriyor; 3 şarkıyla devam etme kararı verildi. Model B'nin sentetik payı küçük olacak.
- **Train / test dakikası:** 15.1 / 2.4

## Aşama 2 — Data cleaning ve sentetik data
**Ayırma:** 13 şarkı GPU'da `bs_roformer_karaoke` + `dereverb_mel_band_roformer` ile ayrıldı (`stems/`).

**Temizlik (`hazirla.py`):** 44.1 kHz mono; şarkı tepe noktasına göre −35 dB altı sessizlik kesildi, 0.35 sn'den kısa boşluklar birleştirildi,
segmentler 1.5–12 sn; pyin'e göre notalı oranı < %35 olan segmentler atıldı (hiç atılmadı); her segmentin tepe noktası −3 dB. Kompresör ve gürültü azaltma yok.
Train 15 dk'ya kadar her seferinde en az süreli şarkıdan segment alınarak dolduruldu.

| | Dakika |
|---|---|
| Gerçek train (7 şarkı, 138 segment) | 15.14 |
| Test (Pretty Please) | 2.38 |
| Sentetik üretilen (Seed-VC, 3 şarkı, 51 parça) | 8.93 |
| Sentetik tutulan (kulakla, 27 parça) | 4.95 |

Train şarkı başına: Boys Will Be Boys 2.19, Break My Heart 2.10, Cool 2.16, Don't Start Now 2.04, Hallucinate 2.20, Love Again 2.20, Physical 2.25 dk.

**Seed-VC referansı:** `dataset_temiz/ref/seedvc_ref.wav`, Love Again 153. sn'den 20 sn (notalı oran %90), train'den.

**Ses aralığı:** ![ses aralığı](outputs/ses_araligi.png)

| | Ortanca nota | Dua'ya fark | Kaydırma |
|---|---|---|---|
| Dua Lipa train | E4 | 0 | — |
| Simge – Önümüz Yaz | E4 | −0.2 | 0 |
| Simge – Üzülmedin mi | F♯4 | +1.9 | 0 |
| Sentetik şarkılar | F4 | +1.0 | 0 |

**Seçilen kaydırma: 0** (tüm şarkılar).

**Sentetik ayıklama (`ayikla.py`, Tut/At sayfası):**

| Şarkı | Tut | At | Tutulan |
|---|---|---|---|
| Demet Akalın – Afedersin | 8 | 9 | 1.38 dk |
| Hadise – Düm Tek Tek | 9 | 6 | 1.68 dk |
| Hadise – Sıfır Tolerans | 10 | 9 | 1.88 dk |

Oran kuralı: tutulan sentetik 4.95 dk ≤ gerçek train 15.14 dk ✅ (Model B datasının %25'i sentetik).

**Bir sentetik şarkıyı baştan sona dinleme notu:** _(Zehra yazacak: Dua Lipa'ya benziyor mu, nerede bozuluyor?)_

## Aşama 3 — Model seçimi
**Ortak tarif:** RVC v2 (Applio 3.7.0), 40 kHz, RMVPE, ContentVec, batch 16, cache_gpu, Applio pretrained, iki model için aynı adım sayısı (3000), checkpoint her 10 epoch.

| | Data | Tahmini dilim | Adım/epoch | Epoch (3000 adım) |
|---|---|---|---|---|
| Model A (sadece gerçek) | 15.14 dk | ~392 | ~25 | ~120 |
| Model B (gerçek + sentetik) | 15.14 + 4.95 = 20.09 dk | ~510 | ~32 | ~94 |

**Tahminim (Zehra):** Model B kazanır; farkı özellikle yüksek notalarda daha iyi performansla gösterir.

## Aşama 4 — Training ve metrikler
**Eğitim çalıştırmaları (GPU, RTX 4090, batch 16, cache_gpu):**

| Çalıştırma | Model | Data | Dilim | Adım/epoch | Epoch | Adım | sn/epoch |
|---|---|---|---|---|---|---|---|
| 1 (10:22, otomatik başladı) | A | 15.14 dk gerçek | 379 | 26 | 115 | 2990 | 4.4 |
| 1 | B_ayiklanmamis | gerçek + **ayıklanmamış** `synth/` (8.9 dk) | 570 | 39 | 77 | 3003 | 6.8 |
| 2 (10:56) | B (ayıklanmış) | gerçek + `synth_keep/` (4.95 dk) | 486 | 33 | 91 | 3003 | **öğretmen 11:02'de iptal etti** |

Not: 1. çalıştırma Tut/At kararlarından önce başladığı için B, ayıklanmamış sentetikle eğitildi (Applio dilimlemesi sunucuda tekrarlanarak doğrulandı: `synth/` = 191 dilim). Ayıklanmış B'nin yeniden eğitimi (2. çalıştırma) öğretmen tarafından iptal edildi; **final Model B = 1. çalıştırmadaki B (ayıklanmamış sentetik)**. Sentetik oranı: 8.9 dk / 24.0 dk ≈ %37 (oran kuralı sağlanıyor), ama kulakla eleme B'ye yansımadı.
Not: GPU çıktısında sadece son checkpoint geldi (`kaydet_her: 10` ara checkpoint'leri dışa aktarılmadı); checkpoint'leri dinleme yapılamadı, son checkpoint kullanıldı.

**Ara sonuç (hedef: Simge – Üzülmedin mi, kaydırma 0):**

| Satır | Ses benzerliği (medyan) | %25–%75 | Oktav kontrolü |
|---|---|---|---|
| Orijinal şarkıcı (Simge) | %0 (tanım gereği) | | — |
| Dua Lipa test kaydı | ≈ %100 | | — |
| Öğretmen (Seed-VC, eğitimsiz) | %46.8 | 37.5–59.6 | %88.9 |
| Model A (115e, 2990 adım) | %72.7 | 61.2–84.7 | %95.4 |
| Model B (77e, 3003 adım; ayıklanmamış sentetik) | %63.4 | 47.6–76.7 | %95.4 |

**Dinleme notu (Zehra, Model A):** Dua Lipa ve Simge Sağın'ın sesleri birbirine baya benziyor; orijinal ile Model A arasında kulakla çok bir farklılık göremedim.

**Rakamlara göre önde:** Model A (%72.7 vs %63.4). Aşama 3 tahmini (B kazanır) metrikte doğrulanmadı. Olası sebep: B'nin sentetiği kulakla elenmedi (metalik/bozuk parçalar dahil). Son karar CoverArena'da.

## Aşama 5 — CoverArena

## Aşama 6 — Cover ve deploy

