"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useGoalSettings } from "@/lib/useGoalSettings";
import { getResultData } from "@/lib/mockData";
import { formatPct, formatWon } from "@/lib/format";
import type { ResultOutcome } from "@/lib/types";

export default function ResultPage() {
  const router = useRouter();
  const { goal } = useGoalSettings();
  const [outcome, setOutcome] = useState<ResultOutcome>("win");
  const [chosenId, setChosenId] = useState<string | null>(null);

  const result = getResultData(goal, outcome);
  const isWin = outcome === "win";
  const activeChosen = chosenId ?? result.suggestions[0]?.id ?? null;

  return (
    <>
      <div className="canvas-head">
        <div>
          <h1>결과 확인</h1>
          <div className="date">목표 기간이 끝나면 다짐이 알려드려요</div>
        </div>
      </div>

      <div>
        <div className="segctrl">
          <button
            className={isWin ? "active" : ""}
            onClick={() => {
              setOutcome("win");
              setChosenId(null);
            }}
          >
            달성 예시
          </button>
          <button
            className={!isWin ? "active" : ""}
            onClick={() => {
              setOutcome("lose");
              setChosenId(null);
            }}
          >
            실패 예시
          </button>
        </div>

        <div style={{ marginTop: 16 }}>
          <Card className={`result-hero ${isWin ? "win" : "lose"}`}>
            <div className="ic">
              <Icon name={isWin ? "i-check" : "i-sad"} style={{ width: 28, height: 28 }} />
            </div>
            <h2 style={{ whiteSpace: "pre-line" }}>{result.headline}</h2>
            <p>{result.body}</p>
            <div className="result-compare">
              <div className="box">
                <div className="l">목표</div>
                <div className="v num">-{result.targetPct}%</div>
              </div>
              <div className="box">
                <div className="l">실제</div>
                <div className="v num" style={{ color: isWin ? "var(--brand)" : "var(--ink)" }}>
                  {formatPct(-result.actualPct)}
                </div>
              </div>
              <div className="box">
                <div className="l">절감액</div>
                <div className="v num">{formatWon(result.savedWon)}</div>
              </div>
            </div>
          </Card>

          {isWin ? (
            <Card style={{ padding: "18px 20px", marginTop: 14 }}>
              <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 6 }}>
                다음 다짐을 추천해요
              </div>
              {result.suggestions.map((s) => (
                <div key={s.id} className="reset-card chosen">
                  <div className="t">{s.title}</div>
                  <div className="d">{s.description}</div>
                </div>
              ))}
            </Card>
          ) : (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 4 }}>
                목표 재설정을 추천해요
              </div>
              {result.suggestions.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`reset-card ${activeChosen === s.id ? "chosen" : ""}`}
                  onClick={() => setChosenId(s.id)}
                >
                  <div className="t">{s.title}</div>
                  <div className="d">{s.description}</div>
                </button>
              ))}
            </div>
          )}

          <Button
            variant="accent"
            block
            style={{ marginTop: 16 }}
            onClick={() => router.push("/goal")}
          >
            {isWin ? "다음 다짐 시작하기" : "이 방법으로 다시 다짐하기"}
          </Button>
        </div>
      </div>
    </>
  );
}
