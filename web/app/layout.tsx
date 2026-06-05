import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Research Perks Radar",
  description:
    "An open, auto-updating radar for research perks — free AI credits, funding, grants, software, datasets, awards, and travel support.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
