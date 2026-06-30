"""
src/data/temporal_stacker.py
Builds multi-date reference stacks — the core novelty of LISSclear.

For each cloudy target patch, selects N cloud-free tiles from the same
geographic location at different acquisition dates, then assembles them
into a temporal reference stack for conditioning the diffusion model.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .preprocessor import SatellitePreprocessor
from .cloud_masker import CloudMasker

logger = logging.getLogger(__name__)


class TemporalStacker:
    """
    Builds multi-date reference stacks for temporal conditioning.

    Workflow:
    1. For a given geographic tile location, collect all available dates.
    2. Filter dates with low cloud coverage (< max_cloud_coverage).
    3. Select the N closest-in-time cloud-free dates relative to target.
    4. Stack: [target_tile, ref1, ref2, ..., refN]  →  (1+N, C, H, W)

    The temporal conditioning stack is the key architectural differentiator —
    standard inpainting sees only the masked image. LISSclear sees a stack of
    historical clear-sky observations from the same location.
    """

    def __init__(
        self,
        n_refs: int = 3,
        max_cloud_coverage: float = 0.05,
        prefer_recent: bool = True,
    ):
        """
        Args:
            n_refs:              Number of reference frames to include.
            max_cloud_coverage:  Maximum cloud % for a tile to qualify as reference.
            prefer_recent:       If True, prefer most recent clear tiles as references.
        """
        self.n_refs = n_refs
        self.max_cloud = max_cloud_coverage
        self.prefer_recent = prefer_recent
        self.preprocessor = SatellitePreprocessor()
        self.masker = CloudMasker()

    def build_stack(
        self,
        target_tile: np.ndarray,
        candidate_paths: List[Path],
        scl_paths: Optional[List[Path]] = None,
        sensor: str = "sentinel2",
        bands: List[int] = None,
    ) -> np.ndarray:
        """
        Build temporal reference stack for a target patch.

        Args:
            target_tile:      (C, H, W) float32 — the cloudy target patch.
            candidate_paths:  List of tile paths from the same location, other dates.
                              Should be ordered chronologically (newest last).
            scl_paths:        Parallel list of SCL paths for cloud masking candidates.
            sensor:           'sentinel2' or 'liss4'.
            bands:            Band indices (1-indexed).

        Returns:
            (1 + n_refs, C, H, W) numpy array.
            [0] = target_tile, [1..n_refs] = cloud-free references.
            Zero-padded if fewer than n_refs clear candidates found.
        """
        default_bands = [4, 3, 2, 8] if sensor == "sentinel2" else [3, 2, 1, 4]
        bands = bands or default_bands
        C, H, W = target_tile.shape

        cloud_free_refs: List[np.ndarray] = []
        candidates = list(reversed(candidate_paths)) if self.prefer_recent else candidate_paths

        for i, path in enumerate(candidates):
            if len(cloud_free_refs) >= self.n_refs:
                break

            try:
                tile, _ = self.preprocessor.load_tile(path, bands=bands, sensor=sensor)
            except Exception as e:
                logger.warning("Could not load candidate %s: %s", path, e)
                continue

            # Resize to match target spatial dimensions
            if tile.shape[1:] != (H, W):
                tile = self.preprocessor.resize_tile(tile, size=H)

            # Get cloud mask for this candidate
            scl_path = scl_paths[i] if (scl_paths and i < len(scl_paths)) else None
            mask = self.masker.from_tile(tile, scl_path)

            if self.masker.is_clear_enough(mask, threshold=self.max_cloud):
                cloud_free_refs.append(tile)
                logger.debug(
                    "Added reference %d: %s (cloud=%.1f%%)",
                    len(cloud_free_refs), path.name, mask.mean() * 100,
                )
            else:
                logger.debug(
                    "Skipped %s — too cloudy (%.1f%%)", path.name, mask.mean() * 100
                )

        # Zero-pad if not enough clear references found
        while len(cloud_free_refs) < self.n_refs:
            cloud_free_refs.append(np.zeros_like(target_tile))
            logger.debug("Padded reference stack with zeros (insufficient clear dates).")

        # Stack: target + references
        stack = np.concatenate(
            [target_tile[np.newaxis], np.array(cloud_free_refs)], axis=0
        )
        # Shape: (1 + n_refs, C, H, W)
        assert stack.shape == (1 + self.n_refs, C, H, W), \
            f"Stack shape mismatch: {stack.shape}"

        return stack

    def build_from_preloaded(
        self,
        target_patch: np.ndarray,
        reference_patches: List[np.ndarray],
    ) -> np.ndarray:
        """
        Build stack from already-loaded numpy arrays (used at inference time).

        Args:
            target_patch:      (C, H, W) float32.
            reference_patches: List of (C, H, W) float32 — already cloud-free.

        Returns:
            (1 + n_refs, C, H, W) numpy array.
        """
        refs = reference_patches[:self.n_refs]
        while len(refs) < self.n_refs:
            refs.append(np.zeros_like(target_patch))

        return np.concatenate(
            [target_patch[np.newaxis], np.array(refs)], axis=0
        )

    def flatten_refs(self, stack: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Split stack into (target, ref_flat) where ref_flat has shape (n_refs*C, H, W).
        This is the format expected by the model.
        """
        target = stack[0]  # (C, H, W)
        refs = stack[1:]   # (n_refs, C, H, W)
        n, C, H, W = refs.shape
        ref_flat = refs.reshape(n * C, H, W)  # (n_refs*C, H, W)
        return target, ref_flat

    def save_reference_stack(
        self,
        stack: np.ndarray,
        output_path: Path,
    ) -> None:
        """Save a reference stack as .npy file."""
        np.save(output_path, stack)

    def load_reference_stack(self, path: Path) -> np.ndarray:
        """Load a saved reference stack."""
        return np.load(path)
