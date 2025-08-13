from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt

from src.backtest.strategies import SmaCrossStrategy
from src.config import OUTPUTS_DIR


def _setup_broker(cerebro: bt.Cerebro, commission: float, slippage_bps: int, risk_pct: float) -> None:
    cerebro.broker.set_cash(100000.0)
    cerebro.broker.setcommission(commission=commission)
    if slippage_bps > 0:
        cerebro.broker.set_slippage_perc(perc=slippage_bps / 10000.0)
    # 使用百分比倉位配置（% 現金）
    percents = int(max(1, min(100, round(risk_pct * 100.0))))
    cerebro.addsizer(bt.sizers.PercentSizer, percents=percents)


def run_backtest_from_dataframe(
    df: pd.DataFrame,
    symbol: str,
    fast: int = 10,
    slow: int = 30,
    commission: float = 0.001,
    slippage_bps: int = 0,
    risk_pct: float = 0.1,
) -> Path:
    cerebro = bt.Cerebro()
    _setup_broker(cerebro, commission=commission, slippage_bps=slippage_bps, risk_pct=risk_pct)

    data = bt.feeds.PandasData(
        dataname=df,
        datetime="date",
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
        openinterest=None,
    )
    cerebro.adddata(data)
    cerebro.addstrategy(SmaCrossStrategy, fast_period=fast, slow_period=slow)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", timeframe=bt.TimeFrame.Days, compression=1)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    results = cerebro.run()
    strat = results[0]
    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()

    plots = cerebro.plot(style="candlestick", volume=False, iplot=False)
    # 嘗試從回傳結構中找出 Figure 並儲存第一張
    def iter_figs(obj: Any):
        if obj is None:
            return
        if hasattr(obj, "savefig"):
            yield obj
        elif isinstance(obj, (list, tuple)):
            for x in obj:
                yield from iter_figs(x)

    figs: List[Any] = list(iter_figs(plots))
    out_path = OUTPUTS_DIR / f"backtest_{symbol}.png"
    if figs:
        figs[0].savefig(out_path, dpi=180, bbox_inches="tight")

    # 亦可將指標輸出為文字檔與面板數據
    summary_path = OUTPUTS_DIR / f"backtest_{symbol}.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("回測摘要\n")
        f.write(f"Sharpe: {sharpe}\n")
        f.write(f"Max Drawdown: {dd.get('max', {})}\n")
        f.write(f"Trades: {trades}\n")

    # 風險指標面板（CSV）：年化波動、Calmar、Sortino（近似）
    import numpy as np
    returns = df['close'].pct_change().dropna().values
    daily_vol = float(np.std(returns))
    ann_vol = daily_vol * np.sqrt(252)
    max_dd = float(dd.get('max', {}).get('drawdown', 0.0)) / 100.0
    sharpe_val = float(sharpe.get('sharperatio', 0) or 0)
    calmar = (sharpe_val * ann_vol) / max(1e-9, abs(max_dd)) if max_dd != 0 else np.nan
    sortino = sharpe_val  # 簡化：若需精確，另計下行波動
    import pandas as pd
    panel = pd.DataFrame([{
        'ann_vol': ann_vol,
        'max_drawdown': max_dd,
        'sharpe': sharpe_val,
        'calmar': calmar,
        'sortino_approx': sortino,
    }])
    panel.to_csv(OUTPUTS_DIR / f"risk_panel_{symbol}.csv", index=False)

    # 輸出交易記錄供 UI 疊加
    trades_csv = OUTPUTS_DIR / f"trades_{symbol}.csv"
    import pandas as pd
    pd.DataFrame(strat.trades).to_csv(trades_csv, index=False)
    return out_path


class SmaCrossMultiStrategy(bt.Strategy):
    params = dict(
        fast_period=10,
        slow_period=30,
    )

    def __init__(self):
        self.inds: Dict[bt.LineSeries, Dict[str, Any]] = {}
        self.symbols: List[str] = []
        self.dates: List[pd.Timestamp] = []
        self.equity: List[float] = []
        self.positions_by_symbol: Dict[str, List[float]] = {}
        for d in self.datas:
            name = getattr(d, "_name", "") or str(len(self.symbols))
            self.symbols.append(name)
            self.positions_by_symbol[name] = []
            inds = {}
            inds["fast"] = bt.indicators.SMA(d.close, period=self.p.fast_period)
            inds["slow"] = bt.indicators.SMA(d.close, period=self.p.slow_period)
            inds["cross"] = bt.indicators.CrossOver(inds["fast"], inds["slow"])
            self.inds[d] = inds

    def next(self):
        for d in self.datas:
            pos = self.getposition(d)
            cross = self.inds[d]["cross"]
            if not pos:
                if cross > 0:
                    self.buy(data=d)
            else:
                if cross < 0:
                    self.sell(data=d)

        # 記錄組合淨值與持倉
        self.dates.append(pd.Timestamp(self.datas[0].datetime.date(0)))
        self.equity.append(float(self.broker.getvalue()))
        for d in self.datas:
            name = getattr(d, "_name", "")
            size = float(self.getposition(d).size)
            self.positions_by_symbol[name].append(size)


def run_backtest_portfolio(
    dataframes_by_symbol: Dict[str, pd.DataFrame],
    fast: int = 10,
    slow: int = 30,
    commission: float = 0.001,
    slippage_bps: int = 0,
    risk_pct: float = 0.1,
) -> Path:
    cerebro = bt.Cerebro()
    _setup_broker(cerebro, commission=commission, slippage_bps=slippage_bps, risk_pct=risk_pct)

    for symbol, df in dataframes_by_symbol.items():
        data = bt.feeds.PandasData(
            dataname=df,
            datetime="date",
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
            openinterest=None,
            plot=True,
        )
        data._name = symbol
        cerebro.adddata(data)

    cerebro.addstrategy(SmaCrossMultiStrategy, fast_period=fast, slow_period=slow)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", timeframe=bt.TimeFrame.Days, compression=1)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    results = cerebro.run()
    out_path = OUTPUTS_DIR / "backtest_portfolio.png"
    plots = cerebro.plot(style="candlestick", volume=False, iplot=False)
    def iter_figs(obj: Any):
        if obj is None:
            return
        if hasattr(obj, "savefig"):
            yield obj
        elif isinstance(obj, (list, tuple)):
            for x in obj:
                yield from iter_figs(x)
    figs: List[Any] = list(iter_figs(plots))
    if figs:
        figs[0].savefig(out_path, dpi=180, bbox_inches="tight")

    # 組合資產曲線與持倉曲線
    strat: SmaCrossMultiStrategy = results[0]
    equity_df = pd.DataFrame({
        "date": strat.dates,
        "equity": strat.equity,
    })
    equity_df.to_csv(OUTPUTS_DIR / "portfolio_equity.csv", index=False)

    plt.figure(figsize=(10, 4))
    plt.plot(equity_df["date"], equity_df["equity"], label="Portfolio Equity")
    plt.title("Portfolio Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "portfolio_equity.png", dpi=160)
    plt.close()

    pos_df = pd.DataFrame({"date": strat.dates})
    for name, series in strat.positions_by_symbol.items():
        pos_df[name] = series
    pos_df.to_csv(OUTPUTS_DIR / "portfolio_positions.csv", index=False)

    plt.figure(figsize=(10, 4))
    for name in strat.positions_by_symbol.keys():
        plt.plot(pos_df["date"], pos_df[name], label=name)
    plt.title("Positions by Symbol (Size)")
    plt.xlabel("Date")
    plt.ylabel("Position Size")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "portfolio_positions.png", dpi=160)
    plt.close()
    return out_path


__all__ = ["run_backtest_from_dataframe"]
