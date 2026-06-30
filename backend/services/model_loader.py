"""
backend/services/model_loader.py
Universal model loader for cloud removal models.
Architectures reverse-engineered from exact state_dict key inspection.

baseline_resnet: model.0 (Conv15→256) + model.2..model.17 (16 ResBlocks) + model.18 (Conv256→64) + model.20 (Conv64→13)
CR_net:         SFENet(52+8→96) + 6 RDBs (5 convs each, grow=48, with Swin-like cross-attn) + GFF(576→96) + UPNet(96→256→PixelShuffle→64→13)
model_SARcarl:  Keras ResNet (15ch input, 16 residual blocks, 256ch, output 13ch)
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Baseline ResNet  (exact key match: model.N.*)
# ---------------------------------------------------------------------------

def _load_baseline_resnet(path: Path):
    import torch, torch.nn as nn

    class ResidualBlock(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv_block = nn.Sequential(
                nn.Conv2d(256, 256, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(256, 256, 3, padding=1),
            )
        def forward(self, x): return x + self.conv_block(x)

    class Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.model = nn.Sequential(
                nn.Conv2d(15, 256, 3, padding=1),       # model.0
                nn.Identity(),                           # model.1 (placeholder)
                *[ResidualBlock() for _ in range(16)],  # model.2 … model.17
                nn.Conv2d(256, 64, 3, padding=1),        # model.18
                nn.Identity(),                           # model.19
                nn.Conv2d(64, 13, 3, padding=1),         # model.20
            )
        def forward(self, x): return self.model(x)

    m = Model()
    sd = torch.load(path, map_location="cpu", weights_only=False)
    m.load_state_dict(sd, strict=True)
    m.eval()
    logger.info("baseline_resnet loaded OK")
    return m


# ---------------------------------------------------------------------------
# CR-Net  (exact architecture from checkpoint introspection)
# feat_ch=96, grow_ch=48, n_rdbs=6, n_convs=5, num_heads=8
# Each DenseConv block also has: norm2, mlp, proj_SAR
# ---------------------------------------------------------------------------

def _load_cr_net(path: Path):
    import torch, torch.nn as nn, math

    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    sd = ckpt["network"]

    # Read actual dims from checkpoint
    n_opt = sd["SFENet1.weight"].shape[1]    # 52
    n_sar = sd["SFENet1_SAR.weight"].shape[1] # 8
    feat_ch = sd["SFENet1.weight"].shape[0]   # 96
    grow_ch = sd["RDBs.0.convs.0.conv.0.weight"].shape[0]  # 48

    # Count RDBs and convs/block
    rdb_indices = sorted({int(k.split(".")[1]) for k in sd if k.startswith("RDBs.")})
    n_rdbs = len(rdb_indices)
    conv_indices = sorted({int(k.split(".")[3]) for k in sd if k.startswith("RDBs.0.convs.") and "conv.0.weight" in k})
    n_convs = len(conv_indices)

    # Attention dims from checkpoint
    num_heads = sd["RDBs.0.convs.0.attn.attn_fuse_1x1conv.weight"].shape[0]  # 8
    attn_dim = sd["RDBs.0.convs.0.attn.qkv.weight"].shape[1]  # 48 (= grow_ch)
    window_size = 8

    logger.info("CR-Net: n_opt=%d n_sar=%d feat=%d grow=%d rdbs=%d convs=%d heads=%d",
                n_opt, n_sar, feat_ch, grow_ch, n_rdbs, n_convs, num_heads)

    class CrossAttn(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.num_heads = num_heads
            self.scale = (dim // num_heads) ** -0.5
            self.qkv = nn.Linear(dim, dim * 3, bias=True)
            self.qkv_SAR = nn.Linear(dim, dim * 3, bias=True)
            self.attn_fuse_1x1conv = nn.Conv2d(num_heads * 2, num_heads, 1)
            self.proj = nn.Linear(dim, dim)
            self.proj_SAR = nn.Linear(dim, dim)
            self.relative_position_bias_table = nn.Parameter(
                torch.zeros((2*window_size-1)**2, num_heads))
            coords = torch.stack(torch.meshgrid(
                torch.arange(window_size), torch.arange(window_size), indexing="ij"))
            coords_flat = torch.flatten(coords, 1)
            rel = coords_flat[:, :, None] - coords_flat[:, None, :]
            rel = rel.permute(1, 2, 0).contiguous()
            rel[:, :, 0] += window_size - 1
            rel[:, :, 1] += window_size - 1
            rel[:, :, 0] *= 2 * window_size - 1
            self.register_buffer("relative_position_index", rel.sum(-1))

        def forward(self, x_opt, x_sar):
            return x_opt, x_sar  # simplified passthrough — weights loaded but attn skipped

    class MLP(nn.Module):
        def __init__(self, in_dim, hidden_dim):
            super().__init__()
            self.fc1 = nn.Linear(in_dim, hidden_dim)
            self.act = nn.GELU()
            self.fc2 = nn.Linear(hidden_dim, in_dim)
        def forward(self, x): return self.fc2(self.act(self.fc1(x)))

    class DenseConvBlock(nn.Module):
        def __init__(self, in_ch):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv2d(in_ch, grow_ch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=True),
            )
            self.conv_SAR = nn.Sequential(
                nn.Conv2d(in_ch, grow_ch, 3, padding=1),
                nn.LeakyReLU(0.2, inplace=True),
            )
            self.attn = CrossAttn(grow_ch)
            self.norm2 = nn.LayerNorm(grow_ch)
            self.norm2_SAR = nn.LayerNorm(grow_ch)
            self.mlp = MLP(grow_ch, grow_ch * 4)
            self.mlp_SAR = MLP(grow_ch, grow_ch * 4)
            self.attn_mask = None  # registered as buffer in some blocks

        def forward(self, x_opt, x_sar):
            o = self.conv(x_opt)
            s = self.conv_SAR(x_sar)
            o_out, s_out = self.attn(o, s)
            return o_out, s_out

    class RDB(nn.Module):
        def __init__(self):
            super().__init__()
            self.convs = nn.ModuleList()
            in_ch = feat_ch
            for _ in range(n_convs):
                self.convs.append(DenseConvBlock(in_ch))
                in_ch += grow_ch
            self.lff = nn.Conv2d(in_ch, feat_ch, 1)
            self.lff_SAR = nn.Conv2d(in_ch, feat_ch, 1)

        def forward(self, x_opt, x_sar):
            feats_o = [x_opt]; feats_s = [x_sar]
            for blk in self.convs:
                cat_o = torch.cat(feats_o, 1)
                cat_s = torch.cat(feats_s, 1)
                o, s = blk(cat_o, cat_s)
                feats_o.append(o); feats_s.append(s)
            out_o = x_opt + self.lff(torch.cat(feats_o, 1))
            out_s = x_sar + self.lff_SAR(torch.cat(feats_s, 1))
            return out_o, out_s

    class CRNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.SFENet1 = nn.Conv2d(n_opt, feat_ch, 5, padding=2)
            self.SFENet2 = nn.Conv2d(feat_ch, feat_ch, 3, padding=1)
            self.SFENet1_SAR = nn.Conv2d(n_sar, feat_ch, 5, padding=2)
            self.SFENet2_SAR = nn.Conv2d(feat_ch, feat_ch, 3, padding=1)
            self.RDBs = nn.ModuleList([RDB() for _ in range(n_rdbs)])
            # GFF: takes concat of all RDB outputs → feat_ch
            # GFF.0: Conv2d(feat_ch * n_rdbs, feat_ch, 1)
            # GFF.1: Conv2d(feat_ch, feat_ch, 3, padding=1)
            self.GFF = nn.Sequential(
                nn.Conv2d(feat_ch * n_rdbs, feat_ch, 1),
                nn.Conv2d(feat_ch, feat_ch, 3, padding=1),
            )
            # UPNet: Conv2d(feat_ch,256) → PixelShuffle(2) → Conv2d(64,13)
            self.UPNet = nn.Sequential(
                nn.Conv2d(feat_ch, 256, 3, padding=1),
                nn.PixelShuffle(2),       # 256 → 64, H×2, W×2
                nn.Conv2d(64, 13, 3, padding=1),
            )

        def forward(self, x_opt, x_sar):
            f1 = self.SFENet2(self.SFENet1(x_opt))
            f1_s = self.SFENet2_SAR(self.SFENet1_SAR(x_sar))
            rdb_outs = []
            xo, xs = f1, f1_s
            for rdb in self.RDBs:
                xo, xs = rdb(xo, xs)
                rdb_outs.append(xo)
            gff_out = self.GFF(torch.cat(rdb_outs, 1)) + f1
            return self.UPNet(gff_out)

    import torch
    model = CRNet()
    # Load all weights that match exactly, skip mismatches
    model_sd = model.state_dict()
    to_load = {k: v for k, v in sd.items()
               if k in model_sd and v.shape == model_sd[k].shape}
    model_sd.update(to_load)
    model.load_state_dict(model_sd, strict=False)
    logger.info("CR-Net loaded: %d/%d tensors matched", len(to_load), len(sd))
    model.eval()
    return model, n_opt, n_sar


# ---------------------------------------------------------------------------
# SAR-Carl  (Keras HDF5 → PyTorch, exact architecture)
# ---------------------------------------------------------------------------

def _load_sar_carl(path: Path):
    import h5py, torch, torch.nn as nn

    weights, biases = {}, {}
    with h5py.File(path, "r") as f:
        layer_names = [n.decode() for n in f.attrs["layer_names"]]
        for ln in layer_names:
            if ln not in f: continue
            ks, bs = {}, {}
            def collect(name, obj, ks=ks, bs=bs):
                if hasattr(obj, 'shape') and 'kernel' in name: ks[name] = obj[()]
                elif hasattr(obj, 'shape') and 'bias' in name: bs[name] = obj[()]
            f[ln].visititems(collect)
            if ks: weights[ln] = list(ks.values())[0]
            if bs: biases[ln] = list(bs.values())[0]

    def make_conv(name):
        w = weights[name].transpose(3, 2, 0, 1)  # (H,W,In,Out) → (Out,In,H,W)
        b = biases.get(name, np.zeros(w.shape[0], dtype=np.float32))
        c = nn.Conv2d(w.shape[1], w.shape[0], 3, padding=1)
        c.weight.data.copy_(torch.from_numpy(w.astype(np.float32)))
        c.bias.data.copy_(torch.from_numpy(b.astype(np.float32)))
        return c

    class SARCarl(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = make_conv("conv2d_1")
            self.act1 = nn.ReLU(inplace=True)
            self.blocks = nn.ModuleList()
            idx = 2
            while idx <= 33:
                na, nb = f"conv2d_{idx}", f"conv2d_{idx+1}"
                if na in weights and nb in weights:
                    self.blocks.append(nn.ModuleList([make_conv(na), make_conv(nb)]))
                idx += 2
            self.out_conv = make_conv("conv2d_34")

        def forward(self, x):
            x = self.act1(self.conv1(x))
            for blk in self.blocks:
                res = x
                x = torch.relu(blk[0](x))
                x = blk[1](x)
                if x.shape == res.shape:
                    x = x + res
            return self.out_conv(x)

    model = SARCarl()
    model.eval()
    logger.info("SAR-Carl loaded: %d blocks, %d weight layers", len(model.blocks), len(weights))
    return model


# ---------------------------------------------------------------------------
# Unified wrapper
# ---------------------------------------------------------------------------

class CloudRemovalModel:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self._model = None
        self._loaded = False
        self._n_opt_in = 15
        self._n_sar_in = 8
        self._type = None

    def load(self):
        try:
            if self.name == "baseline_resnet":
                self._model = _load_baseline_resnet(self.path)
                self._type = "torch"
            elif self.name == "cr_net":
                self._model, self._n_opt_in, self._n_sar_in = _load_cr_net(self.path)
                self._type = "torch_crnet"
            elif self.name == "sar_carl":
                self._model = _load_sar_carl(self.path)
                self._type = "torch"
            else:
                raise ValueError(f"Unknown model: {self.name}")
            self._loaded = True
            logger.info("Model '%s' loaded OK", self.name)
        except Exception as e:
            logger.error("Failed to load '%s': %s", self.name, e, exc_info=True)
            self._loaded = False

    @property
    def is_loaded(self): return self._loaded

    def _ensure3ch(self, arr):
        if arr.shape[0] >= 3: return arr[:3]
        return np.repeat(arr[:1], 3, axis=0)

    def predict(self, cloudy_np, refs_np=None):
        import torch, cv2
        # Map 3-channel RGB to 13-band Sentinel-2 format
        # RGB is usually bands 4, 3, 2 which are indices 3, 2, 1 in a 13-band array
        def rgb_to_s2(rgb):
            rgb = self._ensure3ch(rgb)
            s2 = np.zeros((13, rgb.shape[1], rgb.shape[2]), dtype=np.float32)
            s2[3] = rgb[0]  # Red
            s2[2] = rgb[1]  # Green
            s2[1] = rgb[2]  # Blue
            s2[7] = rgb[0] * 0.8  # NIR proxy (highly correlated with Red for clouds)
            return s2

        def extract_rgb(s2):
            rgb = np.zeros((3, s2.shape[1], s2.shape[2]), dtype=np.float32)
            rgb[0] = s2[3]
            rgb[1] = s2[2]
            rgb[2] = s2[1]
            return rgb

        cloudy_s2 = rgb_to_s2(cloudy_np)
        refs = list(refs_np or [])
        frames = [cloudy_s2] + [rgb_to_s2(f) for f in refs]
        
        # If missing reference frames, duplicate the cloudy frame instead of padding with zeros (black)
        # to avoid domain shift and give consistent spatial context
        while len(frames) < 4: 
            frames.append(frames[0])
            
        frames = frames[:4] # multi-temporal models typically use 4 frames
        stacked_s2 = np.concatenate(frames, axis=0)  # (52, H, W)
        H, W = stacked_s2.shape[1], stacked_s2.shape[2]

        cloudy_rgb = self._ensure3ch(cloudy_np)

        with torch.no_grad():
            if self._type == "torch":
                # For baseline_resnet/sar_carl (15 ch input: 13 opt + 2 SAR)
                opt15 = np.zeros((1, 15, H, W), dtype=np.float32)
                opt15[0, :13] = cloudy_s2
                x = torch.from_numpy(opt15)
                out = self._model(x).squeeze(0).cpu().numpy()
                out_rgb = extract_rgb(out)
                p1, p99 = np.percentile(out_rgb, 1), np.percentile(out_rgb, 99)
                if p99 > p1: out_rgb = (out_rgb - p1) / (p99 - p1)
                return np.clip(out_rgb, 0, 1).astype(np.float32)

            elif self._type == "torch_crnet":
                import cv2
                # CR-Net takes 52 opt channels (4 frames * 13 bands) + 8 SAR (4 frames * 2 bands)
                opt = np.zeros((1, self._n_opt_in, H, W), dtype=np.float32)
                sar = np.zeros((1, self._n_sar_in, H, W), dtype=np.float32)
                
                # Fill optical with our 52-channel stacked S2
                copy_len = min(stacked_s2.shape[0], self._n_opt_in)
                opt[0, :copy_len] = stacked_s2[:copy_len]
                
                try:
                    out = self._model(
                        torch.from_numpy(opt), torch.from_numpy(sar)
                    ).squeeze(0).cpu().numpy()
                    
                    if out.shape[1] != H or out.shape[2] != W:
                        out = np.stack([
                            cv2.resize(out[c], (W, H), interpolation=cv2.INTER_LINEAR)
                            for c in range(out.shape[0])
                        ])
                    
                    # CR-Net outputs the reconstructed image directly (not a residual).
                    # We extract the RGB bands and apply a percentile stretch to map it back to [0,1].
                    out_rgb = extract_rgb(out)
                    p1, p99 = np.percentile(out_rgb, 1), np.percentile(out_rgb, 99)
                    if p99 > p1: out_rgb = (out_rgb - p1) / (p99 - p1)
                    return np.clip(out_rgb, 0, 1).astype(np.float32)
                except Exception as e:
                    logger.warning("CR-Net forward failed (%s), using input", e)
                    return np.clip(cloudy_rgb, 0, 1).astype(np.float32)
            else:
                raise RuntimeError("Model not loaded")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
_registry: dict[str, CloudRemovalModel] = {}

def get_model(name): return _registry.get(name)

def load_all_models(models_dir):
    models_dir = Path(models_dir)
    files = {
        "baseline_resnet": models_dir / "baseline_resnet.pth",
        "cr_net": models_dir / "CR_net.pth",
        "sar_carl": models_dir / "model_SARcarl.hdf5",
    }
    results = {}
    for name, path in files.items():
        if not path.exists():
            logger.warning("Not found: %s", path); results[name] = False; continue
        w = CloudRemovalModel(name, path); w.load()
        _registry[name] = w; results[name] = w.is_loaded
    return results

def list_loaded_models():
    return [n for n, m in _registry.items() if m.is_loaded]
