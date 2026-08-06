"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { PredictCard } from "@/components/PredictCard";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { useGoalSettings } from "@/lib/useGoalSettings";
import { getHomeSummary, getPredictionScenario, getUser } from "@/lib/mockData";
import { formatPct, formatWon } from "@/lib/format";
import { getCategory } from "@/lib/categories";

const today = new Intl.DateTimeFormat("ko-KR", {
  month: "long",
  day: "numeric",
  weekday: "long",
}).format(new Date());

const LINKS = [
  {
    href: "/spending",
    icon: "i-receipt",
    title: "나의 소비 확인",
    desc: "통장별 · 날짜별 지출 내역 보기",
  },
  {
    href: "/goal",
    icon: "i-target",
    title: "목표 설정",
    desc: "기간 · 감소율 · 트래킹 주기 정하기",
  },
  {
    href: "/tracking",
    icon: "i-trend",
    title: "소비 트래킹",
    desc: "주기별 분석 리포트 확인",
  },
  {
    href: "/result",
    icon: "i-flag",
    title: "결과 확인",
    desc: "달성 여부 및 다음 다짐 추천",
  },
] as const;

export default function HomePage() {
  const router = useRouter();
  const { goal } = useGoalSettings();
  const user = getUser();
  const summary = getHomeSummary();
  const scenario = getPredictionScenario("neg", goal);
  const category = getCategory(goal.categoryId);

  return (
    <>
      <div className="canvas-head">
        <div>
          <h1>{user.name}님, 오늘도 다짐과 함께해요</h1>
          <div className="date">{today}</div>
        </div>
        <Pill tone="streak">다짐 {user.streakDays}일째</Pill>
      </div>

      <div className="bento">
        <div className="bento-full">
          <PredictCard
            scenario={scenario}
            as="button"
            onClick={() => router.push("/scenario")}
          />
        </div>

        <Card className="stat-card">
          <div className="label">이번 달 총 지출</div>
          <div className="value num">{formatWon(summary.totalSpendWon)}</div>
          <div className="change up">
            전월 동기간 대비 {formatPct(summary.totalSpendChangePct)}
          </div>
        </Card>
        <Card className="stat-card">
          <div className="label">목표 진행률</div>
          <div className="value num">{summary.goalProgressPct}%</div>
          <div className="change">
            {category.label} {goal.percent}%↓ · {goal.durationMonths}개월 목표
          </div>
        </Card>
        <Card className="stat-card">
          <div className="label">다음 트래킹까지</div>
          <div className="value num">D-{summary.trackingDaysLeft}</div>
          <div className="change">
            {goal.trackingDays}일 주기 · {summary.trackingCycleIndex}회차
          </div>
        </Card>

        <div className="bento-full">
          <Card className="link-list">
            {LINKS.map((link) => (
              <Link key={link.href} href={link.href} className="row-link">
                <span className="ic">
                  <Icon name={link.icon} />
                </span>
                <span className="txt">
                  <div className="t">{link.title}</div>
                  <div className="d">{link.desc}</div>
                </span>
                <Icon name="i-chev" className="chev" />
              </Link>
            ))}
          </Card>
        </div>
      </div>
    </>
  );
}
