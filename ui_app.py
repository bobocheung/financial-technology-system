from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path

from src.config import ensure_directories, OUTPUTS_DIR
from src.utils.symbols import normalize_hk_symbol
from src.data.fetch_hk_data import fetch_hk_daily, load_cached
from src.visualize.plot import kline_with_mas
from src.backtest.run_backtest import run_backtest_from_dataframe
from src.visualize.handdrawn_theme import HANDDRAWN_CSS


def main():
    ensure_directories()
    st.set_page_config(page_title="金融科技系統（手繪風）", layout="wide")
    st.markdown(HANDDRAWN_CSS, unsafe_allow_html=True)
    st.markdown("<h2 class='sketch-title'>一步一步了解：下載 ➜ 視覺化 ➜ 回測 ➜ 風險</h2>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='paper'>", unsafe_allow_html=True)
        st.subheader("1) 下載港股資料")
        col1, col2, col3 = st.columns([2,2,3])
        with col1:
            symbol_in = st.text_input("輸入代碼（700/0700/0700.HK）", value="700")
        with col2:
            start = st.text_input("開始日期", value="2018-01-01")
        with col3:
            end = st.text_input("結束日期（可留空）", value="")
        if st.button("下載/更新資料", type="primary"):
            try:
                path = fetch_hk_daily(symbol_in, start=start or None, end=end or None)
                st.success(f"已下載：{path}")
            except Exception as e:
                st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='paper'>", unsafe_allow_html=True)
        st.subheader("2) 互動式視覺化（K線 + 均線 + 交叉點提示）")
        ma = st.multiselect("選擇均線週期", options=[5,10,20,30,60,120,250], default=[20,60,120])
        explain = st.toggle("顯示新手註解", value=True)
        if st.button("生成圖表"):
            try:
                symbol = normalize_hk_symbol(symbol_in)
                df = load_cached(symbol)
                out = kline_with_mas(df, symbol, ma_periods=ma, explain=explain)
                st.success(f"輸出：{out}")
                st.components.v1.html(Path(out).read_text(encoding="utf-8"), height=600, scrolling=True)
            except Exception as e:
                st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='paper'>", unsafe_allow_html=True)
        st.subheader("3) 快速回測（SMA 交叉）")
        c1, c2, c3 = st.columns(3)
        with c1:
            fast = st.number_input("短均線", min_value=2, max_value=200, value=10)
        with c2:
            slow = st.number_input("長均線", min_value=5, max_value=400, value=30)
        with c3:
            risk_pct = st.slider("單筆倉位(%)", min_value=1, max_value=100, value=10)
        c4, c5 = st.columns(2)
        with c4:
            commission = st.number_input("手續費率", min_value=0.0, max_value=0.01, value=0.001, step=0.0005, format="%.4f")
        with c5:
            slippage_bps = st.number_input("滑點(bp)", min_value=0, max_value=100, value=0)
        if st.button("執行回測"):
            try:
                symbol = normalize_hk_symbol(symbol_in)
                df = load_cached(symbol)
                out = run_backtest_from_dataframe(df, symbol, fast=int(fast), slow=int(slow),
                                                  commission=float(commission), slippage_bps=int(slippage_bps),
                                                  risk_pct=float(risk_pct)/100.0)
                st.success(f"回測圖：{out}")
                st.image(str(out))
                summ = OUTPUTS_DIR / f"backtest_{symbol}.txt"
                if summ.exists():
                    st.text(summ.read_text(encoding="utf-8"))
            except Exception as e:
                st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<p class='small tip'>提示：手繪風格僅做視覺親和，核心仍以清晰可讀、互動簡潔為先。</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

