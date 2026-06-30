"""
backend/core/config.py
FastAPI application settings loaded from environment variables.
Uses pydantic-settings for type-safe env var parsing.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Model paths ───────────────────────────────────────────────────────────
    models_dir: str = Field(
        default="./models",
        description="Directory containing the cloud removal model files",
    )

    # ── Server ────────────────────────────────────────────────────────────────
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    frontend_url: str = Field(default="http://localhost:3000")

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "https://lissclear.vercel.app"]
    )

    # ── Inference ─────────────────────────────────────────────────────────────
    device: str = Field(default="cpu", description="'cuda' or 'cpu'")
    n_reference_frames: int = Field(default=3)
    max_tile_size_mb: int = Field(default=50)
    image_size: int = Field(default=256)
    n_bands: int = Field(default=4)
    diffusion_timestep: int = Field(default=50)

    # ── Uploads ───────────────────────────────────────────────────────────────
    upload_dir: str = Field(default="/tmp/lissclear_uploads")
    max_upload_size_bytes: int = Field(default=50 * 1024 * 1024)  # 50 MB

    # ── API ───────────────────────────────────────────────────────────────────
    api_title: str = "LISSclear API"
    api_description: str = "Multi-temporal cloud removal for LISS-IV satellite imagery"
    api_version: str = "1.0.0"

    def models_dir_exists(self) -> bool:
        return Path(self.models_dir).exists()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level settings instance
settings = get_settings()
