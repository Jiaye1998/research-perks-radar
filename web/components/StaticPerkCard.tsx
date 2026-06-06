import { Perk, CATEGORY_META } from "@/lib/types";

// A non-interactive card for statically-rendered pages (e.g. category pages).
// No bookmark/calendar actions, so it stays a pure server component.
export default function StaticPerkCard({ perk }: { perk: Perk }) {
  const meta = CATEGORY_META[perk.category];
  return (
    <a
      className="card"
      href={perk.url}
      target="_blank"
      rel="noopener noreferrer"
    >
      <span className="cat" style={{ color: meta.accent }}>
        <span aria-hidden>{meta.icon}</span>
        {meta.label}
      </span>
      <h4>{perk.title}</h4>
      {perk.summary && <p className="desc">{perk.summary}</p>}

      <div className="meta-row">
        {perk.is_new && <span className="tag new">🆕 New</span>}
        {perk.status === "closing_soon" && perk.days_left != null && (
          <span className="tag soon">
            ⏰ {perk.days_left === 0 ? "today" : `${perk.days_left}d left`}
          </span>
        )}
        {perk.amount && <span className="tag">💰 {perk.amount}</span>}
        {perk.deadline && perk.status !== "closing_soon" && (
          <span className="tag">📅 {perk.deadline}</span>
        )}
        {perk.region_restrictions && (
          <span className="tag">🌍 {perk.region_restrictions}</span>
        )}
      </div>

      <div className="card-foot">
        <span className="provider">{perk.provider}</span>
        <span className="go">Open →</span>
      </div>
    </a>
  );
}
