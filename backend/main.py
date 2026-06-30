"""
backend/main.py
FastAPI application entry point for LISSclear API.

Endpoints:
  POST /api/remove-clouds  — cloud removal inference
  GET  /api/health         — liveness check
  GET  /api/metrics        — metric info
  GET  /docs               — Swagger UI (auto-generated)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.exceptions import register_exception_handlers
from routers import health, inference, metrics
from services.inference_service import get_inference_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("lissclear.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup, clean up at shutdown."""
    logger.info("=" * 60)
    logger.info("  LISSclear API v%s starting up...", settings.api_version)
    logger.info("  Device: %s | Models dir: %s", settings.device, settings.models_dir)
    logger.info("=" * 60)

    # Initialise and load model
    service = get_inference_service()
    service.load_model()

    if service.is_loaded:
        logger.info("✅ Model loaded successfully — API ready.")
    else:
        logger.warning("⚠️  Model failed to load — running in degraded mode.")

    yield

    # Cleanup
    logger.info("LISSclear API shutting down.")


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + [settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Exception Handlers ────────────────────────────────────────────────────────

register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(inference.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({
        "service": "LISSclear API",
        "version": settings.api_version,
        "description": "Multi-temporal cloud removal for LISS-IV satellite imagery",
        "docs": "/docs",
        "health": "/api/health",
    })
