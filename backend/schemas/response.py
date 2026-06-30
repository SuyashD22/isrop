"""
backend/schemas/response.py
Pydantic response models for LISSclear API.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class MetricsResult(BaseModel):
    """Quality metrics for a cloud removal result."""
    psnr: float = Field(..., description="Peak Signal-to-Noise Ratio (dB). Higher is better. Threshold: >30.")
    ssim: float = Field(..., description="Structural Similarity Index. Higher is better. Threshold: >0.85.")
    sam: float = Field(..., description="Spectral Angle Mapper (radians). Lower is better. Threshold: <0.10.")
    ndvi_mae: Optional[float] = Field(
        default=None,
        description="NDVI Mean Absolute Error. Lower is better. Threshold: <0.05.",
    )
    cloud_coverage: float = Field(
        ...,
        description="Fraction of pixels classified as cloud (0.0–1.0).",
    )


class InferenceResponse(BaseModel):
    """Response from the /api/remove-clouds endpoint."""
    output_image: str = Field(
        ...,
        description="Cloud-removed output tile as base64 PNG.",
    )
    cloud_mask: str = Field(
        ...,
        description="Binary cloud mask as base64 PNG (white=cloud).",
    )
    metrics: MetricsResult = Field(
        ...,
        description="Quality metrics for the reconstruction.",
    )
    processing_time_ms: int = Field(
        ...,
        description="Total inference time in milliseconds.",
    )
    model_version: str = Field(
        default="1.0.0",
        description="Model version used for inference.",
    )
    tile_id: Optional[str] = Field(
        default=None,
        description="Echo of the tile_id from the request.",
    )


class HealthResponse(BaseModel):
    """Response from the /api/health endpoint."""
    status: str = Field(..., example="ok")
    model_loaded: bool = Field(..., description="Whether the inference model is loaded.")
    device: str = Field(..., description="Compute device: 'cuda' or 'cpu'.")
    version: str = Field(..., example="1.0.0")
    message: str = Field(..., example="LISSclear API is running.")
