"use client";

import { useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { Card } from "@/components/ui/Card";
import { Chip } from "@/components/ui/Chip";
import { Pill } from "@/components/ui/Pill";
import { fetchHomeSummary, fetchTransactions } from "@/lib/api";
import { formatPct, formatWon } from "@/lib/format";
import type { HomeSummary, Transaction } from "@/lib/types";

const ALL = "전체";

export default function SpendingPage() {
  const [account, setAccount] = useState(ALL);
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[] | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;
    fetchHomeSummary().then((data) => {
      if (!cancelled) setSummary(data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchTransactions().then((res) => {
      if (!cancelled) setTransactions(res.transactions);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Account names now come from wherever the transactions originated
  // (mock data or a real Plaid Item), so the chip list is derived, not fixed.
  const accounts = useMemo(() => {
    const distinct = new Set((transactions ?? []).map((t) => t.account));
    return [ALL, ...Array.from(distinct)];
  }, [transactions]);

  const filtered = useMemo(
    () =>
      account === ALL
        ? (transactions ?? [])
        : (transactions ?? []).filter((t) => t.account === account),
    [transactions, account],
  );

  const grouped = useMemo(() => {
    const map = new Map<string, Transaction[]>();
    for (const t of filtered) {
      const list = map.get(t.day) ?? [];
      list.push(t);
      map.set(t.day, list);
    }
    return Array.from(map.entries());
  }, [filtered]);

  return (
    <>
      <div className="canvas-head">
        <div>
          <h1>나의 소비 확인</h1>
          <div className="date">토스처럼, 통장별 · 시간별로 한눈에</div>
        </div>
      </div>

      <Card
        style={{
          padding: "20px 22px",
          marginBottom: 16,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <div style={{ fontSize: 12.5, color: "var(--ink-soft)", fontWeight: 600 }}>
            이번 달 총 지출
          </div>
          <div className="value num" style={{ fontSize: 24, fontWeight: 800, marginTop: 4 }}>
            {summary ? formatWon(summary.totalSpendWon) : "—"}
          </div>
        </div>
        <Pill tone="warn">
          전월 대비 {summary ? formatPct(summary.totalSpendChangePct) : "—"}
        </Pill>
      </Card>

      <div className="chiprow" style={{ marginBottom: 8 }}>
        {accounts.map((a) => (
          <Chip key={a} selected={account === a} onClick={() => setAccount(a)}>
            {a}
          </Chip>
        ))}
      </div>

      <Card style={{ padding: "6px 20px 14px", marginTop: 10 }}>
        {transactions === null && (
          <div className="empty-note">불러오는 중…</div>
        )}
        {transactions !== null && grouped.length === 0 && (
          <div className="empty-note">해당 통장의 내역이 없어요.</div>
        )}
        {grouped.map(([day, items]) => (
          <div key={day}>
            <div className="tx-day">{day}</div>
            {items.map((t) => (
              <div className="tx-row" key={t.id}>
                <span className="tx-ic">
                  <Icon name={t.icon} />
                </span>
                <div className="tx-mid">
                  <div className="t">{t.merchant}</div>
                  <div className="d">
                    {t.time ? `${t.time} · ` : ""}
                    {t.account}
                  </div>
                </div>
                <div className="tx-amt">-{formatWon(t.amountWon)}</div>
              </div>
            ))}
          </div>
        ))}
      </Card>
    </>
  );
}
