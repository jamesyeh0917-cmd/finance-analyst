# tw-coverage.md — My-TW-Coverage 台股研究資料庫

> 本文件說明如何在台股分析中整合 **My-TW-Coverage 1,733家公司** 本地資料庫。
> 當分析台股個股、產業、供應鏈影響時，**優先從本資料庫提取結構化數據**，再補充即時網路搜尋。

---

## 資料庫概覽

| 項目 | 內容 |
|------|------|
| 覆蓋範圍 | 台灣上市+上櫃共 **1,733 家**公司 |
| 產業分類 | **98 個**產業 (Semiconductors, Electronic Components, Software...) |
| 研究報告 | **1,735 個** Markdown 研究報告 (Pilot_Reports/) |
| 財務資料來源 | yfinance 定期更新 (P/E, P/B, 毛利率, 客戶, 供應商) |
| 供應鏈索引 | tw_rev_index.json — entity → [ticker...] 逆向查詢 |
| 更新週期 | 每月 1 日自動更新 (monthly_update.py) |
| 資料路徑 | 股票監控平台/Pilot_Reports/ + tw_index.json + tw_rev_index.json |

---

## 可用 API 端點（股票監控平台運行時）

```
GET /api/company/{ticker}/profile
→ { name, sector, industry, description, wikilinks[], themes[], found }

GET /api/company/{ticker}/financials
→ { pe_ttm, forward_pe, pb, ps, ev_ebitda,
    gross_margin, op_margin, net_margin,
    revenue_ttm, mktcap, ev, price, price_date,
    customers[], suppliers[] }

GET /api/search-companies?q={關鍵字}
→ [{ ticker, name, sector, industry, match_type, themes[] }]

GET /api/sector/{sector}/leaders?n=10
→ { sector, results: [{ ticker, name, industry, mktcap_bil }] }

POST /api/supply-chain-impact
Body: { title: "新聞標題", portfolio: ["2330","2454"] }
→ { entities_found[], affected_holdings[], non_holding_affected[] }
```

---

## Python 模組 (tw_coverage.py) 直接使用

```python
import tw_coverage as twcov

# 1. 個股基本資料
profile = twcov.get_profile("2330")
# → { name:"台積電", sector:"Technology", industry:"Semiconductors",
#     wikilinks:["NVIDIA","Apple","CoWoS","HBM",...], themes:["AI","先進製程"] }

# 2. 財務數據（從 Pilot_Reports markdown 解析）
fin = twcov.get_financials("2330")
# → { pe_ttm:22.3, forward_pe:19.8, pb:6.2, gross_margin:54.3,
#     customers:["NVIDIA","Apple","AMD"], suppliers:["ASML","Applied Materials"] }

# 3. 供應鏈反查：誰跟 NVIDIA 有關？
companies = twcov.find_related_companies("NVIDIA", max_results=15)

# 4. 關鍵字搜尋（wikilink精確 + 描述模糊）
results = twcov.search_companies_by_keyword("CoWoS")
results = twcov.search_companies_by_keyword("AI伺服器")

# 5. 多股供應鏈重疊分析
overlap = twcov.get_supply_chain_overlap(["2330","2454","3711"])
# → { "2330-2454": ["NVIDIA","ARM","CoWoS"], ... }

# 6. 新聞供應鏈影響分析
impact = twcov.analyze_supply_chain_impact(
    "NVIDIA H200 出貨延遲影響台積電訂單",
    portfolio_tickers=["2330","2454"]
)

# 7. 產業龍頭（按市值排序）
leaders = twcov.get_sector_leaders("Semiconductors", top_n=10)

# 8. 資料庫統計
stats = twcov.db_stats()
```

---

## 台股個股深度分析整合流程

分析台股任何個股時，按此四步驟整合本地資料庫與即時搜尋：

```
Step 1  get_profile(ticker)
        → 取得公司名稱、產業定位、供應鏈節點(wikilinks)、主題標籤

Step 2  get_financials(ticker)
        → P/E、P/B、毛利率、客戶清單、供應商清單
        → 若 found=False，此步跳過，完全依賴 web_search

Step 3  web_search 最新即時數據（必做）
        → 最新股價、近期法人動向、最新財報、重大新聞

Step 4  整合三維輸出
        → 基本面(DB估值+客戶結構) + 即時數據(股價+法人) + 籌碼面(tw-market.md)
```

**估值比較範例（同業橫比）：**
先用 `get_sector_leaders("Semiconductors")` 拿到同業清單，
再批量呼叫 `get_financials()` 對比 P/E、毛利率，
最後 web_search 補充最新股價計算實時估值。

---

## 產業鏈新聞影響分析框架

新聞提到「客戶/供應商/技術名詞」時，用供應鏈逆查找出受影響台股：

```
Step 1  identify entities from title
        觸發詞：Apple/NVIDIA/HBM/CoWoS/AI伺服器/EUV/碳化矽...

Step 2  find_related_companies(entity)
        → 找出 wikilinks 中包含該 entity 的所有台股

Step 3  分層分析影響
        直接受益/受損：持有該客戶訂單的第一層供應商
        間接傳導：上游設備/材料商、下游組裝廠
        無關：wikilinks 不含該 entity 的同業

Step 4  時間維度
        瞬間(1-2天): 情緒炒作，CoWoS/HBM等熱門主題波動最大
        短期(3-10天): 訂單調整預期，看法說會更新
        中長期(1月+): 實際出貨/盈利影響反映財報
```

---

## 重要供應鏈 Entity（資料庫識別關鍵詞）

新聞標題含以下關鍵詞時，自動觸發供應鏈分析：

**國際科技客戶：**
Apple · NVIDIA · Microsoft · Meta · Google · Amazon · Tesla ·
Qualcomm · AMD · Intel · Broadcom · Samsung · MediaTek

**台灣主要公司：**
台積電 · 鴻海 · 聯發科 · 日月光 · 聯電 · 廣達 · 緯創 · 仁寶 ·
英業達 · 台達電 · 鴻準 · 大立光 · 台光電 · 華碩 · 微星

**技術/產品主題（高市場敏感度）：**
CoWoS · HBM · AI伺服器 · 矽光子 · CPO · EUV · VCSEL ·
MLCC · ABF · 碳化矽 · 氮化鎵 · 磷化銦 · 電動車 · 低軌衛星 · 5G · PCB

---

## 98 個產業分類（get_sector_leaders 可用）

**半導體與科技（核心）：**
Semiconductors · Semiconductor Equipment & Materials ·
Electronic Components · Computer Hardware ·
Software - Application · Software - Infrastructure ·
Information Technology Services · Communication Equipment ·
Scientific & Technical Instruments

**AI / 伺服器 / 雲端：**
Electronic Components(CoWoS封裝) · Semiconductors(晶圓代工/IC設計) ·
Computer Hardware(伺服器/儲存) · Internet Content & Information

**電動車 / 綠能：**
Auto Parts · Solar · Utilities - Renewable ·
Specialty Chemicals(電池材料) · Electrical Equipment & Parts

**傳統台灣強項：**
Specialty Industrial Machinery · Metal Fabrication · Steel ·
Textile Manufacturing · Packaging & Containers ·
Chemicals · Conglomerates

---

## 數據限制與解決方案

| 限制 | 說明 | 解決方案 |
|------|------|---------|
| 財務數據時效 | 每月更新，非即時 | 必須 web_search 補充最新財報/股價 |
| 股價引用 | 報告中股價為更新當時 | 永遠以 web_search 即時股價為準 |
| 部分財務缺失 | found=False 代表無報告 | 完全依賴 web_search |
| 英文產業名稱 | Pilot_Reports 使用英文分類 | ticker 格式：4-5位數字，不含 .TW |
| 中小型股深度 | 小型股研究報告較簡略 | 大型股優先；中小型用描述/wikilink搜尋 |

---

## 使用優先順序總結

```
台股分析 3 步驟：
①  tw_coverage 本地 DB  →  供應鏈、估值基準、客戶/供應商結構
②  web_search 即時數據  →  最新股價、法人動向、當日新聞、財報
③  tw-market.md 框架   →  三大法人籌碼解讀、融資融券、技術型態

核心價值：
- 供應鏈連動分析：新聞 entity → 受影響台股（持倉+非持倉）
- 同業估值橫比：同產業 P/E / 毛利率 / 供應鏈深度比較
- 客戶/供應商結構：理解公司在全球科技鏈中的定位
```

> ⚠️ **股價永遠以即時搜尋為準。** 資料庫的核心優勢是結構化知識（供應鏈、估值脈絡、客戶結構），
> 而非即時報價。
