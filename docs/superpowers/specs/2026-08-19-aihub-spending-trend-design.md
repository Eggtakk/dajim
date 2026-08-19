# 설계: AI Hub 금융 합성 데이터 연동 + 소비 추이 예측 모델 (Python)

## 배경

`docs/api-and-model-plan.md` §2-2에 정의된 "소비 추이 예측 모델"은 현재 `dajim-web/lib/predictTrend.ts`에 TypeScript로 프론트엔드 목데이터 위에서만 구현되어 있다. 실제 백엔드/모델 레이어를 별도로 구현하기 위해, 팀원 중 한 명(사용자)이 이 모델을 독립된 `.py` 알고리즘으로 설계하기로 했다. 사용자는 AI Hub의 "금융 합성 데이터"(dataSetSn 71792) 다운로드 승인을 이미 받아둔 상태다.

작업은 두 단계로 나눈다:
1. AI Hub 데이터 연동 (다운로드 자동화 + 로딩/집계 파이프라인)
2. 소비 추이 예측 모델 (1단계 산출물을 입력으로 받는 알고리즘)

## 저장소 구조

`dajim-web`(Next.js), `prototype`(정적 HTML)과 동급으로 `model/`을 저장소 루트에 추가한다.

```
model/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── __init__.py
│   ├── config.py
│   ├── aihub_client.py
│   ├── schema.py
│   └── loader.py
├── prediction/
│   ├── __init__.py
│   └── trend_model.py
├── scripts/
│   ├── fetch_data.py
│   └── run_prediction.py
└── tests/
    ├── test_loader.py
    └── test_trend_model.py
```

## 브랜치 1 — `feature/data-aihub-integration`

**범위**: AI Hub "금융 합성 데이터"(dataSetSn 71792) 중 "카드 승인매출정보"(거래 단위, ~430컬럼) 파일을 내려받고, 예측 모델이 쓸 수 있는 카테고리별 주간 집계로 변환하는 파이프라인.

- `aihub_client.py`: 공식 CLI `aihubshell`을 `subprocess`로 감싼 래퍼. 비공개 REST 엔드포인트를 직접 재현하지 않는다 — 문서화되지 않았고 깨지기 쉽기 때문. `AIHUB_API_KEY`/`AIHUB_DATASET_KEY`는 `.env`에서만 읽는다(코드/커밋에 절대 포함하지 않음).
- **API vs 수동 다운로드 판단**: AI Hub Open API(`aihubshell`)는 레코드 단위 스트리밍 쿼리가 아니라 브라우저 클릭을 대신하는 파일 다운로드 자동화 도구다. 따라서 "API가 메모리 효율적"이라는 전제는 다운로드 방식 자체보다 다운로드된 CSV를 어떻게 읽느냐에 달려 있다. 그래도 API 방식을 택하는 이유는 (a) 재현 가능한 스크립트로 남길 수 있고 (b) 파일 단위 선택 다운로드(`filekey`)로 필요한 파일만 받을 수 있어서다. 실제 메모리 효율은 `loader.py`의 청크 읽기가 담당한다.
- `loader.py`: 430컬럼 원본에서 예측에 필요한 컬럼(거래일자, 가맹점/업종, 승인금액)만 `usecols`로 선택하고 `chunksize`로 순회하며 카테고리별 주간(월요일 시작) 합계로 집계한다. `dajim-web/lib/historicalSpend.ts`가 흉내내던 "백엔드 집계 쿼리"의 Python 버전이며, 출력 스키마는 `WeeklySpendPoint`(주 시작일, 합계, 경과일수)와 1:1 대응시킨다.
- `schema.py`: 카드 승인매출정보 컬럼 부분집합과 dtype, 그리고 가맹점 업종코드 → dajim 카테고리(`delivery`/`cafe`/`shopping`/`subscription`) 매핑 규칙.
- **검증**: 이번 세션에는 실제 `AIHUB_API_KEY`가 없어 다운로드를 실행할 수 없다. 430컬럼 스키마를 축소 재현한 합성 CSV 픽스처로 `loader.py`의 파싱/집계 로직을 테스트한다. 실제 다운로드 실행은 사용자가 로컬에서 `.env`를 채운 뒤 `scripts/fetch_data.py`로 진행한다.

## 브랜치 2 — `feature/model-spending-trend` (브랜치 1 위에서 분기)

**범위**: `docs/api-and-model-plan.md` §2-2 그대로, `predictTrend.ts`의 로직(완료된 주에 대한 최소자승 선형추세 + 진행 중인 주의 페이스를 블렌딩해 이번 달 예상 소비액 산출)을 Python으로 이식한다.

- `trend_model.py`: `loader.py`가 만든 주간 집계 리스트를 입력으로 받아 `projected_month_won`, `last_month_won`, `change_pct`, `trend`(최근 N주 시계열)를 반환. 함수 시그니처를 이동평균/선형추세 로직과 분리해 두어, 문서에 명시된 업그레이드 경로(지수평활/Prophet 등)로 나중에 교체하기 쉽게 한다.
- **검증**: `dajim-web/lib/historicalSpend.ts`의 `HISTORY` 목데이터를 Python 픽스처로 옮기고, TS 버전(`predictCategoryTrend`)과 동일한 입력에 대해 동일한 출력(허용 오차 내)이 나오는지 교차 검증하는 테스트를 작성한다. 이는 이식 정확성을 담보하는 회귀 테스트 역할을 한다.

## 브랜치/커밋 전략

- 두 브랜치 모두 로컬 커밋까지만 진행한다. `origin`에 push하거나 PR을 여는 것은 팀 리뷰 프로세스(`CONTRIBUTING.md`)가 있으므로 별도로 사용자에게 확인 후 진행한다.
- 브랜치 2는 브랜치 1의 산출물(`data/loader.py`)을 바로 쓸 수 있도록 브랜치 1 위에서 분기한다. 브랜치 1이 실제로 `main`에 머지되면, 브랜치 2를 `main` 기준으로 리베이스해야 한다는 점을 완료 시점에 안내한다.

## 범위 밖

- 실제 AI Hub 서버 접속/다운로드 실행 (API 키가 이 세션에 없음)
- 카드 채널정보 등 다른 11종 데이터 연동
- 시계열 모델 고도화(지수평활/Prophet) — 문서상 3단계 항목, 이번 작업은 1~2단계(이동평균/선형추세)까지
- `dajim-web` Next.js 코드 변경 (별도 팀원 작업 영역)
