import { Manrope, Unbounded } from "next/font/google";
import "./globals.css";

const baslik = Unbounded({ subsets: ["latin", "latin-ext"], weight: ["600", "700", "800", "900"], variable: "--font-baslik" });
const govde = Manrope({ subsets: ["latin", "latin-ext"], variable: "--font-govde" });

export const metadata = {
  title: "Kim söylüyor? — Dua Lipa ses klonu",
  description: "3 şarkı, iki kayıt: hangisi yapay zekâ ile klonlanmış Dua Lipa sesi? (Exposure AI Academy, Proje 3)",
  robots: { index: false, follow: false, googleBot: { index: false, follow: false } },
};

export const viewport = { width: "device-width", initialScale: 1, themeColor: "#0c0a0f" };

export default function RootLayout({ children }) {
  return (
    <html lang="tr" className={`${baslik.variable} ${govde.variable}`}>
      <body>{children}</body>
    </html>
  );
}
