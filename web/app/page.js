"use client";
import { useEffect, useRef, useState } from "react";

const REPO = "https://github.com/zehrakaradayi/voice-conversion-dua-lipa";
const ETIKET = "Yapay zekâ ile üretilmiştir, Dua Lipa bu şarkıyı söylemedi";

// her cover: AI klibi (Dua Lipa sesi) ve orijinalin aynı 30 saniyesi
const SARKILAR = [
  { id: "cover1", sarki: "Üzülmedin mi", sanatci: "Simge Sağın", benzerlik: 77.3 },
  { id: "cover2", sarki: "Sıfır Tolerans", sanatci: "Hadise", benzerlik: 75.2 },
  { id: "cover3", sarki: "Düm Tek Tek", sanatci: "Hadise", benzerlik: 91.3 },
];

const klip = (s, ai) => `/clips/${s.id}${ai ? "" : "_orijinal"}.mp3`;

function Oynatici({ src, harf, oynayan, setOynayan, children, durum }) {
  const ses = useRef(null);
  const [oran, setOran] = useState(0);
  const caliyor = oynayan === src;

  useEffect(() => {
    const a = ses.current;
    if (caliyor) a.play().catch(() => setOynayan(null));
    else a.pause();
  }, [caliyor, setOynayan]);

  useEffect(() => {
    const a = ses.current;
    const tick = () => setOran(a.duration ? a.currentTime / a.duration : 0);
    const bitti = () => { setOynayan((o) => (o === src ? null : o)); a.currentTime = 0; setOran(0); };
    a.addEventListener("timeupdate", tick);
    a.addEventListener("ended", bitti);
    return () => { a.removeEventListener("timeupdate", tick); a.removeEventListener("ended", bitti); };
  }, [src, setOynayan]);

  const R = 34, C = 2 * Math.PI * R;
  return (
    <div className={`kayit ${durum || ""}`}>
      <button className="disk" onClick={() => setOynayan(caliyor ? null : src)}
              aria-label={`${harf} kaydını ${caliyor ? "durdur" : "çal"}`}>
        <svg viewBox="0 0 80 80" aria-hidden="true">
          <circle cx="40" cy="40" r={R} className="halka-iz" />
          <circle cx="40" cy="40" r={R} className="halka" strokeDasharray={C} strokeDashoffset={C * (1 - oran)} />
        </svg>
        <span className="harf">{harf}</span>
        <span className="ikon" aria-hidden="true">{caliyor ? "❚❚" : "▶"}</span>
      </button>
      <audio ref={ses} src={src} preload="metadata" />
      {children}
    </div>
  );
}

export default function Page() {
  const [ekran, setEkran] = useState("giris"); // giris | tur | son
  const [tur, setTur] = useState(0);
  const [aiSolda, setAiSolda] = useState([]); // her tur için AI klibi A tarafında mı
  const [cevaplar, setCevaplar] = useState([]); // her tur için doğru bildi mi
  const [oynayan, setOynayan] = useState(null);

  const basla = () => {
    setAiSolda(SARKILAR.map(() => Math.random() < 0.5));
    setCevaplar([]); setTur(0); setOynayan(null); setEkran("tur");
  };

  const s = SARKILAR[tur];
  const cevap = cevaplar[tur];
  const cevaplandi = cevap !== undefined;
  const taraflar = ekran === "tur"
    ? [{ harf: "A", ai: aiSolda[tur] }, { harf: "B", ai: !aiSolda[tur] }]
    : [];

  const sec = (ai) => { if (!cevaplandi) setCevaplar((c) => { const y = [...c]; y[tur] = ai; return y; }); };
  const sonraki = () => {
    setOynayan(null);
    if (tur + 1 < SARKILAR.length) setTur(tur + 1); else setEkran("son");
  };
  const skor = cevaplar.filter(Boolean).length;

  return (
    <main>
      <header className="ust">
        <p className="ust-etiket">Ses klonlama oyunu</p>
        <h1>Kim söylüyor?</h1>
      </header>

      {ekran === "giris" && (
        <section className="kart giris">
          <p className="buyuk">Her şarkıda iki kayıt var. Biri şarkının gerçek sahibi, diğeri <b>yapay zekâyla klonlanmış Dua Lipa sesi</b>.</p>
          <p>Dinle ve hangisinin Dua Lipa olduğunu bul. 3 şarkı, 30'ar saniye.</p>
          <div className="etiket">Bu sitedeki kayıtların yarısı yapay zekâ ile üretilmiştir. Dua Lipa bu şarkıları söylemedi.</div>
          <button className="ana" onClick={basla}>Başla</button>
          <p className="kucuk">Kulaklıkla daha zor 🎧</p>
        </section>
      )}

      {ekran === "tur" && (
        <section className="kart">
          <div className="ilerleme" aria-label={`Şarkı ${tur + 1} / ${SARKILAR.length}`}>
            {SARKILAR.map((_, i) => (
              <span key={i} className={i < tur ? (cevaplar[i] ? "dogru" : "yanlis") : i === tur ? "simdi" : ""} />
            ))}
          </div>
          <p className="sarki-baslik">“{s.sarki}”</p>
          <p className="sub">Şarkı: {s.sanatci}</p>

          <div className="ikili">
            {taraflar.map(({ harf, ai }) => (
              <Oynatici key={`${tur}-${harf}`} src={klip(s, ai)} harf={harf} oynayan={oynayan} setOynayan={setOynayan}
                        durum={cevaplandi ? (ai ? "ai" : "orijinal") : ""}>
                {!cevaplandi ? (
                  <button className="sec" onClick={() => sec(ai)}>Dua Lipa bu</button>
                ) : ai ? (
                  <p className="kim">Dua Lipa sesi <small>yapay zekâ</small></p>
                ) : (
                  <p className="kim">{s.sanatci} <small>orijinal kayıt</small></p>
                )}
                <p className="klip-etiket">{cevaplandi && !ai ? "Gerçek kayıt" : cevaplandi ? ETIKET : "İkisinden biri yapay zekâ ile üretilmiştir, Dua Lipa bu şarkıyı söylemedi"}</p>
              </Oynatici>
            ))}
          </div>

          {cevaplandi && (
            <div className={`sonuc ${cevap ? "dogru" : "yanlis"}`} role="status">
              <p className="sonuc-baslik">{cevap ? "Bildin!" : "Kandırdı!"}</p>
              <p>Ses benzerliği ölçümüne göre bu klonlanmış ses Dua Lipa'ya <b>%{s.benzerlik.toLocaleString("tr-TR")}</b> benziyor
                (%0 = {s.sanatci}, %100 = Dua Lipa'nın kendi kaydı).</p>
              <button className="ana" onClick={sonraki}>{tur + 1 < SARKILAR.length ? "Sıradaki şarkı →" : "Sonucu gör →"}</button>
            </div>
          )}
        </section>
      )}

      {ekran === "son" && (
        <>
          <section className="kart son">
            <p className="skor">{skor}<span>/{SARKILAR.length}</span></p>
            <p className="buyuk">{skor === 3 ? "Kulağın keskin, yapay zekâ seni kandıramadı." : skor === 0 ? "Yapay zekâ seni her seferinde kandırdı." : "Bazılarında yapay zekâ seni kandırdı."}</p>
            <p className="sub">Bu sesleri yapan ben bile Simge ile yapay zekâ Dua Lipa'yı kulakla zor ayırt ettim.</p>
            <button className="ana" onClick={basla}>Tekrar oyna</button>
          </section>

          <section className="kart">
            <h2>Üç cover</h2>
            {SARKILAR.map((x) => (
              <div key={x.id} className="liste-satir">
                <p><b>Dua Lipa</b>, {x.sanatci}'nin “{x.sarki}” şarkısını söylüyor</p>
                <div className="ikili kucuk-ikili">
                  <Oynatici src={klip(x, false)} harf="O" oynayan={oynayan} setOynayan={setOynayan} durum="orijinal">
                    <p className="kim">{x.sanatci} <small>orijinal</small></p>
                  </Oynatici>
                  <Oynatici src={klip(x, true)} harf="AI" oynayan={oynayan} setOynayan={setOynayan} durum="ai">
                    <p className="kim">Dua Lipa sesi <small>%{x.benzerlik.toLocaleString("tr-TR")} benzerlik</small></p>
                    <p className="klip-etiket">{ETIKET}</p>
                  </Oynatici>
                </div>
              </div>
            ))}
          </section>
        </>
      )}

      <footer className="kart alt">
        <h2>Krediler</h2>
        <dl>
          <dt>Şarkılar</dt><dd>“Üzülmedin mi”, Simge Sağın · “Sıfır Tolerans”, Hadise · “Düm Tek Tek”, Hadise. Tüm hakları sahiplerine aittir.</dd>
          <dt>Klonlanan ses</dt><dd>Dua Lipa, <i>Future Nostalgia</i> (2020) stüdyo kayıtlarından ayrılmış vokaller</dd>
          <dt>Model</dt><dd>RVC v2 (Applio), ~15 dk gerçek vokalle eğitildi. Model ve tam şarkılar yayınlanmaz; sitede yalnızca 30 saniyelik klipler var.</dd>
          <dt>Kullanım</dt><dd>Exposure AI Academy ders projesi, eğitim amaçlı, ticari değil.</dd>
        </dl>
        <p className="kucuk">Zehra Karadayı · <a href={REPO}>GitHub: {REPO.replace("https://", "")}</a></p>
      </footer>
    </main>
  );
}
