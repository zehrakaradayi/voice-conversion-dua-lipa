import "./globals.css";

export const metadata = {
  title: "Kim söylüyor? — Dua Lipa ses klonu",
  description: "3 şarkı, iki kayıt: hangisi yapay zekâ ile klonlanmış Dua Lipa sesi? (Exposure AI Academy, Proje 3)",
  robots: { index: false, follow: false, googleBot: { index: false, follow: false } },
};

export const viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
