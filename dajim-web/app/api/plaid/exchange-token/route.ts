import { NextResponse } from "next/server";
import { plaidClient, plaidConfigured } from "@/lib/plaidClient";
import { saveAccessToken } from "@/lib/plaidToken";

export async function POST(request: Request) {
  if (!plaidConfigured) {
    return NextResponse.json(
      { error: "Plaid가 설정되지 않았어요." },
      { status: 501 },
    );
  }

  const { publicToken } = await request.json();
  if (typeof publicToken !== "string" || !publicToken) {
    return NextResponse.json(
      { error: "publicToken이 필요해요." },
      { status: 400 },
    );
  }

  try {
    const response = await plaidClient.itemPublicTokenExchange({
      public_token: publicToken,
    });
    saveAccessToken(response.data.access_token);
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error("Plaid token exchange failed", error);
    return NextResponse.json(
      { error: "계좌 연결에 실패했어요." },
      { status: 502 },
    );
  }
}
