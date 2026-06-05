# Data Breadth & Quality — Design

**Date:** 2026-06-05
**Status:** Approved (pending written-spec review)
**Scope:** `pipeline/` and `.github/` only. The `web/` site is untouched.

## Goals

Two goals, both served by this single track:

1. **More GitHub attention.** A clear, low-friction, guard-railed contribution
   flow turns visitors into PR authors; trustworthy data makes the project worth
   starring and sharing.
2. **More practical / more functional, in-scope.** Better source coverage and
   more accurate extraction make the radar genuinely more useful — strictly
   within the "research perks" remit, no unrelated scope creep.

## Non-Goals

- No changes to the Next.js site, CV matching, or styling.
- No LLM anywhere in the pipeline — it stays a pure rule engine.
- No paid services; everything runs on free tiers / public endpoints.
- No new perk *categories* — the six categories are fixed.

## Constraints (inherited from the project)

- Zero-server, zero-LLM, free-tier only.
- Pipeline targets Python 3.10+ (uses `str | None`, `removeprefix`). Locally on
  this machine it is run with `py -3.14`; CI uses 3.12.
- `sources.yaml` is the community contribution surface and must stay simple to
  hand-edit.

## Architecture / New & Changed Files

```
pipeline/validate_sources.py            # NEW: static schema validator (blocking gate)
pipeline/smoke_sources.py               # NEW: live smoke fetch, per-source candidate counts (non-blocking)
pipeline/sources.yaml                   # CHANGED: fill empty data/awards/events categories
tests/test_extract.py                   # NEW: golden-fixture tests for extract.py
tests/test_validate_sources.py          # NEW: tests for the validator itself
tests/fixtures/extract_cases.yaml       # NEW: real text snippets -> expected extraction
requirements-dev.txt                    # NEW: pytest (kept separate from runtime deps)
.github/workflows/ci.yml                # NEW: PR/push -> validate + pytest (blocking)
.github/workflows/smoke-sources.yml     # NEW: smoke fetch (manual + PRs touching sources.yaml, non-blocking)
.github/ISSUE_TEMPLATE/suggest-a-source.yml  # NEW: structured "suggest a source" form
.github/pull_request_template.md        # NEW: contributor checklist
CONTRIBUTING.md                         # NEW: how to add a source
```

Both new scripts live flat in `pipeline/` to match the existing flat layout, and
both import shared truth from existing modules rather than re-declaring it
(e.g. `from rules.classify import CATEGORIES`, reuse `fetchers/` for smoke).

## Component A — `validate_sources.py` (blocking gate, static, no network)

A standalone script (also importable) that loads `sources.yaml` and validates
**structure only** — no network calls, so it is fast and has zero false
positives from flaky external sites. It is the hard gate every PR must pass.

Checks:

- Top-level keys must be a subset of `{curated, rss, search, reddit}`.
- Each entry has its required field:
  - `curated`, `rss` → `url`
  - `search` → `query`
  - `reddit` → `subreddit`
- `category`, **if present**, must be in `CATEGORIES` (imported from
  `rules.classify`). `null` or omitted is allowed (existing reddit entries use
  `category: null`).
- `curated`/`rss` URLs must be syntactically valid `http(s)` URLs.
- No duplicate `url` (curated/rss), `query` (search), or `subreddit` (reddit).

Behavior: prints a clear, per-error report and exits non-zero on any failure;
exits zero and prints a one-line summary on success. Runnable locally
(`py -3.14 pipeline/validate_sources.py`) and in CI.

## Component B — `smoke_sources.py` + smoke workflow (non-blocking report)

A script that runs the real fetchers and prints a table of **candidates produced
per source**, written to the GitHub Actions job summary.

Decision (confirmed): **smoke-fetches ALL sources**, not just the changed ones.
The full set is small (~13 entries) and runs comfortably; this avoids fragile
YAML-diff parsing to detect "which entries changed."

The workflow triggers on:
- `workflow_dispatch` (manual), and
- PRs that modify `pipeline/sources.yaml`.

It is **non-blocking** (`continue-on-error` / informational): an external site
returning 503 or rate-limiting must never fail an honest PR. The report lets a
human judge whether a new source actually produces candidates.

## Component C — Extraction improvements (test-driven)

The extractor in `pipeline/rules/extract.py` is pure heuristics. Improvements are
made **test-first**: golden fixtures first pin current behavior, then regex is
changed without regression.

Concrete improvements already identified:

- **De-rot hardcoded years.** `extract.py:49` uses
  `default=datetime(2026, 1, 1)` and `extract.py:51` uses a `date(2024, 1, 1)`
  plausibility floor — both hardcoded and will silently rot. Make them relative
  to today (current year as parse default; floor relative to today).
- **Day-first dates.** `_DATE_NEAR` only matches month-first
  ("March 15, 2026"); add day-first ("15 March 2026").
- **More currencies.** Amount regex only handles `$`; add `€` and `£`
  (relevant to region-restricted perks).
- **Explicit no-deadline.** "rolling" / "ongoing" / "no deadline" resolve to
  `None` cleanly rather than matching a stray date.

Specific regex changes are decided during implementation, driven by the fixtures.
This design commits to the *categories* of improvement and to "no regression."

## Component D — Source expansion & rebalancing (behind the A/B guard-rails)

Fill the currently-empty `data`, `awards`, and `events` categories.

Principles:
- **Prefer `search` queries** (they do not rot year-over-year) plus a small
  number of stable official pages / RSS feeds.
- Every new source must (1) pass `validate_sources` and (2) produce ≥1 candidate
  in a smoke run before it is committed.

The concrete source list is produced and verified during implementation — that
is the entire point of building the mechanism first: it prevents hand-waving
dead links into the file.

## Component E — Contribution mechanism (serves Goal 1)

- `.github/ISSUE_TEMPLATE/suggest-a-source.yml`: a structured form (source type,
  URL/query, suggested category, why it's relevant to researchers) that yields a
  ready-to-paste `sources.yaml` snippet.
- `.github/pull_request_template.md`: a short checklist — "ran the validator",
  "ran a smoke fetch", "source is on-topic".
- `CONTRIBUTING.md`: documents the add-a-source flow and the validator/smoke
  commands.
- Update the header comment in `sources.yaml` to point at the validator.

## CI Wiring

- **`ci.yml` (blocking):** on PRs and pushes — install runtime + dev deps, run
  `validate_sources.py`, run `pytest`. Kept separate from `daily.yml` so the
  deploy workflow stays focused on build+deploy.
- **`smoke-sources.yml` (non-blocking):** manual + PRs touching `sources.yaml`.

## Success Criteria

- `validate_sources` blocks malformed entries, bad categories, and duplicate
  sources in CI.
- `tests/` covers extract.py's key paths; CI is green.
- `data`, `awards`, and `events` each go from 0 to >0 perks, verified by a smoke
  run (not asserted blindly).
- An outside contributor can open a source PR that passes the validator by
  following the templates.

## Risks & Mitigations

- **Flaky external sites** → smoke fetch is non-blocking; the blocking gate is
  static-only.
- **Source rot over time** → prefer rot-resistant `search` queries; de-rot the
  hardcoded years in `extract.py`.
- **Over-broad sources pulling in off-topic noise** → existing `filter.keep`
  whitelist/blacklist still applies; new sources are smoke-verified before commit.

## Implementation Sequencing

1. Validator + `ci.yml` + extract golden-fixture harness (pin current behavior).
2. Extraction improvements (test-driven).
3. `smoke_sources.py` + `smoke-sources.yml`.
4. Source expansion & rebalancing (verified via validator + smoke).
5. Contribution templates + `CONTRIBUTING.md` + `sources.yaml` header update.
