"""Spending trend prediction model — Python port of
dajim-web/lib/predictTrend.ts (docs/api-and-model-plan.md §2-2).

Input is category-level weekly spend history, the shape
data.loader.aggregate_weekly_spend() produces. This is the "이동평균/선형
추세 외삽" step: fit a least-squares line over completed weeks, blend it
with the still-in-progress current week's pace, and extrapolate to a
full-month projection. Upgrade path is a day-of-week/month-position aware
time series model (exponential smoothing, Prophet, ...) once enough real
data has accumulated.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import TypedDict

TREND_WEEKS = 7


class WeeklySpendPoint(TypedDict):
    week_start: str  # ISO date (YYYY-MM-DD), Monday this week starts on
    total_won: int
    days_elapsed: int  # 1-7, 7 means the week is fully elapsed


@dataclass(frozen=True)
class TrendPrediction:
    trend: list[int]
    projected_month_won: int
    last_month_won: int
    change_pct: int


@dataclass(frozen=True)
class _LinearFit:
    slope: float
    intercept: float


def _round_half_up(value: float) -> int:
    """Match JS's Math.round (rounds half toward +Infinity), not Python's
    round() (rounds half to even) — needed for exact numeric parity with
    predictTrend.ts."""
    return math.floor(value + 0.5)


def _fit_linear_trend(ys: list[float]) -> _LinearFit:
    """Least-squares fit of y = intercept + slope * x over x = 0..len(ys)-1."""
    n = len(ys)
    if n == 0:
        return _LinearFit(slope=0.0, intercept=0.0)
    if n == 1:
        return _LinearFit(slope=0.0, intercept=ys[0])

    x_mean = (n - 1) / 2
    y_mean = sum(ys) / n
    numerator = 0.0
    denominator = 0.0
    for x, y in enumerate(ys):
        numerator += (x - x_mean) * (y - y_mean)
        denominator += (x - x_mean) ** 2
    slope = 0.0 if denominator == 0 else numerator / denominator
    return _LinearFit(slope=slope, intercept=y_mean - slope * x_mean)


def _parse_iso_date(iso: str) -> dt.date:
    return dt.date.fromisoformat(iso)


def _month_key(date: dt.date) -> str:
    return f"{date.year:04d}-{date.month:02d}"


def _previous_month_key(date: dt.date) -> str:
    last_of_prev_month = date.replace(day=1) - dt.timedelta(days=1)
    return _month_key(last_of_prev_month)


def _days_in_month(date: dt.date) -> int:
    if date.month == 12:
        next_month = date.replace(year=date.year + 1, month=1, day=1)
    else:
        next_month = date.replace(month=date.month + 1, day=1)
    return (next_month - dt.timedelta(days=1)).day


def infer_now(history: list[WeeklySpendPoint]) -> dt.date:
    """The 'now' this history implies: the last elapsed day of its final
    (possibly partial) week. Mirrors predictTrend.ts's inferNow() — other
    model modules should reuse this instead of wall-clock time so cycle math
    stays consistent with whichever history was passed in."""
    if not history:
        return dt.date.today()
    last = history[-1]
    days_elapsed = min(7, max(1, last["days_elapsed"]))
    return _parse_iso_date(last["week_start"]) + dt.timedelta(days=days_elapsed - 1)


def predict_category_trend(history: list[WeeklySpendPoint]) -> TrendPrediction:
    if not history:
        return TrendPrediction(trend=[], projected_month_won=0, last_month_won=0, change_pct=0)

    current = history[-1]
    completed = history[:-1]
    fit = _fit_linear_trend([p["total_won"] for p in completed])

    days_elapsed = min(7, max(1, current["days_elapsed"]))
    pace_estimate = (current["total_won"] / days_elapsed) * 7
    regression_estimate = fit.intercept + fit.slope * len(completed)
    weight = days_elapsed / 7
    blended_current_week = (
        pace_estimate
        if not completed
        else weight * pace_estimate + (1 - weight) * regression_estimate
    )

    trend_tail = completed[-(TREND_WEEKS - 1):]
    trend = [_round_half_up(p["total_won"]) for p in trend_tail] + [
        _round_half_up(blended_current_week)
    ]

    now = infer_now(history)
    current_month_key = _month_key(now)
    last_month_key = _previous_month_key(now)

    actual_so_far_this_month = sum(
        p["total_won"]
        for p in history
        if _month_key(_parse_iso_date(p["week_start"])) == current_month_key
    )
    last_month_won = sum(
        p["total_won"]
        for p in history
        if _month_key(_parse_iso_date(p["week_start"])) == last_month_key
    )

    daily_rate = blended_current_week / 7
    days_remaining_in_month = _days_in_month(now) - now.day
    projected_month_won = actual_so_far_this_month + daily_rate * days_remaining_in_month

    change_pct = (
        _round_half_up(((projected_month_won - last_month_won) / last_month_won) * 100)
        if last_month_won > 0
        else 0
    )

    return TrendPrediction(
        trend=trend,
        projected_month_won=_round_half_up(projected_month_won),
        last_month_won=_round_half_up(last_month_won),
        change_pct=change_pct,
    )
