# Data Breadth & Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guard-railed data pipeline — a static `sources.yaml` validator (blocking CI gate), a non-blocking live smoke fetch, golden-fixture tests for extraction, more accurate extraction, rebalanced sources filling the empty categories, and a contributor flow.

**Architecture:** All work lands in `pipeline/` and `.github/`; `web/` is untouched. Two new standalone scripts (`validate_sources.py`, `smoke_sources.py`) reuse existing modules (`rules.classify`, `fetchers/`). A `tests/` suite (pytest) is introduced with `pipeline/` on the path. Two new workflows: `ci.yml` (blocking validate+test) and `smoke-sources.yml` (non-blocking report).

**Tech Stack:** Python 3.10+ (run locally with `py -3.14`; CI uses 3.12), pytest, PyYAML, GitHub Actions.

---

## Conventions for this plan

- **Run Python locally with `py -3.14`** (the default `python` on this machine is 3.7 and cannot run this code). CI uses `python` 3.12.
- **All commits end with the repo trailer** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Work on a branch.** Before Task 1, create it:

```bash
git switch -c feat/data-breadth-quality
```

- **Spec deviation (noted):** the spec listed `tests/fixtures/extract_cases.yaml`. This plan uses inline `pytest.mark.parametrize`/explicit test functions instead — same coverage, no YAML loader to maintain (YAGNI).

---

## File Structure

| File | Responsibility |
|---|---|
| `pytest.ini` | Put `pipeline/` on the import path; point pytest at `tests/`. |
| `requirements-dev.txt` | Dev-only deps (pytest), separate from runtime `requirements.txt`. |
| `tests/test_extract.py` | Golden tests pinning + driving `rules/extract.py`. |
| `tests/test_validate_sources.py` | Tests for the validator's `validate()` function. |
| `tests/test_smoke_sources.py` | Tests for the smoke report's pure helpers. |
| `pipeline/validate_sources.py` | Static schema validation (blocking gate). |
| `pipeline/smoke_sources.py` | Live per-source candidate counts (non-blocking). |
| `pipeline/rules/extract.py` | Heuristic extraction (improved). |
| `pipeline/sources.yaml` | Expanded to fill `data`/`awards`/`events`. |
| `.github/workflows/ci.yml` | PR/push: validate + pytest (blocking). |
| `.github/workflows/smoke-sources.yml` | Manual + sources PRs: smoke (non-blocking). |
| `.github/ISSUE_TEMPLATE/suggest-a-source.yml` | Structured "suggest a source" form. |
| `.github/pull_request_template.md` | Contributor checklist. |
| `CONTRIBUTING.md` | Add-a-source flow. |

---

## Task 1: Test harness + pin current extraction behavior

**Files:**
- Create: `pytest.ini`
- Create: `requirements-dev.txt`
- Create: `tests/test_extract.py`

- [ ] **Step 1: Create `pytest.ini`**

```ini
[pytest]
pythonpath = pipeline
testpaths = tests
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest>=8.0
```

- [ ] **Step 3: Install dev deps**

Run: `py -3.14 -m pip install -r requirements-dev.txt`
Expected: pytest installs (or "already satisfied").

- [ ] **Step 4: Write tests that pin CURRENT behavior (must pass as-is)**

Create `tests/test_extract.py`:

```python
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
def test_extract_amount_dollar(text, expected):
    assert extract_amount(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Applications close March 15, 2026.", "2026-03-15"),
    ("Apply by 2026-09-01 for funding.", "2026-09-01"),
])
def test_extract_deadline_month_first_and_iso(text, expected):
    assert extract_deadline(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Open to international applicants worldwide.", "International OK"),
    ("Must be a US citizen to apply.", "US only"),
    ("No region mentioned.", None),
])
def test_extract_region(text, expected):
    assert extract_region(text) == expected
```

- [ ] **Step 5: Run tests — all pass against current code**

Run: `py -3.14 -m pytest -q`
Expected: PASS (9 passed). This confirms the harness imports `rules.extract` via `pythonpath = pipeline`.

- [ ] **Step 6: Commit**

```bash
git add pytest.ini requirements-dev.txt tests/test_extract.py
git commit -m "test: add pytest harness pinning extract.py behavior"
```

---

## Task 2: `validate_sources.py` (static blocking gate)

**Files:**
- Create: `tests/test_validate_sources.py`
- Create: `pipeline/validate_sources.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_validate_sources.py`:

```python
import pytest

from validate_sources import validate, SOURCES
import yaml


def test_valid_minimal():
    data = {
        "curated": [{"name": "X", "url": "https://example.com", "category": "software"}],
        "reddit": [{"subreddit": "PhD", "category": None}],
    }
    assert validate(data) == []


def test_unknown_top_level_key():
    errs = validate({"nope": []})
    assert any("unknown top-level key" in e for e in errs)


def test_missing_required_field():
    errs = validate({"curated": [{"name": "X"}]})
    assert any("missing required field 'url'" in e for e in errs)


def test_bad_category():
    errs = validate({"search": [{"query": "q", "category": "bogus"}]})
    assert any("category 'bogus'" in e for e in errs)


def test_null_category_is_allowed():
    assert validate({"reddit": [{"subreddit": "PhD", "category": None}]}) == []


def test_bad_url():
    errs = validate({"rss": [{"name": "X", "url": "not a url"}]})
    assert any("not a valid http(s) URL" in e for e in errs)


def test_duplicate_url():
    data = {"curated": [
        {"name": "A", "url": "https://example.com"},
        {"name": "B", "url": "https://example.com"},
    ]}
    errs = validate(data)
    assert any("duplicate url" in e for e in errs)


def test_real_sources_file_is_valid():
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    assert validate(data) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `py -3.14 -m pytest tests/test_validate_sources.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_sources'`.

- [ ] **Step 3: Implement `pipeline/validate_sources.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.14 -m pytest tests/test_validate_sources.py -q`
Expected: PASS (8 passed). If `test_real_sources_file_is_valid` fails, the existing `sources.yaml` has a real problem — fix the file, not the test.

- [ ] **Step 5: Run the script directly as a smoke check**

Run: `py -3.14 pipeline/validate_sources.py`
Expected: prints `OK sources.yaml valid - 19 sources across 4 types`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add pipeline/validate_sources.py tests/test_validate_sources.py
git commit -m "feat: add static sources.yaml validator"
```

---

## Task 3: CI workflow (blocking validate + test)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Locally reproduce what CI will run (must be green first)**

Run: `py -3.14 pipeline/validate_sources.py; py -3.14 -m pytest -q`
Expected: validator exit 0; pytest all pass.

- [ ] **Step 2: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  validate-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Validate sources.yaml
        run: python pipeline/validate_sources.py
      - name: Run tests
        run: pytest -q
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: validate sources and run tests on PRs and pushes"
```

---

## Task 4: Extraction — refactor deadline parsing + de-rot hardcoded years

**Files:**
- Modify: `pipeline/rules/extract.py` (the deadline section, lines ~32-55)
- Modify: `tests/test_extract.py`

- [ ] **Step 1: Add the failing test + make existing deadline cases deterministic**

First, re-introduce the date import and a fixed `TODAY` at the top of
`tests/test_extract.py` (Task 1 removed the then-unused constant). Change the
top imports block to:

```python
"""Golden tests pinning current behavior of rules/extract.py — no mocks."""
from datetime import date

import pytest

from rules.extract import extract_amount, extract_deadline, extract_region

TODAY = date(2026, 6, 5)
```

Then pass `today=TODAY` to the existing month-first/iso deadline test so it
stays valid after the floor becomes relative (otherwise it rots in future
years):

```python
@pytest.mark.parametrize("text,expected", [
    ("Applications close March 15, 2026.", "2026-03-15"),
    ("Apply by 2026-09-01 for funding.", "2026-09-01"),
])
def test_extract_deadline_month_first_and_iso(text, expected):
    assert extract_deadline(text, today=TODAY) == expected
```

Finally append the new failing test:

```python
def test_deadline_floor_is_relative_to_today():
    # A date two years before "today" is stale -> None, regardless of calendar year.
    assert extract_deadline("Deadline January 1, 2031.", today=date(2035, 1, 1)) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `py -3.14 -m pytest tests/test_extract.py::test_deadline_floor_is_relative_to_today -q`
Expected: FAIL — current `extract_deadline` takes no `today` kwarg (`TypeError`), and its floor is hardcoded to 2024.

- [ ] **Step 3: Replace the deadline section in `pipeline/rules/extract.py`**

Replace everything from the `# ---- deadline` comment through the end of `extract_deadline` with:

```python
# ---- deadline -------------------------------------------------------------
_MONTH_FIRST = r"[A-Z][a-z]+ \d{1,2},? \d{4}"
_NUMERIC = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
_ISO = r"\d{4}-\d{2}-\d{2}"

_DATE_NEAR = re.compile(
    r"(?:deadline|due|closes?|apply by|applications? close|submit by)\D{0,20}"
    rf"({_MONTH_FIRST}|{_NUMERIC}|{_ISO})",
    re.I,
)
_ANY_DATE = re.compile(rf"({_MONTH_FIRST}|{_ISO})")


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
    m = _ANY_DATE.search(text)
    if m:
        return _parse_date(m.group(1), today)
    return None
```

- [ ] **Step 4: Run the full extract suite to verify pass + no regression**

Run: `py -3.14 -m pytest tests/test_extract.py -q`
Expected: PASS (all, including the new floor test and the pinned month-first/iso tests).

- [ ] **Step 5: Commit**

```bash
git add pipeline/rules/extract.py tests/test_extract.py
git commit -m "fix: make deadline floor relative to today and add today param"
```

---

## Task 5: Extraction — day-first dates ("15 March 2026")

**Files:**
- Modify: `pipeline/rules/extract.py`
- Modify: `tests/test_extract.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_extract.py`:

```python
def test_deadline_day_first():
    assert extract_deadline("Deadline: 15 March 2026.", today=date(2026, 6, 5)) == "2026-03-15"
```

- [ ] **Step 2: Run to verify it fails**

Run: `py -3.14 -m pytest tests/test_extract.py::test_deadline_day_first -q`
Expected: FAIL — current patterns only match month-first; day-first returns None.

- [ ] **Step 3: Add the day-first pattern in `pipeline/rules/extract.py`**

After the `_MONTH_FIRST = ...` line, add:

```python
_DAY_FIRST = r"\d{1,2} [A-Z][a-z]+ \d{4}"
```

Then update the two compiled patterns to include it:

```python
_DATE_NEAR = re.compile(
    r"(?:deadline|due|closes?|apply by|applications? close|submit by)\D{0,20}"
    rf"({_MONTH_FIRST}|{_DAY_FIRST}|{_NUMERIC}|{_ISO})",
    re.I,
)
_ANY_DATE = re.compile(rf"({_MONTH_FIRST}|{_DAY_FIRST}|{_ISO})")
```

- [ ] **Step 4: Run to verify pass + no regression**

Run: `py -3.14 -m pytest tests/test_extract.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add pipeline/rules/extract.py tests/test_extract.py
git commit -m "feat: extract day-first deadline dates"
```

---

## Task 6: Extraction — honor rolling / no-deadline phrasing

**Files:**
- Modify: `pipeline/rules/extract.py`
- Modify: `tests/test_extract.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_extract.py`:

```python
def test_deadline_rolling_ignores_stray_date():
    text = "Applications reviewed on a rolling basis. Program launched January 1, 2025."
    assert extract_deadline(text, today=date(2026, 6, 5)) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `py -3.14 -m pytest tests/test_extract.py::test_deadline_rolling_ignores_stray_date -q`
Expected: FAIL — `_ANY_DATE` grabs "January 1, 2025" and returns "2025-01-01".

- [ ] **Step 3: Add the no-deadline guard in `pipeline/rules/extract.py`**

After the `_ANY_DATE = ...` line, add:

```python
_NO_DEADLINE = re.compile(
    r"\b(rolling basis|rolling deadline|ongoing basis|no deadline|"
    r"open year[- ]round|accepted year[- ]round)\b",
    re.I,
)
```

Then, in `extract_deadline`, insert the guard between the `_DATE_NEAR` block and the `_ANY_DATE` block so the function reads:

```python
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
```

- [ ] **Step 4: Run to verify pass + no regression**

Run: `py -3.14 -m pytest tests/test_extract.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add pipeline/rules/extract.py tests/test_extract.py
git commit -m "feat: return no deadline for rolling/ongoing sources"
```

---

## Task 7: Extraction — euro and pound amounts

**Files:**
- Modify: `pipeline/rules/extract.py` (the amount section, lines ~10-29)
- Modify: `tests/test_extract.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_extract.py`:

```python
@pytest.mark.parametrize("text,expected", [
    ("Receive €2,500 in support.", "€2,500"),
    ("A £500 travel stipend.", "£500"),
    ("Up to €3 million for consortia.", "€3M"),
])
def test_extract_amount_currencies(text, expected):
    assert extract_amount(text) == expected
```

- [ ] **Step 2: Run to verify it fails**

Run: `py -3.14 -m pytest tests/test_extract.py::test_extract_amount_currencies -q`
Expected: FAIL — current `_AMOUNT` only matches `$`, returns None for €/£.

- [ ] **Step 3: Update the amount regex + builder in `pipeline/rules/extract.py`**

Replace the `_AMOUNT` definition and the body of `extract_amount` with:

```python
_AMOUNT = re.compile(
    r"(?:US)?([$€£])\s?([\d,]+(?:\.\d+)?)\s?(k|thousand|million|m|bn)?",
    re.I,
)
_CREDIT = re.compile(r"([\d,]+)\s*(?:in\s+)?(?:free\s+)?(?:api\s+)?credits?", re.I)


def extract_amount(text: str) -> str | None:
    m = _AMOUNT.search(text)
    if m:
        sym = m.group(1)
        num = m.group(2)
        unit = (m.group(3) or "").lower()
        suffix = {"k": "K", "thousand": "K", "million": "M",
                  "m": "M", "bn": "B"}.get(unit, "")
        return f"{sym}{num}{suffix}"
    c = _CREDIT.search(text)
    if c:
        return f"{c.group(1)} credits"
    return None
```

- [ ] **Step 4: Run the full suite (currencies + no regression on `$`)**

Run: `py -3.14 -m pytest -q`
Expected: PASS (all). Confirms `$5,000`/`$2M`/credits still work and `score._amount_points` is unaffected (it keys off digits and K/M/B/credit, which are preserved).

- [ ] **Step 5: Commit**

```bash
git add pipeline/rules/extract.py tests/test_extract.py
git commit -m "feat: extract euro and pound amounts"
```

---

## Task 8: `smoke_sources.py` (live per-source counts, non-blocking)

**Files:**
- Create: `tests/test_smoke_sources.py`
- Create: `pipeline/smoke_sources.py`

- [ ] **Step 1: Write failing tests for the pure helpers**

Create `tests/test_smoke_sources.py`:

```python
from smoke_sources import _label, render


def test_label_prefers_name():
    assert _label("curated", {"name": "Foo", "url": "https://x"}) == "Foo"


def test_label_falls_back_to_query_then_subreddit():
    assert _label("search", {"query": "free credits"}) == "free credits"
    assert _label("reddit", {"subreddit": "PhD"}) == "PhD"


def test_render_has_table_and_totals():
    out = render([("curated", "Foo", 3), ("reddit", "PhD", 0)])
    assert "| type | source | candidates |" in out
    assert "| curated | Foo | 3 |" in out
    assert "Total candidates: 3" in out
    assert "producing 0: 1" in out
```

- [ ] **Step 2: Run to verify it fails**

Run: `py -3.14 -m pytest tests/test_smoke_sources.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'smoke_sources'`.

- [ ] **Step 3: Implement `pipeline/smoke_sources.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.14 -m pytest tests/test_smoke_sources.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Run the script live (sanity, network)**

Run: `py -3.14 pipeline/smoke_sources.py`
Expected: a markdown table of every source and its candidate count, then a totals line. (curated/rss/reddit work without keys; search rows show 0 unless `TAVILY_API_KEY`/`BRAVE_API_KEY` are set — that is expected.)

- [ ] **Step 6: Commit**

```bash
git add pipeline/smoke_sources.py tests/test_smoke_sources.py
git commit -m "feat: add non-blocking smoke fetch report for sources"
```

---

## Task 9: Smoke workflow (manual + sources PRs, non-blocking)

**Files:**
- Create: `.github/workflows/smoke-sources.yml`

- [ ] **Step 1: Create `.github/workflows/smoke-sources.yml`**

```yaml
name: Smoke sources

on:
  workflow_dispatch: {}
  pull_request:
    paths:
      - "pipeline/sources.yaml"

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install runtime deps
        run: pip install -r requirements.txt
      - name: Smoke fetch all sources (non-blocking)
        continue-on-error: true
        env:
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
          BRAVE_API_KEY: ${{ secrets.BRAVE_API_KEY }}
        run: python pipeline/smoke_sources.py
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/smoke-sources.yml
git commit -m "ci: add non-blocking smoke-sources workflow"
```

---

## Task 10: Expand & rebalance sources (fill data / awards / events)

This task is verification-driven: add candidate sources, then keep only those that validate and actually produce candidates of the intended category. The empty categories are `data`, `awards`, `events` (current `by_category`: ai_compute 16, software 4, funding 3, the rest 0).

**Files:**
- Modify: `pipeline/sources.yaml`

- [ ] **Step 1: Add candidate sources to `pipeline/sources.yaml`**

Under the existing `search:` list, add (rot-resistant queries, one+ per empty category):

```yaml
  - query: "research data repository access program for academics 2026"
    category: data
  - query: "open dataset access grant researchers 2026"
    category: data
  - query: "early career researcher award nomination 2026"
    category: awards
  - query: "summer school scholarship PhD students 2026"
    category: events
  - query: "conference travel grant application researchers 2026"
    category: events
```

Under the existing `curated:` list, add (key-independent, so the empty categories can fill even without search keys):

```yaml
  - name: "Schmidt Science Fellows"
    url: "https://schmidtsciencefellows.org/fellowship/"
    category: awards
  - name: "AWS Registry of Open Data"
    url: "https://registry.opendata.aws/"
    category: data
```

- [ ] **Step 2: Validate the edited file (blocking gate must pass)**

Run: `py -3.14 pipeline/validate_sources.py`
Expected: `OK sources.yaml valid - 26 sources across 4 types`, exit 0. If it fails, fix the YAML.

- [ ] **Step 3: Smoke the new sources (which actually produce candidates?)**

Run: `py -3.14 pipeline/smoke_sources.py`
Expected: a table. Note which of the newly added curated rows produce ≥1 candidate. (Search rows need keys; if you have `TAVILY_API_KEY`/`BRAVE_API_KEY`, export them first to verify the search additions too.)

- [ ] **Step 4: Run the full pipeline and check category balance**

Run: `cd pipeline; py -3.14 main.py; cd ..`
Expected: console prints `by_category`-style output ending in `wrote N perks`. Then inspect:

Run: `py -3.14 -c "import json; d=json.load(open('data/perks.json',encoding='utf-8')); print(d['by_category'])"`
Expected: `data`, `awards`, and `events` are each **> 0**.

- [ ] **Step 5: Prune dead weight**

For any newly added source that produced **0** candidates across Steps 3–4 (e.g. a curated page that is bot-blocked or JS-only and yields nothing), remove it from `sources.yaml`. Keep only sources that demonstrably contribute. Re-run Steps 2 and 4 after pruning.

> If a category is still 0 after pruning because its only contributors are search queries and no API keys are available locally, that is acceptable: note it in the commit message and rely on the CI smoke run (which has keys) to confirm. The hard local requirement is that **at least the key-independent curated additions validate and the pipeline still runs clean**.

- [ ] **Step 6: Commit**

```bash
git add pipeline/sources.yaml data/perks.json data/history/
git commit -m "feat: add sources to fill data/awards/events categories"
```

---

## Task 11: Contribution mechanism

**Files:**
- Create: `.github/ISSUE_TEMPLATE/suggest-a-source.yml`
- Create: `.github/pull_request_template.md`
- Create: `CONTRIBUTING.md`
- Modify: `pipeline/sources.yaml` (header comment)

- [ ] **Step 1: Create `.github/ISSUE_TEMPLATE/suggest-a-source.yml`**

```yaml
name: Suggest a source
description: Propose a new data source for the radar
title: "[source] <name of the program / feed>"
labels: ["source-suggestion"]
body:
  - type: dropdown
    id: type
    attributes:
      label: Source type
      options: [curated, rss, search, reddit]
    validations:
      required: true
  - type: input
    id: value
    attributes:
      label: URL / query / subreddit
      description: A URL (curated/rss), a search query, or a subreddit name.
    validations:
      required: true
  - type: dropdown
    id: category
    attributes:
      label: Category
      options: [ai_compute, funding, software, data, awards, events]
    validations:
      required: true
  - type: textarea
    id: why
    attributes:
      label: Why is this relevant to researchers?
      description: One or two sentences. On-topic perks only (no general ads/admissions).
    validations:
      required: true
```

- [ ] **Step 2: Create `.github/pull_request_template.md`**

```markdown
## What this changes

<!-- brief description -->

## Source PRs checklist

- [ ] Ran `python pipeline/validate_sources.py` — passes
- [ ] Ran `python pipeline/smoke_sources.py` — the new source produces candidates
- [ ] The source is on-topic (a research perk: credits / funding / software / data / awards / events)
- [ ] `category` is one of: ai_compute, funding, software, data, awards, events
```

- [ ] **Step 3: Create `CONTRIBUTING.md`**

```markdown
# Contributing

The easiest way to help is to add a data source.

## Add a source

1. Edit `pipeline/sources.yaml`. Pick the right list:
   - `curated` — a specific page to scrape (`name`, `url`, optional `category`)
   - `rss` — an RSS/Atom feed (`name`, `url`, optional `category`)
   - `search` — a query for the free search APIs (`query`, optional `category`)
   - `reddit` — a subreddit scanned via its public JSON (`subreddit`, optional `category`)
2. `category`, if set, must be one of: `ai_compute`, `funding`, `software`,
   `data`, `awards`, `events`.
3. Validate it (no network, must pass — this is the CI gate):

   ```bash
   python pipeline/validate_sources.py
   ```

4. Optionally smoke-test that it actually returns something:

   ```bash
   python pipeline/smoke_sources.py
   ```

5. Open a PR. CI runs the validator and the tests; a non-blocking smoke job
   reports how many candidates each source produced.

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Keep sources on-topic: real research perks only.
```

- [ ] **Step 4: Update the header comment in `pipeline/sources.yaml`**

After the existing `# category ...` comment block (before the `curated:` line), add:

```yaml
# Validate your edits before opening a PR (no network, this is the CI gate):
#     python validate_sources.py
# Optionally check a source actually returns candidates:
#     python smoke_sources.py
```

- [ ] **Step 5: Validate the file still passes**

Run: `py -3.14 pipeline/validate_sources.py`
Expected: exit 0 (comment-only change).

- [ ] **Step 6: Commit**

```bash
git add .github/ISSUE_TEMPLATE/suggest-a-source.yml .github/pull_request_template.md CONTRIBUTING.md pipeline/sources.yaml
git commit -m "docs: add contribution templates and validator guidance"
```

---

## Final verification

- [ ] **Run the whole gate locally**

Run: `py -3.14 pipeline/validate_sources.py; py -3.14 -m pytest -q`
Expected: validator exit 0; all tests pass.

- [ ] **Confirm the site still consumes the refreshed data** (no `web/` code changed, but data did)

Run: `Copy-Item data/perks.json web/public/perks.json -Force`
Then (if the dev server is running) reload `http://localhost:3000` and confirm perks render, including newly filled categories.

---

## Spec coverage check

- Component A (validator, blocking, static) → Task 2 + Task 3.
- Component B (smoke, all sources, non-blocking) → Task 8 + Task 9.
- Component C (extraction, test-driven: de-rot years, day-first, currencies, rolling) → Tasks 4–7.
- Component D (fill data/awards/events behind the guard-rails) → Task 10.
- Component E (issue/PR templates, CONTRIBUTING, sources.yaml header) → Task 11.
- Success criteria (blocking gate, green tests, empty categories > 0, contributor flow) → Final verification + Tasks 10/11.
