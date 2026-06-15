"""
Step 5 — 311 complaint density (optional).

Loads sidewalk-related 311 complaints from a local CSV and joins their density
onto each segment. Skipped gracefully when the CSV is absent.
"""

import pandas as pd
import geopandas as gpd

from pipeline.config import METERS_CRS


def load_complaints(csv_path: str) -> gpd.GeoDataFrame | None:
    print(f"[5] Loading 311 complaints from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)

    lat_col = next((c for c in ["latitude", "lat", "Y", "y_coord"] if c in df.columns), None)
    lon_col = next((c for c in ["longitude", "lon", "X", "x_coord"] if c in df.columns), None)
    if not lat_col or not lon_col:
        print(f"    !! Lat/lon columns not found. Available: {df.columns.tolist()}")
        return None

    kw  = ["sidewalk", "accessibility", "curb", "pavement", "walkway"]
    svc = next((c for c in ["service_name", "type", "request_type"] if c in df.columns), None)
    if svc:
        df = df[df[svc].str.lower().str.contains("|".join(kw), na=False)]

    df = df.dropna(subset=[lat_col, lon_col])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                           crs="EPSG:4326").to_crs(METERS_CRS)
    print(f"    -> {len(gdf):,} complaints loaded")
    return gdf


def join_complaints(segments: gpd.GeoDataFrame, complaints_gdf: gpd.GeoDataFrame,
                    buffer_m: int = 15) -> gpd.GeoDataFrame:
    print(f"[5] Spatially joining complaints (buffer={buffer_m}m)...")
    segs_m   = segments.to_crs(METERS_CRS)
    buffered = segs_m[["geometry"]].copy()
    buffered["geometry"] = segs_m.geometry.buffer(buffer_m)
    joined   = gpd.sjoin(buffered, complaints_gdf[["geometry"]], how="left", predicate="contains")
    segs_m["complaint_count"]  = joined.groupby(joined.index).size().reindex(segs_m.index, fill_value=0)
    segments["complaint_count"] = segs_m["complaint_count"].values
    print(f"    -> Avg complaints per segment: {segments['complaint_count'].mean():.2f}")
    return segments
