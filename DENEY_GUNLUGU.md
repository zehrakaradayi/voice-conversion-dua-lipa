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
**Atlandı (Zehra'nın kararı, 25 Ekim).** Kör dinleme testi yapılmadı; kazanan metriğe göre seçildi: **Model A** (Ses benzerliği %72.7 vs B %63.4).
Zorunlu gereksinim "CoverArena: en az 10 dinleyici × 3 bölüm" karşılanmadı. Arena yapılırsa ve oylar B derse, kural gereği oylar kazanır ve cover yeniden üretilir.

## Aşama 6 — Cover ve deploy
**Miks (`miksle.py`):** Model A, Üzülmedin mi'nin tam kuru vokali (rmvpe, index 0.5, protect 0.33, volume_envelope 0.25, split_audio, autotune kapalı).
Vokal zinciri (pedalboard): high-pass 90 Hz, 3 kHz −2 dB, 6.5 kHz −3 dB, kompresör 3:1, +2 dB air shelf (10 kHz), %20 reverb.
Seviye orijinal vokale eşitlendi (pyloudnorm), enstrüman + orijinal arka vokallerle toplandı. Master: −14.0 LUFS, tepe −1.5 dB
(pedalboard Limiter makeup kazancı eklediği için kendi tepe limiterimiz kullanıldı).

**Nakarat:** 81.5–111.5 sn (30 sn, 1 sn fade). Orijinal ve AI klibi aynı işlemle, ikisi de −13.2 LUFS.
**Tam cover (özel):** `outputs/cover/cover_simge_uzulmedin_mi_A_tam.wav` → Drive'a yüklenecek.
**Cover Player (`web/`, Next.js 14):** iki senkron oynatıcı, tek tuşla orijinal ↔ AI, "Yapay zekâ ile üretilmiştir" etiketi, krediler, model kartı, `noindex, nofollow`.
**Vercel linki:** _deploy bekleniyor_


## Ödev — 3 cover'ı iyileştir (6 Kasım)
**Cover'lar (hepsi Model A, Dua Lipa sesi):** Simge – Üzülmedin mi, Hadise – Sıfır Tolerans, Hadise – Düm Tek Tek.
Hadise şarkılarında Model B kullanılmadı: B, bu şarkıların Seed-VC versiyonlarıyla eğitildi, skor şişer.
GPU kullanılmadı; tüm çeviriler CPU'da (`outputs/odev/`). Baz = Aşama 6 ayarları (index 0.5, protect 0.33, pitch 0, rmvpe).
Varyantlar bazdan **tek** parametre değiştirir (`outputs/odev/varyant.py`), dinleme sayfası `outputs/odev/dinle_odev.py` (7860).

| Kesit | baz | index 0.75 | index 1.0 | protect 0.5 | protect 0.2 |
|---|---|---|---|---|---|
| Üzülmedin mi, nakarat 81.5–111.5 sn | 85.0 | 96.7 | 100.1 | 87.2 | 87.4 |
| Sıfır Tolerans, 95–135 sn | 56.1 | 59.2 | 63.3 | 56.5 | 60.1 |
| Düm Tek Tek, 28–68 sn | 96.6 | 95.8 | 94.9 | 96.4 | 101.6 |

(Ses benzerliği medyanı, %; 0 = orijinal şarkıcı, 100 = Dua'nın test kaydı. Hiçbir varyant nota doğruluğunu değiştirmedi.)

**Üzülmedin mi — dinleme (Zehra):** Bütün numaralar birbirine benziyor, hiçbirinde tam olarak Dua Lipa'nın sesini duymuyorum; en iyisi 3 (index_rate 1.0).
→ Seçim: **index_rate 0.5 → 1.0**. Metrikte nakarat %85.0 → %100.1; kulakta fark küçük.

**Sıfır Tolerans — dinleme (Zehra):** 1 (baz) ve 2 (index 0.75) Hadise'nin neredeyse birebir aynısı. En iyi 3 (index 1.0); 4 (protect 0.5) fena değil; 5 (protect 0.2) yine 1 ve 2'ye benziyor.
→ Seçim: **index_rate 0.5 → 1.0**. Metrikte 95–135 sn %56.1 → %63.3 (alt çeyrek 45 → 53). Kulak ve metrik aynı sırayı veriyor (3 > 2, 5 ≈ 1); tek ayrılık 4: kulakta iyi, metrikte baz kadar (%56.5).

**Düm Tek Tek — dinleme (Zehra):** Genel olarak en başarılı cover. 5 (protect 0.2) diğer şarkılara kıyasla çok başarılı, ama en çok 1 (baz) beğenildi.
→ Çeviri ayarı değişmiyor (baz). İyileştirme miks tarafında aranacak (vokal seviyesi / reverb, tek tek).

**Düm Tek Tek — miks (Zehra):** A (ilk miks: vokal = orijinal seviye, reverb %20) en iyi, ikinci B (vokal +3 dB). C, D, E daha kötü.
→ İlk versiyon tutuldu. Denenen tek değişikliklerin (protect 0.2, index 0.75/1.0, vokal ±3 dB, reverb %10/%35) hiçbiri ilkini geçmedi.

**Önce → sonra (tam şarkı, Model A):** Üzülmedin mi %72.7 → %77.3; Sıfır Tolerans %69.6 → %75.2; Düm Tek Tek %91.3 (değişmedi).
40 sn kliplerde ~10 pencere var, medyan birkaç puan oynuyor (Sıfır Tolerans klibi tam şarkı çevirisinde %63.6 → %55.5 çıktı), bu yüzden notlarda tam şarkı rakamları.
Zehra (miksli klipler): iki şarkıda da "sonra" daha iyi; kliplerde nakarat var.
**Teslim:** `outputs/odev/teslim/covers.zip` = cover1 (Üzülmedin mi 1:16–1:56), cover2 (Sıfır Tolerans 1:35–2:15), cover3 (Düm Tek Tek 0:28–1:08), 40 sn, 192 kbps + `notes.txt`. 2.9 MB.

## Ödev — Cover'lar web'de (6 Kasım)
**Fikir (Zehra):** "Kim söylüyor?" oyunu. Her şarkıda A/B: biri orijinal şarkıcı, biri AI Dua Lipa (taraf rastgele). "Dua Lipa bu" → cevap + ses benzerliği; sonda skor ve 3 cover'ın tamamı.
**Klipler (`web/public/clips/`, `outputs/odev/web_klipler.py`):** 30 sn, 192 kbps; cover ve orijinal aynı saniyeler: Üzülmedin mi 1:21–1:51, Sıfır Tolerans 1:40–2:10, Düm Tek Tek 0:33–1:03.
**Etiket:** cevaptan önce her iki klipte "İkisinden biri yapay zekâ ile üretilmiştir, Dua Lipa bu şarkıyı söylemedi" (cevabı ele vermesin diye); cevaptan sonra AI klipte tam etiket. Krediler, noindex, GitHub linki altta.
Repo public yapıldı (geçmişte ses/model/anahtar yok, kontrol edildi).
