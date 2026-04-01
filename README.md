# Fantasy Wrapped

End-of-season recap for the Lucas Basketball Association, 2025-26. Personalized stats, trade analysis, draft grades, and awards for each team.

## How it works

The app has two halves: a Python data pipeline that pulls everything from ESPN's API, and a Next.js frontend that renders the results.

### Data pipeline

The `data/` directory is a modular Python package that authenticates against ESPN's private fantasy API (via `espn-api`) and produces one JSON file per team plus a `league_meta.json` with standings, trades, waivers, and draft analysis. The entry point is `data/extract.py`, which delegates to `data/pipeline.py`.

The extraction runs in two phases because ESPN's box score endpoint behaves differently depending on how you call it:

- **Phase 1** (`matchup_total=True`, 21 API calls) returns weekly scores and starter totals, but assigns every player to the PG slot regardless of where they were actually rostered.
- **Phase 2** (`matchup_total=False`, ~153 API calls) returns per-scoring-period data with correct roster slots, bench players, and eligible positions (but only for a single day at a time).

The script merges both: Phase 1 gives accurate weekly point totals per player, Phase 2 gives the actual lineup structure. This merge is necessary for computing optimal lineups (which need to know who was eligible for which slot) and bench misplays (which need to know who was benched vs. started).

Once the raw data is assembled, the script derives everything else:

- **Trade analysis** uses `player_info()` to pull per-scoring-period breakdowns for every traded player, sums only the periods after the trade, and computes a net impact. Uneven trades (2-for-1) get a roster slot adjustment valued at replacement-level production.
- **Draft grades** compare each pick's draft position against their end-of-season rank. Season rank uses adjusted totals (actual points plus replacement-level production for missed weeks, capped at the player's own rate) so injuries don't automatically make a pick a "bust." Team-level grades are relative (ranked against the league using capped clustering, max 3 teams per grade tier).
- **All-play records** simulate every team against every other team each week to measure luck vs. skill.
- **Scoring profiles** break down each team's fantasy points by statistical category (PTS, REB, AST, STL, BLK, TO) as a percentage of total output, then compare against the league average.

The pipeline makes roughly 175 API calls total and takes about 2 minutes. Results are written to `public/data/` as static JSON, which the frontend reads at runtime.

### Frontend

The frontend is a Next.js app with two routes:

- `/`: league dashboard with tabs for team standings, trades, waivers, and draft analysis
- `/team/[id]`: individual team page with 12 scrollable sections (timeline, trades, waivers, roster heatmap, scoring profile, luck analysis, optimal lineup, bench misplays, awards, head-to-head, and report card)

Each team page applies a unique color scheme via CSS custom properties injected at the page level. The 12 color palettes in `lib/team-colors.ts` map to `--team-primary`, `--team-secondary`, and `--team-glow`, which cascade through the entire page without any component needing to know which team it's rendering.

Scroll-driven animations use a mix of GSAP ScrollTrigger (for batch reveals and section pinning) and Framer Motion (for parallax transforms). Three custom hooks handle the patterns that repeat across sections:

- `useScrollBatch`: staggers child elements into view as a group using GSAP batching
- `useScrollPin`: pins a section during scroll and reports a 0–1 progress value, used to drive the radar chart animation and category breakdown reveal
- `useActiveSection`: tracks which section is in the viewport via IntersectionObserver, driving the sticky nav indicator

Charts use Recharts. Tooltips are portaled to the document body to avoid clipping inside overflow-hidden containers.

### Stack

| Layer | Tech |
| --- | --- |
| Framework | Next.js 16, React 19, TypeScript |
| Styling | Tailwind CSS 4 with OKLCh color system |
| Animation | GSAP + ScrollTrigger, Framer Motion, Lenis |
| Charts | Recharts |
| UI primitives | Radix UI (select, tooltip) |
| Data extraction | Python, espn-api |
| Lint/format | Biome |

## Project structure

```text
app/
  page.tsx                 League dashboard (standings, tabs)
  team/[id]/page.tsx       Individual team wrapped page
  globals.css              Theme variables, animations, grade colors

components/
  wrapped/                 Section components (one per wrapped section)
  ui/                      Shared primitives (chart tooltip, select, etc.)
  providers/               Smooth scroll (Lenis) context

hooks/                     Custom hooks (scroll batch, pin, count-up, data fetching)
lib/                       Types, chart constants, team colors, utilities

data/
  extract.py               Entry point (thin shim → pipeline.py)
  pipeline.py              Orchestration (fetch, extract, main)
  fetch.py                 ESPN API calls
  standings.py             Standings, scores, player totals
  trades.py                Trade extraction + league aggregation
  waivers.py               Waiver pickup extraction + aggregation
  lineup.py                Optimal lineup solver, bench misplays
  draft.py                 Draft analysis + grading
  grades.py                Rank clustering, league-wide grades
  team.py                  Per-team assembly, awards, H2H
  ownership.py             Player ownership timeline
  models.py                Domain types (TeamRef, PlayerData, etc.)
  constants.py             Config, matchup dates, ESPN maps
  helpers.py               Shared utilities
  cache.py                 Cache serialization/deserialization
  validate*.py             Data integrity checks
  tests/                   pytest suite

public/data/               Static JSON (league_meta + per-team files)
```
