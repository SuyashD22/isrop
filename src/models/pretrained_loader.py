"""
src/models/pretrained_loader.py
Utilities for loading, verifying, and fine-tuning pretrained model weights.
Handles SD-2 inpainting checkpoint download + partial weight injection.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import torch

logger = logging.getLogger(__name__)


class PretrainedLoader:
    """
    Manages pretrained model weight loading and Hugging Face Hub integration.

    Handles:
    - Initial SD-2 weight download from HF Hub
    - Checkpoint resume (Colab session crash recovery)
    - Upload trained weights to HF Hub for deployment
    """

    # Hugging Face model IDs
    SD2_INPAINTING_ID = "stabilityai/stable-diffusion-2-inpainting"

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        hf_token: Optional[str] = None,
    ):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.hf_token = hf_token

    def load_sd2_unet(self, device: str = "cuda") -> "UNet2DConditionModel":
        """
        Load SD-2 inpainting U-Net weights from Hugging Face Hub.

        The SD-2 inpainting U-Net has 9 input channels (4+1+4) by design,
        exactly matching our required architecture.
        """
        from diffusers import UNet2DConditionModel

        logger.info("Downloading SD-2 inpainting U-Net from HF Hub...")
        unet = UNet2DConditionModel.from_pretrained(
            self.SD2_INPAINTING_ID,
            subfolder="unet",
            torch_dtype=torch.float32,
            cache_dir=str(self.cache_dir) if self.cache_dir else None,
            token=self.hf_token,
        )
        unet = unet.to(device)
        logger.info("U-Net loaded. Parameters: %.1fM", self._count_params(unet) / 1e6)
        return unet

    def load_sd2_vae(self, device: str = "cuda") -> "AutoencoderKL":
        """Load SD-2 VAE for image encoding/decoding."""
        from diffusers import AutoencoderKL

        logger.info("Downloading SD-2 VAE from HF Hub...")
        vae = AutoencoderKL.from_pretrained(
            self.SD2_INPAINTING_ID,
            subfolder="vae",
            torch_dtype=torch.float32,
            cache_dir=str(self.cache_dir) if self.cache_dir else None,
            token=self.hf_token,
        )
        return vae.to(device)

    def resume_from_checkpoint(
        self,
        model: "LISSClearModel",
        checkpoint_dir: Path,
    ) -> int:
        """
        Resume training from latest checkpoint in checkpoint_dir.
        Handles Colab session crashes gracefully.

        Returns:
            Starting epoch number (0 if no checkpoint found).
        """
        checkpoint_dir = Path(checkpoint_dir)
        checkpoints = sorted(checkpoint_dir.glob("ckpt_epoch*.pt"))

        if not checkpoints:
            logger.info("No checkpoint found in %s — starting from scratch.", checkpoint_dir)
            return 0

        latest = checkpoints[-1]
        epoch_num = int(latest.stem.split("epoch")[-1])
        logger.info("Resuming from checkpoint: %s (epoch %d)", latest.name, epoch_num)

        model.load_checkpoint(latest)
        return epoch_num + 1

    def upload_to_hf_hub(
        self,
        checkpoint_path: Path,
        repo_id: str,
        commit_message: str = "Upload LISSclear checkpoint",
    ) -> str:
        """
        Upload trained checkpoint to Hugging Face Hub.
        Requires: pip install huggingface_hub

        Args:
            checkpoint_path: Local path to .pt checkpoint file.
            repo_id:         HF repo (e.g. 'yourname/lissclear').
            commit_message:  Git commit message.

        Returns:
            URL of uploaded file.
        """
        from huggingface_hub import HfApi

        api = HfApi(token=self.hf_token)

        # Create repo if it doesn't exist
        try:
            api.create_repo(repo_id, repo_type="model", exist_ok=True)
        except Exception:
            pass

        url = api.upload_file(
            path_or_fileobj=str(checkpoint_path),
            path_in_repo=checkpoint_path.name,
            repo_id=repo_id,
            commit_message=commit_message,
        )
        logger.info("Uploaded checkpoint to: %s", url)
        return url

    @staticmethod
    def _count_params(model: torch.nn.Module) -> int:
        return sum(p.numel() for p in model.parameters())

    @staticmethod
    def get_colab_resume_snippet() -> str:
        """Print Colab-ready code snippet for checkpoint resumption."""
        return '''
# ── Colab Checkpoint Resume ──────────────────────────────────────────────────
from google.colab import drive
drive.mount("/content/drive")

import shutil
from pathlib import Path

GDRIVE_CKPT_DIR = Path("/content/drive/MyDrive/lissclear/checkpoints")
LOCAL_CKPT_DIR = Path("data/checkpoints/inpainting")
LOCAL_CKPT_DIR.mkdir(parents=True, exist_ok=True)

# Copy latest checkpoint from Drive to local (faster I/O during training)
for ckpt in sorted(GDRIVE_CKPT_DIR.glob("*.pt")):
    shutil.copy(ckpt, LOCAL_CKPT_DIR / ckpt.name)
    print(f"Restored: {ckpt.name}")

from src.models.inpainting_model import LISSClearModel
from src.models.pretrained_loader import PretrainedLoader

model = LISSClearModel(n_refs=3).load_pretrained()
loader = PretrainedLoader()
start_epoch = loader.resume_from_checkpoint(model, LOCAL_CKPT_DIR)
print(f"Resuming from epoch {start_epoch}")
'''
