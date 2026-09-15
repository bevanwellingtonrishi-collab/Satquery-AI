import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "SatQuery AI — Satellite Intelligence Platform",
  description: "Ask questions about satellite imagery. Get structured AI-powered intelligence for geospatial decision-making.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-[#070b14] text-gray-100 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
