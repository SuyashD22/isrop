"""
src/training/augmentations.py
Data augmentations for satellite imagery cloud removal training.

Augmentations must be applied consistently to ALL inputs:
  cloudy_tile, cloud_mask, ref_stack, target_tile

Includes:
  - Geometric: horizontal flip, vertical flip, 90° rotations
  - Spectral: brightness/contrast jitter (applied to cloudy + refs, NOT target)
  - Noise:    Gaussian noise injection (simulates sensor noise)
"""

from __future__ import annotations

import random
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn


class SpectralAugmentation(nn.Module):
    """
    Spectral jitter augmentation for satellite imagery.

    Perturbs brightness, contrast, and adds band-correlated noise.
    Applied only to the cloudy INPUT and reference frames, NOT to the target.
    This teaches the model to be robust to sensor calibration differences
    across dates (seasonal illumination changes, atmospheric variation).
    """

    def __init__(
        self,
        brightness_range: Tuple[float, float] = (0.85, 1.15),
        contrast_range: Tuple[float, float] = (0.90, 1.10),
        noise_std: float = 0.02,
        p: float = 0.5,
    ):
        """
        Args:
            brightness_range: Multiplicative brightness perturbation range.
            contrast_range:   Multiplicative contrast perturbation range.
            noise_std:        Standard deviation of additive Gaussian noise.
            p:                Probability of applying augmentation.
        """
        super().__init__()
        self.brightness_range = brightness_range
        self.contrast_range = contrast_range
        self.noise_std = noise_std
        self.p = p

    def forward(self, tile: torch.Tensor) -> torch.Tensor:
        """
        Apply spectral jitter to a single tile tensor.

        Args:
            tile: (C, H, W) or (B, C, H, W) float32 in [0, 1].

        Returns:
            Augmented tile, same shape, clipped to [0, 1].
        """
        if random.random() > self.p:
            return tile

        # Brightness scaling
        alpha = random.uniform(*self.brightness_range)
        tile = tile * alpha

        # Contrast scaling (around mean)
        beta = random.uniform(*self.contrast_range)
        mean = tile.mean()
        tile = (tile - mean) * beta + mean

        # Additive Gaussian noise
        if self.noise_std > 0:
            noise = torch.randn_like(tile) * self.noise_std
            tile = tile + noise

        return torch.clamp(tile, 0.0, 1.0)


class GeometricAugmentation:
    """
    Consistent geometric augmentations applied to all inputs simultaneously.
    Uses numpy for deterministic application across cloudy/mask/refs/target.
    """

    def __init__(
        self,
        flip_h: float = 0.5,
        flip_v: float = 0.5,
        rotate90: float = 0.5,
    ):
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.rotate90 = rotate90

    def __call__(
        self,
        cloudy: np.ndarray,    # (C, H, W)
        mask: np.ndarray,      # (H, W)
        ref_flat: np.ndarray,  # (n_refs*C, H, W)
        target: np.ndarray,    # (C, H, W)
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:

        # Horizontal flip (along W axis)
        if random.random() < self.flip_h:
            cloudy = np.flip(cloudy, axis=2).copy()
            mask = np.flip(mask, axis=1).copy()
            ref_flat = np.flip(ref_flat, axis=2).copy()
            target = np.flip(target, axis=2).copy()

        # Vertical flip (along H axis)
        if random.random() < self.flip_v:
            cloudy = np.flip(cloudy, axis=1).copy()
            mask = np.flip(mask, axis=0).copy()
            ref_flat = np.flip(ref_flat, axis=1).copy()
            target = np.flip(target, axis=1).copy()

        # Random 90° rotation
        if random.random() < self.rotate90:
            k = random.randint(1, 3)
            cloudy = np.rot90(cloudy, k, axes=(1, 2)).copy()
            mask = np.rot90(mask, k, axes=(0, 1)).copy()
            ref_flat = np.rot90(ref_flat, k, axes=(1, 2)).copy()
            target = np.rot90(target, k, axes=(1, 2)).copy()

        return cloudy, mask, ref_flat, target


class CloudSimulationAugmentation:
    """
    Synthetic cloud injection for data augmentation.
    Generates synthetic cloud patches using Perlin-noise-like patterns.
    Allows training on clear-sky pairs by synthetically adding clouds.

    Usage:
        aug = CloudSimulationAugmentation()
        cloudy_synth, mask_synth = aug(clear_tile)
        # Train model to recover clear_tile from cloudy_synth
    """

    def __init__(
        self,
        min_coverage: float = 0.15,
        max_coverage: float = 0.75,
        cloud_brightness: float = 0.85,
    ):
        self.min_coverage = min_coverage
        self.max_coverage = max_coverage
        self.cloud_brightness = cloud_brightness

    def __call__(
        self,
        clear_tile: np.ndarray,  # (C, H, W)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns:
            cloudy_tile: (C, H, W) with synthetic cloud patches
            cloud_mask:  (H, W) binary mask
        """
        C, H, W = clear_tile.shape

        # Generate cloud mask using random ellipses (simple but effective)
        mask = np.zeros((H, W), dtype=np.uint8)
        n_blobs = random.randint(1, 5)
        for _ in range(n_blobs):
            cy, cx = random.randint(0, H), random.randint(0, W)
            ry = random.randint(H // 8, H // 3)
            rx = random.randint(W // 8, W // 3)
            yy, xx = np.ogrid[:H, :W]
            ellipse = ((yy - cy) ** 2 / ry ** 2 + (xx - cx) ** 2 / rx ** 2) <= 1.0
            mask[ellipse] = 1

        # Soft cloud: bright overlay on masked region
        cloudy_tile = clear_tile.copy()
        for c in range(C):
            cloudy_tile[c][mask == 1] = (
                cloudy_tile[c][mask == 1] * 0.3 + self.cloud_brightness * 0.7
            )
            cloudy_tile[c] = np.clip(cloudy_tile[c], 0, 1)

        return cloudy_tile, mask
