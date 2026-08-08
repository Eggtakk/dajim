import { DEFAULT_GOAL } from "./goal";
import type { CategoryId, GoalSettings } from "./types";

/** Reconstructs GoalSettings from the query string a client sends. */
export function parseGoalParams(searchParams: URLSearchParams): GoalSettings {
  return {
    categoryId:
      (searchParams.get("categoryId") as CategoryId | null) ??
      DEFAULT_GOAL.categoryId,
    percent: Number(searchParams.get("percent") ?? DEFAULT_GOAL.percent),
    durationMonths: Number(
      searchParams.get("durationMonths") ?? DEFAULT_GOAL.durationMonths,
    ),
    trackingDays: Number(
      searchParams.get("trackingDays") ?? DEFAULT_GOAL.trackingDays,
    ),
  };
}
