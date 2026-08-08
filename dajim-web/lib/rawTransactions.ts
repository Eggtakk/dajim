import type { RawTransaction } from "./types";

/**
 * Stands in for what an open-banking/card feed would return: just the
 * merchant name, no category. Category is assigned by the classifier
 * (lib/categorize.ts) in the /api/transactions route, not stored here.
 */
export function getRawTransactions(): RawTransaction[] {
  return [
    {
      id: "t1",
      merchant: "배달의민족",
      day: "8월 6일 목요일",
      time: "저녁 8:42",
      account: "카카오뱅크",
      amountWon: 18500,
    },
    {
      id: "t2",
      merchant: "스타벅스",
      day: "8월 6일 목요일",
      time: "오후 3:10",
      account: "신한카드",
      amountWon: 6500,
    },
    {
      id: "t3",
      merchant: "쿠팡",
      day: "8월 5일 수요일",
      time: "오전 11:20",
      account: "신한카드",
      amountWon: 34900,
    },
    {
      id: "t4",
      merchant: "요기요",
      day: "8월 5일 수요일",
      time: "저녁 7:55",
      account: "카카오뱅크",
      amountWon: 21000,
    },
    {
      id: "t5",
      merchant: "신한카드 자동이체",
      day: "8월 4일 화요일",
      time: "오전 9:00",
      account: "신한카드",
      amountWon: 13900,
    },
    {
      id: "t6",
      merchant: "GS25",
      day: "8월 4일 화요일",
      time: "오후 1:15",
      account: "신한카드",
      amountWon: 8200,
    },
  ];
}
