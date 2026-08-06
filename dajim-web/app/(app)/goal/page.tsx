"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Chip } from "@/components/ui/Chip";
import { CATEGORIES, DURATION_OPTIONS, TRACKING_DAY_OPTIONS, getCategory } from "@/lib/categories";
import { useGoalSettings } from "@/lib/useGoalSettings";
import { getExpectedSavingWon } from "@/lib/mockData";
import { formatWon } from "@/lib/format";

export default function GoalPage() {
  const router = useRouter();
  const { goal, setGoal } = useGoalSettings();

  const category = getCategory(goal.categoryId);
  const expectedSaving = getExpectedSavingWon(goal);

  return (
    <>
      <div className="canvas-head">
        <div>
          <h1>목표 설정</h1>
          <div className="date">개선 수준을 직접 정하면, 예측도 함께 바뀌어요</div>
        </div>
      </div>

      <Card style={{ padding: "26px 30px" }}>
        <div className="field-label">어떤 소비를 줄일까요</div>
        <div className="chiprow">
          {CATEGORIES.map((c) => (
            <Chip
              key={c.id}
              selected={goal.categoryId === c.id}
              onClick={() => setGoal({ categoryId: c.id })}
            >
              {c.label}
            </Chip>
          ))}
        </div>

        <div className="field-label">기간</div>
        <div className="chiprow">
          {DURATION_OPTIONS.map((m) => (
            <Chip
              key={m}
              selected={goal.durationMonths === m}
              onClick={() => setGoal({ durationMonths: m })}
            >
              {m}개월
            </Chip>
          ))}
        </div>

        <div className="field-label">
          얼마나 줄일까요
          <span className="pill pill-neutral num">{goal.percent}%</span>
        </div>
        <div className="slider-wrap">
          <input
            type="range"
            min={5}
            max={50}
            step={1}
            value={goal.percent}
            onChange={(e) => setGoal({ percent: Number(e.target.value) })}
          />
          <div className="slider-nums">
            <span>5%</span>
            <span>50%</span>
          </div>
        </div>

        <div className="field-label">얼마나 자주 확인할까요</div>
        <div className="chiprow">
          {TRACKING_DAY_OPTIONS.map((d) => (
            <Chip
              key={d}
              selected={goal.trackingDays === d}
              onClick={() => setGoal({ trackingDays: d })}
            >
              {d}일마다
            </Chip>
          ))}
        </div>

        <div className="preview-box">
          <div className="t1">
            {category.label} 소비를 {goal.durationMonths}개월간{" "}
            <span className="num">{goal.percent}%</span> 줄이고, {goal.trackingDays}
            일마다 확인할게요.
          </div>
          <div className="t2">
            이번 달 {category.label} 지출({formatWon(category.thisMonthSpend)}) 기준
            예상 절감액 약 <span className="num">{formatWon(expectedSaving)}</span>
          </div>
        </div>

        <Button block style={{ marginTop: 20 }} onClick={() => router.push("/scenario")}>
          다짐 시작하기
        </Button>
      </Card>
    </>
  );
}
