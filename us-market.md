# us-market.md — 美股深度分析框架

> 本文件為 `SKILL.md` 的美股專屬延伸，涵蓋期權流、機構動向、重點族群、重要事件日曆等美股特有分析工具。
> 使用前請先確認 SKILL.md 的市場環境判斷，再搭配本文件操作。

---

## 一、期權流解讀（Options Flow）

### 為何期權流是領先指標
- 機構和聰明錢在建倉**股票前，通常先佈局期權**
- 異常的期權買盤（尤其是大型掃單）往往預示 1-5 天內的方向
- 散戶通常買 Put 保護或賣 Call，機構的反向操作是真正的信號

### 關鍵術語

| 術語 | 說明 |
|------|------|
| Sweep | 跨多個交易所的大型掃單，代表急迫性，機構主導 |
| Block | 單筆大宗交易，通常是機構一次性建倉 |
| Unusual Options Activity (UOA) | 相較於日均量，成交量異常放大的期權 |
| IV Crush | 財報後隱含波動率驟降，買方期權大虧 |
| Gamma Squeeze | 造市商被迫 Delta 對沖引發的股價加速上漲 |
| Dark Pool | 暗池交易，大宗買賣不顯示在公開盤，但事後可查 |

### 期權流訊號解讀

| 訊號 | 意涵 | 操作建議 |
|------|------|---------|
| 大量 Call Sweep（OTM，近期到期）| 機構急迫性做多 | 跟隨多方操作 |
| 大量 Put Sweep（OTM，近期到期）| 機構急迫性做空或對沖 | 注意下行風險 |
| 深度 OTM Call（1-3 個月後到期）| 機構中線看漲，可能有催化劑 | 中線做多參考 |
| Put/Call Ratio 急升至 2.0+ | 市場極度恐慌 | 逆向做多考慮 |
| IV 遠低於歷史均值 | 市場低估波動性 | 考慮買入期權 |
| 財報前 IV 急升 | 市場預期大波動 | 避免裸買期權 |

### 期權流查詢工具
- **Unusual Whales**：https://unusualwhales.com/（付費，最全面）
- **Barchart Unusual Options**：https://www.barchart.com/options/unusual-activity（免費）
- **Market Chameleon**：https://marketchameleon.com/（IV 比較）
- **Finviz**：https://finviz.com/（族群熱力圖，免費）

---

## 二、機構動向追蹤

### 13F 申報（季度持股揭露）
- 管理資產超過 1 億美元的機構，每季須向 SEC 申報持股（13F）
- **申報截止日**：每季結束後 45 天內（Q1→5/15，Q2→8/15，Q3→11/15，Q4→2/15）
- 查詢來源：
  - https://www.sec.gov/cgi-bin/browse-edgar（官方 SEC）
  - https://whalewisdom.com/（整合版，追蹤巴菲特、Druckenmiller 等大師持倉）
  - https://fintel.io/（機構持股變化追蹤）

### 重要機構持倉解讀
- **增持 + 股價尚未大漲**：最佳進場機會
- **多家機構同時增持同一股**：籌碼共識強，中線偏多
- **大師清倉**：不一定看空（可能再平衡），但需注意
- 注意：13F 有 45 天延遲，進出場時效較低，適合作為中線參考

### 內部人買賣（Insider Trading）
- 內部人**買入**（尤其 CEO/CFO 大額買入）= 強烈看好訊號
- 內部人賣出 = 不一定看空（可能是節稅、行使選擇權）
- 查詢來源：https://www.sec.gov/cgi-bin/browse-edgar 或 https://openinsider.com/

### 暗池（Dark Pool）成交
- 暗池成交佔美股總量約 30-40%，是機構大宗交易的主要場所
- 暗池買入後股價未動 → 可能是分批建倉，後續有上漲潛力
- 查詢來源：https://unusualwhales.com/darkpool（付費）

---

## 三、總體環境判斷工具

### 必看指標清單

| 指標 | 意涵 | 多空判斷 |
|------|------|---------|
| **VIX（恐慌指數）** | S&P 500 的隱含波動率 | <15 偏多；>25 恐慌；>35 極端恐慌（反向做多機會）|
| **AAII 散戶情緒調查** | 散戶看多/看空比例（週報） | 逆向指標：散戶極度看空時往往是底部 |
| **美債 10 年期殖利率** | 無風險利率，影響科技股估值 | 殖利率快速上升 → 科技股承壓 |
| **DXY（美元指數）** | 美元強弱 | 美元強 → 壓制原物料與新興市場；美元弱 → 利好風險資產 |
| **Fed Funds Rate 期貨** | 市場對 Fed 升降息的預期 | CME FedWatch 工具可查實時概率 |
| **納指 / 標普 200MA** | 長期趨勢判斷 | 站上 200MA = 多頭；跌破 200MA = 空頭 |
| **NYSE 漲跌線（A/D Line）** | 市場廣度 | A/D 上升但指數滯漲 → 上漲確認；A/D 下跌但指數新高 → 背離警示 |

### CME FedWatch 工具
- 查詢 Fed 升降息概率：https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html
- 分析框架：
  - 市場預期降息 → 成長股/科技股利好
  - 市場預期升息 → 價值股/金融股相對強勢，科技股承壓
  - 預期轉向時（pivot 訊號）→ 成長股大幅反彈機會

---

## 四、美股重點族群

### 🤖 AI / 科技族群（Magnificent 7 + 供應鏈）

| 類別 | 代表股 | Ticker | 主要觀察重點 |
|------|--------|--------|------------|
| AI 基礎設施 | NVIDIA | NVDA | GPU 出貨量、Blackwell 架構、資料中心營收 |
| AI 雲端 | Microsoft | MSFT | Azure AI 成長率、Copilot 商業化 |
| AI 雲端 | Amazon | AMZN | AWS 成長率、Bedrock AI 服務 |
| AI 雲端 | Google | GOOGL | Gemini 進展、YouTube 廣告、搜尋市佔 |
| AI 應用 | Meta | META | AI 廣告 ROI、Llama 開源生態、Reality Labs |
| 消費科技 | Apple | AAPL | iPhone 銷量、Apple Intelligence、服務收入比例 |
| 電動車/AI | Tesla | TSLA | FSD 進展、Optimus 機器人、能源業務 |
| 半導體 | AMD | AMD | MI 系列 AI GPU 市佔、資料中心 CPU |
| 半導體 | Broadcom | AVGO | 客製化 AI 晶片（XPU）、VMware 整合 |
| 半導體設備 | ASML | ASML | EUV 出貨量、中國銷售限制影響 |

### 💊 生技醫療族群

| 類別 | 代表股 | Ticker | 主要觀察重點 |
|------|--------|--------|------------|
| 減肥藥 | Eli Lilly | LLY | GLP-1 需求（Mounjaro/Zepbound）、產能擴充 |
| 減肥藥 | Novo Nordisk | NVO | Ozempic/Wegovy 全球滲透率 |
| 醫療設備 | UnitedHealth | UNH | 保險業績、醫療費用通膨 |
| 生技指數 | iShares Biotech | IBB | 生技族群整體走勢參考 |

### 🏦 金融族群

| 類別 | 代表股 | Ticker | 主要觀察重點 |
|------|--------|--------|------------|
| 投資銀行 | JPMorgan | JPM | 利差收益、交易部門、貸款品質 |
| 投資銀行 | Goldman Sachs | GS | M&A 活動、資本市場復甦 |
| 支付 | Visa | V | 消費支出數據、跨境交易量 |
| 支付 | Mastercard | MA | 跨境旅遊恢復、數位支付滲透 |
| 加密相關 | Coinbase | COIN | 加密市場成交量、監管環境 |

### ⚡ 能源 / 傳統產業

| 類別 | 代表股 | Ticker | 主要觀察重點 |
|------|--------|--------|------------|
| 石油 | ExxonMobil | XOM | 油價走勢、產能規劃 |
| 石油 | Chevron | CVX | 自由現金流、股息成長 |
| 天然氣 | LNG 相關 | LNG | 歐洲能源需求、出口量 |

### 🛡️ 防禦族群（避險首選）

| 類別 | 代表股 | Ticker | 主要觀察重點 |
|------|--------|--------|------------|
| 消費必需 | Walmart | WMT | 零售銷售數據、通膨影響 |
| 公用事業 | NextEra Energy | NEE | 利率敏感性、綠能發展 |
| 黃金 | Gold ETF | GLD | 避險需求、實際利率走勢 |
| 國防 | Lockheed Martin | LMT | 地緣政治緊張度、國防預算 |

---

## 五、重要事件日曆

### 每月固定事件

| 日期區間 | 事件 | 影響 |
|---------|------|------|
| 每月第一個週五 | 非農就業報告（NFP） | 影響 Fed 政策預期，市場波動大 |
| 每月中旬 | CPI（消費者物價指數） | 通膨數據，直接影響降息預期 |
| 每月中旬 | PPI（生產者物價指數） | 通膨領先指標 |
| 每月下旬 | PCE（個人消費支出物價） | Fed 最偏好的通膨指標 |
| 每月下旬 | GDP 初值/修正值 | 經濟成長速度 |

### 季度財報季

| 時期 | 說明 |
|------|------|
| 1 月中旬 ～ 2 月底 | Q4 財報季，全年展望最重要 |
| 4 月中旬 ～ 5 月底 | Q1 財報季 |
| 7 月中旬 ～ 8 月底 | Q2 財報季，夏季量縮 |
| 10 月中旬 ～ 11 月底 | Q3 財報季 |

### 財報操作原則
- **財報前**：IV 上升 → 避免裸買期權，除非有強烈方向性預判
- **財報後**：IV Crush → 期權持有者多數虧損，但股價可能大幅波動
- **Beat & Raise**：EPS 與營收雙超預期 + 上調展望 → 強烈做多訊號
- **Miss & Lower**：雙項不及預期 + 下調展望 → 強烈做空訊號
- **Beat 但股價不漲**：市場預期已充分反映，或指引令人失望 → 小心陷阱

### FOMC 會議（每年 8 次）
- **會議前**：市場通常盤整等待，波動性降低
- **決策公布後**：鮑威爾記者會言論比利率決定本身更重要
- **觀察重點**：利率點陣圖（Dot Plot）、前瞻指引措辭
- FOMC 日期查詢：https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

---

## 六、美股技術面特有觀察

### 主要指數對比分析

| 指數 | 特性 | 強弱解讀 |
|------|------|---------|
| S&P 500（SPX） | 大盤整體，500 大企業 | 主要趨勢指標 |
| Nasdaq 100（NDX）| 科技權重高 | 科技/成長股方向 |
| Dow Jones（DJIA）| 30 大藍籌，工業偏重 | 傳統經濟健康度 |
| Russell 2000（RUT）| 小型股 | 風險偏好指標，領先反轉 |
| S&P Equal Weight | 等權重 S&P | 市場廣度，排除 Mag7 扭曲 |

- **NDX > SPX 強**：科技/成長股主導，風險偏好高
- **RUT > SPX 強**：小型股超漲，市場廣泛參與（健康多頭）
- **DJIA > NDX 強**：防禦輪動，市場偏保守

### 關鍵支撐/壓力區
- **整數關卡**：SPX 5000/5500/6000，NDX 20000/21000
- **斐波那契回調**：38.2%、50%、61.8% 是常見支撐/壓力
- **前高/前低**：突破前高要有量能配合，否則假突破機率高
- **200MA**：長期多空分界線，機構高度重視

---

## 七、美股數據來源

| 資料類型 | 來源 |
|---------|------|
| 即時行情 / 技術圖表 | https://www.tradingview.com/ |
| 期權流 / 異常活動 | https://www.barchart.com/options/unusual-activity |
| 機構持倉 13F | https://whalewisdom.com/ |
| 內部人交易 | https://openinsider.com/ |
| 財報日程 | https://finance.yahoo.com/calendar/earnings |
| 總經日曆 | https://www.forexfactory.com/calendar |
| Fed Watch | https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html |
| 族群熱力圖 | https://finviz.com/map.ashx |
| SEC 申報 | https://www.sec.gov/cgi-bin/browse-edgar |
| 美股新聞 | https://www.bloomberg.com/ 或 https://www.reuters.com/ |

---

## 八、美股操作心法

1. **跟著機構的期權流走**：大型 Sweep Call 是短線方向最可靠的訊號
2. **財報季是最大機會也是最大風險**：Beat & Raise 是最強的催化劑，但 IV Crush 會吃掉期權獲利
3. **VIX > 30 是買入機會**：恐慌指數極端高位往往是逆向做多的好時機
4. **美聯準會政策是一切的錨**：降息週期中成長股/科技股跑贏，升息週期中價值股/能源跑贏
5. **Mag7 決定趨勢，小型股確認廣度**：大盤創新高但 RUT 疲軟 → 行情可能不持久
6. **缺口理論**：跳空缺口是強力支撐/壓力，尤其財報後的缺口
7. **流動性優先**：美股流動性遠高於台股，可用更小的停損換更大的部位
8. **美股盤前/盤後行情**：財報通常在盤後或盤前公布，注意隔夜跳空風險
