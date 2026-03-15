"""Volatility-based technical indicators."""

import pandas as pd
import numpy as np


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.

    Returns:
        (upper_band, middle_band, lower_band)
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) – measures market volatility.

    Args:
        df: DataFrame with High, Low, Close columns
        period: Lookback period
    """
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean()


def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common volatility indicators to a OHLCV DataFrame."""
    df = df.copy()
    upper, middle, lower = bollinger_bands(df["Close"])
    df["BB_Upper"] = upper
    df["BB_Middle"] = middle
    df["BB_Lower"] = lower
    df["BB_Width"] = (upper - lower) / middle
    df["ATR_14"] = atr(df, 14)
    return df
