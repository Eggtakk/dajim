"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "./icons/Icon";
import { getUser } from "@/lib/mockData";
import { NAV_ITEMS } from "@/lib/nav";

export function Sidebar() {
  const pathname = usePathname();
  const user = getUser();
  const initials = user.name.slice(1);

  return (
    <nav className="rail" aria-label="주요 메뉴">
      <div className="rail-brand">
        다짐
        <small>DAJIM · 소비 습관 코칭</small>
      </div>
      <div className="rail-user">
        <div className="avatar">{initials}</div>
        <div>
          <div className="name">{user.name}님</div>
          <div className="desc">
            {user.age}세 · 다짐 {user.streakDays}일째
          </div>
        </div>
      </div>
      <div className="rail-nav">
        {NAV_ITEMS.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={active ? "active" : ""}
              aria-current={active ? "page" : undefined}
            >
              <Icon name={item.icon} />
              {item.label}
            </Link>
          );
        })}
      </div>
      <div className="rail-foot">
        연결 계좌 2개
        <br />
        카카오뱅크 · 신한카드
      </div>
    </nav>
  );
}
