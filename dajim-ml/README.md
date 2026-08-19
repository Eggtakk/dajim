# `dajim-ml/` — 모델 레이어

다짐 서비스의 예측·분류 모델이 들어가는 영역입니다.
현재는 **거래 카테고리 분류기**가 구현되어 있고, 소비 추이 예측·목표 시뮬레이션이 뒤이어 붙습니다.

| 모델 | 상태 | 담당 |
| --- | --- | --- |
| ① 거래 카테고리 분류기 | ✅ v0.1 | 정채영 |

---

## 빠른 사용법

원본 데이터를 받을 필요 없습니다. `artifacts/`에 학습 결과가 커밋되어 있습니다.

```python
from category_classifier import MerchantClassifier

clf = MerchantClassifier.load("dajim-ml/artifacts")

clf.predict("스타벅스 강남2호점")
# {'category': 'food', 'layer': 'L2_brand', 'confidence': 0.99, 'evidence': '스타벅스'}

clf.predict("김철수", tx_type="이체")
# {'category': 'transfer', ...}   ← 소비가 아니므로 합계에서 제외해야 함
```

```bash
pip install -r dajim-ml/requirements.txt   # numpy, pandas 뿐
```

### 반환값 읽는 법

| 필드 | 의미 |
| --- | --- |
| `category` | 10개 카테고리 중 하나, `transfer`(소비 아님), `unknown`(판단 불가) |
| `layer` | 어느 단계에서 판정했는지 (`L1`~`L5`) |
| `confidence` | 0~1. `unknown`은 0 |
| `evidence` | 근거가 된 문자열 (사용자에게 "왜 이 카테고리인지" 보여줄 때 사용) |

**`transfer`와 `unknown`은 반드시 소비 합계에서 빼야 합니다.**
이체를 소비로 세면 월 지출이 몇 배로 부풀어 뒤의 예측·시나리오가 전부 틀어집니다.

---

## 카테고리 체계

앞의 6개가 시나리오 엔진이 행동 추천을 거는 변동비 카테고리입니다.

```
food(식비)  delivery(배달)  shopping(쇼핑)
transport(교통)  subscription(구독)  leisure(여가)
─────────────────────────────────────────────
medical(의료)  education(교육)  living(생활·고정)  other(기타)
transfer(소비 아님)  unknown(판단 불가)
```

---

## 구조

```
dajim-ml/
├─ category_classifier/     파이썬 패키지 (FastAPI 에서 import)
│  ├─ taxonomy.py           카테고리 정의 + 업종코드 247개 매핑
│  ├─ brands.py             온라인·구독·배달 브랜드 사전 (직접 구축)
│  └─ classifier.py         5단계 캐스케이드 + 문자 n-gram 모델
├─ artifacts/               학습 산출물 (커밋됨, 3.8MB)
├─ notebooks/               학습·평가 과정 (실행 결과 포함)
├─ scripts/train.py         재학습 CLI
└─ MODEL_DESIGN.md          설계 근거 — 왜 이 구조인가
```

---

## 성능 (2026-08-18 기준)

원본 277만 건, 고유 상호명 183만 건. 상호명 단위 그룹 분할로 누수 차단.

| 지표 | 값 |
| --- | --- |
| 정확도 (판정된 건 기준) | 0.750 |
| macro F1 | 0.731 |
| 미분류율 | 2.9% |

**이 수치를 액면 그대로 읽으면 안 됩니다.** 정답 라벨이 업종코드에서 파생된 것이라,
"카페인데 업종코드가 소매로 등록된 가게" 같은 원본의 오류까지 오답으로 계산됩니다.
실제 결제 표기 샘플에 대한 체감 정확도는 이보다 높습니다. 자세한 건 `MODEL_DESIGN.md` 참고.

---

## 재학습

원본 데이터는 용량 때문에 저장소에 없습니다. 필요할 때만 받으면 됩니다.

1. [공공데이터포털 상가(상권)정보](https://www.data.go.kr/data/15083033/fileData.do) 다운로드
2. 압축 해제 후 경로 지정
3. 실행

```bash
export DAJIM_SANGGA_DIR="/path/to/소상공인시장진흥공단_상가(상권)정보_20260630"
python dajim-ml/scripts/train.py
```

약 8분 걸리고 `artifacts/`가 갱신됩니다.

**브랜드 사전만 고칠 거라면 재학습이 필요 없습니다.** `brands.py`는 런타임에 직접 읽히므로
수정 후 바로 반영됩니다. 온라인 브랜드 추가는 이쪽이 훨씬 빠릅니다.

---

## 기여

브랜드 사전은 계속 채워야 합니다. `brands.py`의 카테고리별 리스트에 한 줄씩 추가하면 됩니다.

```python
"delivery": [
    "배달의민족", "배민", ...
    "새로운배달앱",        # ← 여기
],
```

주의: **3글자 미만 브랜드는 넣지 마세요.** 부분 문자열 매칭이라 오탐이 납니다.
2글자 브랜드는 `EXACT_BRANDS`에 따로 넣어 정확 일치로만 처리합니다.
