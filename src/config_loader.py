"""
ConfigLoader — 動態設定檔載入器

功能：
  • 從 YAML 檔案讀取設定
  • 提供便捷的 API 存取設定
  • 支持全域、分組、個別股票的規則

使用例：
  loader = ConfigLoader()
  stop_loss = loader.get_stock_setting('TSMC_2330', 'custom_stop_loss')
  # 得到: -10
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """載入和管理 YAML 設定檔"""
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """
        初始化 ConfigLoader
        
        Args:
            config_path: 設定檔路徑（預設 config/settings.yaml）
        
        Raises:
            FileNotFoundError: 如果設定檔不存在
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        載入 YAML 設定檔
        
        Returns:
            設定字典
        
        Raises:
            FileNotFoundError: 設定檔不存在
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"❌ 設定檔不存在: {self.config_path}\n"
                f"請執行以下命令複製範本：\n"
                f"  cp config/settings.example.yaml config/settings.yaml"
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config is None:
                    raise ValueError("設定檔為空")
                return config
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 語法錯誤: {e}")
    
    # ==========================================
    # 全域設定
    # ==========================================
    
    def get_global(self, key: str, default: Any = None) -> Any:
        """
        取得全域設定
        
        Args:
            key: 設定鍵名（如 'default_stop_loss'）
            default: 預設值
        
        Returns:
            設定值或預設值
        
        Example:
            >>> loader.get_global('default_stop_loss')
            -15
        """
        global_config = self.config.get('global', {})
        return global_config.get(key, default)
    
    # ==========================================
    # 股票分組規則
    # ==========================================
    
    def get_group(self, group_name: str) -> Dict[str, Any]:
        """
        取得股票分組的完整設定
        
        Args:
            group_name: 分組名稱（如 'taiwan_tech'）
        
        Returns:
            分組設定字典
        
        Example:
            >>> loader.get_group('taiwan_tech')
            {'description': '台灣科技股', 'risk_level': 'medium', ...}
        """
        stock_groups = self.config.get('stock_groups', {})
        return stock_groups.get(group_name, {})
    
    def get_group_setting(self, group_name: str, key: str, default: Any = None) -> Any:
        """
        取得特定分組的特定設定
        
        Args:
            group_name: 分組名稱
            key: 設定鍵名
            default: 預設值
        
        Returns:
            設定值
        
        Example:
            >>> loader.get_group_setting('taiwan_tech', 'stop_loss')
            -12
        """
        group = self.get_group(group_name)
        return group.get(key, default)
    
    # ==========================================
    # 個別股票規則
    # ==========================================
    
    def get_stock(self, stock_symbol: str) -> Dict[str, Any]:
        """
        取得股票的完整設定
        
        Args:
            stock_symbol: 股票代碼（如 'TSMC_2330'）
        
        Returns:
            股票設定字典
        
        Example:
            >>> loader.get_stock('TSMC_2330')
            {'name': '台積電', 'market': 'taiwan', ...}
        """
        stocks = self.config.get('stocks', {})
        return stocks.get(stock_symbol, {})
    
    def get_stock_setting(self, stock_symbol: str, key: str, default: Any = None) -> Any:
        """
        取得股票的特定設定，支持三層級優先順序
        
        優先順序：
          1. 個別股票設定（最高）
          2. 分組設定
          3. 全域設定（最低）
        
        Args:
            stock_symbol: 股票代碼
            key: 設定鍵名
            default: 預設值
        
        Returns:
            設定值
        
        Example:
            >>> loader.get_stock_setting('TSMC_2330', 'stop_loss')
            # 檢查順序：
            # 1. TSMC_2330 的 custom_stop_loss（-10）← 會用這個
            # 2. taiwan_tech 分組的 stop_loss（-12）
            # 3. 全域的 default_stop_loss（-15）
            -10
        """
        stock_config = self.get_stock(stock_symbol)
        
        # 第一層：個別股票設定
        if f'custom_{key}' in stock_config:
            return stock_config[f'custom_{key}']
        
        # 第二層：分組設定
        if 'group' in stock_config:
            group_name = stock_config['group']
            group_config = self.get_group(group_name)
            if key in group_config:
                return group_config[key]
        
        # 第三層：全域設定
        global_key = f'default_{key}'
        global_value = self.get_global(global_key)
        if global_value is not None:
            return global_value
        
        # 都沒有的話，回傳預設值
        return default
    
    # ==========================================
    # 便利方法：常用設定
    # ==========================================
    
    def get_stop_loss(self, stock_symbol: str) -> float:
        """取得股票的停損點"""
        return self.get_stock_setting(stock_symbol, 'stop_loss', -15)
    
    def get_take_profit_1(self, stock_symbol: str) -> float:
        """取得股票的第一個停利點"""
        return self.get_stock_setting(stock_symbol, 'take_profit_1', 10)
    
    def get_take_profit_2(self, stock_symbol: str) -> float:
        """取得股票的第二個停利點"""
        return self.get_stock_setting(stock_symbol, 'take_profit_2', 20)
    
    def get_max_allocation(self, stock_symbol: str) -> float:
        """取得股票的最大配置百分比"""
        return self.get_stock_setting(stock_symbol, 'max_allocation', 20)
    
    # ==========================================
    # 除錯和驗證
    # ==========================================
    
    def print_summary(self) -> None:
        """列印設定檔摘要（用於除錯）"""
        print("=" * 50)
        print("📋 設定檔摘要")
        print("=" * 50)
        
        print("\n🌍 全域設定：")
        for key, value in self.config.get('global', {}).items():
            print(f"  {key}: {value}")
        
        print("\n📊 股票分組：")
        for group_name in self.config.get('stock_groups', {}).keys():
            print(f"  • {group_name}")
        
        print("\n💰 個別股票：")
        for stock_symbol in self.config.get('stocks', {}).keys():
            print(f"  • {stock_symbol}")
        
        print("\n" + "=" * 50)


# ==========================================
# 範例和測試
# ==========================================

if __name__ == '__main__':
    print("📦 ConfigLoader 測試")
    print("=" * 50)
    
    try:
        # 初始化載入器
        loader = ConfigLoader()
        print("✅ 設定檔載入成功！\n")
        
        # 測試全域設定
        print("🌍 全域設定示例：")
        print(f"  預設停損: {loader.get_global('default_stop_loss')}%")
        print(f"  預設停利1: {loader.get_global('default_take_profit_1')}%")
        print(f"  預設停利2: {loader.get_global('default_take_profit_2')}%\n")
        
        # 測試分組設定
        print("📊 分組設定示例（台灣科技股）：")
        taiwan_tech = loader.get_group('taiwan_tech')
        print(f"  風險等級: {taiwan_tech.get('risk_level')}")
        print(f"  停損: {taiwan_tech.get('stop_loss')}%")
        print(f"  停利1: {taiwan_tech.get('take_profit_1')}%\n")
        
        # 測試個別股票設定（三層級優先順序）
        print("💰 個別股票設定示例（台積電）：")
        print(f"  股票: {loader.get_stock('TSMC_2330').get('name')}")
        print(f"  停損: {loader.get_stop_loss('TSMC_2330')}%")
        print(f"    ↳ 來自個別設定的 custom_stop_loss: -10%")
        print(f"  停利1: {loader.get_take_profit_1('TSMC_2330')}%")
        print(f"  停利2: {loader.get_take_profit_2('TSMC_2330')}%\n")
        
        # 列印摘要
        loader.print_summary()
        
    except FileNotFoundError as e:
        print(f"❌ 錯誤: {e}")

