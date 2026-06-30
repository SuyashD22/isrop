"""
src/utils/image_utils.py
Tensor ↔ PIL ↔ numpy conversions, band utilities, and base64 encoding.
Used by both the training pipeline and the backend API.
"""

from __future__ import annotations

import base64
import io
from typing import List, Optional, Tuple, Union

import numpy as np
import torch
from PIL import Image


class ImageUtils:
    """
    Static utility methods for image format conversions.
    All methods handle (C, H, W) numpy arrays and (B, C, H, W) torch tensors.
    """

    # ── Conversions ───────────────────────────────────────────────────────────

    @staticmethod
    def tensor_to_numpy(t: torch.Tensor) -> np.ndarray:
        """(C, H, W) tensor → (C, H, W) float32 numpy."""
        if t.ndim == 4:
            t = t.squeeze(0)
        return t.detach().cpu().float().numpy()

    @staticmethod
    def numpy_to_tensor(arr: np.ndarray) -> torch.Tensor:
        """(C, H, W) numpy → (C, H, W) float32 tensor."""
        return torch.from_numpy(arr).float()

    @staticmethod
    def numpy_to_pil(arr: np.ndarray, band_indices: List[int] = [0, 1, 2]) -> Image.Image:
        """
        Convert (C, H, W) float32 [0, 1] numpy array to RGB PIL image.

        Args:
            arr:          (C, H, W) float32 in [0, 1].
            band_indices: Which bands to use as R, G, B.
        """
        rgb = np.stack([arr[i] for i in band_indices], axis=-1)
        rgb = np.clip(rgb * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(rgb, mode="RGB")

    @staticmethod
    def pil_to_numpy(img: Image.Image, n_channels: int = 3) -> np.ndarray:
        """PIL image → (C, H, W) float32 [0, 1]."""
        arr = np.array(img).astype(np.float32) / 255.0
        if arr.ndim == 2:
            arr = arr[np.newaxis]  # (1, H, W)
        else:
            arr = arr.transpose(2, 0, 1)  # (H, W, C) → (C, H, W)
        return arr

    @staticmethod
    def pil_to_tensor(img: Image.Image) -> torch.Tensor:
        """PIL → (C, H, W) float32 tensor in [0, 1]."""
        arr = ImageUtils.pil_to_numpy(img)
        return torch.from_numpy(arr).float()

    @staticmethod
    def tensor_to_pil(t: torch.Tensor, band_indices: List[int] = [0, 1, 2]) -> Image.Image:
        """(C, H, W) or (B, C, H, W) tensor → PIL image."""
        arr = ImageUtils.tensor_to_numpy(t)
        return ImageUtils.numpy_to_pil(arr, band_indices)

    # ── Base64 encoding (for API responses) ───────────────────────────────────

    @staticmethod
    def numpy_to_base64_png(
        arr: np.ndarray,
        band_indices: List[int] = [0, 1, 2],
    ) -> str:
        """Encode (C, H, W) float32 array as base64 PNG string."""
        img = ImageUtils.numpy_to_pil(arr, band_indices)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def mask_to_base64_png(mask: np.ndarray) -> str:
        """Encode (H, W) binary mask as base64 PNG."""
        mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
        buf = io.BytesIO()
        mask_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def bytes_to_numpy(
        img_bytes: bytes,
        target_size: Optional[int] = 256,
        n_bands: int = 4,
    ) -> np.ndarray:
        """
        Decode uploaded image bytes to (C, H, W) float32 numpy array.
        Used in backend API for processing uploaded tiles.
        """
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        if target_size:
            img = img.resize((target_size, target_size), Image.BILINEAR)
        arr = np.array(img).astype(np.float32) / 255.0  # (H, W, 3)
        arr = arr.transpose(2, 0, 1)  # (3, H, W)

        # Pad to n_bands by duplicating NIR-like from red channel
        if n_bands > arr.shape[0]:
            pad = np.stack([arr[0]] * (n_bands - arr.shape[0]))
            arr = np.concatenate([arr, pad], axis=0)
        return arr[:n_bands]

    # ── Band utilities ─────────────────────────────────────────────────────────

    @staticmethod
    def compute_ndvi(tile: np.ndarray, red_idx: int = 0, nir_idx: int = 3) -> np.ndarray:
        """Compute NDVI from (C, H, W) tile. Returns (H, W) float32."""
        red = tile[red_idx]
        nir = tile[nir_idx]
        return (nir - red) / (nir + red + 1e-8)

    @staticmethod
    def compute_ndwi(tile: np.ndarray, green_idx: int = 1, nir_idx: int = 3) -> np.ndarray:
        """Compute NDWI (water index) from (C, H, W) tile."""
        green = tile[green_idx]
        nir = tile[nir_idx]
        return (green - nir) / (green + nir + 1e-8)

    @staticmethod
    def percentile_clip(arr: np.ndarray, low: float = 2, high: float = 98) -> np.ndarray:
        """Per-band percentile stretch for display."""
        out = np.zeros_like(arr)
        for c in range(arr.shape[0]):
            lo = np.percentile(arr[c], low)
            hi = np.percentile(arr[c], high)
            out[c] = np.clip((arr[c] - lo) / (hi - lo + 1e-8), 0, 1)
        return out
