import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BRICK - Architectural PDF Assistant",
  description: "Query technical PDFs with AI-powered insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
