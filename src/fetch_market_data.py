"""
📊 Fetch Market Data — 數據收集引擎

功能：
  • 從配置文件動態讀取股票清單
  • 使用 yfinance 自動抓取股價歷史數據
  • 將數據保存為 CSV 格式到 data/raw/
  • 全自動化、雲端友善（無需人工互動）

設計原則：
  1. 動態讀取配置（ConfigLoader）
  2. 雲端友善（無 input()，API Key 從環境變數讀取）
  3. 模組化設計（獨立 Function）
  4. 完整的錯誤處理和日誌
  5. 重試機制和超時控制

使用示例：
  python src/fetch_market_data.py
  或
  python -m src.fetch_market_data
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

# ==========================================
# 路徑設置 - 確保能找到 config_loader
# ==========================================

def setup_path():
    """確保 Python 能找到 config_loader"""
    # 方式 1：如果在 src 目錄裡執行，往上找一級
    current_dir = Path(__file__).parent.parent.resolve()
    if current_dir not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # 方式 2：也嘗試加入當前工作目錄
    cwd = Path.cwd()
    if cwd not in sys.path:
        sys.path.insert(0, str(cwd))

setup_path()

try:
    from config_loader import ConfigLoader
except ModuleNotFoundError as e:
    print(f"❌ 找不到 config_loader 模組: {e}")
    print(f"💡 提示：請確保在專案根目錄執行此程式")
    print(f"   當前工作目錄：{Path.cwd()}")
    print(f"   sys.path：{sys.path}")
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
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    # 日誌格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加處理器（避免重複）
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()


# ==========================================
# 路徑管理
# ==========================================

def get_data_dir() -> Path:
    """
    獲取 data/raw/ 目錄路徑，不存在則創建
    
    Returns:
        data/raw/ 目錄的 Path 物件
    """
    # 找到專案根目錄
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # src 的上一級
    
    # 驗證是否是專案根目錄
    if not (project_root / '.git').exists():
        logger.warning(f"⚠️ 警告：未找到 .git 目錄，嘗試使用當前工作目錄")
        project_root = Path.cwd()
    
    data_dir = project_root / 'data' / 'raw'
    
    # 如果目錄不存在，創建它
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ 數據目錄已確認：{data_dir}")
    
    return data_dir


# ==========================================
# 配置讀取
# ==========================================

def load_stock_config() -> Tuple[Dict, Optional[ConfigLoader]]:
    """
    從 settings.yaml 讀取股票配置
    
    Returns:
        (股票配置字典, ConfigLoader 物件) 
        
    Raises:
        FileNotFoundError: 找不到配置文件
        ValueError: 配置文件格式錯誤
    """
    try:
        logger.info("📖 正在讀取配置文件...")
        loader = ConfigLoader('config/settings.yaml')
        stocks_config = loader.config.get('stocks', {})
        
        if not stocks_config:
            logger.warning("⚠️ 配置文件中沒有定義任何股票")
            return {}, loader
        
        logger.info(f"✅ 成功讀取 {len(stocks_config)} 只股票的配置")
        
        # 列印股票清單
        stock_list = [f"{code} ({info.get('name', '未知')})" 
                      for code, info in stocks_config.items()]
        logger.info(f"   股票清單：{', '.join(stock_list)}")
        
        return stocks_config, loader
        
    except FileNotFoundError as e:
        logger.error(f"❌ 找不到配置文件: {e}")
        logger.error("💡 提示：請確保已執行 'cp config/settings.example.yaml config/settings.yaml'")
        raise
    except Exception as e:
        logger.error(f"❌ 讀取配置文件時出錯: {e}")
        raise ValueError(f"配置文件格式錯誤: {e}")


# ==========================================
# 單只股票數據抓取
# ==========================================

def fetch_single_stock(
    symbol: str,
    name: str,
    period: str = "1y",
    retries: int = 3,
) -> Optional[pd.DataFrame]:
    """
    抓取單只股票的歷史數據
    
    Args:
        symbol: 股票代碼（如 '2330.TW' 或 'AAPL'）
        name: 股票名稱（用於日誌）
        period: 數據週期（'1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', 等）
        retries: 重試次數
    
    Returns:
        包含股票數據的 DataFrame，或 None 如果抓取失敗
    """
    logger.info(f"📥 正在抓取 {name} ({symbol})，週期：{period}")
    
    for attempt in range(retries):
        try:
            # 使用 yfinance 抓取數據
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                logger.warning(f"  ⚠️ 第 {attempt + 1} 次嘗試：沒有返回數據")
                if attempt < retries - 1:
                    logger.info(f"  ↻ 等待後重試...")
                    continue
                else:
                    logger.error(f"  ❌ {name} ({symbol}) 重試 {retries} 次後仍失敗")
                    return None
            
            # 添加元數據
            df['Symbol'] = symbol
            df['Name'] = name
            df['FetchDate'] = datetime.now().isoformat()
            
            # 重新排序列
            cols = ['Symbol', 'Name', 'FetchDate', 'Open', 'High', 'Low', 'Close', 'Volume']
            available_cols = [col for col in cols if col in df.columns]
            df = df[available_cols]
            
            # 重置索引（將日期從索引變成列）
            df = df.reset_index()
            
            logger.info(f"  ✅ 成功抓取 {name}，共 {len(df)} 條數據")
            return df
            
        except Exception as e:
            logger.warning(f"  ⚠️ 第 {attempt + 1} 次嘗試失敗: {str(e)}")
            if attempt == retries - 1:
                logger.error(f"  ❌ {name} ({symbol}) 經過 {retries} 次重試仍失敗")
                return None
    
    return None


# ==========================================
# 多只股票數據抓取
# ==========================================

def fetch_all_stocks(
    period: str = "1y",
    save_csv: bool = True,
) -> Dict[str, bool]:
    """
    抓取所有配置的股票數據
    
    Args:
        period: 數據週期
        save_csv: 是否保存為 CSV 檔案
    
    Returns:
        {股票代碼: 是否成功} 的字典
        
    Example:
        >>> result = fetch_all_stocks(period="1y", save_csv=True)
        >>> print(result)
        {'TSMC_2330': True, 'NVDA': True, 'BRK_B': False}
    """
    logger.info("=" * 60)
    logger.info("🚀 開始執行數據收集任務")
    logger.info("=" * 60)
    
    # 第一步：讀取配置
    try:
        stocks_config, loader = load_stock_config()
        if not stocks_config:
            logger.error("❌ 沒有可抓取的股票配置")
            return {}
    except Exception as e:
        logger.error(f"❌ 無法讀取配置: {e}")
        return {}
    
    # 第二步：確認數據目錄
    data_dir = get_data_dir()
    
    # 第三步：抓取數據
    results = {}
    all_dataframes = {}
    
    logger.info("")
    logger.info(f"📊 開始抓取 {len(stocks_config)} 只股票的數據...")
    logger.info("")
    
    for stock_code, stock_info in stocks_config.items():
        try:
            name = stock_info.get('name', stock_code)
            market = stock_info.get('market', 'unknown')
            
            # 根據市場調整股票代碼格式
            if market.lower() == 'taiwan':
                # 台灣股票需要加上 .TW
                symbol = f"{stock_code}.TW"
            else:
                # 美股、香港等直接使用
                symbol = stock_code
            
            # 抓取數據
            df = fetch_single_stock(
                symbol=symbol,
                name=name,
                period=period,
                retries=3
            )
            
            if df is not None:
                all_dataframes[stock_code] = df
                results[stock_code] = True
            else:
                results[stock_code] = False
                
        except Exception as e:
            logger.error(f"❌ 處理股票 {stock_code} 時發生錯誤: {e}")
            results[stock_code] = False
    
    # 第四步：保存數據
    logger.info("")
    logger.info("💾 正在保存數據...")
    logger.info("")
    
    saved_count = 0
    for stock_code, df in all_dataframes.items():
        try:
            if save_csv:
                # 生成檔案名稱
                csv_filename = f"{stock_code}_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
                csv_path = data_dir / csv_filename
                
                # 保存為 CSV
                df.to_csv(csv_path, index=False, encoding='utf-8')
                logger.info(f"✅ 已保存 {stock_code} 至 {csv_path}")
                saved_count += 1
                
        except Exception as e:
            logger.error(f"❌ 保存 {stock_code} 時失敗: {e}")
    
    # 第五步：總結
    logger.info("")
    logger.info("=" * 60)
    logger.info("📈 任務完成！")
    logger.info("=" * 60)
    logger.info(f"✅ 成功抓取：{sum(results.values())} / {len(results)} 只股票")
    logger.info(f"💾 成功保存：{saved_count} 個 CSV 檔案至 {data_dir}")
    logger.info("")
    
    # 詳細統計
    success_stocks = [code for code, success in results.items() if success]
    failed_stocks = [code for code, success in results.items() if not success]
    
    if success_stocks:
        logger.info(f"✅ 成功股票：{', '.join(success_stocks)}")
    if failed_stocks:
        logger.warning(f"❌ 失敗股票：{', '.join(failed_stocks)}")
    
    logger.info("=" * 60)
    
    return results


# ==========================================
# 主函數（給 GitHub Actions 和本地測試用）
# ==========================================

def main():
    """
    主函數：執行完整的數據收集流程
    
    這個函數設計為：
    1. 本地終端機可直接執行：python -m src.fetch_market_data
    2. GitHub Actions 可排程執行
    3. 完全自動化，無需任何手動互動
    """
    try:
        # 執行數據收集
        results = fetch_all_stocks(
            period="1y",
            save_csv=True
        )
        
        # 根據結果返回退出碼
        if all(results.values()):
            logger.info("✅ 所有股票都成功抓取！")
            return 0
        else:
            failed_count = len([v for v in results.values() if not v])
            logger.warning(f"⚠️ 有 {failed_count} 只股票抓取失敗，但任務繼續進行")
            return 1
            
    except KeyboardInterrupt:
        logger.info("❌ 任務被用戶中止")
        return 130
    except Exception as e:
        logger.error(f"❌ 任務執行失敗: {e}")
        logger.error("💡 請檢查日誌信息並重試")
        return 1


# ==========================================
# 如果直接執行此檔案
# ==========================================

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

