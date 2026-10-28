import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "LAN LMS",
  description: "Hệ thống quản lý học tập trong mạng LAN",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}