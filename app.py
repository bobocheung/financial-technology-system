from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

from src.config import ensure_directories
from src.utils.symbols import normalize_hk_symbol
from src.data.fetch_hk_data import fetch_hk_daily, load_cached
from src.backtest.run_backtest import run_backtest_from_dataframe
from src.backtest.run_backtest import run_backtest_portfolio
from src.visualize.plot import kline_with_mas
from src.risk.dataset import prepare_dataset
from src.risk.train_model import train_quantile_rnn
from src.risk.predict_model import predict_next_day_quantiles, save_quantile_table


def cmd_fetch(args):
    path = fetch_hk_daily(args.symbol, start=args.start, end=args.end)
    print(f"已下載：{path}")


def cmd_backtest(args):
    symbol = normalize_hk_symbol(args.symbol)
    df = load_cached(symbol)
    out = run_backtest_from_dataframe(
        df, symbol,
        fast=args.fast,
        slow=args.slow,
        commission=args.commission,
        slippage_bps=args.slippage_bps,
        risk_pct=args.risk_pct,
    )
    print(f"回測圖輸出：{out}")


def cmd_plot(args):
    symbol = normalize_hk_symbol(args.symbol)
    df = load_cached(symbol)
    out = kline_with_mas(df, symbol, ma_periods=args.ma, explain=args.explain)
    print(f"互動圖輸出：{out}")


def cmd_train(args):
    symbol = normalize_hk_symbol(args.symbol)
    df = load_cached(symbol)
    training, validation, mapping = prepare_dataset(df, symbol)
    ckpt = train_quantile_rnn(training, validation, symbol, max_epochs=args.epochs)
    print(f"模型已儲存：{ckpt}")


def cmd_predict(args):
    symbol = normalize_hk_symbol(args.symbol)
    df = load_cached(symbol)
    training, validation, mapping = prepare_dataset(df, symbol)
    ckpt_path = Path(args.ckpt) if args.ckpt else Path("models") / symbol / "tft_quantile.ckpt"
    result = predict_next_day_quantiles(validation, ckpt_path)
    out = save_quantile_table(result, symbol)
    print(f"風險分位數輸出：{out}")


def cmd_quickstart(args):
    symbol = normalize_hk_symbol(args.symbol)
    ensure_directories()
    # 1) 下載
    fetch_hk_daily(symbol, start=args.start, end=args.end)
    df = load_cached(symbol)
    # 2) 回測
    run_backtest_from_dataframe(df, symbol)
    # 3) 視覺化
    kline_with_mas(df, symbol)
    # 4) 風險模型
    training, validation, _ = prepare_dataset(df, symbol)
    ckpt = train_quantile_rnn(training, validation, symbol, max_epochs=3)
    result = predict_next_day_quantiles(validation, ckpt)
    save_quantile_table(result, symbol)
    print("Quickstart 完成，請查看 outputs/ 與 models/ 目錄。")


def cmd_backtest_portfolio(args):
    symbols = [normalize_hk_symbol(s) for s in args.symbols]
    # 讀取或下載資料
    dfs = {}
    for s in symbols:
        try:
            df = load_cached(s)
        except FileNotFoundError:
            fetch_hk_daily(s, start=args.start, end=args.end)
            df = load_cached(s)
        dfs[s] = df
    out = run_backtest_portfolio(
        dfs, fast=args.fast, slow=args.slow,
        commission=args.commission, slippage_bps=args.slippage_bps, risk_pct=args.risk_pct,
    )
    print(f"組合回測圖輸出：{out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="金融科技系統：港股資料 + 回測 + 風險模型")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="下載港股資料")
    p_fetch.add_argument("--symbol", required=True, help="如 700/0700/0700.HK")
    p_fetch.add_argument("--start", default="2015-01-01")
    p_fetch.add_argument("--end", default=None)
    p_fetch.set_defaults(func=cmd_fetch)

    p_bt = sub.add_parser("backtest", help="回測（SMA 交叉）")
    p_bt.add_argument("--symbol", required=True)
    p_bt.add_argument("--fast", type=int, default=10)
    p_bt.add_argument("--slow", type=int, default=30)
    p_bt.add_argument("--commission", type=float, default=0.001, help="手續費率（例：0.001=千分之一）")
    p_bt.add_argument("--slippage_bps", type=int, default=0, help="滑點（基點，1bp=0.01%）")
    p_bt.add_argument("--risk_pct", type=float, default=0.1, help="單筆倉位比例（0~1，預設10%）")
    p_bt.set_defaults(func=cmd_backtest)

    p_plot = sub.add_parser("plot", help="繪製互動 K 線 + 均線")
    p_plot.add_argument("--symbol", required=True)
    p_plot.add_argument("--ma", type=int, nargs="+", default=[20, 60, 120])
    p_plot.add_argument("--explain", action="store_true", help="加上新手註解")
    p_plot.set_defaults(func=cmd_plot)

    p_train = sub.add_parser("train", help="訓練風險模型（RNN + 分位數）")
    p_train.add_argument("--symbol", required=True)
    p_train.add_argument("--epochs", type=int, default=5)
    p_train.set_defaults(func=cmd_train)

    p_pred = sub.add_parser("predict", help="使用已訓練模型做隔日分位數預測")
    p_pred.add_argument("--symbol", required=True)
    p_pred.add_argument("--ckpt", default=None, help="模型路徑，預設 models/<symbol>/quantile_rnn.ckpt")
    p_pred.set_defaults(func=cmd_predict)

    p_quick = sub.add_parser("quickstart", help="一鍵流程：下載+回測+視覺化+訓練+預測")
    p_quick.add_argument("--symbol", required=True)
    p_quick.add_argument("--start", default="2018-01-01")
    p_quick.add_argument("--end", default=None)
    p_quick.set_defaults(func=cmd_quickstart)

    p_port = sub.add_parser("backtest-portfolio", help="多標的組合回測（SMA 交叉）")
    p_port.add_argument("--symbols", nargs="+", required=True, help="多檔，如 700 5 1299")
    p_port.add_argument("--start", default="2018-01-01")
    p_port.add_argument("--end", default=None)
    p_port.add_argument("--fast", type=int, default=10)
    p_port.add_argument("--slow", type=int, default=30)
    p_port.add_argument("--commission", type=float, default=0.001)
    p_port.add_argument("--slippage_bps", type=int, default=0)
    p_port.add_argument("--risk_pct", type=float, default=0.1)
    p_port.set_defaults(func=cmd_backtest_portfolio)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

