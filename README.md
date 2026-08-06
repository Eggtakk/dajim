# 다짐 (Dajim)

소비 습관을 예측하고, 목표를 세우고, 결과로 확인하는 소비 습관 코칭 서비스입니다. 이 저장소에는 두 가지 버전이 있습니다.

## [`prototype/`](./prototype) — 클릭 가능한 UI 프로토타입

디자인 논의용 정적 HTML 프로토타입입니다. 빌드 없이 `dajim-prototype.html` 파일을 브라우저로 바로 열면 됩니다. 노트북/iPhone 두 화면 크기를 상단 토글로 전환하며 7개 화면(온보딩·홈·나의소비·목표설정·예측시나리오·소비트래킹·결과확인)을 클릭해볼 수 있습니다.

## [`dajim-web/`](./dajim-web) — 실사용 웹 버전 (Next.js)

노트북/모바일 반응형까지 대응한 실제 동작하는 웹 앱입니다.

```bash
cd dajim-web
npm install
npm run dev   # http://localhost:3000
```

목표 설정값은 localStorage에 저장되어 화면을 이동해도 유지됩니다. 예측·트래킹·결과 데이터는 전부 `dajim-web/lib/mockData.ts`의 목데이터이며, 추후 알고리즘/모델을 연결할 지점으로 설계해뒀습니다. 자세한 내용은 [`dajim-web/README.md`](./dajim-web/README.md)를 참고하세요.
