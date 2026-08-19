"""
가맹점명 → 거래 카테고리 분류기

구조: 5단계 캐스케이드
  L0  정규화        표기 흔들림 제거
  L1  이체/PG 필터   소비가 아닌 거래를 먼저 걷어낸다
  L2  브랜드 사전    온라인·구독·배달 (상가정보에 없는 영역)
  L3  상호명 사전    상가정보에서 추출한 빈출 상호명
  L4  키워드 규칙    상호명에 업종 단서가 들어있는 경우
  L5  ML 폴백        위에서 다 놓친 롱테일

위로 갈수록 정확하고 아래로 갈수록 커버리지가 넓다.
각 단계는 자기가 확신하는 것만 처리하고 나머지를 아래로 넘긴다.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

# 패키지로 import 될 때(`from category_classifier import ...`)와
# 파일을 직접 실행할 때 모두 동작하도록 두 방식을 모두 허용한다.
try:
    from .taxonomy import ALL_LABELS, NON_SPENDING, code_to_category
    from .brands import (BRANDS, EXACT_BRANDS, NON_SPENDING_EXACT,
                         NON_SPENDING_PATTERNS, NON_SPENDING_TX_TYPES,
                         PG_KEYWORDS, split_brands)
except ImportError:
    from taxonomy import ALL_LABELS, NON_SPENDING, code_to_category
    from brands import (BRANDS, EXACT_BRANDS, NON_SPENDING_EXACT,
                        NON_SPENDING_PATTERNS, NON_SPENDING_TX_TYPES,
                        PG_KEYWORDS, split_brands)

_NONSPEND_RX = re.compile("|".join(NON_SPENDING_PATTERNS))

# ===========================================================================
# L0. 정규화
# ===========================================================================
_CORP = re.compile(r"\(주\)|\(유\)|\(사\)|㈜|㈐|주식회사|유한회사|합자회사|사단법인|재단법인")
_BRACKET = re.compile(r"[\(\[\{<][^\)\]\}>]*[\)\]\}>]")
_KEEP = re.compile(r"[^가-힣a-z0-9]")

# 지점 표기 제거는 '확실한 표시'만 건드린다.
#
# 처음에는 r"[가-힣]{1,6}점$" 으로 '역삼점' 같은 지역명까지 지우려 했는데,
# 정규식이 왼쪽부터 최장 매칭을 하는 바람에
#   '김밥천국역삼점' → '밥천국역삼점'을 매칭 → 남는 글자가 1자라 스킵
#   'gs25서울대점'  → '서울대점'을 매칭 → 정상 제거
# 처럼 같은 패턴인데 결과가 갈렸다. 어느 글자가 지역명인지 규칙으로는 알 수 없다.
#
# 그래서 방향을 바꿨다. 정규화는 '본점/2호점/1층'처럼 명시적 표기만 지우고,
# 지역명이 붙은 지점은 아래 사전 단계에서 **접두어 매칭**으로 흡수한다.
#   '김밥천국역삼점' → 접두어 '김밥천국'이 사전에 있으면 매칭
# 규칙을 정교하게 만드는 대신 매칭 방식을 바꾸는 쪽이 훨씬 안정적이다.
_BRANCH = re.compile(r"(\d+호점|본점|직영점|가맹점|지점|점포)$")
_FLOOR = re.compile(r"(지하\d+층|\d+층|\d+호|b\d+|\d+f)$")


def normalize(name) -> str:
    """가맹점명 표기 흔들림을 제거한다.

    '(주)스타벅스커피코리아 2호점' → '스타벅스커피코리아'
    """
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKC", name).lower()
    s = _CORP.sub("", s)
    s = _BRACKET.sub("", s)
    s = _KEEP.sub("", s)
    for _ in range(2):                      # '강남2호점1층' 같은 중첩 대비
        before = s
        for rx in (_FLOOR, _BRANCH):
            m = rx.search(s)
            if m and len(s) - len(m.group()) >= 3:
                s = s[: m.start()]
        if s == before:
            break
    return s


# ===========================================================================
# L2-b. 짧은 브랜드 — 부분매칭이 위험해 패턴으로 처리
# ===========================================================================
# 'cu'를 부분매칭하면 'cucina', 'documan' 같은 상호에 오탐이 난다.
# 그렇다고 빼면 편의점 결제가 통째로 누락된다. 앞뒤 문맥을 패턴으로 묶어 해결한다.
SHORT_BRAND_PATTERNS = [
    (re.compile(r"^cu[가-힣0-9]{0,10}$"), "food", "CU편의점"),
    (re.compile(r"^gs25"), "food", "GS25"),
    (re.compile(r"^gs더프레시"), "food", "GS더프레시"),
    (re.compile(r"^kt[가-힣]{1,8}$"), "living", "KT"),
    (re.compile(r"^skt|^sk텔레콤"), "living", "SKT"),
]


# ===========================================================================
# L4. 키워드 규칙
# ===========================================================================
# 상호명 안에 업종이 그대로 드러나는 경우가 많다("○○약국", "○○치과").
# 긴 키워드를 먼저 검사해야 '커피빈'이 '커피'로 잘못 잡히지 않는다.
KEYWORD_RULES = {
    # 식비
    "food": [
        "김밥천국", "분식", "국밥", "칼국수", "설렁탕", "곰탕", "냉면", "한정식",
        "백반", "돈까스", "돈가스", "쌀국수", "떡볶이", "순대", "만두",
        "치킨", "피자", "버거", "햄버거", "샌드위치", "토스트", "샐러드",
        "베이커리", "제과", "빵집", "도넛", "케이크", "디저트", "아이스크림",
        "카페", "커피", "coffee", "cafe", "다방", "티하우스",
        "식당", "밥집", "맛집", "정육", "반찬", "청과", "농협하나로",
        "마트", "슈퍼", "편의점", "식품", "먹거리", "푸드", "food",
        "중국집", "짜장", "초밥", "스시", "회집", "횟집", "일식", "중식",
        "구이", "삼겹", "갈비", "곱창", "족발", "보쌈", "찜닭", "덮밥",
    ],
    # 배달 (오프라인 상호에는 거의 없지만 결제 표기에 나타난다)
    "delivery": ["배달", "딜리버리", "delivery", "퀵배송"],
    # 쇼핑
    "shopping": [
        "의류", "패션", "부티크", "브랜드", "아울렛", "백화점", "쇼핑",
        "화장품", "코스메틱", "뷰티샵", "향수",
        "가구", "인테리어소품", "생활용품", "잡화", "문구", "팬시",
        "전자", "가전", "휴대폰", "핸드폰", "통신기기", "컴퓨터",
        "귀금속", "주얼리", "시계", "안경원", "안경점",
        "꽃집", "화원", "플라워", "애견용품", "펫샵",
    ],
    # 교통
    "transport": [
        "주유소", "충전소", "가스충전", "셀프주유", "오일뱅크", "에스오일",
        "택시", "콜택시", "렌터카", "카셰어", "대리운전",
        "정비", "카센타", "카센터", "세차", "타이어", "튜닝",
        "주차장", "주차타워", "터미널", "고속버스", "철도",
    ],
    # 여가
    "leisure": [
        "노래방", "노래연습장", "코인노래", "pc방", "피시방", "당구장", "볼링장",
        "헬스", "피트니스", "짐", "요가", "필라테스", "클라이밍", "골프연습",
        "미용실", "헤어", "헤어샵", "살롱", "네일", "속눈썹", "왁싱",
        "피부관리", "에스테틱", "마사지", "안마", "사우나", "찜질방", "목욕탕",
        "펜션", "리조트", "호텔", "모텔", "게스트하우스", "캠핑", "글램핑",
        "여행사", "투어", "영화관", "시네마", "공연", "전시",
        "호프", "포차", "이자카야", "바", "펍", "주점", "술집", "와인",
        "스튜디오", "사진관", "만화방", "보드게임", "방탈출",
    ],
    # 의료
    "medical": [
        "약국", "약방", "병원", "의원", "치과", "한의원", "한방", "정형외과",
        "피부과", "안과", "이비인후과", "산부인과", "소아과", "내과", "외과",
        "정신건강의학", "신경과", "비뇨", "재활", "검진", "clinic", "메디컬",
        "동물병원", "수의과",
    ],
    # 교육
    "education": [
        "학원", "교습소", "공부방", "과외", "교육원", "아카데미", "어학원",
        "유치원", "어린이집", "학교", "대학교", "도서실", "독서실", "스터디카페",
        "학습지", "입시", "재수", "논술", "수학", "영어회화",
    ],
    # 생활·고정
    "living": [
        "세탁소", "빨래방", "코인세탁", "수선", "구두수선",
        "부동산", "공인중개", "이사", "청소", "방역", "소독",
        "철물", "건자재", "인테리어시공", "설비", "도배",
        "통신요금", "관리비", "전기요금", "가스요금", "수도요금", "보험",
    ],
}

# 긴 키워드를 먼저 검사한다 ('커피빈'이 '커피'로 잘못 잡히지 않게).
#
# 처음에는 파이썬 for 루프로 250개 키워드를 하나씩 `in` 검사했는데,
# 테스트 36만 건 x (브랜드 342 + 키워드 250) = 2억 회 문자열 검색이 되어
# 평가 셀 하나가 몇 분씩 걸렸다.
# 하나의 정규식 alternation 으로 합치면 C 레벨에서 한 번에 스캔한다.
_KEYWORD_SORTED = sorted(
    [(kw, cat) for cat, kws in KEYWORD_RULES.items() for kw in kws],
    key=lambda x: -len(x[0]),
)
_KEYWORD_CAT = dict(_KEYWORD_SORTED)
_KEYWORD_RX = re.compile("|".join(re.escape(k) for k, _ in _KEYWORD_SORTED))


def keyword_match(norm: str):
    m = _KEYWORD_RX.search(norm)
    if m:
        kw = m.group()
        return _KEYWORD_CAT[kw], kw
    return None, None


# ===========================================================================
# L5. ML 폴백 — 문자 n-gram 나이브베이즈 (의존성 없는 기본 구현)
# ===========================================================================
class CharNGramNB:
    """해싱 트릭 기반 Multinomial Naive Bayes.

    scikit-learn 없이도 동작하도록 numpy만으로 구현했다.
    실서비스에서는 sklearn LinearSVC 로 교체 가능하며, 인터페이스는 동일하다.
    """

    def __init__(self, n_buckets: int = 1 << 18, ngram_range=(2, 4),
                 alpha: float = 0.2, temperature: float = 8.0):
        self.n_buckets = n_buckets
        self.ngram_range = ngram_range
        self.alpha = alpha
        self.temperature = temperature   # 신뢰도 분포를 벌리는 계수 (검증셋으로 조정)
        self.classes_: list[str] = []
        self.log_prior_: np.ndarray | None = None
        self.log_prob_: np.ndarray | None = None

    # -- 특징 추출 ---------------------------------------------------------
    # 처음에는 n-gram 문자열마다 crc32 를 돌렸는데 183만 건 학습에 17분이 걸렸다.
    # 문자열 슬라이싱과 encode() 가 병목이라 롤링 폴리노미얼 해시로 바꿨다.
    # 코드포인트 배열 위에서 numpy 연산만 쓰므로 파이썬 루프가 n-gram 길이(3회)로 줄어든다.
    _B = np.uint64(1000003)

    def _hashes(self, text: str) -> np.ndarray:
        lo, hi = self.ngram_range
        t = f"^{text}$"
        a = np.frombuffer(t.encode("utf-32-le"), dtype=np.uint32).astype(np.uint64)
        L = a.size
        parts = []
        with np.errstate(over="ignore"):        # uint64 오버플로 wrap 은 의도된 동작
            for n in range(lo, hi + 1):
                if L < n:
                    continue
                h = np.zeros(L - n + 1, dtype=np.uint64)
                for j in range(n):
                    h = h * self._B + a[j:L - n + 1 + j]
                parts.append(h)
        if not parts:
            return np.empty(0, dtype=np.int64)
        return (np.concatenate(parts) % np.uint64(self.n_buckets)).astype(np.int64)

    # -- 학습 --------------------------------------------------------------
    def fit(self, texts, labels, flush_every=200_000, verbose=False):
        """청크 단위로 bincount 를 누적한다.

        183만 건의 해시를 한 번에 concatenate 하면 int64 배열이 수백 MB로 불어난다.
        일정 개수마다 bincount 로 접어 넣으면 메모리가 클래스별 카운터 크기로 고정된다.
        """
        self.classes_ = sorted(set(labels))
        idx = {c: i for i, c in enumerate(self.classes_)}
        K = len(self.classes_)
        counts = np.zeros((K, self.n_buckets), dtype=np.float64)
        prior = np.zeros(K, dtype=np.float64)

        buf = defaultdict(list)
        pending = 0

        def flush():
            nonlocal pending
            for k, arrs in buf.items():
                if arrs:
                    counts[k] += np.bincount(np.concatenate(arrs),
                                             minlength=self.n_buckets)
            buf.clear()
            pending = 0

        for i, (t, y) in enumerate(zip(texts, labels)):
            k = idx[y]
            h = self._hashes(t)
            if h.size:
                buf[k].append(h)
                pending += 1
            prior[k] += 1
            if pending >= flush_every:
                flush()
                if verbose:
                    print(f"  ... {i + 1:,}건 처리")
        flush()

        counts += self.alpha
        self.log_prob_ = np.log(counts / counts.sum(axis=1, keepdims=True))
        self.log_prior_ = np.log(prior / prior.sum())
        return self

    # -- 추론 --------------------------------------------------------------
    def _scores(self, text: str) -> np.ndarray:
        h = self._hashes(text)
        if h.size == 0:
            return self.log_prior_.copy()
        return self.log_prior_ + self.log_prob_[:, h].sum(axis=1)

    def predict_one(self, text: str):
        h = self._hashes(text)
        n = max(1, h.size)
        s = self.log_prior_ if h.size == 0 else (
            self.log_prior_ + self.log_prob_[:, h].sum(axis=1))

        # 나이브베이즈는 n-gram 을 독립으로 가정해 확률을 전부 곱하므로,
        # 글자가 길수록 로그점수 차이가 벌어져 softmax 가 항상 1.0 을 뱉는다.
        # (실제로 첫 구현에서 모든 예측 신뢰도가 0.9999 로 나왔다)
        # n-gram 개수로 나눠 '평균 로그확률'로 만들면 길이에 무관한 신뢰도가 된다.
        z = (s - s.max()) / n * self.temperature
        p = np.exp(z)
        p /= p.sum()
        k = int(p.argmax())
        return self.classes_[k], float(p[k])

    def predict(self, texts):
        return [self.predict_one(t) for t in texts]

    # -- 저장/로드 ----------------------------------------------------------
    def save(self, path):
        np.savez_compressed(
            path,
            classes=np.array(self.classes_),
            log_prior=self.log_prior_,
            log_prob=self.log_prob_.astype(np.float32),
            meta=np.array([self.n_buckets, self.ngram_range[0],
                           self.ngram_range[1], self.temperature]),
        )

    @classmethod
    def load(cls, path):
        z = np.load(path, allow_pickle=False)
        n_buckets, lo, hi, temp = z["meta"]
        m = cls(n_buckets=int(n_buckets), ngram_range=(int(lo), int(hi)),
                temperature=float(temp))
        m.classes_ = list(z["classes"])
        m.log_prior_ = z["log_prior"]
        m.log_prob_ = z["log_prob"].astype(np.float64)
        return m


# ===========================================================================
# 캐스케이드 분류기
# ===========================================================================
class MerchantClassifier:
    def __init__(self, merchant_dict=None, model=None,
                 ml_threshold: float = 0.45):
        self.brand_partial, self.brand_exact = split_brands()
        self.brand_sorted = sorted(self.brand_partial.items(), key=lambda x: -len(x[0]))
        self._brand_rx = re.compile(
            "|".join(re.escape(b) for b, _ in self.brand_sorted))
        self.merchant_dict = merchant_dict or {}
        self.model = model
        self.ml_threshold = ml_threshold

    # -- 각 단계 -----------------------------------------------------------
    def _non_spending(self, norm: str):
        # 부분 문자열이 아니라 '정확 일치 + 앵커된 패턴'만 인정한다.
        # ('성주식당'이 '주식'에 걸려 소비에서 사라지는 사고를 막기 위함)
        return norm in NON_SPENDING_EXACT or bool(_NONSPEND_RX.search(norm))

    def _is_pg(self, norm: str):
        for kw in PG_KEYWORDS:
            if kw in norm:
                return True
        return False

    def _brand(self, norm: str):
        if norm in self.brand_exact:
            return self.brand_exact[norm], norm
        for rx, cat, tag in SHORT_BRAND_PATTERNS:
            if rx.match(norm):
                return cat, tag
        m = self._brand_rx.search(norm)
        if m:
            return self.brand_partial[m.group()], m.group()
        return None, None

    def _merchant(self, norm: str):
        """정확 일치 → 접두어 일치 순으로 조회.

        접두어 매칭이 '○○브랜드 + 지점명' 형태를 흡수한다.
        한국 상호는 브랜드가 앞, 지점이 뒤에 오므로 접두어 방향이 맞다.
        오탐을 막기 위해 4글자 이상 접두어만 인정한다.
        """
        if norm in self.merchant_dict:
            cat, purity = self.merchant_dict[norm]
            return cat, purity, norm
        for L in range(min(len(norm) - 1, 12), 3, -1):
            p = norm[:L]
            if p in self.merchant_dict:
                cat, purity = self.merchant_dict[p]
                return cat, purity * 0.95, p     # 접두어 매칭은 신뢰도를 약간 깎는다
        return None, None, None

    # -- 메인 --------------------------------------------------------------
    def predict(self, raw_name: str, tx_type: str | None = None) -> dict:
        """tx_type: CSV 의 '거래유형' 컬럼. 있으면 이체 판별의 1순위로 쓴다."""
        norm = normalize(raw_name)

        # 거래유형이 주어지면 가맹점명 추측보다 항상 우선한다.
        if tx_type and str(tx_type).strip() in NON_SPENDING_TX_TYPES:
            return self._r(raw_name, norm, NON_SPENDING, "L1_tx_type", 1.0, tx_type)

        if not norm:
            return self._r(raw_name, norm, "unknown", "L0_empty", 0.0)

        if self._non_spending(norm):
            return self._r(raw_name, norm, NON_SPENDING, "L1_non_spending", 1.0)
        if self._is_pg(norm):
            # PG사 이름만으로는 무엇을 샀는지 알 수 없다. 억지로 찍지 않는다.
            return self._r(raw_name, norm, "unknown", "L1_pg", 0.0)

        cat, hit = self._brand(norm)
        if cat:
            return self._r(raw_name, norm, cat, "L2_brand", 0.99, hit)

        cat, purity, hit = self._merchant(norm)
        if cat:
            return self._r(raw_name, norm, cat, "L3_merchant", purity, hit)

        cat, kw = keyword_match(norm)
        if cat:
            return self._r(raw_name, norm, cat, "L4_keyword", 0.85, kw)

        if self.model is not None:
            cat, conf = self.model.predict_one(norm)
            if conf >= self.ml_threshold:
                return self._r(raw_name, norm, cat, "L5_ml", conf)
            return self._r(raw_name, norm, "unknown", "L5_ml_lowconf", conf)

        return self._r(raw_name, norm, "unknown", "L6_none", 0.0)

    def predict_many(self, names, tx_types=None):
        if tx_types is None:
            return [self.predict(n) for n in names]
        return [self.predict(n, t) for n, t in zip(names, tx_types)]

    @staticmethod
    def _r(raw, norm, cat, layer, conf, evidence=None):
        return {"raw": raw, "normalized": norm, "category": cat,
                "layer": layer, "confidence": round(float(conf), 3),
                "evidence": evidence}

    # -- 저장/로드 ----------------------------------------------------------
    def save(self, outdir):
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        json.dump(self.merchant_dict, open(outdir / "merchant_dict.json", "w"),
                  ensure_ascii=False)
        json.dump({"brands": BRANDS, "exact": EXACT_BRANDS,
                   "non_spending_exact": sorted(NON_SPENDING_EXACT),
                   "pg": PG_KEYWORDS},
                  open(outdir / "brand_dict.json", "w"),
                  ensure_ascii=False, indent=1)
        if self.model is not None:
            self.model.save(outdir / "model.npz")

    @classmethod
    def load(cls, outdir):
        outdir = Path(outdir)
        md = json.load(open(outdir / "merchant_dict.json"))
        md = {k: (v[0], v[1]) for k, v in md.items()}
        model = None
        if (outdir / "model.npz").exists():
            model = CharNGramNB.load(outdir / "model.npz")
        return cls(merchant_dict=md, model=model)


# ===========================================================================
# 상호명 사전 구축 (L3)
# ===========================================================================
def build_merchant_dict(norm_names, labels, min_count=3, min_purity=0.80):
    """상가정보에서 '이 이름은 거의 항상 이 카테고리'인 항목만 사전으로 승격.

    min_count : 몇 번 이상 등장해야 신뢰할지
    min_purity: 최빈 카테고리 비율이 이 값을 넘어야 등재
      → 순도가 낮은 이름(예: '본점')은 사전에 넣지 않고 ML 로 넘긴다
    """
    agg = defaultdict(Counter)
    for n, y in zip(norm_names, labels):
        if n:
            agg[n][y] += 1

    out = {}
    for name, c in agg.items():
        total = sum(c.values())
        if total < min_count or len(name) < 2:
            continue
        cat, cnt = c.most_common(1)[0]
        purity = cnt / total
        if purity >= min_purity:
            out[name] = (cat, round(purity, 3))
    return out
