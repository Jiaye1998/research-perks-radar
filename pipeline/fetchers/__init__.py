"""Fetchers turn data sources into raw `Candidate` records.

Each fetcher is intentionally dumb: it only collects (title, url, summary,
source, category_hint). All quality control lives in pipeline/rules/.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests

USER_AGENT = (
    "research-perks-radar/1.0 (+https://github.com/your-user/research-perks-radar)"
)
DEFAULT_TIMEOUT = 20


@dataclass
class Candidate:
    title: str
    url: str
    summary: str = ""
    source: str = ""          # human-readable origin, e.g. "RSS: NSF"
    category_hint: Optional[str] = None
    raw_text: str = ""        # any extra text the rule engine can mine

    def to_dict(self) -> dict:
        return asdict(self)


def http_get(url: str, params: dict | None = None,
             headers: dict | None = None, timeout: int = DEFAULT_TIMEOUT):
    """GET with a polite UA and basic retry. Returns Response or None."""
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 503):
                time.sleep(2 * (attempt + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(1 + attempt)
    return None
