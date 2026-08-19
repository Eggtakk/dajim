"""Next-month spend projection for AI Hub's pre-aggregated monthly panel
data (data/monthly_loader.py).

Unlike trend_model.py's weekly model, there's no partial "current period"
to blend here — every month in the AI Hub file is a closed, complete
period, not a still-accumulating one. So this is just a plain least-squares
linear trend fit over the historical monthly totals, extrapolated one step
forward — the same "선형 추세 외삽" idea as trend_model.py's weekly version,
without the within-month pace-blending that only makes sense for a
still-in-progress period. Reuses trend_model's regression/rounding helpers,
since that math doesn't depend on what a "period" means.
"""
from __future__ import annotations

from dataclasses import dataclass

from .trend_model import fit_linear_trend, round_half_up


@dataclass(frozen=True)
class MonthlyTrendPrediction:
    trend: list[int]  # historical monthly totals, oldest -> newest
    projected_next_month_won: int
    last_month_won: int
    change_pct: int


def predict_next_month(history: list[dict]) -> MonthlyTrendPrediction:
    """history: MonthlySpendPoint list (month/total_won dicts), oldest ->
    newest, as produced by data.monthly_loader.load_customer_monthly_spend.
    """
    if not history:
        return MonthlyTrendPrediction(
            trend=[], projected_next_month_won=0, last_month_won=0, change_pct=0
        )

    totals = [p["total_won"] for p in history]
    fit = fit_linear_trend(totals)
    projected = fit.intercept + fit.slope * len(totals)
    last = totals[-1]

    change_pct = round_half_up(((projected - last) / last) * 100) if last > 0 else 0

    return MonthlyTrendPrediction(
        trend=totals,
        projected_next_month_won=round_half_up(projected),
        last_month_won=last,
        change_pct=change_pct,
    )
