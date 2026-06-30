"""
backend/routers/metrics.py
GET /api/metrics — retrieve metrics for a completed job.
(Placeholder for async job tracking in future versions.)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Metric thresholds and benchmarks",
    description="Returns benchmark thresholds and descriptions for all quality metrics.",
)
async def get_metric_info() -> dict:
    """Return metric descriptions and benchmark thresholds."""
    return {
        "metrics": {
            "ssim": {
                "name": "Structural Similarity Index",
                "description": "Measures structural similarity between reconstructed and ground-truth tiles.",
                "range": "0.0 – 1.0 (higher is better)",
                "threshold_good": 0.85,
                "unit": "dimensionless",
            },
            "psnr": {
                "name": "Peak Signal-to-Noise Ratio",
                "description": "Ratio of maximum signal to reconstruction noise. Log-scaled.",
                "range": "0 – 60+ dB (higher is better)",
                "threshold_good": 30.0,
                "unit": "dB",
            },
            "sam": {
                "name": "Spectral Angle Mapper",
                "description": "Angle between spectral vectors. Measures spectral fidelity independent of brightness. Critical for NDVI/NDWI preservation.",
                "range": "0 – π/2 radians (lower is better)",
                "threshold_good": 0.10,
                "unit": "radians",
            },
            "ndvi_mae": {
                "name": "NDVI Mean Absolute Error",
                "description": "Mean absolute error in Normalised Difference Vegetation Index on cloud-masked pixels. Directly measures agricultural monitoring accuracy.",
                "range": "0.0 – 2.0 (lower is better)",
                "threshold_good": 0.05,
                "unit": "dimensionless",
            },
        },
        "evaluation_protocol": (
            "All metrics computed exclusively on cloud-masked pixels (where reconstruction occurred). "
            "Clear-sky pixels are excluded to avoid inflating scores."
        ),
    }
