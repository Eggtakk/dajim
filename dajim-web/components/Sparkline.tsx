const CSS_COLOR: Record<string, string> = {
  ink: "var(--ink)",
  brand: "var(--brand)",
};

export function Sparkline({
  values,
  color,
}: {
  values: number[];
  color: "ink" | "brand";
}) {
  const w = 520;
  const h = 90;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const yOf = (v: number) => h - ((v - min) / (max - min || 1)) * (h - 14) - 7;
  const points = values
    .map((v, i) => `${(i / (values.length - 1)) * w},${yOf(v)}`)
    .join(" ");
  const lastYPct = (yOf(values[values.length - 1]) / h) * 100;
  const stroke = CSS_COLOR[color];

  return (
    <div style={{ position: "relative", width: "100%", height: 90 }}>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
        style={{ width: "100%", height: 90, display: "block" }}
      >
        <polyline
          points={points}
          fill="none"
          stroke={stroke}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <span
        style={{
          position: "absolute",
          right: 0,
          top: `${lastYPct}%`,
          transform: "translate(50%, -50%)",
          width: 9,
          height: 9,
          borderRadius: "50%",
          background: stroke,
        }}
      />
    </div>
  );
}

export function DualSparkline({
  goalSeries,
  actualSeries,
}: {
  goalSeries: number[];
  actualSeries: number[];
}) {
  const w = 520;
  const h = 100;
  const max = 100;
  const min = 45;
  const toPoints = (arr: number[]) =>
    arr
      .map((v, i) => {
        const x = (i / (arr.length - 1)) * w;
        const y = h - ((v - min) / (max - min)) * (h - 14) - 7;
        return `${x},${y}`;
      })
      .join(" ");

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height: 100, display: "block" }}
    >
      <polyline
        points={toPoints(goalSeries)}
        fill="none"
        stroke="var(--line-strong)"
        strokeWidth={2}
        strokeDasharray="5 5"
        vectorEffect="non-scaling-stroke"
      />
      <polyline
        points={toPoints(actualSeries)}
        fill="none"
        stroke="var(--brand)"
        strokeWidth={2.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
