"""Compute a generic 0-100 score used for default ranking (no CV).
Weights: reward value, source trust, freshness, and signal density."""
from __future__ import annotations

import re

# Domains we trust more (official programs, gov, big providers).
_TRUSTED = (
    "openai.com", "anthropic.com", "google.com", "cloud.google.com",
    "microsoft.com", "aws.amazon.com", "nsf.gov", "nih.gov", "grants.gov",
    "ec.europa.eu", "ukri.org", "github.com", "jetbrains.com",
    "overleaf.com", ".edu", ".ac.",
)

_VALUE_WORDS = ("fully funded", "full scholarship", "no cost", "free",
                "stipend", "salary", "covers travel", "all expenses")


def _amount_points(amount: str | None) -> int:
    if not amount:
        return 0
    if "M" in amount or "B" in amount:
        return 25
    m = re.search(r"([\d,]+)", amount)
    if not m:
        return 8
    n = int(m.group(1).replace(",", ""))
    if "K" in amount:
        n *= 1000
    if "credit" in amount.lower():
        return 12
    if n >= 100_000:
        return 22
    if n >= 10_000:
        return 16
    if n >= 1_000:
        return 10
    return 6


def score(candidate, fields: dict) -> int:
    pts = 30  # base
    url = candidate.url.lower()

    if any(t in url for t in _TRUSTED):
        pts += 22

    pts += _amount_points(fields.get("amount"))

    text = f"{candidate.title} {candidate.summary}".lower()
    pts += sum(4 for w in _VALUE_WORDS if w in text)

    if fields.get("deadline"):
        pts += 8   # concrete deadline = real opportunity

    if candidate.source.startswith("curated"):
        pts += 6
    elif candidate.source.startswith("rss"):
        pts += 4
    elif candidate.source.startswith("reddit"):
        pts -= 4   # noisier

    return max(0, min(100, pts))
