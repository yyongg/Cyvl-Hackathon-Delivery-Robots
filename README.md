# Delivery Robot Feasibility Map — Somerville, MA

Which streets in Somerville can an autonomous sidewalk-delivery robot actually
traverse? This project answers that question by fusing **Cyvl** infrastructure
data, **local LiDAR** point clouds, and **open city data** into a per-segment
feasibility score, then renders it as an interactive web map.

Built for the Cyvl Hackathon.

---

## How it works

The system has two halves:

1. **A Python data pipeline** (`pipeline/`) that scores every street segment and
   writes a single `scored.geojson`.
2. **A React + MapLibre web app** (`web/`) that visualizes those scores
   interactively.

```
┌──────────────────────┐     ┌────────────────────────────┐     ┌──────────────────┐
│  Cyvl S3 (GeoJSON)   │     │   pipeline/  (Python)      │     │  web/  (React)   │
│  pavements / rollup  │ ──► │  load → segments → lidar   │ ──► │  MapLibre map +  │
│  aboveGroundAssets   │     │  → assets → complaints     │     │  score panels    │
│  + local LiDAR .laz  │     │  → scoring → export        │     │                  │
│  + 311 / vision-zero │     │        scored.geojson      │     │                  │
└──────────────────────┘     └────────────────────────────┘     └──────────────────┘
```

### The feasibility score

Each segment gets a `composite_score` (0–100) from a weighted blend of six
metrics, then a tier: **green** (≥70, robot-ready), **yellow** (40–70, marginal),
**red** (<40, infeasible).

| Metric          | Weight | Source                                   |
| --------------- | -----: | ---------------------------------------- |
| Pavement (PCI)  |   30%  | Cyvl `pavements_v2`                      |
| Sidewalk width  |   25%  | Local LiDAR `.laz`                       |
| Slope / grade   |   15%  | Local LiDAR `.laz`                       |
| Curb ramps      |   15%  | Cyvl `aboveGroundAssets_v2`              |
| Obstructions    |   10%  | Cyvl `aboveGroundAssets_v2` (manholes…)  |
| 311 complaints  |    5%  | `data/311_complaints.csv` (optional)     |

Weights live in [`pipeline/config.py`](pipeline/config.py); the normalisation
curves for each metric are documented inline in
[`pipeline/scoring.py`](pipeline/scoring.py).

---

## Project structure

```
.
├── run_pipeline.py          # thin CLI entry point → pipeline.cli.main()
├── pipeline/                # Python package, one module per pipeline stage
│   ├── config.py            #   paths, CRS, LiDAR params, scoring weights
│   ├── data_sources.py      #   [1] load Cyvl layers (cache → S3)
│   ├── segments.py          #   [2] build the base segment layer
│   ├── lidar.py             #   [3] width / slope / curb height from .laz
│   ├── assets.py            #   [4] curb ramps + obstructions (spatial join)
│   ├── complaints.py        #   [5] 311 complaint density (optional)
│   ├── scoring.py           #   [6] normalise → weighted composite → tiers
│   ├── export.py            #   [7] write scored.geojson (WGS84)
│   └── cli.py               #   orchestrates steps 1–7
├── web/                     # React + Vite + MapLibre frontend
│   └── src/
│       ├── App.jsx          #   composition root
│       ├── hooks/           #   useFeasibilityMap — MapLibre lifecycle
│       ├── components/      #   Sidebar, DetailPanel, Tooltip, ScoreBar
│       ├── utils/           #   color helpers
│       └── constants.js     #   tier colors / labels / score fields
├── data/                    # large inputs — gitignored (see "Data" below)
├── requirements.txt
└── pyproject.toml
```

---

## Quick start

### 1. Run the pipeline

```bash
pip install -r requirements.txt
python run_pipeline.py
```

No credentials needed — Cyvl layers stream from the public S3 bucket and cache
to `data/cache/` on first run. The pipeline writes
`web/public/scored.geojson`.

> **LiDAR:** Step 3 reads a local point cloud at `data/merged.laz`. Only
> segments inside that file's footprint are scored. Point `LAZ_PATH` in
> [`pipeline/config.py`](pipeline/config.py) at your own `.laz` if it lives
> elsewhere.

### 2. Run the web app

```bash
cd web
npm install
npm run dev
```

Open the printed local URL. The app loads `scored.geojson` from `web/public/`,
colors each segment by its composite score, and lets you hover for a quick
readout or click for a full breakdown. The sidebar filters by tier.

---

## Data

The `data/` directory is **gitignored** — the LiDAR and full GeoJSON layers are
hundreds of megabytes and exceed GitHub's limits. Nothing in `data/` is required
to be present in the repo:

- **Cyvl layers** (`pavements_v2`, `rollup_v2`, `aboveGroundAssets_v2`) are
  fetched automatically from the public Cyvl S3 bucket and cached to
  `data/cache/`.
- **LiDAR** (`data/merged.laz`) must be supplied locally — place your `.laz`
  there (or update `LAZ_PATH`).
- **Open data** (optional, improves scoring):
  - `data/311_complaints.csv` — from [data.somervillema.gov](https://data.somervillema.gov)
  - `data/vision_zero.csv` — from [data.boston.gov](https://data.boston.gov)

---

## Configuration

All tunables are centralised in [`pipeline/config.py`](pipeline/config.py):
data-source URLs, file paths, coordinate reference systems, LiDAR sampling
parameters, and the scoring weights (which must sum to 1.0).
