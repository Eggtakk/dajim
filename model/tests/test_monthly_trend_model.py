from prediction.monthly_trend_model import MonthlyTrendPrediction, predict_next_month


def test_predict_next_month_empty_history_returns_zeros():
    result = predict_next_month([])
    assert result == MonthlyTrendPrediction(
        trend=[], projected_next_month_won=0, last_month_won=0, change_pct=0
    )


def test_predict_next_month_single_point_repeats_it():
    history = [{"month": "2018-07", "total_won": 140824}]
    result = predict_next_month(history)
    assert result.trend == [140824]
    assert result.projected_next_month_won == 140824
    assert result.last_month_won == 140824
    assert result.change_pct == 0


def test_predict_next_month_extrapolates_linear_trend():
    history = [
        {"month": "2018-07", "total_won": 100},
        {"month": "2018-08", "total_won": 200},
        {"month": "2018-09", "total_won": 300},
    ]
    result = predict_next_month(history)
    assert result.trend == [100, 200, 300]
    assert result.projected_next_month_won == 400
    assert result.last_month_won == 300
    assert result.change_pct == 33


def test_predict_next_month_zero_last_month_avoids_division_by_zero():
    history = [
        {"month": "2018-07", "total_won": 0},
        {"month": "2018-08", "total_won": 0},
    ]
    result = predict_next_month(history)
    assert result.change_pct == 0
