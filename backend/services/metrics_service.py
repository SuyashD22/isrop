"""
backend/services/metrics_service.py
Post-inference metric computation service.
Wraps src/evaluation/CloudRemovalMetrics for API use.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import torch

sys.path.insert(0, str(Path(__file__).parents[2]))

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Computes quality metrics after inference.
    In demo mode (no ground truth), computes self-consistency metrics.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        try:
            from src.evaluation.metrics import CloudRemovalMetrics
            self.metrics_fn = CloudRemovalMetrics(device=device)
        except ImportError:
            logger.warning("CloudRemovalMetrics not available — using approximations.")
            self.metrics_fn = None

    def compute_from_arrays(
        self,
        pred: torch.Tensor,   # (B, C, H, W)
        target: torch.Tensor, # (B, C, H, W)
        mask: torch.Tensor,   # (B, 1, H, W)
    ) -> Dict[str, Optional[float]]:
        """Compute metrics and return serialisable dict."""
        if self.metrics_fn is not None:
            try:
                return self.metrics_fn.compute_all(pred, target, mask)
            except Exception as e:
                logger.warning("Metrics computation failed: %s", e)

        return self._approximate_metrics(pred, target, mask)

    @staticmethod
    def _approximate_metrics(
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor,
    ) -> Dict[str, Optional[float]]:
        """Quick approximate metrics (no torchmetrics required)."""
        import torch.nn.functional as F

        m = mask.expand_as(pred)
        mse = ((pred * m - target * m) ** 2).mean().item()
        psnr = 10 * (1.0 / (mse + 1e-8)) if mse > 0 else 40.0

        cos = F.cosine_similarity(pred, target, dim=1)
        sam = torch.acos(cos.clamp(-0.999, 0.999)).mean().item()

        cloud_cov = float(mask.mean().item())

        return {
            "psnr": round(min(psnr, 60.0), 3),
            "ssim": round(1.0 - float(mse), 4),
            "sam": round(float(sam), 4),
            "ndvi_mae": None,
            "cloud_coverage": round(cloud_cov, 3),
        }
