from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List, Literal, Optional, Protocol
from urllib import error, request

try:
    from .scenario_tone_presets import (
        DEFAULT_SCENARIO_TONE,
        ScenarioToneKey,
        build_tone_instruction,
    )
except ImportError:
    from scenario_tone_presets import (
        DEFAULT_SCENARIO_TONE,
        ScenarioToneKey,
        build_tone_instruction,
    )


CategoryKey = Literal[
    "shopping",
    "dining",
    "transport",
    "leisure",
    "social",
    "simple_pay",
    "installment",
    "cash_advance",
]

AVAILABLE_SCORE_GOALS = (5, 10, 15)


@dataclass(frozen=True)
class CategoryPolicy:
    label: str
    controllability: float
    risk_weight: float
    max_cut_rate: float


@dataclass(frozen=True)
class PredictionSnapshot:
    user_id: str
    current_risk_score: float
    previous_month_total_spend: int
    predicted_month_total_spend: int
    predicted_category_spend: Dict[CategoryKey, int]
    predicted_category_growth_rate: Dict[CategoryKey, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoreGoal:
    target_score_reduction: int
    horizon_months: int = 1


@dataclass(frozen=True)
class ScenarioResult:
    category: CategoryKey
    category_label: str
    action: str
    change_rate: float
    category_spend_before: int
    expected_category_spend: int
    category_spend_change_amount: int
    expected_month_total_spend: int
    monthly_spend_change_amount_vs_previous: int
    monthly_spend_change_amount_vs_baseline: int
    spend_change_rate_vs_previous_month: float
    spend_change_rate_vs_baseline_prediction: float
    expected_risk_score: float
    expected_score_reduction: float
    goal_attainment_rate: float
    message: str


@dataclass(frozen=True)
class ScenarioPresentationProfile:
    display_name: Optional[str] = None
    tone_preset: ScenarioToneKey = DEFAULT_SCENARIO_TONE
    tone: Literal["friendly", "calm", "encouraging"] = "friendly"
    financial_literacy: Literal["beginner", "intermediate", "advanced"] = "beginner"
    channel: Literal["app_card", "chat", "push"] = "app_card"


class ScenarioNarrativeProvider(Protocol):
    def rewrite_goal_plan(
        self,
        plan: Dict[str, object],
        snapshot: PredictionSnapshot,
        goal: ScoreGoal,
        profile: ScenarioPresentationProfile,
    ) -> Dict[str, object]:
        """Rewrite user-facing scenario messages without changing calculated values."""


class OpenAIScenarioNarrativeProvider:
    """AI narrator that rewrites scenario messages through the OpenAI Responses API.

    Set OPENAI_API_KEY before using this provider. If the API call fails or returns
    invalid JSON, the original rule-based plan is returned unchanged.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY",
        model_env: str = "OPENAI_SCENARIO_MODEL",
        timeout_seconds: int = 300,
        max_retries: int = 2,
    ) -> None:
        self.api_key = (os.getenv(api_key_env) or "").strip()
        self.model = model or os.getenv(model_env, "gpt-5-mini")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.last_used_ai = False
        self.last_error: Optional[str] = None

    def rewrite_goal_plan(
        self,
        plan: Dict[str, object],
        snapshot: PredictionSnapshot,
        goal: ScoreGoal,
        profile: ScenarioPresentationProfile,
    ) -> Dict[str, object]:
        self.last_used_ai = False
        self.last_error = None

        if not self.api_key:
            self.last_error = "OPENAI_API_KEY is not set."
            return plan

        try:
            response = self._create_response(plan, snapshot, goal, profile)
            content = _extract_response_text(response)
            narrative = json.loads(content)
        except error.HTTPError as exc:
            self.last_error = _format_http_error(exc)
            return plan
        except (OSError, ValueError, KeyError, TypeError, error.URLError) as exc:
            self.last_error = str(exc)
            return plan

        rewritten = apply_ai_narrative(plan, narrative)
        self.last_used_ai = rewritten is not plan
        if not self.last_used_ai:
            self.last_error = "AI narrative response did not match the expected shape."
        return rewritten

    def _create_response(
        self,
        plan: Dict[str, object],
        snapshot: PredictionSnapshot,
        goal: ScoreGoal,
        profile: ScenarioPresentationProfile,
    ) -> Dict[str, object]:
        tone_instruction = build_tone_instruction(profile.tone_preset)
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "너는 금융 앱의 소비 코칭 문구를 작성하는 한국어 UX 라이터다. "
                        "사용자가 부담스럽지 않게 이해하도록 친근하고 구체적으로 말한다. "
                        "계산된 금액, 비율, 점수는 절대 바꾸거나 새로 만들지 않는다. "
                        "금융상품 추천, 신용 보장, 단정적 조언은 하지 않는다. "
                        "각 문장은 앱 카드에서 읽기 좋게 짧게 쓴다."
                        f"\n\n{tone_instruction}"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "profile": asdict(profile),
                            "goal": asdict(goal),
                            "snapshot": asdict(snapshot),
                            "calculated_plan": plan,
                            "task": (
                                "summary_message, positive_scenarios, negative_scenarios를 "
                                "사용자 친화적인 한국어 문장으로 다시 작성해줘. "
                                "positive_scenarios와 negative_scenarios는 입력 순서와 개수를 유지해."
                            ),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "scenario_narrative",
                    "strict": True,
                    "schema": _narrative_schema(
                        positive_count=len(plan.get("positive_scenarios", [])),
                        negative_count=len(plan.get("negative_scenarios", [])),
                    ),
                }
            },
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        api_request = request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers=headers,
            method="POST",
        )

        for attempt in range(self.max_retries + 1):
            try:
                with request.urlopen(api_request, timeout=self.timeout_seconds) as api_response:
                    return json.loads(api_response.read().decode("utf-8"))
            except error.HTTPError as exc:
                if exc.code != 429 or attempt >= self.max_retries:
                    raise
                time.sleep(_retry_delay_seconds(exc, attempt))

        raise RuntimeError("OpenAI request retry loop ended unexpectedly.")


class GoalSimulationEngine:
    """What-if simulator for adjustable spending coaching."""

    DEFAULT_POLICIES: Dict[CategoryKey, CategoryPolicy] = {
        "shopping": CategoryPolicy("쇼핑", 0.85, 0.90, 0.30),
        "dining": CategoryPolicy("요식", 0.80, 0.75, 0.25),
        "transport": CategoryPolicy("교통", 0.45, 0.35, 0.12),
        "leisure": CategoryPolicy("여유생활", 0.90, 0.80, 0.35),
        "social": CategoryPolicy("사교활동", 0.75, 0.70, 0.25),
        "simple_pay": CategoryPolicy("간편결제", 0.70, 0.65, 0.20),
        "installment": CategoryPolicy("할부", 0.65, 0.95, 0.20),
        "cash_advance": CategoryPolicy("현금서비스", 0.95, 1.30, 0.60),
    }

    def __init__(
        self,
        policies: Optional[Dict[CategoryKey, CategoryPolicy]] = None,
        narrative_provider: Optional[ScenarioNarrativeProvider] = None,
        presentation_profile: Optional[ScenarioPresentationProfile] = None,
    ) -> None:
        self.policies = policies or self.DEFAULT_POLICIES
        self.narrative_provider = narrative_provider
        self.presentation_profile = presentation_profile or ScenarioPresentationProfile()

    def simulate(
        self,
        snapshot: PredictionSnapshot,
        goal: ScoreGoal,
        categories: Optional[Iterable[CategoryKey]] = None,
    ) -> List[ScenarioResult]:
        selected_categories = list(categories or self.policies.keys())
        results = [
            self._positive_scenario(snapshot, goal, category)
            for category in selected_categories
            if category in snapshot.predicted_category_spend
        ]

        results.sort(
            key=lambda item: (
                item.goal_attainment_rate,
                item.expected_score_reduction,
                -item.expected_month_total_spend,
            ),
            reverse=True,
        )
        return results

    def negative_scenarios(
        self,
        snapshot: PredictionSnapshot,
        categories: Optional[Iterable[CategoryKey]] = None,
    ) -> List[ScenarioResult]:
        selected_categories = list(categories or self.policies.keys())
        results = [
            self._negative_scenario(snapshot, category)
            for category in selected_categories
            if category in snapshot.predicted_category_spend
        ]

        results.sort(
            key=lambda item: (
                item.expected_risk_score,
                item.spend_change_rate_vs_previous_month,
            ),
            reverse=True,
        )
        return results

    def recommend_goal_plan(
        self,
        snapshot: PredictionSnapshot,
        goal: ScoreGoal,
        top_n: int = 3,
    ) -> Dict[str, object]:
        positive = self.simulate(snapshot, goal)
        negative = self.negative_scenarios(snapshot)
        best_actions = positive[:top_n]

        combined_expected_spend = snapshot.predicted_month_total_spend
        combined_score_reduction = 0.0

        for result in best_actions:
            base_amount = snapshot.predicted_category_spend[result.category]
            cut_amount = int(base_amount * result.change_rate)
            combined_expected_spend -= cut_amount
            combined_score_reduction += result.expected_score_reduction

        combined_score_reduction = min(combined_score_reduction, float(goal.target_score_reduction))
        combined_expected_score = clamp_score(snapshot.current_risk_score - combined_score_reduction)
        combined_change_rate = percent_change(
            combined_expected_spend,
            snapshot.previous_month_total_spend,
        )
        combined_baseline_change_rate = percent_change(
            combined_expected_spend,
            snapshot.predicted_month_total_spend,
        )
        attainment_rate = attainment(combined_score_reduction, goal.target_score_reduction)

        plan = {
            "user_id": snapshot.user_id,
            "current_risk_score": round(snapshot.current_risk_score, 1),
            "target_risk_score": round(
                clamp_score(snapshot.current_risk_score - goal.target_score_reduction),
                1,
            ),
            "expected_risk_score": round(combined_expected_score, 1),
            "expected_score_reduction": round(combined_score_reduction, 1),
            "goal_attainment_rate": round(attainment_rate, 1),
            "expected_month_total_spend": combined_expected_spend,
            "monthly_spend_change_amount_vs_previous": (
                combined_expected_spend - snapshot.previous_month_total_spend
            ),
            "monthly_spend_change_amount_vs_baseline": (
                combined_expected_spend - snapshot.predicted_month_total_spend
            ),
            "spend_change_rate_vs_previous_month": round(combined_change_rate, 1),
            "spend_change_rate_vs_baseline_prediction": round(combined_baseline_change_rate, 1),
            "positive_scenarios": [asdict(scenario) for scenario in best_actions],
            "negative_scenarios": [asdict(scenario) for scenario in negative[:top_n]],
            "summary_message": self._summary_message(
                goal,
                combined_expected_spend - snapshot.previous_month_total_spend,
                combined_expected_spend - snapshot.predicted_month_total_spend,
                combined_change_rate,
                combined_baseline_change_rate,
                snapshot.current_risk_score,
                combined_expected_score,
                attainment_rate,
            ),
        }
        if self.narrative_provider is None:
            return plan

        return self.narrative_provider.rewrite_goal_plan(
            plan=plan,
            snapshot=snapshot,
            goal=goal,
            profile=self.presentation_profile,
        )

    def _positive_scenario(
        self,
        snapshot: PredictionSnapshot,
        goal: ScoreGoal,
        category: CategoryKey,
    ) -> ScenarioResult:
        policy = self.policies[category]
        base_amount = snapshot.predicted_category_spend[category]
        spend_share = safe_divide(base_amount, max(snapshot.predicted_month_total_spend, 1))
        target_intensity = min(max(goal.target_score_reduction / 15, 0.0), 1.0)
        recommended_cut_rate = 0.05 + (policy.max_cut_rate - 0.05) * target_intensity
        cut_amount = int(base_amount * recommended_cut_rate)
        expected_category_spend = max(0, base_amount - cut_amount)
        expected_spend = max(0, snapshot.predicted_month_total_spend - cut_amount)
        score_reduction = score_delta(
            spend_share=spend_share,
            change_rate=recommended_cut_rate,
            policy=policy,
            direction="decrease",
            target_score_reduction=goal.target_score_reduction,
        )
        expected_score = clamp_score(snapshot.current_risk_score - score_reduction)
        spend_change = percent_change(expected_spend, snapshot.previous_month_total_spend)
        baseline_change = percent_change(expected_spend, snapshot.predicted_month_total_spend)
        goal_rate = attainment(score_reduction, goal.target_score_reduction)
        message = positive_message(
            label=policy.label,
            cut_rate=recommended_cut_rate,
            cut_amount=cut_amount,
            spend_change=spend_change,
            spend_change_amount=expected_spend - snapshot.previous_month_total_spend,
            baseline_change=baseline_change,
            baseline_change_amount=expected_spend - snapshot.predicted_month_total_spend,
            current_score=snapshot.current_risk_score,
            expected_score=expected_score,
        )

        return ScenarioResult(
            category=category,
            category_label=policy.label,
            action="decrease",
            change_rate=round(recommended_cut_rate, 4),
            category_spend_before=base_amount,
            expected_category_spend=expected_category_spend,
            category_spend_change_amount=-cut_amount,
            expected_month_total_spend=expected_spend,
            monthly_spend_change_amount_vs_previous=(
                expected_spend - snapshot.previous_month_total_spend
            ),
            monthly_spend_change_amount_vs_baseline=(
                expected_spend - snapshot.predicted_month_total_spend
            ),
            spend_change_rate_vs_previous_month=round(spend_change, 2),
            spend_change_rate_vs_baseline_prediction=round(baseline_change, 2),
            expected_risk_score=round(expected_score, 2),
            expected_score_reduction=round(score_reduction, 2),
            goal_attainment_rate=round(goal_rate, 2),
            message=message,
        )

    def _negative_scenario(
        self,
        snapshot: PredictionSnapshot,
        category: CategoryKey,
    ) -> ScenarioResult:
        policy = self.policies[category]
        base_amount = snapshot.predicted_category_spend[category]
        spend_share = safe_divide(base_amount, max(snapshot.predicted_month_total_spend, 1))
        growth_rate = snapshot.predicted_category_growth_rate.get(category, 0.08)
        assumed_growth_rate = max(0.03, min(growth_rate, 0.25))
        growth_amount = int(base_amount * assumed_growth_rate)
        expected_category_spend = base_amount + growth_amount
        expected_spend = snapshot.predicted_month_total_spend + growth_amount
        score_increase = score_delta(
            spend_share=spend_share,
            change_rate=assumed_growth_rate,
            policy=policy,
            direction="increase",
            target_score_reduction=10,
        )
        expected_score = clamp_score(snapshot.current_risk_score + score_increase)
        spend_change = percent_change(expected_spend, snapshot.previous_month_total_spend)
        baseline_change = percent_change(expected_spend, snapshot.predicted_month_total_spend)

        message = (
            f"{policy.label} 소비가 현재 흐름대로 {format_won(growth_amount)} "
            f"늘어나면({assumed_growth_rate * 100:.0f}%), "
            f"이번 달 소비량은 기본 예측보다 {format_won(growth_amount)} 많아지고 "
            f"전월 대비 {format_signed_won(expected_spend - snapshot.previous_month_total_spend)}"
            f"({spend_change:+.1f}%) 수준이 되며, "
            f"종합 금융 위험 점수는 {snapshot.current_risk_score:.0f}점에서 "
            f"{expected_score:.0f}점까지 오를 수 있습니다."
        )

        return ScenarioResult(
            category=category,
            category_label=policy.label,
            action="increase",
            change_rate=round(assumed_growth_rate, 4),
            category_spend_before=base_amount,
            expected_category_spend=expected_category_spend,
            category_spend_change_amount=growth_amount,
            expected_month_total_spend=expected_spend,
            monthly_spend_change_amount_vs_previous=(
                expected_spend - snapshot.previous_month_total_spend
            ),
            monthly_spend_change_amount_vs_baseline=(
                expected_spend - snapshot.predicted_month_total_spend
            ),
            spend_change_rate_vs_previous_month=round(spend_change, 2),
            spend_change_rate_vs_baseline_prediction=round(baseline_change, 2),
            expected_risk_score=round(expected_score, 2),
            expected_score_reduction=round(-score_increase, 2),
            goal_attainment_rate=0.0,
            message=message,
        )

    @staticmethod
    def _summary_message(
        goal: ScoreGoal,
        spend_change_amount: int,
        baseline_change_amount: int,
        spend_change_rate: float,
        baseline_change_rate: float,
        current_score: float,
        expected_score: float,
        attainment_rate: float,
    ) -> str:
        if spend_change_amount < 0:
            spend_part = (
                f"전월보다 {format_won(abs(spend_change_amount))} 적게 쓰는 "
                f"흐름({spend_change_rate:.1f}%)으로 바뀌고"
            )
        else:
            spend_part = (
                f"전월 대비 {format_signed_won(spend_change_amount)}"
                f"({spend_change_rate:+.1f}%)이고, "
                f"기본 예측보다는 {format_won(abs(baseline_change_amount))} "
                f"낮습니다({baseline_change_rate:.1f}%)"
            )

        return (
            f"{goal.horizon_months}개월 동안 위험 점수 {goal.target_score_reduction}점 낮추기 목표 기준, "
            f"추천 행동을 적용하면 이번 달 조절 가능 소비는 {spend_part}. "
            f"종합 금융 위험 점수는 {current_score:.0f}점에서 {expected_score:.0f}점으로 "
            f"변할 것으로 예상됩니다. 목표 달성률은 약 {attainment_rate:.0f}%입니다."
        )


def apply_ai_narrative(plan: Dict[str, object], narrative: Dict[str, object]) -> Dict[str, object]:
    summary_message = narrative.get("summary_message")
    positive_messages = narrative.get("positive_scenarios")
    negative_messages = narrative.get("negative_scenarios")
    positive_scenarios = plan.get("positive_scenarios", [])
    negative_scenarios = plan.get("negative_scenarios", [])

    if not isinstance(summary_message, str) or not summary_message.strip():
        return plan
    if not _valid_message_list(positive_messages, len(positive_scenarios)):
        return plan
    if not _valid_message_list(negative_messages, len(negative_scenarios)):
        return plan

    rewritten = dict(plan)
    rewritten["summary_message"] = summary_message.strip()
    rewritten["positive_scenarios"] = [
        {**scenario, "message": message.strip()}
        for scenario, message in zip(positive_scenarios, positive_messages)
    ]
    rewritten["negative_scenarios"] = [
        {**scenario, "message": message.strip()}
        for scenario, message in zip(negative_scenarios, negative_messages)
    ]
    return rewritten


def _valid_message_list(value: object, expected_length: int) -> bool:
    return (
        isinstance(value, list)
        and len(value) == expected_length
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _extract_response_text(response_body: Dict[str, object]) -> str:
    output_text = response_body.get("output_text")
    if isinstance(output_text, str):
        return output_text

    for output in response_body.get("output", []):
        if not isinstance(output, dict):
            continue
        for content in output.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                return text

    raise ValueError("OpenAI response did not include text output.")


def _format_http_error(exc: error.HTTPError) -> str:
    details = [f"HTTP {exc.code}: {exc.reason}"]
    request_id = exc.headers.get("x-request-id")
    retry_after = exc.headers.get("retry-after")
    rate_limit_headers = {
        "x-ratelimit-limit-requests": exc.headers.get("x-ratelimit-limit-requests"),
        "x-ratelimit-remaining-requests": exc.headers.get("x-ratelimit-remaining-requests"),
        "x-ratelimit-reset-requests": exc.headers.get("x-ratelimit-reset-requests"),
        "x-ratelimit-limit-tokens": exc.headers.get("x-ratelimit-limit-tokens"),
        "x-ratelimit-remaining-tokens": exc.headers.get("x-ratelimit-remaining-tokens"),
        "x-ratelimit-reset-tokens": exc.headers.get("x-ratelimit-reset-tokens"),
    }

    if request_id:
        details.append(f"x-request-id={request_id}")
    if retry_after:
        details.append(f"retry-after={retry_after}")

    visible_rate_limits = [
        f"{key}={value}" for key, value in rate_limit_headers.items() if value
    ]
    if visible_rate_limits:
        details.append("rate-limit: " + ", ".join(visible_rate_limits))

    response_body = exc.read().decode("utf-8", errors="replace").strip()
    if response_body:
        details.append(f"body={response_body[:1000]}")

    return " | ".join(details)


def _retry_delay_seconds(exc: error.HTTPError, attempt: int) -> float:
    retry_after = exc.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass

    return min(2.0 * (attempt + 1), 10.0)


def _narrative_schema(positive_count: int, negative_count: int) -> Dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["summary_message", "positive_scenarios", "negative_scenarios"],
        "properties": {
            "summary_message": {
                "type": "string",
                "description": "One concise, friendly Korean summary for the whole plan.",
            },
            "positive_scenarios": {
                "type": "array",
                "minItems": positive_count,
                "maxItems": positive_count,
                "items": {"type": "string"},
            },
            "negative_scenarios": {
                "type": "array",
                "minItems": negative_count,
                "maxItems": negative_count,
                "items": {"type": "string"},
            },
        },
    }


def positive_message(
    label: str,
    cut_rate: float,
    cut_amount: int,
    spend_change: float,
    spend_change_amount: int,
    baseline_change: float,
    baseline_change_amount: int,
    current_score: float,
    expected_score: float,
) -> str:
    if spend_change < 0:
        spend_part = (
            f"이번 달 소비량이 전월보다 {format_won(abs(spend_change_amount))} "
            f"줄어드는 흐름으로 바뀌고({spend_change:.1f}%)"
        )
    else:
        spend_part = (
            f"이번 달 예상 소비는 기본 예측보다 "
            f"{format_won(abs(baseline_change_amount))} 낮아집니다"
            f"({baseline_change:.1f}%). "
            f"전월 대비로는 {format_signed_won(spend_change_amount)}"
            f"({spend_change:+.1f}%) 수준입니다"
        )

    return (
        f"{label} 소비를 {format_won(cut_amount)} 줄이면({cut_rate * 100:.0f}%), "
        f"{spend_part}. 종합 금융 위험 점수는 {current_score:.0f}점에서 "
        f"{expected_score:.0f}점으로 낮아질 수 있습니다."
    )


def format_won(amount: int) -> str:
    return f"{amount:,}원"


def format_signed_won(amount: int) -> str:
    sign = "+" if amount > 0 else ""
    return f"{sign}{amount:,}원"


def score_delta(
    spend_share: float,
    change_rate: float,
    policy: CategoryPolicy,
    direction: Literal["increase", "decrease"],
    target_score_reduction: int,
) -> float:
    base_delta = spend_share * change_rate * policy.controllability * policy.risk_weight * 100
    if direction == "decrease":
        return min(base_delta, float(target_score_reduction))
    return min(base_delta, 12.0)


def percent_change(current: int, previous: int) -> float:
    if previous <= 0:
        return 0.0
    return (current - previous) / previous * 100


def attainment(score_reduction: float, target_score_reduction: int) -> float:
    if target_score_reduction <= 0:
        return 100.0
    return min(max(score_reduction / target_score_reduction * 100, 0.0), 100.0)


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def clamp_score(score: float) -> float:
    return min(max(score, 0.0), 100.0)


def demo_snapshot() -> PredictionSnapshot:
    return PredictionSnapshot(
        user_id="SYN_20S_RV_CA_SAMPLE",
        current_risk_score=72,
        previous_month_total_spend=1_450_000,
        predicted_month_total_spend=1_620_000,
        predicted_category_spend={
            "shopping": 310_000,
            "dining": 280_000,
            "transport": 130_000,
            "leisure": 180_000,
            "social": 120_000,
            "simple_pay": 260_000,
            "installment": 210_000,
            "cash_advance": 130_000,
        },
        predicted_category_growth_rate={
            "shopping": 0.12,
            "dining": 0.10,
            "transport": 0.04,
            "leisure": 0.16,
            "social": 0.09,
            "simple_pay": 0.14,
            "installment": 0.08,
            "cash_advance": 0.20,
        },
    )


if __name__ == "__main__":
    engine = GoalSimulationEngine()
    plan = engine.recommend_goal_plan(
        snapshot=demo_snapshot(),
        goal=ScoreGoal(target_score_reduction=10, horizon_months=1),
    )

    print(plan["summary_message"])
    print("\n[긍정 시나리오]")
    for scenario in plan["positive_scenarios"]:
        print("-", scenario["message"])

    print("\n[부정 시나리오]")
    for scenario in plan["negative_scenarios"]:
        print("-", scenario["message"])

