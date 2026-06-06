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
