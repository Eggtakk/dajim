"use client";

/**
 * Client-side fetchers for the /api routes. Pages call these instead of
 * importing lib/mockData.ts directly — the data now genuinely travels over
 * HTTP, so swapping a route handler's body for a real backend call later
 * won't require touching any page component.
 */
import type {
  GoalSettings,
  HomeSummary,
  PredictionScenario,
  ResultData,
  ResultOutcome,
  ScenarioMode,
  TrackingReport,
  Transaction,
} from "./types";

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${url} → ${res.status}${body ? `: ${body}` : ""}`);
  }
  return res.json() as Promise<T>;
}

function goalSearchParams(goal: GoalSettings): URLSearchParams {
  return new URLSearchParams({
    categoryId: goal.categoryId,
    percent: String(goal.percent),
    durationMonths: String(goal.durationMonths),
    trackingDays: String(goal.trackingDays),
  });
}

export function fetchUser() {
  return getJSON<{ name: string; age: number; streakDays: number }>(
    "/api/user",
  );
}

export function fetchHomeSummary() {
  return getJSON<HomeSummary>("/api/home-summary");
}

export function fetchTransactions(account?: string) {
  const qs = account ? `?account=${encodeURIComponent(account)}` : "";
  return getJSON<{ transactions: Transaction[] }>(`/api/transactions${qs}`);
}

export function fetchPredictionScenario(
  mode: ScenarioMode,
  goal: GoalSettings,
) {
  const params = goalSearchParams(goal);
  params.set("mode", mode);
  return getJSON<PredictionScenario>(`/api/prediction-scenario?${params}`);
}

export function fetchTrackingReport(goal: GoalSettings) {
  return getJSON<TrackingReport>(
    `/api/tracking-report?${goalSearchParams(goal)}`,
  );
}

export function fetchResult(goal: GoalSettings, outcome: ResultOutcome) {
  const params = goalSearchParams(goal);
  params.set("outcome", outcome);
  return getJSON<ResultData>(`/api/result?${params}`);
}
