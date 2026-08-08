import { NextResponse } from "next/server";
import { getTrackingReport } from "@/lib/mockData";
import { parseGoalParams } from "@/lib/parseGoalParams";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const goal = parseGoalParams(searchParams);

  return NextResponse.json(getTrackingReport(goal));
}
