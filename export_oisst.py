#!/usr/bin/env python3
"""export_oisst.py ── Export daily OISST SST to Google Drive at a user-chosen scale.

Usage
-----
    python export_oisst.py SCALE

where *SCALE* is the desired pixel size **in metres** (e.g. 10000, 250000).
The script queues a Drive export named

    oisst_20200315_s{SCALE/1000}k.tif

in the folder `EE_exports` (created if absent).

Dependences: Google Earth Engine Python API (``pip install earthengine-api``).
Ensure you have authenticated EE and enabled Drive access.
"""

from __future__ import annotations

import sys
from datetime import date

import ee

def main(scale_m: int) -> None:
    """Queue an Earth Engine export at *scale_m* metres/pixel."""
    ee.Initialize()

    # ─── date & image (hard-coded: 15 Mar 2020) ──────────────────────────
    d0 = ee.Date.fromYMD(2020, 3, 15)
    img = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate(d0, d0.advance(1, "day"))
        .first()
        .select("sst")
    )

    # ─── explicit, bounded region (-180…180, -90…90) ────────────────────
    bbox = ee.Geometry.Rectangle(
        coords=[-180, -90, 180, 90],
        proj="EPSG:4326",
        geodesic=False,
    )
    img = img.clip(bbox)

    # ─── prepare export ─────────────────────────────────────────────────
    tag = f"s{scale_m // 1000}k"  # e.g. s10k, s250k, s1000k
    name = f"oisst_20200315_{tag}"

    task = ee.batch.Export.image.toDrive(
        image=img,
        description=name,
        folder="EE_exports",
        fileNamePrefix=name,
        region=bbox,
        scale=scale_m,
        crs="EPSG:4326",
        maxPixels=1_000_000_000,
    )
    task.start()

    print(
        f"✓ Started Drive export '{name}'.\n"
        f"  ‣ scale   : {scale_m} m/pixel\n"
        f"  ‣ task id : {task.id}\n"
        f"Check the Earth Engine Tasks panel and wait for COMPLETED."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python export_oisst.py SCALE_in_metres (e.g. 10000)")

    try:
        scale = int(sys.argv[1])
        if scale <= 0:
            raise ValueError
    except ValueError:
        sys.exit("SCALE must be a positive integer (metres per pixel).")

    main(scale)
