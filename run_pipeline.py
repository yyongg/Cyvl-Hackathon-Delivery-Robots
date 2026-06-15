#!/usr/bin/env python
"""
run_pipeline.py
---------------
Delivery Robot Feasibility Map — Somerville, MA

Thin entry point. The pipeline implementation lives in the ``pipeline`` package
(one module per stage); this shim just runs it end-to-end.

Usage:
    pip install -r requirements.txt
    python run_pipeline.py

No credentials required. All Cyvl data is pulled from the public CDN
(~120 MB cached to data/cache on first run) or the public S3 bucket.

Optional open-data inputs (improve scoring if present):
    data/311_complaints.csv   — from data.somervillema.gov
    data/vision_zero.csv      — from data.boston.gov / visionzero.boston.gov
"""

from pipeline.cli import main

if __name__ == "__main__":
    main()
