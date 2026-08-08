/**
 * Mock stand-in for the goals.started_at a real `POST /goals` record would
 * store (docs/api-and-model-plan.md §1) — the "목표 시작일" input
 * lib/trackingReport.ts needs to work out which tracking cycle we're in.
 * Anchored a couple weeks before lib/historicalSpend.ts's implicit "now"
 * (2026-08-06) so the cycle math lines up with that mock history.
 */
export function getGoalStartDate(): string {
  return "2026-07-26";
}
