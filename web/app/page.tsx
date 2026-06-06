import fs from "fs";
import path from "path";
import { PerksFeed } from "@/lib/types";
import PerksExplorer from "@/components/PerksExplorer";

// Read the feed at BUILD time so every perk is baked into the static HTML
// (this is what makes the content crawlable). Falls back to an empty feed so
// the build never crashes if perks.json is missing.
function loadFeed(): PerksFeed {
  try {
    const raw = fs.readFileSync(
      path.join(process.cwd(), "public", "perks.json"),
      "utf-8"
    );
    return JSON.parse(raw) as PerksFeed;
  } catch {
    return {
      generated_at: "",
      count: 0,
      by_category: {} as PerksFeed["by_category"],
      perks: [],
    };
  }
}

export default function Page() {
  const feed = loadFeed();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Research perks",
    itemListElement: feed.perks.slice(0, 50).map((p, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: p.url,
      name: p.title,
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <PerksExplorer feed={feed} />
    </>
  );
}
