from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd
import plotly.graph_objects as go

from src.config import OUTPUTS_DIR


def kline_with_mas(
    df: pd.DataFrame,
    symbol: str,
    ma_periods: Iterable[int] = (20, 60, 120),
    explain: bool = False,
) -> Path:
    df = df.copy().sort_values("date")
    for p in ma_periods:
        df[f"ma{p}"] = df["close"].rolling(p).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name="K線"
        )
    )
    for p in ma_periods:
        fig.add_trace(
            go.Scatter(x=df["date"], y=df[f"ma{p}"], name=f"MA{p}")
        )

    # 均線交叉點提示：以最短與最長均線示範
    if len(list(ma_periods)) >= 2:
        mas = sorted(list(ma_periods))
        short, long = mas[0], mas[-1]
        s = df[f"ma{short}"]
        l = df[f"ma{long}"]
        cross_up = (s.shift(1) <= l.shift(1)) & (s > l)
        cross_dn = (s.shift(1) >= l.shift(1)) & (s < l)
        up_points = df.loc[cross_up, ["date", f"ma{short}"]]
        dn_points = df.loc[cross_dn, ["date", f"ma{short}"]]
        fig.add_trace(go.Scatter(
            x=up_points["date"], y=up_points[f"ma{short}"],
            mode="markers", marker=dict(color="green", size=8, symbol="triangle-up"),
            name="黃金交叉",
            hovertemplate="日期=%{x}<br>短均線上穿長均線：可能趨勢轉強<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=dn_points["date"], y=dn_points[f"ma{short}"],
            mode="markers", marker=dict(color="red", size=8, symbol="triangle-down"),
            name="死亡交叉",
            hovertemplate="日期=%{x}<br>短均線下穿長均線：可能趨勢轉弱<extra></extra>",
        ))

    fig.update_layout(
        title=f"{symbol} K線與均線",
        xaxis_title="日期",
        yaxis_title="價格",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        legend_title_text="圖例",
    )

    if explain:
        notes = (
            "K線：每根顯示一日的開盤/最高/最低/收盤。\n"
            "均線：MA20/60/120 是收盤價的移動平均，短線上穿長線常被視為趨勢轉強的訊號。\n"
            "互動：滑鼠移動可查看 OHLC，點擊圖例可顯示/隱藏線。"
        )
        fig.add_annotation(
            text=notes,
            xref="paper", yref="paper",
            x=0.01, y=0.99, showarrow=False,
            align="left",
            bordercolor="#C7C7C7", borderwidth=1,
            bgcolor="#F9F9F9", opacity=0.9,
        )

    out_path = OUTPUTS_DIR / f"chart_{symbol}.html"
    fig.write_html(out_path)
    return out_path


__all__ = ["kline_with_mas"]
