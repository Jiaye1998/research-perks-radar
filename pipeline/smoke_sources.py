"""Live smoke test for sources.yaml: run each fetcher and report how many
candidates it produced. Informational only - never a gate.

Run:
    python smoke_sources.py            # from pipeline/
    python pipeline/smoke_sources.py   # from repo root
Prints a markdown table; also appends it to $GITHUB_STEP_SUMMARY when set.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

from fetchers.curated import fetch_curated
from fetchers.rss import fetch_rss
from fetchers.search import fetch_search
from fetchers.reddit import fetch_reddit

SOURCES = Path(__file__).resolve().parent / "sources.yaml"

FETCHERS = {
    "curated": fetch_curated,
    "rss": fetch_rss,
    "search": fetch_search,
    "reddit": fetch_reddit,
}


def _label(stype: str, entry: dict) -> str:
    return (entry.get("name") or entry.get("query") or entry.get("subreddit")
            or entry.get("url") or "?")


def smoke(data: dict) -> list[tuple[str, str, int]]:
    rows: list[tuple[str, str, int]] = []
    for stype, fetch in FETCHERS.items():
        for entry in data.get(stype) or []:
            label = _label(stype, entry)
            try:
                rows.append((stype, label, len(fetch([entry]))))
            except Exception as exc:  # informational: one bad source never crashes the run
                rows.append((stype, f"{label} (error: {exc})", 0))
    return rows


def render(rows: list[tuple[str, str, int]]) -> str:
    lines = ["| type | source | candidates |", "|---|---|---|"]
    for stype, label, n in rows:
        lines.append(f"| {stype} | {label} | {n} |")
    total = sum(n for _, _, n in rows)
    zeros = sum(1 for _, _, n in rows if n == 0)
    lines.append(f"\n**Total candidates: {total}** - sources producing 0: {zeros}")
    return "\n".join(lines)


def main() -> int:
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    table = render(smoke(data))
    print(table)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(table + "\n")
    return 0  # always success - non-blocking by design


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
