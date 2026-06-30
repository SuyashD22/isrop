"""
backend/routers/inference.py
POST /api/remove-clouds — main inference endpoint.
Accepts multipart form: cloudy tile + optional reference tiles + model selection.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from core.config import settings
from core.exceptions import (
    FileTooLargeException,
    InferenceFailedException,
    InvalidFileFormatException,
    ModelNotLoadedException,
)
from services.inference_service import get_inference_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Inference"])

ACCEPTED_FORMATS = {"image/png", "image/jpeg", "image/tiff", "image/tif", "application/octet-stream"}
ACCEPTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

VALID_MODELS = {"baseline_resnet", "cr_net", "sar_carl"}


def _validate_file(upload: UploadFile, content_bytes: bytes) -> None:
    """Validate file format and size."""
    suffix = "." + upload.filename.split(".")[-1].lower() if upload.filename else ""
    if suffix not in ACCEPTED_EXTENSIONS and upload.content_type not in ACCEPTED_FORMATS:
        raise InvalidFileFormatException(upload.filename, list(ACCEPTED_EXTENSIONS))

    size_mb = len(content_bytes) / (1024 * 1024)
    if size_mb > settings.max_tile_size_mb:
        raise FileTooLargeException(size_mb, settings.max_tile_size_mb)


@router.post(
    "/remove-clouds",
    summary="Remove clouds from satellite imagery using AI models",
    description=(
        "Upload a cloudy satellite image (PNG/JPG/GeoTIFF) and optional cloud-free "
        "reference images from the same location. Select from 3 models: "
        "Baseline ResNet, CR-Net, or SAR-Carl. "
        "Returns the cloud-removed output as base64 PNG with quality metrics."
    ),
    responses={
        200: {"description": "Successful cloud removal"},
        400: {"description": "Invalid file format or unknown model"},
        413: {"description": "File too large"},
        422: {"description": "Validation error"},
        503: {"description": "Model not loaded"},
    },
)
def remove_clouds(
    cloudy_tile: UploadFile = File(
        ...,
        description="Cloudy input image (PNG, JPG or GeoTIFF, max 50MB)",
    ),
    reference_tiles: List[UploadFile] = File(
        default=[],
        description="Cloud-free reference images (same location, different dates)",
    ),
    sensor: str = Form(default="sentinel2", description="Sensor type: sentinel2 or liss4"),
    cloud_mask_method: str = Form(default="auto", description="Masking method: auto|ndsi|brightness"),
    model_name: str = Form(default="cr_net", description="Model: baseline_resnet|cr_net|sar_carl"),
) -> JSONResponse:
    """
    Cloud removal endpoint.

    Pipeline:
    1. Validate and read uploaded images
    2. Generate cloud mask from cloudy tile
    3. Stack cloudy + reference frames as multi-temporal input
    4. Run selected model inference
    5. Return cloud-free output + quality metrics
    """
    service = get_inference_service()

    if not service.is_loaded:
        raise ModelNotLoadedException()

    # Validate model name
    if model_name not in VALID_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model '{model_name}'. Valid options: {sorted(VALID_MODELS)}",
        )

    # Read and validate cloudy tile
    cloudy_bytes = cloudy_tile.file.read()
    _validate_file(cloudy_tile, cloudy_bytes)
    logger.info("Received tile: %s (%.1f KB)", cloudy_tile.filename, len(cloudy_bytes) / 1024)

    # Read and validate reference tiles
    ref_bytes_list = []
    for ref in reference_tiles[:settings.n_reference_frames]:
        ref_bytes = ref.file.read()
        _validate_file(ref, ref_bytes)
        ref_bytes_list.append(ref_bytes)

    logger.info("Reference frames: %d | Model: %s", len(ref_bytes_list), model_name)

    # Run inference
    try:
        result = service.run_inference(
            cloudy_bytes,
            ref_bytes_list,
            model_name=model_name,
            cloud_mask_method=cloud_mask_method,
        )
    except Exception as e:
        logger.exception("Inference failed")
        raise InferenceFailedException(str(e))

    return JSONResponse(content=result)


@router.get(
    "/models",
    summary="List available cloud removal models",
    description="Returns the list of loaded models and their status.",
)
async def list_models() -> JSONResponse:
    """List which models are currently loaded and available."""
    service = get_inference_service()
    from services.inference_service import MODEL_DISPLAY_NAMES
    from services.model_loader import _registry

    models = []
    for key in ["baseline_resnet", "cr_net", "sar_carl"]:
        m = _registry.get(key)
        models.append({
            "id": key,
            "name": MODEL_DISPLAY_NAMES.get(key, key),
            "loaded": m.is_loaded if m else False,
        })

    return JSONResponse(content={
        "models": models,
        "default": "cr_net",
    })
