from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
import torch
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.models.temporal_fusion_transformer import TemporalFusionTransformer

from src.config import OUTPUTS_DIR


def predict_next_day_quantiles(dataset: TimeSeriesDataSet, ckpt_path: Path) -> pd.DataFrame:
    model = TemporalFusionTransformer.load_from_checkpoint(ckpt_path.as_posix())
    model.eval()

    # 取 validation dataloader 的最後一批（含未來一步）
    dl = dataset.to_dataloader(train=False, batch_size=64, num_workers=0)
    model.cpu()
    model.eval()
    batch = list(dl)[-1]
    x, y = batch
    with torch.no_grad():
        out = model(x)
    # out 是一個包含 'prediction' 的 Output 物件
    pred = out["prediction"]  # Tensor 或 ndarray-like
    arr = pred.detach().cpu().numpy()
    # 形狀可能為 (batch, pred_len, n_quantiles) 或 (batch, n_quantiles)
    if arr.ndim == 3:
        y_hat = arr[0, -1, :]
    elif arr.ndim == 2:
        y_hat = arr[0, :]
    else:
        y_hat = arr.reshape(-1)
    quantiles = getattr(model.loss, "quantiles", [0.05, 0.5, 0.95])
    result = pd.DataFrame({"quantile": quantiles, "prediction": y_hat[: len(quantiles)]})
    return result


def save_quantile_table(result: pd.DataFrame, symbol: str) -> Path:
    out_path = OUTPUTS_DIR / f"risk_quantiles_{symbol}.csv"
    result.to_csv(out_path, index=False)
    return out_path


def conservative_position_limit_from_quantiles(result: pd.DataFrame) -> float:
    """根據分位數結果回傳建議單筆倉位上限（0~1）。
    - 若 5% 分位數小於 -2%：風險偏高，上限 0.05
    - 若 5% 在 -2%~0%：中性，上限 0.10
    - 否則：較樂觀，上限 0.20
    """
    qmap = {float(q): float(v) for q, v in zip(result["quantile"], result["prediction"])}
    q05 = qmap.get(0.05) or qmap.get(0.1) or 0.0
    if q05 <= -0.02:
        return 0.05
    if q05 <= 0.0:
        return 0.10
    return 0.20


__all__ = ["predict_next_day_quantiles", "save_quantile_table"]
