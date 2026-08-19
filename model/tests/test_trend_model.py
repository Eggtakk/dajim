import pytest

from prediction.trend_model import (
    TrendPrediction,
    infer_now,
    predict_category_trend,
)
from tests.fixtures_ts_cross_check import CASES


def test_predict_category_trend_empty_history_returns_zeros():
    result = predict_category_trend([])
    assert result == TrendPrediction(
        trend=[], projected_month_won=0, last_month_won=0, change_pct=0
    )


def test_infer_now_uses_last_weeks_elapsed_days():
    history = [
        {"week_start": "2026-08-03", "total_won": 10000, "days_elapsed": 4},
    ]
    # Monday 2026-08-03 + (4 - 1) days = Thursday 2026-08-06
    assert infer_now(history).isoformat() == "2026-08-06"


def test_predict_category_trend_single_completed_week_paces_current_week():
    history = [
        {"week_start": "2026-07-27", "total_won": 70000, "days_elapsed": 7},
        {"week_start": "2026-08-03", "total_won": 20000, "days_elapsed": 2},
    ]
    result = predict_category_trend(history)
    # No completed weeks feed the regression (len(completed) == 1 still uses
    # slope=0, intercept=70000), but with only one completed point the
    # pace-vs-regression blend still applies; assert the shape/types rather
    # than a hand-derived number here (the cross-validation test covers
    # exact-value parity against the real TS implementation).
    assert len(result.trend) == 2
    assert isinstance(result.projected_month_won, int)
    assert isinstance(result.change_pct, int)


@pytest.mark.parametrize("category", sorted(CASES))
def test_matches_predictTrend_ts_output(category):
    case = CASES[category]
    result = predict_category_trend(case["history"])
    expected = case["prediction"]

    assert result.trend == expected["trend"]
    assert result.projected_month_won == expected["projected_month_won"]
    assert result.last_month_won == expected["last_month_won"]
    assert result.change_pct == expected["change_pct"]
