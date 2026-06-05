"""Classify a candidate into one of six categories via keyword scoring.
Falls back to the source's category_hint, then to 'funding'."""
from __future__ import annotations

CATEGORIES = ("ai_compute", "funding", "software", "data", "awards", "events")

_KEYWORDS = {
    "ai_compute": [
        "api credit", "free credits", "compute", "gpu", "tpu", "cloud credit",
        "openai", "anthropic", "azure", "aws", "hpc", "tokens", "ai model",
        "inference", "supercomput",
    ],
    "funding": [
        "grant", "funding", "seed fund", "research fund", "rfp",
        "call for proposals", "principal investigator", "budget",
    ],
    "software": [
        "license", "discount", "free for students", "academic plan",
        "education plan", "jetbrains", "github", "overleaf", "notion",
        "subscription",
    ],
    "data": [
        "dataset", "data access", "corpus", "benchmark", "data repository",
        "infrastructure", "data program",
    ],
    "awards": [
        "fellowship", "scholarship", "prize", "award", "stipend",
        "early career", "postdoctoral fellow",
    ],
    "events": [
        "travel grant", "conference", "registration waiver", "summer school",
        "workshop", "symposium", "attend", "travel award", "travel support",
    ],
}


def classify(candidate) -> str:
    text = f"{candidate.title} {candidate.summary} {candidate.raw_text}".lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, words in _KEYWORDS.items():
        for w in words:
            if w in text:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return candidate.category_hint or "funding"
    # Give the hint a small tie-breaking nudge.
    if candidate.category_hint and scores[candidate.category_hint] >= scores[best] - 1:
        return candidate.category_hint
    return best
