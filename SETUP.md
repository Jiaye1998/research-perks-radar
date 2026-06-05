# Setup — from zip to live site

You have the project locally at `E:\research-perks-radar`. Here's how to get it running and deployed. ~10 minutes.

## 1. Create the GitHub repo

1. Make a new **public** repo on GitHub named `research-perks-radar` (public is required for free GitHub Pages + Actions).
2. In a terminal at `E:\research-perks-radar`:

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<your-user>/research-perks-radar.git
git push -u origin main
```

## 2. Turn on GitHub Pages

Repo → **Settings → Pages** → under "Build and deployment", set **Source = GitHub Actions**. (No branch to pick — the workflow handles it.)

## 3. (Optional) add free search API keys

Without keys the radar still works off curated sites, RSS, and Reddit. Keys make it find a lot more.

- Tavily: sign up at tavily.com (1000 searches/mo free) → copy key
- Brave: brave.com/search/api (2000/mo free) → copy key

Repo → **Settings → Secrets and variables → Actions → New repository secret**, add:

- `TAVILY_API_KEY` = your Tavily key
- `BRAVE_API_KEY` = your Brave key

## 4. Run it

Repo → **Actions → Daily Radar → Run workflow**. First run will:
- run the pipeline, commit a fresh `data/perks.json`
- build the site and deploy to Pages

After it finishes, your site is at:
`https://<your-user>.github.io/research-perks-radar/`

It then re-runs automatically every day at 06:00 UTC. Change the time in `.github/workflows/daily.yml` (the `cron` line) if you like.

## 5. Using the CV match

On the live site, open the "Match perks to your CV" panel, paste your CV, pick a provider (Anthropic / OpenAI / Google), and paste *your own* API key. The CV and key stay in your browser and go straight to that provider — nothing hits a server you'd have to run. A cheap small model is used (Haiku / gpt-4o-mini / Gemini Flash).

## Local development

```bash
# pipeline
pip install -r requirements.txt
cd pipeline && python main.py      # writes ../data/perks.json

# site (in another terminal)
cd web
npm install
cp ../data/perks.json public/perks.json
npm run dev                        # http://localhost:3000
```

## Adding more sources

Edit `pipeline/sources.yaml` — add curated pages, RSS feeds, search queries, or subreddits. Commit and push; the next run picks them up. The schema is documented at the top of that file.

## Notes & limits

- The rule engine is heuristic: it extracts amounts/deadlines by pattern, so always confirm details on the official page (the footer says this too).
- GitHub Pages project sites serve under `/research-perks-radar/`; the workflow sets `NEXT_PUBLIC_BASE_PATH` automatically from the repo name. If you rename the repo, no code change needed.
- All free tiers: GitHub Actions minutes (public repos are generous), Tavily/Brave free quotas, and the user's own LLM key for CV match.
