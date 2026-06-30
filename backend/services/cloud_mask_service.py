"""
backend/services/cloud_mask_service.py
Cloud mask generation service for the API.
Wraps the src/data/CloudMasker for use in the inference pipeline.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[2]))

logger = logging.getLogger(__name__)


class CloudMaskService:
    """
    Generates binary cloud masks from uploaded tiles.
    Falls back through: NDSI → Brightness if bands are insufficient.
    """

    def __init__(self, dilation_px: int = 5):
        try:
            from src.data.cloud_masker import CloudMasker
            self.masker = CloudMasker(dilation_px=dilation_px)
        except ImportError:
            logger.warning("CloudMasker not available — using brightness fallback.")
            self.masker = None

    def generate_mask(
        self,
        tile: np.ndarray,   # (C, H, W) float32 [0, 1]
        method: str = "auto",
    ) -> np.ndarray:
        """
        Generate binary cloud mask.

        Args:
            tile:   (C, H, W) float32 satellite tile in [0, 1].
            method: 'auto' | 'ndsi' | 'brightness'.

        Returns:
            (H, W) uint8 — 1=cloud, 0=clear.
        """
        if self.masker is None:
            return self._brightness_fallback(tile)

        if method == "brightness":
            return self.masker.from_brightness(tile)
        elif method == "ndsi" and tile.shape[0] >= 4:
            return self.masker.from_ndsi_tile(tile)
        else:
            return self.masker.from_tile(tile)

    @staticmethod
    def _brightness_fallback(tile: np.ndarray, threshold: float = 0.80) -> np.ndarray:
        """Minimal brightness-based cloud mask."""
        import cv2
        mean = tile.mean(axis=0)
        mask = (mean > threshold).astype(np.uint8)
        kernel = np.ones((5, 5), np.uint8)
        return cv2.dilate(mask, kernel, iterations=2)
