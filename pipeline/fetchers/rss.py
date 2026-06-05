"""RSS/Atom fetcher."""
from __future__ import annotations

import feedparser

from . import Candidate, USER_AGENT


def fetch_rss(entries: list[dict], max_per_feed: int = 40) -> list[Candidate]:
    out: list[Candidate] = []
    for e in entries:
        url = e["url"]
        name = e.get("name", url)
        hint = e.get("category")
        feed = feedparser.parse(url, agent=USER_AGENT)
        for item in feed.entries[:max_per_feed]:
            title = getattr(item, "title", "").strip()
            link = getattr(item, "link", "").strip()
            if not title or not link:
                continue
            summary = getattr(item, "summary", "") or getattr(item, "description", "")
            out.append(Candidate(
                title=title, url=link,
                summary=_strip(summary)[:1000],
                source=f"rss: {name}", category_hint=hint,
                raw_text=_strip(summary),
            ))
    return out


def _strip(html: str) -> str:
    from bs4 import BeautifulSoup
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
