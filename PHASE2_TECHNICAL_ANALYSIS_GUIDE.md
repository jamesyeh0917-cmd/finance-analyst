# Phase 2 技術分析快速指南

## 執行步驟

1. 確保已有原始數據：
   ls data/raw/

2. 執行技術分析：
   python src/technical_analysis.py

3. 檢查輸出：
   ls data/processed/analyzed_*.csv

## 計算的指標

1. 移動平均線：MA5、MA20、MA50、MA200
2. RSI（14 日）：測量超買超賣
3. MACD（12/26/9）：MACD、Signal、Histogram
4. 布林帶（20 日，2σ）：Upper、Lower、Middle、Width、Position

## 參數修改位置

編輯 config/settings.yaml 中的 technical_indicators 部分

## 輸出結構

data/processed/analyzed_[股票代碼]_[週期]_[日期].csv

每個文件包含原始數據 + 12 個新指標列
