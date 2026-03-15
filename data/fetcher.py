"""Stock data fetching using yfinance."""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import DEFAULT_PERIOD, DEFAULT_INTERVAL


class DataFetcher:
    """Fetches and caches historical stock data."""

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
        Fetch OHLCV data for a symbol.

        Args:
            symbol: Ticker symbol (e.g. '600519.SS' for A-shares, 'AAPL' for US)
            period:  yfinance period string ('1mo','3mo','6mo','1y','2y','5y','max')
            interval: Data interval ('1d','1wk','1mo')
            start: Start date string 'YYYY-MM-DD' (overrides period)
            end: End date string 'YYYY-MM-DD'

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        cache_key = f"{symbol}_{period}_{interval}_{start}_{end}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        ticker = yf.Ticker(symbol)
        if start:
            df = ticker.history(start=start, end=end, interval=interval)
        else:
            df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise ValueError(f"No data returned for symbol '{symbol}'. Check the ticker.")

        # Normalize column names
        df.index = pd.to_datetime(df.index)
        df.index.name = "Date"
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)

        self._cache[cache_key] = df
        return df

    def fetch_multiple(
        self,
        symbols: list[str],
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols."""
        return {sym: self.fetch(sym, period, interval) for sym in symbols}

    def get_info(self, symbol: str) -> dict:
        """Return basic info about a ticker."""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        keys = ["longName", "sector", "industry", "marketCap", "currency", "exchange"]
        return {k: info.get(k, "N/A") for k in keys}
