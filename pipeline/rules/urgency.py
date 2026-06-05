"""Compute status and days-left from an ISO deadline string."""
from __future__ import annotations

from datetime import date

CLOSING_SOON_DAYS = 14


def urgency(deadline_iso: str | None) -> tuple[str, int | None]:
    """Return (status, days_left). status in open|closing_soon|expired|unknown."""
    if not deadline_iso:
        return "unknown", None
    try:
        d = date.fromisoformat(deadline_iso)
    except ValueError:
        return "unknown", None
    days = (d - date.today()).days
    if days < 0:
        return "expired", days
    if days <= CLOSING_SOON_DAYS:
        return "closing_soon", days
    return "open", days
