import type { WeeklySpendPoint } from "./predictTrend";

/**
 * Tracking report generation (docs/api-and-model-plan.md §2-4): aggregation
 * plus threshold classification, same spirit as predictCategoryTrend but
 * scoped to the user's tracking cadence (3/7/14 days) instead of a month.
 */

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/** Spreads each week's total evenly across the days that have elapsed in
 *  it. A real backend would sum actual daily transaction totals instead —
 *  this is the same simplification predictCategoryTrend makes for months. */
function toDailyAmounts(history: WeeklySpendPoint[]): number[] {
  const days: number[] = [];
  for (const point of history) {
    const elapsed = Math.min(7, Math.max(1, point.daysElapsed));
    const perDay = point.totalWon / elapsed;
    for (let i = 0; i < elapsed; i++) days.push(perDay);
  }
  return days;
}

/**
 * % change in spend during the most recent `trackingDays` vs the daily rate
 * from just before that window — the tracking-cycle analog of
 * predictCategoryTrend's month-over-month comparison. Positive means spend
 * went up, matching predictCategoryTrend/simulateGoalAchievement's sign
 * convention.
 */
export function computeTrackingWindowChangePct(
  history: WeeklySpendPoint[],
  trackingDays: number,
): number {
  const daily = toDailyAmounts(history);
  if (daily.length <= trackingDays) return 0;

  const windowActual = daily.slice(-trackingDays).reduce((sum, v) => sum + v, 0);
  const before = daily.slice(0, -trackingDays);
  const beforeDailyAvg = before.reduce((sum, v) => sum + v, 0) / before.length;
  const windowExpected = beforeDailyAvg * trackingDays;

  if (windowExpected === 0) return 0;
  return Math.round(((windowActual - windowExpected) / windowExpected) * 100);
}

export type StatusTone = "good" | "warn" | "neutral";

export interface StatusClassification {
  label: string;
  tone: StatusTone;
}

/**
 * Threshold classification (docs §2-4): actual reduction >= 1.1x the target
 * is "초과 달성", >= 0.9x is "on track", otherwise behind or reversing.
 */
export function classifyTrackingStatus(
  windowChangePct: number,
  targetPct: number,
): StatusClassification {
  const reductionPct = -windowChangePct;
  if (targetPct <= 0) return { label: "목표 진행 중", tone: "neutral" };
  if (reductionPct >= targetPct * 1.1) return { label: "목표 초과 달성 중", tone: "good" };
  if (reductionPct >= targetPct * 0.9) return { label: "목표대로 가고 있어요", tone: "good" };
  if (reductionPct >= 0) return { label: "목표에 조금 못 미치고 있어요", tone: "warn" };
  return { label: "목표와 반대로 가고 있어요", tone: "warn" };
}

export interface TrackingCycle {
  cycleIndex: number;
  totalCycles: number;
  daysUntilNext: number;
}

export function computeTrackingCycle(
  goalStartDate: string,
  now: Date,
  trackingDays: number,
  durationMonths: number,
): TrackingCycle {
  const [y, m, d] = goalStartDate.split("-").map(Number);
  const start = new Date(Date.UTC(y, m - 1, d));
  const daysSinceStart = Math.max(0, Math.round((now.getTime() - start.getTime()) / MS_PER_DAY));

  const totalCycles = Math.max(1, Math.ceil((durationMonths * 30) / trackingDays));
  const cycleIndex = Math.min(totalCycles, Math.floor(daysSinceStart / trackingDays) + 1);
  const daysUntilNext = trackingDays - (daysSinceStart % trackingDays);

  return { cycleIndex, totalCycles, daysUntilNext };
}

/**
 * Straight declining line from 100 to (100 - totalReductionPct), clamped to
 * the DualSparkline chart's expected 45-100 display range so an
 * increasing-spend category never renders outside the chart.
 */
export function buildIndexSeries(totalReductionPct: number, points: number): number[] {
  const clamp = (v: number) => Math.min(100, Math.max(45, v));
  return Array.from({ length: points }, (_, i) =>
    Math.round(clamp(100 - (totalReductionPct * i) / (points - 1))),
  );
}
