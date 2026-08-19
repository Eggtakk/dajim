from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from prediction.goal_simulation import (
    GoalSimulationEngine,
    OpenAIScenarioNarrativeProvider,
    ScoreGoal,
    ScenarioPresentationProfile,
    demo_snapshot,
)
from prediction.scenario_tone_presets import (
    DEFAULT_SCENARIO_TONE,
    SCENARIO_TONE_PRESETS,
    ScenarioToneKey,
    get_scenario_tone,
)


def main() -> None:
    load_env_file(Path(".env"))
    args = parse_args()
    tone_keys = list(SCENARIO_TONE_PRESETS) if args.all else [args.tone]

    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("OPENAI_API_KEY가 없습니다. .env 파일에 API 키를 넣은 뒤 다시 실행해주세요.")
        return

    for tone_key in tone_keys:
        run_tone_demo(tone_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI 시나리오 문장을 선택한 말투로 생성해 비교합니다."
    )
    parser.add_argument(
        "--tone",
        choices=list(SCENARIO_TONE_PRESETS),
        default=os.getenv("SCENARIO_TONE", DEFAULT_SCENARIO_TONE),
        help="테스트할 말투를 선택합니다.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="세 가지 말투를 모두 실행해 비교합니다.",
    )
    return parser.parse_args()


def run_tone_demo(tone_key: ScenarioToneKey) -> None:
    preset = get_scenario_tone(tone_key)
    provider = OpenAIScenarioNarrativeProvider()
    engine = GoalSimulationEngine(
        narrative_provider=provider,
        presentation_profile=ScenarioPresentationProfile(
            tone_preset=tone_key,
            financial_literacy="beginner",
            channel="app_card",
        ),
    )
    plan = engine.recommend_goal_plan(
        snapshot=demo_snapshot(),
        goal=ScoreGoal(target_score_reduction=10, horizon_months=1),
    )

    print("\n" + "=" * 70)
    print(f"[{preset.label}] {preset.description}")
    print(f"AI 적용 여부: {'성공' if provider.last_used_ai else '실패'}")
    if provider.last_error:
        print(f"오류: {provider.last_error}")
    print("\n[요약]")
    print(plan["summary_message"])

    print("\n[긍정 시나리오]")
    for scenario in plan["positive_scenarios"]:
        print(f"- {scenario['message']}")

    print("\n[부정 시나리오]")
    for scenario in plan["negative_scenarios"]:
        print(f"- {scenario['message']}")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


if __name__ == "__main__":
    main()


