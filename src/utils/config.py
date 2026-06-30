"""
src/utils/config.py
Central configuration dataclass for LISSclear.
Import this everywhere — single source of truth for all paths and hyperparameters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Config:
    # ── Root paths ────────────────────────────────────────────────────────────
    root: Path = Path(".")

    # Raw data
    raw_liss4: Path = field(default_factory=lambda: Path("data/raw/liss4"))
    raw_sentinel2: Path = field(default_factory=lambda: Path("data/raw/sentinel2"))
    raw_sen12ms: Path = field(default_factory=lambda: Path("data/raw/sen12ms"))

    # Processed data
    processed_patches: Path = field(
        default_factory=lambda: Path("data/processed/patches")
    )
    metadata_json: Path = field(
        default_factory=lambda: Path("data/processed/metadata.json")
    )

    # Checkpoints
    checkpoints: Path = field(default_factory=lambda: Path("data/checkpoints"))
    cloud_seg_ckpt: Path = field(
        default_factory=lambda: Path("data/checkpoints/cloud_seg")
    )
    inpainting_ckpt: Path = field(
        default_factory=lambda: Path("data/checkpoints/inpainting")
    )

    # ── Patch extraction ──────────────────────────────────────────────────────
    patch_size: int = 256
    stride: int = 128
    min_cloud_coverage: float = 0.15   # min 15% cloud to include patch
    max_cloud_coverage: float = 0.90   # max 90% — too cloudy = unusable

    # ── Bands ─────────────────────────────────────────────────────────────────
    # Sentinel-2 L2A 10 m bands (1-indexed): B4=Red, B3=Green, B2=Blue, B8=NIR
    optical_bands: List[int] = field(default_factory=lambda: [4, 3, 2, 8])
    n_reference_frames: int = 3

    # ── Training ──────────────────────────────────────────────────────────────
    batch_size: int = 4
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    num_epochs: int = 30
    train_ratio: float = 0.85
    grad_clip: float = 1.0
    mixed_precision: bool = True       # fp16 for Colab T4

    # ── Device ────────────────────────────────────────────────────────────────
    device: str = "cuda"

    # ── Model ─────────────────────────────────────────────────────────────────
    latent_channels: int = 4
    image_size: int = 256
    unet_base_channels: int = 320
    n_temporal_heads: int = 8
    freeze_encoder: bool = True        # Only fine-tune U-Net decoder
    diffusion_timesteps: int = 50

    # ── Loss weights ──────────────────────────────────────────────────────────
    loss_weights: dict = field(
        default_factory=lambda: {"l1": 1.0, "ssim": 0.3, "sam": 0.1}
    )

    # ── Pretrained model ──────────────────────────────────────────────────────
    sd2_model_id: str = "stabilityai/stable-diffusion-2-inpainting"

    # ── Colab ─────────────────────────────────────────────────────────────────
    # Set GDRIVE_CHECKPOINT_DIR in .env when running in Colab
    gdrive_checkpoint_dir: str = "/content/drive/MyDrive/lissclear/checkpoints"

    def __post_init__(self):
        """Resolve relative paths against root."""
        for attr in [
            "raw_liss4", "raw_sentinel2", "raw_sen12ms",
            "processed_patches", "metadata_json",
            "checkpoints", "cloud_seg_ckpt", "inpainting_ckpt",
        ]:
            val = getattr(self, attr)
            if not val.is_absolute():
                setattr(self, attr, self.root / val)


# Default config instance — override fields as needed
default_config = Config()
