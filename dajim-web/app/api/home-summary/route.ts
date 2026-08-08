import { NextResponse } from "next/server";
import { getHomeSummary } from "@/lib/mockData";

export async function GET() {
  return NextResponse.json(getHomeSummary());
}
