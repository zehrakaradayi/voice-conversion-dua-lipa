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

const klip = (s, ai) => `clips/${s.id}${ai ? "" : "_orijinal"}.mp3`;
const yuzde = (x) => `%${x.toLocaleString("tr-TR")}`;

function Serit() {
  const metin = "Yapay zekâ ile üretilmiştir ✦ Dua Lipa bu şarkıları söylemedi ✦ ";
  return (
    <div className="serit" role="note" aria-label="Yapay zekâ ile üretilmiştir. Dua Lipa bu şarkıları söylemedi.">
      <div className="serit-ic" aria-hidden="true">{metin.repeat(6)}</div>
    </div>
  );
}

// dönen plak: tıklayınca çalar; halka ilerlemeyi, damga cevabı gösterir
function Plak({ src, harf, renk, oynayan, setOynayan, damga, kucuk }) {
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

  const R = 48, C = 2 * Math.PI * R;
  return (
    <div className={`deck ${kucuk ? "kucuk" : ""} ${caliyor ? "caliyor" : ""}`} style={{ "--renk": renk }}>
      <button className="plak-dugme" onClick={() => setOynayan(caliyor ? null : src)}
              aria-label={`${harf} kaydını ${caliyor ? "durdur" : "çal"}`} aria-pressed={caliyor}>
        <svg className="halka" viewBox="0 0 100 100" aria-hidden="true">
          <circle cx="50" cy="50" r={R} className="halka-iz" />
          <circle cx="50" cy="50" r={R} className="halka-dolu" strokeDasharray={C} strokeDashoffset={C * (1 - oran)} />
        </svg>
        <span className="plak">
          <span className="plak-orta"><b>{harf}</b><i>{caliyor ? "❚❚" : "▶"}</i></span>
        </span>
        <span className="kol" aria-hidden="true" />
        {damga && <span className={`damga ${damga}`}>{damga === "ai" ? "Yapay zekâ" : "Gerçek"}</span>}
      </button>
      <span className="eq" aria-hidden="true"><i /><i /><i /><i /><i /></span>
      <audio ref={ses} src={src} preload="metadata" />
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
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const s = SARKILAR[tur];
  const cevap = cevaplar[tur];
  const cevaplandi = cevap !== undefined;
  const taraflar = ekran === "tur"
    ? [{ harf: "A", renk: "var(--a)", ai: aiSolda[tur] }, { harf: "B", renk: "var(--b)", ai: !aiSolda[tur] }]
    : [];

  const sec = (ai) => { if (!cevaplandi) setCevaplar((c) => { const y = [...c]; y[tur] = ai; return y; }); };
  const sonraki = () => {
    setOynayan(null);
    if (tur + 1 < SARKILAR.length) setTur(tur + 1); else setEkran("son");
  };
  const skor = cevaplar.filter(Boolean).length;

  return (
    <>
      <Serit />
      <main>
        {ekran === "giris" && (
          <section className="giris">
            <div className="giris-plaklar" aria-hidden="true"><span /><span /></div>
            <p className="ust-yazi">Ses klonlama oyunu · 3 şarkı</p>
            <h1>Kim<br />söylü&shy;yor?</h1>
            <p className="giris-metin">
              Her şarkıda iki plak var. Biri şarkının gerçek sahibi, diğeri <mark>yapay zekâyla klonlanmış Dua Lipa</mark>.
              Dinle, sahteyi bul.
            </p>
            <button className="ana" onClick={basla}>Plakları çevir →</button>
            <p className="ipucu">🎧 Kulaklıkla daha zor</p>
          </section>
        )}

        {ekran === "tur" && (
          <section className="tur">
            <div className="tur-ust">
              <span className="tur-no">Tur {tur + 1}/{SARKILAR.length}</span>
              <span className="pipler" aria-hidden="true">
                {SARKILAR.map((_, i) => (
                  <i key={i} className={i < tur || (i === tur && cevaplandi) ? (cevaplar[i] ? "dogru" : "yanlis") : i === tur ? "simdi" : ""} />
                ))}
              </span>
            </div>
            <h2 className="sarki">“{s.sarki}”</h2>
            <p className="kimin">şarkının sahibi: <b>{s.sanatci}</b></p>
            <p className="soru">{cevaplandi ? " " : "Hangisi Dua Lipa?"}</p>

            <div className="decks">
              {taraflar.map(({ harf, renk, ai }) => (
                <div key={`${tur}-${harf}`} className="deck-kolon">
                  <Plak src={klip(s, ai)} harf={harf} renk={renk} oynayan={oynayan} setOynayan={setOynayan}
                        damga={cevaplandi ? (ai ? "ai" : "gercek") : null} />
                  {!cevaplandi ? (
                    <button className="sec" onClick={() => sec(ai)}>Dua Lipa bu</button>
                  ) : (
                    <p className={`kim ${ai ? "ai" : ""}`}>{ai ? "Dua Lipa klonu" : s.sanatci}</p>
                  )}
                  <p className="klip-etiket">
                    {!cevaplandi ? "İkisinden biri yapay zekâ ile üretilmiştir, Dua Lipa bu şarkıyı söylemedi" : ai ? ETIKET : "Orijinal kayıt"}
                  </p>
                </div>
              ))}
            </div>

            {cevaplandi && (
              <div className={`sonuc ${cevap ? "dogru" : "yanlis"}`} role="status">
                <p className="sonuc-baslik">{cevap ? "Yakaladın!" : "Kandırıldın!"}</p>
                <p className="sonuc-metin">Klon bu şarkıda Dua Lipa'ya <b>{yuzde(s.benzerlik)}</b> benziyor.</p>
                <div className="olcek" aria-hidden="true">
                  <span style={{ width: `${Math.min(s.benzerlik, 100)}%` }} />
                </div>
                <p className="olcek-yazi"><span>{s.sanatci}</span><span>Dua Lipa</span></p>
                <button className="ana" onClick={sonraki}>{tur + 1 < SARKILAR.length ? "Sıradaki plak →" : "Sonucu gör →"}</button>
              </div>
            )}
          </section>
        )}

        {ekran === "son" && (
          <section className="son">
            <p className="ust-yazi">Sonuç</p>
            <p className="skor">{skor}<span>/{SARKILAR.length}</span></p>
            <p className="son-metin">{skor === 3 ? "Kulağın keskin. Yapay zekâ seni kandıramadı." : skor === 0 ? "Yapay zekâ seni her seferinde kandırdı." : "Yapay zekâ seni bazen kandırdı."}</p>
            <p className="son-alt">Bu sesleri yapan ben bile Simge ile yapay zekâ Dua Lipa'yı kulakla zor ayırt ettim.</p>
            <button className="ana" onClick={basla}>Tekrar oyna ↻</button>

            <h2 className="raf-baslik">Raf</h2>
            <ul className="raf">
              {SARKILAR.map((x) => (
                <li key={x.id}>
                  <div className="raf-yazi">
                    <b>“{x.sarki}”</b>
                    <span>{x.sanatci} · Dua Lipa klonu {yuzde(x.benzerlik)}</span>
                    <small>{ETIKET}</small>
                  </div>
                  <div className="raf-plaklar">
                    <Plak kucuk src={klip(x, false)} harf="Orj" renk="var(--b)" oynayan={oynayan} setOynayan={setOynayan} />
                    <Plak kucuk src={klip(x, true)} harf="AI" renk="var(--ai)" oynayan={oynayan} setOynayan={setOynayan} />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>

      <footer className="alt">
        <p>
          Şarkılar: Simge Sağın “Üzülmedin mi”, Hadise “Sıfır Tolerans” ve “Düm Tek Tek” · Klonlanan ses: Dua Lipa · haklar sahiplerine aittir
        </p>
        <details>
          <summary>Ayrıntılar</summary>
          <p>Ses modeli RVC v2 (Applio), Dua Lipa'nın <i>Future Nostalgia</i> (2020) kayıtlarından ayrılmış ~15 dk vokalle eğitildi.
            Benzerlik: ECAPA ses parmak izi, %0 = orijinal şarkıcı, %100 = Dua Lipa'nın kendi kaydı.
            Model ve tam şarkılar yayınlanmaz; sitede yalnızca 30 saniyelik klipler var.
            Exposure AI Academy ders projesi, eğitim amaçlı, ticari değil.</p>
        </details>
        <p>Zehra Karadayı · <a href={REPO}>GitHub</a></p>
      </footer>
    </>
  );
}
