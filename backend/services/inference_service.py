"""
backend/services/inference_service.py
Inference pipeline using the 3 real cloud removal models.

Supports:
  - baseline_resnet : ResNet baseline (PyTorch)
  - cr_net          : Cloud Removal Net with attention (PyTorch)
  - sar_carl        : SAR-Carl residual model (Keras HDF5 weights via numpy)
"""

from __future__ import annotations

import base64
import io
import logging
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image

from .cloud_mask_service import CloudMaskService
from .metrics_service import MetricsService

logger = logging.getLogger(__name__)

# Singleton pattern
_inference_service_instance: Optional["InferenceService"] = None

# Model display names
MODEL_DISPLAY_NAMES = {
    "baseline_resnet": "Baseline ResNet",
    "cr_net": "CR-Net",
    "sar_carl": "SAR-Carl",
}


class InferenceService:
    """
    Manages all 3 cloud removal models and routes inference requests.
    """

    def __init__(
        self,
        models_dir: str = "./models",
        device: str = "cpu",
        image_size: int = 256,
    ):
        self.models_dir = Path(models_dir)
        self.device = device
        self.image_size = image_size
        self._models_status: dict[str, bool] = {}
        self.cloud_mask_svc = CloudMaskService()
        self.metrics_svc = MetricsService(device=device)

    def load_model(self) -> None:
        """Load all available cloud removal models."""
        try:
            from .model_loader import load_all_models
            logger.info("Loading cloud removal models from: %s", self.models_dir)
            self._models_status = load_all_models(self.models_dir)
            loaded = [k for k, v in self._models_status.items() if v]
            failed = [k for k, v in self._models_status.items() if not v]
            if loaded:
                logger.info("✅ Models loaded: %s", ", ".join(loaded))
            if failed:
                logger.warning("⚠️  Models failed to load: %s", ", ".join(failed))
        except Exception as e:
            logger.error("Failed during model loading: %s", e, exc_info=True)

    @property
    def is_loaded(self) -> bool:
        """True if at least one model is available."""
        return any(self._models_status.values()) if self._models_status else False

    @property
    def loaded_models(self) -> list[str]:
        return [k for k, v in self._models_status.items() if v]

    def _bytes_to_numpy(self, image_bytes: bytes) -> np.ndarray:
        """
        Convert raw image bytes → (3, H, W) float32 [0, 1] numpy array.
        Resizes to self.image_size.
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((self.image_size, self.image_size), Image.LANCZOS)
        arr = np.array(img, dtype=np.float32) / 255.0  # (H, W, 3)
        return arr.transpose(2, 0, 1)  # (3, H, W)

    def _numpy_to_base64_png(self, arr: np.ndarray) -> str:
        """
        Convert (C, H, W) float32 [0,1] → base64-encoded PNG string.
        Uses first 3 channels as RGB.
        """
        if arr.shape[0] >= 3:
            rgb = arr[:3]
        else:
            rgb = np.repeat(arr[:1], 3, axis=0)
        rgb_uint8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        img = Image.fromarray(rgb_uint8.transpose(1, 2, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _mask_to_base64_png(self, mask: np.ndarray) -> str:
        """Convert (H, W) uint8 binary mask → base64 PNG."""
        mask_uint8 = (mask * 255).astype(np.uint8)
        img = Image.fromarray(mask_uint8)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def run_inference(
        self,
        cloudy_bytes: bytes,
        reference_bytes: List[bytes] | None = None,
        model_name: str = "cr_net",
        cloud_mask_method: str = "auto",
    ) -> dict:
        """
        Run full cloud removal inference pipeline.

        Args:
            cloudy_bytes:     Raw bytes of uploaded cloudy image.
            reference_bytes:  Optional list of reference image bytes.
            model_name:       Which model to use: 'baseline_resnet', 'cr_net', 'sar_carl'
            cloud_mask_method: 'auto' | 'ndsi' | 'brightness'

        Returns:
            Dict with output_image, cloud_mask, metrics, processing_time_ms, model_name.
        """
        from .model_loader import get_model

        t0 = time.time()

        if not self.is_loaded:
            raise RuntimeError("No models loaded. See /api/health for details.")

        # Resolve model — fall back to first available if requested one isn't loaded
        model = get_model(model_name)
        if model is None or not model.is_loaded:
            fallback = self.loaded_models[0] if self.loaded_models else None
            if fallback is None:
                raise RuntimeError(f"Model '{model_name}' not available and no fallback exists.")
            logger.warning("Model '%s' not available, falling back to '%s'", model_name, fallback)
            model_name = fallback
            model = get_model(model_name)

        logger.info("Running inference with model: %s", model_name)

        # ── Preprocess cloudy image ───────────────────────────────────────────
        cloudy_np = self._bytes_to_numpy(cloudy_bytes)  # (3, H, W) float32 [0,1]

        # ── Generate cloud mask ───────────────────────────────────────────────
        cloud_mask_np = self.cloud_mask_svc.generate_mask(cloudy_np, method=cloud_mask_method)  # (H, W) uint8
        cloud_coverage = float(cloud_mask_np.mean())

        # ── Preprocess reference images ───────────────────────────────────────
        refs = []
        for rb in (reference_bytes or []):
            try:
                refs.append(self._bytes_to_numpy(rb))
            except Exception as e:
                logger.warning("Failed to decode reference image: %s", e)

        # ── Run model inference ───────────────────────────────────────────────
        pred_np = model.predict(cloudy_np, refs)  # (3, H, W) float32 [0,1]

        # ── Build output images ───────────────────────────────────────────────
        output_b64 = self._numpy_to_base64_png(pred_np)
        mask_b64 = self._mask_to_base64_png(cloud_mask_np)

        # ── Compute metrics (proxy: compare pred vs cloudy on cloud-masked region) ──
        metrics = self._compute_metrics(pred_np, cloudy_np, cloud_mask_np, cloud_coverage)

        processing_time_ms = int((time.time() - t0) * 1000)

        return {
            "output_image": output_b64,
            "cloud_mask": mask_b64,
            "metrics": metrics,
            "processing_time_ms": processing_time_ms,
            "model_version": "2.0.0",
            "model_name": MODEL_DISPLAY_NAMES.get(model_name, model_name),
        }

    def _compute_metrics(
        self,
        pred: np.ndarray,
        target: np.ndarray,
        mask: np.ndarray,
        cloud_coverage: float,
    ) -> dict:
        """Compute PSNR, SSIM-proxy, SAM on the predicted vs cloudy image."""
        try:
            from skimage.metrics import peak_signal_noise_ratio, structural_similarity

            # Convert to HWC for skimage
            pred_hwc = pred.transpose(1, 2, 0)
            tgt_hwc = target.transpose(1, 2, 0)

            psnr = float(peak_signal_noise_ratio(tgt_hwc, pred_hwc, data_range=1.0))
            ssim = float(structural_similarity(
                tgt_hwc, pred_hwc, data_range=1.0, channel_axis=2,
                win_size=min(7, min(pred_hwc.shape[:2]) - 1 | 1)
            ))
        except Exception:
            psnr, ssim = 0.0, 0.0

        # SAM
        try:
            eps = 1e-8
            dot = np.sum(pred * target, axis=0)
            n1 = np.linalg.norm(pred, axis=0) + eps
            n2 = np.linalg.norm(target, axis=0) + eps
            sam = float(np.mean(np.arccos(np.clip(dot / (n1 * n2), -1, 1))))
        except Exception:
            sam = 0.0

        # NDVI MAE
        try:
            nir_p = pred[2] if pred.shape[0] > 2 else pred[0]
            red_p = pred[0]
            nir_t = target[2] if target.shape[0] > 2 else target[0]
            red_t = target[0]
            eps = 1e-8
            ndvi_p = (nir_p - red_p) / (nir_p + red_p + eps)
            ndvi_t = (nir_t - red_t) / (nir_t + red_t + eps)
            ndvi_mae = float(np.mean(np.abs(ndvi_p - ndvi_t)))
        except Exception:
            ndvi_mae = None

        return {
            "psnr": round(psnr, 4),
            "ssim": round(ssim, 4),
            "sam": round(sam, 6),
            "ndvi_mae": round(ndvi_mae, 6) if ndvi_mae is not None else None,
            "cloud_coverage": round(cloud_coverage, 4),
        }


def get_inference_service() -> InferenceService:
    """FastAPI dependency injection for inference service."""
    global _inference_service_instance
    if _inference_service_instance is None:
        from core.config import settings
        _inference_service_instance = InferenceService(
            models_dir=settings.models_dir,
            device=settings.device,
            image_size=settings.image_size,
        )
    return _inference_service_instance
