import { NextResponse } from "next/server";
import { getResultData } from "@/lib/mockData";
import { parseGoalParams } from "@/lib/parseGoalParams";
import type { ResultOutcome } from "@/lib/types";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const outcome = (searchParams.get("outcome") as ResultOutcome | null) ?? "win";
  const goal = parseGoalParams(searchParams);

  return NextResponse.json(getResultData(goal, outcome));
}
