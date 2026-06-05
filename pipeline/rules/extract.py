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
_MONTH_FIRST = r"[A-Z][a-z]+ \d{1,2},? \d{4}"
_DAY_FIRST = r"(?<!\d)\d{1,2} [A-Z][a-z]+ \d{4}"
_NUMERIC = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
_ISO = r"\d{4}-\d{2}-\d{2}"

_DATE_NEAR = re.compile(
    r"(?:deadline|due|closes?|apply by|applications? close|submit by)\D{0,20}"
    rf"({_MONTH_FIRST}|{_DAY_FIRST}|{_NUMERIC}|{_ISO})",
    re.I,
)
_NO_DEADLINE = re.compile(
    r"\b(rolling basis|rolling deadline|ongoing basis|no deadline|"
    r"open year[- ]round|accepted year[- ]round)\b",
    re.I,
)
_ANY_DATE = re.compile(rf"({_MONTH_FIRST}|{_DAY_FIRST}|{_ISO})")


def _parse_date(raw: str, today: date) -> str | None:
    try:
        dt = dateparser.parse(raw, fuzzy=True, default=datetime(today.year, 1, 1))
    except (ValueError, OverflowError):
        return None
    # Reject implausibly old dates. Relative to today so it never rots.
    if dt.date() >= date(today.year - 1, 1, 1):
        return dt.date().isoformat()
    return None


def extract_deadline(text: str, today: date | None = None) -> str | None:
    today = today or date.today()
    m = _DATE_NEAR.search(text)
    if m:
        d = _parse_date(m.group(1), today)
        if d:
            return d
    # If the source says rolling/ongoing, don't guess a stray date.
    if _NO_DEADLINE.search(text):
        return None
    m = _ANY_DATE.search(text)
    if m:
        return _parse_date(m.group(1), today)
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
