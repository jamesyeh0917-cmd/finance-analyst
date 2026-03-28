"""
📊 Probability Analysis — 概率風險評估模組 (Phase 3.2)

功能：
  • 蒙特卡洛模擬（10,000 種股價走勢）
  • VaR (Value at Risk) 計算 @ 95% 信心水準
  • 最大回撤分析 (Max Drawdown)
  • 基本面評分連動（高分 → 高成長，低分 → 高風險）
  • 三情景目標價（樂觀/基準/悲觀）
  • Markdown 報告生成
"""

import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime
from pathlib import Path
import logging

# ==========================================
# 日誌配置
# ==========================================

logger = logging.getLogger(__name__)


# ==========================================
# 蒙特卡洛模擬器
# ==========================================

class MonteCarloSimulator:
    """
    蒙特卡洛模擬器
    使用幾何布朗運動 (GBM) 模擬股價走勢
    """
    
    def __init__(self, n_simulations: int = 10000, n_days: int = 252):
        self.n_simulations = n_simulations
        self.n_days = n_days
        self.dt = 1.0 / n_days
    
    def simulate(self, 
                initial_price: float,
                annual_return: float,
                volatility: float,
                random_seed: int = 42) -> np.ndarray:
        """
        執行蒙特卡洛模擬（向量化）
        
        使用幾何布朗運動：dS = μ*S*dt + σ*S*dW
        其中 μ 是年化回報率，σ 是年化波動率
        
        Returns:
            形狀為 (n_simulations, n_days) 的股價陣列
        """
        np.random.seed(random_seed)
        
        # 初始化路徑陣列
        paths = np.zeros((self.n_simulations, self.n_days + 1))
        paths[:, 0] = initial_price
        
        # 計算每日漂移和波動率
        # 使用年化回報率和波動率，轉換為每日
        daily_drift = annual_return * self.dt
        daily_vol_sqrt_dt = volatility * np.sqrt(self.dt)
        
        # 生成隨機數（向量化）
        random_numbers = np.random.standard_normal((self.n_simulations, self.n_days))
        
        # 計算所有路徑
        # S_{t+1} = S_t * exp((μ - σ²/2)*dt + σ*sqrt(dt)*Z)
        for day in range(self.n_days):
            # 漂移項：(μ - σ²/2)*dt
            drift_component = (annual_return - 0.5 * volatility ** 2) * self.dt
            # 隨機項：σ*sqrt(dt)*Z
            diffusion_component = daily_vol_sqrt_dt * random_numbers[:, day]
            
            paths[:, day + 1] = paths[:, day] * np.exp(
                drift_component + diffusion_component
            )
        
        return paths
    
    def calculate_metrics(self, 
                         price_paths: np.ndarray,
                         initial_price: float) -> Dict:
        """計算蒙特卡洛結果的風險指標"""
        
        final_prices = price_paths[:, -1]
        returns = (final_prices - initial_price) / initial_price
        
        # 基本統計
        expected_price = np.median(final_prices)
        opt_price = np.percentile(final_prices, 75)
        base_price = np.percentile(final_prices, 50)
        pess_price = np.percentile(final_prices, 25)
        
        # VaR @ 95%
        var_price = np.percentile(final_prices, 5)
        var_loss = initial_price - var_price
        var_pct = (var_loss / initial_price) * 100
        
        # CVaR
        cvar_price = np.mean(final_prices[final_prices <= var_price])
        cvar_loss = initial_price - cvar_price
        cvar_pct = (cvar_loss / initial_price) * 100
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(price_paths)
        
        # 勝率
        upside_paths = np.sum(final_prices > initial_price)
        win_rate = (upside_paths / self.n_simulations) * 100
        
        # 平均上漲和下跌
        upside = returns[returns > 0]
        downside = returns[returns < 0]
        avg_upside = np.mean(upside) * 100 if len(upside) > 0 else 0
        avg_downside = np.mean(downside) * 100 if len(downside) > 0 else 0
        
        # Sharpe Ratio
        volatility = np.std(returns)
        sharpe = np.mean(returns) / volatility if volatility > 0 else 0
        
        return {
            'expected_price': expected_price,
            'optimistic_price': opt_price,
            'base_price': base_price,
            'pessimistic_price': pess_price,
            'var_95_price': var_price,
            'var_95_loss': var_loss,
            'var_95_pct': var_pct,
            'cvar_95_price': cvar_price,
            'cvar_95_loss': cvar_loss,
            'cvar_95_pct': cvar_pct,
            'max_drawdown_pct': max_drawdown,
            'win_rate': win_rate,
            'avg_upside_pct': avg_upside,
            'avg_downside_pct': avg_downside,
            'sharpe_ratio': sharpe,
            'volatility_pct': volatility * 100,
        }
    
    def _calculate_max_drawdown(self, paths: np.ndarray) -> float:
        """計算最大回撤百分比"""
        max_drawdowns = []
        for path in paths:
            peak = np.maximum.accumulate(path)
            drawdown = np.min((path - peak) / peak)
            max_drawdowns.append(drawdown)
        return np.mean(max_drawdowns) * 100


# ==========================================
# 參數推導
# ==========================================

def derive_volatility_from_score(fundamental_score: float) -> float:
    """根據基本面評分推導波動率"""
    # 高評分 → 低波動率
    volatility = 0.60 - (fundamental_score / 100) * 0.45
    return max(0.15, min(0.60, volatility))


def derive_expected_return(fundamental_score: float) -> Tuple[float, float, float]:
    """
    根據基本面評分推導預期回報率（三情景）
    
    評分 60 → 12% 基準回報（保守）
    評分 73 → 18% 基準回報（合理 — TSMC）
    評分 80 → 22% 基準回報（優秀 — NVDA）
    評分 100 → 30% 基準回報（傑出）
    """
    # 線性映射：評分 50 → 5%，評分 100 → 30%
    base = 0.05 + (fundamental_score - 50) / 50 * 0.25
    base = max(-0.05, min(0.35, base))
    
    # 樂觀情景：基準 + 30% 的上升空間
    optimistic = base * 1.3
    
    # 悲觀情景：基準 - 40% 的下行空間
    pessimistic = base * 0.6
    
    return optimistic, base, pessimistic


# ==========================================
# 完整分析
# ==========================================

def analyze_probability(stock_code: str,
                       current_price: float,
                       fundamental_score: float) -> Dict:
    """執行完整的概率風險分析"""
    
    # 參數推導
    volatility = derive_volatility_from_score(fundamental_score)
    opt_ret, base_ret, pess_ret = derive_expected_return(fundamental_score)
    
    # 蒙特卡洛模擬
    simulator = MonteCarloSimulator()
    
    # 三情景模擬
    opt_paths = simulator.simulate(current_price, opt_ret, volatility)
    base_paths = simulator.simulate(current_price, base_ret, volatility)
    pess_paths = simulator.simulate(current_price, pess_ret, volatility)
    
    # 計算指標
    opt_metrics = simulator.calculate_metrics(opt_paths, current_price)
    base_metrics = simulator.calculate_metrics(base_paths, current_price)
    pess_metrics = simulator.calculate_metrics(pess_paths, current_price)
    
    # 風險評分
    risk_score = _calculate_risk_score(
        fundamental_score,
        base_metrics['var_95_pct'],
        abs(base_metrics['max_drawdown_pct']),
        base_metrics['win_rate']
    )
    
    # 綜合評分
    final_score = fundamental_score * 0.6 + risk_score * 0.4
    
    return {
        'stock_code': stock_code,
        'current_price': current_price,
        'fundamental_score': fundamental_score,
        'risk_score': risk_score,
        'final_score': final_score,
        'volatility': volatility,
        'returns': {
            'optimistic': opt_ret,
            'base': base_ret,
            'pessimistic': pess_ret,
        },
        'scenarios': {
            'optimistic': opt_metrics,
            'base': base_metrics,
            'pessimistic': pess_metrics,
        },
    }


def _calculate_risk_score(fundamental_score: float,
                         var_pct: float,
                         max_dd: float,
                         win_rate: float) -> float:
    """計算風險評分（0-100，高分=低風險）"""
    
    fundamental_contrib = (fundamental_score / 100) * 30
    var_contrib = max(0, 40 - var_pct * 2)
    dd_contrib = max(0, 20 - max_dd * 1)
    win_contrib = max(0, min(10, (win_rate - 50) / 50 * 10))
    
    return min(100, max(0, 
        fundamental_contrib + var_contrib + dd_contrib + win_contrib
    ))


# ==========================================
# 報告生成
# ==========================================

def generate_markdown_report(results: List[Dict]) -> str:
    """生成 Markdown 報告"""
    
    report = f"""# 📊 Phase 3.2 概率風險評估報告

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📋 投資建議對照表

| 股票 | 基本面評分 | 風險評分 | 綜合評分 | 基準目標價 | VaR 損失 | 最大回撤 | 建議 |
|------|-----------|---------|---------|-----------|---------|---------|------|
"""
    
    for result in results:
        code = result['stock_code']
        fundamental = result['fundamental_score']
        risk = result['risk_score']
        final = result['final_score']
        base = result['scenarios']['base']
        
        target = base['base_price']
        var_loss = base['var_95_loss']
        max_dd = abs(base['max_drawdown_pct'])
        
        if final >= 75:
            rec = "💚 強烈買入"
        elif final >= 60:
            rec = "💛 買入"
        elif final >= 45:
            rec = "⚪ 持有"
        else:
            rec = "🟠 減持"
        
        report += f"| {code} | {fundamental:.1f} | {risk:.1f} | {final:.1f} | ${target:.2f} | ${var_loss:.2f} | {max_dd:.1f}% | {rec} |\n"
    
    report += "\n---\n\n"
    
    # 詳細分析
    for result in results:
        report += _generate_stock_detail(result)
    
    return report


def _generate_stock_detail(result: Dict) -> str:
    """生成單支股票詳細報告"""
    
    code = result['stock_code']
    curr = result['current_price']
    fund = result['fundamental_score']
    risk = result['risk_score']
    final = result['final_score']
    vol = result['volatility']
    
    base = result['scenarios']['base']
    opt = result['scenarios']['optimistic']
    pess = result['scenarios']['pessimistic']
    
    return f"""## {code} — 詳細分析

### 評分組成
- **基本面評分**: {fund:.1f}/100
- **風險評分**: {risk:.1f}/100
- **綜合評分**: {final:.1f}/100

### 三情景目標價

| 情景 | 樂觀 | 基準 | 悲觀 |
|-----|------|------|------|
| **目標價** | ${opt['base_price']:.2f} | ${base['base_price']:.2f} | ${pess['base_price']:.2f} |
| **收益率** | {((opt['base_price']-curr)/curr*100):.1f}% | {((base['base_price']-curr)/curr*100):.1f}% | {((pess['base_price']-curr)/curr*100):.1f}% |

### 風險指標（基準情景）
- **預期股價**: ${base['expected_price']:.2f}
- **勝率**: {base['win_rate']:.1f}%
- **VaR (95%)**: ${base['var_95_loss']:.2f} ({base['var_95_pct']:.1f}%)
- **最大回撤**: {abs(base['max_drawdown_pct']):.1f}%
- **波動率**: {vol*100:.1f}%
- **Sharpe Ratio**: {base['sharpe_ratio']:.2f}

---

"""


if __name__ == "__main__":
    # 測試示例
    test_cases = [
        {'code': 'NVDA', 'price': 875.50, 'score': 80.0},
        {'code': '2330', 'price': 136.45, 'score': 73.0},
        {'code': '2412', 'price': 710.00, 'score': 75.0},
    ]
    
    results = []
    for test in test_cases:
        result = analyze_probability(test['code'], test['price'], test['score'])
        results.append(result)
    
    # 生成報告
    report = generate_markdown_report(results)
    
    # 保存
    outputs_dir = Path('/mnt/user-data/outputs')
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    with open(outputs_dir / 'Phase3.2_概率風險評估報告.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ 報告已生成")
