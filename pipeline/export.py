"""
Step 7 — Export.

Writes the scored segments to a WGS84 GeoJSON consumed by the web frontend.
"""

import os

import geopandas as gpd


def export_geojson(segments: gpd.GeoDataFrame, output_path: str):
    print(f"[7] Exporting to {output_path}...")

    keep = [
        "id", "geometry",
        "composite_score", "tier",
        "score_pavement", "score_width", "score_slope",
        "score_curb_ramp", "score_obstructions", "score_complaints",
        "pavement_score", "label",
        "width_m", "slope_pct", "curb_height_m",
        "curb_ramp_count", "obstruction_count",
        "complaint_count",
    ]
    export_cols = [c for c in keep if c in segments.columns]
    out = segments[export_cols].copy()

    # Re-project to WGS84 for Mapbox
    if out.crs and out.crs.to_epsg() != 4326:
        out = out.to_crs("EPSG:4326")

    # Convert categorical 'tier' to string (GeoJSON chokes on Categorical)
    if "tier" in out.columns:
        out["tier"] = out["tier"].astype(str)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    out.to_file(output_path, driver="GeoJSON")

    size_mb = os.path.getsize(output_path) / 1e6
    print(f"    -> Exported {len(out):,} segments  ({size_mb:.1f} MB)")
    print(f"    -> File ready at: {output_path}")
