import type { Transaction as PlaidTransaction, AccountBase } from "plaid";
import type { RawTransaction } from "./types";

/** Rough USD -> KRW rate, only for making Sandbox test amounts look plausible. */
const USD_TO_KRW = 1350;

const dayFormatter = new Intl.DateTimeFormat("ko-KR", {
  month: "long",
  day: "numeric",
  weekday: "long",
});
const timeFormatter = new Intl.DateTimeFormat("ko-KR", {
  hour: "numeric",
  minute: "2-digit",
  hour12: true,
});

export function mapPlaidTransaction(
  tx: PlaidTransaction,
  accountsById: Map<string, AccountBase>,
): RawTransaction {
  const account = accountsById.get(tx.account_id);
  const merchant = tx.merchant_name ?? tx.name;
  const day = dayFormatter.format(new Date(`${tx.date}T00:00:00`));
  const time = tx.datetime ? timeFormatter.format(new Date(tx.datetime)) : "";
  const amountWon = Math.round((tx.amount * USD_TO_KRW) / 10) * 10;

  return {
    id: tx.transaction_id,
    merchant,
    day,
    time,
    account: account?.name ?? "연결된 계좌",
    amountWon,
  };
}
