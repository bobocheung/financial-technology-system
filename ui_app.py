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
from src.risk.predict_model import conservative_position_limit_from_quantiles


def _init_session_state() -> None:
    defaults = {
        "task_fetch": False,
        "task_plot": False,
        "task_backtest": False,
        "last_symbol": "700",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _compute_insights(df: pd.DataFrame, ma_periods: list[int]) -> list[str]:
    tips: list[str] = []
    if df.empty:
        return ["資料為空，請先下載或縮短日期範圍"]
    df = df.copy().sort_values("date")
    mas = sorted(ma_periods)
    short, long = mas[0], mas[-1]
    df[f"ma{short}"] = df["close"].rolling(short).mean()
    df[f"ma{long}"] = df["close"].rolling(long).mean()
    last = df.iloc[-1]
    if last[f"ma{short}"] > last[f"ma{long}"]:
        tips.append("趨勢轉強：短均線在長均線之上，偏多格局（留意風險）")
    elif last[f"ma{short}"] < last[f"ma{long}"]:
        tips.append("趨勢轉弱：短均線在長均線之下，偏空格局（保守為主）")
    if last["close"] > last[f"ma{long}"] and abs(last["close"] - last[f"ma{long}"]) / max(1e-6, last[f"ma{long}"]) < 0.02:
        tips.append("回檔靠近長均線：多頭中繼的常見現象，觀察是否止穩再續漲")
    dist = abs(last[f"ma{short}"] - last[f"ma{long}"]) / max(1e-6, last[f"ma{long}"])
    if dist < 0.005:
        tips.append("盤整：短長均線糾纏，訊號不明確，建議減少操作或等待突破")
    tips.append("指標僅供教學，請務必控制單筆倉位與總風險")
    return tips


def main():
    ensure_directories()
    st.set_page_config(page_title="金融科技系統（手繪風）", layout="wide")
    _init_session_state()
    st.markdown(HANDDRAWN_CSS, unsafe_allow_html=True)
    st.markdown("<h2 class='sketch-title contrast'>一步一步了解：下載 ➜ 視覺化 ➜ 回測 ➜ 風險</h2>", unsafe_allow_html=True)

    # 顯示五個可用性改善點
    with st.expander("五個 UI 改善（已套用）"):
        st.markdown("- 更高對比字色與字級，避免文字過淡或太小\n- 亮色溫暖背景 + 白色內容卡片，提升可讀性\n- 手繪膠囊提示與分區標題，讓步驟清晰\n- 重要動作按鈕風格強化（陰影/粗框）\n- 圖表加入明確圖例、交叉點標記與新手註解")

    # 左側導覽欄與新手任務
    st.sidebar.title("導覽")
    section = st.sidebar.radio("快速跳轉", options=["全部", "下載資料", "視覺化", "回測"], index=0)
    st.sidebar.markdown(
        """
        - 📥 下載：輸入代碼與日期，先取得真實數據
        - 📊 視覺化：K線 + 均線、交叉點、買賣箭頭與盈虧
        - 🔁 回測：用 SMA 交叉策略檢視績效與風險
        """
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("新手任務")
    st.sidebar.checkbox("① 下載一檔股票資料", key="task_fetch")
    st.sidebar.checkbox("② 生成一張互動圖", key="task_plot")
    st.sidebar.checkbox("③ 跑一次回測", key="task_backtest")
    progress = sum([st.session_state.task_fetch, st.session_state.task_plot, st.session_state.task_backtest]) / 3
    st.sidebar.progress(progress)
    # 導覽「下一步」按鈕：依任務狀態切換 section
    if st.sidebar.button("下一步 →"):
        if not st.session_state.task_fetch:
            section = "下載資料"
        elif not st.session_state.task_plot:
            section = "視覺化"
        elif not st.session_state.task_backtest:
            section = "回測"

    if section in ("全部", "下載資料"):
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
                st.session_state.task_fetch = True
                st.session_state.last_symbol = normalize_hk_symbol(symbol_in)
            except Exception as e:
                st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    if section in ("全部", "視覺化"):
        with st.container():
            st.markdown("<div class='paper'>", unsafe_allow_html=True)
            st.subheader("2) 互動式視覺化（K線 + 均線 + 交叉點提示）")
            ma = st.multiselect("選擇均線週期", options=[5,10,20,30,60,120,250], default=[20,60,120])
            explain = st.toggle("顯示新手註解", value=True)
            show_cards = st.toggle("顯示『建議解讀』小卡", value=True)
            show_signals = st.toggle("圖上標註買/賣與盈虧區間", value=True)
            overlays = st.multiselect("疊加指標 (可複選)", options=["EMA","BOLL","RSI"], default=["EMA","BOLL"]) 
            if st.button("生成圖表"):
                try:
                    symbol = normalize_hk_symbol(st.session_state.get("last_symbol", "700"))
                    df = load_cached(symbol)
                    out = kline_with_mas(
                        df, symbol,
                        ma_periods=ma, explain=explain,
                        show_signals=show_signals, show_trade_pnl=show_signals,
                        overlay_indicators=overlays,
                    )
                    st.success(f"輸出：{out}")
                    st.components.v1.html(Path(out).read_text(encoding="utf-8"), height=600, scrolling=True)
                    st.session_state.task_plot = True
                    if show_cards:
                        tips = _compute_insights(df, [int(x) for x in ma])
                        st.markdown("#### 建議解讀")
                        for t in tips:
                            st.info(t)
                        # 建議動作模板（非投資建議）
                        st.markdown("#### 建議動作（模板）")
                        last_tips = " ".join(tips)
                        if "轉強" in last_tips:
                            st.success("偏多環境：單筆倉位上限 10%~20%，設止損 5%~8%，分批進場")
                        elif "轉弱" in last_tips:
                            st.warning("偏空環境：減少倉位至 0%~5%，或僅觀察不交易")
                        elif "盤整" in last_tips:
                            st.info("盤整環境：耐心等待突破後再行動，避免過度進出")
                except Exception as e:
                    st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)

    if section in ("全部", "回測"):
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
                    symbol = normalize_hk_symbol(st.session_state.get("last_symbol", "700"))
                    df = load_cached(symbol)
                    out = run_backtest_from_dataframe(df, symbol, fast=int(fast), slow=int(slow),
                                                      commission=float(commission), slippage_bps=int(slippage_bps),
                                                      risk_pct=float(risk_pct)/100.0)
                    st.success(f"回測圖：{out}")
                    st.image(str(out))
                    summ = OUTPUTS_DIR / f"backtest_{symbol}.txt"
                    if summ.exists():
                        st.text(summ.read_text(encoding="utf-8"))
                    st.session_state.task_backtest = True
                except Exception as e:
                    st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<p class='small tip'>提示：手繪風格僅做視覺親和，核心仍以清晰可讀、互動簡潔為先。</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

