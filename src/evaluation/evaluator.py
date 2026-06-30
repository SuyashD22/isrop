"""
src/evaluation/evaluator.py
Full evaluation pipeline on the held-out test set.
Runs inference on all test patches and aggregates metrics.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from ..data.dataset import CloudRemovalDataset
from ..models.inpainting_model import LISSClearModel
from .metrics import CloudRemovalMetrics

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Runs model inference on the validation/test set and reports aggregate metrics.

    Usage in Colab:
        evaluator = Evaluator(model, patches_dir, device="cuda")
        results = evaluator.evaluate()
        print(evaluator.metrics.format_report(results))
    """

    def __init__(
        self,
        model: LISSClearModel,
        patches_dir: Path,
        device: str = "cuda",
        batch_size: int = 4,
        n_refs: int = 3,
        split: str = "val",
    ):
        self.model = model
        self.device = device
        self.metrics = CloudRemovalMetrics(device=device)

        dataset = CloudRemovalDataset(
            patches_dir,
            split=split,
            augment=False,
            n_refs=n_refs,
        )
        self.loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=2,
            collate_fn=CloudRemovalDataset.collate_fn,
        )
        logger.info("Evaluating on %d samples [%s]", len(dataset), split)

    @torch.no_grad()
    def evaluate(self, output_dir: Optional[Path] = None) -> Dict[str, float]:
        """
        Run evaluation loop.

        Args:
            output_dir: If set, save per-patch metric JSON files here.

        Returns:
            Aggregated metrics dict.
        """
        self.model.eval()
        all_metrics: List[Dict] = []

        for batch_idx, (cloudy, mask, refs, target) in enumerate(
            tqdm(self.loader, desc="Evaluating")
        ):
            cloudy = cloudy.to(self.device)
            mask = mask.to(self.device)
            refs = refs.to(self.device)
            target = target.to(self.device)

            # Forward pass
            cloudy_m = cloudy * 2.0 - 1.0
            pred = self.model(cloudy_m, mask, refs)
            pred_01 = (pred + 1.0) / 2.0

            # Compute metrics
            batch_metrics = self.metrics.compute_all(pred_01, target, mask)
            all_metrics.append(batch_metrics)

            if output_dir:
                out_path = Path(output_dir) / f"batch_{batch_idx:04d}_metrics.json"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w") as f:
                    json.dump(batch_metrics, f, indent=2)

        # Aggregate
        aggregated = self.metrics.compute_batch_mean(all_metrics)

        print(self.metrics.format_report(aggregated))
        return aggregated

    def evaluate_single(
        self,
        cloudy: torch.Tensor,   # (C, H, W)
        mask: torch.Tensor,     # (H, W)
        refs: torch.Tensor,     # (n_refs*C, H, W)
        target: Optional[torch.Tensor] = None,  # (C, H, W)
    ) -> Dict:
        """Evaluate a single example (for demo/notebook use)."""
        self.model.eval()
        with torch.no_grad():
            # Add batch dimension
            cloudy_b = cloudy.unsqueeze(0).to(self.device)
            mask_b = mask.unsqueeze(0).unsqueeze(0).to(self.device)
            refs_b = refs.unsqueeze(0).to(self.device)

            cloudy_m = cloudy_b * 2.0 - 1.0
            pred = self.model(cloudy_m, mask_b, refs_b)
            pred_01 = (pred + 1.0) / 2.0

        result = {"output": pred_01.squeeze(0).cpu()}

        if target is not None:
            target_b = target.unsqueeze(0).to(self.device)
            batch_metrics = self.metrics.compute_all(pred_01, target_b, mask_b)
            result["metrics"] = batch_metrics

        return result
