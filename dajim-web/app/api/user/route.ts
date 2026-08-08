import { NextResponse } from "next/server";
import { getUser } from "@/lib/mockData";

export async function GET() {
  return NextResponse.json(getUser());
}
