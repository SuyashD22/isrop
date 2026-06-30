"""
src/data/cloud_masker.py
Binary cloud mask generation for LISS-IV and Sentinel-2 tiles.
Three methods ordered by accuracy:
  1. SCL band (Sentinel-2 only) — most accurate
  2. NDSI thresholding — good for LISS-IV
  3. Brightness threshold — simplest fallback
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import rasterio

logger = logging.getLogger(__name__)


class CloudMasker:
    """
    Generates binary cloud masks from Sentinel-2 or LISS-IV imagery.

    Mask convention:
        1 = cloud / cloud shadow
        0 = clear sky
    """

    # Sentinel-2 Scene Classification Layer values indicating cloud
    # 8 = cloud medium probability, 9 = cloud high probability, 10 = thin cirrus
    CLOUD_SCL_VALUES = [8, 9, 10]

    # SCL value 3 = cloud shadow — optionally include
    SHADOW_SCL_VALUE = 3

    def __init__(
        self,
        dilation_px: int = 5,
        include_shadows: bool = True,
    ):
        """
        Args:
            dilation_px:      Dilation kernel size to catch cloud edges.
            include_shadows:  Whether to include cloud shadows in mask.
        """
        self.dilation_px = dilation_px
        self.include_shadows = include_shadows
        self._scl_values = list(self.CLOUD_SCL_VALUES)
        if include_shadows:
            self._scl_values.append(self.SHADOW_SCL_VALUE)

    # ── Primary method: Sentinel-2 SCL band ──────────────────────────────────

    def from_scl(self, scl_path: Path) -> np.ndarray:
        """
        Generate mask from Sentinel-2 Scene Classification Layer (SCL).
        Most accurate method — use when SCL band is available.

        Args:
            scl_path: Path to SCL band GeoTIFF (single-band, uint8).

        Returns:
            (H, W) uint8 — 1=cloud/shadow, 0=clear
        """
        with rasterio.open(scl_path) as src:
            scl = src.read(1)

        mask = np.isin(scl, self._scl_values).astype(np.uint8)
        dilated = self._dilate_mask(mask, self.dilation_px)
        logger.debug("SCL mask coverage: %.1f%%", dilated.mean() * 100)
        return dilated

    def from_scl_array(self, scl: np.ndarray) -> np.ndarray:
        """Same as from_scl but accepts numpy array directly."""
        mask = np.isin(scl, self._scl_values).astype(np.uint8)
        return self._dilate_mask(mask, self.dilation_px)

    # ── Fallback: NDSI-based masking ─────────────────────────────────────────

    def from_ndsi(
        self,
        red: np.ndarray,
        nir: np.ndarray,
        threshold: float = 0.10,
    ) -> np.ndarray:
        """
        Normalised Difference Snow/Cloud Index for LISS-IV imagery.
        Clouds and snow appear bright in Red and dark in NIR.

        Args:
            red:       (H, W) float32 Red band in [0, 1].
            nir:       (H, W) float32 NIR band in [0, 1].
            threshold: NDSI value above which pixels are classified as cloud.

        Returns:
            (H, W) uint8 — 1=cloud, 0=clear
        """
        ndsi = (red - nir) / (red + nir + 1e-8)
        mask = (ndsi > threshold).astype(np.uint8)
        return self._dilate_mask(mask, kernel_size=3)

    def from_ndsi_tile(
        self,
        tile: np.ndarray,
        red_idx: int = 0,
        nir_idx: int = 3,
        threshold: float = 0.10,
    ) -> np.ndarray:
        """NDSI mask from (C, H, W) tile array."""
        return self.from_ndsi(tile[red_idx], tile[nir_idx], threshold)

    # ── Fallback: Brightness threshold ────────────────────────────────────────

    def from_brightness(
        self,
        tile: np.ndarray,
        threshold: float = 0.80,
    ) -> np.ndarray:
        """
        Simplest fallback: very bright pixels are likely cloud.
        Uses per-pixel mean across all bands.

        Args:
            tile:      (C, H, W) float32 in [0, 1].
            threshold: Mean brightness above which pixel = cloud.

        Returns:
            (H, W) uint8 — 1=cloud, 0=clear
        """
        mean_brightness = tile.mean(axis=0)
        mask = (mean_brightness > threshold).astype(np.uint8)
        return self._dilate_mask(mask, self.dilation_px)

    # ── Combined approach ─────────────────────────────────────────────────────

    def from_tile(
        self,
        tile: np.ndarray,
        scl_path: Optional[Path] = None,
        red_idx: int = 0,
        nir_idx: int = 3,
    ) -> np.ndarray:
        """
        Auto-select best available method.
        Priority: SCL > NDSI > Brightness.

        Args:
            tile:     (C, H, W) float32.
            scl_path: Path to SCL GeoTIFF — uses SCL if provided.

        Returns:
            (H, W) uint8 mask.
        """
        if scl_path and Path(scl_path).exists():
            return self.from_scl(scl_path)

        if tile.shape[0] >= 4:
            return self.from_ndsi_tile(tile, red_idx, nir_idx)

        return self.from_brightness(tile)

    # ── Statistics ────────────────────────────────────────────────────────────

    def coverage(self, mask: np.ndarray) -> float:
        """Return fraction of pixels classified as cloud (0.0 – 1.0)."""
        return float(mask.mean())

    def is_too_cloudy(self, mask: np.ndarray, threshold: float = 0.90) -> bool:
        return self.coverage(mask) >= threshold

    def is_clear_enough(self, mask: np.ndarray, threshold: float = 0.05) -> bool:
        """True if tile is suitable as a cloud-free reference."""
        return self.coverage(mask) <= threshold

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _dilate_mask(self, mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Dilate mask to include cloud edges (halos)."""
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        return cv2.dilate(mask, kernel, iterations=2)
