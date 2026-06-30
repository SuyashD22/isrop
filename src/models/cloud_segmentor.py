"""
src/models/cloud_segmentor.py
U-Net binary cloud segmentation model.
Takes a satellite tile as input and outputs a pixel-wise cloud probability map.

Used as a preprocessing step when SCL band is unavailable (e.g. LISS-IV).
Pre-train on SEN12MS cloud labels, then fine-tune on LISS-IV.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Building blocks ───────────────────────────────────────────────────────────

class DoubleConv(nn.Module):
    """Two consecutive Conv2d → GroupNorm → SiLU blocks."""

    def __init__(self, in_ch: int, out_ch: int, groups: int = 8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(min(groups, out_ch), out_ch),
            nn.SiLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(min(groups, out_ch), out_ch),
            nn.SiLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DownBlock(nn.Module):
    """Max-pool → DoubleConv."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.pool = nn.MaxPool2d(2)
        self.conv = DoubleConv(in_ch, out_ch)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(self.pool(x))


class UpBlock(nn.Module):
    """Bilinear upsample → concat skip → DoubleConv."""

    def __init__(self, in_ch: int, skip_ch: int, out_ch: int):
        super().__init__()
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        self.conv = DoubleConv(in_ch + skip_ch, out_ch)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        # Handle odd spatial dims
        if x.shape != skip.shape:
            x = F.pad(x, [0, skip.shape[3]-x.shape[3], 0, skip.shape[2]-x.shape[2]])
        return self.conv(torch.cat([x, skip], dim=1))


# ── Main U-Net ────────────────────────────────────────────────────────────────

class CloudSegmentor(nn.Module):
    """
    Lightweight U-Net for binary cloud segmentation.

    Input:  (B, C, H, W) satellite tile — C=4 for LISS-IV/Sentinel-2 (R,G,B,NIR)
    Output: (B, 1, H, W) cloud probability map (sigmoid activated)

    Post-processing: threshold at 0.5 to get binary mask.

    Architecture:
        Encoder: 4→64→128→256→512
        Bottleneck: 512→1024
        Decoder: 1024→512→256→128→64→1 (with skip connections)

    ~31M parameters — fits comfortably on Colab T4 (16GB VRAM).
    """

    def __init__(self, in_channels: int = 4, base_channels: int = 64):
        super().__init__()

        # Encoder
        self.enc1 = DoubleConv(in_channels, base_channels)
        self.enc2 = DownBlock(base_channels, base_channels * 2)
        self.enc3 = DownBlock(base_channels * 2, base_channels * 4)
        self.enc4 = DownBlock(base_channels * 4, base_channels * 8)

        # Bottleneck
        self.bottleneck = DownBlock(base_channels * 8, base_channels * 16)

        # Decoder
        self.dec4 = UpBlock(base_channels * 16, base_channels * 8, base_channels * 8)
        self.dec3 = UpBlock(base_channels * 8, base_channels * 4, base_channels * 4)
        self.dec2 = UpBlock(base_channels * 4, base_channels * 2, base_channels * 2)
        self.dec1 = UpBlock(base_channels * 2, base_channels, base_channels)

        # Output head
        self.head = nn.Sequential(
            nn.Conv2d(base_channels, base_channels // 2, kernel_size=3, padding=1),
            nn.SiLU(inplace=True),
            nn.Conv2d(base_channels // 2, 1, kernel_size=1),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Returns cloud probability map (B, 1, H, W) in [0, 1].
        """
        # Encoder path with skip connections
        s1 = self.enc1(x)
        s2 = self.enc2(s1)
        s3 = self.enc3(s2)
        s4 = self.enc4(s3)

        # Bottleneck
        b = self.bottleneck(s4)

        # Decoder path
        d4 = self.dec4(b, s4)
        d3 = self.dec3(d4, s3)
        d2 = self.dec2(d3, s2)
        d1 = self.dec1(d2, s1)

        return torch.sigmoid(self.head(d1))

    def predict_mask(
        self,
        x: torch.Tensor,
        threshold: float = 0.5,
    ) -> torch.Tensor:
        """
        Convenience method: returns binary mask (B, 1, H, W) uint8.
        """
        with torch.no_grad():
            prob = self.forward(x)
        return (prob > threshold).to(torch.uint8)

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
