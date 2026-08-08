import { CATEGORIES } from "./categories";
import { getWeeklySpendHistory } from "./historicalSpend";
import { predictCategoryTrend } from "./predictTrend";

/**
 * Savings goal estimation (docs/api-and-model-plan.md §2-6), replacing the
 * SAVING_GOAL_WON constant. The doc allows either deriving this from the
 * user's income/spending pattern or collecting it directly during
 * onboarding. There's no income signal to work from yet (§1's user/account
 * APIs don't collect it) and no goal-input step for it either, so this
 * derives a goal from the one real signal already available — this
 * month's projected spend across every tracked category (§2-2's
 * predictCategoryTrend) — instead of a fixed number. Once onboarding can
 * collect income or the user can set an explicit target, that should take
 * priority over this derived default.
 */
const SUGGESTED_SAVINGS_RATE = 0.15;
const MIN_GOAL_WON = 50000;
const ROUND_TO_WON = 10000;

export function estimateSavingsGoalWon(): number {
  const totalMonthlySpendWon = CATEGORIES.reduce((sum, category) => {
    const { projectedMonthWon } = predictCategoryTrend(getWeeklySpendHistory(category.id));
    return sum + projectedMonthWon;
  }, 0);

  const suggested = totalMonthlySpendWon * SUGGESTED_SAVINGS_RATE;
  return Math.max(MIN_GOAL_WON, Math.round(suggested / ROUND_TO_WON) * ROUND_TO_WON);
}
