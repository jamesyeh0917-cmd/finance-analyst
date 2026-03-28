"""
📊 Phase 3.4 — GitHub Actions 報告生成器

功能：
  • 整合技術面、基本面、機率面三維度數據
  • 生成策略雷達圖 (Decision Radar)
  • 生成情景預測表 (Scenario Matrix) with LaTeX 公式
  • GitHub Job Summary 輸出格式
  • 風險警告標籤（紅色警告機制）
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import math

# ==========================================
# 數據讀取模組
# ==========================================

def read_stock_analysis_data(stock_code: str) -> Dict:
    """
    整合一支股票的技術面、基本面、機率面數據
    
    返回格式：
    {
        'code': 'NVDA',
        'technical': {...},
        'fundamental': {...},
        'probability': {...},
    }
    """
    
    data = {
        'code': stock_code,
        'technical': {},
        'fundamental': {},
        'probability': {},
    }
    
    # 這裡會連接到實際的數據源
    # 目前使用測試數據
    
    return data


# ==========================================
# 策略雷達圖 (Decision Radar)
# ==========================================

def generate_radar_svg(tech_score: float,
                      fundamental_score: float,
                      risk_score: float,
                      stock_code: str = 'STOCK') -> str:
    """
    生成 SVG 格式的三維度策略雷達圖
    
    雷達圖三個維度：
      1. 技術面評分（0-100）
      2. 基本面評分（0-100）
      3. 風險評分（0-100，高分 = 低風險）
    
    Args:
        tech_score: 技術面評分 (0-100)
        fundamental_score: 基本面評分 (0-100)
        risk_score: 風險評分 (0-100)
        stock_code: 股票代碼
    
    Returns:
        SVG 格式的雷達圖 HTML
    """
    
    # 三個維度的極座標點
    center_x, center_y = 150, 150
    radius = 100
    
    # 角度（三個維度均勻分佈）
    angles = [0, 120, 240]  # 度數
    labels = ['技術面', '基本面', '風險']
    values = [tech_score, fundamental_score, risk_score]
    
    # 轉換為弧度並計算座標
    points = []
    for i, angle in enumerate(angles):
        rad = math.radians(angle)
        # 根據分數計算半徑
        r = radius * (values[i] / 100)
        x = center_x + r * math.cos(rad)
        y = center_y + r * math.sin(rad)
        points.append((x, y))
    
    # 創建 SVG
    svg = f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg" style="max-width: 300px; margin: 10px auto;">
  <!-- 背景 -->
  <rect width="300" height="300" fill="#f8f9fa"/>
  
  <!-- 網格線（三層）-->
  <g stroke="#ddd" fill="none" stroke-width="1">
    <!-- 25% 圓 -->
    <circle cx="150" cy="150" r="25"/>
    <!-- 50% 圓 -->
    <circle cx="150" cy="150" r="50"/>
    <!-- 75% 圓 -->
    <circle cx="150" cy="150" r="75"/>
    <!-- 100% 圓 -->
    <circle cx="150" cy="150" r="100"/>
  </g>
  
  <!-- 軸線 -->
  <g stroke="#999" stroke-width="1.5" stroke-dasharray="2,2">
    <!-- 技術面軸 -->
    <line x1="150" y1="150" x2="250" y2="150"/>
    <!-- 基本面軸 -->
    <line x1="150" y1="150" x2="{150 + 100*math.cos(math.radians(120)):.0f}" y2="{150 + 100*math.sin(math.radians(120)):.0f}"/>
    <!-- 風險軸 -->
    <line x1="150" y1="150" x2="{150 + 100*math.cos(math.radians(240)):.0f}" y2="{150 + 100*math.sin(math.radians(240)):.0f}"/>
  </g>
  
  <!-- 數據填充區域（三角形）-->
  <polygon points="{points[0][0]:.0f},{points[0][1]:.0f} {points[1][0]:.0f},{points[1][1]:.0f} {points[2][0]:.0f},{points[2][1]:.0f}" 
           fill="#3498db" fill-opacity="0.3" stroke="#3498db" stroke-width="2"/>
  
  <!-- 數據點 -->
  <g fill="#e74c3c" r="4">
    <circle cx="{points[0][0]:.0f}" cy="{points[0][1]:.0f}" r="4"/>
    <circle cx="{points[1][0]:.0f}" cy="{points[1][1]:.0f}" r="4"/>
    <circle cx="{points[2][0]:.0f}" cy="{points[2][1]:.0f}" r="4"/>
  </g>
  
  <!-- 標籤和數值 -->
  <g font-size="12" text-anchor="middle" fill="#333">
    <!-- 技術面 -->
    <text x="260" y="155" font-weight="bold">技術面</text>
    <text x="260" y="170" fill="#e74c3c" font-size="14" font-weight="bold">{tech_score:.0f}</text>
    
    <!-- 基本面 -->
    <text x="45" y="95" font-weight="bold">基本面</text>
    <text x="45" y="110" fill="#e74c3c" font-size="14" font-weight="bold">{fundamental_score:.0f}</text>
    
    <!-- 風險 -->
    <text x="200" y="260" font-weight="bold">風險</text>
    <text x="200" y="275" fill="#e74c3c" font-size="14" font-weight="bold">{risk_score:.0f}</text>
  </g>
  
  <!-- 中心標題 -->
  <g font-size="16" text-anchor="middle" fill="#2c3e50" font-weight="bold">
    <text x="150" y="145">{stock_code}</text>
    <text x="150" y="165" font-size="12" fill="#666">決策雷達圖</text>
  </g>
  
  <!-- 品質指示 -->
  <g font-size="10" fill="#666">
    <text x="150" y="295" text-anchor="middle">三維度均衡評分（越外擴越優秀）</text>
  </g>
</svg>'''
    
    return svg


# ==========================================
# 情景預測表 (Scenario Matrix)
# ==========================================

def generate_scenario_matrix_html(stock_code: str,
                                 current_price: float,
                                 opt_price: float,
                                 base_price: float,
                                 pess_price: float) -> str:
    """
    生成包含 LaTeX 公式的情景預測表
    
    使用幾何布朗運動公式：
    S_t = S_0 * exp((μ - σ²/2)*t + σ*W_t)
    """
    
    # 計算收益率
    opt_return = ((opt_price - current_price) / current_price) * 100
    base_return = ((base_price - current_price) / current_price) * 100
    pess_return = ((pess_price - current_price) / current_price) * 100
    
    # 顏色編碼
    color_opt = '#27ae60'    # 綠色（樂觀）
    color_base = '#f39c12'   # 橙色（基準）
    color_pess = '#e74c3c'   # 紅色（悲觀）
    
    html = f'''
<div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
  <h4 style="margin-top: 0; color: #2c3e50;">📊 情景預測矩陣 - {stock_code}</h4>
  
  <p style="font-size: 12px; color: #666;">
    基於幾何布朗運動模型：
  </p>
  
  <div style="background: white; padding: 12px; border-left: 4px solid #3498db; margin: 10px 0;">
    <code style="font-size: 11px;">S<sub>t</sub> = S₀ · exp((μ - σ²/2)·t + σ·W<sub>t</sub>)</code>
  </div>
  
  <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
    <thead>
      <tr style="background: #ecf0f1;">
        <th style="padding: 10px; text-align: left; border: 1px solid #bdc3c7;">情景</th>
        <th style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">目標價</th>
        <th style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">預期收益</th>
        <th style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">機率</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px; border: 1px solid #bdc3c7;">
          <span style="color: {color_opt}; font-weight: bold;">🟢 樂觀</span>
          <br/><span style="font-size: 11px; color: #666;">(高成長假設)</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="font-weight: bold; font-size: 14px;">${opt_price:.2f}</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="color: {color_opt}; font-weight: bold;">+{opt_return:.1f}%</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="background: {color_opt}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">25%</span>
        </td>
      </tr>
      <tr style="background: #f8f9fa;">
        <td style="padding: 10px; border: 1px solid #bdc3c7;">
          <span style="color: {color_base}; font-weight: bold;">🟡 基準</span>
          <br/><span style="font-size: 11px; color: #666;">(正常成長)</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="font-weight: bold; font-size: 14px;">${base_price:.2f}</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="color: {color_base}; font-weight: bold;">{base_return:+.1f}%</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="background: {color_base}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">50%</span>
        </td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #bdc3c7;">
          <span style="color: {color_pess}; font-weight: bold;">🔴 悲觀</span>
          <br/><span style="font-size: 11px; color: #666;">(衰退假設)</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="font-weight: bold; font-size: 14px;">${pess_price:.2f}</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="color: {color_pess}; font-weight: bold;">{pess_return:+.1f}%</span>
        </td>
        <td style="padding: 10px; text-align: center; border: 1px solid #bdc3c7;">
          <span style="background: {color_pess}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">25%</span>
        </td>
      </tr>
    </tbody>
  </table>
  
  <p style="font-size: 11px; color: #666; margin: 10px 0;">
    <strong>當前股價：</strong> ${current_price:.2f}
  </p>
</div>
'''
    
    return html


# ==========================================
# 風險警告標籤
# ==========================================

def generate_risk_warning(var_pct: float,
                        max_dd_pct: float,
                        win_rate: float) -> str:
    """
    生成風險警告標籤
    
    Rules:
      • VaR > 30% → 🔴 高風險
      • VaR 20-30% → 🟠 中風險
      • VaR < 20% → 🟢 低風險
      
      • Max Drawdown > 30% → 🔴 高波動
      • Win Rate < 50% → 🔴 下行風險
    """
    
    warnings = []
    
    # VaR 評估
    if var_pct > 30:
        warnings.append({
            'icon': '🔴',
            'label': '高風險',
            'message': f'VaR 損失 {var_pct:.1f}%（高於 30%）',
            'color': '#e74c3c'
        })
    elif var_pct > 20:
        warnings.append({
            'icon': '🟠',
            'label': '中風險',
            'message': f'VaR 損失 {var_pct:.1f}%（20-30%）',
            'color': '#f39c12'
        })
    else:
        warnings.append({
            'icon': '🟢',
            'label': '低風險',
            'message': f'VaR 損失 {var_pct:.1f}%（低於 20%）',
            'color': '#27ae60'
        })
    
    # 最大回撤評估
    if max_dd_pct > 30:
        warnings.append({
            'icon': '🔴',
            'label': '高波動',
            'message': f'最大回撤 {max_dd_pct:.1f}%（高於 30%）',
            'color': '#e74c3c'
        })
    
    # 勝率評估
    if win_rate < 50:
        warnings.append({
            'icon': '🔴',
            'label': '下行風險',
            'message': f'勝率僅 {win_rate:.1f}%（低於 50%）',
            'color': '#e74c3c'
        })
    
    # 生成 HTML
    html = '<div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">'
    
    for warning in warnings:
        html += f'''
    <div style="
        background: {warning['color']};
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    ">
        {warning['icon']} {warning['label']}
        <br/>
        <span style="font-size: 11px; opacity: 0.9;">{warning['message']}</span>
    </div>
    '''
    
    html += '</div>'
    
    return html


# ==========================================
# 完整報告生成
# ==========================================

def generate_comprehensive_report(stock_data_list: List[Dict]) -> str:
    """
    生成完整的綜合報告，包含所有視覺化組件
    """
    
    report = f'''# 📊 Finance Analyst — AI 驅動投資決策系統

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S (台北時間)')}  
**系統版本**: Phase 3.4 (完整版)

---

## 🎯 執行摘要

本報告整合了技術面、基本面與機率面的三維度分析，為每支股票提供量化的投資建議。

'''
    
    # 添加綜合評分表
    report += '## 📈 綜合評分對照表\n\n'
    report += '| 股票 | 技術面 | 基本面 | 風險評分 | 綜合評分 | 建議 |\n'
    report += '|------|--------|--------|---------|---------|------|\n'
    
    for stock in stock_data_list:
        code = stock['code']
        tech = stock.get('technical_score', 0)
        fundamental = stock.get('fundamental_score', 0)
        risk = stock.get('risk_score', 0)
        composite = (tech * 0.3 + fundamental * 0.4 + risk * 0.3)
        
        if composite >= 75:
            rec = '💚 強烈買入'
        elif composite >= 60:
            rec = '💛 買入'
        elif composite >= 45:
            rec = '⚪ 持有'
        elif composite >= 30:
            rec = '🟠 減持'
        else:
            rec = '💔 賣出'
        
        report += f'| {code} | {tech:.0f} | {fundamental:.0f} | {risk:.0f} | **{composite:.1f}** | {rec} |\n'
    
    report += '\n---\n\n'
    
    # 添加詳細分析
    for stock in stock_data_list:
        code = stock['code']
        
        report += f'## {code} — 詳細分析\n\n'
        
        # 雷達圖
        radar_svg = generate_radar_svg(
            stock.get('technical_score', 0),
            stock.get('fundamental_score', 0),
            stock.get('risk_score', 0),
            code
        )
        report += radar_svg + '\n\n'
        
        # 情景預測表
        scenario_html = generate_scenario_matrix_html(
            code,
            stock.get('current_price', 0),
            stock.get('optimistic_price', 0),
            stock.get('base_price', 0),
            stock.get('pessimistic_price', 0)
        )
        report += scenario_html + '\n\n'
        
        # 風險警告
        risk_warning = generate_risk_warning(
            stock.get('var_pct', 0),
            stock.get('max_dd_pct', 0),
            stock.get('win_rate', 0)
        )
        report += risk_warning + '\n\n'
        
        # 詳細指標
        report += f'''### 核心指標

**價格信息**：
- 當前股價：${stock.get('current_price', 0):.2f}
- 基準目標價：${stock.get('base_price', 0):.2f}
- 預期上升空間：{((stock.get('base_price', 0) - stock.get('current_price', 0)) / stock.get('current_price', 1) * 100):.1f}%

**蒙特卡洛風險指標**：
- 勝率（上漲概率）：{stock.get('win_rate', 0):.1f}%
- VaR @95%：${stock.get('var_loss', 0):.2f} ({stock.get('var_pct', 0):.1f}%)
- 最大回撤：{stock.get('max_dd_pct', 0):.1f}%
- Sharpe Ratio：{stock.get('sharpe_ratio', 0):.2f}

---

'''
    
    return report


# ==========================================
# GitHub Job Summary 輸出
# ==========================================

def write_github_summary(report: str):
    """
    寫入 GitHub Job Summary
    
    環境變數：GITHUB_STEP_SUMMARY
    """
    
    summary_file = os.getenv('GITHUB_STEP_SUMMARY', None)
    
    if summary_file:
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 已寫入 GitHub Job Summary: {summary_file}")
    else:
        # 本地開發環境
        output_path = Path('/mnt/user-data/outputs/github_summary.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 已保存報告到：{output_path}")


# ==========================================
# 主函數
# ==========================================

def main():
    """主執行函數"""
    
    print("=" * 80)
    print("🚀 Phase 3.4 — GitHub Actions 報告生成")
    print("=" * 80)
    print()
    
    # 測試數據
    test_stocks = [
        {
            'code': 'NVDA',
            'current_price': 875.50,
            'technical_score': 72.0,
            'fundamental_score': 80.0,
            'risk_score': 29.1,
            'base_price': 1026.30,
            'optimistic_price': 1128.57,
            'pessimistic_price': 969.43,
            'var_loss': 186.37,
            'var_pct': 21.3,
            'max_dd_pct': 19.9,
            'win_rate': 75.3,
            'sharpe_ratio': 0.71,
        },
        {
            'code': '2330',
            'current_price': 136.45,
            'technical_score': 68.0,
            'fundamental_score': 73.0,
            'risk_score': 25.9,
            'base_price': 156.42,
            'optimistic_price': 170.80,
            'pessimistic_price': 148.37,
            'var_loss': 36.77,
            'var_pct': 26.9,
            'max_dd_pct': 23.2,
            'win_rate': 70.2,
            'sharpe_ratio': 0.58,
        },
        {
            'code': '2412',
            'current_price': 710.00,
            'technical_score': 70.0,
            'fundamental_score': 75.0,
            'risk_score': 26.8,
            'base_price': 819.19,
            'optimistic_price': 896.33,
            'pessimistic_price': 776.12,
            'var_loss': 180.09,
            'var_pct': 25.4,
            'max_dd_pct': 22.3,
            'win_rate': 71.7,
            'sharpe_ratio': 0.62,
        },
    ]
    
    print("📊 生成綜合報告...")
    report = generate_comprehensive_report(test_stocks)
    
    # 寫入輸出
    print("\n📝 寫入 GitHub Job Summary...")
    write_github_summary(report)
    
    print("\n" + "=" * 80)
    print("✅ Phase 3.4 報告生成完成！")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)

