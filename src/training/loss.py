"""
src/training/loss.py
Combined loss function for cloud removal training.

Components:
  L1:          Pixel-level accuracy on cloud-masked pixels
  SSIM:        Structural similarity (global — structure matters beyond cloud region)
  SAM:         Spectral Angle Mapper — preserves band ratios for downstream indices
  Perceptual:  Optional VGG feature matching (improves visual sharpness)

SAM loss is the scientific differentiator. It penalises spectral distortion
independent of pixel intensity, which is essential for preserving NDVI, NDWI,
and other band-ratio vegetation/water indices used in agricultural monitoring.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchmetrics.image import StructuralSimilarityIndexMeasure


class SpectralAngleMapperLoss(nn.Module):
    """
    Differentiable Spectral Angle Mapper (SAM) loss.

    SAM measures the angle between two spectral vectors in N-dimensional band space.
    Zero angle = identical spectral signature. pi/2 = orthogonal (maximum distortion).

    Formula: SAM(x, y) = arccos( (x·y) / (||x|| * ||y||) )

    Range: [0, π/2]. Lower is better.

    This is computed only on cloud-masked pixels (where reconstruction matters).
    """

    def __init__(self, eps: float = 1e-7):
        super().__init__()
        self.eps = eps

    def forward(
        self,
        pred: torch.Tensor,   # (B, C, H, W)
        target: torch.Tensor, # (B, C, H, W)
        mask: Optional[torch.Tensor] = None,  # (B, 1, H, W) or None
    ) -> torch.Tensor:
        """
        Compute mean SAM loss.
        If mask provided, compute only on cloud-covered pixels.
        """
        # Cosine similarity along band (channel) dimension
        cos_sim = F.cosine_similarity(pred, target, dim=1)  # (B, H, W)
        sam = torch.acos(cos_sim.clamp(-1.0 + self.eps, 1.0 - self.eps))  # (B, H, W)

        if mask is not None:
            # Only average over cloud-masked pixels
            mask_2d = mask.squeeze(1)  # (B, H, W)
            if mask_2d.sum() > 0:
                return (sam * mask_2d).sum() / (mask_2d.sum() + self.eps)
            else:
                return sam.mean()  # fallback if mask is empty

        return sam.mean()


class CloudRemovalLoss(nn.Module):
    """
    Combined loss for multi-temporal cloud removal training.

    Total = w_l1 * L1 + w_ssim * (1-SSIM) + w_sam * SAM

    L1 and SAM are computed only on cloud-masked pixels.
    SSIM is computed globally (structural consistency matters everywhere).

    Default weights are tuned for Sentinel-2 4-band imagery.
    Adjust w_sam higher for applications requiring spectral fidelity (agriculture).
    """

    def __init__(
        self,
        w_l1: float = 1.0,
        w_ssim: float = 0.3,
        w_sam: float = 0.1,
        ssim_window_size: int = 11,
    ):
        super().__init__()
        self.w_l1 = w_l1
        self.w_ssim = w_ssim
        self.w_sam = w_sam

        self.sam_loss = SpectralAngleMapperLoss()
        self.ssim_fn = StructuralSimilarityIndexMeasure(
            data_range=1.0,
            kernel_size=ssim_window_size,
        )

    def forward(
        self,
        pred: torch.Tensor,   # (B, C, H, W) model output, [0, 1]
        target: torch.Tensor, # (B, C, H, W) ground truth, [0, 1]
        mask: torch.Tensor,   # (B, 1, H, W) binary — 1=cloud
    ) -> Dict[str, torch.Tensor]:
        """
        Compute combined loss.

        Returns:
            Dict with 'total' (differentiable) and individual components (for logging).
        """
        # Expand mask to all channels for pixel-wise computation
        m = mask.expand_as(pred)

        # ── L1 on masked pixels ────────────────────────────────────────────────
        # Only penalise reconstruction error in cloud-covered regions
        masked_pred = pred * m
        masked_target = target * m
        n_cloud_px = m.sum().clamp(min=1)
        l1 = torch.abs(masked_pred - masked_target).sum() / n_cloud_px

        # ── SSIM on full image ─────────────────────────────────────────────────
        # Global structural similarity — model should not distort clear regions
        ssim_score = self.ssim_fn(pred.float(), target.float())
        ssim_loss = 1.0 - ssim_score

        # ── SAM on masked pixels ───────────────────────────────────────────────
        sam = self.sam_loss(pred, target, mask)

        # ── Total weighted loss ────────────────────────────────────────────────
        total = (
            self.w_l1 * l1
            + self.w_ssim * ssim_loss
            + self.w_sam * sam
        )

        return {
            "total": total,
            "l1": l1.detach().item(),
            "ssim": ssim_loss.detach().item(),
            "sam": sam.detach().item(),
            "ssim_score": ssim_score.detach().item(),
        }

    def __repr__(self) -> str:
        return (
            f"CloudRemovalLoss("
            f"w_l1={self.w_l1}, w_ssim={self.w_ssim}, w_sam={self.w_sam})"
        )
