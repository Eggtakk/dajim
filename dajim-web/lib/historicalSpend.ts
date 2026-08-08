import type { CategoryId } from "./types";
import type { WeeklySpendPoint } from "./predictTrend";

/**
 * Mock stand-in for the backend query that aggregates a category's raw
 * transactions into weekly totals — the input predictCategoryTrend
 * (lib/predictTrend.ts) expects, per docs/api-and-model-plan.md §2-2.
 * Once /transactions is backed by a real feed, this becomes a GROUP BY
 * week SQL query (or equivalent) over lib/rawTransactions.ts's real
 * successor, scoped to a category.
 *
 * Each series is 8 completed weeks followed by the current, still
 * in-progress week (daysElapsed < 7).
 */
const HISTORY: Record<CategoryId, WeeklySpendPoint[]> = {
  delivery: [
    { weekStart: "2026-06-08", totalWon: 118000, daysElapsed: 7 },
    { weekStart: "2026-06-15", totalWon: 124000, daysElapsed: 7 },
    { weekStart: "2026-06-22", totalWon: 129000, daysElapsed: 7 },
    { weekStart: "2026-06-29", totalWon: 137000, daysElapsed: 7 },
    { weekStart: "2026-07-06", totalWon: 142000, daysElapsed: 7 },
    { weekStart: "2026-07-13", totalWon: 150000, daysElapsed: 7 },
    { weekStart: "2026-07-20", totalWon: 158000, daysElapsed: 7 },
    { weekStart: "2026-07-27", totalWon: 167000, daysElapsed: 7 },
    { weekStart: "2026-08-03", totalWon: 98000, daysElapsed: 4 },
  ],
  cafe: [
    { weekStart: "2026-06-08", totalWon: 17500, daysElapsed: 7 },
    { weekStart: "2026-06-15", totalWon: 18200, daysElapsed: 7 },
    { weekStart: "2026-06-22", totalWon: 17800, daysElapsed: 7 },
    { weekStart: "2026-06-29", totalWon: 19000, daysElapsed: 7 },
    { weekStart: "2026-07-06", totalWon: 18700, daysElapsed: 7 },
    { weekStart: "2026-07-13", totalWon: 19600, daysElapsed: 7 },
    { weekStart: "2026-07-20", totalWon: 20100, daysElapsed: 7 },
    { weekStart: "2026-07-27", totalWon: 20800, daysElapsed: 7 },
    { weekStart: "2026-08-03", totalWon: 12400, daysElapsed: 4 },
  ],
  shopping: [
    { weekStart: "2026-06-08", totalWon: 58000, daysElapsed: 7 },
    { weekStart: "2026-06-15", totalWon: 55000, daysElapsed: 7 },
    { weekStart: "2026-06-22", totalWon: 56500, daysElapsed: 7 },
    { weekStart: "2026-06-29", totalWon: 52000, daysElapsed: 7 },
    { weekStart: "2026-07-06", totalWon: 50000, daysElapsed: 7 },
    { weekStart: "2026-07-13", totalWon: 48500, daysElapsed: 7 },
    { weekStart: "2026-07-20", totalWon: 46000, daysElapsed: 7 },
    { weekStart: "2026-07-27", totalWon: 44500, daysElapsed: 7 },
    { weekStart: "2026-08-03", totalWon: 24000, daysElapsed: 4 },
  ],
  subscription: [
    { weekStart: "2026-06-08", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-06-15", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-06-22", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-06-29", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-07-06", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-07-13", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-07-20", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-07-27", totalWon: 10475, daysElapsed: 7 },
    { weekStart: "2026-08-03", totalWon: 5985, daysElapsed: 4 },
  ],
};

export function getWeeklySpendHistory(categoryId: CategoryId): WeeklySpendPoint[] {
  return HISTORY[categoryId];
}
