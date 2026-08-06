import type { CategoryMeta } from "./types";

export const CATEGORIES: CategoryMeta[] = [
  {
    id: "delivery",
    label: "배달음식",
    icon: "i-bag",
    lastMonthSpend: 145000,
    thisMonthSpend: 186000,
  },
  {
    id: "cafe",
    label: "카페",
    icon: "i-cup",
    lastMonthSpend: 78000,
    thisMonthSpend: 82000,
  },
  {
    id: "shopping",
    label: "쇼핑",
    icon: "i-store",
    lastMonthSpend: 216000,
    thisMonthSpend: 209000,
  },
  {
    id: "subscription",
    label: "구독서비스",
    icon: "i-card",
    lastMonthSpend: 41900,
    thisMonthSpend: 41900,
  },
];

export function getCategory(id: string): CategoryMeta {
  return CATEGORIES.find((c) => c.id === id) ?? CATEGORIES[0];
}

export const DURATION_OPTIONS = [1, 2, 3, 6];
export const TRACKING_DAY_OPTIONS = [3, 7, 14];
