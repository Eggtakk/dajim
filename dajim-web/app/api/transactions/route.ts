import { NextResponse } from "next/server";
import { classifyMerchant } from "@/lib/categorize";
import { getCategory } from "@/lib/categories";
import { getRawTransactions } from "@/lib/rawTransactions";
import type { Account, Transaction } from "@/lib/types";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const account = searchParams.get("account") as Account | null;

  const transactions: Transaction[] = getRawTransactions().map((raw) => {
    const { categoryId } = classifyMerchant(raw.merchant);
    return { ...raw, categoryId, icon: getCategory(categoryId).icon };
  });

  const filtered = account
    ? transactions.filter((t) => t.account === account)
    : transactions;

  return NextResponse.json({ transactions: filtered });
}
