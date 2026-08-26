import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aetheria - AI Grocery Inventory Management",
  description: "A production-grade AI-powered inventory system using computer vision to track shelf inventory automatically.",
};

import { ToastProvider } from "../components/ui/toast";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen bg-neutral-950 text-neutral-50" style={{ fontFamily: "'Outfit', sans-serif" }}>
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
