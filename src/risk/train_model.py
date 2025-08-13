from __future__ import annotations

from pathlib import Path
from typing import Dict

import torch
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.models.temporal_fusion_transformer import TemporalFusionTransformer
from pytorch_forecasting.metrics import QuantileLoss
from lightning.pytorch import Trainer

from src.config import MODELS_DIR


def train_quantile_rnn(training: TimeSeriesDataSet, validation: TimeSeriesDataSet, symbol: str, max_epochs: int = 5) -> Path:
    dataloaders = {
        "train": training.to_dataloader(train=True, batch_size=64, num_workers=0),
        "val": validation.to_dataloader(train=False, batch_size=64, num_workers=0),
    }

    model = TemporalFusionTransformer.from_dataset(
        training,
        learning_rate=1e-3,
        hidden_size=64,
        attention_head_size=2,
        dropout=0.1,
        loss=QuantileLoss(quantiles=[0.05, 0.5, 0.95]),
        hidden_continuous_size=16,
        output_size=3,  # 三個分位數
    )

    trainer = Trainer(
        max_epochs=max_epochs,
        accelerator="cpu",
        log_every_n_steps=10,
        enable_progress_bar=True,
    )
    trainer.fit(model, train_dataloaders=dataloaders["train"], val_dataloaders=dataloaders["val"])

    model_dir = MODELS_DIR / symbol
    model_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = model_dir / "tft_quantile.ckpt"
    trainer.save_checkpoint(ckpt_path.as_posix())
    return ckpt_path


__all__ = ["train_quantile_rnn"]
