/**
 * Spending trend prediction model (docs/api-and-model-plan.md §2-2).
 *
 * Input is already day/week-aggregated history, not raw transaction rows —
 * aggregating a category's transactions into weekly totals is a query a
 * real backend does once (see lib/historicalSpend.ts for the mock stand-in
 * for that endpoint). This module is the "이동평균/선형 추세 외삽" step: fit
 * a least-squares line over completed weeks, blend it with the
 * still-in-progress current week's pace, and extrapolate to a full-month
 * projection. Upgrade path (per the doc) is a day-of-week/month-position
 * aware time series model once enough real data has accumulated.
 */

/** One week of a category's spend. All entries are expected to be complete
 *  (daysElapsed === 7) except optionally the last, which may be partial —
 *  the week containing "now". */
export interface WeeklySpendPoint {
  /** ISO date (YYYY-MM-DD) of the Monday this week starts on. */
  weekStart: string;
  /** Total spend in that week so far, in KRW. */
  totalWon: number;
  /** Days of the week elapsed so far, 1-7. 7 means the week is complete. */
  daysElapsed: number;
}

export interface TrendPrediction {
  /** Weekly totals, oldest → newest, capped at TREND_WEEKS points. The last
   *  point blends the current week's actual-so-far pace with the trend
   *  line's estimate for it — the "forecast" component. */
  trend: number[];
  /** Linear-trend extrapolation of this (in-progress) month's total spend. */
  projectedMonthWon: number;
  /** Actual total for the most recently completed calendar month. */
  lastMonthWon: number;
  /** projectedMonthWon vs lastMonthWon, rounded to the nearest percent. */
  changePct: number;
}

const TREND_WEEKS = 7;

interface LinearFit {
  slope: number;
  intercept: number;
}

/** Least-squares fit of y = intercept + slope * x over x = 0..ys.length-1. */
function fitLinearTrend(ys: number[]): LinearFit {
  const n = ys.length;
  if (n === 0) return { slope: 0, intercept: 0 };
  if (n === 1) return { slope: 0, intercept: ys[0] };

  const xMean = (n - 1) / 2;
  const yMean = ys.reduce((sum, y) => sum + y, 0) / n;
  let numerator = 0;
  let denominator = 0;
  ys.forEach((y, x) => {
    numerator += (x - xMean) * (y - yMean);
    denominator += (x - xMean) ** 2;
  });
  const slope = denominator === 0 ? 0 : numerator / denominator;
  return { slope, intercept: yMean - slope * xMean };
}

function parseISODate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function addUTCDays(date: Date, days: number): Date {
  const result = new Date(date.getTime());
  result.setUTCDate(result.getUTCDate() + days);
  return result;
}

function monthKey(date: Date): string {
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

function previousMonthKey(date: Date): string {
  const prev = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() - 1, 1));
  return monthKey(prev);
}

function daysInMonth(date: Date): number {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)).getUTCDate();
}

/**
 * The "now" this history implies: the last elapsed day of its final
 * (possibly partial) week. Other model modules (e.g. lib/trackingReport.ts)
 * reuse this instead of wall-clock time so cycle math stays consistent with
 * whichever mock/real history was passed in.
 */
export function inferNow(history: WeeklySpendPoint[]): Date {
  if (history.length === 0) return new Date();
  const last = history[history.length - 1];
  const daysElapsed = Math.min(7, Math.max(1, last.daysElapsed));
  return addUTCDays(parseISODate(last.weekStart), daysElapsed - 1);
}

export function predictCategoryTrend(history: WeeklySpendPoint[]): TrendPrediction {
  if (history.length === 0) {
    return { trend: [], projectedMonthWon: 0, lastMonthWon: 0, changePct: 0 };
  }

  const current = history[history.length - 1];
  const completed = history.slice(0, -1);
  const { slope, intercept } = fitLinearTrend(completed.map((p) => p.totalWon));

  const daysElapsed = Math.min(7, Math.max(1, current.daysElapsed));
  const paceEstimate = (current.totalWon / daysElapsed) * 7;
  const regressionEstimate = intercept + slope * completed.length;
  const weight = daysElapsed / 7;
  const blendedCurrentWeek =
    completed.length === 0
      ? paceEstimate
      : weight * paceEstimate + (1 - weight) * regressionEstimate;

  const trend = [
    ...completed.slice(-(TREND_WEEKS - 1)).map((p) => p.totalWon),
    blendedCurrentWeek,
  ].map((v) => Math.round(v));

  const now = inferNow(history);
  const currentMonthKey = monthKey(now);
  const lastMonthKey = previousMonthKey(now);

  const actualSoFarThisMonth = history
    .filter((p) => monthKey(parseISODate(p.weekStart)) === currentMonthKey)
    .reduce((sum, p) => sum + p.totalWon, 0);

  const lastMonthWon = history
    .filter((p) => monthKey(parseISODate(p.weekStart)) === lastMonthKey)
    .reduce((sum, p) => sum + p.totalWon, 0);

  const dailyRate = blendedCurrentWeek / 7;
  const daysRemainingInMonth = daysInMonth(now) - now.getUTCDate();
  const projectedMonthWon = actualSoFarThisMonth + dailyRate * daysRemainingInMonth;

  const changePct =
    lastMonthWon > 0
      ? Math.round(((projectedMonthWon - lastMonthWon) / lastMonthWon) * 100)
      : 0;

  return {
    trend,
    projectedMonthWon: Math.round(projectedMonthWon),
    lastMonthWon: Math.round(lastMonthWon),
    changePct,
  };
}
