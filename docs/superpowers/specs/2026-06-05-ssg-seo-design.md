# SSG & SEO (MVP) — Design

**Date:** 2026-06-05
**Status:** Approved (pending written-spec review)
**Scope:** `web/` only. The pipeline and data are untouched.

## Goal

Make the site's perk content visible to search engines. Today `app/page.tsx`
is a client component that fetches `perks.json` at runtime, so the statically
exported HTML contains no perk content — crawlers see an empty shell. Render the
perks into the static HTML at build time, and add the standard SEO metadata
(OpenGraph, canonical, sitemap, robots, JSON-LD). This is the largest lever for
organic discovery (Goal 1: GitHub/site attention).

## Non-Goals

- No per-category or per-perk static pages (deliberately deferred — perks churn
  daily and link out to external official pages, so dedicated thin pages have low
  SEO value and duplicate-content risk).
- No visual/UI redesign — the look stays identical.
- No custom OG image (text-based OG metadata only for MVP).
- No changes to the pipeline, `sources.yaml`, or `daily.yml`.
- CV matching stays entirely client-side.

## Constraints (inherited)

- Must remain a static export (`output: "export"` in `next.config.js`) — no SSR
  server at runtime; everything is generated at build.
- GitHub Pages project site: served under `basePath` = `/research-perks-radar`
  (set via `NEXT_PUBLIC_BASE_PATH` in CI; empty locally). Canonical/sitemap URLs
  must use the full absolute site URL.
- Free-tier, zero-server.

## Site URL

Canonical site URL: `https://jiaye1998.github.io/research-perks-radar/`

## Architecture / Components

```
web/app/page.tsx              # CHANGED: client -> Server Component (reads data at build, embeds JSON-LD)
web/components/PerksExplorer.tsx  # NEW: client component — the former page.tsx interactive body, takes `feed` as a prop
web/app/layout.tsx            # CHANGED: full SEO metadata (metadataBase, openGraph, twitter, canonical)
web/app/robots.ts             # NEW: generates robots.txt
web/app/sitemap.ts            # NEW: generates sitemap.xml
web/lib/site.ts               # NEW: shared SITE_URL / site constants (single source of truth)
web/components/PerkCard.tsx   # unchanged
web/components/CvPanel.tsx    # unchanged
web/lib/types.ts, cv-match.ts # unchanged
```

### `app/page.tsx` (Server Component)

- Becomes a Server Component (remove `"use client"`).
- At build time, reads the feed: `fs.readFileSync(path.join(process.cwd(), "public", "perks.json"))`, parsed to a `PerksFeed`. On any read/parse error, fall back to an empty feed (`{ generated_at: "", count: 0, by_category: {}, perks: [] }`) so the build never crashes.
- Renders `<PerksExplorer feed={feed} />`.
- Emits a `<script type="application/ld+json">` block: a schema.org `ItemList` whose items are the perks (name = title, url = perk.url, plus position). This is static structured data for rich results.

### `components/PerksExplorer.tsx` (Client Component)

- `"use client"`. Receives `feed: PerksFeed` as a prop.
- Contains exactly the current interactive logic moved out of `page.tsx`:
  header, hero, the three bento cards (closing-soon / most-rewarding / best-fit),
  the `CvPanel`, the filter pills + search box, and the perk grid.
- **Removes** the `useEffect` + `fetch("/perks.json")` — `feed` now comes from
  props. All `useState`/`useMemo`/CV-match behavior is otherwise unchanged.
- Because Next.js server-renders client components at build time, the initial
  (unfiltered) perk grid is included in the exported HTML — which is the SEO win.

### Data flow

- Build: `page.tsx` reads `public/perks.json` → passes `feed` to
  `PerksExplorer` → initial render (all perks) is baked into `out/index.html`.
- Runtime: hydration enables filtering/search/CV matching against the in-memory
  `feed`. No runtime `fetch`.
- The CI workflow already copies `data/perks.json` to `web/public/perks.json`
  before `npm run build`; no workflow change needed. For local builds the same
  copy must exist (documented in the plan's verification).

## SEO Additions

- **`lib/site.ts`**: exports `SITE_URL = "https://jiaye1998.github.io/research-perks-radar/"` (and a name/description) used by metadata, sitemap, robots — one source of truth.
- **`layout.tsx` metadata**: `metadataBase: new URL(SITE_URL)`, `title`, `description`, `alternates.canonical: "/"`, `openGraph` (type=website, url, title, description, siteName), `twitter` (card=summary).
- **`app/robots.ts`**: returns `{ rules: [{ userAgent: "*", allow: "/" }], sitemap: SITE_URL + "sitemap.xml" }`.
- **`app/sitemap.ts`**: returns a single entry for `SITE_URL` with `lastModified` = feed `generated_at` (or build time). (Static export emits `out/sitemap.xml`.)
- **JSON-LD** `ItemList` embedded in `page.tsx` (see above).

## Error Handling

- Missing/invalid `public/perks.json` at build → empty feed fallback; page still
  builds and renders the shell (no crash).
- `metadataBase` ensures OG/canonical URLs resolve to absolute even though the
  app uses a basePath.

## Testing / Verification

The `web/` project has no JS test framework; per YAGNI we do not add one. Success
is verified against the build output:

1. `npm run build` succeeds.
2. `out/index.html` contains real perk title text (proves content is in the
   static HTML, not fetched at runtime) — grep for a known perk title.
3. `out/sitemap.xml` and `out/robots.txt` exist and contain the site URL.
4. `out/index.html` contains the JSON-LD `ItemList` script.
5. The dev server (`npm run dev`) still renders the page correctly with working
   filters and CV panel (no regression).

## Success Criteria

- View-source of the built homepage shows all perks (titles, summaries, links) in
  the HTML.
- `sitemap.xml`, `robots.txt`, OpenGraph, and canonical are present and correct.
- No runtime `fetch` of `perks.json`; UI behavior (filters/search/CV) unchanged.
- Still a clean static export deployable to GitHub Pages under the basePath.

## Risks & Mitigations

- **fs read during static export** — server components run in Node at build, so
  `fs` is available; guarded with a try/catch fallback.
- **basePath vs absolute SEO URLs** — handled by `metadataBase` + `SITE_URL`
  constant; internal asset/links continue to use `NEXT_PUBLIC_BASE_PATH`.
- **Hydration mismatch** — avoided because the same `feed` props drive both the
  build-time render and client hydration (deterministic; no `Date.now()`/random
  in initial render).

## Implementation Sequencing

1. Add `lib/site.ts`.
2. Extract `PerksExplorer.tsx` from `page.tsx` (client), drop the fetch, take props.
3. Convert `page.tsx` to a Server Component that reads the feed and renders
   `PerksExplorer` + JSON-LD.
4. Enrich `layout.tsx` metadata; add `robots.ts` and `sitemap.ts`.
5. Build, verify the output assertions; run dev to confirm no UI regression.
