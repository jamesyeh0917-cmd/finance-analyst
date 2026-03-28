"""
📊 Stock Classifier — 股票自動分類器

功能：
  • 根據 EPS 成長率 和 股息收益率 自動判定股票類型
  • 支持三類股票：成長股 (Growth)、價值股 (Value)、防守股 (Defensive)
  • 可選：四類股票 (Growth, Value, Defensive, 加上 ETF)

設計邏輯：
  成長股 (Growth)：
    • EPS 成長 > 25% 且 P/E > 30
    • 追求資本增值，低股息或無股息
    
  防守股 (Defensive)：
    • 股息收益率 > 1.5% 且 EPS 成長 < 15%
    • 追求穩定現金流，低波動性
    
  價值股 (Value)：
    • 介於兩者之間，P/E 低於行業平均
    
  ETF：
    • 特殊分類（如果是指數基金）

使用示例：
  classifier = StockClassifier(config)
  stock_type = classifier.classify(
      stock_code='NVDA',
      pe_ratio=199.9,
      eps_growth=0.35,
      dividend_yield=0.0005,
      dividend_per_share=0.04
  )
  # 輸出：'growth'
"""

import logging
from typing import Dict, Tuple
from pathlib import Path
import sys

# ==========================================
# 日誌配置
# ==========================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """配置日誌系統"""
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level))
    
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()


# ==========================================
# 股票分類器
# ==========================================

class StockClassifier:
    """
    股票自動分類器
    
    根據財務指標自動判定股票類型，支持 3-4 種分類方案
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化分類器
        
        Args:
            config: 配置字典（可選）
        """
        self.config = config or {}
        
        # 分類閾值（可從配置中讀取，否則使用預設值）
        self.thresholds = self.config.get('stock_classifier', {})
        
        # 成長股閾值
        self.growth_thresholds = self.thresholds.get('growth', {})
        self.growth_min_eps_growth = self.growth_thresholds.get('min_eps_growth', 0.25)
        self.growth_min_pe = self.growth_thresholds.get('min_pe', 30)
        
        # 防守股閾值
        self.defensive_thresholds = self.thresholds.get('defensive', {})
        self.defensive_min_dividend_yield = self.defensive_thresholds.get('min_dividend_yield', 0.015)
        self.defensive_max_eps_growth = self.defensive_thresholds.get('max_eps_growth', 0.15)
        
        # 價值股閾值
        self.value_thresholds = self.thresholds.get('value', {})
        self.value_max_pe = self.value_thresholds.get('max_pe', 25)
        
        logger.info("✅ 股票分類器初始化完成")
    
    def classify(self,
                stock_code: str,
                pe_ratio: float,
                eps_growth: float,
                dividend_yield: float = 0.0,
                dividend_per_share: float = 0.0,
                market: str = 'GLOBAL') -> str:
        """
        自動分類股票
        
        Args:
            stock_code: 股票代碼
            pe_ratio: 本益比
            eps_growth: EPS 成長率（0-1，例如 0.35 表示 35%）
            dividend_yield: 股息收益率（0-1，例如 0.015 表示 1.5%）
            dividend_per_share: 每股股息（絕對值）
            market: 市場（GLOBAL、TW、US 等）
        
        Returns:
            股票類型（'growth'、'value'、'defensive'、'etf'）
        """
        
        logger.debug(f"正在分類 {stock_code}...")
        logger.debug(f"  P/E: {pe_ratio:.2f}, EPS 成長: {eps_growth*100:.1f}%, 股息率: {dividend_yield*100:.2f}%")
        
        # 特殊情況：ETF（代碼包含 ETF 或 0050 等指數）
        if self._is_etf(stock_code, market):
            logger.debug(f"  → 判定為 ETF")
            return 'etf'
        
        # 成長股判定
        if self._is_growth_stock(pe_ratio, eps_growth, dividend_yield):
            logger.debug(f"  → 判定為成長股")
            return 'growth'
        
        # 防守股判定
        if self._is_defensive_stock(eps_growth, dividend_yield, dividend_per_share):
            logger.debug(f"  → 判定為防守股")
            return 'defensive'
        
        # 預設：價值股
        logger.debug(f"  → 判定為價值股（預設）")
        return 'value'
    
    def _is_etf(self, stock_code: str, market: str) -> bool:
        """判定是否為 ETF"""
        # 台灣 ETF 通常代碼在 0050-0999 範圍
        if market == 'TW':
            try:
                code_num = int(stock_code)
                if 0 < code_num < 1000:
                    return True
            except ValueError:
                pass
        
        # 代碼包含 ETF 關鍵字
        etf_keywords = ['ETF', 'ETF_', 'INDEX', 'FUND']
        return any(kw in stock_code.upper() for kw in etf_keywords)
    
    def _is_growth_stock(self, pe_ratio: float, eps_growth: float, dividend_yield: float) -> bool:
        """
        判定是否為成長股
        
        條件：
        1. EPS 成長 > 25%（快速成長）
        2. P/E > 30（高估值反映成長潛力）
        3. 股息率 < 1%（不追求股息）
        """
        
        # 條件 1：EPS 成長 > 25%
        high_growth = eps_growth > self.growth_min_eps_growth
        
        # 條件 2：P/E > 30
        high_pe = pe_ratio > self.growth_min_pe
        
        # 條件 3：股息率 < 1%（成長股通常不分紅或分紅少）
        low_dividend = dividend_yield < 0.01
        
        # 成長股條件：(高成長 AND 高 P/E) OR (高成長 AND 低股息)
        return (high_growth and high_pe) or (high_growth and low_dividend)
    
    def _is_defensive_stock(self,
                           eps_growth: float,
                           dividend_yield: float,
                           dividend_per_share: float) -> bool:
        """
        判定是否為防守股
        
        條件：
        1. 股息收益率 > 1.5%（高股息）
        2. EPS 成長 < 15%（穩健成長）
        或
        3. 每股股息 > 1（高股息）且 EPS 成長 < 20%
        """
        
        # 條件 1 + 2：高股息 + 穩健成長
        high_dividend_low_growth = (
            dividend_yield > self.defensive_min_dividend_yield and
            eps_growth < self.defensive_max_eps_growth
        )
        
        # 條件 3：絕對股息值高 + 相對低成長
        high_abs_dividend_moderate_growth = (
            dividend_per_share > 1.0 and
            eps_growth < 0.20
        )
        
        return high_dividend_low_growth or high_abs_dividend_moderate_growth
    
    def get_classification_reason(self,
                                 stock_code: str,
                                 stock_type: str,
                                 pe_ratio: float,
                                 eps_growth: float,
                                 dividend_yield: float) -> str:
        """
        獲取分類原因説明（用於日誌和調試）
        
        Returns:
            分類原因的文字說明
        """
        
        reasons = {
            'growth': (
                f"{stock_code} 判定為成長股，原因：\n"
                f"  • EPS 成長率 {eps_growth*100:.1f}% > 25%（快速成長）\n"
                f"  • P/E {pe_ratio:.1f} > 30（高估值）\n"
                f"  • 股息率 {dividend_yield*100:.2f}% < 1%（低股息）\n"
                f"  → 應用權重：技術面 70%, 基本面 20%, 風險 10%"
            ),
            'value': (
                f"{stock_code} 判定為價值股，原因：\n"
                f"  • EPS 成長率 {eps_growth*100:.1f}%（中等成長）\n"
                f"  • P/E {pe_ratio:.1f}（合理估值）\n"
                f"  • 股息率 {dividend_yield*100:.2f}%（適度股息）\n"
                f"  → 應用權重：技術面 40%, 基本面 50%, 風險 10%"
            ),
            'defensive': (
                f"{stock_code} 判定為防守股，原因：\n"
                f"  • 股息率 {dividend_yield*100:.2f}% > 1.5%（高股息）\n"
                f"  • EPS 成長率 {eps_growth*100:.1f}% < 15%（穩健成長）\n"
                f"  • 重點：穩定現金流和低波動性\n"
                f"  → 應用權重：技術面 20%, 基本面 70%, 風險 10%"
            ),
            'etf': (
                f"{stock_code} 判定為 ETF（指數基金），原因：\n"
                f"  • 是指數基金或 ETF\n"
                f"  • 代表市場整體特性\n"
                f"  → 應用權重：技術面 30%, 基本面 70%, 風險 0%"
            )
        }
        
        return reasons.get(stock_type, "未知類型")


# ==========================================
# 權重管理器
# ==========================================

class WeightManager:
    """
    權重管理器
    
    根據股票類型應用差異化權重
    """
    
    def __init__(self, config: Dict):
        """
        初始化權重管理器
        
        Args:
            config: 配置字典（包含 stock_profiles）
        """
        self.config = config
        self.stock_profiles = config.get('fundamental_analysis', {}).get('stock_profiles', {})
        
        # 預設權重（如果配置中沒有）
        self.default_weights = {
            'valuation': 0.30,
            'profitability': 0.25,
            'financial_health': 0.20,
            'growth': 0.20,
            'cash_flow': 0.05
        }
        
        logger.info("✅ 權重管理器初始化完成")
    
    def get_weights(self, stock_type: str) -> Dict[str, float]:
        """
        根據股票類型獲取權重
        
        Args:
            stock_type: 股票類型（'growth'、'value'、'defensive'、'etf'）
        
        Returns:
            權重字典
        """
        
        # 從配置中讀取
        profile = self.stock_profiles.get(stock_type, {})
        
        if not profile:
            logger.warning(f"⚠️ 未找到 {stock_type} 的配置，使用預設權重")
            return self.default_weights
        
        # 如果配置中有直接的權重定義，使用它
        if 'scoring_weights' in profile:
            return profile['scoring_weights']
        
        # 否則，構建權重字典
        weights = {
            'valuation': profile.get('weight_valuation', self.default_weights['valuation']),
            'profitability': profile.get('weight_profitability', self.default_weights['profitability']),
            'financial_health': profile.get('weight_financial_health', self.default_weights['financial_health']),
            'growth': profile.get('weight_growth', self.default_weights['growth']),
            'cash_flow': profile.get('weight_cash_flow', self.default_weights['cash_flow'])
        }
        
        # 驗證權重總和為 1.0
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"⚠️ {stock_type} 的權重總和為 {total:.2f}，應該為 1.0")
            # 正規化
            for key in weights:
                weights[key] = weights[key] / total
        
        logger.info(f"✅ 為 {stock_type} 應用權重：{weights}")
        
        return weights
    
    def get_weight_description(self, stock_type: str) -> str:
        """
        獲取權重說明
        
        Returns:
            權重的文字說明
        """
        weights = self.get_weights(stock_type)
        
        descriptions = {
            'growth': (
                "成長股權重配置（追求資本增值）：\n"
                f"  • 估值指標：{weights['valuation']*100:.0f}% (↓ 允許高 P/E)\n"
                f"  • 獲利能力：{weights['profitability']*100:.0f}%\n"
                f"  • 財務健康：{weights['financial_health']*100:.0f}%\n"
                f"  • 成長能力：{weights['growth']*100:.0f}% (↑ 最重要)\n"
                f"  • 現金流：{weights['cash_flow']*100:.0f}%"
            ),
            'value': (
                "價值股權重配置（平衡成長與估值）：\n"
                f"  • 估值指標：{weights['valuation']*100:.0f}%\n"
                f"  • 獲利能力：{weights['profitability']*100:.0f}%\n"
                f"  • 財務健康：{weights['financial_health']*100:.0f}%\n"
                f"  • 成長能力：{weights['growth']*100:.0f}%\n"
                f"  • 現金流：{weights['cash_flow']*100:.0f}%"
            ),
            'defensive': (
                "防守股權重配置（追求穩定現金流）：\n"
                f"  • 估值指標：{weights['valuation']*100:.0f}%\n"
                f"  • 獲利能力：{weights['profitability']*100:.0f}%\n"
                f"  • 財務健康：{weights['financial_health']*100:.0f}% (↑ 最重要)\n"
                f"  • 成長能力：{weights['growth']*100:.0f}% (↓ 不追求)\n"
                f"  • 現金流：{weights['cash_flow']*100:.0f}% (↑ 股息重要)"
            ),
            'etf': (
                "ETF 權重配置（指數基金）：\n"
                f"  • 估值指標：{weights['valuation']*100:.0f}%\n"
                f"  • 獲利能力：{weights['profitability']*100:.0f}%\n"
                f"  • 財務健康：{weights['financial_health']*100:.0f}%\n"
                f"  • 成長能力：{weights['growth']*100:.0f}%\n"
                f"  • 現金流：{weights['cash_flow']*100:.0f}%"
            )
        }
        
        return descriptions.get(stock_type, "未知類型")


# ==========================================
# 測試函數
# ==========================================

def test_classifier():
    """測試分類器"""
    
    print("\n" + "="*80)
    print("🧪 股票分類器測試")
    print("="*80 + "\n")
    
    # 初始化分類器（不需要配置，使用預設值）
    classifier = StockClassifier()
    weight_manager = WeightManager({
        'fundamental_analysis': {
            'stock_profiles': {
                'growth': {
                    'weight_valuation': 0.15,
                    'weight_profitability': 0.30,
                    'weight_financial_health': 0.15,
                    'weight_growth': 0.35,
                    'weight_cash_flow': 0.05
                },
                'value': {
                    'weight_valuation': 0.35,
                    'weight_profitability': 0.25,
                    'weight_financial_health': 0.20,
                    'weight_growth': 0.15,
                    'weight_cash_flow': 0.05
                },
                'defensive': {
                    'weight_valuation': 0.20,
                    'weight_profitability': 0.30,
                    'weight_financial_health': 0.30,
                    'weight_growth': 0.10,
                    'weight_cash_flow': 0.10
                },
                'etf': {
                    'weight_valuation': 0.30,
                    'weight_profitability': 0.25,
                    'weight_financial_health': 0.20,
                    'weight_growth': 0.20,
                    'weight_cash_flow': 0.05
                }
            }
        }
    })
    
    # 測試數據
    test_cases = [
        {
            'code': 'NVDA',
            'pe': 199.9,
            'eps_growth': 0.35,
            'div_yield': 0.0005,
            'div_per_share': 0.04,
            'market': 'US'
        },
        {
            'code': '2330',
            'pe': 16.05,
            'eps_growth': 0.15,
            'div_yield': 0.0257,
            'div_per_share': 3.5,
            'market': 'TW'
        },
        {
            'code': '2412',
            'pe': 21.65,
            'eps_growth': 0.08,
            'div_yield': 0.012,
            'div_per_share': 8.5,
            'market': 'TW'
        },
        {
            'code': '0050',
            'pe': 14.99,
            'eps_growth': 0.05,
            'div_yield': 0.024,
            'div_per_share': 4.5,
            'market': 'TW'
        }
    ]
    
    results = {}
    
    for test in test_cases:
        print(f"📊 分類 {test['code']}...")
        print("─" * 80)
        
        stock_type = classifier.classify(
            stock_code=test['code'],
            pe_ratio=test['pe'],
            eps_growth=test['eps_growth'],
            dividend_yield=test['div_yield'],
            dividend_per_share=test['div_per_share'],
            market=test['market']
        )
        
        print(f"✅ 分類結果：{stock_type.upper()}\n")
        
        # 打印分類原因
        reason = classifier.get_classification_reason(
            test['code'],
            stock_type,
            test['pe'],
            test['eps_growth'],
            test['div_yield']
        )
        print(reason)
        print()
        
        # 打印權重
        weight_desc = weight_manager.get_weight_description(stock_type)
        print(weight_desc)
        print("\n")
        
        results[test['code']] = {
            'type': stock_type,
            'weights': weight_manager.get_weights(stock_type)
        }
    
    print("="*80)
    print("✅ 分類測試完成！")
    print("="*80 + "\n")
    
    return results


# ==========================================
# 主函數
# ==========================================

def main():
    """主函數"""
    test_classifier()


if __name__ == "__main__":
    main()

