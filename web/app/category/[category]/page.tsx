import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { loadFeed } from "@/lib/feed";
import { Category, CATEGORY_META } from "@/lib/types";
import StaticPerkCard from "@/components/StaticPerkCard";
import { SITE_URL, SITE_NAME } from "@/lib/site";

const CATEGORIES: Category[] = [
  "ai_compute",
  "funding",
  "software",
  "data",
  "awards",
  "events",
];

export const dynamic = "force-static";

export function generateStaticParams() {
  return CATEGORIES.map((category) => ({ category }));
}

export function generateMetadata({
  params,
}: {
  params: { category: string };
}): Metadata {
  const meta = CATEGORY_META[params.category as Category];
  if (!meta) return {};
  const title = `${meta.label} for researchers — ${SITE_NAME}`;
  const description = `Free ${meta.label.toLowerCase()} perks for researchers — scanned daily, scored automatically, and matched to your CV.`;
  const url = `${SITE_URL}category/${params.category}/`;
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      type: "website",
      url,
      siteName: SITE_NAME,
      title,
      description,
    },
  };
}

export default function CategoryPage({
  params,
}: {
  params: { category: string };
}) {
  const cat = params.category as Category;
  const meta = CATEGORY_META[cat];
  if (!meta) notFound();

  const feed = loadFeed();
  const perks = feed.perks
    .filter((p) => p.category === cat)
    .sort((a, b) => b.score - a.score);

  return (
    <>
      <header className="header">
        <div className="wrap header-inner">
          <Link href="/" className="logo">
            <span className="dot" />
            Research Perks Radar
          </Link>
          <Link href="/" className="updated">
            ← All perks
          </Link>
        </div>
      </header>

      <main className="wrap">
        <section className="hero">
          <h1>
            {meta.icon} {meta.label}
          </h1>
          <p>
            {perks.length} {meta.label.toLowerCase()} perk
            {perks.length === 1 ? "" : "s"} for researchers — scanned
            automatically every day and scored.
          </p>
        </section>

        <nav className="filters" aria-label="Browse categories">
          <Link href="/" className="pill">
            All
          </Link>
          {CATEGORIES.map((c) => (
            <Link
              key={c}
              href={`/category/${c}/`}
              className={`pill ${c === cat ? "active" : ""}`}
            >
              {CATEGORY_META[c].label}
            </Link>
          ))}
        </nav>

        <div className="grid">
          {perks.map((p) => (
            <StaticPerkCard key={p.id} perk={p} />
          ))}
        </div>
        {perks.length === 0 && (
          <p style={{ color: "var(--ink-3)", paddingBottom: 80 }}>
            No {meta.label.toLowerCase()} perks right now — check back after the
            next daily run.
          </p>
        )}
      </main>

      <footer className="footer">
        <div className="wrap">
          Open source · zero servers · updated daily by GitHub Actions.
          <br />
          Always verify eligibility and deadlines on the official page before
          applying.
        </div>
      </footer>
    </>
  );
}
