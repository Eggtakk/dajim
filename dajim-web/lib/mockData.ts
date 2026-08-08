/**
 * Mock data layer, now called from the /api route handlers instead of
 * directly from page components (see lib/api.ts for the client side).
 *
 * Every function here stands in for a future call to the prediction
 * algorithm / model backend. Signatures are shaped the way a real API
 * response would be (given the user's goal settings, return a scenario /
 * report / result) so that swapping the body for a real computation later
 * doesn't require touching any route handler or page component.
 *
 * Raw transactions live in lib/rawTransactions.ts and get categorized by
 * lib/categorize.ts inside app/api/transactions/route.ts.
 */
import { CATEGORIES, getCategory } from "./categories";
import { formatPct, formatWon } from "./format";
import { getWeeklySpendHistory } from "./historicalSpend";
import { eulReul } from "./korean";
import { predictCategoryTrend } from "./predictTrend";
import { simulateGoalAchievement } from "./simulateGoal";
import type {
  CategoryDelta,
  GoalSettings,
  HomeSummary,
  PredictionScenario,
  ResultData,
  ScenarioMode,
  TrackingReport,
} from "./types";

const SAVING_GOAL_WON = 320000;

export function getUser() {
  return { name: "김지은", age: 28, streakDays: 42 };
}

export function getHomeSummary(): HomeSummary {
  return {
    totalSpendWon: 812400,
    totalSpendChangePct: 15,
    goalProgressPct: 32,
    trackingDaysLeft: 3,
    trackingCycleIndex: 2,
    trackingTotalCycles: 4,
  };
}

function getBaselineTrend(goal: GoalSettings) {
  return predictCategoryTrend(getWeeklySpendHistory(goal.categoryId));
}

export function getPredictionScenario(
  mode: ScenarioMode,
  goal: GoalSettings,
): PredictionScenario {
  const category = getCategory(goal.categoryId);
  const baseline = getBaselineTrend(goal);

  if (mode === "neg") {
    return {
      mode,
      lead: `지금처럼 ${category.label} 소비를 지속하다가는 1개월 이내로 이번 달 저축 목표(${formatWon(SAVING_GOAL_WON)}) 달성이 어려워질 것으로 예측돼요.`,
      metricLabel: `${category.label} 지출 전월 대비`,
      metricValue: formatPct(baseline.changePct),
      trend: baseline.trend,
      note: "최근 8주 소비 패턴 기반 예측이에요.",
    };
  }

  const simulation = simulateGoalAchievement(baseline, goal.percent, SAVING_GOAL_WON);
  const direction = simulation.changePct <= 0 ? "감소" : "증가";
  const achievability = simulation.goalAchievable
    ? `저축 목표(${formatWon(SAVING_GOAL_WON)}) 달성이 가능해요.`
    : `저축 목표(${formatWon(SAVING_GOAL_WON)})에는 ${formatWon(SAVING_GOAL_WON - simulation.savedWon)} 부족해요.`;

  return {
    mode,
    lead: `${eulReul(category.label)} 주 1회로 줄이면 이번 달 소비량이 전월 대비 ${Math.abs(simulation.changePct)}% ${direction}해요. ${achievability}`,
    metricLabel: "예상 이번 달 소비 전월 대비",
    metricValue: formatPct(simulation.changePct),
    trend: simulation.trend,
    note: "최근 8주 소비 패턴 기반 예측이에요.",
  };
}

export function getExpectedSavingWon(goal: GoalSettings): number {
  const simulation = simulateGoalAchievement(
    getBaselineTrend(goal),
    goal.percent,
    SAVING_GOAL_WON,
  );
  return simulation.savedWon;
}

export function getBaselineMonthSpendWon(goal: GoalSettings): number {
  return getBaselineTrend(goal).projectedMonthWon;
}

export function getTrackingReport(goal: GoalSettings): TrackingReport {
  const category = getCategory(goal.categoryId);
  const otherCategories = CATEGORIES.filter((c) => c.id !== category.id);
  const categoryDeltas: CategoryDelta[] = [
    { categoryId: category.id, label: category.label, changePct: -22 },
    ...otherCategories.map((c, i) => ({
      categoryId: c.id,
      label: c.label,
      changePct: [5, -3, 0][i] ?? 0,
    })),
  ];

  return {
    cycleIndex: 2,
    totalCycles: 4,
    daysUntilNext: 3,
    statusLabel: "목표 초과 달성 중",
    goalSeries: [100, 96, 92, 88, 84, 80, 76, 72],
    actualSeries: [100, 94, 89, 80, 74, 66, 58, 52],
    categoryDeltas,
    headline: `이번 ${goal.trackingDays}일간 ${category.label} 소비 -22%, 목표(-${goal.percent}%)보다 잘 하고 있어요.`,
  };
}

export function getResultData(
  goal: GoalSettings,
  outcome: "win" | "lose",
): ResultData {
  const category = getCategory(goal.categoryId);

  if (outcome === "win") {
    return {
      outcome,
      targetPct: goal.percent,
      actualPct: goal.percent + 4,
      savedWon: 46800,
      headline: `${goal.durationMonths}개월간의 다짐, 완주했어요`,
      body: `${category.label} 소비를 목표보다 더 줄였고, 이번 달 저축 목표도 달성했어요.`,
      suggestions: [
        {
          id: "next-cafe",
          title: "카페 소비 15% 줄이기 · 2개월",
          description:
            "최근 두 달간 카페 지출이 꾸준히 늘고 있어요. 이번엔 카페로 다짐해볼까요?",
        },
      ],
    };
  }

  return {
    outcome,
    targetPct: goal.percent,
    actualPct: Math.max(1, Math.round(goal.percent * 0.3)),
    savedWon: 11200,
    headline: "목표에는 못 미쳤지만, 시작한 것만으로 의미 있어요",
    body: `${category.label} 소비가 예상보다 줄지 않았어요. 방법을 조금 바꿔서 다시 다짐해볼까요?`,
    suggestions: [
      {
        id: "extend",
        title: "기간을 2개월 더 연장하기",
        description: "급하게 줄이기보다, 천천히 습관을 만들어가는 방법이에요.",
      },
      {
        id: "ease",
        title: `목표를 ${goal.percent}% → ${Math.max(5, goal.percent - 8)}%로 완화하기`,
        description:
          "달성 가능한 수준부터 시작하면 다음 다짐이 더 쉬워져요.",
      },
      {
        id: "switch",
        title: `${category.label} 대신 구독서비스 줄이기`,
        description: "최근 구독서비스 지출이 늘었어요. 카테고리를 바꿔볼 수 있어요.",
      },
    ],
  };
}
