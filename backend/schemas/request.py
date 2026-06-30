"""
backend/schemas/request.py
Pydantic request models for LISSclear API.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CloudRemovalRequest(BaseModel):
    """
    Metadata accompanying a cloud removal request.
    The actual files are uploaded as multipart form data.
    """
    tile_id: Optional[str] = Field(
        default=None,
        description="Optional tile identifier for tracking",
        example="LISS4_UP_078_20230715",
    )
    sensor: str = Field(
        default="sentinel2",
        description="Sensor type: 'sentinel2' or 'liss4'",
        example="sentinel2",
    )
    cloud_mask_method: str = Field(
        default="auto",
        description="Cloud masking method: 'auto' | 'scl' | 'ndsi' | 'brightness'",
        example="auto",
    )
    n_reference_frames: Optional[int] = Field(
        default=None,
        ge=0,
        le=5,
        description="Number of reference frames to use (None = server default)",
    )
