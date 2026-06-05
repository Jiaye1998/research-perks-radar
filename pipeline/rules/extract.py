"""Extract structured fields from candidate text using regex/heuristics.
Returns (amount, deadline_iso, region_restrictions)."""
from __future__ import annotations

import re
from datetime import datetime, date

from dateutil import parser as dateparser

# ---- amount ---------------------------------------------------------------
_AMOUNT = re.compile(
    r"(?:US)?\$\s?([\d,]+(?:\.\d+)?)\s?(k|thousand|million|m|bn)?",
    re.I,
)
_CREDIT = re.compile(r"([\d,]+)\s*(?:in\s+)?(?:free\s+)?(?:api\s+)?credits?", re.I)


def extract_amount(text: str) -> str | None:
    m = _AMOUNT.search(text)
    if m:
        num = m.group(1)
        unit = (m.group(2) or "").lower()
        suffix = {"k": "K", "thousand": "K", "million": "M",
                  "m": "M", "bn": "B"}.get(unit, "")
        return f"${num}{suffix}"
    c = _CREDIT.search(text)
    if c:
        return f"{c.group(1)} credits"
    return None


# ---- deadline -------------------------------------------------------------
_DATE_NEAR = re.compile(
    r"(?:deadline|due|closes?|apply by|applications? close|submit by)\D{0,20}"
    r"([A-Z][a-z]+ \d{1,2},? \d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})",
    re.I,
)
_ANY_DATE = re.compile(
    r"([A-Z][a-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})"
)


def extract_deadline(text: str) -> str | None:
    for rx in (_DATE_NEAR, _ANY_DATE):
        m = rx.search(text)
        if not m:
            continue
        try:
            dt = dateparser.parse(m.group(1), fuzzy=True, default=datetime(2026, 1, 1))
            # Only accept plausible future-ish deadlines.
            if dt.date() >= date(2024, 1, 1):
                return dt.date().isoformat()
        except (ValueError, OverflowError):
            continue
    return None


# ---- region ---------------------------------------------------------------
_REGION_HINTS = {
    "US only": ["u.s. citizen", "us citizen", "domestic applicants",
                "must be a us", "united states only"],
    "EU/EEA": ["eu member", "european union", "eea", "horizon europe"],
    "UK": ["uk-based", "united kingdom", "ukri"],
    "International OK": ["international applicants", "worldwide", "any nationality",
                         "open to all", "regardless of nationality"],
}


def extract_region(text: str) -> str | None:
    low = text.lower()
    for label, hints in _REGION_HINTS.items():
        if any(h in low for h in hints):
            return label
    return None


def extract_all(candidate) -> dict:
    text = f"{candidate.title}. {candidate.summary} {candidate.raw_text}"
    return {
        "amount": extract_amount(text),
        "deadline": extract_deadline(text),
        "region_restrictions": extract_region(text),
    }
