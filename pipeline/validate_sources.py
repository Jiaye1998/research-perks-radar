"""Static validator for sources.yaml — no network calls.

Run:
    python validate_sources.py            # from pipeline/
    python pipeline/validate_sources.py   # from repo root
Exits non-zero and prints a per-error report on any problem.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

from rules.classify import CATEGORIES

SOURCES = Path(__file__).resolve().parent / "sources.yaml"

TOP_KEYS = {"curated", "rss", "search", "reddit"}
REQUIRED_FIELD = {
    "curated": "url",
    "rss": "url",
    "search": "query",
    "reddit": "subreddit",
}


def _valid_url(value: str) -> bool:
    try:
        p = urlparse(value)
    except (ValueError, AttributeError):
        return False
    return p.scheme in ("http", "https") and bool(p.netloc) and " " not in value


def validate(data: dict) -> list[str]:
    """Return a list of human-readable error strings (empty == valid)."""
    if not isinstance(data, dict):
        return ["top level must be a mapping of source-type -> list"]

    errors: list[str] = []
    for k in sorted(set(data) - TOP_KEYS):
        errors.append(f"unknown top-level key: {k!r} (allowed: {sorted(TOP_KEYS)})")

    seen: dict[str, set[str]] = {k: set() for k in TOP_KEYS}

    for stype in TOP_KEYS:
        entries = data.get(stype)
        if entries is None:
            continue
        if not isinstance(entries, list):
            errors.append(f"{stype}: expected a list, got {type(entries).__name__}")
            continue
        field = REQUIRED_FIELD[stype]
        for i, e in enumerate(entries):
            where = f"{stype}[{i}]"
            if not isinstance(e, dict):
                errors.append(f"{where}: entry must be a mapping")
                continue
            value = e.get(field)
            if not value or not isinstance(value, str):
                errors.append(f"{where}: missing required field {field!r}")
            else:
                if value in seen[stype]:
                    errors.append(f"{where}: duplicate {field} {value!r}")
                seen[stype].add(value)
                if field == "url" and not _valid_url(value):
                    errors.append(f"{where}: {value!r} is not a valid http(s) URL")
            cat = e.get("category")
            if cat is not None and cat not in CATEGORIES:
                errors.append(f"{where}: category {cat!r} not in {list(CATEGORIES)}")
    return errors


def main() -> int:
    try:
        data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        print(f"X sources.yaml is not valid YAML: {exc}")
        return 1
    errors = validate(data)
    if errors:
        print(f"X {len(errors)} problem(s) in sources.yaml:")
        for e in errors:
            print(f"  - {e}")
        return 1
    total = sum(len(data.get(k) or []) for k in TOP_KEYS)
    types = len([k for k in TOP_KEYS if data.get(k)])
    print(f"OK sources.yaml valid - {total} sources across {types} types")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
