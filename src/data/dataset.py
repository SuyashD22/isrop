"""
src/data/dataset.py
PyTorch Dataset for cloud removal training.
Each item: (cloudy_tile, cloud_mask, ref_flat, target_tile)

Loaded from pre-extracted .npy patches saved by PatchExtractor.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class CloudRemovalDataset(Dataset):
    """
    PyTorch Dataset for training the LISSclear model.

    Directory structure expected:
        patches_dir/
            cloudy/       *.npy  — (C, H, W) cloudy input tiles
            cloud_masks/  *.npy  — (H, W) binary cloud masks
            references/   *.npy  — (n_refs, C, H, W) temporal reference stacks
            targets/      *.npy  — (C, H, W) ground-truth cloud-free tiles

    If targets/ is missing (inference-only), __getitem__ returns None for target.
    """

    def __init__(
        self,
        patches_dir: Path,
        split: str = "train",
        train_ratio: float = 0.85,
        augment: bool = True,
        n_refs: int = 3,
    ):
        """
        Args:
            patches_dir:  Root patches directory.
            split:        'train' or 'val'.
            train_ratio:  Fraction of data used for training.
            augment:      Apply random augmentations (train split only).
            n_refs:       Number of reference frames expected in stack.
        """
        self.patches_dir = Path(patches_dir)
        self.cloudy_dir = self.patches_dir / "cloudy"
        self.masks_dir = self.patches_dir / "cloud_masks"
        self.refs_dir = self.patches_dir / "references"
        self.targets_dir = self.patches_dir / "targets"
        self.augment = augment and (split == "train")
        self.n_refs = n_refs

        # Discover all files
        all_files = sorted(self.cloudy_dir.glob("*.npy"))
        if len(all_files) == 0:
            raise RuntimeError(
                f"No .npy patches found in {self.cloudy_dir}. "
                "Run PatchExtractor first."
            )

        n_train = int(len(all_files) * train_ratio)
        if split == "train":
            self.files = all_files[:n_train]
        else:
            self.files = all_files[n_train:]

        # Check which directories exist
        self._has_targets = self.targets_dir.exists()
        self._has_refs = self.refs_dir.exists()

        logger.info(
            "Dataset [%s]: %d patches | targets=%s | refs=%s | augment=%s",
            split, len(self.files), self._has_targets, self._has_refs, self.augment,
        )

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, ...]:
        stem = self.files[idx].stem

        # ── Load arrays ───────────────────────────────────────────────────────
        cloudy: np.ndarray = np.load(self.cloudy_dir / f"{stem}.npy")  # (C, H, W)
        mask: np.ndarray = np.load(self.masks_dir / f"{stem}.npy")     # (H, W)

        # Reference stack: (n_refs, C, H, W) → flatten to (n_refs*C, H, W)
        if self._has_refs:
            ref_stack: np.ndarray = np.load(self.refs_dir / f"{stem}.npy")
            if ref_stack.ndim == 4:
                n, C, H, W = ref_stack.shape
                ref_flat = ref_stack.reshape(n * C, H, W)
            else:
                ref_flat = ref_stack  # already flat
        else:
            # Dummy zeros if no reference stack available
            C, H, W = cloudy.shape
            ref_flat = np.zeros((self.n_refs * C, H, W), dtype=np.float32)

        # Target (ground truth cloud-free)
        if self._has_targets:
            target: np.ndarray = np.load(self.targets_dir / f"{stem}.npy")  # (C, H, W)
        else:
            target = np.zeros_like(cloudy)

        # ── Augmentations ─────────────────────────────────────────────────────
        if self.augment:
            cloudy, mask, ref_flat, target = self._augment(cloudy, mask, ref_flat, target)

        # ── Convert to tensors ────────────────────────────────────────────────
        return (
            torch.from_numpy(np.ascontiguousarray(cloudy)).float(),
            torch.from_numpy(np.ascontiguousarray(mask)).float().unsqueeze(0),  # (1, H, W)
            torch.from_numpy(np.ascontiguousarray(ref_flat)).float(),
            torch.from_numpy(np.ascontiguousarray(target)).float(),
        )

    def _augment(
        self,
        cloudy: np.ndarray,
        mask: np.ndarray,
        ref_flat: np.ndarray,
        target: np.ndarray,
    ) -> Tuple[np.ndarray, ...]:
        """Consistent random flips + 90° rotations across all inputs."""
        # Random horizontal flip
        if np.random.random() > 0.5:
            cloudy = np.flip(cloudy, axis=2).copy()
            mask = np.flip(mask, axis=1).copy()
            target = np.flip(target, axis=2).copy()
            # Flip each reference frame
            C = cloudy.shape[0]
            ref_flat = np.flip(ref_flat, axis=2).copy()

        # Random vertical flip
        if np.random.random() > 0.5:
            cloudy = np.flip(cloudy, axis=1).copy()
            mask = np.flip(mask, axis=0).copy()
            target = np.flip(target, axis=1).copy()
            ref_flat = np.flip(ref_flat, axis=1).copy()

        # Random 90° rotation (k=0,1,2,3)
        k = np.random.randint(0, 4)
        if k > 0:
            cloudy = np.rot90(cloudy, k, axes=(1, 2)).copy()
            mask = np.rot90(mask, k, axes=(0, 1)).copy()
            target = np.rot90(target, k, axes=(1, 2)).copy()
            ref_flat = np.rot90(ref_flat, k, axes=(1, 2)).copy()

        return cloudy, mask, ref_flat, target

    @staticmethod
    def collate_fn(batch):
        """Custom collate for DataLoader."""
        cloudys, masks, refs, targets = zip(*batch)
        return (
            torch.stack(cloudys),
            torch.stack(masks),
            torch.stack(refs),
            torch.stack(targets),
        )
