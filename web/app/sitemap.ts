import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

// Static export: emits out/sitemap.xml at build time.
export const dynamic = "force-static";

const CATEGORIES = [
  "ai_compute",
  "funding",
  "software",
  "data",
  "awards",
  "events",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    {
      url: SITE_URL,
      lastModified: now,
      changeFrequency: "daily",
      priority: 1,
    },
    ...CATEGORIES.map((c) => ({
      url: `${SITE_URL}category/${c}/`,
      lastModified: now,
      changeFrequency: "daily" as const,
      priority: 0.7,
    })),
  ];
}
