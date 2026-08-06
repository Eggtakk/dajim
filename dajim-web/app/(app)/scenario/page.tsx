"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PredictCard } from "@/components/PredictCard";
import { Sparkline } from "@/components/Sparkline";
import { Button } from "@/components/ui/Button";
import { useGoalSettings } from "@/lib/useGoalSettings";
import { getPredictionScenario } from "@/lib/mockData";
import { getCategory } from "@/lib/categories";
import type { ScenarioMode } from "@/lib/types";

export default function ScenarioPage() {
  const router = useRouter();
  const { goal } = useGoalSettings();
  const [mode, setMode] = useState<ScenarioMode>("neg");

  const scenario = getPredictionScenario(mode, goal);
  const category = getCategory(goal.categoryId);

  return (
    <>
      <div className="canvas-head">
        <div>
          <h1>예측 시나리오</h1>
          <div className="date">지금 습관을 유지하면 vs 목표를 달성하면</div>
        </div>
      </div>

      <div>
        <div className="segctrl">
          <button
            className={mode === "neg" ? "active" : ""}
            onClick={() => setMode("neg")}
          >
            이대로 유지하면
          </button>
          <button
            className={mode === "pos" ? "active" : ""}
            onClick={() => setMode("pos")}
          >
            목표를 달성하면
          </button>
        </div>

        <div style={{ marginTop: 18 }}>
          <PredictCard scenario={scenario} />
        </div>

        <div className="chart-wrap" style={{ marginTop: 16 }}>
          <div className="chart-title">{category.label} 소비 추이 (최근 7주 · 예측 포함)</div>
          <Sparkline values={scenario.trend} color={mode === "neg" ? "ink" : "brand"} />
        </div>

        <Button
          variant="accent"
          block
          style={{ marginTop: 18 }}
          onClick={() => router.push("/goal")}
        >
          이 목표로 다짐하기
        </Button>
      </div>
    </>
  );
}
