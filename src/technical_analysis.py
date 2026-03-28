"""
📈 Technical Analysis — 技術指標計算引擎

功能：
  • 自動掃描 data/raw/ 並讀取最新的股價 CSV 檔案
  • 計算四大核心技術指標：RSI、MACD、布林帶、移動平均線
  • 將計算結果合併到原始數據
  • 保存加工後的數據到 data/processed/ 資料夾
  • 所有參數從 settings.yaml 動態讀取（無需改代碼）

設計原則：
  1. 資料接力：自動讀取 data/raw/ 的 CSV
  2. 加工與落地：結果存入 data/processed/
  3. 參數動態化：從 settings.yaml 讀取所有參數
  4. 模組化設計：每個指標獨立 Function

技術指標說明：
  • RSI（Relative Strength Index）— 測量動量，0-100，>70 超買，<30 超賣
  • MACD（Moving Average Convergence Divergence）— 趨勢跟隨指標，包括 MACD 線、信號線、柱狀圖
  • 布林帶（Bollinger Bands）— 波動性指標，包括上軌、中線、下軌
  • 移動平均線（Moving Averages）— 趨勢指標，支持多條 MA

使用示例：
  python src/technical_analysis.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime

import pandas as pd
import numpy as np

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


# ==========================================
# 日誌配置
# ==========================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    配置日誌系統
    
    Args:
        log_level: 日誌級別（DEBUG/INFO/WARNING/ERROR）
    
    Returns:
        配置好的 logger 物件
    """
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
# 路徑管理
# ==========================================

def get_data_dirs() -> Tuple[Path, Path]:
    """
    獲取數據目錄路徑
    
    Returns:
        (data/raw/ 目錄, data/processed/ 目錄)
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    if not (project_root / '.git').exists():
        logger.warning("⚠️ 警告：未找到 .git 目錄")
        project_root = Path.cwd()
    
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    
    # 創建目錄
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"✅ 數據目錄已確認：")
    logger.info(f"   原始數據：{raw_dir}")
    logger.info(f"   處理後：{processed_dir}")
    
    return raw_dir, processed_dir


# ==========================================
# 配置讀取
# ==========================================

def load_technical_config() -> Tuple[Dict, ConfigLoader]:
    """
    從 settings.yaml 讀取技術指標配置
    
    Returns:
        (技術指標配置字典, ConfigLoader 物件)
    """
    try:
        logger.info("📖 正在讀取技術指標配置...")
        loader = ConfigLoader('config/settings.yaml')
        
        # 獲取技術指標配置，如果沒有則使用預設值
        tech_config = loader.config.get('technical_indicators', {})
        
        # 預設參數（如果配置文件中沒有）
        if not tech_config:
            logger.warning("⚠️ 配置文件中沒有技術指標配置，使用預設值")
            tech_config = {
                'moving_averages': {'periods': [5, 20, 50, 200]},
                'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
                'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
                'bollinger_bands': {'period': 20, 'num_std': 2}
            }
        
        logger.info("✅ 成功讀取技術指標配置")
        return tech_config, loader
        
    except Exception as e:
        logger.error(f"❌ 讀取配置文件時出錯: {e}")
        raise


# ==========================================
# CSV 檔案掃描
# ==========================================

def scan_raw_csv_files(raw_dir: Path) -> List[Path]:
    """
    掃描 data/raw/ 並找到所有 CSV 檔案
    
    Args:
        raw_dir: data/raw/ 目錄路徑
    
    Returns:
        CSV 檔案路徑列表（按修改時間排序，最新的在前）
    """
    logger.info("📂 正在掃描 data/raw/ 目錄...")
    
    csv_files = list(raw_dir.glob('*.csv'))
    
    if not csv_files:
        logger.warning("⚠️ 在 data/raw/ 中找不到任何 CSV 檔案")
        return []
    
    # 按修改時間排序（最新的在前）
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    logger.info(f"✅ 找到 {len(csv_files)} 個 CSV 檔案")
    for csv_file in csv_files:
        logger.info(f"   • {csv_file.name}")
    
    return csv_files


# ==========================================
# 技術指標計算 — 獨立 Function
# ==========================================

def calculate_moving_averages(
    df: pd.DataFrame,
    periods: List[int],
    price_column: str = 'Close'
) -> pd.DataFrame:
    """
    計算移動平均線（MA）
    
    Args:
        df: 包含股價數據的 DataFrame
        periods: 要計算的週期列表（如 [5, 20, 50, 200]）
        price_column: 用於計算 MA 的價格列名稱
    
    Returns:
        添加了 MA 列的 DataFrame
    """
    logger.info(f"📊 計算移動平均線（MA）：{periods}")
    
    try:
        for period in periods:
            ma_column = f'MA{period}'
            df[ma_column] = df[price_column].rolling(window=period).mean()
            logger.info(f"   ✅ 已計算 MA{period}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ 計算 MA 時出錯: {e}")
        raise


def calculate_rsi(
    df: pd.DataFrame,
    period: int = 14,
    price_column: str = 'Close'
) -> pd.DataFrame:
    """
    計算相對強度指標（RSI）
    
    RSI 的計算步驟：
    1. 計算價格變化（delta）
    2. 分離上漲和下跌
    3. 計算平均上漲和平均下跌
    4. 計算 RS = 平均上漲 / 平均下跌
    5. 計算 RSI = 100 - (100 / (1 + RS))
    
    Args:
        df: 包含股價數據的 DataFrame
        period: RSI 週期（通常 14 天）
        price_column: 用於計算 RSI 的價格列名稱
    
    Returns:
        添加了 RSI 列的 DataFrame
    """
    logger.info(f"📊 計算相對強度指標（RSI）：周期 {period}")
    
    try:
        # 計算價格變化
        delta = df[price_column].diff()
        
        # 分離上漲和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 計算相對強度（RS）
        rs = gain / loss
        
        # 計算 RSI
        df['RSI'] = 100 - (100 / (1 + rs))
        
        logger.info(f"   ✅ 已計算 RSI（周期 {period}）")
        return df
        
    except Exception as e:
        logger.error(f"❌ 計算 RSI 時出錯: {e}")
        raise


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    price_column: str = 'Close'
) -> pd.DataFrame:
    """
    計算 MACD（指數平滑移動平均線）
    
    MACD 包含三個成分：
    1. MACD 線 = 12日 EMA - 26日 EMA
    2. 信號線 = MACD 線的 9日 EMA
    3. 柱狀圖 = MACD 線 - 信號線
    
    Args:
        df: 包含股價數據的 DataFrame
        fast_period: 快速 EMA 週期（通常 12）
        slow_period: 慢速 EMA 週期（通常 26）
        signal_period: 信號線 EMA 週期（通常 9）
        price_column: 用於計算 MACD 的價格列名稱
    
    Returns:
        添加了 MACD、MACD_Signal、MACD_Histogram 列的 DataFrame
    """
    logger.info(f"📊 計算 MACD（{fast_period}/{slow_period}/{signal_period}）")
    
    try:
        # 計算 EMA（指數加權移動平均）
        ema_fast = df[price_column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df[price_column].ewm(span=slow_period, adjust=False).mean()
        
        # 計算 MACD 線
        df['MACD'] = ema_fast - ema_slow
        
        # 計算信號線（MACD 的 EMA）
        df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        
        # 計算柱狀圖（直方圖）
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        logger.info(f"   ✅ 已計算 MACD 及其衍生指標")
        return df
        
    except Exception as e:
        logger.error(f"❌ 計算 MACD 時出錯: {e}")
        raise


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2,
    price_column: str = 'Close'
) -> pd.DataFrame:
    """
    計算布林帶（Bollinger Bands）
    
    布林帶包含三條線：
    1. 中線 = 簡單移動平均線（SMA）
    2. 上軌 = 中線 + （標準差 × num_std）
    3. 下軌 = 中線 - （標準差 × num_std）
    
    Args:
        df: 包含股價數據的 DataFrame
        period: 移動平均線週期（通常 20 天）
        num_std: 標準差倍數（通常 2）
        price_column: 用於計算布林帶的價格列名稱
    
    Returns:
        添加了 BB_Middle、BB_Upper、BB_Lower、BB_Width、BB_Position 列的 DataFrame
    """
    logger.info(f"📊 計算布林帶（周期 {period}，標準差倍數 {num_std}）")
    
    try:
        # 計算中線（SMA）
        sma = df[price_column].rolling(window=period).mean()
        
        # 計算標準差
        std = df[price_column].rolling(window=period).std()
        
        # 計算布林帶
        df['BB_Middle'] = sma
        df['BB_Upper'] = sma + (std * num_std)
        df['BB_Lower'] = sma - (std * num_std)
        
        # 計算帶寬（上軌 - 下軌）
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        
        # 計算 BB Position（價格在帶中的位置，0-1，0 = 下軌，1 = 上軌）
        df['BB_Position'] = (df[price_column] - df['BB_Lower']) / df['BB_Width']
        
        logger.info(f"   ✅ 已計算布林帶及其衍生指標")
        return df
        
    except Exception as e:
        logger.error(f"❌ 計算布林帶時出錯: {e}")
        raise


# ==========================================
# 主要分析流程
# ==========================================

def analyze_single_csv(
    csv_path: Path,
    tech_config: Dict,
    processed_dir: Path
) -> Optional[pd.DataFrame]:
    """
    分析單個 CSV 檔案並計算所有技術指標
    
    Args:
        csv_path: CSV 檔案路徑
        tech_config: 技術指標配置字典
        processed_dir: 輸出目錄（data/processed/）
    
    Returns:
        計算後的 DataFrame，或 None 如果失敗
    """
    logger.info(f"📊 正在分析 {csv_path.name}...")
    
    try:
        # 讀取 CSV 檔案
        df = pd.read_csv(csv_path)
        logger.info(f"   ✅ 讀取成功，包含 {len(df)} 行資料")
        
        # 確保日期列被正確解析
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # 按日期排序（確保時間序列正確）
        if 'Date' in df.columns:
            df = df.sort_values('Date').reset_index(drop=True)
        
        # ========================================
        # 計算所有技術指標
        # ========================================
        
        # 1. 移動平均線
        ma_periods = tech_config.get('moving_averages', {}).get('periods', [5, 20, 50, 200])
        df = calculate_moving_averages(df, ma_periods)
        
        # 2. RSI
        rsi_config = tech_config.get('rsi', {})
        rsi_period = rsi_config.get('period', 14)
        df = calculate_rsi(df, period=rsi_period)
        
        # 3. MACD
        macd_config = tech_config.get('macd', {})
        df = calculate_macd(
            df,
            fast_period=macd_config.get('fast_period', 12),
            slow_period=macd_config.get('slow_period', 26),
            signal_period=macd_config.get('signal_period', 9)
        )
        
        # 4. 布林帶
        bb_config = tech_config.get('bollinger_bands', {})
        df = calculate_bollinger_bands(
            df,
            period=bb_config.get('period', 20),
            num_std=bb_config.get('num_std', 2)
        )
        
        # ========================================
        # 保存處理後的數據
        # ========================================
        
        # 生成輸出檔案名稱
        output_filename = f"analyzed_{csv_path.name}"
        output_path = processed_dir / output_filename
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"   ✅ 已保存至 {output_path}")
        
        # 顯示統計信息
        logger.info(f"   📊 數據統計：")
        logger.info(f"      • 總行數：{len(df)}")
        logger.info(f"      • 總列數：{len(df.columns)}")
        logger.info(f"      • 新增指標列：{len(df.columns) - 8}（原始 8 列）")
        
        return df
        
    except Exception as e:
        logger.error(f"   ❌ 分析失敗: {e}")
        return None


def analyze_all_csv_files(
    raw_dir: Path,
    processed_dir: Path,
    tech_config: Dict
) -> Dict[str, bool]:
    """
    分析所有 CSV 檔案
    
    Args:
        raw_dir: data/raw/ 目錄
        processed_dir: data/processed/ 目錄
        tech_config: 技術指標配置
    
    Returns:
        {檔案名稱: 是否成功} 的字典
    """
    logger.info("=" * 60)
    logger.info("🚀 開始執行技術分析任務")
    logger.info("=" * 60)
    
    # 掃描 CSV 檔案
    csv_files = scan_raw_csv_files(raw_dir)
    
    if not csv_files:
        logger.error("❌ 沒有可分析的 CSV 檔案")
        return {}
    
    logger.info("")
    results = {}
    
    # 分析每個 CSV 檔案
    for csv_path in csv_files:
        try:
            df = analyze_single_csv(csv_path, tech_config, processed_dir)
            results[csv_path.name] = (df is not None)
        except Exception as e:
            logger.error(f"❌ 處理 {csv_path.name} 時出錯: {e}")
            results[csv_path.name] = False
    
    # 總結
    logger.info("")
    logger.info("=" * 60)
    logger.info("📈 任務完成！")
    logger.info("=" * 60)
    
    success_count = sum(results.values())
    total_count = len(results)
    logger.info(f"✅ 成功分析：{success_count} / {total_count} 個檔案")
    
    if success_count > 0:
        success_files = [f for f, success in results.items() if success]
        logger.info(f"✅ 成功檔案：{', '.join(success_files)}")
    
    failed_count = total_count - success_count
    if failed_count > 0:
        failed_files = [f for f, success in results.items() if not success]
        logger.warning(f"❌ 失敗檔案：{', '.join(failed_files)}")
    
    logger.info("=" * 60)
    
    return results


# ==========================================
# 主函數
# ==========================================

def main():
    """
    主函數：執行完整的技術分析流程
    
    流程：
    1. 讀取配置
    2. 掃描 data/raw/ 中的 CSV 檔案
    3. 計算四大技術指標
    4. 保存結果到 data/processed/
    """
    try:
        # 第一步：讀取配置
        tech_config, loader = load_technical_config()
        
        # 第二步：獲取目錄
        raw_dir, processed_dir = get_data_dirs()
        
        # 第三步：分析所有 CSV 檔案
        results = analyze_all_csv_files(raw_dir, processed_dir, tech_config)
        
        # 第四步：返回退出碼
        if all(results.values()):
            logger.info("✅ 所有檔案都成功分析！")
            return 0
        else:
            logger.warning("⚠️ 有部分檔案分析失敗，但任務繼續進行")
            return 1
            
    except KeyboardInterrupt:
        logger.info("❌ 任務被用戶中止")
        return 130
    except Exception as e:
        logger.error(f"❌ 任務執行失敗: {e}")
        return 1


# ==========================================
# 進入點
# ==========================================

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

