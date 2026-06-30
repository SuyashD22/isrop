"""
Fixed model_loader.py to map 3-channel RGB to the 13-band Sentinel-2 format.
Sentinel-2 bands:
0: B1, 1: B2(Blue), 2: B3(Green), 3: B4(Red), ...
So RGB (0, 1, 2) maps to bands (3, 2, 1).
"""
import numpy as np

def rgb_to_s2(rgb_np):
    """Convert (3, H, W) RGB to (13, H, W) Sentinel-2 format."""
    C, H, W = rgb_np.shape
    s2 = np.zeros((13, H, W), dtype=np.float32)
    s2[3] = rgb_np[0] # Red
    s2[2] = rgb_np[1] # Green
    s2[1] = rgb_np[2] # Blue
    # Fill other bands with something reasonable to avoid zero-activations killing the network
    # E.g., B8 (NIR) is often correlated with Red/Green
    s2[7] = rgb_np[0] * 0.5
    s2[0] = rgb_np[2] * 0.8 # Coastal aerosol ~ Blue
    return s2

def s2_to_rgb(s2_np):
    """Convert (13, H, W) Sentinel-2 format to (3, H, W) RGB."""
    rgb = np.zeros((3, s2_np.shape[1], s2_np.shape[2]), dtype=np.float32)
    rgb[0] = s2_np[3] # Red
    rgb[1] = s2_np[2] # Green
    rgb[2] = s2_np[1] # Blue
    return rgb

# Quick test
rgb = np.random.rand(3, 256, 256).astype(np.float32)
s2 = rgb_to_s2(rgb)
rgb_out = s2_to_rgb(s2)
print("RGB match:", np.allclose(rgb, rgb_out))
