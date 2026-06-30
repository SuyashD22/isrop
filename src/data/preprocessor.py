"""
src/data/preprocessor.py
Rasterio-based pipeline for loading, normalising, and co-registering
LISS-IV and Sentinel-2 GeoTIFF tiles.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject

logger = logging.getLogger(__name__)


class SatellitePreprocessor:
    """
    Loads GeoTIFF tiles, normalises bands to [0, 1], and optionally
    co-registers multiple scenes to a common reference grid.

    Supports LISS-IV (4-band) and Sentinel-2 (multi-band, L2A).
    """

    # Sentinel-2 L2A surface reflectance scale factor (DN → reflectance)
    S2_SCALE = 10_000.0
    # LISS-IV typical DN range (varies by gain setting)
    LISS4_SCALE = 1024.0

    def __init__(self, target_size: int = 256):
        self.target_size = target_size

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_tile(
        self,
        path: Path,
        bands: List[int] = None,
        sensor: str = "sentinel2",
    ) -> Tuple[np.ndarray, dict]:
        """
        Load a GeoTIFF and return a normalised (C, H, W) float32 array.

        Args:
            path:   Path to GeoTIFF file.
            bands:  1-indexed band indices to read. None = all bands.
            sensor: 'sentinel2' | 'liss4' — sets the DN scale factor.

        Returns:
            data:    (C, H, W) float32 in [0, 1]
            profile: rasterio profile dict (CRS, transform, etc.)
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Tile not found: {path}")

        with rasterio.open(path) as src:
            band_indices = bands if bands else list(range(1, src.count + 1))
            data = src.read(band_indices).astype(np.float32)
            profile = src.profile.copy()

        scale = self.S2_SCALE if sensor == "sentinel2" else self.LISS4_SCALE
        data = np.clip(data / scale, 0.0, 1.0)

        logger.debug(
            "Loaded %s | bands=%s | shape=%s | sensor=%s",
            path.name, band_indices, data.shape, sensor,
        )
        return data, profile

    def load_band(self, path: Path, band_idx: int) -> np.ndarray:
        """Load a single band as (H, W) float32."""
        with rasterio.open(path) as src:
            data = src.read(band_idx).astype(np.float32)
        return data

    # ── Resizing ──────────────────────────────────────────────────────────────

    def resize_tile(
        self,
        tile: np.ndarray,
        size: Optional[int] = None,
        interpolation: int = cv2.INTER_LINEAR,
    ) -> np.ndarray:
        """
        Resize (C, H, W) to (C, size, size).
        Defaults to self.target_size if size not provided.
        """
        size = size or self.target_size
        return np.stack(
            [cv2.resize(tile[c], (size, size), interpolation=interpolation)
             for c in range(tile.shape[0])]
        )

    # ── Normalisation ─────────────────────────────────────────────────────────

    def normalize_percentile(
        self,
        tile: np.ndarray,
        low: float = 2.0,
        high: float = 98.0,
    ) -> np.ndarray:
        """
        Per-band percentile stretch to [0, 1].
        Improves visual quality — use for display, NOT training.
        """
        out = np.zeros_like(tile)
        for c in range(tile.shape[0]):
            lo = np.percentile(tile[c], low)
            hi = np.percentile(tile[c], high)
            out[c] = np.clip((tile[c] - lo) / (hi - lo + 1e-8), 0.0, 1.0)
        return out

    def normalize_minmax(self, tile: np.ndarray) -> np.ndarray:
        """Global min-max normalisation across all bands."""
        mn, mx = tile.min(), tile.max()
        return (tile - mn) / (mx - mn + 1e-8)

    def to_model_range(self, tile: np.ndarray) -> np.ndarray:
        """Convert [0, 1] → [-1, 1] for diffusion model input."""
        return tile * 2.0 - 1.0

    def from_model_range(self, tile: np.ndarray) -> np.ndarray:
        """Convert [-1, 1] → [0, 1]."""
        return (tile + 1.0) / 2.0

    # ── Co-registration ───────────────────────────────────────────────────────

    def coregister(
        self,
        source_path: Path,
        reference_path: Path,
        output_path: Path,
    ) -> None:
        """
        Reproject source GeoTIFF to match reference CRS and grid.
        Uses bilinear resampling. Required when mixing Sentinel-2 + LISS-IV tiles.
        """
        with rasterio.open(reference_path) as ref:
            ref_crs = ref.crs
            ref_transform = ref.transform
            ref_width = ref.width
            ref_height = ref.height

        with rasterio.open(source_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, ref_crs, src.width, src.height, *src.bounds
            )
            profile = src.profile.copy()
            profile.update(
                crs=ref_crs,
                transform=ref_transform,
                width=ref_width,
                height=ref_height,
            )

            with rasterio.open(output_path, "w", **profile) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=ref_transform,
                        dst_crs=ref_crs,
                        resampling=Resampling.bilinear,
                    )
        logger.info("Co-registered %s → %s", source_path.name, output_path.name)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def get_profile(self, path: Path) -> dict:
        """Return rasterio profile without reading data."""
        with rasterio.open(path) as src:
            return src.profile.copy()

    def tile_to_rgb(
        self, tile: np.ndarray, r: int = 0, g: int = 1, b: int = 2
    ) -> np.ndarray:
        """
        Extract RGB preview from multi-band tile.
        Returns (H, W, 3) uint8 for display.
        """
        rgb = np.stack([tile[r], tile[g], tile[b]], axis=-1)
        rgb = np.clip(rgb * 255, 0, 255).astype(np.uint8)
        return rgb
