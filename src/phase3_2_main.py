"""
🚀 Phase 3.2 - 概率風險評估完整執行流程

執行步驟：
1. 讀取基本面分析結果
2. 執行蒙特卡洛模擬
3. 生成風險指標（VaR、CVaR、Max Drawdown）
4. 生成 Markdown 報告和 CSV 對照表
5. 保存到 outputs/ 資料夾

使用方式：
  python3 src/phase3_2_main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import logging
from datetime import datetime

from src.config_loader import ConfigLoader
from src.stock_classifier import StockClassifier, WeightManager
from src.fundamental_analysis import (
    analyze_fundamental, load_fundamental_config, setup_logging as fund_setup_logging
)
from src.probability_analysis import ProbabilityAnalyzer
from src.report_generator import ReportGenerator

# ==========================================
# 日誌設置
# ==========================================

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# ==========================================
# 主執行函數
# ==========================================

def run_phase_3_2():
    """執行 Phase 3.2 - 概率風險評估"""
    
    print("\n" + "="*80)
    print("🚀 Phase 3.2 - 概率風險評估（Probability Analysis）")
    print("="*80 + "\n")
    
    try:
        # ========== 步驟 1：讀取配置和初始化 ==========
        logger.info("📖 讀取配置並初始化模組...")
        
        fund_config, _ = load_fundamental_config()
        classifier = StockClassifier(fund_config)
        weight_manager = WeightManager(fund_config)
        analyzer = ProbabilityAnalyzer(fund_config)
        report_gen = ReportGenerator()
        
        # ========== 步驟 2：定義測試股票 ==========
        logger.info("📊 定義測試股票...")
        
        sample_stocks = {
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
        
        # ========== 步驟 3：執行基本面分析 ==========
        logger.info("\n📈 執行基本面分析...\n")
        
        fundamental_results = {}
        
        for stock_code, data in sample_stocks.items():
            result = analyze_fundamental(
                stock_code, data, fund_config,
                classifier=classifier,
                weight_manager=weight_manager
            )
            fundamental_results[stock_code] = result
        
        # ========== 步驟 4：執行蒙特卡洛模擬 ==========
        logger.info("\n🎲 執行蒙特卡洛模擬和風險分析...\n")
        
        probability_results = {}
        
        for stock_code, fund_result in fundamental_results.items():
            prob_result = analyzer.analyze(
                stock_code=stock_code,
                current_price=fund_result.get('metrics', {}).get('current_price', 
                                                                  sample_stocks[stock_code]['Close']),
                fundamental_score=fund_result.get('score', 50)
            )
            probability_results[stock_code] = prob_result
        
        # ========== 步驟 5：生成報告 ==========
        logger.info("\n📝 生成報告...\n")
        
        # 生成 Markdown 報告
        markdown_report = report_gen.generate_probability_report(probability_results)
        
        # 生成 CSV 對照表
        csv_table = report_gen.generate_target_price_table(probability_results)
        
        # ========== 步驟 6：保存檔案 ==========
        logger.info("\n💾 保存檔案到 outputs/...\n")
        
        output_dir = Path('outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 Markdown 報告
        markdown_path = output_dir / 'Phase3.2_概率風險分析報告.md'
        report_gen.save_report(markdown_report, str(markdown_path))
        
        # 保存 CSV 對照表
        csv_path = output_dir / 'Phase3.2_三情景目標價對照表.csv'
        report_gen.save_csv_table(csv_table, str(csv_path))
        
        # ========== 步驟 7：打印摘要 ==========
        logger.info("\n" + "="*80)
        logger.info("✅ Phase 3.2 完成！")
        logger.info("="*80 + "\n")
        
        print("\n📊 概率分析結果摘要：\n")
        
        for code, result in probability_results.items():
            if 'error' in result:
                continue
            
            score = result['fundamental_score']
            current = result['current_price']
            base_target = result['target_prices']['base']
            bullish = result['target_prices']['bullish']
            bearish = result['target_prices']['bearish']
            var_pct = result['risk_metrics']['var_95_return'] * 100
            max_dd = result['risk_metrics']['max_drawdown'] * 100
            
            print(f"📈 {code}")
            print(f"   基本面評分：{score:.1f}")
            print(f"   當前股價：${current:.2f}")
            print(f"   基準目標：${base_target:.2f} ({(base_target/current-1)*100:+.1f}%)")
            print(f"   牛市目標：${bullish:.2f}")
            print(f"   熊市目標：${bearish:.2f}")
            print(f"   VaR (95%)：{var_pct:.2f}%")
            print(f"   最大回撤：{max_dd:.2f}%")
            print()
        
        print("="*80)
        print(f"✅ Markdown 報告已保存到：{markdown_path}")
        print(f"✅ CSV 對照表已保存到：{csv_path}")
        print("="*80 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("❌ 任務被用戶中止")
        return 130
    except Exception as e:
        logger.error(f"❌ 任務執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_phase_3_2())

