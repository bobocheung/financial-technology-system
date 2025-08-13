from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd
import plotly.graph_objects as go

from src.config import OUTPUTS_DIR


def kline_with_mas(
    df: pd.DataFrame,
    symbol: str,
    ma_periods: Iterable[int] = (20, 60, 120),
    explain: bool = False,
    show_signals: bool = True,
    show_trade_pnl: bool = True,
    overlay_indicators: Iterable[str] | None = None,
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

    # 額外疊加指標
    overlays = set((overlay_indicators or []))
    if "EMA" in overlays:
        import pandas as pd
        for p in ma_periods:
            df[f"ema{p}"] = df["close"].ewm(span=p, adjust=False).mean()
            fig.add_trace(go.Scatter(x=df["date"], y=df[f"ema{p}"], name=f"EMA{p}", line=dict(dash="dot")))
    if "BOLL" in overlays:
        import pandas as pd
        p = min(list(ma_periods))
        ma = df["close"].rolling(p).mean()
        std = df["close"].rolling(p).std()
        upper = ma + 2 * std
        lower = ma - 2 * std
        fig.add_trace(go.Scatter(x=df["date"], y=upper, name=f"BOLL上軌", line=dict(color="#888")))
        fig.add_trace(go.Scatter(x=df["date"], y=lower, name=f"BOLL下軌", line=dict(color="#888")))
    if "RSI" in overlays:
        # 在副圖用 RSI
        delta = df["close"].diff()
        gain = (delta.clip(lower=0)).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-9)
        rsi = 100 - 100 / (1 + rs)
        fig.add_trace(go.Scatter(x=df["date"], y=rsi, name="RSI(14)", yaxis="y2"))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0,100], showgrid=False, title="RSI"))

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

        if show_signals:
            # 在收盤價上標註買賣箭頭
            buy_pts = df.loc[cross_up, ["date", "close"]]
            sell_pts = df.loc[cross_dn, ["date", "close"]]
            fig.add_trace(go.Scatter(
                x=buy_pts["date"], y=buy_pts["close"], mode="markers+text",
                marker=dict(symbol="triangle-up", color="#2ecc71", size=12),
                text=["買" for _ in range(len(buy_pts))], textposition="top center",
                name="買進",
                hovertemplate="買進 @ %{y:.2f}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=sell_pts["date"], y=sell_pts["close"], mode="markers+text",
                marker=dict(symbol="triangle-down", color="#e74c3c", size=12),
                text=["賣" for _ in range(len(sell_pts))], textposition="bottom center",
                name="賣出",
                hovertemplate="賣出 @ %{y:.2f}<extra></extra>",
            ))

        if show_trade_pnl:
            # 計算每筆多頭交易的盈虧，並在區間中點標註百分比
            entry_idx = None
            for i in range(len(df)):
                if cross_up.iloc[i] and entry_idx is None:
                    entry_idx = i
                elif cross_dn.iloc[i] and entry_idx is not None:
                    seg = df.iloc[entry_idx:i + 1]
                    entry_price = float(seg.iloc[0]["close"])
                    exit_price = float(seg.iloc[-1]["close"])
                    pnl = (exit_price / max(1e-9, entry_price)) - 1.0
                    mid = seg.iloc[len(seg) // 2]
                    # 期間陰影帶
                    fig.add_vrect(
                        x0=seg.iloc[0]["date"], x1=seg.iloc[-1]["date"],
                        fillcolor="#C9F7CA" if pnl >= 0 else "#FAD4D4",
                        opacity=0.12, line_width=0, layer="below",
                    )
                    fig.add_annotation(
                        x=mid["date"], y=float(seg["close"].median()),
                        text=f"{pnl*100:.1f}%",
                        showarrow=False,
                        bgcolor="#ECFDF3" if pnl >= 0 else "#FDECEC",
                        bordercolor="#2ECC71" if pnl >= 0 else "#E74C3C",
                        borderwidth=1,
                        opacity=0.9,
                    )
                    # 區間最大回撤
                    cummax = seg["close"].cummax()
                    dd = (seg["close"] / cummax - 1.0).min()
                    fig.add_annotation(
                        x=seg.iloc[-1]["date"], y=float(seg["close"].min()),
                        text=f"DD {dd*100:.1f}%",
                        showarrow=False, bgcolor="#FFF7E6", bordercolor="#F5A623",
                        borderwidth=1, opacity=0.9,
                    )
                    entry_idx = None

    fig.update_layout(
        title=f"{symbol} K線與均線",
        xaxis_title="日期",
        yaxis_title="價格",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        legend_title_text="圖例",
    )
    # 加入更友善的新手引導敘述
    fig.add_annotation(
        text="K線：每根顯示一日的開盤/最高/最低/收盤。 均線：MA20/60/120 是收盤價的移動平均，短線上穿長線常被視為趨勢轉強的訊號。 互動：滑鼠移動可查看 OHLC，點擊圖例可顯示/隱藏線。",
        xref="paper", yref="paper", x=0, y=1.05, showarrow=False, align="left",
        bgcolor="#ffffff", bordercolor="#d9d9d9", borderwidth=1, opacity=0.95
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
