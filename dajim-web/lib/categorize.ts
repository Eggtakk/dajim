import type { CategoryId } from "./types";

/**
 * Rule-based merchant → category classifier.
 *
 * This is the "start with rules, upgrade to a model later" version described
 * in docs/api-and-model-plan.md (§2-1): once real open-banking transactions
 * come in with unseen merchant names, track how often `matchedKeyword` is
 * null (falling back to the default) and use those misses to grow the rule
 * table or justify training a text classifier.
 */
interface CategoryRule {
  categoryId: CategoryId;
  keywords: string[];
}

const RULES: CategoryRule[] = [
  {
    categoryId: "delivery",
    keywords: [
      "배달의민족",
      "배민",
      "요기요",
      "쿠팡이츠",
      "땡겨요",
      "배달",
    ],
  },
  {
    categoryId: "cafe",
    keywords: [
      "스타벅스",
      "이디야",
      "투썸플레이스",
      "컴포즈커피",
      "메가커피",
      "빽다방",
      "카페",
      "커피",
    ],
  },
  {
    categoryId: "subscription",
    keywords: [
      "자동이체",
      "정기결제",
      "넷플릭스",
      "유튜브",
      "멜론",
      "왓챠",
      "구독",
    ],
  },
  {
    categoryId: "shopping",
    keywords: [
      "쿠팡",
      "지마켓",
      "11번가",
      "올리브영",
      "이마트",
      "GS25",
      "CU",
      "세븐일레븐",
      "마트",
      "편의점",
    ],
  },
];

/** Used when no rule matches — shopping is the broadest, least-wrong bucket. */
const DEFAULT_CATEGORY: CategoryId = "shopping";

export interface ClassificationResult {
  categoryId: CategoryId;
  /** The keyword that matched, or null if the default fallback was used. */
  matchedKeyword: string | null;
}

export function classifyMerchant(merchantName: string): ClassificationResult {
  const name = merchantName.trim();
  for (const rule of RULES) {
    const matchedKeyword = rule.keywords.find((keyword) =>
      name.includes(keyword),
    );
    if (matchedKeyword) {
      return { categoryId: rule.categoryId, matchedKeyword };
    }
  }
  return { categoryId: DEFAULT_CATEGORY, matchedKeyword: null };
}
