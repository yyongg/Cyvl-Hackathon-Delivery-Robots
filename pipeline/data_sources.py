"""
Step 1 — Load Cyvl layers.

Pulls the GeoJSON layers the pipeline needs from a local cache, falling back
to streaming them directly from the public Cyvl S3 bucket.
"""

import os

import geopandas as gpd

from pipeline.config import CACHE_DIR, S3_BASE


def load_layer(name: str, cache_dir: str = CACHE_DIR) -> gpd.GeoDataFrame:
    """
    Load a GeoJSON layer from the local cache if present, otherwise
    stream it directly from the public S3 bucket over HTTPS.

    Available layers (from the hackathon README):
        rollup_v2              — street network with overall condition score
        pavements_v2           — road segments with PCI-style scores + labels
        distresses_v2          — individual cracks/potholes
        aboveGroundAssets_v2   — manholes, drains, hydrants, curb ramps, etc.
        signs_v2               — MUTCD-classified traffic signs
        sam_v2                 — pavement markings / striping
        plainImagery_v2        — geotagged street-level photo points
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{name}.geojson")

    if os.path.exists(cache_path):
        print(f"    [{name}] loading from cache...")
        return gpd.read_file(cache_path)

    url = f"{S3_BASE}/data/{name}.geojson"
    print(f"    [{name}] downloading from S3 ({url})...")
    gdf = gpd.read_file(url)
    gdf.to_file(cache_path, driver="GeoJSON")
    print(f"    [{name}] {len(gdf):,} features cached to {cache_path}")
    return gdf


def load_cyvl_layers():
    """Load all Cyvl layers needed for the pipeline."""
    print("[1] Loading Cyvl layers from public S3 bucket...")

    # Primary scoring source: pavement condition segments
    pavements = load_layer("pavements_v2")

    # Street-level network for segment geometry + overall rollup scores
    rollup = load_layer("rollup_v2")

    # Above-ground assets: curb ramps, manholes, drains, hydrants
    assets = load_layer("aboveGroundAssets_v2")

    # Print available columns so we can verify field names
    print(f"\n    pavements_v2 columns: {list(pavements.columns)}")
    print(f"    rollup_v2 columns:    {list(rollup.columns)}")
    print(f"    aboveGroundAssets columns: {list(assets.columns)}\n")

    return pavements, rollup, assets
