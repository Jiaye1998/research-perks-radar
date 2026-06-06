"""Curated fetcher: scrape a known page and emit it (plus notable child links)
as candidates. Kept conservative — the page itself is always a candidate."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from . import Candidate, http_get

# Link text containing any of these is likely an actual opportunity.
_SIGNAL_WORDS = (
    "apply", "application", "program", "grant", "fellowship", "credit",
    "funding", "award", "scholarship", "researcher", "academic", "free",
    "eligibility", "deadline",
)

# Child links pointing at these hosts are papers/citations, not perks.
_NOISE_HOSTS = (
    "arxiv.org", "doi.org", "biorxiv.org", "medrxiv.org",
    "semanticscholar.org", "researchgate.net", "ncbi.nlm.nih.gov",
)


def _looks_like_noise(text: str, href: str) -> bool:
    """True if a scraped child link is a paper/citation rather than a perk."""
    host = urlparse(href).netloc.lower().removeprefix("www.")
    if any(host == h or host.endswith("." + h) for h in _NOISE_HOSTS):
        return True
    # Author lists / citations carry several commas; real opportunity titles rarely do.
    if text.count(",") >= 2:
        return True
    return False


def fetch_curated(entries: list[dict]) -> list[Candidate]:
    out: list[Candidate] = []
    for e in entries:
        url = e["url"]
        name = e.get("name", url)
        hint = e.get("category")
        resp = http_get(url)
        if resp is None:
            # Still emit the source itself; it may simply block bots.
            out.append(Candidate(title=name, url=url, source=f"curated: {name}",
                                  category_hint=hint))
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        page_title = (soup.title.string.strip()
                      if soup.title and soup.title.string else name)
        meta = soup.find("meta", attrs={"name": "description"})
        summary = meta["content"].strip() if meta and meta.get("content") else ""

        out.append(Candidate(title=page_title, url=url,
                             summary=summary, source=f"curated: {name}",
                             category_hint=hint,
                             raw_text=soup.get_text(" ", strip=True)[:4000]))

        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        seen = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(" ", strip=True)
            if not text or len(text) < 6:
                continue
            low = text.lower()
            if not any(w in low for w in _SIGNAL_WORDS):
                continue
            href = urljoin(base, a["href"])
            if href in seen or href == url:
                continue
            if _looks_like_noise(text, href):
                continue
            seen.add(href)
            out.append(Candidate(title=text, url=href,
                                 source=f"curated-link: {name}",
                                 category_hint=hint))
            if len(seen) >= 15:   # cap per page
                break
    return out
