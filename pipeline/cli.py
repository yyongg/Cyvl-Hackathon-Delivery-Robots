"""
Pipeline orchestration / entry point.

Wires the seven steps together into a single run. Invoke via the project-root
``run_pipeline.py`` shim or ``python -m pipeline``.
"""

import os
import warnings

from pipeline.config import COMPLAINTS_CSV, LAZ_PATH, OUTPUT_PATH
from pipeline.data_sources import load_cyvl_layers
from pipeline.segments import build_segments
from pipeline.lidar import extract_lidar_metrics_local
from pipeline.assets import join_assets
from pipeline.complaints import load_complaints, join_complaints
from pipeline.scoring import run_scoring
from pipeline.export import export_geojson

warnings.filterwarnings("ignore", category=FutureWarning)


def main():
    print("=" * 60)
    print("  Delivery Robot Feasibility Pipeline — Somerville MA")
    print("  Data source: cyvl-hackathon S3 + cyvl-spatial-sdk")
    print("=" * 60)

    # ── 1. Load Cyvl layers ───────────────────────────────────────────────
    pavements, rollup, assets = load_cyvl_layers()

    # ── 2. Build base segment layer ───────────────────────────────────────
    segments = build_segments(pavements, rollup)

    # ── 3. LiDAR width + slope (local .laz file) ────────────────────────
    # Returns only the segments covered by the LAZ footprint.
    segments = extract_lidar_metrics_local(segments, LAZ_PATH)
    if len(segments) == 0:
        print("No segments found in LAZ coverage area — check LAZ_PATH.")
        return

    # ── 4. Curb ramps + obstructions from Cyvl assets ───────────────────
    segments = join_assets(segments, assets)

    # ── 5. 311 complaint density (optional open data) ────────────────────
    if os.path.exists(COMPLAINTS_CSV):
        complaints_gdf = load_complaints(COMPLAINTS_CSV)
        if complaints_gdf is not None:
            segments = join_complaints(segments, complaints_gdf)
        else:
            segments["complaint_count"] = 0
    else:
        print(f"[5] SKIPPING — {COMPLAINTS_CSV} not found.")
        print("    Download from data.somervillema.gov to include complaint density.")
        segments["complaint_count"] = 0

    # ── 6. Score ──────────────────────────────────────────────────────────
    segments = run_scoring(segments)

    # ── 7. Export ─────────────────────────────────────────────────────────
    export_geojson(segments, OUTPUT_PATH)

    print()
    print("Pipeline complete.")
    print("Next step:  cd web && npm install && npm run dev")
    print()
    print("Tip: set CYVL_SCENE_DIR=/path/to/parquet-dir to use a local")
    print("     copy of the parquet files instead of streaming from CDN.")


if __name__ == "__main__":
    main()
