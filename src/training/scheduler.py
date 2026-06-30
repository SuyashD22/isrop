"""
src/training/scheduler.py
Learning rate scheduler configuration for LISSclear training.

Uses cosine annealing with warm restarts — standard for diffusion fine-tuning.
Also includes linear warmup to avoid early training instability.
"""

from __future__ import annotations

import math

import torch
from torch.optim import Optimizer
from torch.optim.lr_scheduler import (
    CosineAnnealingLR,
    CosineAnnealingWarmRestarts,
    LambdaLR,
    SequentialLR,
)


def build_scheduler(
    optimizer: Optimizer,
    num_epochs: int,
    warmup_epochs: int = 2,
    min_lr_ratio: float = 0.01,
    restart_period: Optional[int] = None,
) -> "SequentialLR | CosineAnnealingLR":
    """
    Build a learning rate scheduler with optional linear warmup.

    Args:
        optimizer:      PyTorch optimizer.
        num_epochs:     Total training epochs.
        warmup_epochs:  Number of linear warmup epochs.
        min_lr_ratio:   Minimum LR as fraction of base LR.
        restart_period: If set, use cosine annealing with warm restarts every N epochs.

    Returns:
        Learning rate scheduler.
    """
    if warmup_epochs > 0:
        # Phase 1: Linear warmup
        warmup_scheduler = LambdaLR(
            optimizer,
            lr_lambda=lambda epoch: (epoch + 1) / warmup_epochs,
        )

        # Phase 2: Cosine annealing after warmup
        if restart_period:
            cosine_scheduler = CosineAnnealingWarmRestarts(
                optimizer,
                T_0=restart_period,
                T_mult=2,
                eta_min=optimizer.param_groups[0]["lr"] * min_lr_ratio,
            )
        else:
            cosine_scheduler = CosineAnnealingLR(
                optimizer,
                T_max=num_epochs - warmup_epochs,
                eta_min=optimizer.param_groups[0]["lr"] * min_lr_ratio,
            )

        return SequentialLR(
            optimizer,
            schedulers=[warmup_scheduler, cosine_scheduler],
            milestones=[warmup_epochs],
        )
    else:
        if restart_period:
            return CosineAnnealingWarmRestarts(
                optimizer,
                T_0=restart_period,
                T_mult=2,
                eta_min=optimizer.param_groups[0]["lr"] * min_lr_ratio,
            )
        return CosineAnnealingLR(
            optimizer,
            T_max=num_epochs,
            eta_min=optimizer.param_groups[0]["lr"] * min_lr_ratio,
        )


# Type hint fix
from typing import Optional


def get_cosine_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    num_cycles: float = 0.5,
    last_epoch: int = -1,
) -> LambdaLR:
    """
    Hugging Face-style cosine schedule with warmup (step-based, not epoch-based).
    Use this when training with gradient accumulation.

    Args:
        num_warmup_steps:    Number of warmup steps.
        num_training_steps:  Total training steps.
        num_cycles:          Number of cosine cycles (0.5 = half cosine decay).
    """
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(
            max(1, num_training_steps - num_warmup_steps)
        )
        return max(
            0.0,
            0.5 * (1.0 + math.cos(math.pi * num_cycles * 2.0 * progress)),
        )

    return LambdaLR(optimizer, lr_lambda, last_epoch=last_epoch)
