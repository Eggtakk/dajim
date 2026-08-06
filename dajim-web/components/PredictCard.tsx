import { Icon } from "./icons/Icon";
import type { PredictionScenario } from "@/lib/types";

export function PredictCard({
  scenario,
  as: Tag = "div",
  onClick,
}: {
  scenario: PredictionScenario;
  as?: "div" | "button";
  onClick?: () => void;
}) {
  const isNeg = scenario.mode === "neg";
  const Comp = Tag as React.ElementType;
  return (
    <Comp
      className={`predict-card ${isNeg ? "neg" : "pos"}`}
      onClick={onClick}
      type={Tag === "button" ? "button" : undefined}
    >
      <div className="icon-badge">
        <Icon name={isNeg ? "i-alert" : "i-check"} style={{ width: 18, height: 18 }} />
      </div>
      <p className="lead">{scenario.lead}</p>
      <div className="metric">
        {scenario.metricLabel} <span className="num">{scenario.metricValue}</span>
      </div>
      <div className="predict-note">{scenario.note}</div>
    </Comp>
  );
}
