"use client";

import { useEffect, useState } from "react";
import { DualSparkline } from "@/components/Sparkline";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { useGoalSettings } from "@/lib/useGoalSettings";
import { fetchTrackingReport } from "@/lib/api";
import { formatPct } from "@/lib/format";
import type { TrackingReport } from "@/lib/types";

export default function TrackingPage() {
  const { goal } = useGoalSettings();
  const [report, setReport] = useState<TrackingReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchTrackingReport(goal)
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [goal]);

  return (
    <>
      <div className="canvas-head">
        <div>
          <h1>소비 트래킹</h1>
          <div className="date">설정한 주기마다 자동으로 분석해드려요</div>
        </div>
      </div>

      {error ? (
        <p className="empty-note">
          불러오지 못했어요: {error}
          <br />
          <button className="btn btn-ghost" style={{ marginTop: 12 }} onClick={() => location.reload()}>
            다시 시도
          </button>
        </p>
      ) : !report ? (
        <p className="empty-note">불러오는 중…</p>
      ) : (
        <div>
          <Card style={{ padding: "18px 20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14.5 }}>
                  {goal.trackingDays}일마다 확인하는 다짐 리포트
                </div>
                <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 2 }}>
                  다음 확인까지 D-{report.daysUntilNext} · {report.cycleIndex}회차 진행 중
                </div>
              </div>
              <Pill tone={report.statusTone}>{report.statusLabel}</Pill>
            </div>
            <div className="track-progress">
              {Array.from({ length: report.totalCycles }, (_, i) => {
                const state =
                  i < report.cycleIndex - 1
                    ? "done"
                    : i === report.cycleIndex - 1
                      ? "now"
                      : "";
                return <div key={i} className={`seg ${state}`} />;
              })}
            </div>
          </Card>

          <div className="chart-wrap" style={{ marginTop: 14 }}>
            <div className="chart-title">목표선 대비 실제 소비</div>
            <DualSparkline
              goalSeries={report.goalSeries}
              actualSeries={report.actualSeries}
            />
            <div className="chart-legend">
              <span>
                <span className="dot" style={{ background: "var(--line-strong)" }} />
                목표선
              </span>
              <span>
                <span className="dot" style={{ background: "var(--brand)" }} />
                실제 소비
              </span>
            </div>
          </div>

          <Card style={{ padding: "16px 20px", marginTop: 14 }}>
            <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 8 }}>
              {report.headline}
            </div>
            {report.categoryDeltas.map((d) => {
              const positive = d.changePct <= 0;
              const color = positive ? "var(--brand)" : "var(--ink)";
              return (
                <div className="cat-row" key={d.categoryId}>
                  <span className="name">
                    <span className="sw" style={{ background: color }} />
                    {d.label}
                  </span>
                  <span className="num" style={{ color, fontWeight: 700 }}>
                    {formatPct(d.changePct)}
                  </span>
                </div>
              );
            })}
          </Card>
        </div>
      )}
    </>
  );
}
