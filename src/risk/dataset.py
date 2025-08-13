from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import torch
from pytorch_forecasting import TimeSeriesDataSet


@dataclass
class RiskDataConfig:
    time_idx: str = "time_idx"
    target: str = "return"
    group_id: str = "symbol_id"
    max_encoder_length: int = 60
    max_prediction_length: int = 1


def prepare_dataset(df: pd.DataFrame, symbol: str, config: RiskDataConfig | None = None) -> Tuple[TimeSeriesDataSet, TimeSeriesDataSet, Dict[str, int]]:
    if config is None:
        config = RiskDataConfig()

    data = df.copy().sort_values("date").reset_index(drop=True)
    data[config.group_id] = 0  # 單一標的
    data[config.time_idx] = (data.index + 1).astype(int)

    # 使用對數報酬（可避免價位尺度差異），加上 1e-9 防止 log(0)
    data[config.target] = (data["close"].pct_change().fillna(0.0)).astype("float32")

    # 特徵：價格與成交量的標準化（簡化示例）
    for col in ["open", "high", "low", "close", "volume"]:
        mean = float(data[col].mean())
        std = float(data[col].std() or 1.0)
        data[f"{col}_norm"] = ((data[col] - mean) / std).astype("float32")

    training_cutoff = data[config.time_idx].max() - config.max_prediction_length

    training = TimeSeriesDataSet(
        data[lambda x: x[config.time_idx] <= training_cutoff],
        time_idx=config.time_idx,
        target=config.target,
        group_ids=[config.group_id],
        max_encoder_length=config.max_encoder_length,
        max_prediction_length=config.max_prediction_length,
        time_varying_known_reals=[config.time_idx],
        # 為符合 RecurrentNetwork 要求（encoder/decoder 變數一致），僅保留 target 作為 unknown
        time_varying_unknown_reals=[config.target],
        target_normalizer=None,
    )

    validation = TimeSeriesDataSet.from_dataset(training, data, min_prediction_idx=training_cutoff + 1)
    return training, validation, {symbol: 0}


__all__ = ["RiskDataConfig", "prepare_dataset"]
