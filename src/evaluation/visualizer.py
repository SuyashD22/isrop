"""
src/evaluation/visualizer.py
Generate comparison figures for report and demo.
Produces side-by-side plots: Cloudy | Cloud Mask | Predicted | Ground Truth
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import torch


matplotlib.use("Agg")  # Non-interactive backend — works on Colab + server


class ResultVisualizer:
    """
    Create publication-quality comparison figures for cloud removal results.
    """

    def __init__(
        self,
        output_dir: Path = Path("outputs/figures"),
        dpi: int = 150,
        fig_size: tuple = (16, 4),
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        self.fig_size = fig_size

    def comparison_figure(
        self,
        cloudy: np.ndarray,     # (C, H, W) float32
        cloud_mask: np.ndarray, # (H, W) binary
        predicted: np.ndarray,  # (C, H, W) float32
        target: Optional[np.ndarray] = None,  # (C, H, W) float32
        metrics: Optional[Dict] = None,
        title: str = "Cloud Removal Result",
        save_name: Optional[str] = None,
    ) -> plt.Figure:
        """
        4-panel figure: Cloudy | Mask | Predicted | Ground Truth (if available).
        """
        n_panels = 4 if target is not None else 3
        fig, axes = plt.subplots(1, n_panels, figsize=self.fig_size, dpi=self.dpi)

        # ── Panel 1: Cloudy input ─────────────────────────────────────────────
        axes[0].imshow(self._to_rgb(cloudy))
        axes[0].set_title("Cloudy Input", fontsize=11, fontweight="bold")
        axes[0].axis("off")

        # ── Panel 2: Cloud mask ────────────────────────────────────────────────
        axes[1].imshow(cloud_mask, cmap="hot", vmin=0, vmax=1)
        cov = float(cloud_mask.mean()) * 100
        axes[1].set_title(f"Cloud Mask ({cov:.0f}% coverage)", fontsize=11, fontweight="bold")
        axes[1].axis("off")

        # ── Panel 3: Predicted ────────────────────────────────────────────────
        axes[2].imshow(self._to_rgb(predicted))
        if metrics:
            subtitle = f"SSIM={metrics.get('ssim','?'):.3f}  PSNR={metrics.get('psnr','?'):.1f}dB  SAM={metrics.get('sam','?'):.3f}"
            axes[2].set_title(f"Predicted\n{subtitle}", fontsize=9, fontweight="bold")
        else:
            axes[2].set_title("Predicted", fontsize=11, fontweight="bold")
        axes[2].axis("off")

        # ── Panel 4: Ground truth ─────────────────────────────────────────────
        if target is not None:
            axes[3].imshow(self._to_rgb(target))
            axes[3].set_title("Ground Truth", fontsize=11, fontweight="bold")
            axes[3].axis("off")

        fig.suptitle(title, fontsize=13, fontweight="bold", y=1.02)
        plt.tight_layout()

        if save_name:
            save_path = self.output_dir / f"{save_name}.png"
            fig.savefig(save_path, bbox_inches="tight", dpi=self.dpi)

        return fig

    def training_curves(
        self,
        history: List[Dict],
        save_name: str = "training_curves",
    ) -> plt.Figure:
        """
        Plot train/val loss curves from training history JSON.
        """
        epochs = [h["epoch"] + 1 for h in history]
        train_loss = [h["train"]["total"] for h in history]
        val_loss = [h["val"]["total"] for h in history]

        fig, axes = plt.subplots(1, 2, figsize=(12, 4), dpi=self.dpi)

        # Total loss
        axes[0].plot(epochs, train_loss, label="Train", color="#2563EB", linewidth=2)
        axes[0].plot(epochs, val_loss, label="Val", color="#DC2626", linewidth=2, linestyle="--")
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Loss")
        axes[0].set_title("Training Loss", fontweight="bold")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Component losses (SAM highlighted)
        components = ["l1", "ssim", "sam"]
        colors = ["#059669", "#7C3AED", "#D97706"]
        for comp, color in zip(components, colors):
            vals = [h["train"][comp] for h in history]
            lw = 2.5 if comp == "sam" else 1.5
            axes[1].plot(epochs, vals, label=comp.upper(), color=color, linewidth=lw)

        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("Component Loss")
        axes[1].set_title("Loss Components (SAM highlighted)", fontweight="bold")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        save_path = self.output_dir / f"{save_name}.png"
        fig.savefig(save_path, bbox_inches="tight", dpi=self.dpi)
        return fig

    def ndvi_comparison(
        self,
        pred: np.ndarray,   # (C, H, W)
        target: np.ndarray, # (C, H, W)
        mask: np.ndarray,   # (H, W)
        red_idx: int = 0,
        nir_idx: int = 3,
        save_name: Optional[str] = None,
    ) -> plt.Figure:
        """
        NDVI comparison map — shows vegetation index accuracy.
        Key for ISRO agricultural monitoring use cases.
        """
        eps = 1e-8

        ndvi_pred = (pred[nir_idx] - pred[red_idx]) / (pred[nir_idx] + pred[red_idx] + eps)
        ndvi_tgt = (target[nir_idx] - target[red_idx]) / (target[nir_idx] + target[red_idx] + eps)
        ndvi_diff = np.abs(ndvi_pred - ndvi_tgt) * mask  # Only on cloud pixels

        fig, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=self.dpi)

        im0 = axes[0].imshow(ndvi_tgt, cmap="RdYlGn", vmin=-0.3, vmax=0.8)
        axes[0].set_title("Ground Truth NDVI", fontweight="bold")
        axes[0].axis("off")
        plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

        im1 = axes[1].imshow(ndvi_pred, cmap="RdYlGn", vmin=-0.3, vmax=0.8)
        axes[1].set_title("Predicted NDVI", fontweight="bold")
        axes[1].axis("off")
        plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

        im2 = axes[2].imshow(ndvi_diff, cmap="hot_r", vmin=0, vmax=0.2)
        mae = ndvi_diff[mask == 1].mean() if mask.sum() > 0 else 0
        axes[2].set_title(f"NDVI Error (MAE={mae:.4f})", fontweight="bold")
        axes[2].axis("off")
        plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

        plt.suptitle("NDVI Preservation Analysis", fontsize=13, fontweight="bold")
        plt.tight_layout()

        if save_name:
            save_path = self.output_dir / f"{save_name}.png"
            fig.savefig(save_path, bbox_inches="tight", dpi=self.dpi)

        return fig

    @staticmethod
    def _to_rgb(tile: np.ndarray, r: int = 0, g: int = 1, b: int = 2) -> np.ndarray:
        """Convert (C, H, W) → (H, W, 3) uint8 for display."""
        rgb = np.stack([
            np.clip(tile[r], 0, 1),
            np.clip(tile[g], 0, 1),
            np.clip(tile[b], 0, 1),
        ], axis=-1)
        return (rgb * 255).astype(np.uint8)
