# Finance Analyst Skill — AI 動力的智能股票分析平台

## 🎯 這是什麼？

Finance Analyst 是一個結合 Claude AI 的智能股票分析平台，提供：

- 🤖 **Claude AI** — 智能分析和推理
- 📊 **數據自動化** — 從多個 API 自動收集股價、財報、新聞
- 📈 **多層分析** — 技術面 + 基本面 + 機率分析
- 🎛️ **動態規則系統** — 每檔股票可自訂監控標準，無需修改代碼

## 🏗️ 系統架構

```
Layer 1: 數據收集 (fetch_market_data.py — 開發中)
   ↓ 自動從多個 API 抓取股價、財報、新聞

Layer 2: 指標計算 (technical_analysis.py + fundamental_analysis.py — 開發中)
   ↓ 計算技術指標（RSI、MACD）、基本面指標（PE、ROE）

Layer 3: 機率分析 (probability_analysis.py — 開發中)
   ↓ 三情景分析 + 蒙特卡洛模擬 + 歷史驗證

Layer 4: 報告生成 (analysis_report_generator.py — 開發中)
   ↓ 輸出專業分析報告
```

## 🤖 Claude 會如何協助分析？

### 場景：用戶問「分析台積電值不值得買？」

**Claude 的完整分析流程：**

```
1️⃣ 讀取動態規則
   ├─ 讀取全域規則（預設停損 -15%）
   ├─ 讀取分組規則（台灣科技股停損 -12%）
   ├─ 讀取個別股票規則（TSMC 停損 -10%）
   └─ 決定使用: -10% 作為停損點

2️⃣ 數據收集階段
   ├─ 自動抓取股價 940 元
   ├─ 自動抓取技術指標（均線、成交量）
   ├─ 自動抓取財務數據（EPS、PE、ROE）
   └─ 自動抓取最新新聞和法人動向

3️⃣ 分析階段
   ├─ 技術面分析
   │  └─ RSI 65（超買信號 ⚠️）
   │
   ├─ 基本面分析
   │  └─ PE 15.2 vs 同業 18.5（相對便宜 ✅）
   │
   └─ 機率分析
      ├─ Bull case（35% 機率）→ 目標 1150
      ├─ Base case（50% 機率）→ 目標 1000
      └─ Bear case（15% 機率）→ 目標 850

4️⃣ 生成建議
   └─ 「預期報酬 9.6%，虧錢機率 40%
        建議配置 15% 資金，停損 900 元，停利 1052/1176」
```

### 關鍵特性：動態規則系統

**傳統做法（不好）：**
```python
# 代碼中寫死規則
stop_loss = -15  # 停損 -15%
if stock == 'TSMC':
    stop_loss = -10  # 特例
```
❌ 缺點：改規則要改代碼、測試、部署

**新做法（好）：**
```python
# 從 YAML 讀取規則
loader = ConfigLoader()
stop_loss = loader.get_stop_loss('TSMC_2330')  # → -10
```
✅ 優點：改規則 = 編輯 YAML 檔案，完成！

## 📁 專案結構

```
finance-analyst/
├── .git/                     # Git 版本控制
├── .gitignore               # 防止敏感資訊洩露（API Key 等）
│
├── 📁 src/                  # 程式碼
│   ├── __init__.py
│   ├── config_loader.py     # ✅ 讀取動態規則（已完成）
│   ├── fetch_market_data.py # 數據收集（Phase 2）
│   ├── technical_analysis.py# 技術分析（Phase 2）
│   ├── fundamental_analysis.py# 基本面分析（Phase 3）
│   └── probability_analysis.py# 機率分析（Phase 3）
│
├── 📁 config/               # 設定檔（動態規則容器）
│   ├── settings.example.yaml # ✅ 範本（會上傳，安全）
│   └── settings.yaml        # ✅ 實際設定（.gitignore 忽略，保密）
│       ├─ 全域規則
│       ├─ 股票分組規則
│       └─ 個別股票規則（TSMC、NVDA、BRK_B 等）
│
├── 📁 data/                 # 市場數據
│   ├── raw/                 # 原始數據（未處理）
│   ├── processed/           # 處理後的數據
│   └── temp/                # 暫時文件
│
├── 📁 tests/                # 單元測試（Phase 2+）
│
├── 📁 docs/                 # 文檔（開發中）
│
├── 📁 logs/                 # 執行日誌
│
├── 📁 outputs/              # 分析結果輸出
│
├── requirements.txt         # ✅ Python 依賴清單
├── README.md               # ✅ 本檔案
└── SKILL.md                # Skill 定義
```

## 🚀 快速開始

### 1. 複製設定範本

```bash
# 範本已經複製為 settings.yaml
# 只需要編輯 config/settings.yaml，填入：
# - API Key
# - 你的監控規則
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 測試配置讀取

```python
from src.config_loader import ConfigLoader

# 初始化
loader = ConfigLoader()

# 取得台積電的停損點
stop_loss = loader.get_stop_loss('TSMC_2330')
print(f"TSMC 停損: {stop_loss}%")  # 輸出: -10

# 取得 NVIDIA 的停利點
tp1 = loader.get_take_profit_1('NVDA')
print(f"NVDA 停利1: {tp1}%")  # 輸出: 15

# 列印設定摘要
loader.print_summary()
```

## 🎯 核心特性

### ✅ 動態規則系統
- **全域規則** — 應用於所有股票的預設值
- **分組規則** — 針對不同風險等級的股票分組
- **個別規則** — 特定股票可覆蓋上層規則
- **無需改代碼** — 改規則 = 編輯 YAML 檔案

### ✅ 安全第一
- `.gitignore` 防止 API Key 洩露
- `settings.example.yaml` 作為公開範本
- `settings.yaml` 包含敏感信息，被保護

### ✅ 機率而非預測
- 不聲稱能「預測確切價格」
- 提供「機率分佈」和「期望報酬」
- 三情景分析（Bear/Base/Bull）

### ✅ 易於擴展
- 清晰的資料夾結構
- 模組化設計
- 新增股票 = 在 settings.yaml 加一行

## 🔒 安全性

⚠️ **重要提醒：**

```
❌ 不要：
   • 上傳 config/settings.yaml（包含 API Key）
   • 上傳 .env 檔案
   • 在代碼中寫 API Key

✅ 要做：
   • 使用 settings.example.yaml 作為範本
   • settings.yaml 已被 .gitignore 忽略
   • API Key 應從環境變數讀取（更安全）
```

## 📈 開發計劃

### ✅ Phase 1（本週完成）
- [x] Git 初始化 + .gitignore
- [x] 資料夾結構
- [x] requirements.txt
- [x] 動態規則系統
- [x] README

### 📍 Phase 2（下週）
- [ ] fetch_market_data.py（數據收集）
- [ ] technical_analysis.py（技術分析）
- [ ] 評估集建立

### 📍 Phase 3（下下週）
- [ ] fundamental_analysis.py（基本面分析）
- [ ] probability_analysis.py（機率分析）
- [ ] 完整測試

### 📍 Phase 4（月底）
- [ ] analysis_report_generator.py（報告生成）
- [ ] Claude 完整整合
- [ ] 文檔完善

## 📝 使用範例

### 新增股票

只需在 `config/settings.yaml` 中添加：

```yaml
stocks:
  APPLE_AAPL:
    name: "Apple"
    market: "us"
    exchange: "NASDAQ"
    group: "us_mega_cap"
    custom_stop_loss: -18
    custom_take_profit_1: 6
    custom_take_profit_2: 12
```

然後代碼會自動使用這些規則：

```python
loader.get_stop_loss('APPLE_AAPL')  # → -18
loader.get_take_profit_1('APPLE_AAPL')  # → 6
```

### 修改分組規則

只需修改 `config/settings.yaml` 中的分組設定：

```yaml
stock_groups:
  taiwan_tech:
    stop_loss: -10  # 改為 -10（之前是 -12）
```

所有屬於 `taiwan_tech` 的股票都會自動使用新規則。

## 🔗 相關資源

- **Claude API 文檔**：https://docs.claude.com
- **YAML 學習**：https://yaml.org/
- **技術分析指標**：references/tools/technical-indicators.md
- **市場指南**：references/markets/

## 📞 開發狀態

```
目前進度：Phase 1 完成 ✅

下一步：開始 Phase 2
  1. 實裝 fetch_market_data.py
  2. 實裝 technical_analysis.py
  3. 建立測試
```

## 📄 License

MIT License

---

**最後更新**：2025-03-28
**版本**：1.0.0
**狀態**：Phase 1 完成，準備 Phase 2

