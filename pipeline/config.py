"""
Pipeline configuration.

All tunable constants — data sources, file paths, coordinate systems, and
scoring weights — live here so they can be adjusted in one place.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Data sources
# ─────────────────────────────────────────────────────────────────────────────

# Public S3 bucket for Cyvl hackathon data — no credentials needed.
S3_BASE = "https://cyvl-hackathon.s3.amazonaws.com"

# Local cache directory for downloaded Cyvl GeoJSON layers.
CACHE_DIR = "data/cache"

# Optional local open-data CSVs (improve scoring if present).
COMPLAINTS_CSV = "data/311_complaints.csv"
CRASHES_CSV = "data/vision_zero.csv"

# Local LiDAR point cloud — only segments whose centroid falls inside this
# file's footprint are scored.
LAZ_PATH = "data/merged.laz"

# Pipeline output, consumed by the web frontend.
OUTPUT_PATH = "web/public/scored.geojson"


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate reference systems
# ─────────────────────────────────────────────────────────────────────────────

# Massachusetts State Plane (meters) — used for spatial joins / buffering.
METERS_CRS = "EPSG:26986"

# UTM zone 19N (meters) — used to align segments with the LiDAR point cloud.
UTM_EPSG = 32619


# ─────────────────────────────────────────────────────────────────────────────
# LiDAR extraction parameters
# ─────────────────────────────────────────────────────────────────────────────

# Radius (meters) around a segment centroid to sample points for width/slope.
LIDAR_RADIUS_M = 30

# Target point count after subsampling so the KD-tree builds in seconds.
LIDAR_TARGET_POINTS = 5_000_000


# ─────────────────────────────────────────────────────────────────────────────
# Scoring weights — must sum to 1.0
# ─────────────────────────────────────────────────────────────────────────────

WEIGHTS = {
    "pavement":     0.30,   # Cyvl PCI-style condition score
    "width":        0.25,   # LiDAR-derived sidewalk width
    "slope":        0.15,   # LiDAR-derived grade
    "curb_ramp":    0.15,   # curb ramp presence from aboveGroundAssets
    "obstructions": 0.10,   # manholes/drains in path (proxy for clutter)
    "complaints":   0.05,   # 311 sidewalk complaint density
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"
