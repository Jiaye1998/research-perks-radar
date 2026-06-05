import { Perk, CATEGORY_META } from "@/lib/types";

export default function PerkCard({ perk, i }: { perk: Perk; i: number }) {
  const meta = CATEGORY_META[perk.category];
  return (
    <a
      className="card"
      href={perk.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ animationDelay: `${Math.min(i, 12) * 0.03}s` }}
    >
      <span className="cat" style={{ color: meta.accent }}>
        <span aria-hidden>{meta.icon}</span>
        {meta.label}
      </span>
      <h4>{perk.title}</h4>
      {perk.summary && <p className="desc">{perk.summary}</p>}

      <div className="meta-row">
        {perk.fit != null && (
          <span className="tag fit">🎯 {perk.fit}% fit</span>
        )}
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

      {perk.fit_reason && (
        <p className="desc" style={{ fontStyle: "italic", flex: "none" }}>
          {perk.fit_reason}
        </p>
      )}

      <div className="card-foot">
        <span className="provider">{perk.provider}</span>
        <span className="go">Open →</span>
      </div>
    </a>
  );
}
