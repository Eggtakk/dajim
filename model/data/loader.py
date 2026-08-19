"""Memory-efficient loading + weekly aggregation of 카드 승인매출정보 data.

Mirrors the backend aggregation query dajim-web/lib/historicalSpend.ts
mocks: turn raw transaction rows into per-category weekly-spend series
shaped like dajim-web/lib/predictTrend.ts's WeeklySpendPoint input. The
source file has ~430 columns and can be tens of millions of rows, so this
reads only schema.USECOLS and streams it in chunksize-row chunks rather
than loading the whole file into memory.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from pathlib import Path
from typing import Iterator, TypedDict

import pandas as pd

from .schema import (
    AMOUNT_COL,
    DTYPES,
    MERCHANT_CATEGORY_COL,
    TRANSACTION_DATE_COL,
    USECOLS,
    merchant_code_to_category,
)

CHUNK_SIZE = 100_000


class WeeklySpendPoint(TypedDict):
    week_start: str  # ISO date (YYYY-MM-DD), Monday this week starts on
    total_won: int
    days_elapsed: int  # 1-7, 7 means the week is fully elapsed


def _iter_chunks(csv_path: Path, chunksize: int) -> Iterator[pd.DataFrame]:
    return pd.read_csv(
        csv_path,
        usecols=USECOLS,
        dtype=DTYPES,
        parse_dates=[TRANSACTION_DATE_COL],
        chunksize=chunksize,
    )


def _week_start(date: dt.date) -> dt.date:
    return date - dt.timedelta(days=date.weekday())


def aggregate_weekly_spend(
    csv_path: Path, chunksize: int = CHUNK_SIZE
) -> dict[str, list[WeeklySpendPoint]]:
    """Aggregate one 카드 승인매출정보 CSV into per-category weekly series,
    sorted oldest -> newest. Categories with no mapped transactions are
    omitted from the result entirely.

    `days_elapsed` is 7 for every week before the one containing the latest
    transaction date seen in the file, and (weekday index + 1) for that
    latest week — matching predictTrend.ts's "current, in-progress week"
    convention, using the file's own latest date as "now".
    """
    totals: dict[str, dict[dt.date, float]] = defaultdict(lambda: defaultdict(float))
    max_date_seen: dt.date | None = None

    for chunk in _iter_chunks(csv_path, chunksize):
        chunk = chunk.dropna(subset=[MERCHANT_CATEGORY_COL, TRANSACTION_DATE_COL, AMOUNT_COL])
        if chunk.empty:
            continue

        categories = chunk[MERCHANT_CATEGORY_COL].map(merchant_code_to_category)
        chunk = chunk.assign(_category=categories).dropna(subset=["_category"])
        if chunk.empty:
            continue

        dates = chunk[TRANSACTION_DATE_COL].dt.date
        chunk_max = dates.max()
        if max_date_seen is None or chunk_max > max_date_seen:
            max_date_seen = chunk_max

        chunk = chunk.assign(_week_start=dates.map(_week_start))
        grouped = chunk.groupby(["_category", "_week_start"])[AMOUNT_COL].sum()
        for (category, week), total in grouped.items():
            totals[category][week] += float(total)

    if max_date_seen is None:
        return {}

    current_week_start = _week_start(max_date_seen)
    current_days_elapsed = max_date_seen.weekday() + 1

    result: dict[str, list[WeeklySpendPoint]] = {}
    for category, weeks in totals.items():
        result[category] = [
            WeeklySpendPoint(
                week_start=week.isoformat(),
                total_won=round(total),
                days_elapsed=current_days_elapsed if week == current_week_start else 7,
            )
            for week, total in sorted(weeks.items())
        ]
    return result
