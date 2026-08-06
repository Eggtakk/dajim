"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { Button } from "@/components/ui/Button";

const STEPS = [
  {
    eyebrow: "매달 다짐하지만",
    title: "이번 달도 다짐만으로\n끝났다면",
    body: "다짐은 소비 습관을 바꾸는 걸 도와주는 서비스예요. 작심삼일이어도 괜찮아요, 처음이니까.",
  },
  {
    eyebrow: "다짐이 하는 일",
    title: "지금 습관대로면,\n한 달 뒤 어떻게 될지 미리 보여드려요",
    body: "연결한 계좌의 소비 데이터를 바탕으로, 이 습관을 유지했을 때의 결과를 예측해요.",
  },
  {
    eyebrow: "그다음은",
    title: "목표를 정하면, 며칠마다\n결과로 확인시켜드려요",
    body: "기간과 목표를 직접 정하고, 정해둔 주기마다 얼마나 가까워졌는지 숫자로 알려드려요.",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const isLast = step === STEPS.length - 1;
  const current = STEPS[step];

  return (
    <div className="onboard-page">
      <div className="onboard-card">
        <div className="onboard-illo">
          <Icon name="i-target" />
        </div>
        <div className="eyebrow">{current.eyebrow}</div>
        <h2 style={{ whiteSpace: "pre-line" }}>{current.title}</h2>
        <p>{current.body}</p>
        <div className="dots">
          {STEPS.map((_, i) => (
            <span key={i} className={i === step ? "active" : ""} />
          ))}
        </div>
        <div
          style={{
            marginTop: 28,
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          {isLast ? (
            <Button block onClick={() => router.push("/home")}>
              계좌 연결하고 시작하기
            </Button>
          ) : (
            <Button block onClick={() => setStep((s) => s + 1)}>
              다음
            </Button>
          )}
          <Button
            variant="ghost"
            block
            style={{ borderColor: "transparent" }}
            onClick={() => router.push("/home")}
          >
            나중에 할게요
          </Button>
        </div>
      </div>
    </div>
  );
}
