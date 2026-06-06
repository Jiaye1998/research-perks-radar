"""research-perks-radar pipeline orchestrator (no LLM).

Run from the pipeline/ directory:
    python main.py
Writes ../data/perks.json and a dated snapshot in ../data/history/.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

import yaml

# Ensure UTF-8 console output so status lines with ·/✓/→ don't crash on
# Windows terminals using a legacy code page (e.g. GBK/cp936).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from fetchers.curated import fetch_curated
from fetchers.rss import fetch_rss
from fetchers.search import fetch_search
from fetchers.reddit import fetch_reddit
from dedup import dedup
from rules.classify import classify, CATEGORIES
from rules.extract import extract_all
from rules.filter import keep
from rules.score import score
from rules.urgency import urgency

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HISTORY = DATA / "history"
SOURCES = Path(__file__).resolve().parent / "sources.yaml"


def load_sources() -> dict:
    with open(SOURCES, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def gather(sources: dict) -> list:
    cands = []
    if sources.get("curated"):
        print("· curated …", flush=True)
        cands += fetch_curated(sources["curated"])
    if sources.get("rss"):
        print("· rss …", flush=True)
        cands += fetch_rss(sources["rss"])
    if sources.get("search"):
        print("· search …", flush=True)
        cands += fetch_search(sources["search"])
    if sources.get("reddit"):
        print("· reddit …", flush=True)
        cands += fetch_reddit(sources["reddit"])
    print(f"  raw candidates: {len(cands)}", flush=True)
    return cands


def build_perk(candidate) -> dict | None:
    category = classify(candidate)
    if not keep(candidate, category):
        return None
    fields = extract_all(candidate)
    status, days_left = urgency(fields["deadline"])
    if status == "expired":
        return None
    sc = score(candidate, fields)
    pid = hashlib.sha1(candidate.url.encode("utf-8")).hexdigest()[:12]
    return {
        "id": pid,
        "title": candidate.title.strip()[:200],
        "category": category,
        "provider": _provider(candidate),
        "amount": fields["amount"],
        "deadline": fields["deadline"],
        "days_left": days_left,
        "status": status,
        "region_restrictions": fields["region_restrictions"],
        "url": candidate.url,
        "source": candidate.source,
        "summary": (candidate.summary or "").strip()[:400],
        "score": sc,
        "date_found": date.today().isoformat(),
    }


def _provider(candidate) -> str:
    from urllib.parse import urlparse
    netloc = urlparse(candidate.url).netloc.removeprefix("www.")
    return netloc or candidate.source


NEW_WINDOW_DAYS = 7


def load_prev_perks() -> list:
    """Perks from the previous run's perks.json (used to persist first_seen)."""
    out = DATA / "perks.json"
    if not out.exists():
        return []
    try:
        return json.loads(out.read_text(encoding="utf-8")).get("perks", [])
    except (ValueError, OSError):
        return []


def annotate_recency(perks: list, prev_perks: list, today: date,
                     window_days: int = NEW_WINDOW_DAYS) -> None:
    """Set `first_seen` (persisted across runs) and `is_new` on each perk.

    A perk is "new" if it first appeared within `window_days`. Perks that were
    already present in the previous run but carry no first_seen record (e.g. the
    first run with this field) are treated as old, so nothing is falsely flagged
    new on bootstrap."""
    prev_first = {p["id"]: p["first_seen"]
                  for p in prev_perks if p.get("first_seen")}
    prev_ids = {p["id"] for p in prev_perks}
    old_sentinel = (today - timedelta(days=window_days + 1)).isoformat()
    for p in perks:
        pid = p["id"]
        if pid in prev_first:
            first_seen = prev_first[pid]
        elif pid in prev_ids:
            first_seen = old_sentinel
        else:
            first_seen = today.isoformat()
        p["first_seen"] = first_seen
        try:
            p["is_new"] = (today - date.fromisoformat(first_seen)).days <= window_days
        except ValueError:
            p["is_new"] = False


def main() -> None:
    DATA.mkdir(exist_ok=True)
    HISTORY.mkdir(exist_ok=True)

    sources = load_sources()
    raw = gather(sources)
    raw = dedup(raw)
    print(f"  after dedup: {len(raw)}", flush=True)

    prev_perks = load_prev_perks()
    perks = []
    for c in raw:
        p = build_perk(c)
        if p:
            perks.append(p)

    annotate_recency(perks, prev_perks, date.today())

    perks.sort(key=lambda p: (
        0 if p["status"] == "closing_soon" else 1,
        -p["score"],
    ))

    by_cat = {cat: sum(1 for p in perks if p["category"] == cat)
              for cat in CATEGORIES}

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(perks),
        "by_category": by_cat,
        "perks": perks,
    }

    out = DATA / "perks.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    snap = HISTORY / f"{date.today().isoformat()}.json"
    snap.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print(f"✓ wrote {len(perks)} perks → {out}", flush=True)
    _update_readme_counts(len(perks), by_cat)


def _update_readme_counts(total: int, by_cat: dict) -> None:
    """Best-effort: inject a counts line between markers in README."""
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    marker_a, marker_b = "<!--STATS-->", "<!--/STATS-->"
    text = readme.read_text(encoding="utf-8")
    if marker_a not in text or marker_b not in text:
        return
    line = (f"\n**{total} live perks** · " +
            " · ".join(f"{k}: {v}" for k, v in by_cat.items()) +
            f" · updated {date.today().isoformat()}\n")
    pre = text.split(marker_a)[0]
    post = text.split(marker_b)[1]
    readme.write_text(f"{pre}{marker_a}{line}{marker_b}{post}", encoding="utf-8")


if __name__ == "__main__":
    main()
