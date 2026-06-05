"""Reddit fetcher using public .json endpoints (no auth required).

Scans new + hot posts of each subreddit and keeps ones whose title looks
perk-related. The rule engine does the final filtering."""
from __future__ import annotations

from . import Candidate, http_get

_PERK_HINTS = (
    "funding", "grant", "fellowship", "scholarship", "free", "credit",
    "award", "stipend", "travel", "deadline", "apply", "opportunity",
)


def fetch_reddit(entries: list[dict], limit: int = 40) -> list[Candidate]:
    out: list[Candidate] = []
    for e in entries:
        sub = e["subreddit"]
        hint = e.get("category")
        for listing in ("new", "hot"):
            url = f"https://www.reddit.com/r/{sub}/{listing}.json"
            r = http_get(url, params={"limit": limit})
            if r is None:
                continue
            try:
                children = r.json().get("data", {}).get("children", [])
            except Exception:
                continue
            for c in children:
                d = c.get("data", {})
                title = (d.get("title") or "").strip()
                if not title:
                    continue
                low = title.lower()
                if not any(h in low for h in _PERK_HINTS):
                    continue
                permalink = d.get("permalink", "")
                link = d.get("url_overridden_by_dest") or (
                    f"https://www.reddit.com{permalink}" if permalink else "")
                if not link:
                    continue
                out.append(Candidate(
                    title=title, url=link,
                    summary=(d.get("selftext") or "")[:800],
                    source=f"reddit: r/{sub}", category_hint=hint,
                    raw_text=(d.get("selftext") or "")[:2000],
                ))
    return out
