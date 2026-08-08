import { getCategory } from "./categories";
import { formatPct } from "./format";
import type { CategoryId, GoalSettings, ResetSuggestion } from "./types";

/**
 * Goal reset / next-goal suggestions (docs/api-and-model-plan.md §2-5):
 * fixed rule-based templates combined from the gap between target and
 * actual reduction, plus which category is trending worst right now.
 * Upgrade path per the doc is ranking by which resets historically led to
 * a successful re-attempt, once there's real retry data to learn from.
 */
export interface CategoryTrend {
  categoryId: CategoryId;
  label: string;
  /** % change vs last month — positive means spend is increasing
   *  (predictCategoryTrend's sign convention). */
  changePct: number;
}

function pickWorstTrending(trends: CategoryTrend[]): CategoryTrend | null {
  if (trends.length === 0) return null;
  return [...trends].sort((a, b) => b.changePct - a.changePct)[0];
}

/** Suggestions shown after falling short of a goal: extend, ease, or
 *  redirect the effort at whichever other category is trending worst. */
export function suggestGoalReset(
  goal: GoalSettings,
  gapPct: number,
  otherCategoryTrends: CategoryTrend[],
): ResetSuggestion[] {
  const gap = Math.max(0, gapPct);
  const extendMonths = gap >= 15 ? 3 : gap >= 8 ? 2 : 1;
  const easedPercent = Math.max(5, goal.percent - Math.ceil(gap * 0.6));
  const category = getCategory(goal.categoryId);

  const suggestions: ResetSuggestion[] = [
    {
      id: "extend",
      title: `기간을 ${extendMonths}개월 더 연장하기`,
      description: "급하게 줄이기보다, 천천히 습관을 만들어가는 방법이에요.",
    },
    {
      id: "ease",
      title: `목표를 ${goal.percent}% → ${easedPercent}%로 완화하기`,
      description: "달성 가능한 수준부터 시작하면 다음 다짐이 더 쉬워져요.",
    },
  ];

  const worst = pickWorstTrending(otherCategoryTrends);
  if (worst && worst.changePct > 0) {
    suggestions.push({
      id: "switch",
      title: `${category.label} 대신 ${worst.label} 줄이기`,
      description: `최근 ${worst.label} 지출이 ${formatPct(worst.changePct)}로 늘었어요. 카테고리를 바꿔볼 수 있어요.`,
    });
  }

  return suggestions;
}

/** Suggestion shown after hitting a goal: point at whichever other
 *  category is trending worst as the next thing worth tackling. */
export function suggestNextGoal(
  goal: GoalSettings,
  otherCategoryTrends: CategoryTrend[],
): ResetSuggestion[] {
  const worst = pickWorstTrending(otherCategoryTrends);
  if (!worst) return [];

  const isGrowing = worst.changePct > 0;
  const suggestedPercent = isGrowing
    ? Math.min(30, Math.max(10, Math.round(Math.abs(worst.changePct) / 5) * 5))
    : 15;

  return [
    {
      id: `next-${worst.categoryId}`,
      title: `${worst.label} 소비 ${suggestedPercent}% 줄이기 · ${goal.durationMonths}개월`,
      description: isGrowing
        ? `최근 ${worst.label} 지출이 ${formatPct(worst.changePct)}로 늘고 있어요. 이번엔 ${worst.label}로 다짐해볼까요?`
        : `이번엔 ${worst.label} 소비도 함께 줄여볼까요?`,
    },
  ];
}
