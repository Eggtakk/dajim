"""CLI: run the full pipeline — load a downloaded CSV, aggregate weekly
per-category spend, predict each category's trend.

Usage (from model/):
    python -m scripts.run_prediction <path-to-카드승인매출정보.csv>
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from data.loader import aggregate_weekly_spend
from prediction.trend_model import predict_category_trend


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("사용법: python -m scripts.run_prediction <카드승인매출정보.csv 경로>", file=sys.stderr)
        return 1

    csv_path = Path(argv[1])
    weekly_by_category = aggregate_weekly_spend(csv_path)
    if not weekly_by_category:
        print(
            "매핑 가능한 거래가 없습니다 — data/schema.py의 컬럼명/"
            "MERCHANT_CODE_TO_CATEGORY가 실제 파일과 맞는지 확인하세요.",
            file=sys.stderr,
        )
        return 1

    predictions = {
        category: asdict(predict_category_trend(history))
        for category, history in weekly_by_category.items()
    }
    print(json.dumps(predictions, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
