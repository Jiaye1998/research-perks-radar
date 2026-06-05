"""Deduplicate candidates by normalized URL and fuzzy title fingerprint."""
from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

_TRACKING = re.compile(r"^(utm_|fbclid|gclid|ref|source$)", re.I)


def normalize_url(url: str) -> str:
    try:
        p = urlparse(url.strip())
    except Exception:
        return url.strip().lower()
    netloc = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/") or "/"
    # drop tracking query params
    q = "&".join(
        kv for kv in p.query.split("&")
        if kv and not _TRACKING.match(kv.split("=")[0])
    )
    return urlunparse((p.scheme or "https", netloc, path, "", q, ""))


def title_fingerprint(title: str) -> str:
    t = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    words = [w for w in t.split() if len(w) > 2]
    return " ".join(sorted(set(words))[:12])


def dedup(candidates: list) -> list:
    seen_urls: set[str] = set()
    seen_fps: set[str] = set()
    out = []
    for c in candidates:
        nu = normalize_url(c.url)
        fp = title_fingerprint(c.title)
        if nu in seen_urls or (fp and fp in seen_fps):
            continue
        seen_urls.add(nu)
        if fp:
            seen_fps.add(fp)
        c.url = nu if nu.startswith("http") else c.url
        out.append(c)
    return out
