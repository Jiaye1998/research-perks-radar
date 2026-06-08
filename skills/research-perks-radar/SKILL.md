---
name: research-perks-radar
description: Use when working in Jiaye1998/research-perks-radar to refresh the zero-LLM research perks pipeline, edit sources.yaml, validate sources, run tests, update the Next.js static site, maintain GitHub Pages deployment, or help users install and use this Codex Skill.
---

# Research Perks Radar

## Scope

Use this skill inside the `Jiaye1998/research-perks-radar` repository or when a user asks to install, run, refresh, validate, document, or publish Research Perks Radar.

Research Perks Radar is an open, auto-updating radar for research perks: free AI or compute credits, grants, academic software discounts, datasets, awards, events, and travel support. The project uses a zero-LLM Python pipeline and a static Next.js site. Browser-side CV matching may call the user's own Anthropic, OpenAI, or Google key directly from the page.

## Repo map

- `.github/workflows/daily.yml`: daily pipeline, data commit, static site build, GitHub Pages deploy
- `.github/workflows/ci.yml`: source validation and tests
- `pipeline/main.py`: pipeline orchestrator; writes `data/perks.json` and `data/history/<date>.json`
- `pipeline/sources.yaml`: curated, RSS, search, and Reddit source definitions
- `pipeline/validate_sources.py`: no-network source schema validation
- `pipeline/smoke_sources.py`: optional source smoke check
- `pipeline/rules/`: classify, extract, filter, score, urgency rules
- `data/perks.json`: live feed consumed by the site
- `data/history/`: daily snapshots
- `web/`: Next.js static site
- `README.md`: live counts between `<!--STATS-->` markers

## First steps

1. Inspect `README.md`, `SETUP.md`, and the current working tree before editing.
2. Use `rg --files` to map files quickly.
3. Prefer existing pipeline scripts and GitHub workflow commands.
4. Do not describe the project as an MCP server unless a real `.mcp.json` or plugin MCP config is added.

## Local setup

For pipeline work:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Optional search keys improve results but are not required:

```bash
export TAVILY_API_KEY=...
export BRAVE_API_KEY=...
```

Use the platform-equivalent environment-variable commands on Windows.

For site work:

```bash
cd web
npm install
```

Use `npm ci` when `package-lock.json` is present and the workflow should match CI.

## Source changes

When adding or editing research perk sources:

1. Edit `pipeline/sources.yaml`.
2. Keep search queries specific and assign a category hint when possible.
3. Use only supported categories: `ai_compute`, `funding`, `software`, `data`, `awards`, `events`.
4. Validate before handing back:

```bash
python pipeline/validate_sources.py
pytest -q
```

Optionally smoke-test source reachability:

```bash
cd pipeline
python smoke_sources.py
```

## Data refresh

To refresh the feed locally:

```bash
cd pipeline
python main.py
```

Expected outputs:

- `data/perks.json`
- `data/history/<today>.json`
- updated README stats between `<!--STATS-->` and `<!--/STATS-->`

Preserve `first_seen` and `is_new` behavior. `is_new` means first seen within the configured 7-day window, and existing perks without previous `first_seen` should not be falsely marked new.

## Site validation

After a data or web change, copy the feed into the static site and build:

```bash
cp data/perks.json web/public/perks.json
cd web
NEXT_PUBLIC_BASE_PATH=/research-perks-radar npm run build
```

On Windows PowerShell, set the variable before running the build:

```powershell
$env:NEXT_PUBLIC_BASE_PATH="/research-perks-radar"
npm run build
```

If doing local visual work, run:

```bash
cd web
npm run dev
```

Then inspect `http://localhost:3000`.

## GitHub Actions behavior

The daily workflow runs at 06:00 UTC and can be triggered manually. It:

1. installs Python dependencies
2. runs `cd pipeline && python main.py`
3. commits updated `data/` and `README.md`
4. copies `data/perks.json` to `web/public/perks.json`
5. builds the Next.js static site with `NEXT_PUBLIC_BASE_PATH` set from the repo name
6. deploys `web/out` to GitHub Pages

CI runs:

```bash
python pipeline/validate_sources.py
pytest -q
```

Match these checks before reporting a change as ready.

## Documentation guidance

For Codex installation instructions, point users to:

```text
https://github.com/Jiaye1998/research-perks-radar/tree/main/skills/research-perks-radar
```

Keep public docs concise. Explain that the pipeline is zero-LLM, while CV matching happens in the user's browser with their own provider key.

## Handoff

Before finishing, report:

- files changed
- whether sources were validated
- whether tests ran
- whether the site build ran
- any skipped check and the reason
