"""
거래 카테고리 분류기 — 가맹점명을 소비 카테고리로 분류한다.

사용 예
-------
    from category_classifier import MerchantClassifier

    clf = MerchantClassifier.load("artifacts")
    clf.predict("스타벅스 강남2호점")
    # {'category': 'food', 'layer': 'L2_brand', 'confidence': 0.99, ...}

거래유형 컬럼이 있으면 함께 넘기는 편이 정확하다.
    clf.predict("김철수", tx_type="이체")   # → transfer (소비 아님)
"""

from .classifier import (CharNGramNB, MerchantClassifier, build_merchant_dict,
                         keyword_match, normalize)
from .taxonomy import (CATEGORIES, SERVICE_CATEGORIES, code_to_category,
                       is_essential, korean)
from .brands import BRANDS, brand_stats

__all__ = [
    "MerchantClassifier", "CharNGramNB", "normalize", "keyword_match",
    "build_merchant_dict", "CATEGORIES", "SERVICE_CATEGORIES",
    "code_to_category", "is_essential", "korean", "BRANDS", "brand_stats",
]

__version__ = "0.1.0"
