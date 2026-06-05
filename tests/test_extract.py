"""Golden tests pinning current behavior of rules/extract.py — no mocks."""
from datetime import date

import pytest

from rules.extract import extract_amount, extract_deadline, extract_region

TODAY = date(2026, 6, 5)


@pytest.mark.parametrize("text,expected", [
    ("This grant provides $5,000 to researchers.", "$5,000"),
    ("Awards up to $2 million for labs.", "$2M"),
    ("Get 5000 free API credits.", "5000 credits"),
    ("No money mentioned here.", None),
])
def test_extract_amount(text, expected):
    assert extract_amount(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Applications close March 15, 2026.", "2026-03-15"),
    ("Apply by 2026-09-01 for funding.", "2026-09-01"),
])
def test_extract_deadline_month_first_and_iso(text, expected):
    assert extract_deadline(text, today=TODAY) == expected


@pytest.mark.parametrize("text,expected", [
    ("Open to international applicants worldwide.", "International OK"),
    ("Must be a US citizen to apply.", "US only"),
    ("No region mentioned.", None),
])
def test_extract_region(text, expected):
    assert extract_region(text) == expected


def test_deadline_floor_is_relative_to_today():
    # A date two years before "today" is stale -> None, regardless of calendar year.
    assert extract_deadline("Deadline January 1, 2031.", today=date(2035, 1, 1)) is None
