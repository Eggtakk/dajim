"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "./icons/Icon";
import { getUser } from "@/lib/mockData";
import { NAV_ITEMS } from "@/lib/nav";

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const user = getUser();
  const initials = user.name.slice(1);

  // Close the drawer when navigation happens, adjusted during render
  // (not an effect) per https://react.dev/learn/you-might-not-need-an-effect
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setOpen(false);
  }

  // Prevent background scroll while the drawer is open.
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="mobile-topbar">
        <span className="brand">다짐</span>
        <button
          type="button"
          className="profile-btn"
          aria-label="프로필 열기"
          aria-expanded={open}
          onClick={() => setOpen(true)}
        >
          {initials}
        </button>
      </header>

      <nav className="mobile-tabbar" aria-label="주요 메뉴">
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
      </nav>

      <div
        className={`mobile-drawer-backdrop ${open ? "open" : ""}`}
        onClick={() => setOpen(false)}
        inert={!open}
      />
      <aside
        className={`mobile-drawer ${open ? "open" : ""}`}
        inert={!open}
        aria-label="프로필"
      >
        <div className="mobile-drawer-head">
          <div className="rail-brand">
            다짐
            <small>DAJIM · 소비 습관 코칭</small>
          </div>
          <button
            type="button"
            className="drawer-close"
            aria-label="닫기"
            onClick={() => setOpen(false)}
          >
            ×
          </button>
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
        <div className="rail-foot" style={{ marginTop: "auto" }}>
          연결 계좌 2개
          <br />
          카카오뱅크 · 신한카드
        </div>
      </aside>
    </>
  );
}
