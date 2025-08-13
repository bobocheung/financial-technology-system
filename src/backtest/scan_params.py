from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
import pandas as pd


def _sma_vectorized(df: pd.DataFrame, fast: int, slow: int, commission: float = 0.0) -> pd.DataFrame:
    data = df.copy().sort_values("date")
    data["fast"] = data["close"].rolling(fast).mean()
    data["slow"] = data["close"].rolling(slow).mean()
    signal = (data["fast"] > data["slow"]).astype(int)
    position = signal.shift(1).fillna(0)
    ret = data["close"].pct_change().fillna(0.0)
    trade_change = position.diff().abs().fillna(0.0)
    cost = trade_change * commission
    strat_ret = position * ret - cost
    data["strat_ret"] = strat_ret
    data["equity"] = (1.0 + strat_ret).cumprod()
    return data


def _max_drawdown(equity: pd.Series) -> float:
    cummax = equity.cummax()
    dd = equity / cummax - 1.0
    return float(dd.min())


def scan_sma_grid(
    df: pd.DataFrame,
    fast_grid: Iterable[int],
    slow_grid: Iterable[int],
    commission: float = 0.001,
) -> pd.DataFrame:
    rows = []
    price_ret = df["close"].pct_change().dropna()
    daily_vol = float(price_ret.std())
    ann = np.sqrt(252)
    for f in fast_grid:
        for s in slow_grid:
            if f >= s:
                continue
            sim = _sma_vectorized(df, f, s, commission=commission)
            r = sim["strat_ret"].dropna()
            if len(r) < 10:
                continue
            mean = float(r.mean())
            std = float(r.std() or 1e-9)
            sharpe = (mean / std) * ann
            mdd = _max_drawdown(sim["equity"].fillna(1.0))
            rows.append(dict(fast=f, slow=s, sharpe=sharpe, max_dd=mdd))
    return pd.DataFrame(rows)

