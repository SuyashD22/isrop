import sys, os, time, logging
import numpy as np
import torch
from PIL import Image
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("test_resnet")

INPUT_PATH = r"C:\Users\suyas\Downloads\download (1).png"
if not os.path.exists(INPUT_PATH):
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

cloudy = load_image(INPUT_PATH)

from services.model_loader import _load_baseline_resnet
try:
    model = _load_baseline_resnet(Path("models/baseline_resnet.pth"))
    
    # Map RGB to S2
    s2 = np.zeros((13, 256, 256), dtype=np.float32)
    s2[3] = cloudy[0]  # Red
    s2[2] = cloudy[1]  # Green
    s2[1] = cloudy[2]  # Blue
    s2[7] = cloudy[0] * 0.8  # NIR proxy
    
    opt15 = np.zeros((1, 15, 256, 256), dtype=np.float32)
    opt15[0, :13] = s2
    
    with torch.no_grad():
        out = model(torch.from_numpy(opt15)).squeeze(0).cpu().numpy()
        
    logger.info("ResNet out: min=%.3f max=%.3f", out.min(), out.max())
    
    out_rgb = np.zeros((3, 256, 256), dtype=np.float32)
    out_rgb[0] = out[3]
    out_rgb[1] = out[2]
    out_rgb[2] = out[1]
    
    # Percentile
    p1, p99 = np.percentile(out_rgb, 1), np.percentile(out_rgb, 99)
    if p99 > p1:
        direct = (out_rgb - p1) / (p99 - p1)
    else:
        direct = out_rgb
    save(direct, "test_resnet_direct_percentile.png")
    
    # Residual
    save(np.clip(cloudy + out_rgb, 0, 1), "test_resnet_residual.png")
    
except Exception as e:
    logger.error("Failed", exc_info=True)
