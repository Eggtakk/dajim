export type CategoryId = "delivery" | "cafe" | "shopping" | "subscription";

export interface CategoryMeta {
  id: CategoryId;
  label: string;
  icon: string;
  /** mock last-month spend in KRW, stands in for a real transactions aggregate */
  lastMonthSpend: number;
  /** mock month-to-date spend in KRW */
  thisMonthSpend: number;
}

export interface GoalSettings {
  categoryId: CategoryId;
  durationMonths: number;
  percent: number;
  trackingDays: number;
}

export type ScenarioMode = "neg" | "pos";

export interface PredictionScenario {
  mode: ScenarioMode;
  lead: string;
  metricLabel: string;
  metricValue: string;
  trend: number[];
  note: string;
}

export interface Transaction {
  id: string;
  merchant: string;
  day: string;
  time: string;
  categoryId: CategoryId;
  account: "카카오뱅크" | "신한카드";
  amountWon: number;
  icon: string;
}

export interface HomeSummary {
  totalSpendWon: number;
  totalSpendChangePct: number;
  goalProgressPct: number;
  trackingDaysLeft: number;
  trackingCycleIndex: number;
  trackingTotalCycles: number;
}

export interface CategoryDelta {
  categoryId: CategoryId;
  label: string;
  changePct: number;
}

export interface TrackingReport {
  cycleIndex: number;
  totalCycles: number;
  daysUntilNext: number;
  statusLabel: string;
  goalSeries: number[];
  actualSeries: number[];
  categoryDeltas: CategoryDelta[];
  headline: string;
}

export type ResultOutcome = "win" | "lose";

export interface ResetSuggestion {
  id: string;
  title: string;
  description: string;
}

export interface ResultData {
  outcome: ResultOutcome;
  targetPct: number;
  actualPct: number;
  savedWon: number;
  headline: string;
  body: string;
  suggestions: ResetSuggestion[];
}
