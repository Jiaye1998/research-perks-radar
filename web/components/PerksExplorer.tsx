"use client";

import { useState, useMemo } from "react";
import { Perk, PerksFeed, Category, CATEGORY_META } from "@/lib/types";
import PerkCard from "@/components/PerkCard";
import CvPanel from "@/components/CvPanel";

const FILTERS: ("all" | Category)[] = [
  "all",
  "ai_compute",
  "funding",
  "software",
  "data",
  "awards",
  "events",
];

export default function PerksExplorer({ feed: initialFeed }: { feed: PerksFeed }) {
  // Initialized from build-time props so the first render (baked into the
  // static HTML) already contains every perk. CV matching mutates this state.
  const [feed, setFeed] = useState<PerksFeed>(initialFeed);
  const [filter, setFilter] = useState<"all" | Category>("all");
  const [q, setQ] = useState("");
  const [matched, setMatched] = useState(false);

  const perks = feed?.perks ?? [];

  function onMatched(results: { id: string; fit: number; reason: string }[]) {
    const map = new Map(results.map((r) => [r.id, r]));
    setFeed((f) =>
      f
        ? {
            ...f,
            perks: f.perks.map((p) => {
              const m = map.get(p.id);
              return m ? { ...p, fit: m.fit, fit_reason: m.reason } : { ...p, fit: undefined, fit_reason: undefined };
            }),
          }
        : f
    );
    setMatched(true);
  }

  // highlight lists
  const closingSoon = useMemo(
    () =>
      [...perks]
        .filter((p) => p.status === "closing_soon")
        .sort((a, b) => (a.days_left ?? 99) - (b.days_left ?? 99))
        .slice(0, 4),
    [perks]
  );
  const richest = useMemo(
    () => [...perks].sort((a, b) => b.score - a.score).slice(0, 4),
    [perks]
  );
  const bestFit = useMemo(
    () =>
      matched
        ? [...perks]
            .filter((p) => p.fit != null)
            .sort((a, b) => (b.fit ?? 0) - (a.fit ?? 0))
            .slice(0, 4)
        : [],
    [perks, matched]
  );

  const visible = useMemo(() => {
    let list = perks;
    if (filter !== "all") list = list.filter((p) => p.category === filter);
    if (q.trim()) {
      const s = q.toLowerCase();
      list = list.filter(
        (p) =>
          p.title.toLowerCase().includes(s) ||
          p.summary.toLowerCase().includes(s) ||
          p.provider.toLowerCase().includes(s)
      );
    }
    if (matched)
      return [...list].sort((a, b) => (b.fit ?? -1) - (a.fit ?? -1));
    return list;
  }, [perks, filter, q, matched]);

  // Fixed locale + UTC so the build-time render matches client hydration
  // (avoids a hydration mismatch from differing system locale/timezone).
  const updated = feed?.generated_at
    ? new Date(feed.generated_at).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      })
    : "—";

  return (
    <>
      <header className="header">
        <div className="wrap header-inner">
          <div className="logo">
            <span className="dot" />
            Research Perks Radar
          </div>
          <div className="updated">Updated {updated}</div>
        </div>
      </header>

      <main className="wrap">
        <section className="hero">
          <h1>Every research perk, found for you daily.</h1>
          <p>
            Free AI credits, funding, grants, software, datasets, awards and
            travel support — scanned automatically every day, scored, and
            matched to your CV right in your browser.
          </p>
        </section>

        <div className="bento">
          <BentoCard
            title="⏰ Closing soon"
            sub="Don't miss the deadline"
            items={closingSoon.map((p) => ({
              t: p.title,
              v: p.days_left === 0 ? "today" : `${p.days_left}d`,
            }))}
            empty="No imminent deadlines detected."
          />
          <BentoCard
            title="💰 Most rewarding"
            sub="Highest value & trust"
            items={richest.map((p) => ({
              t: p.title,
              v: p.amount ?? `${p.score}`,
            }))}
            empty="Loading…"
          />
          <BentoCard
            title="🎯 Best fit for you"
            sub={matched ? "Based on your CV" : "Add your CV below"}
            items={bestFit.map((p) => ({ t: p.title, v: `${p.fit}%` }))}
            empty={matched ? "No strong matches." : "Paste your CV to unlock."}
          />
        </div>

        <CvPanel perks={perks} onMatched={onMatched} />

        <div className="filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`pill ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f === "all" ? "All" : CATEGORY_META[f].label}
            </button>
          ))}
          <input
            className="search"
            placeholder="Search…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        <div className="grid">
          {visible.map((p, i) => (
            <PerkCard key={p.id} perk={p} i={i} />
          ))}
        </div>
        {visible.length === 0 && (
          <p style={{ color: "var(--ink-3)", paddingBottom: 80 }}>
            No perks match. The daily pipeline may still be warming up — check
            back after the next run.
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

function BentoCard({
  title,
  sub,
  items,
  empty,
}: {
  title: string;
  sub: string;
  items: { t: string; v: string }[];
  empty: string;
}) {
  return (
    <div className="bento-card">
      <h3>{title}</h3>
      <div className="sub">{sub}</div>
      {items.length === 0 ? (
        <div className="mini">
          <span className="t" style={{ color: "var(--ink-3)" }}>
            {empty}
          </span>
        </div>
      ) : (
        items.map((it, i) => (
          <div className="mini" key={i}>
            <span className="t">{it.t}</span>
            <span className="v">{it.v}</span>
          </div>
        ))
      )}
    </div>
  );
}
