import type { Metadata } from "next";
import { DM_Sans, Sora, JetBrains_Mono } from "next/font/google";
import { AppProviders } from "@/contexts/app-providers";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
});

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Papyr — RAG",
  description: "PDF ingestion, hybrid search, and grounded chat",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${dmSans.variable} ${sora.variable} ${jetBrainsMono.variable} h-full`}
    >
      <body className="h-full bg-bg text-ink font-sans antialiased">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
