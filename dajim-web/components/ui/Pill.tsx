import type { ReactNode } from "react";

type Tone = "warn" | "good" | "neutral" | "streak";

export function Pill({ tone, children }: { tone: Tone; children: ReactNode }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}
