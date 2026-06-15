"""
Step 4 — Curb ramps + obstructions from aboveGroundAssets_v2.

Spatially joins above-ground assets to segments to count nearby curb ramps
(accessibility) and obstructions (manholes, grates — a proxy for path clutter).
"""

import pandas as pd
import geopandas as gpd

from pipeline.config import METERS_CRS


def join_assets(segments: gpd.GeoDataFrame, assets: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Spatially join aboveGroundAssets_v2 to segments to derive:
        curb_ramp_count   — number of curb ramps within 15 m
        obstruction_count — number of obstructions (manholes, grates) within 5 m

    The 'type' / 'asset_type' column in aboveGroundAssets_v2 carries MUTCD-style
    labels such as 'curb_ramp', 'manhole', 'drain', 'hydrant', etc.
    Check assets.columns on your actual data and adjust type_col if needed.
    """
    print("[4] Joining aboveGroundAssets_v2 to segments...")

    if assets is None or len(assets) == 0:
        print("    No assets loaded — skipping.")
        segments["curb_ramp_count"]   = 0
        segments["obstruction_count"] = 0
        return segments

    # Find the type column
    type_candidates = ["type", "asset_type", "label", "class", "category"]
    type_col = next((c for c in type_candidates if c in assets.columns), None)

    if type_col:
        print(f"    Asset types found ({type_col}):")
        print(f"    {assets[type_col].value_counts().head(10).to_dict()}")

        # Keywords that indicate curb ramps / accessibility features
        ramp_kw = ["curb_ramp", "ramp", "curb ramp", "accessible", "dropped kerb"]
        # Keywords that indicate obstructions / clutter
        obs_kw  = ["manhole", "drain", "grate", "cover", "utility"]

        ramps = assets[assets[type_col].str.lower().str.contains(
            "|".join(ramp_kw), na=False, regex=True)]
        obs   = assets[assets[type_col].str.lower().str.contains(
            "|".join(obs_kw), na=False, regex=True)]
    else:
        print("    No type column found — treating all assets as obstructions.")
        ramps = assets.iloc[0:0]   # empty
        obs   = assets

    # Project to meters for accurate buffer distances
    segs_m  = segments.to_crs(METERS_CRS)
    ramps_m = ramps.to_crs(METERS_CRS) if len(ramps) > 0 else ramps
    obs_m   = obs.to_crs(METERS_CRS)   if len(obs)   > 0 else obs

    def sjoin_count(segs, pts, buf):
        if len(pts) == 0:
            return pd.Series(0, index=segs.index)
        buffered = segs[["geometry"]].copy()
        buffered["geometry"] = segs.geometry.buffer(buf)
        joined = gpd.sjoin(buffered, pts[["geometry"]], how="left", predicate="contains")
        return joined.groupby(joined.index).size().reindex(segs.index, fill_value=0)

    segs_m["curb_ramp_count"]   = sjoin_count(segs_m, ramps_m, 15)
    segs_m["obstruction_count"] = sjoin_count(segs_m, obs_m,    5)

    # Copy results back to WGS84 frame
    segments["curb_ramp_count"]   = segs_m["curb_ramp_count"].values
    segments["obstruction_count"] = segs_m["obstruction_count"].values

    ramp_pct = (segments["curb_ramp_count"] > 0).mean() * 100
    print(f"    -> Curb ramp present near {ramp_pct:.1f}% of segments")
    print(f"    -> Avg obstructions per segment: {segments['obstruction_count'].mean():.2f}")
    return segments
