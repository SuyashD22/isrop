"""
backend/routers/health.py
GET /api/health — liveness and readiness check endpoint.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.config import settings
from services.inference_service import get_inference_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns API status, model loading state, and device info.",
)
async def health_check() -> JSONResponse:
    """
    Liveness + readiness check.
    Reports per-model loading status.
    """
    service = get_inference_service()
    loaded_models = getattr(service, "loaded_models", [])
    models_status = getattr(service, "_models_status", {})

    return JSONResponse({
        "status": "ok" if service.is_loaded else "degraded",
        "model_loaded": service.is_loaded,
        "loaded_models": loaded_models,
        "models_status": models_status,
        "device": settings.device,
        "version": settings.api_version,
        "message": (
            f"API ready. Models loaded: {', '.join(loaded_models)}"
            if service.is_loaded
            else "API running but no models loaded. Check backend/models/ directory."
        ),
    })
