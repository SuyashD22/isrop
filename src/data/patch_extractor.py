"""
src/data/patch_extractor.py
Sliding window extraction of 256×256 patches from large GeoTIFF tiles.
Filters patches by cloud coverage, saves as .npy files for fast loading.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from tqdm import tqdm

from .preprocessor import SatellitePreprocessor
from .cloud_masker import CloudMasker

logger = logging.getLogger(__name__)


class PatchExtractor:
    """
    Extracts 256×256 patches from satellite tiles using a sliding window.

    Each patch is saved as a .npy file in:
        patches/cloudy/     — the cloudy target patch
        patches/cloud_masks/— binary cloud mask
        patches/targets/    — cloud-free reference (if available)
        patches/references/ — temporal reference stack

    Metadata (geo-coordinates, dates, cloud%) is saved to metadata.json.
    """

    def __init__(
        self,
        patch_size: int = 256,
        stride: int = 128,
        min_cloud_coverage: float = 0.15,
        max_cloud_coverage: float = 0.90,
        output_dir: Path = Path("data/processed/patches"),
    ):
        self.patch_size = patch_size
        self.stride = stride
        self.min_cloud = min_cloud_coverage
        self.max_cloud = max_cloud_coverage
        self.output_dir = Path(output_dir)
        self.preprocessor = SatellitePreprocessor(target_size=patch_size)
        self.masker = CloudMasker()

        # Create output subdirectories
        for subdir in ["cloudy", "cloud_masks", "references", "targets"]:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)

    def extract_from_tile(
        self,
        tile_path: Path,
        tile_id: str,
        scl_path: Optional[Path] = None,
        target_path: Optional[Path] = None,
        sensor: str = "sentinel2",
        bands: List[int] = None,
        date_str: str = "",
    ) -> List[str]:
        """
        Extract all valid patches from a single tile.

        Args:
            tile_path:   Path to cloudy input GeoTIFF.
            tile_id:     Unique identifier for this tile (e.g. 'S2_20230715_T43RGP').
            scl_path:    Path to SCL band for accurate cloud masking.
            target_path: Path to corresponding cloud-free GeoTIFF (for training pairs).
            sensor:      'sentinel2' or 'liss4'.
            bands:       Band indices to read (1-indexed). None = default.
            date_str:    Acquisition date string 'YYYY-MM-DD'.

        Returns:
            List of patch stem names that were saved.
        """
        default_bands = [4, 3, 2, 8] if sensor == "sentinel2" else [3, 2, 1, 4]
        bands = bands or default_bands

        tile, profile = self.preprocessor.load_tile(tile_path, bands=bands, sensor=sensor)
        _, H, W = tile.shape

        # Generate cloud mask for the full tile
        cloud_mask = self.masker.from_tile(tile, scl_path)

        # Load target if provided
        target_tile = None
        if target_path and Path(target_path).exists():
            target_tile, _ = self.preprocessor.load_tile(target_path, bands=bands, sensor=sensor)

        saved_stems = []
        patch_idx = 0

        for y in range(0, H - self.patch_size + 1, self.stride):
            for x in range(0, W - self.patch_size + 1, self.stride):
                # Extract patch
                cloudy_patch = tile[:, y:y+self.patch_size, x:x+self.patch_size]
                mask_patch = cloud_mask[y:y+self.patch_size, x:x+self.patch_size]

                # Filter by cloud coverage
                coverage = self.masker.coverage(mask_patch)
                if coverage < self.min_cloud or coverage > self.max_cloud:
                    patch_idx += 1
                    continue

                stem = f"{tile_id}_p{patch_idx:04d}"

                # Save cloudy patch
                np.save(self.output_dir / "cloudy" / f"{stem}.npy", cloudy_patch)
                # Save cloud mask
                np.save(self.output_dir / "cloud_masks" / f"{stem}.npy", mask_patch)

                # Save target if available
                if target_tile is not None:
                    tgt_patch = target_tile[:, y:y+self.patch_size, x:x+self.patch_size]
                    np.save(self.output_dir / "targets" / f"{stem}.npy", tgt_patch)

                saved_stems.append(stem)
                patch_idx += 1

        logger.info(
            "Extracted %d patches from %s (cloud %.0f–%.0f%%)",
            len(saved_stems), tile_path.name,
            self.min_cloud * 100, self.max_cloud * 100,
        )
        return saved_stems

    def build_metadata(self, stems: List[str], extra: Dict = None) -> None:
        """Update metadata.json with patch info."""
        meta_path = self.output_dir.parent / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                metadata = json.load(f)
        else:
            metadata = {"patches": []}

        for stem in stems:
            entry = {"stem": stem}
            if extra:
                entry.update(extra)
            metadata["patches"].append(entry)

        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def extract_clear_patches(
        self,
        tile_path: Path,
        tile_id: str,
        target_stem: str,
        scl_path: Optional[Path] = None,
        sensor: str = "sentinel2",
        bands: List[int] = None,
    ) -> Optional[np.ndarray]:
        """
        Extract patches from a cloud-free tile to serve as reference frames.
        Returns the patch at the same position as target_stem, or None if too cloudy.
        """
        default_bands = [4, 3, 2, 8] if sensor == "sentinel2" else [3, 2, 1, 4]
        bands = bands or default_bands

        tile, _ = self.preprocessor.load_tile(tile_path, bands=bands, sensor=sensor)
        mask = self.masker.from_tile(tile, scl_path)

        if not self.masker.is_clear_enough(mask):
            return None

        # Parse patch position from stem
        parts = target_stem.rsplit("_p", 1)
        if len(parts) != 2:
            return None

        patch_idx = int(parts[1])
        _, H, W = tile.shape
        positions = [
            (y, x)
            for y in range(0, H - self.patch_size + 1, self.stride)
            for x in range(0, W - self.patch_size + 1, self.stride)
        ]
        if patch_idx >= len(positions):
            return None

        y, x = positions[patch_idx]
        return tile[:, y:y+self.patch_size, x:x+self.patch_size]
