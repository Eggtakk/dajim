import os
import sys
from pathlib import Path
from pprint import pprint

sys.path.append(str(Path(__file__).resolve().parents[1]))

from prediction.goal_simulation import (
    GoalSimulationEngine,
    OpenAIScenarioNarrativeProvider,
    ScoreGoal,
    ScenarioPresentationProfile,
    demo_snapshot,
)
from prediction.scenario_tone_presets import DEFAULT_SCENARIO_TONE


def main() -> None:
    narrative_provider = (
        OpenAIScenarioNarrativeProvider() if os.getenv("OPENAI_API_KEY") else None
    )
    engine = GoalSimulationEngine(
        narrative_provider=narrative_provider,
        presentation_profile=ScenarioPresentationProfile(
            tone_preset=os.getenv("SCENARIO_TONE", DEFAULT_SCENARIO_TONE),
            tone="friendly",
            financial_literacy="beginner",
            channel="app_card",
        ),
    )

    # 온보딩에서 사용자가 "위험 점수 10점 낮추기"를 선택했다고 가정한 예시입니다.
    goal = ScoreGoal(target_score_reduction=10, horizon_months=1)
    snapshot = demo_snapshot()

    plan = engine.recommend_goal_plan(snapshot=snapshot, goal=goal)

    print("\n[요약]")
    print(plan["summary_message"])

    print("\n[핵심 수치]")
    pprint(
        {
            "현재 위험 점수": plan["current_risk_score"],
            "목표 위험 점수": plan["target_risk_score"],
            "예상 위험 점수": plan["expected_risk_score"],
            "예상 점수 감소": plan["expected_score_reduction"],
            "목표 달성률": f"{plan['goal_attainment_rate']}%",
            "예상 이번 달 소비": f"{plan['expected_month_total_spend']:,}원",
            "전월 대비 소비 변화": (
                f"{plan['monthly_spend_change_amount_vs_previous']:+,}원 "
                f"({plan['spend_change_rate_vs_previous_month']:+.1f}%)"
            ),
            "기본 예측 대비 소비 변화": (
                f"{plan['monthly_spend_change_amount_vs_baseline']:+,}원 "
                f"({plan['spend_change_rate_vs_baseline_prediction']:+.1f}%)"
            ),
        },
        sort_dicts=False,
    )

    print("\n[긍정 시나리오]")
    for scenario in plan["positive_scenarios"]:
        print("-", scenario["message"])
        print(
            "  ",
            f"{scenario['category_label']} {scenario['category_spend_before']:,}원",
            "->",
            f"{scenario['expected_category_spend']:,}원",
            f"({scenario['category_spend_change_amount']:+,}원)",
        )

    print("\n[부정 시나리오]")
    for scenario in plan["negative_scenarios"]:
        print("-", scenario["message"])
        print(
            "  ",
            f"{scenario['category_label']} {scenario['category_spend_before']:,}원",
            "->",
            f"{scenario['expected_category_spend']:,}원",
            f"({scenario['category_spend_change_amount']:+,}원)",
        )


if __name__ == "__main__":
    main()


