#!/usr/bin/env python3
"""
check_tif.py – quick GeoTIFF inspector

Run:
    python check_tif.py path/to/file.tif [--thumb] [--thumb-scale 0.2] [--show]

What it does
------------
1. Prints the raster metadata (driver, size, dtype, CRS, affine transform).
2. Computes and prints basic statistics (min, max, mean, std dev).
3. Saves a PNG thumbnail (default: 20 % of original size) next to the input
   file – unless you pass ``--no-thumb``.
4. Optionally displays the full-resolution raster with matplotlib
   (``--show``).

Dependencies: ``rasterio`` and ``matplotlib``.
Install with::

    pip install rasterio matplotlib

"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None  # only needed when --show or when saving thumbnail


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect a GeoTIFF.")
    p.add_argument("tif", type=Path, help="Path to the GeoTIFF file")

    g = p.add_mutually_exclusive_group()
    g.add_argument("--thumb",  dest="thumb", action="store_true",
                   help="Save PNG thumbnail (default)")
    g.add_argument("--no-thumb", dest="thumb", action="store_false",
                   help="Skip creating thumbnail")
    p.set_defaults(thumb=True)

    p.add_argument("--thumb-scale", type=float, default=0.2,
                   metavar="FRACTION",
                   help="Scale factor for thumbnail (0‒1, default 0.2)")
    p.add_argument("--show", action="store_true",
                   help="Display the image with matplotlib")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    path: Path = args.tif.expanduser().resolve()

    if not path.exists():
        raise SystemExit(f"❌  File not found: {path}")

    with rasterio.open(path) as ds:
        print("\n— Metadata —")
        profile = ds.profile.copy()
        for k in (
            "driver", "dtype", "width", "height", "count",
            "crs", "transform"):
            print(f"{k:>10}: {profile.get(k)}")

        # read first band as masked array
        data = ds.read(1, masked=True)
        stats = {
            "min": np.nanmin(data),
            "max": np.nanmax(data),
            "mean": np.nanmean(data),
            "std": np.nanstd(data),
        }
        print("\n— Statistics —")
        for k, v in stats.items():
            print(f"{k:>4}: {v:0.3f}")

        # optional thumbnail
        if args.thumb:
            if plt is None:
                print("⚠️  matplotlib not available – cannot save thumbnail")
            else:
                scale = max(min(args.thumb_scale, 1.0), 0.01)
                new_h = int(ds.height * scale)
                new_w = int(ds.width * scale)

                thumb = ds.read(
                    1,
                    out_shape=(1, new_h, new_w),
                    resampling=Resampling.average,
                )
                thumb = np.ma.masked_equal(thumb, ds.nodata) if ds.nodata is not None else thumb

                thumb_path = path.with_suffix("") .with_name(path.stem + "_thumb.png")
                plt.imsave(thumb_path, thumb, cmap="turbo")
                print(f"✓  Thumbnail saved: {thumb_path}")

        # optional interactive display
        if args.show:
            if plt is None:
                print("⚠️  matplotlib not available – cannot display image")
            else:
                plt.figure(figsize=(8, 4))
                plt.imshow(data, cmap="turbo")
                plt.colorbar(label="Value")
                plt.title(path.name)
                plt.axis("off")
                plt.show()


if __name__ == "__main__":
    main()
