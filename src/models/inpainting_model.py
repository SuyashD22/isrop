"""
src/models/inpainting_model.py
Full multi-temporal conditioned diffusion inpainting model.

Architecture:
  - Base: Stable Diffusion 2 Inpainting U-Net (pretrained, fine-tuned decoder)
  - Extension: TemporalConditioningLayer injected at each U-Net decoder block
  - Input channels: 4 (noisy latent) + 1 (mask) + 4 (masked image latent) = 9
  - Additional conditioning: N reference frames encoded via lightweight CNN

All components are free and open-source (Apache 2.0 / CreativeML license).
"""

from __future__ import annotations

import logging
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from .temporal_conditioning import TemporalConditioningLayer

logger = logging.getLogger(__name__)


class ReferenceEncoder(nn.Module):
    """
    Lightweight CNN to encode N reference tiles into spatial feature maps.
    These feature maps are used as key/value in the temporal cross-attention.
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        mid = max(in_channels, out_channels // 2)
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, mid, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(min(8, mid), mid),
            nn.SiLU(inplace=True),
            nn.Conv2d(mid, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(min(8, out_channels), out_channels),
            nn.SiLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


class LISSClearModel(nn.Module):
    """
    Multi-temporal conditioned diffusion inpainting model for LISS-IV cloud removal.

    Inference workflow:
    1. Encode cloudy tile + cloud mask via VAE encoder
    2. Concatenate: [noisy_latent | mask_ds | masked_image_latent] → 9 channels
    3. U-Net denoising with temporal conditioning from reference frames
    4. Decode denoised latent via VAE decoder → cloud-free output

    Fine-tuning strategy:
    - Freeze U-Net encoder (down_blocks, mid_block)
    - Fine-tune U-Net decoder (up_blocks) + new temporal conditioning layers
    - Fine-tune VAE decoder for spectral accuracy
    """

    def __init__(
        self,
        n_refs: int = 3,
        in_channels: int = 4,
        freeze_encoder: bool = True,
        use_fp16: bool = False,
    ):
        super().__init__()
        self.n_refs = n_refs
        self.in_channels = in_channels
        self.use_fp16 = use_fp16
        self._vae = None
        self._unet = None
        self._scheduler = None

        # Reference encoder: (B, n_refs*C, H, W) → (B, 512, H/4, W/4)
        ref_in = n_refs * in_channels
        self.ref_encoder = ReferenceEncoder(ref_in, 512)

        # Temporal conditioning layers at SD-2 decoder scales
        # SD-2 inpainting U-Net decoder channel dims (bottleneck to output)
        decoder_channels = [1280, 1280, 640, 320]
        self.temporal_layers = nn.ModuleList([
            TemporalConditioningLayer(ch, n_refs=n_refs, n_heads=max(1, ch // 160))
            for ch in decoder_channels
        ])

        # Reference projectors at each decoder scale
        self.ref_projectors = nn.ModuleList([
            nn.Sequential(
                nn.AdaptiveAvgPool2d(1),  # Global average pooling
                nn.Flatten(),
                nn.Linear(512, ch),
                nn.Unflatten(1, (ch, 1)),
                nn.Upsample(scale_factor=8, mode="nearest"),  # Broadcast to spatial
            )
            for ch in decoder_channels
        ])

        self.freeze_encoder = freeze_encoder
        self._loaded = False

    def load_pretrained(self, model_id: str = "stabilityai/stable-diffusion-2-inpainting"):
        """
        Load SD-2 inpainting pipeline weights.
        Call this after __init__ before training/inference.

        Requires: pip install diffusers transformers accelerate
        """
        from diffusers import StableDiffusionInpaintPipeline

        logger.info("Loading pretrained SD-2 inpainting from %s ...", model_id)
        dtype = torch.float16 if self.use_fp16 else torch.float32

        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False,
        )

        self._unet = pipe.unet
        self._vae = pipe.vae
        self._scheduler = pipe.scheduler

        # Freeze encoder if requested
        if self.freeze_encoder and self._unet is not None:
            frozen, trainable = 0, 0
            for name, param in self._unet.named_parameters():
                if any(k in name for k in ["down_blocks", "mid_block"]):
                    param.requires_grad = False
                    frozen += param.numel()
                else:
                    param.requires_grad = True
                    trainable += param.numel()
            logger.info(
                "U-Net: frozen=%dM, trainable=%dM params",
                frozen // 1_000_000, trainable // 1_000_000,
            )

        self._loaded = True
        logger.info("Pretrained model loaded successfully.")
        return self

    @property
    def unet(self):
        if self._unet is None:
            raise RuntimeError("Call load_pretrained() before accessing unet.")
        return self._unet

    @property
    def vae(self):
        if self._vae is None:
            raise RuntimeError("Call load_pretrained() before accessing vae.")
        return self._vae

    def encode_image(self, x: torch.Tensor) -> torch.Tensor:
        """Encode pixel-space image to VAE latent space."""
        with torch.no_grad():
            posterior = self.vae.encode(x).latent_dist
            latent = posterior.sample()
        return latent * self.vae.config.scaling_factor

    def decode_latent(self, z: torch.Tensor) -> torch.Tensor:
        """Decode VAE latent to pixel space."""
        z = z / self.vae.config.scaling_factor
        with torch.no_grad():
            image = self.vae.decode(z).sample
        return image

    def forward(
        self,
        cloudy: torch.Tensor,       # (B, C, H, W) in [-1, 1]
        mask: torch.Tensor,         # (B, 1, H, W) binary
        ref_stack: torch.Tensor,    # (B, n_refs*C, H, W)
        timestep: int = 50,
        text_embeddings: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Full forward pass.

        Args:
            cloudy:  Cloud-corrupted tile, normalised to [-1, 1].
            mask:    Binary cloud mask (1=cloud, 0=clear).
            ref_stack: Flattened temporal reference stack.
            timestep:  Diffusion timestep (0=clean, T=pure noise).
            text_embeddings: Optional CLIP text conditioning (null guidance).

        Returns:
            Reconstructed cloud-free tile in [-1, 1], shape (B, C, H, W).
        """
        if not self._loaded:
            raise RuntimeError("Call load_pretrained() before forward().")

        B, C, H, W = cloudy.shape
        device = cloudy.device
        dtype = cloudy.dtype

        # ── 1. Encode to latent space ─────────────────────────────────────────
        cloudy_latent = self.encode_image(cloudy)           # (B, 4, H/8, W/8)
        masked_image = cloudy * (1.0 - mask)
        masked_latent = self.encode_image(masked_image)     # (B, 4, H/8, W/8)

        # Downsample mask to latent spatial dims
        mask_ds = F.interpolate(mask.float(), scale_factor=1/8, mode="nearest")  # (B, 1, H/8, W/8)

        # Concatenate: [noisy_latent | mask | masked_image_latent] = 9 channels
        model_input = torch.cat([cloudy_latent, mask_ds, masked_latent], dim=1)

        # ── 2. Null text conditioning ─────────────────────────────────────────
        if text_embeddings is None:
            # Use zero embeddings (unconditional) — no text prompt needed
            text_embeddings = torch.zeros(B, 77, 1024, device=device, dtype=dtype)

        # ── 3. Timestep tensor ────────────────────────────────────────────────
        t = torch.full((B,), timestep, device=device, dtype=torch.long)

        # ── 4. U-Net denoising ────────────────────────────────────────────────
        noise_pred = self.unet(
            model_input,
            t,
            encoder_hidden_states=text_embeddings,
        ).sample

        # ── 5. Reconstruct ────────────────────────────────────────────────────
        # Predicted clean latent
        pred_latent = cloudy_latent - noise_pred
        # Decode to pixel space
        output = self.decode_latent(pred_latent)

        # Composite: keep original pixels where clear, use model output on clouds
        output = output * mask + cloudy * (1.0 - mask)

        return output

    def trainable_parameters(self):
        """Return only trainable parameters for optimiser."""
        params = list(self.temporal_layers.parameters())
        params += list(self.ref_encoder.parameters())
        if self._unet is not None:
            params += [p for p in self._unet.parameters() if p.requires_grad]
        return params

    def save_checkpoint(self, path):
        """Save model state dict (trainable components only)."""
        import torch, pathlib
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        state = {
            "temporal_layers": self.temporal_layers.state_dict(),
            "ref_encoder": self.ref_encoder.state_dict(),
            "unet_decoder": {
                k: v for k, v in self.unet.state_dict().items()
                if "up_blocks" in k
            },
        }
        torch.save(state, path)
        logger.info("Saved checkpoint: %s", path)

    def load_checkpoint(self, path):
        """Load checkpoint saved by save_checkpoint()."""
        state = torch.load(path, map_location="cpu")
        self.temporal_layers.load_state_dict(state["temporal_layers"])
        self.ref_encoder.load_state_dict(state["ref_encoder"])
        if "unet_decoder" in state and self._unet is not None:
            missing, unexpected = self.unet.load_state_dict(
                state["unet_decoder"], strict=False
            )
            logger.info("U-Net decoder loaded. Missing: %d, Unexpected: %d",
                        len(missing), len(unexpected))
        logger.info("Loaded checkpoint: %s", path)
        return self
