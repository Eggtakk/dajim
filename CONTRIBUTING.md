# 브랜치 & 협업 규칙

3명이 함께 작업하는 저장소라 무겁지 않은 트렁크 기반 워크플로우를 씁니다.

## 기본 원칙

- `main`은 항상 배포 가능한 상태로 유지합니다. `main`에 직접 push하지 않고, 모든 변경은 브랜치 → PR → 리뷰 → 머지를 거칩니다.
- 브랜치는 작업 하나가 끝나면 바로 머지하고 삭제하는 걸 기본으로 합니다(짧게 살고 자주 머지).
- 머지는 Squash and merge를 기본으로 사용해 `main`의 커밋 히스토리를 깔끔하게 유지합니다.

## 브랜치 이름

`<타입>/<영역>-<짧은-설명>` 형식을 씁니다. 영역은 작업 대상이 `dajim-web`(실사용 버전)인지 `prototype`(정적 프로토타입)인지 구분하기 위한 접두어입니다.

| 타입 | 용도 | 예시 |
| --- | --- | --- |
| `feature/` | 새 기능 | `feature/web-tracking-chart`, `feature/proto-onboarding` |
| `fix/` | 버그 수정 | `fix/web-goal-slider` |
| `chore/` | 설정, 의존성, 자잘한 정리 | `chore/web-upgrade-next` |
| `docs/` | 문서 | `docs/readme-update` |

두 영역에 걸치지 않는 작업이면 영역 접두어 없이 `feature/<설명>`만 써도 됩니다.

## PR 규칙

- PR 설명에 무엇을, 왜 바꿨는지 간단히 남깁니다.
- 머지 전 팀원 1명 이상의 승인(review approval)을 받습니다.
- `dajim-web`을 바꿨다면 PR 올리기 전에 로컬에서 `npm run lint`와 `npm run build`가 통과하는지 확인합니다.
