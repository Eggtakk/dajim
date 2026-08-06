import type { Metadata } from "next";
import { IconSprite } from "@/components/icons/IconSprite";
import "./globals.css";

export const metadata: Metadata = {
  title: "다짐 — 소비 습관 코칭",
  description: "소비 습관을 예측하고, 목표를 세우고, 결과로 확인하는 다짐",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <IconSprite />
        {children}
      </body>
    </html>
  );
}
