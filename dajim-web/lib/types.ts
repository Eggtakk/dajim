export type CategoryId = "delivery" | "cafe" | "shopping" | "subscription";

export interface CategoryMeta {
  id: CategoryId;
  label: string;
  icon: string;
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

/**
 * Was a fixed "카카오뱅크" | "신한카드" union while transactions were
 * hardcoded. Once a real feed (mock or Plaid Sandbox) can return any
 * institution name, this has to be a plain string.
 */
export type Account = string;

/** What a real open-banking/card feed gives us — no category yet. */
export interface RawTransaction {
  id: string;
  merchant: string;
  day: string;
  time: string;
  account: Account;
  amountWon: number;
}

/** A RawTransaction after the classifier (lib/categorize.ts) has tagged it. */
export interface Transaction extends RawTransaction {
  categoryId: CategoryId;
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
  statusTone: "good" | "warn" | "neutral";
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
