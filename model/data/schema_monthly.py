"""Column names for AI Hub's actual 카드 승인매출정보 files (dataSetSn 71792).

Verified against a real downloaded file on 2026-08-19 — unlike schema.py,
these are not guesses. The real file is NOT per-transaction: each row is one
customer's (발급회원번호) pre-aggregated totals for one month (기준년월), across
430 columns, one CSV per month (e.g. 201807_승인매출정보.csv). There is no
per-transaction date or merchant code to categorize — category totals are
already split out as columns.

This means data/loader.py + data/schema.py's transaction-aggregation
approach doesn't apply to this file; see data/monthly_loader.py instead,
which reads these pre-aggregated columns directly for one customer across
however many monthly files are available.

Category coverage caveat: AI Hub does not split "요식"(dining) into
delivery vs. cafe, so dajim's "delivery" and "cafe" categories can't both be
derived from this file. "delivery" is mapped to 이용금액_요식 as the closest
available proxy (all dining/restaurant spend, not delivery-specific); there
is no cafe-equivalent column, so it's omitted rather than guessed.
"""
from __future__ import annotations

YEAR_MONTH_COL = "기준년월"  # e.g. "201807"
MEMBER_ID_COL = "발급회원번호"  # e.g. "SYN_0" — synthetic customer id, stable across monthly files

# dajim CategoryId -> AI Hub column holding that category's total spend for
# the row's (customer, month). See the module docstring for the "delivery"
# approximation and the missing "cafe" category.
CATEGORY_AMOUNT_COLUMNS: dict[str, str] = {
    "shopping": "이용금액_쇼핑",
    "delivery": "이용금액_요식",
    "subscription": "RP금액_B0M",
}
