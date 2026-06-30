"""
src/training/trainer.py
Training loop for LISSclear with:
  - Mixed precision (fp16) support via torch.cuda.amp
  - Cosine annealing LR scheduler
  - Checkpoint saving every 5 epochs (Colab crash recovery)
  - Best-model tracking by validation loss
  - Structured JSON training history for live loss plotting
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm

from ..data.dataset import CloudRemovalDataset
from ..models.inpainting_model import LISSClearModel
from ..models.pretrained_loader import PretrainedLoader
from ..utils.config import Config
from .loss import CloudRemovalLoss
from .scheduler import build_scheduler

logger = logging.getLogger(__name__)


class Trainer:
    """
    Training loop for the LISSclear multi-temporal diffusion model.

    Designed for Google Colab T4 GPU:
    - Mixed precision (fp16) to fit model + batch in 16GB VRAM
    - Checkpoint every 5 epochs + best model
    - Automatic Google Drive backup (optional)
    - Graceful resume from checkpoint on session restart
    """

    def __init__(self, config: Config):
        self.config = config
        self.device = torch.device(config.device)
        self.use_amp = config.mixed_precision and torch.cuda.is_available()
        self.scaler = GradScaler(enabled=self.use_amp)

        # ── Model ─────────────────────────────────────────────────────────────
        logger.info("Building model...")
        self.model = LISSClearModel(
            n_refs=config.n_reference_frames,
            freeze_encoder=config.freeze_encoder,
            use_fp16=self.use_amp,
        )
        self.model.load_pretrained(config.sd2_model_id)
        self.model = self.model.to(self.device)

        # ── Loss + Optimiser ──────────────────────────────────────────────────
        self.loss_fn = CloudRemovalLoss(
            w_l1=config.loss_weights["l1"],
            w_ssim=config.loss_weights["ssim"],
            w_sam=config.loss_weights["sam"],
        )
        self.optimizer = AdamW(
            self.model.trainable_parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
            betas=(0.9, 0.999),
            eps=1e-8,
        )
        self.scheduler = build_scheduler(
            self.optimizer,
            num_epochs=config.num_epochs,
            warmup_epochs=2,
        )

        # ── Data ──────────────────────────────────────────────────────────────
        logger.info("Building datasets...")
        train_ds = CloudRemovalDataset(
            config.processed_patches, split="train",
            train_ratio=config.train_ratio,
            augment=True,
            n_refs=config.n_reference_frames,
        )
        val_ds = CloudRemovalDataset(
            config.processed_patches, split="val",
            train_ratio=config.train_ratio,
            augment=False,
            n_refs=config.n_reference_frames,
        )

        self.train_loader = DataLoader(
            train_ds,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True,
            collate_fn=CloudRemovalDataset.collate_fn,
        )
        self.val_loader = DataLoader(
            val_ds,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True,
            collate_fn=CloudRemovalDataset.collate_fn,
        )

        # ── State ─────────────────────────────────────────────────────────────
        self.start_epoch = 0
        self.best_val_loss = float("inf")
        self.history: list[dict] = []

        # Resume from checkpoint if available
        loader = PretrainedLoader()
        self.start_epoch = loader.resume_from_checkpoint(
            self.model, config.inpainting_ckpt
        )

    # ── Training ──────────────────────────────────────────────────────────────

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        self.model.train()
        totals = {"total": 0.0, "l1": 0.0, "ssim": 0.0, "sam": 0.0}
        n_batches = len(self.train_loader)

        pbar = tqdm(self.train_loader, desc=f"Train epoch {epoch+1}", leave=False)
        for cloudy, mask, refs, target in pbar:
            cloudy = cloudy.to(self.device)
            mask = mask.to(self.device)
            refs = refs.to(self.device)
            target = target.to(self.device)

            self.optimizer.zero_grad()

            with autocast(enabled=self.use_amp):
                # Convert to model input range [-1, 1]
                cloudy_m = cloudy * 2.0 - 1.0
                pred = self.model(cloudy_m, mask, refs)
                pred_01 = (pred + 1.0) / 2.0  # back to [0, 1] for loss

                losses = self.loss_fn(pred_01, target, mask)

            self.scaler.scale(losses["total"]).backward()
            self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(
                self.model.trainable_parameters(), self.config.grad_clip
            )
            self.scaler.step(self.optimizer)
            self.scaler.update()

            for k in totals:
                totals[k] += losses[k] if isinstance(losses[k], float) else losses[k].item()

            pbar.set_postfix(loss=f"{losses['total'].item():.4f}")

        return {k: v / n_batches for k, v in totals.items()}

    def val_epoch(self, epoch: int) -> Dict[str, float]:
        self.model.eval()
        totals = {"total": 0.0, "l1": 0.0, "ssim": 0.0, "sam": 0.0}
        n_batches = len(self.val_loader)

        with torch.no_grad():
            for cloudy, mask, refs, target in tqdm(
                self.val_loader, desc=f"  Val epoch {epoch+1}", leave=False
            ):
                cloudy = cloudy.to(self.device)
                mask = mask.to(self.device)
                refs = refs.to(self.device)
                target = target.to(self.device)

                with autocast(enabled=self.use_amp):
                    cloudy_m = cloudy * 2.0 - 1.0
                    pred = self.model(cloudy_m, mask, refs)
                    pred_01 = (pred + 1.0) / 2.0
                    losses = self.loss_fn(pred_01, target, mask)

                for k in totals:
                    totals[k] += losses[k] if isinstance(losses[k], float) else losses[k].item()

        return {k: v / n_batches for k, v in totals.items()}

    # ── Main loop ─────────────────────────────────────────────────────────────

    def fit(
        self,
        gdrive_backup_dir: Optional[Path] = None,
    ):
        """
        Run the full training loop.

        Args:
            gdrive_backup_dir: If set, copies checkpoints to Google Drive after each save.
                               Use '/content/drive/MyDrive/lissclear/checkpoints' in Colab.
        """
        logger.info("Starting training from epoch %d / %d", self.start_epoch, self.config.num_epochs)
        logger.info("Training on %s | AMP=%s", self.device, self.use_amp)

        for epoch in range(self.start_epoch, self.config.num_epochs):
            t0 = time.time()

            train_metrics = self.train_epoch(epoch)
            val_metrics = self.val_epoch(epoch)
            self.scheduler.step()

            elapsed = time.time() - t0
            lr = self.optimizer.param_groups[0]["lr"]

            # ── Log ───────────────────────────────────────────────────────────
            record = {
                "epoch": epoch,
                "lr": lr,
                "time_s": round(elapsed, 1),
                "train": train_metrics,
                "val": val_metrics,
            }
            self.history.append(record)

            print(
                f"Epoch {epoch+1:02d}/{self.config.num_epochs} | "
                f"train={train_metrics['total']:.4f} "
                f"val={val_metrics['total']:.4f} | "
                f"lr={lr:.2e} | {elapsed:.0f}s"
            )

            # ── Save history JSON ─────────────────────────────────────────────
            history_path = self.config.inpainting_ckpt / "training_history.json"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, "w") as f:
                json.dump(self.history, f, indent=2)

            # ── Best model ────────────────────────────────────────────────────
            if val_metrics["total"] < self.best_val_loss:
                self.best_val_loss = val_metrics["total"]
                best_path = self.config.inpainting_ckpt / "best_model.pt"
                self.model.save_checkpoint(best_path)
                logger.info("New best model saved (val_loss=%.4f)", self.best_val_loss)

                if gdrive_backup_dir:
                    self._backup_to_drive(best_path, gdrive_backup_dir)

            # ── Periodic checkpoint (crash recovery) ──────────────────────────
            if (epoch + 1) % 5 == 0:
                ckpt_path = self.config.inpainting_ckpt / f"ckpt_epoch{epoch}.pt"
                self.model.save_checkpoint(ckpt_path)

                if gdrive_backup_dir:
                    self._backup_to_drive(ckpt_path, gdrive_backup_dir)

        logger.info("Training complete. Best val loss: %.4f", self.best_val_loss)

    @staticmethod
    def _backup_to_drive(local_path: Path, drive_dir: Path):
        """Copy checkpoint to Google Drive (Colab persistence)."""
        drive_dir = Path(drive_dir)
        drive_dir.mkdir(parents=True, exist_ok=True)
        dest = drive_dir / local_path.name
        shutil.copy2(str(local_path), str(dest))
        logger.info("Backed up to Drive: %s", dest)
