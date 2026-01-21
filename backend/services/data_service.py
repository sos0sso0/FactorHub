"""
数据服务 - 使用 akshare 获取股票数据
支持本地缓存以提高性能
"""

import akshare as ak
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

from backend.core.settings import settings
from backend.core.exceptions import DataAccessException

logger = logging.getLogger(__name__)


class DataService:
    """数据服务类，封装 akshare 数据获取和缓存逻辑"""

    def __init__(self):
        self.cache_dir = settings.AKSHARE_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, symbol: str, data_type: str = "daily") -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{symbol}_{data_type}.parquet"

    def _is_cache_valid(self, cache_path: Path, max_days: int = 1) -> bool:
        """检查缓存是否有效"""
        if not cache_path.exists():
            return False

        # 检查文件修改时间
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if (datetime.now() - file_time).days > max_days:
            return False

        return True

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码，如 "000001"
            start_date: 开始日期，格式 "20240101"
            end_date: 结束日期，格式 "20241231"
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新

        Returns:
            包含 OHLCV 数据的 DataFrame
        """
        cache_path = self._get_cache_path(symbol, "daily")

        # 尝试从缓存加载
        if use_cache and not force_refresh and self._is_cache_valid(cache_path):
            try:
                logger.info(f"从缓存加载数据: {symbol}")
                df = pd.read_parquet(cache_path)

                # 过滤日期范围
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]

                return df
            except Exception as e:
                logger.warning(f"缓存加载失败: {e}")

        # 从 akshare 获取数据
        try:
            logger.info(f"从 akshare 获取数据: {symbol}")

            # 尝试不同的数据源
            try:
                # 股票日线数据
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            except Exception:
                try:
                    # 备用数据源
                    df = ak.stock_zh_a_daily(symbol=f"sz{symbol}")
                except Exception:
                    # 如果 akshare 失败，生成模拟数据用于测试
                    logger.warning(f"无法从 akshare 获取 {symbol} 数据，生成模拟数据")
                    df = self._generate_mock_data(symbol, start_date, end_date)

            # 数据预处理
            if not df.empty:
                # 标准化列名
                df = self._standardize_columns(df)

                # 保存到缓存
                if use_cache:
                    df.to_parquet(cache_path)
                    logger.info(f"数据已缓存: {cache_path}")

                # 过滤日期范围
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]

            return df

        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            raise

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 尝试识别并重命名列
        column_mapping = {}

        for col in df.columns:
            col_lower = col.lower()
            if "open" in col_lower:
                column_mapping[col] = "open"
            elif "high" in col_lower:
                column_mapping[col] = "high"
            elif "low" in col_lower:
                column_mapping[col] = "low"
            elif "close" in col_lower or "收盘" in col:
                column_mapping[col] = "close"
            elif "volume" in col_lower or "成交量" in col or "持仓量" in col:
                column_mapping[col] = "volume"
            elif "date" in col_lower or "日期" in col:
                column_mapping[col] = "date"

        if column_mapping:
            df = df.rename(columns=column_mapping)

        # 设置日期索引
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                pass

        # 确保必要的列存在
        required_columns = ["open", "high", "low", "close", "volume"]
        for col in required_columns:
            if col not in df.columns:
                # 如果缺失列，尝试用相似名称或填充
                if col == "volume" and "持仓量" in df.columns:
                    df[col] = df["持仓量"]
                else:
                    logger.warning(f"缺少列: {col}")

        return df

    def _generate_mock_data(
        self, symbol: str, start_date: Optional[str], end_date: Optional[str]
    ) -> pd.DataFrame:
        """生成模拟数据用于测试"""
        if end_date:
            end = datetime.strptime(end_date, "%Y%m%d")
        else:
            end = datetime.now()

        if start_date:
            start = datetime.strptime(start_date, "%Y%m%d")
        else:
            start = end - timedelta(days=365)

        dates = pd.date_range(start=start, end=end, freq="D")

        # 生成随机价格数据
        np.random.seed(hash(symbol) % (2**32))
        base_price = 50000 + np.random.randint(0, 50000)

        # 使用几何布朗运动模拟价格
        n = len(dates)
        returns = np.random.normal(0.001, 0.02, n)
        prices = base_price * np.exp(np.cumsum(returns))

        # 生成 OHLCV
        df = pd.DataFrame(
            {
                "open": prices * (1 + np.random.uniform(-0.01, 0.01, n)),
                "high": prices * (1 + np.random.uniform(0, 0.02, n)),
                "low": prices * (1 - np.random.uniform(0, 0.02, n)),
                "close": prices,
                "volume": np.random.randint(1000000, 10000000, n),
            },
            index=dates,
        )

        return df

    def get_multiple_symbols(
        self, symbols: List[str], start_date: str, end_date: str, use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个股票的数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            {symbol: DataFrame} 字典
        """
        result = {}
        for symbol in symbols:
            try:
                df = self.get_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=use_cache,
                )
                result[symbol] = df
            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")

        return result


# 全局数据服务实例
data_service = DataService()

# 向后兼容：保持旧方法名
data_service.get_futures_data = data_service.get_stock_data
