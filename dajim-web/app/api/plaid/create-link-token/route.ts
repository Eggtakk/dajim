import { NextResponse } from "next/server";
import { CountryCode, Products } from "plaid";
import { plaidClient, plaidConfigured } from "@/lib/plaidClient";

export async function POST() {
  if (!plaidConfigured) {
    return NextResponse.json(
      {
        error:
          "PLAID_CLIENT_ID/PLAID_SECRET이 설정되지 않았어요. dajim-web/.env.local.example을 참고해서 .env.local을 만들어주세요.",
      },
      { status: 501 },
    );
  }

  try {
    const response = await plaidClient.linkTokenCreate({
      client_name: "다짐 (Dajim)",
      language: "en",
      country_codes: [CountryCode.Us],
      user: { client_user_id: "dajim-demo-user" },
      products: [Products.Transactions],
    });
    return NextResponse.json({ linkToken: response.data.link_token });
  } catch (error) {
    console.error("Plaid link token creation failed", error);
    return NextResponse.json(
      { error: "Plaid link token 생성에 실패했어요." },
      { status: 502 },
    );
  }
}
