"""
거래 카테고리 체계 + 업종코드 매핑

설계 원칙
---------
매핑을 소분류 247개에 대해 하나하나 쓰지 않는다.
중분류 75개에 기본값을 주고, 상식과 어긋나는 소분류만 예외로 덮어쓴다.
  → 유지보수 대상이 247개에서 약 90개로 줄고,
    "왜 이 업종이 이 카테고리인가"를 중분류 단위로 설명할 수 있다.

소분류코드는 항상 [중분류코드 4자리 + 2자리] 구조이므로 prefix로 상위를 얻는다.
  예) G20404(슈퍼마켓) → G204(종합 소매)
"""

# ---------------------------------------------------------------------------
# 1. 카테고리 정의
# ---------------------------------------------------------------------------
# 앞의 6개는 시나리오 엔진이 직접 다루는 변동비 카테고리다.
# 뒤의 4개는 행동 추천 대상은 아니지만 소비 총액과 필수/비필수 판정에 필요하다.
CATEGORIES = {
    # code            한글        서비스 취급    필수 여부
    "food":         ("식비",      "variable",   True),
    "delivery":     ("배달",      "variable",   False),
    "shopping":     ("쇼핑",      "variable",   False),
    "transport":    ("교통",      "variable",   True),
    "subscription": ("구독",      "variable",   False),
    "leisure":      ("여가",      "variable",   False),
    "medical":      ("의료",      "essential",  True),
    "education":    ("교육",      "essential",  True),
    "living":       ("생활·고정",  "fixed",      True),
    "other":        ("기타",      "excluded",   True),
}

# 소비가 아닌 것 — 가계부에서 반드시 걸러야 한다.
# 이체·카드대금·현금서비스를 소비로 세면 지출이 두 배로 부풀어 모든 예측이 망가진다.
NON_SPENDING = "transfer"

SERVICE_CATEGORIES = [c for c, v in CATEGORIES.items() if v[1] == "variable"]
ALL_LABELS = list(CATEGORIES.keys())


# ---------------------------------------------------------------------------
# 2. 중분류(75개) 기본 매핑
# ---------------------------------------------------------------------------
MID_MAP = {
    # ---- 소매 G2 ----
    "G202": "transport",   # 자동차 부품 소매
    "G203": "transport",   # 모터사이클 소매
    "G204": "food",        # 종합 소매 (슈퍼마켓·편의점) — 장보기는 식비로 본다
    "G205": "food",        # 식료품 소매
    "G206": "food",        # 음료 소매
    "G207": "living",      # 담배 소매
    "G208": "shopping",    # 가전·통신 소매
    "G209": "shopping",    # 섬유·의복·신발 소매
    "G210": "living",      # 철물·건설자재 소매
    "G211": "shopping",    # 가구 소매
    "G212": "shopping",    # 기타 생활용품 소매
    "G213": "shopping",    # 오락용품 소매
    "G214": "transport",   # 연료 소매 (주유소)
    "G215": "shopping",    # 의약·화장품 소매
    "G216": "shopping",    # 안경·정밀기기 소매
    "G217": "shopping",    # 시계·귀금속 소매
    "G218": "shopping",    # 장식품 소매
    "G219": "shopping",    # 식물 소매 (꽃집)
    "G220": "shopping",    # 애완동물·용품 소매
    "G221": "shopping",    # 기타 상품 소매
    "G222": "shopping",    # 중고 상품 소매

    # ---- 숙박 I1 ----
    "I101": "leisure",     # 일반 숙박 (펜션·호텔·모텔) — 여행 지출
    "I102": "living",      # 기타 숙박 (기숙사·고시원) — 주거비에 가깝다

    # ---- 음식 I2 ----
    "I201": "food",        # 한식
    "I202": "food",        # 중식
    "I203": "food",        # 일식
    "I204": "food",        # 서양식
    "I205": "food",        # 동남아시아
    "I206": "food",        # 기타 외국
    "I207": "food",        # 구내식당·뷔페
    "I210": "food",        # 기타 간이 (분식·치킨·빵)
    "I211": "leisure",     # 주점 — 비필수이므로 식비와 분리한다
    "I212": "food",        # 비알코올 (카페)

    # ---- 부동산 L1 ----
    "L102": "living",      # 부동산 서비스 (중개수수료)

    # ---- 전문·과학·기술 M1 ---- (대부분 B2B)
    "M103": "other",       # 법무
    "M104": "other",       # 회계·세무
    "M105": "other",       # 광고
    "M106": "other",       # 시장 조사
    "M107": "other",       # 본사·경영 컨설팅
    "M109": "other",       # 기술 서비스
    "M111": "living",      # 수의 (동물병원) — 개인 지출
    "M112": "other",       # 전문 디자인
    "M113": "leisure",     # 사진 촬영 (스튜디오)
    "M114": "other",       # 인쇄·제품제작
    "M115": "other",       # 기타 전문 과학

    # ---- 시설관리·임대 N1 ----
    "N101": "other",       # 시설관리
    "N102": "living",      # 청소·방제
    "N103": "other",       # 조경·유지
    "N104": "other",       # 고용 알선
    "N105": "leisure",     # 여행사·보조
    "N107": "other",       # 사무 지원
    "N108": "other",       # 기타 사업 서비스
    "N109": "transport",   # 운송장비 대여 (렌터카)
    "N110": "living",      # 가정용품 대여
    "N111": "other",       # 산업용품 대여

    # ---- 교육 P1 ----
    "P105": "education",   # 일반 교육
    "P106": "education",   # 기타 교육
    "P107": "education",   # 교육 지원

    # ---- 보건의료 Q1 ----
    "Q101": "medical",     # 병원
    "Q102": "medical",     # 의원
    "Q104": "medical",     # 기타 보건

    # ---- 예술·스포츠 R1 ----
    "R102": "leisure",     # 도서관·사적지
    "R103": "leisure",     # 스포츠 서비스
    "R104": "leisure",     # 유원지·오락

    # ---- 수리·개인 S2 ----
    "S201": "living",      # 컴퓨터 수리
    "S202": "living",      # 통신장비 수리
    "S203": "transport",   # 자동차 수리·세차
    "S204": "transport",   # 모터사이클 수리
    "S205": "living",      # 가전제품 수리
    "S206": "living",      # 기타 가정용품 수리
    "S207": "leisure",     # 이용·미용 (미용실·네일)
    "S208": "leisure",     # 욕탕·신체관리
    "S209": "living",      # 세탁
    "S210": "other",       # 장례식장
    "S211": "other",       # 기타 개인 (예식장)
}


# ---------------------------------------------------------------------------
# 3. 소분류 예외 (중분류 기본값이 상식과 어긋나는 경우만)
# ---------------------------------------------------------------------------
SUB_OVERRIDE = {
    # 오락용품 소매(G213 = shopping) 안의 예외
    "G21301": "leisure",    # 서점 — 도서는 여가 소비
    "G21304": "leisure",    # 운동용품 소매업
    "G21305": "transport",  # 자전거 소매업 — 이동수단

    # 연료 소매(G214 = transport) 안의 예외
    "G21403": "living",     # 가정용 연료 소매업 — 난방비

    # 의약·화장품 소매(G215 = shopping) 안의 예외
    "G21501": "medical",    # 약국
    "G21502": "medical",    # 의료기기 소매업

    # 안경·정밀기기 소매(G216 = shopping) 안의 예외
    "G21602": "medical",    # 안경렌즈 소매업 — 시력 교정

    # 음료 소매(G206 = food) 안의 예외
    "G20602": "leisure",    # 주류 소매업 — 주점과 동일하게 비필수로

    # 가정용품 대여(N110 = living) 안의 예외
    "N11001": "leisure",    # 스포츠/레크리에이션 용품 대여업
    "N11003": "leisure",    # 만화방

    # 기타 교육(P106 = education) 안의 예외
    "P10603": "leisure",    # 요가/필라테스 학원 — 헬스장과 같은 성격
}


def code_to_category(sub_code) -> str:
    """소분류코드 → 카테고리. 예외 → 중분류 기본값 → other 순으로 조회."""
    if not isinstance(sub_code, str) or len(sub_code) < 4:
        return "other"
    if sub_code in SUB_OVERRIDE:
        return SUB_OVERRIDE[sub_code]
    return MID_MAP.get(sub_code[:4], "other")


def is_essential(category: str) -> bool:
    return CATEGORIES.get(category, ("", "", True))[2]


def korean(category: str) -> str:
    return CATEGORIES.get(category, (category,))[0]
