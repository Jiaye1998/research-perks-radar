import PerksExplorer from "@/components/PerksExplorer";
import { loadFeed } from "@/lib/feed";

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
