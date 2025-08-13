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

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(size=1)
        else:
            if self.crossover < 0:
                self.sell(size=1)

    def log(self, txt):
        if self.p.printlog:
            dt = self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()}, {txt}")


__all__ = ["SmaCrossStrategy"]
