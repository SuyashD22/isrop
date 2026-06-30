"""
Fixed inference test: apply correct pre/post processing for satellite models.
These models expect multispectral data. We adapt by:
1. For ResNet/SAR-Carl: apply proper per-channel normalization & use tanh-output assumption
2. For CR-Net: the output [-0.7, +0.6] is likely residual (delta from input) — add back to input
"""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("test_fixed")

import numpy as np
import torch
from PIL import Image
from pathlib import Path

INPUT_PATH = r"C:\Users\suyas\Downloads\download.png"
OUT_DIR = r"C:\Users\suyas\OneDrive\Desktop\isrop\backend"

def load_image(path, size=256):
    img = Image.open(path).convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.transpose(2, 0, 1)  # (3, H, W)

def save(arr, name):
    arr = np.clip(arr, 0, 1)
    rgb = arr[:3] if arr.shape[0] >= 3 else np.repeat(arr[:1], 3, axis=0)
    img = Image.fromarray((rgb.transpose(1,2,0)*255).astype(np.uint8))
    p = os.path.join(OUT_DIR, name)
    img.save(p)
    logger.info("Saved: %s", p)
    return p

def norm_percentile(arr):
    """Normalize to [0,1] using 1st-99th percentile stretch."""
    p1, p99 = np.percentile(arr, 1), np.percentile(arr, 99)
    if p99 > p1:
        return np.clip((arr - p1) / (p99 - p1), 0, 1)
    return np.clip(arr, 0, 1)

cloudy = load_image(INPUT_PATH)
logger.info("Input: %s  min=%.3f max=%.3f", cloudy.shape, cloudy.min(), cloudy.max())

# Stack 5 identical frames to get 15 channels
stacked = np.concatenate([cloudy]*5, axis=0)  # (15, 256, 256)

# ── TEST 1: Baseline ResNet with output treated as residual ────────────────
logger.info("=" * 60)
logger.info("Baseline ResNet - residual interpretation")
try:
    from services.model_loader import _load_baseline_resnet
    model = _load_baseline_resnet(Path("models/baseline_resnet.pth"))
    x = torch.from_numpy(stacked).unsqueeze(0)
    with torch.no_grad():
        out = model(x).squeeze(0).cpu().numpy()  # (13, 256, 256)
    logger.info("Raw out: min=%.3e max=%.3e", out.min(), out.max())

    # Strategy 1: treat output as direct prediction, normalize via percentile
    direct = norm_percentile(out[:3])
    save(direct, "fixed_resnet_direct.png")

    # Strategy 2: treat output channels as residual added to cloudy input
    # Scale residual output to match input scale
    residual_scale = 1.0 / max(abs(out.max()), abs(out.min()), 1e-6)
    residual = out[:3] * residual_scale
    combined = np.clip(cloudy + residual, 0, 1)
    save(combined, "fixed_resnet_residual.png")

except Exception as e:
    logger.error("ResNet failed: %s", e, exc_info=True)

# ── TEST 2: SAR-Carl with residual interpretation ──────────────────────────
logger.info("=" * 60)
logger.info("SAR-Carl - residual interpretation")
try:
    from services.model_loader import _load_sar_carl
    model = _load_sar_carl(Path("models/model_SARcarl.hdf5"))
    x = torch.from_numpy(stacked).unsqueeze(0)
    with torch.no_grad():
        out = model(x).squeeze(0).cpu().numpy()
    logger.info("Raw out: min=%.3e max=%.3e", out.min(), out.max())

    direct = norm_percentile(out[:3])
    save(direct, "fixed_sarcal_direct.png")

    residual_scale = 1.0 / max(abs(out.max()), abs(out.min()), 1e-6)
    residual = out[:3] * residual_scale
    combined = np.clip(cloudy + residual, 0, 1)
    save(combined, "fixed_sarcal_residual.png")

except Exception as e:
    logger.error("SAR-Carl failed: %s", e, exc_info=True)

# ── TEST 3: CR-Net - output range [-0.7, 0.6] = residual delta ────────────
logger.info("=" * 60)
logger.info("CR-Net - residual interpretation")
try:
    from services.model_loader import _load_cr_net
    import cv2
    model_cr, n_opt, n_sar = _load_cr_net(Path("models/CR_net.pth"))
    H, W = 256, 256
    opt = np.zeros((1, n_opt, H, W), dtype=np.float32)
    sar = np.zeros((1, n_sar, H, W), dtype=np.float32)
    opt[0, :3] = cloudy

    opt_t = torch.from_numpy(opt)
    sar_t = torch.from_numpy(sar)
    with torch.no_grad():
        out = model_cr(opt_t, sar_t).squeeze(0).cpu().numpy()
    logger.info("CR-Net out: shape=%s min=%.3f max=%.3f", out.shape, out.min(), out.max())

    # Resize to original if needed
    if out.shape[1] != H or out.shape[2] != W:
        out = np.stack([cv2.resize(out[c], (W, H)) for c in range(out.shape[0])])

    # Strategy 1: direct normalized
    direct = norm_percentile(out[:3])
    save(direct, "fixed_crnet_direct.png")

    # Strategy 2: treat output as residual (delta), add back to cloudy
    # CR-Net output range is [-0.7, 0.6] which is a reasonable residual range
    residual = out[:3]  # already in [-1, 1] range approximately
    combined = np.clip(cloudy + residual, 0, 1)
    save(combined, "fixed_crnet_residual.png")

    # Strategy 3: tanh normalization of output
    tanh_out = (np.tanh(out[:3]) + 1) / 2
    save(tanh_out, "fixed_crnet_tanh.png")

    logger.info("CR-Net: saved 3 variants")
except Exception as e:
    logger.error("CR-Net failed: %s", e, exc_info=True)

logger.info("=" * 60)
logger.info("DONE — check fixed_*.png files")
