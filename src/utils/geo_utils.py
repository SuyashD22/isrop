"""
src/utils/geo_utils.py
Geospatial utility functions for coordinate transforms,
bounding box operations, and co-registration helpers.
Wraps rasterio and pyproj for common satellite imagery operations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class GeoUtils:
    """
    Geospatial utilities for satellite tile operations.
    All coordinate operations use WGS84 (EPSG:4326) as the canonical CRS.
    """

    # India bounding box (lon_min, lat_min, lon_max, lat_max)
    INDIA_BBOX = (68.17, 8.40, 97.40, 37.60)
    # Monsoon belt (focus area for cloud removal)
    MONSOON_BBOX = (72.0, 16.0, 88.0, 28.0)

    @staticmethod
    def get_tile_bounds(path: Path) -> Tuple[float, float, float, float]:
        """
        Get bounding box of a GeoTIFF tile in WGS84.

        Returns:
            (lon_min, lat_min, lon_max, lat_max)
        """
        import rasterio
        from rasterio.warp import transform_bounds

        with rasterio.open(path) as src:
            bounds = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
        return bounds  # (west, south, east, north)

    @staticmethod
    def get_tile_center(path: Path) -> Tuple[float, float]:
        """Return (lon, lat) center of a GeoTIFF tile."""
        bounds = GeoUtils.get_tile_bounds(path)
        lon = (bounds[0] + bounds[2]) / 2
        lat = (bounds[1] + bounds[3]) / 2
        return lon, lat

    @staticmethod
    def tiles_overlap(path_a: Path, path_b: Path, min_overlap: float = 0.5) -> bool:
        """
        Check if two GeoTIFF tiles have sufficient spatial overlap.
        Required for pairing cloud-free references with target tiles.

        Args:
            min_overlap: Minimum fractional overlap required (0.0–1.0).
        """
        b1 = GeoUtils.get_tile_bounds(path_a)
        b2 = GeoUtils.get_tile_bounds(path_b)

        inter_x = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
        inter_y = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
        inter_area = inter_x * inter_y

        area_a = (b1[2] - b1[0]) * (b1[3] - b1[1])
        area_b = (b2[2] - b2[0]) * (b2[3] - b2[1])

        if area_a == 0 or area_b == 0:
            return False

        overlap = inter_area / min(area_a, area_b)
        return overlap >= min_overlap

    @staticmethod
    def find_matching_tiles(
        target_path: Path,
        candidate_dir: Path,
        pattern: str = "*.tif",
        min_overlap: float = 0.5,
    ) -> List[Path]:
        """
        Find candidate tiles in a directory that spatially overlap with target.
        Used to find cloud-free reference candidates for the same location.

        Args:
            target_path:  The target (cloudy) tile.
            candidate_dir: Directory of candidate clear-sky tiles.
            pattern:      Glob pattern for tile files.
            min_overlap:  Minimum spatial overlap required.

        Returns:
            List of overlapping tile paths, sorted by filename (i.e., date).
        """
        candidates = sorted(Path(candidate_dir).glob(pattern))
        matching = []
        for c in candidates:
            if c == target_path:
                continue
            try:
                if GeoUtils.tiles_overlap(target_path, c, min_overlap):
                    matching.append(c)
            except Exception as e:
                logger.debug("Could not check overlap for %s: %s", c.name, e)

        logger.info(
            "Found %d overlapping tiles in %s", len(matching), candidate_dir
        )
        return matching

    @staticmethod
    def parse_sentinel2_date(filename: str) -> str:
        """
        Extract acquisition date from Sentinel-2 filename.
        Example: S2A_MSIL2A_20230715T050721_... → '2023-07-15'
        """
        parts = filename.split("_")
        for part in parts:
            if len(part) == 15 and part[8] == "T" and part[:8].isdigit():
                return f"{part[:4]}-{part[4:6]}-{part[6:8]}"
        return "unknown"

    @staticmethod
    def latlon_to_pixel(
        lat: float,
        lon: float,
        tile_path: Path,
    ) -> Tuple[int, int]:
        """
        Convert lat/lon coordinate to pixel row/col in a GeoTIFF.
        Useful for querying specific locations in a tile.
        """
        import rasterio
        from rasterio.warp import transform as warp_transform

        with rasterio.open(tile_path) as src:
            xs, ys = warp_transform("EPSG:4326", src.crs, [lon], [lat])
            row, col = src.index(xs[0], ys[0])
        return int(row), int(col)

    @staticmethod
    def bbox_to_wkt(lon_min: float, lat_min: float, lon_max: float, lat_max: float) -> str:
        """Convert bounding box to WKT POLYGON string (for Sentinel API queries)."""
        return (
            f"POLYGON(({lon_min} {lat_min}, {lon_max} {lat_min}, "
            f"{lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))"
        )

    @staticmethod
    def india_monsoon_wkt() -> str:
        """Return WKT polygon for Indian monsoon belt search area."""
        return GeoUtils.bbox_to_wkt(*GeoUtils.MONSOON_BBOX)
