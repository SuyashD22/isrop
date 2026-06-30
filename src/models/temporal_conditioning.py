"""
src/models/temporal_conditioning.py
Cross-attention layer that injects N cloud-free reference frames
into the diffusion U-Net decoder.

This is the architectural novelty of LISSclear. Standard SD-2 inpainting
only conditions on the masked image. We additionally condition on a
temporal stack of cloud-free observations from the same location,
enabling spectrally-accurate reconstruction.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from einops import rearrange


class TemporalConditioningLayer(nn.Module):
    """
    Multi-head cross-attention layer for temporal reference fusion.

    Query  = current noisy feature map (from U-Net decoder)
    Key/Value = projected reference frame features (from temporal stack)

    This follows the cross-attention design in Prompt-to-Prompt and
    ControlNet, adapted for temporal satellite imagery conditioning.

    Args:
        channels:  Feature channel count (must match U-Net decoder block).
        n_refs:    Number of reference frames in the stack.
        n_heads:   Number of attention heads.
        dropout:   Attention dropout probability.
    """

    def __init__(
        self,
        channels: int = 320,
        n_refs: int = 3,
        n_heads: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.channels = channels
        self.n_refs = n_refs
        self.n_heads = n_heads

        # Project concatenated reference features → channels
        ref_input_channels = channels * n_refs
        self.ref_projector = nn.Sequential(
            nn.Conv2d(ref_input_channels, channels, kernel_size=1, bias=False),
            nn.GroupNorm(min(8, channels), channels),
            nn.SiLU(inplace=True),
        )

        # Cross-attention: query from noisy features, key/value from references
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=channels,
            num_heads=n_heads,
            batch_first=True,
            dropout=dropout,
        )

        # Layer norm + residual
        self.norm_query = nn.LayerNorm(channels)
        self.norm_out = nn.LayerNorm(channels)

        # Learnable scale — initialised near 0 so layer starts as identity
        self.scale = nn.Parameter(torch.zeros(1))

    def forward(
        self,
        x: torch.Tensor,
        ref_stack: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            x:         (B, C, H, W)      — current noisy feature map
            ref_stack: (B, n_refs*C, H, W) — concatenated reference features

        Returns:
            (B, C, H, W) — features conditioned on temporal references
        """
        B, C, H, W = x.shape

        # Project reference stack: (B, n_refs*C, H, W) → (B, C, H, W)
        ref_ctx = self.ref_projector(ref_stack)

        # Flatten spatial dims for attention computation
        # Query from current noisy features
        x_seq = rearrange(x, "b c h w -> b (h w) c")         # (B, HW, C)
        # Key/Value from reference features
        ref_seq = rearrange(ref_ctx, "b c h w -> b (h w) c")  # (B, HW, C)

        # Pre-norm on query
        x_seq = self.norm_query(x_seq)

        # Cross-attention: noisy features query the cloud-free references
        attn_out, attn_weights = self.cross_attention(
            query=x_seq,
            key=ref_seq,
            value=ref_seq,
            need_weights=False,
        )

        # Post-norm + learned residual (starts as pass-through, learns to fuse)
        out_seq = self.norm_out(x_seq + self.scale * attn_out)

        # Reshape back to spatial
        out = rearrange(out_seq, "b (h w) c -> b c h w", h=H, w=W)
        return out


class MultiScaleTemporalConditioning(nn.Module):
    """
    Applies TemporalConditioningLayer at multiple U-Net decoder feature scales.

    SD-2 decoder block channel sizes (in order from bottleneck to output):
        1280 → 1280 → 640 → 320

    We inject temporal conditioning at each scale.
    """

    # SD-2 inpainting U-Net decoder block channel dims (bottleneck → output)
    SD2_DECODER_CHANNELS = [1280, 1280, 640, 320]

    def __init__(self, n_refs: int = 3, n_heads: int = 8):
        super().__init__()
        self.n_refs = n_refs
        self.layers = nn.ModuleList([
            TemporalConditioningLayer(
                channels=ch,
                n_refs=n_refs,
                n_heads=min(n_heads, ch // 40),  # Ensure head_dim >= 40
            )
            for ch in self.SD2_DECODER_CHANNELS
        ])

    def forward(
        self,
        feature_maps: list[torch.Tensor],
        ref_stacks: list[torch.Tensor],
    ) -> list[torch.Tensor]:
        """
        Args:
            feature_maps: List of (B, C_i, H_i, W_i) decoder feature maps.
            ref_stacks:   List of (B, n_refs*C_i, H_i, W_i) reference feature stacks.

        Returns:
            List of conditioned feature maps (same shapes as input).
        """
        assert len(feature_maps) == len(self.layers), \
            f"Expected {len(self.layers)} feature maps, got {len(feature_maps)}"

        return [
            layer(fm, rs)
            for layer, fm, rs in zip(self.layers, feature_maps, ref_stacks)
        ]
