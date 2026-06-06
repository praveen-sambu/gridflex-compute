import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "GridFlex Compute",
  description: "Grid-aware scheduling dashboard for flexible AI/GPU workloads."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}