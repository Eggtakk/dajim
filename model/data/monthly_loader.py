"""Load one customer's monthly category totals from AI Hub's 카드
승인매출정보 files (see schema_monthly.py for why this is a separate path
from loader.py — the real file is a pre-aggregated monthly panel, not
per-transaction rows).
"""
from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import TypedDict

from .schema_monthly import CATEGORY_AMOUNT_COLUMNS, MEMBER_ID_COL, YEAR_MONTH_COL


class MonthlySpendPoint(TypedDict):
    month: str  # "YYYY-MM"
    total_won: int


def load_customer_monthly_spend(
    zip_path: Path, month_filenames: list[str], member_id: str
) -> dict[str, list[MonthlySpendPoint]]:
    """Read one customer's category totals across the given monthly CSV
    filenames inside zip_path (e.g. "201807_승인매출정보.csv"), sorted
    oldest -> newest. A month file with no row for member_id simply
    contributes nothing for that month.
    """
    by_category: dict[str, dict[str, int]] = {cat: {} for cat in CATEGORY_AMOUNT_COLUMNS}

    with zipfile.ZipFile(zip_path) as z:
        for filename in month_filenames:
            with z.open(filename) as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8"))
                header = next(reader)
                idx = {name: i for i, name in enumerate(header)}
                for row in reader:
                    if row[idx[MEMBER_ID_COL]] != member_id:
                        continue
                    year_month = row[idx[YEAR_MONTH_COL]]
                    month = f"{year_month[:4]}-{year_month[4:]}"
                    for category, column in CATEGORY_AMOUNT_COLUMNS.items():
                        by_category[category][month] = int(row[idx[column]])
                    break

    return {
        category: [
            MonthlySpendPoint(month=month, total_won=total)
            for month, total in sorted(months.items())
        ]
        for category, months in by_category.items()
    }
