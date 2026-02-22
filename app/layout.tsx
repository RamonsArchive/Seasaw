import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Seasaw — Know What You're Agreeing To",
  description:
    "Seasaw analyzes Terms of Service and Privacy Policies using local AI, giving every service a TrustScore so you can make informed decisions.",
  keywords: ["terms of service", "privacy policy", "trust score", "AI analysis"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.variable}>
        {children}
      </body>
    </html>
  );
}
