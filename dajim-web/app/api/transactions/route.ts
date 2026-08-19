import { NextResponse } from "next/server";
import { classifyMerchant } from "@/lib/categorize";
import { getCategory } from "@/lib/categories";
import { getRawTransactions } from "@/lib/rawTransactions";
import { mapPlaidTransaction } from "@/lib/mapPlaidTransaction";
import { plaidClient, plaidConfigured } from "@/lib/plaidClient";
import { loadAccessToken } from "@/lib/plaidToken";
import type { RawTransaction, Transaction } from "@/lib/types";

async function loadRawTransactions(): Promise<RawTransaction[]> {
  const accessToken = plaidConfigured ? loadAccessToken() : null;
  if (!accessToken) {
    return getRawTransactions();
  }

  try {
    const response = await plaidClient.transactionsSync({
      access_token: accessToken,
    });
    const accountsById = new Map(
      response.data.accounts.map((a) => [a.account_id, a]),
    );
    return response.data.added
      .map((tx) => mapPlaidTransaction(tx, accountsById))
      .sort((a, b) => (a.day < b.day ? 1 : -1));
  } catch (error) {
    console.error(
      "Plaid transactions/sync failed, falling back to mock data",
      error,
    );
    return getRawTransactions();
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const account = searchParams.get("account");

  const raw = await loadRawTransactions();
  const transactions: Transaction[] = raw.map((t) => {
    const { categoryId } = classifyMerchant(t.merchant);
    return { ...t, categoryId, icon: getCategory(categoryId).icon };
  });

  const filtered = account
    ? transactions.filter((t) => t.account === account)
    : transactions;

  return NextResponse.json({ transactions: filtered });
}
