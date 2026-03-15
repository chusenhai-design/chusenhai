"""Stock data fetching – supports akshare, CSV files, and mock data."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from config import DEFAULT_PERIOD, DEFAULT_INTERVAL


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convert period string to (start, end) date strings (YYYYMMDD)."""
    end = datetime.today()
    mapping = {
        "1mo": 30, "3mo": 90, "6mo": 180,
        "1y": 365, "2y": 730, "3y": 1095,
        "5y": 1825, "max": 3650,
    }
    days = mapping.get(period, 730)
    start = end - timedelta(days=days)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def generate_mock_data(
    symbol: str = "MOCK",
    days: int = 500,
    start_price: float = 100.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    生成模拟股价数据（几何布朗运动），用于离线测试。

    Args:
        symbol: 股票代码（仅用于打印提示）
        days: 生成天数
        start_price: 起始价格
        seed: 随机种子（保证可重现）

    Returns:
        DataFrame with Open/High/Low/Close/Volume columns
    """
    rng = np.random.default_rng(seed)
    mu = 0.0003       # 日均收益率
    sigma = 0.015     # 日波动率

    dates = pd.date_range(
        end=datetime.today().strftime("%Y-%m-%d"),
        periods=days,
        freq="B",  # 工作日
    )
    n = len(dates)

    returns = rng.normal(mu, sigma, n)
    prices = start_price * np.exp(np.cumsum(returns))

    # 生成 OHLCV
    noise = rng.uniform(0.005, 0.02, n)
    opens = prices * rng.uniform(0.995, 1.005, n)
    highs = prices * (1 + noise)
    lows = prices * (1 - noise)
    closes = prices
    volumes = rng.integers(1_000_000, 10_000_000, n).astype(float)

    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    }, index=dates)
    df.index.name = "Date"
    return df


class DataFetcher:
    """
    获取股票 OHLCV 历史数据，支持三种来源：
      1. akshare  – 联网获取真实行情（A股/港股/美股）
      2. CSV 文件 – 从本地文件读取
      3. mock     – 离线模拟数据，用于测试
    """

    def __init__(self):
        self._cache: dict[str, pd.DataFrame] = {}

    def fetch(
        self,
        symbol: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        获取股票数据。

        symbol 格式：
          - A股 6位数字：'600519'
          - 港股 5位数字：'00700'
          - 美股英文：'AAPL'
          - CSV文件：'csv:path/to/file.csv'
          - 离线模拟：'mock' 或 'mock:500:100.0'（天数:起始价）
        """
        cache_key = f"{symbol}_{period}_{interval}_{start}_{end}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # --- CSV 文件 ---
        if symbol.startswith("csv:"):
            path = symbol[4:]
            df = self._fetch_csv(path)

        # --- 模拟数据 ---
        elif symbol.startswith("mock"):
            parts = symbol.split(":")
            days = int(parts[1]) if len(parts) > 1 else 500
            price = float(parts[2]) if len(parts) > 2 else 100.0
            df = generate_mock_data(symbol, days=days, start_price=price)

        # --- akshare 联网 ---
        else:
            if start:
                start_dt = start.replace("-", "")
                end_dt = (end or datetime.today().strftime("%Y-%m-%d")).replace("-", "")
            else:
                start_dt, end_dt = _period_to_dates(period)

            if symbol.isdigit() and len(symbol) == 6:
                df = self._fetch_ashare(symbol, start_dt, end_dt)
            elif symbol.isdigit() and len(symbol) == 5:
                df = self._fetch_hkshare(symbol, start_dt, end_dt)
            else:
                df = self._fetch_us(symbol, start_dt, end_dt)

        if df.empty:
            raise ValueError(f"未获取到 '{symbol}' 的数据，请检查代码或网络。")

        df.dropna(inplace=True)
        self._cache[cache_key] = df
        return df

    def _fetch_csv(self, path: str) -> pd.DataFrame:
        """
        从 CSV 文件读取数据。

        CSV 格式要求：
          - 必须有 Date 列（或第一列为日期）
          - 必须有 Open, High, Low, Close, Volume 列
        """
        df = pd.read_csv(path, parse_dates=True)
        # 尝试自动识别日期列
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            df.index.name = "Date"
        else:
            df.index = pd.to_datetime(df.index)
            df.index.name = "Date"

        # 统一列名（兼容中英文）
        col_map = {
            "open": "Open", "high": "High", "low": "Low",
            "close": "Close", "volume": "Volume",
            "开盘": "Open", "最高": "High", "最低": "Low",
            "收盘": "Close", "成交量": "Volume",
        }
        df = df.rename(columns=col_map)
        return df[["Open", "High", "Low", "Close", "Volume"]]

    def _fetch_ashare(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        import akshare as ak
        raw = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq",
        )
        raw = raw.rename(columns={
            "日期": "Date", "开盘": "Open", "最高": "High",
            "最低": "Low", "收盘": "Close", "成交量": "Volume",
        })
        raw["Date"] = pd.to_datetime(raw["Date"])
        return raw.set_index("Date")[["Open", "High", "Low", "Close", "Volume"]]

    def _fetch_hkshare(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        import akshare as ak
        raw = ak.stock_hk_hist(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq",
        )
        raw = raw.rename(columns={
            "日期": "Date", "开盘": "Open", "最高": "High",
            "最低": "Low", "收盘": "Close", "成交量": "Volume",
        })
        raw["Date"] = pd.to_datetime(raw["Date"])
        return raw.set_index("Date")[["Open", "High", "Low", "Close", "Volume"]]

    def _fetch_us(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        import akshare as ak
        raw = ak.stock_us_hist(
            symbol=symbol.lower(), period="daily",
            start_date=start, end_date=end, adjust="qfq",
        )
        raw = raw.rename(columns={
            "日期": "Date", "开盘": "Open", "最高": "High",
            "最低": "Low", "收盘": "Close", "成交量": "Volume",
        })
        raw["Date"] = pd.to_datetime(raw["Date"])
        return raw.set_index("Date")[["Open", "High", "Low", "Close", "Volume"]]

    def fetch_multiple(
        self,
        symbols: list[str],
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
    ) -> dict[str, pd.DataFrame]:
        """批量获取多只股票数据。"""
        return {sym: self.fetch(sym, period, interval) for sym in symbols}

    def get_info(self, symbol: str) -> dict:
        """获取股票基本信息（联网）。"""
        if symbol.isdigit() and len(symbol) == 6:
            try:
                import akshare as ak
                df = ak.stock_individual_info_em(symbol=symbol)
                return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
            except Exception:
                pass
        return {"symbol": symbol, "说明": "暂无信息（网络不可用或非A股代码）"}
