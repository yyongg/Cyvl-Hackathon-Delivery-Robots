"""
Step 2 — Build the base segment GeoDataFrame.

Normalises the pavement layer into a consistent schema (id, geometry,
pavement_score, label) that the rest of the pipeline can rely on.
"""

import geopandas as gpd


def build_segments(pavements: gpd.GeoDataFrame, rollup: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Use pavements_v2 as the primary geometry source (it has the most
    granular condition data).  If it lacks a 'score' column we fall back to
    the rollup_v2 score joined on client_seg_id.

    Returns a GeoDataFrame with at minimum:
        id, geometry, pavement_score, label
    """
    print("[2] Building base segment layer...")

    seg = pavements.copy()

    # ── Normalise the score column ────────────────────────────────────────
    # pavements_v2 uses 'score' per schemas.md; rollup_v2 also has 'score'
    score_candidates = ["score", "condition_score", "pci", "pci_score"]
    score_col = next((c for c in score_candidates if c in seg.columns), None)

    if score_col:
        seg = seg.rename(columns={score_col: "pavement_score"})
        print(f"    Using '{score_col}' as pavement_score")
    else:
        # Fall back: join rollup score on shared geometry or id
        print("    'score' not found in pavements_v2 — attempting join from rollup_v2")
        join_key = next((c for c in ["client_seg_id", "seg_id", "id"] if c in seg.columns and c in rollup.columns), None)
        if join_key:
            seg = seg.merge(
                rollup[[join_key, "score"]].rename(columns={"score": "pavement_score"}),
                on=join_key, how="left"
            )
        else:
            seg["pavement_score"] = 50.0   # neutral default

    # ── Normalise label column ────────────────────────────────────────────
    label_candidates = ["label", "condition", "condition_label", "rating"]
    label_col = next((c for c in label_candidates if c in seg.columns), None)
    if label_col and label_col != "label":
        seg = seg.rename(columns={label_col: "label"})
    elif "label" not in seg.columns:
        seg["label"] = "unknown"

    # ── Assign a stable string ID ─────────────────────────────────────────
    id_candidates = ["client_seg_id", "seg_id", "id", "objectid", "fid"]
    id_col = next((c for c in id_candidates if c in seg.columns), None)
    if id_col:
        seg["id"] = seg[id_col].astype(str)
    else:
        seg["id"] = seg.index.astype(str)

    # Keep only rows with valid geometry
    seg = seg[seg.geometry.notnull() & ~seg.geometry.is_empty].copy()

    print(f"    -> {len(seg):,} segments, pavement_score range: "
          f"{seg['pavement_score'].min():.1f}–{seg['pavement_score'].max():.1f}")
    return seg
