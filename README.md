# MetaRank — The leaderboard of leaderboards

MetaRank takes the top public AI-model rankings and averages them into a
single consensus view, with tabs for **Overall**, **Chat**, **Coding**,
**Agents**, **Pricing**, **Open Weights**, and **Self-Hosted**. Built for
newcomers — a plain-English explainer, "how to read it", and per-model
source breakdowns.

The live site is served from this repo via GitHub Pages (`docs/`).

## Sources (8 live, 1 optional) + pricing

| ID | Source | Measures | Tab | Data date | Key? |
|----|--------|----------|-----|-----------|------|
| `lmarena` | [LMArena](https://lmarena.ai/leaderboard) (public HF dataset, CC-BY-4.0) | Millions of blind human votes, Bradley-Terry rating | Chat | 2026-09-11 | no |
| `aa` | [Artificial Analysis](https://artificialanalysis.ai/) Intelligence Index API | Independent evals across ~10 benchmarks | Chat | — (skipped until key) | **yes** (free) |
| `swebench` | [SWE-bench Verified](https://www.swebench.com/) (raw JSON from GitHub) | Real GitHub issue fixes, % resolved | Coding | 2026-02-26 | no |
| `webdev` | [LMArena WebDev Arena](https://lmarena.ai/leaderboard) (public HF dataset, CC-BY-4.0) | Blind human votes on web-app builds, Bradley-Terry rating | Coding | 2026-09-11 | no |
| `terminalbench` | [Terminal-Bench 2.1](https://www.tbench.ai/leaderboard/terminal-bench/2.1) | 89 hard terminal tasks run by an agent, accuracy % | Coding | 2026-09-10 | no |
| `cursorbench` | [CursorBench](https://cursor.com/cursorbench) (SSR HTML table, 43 models) | Ambiguous multi-file coding tasks from real Cursor sessions, score % | Coding | 2026-09-12 | no |
| `epoch` | [Epoch AI](https://epoch.ai/data/benchmark_data.zip) capabilities index (CC-BY-4.0) | Independent re-runs of hard benchmarks | Agents | (zip has no date) | no |
| `livebench` | [LiveBench](https://livebench.ai/) GitHub CSVs | Fresh monthly questions, contamination-resistant scores | General (Overall only) | 2026-06-25 | no |
| `pricing` | [OpenRouter](https://openrouter.ai/api/v1/models) public models API | Live per-token prices → $ per 1M tokens (input/output) | Pricing | live | no |

## Site features

- **7 tabs:** Overall, Chat, Coding, Agents, Pricing (input/output $/1M,
  sortable by price, from OpenRouter), Open Weights, Self-Hosted.
- **No-rollup policy:** every distinct model variant is its own row —
  `GPT-5`, `GPT-5 (high)` and `GPT-5 (low)` are ranked separately. Only
  casing/punctuation/vendor naming is normalized; each variant keeps its
  best rank per source.
- **Filters:** model-name search, minimum-sources dropdown (All / 2+ / 3+ /
  4+), and a **region filter** (All regions / USA / China / Europe / Canada /
  UK / Singapore / UAE / Other) — region = the lab's headquarters country,
  from a curated map, applied client-side to whichever tab is active.
- **Export CSV / Export JSON** buttons download the currently visible
  (filtered + sorted) rows of the active tab.
- Click a model for its per-source breakdown; click any column header to sort.

## Curated data files

Two aspects aren't auto-detectable, so they live in curated JSON under
`metarank/data/`:

- **`open_models.json`** — normalized model key → `{params_b,
  self_hostable}`. Seeds the Open Weights tab (publicly released weights)
  and the Self-Hosted tab (commonly runnable locally via Ollama/vLLM:
  roughly ≤32B dense, or popular MoEs people actually self-host —
  conservative by design).
- **`model_origins.json`** — normalized model key → region code, seeded
  from each lab's headquarters country (`prefixes` matches the start of the
  normalized key, longest match wins; `models` holds exact-key overrides).

Both are plainly labeled as curated on the site. Spot something wrong or
missing? Contributions are welcome via GitHub pull request.

## How it works

1. Each source's leaderboard is fetched and ranked internally.
2. Model names are normalized (casing, punctuation, vendor naming) but
   **never rolled up**: every distinct variant stays its own row, and each
   variant's best rank per source wins.
3. **Average rank** = mean of a model's ranks across the sources it appears
   on (lower is better). Ties break on #1st-place finishes, then source count.
4. OpenRouter pricing is fetched (no key needed) and matched onto ranked
   models by normalized name; unmatched models show "—".
5. Each row is tagged `open_weights` / `self_hostable` /
   `params_b` (from `metarank/data/open_models.json`) and `region`
   (from `metarank/data/model_origins.json`).
6. Output: `data-YYYY-MM-DD.json` with per-tab rankings — `overall`
   (min 2 sources, top 60), `chat` / `coding` / `agents` (min 1 source,
   top 60), `pricing` (overall models + prices), `open` / `selfhosted`
   (overall models filtered to those subsets). LiveBench is "general":
   it only counts toward Overall.
7. `site/build.py` (stdlib only) renders `docs/index.html` (self-contained,
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
  data/              curated JSON: open_models.json, model_origins.json
  normalize.py       model-name canonicalization (no variant roll-up)
  aggregate.py       fetch + rank + per-tab aggregation -> data-*.json
site/build.py        stdlib static site generator -> docs/
docs/                GitHub Pages output (index.html, data.json)
data-YYYY-MM-DD.json dated snapshots (committed)
.github/workflows/  daily refresh cron
```

Reference repos cloned during research (`ref-llm-rating/`, `ref-model-watch/`)
are git-ignored scratch material and can be deleted.
