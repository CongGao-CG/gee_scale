#!/usr/bin/env python3
"""compare_sst.py – Compare OISST SST at a given lon/lat from Earth Engine
and from a locally exported GeoTIFF at the same pixel scale.

Usage
-----
    python compare_sst.py LON LAT SCALE

Arguments
~~~~~~~~~
LON     Longitude in degrees (−180 … 180)
LAT     Latitude  in degrees (−90  …  90)
SCALE   Pixel size in **metres** that matches the GeoTIFF you exported.
        The script expects the file to be named::

            oisst_20200315_s{SCALE/1000}k.tif

        in the current directory (or provide a FULL path via the optional
        ``--file`` flag).

Example
~~~~~~~
    python compare_sst.py 150 20 20000

Dependencies
~~~~~~~~~~~~
* Google Earth Engine Python API  – ``pip install earthengine-api``
* rasterio  – ``pip install rasterio``
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import ee
import numpy as np
import rasterio

# ────────────────────────────────────────────────────────────────────────

def make_default_fname(scale_m: int) -> Path:
    """Return default TIFF name based on *scale_m* (metres)."""
    tag = f"s{scale_m // 1000}k"  # s20k, s250k, …
    return Path(f"oisst_20200315_{tag}.tif")


def ee_sst_value(lon: float, lat: float, scale_m: int) -> float:
    """Fetch SST *100 value from Earth Engine at lon/lat for 2020-03-15."""
    ee.Initialize()
    d0 = ee.Date.fromYMD(2020, 3, 15)
    img = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate(d0, d0.advance(1, "day"))
        .first()
        .select("sst")
    )
    point = ee.Geometry.Point(lon, lat)
    val = (
        img.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=scale_m,
            bestEffort=True,
        )
        .get("sst")
        .getInfo()
    )
    return float(val) if val is not None else np.nan


def tiff_sst_value(path: Path, lon: float, lat: float) -> float:
    """Read SST value from GeoTIFF at lon/lat (nearest pixel)."""
    if not path.exists():
        sys.exit(f"❌  TIFF not found: {path}")
    with rasterio.open(path) as ds:
        if ds.crs.to_epsg() != 4326:
            sys.exit("❌  TIFF CRS is not EPSG:4326 – re-project or adjust code.")
        row, col = ds.index(lon, lat)
        data = ds.read(1)
        val = data[row, col]
        # handle nodata
        nodata = ds.nodata
        if nodata is not None and np.isclose(val, nodata):
            return np.nan
        return float(val)


# ─── CLI ────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare OISST SST value from EE and GeoTIFF.")
    p.add_argument("lon", type=float, help="Longitude in degrees (-180 … 180)")
    p.add_argument("lat", type=float, help="Latitude in degrees (-90 … 90)")
    p.add_argument("scale", type=int, help="Pixel scale in metres")
    p.add_argument("--file", type=Path, default=None,
                   help="Path to GeoTIFF (default based on scale)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    lon, lat, scale_m = args.lon, args.lat, args.scale
    tiff_path = args.file or make_default_fname(scale_m)

    print(f"→ Comparing SST at lon={lon}, lat={lat}, scale={scale_m} m")
    print(f"  GeoTIFF : {tiff_path}\n")

    ee_val = ee_sst_value(lon, lat, scale_m)
    tif_val = tiff_sst_value(tiff_path, lon, lat)

    print("EE  value :", ee_val)
    print("TIFF value:", tif_val)
    if np.isnan(ee_val) or np.isnan(tif_val):
        print("⚠️  One of the values is NaN (nodata).")
    else:
        diff = tif_val - ee_val
        print("Difference (TIFF − EE):", diff)


if __name__ == "__main__":
    main()
