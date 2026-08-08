import type { TrendPrediction } from "./predictTrend";

/**
 * Goal-achievement what-if simulation (docs/api-and-model-plan.md §2-3).
 *
 * Input is §2-2's baseline forecast (predictCategoryTrend) plus the
 * reduction rate the user picked on the goal slider. Per the doc, arithmetic
 * scaling of the baseline — 기준 예측치 × (1 - 감소율) — is enough to start;
 * accounting for cross-category spend transfer ("cut delivery, cafe goes
 * up") is the upgrade path once there's real data to model it from.
 */
export interface GoalSimulation {
  /** Baseline trend scaled by (1 - reductionPercent/100), same shape as
   *  TrendPrediction.trend. */
  trend: number[];
  /** Projected spend for this month if the goal's reduction is held to. */
  projectedMonthWon: number;
  /** Amount saved vs the baseline's "if nothing changes" projection. */
  savedWon: number;
  /** projectedMonthWon vs the baseline's lastMonthWon, nearest percent. */
  changePct: number;
  /** Whether savedWon alone covers the flat monthly savings goal. */
  goalAchievable: boolean;
}

export function simulateGoalAchievement(
  baseline: TrendPrediction,
  reductionPercent: number,
  savingsGoalWon: number,
): GoalSimulation {
  const factor = 1 - reductionPercent / 100;
  const projectedMonthWon = baseline.projectedMonthWon * factor;
  const savedWon = baseline.projectedMonthWon - projectedMonthWon;
  const changePct =
    baseline.lastMonthWon > 0
      ? Math.round(
          ((projectedMonthWon - baseline.lastMonthWon) / baseline.lastMonthWon) * 100,
        )
      : 0;

  return {
    trend: baseline.trend.map((v) => Math.round(v * factor)),
    projectedMonthWon: Math.round(projectedMonthWon),
    savedWon: Math.round(savedWon),
    changePct,
    goalAchievable: savedWon >= savingsGoalWon,
  };
}
