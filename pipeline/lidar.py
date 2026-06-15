"""
Step 3 — Extract LiDAR width + slope from a local .laz file.

Reads a local point cloud, restricts scoring to segments inside its footprint,
and derives per-segment width, slope, and curb height. No network calls.
"""

import time

import numpy as np
import pandas as pd
import geopandas as gpd

from pipeline.config import LIDAR_RADIUS_M, LIDAR_TARGET_POINTS, UTM_EPSG


def extract_lidar_metrics_local(segments: gpd.GeoDataFrame, laz_path: str) -> gpd.GeoDataFrame:
    """
    Load a local .laz file, find segments whose centroid falls inside it,
    extract width/slope/curb_height, and return ONLY those covered segments.

    No network calls — completes in under a minute.
    """
    import laspy

    print(f"[3] Loading local LiDAR from {laz_path} ...")
    t0  = time.time()
    las = laspy.read(laz_path)
    sx, sy, sz = las.header.scales
    x0, y0, z0 = las.header.offsets
    print(f"    {len(las.points):,} pts loaded in {time.time()-t0:.1f}s")

    # Actual float bounds from the data (header bounds can be stale after merge)
    laz_xmin = float(las.X.min()) * sx + x0
    laz_xmax = float(las.X.max()) * sx + x0
    laz_ymin = float(las.Y.min()) * sy + y0
    laz_ymax = float(las.Y.max()) * sy + y0
    print(f"    Coverage: X[{laz_xmin:.0f}, {laz_xmax:.0f}]  "
          f"Y[{laz_ymin:.0f}, {laz_ymax:.0f}]")

    # Keep only segments whose centroid is inside the LAZ footprint
    seg_utm   = segments.to_crs(f"EPSG:{UTM_EPSG}")
    centroids = seg_utm.geometry.centroid
    inside    = (
        (centroids.x >= laz_xmin) & (centroids.x <= laz_xmax) &
        (centroids.y >= laz_ymin) & (centroids.y <= laz_ymax)
    )
    covered     = segments[inside].copy()
    covered_utm = seg_utm[inside]
    print(f"    {inside.sum()} of {len(segments)} segments inside LAZ footprint")

    if inside.sum() == 0:
        print("    No segments overlap the LAZ file — check LAZ_PATH.")
        return covered  # empty, correct columns

    # Subsample to ~5M points so the KD-tree builds in seconds.
    # Systematic stride keeps spatial coverage uniform; metrics stay accurate
    # because even at 1/44 density a 30 m circle still contains thousands of pts.
    step = max(1, len(las.points) // LIDAR_TARGET_POINTS)
    Xs = np.array(las.X[::step], dtype=np.float64) * sx + x0
    Ys = np.array(las.Y[::step], dtype=np.float64) * sy + y0
    Zs = np.array(las.Z[::step], dtype=np.float64) * sz + z0
    del las
    xyz = np.column_stack([Xs, Ys, Zs])
    del Xs, Ys, Zs
    print(f"    Subsampled to {len(xyz):,} pts (stride {step})")

    # Spatial index for fast radius queries
    try:
        from scipy.spatial import cKDTree
        tree = cKDTree(xyz[:, :2])
        def query_radius(cx, cy):
            return tree.query_ball_point([cx, cy], LIDAR_RADIUS_M)
    except ImportError:
        def query_radius(cx, cy):
            d2 = (xyz[:, 0] - cx) ** 2 + (xyz[:, 1] - cy) ** 2
            return list(np.where(d2 <= LIDAR_RADIUS_M ** 2)[0])

    results = []
    for (_, _row), (_, row_utm) in zip(covered.iterrows(), covered_utm.iterrows()):
        cx, cy = row_utm.geometry.centroid.x, row_utm.geometry.centroid.y
        idx    = query_radius(cx, cy)

        if len(idx) < 20:
            results.append({"width_m": None, "slope_pct": None, "curb_height_m": None})
            continue

        pts      = xyz[idx]
        median_z = float(np.median(pts[:, 2]))
        ground   = pts[np.abs(pts[:, 2] - median_z) < 0.3]

        minx, miny, maxx, maxy = row_utm.geometry.bounds
        dx_m, dy_m = maxx - minx, maxy - miny
        width_m    = min(dx_m, dy_m)

        if len(ground) > 5:
            axis      = ground[:, 1] if dy_m > dx_m else ground[:, 0]
            slope_pct = abs(float(np.polyfit(axis, ground[:, 2], 1)[0])) * 100
        else:
            slope_pct = 0.0

        road_pts      = pts[pts[:, 2] < median_z - 0.05]
        curb_height_m = float(median_z - np.median(road_pts[:, 2])) if len(road_pts) > 5 else None

        results.append({
            "width_m":       round(width_m, 2),
            "slope_pct":     round(slope_pct, 2),
            "curb_height_m": round(curb_height_m, 2) if curb_height_m is not None else None,
        })

    lidar_df = pd.DataFrame(results, index=covered.index)
    covered  = covered.join(lidar_df)
    w_filled = covered["width_m"].notna().sum()
    print(f"    {w_filled}/{len(covered)} segments with LiDAR data  ({time.time()-t0:.1f}s total)")
    return covered
