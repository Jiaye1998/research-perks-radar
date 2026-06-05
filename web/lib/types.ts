export type Category =
  | "ai_compute"
  | "funding"
  | "software"
  | "data"
  | "awards"
  | "events";

export interface Perk {
  id: string;
  title: string;
  category: Category;
  provider: string;
  amount: string | null;
  deadline: string | null;
  days_left: number | null;
  status: "open" | "closing_soon" | "expired" | "unknown";
  region_restrictions: string | null;
  url: string;
  source: string;
  summary: string;
  score: number;
  date_found: string;
  // added client-side after CV matching:
  fit?: number;
  fit_reason?: string;
}

export interface PerksFeed {
  generated_at: string;
  count: number;
  by_category: Record<Category, number>;
  perks: Perk[];
}

export const CATEGORY_META: Record<
  Category,
  { label: string; icon: string; accent: string }
> = {
  ai_compute: { label: "AI & Compute", icon: "◈", accent: "var(--c-ai)" },
  funding: { label: "Funding", icon: "◆", accent: "var(--c-fund)" },
  software: { label: "Software", icon: "▣", accent: "var(--c-soft)" },
  data: { label: "Data", icon: "▤", accent: "var(--c-data)" },
  awards: { label: "Awards", icon: "✦", accent: "var(--c-award)" },
  events: { label: "Events", icon: "❖", accent: "var(--c-event)" },
};
