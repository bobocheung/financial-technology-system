from __future__ import annotations

import backtrader as bt


class SmaCrossStrategy(bt.Strategy):
    params = dict(
        fast_period=10,
        slow_period=30,
        printlog=False,
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.trades = []  # 收集交易記錄
        self.entry_price = None
        self.entry_datetime = None

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(size=1)
                self.entry_price = float(self.data.close[0])
                self.entry_datetime = self.datas[0].datetime.date(0)
        else:
            if self.crossover < 0:
                self.sell(size=1)
                exit_price = float(self.data.close[0])
                exit_dt = self.datas[0].datetime.date(0)
                if self.entry_price is not None and self.entry_datetime is not None:
                    pnl = exit_price / max(1e-12, self.entry_price) - 1.0
                    self.trades.append(dict(
                        entry_date=str(self.entry_datetime), entry_price=self.entry_price,
                        exit_date=str(exit_dt), exit_price=exit_price, pnl=pnl,
                    ))
                self.entry_price = None
                self.entry_datetime = None

    def log(self, txt):
        if self.p.printlog:
            dt = self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()}, {txt}")


__all__ = ["SmaCrossStrategy"]
