"""Filter out noise: ads, admissions spam, dead links, off-topic posts.
Returns True if the candidate should be KEPT."""
from __future__ import annotations

_BLACKLIST = (
    "casino", "betting", "porn", "viagra", "crypto airdrop", "forex",
    "buy followers", "essay writing service", "write my essay",
    "term paper", "dissertation help", "coupon code", "promo code deal",
)

# A candidate must show at least one of these to be considered a real perk.
_WHITELIST = (
    "research", "researcher", "academic", "phd", "postdoc", "faculty",
    "grant", "fund", "fellowship", "scholarship", "credit", "free",
    "award", "stipend", "apply", "eligib", "compute", "dataset",
    "university", "lab", "scientist", "student",
)


def keep(candidate, category: str) -> bool:
    text = f"{candidate.title} {candidate.summary} {candidate.raw_text}".lower()

    if not candidate.url or not candidate.url.startswith("http"):
        return False
    if len(candidate.title.strip()) < 6:
        return False
    if any(b in text for b in _BLACKLIST):
        return False
    if not any(w in text for w in _WHITELIST):
        return False
    return True
