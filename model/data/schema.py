"""Column subset, dtypes, and category mapping for the AI Hub 금융 합성
데이터 dataset (dataSetSn 71792), 카드 승인매출정보 file.

CAVEAT: the exact column names/merchant codes below are best-effort, based
on standard Korean card-transaction terminology — not a verified copy of AI
Hub's real header row (this session had no downloaded file to inspect).
Before running against a real file: `head -1 <file>.csv` and fix the
constants below. loader.py and every test import from here, so this is the
only place that needs to change.
"""
from __future__ import annotations

TRANSACTION_DATE_COL = "승인일자"
MERCHANT_CATEGORY_COL = "가맹점업종코드"
AMOUNT_COL = "승인금액"

USECOLS = [TRANSACTION_DATE_COL, MERCHANT_CATEGORY_COL, AMOUNT_COL]

DTYPES = {
    MERCHANT_CATEGORY_COL: "string",
    AMOUNT_COL: "int64",
}

CategoryId = str  # "delivery" | "cafe" | "shopping" | "subscription"

# Merchant category code (업종코드) -> dajim CategoryId
# (matches dajim-web/lib/types.ts's CategoryId union).
MERCHANT_CODE_TO_CATEGORY: dict[str, CategoryId] = {
    "5811": "delivery",     # 음식배달
    "5812": "delivery",     # 일반음식점(배달 포함)
    "5814": "cafe",         # 카페/다과
    "5651": "shopping",     # 의류/잡화
    "5311": "shopping",     # 백화점/쇼핑
    "4899": "subscription",  # 구독형 서비스(OTT 등)
}


def merchant_code_to_category(code: str) -> CategoryId | None:
    """Map a raw merchant category code to a dajim CategoryId, or None if
    the code isn't one of dajim's four tracked categories."""
    return MERCHANT_CODE_TO_CATEGORY.get(code)
