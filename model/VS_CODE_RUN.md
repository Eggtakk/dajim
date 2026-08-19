# VS Code 실행 방법

1. VS Code에서 `model` 폴더를 엽니다.
2. 왼쪽의 Run and Debug를 엽니다.
3. `Goal Simulation Demo`를 선택하고 실행합니다.

터미널에서 직접 실행하려면 아래 명령을 사용합니다.

```powershell
python scripts/goal_simulation_demo.py
```

AI 문장 생성을 쓰려면 `model/.env`의 `OPENAI_API_KEY=` 뒤에 API 키를 넣습니다.
API 키 없이 실행하면 규칙 기반 문장으로 동작합니다.

한 가지 말투만 확인하려면 Run and Debug에서 `AI Tone Scenario Single`을 실행합니다.
세 가지 말투를 AI 문장으로 비교하려면 `AI Tone Scenario Compare`를 실행합니다.

```powershell
python scripts/ai_tone_scenario_demo.py --tone playful_friend
python scripts/ai_tone_scenario_demo.py --all
```

사용할 수 있는 말투는 `soft_coach`, `playful_friend`, `sparta_drill`입니다.
