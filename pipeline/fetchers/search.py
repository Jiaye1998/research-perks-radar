"""Search fetcher: queries free search APIs (Tavily + Brave).

Both are optional. If a key is missing that provider is skipped. If neither
key is present, this fetcher returns nothing and the pipeline still works off
curated + RSS + reddit sources.
"""
from __future__ import annotations

import os

from . import Candidate, http_get

TAVILY_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_KEY = os.getenv("BRAVE_API_KEY")


def fetch_search(entries: list[dict], per_query: int = 8) -> list[Candidate]:
    out: list[Candidate] = []
    # Alternate providers across queries so we spread the free quota.
    use_tavily = bool(TAVILY_KEY)
    for i, e in enumerate(entries):
        query = e["query"]
        hint = e.get("category")
        prefer_tavily = use_tavily and (i % 2 == 0 or not BRAVE_KEY)
        results = []
        if prefer_tavily:
            results = _tavily(query, per_query)
            if not results and BRAVE_KEY:
                results = _brave(query, per_query)
        else:
            results = _brave(query, per_query) if BRAVE_KEY else []
            if not results and use_tavily:
                results = _tavily(query, per_query)
        for r in results:
            out.append(Candidate(
                title=r["title"], url=r["url"], summary=r.get("summary", ""),
                source=f"search: {query[:40]}", category_hint=hint,
                raw_text=r.get("summary", ""),
            ))
    return out


def _tavily(query: str, k: int) -> list[dict]:
    try:
        resp = http_get  # placeholder to keep import; we use POST below
    except Exception:
        pass
    import requests
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": query,
                  "max_results": k, "search_depth": "basic"},
            timeout=25,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return [{"title": x.get("title", ""), "url": x.get("url", ""),
                 "summary": x.get("content", "")}
                for x in data.get("results", []) if x.get("url")]
    except Exception:
        return []


def _brave(query: str, k: int) -> list[dict]:
    r = http_get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": k},
        headers={"X-Subscription-Token": BRAVE_KEY,
                 "Accept": "application/json"},
    )
    if r is None:
        return []
    try:
        data = r.json()
        items = data.get("web", {}).get("results", [])
        return [{"title": x.get("title", ""), "url": x.get("url", ""),
                 "summary": x.get("description", "")}
                for x in items if x.get("url")]
    except Exception:
        return []
