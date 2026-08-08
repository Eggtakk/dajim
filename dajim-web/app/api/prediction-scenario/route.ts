import { NextResponse } from "next/server";
import { getPredictionScenario } from "@/lib/mockData";
import { parseGoalParams } from "@/lib/parseGoalParams";
import type { ScenarioMode } from "@/lib/types";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const mode = (searchParams.get("mode") as ScenarioMode | null) ?? "neg";
  const goal = parseGoalParams(searchParams);

  return NextResponse.json(getPredictionScenario(mode, goal));
}
