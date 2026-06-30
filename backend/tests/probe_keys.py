"""
Probe exact state_dict keys for baseline_resnet and cr_net to fix weight mapping.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import torch
from pathlib import Path

print("=" * 60)
print("=== baseline_resnet.pth key structure ===")
raw = torch.load("models/baseline_resnet.pth", map_location="cpu", weights_only=False)
print(f"Type: {type(raw)}")
if isinstance(raw, dict):
    keys = list(raw.keys())
    print(f"Total keys: {len(keys)}")
    print("First 30 keys:")
    for k in keys[:30]:
        print(f"  {k}: {raw[k].shape}")
    print("Last 10 keys:")
    for k in keys[-10:]:
        print(f"  {k}: {raw[k].shape}")
else:
    print("Not a dict — it's a full model")

print()
print("=" * 60)
print("=== CR_net.pth key structure ===")
ckpt = torch.load("models/CR_net.pth", map_location="cpu", weights_only=False)
print(f"Type: {type(ckpt)}, keys: {list(ckpt.keys()) if isinstance(ckpt, dict) else 'N/A'}")
if isinstance(ckpt, dict) and "network" in ckpt:
    sd = ckpt["network"]
    keys = list(sd.keys())
    print(f"Total keys: {len(keys)}")
    print("First 30 keys:")
    for k in keys[:30]:
        print(f"  {k}: {sd[k].shape}")
    # Check the attention keys specifically
    print("\nAll attn keys (first 5):")
    attn_keys = [k for k in keys if "attn" in k]
    for k in attn_keys[:20]:
        print(f"  {k}: {sd[k].shape}")
    # UPNet keys
    print("\nUPNet keys:")
    for k in keys:
        if "UPNet" in k or "upnet" in k or "GFF" in k:
            print(f"  {k}: {sd[k].shape}")
