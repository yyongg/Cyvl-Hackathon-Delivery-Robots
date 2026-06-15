"""
Step 6 — Scoring.

Normalises each raw metric to a 0–100 sub-score, combines them into a weighted
composite, and buckets segments into red / yellow / green feasibility tiers.
"""

import numpy as np
import pandas as pd
import geopandas as gpd

from pipeline.config import WEIGHTS


def normalize_pavement(score) -> float:
    """
    pavements_v2 'score' is already 0–100 per Cyvl's PCI-style scale.
    100 = perfect surface, 0 = failed.  Pass through directly.
    """
    if score is None or (isinstance(score, float) and np.isnan(score)):
        return 50.0
    return float(np.clip(score, 0, 100))


def normalize_width(width_m) -> float:
    """
    < 0.7m  -> 0   (too narrow)
    0.7–2.0 -> 0–100 (linear)
    > 2.0m  -> 100
    """
    if width_m is None or np.isnan(float(width_m if width_m is not None else float("nan"))):
        return 50.0   # neutral when LiDAR not available
    w = float(width_m)
    if w < 0.7:
        return 0.0
    return float(min(100, (w - 0.7) / (2.0 - 0.7) * 100))


def normalize_slope(slope_pct) -> float:
    """
    0%   -> 100 (flat = ideal)
    8%   -> ~47 (most robots' limit)
    15%+ -> 0
    """
    if slope_pct is None:
        return 50.0
    return float(max(0, 100 - (float(slope_pct) / 15.0) * 100))


def normalize_curb_ramp(ramp_count) -> float:
    """
    0 ramps -> 0  (no accessible crossing)
    1+      -> 100
    """
    if ramp_count is None:
        return 50.0
    return 100.0 if int(ramp_count) >= 1 else 0.0


def normalize_obstructions(obs_count) -> float:
    """
    0 -> 100, 1 -> 75, 2 -> 50, 3 -> 25, 4+ -> 0
    """
    if obs_count is None:
        return 75.0
    return float(max(0, 100 - int(obs_count) * 25))


def normalize_complaints(complaint_count) -> float:
    """
    0 complaints -> 100, 5 -> 50, 10+ -> 0
    """
    if complaint_count is None:
        return 75.0
    return float(max(0, 100 - int(complaint_count) * 10))


def score_segment(row) -> pd.Series:
    s = {
        "pavement":     normalize_pavement(row.get("pavement_score")),
        "width":        normalize_width(row.get("width_m")),
        "slope":        normalize_slope(row.get("slope_pct")),
        "curb_ramp":    normalize_curb_ramp(row.get("curb_ramp_count")),
        "obstructions": normalize_obstructions(row.get("obstruction_count")),
        "complaints":   normalize_complaints(row.get("complaint_count")),
    }
    composite = sum(s[k] * WEIGHTS[k] for k in WEIGHTS)

    return pd.Series({
        "score_pavement":     round(s["pavement"],     1),
        "score_width":        round(s["width"],        1),
        "score_slope":        round(s["slope"],        1),
        "score_curb_ramp":    round(s["curb_ramp"],    1),
        "score_obstructions": round(s["obstructions"], 1),
        "score_complaints":   round(s["complaints"],   1),
        "composite_score":    round(composite,         1),
    })


def run_scoring(segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("[6] Scoring all segments...")
    scores   = segments.apply(score_segment, axis=1)
    segments = pd.concat([segments, scores], axis=1)

    segments["tier"] = pd.cut(
        segments["composite_score"],
        bins=[0, 40, 70, 100],
        labels=["red", "yellow", "green"],
        include_lowest=True,
    )

    total  = len(segments)
    green  = (segments["tier"] == "green").sum()
    yellow = (segments["tier"] == "yellow").sum()
    red    = (segments["tier"] == "red").sum()

    print(f"    -> Green  (robot-ready):  {green:5d}  ({green/total*100:.1f}%)")
    print(f"    -> Yellow (marginal):     {yellow:5d}  ({yellow/total*100:.1f}%)")
    print(f"    -> Red    (infeasible):   {red:5d}  ({red/total*100:.1f}%)")
    print(f"    -> Mean composite score: {segments['composite_score'].mean():.1f}")
    return segments
