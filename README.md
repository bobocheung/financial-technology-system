## 金融科技系統（量化回測 + 風險預測）

本專案面向新手投資者，提供：

- 簡單易懂的量化回測（使用 Backtrader）
- 以香港股市真實數據（Yahoo Finance）作為資料來源
- 以 PyTorch Forecasting 建立基礎的時序預測模型（預測隔日報酬分位數，近似 VaR 風險指標）
- 互動式視覺化（Plotly）與回測圖（Matplotlib）

全部說明與註解以繁體中文撰寫，盡量降低金融背景門檻。

---

### 1. 安裝環境

建議使用 Python 3.10 或 3.11。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 請改用 .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

若在安裝 `pytorch-forecasting` 或 `pytorch-lightning` 時遇到相依性問題，可先確保 `torch` 能安裝成功，再安裝其他套件：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install pytorch-lightning==2.3.0 pytorch-forecasting==1.0.0
```

---

### 2. 專案結構

```
金融科技系統/
├─ app.py                        # 主程式 CLI
├─ requirements.txt              # 套件需求
├─ README.md
├─ data/                         # 下載的原始資料（CSV）
├─ models/                       # 訓練後的模型檔
├─ outputs/                      # 圖表與回測結果
└─ src/
   ├─ __init__.py
   ├─ config.py                  # 全域設定（資料夾位置等）
   ├─ utils/
   │  ├─ __init__.py
   │  └─ symbols.py             # 港股代碼正規化工具
   ├─ data/
   │  ├─ __init__.py
   │  └─ fetch_hk_data.py       # 從 Yahoo Finance 擷取港股資料
   ├─ backtest/
   │  ├─ __init__.py
   │  ├─ strategies.py          # 範例策略（SMA 交叉）
   │  └─ run_backtest.py        # 回測驅動程式
   ├─ visualize/
   │  ├─ __init__.py
   │  └─ plot.py                # 互動式 K 線、均線與成交量圖
   └─ risk/
      ├─ __init__.py
      ├─ dataset.py             # 建立時序資料集（TimeSeriesDataSet）
      ├─ train_model.py         # 使用 RNNModel 訓練分位數模型
      └─ predict_model.py       # 載入模型並輸出隔日風險分位數
```

---

### 3. 快速開始（以騰訊控股 0700.HK 為例）

以下指令會自動：

1) 下載資料 2) 跑一個簡單的均線交叉回測 3) 繪製互動式圖表 4) 訓練簡單風險模型並做一次預測。

```bash
python app.py quickstart --symbol 700 --start 2018-01-01 --end 2024-12-31
```

完成後你可以在：

- `data/0700.HK.csv`：原始日線資料
- `outputs/backtest_0700.HK.png`：回測曲線圖
- `outputs/chart_0700.HK.html`：互動式 K 線圖（用瀏覽器打開）
- `models/0700.HK/`：已訓練模型與資料設定

---

### 4. 常用子指令

- 下載資料：
```bash
python app.py fetch --symbol 5 --start 2015-01-01 --end 2024-12-31
```

- 回測（SMA 交叉）：
```bash
python app.py backtest --symbol 5 --fast 10 --slow 30 \
  --commission 0.001 --slippage_bps 5 --risk_pct 0.2
```

- 視覺化（K 線 + 均線）：
```bash
python app.py plot --symbol 5 --ma 20 60 120 --explain
```

- 訓練風險模型（RNNModel + 分位數損失）：
```bash
python app.py train --symbol 5
```

- 預測隔日風險（輸出 5% / 50% / 95% 量化預測）：
```bash
python app.py predict --symbol 5
```

- 多標的組合回測（自動讀取本地資料；若無則會先下載）：
```bash
python app.py backtest-portfolio \
  --symbols 700 5 1299 \
  --start 2019-01-01 --end 2021-12-31 \
  --fast 10 --slow 30 \
  --commission 0.001 --slippage_bps 5 --risk_pct 0.2
```

說明：

- `--symbol` 可以輸入「700」「0700」「0700.HK」，程式會自動轉為 Yahoo 代碼 `0700.HK`。
- 回測策略僅為教學範例，非投資建議。

---

### 5. 新手視覺化提示

- 在互動圖中加入均線交叉（以最短與最長均線示範）：
  - 「黃金交叉」：短均線上穿長均線，可能代表趨勢轉強（綠色三角向上標記）
  - 「死亡交叉」：短均線下穿長均線，可能代表趨勢轉弱（紅色三角向下標記）
- 開啟 `--explain` 會在圖上顯示簡短註解，包含 K 線、均線與互動操作說明

---

### 5. 新手小百科

- 「K 線」：每根包含開盤、最高、最低、收盤（OHLC）資訊，日線代表一天一根。
- 「均線」：移動平均線，例如 20 日均線是最近 20 天的收盤平均，常用於判斷趨勢。
- 「交叉策略」：短均線上穿長均線視為趨勢向上，反之向下。
- 「分位數預測」：模型同時預測 5%、50%、95% 等分位數，可近似下行風險（如 5% 分位數對應較保守預測）。

---

### 6. 專案報告（精簡版）

- 目標：以港股真實數據，提供「可理解」的量化回測與基礎風險預測（分位數）。
- 資料來源：Yahoo Finance（`yfinance`），日線級別。
- 回測方法：Backtrader + SMA 交叉策略，加入成本參數：
  - `--commission` 手續費率；`--slippage_bps` 滑點（基點，1bp=0.01%）；`--risk_pct` 單筆倉位比例
- 視覺化：Plotly 互動式 K 線、均線、交叉點提示與新手註解。
- 風險模型：PyTorch Forecasting 的 TemporalFusionTransformer（TFT）+ 分位數損失，輸出 5%/50%/95% 分位數近似下行風險範圍。
- 模型訓練：以單一標的為例（可擴展多標的與更完整特徵工程），訓練輪數與參數較保守，重在流程可跑與輸出可讀。
- 產出：回測圖、回測摘要、互動圖、風險分位數 CSV。

進一步可改善：
- 更合理交易成本模型與分檔倉位控制；多策略組合；風險平價或目標波動度配置
- 更豐富的特徵（成交量、技術指標、指數/期貨/匯率/利率/宏觀因子）
- 更強模型（N-HiTS、TIDE、TFT with static covariates）、模型選擇與交叉驗證

---

### 7. 演示方法（建議步驟）

1) 快速體驗（單標的）
```bash
python app.py quickstart --symbol 700 --start 2018-01-01 --end 2024-12-31
```
查看：`outputs/backtest_0700.HK.png`、`outputs/chart_0700.HK.html`、`outputs/risk_quantiles_0700.HK.csv`

2) 多標的組合回測（示例 700、0005、1299）
```bash
python app.py backtest-portfolio --symbols 700 5 1299 --start 2019-01-01 --end 2021-12-31
```
查看：`outputs/backtest_portfolio.png`、`outputs/portfolio_equity.png`、`outputs/portfolio_positions.png`

3) 新手視覺化解說
```bash
python app.py plot --symbol 700 --ma 20 60 120 --explain
```
開啟 `outputs/chart_0700.HK.html`，操作滑鼠 hover，觀察交叉點提示。

---


```


---

### 9. 免責聲明

本專案僅供教學研究，不構成投資建議。股市有風險，投資需謹慎。

