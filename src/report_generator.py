"""
📋 Report Generator — 分析報告生成器

功能：
  • 生成 Markdown 格式的完整分析報告
  • 生成三情景（牛市/基準/熊市）對照表
  • 生成綜合風險評估摘要

使用示例：
  generator = ReportGenerator()
  report = generator.generate_probability_report(results)
  generator.save_report(report, 'outputs/report.md')
"""

import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """分析報告生成器"""
    
    def __init__(self):
        """初始化報告生成器"""
        logger.info("✅ 報告生成器初始化完成")
    
    def generate_probability_report(self, results: Dict) -> str:
        """
        生成概率風險分析的完整報告
        
        Args:
            results: 蒙特卡洛分析結果字典
        
        Returns:
            Markdown 格式的報告文本
        """
        
        report = f"""# 📊 概率風險分析報告
        
生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📌 執行摘要

本報告基於蒙特卡洛模擬（10,000 條股價路徑），為三檔股票計算了一年期預期目標價
和風險指標。模擬基於公平的基本面評分，確保高分股獲得更高的成長假設。

---

## 📈 股票分析結果

"""
        
        # 為每支股票生成詳細分析
        for code, result in results.items():
            if 'error' in result:
                continue
            
            report += self._generate_stock_section(code, result)
        
        # 添加三情景對照表
        report += self._generate_scenario_table(results)
        
        # 添加風險指標總結
        report += self._generate_risk_summary(results)
        
        # 添加方法論說明
        report += self._generate_methodology()
        
        return report
    
    def _generate_stock_section(self, stock_code: str, result: Dict) -> str:
        """生成單支股票的分析段落"""
        
        current_price = result['current_price']
        fundamental_score = result['fundamental_score']
        normalized_score = result['normalized_score']
        score_level = result['score_level']
        
        drift = result['drift']
        volatility = result['volatility']
        
        target_prices = result['target_prices']
        risk_metrics = result['risk_metrics']
        stats = result['statistics']
        
        section = f"""### {stock_code} — {score_level}

**基本面評分**
- 原始評分：{fundamental_score:.1f}
- 歸一化評分：{normalized_score:.1f}/100
- 評分等級：{score_level}

**當前股價**
- 現在價格：${current_price:.2f}

**模擬參數**（基於評分）
- 預期年成長率：{drift*100:.2f}%
- 年化波動率：{volatility*100:.2f}%
- 信心水準：95%（1 年期）

**目標價區間**

| 情景 | 目標價 | 相對現價 | 備註 |
|------|--------|----------|------|
| 🔺 牛市 | ${target_prices['bullish']:.2f} | +{((target_prices['bullish']/current_price - 1)*100):.1f}% | 75 百分位 |
| ➡️ 基準 | ${target_prices['base']:.2f} | +{((target_prices['base']/current_price - 1)*100):.1f}% | 均值 |
| 🔻 熊市 | ${target_prices['bearish']:.2f} | {((target_prices['bearish']/current_price - 1)*100):.1f}% | 25 百分位 |

**風險指標**（95% 信心水準）

- **VaR（風險價值）**
  - 相對損失：{risk_metrics['var_95_return']*100:.2f}%
  - 絕對損失：${risk_metrics['var_95_dollar']:.2f}
  - 解釋：在 95% 的情況下，年內虧損不超過此值

- **CVaR（期望缺口）**
  - 相對損失：{risk_metrics['cvar_95_return']*100:.2f}%
  - 絕對損失：${risk_metrics['cvar_95_dollar']:.2f}
  - 解釋：超出 VaR 部分的平均損失

- **最大回撤**
  - 平均最大下跌：{risk_metrics['max_drawdown']*100:.2f}%
  - 解釋：路徑中相對高點的最大下跌幅度

**統計分佈**

| 指標 | 數值 |
|------|------|
| 最小價格 | ${stats['min_price']:.2f} |
| 5 百分位 | ${stats['percentile_5']:.2f} |
| 25 百分位 | ${stats['percentile_25']:.2f} |
| 中位數 | ${stats['median_price']:.2f} |
| 75 百分位 | ${stats['percentile_75']:.2f} |
| 95 百分位 | ${stats['percentile_95']:.2f} |
| 最大價格 | ${stats['max_price']:.2f} |
| 平均回報率 | {stats['mean_return']*100:.2f}% |

---

"""
        
        return section
    
    def _generate_scenario_table(self, results: Dict) -> str:
        """生成三情景對照表"""
        
        table = """## 📊 三情景對照表

| 股票 | 當前價 | 熊市 | 基準 | 牛市 | 基準回報 | 風險等級 |
|------|--------|------|------|------|----------|---------|
"""
        
        for code, result in results.items():
            if 'error' in result:
                continue
            
            current = result['current_price']
            bearish = result['target_prices']['bearish']
            base = result['target_prices']['base']
            bullish = result['target_prices']['bullish']
            
            return_pct = (base / current - 1) * 100
            risk = result['risk_metrics']['var_95_return'] * 100
            
            risk_level = "🔴 高風險" if risk < -20 else "🟠 中風險" if risk < -15 else "🟢 低風險"
            
            table += f"| {code} | ${current:.2f} | ${bearish:.2f} | ${base:.2f} | ${bullish:.2f} | {return_pct:+.1f}% | {risk_level} |\n"
        
        table += "\n---\n\n"
        
        return table
    
    def _generate_risk_summary(self, results: Dict) -> str:
        """生成風險指標總結"""
        
        summary = """## ⚠️ 風險指標總結

### VaR 排序（95% 信心水準）

損失幅度最小（風險最低）到最大（風險最高）：

"""
        
        risk_ranking = []
        for code, result in results.items():
            if 'error' in result:
                continue
            
            var_pct = result['risk_metrics']['var_95_return'] * 100
            risk_ranking.append((code, var_pct))
        
        risk_ranking.sort(key=lambda x: x[1], reverse=True)  # 從低損失到高損失
        
        for i, (code, var_pct) in enumerate(risk_ranking, 1):
            summary += f"{i}. **{code}**：{var_pct:.2f}%\n"
        
        summary += """

### 最大回撤排序

單次跌幅最小到最大：

"""
        
        dd_ranking = []
        for code, result in results.items():
            if 'error' in result:
                continue
            
            max_dd = result['risk_metrics']['max_drawdown'] * 100
            dd_ranking.append((code, max_dd))
        
        dd_ranking.sort(key=lambda x: x[1])  # 從低到高
        
        for i, (code, max_dd) in enumerate(dd_ranking, 1):
            summary += f"{i}. **{code}**：{max_dd:.2f}%\n"
        
        summary += "\n---\n\n"
        
        return summary
    
    def _generate_methodology(self) -> str:
        """生成方法論說明"""
        
        methodology = """## 🔬 方法論

### 蒙特卡洛模擬

本分析使用**幾何布朗運動**（Geometric Brownian Motion, GBM）模型：

```
dS = μ·S·dt + σ·S·dW
```

其中：
- S：股價
- μ：預期收益率（Drift），根據基本面評分推導
- σ：波動率，根據基本面評分調整
- dt：時間微元（1 天）
- dW：維納過程（Wiener Process）

### 參數推導

**預期收益率（Drift）**

基於基本面評分進行映射：
- 評分 50 → 預期成長 5%（市場平均）
- 評分 75 → 預期成長 12%（超額成長）
- 評分 100 → 預期成長 20%（最優異）
- 評分 136+ → 預期成長 ~19-30%（超級優秀，有上限）

**波動率（Volatility）**

根據基本面評分調整：
- 高分股（>75）：波動率 20-25%（成長穩定）
- 低分股（<50）：波動率 30-50%（風險較高）

### 風險指標

**VaR（風險價值，95% 信心水準）**
- 在 95% 的情況下，年內損失不會超過此值
- 例：VaR = -14.16% 意味著 95% 機率年內虧損 ≤ 14.16%

**CVaR（條件風險價值）**
- 超出 VaR 的平均損失（最壞 5% 情況的平均虧損）
- 例：CVaR = -20.77% 意味著最壞 5% 情況平均虧損 20.77%

**最大回撤**
- 股價相對歷史高點的最大下跌幅度
- 反映單次最壞情況下的跌幅

### 模擬配置

- 模擬路徑：10,000 條
- 時間步長：252 個交易日（一年）
- 隨機種子：固定（確保重複性）
- 計算時間：< 1 秒

---

## 📝 免責聲明

本報告僅供參考，不構成投資建議。蒙特卡洛模擬基於歷史數據和假設推導，
未來實際走勢可能與模擬結果有重大差異。投資決策應綜合考慮多重因素，
並諮詢專業投資顧問。

"""
        
        return methodology
    
    def save_report(self, report: str, filepath: str) -> None:
        """
        保存報告到文件
        
        Args:
            report: 報告文本
            filepath: 文件路徑
        """
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ 報告已保存到：{filepath}")
    
    def generate_target_price_table(self, results: Dict) -> str:
        """
        生成簡潔的目標價對照表（CSV 格式）
        
        Args:
            results: 分析結果
        
        Returns:
            CSV 格式的對照表
        """
        
        csv = "股票代碼,當前股價,熊市目標,基準目標,牛市目標,基準漲幅%,VaR_%,最大回撤_%\n"
        
        for code, result in results.items():
            if 'error' in result:
                continue
            
            current = result['current_price']
            targets = result['target_prices']
            risks = result['risk_metrics']
            
            return_pct = (targets['base'] / current - 1) * 100
            var_pct = risks['var_95_return'] * 100
            dd_pct = risks['max_drawdown'] * 100
            
            csv += (f"{code},{current:.2f},{targets['bearish']:.2f},"
                   f"{targets['base']:.2f},{targets['bullish']:.2f},"
                   f"{return_pct:.1f},{var_pct:.2f},{dd_pct:.2f}\n")
        
        return csv
    
    def save_csv_table(self, csv_data: str, filepath: str) -> None:
        """
        保存 CSV 對照表到文件
        
        Args:
            csv_data: CSV 數據
            filepath: 文件路徑
        """
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        logger.info(f"✅ CSV 對照表已保存到：{filepath}")


# ==========================================
# 主函數
# ==========================================

def main():
    """測試報告生成器"""
    
    print("✅ 報告生成器模組已準備")


if __name__ == "__main__":
    main()

