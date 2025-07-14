#!/usr/bin/env python3
"""export_hycom_temp0.py – Export HYCOM surface water temperature (band
`water_temp_0`) for 15 March 2020 to Google Drive, at a user-supplied
pixel scale.

Usage
-----
    python export_hycom_temp0.py SCALE

Arguments
~~~~~~~~~
SCALE  Pixel size in metres (e.g. 10000, 500000). The script queues an Earth
       Engine export named::

           hycom_temp0_20200315_s{SCALE/1000}k.tif

       in your Drive folder ``EE_exports``.

Prerequisites
~~~~~~~~~~~~~
* Google Earth Engine Python API (``pip install earthengine-api``).
* EE authentication (``earthengine authenticate``) and Drive access enabled.
"""

from __future__ import annotations

import sys
import ee

def main(scale_m: int) -> None:
    ee.Initialize()

    # ─── image for 15 Mar 2020 ───────────────────────────────────────────
    d0 = ee.Date.fromYMD(2020, 3, 15)
    img = (
        ee.ImageCollection("HYCOM/sea_temp_salinity")
        .filterDate(d0, d0.advance(1, "day"))
        .first()
        .select("water_temp_0")
    )

    # ─── bounded global rectangle ───────────────────────────────────────
    bbox = ee.Geometry.Rectangle([-180, -90, 180, 90], "EPSG:4326", False)
    img = img.clip(bbox)

    # ─── export task ────────────────────────────────────────────────────
    tag = f"s{scale_m // 1000}k"
    name = f"hycom_temp0_20200315_{tag}"

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
        "Check the Earth Engine Tasks panel until the job is COMPLETED."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python export_hycom_temp0.py SCALE (metres)")
    try:
        scale = int(sys.argv[1])
        if scale <= 0:
            raise ValueError
    except ValueError:
        sys.exit("SCALE must be a positive integer (metres per pixel).")

    main(scale)
