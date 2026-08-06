# 다짐 (Dajim)

소비 습관을 예측하고, 목표를 세우고, 결과로 확인하는 소비 습관 코칭 서비스의 노트북 웹 버전입니다.

## 실행

```bash
npm install
npm run dev   # http://localhost:3000
```

```bash
npm run build && npm run start   # 프로덕션 빌드
```

## 구조

- `app/onboarding` — 온보딩 (사이드바 없는 풀스크린)
- `app/(app)/*` — 홈 / 나의 소비 / 목표 설정 / 예측 시나리오 / 소비 트래킹 / 결과 확인 (사이드바 레이아웃 공유)
- `components/` — 재사용 UI 컴포넌트 (Button, Chip, Pill, Card, Sparkline, PredictCard, Sidebar)
- `lib/mockData.ts` — **추후 알고리즘/모델을 연결할 지점.** 지금은 목데이터를 반환하지만, 함수 시그니처는 실제 API 응답과 동일한 모양으로 맞춰뒀습니다. 각 함수 본문을 `fetch()` 호출로 교체하면 됩니다.
- `lib/useGoalSettings.ts` — 목표 설정값을 localStorage에 저장하는 훅. 백엔드가 생기면 이 안에서 API 동기화를 추가하면 됩니다.
- `lib/categories.ts`, `lib/types.ts` — 카테고리 목데이터, 공용 타입 정의

## 지금은 없는 것

- 로그인/인증, 실제 계좌 연동
- 실제 예측 알고리즘 (전부 `lib/mockData.ts`의 목데이터)
- 모바일(반응형) 레이아웃 — 이번 작업은 노트북 웹 화면만 대상으로 했습니다
