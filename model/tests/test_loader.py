import csv
from pathlib import Path

from data.loader import aggregate_weekly_spend
from data.schema import AMOUNT_COL, MERCHANT_CATEGORY_COL, TRANSACTION_DATE_COL

ROWS = [
    # date, merchant_category_code, amount
    ("2026-08-03", "5811", "10000"),  # delivery, week of 08-03
    ("2026-08-04", "5811", "12000"),  # delivery, week of 08-03
    ("2026-08-10", "5811", "15000"),  # delivery, week of 08-10
    ("2026-08-17", "5811", "8000"),   # delivery, week of 08-17 (latest date)
    ("2026-08-03", "5814", "4000"),   # cafe, week of 08-03
    ("2026-08-10", "5814", "5000"),   # cafe, week of 08-10
    ("2026-08-17", "5814", "6000"),   # cafe, week of 08-17 (latest date)
    ("2026-08-01", "0000", "999999"),  # unmapped category -> must be dropped
]


def _write_fixture_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([TRANSACTION_DATE_COL, MERCHANT_CATEGORY_COL, AMOUNT_COL])
        writer.writerows(ROWS)


def test_aggregate_weekly_spend_groups_by_category_and_week(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    _write_fixture_csv(csv_path)

    result = aggregate_weekly_spend(csv_path)

    assert result["delivery"] == [
        {"week_start": "2026-08-03", "total_won": 22000, "days_elapsed": 7},
        {"week_start": "2026-08-10", "total_won": 15000, "days_elapsed": 7},
        {"week_start": "2026-08-17", "total_won": 8000, "days_elapsed": 1},
    ]
    assert result["cafe"] == [
        {"week_start": "2026-08-03", "total_won": 4000, "days_elapsed": 7},
        {"week_start": "2026-08-10", "total_won": 5000, "days_elapsed": 7},
        {"week_start": "2026-08-17", "total_won": 6000, "days_elapsed": 1},
    ]
    assert "shopping" not in result
    assert "subscription" not in result


def test_aggregate_weekly_spend_is_chunksize_independent(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    _write_fixture_csv(csv_path)

    whole_file = aggregate_weekly_spend(csv_path, chunksize=1_000_000)
    chunked = aggregate_weekly_spend(csv_path, chunksize=2)

    assert chunked == whole_file
