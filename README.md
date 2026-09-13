# MetaRank — The leaderboard of leaderboards

MetaRank takes the top public AI-model rankings and averages them into a
single consensus view, with tabs for **Overall**, **Chat**, **Coding**
and **Agents**. Built for newcomers — a plain-English explainer, "how to
read it", and per-model source breakdowns.

The live site is served from this repo via GitHub Pages (`docs/`).

## Sources (4 live, 1 optional)

| ID | Source | Measures | Tab | Key? |
|----|--------|----------|-----|------|
| `lmarena` | [LMArena](https://lmarena.ai/leaderboard) (public HF dataset, CC-BY-4.0) | Millions of blind human votes, Bradley-Terry rating | Chat | no |
| `aa` | [Artificial Analysis](https://artificialanalysis.ai/) Intelligence Index API | Independent evals across ~10 benchmarks | Chat | **yes** (free) |
| `aider` | [Aider](https://aider.chat/docs/leaderboards/) polyglot leaderboard | 225 real coding exercises, 6 languages | Coding | no |
| `epoch` | [Epoch AI](https://epoch.ai/data/benchmark_data.zip) capabilities index (CC-BY-4.0) | Independent re-runs of hard benchmarks | Agents | no |
| `livebench` | [LiveBench](https://livebench.ai/) GitHub CSVs | Fresh monthly questions, contamination-resistant scores | General (Overall only) | no |

## How it works

1. Each source's leaderboard is fetched and ranked internally.
2. Model name variants (e.g. reasoning-effort suffixes like `-high`/`-max`,
   site-specific naming) collapse to one canonical model; best rank per
   source wins.
3. **Average rank** = mean of a model's ranks across the sources it appears
   on (lower is better). Ties break on #1st-place finishes, then source count.
4. Output: `data-YYYY-MM-DD.json` with per-tab rankings — `overall`
   (min 2 sources, top 60), `chat` / `coding` / `agents` (min 1 source, top 60).
   LiveBench is "general": it only counts toward Overall.
5. `site/build.py` (stdlib only) renders `docs/index.html` (self-contained,
   data embedded) + `docs/data.json` from the newest dated JSON.

## Run locally

```bash
pip install -r requirements.txt
python metarank/aggregate.py data-$(date +%F).json
python site/build.py
# open docs/index.html
```

## Adding the Artificial Analysis key

The AA fetcher is key-gated: without a key it logs `SKIP aa` and the
pipeline continues with the other sources.

- **Locally:** `export ARTIFICIALANALYSIS_API_KEY=...` (free key at
  artificialanalysis.ai, 100 req/day).
- **On GitHub:** repo Settings → Secrets and variables → Actions →
  New repository secret named `ARTIFICIALANALYSIS_API_KEY`. The daily
  workflow picks it up automatically.

## Daily auto-refresh

`.github/workflows/daily.yml` runs ~06:00 UTC: installs deps, runs the
pipeline to a new dated JSON, rebuilds the site, and commits + pushes
`data-*.json` + `docs/` if anything changed. Manual runs: Actions tab →
"Daily refresh" → Run workflow.

## Enable GitHub Pages

Settings → Pages → **Deploy from a branch** → branch `main`, folder
`/docs` → Save. The site appears at
`https://<user>.github.io/<repo>/`.

## Layout

```
metarank/            pipeline package
  fetchers/          one module per source (each exposes SOURCE + fetch())
  normalize.py       model-name canonicalization
  aggregate.py       fetch + rank + per-tab aggregation -> data-*.json
site/build.py        stdlib static site generator -> docs/
docs/                GitHub Pages output (index.html, data.json)
data-YYYY-MM-DD.json dated snapshots (committed)
.github/workflows/  daily refresh cron
```

Reference repos cloned during research (`ref-llm-rating/`, `ref-model-watch/`)
are git-ignored scratch material and can be deleted.
