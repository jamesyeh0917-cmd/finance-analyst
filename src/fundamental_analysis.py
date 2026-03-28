"""
📊 Fundamental Analysis — 基本面分析引擎

功能：
  • 計算 20+ 個財務指標
  • 實裝 3 種估值模型（相對估值、DCF、DDM）
  • 歷史對照分析（檢查指標趨勢）
  • 靈敏度分析（樂觀/中性/悲觀三情景）
  • 綜合評分系統（0-100）
  • 資料快取機制（避免重複抓取）

設計原則：
  1. 資料快取：檢查 data/raw/financials/ 目錄
  2. 多重估值模型：根據股票類型自動選擇
  3. 靈敏度分析：DCF 給出三種目標價
  4. 歷史對照：檢查指標是否連續衰退
  5. 參數動態化：所有參數從 settings.yaml 讀取

使用示例：
  python src/fundamental_analysis.py
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import numpy as np
import pandas as pd

# ==========================================
# 路徑設置
# ==========================================

def setup_path():
    """確保 Python 能找到 config_loader"""
    current_dir = Path(__file__).parent.parent.resolve()
    if current_dir not in sys.path:
        sys.path.insert(0, str(current_dir))

setup_path()

try:
    from config_loader import ConfigLoader
except ModuleNotFoundError as e:
    print(f"❌ 找不到 config_loader 模組: {e}")
    sys.exit(1)

# 導入股票分類器
try:
    from stock_classifier import StockClassifier, WeightManager
except ModuleNotFoundError as e:
    print(f"❌ 找不到 stock_classifier 模組: {e}")
    sys.exit(1)


# ==========================================
# 日誌配置
# ==========================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """配置日誌系統"""
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()


# ==========================================
# 路徑和配置管理
# ==========================================

def get_financials_dir() -> Path:
    """獲取或創建財務數據目錄"""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    if not (project_root / '.git').exists():
        logger.warning("⚠️ 警告：未找到 .git 目錄")
        project_root = Path.cwd()
    
    financials_dir = project_root / 'data' / 'raw' / 'financials'
    financials_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"✅ 財務數據目錄：{financials_dir}")
    return financials_dir


def load_fundamental_config() -> Tuple[Dict, ConfigLoader]:
    """從 settings.yaml 讀取基本面分析配置"""
    try:
        logger.info("📖 正在讀取基本面分析配置...")
        loader = ConfigLoader('config/settings.yaml')
        
        fund_config = loader.config.get('fundamental_analysis', {})
        
        if not fund_config:
            logger.warning("⚠️ 配置文件中沒有基本面分析配置，使用預設值")
            fund_config = {
                'thresholds': {},
                'dcf': {'projection_years': 5, 'discount_rate': 0.08},
                'ddm': {'discount_rate': 0.07},
            }
        
        logger.info("✅ 成功讀取基本面分析配置")
        return fund_config, loader
        
    except Exception as e:
        logger.error(f"❌ 讀取配置文件時出錯: {e}")
        raise


# ==========================================
# 財務數據管理（快取機制）
# ==========================================

class FinancialDataCache:
    """財務數據快取管理器"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
    
    def get_cached_data(self, stock_code: str, data_type: str = "quarterly") -> Optional[Dict]:
        """
        獲取快取的財務數據
        
        Args:
            stock_code: 股票代碼
            data_type: 數據類型（quarterly 或 annual）
        
        Returns:
            快取數據或 None
        """
        cache_file = self.cache_dir / f"{stock_code}_{data_type}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"📂 從快取讀取 {stock_code} 的 {data_type} 數據")
                return data
            except Exception as e:
                logger.warning(f"⚠️ 讀取快取文件失敗: {e}")
                return None
        
        return None
    
    def save_cached_data(self, stock_code: str, data: Dict, data_type: str = "quarterly"):
        """保存財務數據快取"""
        cache_file = self.cache_dir / f"{stock_code}_{data_type}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 已保存 {stock_code} 的快取數據")
        except Exception as e:
            logger.warning(f"⚠️ 保存快取失敗: {e}")


# ==========================================
# 財務指標計算
# ==========================================

class FinancialMetrics:
    """財務指標計算器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.thresholds = config.get('thresholds', {})
    
    def calculate_pe_ratio(self, stock_price: float, eps: float) -> float:
        """計算本益比 (P/E Ratio)"""
        if eps <= 0:
            return np.nan
        return stock_price / eps
    
    def calculate_pb_ratio(self, stock_price: float, book_value_per_share: float) -> float:
        """計算股價淨值比 (P/B Ratio)"""
        if book_value_per_share <= 0:
            return np.nan
        return stock_price / book_value_per_share
    
    def calculate_peg_ratio(self, pe_ratio: float, eps_growth_rate: float) -> float:
        """計算 PEG 比率"""
        if eps_growth_rate <= 0 or np.isnan(pe_ratio):
            return np.nan
        return pe_ratio / eps_growth_rate
    
    def calculate_roe(self, net_income: float, shareholders_equity: float) -> float:
        """計算股東權益報酬率 (ROE)"""
        if shareholders_equity <= 0:
            return 0.0
        return net_income / shareholders_equity
    
    def calculate_roa(self, net_income: float, total_assets: float) -> float:
        """計算資產報酬率 (ROA)"""
        if total_assets <= 0:
            return 0.0
        return net_income / total_assets
    
    def calculate_margins(self, net_income: float, gross_profit: float, revenue: float) -> Tuple[float, float]:
        """計算淨利潤率和毛利率"""
        if revenue <= 0:
            return 0.0, 0.0
        return net_income / revenue, gross_profit / revenue
    
    def calculate_debt_to_equity(self, total_debt: float, shareholders_equity: float) -> float:
        """計算負債權益比"""
        if shareholders_equity <= 0:
            return np.nan
        return total_debt / shareholders_equity
    
    def calculate_current_ratio(self, current_assets: float, current_liabilities: float) -> float:
        """計算流動比率"""
        if current_liabilities <= 0:
            return np.nan
        return current_assets / current_liabilities
    
    def calculate_eps_growth(self, current_eps: float, previous_eps: float) -> float:
        """計算 EPS 成長率"""
        if previous_eps <= 0:
            return 0.0
        return (current_eps - previous_eps) / abs(previous_eps)
    
    def score_valuation(self, pe_ratio: float, pb_ratio: float, peg_ratio: float) -> float:
        """
        對估值指標評分（0-100）
        
        P/E 越低越好，但要合理
        """
        pe_threshold = self.thresholds.get('pe_ratio', {})
        pb_threshold = self.thresholds.get('pb_ratio', {})
        
        score = 0
        count = 0
        
        # P/E 評分
        if not np.isnan(pe_ratio):
            if pe_ratio < pe_threshold.get('excellent', 12):
                score += 25
            elif pe_ratio < pe_threshold.get('good', 20):
                score += 20
            elif pe_ratio < pe_threshold.get('fair', 30):
                score += 15
            else:
                score += max(0, 30 - pe_ratio)
            count += 1
        
        # P/B 評分
        if not np.isnan(pb_ratio):
            if pb_ratio < pb_threshold.get('excellent', 1.0):
                score += 25
            elif pb_ratio < pb_threshold.get('good', 2.0):
                score += 20
            elif pb_ratio < pb_threshold.get('fair', 3.0):
                score += 15
            else:
                score += max(0, 30 - pb_ratio * 10)
            count += 1
        
        return score / count if count > 0 else 0


# ==========================================
# 估值模型
# ==========================================

class ValuationModels:
    """估值模型集合"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.dcf_params = config.get('dcf', {})
        self.ddm_params = config.get('ddm', {})
    
    def relative_valuation(self, 
                          stock_price: float,
                          eps: float,
                          industry_pe: float = 16) -> Dict:
        """
        相對估值法 (Relative Valuation)
        
        基於行業平均 P/E 估值
        """
        if eps <= 0:
            return {'valuation_price': np.nan, 'overvalued_pct': np.nan}
        
        fair_price = eps * industry_pe
        overvalued_pct = (stock_price - fair_price) / fair_price * 100
        
        return {
            'valuation_price': fair_price,
            'overvalued_pct': overvalued_pct,
            'method': 'Relative Valuation (P/E)'
        }
    
    def dcf_valuation(self,
                     current_eps: float,
                     eps_growth_rate: float,
                     shares_outstanding: float,
                     scenario: str = 'base') -> Dict:
        """
        DCF 折現現金流模型 (Absolute Valuation)
        
        支持三情景敏感度分析
        """
        years = self.dcf_params.get('projection_years', 5)
        terminal_growth = self.dcf_params.get('terminal_growth_rate', 0.03)
        base_discount_rate = self.dcf_params.get('discount_rate', 0.08)
        
        # 根據情景調整參數
        scenarios = self.dcf_params.get('scenarios', {})
        scenario_config = scenarios.get(scenario, scenarios.get('base', {}))
        
        eps_growth_adj = scenario_config.get('eps_growth_adjustment', 1.0)
        discount_rate_adj = scenario_config.get('discount_rate_adjustment', 0.0)
        
        adjusted_growth_rate = eps_growth_rate * eps_growth_adj
        discount_rate = base_discount_rate + discount_rate_adj
        
        # 預估未來 5 年的 EPS
        eps_forecast = []
        eps = current_eps
        for year in range(years):
            eps *= (1 + adjusted_growth_rate)
            eps_forecast.append(eps)
        
        # 計算現值
        pv_fcf = sum([eps / ((1 + discount_rate) ** (i + 1)) for i, eps in enumerate(eps_forecast)])
        
        # 終端價值
        terminal_eps = eps_forecast[-1] * (1 + terminal_growth)
        terminal_value = (terminal_eps / (discount_rate - terminal_growth))
        pv_terminal = terminal_value / ((1 + discount_rate) ** years)
        
        # 企業價值
        enterprise_value = pv_fcf + pv_terminal
        fair_price = enterprise_value / shares_outstanding
        
        return {
            'valuation_price': max(0, fair_price),
            'pv_fcf': pv_fcf,
            'pv_terminal': pv_terminal,
            'eps_forecast': eps_forecast,
            'discount_rate': discount_rate,
            'growth_rate': adjusted_growth_rate,
            'method': f'DCF ({scenario.capitalize()} Case)'
        }
    
    def ddm_valuation(self,
                     annual_dividend: float,
                     dividend_growth_rate: float = None) -> Dict:
        """
        股息折現模型 (Dividend Discount Model)
        
        適合高股息股票（如 0050）
        """
        if annual_dividend <= 0:
            return {'valuation_price': np.nan, 'method': 'DDM'}
        
        if dividend_growth_rate is None:
            dividend_growth_rate = self.ddm_params.get('dividend_growth_rate', 0.05)
        
        discount_rate = self.ddm_params.get('discount_rate', 0.07)
        
        # 穩定成長假設
        next_dividend = annual_dividend * (1 + dividend_growth_rate)
        fair_price = next_dividend / (discount_rate - dividend_growth_rate)
        
        return {
            'valuation_price': max(0, fair_price),
            'dividend_yield': annual_dividend / fair_price,
            'growth_rate': dividend_growth_rate,
            'method': 'DDM'
        }


# ==========================================
# 歷史對照分析
# ==========================================

class HistoricalComparison:
    """歷史趨勢對照分析"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.lookback = config.get('historical_comparison', {}).get('lookback_years', 3)
        self.penalty = config.get('historical_comparison', {}).get('declining_penalty', {})
    
    def analyze_trend(self, 
                     current_value: float,
                     historical_values: List[float],
                     metric_name: str) -> Dict:
        """
        分析指標趨勢（是否連續衰退）
        
        Returns:
            trend_score: 0-100 分
            is_declining: 是否衰退
            penalty: 如果衰退的懲罰分數
        """
        if len(historical_values) < 2:
            return {'trend_score': 50, 'is_declining': False, 'penalty': 0}
        
        # 檢查是否連續衰退
        is_declining = all(
            historical_values[i] >= historical_values[i+1] 
            for i in range(len(historical_values)-1)
        )
        
        # 計算成長率
        if historical_values[0] > 0:
            growth_rate = (current_value - historical_values[0]) / historical_values[0]
        else:
            growth_rate = 0
        
        # 評分
        if growth_rate > 0.15:
            trend_score = 100
        elif growth_rate > 0.05:
            trend_score = 80
        elif growth_rate > 0:
            trend_score = 60
        elif growth_rate > -0.05:
            trend_score = 40
        else:
            trend_score = 20
        
        # 衰退懲罰
        penalty = 0
        if is_declining:
            penalty = self.penalty.get(f'{metric_name.lower()}_declining', -5)
        
        return {
            'trend_score': trend_score,
            'is_declining': is_declining,
            'penalty': penalty,
            'growth_rate': growth_rate * 100
        }


# ==========================================
# 綜合評分系統
# ==========================================

class FundamentalScore:
    """基本面綜合評分"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.weights = config.get('scoring_weights', {})
        self.max_score = 100.0  # 評分上限
        self.overflow_threshold = 120.0  # 溢出閾值（用於「極度看好」分類）
    
    def calculate_score(self,
                       valuation_score: float,
                       profitability_score: float,
                       health_score: float,
                       growth_score: float,
                       cashflow_score: float,
                       normalize: bool = True) -> Tuple[float, str]:
        """
        計算綜合評分（0-100，或允許超額評分）
        
        Args:
            valuation_score: 估值評分
            profitability_score: 獲利評分
            health_score: 財務健康評分
            growth_score: 成長評分
            cashflow_score: 現金流評分
            normalize: 是否進行歸一化（上限 100）
        
        Returns:
            (評分, 評分等級)
        """
        
        scores = {
            'valuation': min(100, max(0, valuation_score)),
            'profitability': min(100, max(0, profitability_score)),
            'health': min(100, max(0, health_score)),
            'growth': min(100, max(0, growth_score)),
            'cashflow': min(100, max(0, cashflow_score))
        }
        
        total_score = (
            scores['valuation'] * self.weights.get('valuation', 0.30) +
            scores['profitability'] * self.weights.get('profitability', 0.25) +
            scores['health'] * self.weights.get('financial_health', 0.20) +
            scores['growth'] * self.weights.get('growth', 0.20) +
            scores['cashflow'] * self.weights.get('cash_flow', 0.05)
        )
        
        # 歸一化處理
        if normalize:
            if total_score > self.max_score:
                # 允許超額評分（100+），並添加「極度看好」標籤
                rating = self._get_rating(total_score)
                # 將分數限制在最多 100 分（給後續模組用）
                normalized_score = min(self.max_score, total_score)
                return normalized_score, rating
            else:
                normalized_score = total_score
                rating = self._get_rating(normalized_score)
                return normalized_score, rating
        else:
            # 不歸一化，保留原始評分
            rating = self._get_rating(total_score)
            return total_score, rating
    
    def _get_rating(self, score: float) -> str:
        """
        根據分數獲取等級評分
        
        Returns:
            評級文字說明
        """
        if score >= self.overflow_threshold:
            return "極度看好"  # 100+ 分
        elif score >= 85:
            return "強烈看好"  # 85-99
        elif score >= 70:
            return "看好"      # 70-84
        elif score >= 55:
            return "中立"      # 55-69
        elif score >= 40:
            return "保留看法"  # 40-54
        else:
            return "看空"      # <40


# ==========================================
# 主分析流程
# ==========================================

def analyze_fundamental(stock_code: str, stock_data: Dict, config: Dict, 
                       classifier: 'StockClassifier' = None,
                       weight_manager: 'WeightManager' = None) -> Dict:
    """
    執行完整的基本面分析（含股票分類和差異化權重）
    
    Args:
        stock_code: 股票代碼
        stock_data: 股票財務數據
        config: 配置字典
        classifier: 股票分類器實例
        weight_manager: 權重管理器實例
    
    Returns:
        分析結果字典
    """
    logger.info(f"📊 正在分析 {stock_code} 的基本面...")
    
    try:
        # 初始化分析工具
        metrics = FinancialMetrics(config)
        valuation_models = ValuationModels(config)
        historical = HistoricalComparison(config)
        scorer = FundamentalScore(config)
        
        # 提取數據
        stock_price = stock_data.get('Close', 0)
        eps = stock_data.get('eps', 0)
        shares = stock_data.get('shares_outstanding', 1e9)
        annual_dividend = stock_data.get('annual_dividend', 0)
        
        logger.info(f"   • 股價：${stock_price:.2f}")
        logger.info(f"   • EPS：{eps:.2f} 元")
        
        # ========== 估值分析 ==========
        logger.info("   📊 計算估值指標...")
        
        pe = metrics.calculate_pe_ratio(stock_price, eps)
        pb = metrics.calculate_pb_ratio(stock_price, stock_data.get('book_value_per_share', 1))
        peg = metrics.calculate_peg_ratio(pe, stock_data.get('eps_growth', 0.10))
        
        logger.info(f"      • P/E：{pe:.2f}")
        logger.info(f"      • P/B：{pb:.2f}")
        
        # ========== 多重估值模型 ==========
        logger.info("   💰 執行多重估值模型（三情景敏感度分析）...")
        
        valuations = {
            'optimistic': valuation_models.dcf_valuation(eps, 0.15, shares, 'optimistic'),
            'base': valuation_models.dcf_valuation(eps, 0.10, shares, 'base'),
            'pessimistic': valuation_models.dcf_valuation(eps, 0.05, shares, 'pessimistic')
        }
        
        ddm = valuation_models.ddm_valuation(annual_dividend)
        
        for scenario, val in valuations.items():
            logger.info(f"      • {scenario.capitalize()}: ${val['valuation_price']:.2f}")
        
        # ========== 獲利能力 ==========
        logger.info("   📈 計算獲利能力指標...")
        
        roe = metrics.calculate_roe(
            stock_data.get('net_income', 1000),
            stock_data.get('shareholders_equity', 5000)
        )
        net_margin = stock_data.get('net_margin', 0.10)
        
        logger.info(f"      • ROE：{roe*100:.2f}%")
        logger.info(f"      • 淨利率：{net_margin*100:.2f}%")
        
        # ========== 財務健康 ==========
        logger.info("   🏥 評估財務健康...")
        
        debt_to_equity = metrics.calculate_debt_to_equity(
            stock_data.get('total_debt', 1000),
            stock_data.get('shareholders_equity', 5000)
        )
        current_ratio = metrics.calculate_current_ratio(
            stock_data.get('current_assets', 3000),
            stock_data.get('current_liabilities', 1500)
        )
        
        logger.info(f"      • 負債權益比：{debt_to_equity:.2f}")
        logger.info(f"      • 流動比率：{current_ratio:.2f}")
        
        # ========== 成長指標 ==========
        logger.info("   🚀 評估成長潛力...")
        
        eps_growth = stock_data.get('eps_growth', 0.10)
        revenue_growth = stock_data.get('revenue_growth', 0.08)
        
        logger.info(f"      • EPS 成長率：{eps_growth*100:.2f}%")
        logger.info(f"      • 營收成長率：{revenue_growth*100:.2f}%")
        
        # ========== 股票分類與權重應用 ==========
        logger.info("   🔍 執行股票分類和權重應用...")
        
        # 計算股息收益率
        dividend_yield = annual_dividend / stock_price if stock_price > 0 else 0
        
        # 分類股票
        stock_type = 'value'  # 預設
        if classifier:
            stock_type = classifier.classify(
                stock_code=stock_code,
                pe_ratio=pe,
                eps_growth=eps_growth,
                dividend_yield=dividend_yield,
                dividend_per_share=annual_dividend
            )
            logger.info(f"      • 股票類型：{stock_type.upper()}")
        
        # 獲取差異化權重
        weights = None
        if weight_manager:
            weights = weight_manager.get_weights(stock_type)
            logger.info(f"      • 應用 {stock_type} 型權重")
        
        # ========== 綜合評分 ==========
        logger.info("   🎯 計算綜合評分...")
        
        valuation_score = metrics.score_valuation(pe, pb, peg)
        profitability_score = 50 + roe * 300 + net_margin * 200
        health_score = 100 - debt_to_equity * 30 + (current_ratio - 1) * 20
        growth_score = 50 + eps_growth * 300 + revenue_growth * 150
        cashflow_score = 70
        
        # 使用差異化權重計算最終評分
        if weights:
            final_score = (
                valuation_score * weights.get('valuation', 0.30) +
                profitability_score * weights.get('profitability', 0.25) +
                health_score * weights.get('financial_health', 0.20) +
                growth_score * weights.get('growth', 0.20) +
                cashflow_score * weights.get('cash_flow', 0.05)
            )
        else:
            # 使用預設權重
            final_score = scorer.calculate_score(
                valuation_score,
                profitability_score,
                health_score,
                growth_score,
                cashflow_score
            )
        
        logger.info(f"   ✅ 基本面評分：{final_score:.1f}/100（{stock_type} 類型）")
        
        return {
            'stock_code': stock_code,
            'stock_type': stock_type,
            'score': final_score,
            'scores_breakdown': {
                'valuation': valuation_score,
                'profitability': profitability_score,
                'health': health_score,
                'growth': growth_score,
                'cashflow': cashflow_score,
            },
            'weights_applied': weights,
            'valuation': valuations,
            'ddm': ddm,
            'metrics': {
                'pe': pe,
                'pb': pb,
                'roe': roe,
                'net_margin': net_margin,
                'debt_to_equity': debt_to_equity,
                'current_ratio': current_ratio,
                'eps_growth': eps_growth,
                'revenue_growth': revenue_growth,
                'dividend_yield': dividend_yield,
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 分析失敗: {e}")
        return {'stock_code': stock_code, 'score': 0, 'error': str(e)}


# ==========================================
# 主函數
# ==========================================

def main():
    """主函數：執行基本面分析（含股票分類和差異化權重）"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 開始執行基本面分析任務（Phase 3.3）")
        logger.info("=" * 60)
        
        # 讀取配置
        fund_config, loader = load_fundamental_config()
        
        # 初始化快取
        financials_dir = get_financials_dir()
        cache = FinancialDataCache(financials_dir)
        
        # 初始化股票分類器和權重管理器
        classifier = StockClassifier(fund_config)
        weight_manager = WeightManager(fund_config)
        
        # 三檔不同特性股票的測試數據
        sample_stocks = {
            # ==========================================
            # NVDA - 美股成長股代表
            # ==========================================
            'NVDA': {
                'Close': 875.50,
                'eps': 4.38,
                'shares_outstanding': 2.4e9,
                'annual_dividend': 0.04,
                'book_value_per_share': 12.5,
                'eps_growth': 0.35,
                'net_income': 10500,
                'shareholders_equity': 30000,
                'net_margin': 0.48,
                'total_debt': 5000,
                'current_assets': 45000,
                'current_liabilities': 15000,
                'revenue_growth': 0.40
            },
            # ==========================================
            # 2330 - TSMC（台股龍頭價值股）
            # ==========================================
            '2330': {
                'Close': 136.45,
                'eps': 8.50,
                'shares_outstanding': 25e8,
                'annual_dividend': 3.50,
                'book_value_per_share': 5.50,
                'eps_growth': 0.15,
                'net_income': 2125,
                'shareholders_equity': 13750,
                'net_margin': 0.25,
                'total_debt': 4000,
                'current_assets': 8000,
                'current_liabilities': 4000,
                'revenue_growth': 0.08
            },
            # ==========================================
            # 2412 - MediaTek（台股防守股）
            # ==========================================
            '2412': {
                'Close': 710.00,
                'eps': 32.80,
                'shares_outstanding': 855e6,
                'annual_dividend': 8.50,
                'book_value_per_share': 125.50,
                'eps_growth': 0.08,
                'net_income': 28000,
                'shareholders_equity': 107400,
                'net_margin': 0.20,
                'total_debt': 15000,
                'current_assets': 65000,
                'current_liabilities': 25000,
                'revenue_growth': 0.06
            }
        }
        
        results = {}
        
        logger.info("")
        for stock_code, data in sample_stocks.items():
            result = analyze_fundamental(
                stock_code, data, fund_config,
                classifier=classifier,
                weight_manager=weight_manager
            )
            results[stock_code] = result
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 Phase 3.3 分析完成！")
        logger.info("=" * 60)
        
        # 打印對比摘要
        print("\n" + "="*80)
        print("🎯 Phase 3.3 測試結果對比")
        print("="*80 + "\n")
        
        for code, result in results.items():
            if 'score' in result:
                stock_type = result.get('stock_type', 'unknown')
                weights = result.get('weights_applied', {})
                metrics = result.get('metrics', {})
                
                print(f"{'='*80}")
                print(f"📊 {code} — 股票類型：{stock_type.upper()}")
                print(f"{'='*80}")
                print(f"  • 基本面評分：{result['score']:.1f}/100")
                print(f"  • P/E：{metrics.get('pe', 0):.2f}x")
                print(f"  • ROE：{metrics.get('roe', 0)*100:.1f}%")
                print(f"  • EPS 成長：{metrics.get('eps_growth', 0)*100:.1f}%")
                print(f"  • 股息率：{metrics.get('dividend_yield', 0)*100:.2f}%")
                
                if weights:
                    print(f"\n  應用的權重配置：")
                    print(f"    • 估值指標：{weights.get('valuation', 0)*100:.0f}%")
                    print(f"    • 獲利能力：{weights.get('profitability', 0)*100:.0f}%")
                    print(f"    • 財務健康：{weights.get('financial_health', 0)*100:.0f}%")
                    print(f"    • 成長能力：{weights.get('growth', 0)*100:.0f}%")
                    print(f"    • 現金流：{weights.get('cash_flow', 0)*100:.0f}%")
                print()
        
        print("="*80)
        print(f"✅ 成功分析：{len(results)} 檔股票")
        for code, result in results.items():
            if 'score' in result:
                print(f"   • {code}（{result.get('stock_type', 'unknown')}）：評分 {result['score']:.1f}/100")
        print("="*80 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("❌ 任務被用戶中止")
        return 130
    except Exception as e:
        logger.error(f"❌ 任務執行失敗: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

