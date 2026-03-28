# Phase 2 測試指南 — fetch_market_data.py

## 📋 概述

`fetch_market_data.py` 是 Phase 2 的第一個模組，負責自動抓取股票歷史數據。

## ✅ 驗證清單

### 1️⃣ 檔案結構
```
✅ src/fetch_market_data.py       — 已完整實裝（379 行）
✅ src/config_loader.py            — 已存在（277 行）
✅ config/settings.yaml            — 已配置
✅ data/raw/                       — 目錄已創建
```

### 2️⃣ 代碼邏輯驗證
```
✅ setup_logging()          — 日誌系統 ✓
✅ get_data_dir()           — 路徑管理 ✓
✅ load_stock_config()      — 配置讀取 ✓
✅ fetch_single_stock()     — 單只股票抓取 ✓
✅ fetch_all_stocks()       — 多只股票抓取 ✓
✅ main()                   — 主函數 ✓
```

### 3️⃣ 設計原則驗證
```
✅ 動態讀取配置           — 從 settings.yaml 自動讀取股票清單
✅ 雲端友善              — 無 input()，完全自動化
✅ 模組化設計            — 6 個獨立 Function
✅ 路徑智能              — 自動找到 data/raw/ 目錄
✅ 錯誤處理              — 完整的 try-catch 和日誌
✅ 重試機制              — 自動重試 3 次
✅ 市場適配              — 根據市場自動調整代碼格式
```

## 🚀 本地測試步驟

### 前置條件

```bash
# 1. 確保在專案根目錄
cd /path/to/finance-analyst

# 2. 安裝必要套件（如果還沒裝）
pip install -r requirements.txt

# 3. 確保配置文件存在
test -f config/settings.yaml && echo "✅ 配置文件存在" || echo "❌ 請複製配置文件"
```

### 執行方式 1：直接執行

```bash
python src/fetch_market_data.py
```

### 執行方式 2：使用 -m 執行

```bash
python -m src.fetch_market_data
```

### 預期輸出

如果網路連接正常，你應該看到：

```
============================================================
🚀 開始執行數據收集任務
============================================================
📖 正在讀取配置文件...
✅ 成功讀取 3 只股票的配置
   股票清單：TSMC_2330 (台積電), NVDA (NVIDIA), BRK_B (柏克夏·海瑟威 B 股)
✅ 數據目錄已確認：.../data/raw

📊 開始抓取 3 只股票的數據...

📥 正在抓取 台積電 (TSMC_2330.TW)，週期：1y
  ✅ 成功抓取 台積電，共 252 條數據
  
📥 正在抓取 NVIDIA (NVDA)，週期：1y
  ✅ 成功抓取 NVIDIA，共 252 條數據
  
📥 正在抓取 柏克夏·海瑟威 B 股 (BRK_B)，週期：1y
  ✅ 成功抓取 柏克夏·海瑟威 B 股，共 252 條數據

💾 正在保存數據...
✅ 已保存 TSMC_2330 至 .../data/raw/TSMC_2330_1y_20250328.csv
✅ 已保存 NVDA 至 .../data/raw/NVDA_1y_20250328.csv
✅ 已保存 BRK_B 至 .../data/raw/BRK_B_1y_20250328.csv

============================================================
📈 任務完成！
============================================================
✅ 成功抓取：3 / 3 只股票
💾 成功保存：3 個 CSV 檔案至 .../data/raw
✅ 成功股票：TSMC_2330, NVDA, BRK_B
============================================================
```

## 📊 驗證資料是否存入

執行後，檢查 CSV 檔案是否已創建：

```bash
# 列出 data/raw/ 中的所有 CSV 檔案
ls -lh data/raw/*.csv

# 查看其中一個 CSV 檔案的前幾行
head -5 data/raw/TSMC_2330_1y_20250328.csv

# 查看 CSV 檔案的統計信息（列數和行數）
wc -l data/raw/TSMC_2330_1y_20250328.csv
```

預期會看到：
```
Symbol  Name  FetchDate              Open    High    Low     Close   Volume
TSMC_2330.TW  台積電  2025-03-28T10:20:00.123456  950   960   940   955   1000000
...
```

## 🔍 除錯日誌級別

如果想看更詳細的日誌，可以修改程式碼：

```python
# 將這一行
logger = setup_logging()

# 改為
logger = setup_logging(log_level="DEBUG")
```

## 🧪 Python 測試（不依賴網路）

如果想測試邏輯而不實際抓取數據，可以這樣做：

```python
from src.fetch_market_data import load_stock_config, get_data_dir

# 測試 1：驗證配置讀取
stocks, loader = load_stock_config()
print(f"讀取到的股票數：{len(stocks)}")
for code, info in stocks.items():
    print(f"  • {code}: {info.get('name', 'N/A')}")

# 測試 2：驗證路徑管理
data_dir = get_data_dir()
print(f"數據目錄：{data_dir}")
print(f"目錄是否存在：{data_dir.exists()}")
```

## 📈 GitHub Actions 部署準備

這個程式已經可以直接用於 GitHub Actions 排程，只需在 `.github/workflows/fetch-data.yml` 中：

```yaml
name: Daily Fetch Market Data

on:
  schedule:
    - cron: '0 16 * * *'  # 每天台灣時間 00:00 (UTC 16:00)

jobs:
  fetch-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Fetch market data
        run: python src/fetch_market_data.py
      
      - name: Commit and push
        run: |
          git add data/raw/
          git commit -m "chore: 每日市場數據更新" || echo "無新數據"
          git push
```

## ✅ 現在的狀態

```
Phase 2 進度：
  ✅ fetch_market_data.py — 完整實裝
  ⏳ technical_analysis.py — 待開發
  ⏳ fundamental_analysis.py — 待開發
  ⏳ probability_analysis.py — 待開發
```

---

**下一步：** 開始實裝 `technical_analysis.py`（技術指標計算）

